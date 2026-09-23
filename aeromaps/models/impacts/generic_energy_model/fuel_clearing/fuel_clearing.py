"""The fuel market as a GEMSEO discipline.

``FuelClearing`` is a **global** model: deliberately not namespaced, so its grammar is
written directly in ``{region}:var`` terms and it can read every region's demand in one
call. That is what lets a single convex program clear all regions together
(:mod:`~aeromaps.models.impacts.generic_energy_model.fuel_clearing.kernel`).

At step 1 nothing actually couples the regions -- every constraint is per-region and the
objective is a plain sum, so solving jointly and solving one at a time agree to solver
noise. The global form is what shared feedstock and inter-regional trade will need, and
it costs nothing to adopt now.

**What it replaces.** In this mode ``EnergyUseChoice`` does not run: the market decides
the per-pathway volumes instead of allocating them against a fixed share. It therefore
emits the same output families, under the same names, so nothing downstream can tell the
difference -- the share families come from the shared
:func:`~aeromaps.models.impacts.generic_energy_model.common.energy_use_choice.derive_share_families`
rather than from a second copy of that arithmetic.

**What it adds.** ``{p}_market_mfsp``: the price the market clears at, which
``EnergyCarriersMeans`` weights in place of ``{p}_mean_mfsp``. It differs from the
production cost by the scarcity rent, a quantity that does not exist anywhere else in
AeroMAPS -- ``{type}_marginal_net_mfsp`` is a maximum over pathway costs and so is capped
by the dearest pathway, whereas a shadow price sits above all of them when supply is
tight.

**Decides on net cost, reports on gross.** The allocation uses ``{p}_net_mfsp`` -- the
cost the buyer actually faces, carbon tax and subsidies included -- because that is what
decides which pathway is marginal. On the step-1 bench a carbon tax of only 5 EUR/t
already narrows the sustainable premium by 3 %, and around 164 EUR/t it would reverse the
ordering outright. But ``DirectOperatingCosts`` adds the carbon tax as its own line on top
of the fuel line, so the published price is put back on the same gross basis
``{p}_mean_mfsp`` uses. Decide on net, report on gross, and the tax is counted once.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.models.impacts.generic_energy_model.common.energy_use_choice import (
    derive_share_families,
)

from .kernel import ClearingInputs, clear_market

# The market lives on one hard energy budget. Step 1 is drop-in only: hydrogen and
# electric have their own budgets and their own allocator, and a market that silently
# ignored them would under-serve those aircraft types rather than fail.
SUPPORTED_AIRCRAFT_TYPE = "dropin_fuel"

# Defaults for the market's own parameters, all overridable from configuration_data.
# `sat_gamma = 0` and a loose ramp-up mean "no scarcity", under which the market
# reproduces the current mode exactly -- a behaviour-preserving starting point rather
# than an opinionated one.
DEFAULT_SETTINGS = {
    "pricing_weight": 0.0,
    "discount_rate": 0.04,
    "saturation_intensity": 0.0,
    "saturation_stiffness": 4.0,
    # "No ramp-up limit" is a large FINITE number, not inf: the limit is a coefficient
    # inside the constraint, and the kernel refuses non-finite inputs outright
    # (decision 9). Capacity is different -- there inf is the documented way to say
    # "this pathway does not saturate" and the kernel tests for it.
    "rampup_limit": 1.0e3,
    # Defaults are "no ramp-up", so the mode reproduces the current one out of the box.
    # When the ramp-up IS switched on, `rampup_seed_share` is not a free dial: in the
    # correspondence with the optimisation mode's Eq. 12 it is that constraint's volume
    # branch, `dE * dt`. The published calibration is
    # `volume_ramp_up_constraint_biofuel = 0.2 EJ/yr` scaled by an ASK share of 0.1549,
    # which is about 1.5 % of that scenario's annual demand -- so `0.015` is the
    # calibrated annual value, and anything far from it is a different assumption about
    # industrial capacity addition, not a tuning choice. It matters: on the step-1 bench
    # the seed moves the compliance price 4.3x across the range 0.001 to 1.0.
    "rampup_seed_share": 1.0,
    "rampup_form": "relative",
    "buyout_price": 1.0e3,
    "capacity": np.inf,
    "solver_tolerance": 1.0e-9,
    # Anchors the solve on the mix the previous coupling iteration produced, which is
    # what makes the price a continuous function of the loop's state instead of an
    # arbitrary pick from an interval. Costs nothing at `pricing_weight = 0`, where the
    # price never depended on a dual in the first place; at `pricing_weight > 0` the loop
    # does not converge without it. Zero disables it. See `kernel.proximal_weight`.
    "proximal_weight": 0.0,
    # How much demand the loop OUTSIDE this discipline withdraws when the delivered price
    # rises by 1 %, as a fraction. Not a physical constant and not calibrated: it tells
    # the market what slope of demand curve to price against where its own supply curve
    # is vertical, and it is inert once the loop settles. Zero restores the rigid
    # balance, under which `pricing_weight > 0` does not converge. See
    # `kernel.demand_slope`, and REPORT.md section 8.6 for how to choose it.
    "demand_elasticity": 0.0,
}


# Settings that describe a pathway being *scarce*. A global value for these reaches
# every pathway, which is wrong for the residual -- see `_pathway_setting`. The ramp-up
# keys are not here because the kernel applies the growth limit to eligible rows only,
# so a global value is already inert on the residual.
_SCARCITY_SETTINGS = frozenset({"capacity", "saturation_intensity"})


class FuelClearingConfigurationError(ValueError):
    """The market cannot be built from this scenario.

    Raised at setup rather than at solve time (decision 11): every one of these is a
    configuration mistake whose symptom downstream would be a plausible-looking number.
    """


class FuelClearing(AeroMAPSModel):
    """Clear the drop-in fuel market across all regions in one convex program.

    Parameters
    ----------
    name
        Model instance name.
    configuration_data
        The market's own settings. Per-pathway entries live under ``pathways``; the rest
        are read from the top level with :data:`DEFAULT_SETTINGS` as fallbacks.

    Attributes
    ----------
    regions
        Injected by ``MultiRegionalProcess._wrap_global_model`` before ``custom_setup``.
    pathways_manager
        Likewise injected. A global model gets one manager for all regions, which is only
        meaningful if every region declares the same pathways -- checked in
        :meth:`custom_setup`.
    """

    def __init__(self, name="fuel_clearing", configuration_data=None, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)

        # Injected before custom_setup(); the placeholders keep __init__ importable.
        self.regions = []
        self.global_namespace = "overall"
        self.pathways_manager = None

        self.configuration_data = configuration_data or {}
        self.settings = dict(DEFAULT_SETTINGS)
        self.pathway_names = []
        self.sustainable_names = []
        self.residual_name = None

        self.input_names = {}
        self.output_names = {}

        # The only state this discipline carries between calls: the mix the previous
        # coupling iteration cleared at, as shares of demand. It is an ANCHOR, not a
        # memory of an answer -- see `_anchor_volumes`. Shares rather than volumes so it
        # survives the demand moving underneath it, which is precisely what the traffic
        # loop does to it.
        self._anchor_shares = None
        # ... and the delivered marginal price it cleared at, on the kernel's own (net)
        # basis. This is the point of the demand curve the next solve prices against.
        self._anchor_price = None
        # Per-iteration trace, appended to only when `record_trace` is set. The coupled
        # diagnosis in fuel_clearing_step1/convergence.py reads it.
        self.trace = []
        self.record_trace = False

    # -- setup ---------------------------------------------------------------

    def custom_setup(self):
        """Build the namespaced grammar once the region list and pathways are known."""
        if not self.regions:
            raise FuelClearingConfigurationError(
                "FuelClearing.custom_setup() ran before the region list was injected. "
                "The market must be declared under 'regionalisation.global_models'."
            )
        if self.pathways_manager is None:
            raise FuelClearingConfigurationError(
                "FuelClearing.custom_setup() ran without a pathways_manager. It is "
                "injected by MultiRegionalProcess._wrap_global_model."
            )

        self._read_settings()
        self._collect_pathways()
        self._build_grammar()

    def _read_settings(self):
        for key in DEFAULT_SETTINGS:
            if key in self.configuration_data:
                self.settings[key] = self.configuration_data[key]

    def _collect_pathways(self):
        """Resolve the pathway roles, and refuse the configurations step 1 cannot serve."""
        declared_types = set(self.pathways_manager.get_all_types("aircraft_type"))
        unsupported = declared_types - {SUPPORTED_AIRCRAFT_TYPE}
        if unsupported:
            raise FuelClearingConfigurationError(
                f"The fuel market serves '{SUPPORTED_AIRCRAFT_TYPE}' only, but this "
                f"scenario declares {sorted(unsupported)}. Those aircraft types have "
                "their own energy budget and are allocated by EnergyUseChoice, which "
                "this mode replaces -- so they would silently receive no fuel at all. "
                "Remove them, or leave the fuel market off until it serves them."
            )

        pathways = self.pathways_manager.get(aircraft_type=SUPPORTED_AIRCRAFT_TYPE)
        if len(pathways) < 2:
            raise FuelClearingConfigurationError(
                f"The fuel market needs at least two {SUPPORTED_AIRCRAFT_TYPE} pathways "
                f"to have anything to decide; this scenario declares {len(pathways)}."
            )

        # Decision 6, "for now": a bottom-up cost makes the average cost FALL with volume
        # through the vintage mix, so the cost integral turns concave and the duals stop
        # being prices. See REPORT.md section 6 for the two routes out.
        bottom_up = sorted(p.name for p in pathways if getattr(p, "cost_model", None) != "top-down")
        if bottom_up:
            raise FuelClearingConfigurationError(
                f"The fuel market requires the top-down cost model, but {bottom_up} "
                "use another. A bottom-up cost makes average cost fall as volume rises "
                "(newer, cheaper vintages dilute the mix), which makes the cost integral "
                "concave -- the program stops being convex and its duals stop being "
                "prices. This is a 'for now', not an exclusion."
            )

        residual = [p.name for p in pathways if getattr(p, "default", False)]
        if len(residual) != 1:
            raise FuelClearingConfigurationError(
                f"Exactly one default {SUPPORTED_AIRCRAFT_TYPE} pathway is required to "
                f"close the energy balance; found {residual or 'none'}."
            )

        self.residual_name = residual[0]
        # Deterministic order: the kernel's arrays are positional, and a set-ordering
        # change would silently permute costs against volumes.
        self.pathway_names = sorted(p.name for p in pathways)
        self.sustainable_names = sorted(
            p.name
            for p in pathways
            if p.name != self.residual_name and getattr(p, "mandate_type", None) == "share"
        )
        if not self.sustainable_names:
            raise FuelClearingConfigurationError(
                "No share-mandated pathway found, so the market has no obligation to "
                "clear against. Declare `mandate_type: share` on the sustainable "
                "pathway, or use the standard mode."
            )

    def _build_grammar(self):
        """Namespaced inputs and outputs, one set per region."""
        self.input_names = {}
        self.output_names = {}

        for region in self.regions:
            self.input_names[f"{region}:energy_consumption_{SUPPORTED_AIRCRAFT_TYPE}"] = pd.Series(
                [0.0]
            )
            self.input_names[f"{region}:energy_consumption"] = pd.Series([0.0])
            for pathway in self.pathway_names:
                # Gross production cost and the buyer-faced cost. Both, because the
                # market decides on the second and publishes on the basis of the first.
                self.input_names[f"{region}:{pathway}_mean_mfsp"] = pd.Series([0.0])
                self.input_names[f"{region}:{pathway}_net_mfsp"] = pd.Series([0.0])
            for pathway in self.sustainable_names:
                self.input_names[f"{region}:{pathway}_mandate_share"] = pd.Series([0.0])

        for region in self.regions:
            for pathway in self.pathway_names:
                self.output_names[f"{region}:{pathway}_energy_consumption"] = pd.Series([0.0])
                self.output_names[f"{region}:{pathway}_market_mfsp"] = pd.Series([0.0])
            # Prices of the constraints. `energy_price` and `compliance_price` are only
            # separately meaningful below a full obligation -- see kernel.py.
            self.output_names[f"{region}:fuel_market_energy_price"] = pd.Series([0.0])
            self.output_names[f"{region}:fuel_market_compliance_price"] = pd.Series([0.0])
            self.output_names[f"{region}:fuel_market_unmet_obligation"] = pd.Series([0.0])

            for name in self._derived_output_names():
                self.output_names[f"{region}:{name}"] = pd.Series([0.0])

    def _derived_output_names(self):
        """The share families, named exactly as EnergyUseChoice names them."""
        zero = pd.Series(0.0, index=range(self.historic_start_year, self.end_year + 1))
        derived = derive_share_families(
            volumes={p.name: zero for p in self.pathways_manager.get_all()},
            total_energy_consumption=zero,
            type_energy_consumption={
                aircraft_type: zero
                for aircraft_type in self.pathways_manager.get_all_types("aircraft_type")
            },
            pathways_manager=self.pathways_manager,
            fallback_index=zero.index,
        )
        return list(derived)

    def _initialize_df(self):
        """Seed every coupled input, so the MDA has somewhere to start.

        The market sits inside the traffic loop -- its price reaches the airfare, which
        reaches demand, which comes back as the energy consumption it reads -- and it
        also reads the pathway costs, which are disciplines' outputs rather than
        parameters. GEMSEO's initialisation chain needs one discipline whose inputs are
        ALL available before it can order the rest; seeding only the demand left none,
        and the whole coupled component refused to order.

        The values only have to be sane, not right: one Gauss-Seidel sweep replaces
        them. A zero seed is what is not acceptable -- a zero demand makes the very
        first solve degenerate rather than merely inaccurate, and a zero cost makes
        every pathway equally cheap.
        """
        super()._initialize_df()
        self._anchor_shares = None
        self._anchor_price = None
        self.trace = []
        regions = getattr(self, "regions", [])
        if not regions:
            return

        demand_seed = float(self.configuration_data.get("demand_seed", 1.0e13))
        cost_seed = float(self.configuration_data.get("cost_seed", 0.02))
        index = self.df.index

        defaults = {}
        for region in regions:
            defaults[f"{region}:energy_consumption_{SUPPORTED_AIRCRAFT_TYPE}"] = pd.Series(
                demand_seed, index=index
            )
            defaults[f"{region}:energy_consumption"] = pd.Series(demand_seed, index=index)
            for pathway in self.pathway_names:
                defaults[f"{region}:{pathway}_mean_mfsp"] = pd.Series(cost_seed, index=index)
                defaults[f"{region}:{pathway}_net_mfsp"] = pd.Series(cost_seed, index=index)
        self._coupling_defaults = defaults

    # -- solve ---------------------------------------------------------------

    def _pathway_setting(self, key, pathway, default):
        """Per-pathway override under ``pathways: {name: {...}}``, else the global value.

        **The residual pathway is exempt from the global scarcity settings**, and takes
        ``default`` unless it is named explicitly. Without that, a scenario saying
        "capacity is 1.1e13" -- meaning the sustainable pathway it is studying -- also
        saturates kerosene, and every bench script in this spike did exactly that: the
        residual ran at 90 % utilisation, its marginal cost rose with it, and
        ``energy_price`` stopped being the cost of the marginal conventional fuel. The
        identity ``lambda_E = c_kerosene`` that the report asserts and publishes was
        false by 2.2 % on the coupled grid for that reason alone.

        The residual is the backstop that absorbs whatever the balance needs; a
        *global* default that constrains it is almost never what was meant. Naming it
        under ``pathways:`` still works, because a fossil supply limit is a legitimate
        thing to model -- it just has to be asked for.
        """
        per_pathway = self.configuration_data.get("pathways", {}).get(pathway, {})
        if key in per_pathway:
            return per_pathway[key]
        if key in _SCARCITY_SETTINGS and pathway == self.residual_name:
            return default
        return self.settings.get(key, default)

    def _prospective(self, series):
        return np.asarray(series.loc[self.prospection_start_year : self.end_year], dtype=float)

    def _anchor_volumes(self, demand):
        """Last iteration's mix, re-expressed at this iteration's demand. None on entry.

        The first call has nothing to anchor on and solves the plain program, so a market
        run once outside a coupling loop is untouched by any of this. From the second
        call on, the anchor is the previous mix -- and because the term it weights is
        ``(q - anchor)^2``, it is inert exactly when the mix has stopped moving. The loop
        therefore converges to a solution of the *unregularised* program or not at all:
        there is no fixed point at which the anchor is still bending the answer.
        """
        if self._anchor_shares is None or float(self.settings["proximal_weight"]) <= 0:
            return None
        return self._anchor_shares * demand[:, None, :]

    def _demand_curve(self, demand):
        """``(anchor_price, slope)`` for the elastic balance, or ``(None, None)``.

        The slope is built from a dimensionless elasticity so it carries the units of the
        problem rather than of the configuration file: ``beta = eta * D / p0`` means "a
        1 % rise in the delivered price withdraws ``eta`` % of demand".

        Zeroed wherever there is no price or no demand to take a proportion of -- a
        vertical demand curve there, which is what the market had everywhere before.
        """
        elasticity = float(self.settings["demand_elasticity"])
        if self._anchor_price is None or elasticity <= 0:
            return None, None
        price = self._anchor_price
        usable = (price > 0) & (demand > 0)
        slope = np.where(usable, elasticity * demand / np.where(usable, price, 1.0), 0.0)
        return np.where(usable, price, 0.0), slope

    def _build_inputs(self, input_data):
        """Assemble the kernel's arrays from the namespaced grammar."""
        regions = list(self.regions)
        pathways = list(self.pathway_names)
        years = self.end_year - self.prospection_start_year + 1
        shape = (len(regions), len(pathways), years)

        demand = np.zeros((len(regions), years))
        cost = np.zeros(shape)
        gross = np.zeros(shape)
        capacity = np.full(shape, np.inf)
        mandate_share = np.zeros((len(regions), years))
        buyout = np.zeros((len(regions), years))
        sat_gamma = np.zeros((len(regions), len(pathways)))
        rampup_limit = np.zeros((len(regions), len(pathways)))
        rampup_seed = np.zeros((len(regions), len(pathways)))
        q_init = np.zeros((len(regions), len(pathways)))

        for r, region in enumerate(regions):
            budget = input_data[f"{region}:energy_consumption_{SUPPORTED_AIRCRAFT_TYPE}"]
            demand[r] = np.nan_to_num(self._prospective(budget), nan=0.0)

            # The obligation the market clears against is on the SUM of the mandated
            # pathways: the kernel carries one share per region and flags which pathways
            # count toward it. With a single sustainable pathway -- step 1 -- the two are
            # the same thing.
            share = np.zeros(years)
            for pathway in self.sustainable_names:
                share += np.nan_to_num(
                    self._prospective(input_data[f"{region}:{pathway}_mandate_share"]), nan=0.0
                )
            mandate_share[r] = np.clip(share / 100.0, 0.0, 1.0)

            buyout[r] = float(self.settings["buyout_price"])

            last_historical_budget = float(
                np.nan_to_num(budget.loc[self.last_historical_year], nan=0.0)
            )

            for p, pathway in enumerate(pathways):
                # Decide on the buyer-faced cost; keep the gross one to publish against.
                cost[r, p] = np.nan_to_num(
                    self._prospective(input_data[f"{region}:{pathway}_net_mfsp"]), nan=0.0
                )
                gross[r, p] = np.nan_to_num(
                    self._prospective(input_data[f"{region}:{pathway}_mean_mfsp"]), nan=0.0
                )
                capacity[r, p] = float(self._pathway_setting("capacity", pathway, np.inf))
                sat_gamma[r, p] = float(self._pathway_setting("saturation_intensity", pathway, 0.0))
                rampup_limit[r, p] = float(self._pathway_setting("rampup_limit", pathway, np.inf))
                rampup_seed[r, p] = (
                    float(self._pathway_setting("rampup_seed_share", pathway, 1.0))
                    * last_historical_budget
                )
                # The ramp-up's initial condition is what the last historical year
                # actually produced: the residual pathway carried the whole budget,
                # since no obligation existed before the prospective period.
                q_init[r, p] = last_historical_budget if pathway == self.residual_name else 0.0

        is_sustainable = np.array([p in self.sustainable_names for p in pathways])
        anchor_price, demand_slope = self._demand_curve(demand)

        return (
            ClearingInputs(
                demand=demand,
                cost=cost,
                is_sustainable=is_sustainable,
                mandate_share=mandate_share,
                buyout_price=buyout,
                capacity=capacity,
                sat_gamma=sat_gamma,
                sat_n=float(self.settings["saturation_stiffness"]),
                rampup_limit=rampup_limit,
                rampup_seed=rampup_seed,
                q_init=q_init,
                discount_rate=float(self.settings["discount_rate"]),
                pricing_weight=float(self.settings["pricing_weight"]),
                rampup_form=str(self.settings["rampup_form"]),
                residual_pathway=pathways.index(self.residual_name),
                solver_tolerance=float(self.settings["solver_tolerance"]),
                proximal_anchor=self._anchor_volumes(demand),
                proximal_weight=float(self.settings["proximal_weight"]),
                anchor_price=anchor_price,
                demand_slope=demand_slope,
            ),
            gross,
        )

    def _remember(self, inputs, outputs):
        """Keep the cleared mix for the next call's anchor, and trace if asked.

        A share, not a volume, and guarded at zero demand: a year the traffic loop has
        driven to nothing must not hand the next iteration a 0/0.
        """
        total = np.sum(outputs.volume, axis=1)[:, None, :]
        self._anchor_shares = np.divide(
            outputs.volume, total, out=np.zeros_like(outputs.volume), where=total > 0
        )
        # The delivered MARGINAL price, which is what the elastic balance's stationarity
        # condition equates to the inverse demand -- not `market_mfsp`, which at w < 1 is
        # partly an average and would put the anchor on the wrong curve.
        marginal = np.sum(outputs.marginal_price * outputs.volume, axis=1)
        self._anchor_price = np.divide(
            marginal, total[:, 0, :], out=np.zeros_like(marginal), where=total[:, 0, :] > 0
        )
        if not self.record_trace:
            return
        delivered = np.divide(
            np.sum(outputs.market_mfsp * outputs.volume, axis=1),
            total[:, 0, :],
            out=np.zeros_like(marginal),
            where=total[:, 0, :] > 0,
        )
        self.trace.append(
            {
                "signature": outputs.diagnostics["active_signature"],
                "counts": dict(outputs.diagnostics["active_counts"]),
                "anchor_gap": outputs.diagnostics.get("max_relative_anchor_gap"),
                "demand_adjustment": outputs.diagnostics.get("max_relative_demand_adjustment"),
                "delivered": delivered.tolist(),
                "marginal": self._anchor_price.tolist(),
                "energy_price": outputs.energy_price.tolist(),
                "compliance_price": outputs.compliance_price.tolist(),
                "demand": inputs.demand.tolist(),
            }
        )

    def _reconcile(self, inputs, outputs):
        """Put the volumes back on the budget the traffic model handed in.

        With an elastic balance the program clears at ``demand + a`` rather than at
        ``demand``. That is deliberate -- it is how the price gets pinned on a vertical
        stretch of supply -- but AeroMAPS's energy budget is set by the traffic model,
        not by this discipline, and everything downstream divides by it. So the MIX is
        taken from the market and the LEVEL from the budget.

        At a fixed point ``a`` is zero and the two agree exactly, so this rescale is
        visible only while the loop is still moving. ``max_relative_demand_adjustment``
        in the diagnostics is how much it is doing.
        """
        served = inputs.demand + outputs.demand_adjustment
        if not np.any(np.abs(outputs.demand_adjustment) > 0):
            return outputs
        ratio = np.divide(inputs.demand, served, out=np.ones_like(served), where=served > 0)
        return replace(
            outputs,
            volume=outputs.volume * ratio[:, None, :],
            unmet=outputs.unmet * ratio,
        )

    def compute(self, input_data) -> dict:
        """Clear the market, then emit it in EnergyUseChoice's vocabulary."""
        inputs, gross = self._build_inputs(input_data)
        outputs = clear_market(inputs)
        self._remember(inputs, outputs)
        outputs = self._reconcile(inputs, outputs)

        index = self.df.index
        prospective = slice(self.prospection_start_year, self.end_year)
        output_data = {}

        for r, region in enumerate(self.regions):
            budget = input_data[f"{region}:energy_consumption_{SUPPORTED_AIRCRAFT_TYPE}"]

            volumes = {}
            for p, pathway in enumerate(self.pathway_names):
                series = pd.Series(0.0, index=index)
                series.loc[prospective] = outputs.volume[r, p]
                # Historical years are given, not decided. The residual pathway carried
                # the whole budget before any obligation existed; every other pathway is
                # zero -- NOT NaN, which is what the current mode emits there and what
                # decision 9 rules out. See REPORT.md section 4.
                if pathway == self.residual_name:
                    series.loc[: self.last_historical_year] = budget.loc[
                        : self.last_historical_year
                    ].fillna(0.0)
                volumes[pathway] = series
                output_data[f"{region}:{pathway}_energy_consumption"] = series

                # Decide on net, report on gross: strip the same wedge that separates
                # net_mfsp from mean_mfsp, so DirectOperatingCosts adds the carbon tax
                # once rather than twice.
                price = pd.Series(np.nan, index=index)
                wedge = inputs.cost[r, p] - gross[r, p]
                price.loc[prospective] = outputs.market_mfsp[r, p] - wedge
                price.loc[: self.last_historical_year] = input_data[
                    f"{region}:{pathway}_mean_mfsp"
                ].loc[: self.last_historical_year]
                output_data[f"{region}:{pathway}_market_mfsp"] = price

            for name, values in (
                ("fuel_market_energy_price", outputs.energy_price[r]),
                ("fuel_market_compliance_price", outputs.compliance_price[r]),
                ("fuel_market_unmet_obligation", outputs.unmet[r]),
            ):
                series = pd.Series(0.0, index=index)
                series.loc[prospective] = values
                output_data[f"{region}:{name}"] = series

            # Same arithmetic EnergyUseChoice uses, from volumes the market solved for.
            derived = derive_share_families(
                volumes=volumes,
                total_energy_consumption=input_data[f"{region}:energy_consumption"],
                type_energy_consumption={SUPPORTED_AIRCRAFT_TYPE: budget},
                pathways_manager=self.pathways_manager,
                fallback_index=index,
            )
            for name, series in derived.items():
                output_data[f"{region}:{name}"] = series

        self._store_outputs(output_data)
        return output_data

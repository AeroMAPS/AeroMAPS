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
    "rampup_seed_share": 1.0,
    "rampup_form": "relative",
    "buyout_price": 1.0e3,
    "capacity": np.inf,
    "solver_tolerance": 1.0e-9,
}


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
        """Per-pathway override under ``pathways: {name: {...}}``, else the global value."""
        per_pathway = self.configuration_data.get("pathways", {}).get(pathway, {})
        if key in per_pathway:
            return per_pathway[key]
        return self.settings.get(key, default)

    def _prospective(self, series):
        return np.asarray(series.loc[self.prospection_start_year : self.end_year], dtype=float)

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
            ),
            gross,
        )

    def compute(self, input_data) -> dict:
        """Clear the market, then emit it in EnergyUseChoice's vocabulary."""
        inputs, gross = self._build_inputs(input_data)
        outputs = clear_market(inputs)

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

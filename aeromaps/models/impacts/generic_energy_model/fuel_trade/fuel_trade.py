"""Fuel flows between regions: who makes the fuel each region burns.

``FuelTrade`` is a **global** model, like ``FuelClearing``: not namespaced, its grammar
written directly in ``{region}:var`` terms, so it can read what every region offers or
consumes and write what every region produces and burns. It exists to test the
**plumbing** of inter-regional flows -- production uncoupled from consumption region by
region, each side reaching the models it belongs to, nothing lost on the way -- before a
market decides those flows.

**Two stand-ins for the market**, chosen by ``regionalisation.fuel_trade``:

``matrix``
    Each region's consumption is decided as before, by its own ``EnergyUseChoice``; a
    hand-written sourcing matrix says where it is made::

        sourcing:
          hefa_fog:
            region_B: {region_A: 1.0}          # all of B's HEFA is made in A
          fossil_kerosene:
            region_A: {region_A: 0.75, region_B: 0.25}

    A row must sum to one. A region or pathway not listed makes what it consumes.

``pool``
    Each region **offers** volumes of every non-default drop-in pathway
    (``{p}_energy_offered``, a regional input in MJ). A pathway's offers form one world
    pool, and every region burns a slice of every pool in proportion to its share of world
    drop-in demand -- so every region burns the world mix. The default pathway (fossil
    kerosene) fills what is left of each region's demand and is made where it is burnt.
    ``EnergyUseChoice`` is not instantiated: this model emits consumption and its share
    families itself, exactly as ``FuelClearing`` does, so the market can take its place
    without anything downstream noticing.

    If the world is offered more than it burns, nothing is scaled down: every offered MJ
    is used at the same rate, whatever its pathway or region, and the rest is reported as
    ``{p}_energy_unused``. Production is what is used, so feedstock never counts fuel
    nobody burns. (A market would leave the most expensive offers unused instead; ranking
    them is market logic, which this is a stand-in for.)

    An **eligibility** matrix can bar a region from burning a pathway at all::

        eligibility:
          hefa_fog: {region_A: false}      # A may not burn waste-oil HEFA, even its own

    Everything not listed is eligible, and fossil kerosene cannot be excluded: it closes
    every region's balance. Each pool is then shared among its eligible regions only, by
    demand share; a region handed more than it burns is capped at its demand and the
    excess goes back to the others, by demand share again, until nothing moves
    (``fill_pools``). What no eligible region can take is unused. With nothing excluded
    this is the rule above, exactly. Not to be confused with the market kernel's
    eligibility (``is_sustainable``), which says whether a fuel counts towards a mandate:
    this one says whether a region may burn it.

    Prospective years only. Historical years are data and describe no trade, and no
    eligibility rule: there each region burns what it offers, and fossil kerosene fills
    the rest.

**What it emits**, per region and pathway: ``{p}_energy_production`` and
``{p}_energy_net_export`` (production minus consumption, positive for an exporter); per
traded pathway and ordered pair of regions, ``{p}_energy_flow_{from}_to_{to}`` in the
global namespace; and the unit values of the fuel each region burns (below).

**Unit values** follow the fuel. A region that burns fuel made elsewhere pays the maker's
production cost -- MFSP, and the subsidies and taxes on its resources and processes -- and
books the maker's emission factor, each blended by origin; and it pays its **own** carbon
tax on that blended emission factor. Emitted as ``{p}_delivered_{value}``, read instead of
``{p}_{value}`` by ``EnergyCarriersMeans``, ``NonDiscountedScenarioCost`` and
``TopDownEnvironmental``'s CO2 total. With no trade the blend has one term, and each
delivered value is the region's own to the last bit.

**Who reads production.** With trade on, each region's ``TopDownEnvironmental`` computes
feedstock use from ``{p}_energy_production``: the waste oil is used where the HEFA is made.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.models.impacts.generic_energy_model.common.energy_use_choice import (
    derive_share_families,
)

MODES = ("matrix", "pool")

# The pool serves the drop-in budget only: hydrogen and electric aircraft have their own
# budgets, allocated by EnergyUseChoice, which the pool mode replaces.
POOL_AIRCRAFT_TYPE = "dropin_fuel"

# How far a row of shares may miss one before it is refused. Loose enough for shares
# typed as decimals, tight enough that a forgotten region is caught.
_SHARE_SUM_TOLERANCE = 1.0e-9

# Unit values that travel with the fuel, from the region that made it: TopDownCost and
# TopDownEnvironmental's own outputs, per MJ.
MAKER_VALUES = (
    "mean_co2_emission_factor",
    "mean_mfsp",
    "net_mfsp_without_carbon_tax",
    "mean_unit_subsidy",
    "mean_unit_tax",
)
# ... plus the two the burner adds: its carbon tax on the maker's emission factor, and
# the price that includes it. Same names as the regional families, with `delivered_`.
DELIVERED_VALUES = MAKER_VALUES + ("mean_unit_carbon_tax", "net_mfsp")


# The settings each mode reads; anything else is a typo that would silently do nothing.
SETTINGS = {"matrix": ("sourcing",), "pool": ("eligibility",)}


class FuelTradeConfigurationError(ValueError):
    """The trade settings cannot be applied to this scenario."""


def fill_pools(demand, pool, eligible):
    """What each region burns of each pool: shared by demand, capped at demand.

    Each pool goes to its eligible regions in proportion to their demand. A region handed
    more than its demand, all pools together, keeps a proportional slice of each that
    exactly fills it, and drops out; what it could not take goes back to the regions still
    eligible and not full, by demand share again. Repeat until nothing moves. Every round
    fills at least one region or places everything, so it ends within one round per region.

    With every region eligible for every pool it is the plain pro-rata split: all regions
    fill at the same rate, so either none is capped, or all are, at once, by the same
    factor -- a uniform use rate.

    Parameters
    ----------
    demand
        ``(C,)`` what each region burns in all, MJ.
    pool
        ``(K,)`` what is offered of each pathway, all makers together, MJ.
    eligible
        ``(C, K)`` whether region ``c`` may burn pathway ``k``.

    Returns
    -------
    burnt : ``(C, K)``, what each region burns of each pool.
    left : ``(K,)``, what no eligible region could take -- exactly zero where a pool was
        fully placed, so that a use rate of one is exactly one.
    """
    demand = np.asarray(demand, dtype=float)
    left = np.array(pool, dtype=float)
    burnt = np.zeros(eligible.shape)
    room = demand.copy()
    active = room > 0.0
    for _ in range(len(demand) + 1):
        takers = eligible & active[:, None]
        weight = takers * demand[:, None]
        total = weight.sum(axis=0)
        placed = total > 0.0
        offer = np.divide(weight, total, out=np.zeros_like(weight), where=placed) * left
        asked = offer.sum(axis=1)
        full = asked > room
        scale = np.divide(room, asked, out=np.ones_like(asked), where=full)
        take = offer * scale[:, None]
        burnt += take
        if not full.any():
            # Everything offered to someone was taken: those pools are empty.
            left[placed] = 0.0
            break
        left = np.maximum(left - take.sum(axis=0), 0.0)
        room = np.where(full, 0.0, room - take.sum(axis=1))
        active &= ~full
        if not (eligible & active[:, None]).any() or not left.any():
            break
    return burnt, left


class FuelTrade(AeroMAPSModel):
    """Who makes the fuel each region burns: an explicit matrix, or a pro-rata pool.

    Parameters
    ----------
    name
        Model instance name.
    configuration_data
        From ``regionalisation.global_models.settings.fuel_trade``. Matrix mode:
        ``{"sourcing": {pathway: {consumer: {producer: share}}}}``. Pool mode, optional:
        ``{"eligibility": {pathway: {region: false}}}``.

    Attributes
    ----------
    regions, global_namespace, pathways_manager
        Injected by ``MultiRegionalProcess._wrap_global_model`` before ``custom_setup``.
    mode
        ``"matrix"`` or ``"pool"``, injected by ``MultiRegionalProcess`` from
        ``regionalisation.fuel_trade``, which also tells every region how to wire itself.
    """

    def __init__(self, name="fuel_trade", configuration_data=None, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)

        # Injected before custom_setup(); the placeholders keep __init__ importable.
        self.regions = []
        self.global_namespace = "overall"
        self.pathways_manager = None
        self.mode = None

        self.configuration_data = configuration_data or {}
        self.pathway_names = []
        # Matrix mode: {pathway: (consumer, producer) array of shares}, traded pathways.
        self.sourcing = {}
        # Pool mode: the pooled pathways, the default one that closes each balance, and
        # (region, pooled pathway) eligibility.
        self.pooled_names = []
        self.residual_name = None
        self.eligible = None

        self.input_names = {}
        self.output_names = {}

    # -- setup ---------------------------------------------------------------

    def custom_setup(self):
        if not self.regions:
            raise FuelTradeConfigurationError(
                "FuelTrade.custom_setup() ran before the region list was injected. It "
                "must be declared under 'regionalisation.global_models'."
            )
        if self.pathways_manager is None:
            raise FuelTradeConfigurationError(
                "FuelTrade.custom_setup() ran without a pathways_manager. It is injected "
                "by MultiRegionalProcess._wrap_global_model."
            )
        if self.mode not in MODES:
            raise FuelTradeConfigurationError(
                f"FuelTrade needs a mode, one of {MODES}, from 'regionalisation.fuel_trade'"
                f"; got {self.mode!r}."
            )
        # Every pathway, traded or not: with trade on, every region's environmental model
        # reads production and every region's means read delivered values, so every
        # pathway needs both -- equal to the region's own where nothing is traded.
        self.pathway_names = sorted(p.name for p in self.pathways_manager.get_all())
        unknown = sorted(set(self.configuration_data) - set(SETTINGS[self.mode]))
        if unknown:
            raise FuelTradeConfigurationError(
                f"settings.fuel_trade has {unknown}, which the '{self.mode}' mode does not "
                f"read (it reads {list(SETTINGS[self.mode])}). A setting nobody reads would "
                "look exactly like one that did not take effect."
            )
        if self.mode == "matrix":
            self.sourcing = self._read_sourcing()
        else:
            self._collect_pool_pathways()
            self.eligible = self._read_eligibility()
        self._build_grammar()

    def _read_sourcing(self):
        """The matrix as ``{pathway: S}``, ``S[c, r]`` = share of c's consumption made in r."""
        declared = self.configuration_data.get("sourcing") or {}
        if not declared:
            raise FuelTradeConfigurationError(
                "FuelTrade has no 'sourcing' matrix, so it would trade nothing. Give one "
                "under regionalisation.global_models.settings.fuel_trade.sourcing, or "
                "leave fuel_trade off."
            )
        regions = list(self.regions)
        sourcing = {}
        for pathway, rows in declared.items():
            if pathway not in self.pathway_names:
                raise FuelTradeConfigurationError(
                    f"sourcing names pathway '{pathway}', which this scenario does not "
                    f"declare. Declared: {self.pathway_names}."
                )
            shares = np.eye(len(regions))
            for consumer, row in (rows or {}).items():
                if consumer not in regions:
                    raise FuelTradeConfigurationError(
                        f"sourcing.{pathway} has a row for region '{consumer}', which is "
                        f"not one of {regions}."
                    )
                c = regions.index(consumer)
                shares[c, :] = 0.0
                for producer, share in (row or {}).items():
                    if producer not in regions:
                        raise FuelTradeConfigurationError(
                            f"sourcing.{pathway}.{consumer} names producer '{producer}', "
                            f"which is not one of {regions}."
                        )
                    share = float(share)
                    if not 0.0 <= share <= 1.0:
                        raise FuelTradeConfigurationError(
                            f"sourcing.{pathway}.{consumer}.{producer} is {share}; a share "
                            "is a fraction in [0, 1], not a percentage."
                        )
                    shares[c, regions.index(producer)] = share
                total = shares[c].sum()
                if abs(total - 1.0) > _SHARE_SUM_TOLERANCE:
                    raise FuelTradeConfigurationError(
                        f"sourcing.{pathway}.{consumer} sums to {total:.12g}, not 1. Every "
                        "unit a region consumes is made somewhere, so its shares must "
                        "cover all of it -- including its own, if it makes some."
                    )
            sourcing[pathway] = shares
        return sourcing

    def _collect_pool_pathways(self):
        """Resolve the pool's roles, and refuse what the pool cannot serve."""
        unsupported = set(self.pathways_manager.get_all_types("aircraft_type")) - {
            POOL_AIRCRAFT_TYPE
        }
        if unsupported:
            raise FuelTradeConfigurationError(
                f"The pool serves '{POOL_AIRCRAFT_TYPE}' only, but this scenario declares "
                f"{sorted(unsupported)}. Those aircraft types are allocated by "
                "EnergyUseChoice, which the pool mode replaces, so they would silently "
                "receive no fuel at all."
            )
        pathways = self.pathways_manager.get(aircraft_type=POOL_AIRCRAFT_TYPE)
        residual = [p.name for p in pathways if p.default]
        if len(residual) != 1:
            raise FuelTradeConfigurationError(
                f"Exactly one default {POOL_AIRCRAFT_TYPE} pathway is required to fill "
                f"what the pool leaves of each region's demand; found {residual or 'none'}."
            )
        self.residual_name = residual[0]
        self.pooled_names = sorted(p.name for p in pathways if p.name != self.residual_name)
        if not self.pooled_names:
            raise FuelTradeConfigurationError(
                f"Only the default pathway '{self.residual_name}' is declared, so the "
                "pool has nothing to share."
            )

    def _read_eligibility(self):
        """``(regions, pooled pathways)`` booleans: may this region burn this pathway."""
        regions = list(self.regions)
        eligible = np.ones((len(regions), len(self.pooled_names)), dtype=bool)
        declared = self.configuration_data.get("eligibility") or {}
        for pathway, row in declared.items():
            if pathway == self.residual_name:
                if any(value is not True for value in (row or {}).values()):
                    raise FuelTradeConfigurationError(
                        f"eligibility excludes '{pathway}', the default pathway, which fills "
                        "whatever the pools leave of each region's demand. It cannot be "
                        "excluded anywhere."
                    )
                continue
            if pathway not in self.pooled_names:
                raise FuelTradeConfigurationError(
                    f"eligibility names pathway '{pathway}', which is not pooled here. "
                    f"Pooled: {self.pooled_names}."
                )
            for region, value in (row or {}).items():
                if region not in regions:
                    raise FuelTradeConfigurationError(
                        f"eligibility.{pathway} names region '{region}', which is not one "
                        f"of {regions}."
                    )
                if not isinstance(value, bool):
                    raise FuelTradeConfigurationError(
                        f"eligibility.{pathway}.{region} is {value!r}; it must be true or " "false."
                    )
                eligible[regions.index(region), self.pooled_names.index(pathway)] = value
        return eligible

    def _traded_names(self):
        return list(self.sourcing) if self.mode == "matrix" else list(self.pooled_names)

    def _build_grammar(self):
        self.input_names = {}
        self.output_names = {}
        for region in self.regions:
            self.input_names[f"{region}:carbon_tax"] = pd.Series([0.0])
            for pathway in self.pathway_names:
                for value in MAKER_VALUES:
                    self.input_names[f"{region}:{pathway}_{value}"] = pd.Series([0.0])
                for value in DELIVERED_VALUES:
                    self.output_names[f"{region}:{pathway}_delivered_{value}"] = pd.Series([0.0])
                self.output_names[f"{region}:{pathway}_energy_production"] = pd.Series([0.0])
                self.output_names[f"{region}:{pathway}_energy_net_export"] = pd.Series([0.0])

            if self.mode == "matrix":
                for pathway in self.pathway_names:
                    self.input_names[f"{region}:{pathway}_energy_consumption"] = pd.Series([0.0])
                continue

            self.input_names[f"{region}:energy_consumption_{POOL_AIRCRAFT_TYPE}"] = pd.Series([0.0])
            self.input_names[f"{region}:energy_consumption"] = pd.Series([0.0])
            for pathway in self.pooled_names:
                self.input_names[f"{region}:{pathway}_energy_offered"] = pd.Series([0.0])
                self.output_names[f"{region}:{pathway}_energy_unused"] = pd.Series([0.0])
            for pathway in self.pathway_names:
                self.output_names[f"{region}:{pathway}_energy_consumption"] = pd.Series([0.0])
            for name in self._derived_output_names():
                self.output_names[f"{region}:{name}"] = pd.Series([0.0])

        for name in self._flow_names():
            self.output_names[name] = pd.Series([0.0])
        if self.mode == "pool":
            self.output_names[f"{self.global_namespace}:fuel_pool_use_rate"] = pd.Series([0.0])
            for pathway in self.pooled_names:
                self.output_names[f"{self.global_namespace}:{pathway}_pool_use_rate"] = pd.Series(
                    [0.0]
                )

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

    def _flow_names(self):
        return [
            self._flow_name(pathway, producer, consumer)
            for pathway in self._traded_names()
            for producer in self.regions
            for consumer in self.regions
            if producer != consumer
        ]

    def _flow_name(self, pathway, producer, consumer):
        return f"{self.global_namespace}:{pathway}_energy_flow_{producer}_to_{consumer}"

    def _initialize_df(self):
        """Seed the coupled inputs, so the MDA has somewhere to start.

        Delivered values put this model inside the traffic loop in both modes -- they
        reach the airfare, which reaches demand, which comes back as the consumption (or
        the demand) read here -- and next to TopDownEnvironmental, whose emission factor
        it blends and whose CO2 total it then feeds. GEMSEO orders a coupled component
        from a discipline whose inputs are all available; these seeds are that. One
        sweep replaces them, so they only have to be sane: a zero demand would make the
        first pool split 0/0.
        """
        super()._initialize_df()
        regions = getattr(self, "regions", [])
        if not regions or getattr(self, "mode", None) not in MODES:
            return
        index = self.df.index
        demand_seed = pd.Series(1.0e13, index=index)
        defaults = {}
        for region in regions:
            defaults[f"{region}:carbon_tax"] = pd.Series(0.0, index=index)
            for pathway in self.pathway_names:
                for value in MAKER_VALUES:
                    defaults[f"{region}:{pathway}_{value}"] = pd.Series(0.02, index=index)
                if self.mode == "matrix":
                    defaults[f"{region}:{pathway}_energy_consumption"] = demand_seed.copy()
            if self.mode == "pool":
                defaults[f"{region}:energy_consumption_{POOL_AIRCRAFT_TYPE}"] = demand_seed.copy()
                defaults[f"{region}:energy_consumption"] = demand_seed.copy()
        self._coupling_defaults = defaults

    # -- compute -------------------------------------------------------------

    def compute(self, input_data) -> dict:
        if self.mode == "matrix":
            consumption, flows = self._matrix_flows(input_data)
            output_data = {}
        else:
            consumption, flows, output_data = self._pool_flows(input_data)

        regions = list(self.regions)
        prospective = slice(self.prospection_start_year, self.end_year)

        for pathway in self.pathway_names:
            for r, region in enumerate(regions):
                if pathway in flows:
                    production = sum(flows[pathway][r][c] for c in range(len(regions)))
                    if self.mode == "matrix":
                        # Consumption as it came, NaN included, outside the prospective
                        # years: there nothing is traded, and the environmental model
                        # must see exactly what it saw before trade existed.
                        made = consumption[pathway][r].copy()
                        made.loc[prospective] = production.loc[prospective]
                        production = made
                else:
                    production = consumption[pathway][r].copy()
                output_data[f"{region}:{pathway}_energy_production"] = production
                output_data[f"{region}:{pathway}_energy_net_export"] = production.fillna(
                    0.0
                ) - consumption[pathway][r].fillna(0.0)

            if pathway not in flows:
                continue
            for p, producer in enumerate(regions):
                for c, consumer in enumerate(regions):
                    if producer != consumer:
                        output_data[self._flow_name(pathway, producer, consumer)] = flows[pathway][
                            p
                        ][c]

        output_data.update(self._delivered_values(input_data, consumption, flows))

        self._store_outputs(output_data)
        return output_data

    def _matrix_flows(self, input_data):
        """Consumption as the regions decided it; flows as the matrix says, prospectively."""
        regions = list(self.regions)
        prospective = slice(self.prospection_start_year, self.end_year)
        consumption = {
            pathway: [input_data[f"{region}:{pathway}_energy_consumption"] for region in regions]
            for pathway in self.pathway_names
        }
        flows = {}
        for pathway, shares in self.sourcing.items():
            flows[pathway] = [[None] * len(regions) for _ in regions]
            for c in range(len(regions)):
                burnt = consumption[pathway][c].fillna(0.0)
                for p in range(len(regions)):
                    flow = pd.Series(0.0, index=burnt.index)
                    flow.loc[prospective] = shares[c, p] * burnt.loc[prospective]
                    if p == c:
                        # What a region burns of its own making, in every year: all of
                        # it before the prospective years, its own share after.
                        flow.loc[: self.last_historical_year] = burnt.loc[
                            : self.last_historical_year
                        ]
                    flows[pathway][p][c] = flow
        return consumption, flows

    def _pool_flows(self, input_data):
        """Split every pooled pathway by demand share; fill the rest with the residual."""
        regions = list(self.regions)
        index = self.df.index
        prospective = (index >= self.prospection_start_year) & (index <= self.end_year)
        n = len(regions)

        demand = np.array(
            [
                input_data[f"{region}:energy_consumption_{POOL_AIRCRAFT_TYPE}"]
                .reindex(index)
                .fillna(0.0)
                .to_numpy(dtype=float)
                for region in regions
            ]
        )
        # offered[k, r, t]: pooled pathway k, producer r. A NaN offer is no offer -- the
        # interpolators leave the historical years undefined.
        offered = np.array(
            [
                [
                    input_data[f"{region}:{pathway}_energy_offered"]
                    .reindex(index)
                    .fillna(0.0)
                    .to_numpy(dtype=float)
                    for region in regions
                ]
                for pathway in self.pooled_names
            ]
        )
        if np.any(offered < 0.0):
            k, r, t = np.argwhere(offered < 0.0)[0]
            raise ValueError(
                f"{regions[r]}:{self.pooled_names[k]}_energy_offered is negative "
                f"({offered[k, r, t]:.4g} MJ in {index[t]}); an offer is a volume."
            )

        # Who shares a pool with whom: the whole world in prospective years, under the
        # eligibility matrix; each region alone before them, with no rule at all (the
        # historical years are data, and describe no trade).
        # burnt[k, c, t]: what c burns of pathway k; flow[k, r, c, t]: of it, made in r;
        # rate[k, t]: the share of pathway k's offers that is used, per pool.
        n_pooled = len(self.pooled_names)
        burnt = np.zeros((n_pooled, n, len(index)))
        flow = np.zeros((n_pooled, n, n, len(index)))
        rate = np.ones((n_pooled, n, len(index)))
        everyone = np.ones((1, n_pooled), dtype=bool)
        for t in range(len(index)):
            groups = [list(range(n))] if prospective[t] else [[c] for c in range(n)]
            for group in groups:
                offers = offered[:, group, t]  # (K, producers in the group)
                pool = offers.sum(axis=1)
                eligible = self.eligible[group] if prospective[t] else everyone
                taken, left = fill_pools(demand[group, t], pool, eligible)
                used = np.divide(pool - left, pool, out=np.ones_like(pool), where=pool > 0.0)
                # Each pathway's makers supply its burners pro rata to their offers, so
                # every maker of a pathway sees the same use rate.
                share = np.divide(
                    offers, pool[:, None], out=np.zeros_like(offers), where=pool[:, None] > 0
                )
                for j, c in enumerate(group):
                    burnt[:, c, t] = taken[j]
                    for i, r in enumerate(group):
                        flow[:, r, c, t] = taken[j] * share[:, i]
                rate[:, group, t] = used[:, None]

        output_data = {}
        consumption = {}
        flows = {}
        for k, pathway in enumerate(self.pooled_names):
            flows[pathway] = [
                [pd.Series(flow[k, r, c], index=index) for c in range(n)] for r in range(n)
            ]
            consumption[pathway] = [pd.Series(burnt[k, c], index=index) for c in range(n)]
            for r, region in enumerate(regions):
                output_data[f"{region}:{pathway}_energy_unused"] = pd.Series(
                    offered[k, r] - offered[k, r] * rate[k, r], index=index
                )
            output_data[f"{self.global_namespace}:{pathway}_pool_use_rate"] = pd.Series(
                np.where(prospective, rate[k, 0], np.nan), index=index
            )

        # The residual fills each region's demand, made where it is burnt. `fill_pools`
        # caps every region at its demand, so the difference is never negative beyond
        # rounding -- which is all the clip removes.
        pooled_burnt = sum(
            np.array([series.to_numpy() for series in consumption[pathway]])
            for pathway in self.pooled_names
        )
        residual = np.maximum(demand - pooled_burnt, 0.0)
        consumption[self.residual_name] = [pd.Series(residual[c], index=index) for c in range(n)]

        # All pathways together: the share of everything offered that is used.
        total_offered = offered.sum(axis=(0, 1))
        total_used = (offered * rate).sum(axis=(0, 1))
        world_rate = np.divide(
            total_used, total_offered, out=np.ones_like(total_offered), where=total_offered > 0
        )
        output_data[f"{self.global_namespace}:fuel_pool_use_rate"] = pd.Series(
            np.where(prospective, world_rate, np.nan), index=index
        )
        # No warning here: this runs on every MDA sweep, and an early sweep's demand is
        # not the converged one -- a warning from it names the wrong years. The process
        # warns once, from the converged use rate (MultiRegionalProcess._warn_unused_fuel).

        for c, region in enumerate(regions):
            volumes = {pathway: consumption[pathway][c] for pathway in self.pathway_names}
            for pathway, series in volumes.items():
                output_data[f"{region}:{pathway}_energy_consumption"] = series
            derived = derive_share_families(
                volumes=volumes,
                total_energy_consumption=input_data[f"{region}:energy_consumption"],
                type_energy_consumption={
                    POOL_AIRCRAFT_TYPE: input_data[
                        f"{region}:energy_consumption_{POOL_AIRCRAFT_TYPE}"
                    ]
                },
                pathways_manager=self.pathways_manager,
                fallback_index=index,
            )
            for name, series in derived.items():
                # In prospective years every volume above is a finite number, so a NaN
                # share there can only be 0/0 -- a share of nothing -- and it is emitted
                # as 0. Which years hold nothing is decided by the iterate (fossil
                # kerosene drops to zero once offers exceed demand), and a coupling whose
                # NaN pattern moves between sweeps is what the MDA's NaN guard refuses.
                # EnergyUseChoice's NaN is kept in the historical years, which are data.
                if "_share_" in name:
                    series = series.copy()
                    series.loc[prospective] = series.loc[prospective].fillna(0.0)
                output_data[f"{region}:{name}"] = series

        return consumption, flows, output_data

    def _delivered_values(self, input_data, consumption, flows):
        """The unit values of what each region burns: the makers', blended by origin."""
        regions = list(self.regions)
        output_data = {}
        for pathway in self.pathway_names:
            for c, consumer in enumerate(regions):
                # origin[r]: share of c's consumption of this pathway made in r. Where c
                # burns none, or nothing is traded, the region's own values stand alone.
                if pathway in flows:
                    inflow = [flows[pathway][r][c].fillna(0.0) for r in range(len(regions))]
                    total = sum(inflow)
                    burns = total > 0.0
                    origin = [
                        (inflow[r] / total.where(burns)).where(burns, 1.0 if r == c else 0.0)
                        for r in range(len(regions))
                    ]
                else:
                    ones = pd.Series(1.0, index=consumption[pathway][c].index)
                    origin = [ones if r == c else ones * 0.0 for r in range(len(regions))]

                delivered = {}
                for value in MAKER_VALUES:
                    # A region that contributes nothing contributes nothing, even where
                    # its own value is undefined; one that contributes an undefined value
                    # makes the blend undefined.
                    delivered[value] = sum(
                        (input_data[f"{producer}:{pathway}_{value}"] * origin[r]).where(
                            origin[r] > 0.0, 0.0
                        )
                        for r, producer in enumerate(regions)
                    )
                # TopDownCost's own arithmetic, with the burner's tax on the maker's
                # emission factor: EUR/t -> EUR/kg, and gCO2/MJ -> kgCO2/MJ.
                # Bracketed as TopDownCost brackets it, so that with no trade the result
                # is the region's own to the last bit.
                delivered["mean_unit_carbon_tax"] = (
                    input_data[f"{consumer}:carbon_tax"] / 1000
                ) * (delivered["mean_co2_emission_factor"] / 1000)
                delivered["net_mfsp"] = delivered["net_mfsp_without_carbon_tax"].add(
                    delivered["mean_unit_carbon_tax"], fill_value=0
                )
                for value in DELIVERED_VALUES:
                    output_data[f"{consumer}:{pathway}_delivered_{value}"] = delivered[value]
        return output_data

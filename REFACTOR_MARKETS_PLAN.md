# AeroMAPS — User-Defined Markets Refactor Plan

**Status:** Draft for review  |  **Author:** A. Salgas (with Claude)  |  **Updated:** 2026-04-09

---

## 1. Goal

Replace the hard-coded 4-market structure (`short_range`, `medium_range`, `long_range`, `freight`) with **user-defined markets declared in YAML**, following the energy carriers pattern. The fleet-to-market binding becomes explicit and **many-to-many from day one**.

## 2. Non-goals

- **Belly freight** — out of scope, but `host_market` + `belly_share` reserved in schema.
- **Plots / GUI rework** — deferred to after core refactor lands.
- **Multi-regional changes** — markets are intra-region; orthogonal to multi-regional.
- **LCA / climate models** — assumed to consume aggregated quantities only.

## 3. Target architecture

### 3.1 `markets.yaml` schema

```yaml
# aeromaps/resources/data/default_markets/markets.yaml
short_range:
  name: "Short Range"
  traffic_type: passenger          # passenger | freight
  traffic_unit: RPK                # RPK | RTK
  inputs:
    initial:
      rpk_share_2019: 27.2
      energy_share_2019: 26.01
    growth:
      cagr_reference_periods: []
      cagr_reference_periods_values: [3.0]
    covid:
      drop_start_year: 66.0
      end_year: 2024
      end_year_reference_ratio: 100.0
    measures:
      final_impact: 0.0
      start_year: 2051
      duration: 5.0
    efficiency_simple:   # only used by top-down model
      energy_per_ask_dropin_fuel_gain_reference_years: []
      energy_per_ask_dropin_fuel_gain_reference_years_values: [2.0]
      hydrogen_final_market_share: 0.0
      hydrogen_introduction_year: 2051
      # ... electric equivalents
```

Default file ships 4 markets reproducing today's numerics exactly. Sub-keys under `inputs` are flattened on load with `<key>_<market_id>` naming and pushed to `self.parameters` (same pattern as `_instantiate_generic_energy_models()` at [process.py:1048](aeromaps/core/process.py#L1048)).

### 3.2 `Market` and `MarketRegistry`

New module `aeromaps/models/air_transport/markets/`:

- **`Market`** dataclass: id, name, traffic_type, traffic_unit, flattened inputs.
- **`MarketRegistry`** (analogous to `EnergyCarrierManager`): `get_all()`, `get(traffic_type=...)`, `get_ids()`, etc.

Built once in `AeroMAPSProcess._initialize_markets()`, stored as `self.markets`.

### 3.3 Fleet-to-market binding (many-to-many)

The binding is declared in `fleet.yaml` and supports **many-to-many from day one**: one fleet category can serve multiple markets with declared shares.

```yaml
categories:
  - id: short_range_cat
    name: "Short Range"
    serves_markets:                     # many-to-many
      - market: short_range
        share: 100                      # % of this category's capacity
    parameters:
      life: 25
      limit: 2
    subcategories:
      - sr_conventional_nb
      - sr_hydrogen_nb

  - id: widebody_cat
    name: "Widebody"
    serves_markets:                     # example: one category, two markets
      - market: medium_range
        share: 40
      - market: long_range
        share: 60
```

**Default config:** each category has a single market at 100% share, reproducing today's 1:1 mapping. The many-to-many mechanism is available immediately for advanced users.

**Validation at load time:**
- Every passenger market must be served by at least one category (when bottom-up fleet model is active).
- Shares per category must sum to 100%.
- Freight markets handled by the freight efficiency model, not bound to fleet categories in this iteration.

A `FleetMarketBinding` resolver reads the binding, exposes lookups like `get_categories_for_market(market_id)` and `get_markets_for_category(category_id)`.

### 3.4 Variable naming

Underscore concatenation (unchanged from today):

| Concept | Template | Example |
|---------|----------|---------|
| Traffic | `rpk_<market>` / `rtk_<market>` | `rpk_short_range` |
| ASK | `ask_<market>` | `ask_medium_range` |
| Energy/ASK | `energy_per_ask_<market>_<carrier>` | `energy_per_ask_long_range_dropin_fuel` |
| CAGR | `cagr_<market>` | `cagr_freight` |

Default market ids = legacy names, so variable names are unchanged for default scenarios.

### 3.5 GEMSEO discipline strategy

**One discipline instance per market** (approach A), consistent with the energy carriers pattern. Each instance has a generic compute signature; GEMSEO grammars stay flat. Cost: N disciplines instead of 1, negligible overhead.

### 3.6 Downstream model I/O: `AeroMAPSCustomModelWrapper` pattern

A large part of the work is making **downstream models** (energy consumption, costs, emissions, etc.) wire correctly to dynamic market-named variables. GEMSEO connects disciplines by matching I/O names, so every downstream model must declare inputs/outputs that include market ids.

**The pattern to follow is `NOxEmissionIndexComplex`** ([non_co2_emissions.py:157](aeromaps/models/impacts/emissions/non_co2_emissions.py#L157)):

1. The model inherits from `AeroMAPSModel` with `model_type="custom"`.
2. It implements a **`custom_setup()`** method that dynamically builds `self.input_names` and `self.output_names` dicts based on runtime information (the `MarketRegistry` here, the `EnergyCarrierManager` in the existing example).
3. It is wrapped with **`AeroMAPSCustomModelWrapper`** ([gemseo.py:200](aeromaps/core/gemseo.py#L200)) instead of `AeroMAPSAutoModelWrapper`. The custom wrapper reads `input_names`/`output_names` to build GEMSEO grammars, rather than introspecting the `compute()` signature.
4. `compute()` receives an `input_data` dict and returns an `output_data` dict — no typed signature, fully dynamic.

**Applied to the market refactor:** every model that today has hard-coded `ask_short_range_dropin_fuel`, `ask_medium_range_hydrogen`, etc. in its signature will instead:
- Receive the `MarketRegistry` at `__init__`
- Build `input_names`/`output_names` in `custom_setup()` by iterating over `self.markets.get_all()` and templating variable names
- Use `AeroMAPSCustomModelWrapper` for GEMSEO integration

This is the **same migration done for the generic energy models**, now applied to the market dimension. Models affected: `DropInFuelConsumption`, `PassengerAircraftDocNonEnergyComplex`, `NOxEmissionIndexComplex` itself (adding market dimension), and all other downstream models listed in section 5.

## 4. Fleet model interaction

All fleet renewal models (existing `FleetModel`, `PassengerAircraftEfficiencySimpleShares`, and colleague's new model) must publish outputs under templated market names: `energy_per_ask_<market>_<carrier>`, `ask_<market>_<carrier>_share`, etc.

The many-to-many binding means the fleet model must:
- For each category, distribute its outputs across bound markets according to declared shares.
- The calibration loop at [fleet_model.py:863-1027](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py#L863-L1027) becomes a generic loop over `(category, [(market, share)])` pairs.

Contract enforced by GEMSEO grammar matching at MDA build time (no Python ABC needed).

## 5. File-by-file impact

### New files

| Path | Purpose |
|------|---------|
| `aeromaps/resources/data/default_markets/markets.yaml` | Default 4-market definition |
| `aeromaps/models/air_transport/markets/market.py` | `Market` dataclass |
| `aeromaps/models/air_transport/markets/market_registry.py` | `MarketRegistry`, YAML loader, validation |
| `aeromaps/models/air_transport/markets/binding.py` | `FleetMarketBinding` resolver |

### Refactored files

| File | Change | Phase |
|------|--------|-------|
| [process.py](aeromaps/core/process.py) | Add `_initialize_markets()`, instantiate per-market disciplines, push templated params | 1 |
| [models.py](aeromaps/core/models.py) | Replace static model dicts with builders taking `MarketRegistry` | 2 |
| [config.yaml](aeromaps/resources/data/config.yaml) | Add `models.markets.markets_data_file` | 1 |
| [fleet.yaml](aeromaps/resources/data/default_fleet/fleet.yaml) | Add `serves_markets` field on each category | 3 |
| [rpk.py](aeromaps/models/air_transport/air_traffic/rpk.py) | Per-market instances replacing 3-way loops (lines 144-220) | 2 |
| [rtk.py](aeromaps/models/air_transport/air_traffic/rtk.py) | Unify with RPK (same math, different unit) or keep separate | 2 |
| [ask.py](aeromaps/models/air_transport/air_traffic/ask.py) | Iterate over registry's passenger markets | 2 |
| [fleet_model.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py) | Generic calibration loop over `(category, markets)` pairs; many-to-many distribution | 3 |
| [aircraft_efficiency.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py) | Per-market disciplines + custom wrapper pattern | 3 |
| [energy_consumption.py](aeromaps/models/impacts/energy_resources/energy_consumption.py) | Custom wrapper with dynamic I/O from registry (~40 hard-coded args removed) | 4 |
| [direct_operating_costs.py](aeromaps/models/impacts/costs/airlines/direct_operating_costs.py) | Same custom wrapper treatment | 4 |
| [non_co2_emissions.py](aeromaps/models/impacts/emissions/non_co2_emissions.py) | Add market dimension to existing custom setup | 4 |
| [co2_emissions.py](aeromaps/models/impacts/emissions/co2_emissions.py), [others.py](aeromaps/models/impacts/others/others.py) | Audit and migrate | 4 |
| [parameters.json](aeromaps/resources/data/parameters.json) | Remove ~40 per-market entries (moved to markets.yaml) | 5 |
| Tutorial notebooks + JSON | Migrate per-market entries, re-run | 5 |

### Deferred

- `aeromaps/plots/*` and `aeromaps/gui/*` — Phase 6.

## 6. Phased work plan

Each phase ends with notebooks passing before moving on.

### Phase 0 — Data model & registry

- Define `markets.yaml` schema, implement `Market` and `MarketRegistry`.
- Implement `FleetMarketBinding` with many-to-many support.
- Unit test loader against default 4-market file.
- **Exit:** `MarketRegistry.from_yaml()` + `FleetMarketBinding` match today's constants.

### Phase 1 — Process integration

- Add `markets_data_file` to config, `_initialize_markets()` in process.py.
- Push flattened market params to `self.parameters`.
- Both `parameters.json` and `markets.yaml` work; YAML takes precedence.
- Audit LCA/climate for per-market dependencies.
- **Spike:** prototype one discipline with `AeroMAPSCustomModelWrapper` to confirm dynamic grammar generation works with the market registry.
- **Exit:** notebooks pass unchanged.

### Phase 2 — Air traffic disciplines

- `RPK`, `RPKReference`, `RPKMeasures` become per-market instances with custom wrapper.
- `RTK` unified or kept separate (same math, different unit — decide here).
- `ASK` iterates over passenger markets.
- Aggregator discipline sums totals.
- Update `models.py` builders.
- **Exit:** traffic fully driven by registry; legacy traffic code deleted.

### Phase 3 — Fleet binding & fleet model

- `serves_markets` in fleet.yaml with many-to-many support.
- `_build_fleet_from_yaml()` reads binding.
- Calibration blocks become generic `(category, markets)` loop with share distribution.
- Coordinate with colleague's new fleet model on output naming.
- **Exit:** fleet model emits outputs under market ids with proper share allocation.

### Phase 4 — Downstream impacts (custom wrapper migration)

This is the bulk of the line-count work. Each model follows the `NOxEmissionIndexComplex` pattern:

1. Add `MarketRegistry` to `__init__`.
2. Implement `custom_setup()` building `input_names`/`output_names` from registry.
3. Switch to `AeroMAPSCustomModelWrapper`.
4. Refactor `compute()` to use `input_data` dict.

**Models to migrate:**
- `DropInFuelConsumption` (~630 hard-coded refs)
- `PassengerAircraftDocNonEnergyComplex` (~1150 refs)
- `TotalAirlineCostAndAirfare` (~170 refs)
- `NOxEmissionIndexComplex` (add market dimension to existing custom setup)
- `CO2Emissions`, `EmissionsPerRPK/RTK`, abatement costs — audit and migrate.

**Exit:** zero hard-coded `short_range`/`medium_range`/`long_range`/`freight` in model code.

### Phase 5 — Migration & cleanup

- Remove per-market entries from `parameters.json`.
- Update `data_information.csv`.
- Migrate tutorial notebooks.
- New tutorial: "Defining your own markets".
- **Exit:** test suite green, single source of truth.

### Phase 6 — Plots & GUI (follow-up)

- Generic market plotting.
- GUI pinned to default layout or updated (decision deferred).

## 7. Risks

| # | Risk | Mitigation |
|---|------|------------|
| 1 | GEMSEO dynamic grammar with custom wrapper | Phase 1 spike: prototype one discipline end-to-end |
| 2 | Numerical drift during refactor | Set tolerance in test suite or accept output-update commit |
| 3 | Fleet output key rename cascade | Atomic rename in phase 3 or alias layer — pick based on diff size |
| 4 | Coordination with colleague's fleet model | Land phase 3 binding early, communicate naming convention |
| 5 | Many-to-many complexity in calibration | Default config is 1:1 at 100% share — complex cases tested incrementally |
| 6 | `data_information.csv` consumed by GUI | Verify before removing rows in phase 5 |

## 8. Migration strategy

**Hard cut, no transition shim.** Safe because:
1. Default `markets.yaml` = exact legacy structure.
2. Variable names unchanged for default markets.
3. Notebook test suite is the safety net.

User upgrade path: default scenarios need no action; custom scenarios move market params from `parameters.json` to a custom `markets.yaml`.

## 9. Decision log

| Decision | Rationale |
|----------|-----------|
| Hard cut, no shim | Clean; small user community |
| Underscore naming | Consistency with current codebase |
| No factory for markets | All markets same shape |
| No ABC for fleet models | GEMSEO grammar matching suffices |
| Many-to-many from day one | Avoids costly retrofit; default is 1:1 |
| `AeroMAPSCustomModelWrapper` for downstream | Proven pattern (NOxEmissionIndexComplex); only viable approach for dynamic I/O names |
| One discipline per market | Consistent with energy carriers pattern |
| `serves_markets` in fleet.yaml | Fleet knows its markets; markets shouldn't enumerate fleet categories |
| Belly freight out of scope | Adds market-to-market coupling; follow-up once basic refactor stable |

# AeroMAPS — User-Defined Markets Refactor Plan

**Status:** Draft for review  |  **Author:** A. Salgas (with Claude)  |  **Updated:** 2026-04-10

---

## 1. Goal

Replace the hard-coded 4-market structure (`short_range`, `medium_range`, `long_range`, `freight`) with **user-defined markets declared in YAML**, following the energy carriers pattern. The market replaces the fleet category as the top-level grouping concept. Subcategories and aircraft remain fleet-internal concerns, not propagated to downstream models.

## 2. Non-goals

- **Belly freight** — out of scope, but `host_market` + `belly_share` reserved in schema.
- **Plots / GUI rework** — deferred to after core refactor lands.
- **Multi-regional changes** — markets are intra-region; orthogonal to multi-regional.
- **LCA / climate models** — assumed to consume aggregated quantities only.

## 3. Target architecture

### 3.1 Core concept: market replaces category

Today's hierarchy is:

```
Category (Short Range, Medium Range, Long Range)   ← hard-coded in Python
 └── SubCategory
      └── Aircraft
```

The target hierarchy is:

```
Market (from markets.yaml)   ← user-defined, replaces Category
 └── SubCategory             ← fleet-internal, manages within-market share evolution
      └── Aircraft           ← same aircraft can appear in multiple markets' inventories
```

Key properties:
- **Market = Category.** There is no separate "category" concept. The market *is* the top-level fleet grouping. Fleet parameters (lifetime, S-curve limit) attach to the market in `fleet.yaml`.
- **Subcategories stay fleet-internal.** They manage share evolution within a market (e.g. "conventional narrow-body" vs "hydrogen narrow-body" within `short_range`) but downstream models only see market-level aggregates.
- **Aircraft serving multiple markets** are simply listed in the inventory of each market they serve (possibly with different parameters like ASK/year). No share-splitting or binding resolver needed.

### 3.2 `markets.yaml` schema

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

### 3.3 `Market` and `MarketRegistry`

New module `aeromaps/models/air_transport/markets/`:

- **`Market`** dataclass: id, name, traffic_type, traffic_unit, flattened inputs.
- **`MarketRegistry`** (analogous to `EnergyCarrierManager`): `get_all()`, `get(traffic_type=...)`, `get_ids()`, etc.

Built once in `AeroMAPSProcess._initialize_markets()`, stored as `self.markets`.

### 3.4 `fleet.yaml` — fleet structure per market

`fleet.yaml` declares the fleet structure under each market. Subcategories and aircraft assignments remain here — they are fleet-internal concerns.

```yaml
# aeromaps/resources/data/default_fleet/fleet.yaml
markets:
  - market: short_range
    parameters:
      life: 25
      limit: 2
    subcategories:
      - sr_conventional_nb
      - sr_hydrogen_nb

  - market: medium_range
    parameters:
      life: 25
      limit: 2
    subcategories:
      - mr_conventional_nb

  - market: long_range
    parameters:
      life: 30
      limit: 2
    subcategories:
      - lr_conventional_wb

subcategories:
  - id: sr_conventional_nb
    name: "SR conventional narrow-body"
    share: 80
    reference_aircraft:
      old_ref: sr_old_reference
      recent_ref: sr_recent_reference
    aircraft:
      - sr_next_gen_narrowbody

  - id: sr_hydrogen_nb
    name: "SR hydrogen narrow-body"
    share: 20
    reference_aircraft:
      old_ref: sr_old_reference
      recent_ref: sr_recent_reference
    aircraft:
      - sr_hydrogen_aircraft

  # ... other subcategories
```

**Validation at load time:**
- Every passenger market in the `MarketRegistry` must have a corresponding entry in `fleet.yaml` (when bottom-up fleet model is active).
- Subcategory shares within each market must sum to 100%.
- Freight markets are handled by the freight efficiency model, not present in `fleet.yaml`.

**Aircraft in multiple markets:** An aircraft that serves both short and medium range (e.g. a versatile narrow-body) is simply referenced in the subcategory inventories of both markets, potentially with different parameters in `aircraft_inventory.yaml` (different ASK/year, different performance deltas, etc.).

### 3.5 Variable naming

Underscore concatenation (unchanged from today):

| Concept | Template | Example |
|---------|----------|---------|
| Traffic | `rpk_<market>` / `rtk_<market>` | `rpk_short_range` |
| ASK | `ask_<market>` | `ask_medium_range` |
| Energy/ASK | `energy_per_ask_<market>_<carrier>` | `energy_per_ask_long_range_dropin_fuel` |
| CAGR | `cagr_<market>` | `cagr_freight` |

Default market ids = legacy names, so variable names are unchanged for default scenarios.

### 3.6 GEMSEO discipline strategy

**One discipline instance per market** (approach A), consistent with the energy carriers pattern. Each instance has a generic compute signature; GEMSEO grammars stay flat. Cost: N disciplines instead of 1, negligible overhead.

### 3.7 Downstream model I/O: `AeroMAPSCustomModelWrapper` pattern

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

Since the market *is* the fleet category, the fleet model simply:
- Iterates over markets from the `MarketRegistry`.
- Runs its S-curve assignment + performance computation independently per market.
- Publishes market-level aggregates under market-templated names (subcategory details remain internal to `self.df`).
- The calibration loop at [fleet_model.py:869-1023](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py#L869-L1023) becomes a generic loop over markets, with calibration parameters sourced from `MarketRegistry`.

Contract enforced by GEMSEO grammar matching at MDA build time (no Python ABC needed).

### 4.1 Fleet model prep work — synergies with internal clean-up

The colleague's recently updated fleet model ([fleet_model.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py), [fleet_assignment.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_assignment.py), [fleet_performance.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_performance.py), [fleet_numeric.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_numeric.py)) has several internal patterns that, if cleaned up first, significantly reduce the complexity of the market integration in Phase 3. These are standalone refactors that can land immediately — each one shrinks the Phase 3 diff and lowers its risk.

#### Prep A — Generic calibration loop *(direct prep for Phase 3)*

**Current state:** `_calibrate_reference_aircraft` ([fleet_model.py:869-1023](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py#L869-L1023)) repeats the same 50-line block three times for Short Range, Medium Range, and Long Range, with hardcoded subcategory names like `"SR conventional narrow-body"`.

**Refactor:** Extract into a single loop over a config list:
```python
CALIBRATION_CONFIG = [
    ("Short Range", "SR conventional narrow-body",
     "short_range_energy_share_2019", "short_range_rpk_share_2019"),
    ...
]
```

**Link to market plan:** This is a strict subset of Phase 3. In the final market-integrated form, the config list is replaced by `MarketRegistry` iteration and calibration parameters come from each market's flattened inputs. Doing this prep step means Phase 3 only needs to swap the config source — the loop structure is already correct.

**Effort:** Low | **Risk:** Low | **~95 lines saved**

#### Prep B — Data-driven energy type handling + subcategory-level semantics fix *(prep for Phase 4)*

**Current state:** [fleet_performance.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_performance.py) has repeated `if energy_type == "DROP_IN_FUEL"` / `elif "HYDROGEN"` / `elif "ELECTRIC"` / `elif "HYBRID_ELECTRIC"` blocks in `_compute_energy_consumption_and_share_wrt_energy_type`, `_compute_doc_non_energy`, and `_compute_non_co2_emission_index` (6+ methods total). Adding a new energy type requires touching all of them.

Additionally, all three methods have a **subcategory-level semantics bug**: per-energy-type values (e.g. `doc_non_energy:dropin_fuel`, `energy_consumption:hydrogen`, `emission_index_nox:dropin_fuel`) are stored as share-weighted contributions (`metric_i * aircraft_share / 100`) rather than proper means per energy type. The category-level means come out correct because `_compute_mean_*` methods divide by `share:<energy_type> / 100`, compensating for the weighting. But the subcategory-level values are not directly interpretable as means and would be misleading if read in isolation (e.g. in notebooks or plots).

Note on hybrid-electric: the `hybridization_factor` split only applies to energy consumption (physical energy split between fuel and electricity). For DOC and non-CO2 emissions, hybrid-electric is treated as its own category — DOC is a single operating cost, and NOx/soot come from the combustion side. No hybridization split for these metrics.

**Refactor:** Define `ENERGY_TYPES = ["dropin_fuel", "hydrogen", "electric", "hybrid_electric"]` and loop. Ensure subcategory-level per-energy-type values are proper means (weighted by share within the energy type, not by total share). Apply the `hybridization_factor` split only where physically meaningful (energy consumption shares and energy consumption values).

**Link to market plan:** In Phase 4, downstream models like `DropInFuelConsumption` migrate to `AeroMAPSCustomModelWrapper` with dynamic I/O templated as `energy_per_ask_<market>_<carrier>`. If the fleet model already loops over energy types cleanly, the `custom_setup()` method just iterates `markets × energy_types` — two clean loops. Without this prep, Phase 4 models inherit the hardcoded branching and must refactor it during the wrapper migration, increasing that phase's scope.

**Effort:** Low-Medium | **Risk:** Medium (needs numerical regression test) | **~100 lines saved**

#### Prep C — Vectorize performance methods *(prep for Phase 3 output publishing)*

**Current state:** Several methods in [fleet_performance.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_performance.py) use row-by-row `for idx in self.df.index: self.df.at[idx, ...] += ...` loops, particularly `_compute_non_co2_emission_index` (lines 386-457), `_compute_mean_energy_consumption_per_category_wrt_energy_type` (lines 556-634), `_compute_mean_doc_non_energy` (lines 651-717), and `_compute_mean_non_co2_emission_index` (lines 737-851). Meanwhile, the assignment step and subcategory-level energy/DOC methods already use vectorized numpy with `temp_dict` patterns.

**Refactor:** Replace row-by-row loops with the vectorized `temp_dict` + `pd.DataFrame()` pattern already used elsewhere in the same file.

**Link to market plan:** Phase 3 adds a final step where the fleet model publishes market-level aggregates under market-templated names. With vectorized methods, extracting and renaming these aggregates is straightforward array work. With row-by-row loops, the publishing step would inherit the same verbose pattern.

**Effort:** Low | **Risk:** Low | **~200 lines saved**

#### Prep D — Unify N-subcategory branching *(optional)*

**Current state:** `_compute_single_aircraft_share` in [fleet_assignment.py:74-233](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_assignment.py#L74-L233) has three separate code paths for categories with 1, 2, or 3+ subcategories.

**Refactor:** Collapse into a single general algorithm that iterates subcategories from last to first, each aircraft's cumulative share = `offset + S_curve(...)`, where offset = 0 for the last subcategory and = oldest aircraft share of the next subcategory for earlier ones.

**Link to market plan:** As users define custom markets, the number and structure of subcategories per market may vary more than today's fixed 3 categories. A unified N-subcategory algorithm is more robust for arbitrary market definitions.

**Effort:** Medium-High | **Risk:** High (core S-curve stacking logic) | **~100 lines saved**

#### Prep summary

| Step | Effort | Risk | Lines saved | Link to market plan |
|------|--------|------|-------------|---------------------|
| Prep A — Calibration loop | Low | Low | ~95 | Direct subset of Phase 3 |
| Prep B — Energy type loop + subcat semantics | Low-Medium | Medium | ~100 | Simplifies Phase 4 `custom_setup()`; fixes subcategory-level values |
| Prep C — Vectorize perf. | Low | Low | ~200 | Cleaner Phase 3 output publishing |
| Prep D — Subcategory unify | Medium-High | High | ~100 | Robustness for arbitrary market definitions |

**Recommendation:** Prep A–C should be done before Phase 3. Prep D can be combined with Phase 3 or deferred if the risk is deemed too high.

## 5. File-by-file impact

### New files

| Path | Purpose |
|------|---------|
| `aeromaps/resources/data/default_markets/markets.yaml` | Default 4-market definition |
| `aeromaps/models/air_transport/markets/market.py` | `Market` dataclass |
| `aeromaps/models/air_transport/markets/market_registry.py` | `MarketRegistry`, YAML loader, validation |

### Refactored files

| File | Change | Phase |
|------|--------|-------|
| [fleet_model.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py) | Prep A: generic calibration loop (standalone) | Prep |
| [fleet_performance.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_performance.py) | Prep B: data-driven energy types; Prep C: vectorize performance methods | Prep |
| [fleet_assignment.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_assignment.py) | Prep D (optional): unify subcategory branching | Prep / 3 |
| [process.py](aeromaps/core/process.py) | Add `_initialize_markets()`, instantiate per-market disciplines, push templated params | 1 |
| [models.py](aeromaps/core/models.py) | Replace static model dicts with builders taking `MarketRegistry` | 2 |
| [config.yaml](aeromaps/resources/data/config.yaml) | Add `models.markets.markets_data_file` | 1 |
| [fleet.yaml](aeromaps/resources/data/default_fleet/fleet.yaml) | Replace `categories` with `markets` keying; subcategories and aircraft unchanged | 3 |
| [rpk.py](aeromaps/models/air_transport/air_traffic/rpk.py) | Per-market instances replacing 3-way loops (lines 144-220) | 2 |
| [rtk.py](aeromaps/models/air_transport/air_traffic/rtk.py) | Unify with RPK (same math, different unit) or keep separate | 2 |
| [ask.py](aeromaps/models/air_transport/air_traffic/ask.py) | Iterate over registry's passenger markets | 2 |
| [fleet_model.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py) | Phase 3: iterate over `MarketRegistry`; rename `Category` → market-driven; publish market-templated outputs | 3 |
| [fleet_numeric.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_numeric.py) | Replace hardcoded Short/Medium/Long Range dispatch with market iteration | 3 |
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

### Phase Prep — Fleet model clean-up

Standalone refactors on the fleet model that reduce Phase 3 complexity. Can be done immediately, independently of the market refactor infrastructure. Each step is verified by full DataFrame diff (before/after) to confirm zero numerical change.

- **Prep A:** Generic calibration loop in `_calibrate_reference_aircraft` — replace 3 copy-pasted blocks with a single parameterized loop.
- **Prep B:** Data-driven energy type handling in `fleet_performance.py` — replace `if/elif` branching with loop over energy types list. Also fix subcategory-level per-energy-type values (`energy_consumption`, `doc_non_energy`, `emission_index_nox/soot`) to be proper means rather than share-weighted contributions. Note: `hybridization_factor` split only applies to energy consumption; DOC and non-CO2 emissions treat hybrid-electric as its own category.
- **Prep C:** Vectorize performance methods in `fleet_performance.py` — replace row-by-row `.at[]` loops with numpy array operations (matching the pattern already used in the assignment step).
- **Prep D (optional):** Unify 1/2/3+ subcategory branching in `_compute_single_aircraft_share` into a single N-subcategory algorithm.
- **Exit:** Fleet model code is cleaner; all outputs numerically identical.

### Phase 0 — Data model & registry

- Define `markets.yaml` schema, implement `Market` and `MarketRegistry`.
- Unit test loader against default 4-market file.
- **Exit:** `MarketRegistry.from_yaml()` matches today's constants.

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

### Phase 3 — Fleet model market integration

- `fleet.yaml` restructured: `categories` replaced by `markets` keying; subcategories and aircraft assignments unchanged.
- `Category` class renamed/replaced by market-driven grouping (or simply reads its `name` from the `MarketRegistry` entry).
- Calibration loop (already generic from Prep A) swaps its config source from hardcoded tuples to `MarketRegistry` iteration.
- Fleet model publishes market-level aggregates under market-templated names; subcategory-level details remain internal to `self.df`.
- Energy type loop (from Prep B) ensures the publishing covers all `market × energy_type` combinations cleanly.
- `fleet_numeric.py`: replace hardcoded `if category == "Short Range"` / `"Medium Range"` / `"Long Range"` dispatch with iteration over `MarketRegistry` passenger markets.
- If Prep D was deferred, consider combining it here.
- Coordinate with colleague's fleet model on output naming.
- **Exit:** fleet model driven by `MarketRegistry`; outputs under market-templated names.

### Phase 4 — Downstream impacts (custom wrapper migration)

This is the bulk of the line-count work. Each model follows the `NOxEmissionIndexComplex` pattern:

1. Add `MarketRegistry` to `__init__`.
2. Implement `custom_setup()` building `input_names`/`output_names` from registry.
3. Switch to `AeroMAPSCustomModelWrapper`.
4. Refactor `compute()` to use `input_data` dict.

Because Prep B made the fleet model's energy type handling data-driven, the `custom_setup()` methods in downstream models can iterate `markets × energy_types` — two clean loops — rather than inheriting hardcoded branching.

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
| 3 | Fleet output key rename cascade | Atomic rename in Phase 3 or alias layer — pick based on diff size |
| 4 | Coordination with colleague's fleet model | Land Prep phase early so colleague's code is clean before Phase 3; communicate naming convention |
| 5 | `data_information.csv` consumed by GUI | Verify before removing rows in Phase 5 |
| 6 | Fleet prep refactors introducing regressions | Each prep step verified by full DataFrame diff before/after; prep lands as separate commits |

## 8. Migration strategy

**Hard cut, no transition shim.** Safe because:
1. Default `markets.yaml` = exact legacy structure.
2. Variable names unchanged for default markets.
3. Notebook test suite is the safety net.

User upgrade path: default scenarios need no action; custom scenarios move market params from `parameters.json` to a custom `markets.yaml`.

**Fleet prep work** lands first as independent commits on the current codebase. This de-risks Phase 3 and can be reviewed/merged without waiting for the market infrastructure (Phases 0–2).

## 9. Decision log

| Decision | Rationale |
|----------|-----------|
| Hard cut, no shim | Clean; small user community |
| Underscore naming | Consistency with current codebase |
| No factory for markets | All markets same shape |
| No ABC for fleet models | GEMSEO grammar matching suffices |
| Market replaces Category | Simplifies architecture: no binding layer, no share splitting. Market *is* the fleet grouping level |
| Aircraft in multiple markets via inventory duplication | Simpler than share-based binding; aircraft can have market-specific parameters (ASK/year, etc.) |
| Subcategories stay fleet-internal | Downstream models only need market-level aggregates; subcategory share evolution is a fleet concern |
| `AeroMAPSCustomModelWrapper` for downstream | Proven pattern (NOxEmissionIndexComplex); only viable approach for dynamic I/O names |
| One discipline per market | Consistent with energy carriers pattern |
| Belly freight out of scope | Adds market-to-market coupling; follow-up once basic refactor stable |
| Fleet prep before market phases | Reduces Phase 3 diff size and risk; lands independently; no wasted work even if market refactor is delayed |
| Data-driven energy types in fleet | Orthogonal to market dimension but synergistic: simplifies Phase 4 `custom_setup()` implementations |

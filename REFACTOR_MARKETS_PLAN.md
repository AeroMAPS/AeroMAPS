# AeroMAPS — User-Defined Markets Refactor Plan

**Status:** In progress |  **Updated:** 2026-05-26

**Detailed Phase Interface design notes:** `.claude/plans/optimized-singing-scott.md`

## 0. Progress snapshot

| Phase | Status | Landed in |
|-------|--------|-----------|
| Prep A — Generic calibration loop | ✅ done | `6a4df264` |
| Prep B — Data-driven energy types + subcategory semantics | ✅ done | `9ada8844`, `47640c39` |
| Prep C — Vectorize performance methods | ✅ done | `af31d25d` |
| Prep D — Unify 1/2/3+ subcategory branching | ⏳ deferred | (optional; TBD) |
| Phase 0 — `Market` + `MarketManager` + default `markets.yaml` | ✅ done | `e5f9229e` |
| Phase 1 — Process integration (`_initialize_markets`, flattener) | ✅ done | `70aae1bf`, `0f31098c`, naming fix on top |
| Phase Interface — Flex-market demo ("Custom Markets × Multi-Regions") | 🚧 WIP | chantier commits on `fleet-refactoring` branch |
| Phase 2 — Air traffic disciplines | ✅ done | `720c0f02`–`2b64fde3` |
| Phase 3 — Fleet model market integration | ✅ done | `c42d2a67`–`febffdb8` |
| Phase 4 — Downstream impacts (custom wrapper migration) | ✅ done | `3f37e04d`–`3950aec3` |
| Phase 5 — Migration & cleanup | ✅ done | `1b3ff875`–`183b3867` |
| Phase 6 — Plots & GUI | 🚧 WIP | GUI rename done (`183b3867`); plots in progress on `fleet-refactoring` |

**Conventions locked in by Phase 0–1:**
- Registry class is named **`MarketManager`** (not `MarketManager` as the early drafts read).
- Variable naming is **market-as-prefix**: `<market_id>_<leaf_key>` (e.g. `short_range_rpk_share_2019`, `short_range_measures_final_impact`, `short_range_covid_drop_start_year`). See §3.5.
- `markets.yaml` sub-grouping keys (`initial`, `growth`, `covid`, `measures`, `efficiency_simple`, `costs`) are **organisational only** — the flattener drops them. Leaves that would be ambiguous (e.g. `start_year`, `end_year`, `duration`) explicitly carry the group name, e.g. `measures_start_year`, `covid_end_year`.
- **COVID is now per-market** in `markets.yaml` (legacy had global `covid_rpk_drop_start_year`, `covid_end_year_passenger`, …). Until downstream models migrate (Phase 2+), legacy COVID names remain authoritative in `parameters.json`; the per-market names are additive shadows.

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

### 3.3 `Market` and `MarketManager` *(built — Phase 0/1)*

Module `aeromaps/models/air_transport/markets/`:

- **`Market`** dataclass — `id`, `name`, `traffic_type`, `traffic_unit`, `inputs` (raw nested dict from YAML, not flattened on the dataclass itself). See [market.py](aeromaps/models/air_transport/markets/market.py).
- **`MarketManager`** (analogous to `EnergyCarrierManager`) — `from_yaml(path)` classmethod, plus `get_all()`, `get_ids()`, `get(traffic_type=...)` filter, `add()`, `__iter__`, `__len__`. See [market_manager.py](aeromaps/models/air_transport/markets/market_manager.py).

Built once in [`AeroMAPSProcess._initialize_markets()`](aeromaps/core/process.py#L962), stored as `self.markets`. The method flattens each market's `inputs` into `self.parameters` under `<market_id>_<leaf_key>` names — **no sub-group key is included** (they are dropped when merging sub-group dicts before flattening). Skipped when the user's `config.yaml` has no `models.markets` block, so legacy configs stay functional.

**Validation currently implemented:** none beyond YAML well-formedness. Phase 2/3 will add:
- traffic_type ∈ {passenger, freight}, traffic_unit ∈ {RPK, RTK};
- every passenger market in `MarketManager` has a `fleet.yaml` entry (when bottom-up fleet is active);
- subcategory shares sum to 100%.

### 3.4 `fleet.yaml` — fleet structure per market

`fleet.yaml` declares the fleet structure under each market. Subcategories and aircraft assignments remain here — they are fleet-internal concerns.

```yaml
# aeromaps/resources/data/default_fleet/fleet.yaml
markets:
  - market_served: short_range
    parameters:
      life: 25
      limit: 2
    subcategories:
      - sr_conventional_nb
      - sr_hydrogen_nb

  - market_served: medium_range
    parameters:
      life: 25
      limit: 2
    subcategories:
      - mr_conventional_nb

  - market_served: long_range
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

*(As-landed in chantier 3.A: the top-level key is `market_served:` — not `market:` as the early draft read. The `MarketManager` cross-checks this field against registered market ids at fleet load time.)*

**Validation at load time:**
- Every passenger market in the `MarketManager` must have a corresponding entry in `fleet.yaml` (when bottom-up fleet model is active).
- Subcategory shares within each market must sum to 100%.
- Freight markets are handled by the freight efficiency model, not present in `fleet.yaml`.

**Aircraft in multiple markets:** An aircraft that serves both short and medium range (e.g. a versatile narrow-body) is simply referenced in the subcategory inventories of both markets, potentially with different parameters in `aircraft_inventory.yaml` (different ASK/year, different performance deltas, etc.).

### 3.5 Variable naming *(convention locked — Phase 1)*

**Rule:** market id is always the first segment of the flattened name: `<market_id>_<leaf_key>`. The flattener in `_initialize_markets()` drops the sub-group key (`initial`, `growth`, `covid`, …) and prefixes every leaf with the market id.

| Source in YAML | Flattened name | Example |
|----------------|----------------|---------|
| `inputs.initial.rpk_share_2019` | `<market>_rpk_share_2019` | `short_range_rpk_share_2019` |
| `inputs.initial.energy_share_2019` | `<market>_energy_share_2019` | `short_range_energy_share_2019` |
| `inputs.growth.cagr_reference_periods` | `<market>_cagr_reference_periods` | `long_range_cagr_reference_periods` |
| `inputs.covid.covid_drop_start_year` | `<market>_covid_drop_start_year` | `short_range_covid_drop_start_year` |
| `inputs.covid.covid_end_year` | `<market>_covid_end_year` | `medium_range_covid_end_year` |
| `inputs.measures.measures_final_impact` | `<market>_measures_final_impact` | `short_range_measures_final_impact` |
| `inputs.measures.measures_start_year` | `<market>_measures_start_year` | `long_range_measures_start_year` |
| `inputs.efficiency_simple.hydrogen_final_market_share` | `<market>_hydrogen_final_market_share` | `short_range_hydrogen_final_market_share` |
| `inputs.costs.doc_non_energy_per_ask_dropin_fuel_init` | `<market>_doc_non_energy_per_ask_dropin_fuel_init` | `short_range_doc_non_energy_per_ask_dropin_fuel_init` |

**Disambiguation rule:** where a leaf key would be meaningless on its own (`start_year`, `end_year`, `duration`, `drop_start_year`, `final_impact`, `end_year_reference_ratio`), the YAML leaf key carries its group name as a prefix (`measures_start_year`, `covid_drop_start_year`, …) so the flattened name is self-describing. Groups whose leaves are already semantically clear (`rpk_share_2019`, `hydrogen_final_market_share`, `doc_non_energy_per_ask_dropin_fuel_init`) are *not* prefixed.

**Downstream model names** (produced in Phase 2+) follow the same market-as-prefix rule for consistency with the flattened parameter names:

| Concept | Template | Example |
|---------|----------|---------|
| Traffic | `<market>_rpk` / `<market>_rtk` | `short_range_rpk` |
| ASK | `<market>_ask` | `medium_range_ask` |
| Energy/ASK | `<market>_energy_per_ask_<carrier>` | `long_range_energy_per_ask_dropin_fuel` |
| CAGR | `<market>_cagr` | `freight_cagr` |

**Divergence from legacy:** today's `parameters.json` uses three different conventions (prefix `short_range_rpk_share_2019`, infix `energy_per_ask_short_range_dropin_fuel_gain_reference_years`, suffix `hydrogen_final_market_share_short_range`). Phase 1 does *not* reproduce these names — it creates new templated names as additional attributes on `self.parameters`, while legacy names remain authoritative for downstream consumers. Phase 2/4 completes the rename as models migrate.

### 3.5.1 Old → new variable name mapping (migration reference)

Generated by auditing `dictionary_item_removed` / `dictionary_item_added` between `data/reference/outputs.json` (pre-refactor) and `data/outputs.json` (post-refactor) across **all four tutorials with a `reference/outputs.json`** — `01_run_a_basic_calculation`, `02_create_a_custom_process`, `03_partition_to_a_region`, `05_use_fleet_models`. The four diffs are consistent: union of removed names = 80, union of added names = 113; every diff is a subset of the union. **Every removal has a matching addition except the six `hybrid_electric` outputs in §F below** — those are intentionally dropped.

#### A. Pure renames (token reordering — same semantic, same scope)

| Old name | New name |
|----------|----------|
| `energy_per_ask_<range>_dropin_fuel_gain_reference_years[_values]` | `<range>_energy_per_ask_dropin_fuel_gain_reference_years[_values]` |
| `relative_energy_per_ask_hydrogen_wrt_dropin_<range>_reference_years[_values]` | `<range>_relative_energy_per_ask_hydrogen_wrt_dropin_reference_years[_values]` |
| `relative_energy_per_ask_electric_wrt_dropin_<range>_reference_years[_values]` | `<range>_relative_energy_per_ask_electric_wrt_dropin_reference_years[_values]` |
| `hydrogen_final_market_share_<range>` | `<range>_hydrogen_final_market_share` |
| `hydrogen_introduction_year_<range>` | `<range>_hydrogen_introduction_year` |
| `electric_final_market_share_<range>` | `<range>_electric_final_market_share` |
| `electric_introduction_year_<range>` | `<range>_electric_introduction_year` |
| `doc_non_energy_per_ask_<range>_dropin_fuel_init` | `<range>_doc_non_energy_per_ask_dropin_fuel_init` |
| `doc_non_energy_per_ask_<range>_dropin_fuel_gain` | `<range>_doc_non_energy_per_ask_dropin_fuel_gain` |
| `relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_<range>` | `<range>_relative_doc_non_energy_per_ask_hydrogen_wrt_dropin` |
| `relative_doc_non_energy_per_ask_electric_wrt_dropin_<range>` | `<range>_relative_doc_non_energy_per_ask_electric_wrt_dropin` |

(`<range>` ∈ {`short_range`, `medium_range`, `long_range`}.)

#### B. Renames with token drop (`rpk_` / `passenger_` qualifier removed)

| Old name | New name |
|----------|----------|
| `rpk_<range>_measures_final_impact` | `<range>_measures_final_impact` |
| `rpk_<range>_measures_start_year` | `<range>_measures_start_year` |
| `rpk_<range>_measures_duration` | `<range>_measures_duration` |
| `cagr_passenger_<range>_reference_periods[_values]` | `<range>_cagr_reference_periods[_values]` |
| `annual_growth_rate_passenger_<range>` (vector output) | `annual_growth_rate_rpk_<range>` |

#### C. Freight global → freight-prefixed

| Old name | New name |
|----------|----------|
| `covid_rtk_drop_start_year` | `freight_covid_drop_start_year` |
| `covid_end_year_freight` | `freight_covid_end_year` |
| `covid_end_year_reference_rtk_ratio` | `freight_covid_end_year_reference_ratio` |
| `cagr_freight_reference_periods[_values]` | `freight_cagr_reference_periods[_values]` |
| `reference_cagr_freight_reference_periods[_values]` | `freight_reference_cagr_reference_periods[_values]` |

#### D. 1-to-3 splits (was global passenger, now per-market)

Each old key now exists as **three** keys — one per passenger market. Default `markets.yaml` reproduces the old global value across the three; user-defined `markets.yaml` can diverge.

| Old name (global) | New names (per market) |
|-------------------|------------------------|
| `covid_rpk_drop_start_year` | `{short,medium,long}_range_covid_drop_start_year` |
| `covid_end_year_passenger` | `{short,medium,long}_range_covid_end_year` |
| `covid_end_year_reference_rpk_ratio` | `{short,medium,long}_range_covid_end_year_reference_ratio` |
| `covid_load_factor_2020` | `{short,medium,long}_range_covid_load_factor_2020` |
| `reference_cagr_passenger_reference_periods[_values]` | `{short,medium,long}_range_reference_cagr_reference_periods[_values]` |
| `load_factor_end_year` | `{short,medium,long}_range_load_factor_end_year` |

(Note: `load_factor_end_year` does not appear in `01_basic`'s pre-refactor outputs because that tutorial does not exercise the load-factor model; it surfaces as a global→per-market split in `02_custom_process`, `03_partition`, and `05_fleet`.)

#### E. New variables introduced by the refactor (no prior counterpart)

These have no entry in pre-refactor `outputs.json` — they are genuinely new (mostly emitted by the per-market traffic / RTK aggregator chain added in Phase 2 and the per-market efficiency models in Phase 4).

| Category | New name(s) | Notes |
|----------|-------------|-------|
| `float_inputs` | `freight_rtk_share_2019` | Freight share-of-RTK input, new from `markets.yaml` `initial` block |
| `float_outputs` | `cagr_rtk_freight`, `prospective_evolution_rtk_freight` | Freight equivalents of legacy passenger outputs |
| `vector_outputs` | `ask_{dropin_fuel,hydrogen,electric}_share` | Whole-simulation ASK shares by energy carrier (Phase 4, "total energy type shares") |
| `vector_outputs` | `rtk_freight_{dropin_fuel,hydrogen,electric}_share`, `rtk_freight_{dropin_fuel,hydrogen,electric}` | Per-carrier freight RTK shares + values (new freight efficiency model) |
| `vector_outputs` | `rpk_reference_<range>`, `reference_annual_growth_rate_rpk_<range>` | Per-market reference trajectories (was global only) |
| `vector_outputs` | `rtk_freight`, `annual_growth_rate_rtk_freight`, `rtk_reference_freight`, `reference_annual_growth_rate_rtk_freight` | Freight equivalents of passenger RPK series, emitted by `RTKMarket` aggregator |
| `vector_outputs` | `load_factor_{short,medium,long}_range` | Per-market load-factor series, emitted by `LoadFactorMarket` (legacy only published the aggregated `load_factor`) |

#### F. Always-zero placeholder outputs cleaned up (no behavioral change)

Surfaced only in `05_use_fleet_models`:

| Removed output | Reason |
|----------------|--------|
| `ask_<range>_hybrid_electric_share` (×3 ranges) | Pre-refactor placeholder — `PassengerAircraftEfficiencyComplex` initialized these to `0.0` and never reassigned them anywhere (see `main:aircraft_efficiency.py:935-942`). The refactor drops the unused keys. |
| `energy_per_ask_without_operations_<range>_hybrid_electric` (×3 ranges) | Same — pre-refactor always-zero placeholder. |

**This is a cleanup, not a regression.** Pre-refactor, hybrid-electric energy was already routed through the `dropin_fuel` + `electric` buckets via each hybrid aircraft's `hybridization_factor` (e.g. `0.4` ⇒ 60% to drop-in, 40% to electric); the dedicated `*_hybrid_electric` columns carried no information. Post-refactor preserves the exact same split semantics and emits no zero-valued placeholders.

**Verified against the MEA 2024 notebook** ([`examples_mea_application.ipynb`](aeromaps/notebooks/publications/mea_2024/examples_mea_application.ipynb)) — the only AeroMAPS publication that exercises hybrid-electric aircraft (`sr_nb_hybrid`, `mr_nb_hybrid` with `hybridization_factor: 0.4`, ASK shares 100% / 22.86% in SR / MR). Running both `config_mix.yaml` and `config_others.yaml` confirms zero `hybrid_electric`-named keys in either `outputs_*.json`, identical to the pre-refactor behavior (which would have emitted them with value `0.0`). The notebook's hybrid-electric plots come from `data/mea_data*.csv`, not from process outputs, so the cleanup is invisible to the reader.

**Genuine feature gap (out of scope for this PR — file as separate issue):** publishing a true `*_hybrid_electric` output series (subcategory ASK share + per-ASK energy for hybrid-electric aircraft, not split across other carriers) requires extending `PassengerAircraftEfficiency.custom_setup` / `compute` at [aircraft_efficiency.py:420](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py#L420), [:427](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py#L427), [:491-509](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py#L491-L509) to read `<market>:share:total` from the relevant hybrid-electric subcategories in `fleet_model.df` and to surface the `:hybrid_electric` energy column. This work has never been done in either branch.

#### G. Numerical drifts (not renames — flagged for PR notes)

The same audit reported `values_changed` beyond the 0.01% tolerance. These are **not regressions**; both are expected bug fixes from the refactor (see commits `a3ed83b3`, `3950aec3`):

- `vector_outputs.doc_carbon_tax_lowering_offset_per_ask_short_range_mean[0..50]` — every year shifted upward (~28%). **Cause:** pre-existing carbon-tax-lowering bug, fixed in `a3ed83b3` ("removed existing bug highlighted by refactoring on carbon tax lowering offset").
- `vector_outputs.reference_annual_growth_rate_passenger[20..24]`, `annual_growth_rate_freight[20..24]`, `reference_annual_growth_rate_freight[20..24]` — old reference held a constant 3.0 across the COVID recovery window; new values reflect the actual COVID drop (e.g. `annual_growth_rate_freight[20] = -66%`) and the steep year-over-year rebound. **Cause:** different (more correct) growth-rate computation mode during COVID years (see commit `3950aec3`).

#### H. How this was generated

```bash
# For each tutorial with a data/reference/outputs.json:
for t in 01_run_a_basic_calculation 02_create_a_custom_process \
         03_partition_to_a_region 05_use_fleet_models; do
  cd "aeromaps/notebooks/tutorials/$t"
  python -c "
from aeromaps.utils.functions import compare_json_files
compare_json_files('./data/reference/outputs.json', './data/outputs.json', rtol=0.0001, atol=0)
"
  cd -
done
```

To regenerate the mapping after further refactoring, parse `dictionary_item_removed` / `dictionary_item_added` from each tutorial's DeepDiff, union them, and apply the heuristics: (i) token-permutation per `(category, sorted_tokens)`, (ii) drop the `rpk_` / `passenger_` qualifier, (iii) freight prefix substitution, (iv) explicit 1-to-3 splits for the COVID / load-factor / reference-CAGR keys.

#### I. Per-tutorial diff coverage

| Tutorial | removed | added | Notes |
|----------|---------|-------|-------|
| `01_run_a_basic_calculation` | 73 | 113 | Smallest scope; no load-factor model exercised, hence no `load_factor_end_year` rename. |
| `02_create_a_custom_process` | 62 | 101 | Subset of 01 + adds `load_factor_end_year` split. Fewer renames because the custom process exposes fewer DOC inputs. |
| `03_partition_to_a_region` | 62 | 101 | Identical removed/added set to 02. |
| `05_use_fleet_models` | 38 | 71 | Adds the six `hybrid_electric` removals from §F. Fewer renames because this tutorial doesn't exercise the simple-share / efficiency-simple inputs that the others do. |

Each per-tutorial set is a subset of the §A–F union. **No tutorial reveals a rename absent from the others' union** — i.e. the mapping in §A–F is complete with respect to the four diff-bearing tutorials.

### 3.6 GEMSEO discipline strategy

**One discipline instance per market** (approach A), consistent with the energy carriers pattern. Each instance has a generic compute signature; GEMSEO grammars stay flat. Cost: N disciplines instead of 1, negligible overhead.

### 3.7 Downstream model I/O: `AeroMAPSCustomModelWrapper` pattern

A large part of the work is making **downstream models** (energy consumption, costs, emissions, etc.) wire correctly to dynamic market-named variables. GEMSEO connects disciplines by matching I/O names, so every downstream model must declare inputs/outputs that include market ids.

**The pattern to follow is `NOxEmissionIndexComplex`** ([non_co2_emissions.py:157](aeromaps/models/impacts/emissions/non_co2_emissions.py#L157)):

1. The model inherits from `AeroMAPSModel` with `model_type="custom"`.
2. It implements a **`custom_setup()`** method that dynamically builds `self.input_names` and `self.output_names` dicts based on runtime information (the `MarketManager` here, the `EnergyCarrierManager` in the existing example).
3. It is wrapped with **`AeroMAPSCustomModelWrapper`** ([gemseo.py:200](aeromaps/core/gemseo.py#L200)) instead of `AeroMAPSAutoModelWrapper`. The custom wrapper reads `input_names`/`output_names` to build GEMSEO grammars, rather than introspecting the `compute()` signature.
4. `compute()` receives an `input_data` dict and returns an `output_data` dict — no typed signature, fully dynamic.

**Applied to the market refactor:** every model that today has hard-coded `ask_short_range_dropin_fuel`, `ask_medium_range_hydrogen`, etc. in its signature will instead:
- Receive the `MarketManager` at `__init__`
- Build `input_names`/`output_names` in `custom_setup()` by iterating over `self.markets.get_all()` and templating variable names
- Use `AeroMAPSCustomModelWrapper` for GEMSEO integration

This is the **same migration done for the generic energy models**, now applied to the market dimension. Models affected: `DropInFuelConsumption`, `PassengerAircraftDocNonEnergyComplex`, `NOxEmissionIndexComplex` itself (adding market dimension), and all other downstream models listed in section 5.

## 4. Fleet model interaction

All fleet renewal models (existing `FleetModel`, `PassengerAircraftEfficiencySimpleShares`, and colleague's new model) must publish outputs under templated market names: `energy_per_ask_<market>_<carrier>`, `ask_<market>_<carrier>_share`, etc.

Since the market *is* the fleet category, the fleet model simply:
- Iterates over markets from the `MarketManager`.
- Runs its S-curve assignment + performance computation independently per market.
- Publishes market-level aggregates under market-templated names (subcategory details remain internal to `self.df`).
- The calibration loop at [fleet_model.py:869-1023](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py#L869-L1023) becomes a generic loop over markets, with calibration parameters sourced from `MarketManager`.

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

**Link to market plan:** This is a strict subset of Phase 3. In the final market-integrated form, the config list is replaced by `MarketManager` iteration and calibration parameters come from each market's flattened inputs. Doing this prep step means Phase 3 only needs to swap the config source — the loop structure is already correct.

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

| Path | Purpose | Status |
|------|---------|--------|
| `aeromaps/resources/data/default_markets/markets.yaml` | Default 4-market definition | ✅ done (Phase 0) |
| `aeromaps/models/air_transport/markets/market.py` | `Market` dataclass | ✅ done (Phase 0) |
| `aeromaps/models/air_transport/markets/market_manager.py` | `MarketManager`, YAML loader, validation | ✅ partial (Phase 0; validation TODO) |

### Refactored files

| File | Change | Phase | Status |
|------|--------|-------|--------|
| [fleet_model.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py) | Prep A: generic calibration loop (standalone) | Prep | ✅ |
| [fleet_performance.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_performance.py) | Prep B: data-driven energy types; Prep C: vectorize performance methods | Prep | ✅ |
| [fleet_assignment.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_assignment.py) | Prep D (optional): unify subcategory branching; Phase 3: `market_id` plumbing | Prep / 3 | ⏳ Prep D deferred; Phase 3 changes ✅ (3.D) |
| [process.py](aeromaps/core/process.py) | Add `_initialize_markets()`, instantiate per-market disciplines, push templated params | 1 | ✅ (instantiation + per-market disciplines moved to Phase 2) |
| [models.py](aeromaps/core/models.py) | Replace static model dicts with builders taking `MarketManager` | 2 | ⏱ |
| [config.yaml](aeromaps/resources/data/config.yaml) | Add `models.markets.markets_data_file` | 1 | ✅ |
| [fleet.yaml](aeromaps/resources/data/default_fleet/fleet.yaml) | `categories:` → `markets:` with `market_served:` key per entry | 3 | ✅ (3.A) |
| [rpk.py](aeromaps/models/air_transport/air_traffic/rpk.py) | Per-market instances replacing 3-way loops (lines 144-220) | 2 | ✅ |
| [rtk.py](aeromaps/models/air_transport/air_traffic/rtk.py) | Unify with RPK (same math, different unit) or keep separate | 2 | ✅ |
| [ask.py](aeromaps/models/air_transport/air_traffic/ask.py) | Iterate over registry's passenger markets | 2 | ✅ |
| [fleet_model.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py) | Phase 3: iterate over `MarketManager`; calibration from registry; publish market-templated outputs via custom wrapper | 3 | ✅ (3.B–3.C) |
| [fleet_numeric.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_numeric.py) | Market-driven dispatch replacing hardcoded Short/Medium/Long Range; `FleetEvolutionFromShares` | 3 | ✅ (3.C) |
| [fleet_assignment.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_assignment.py) | `market_id` plumbing + explicit first-subcategory ref | 3 | ✅ (3.D) |
| [aircraft_efficiency.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py) | Per-market disciplines + custom wrapper pattern | 3 | ✅ (3.E) |
| [energy_consumption.py](aeromaps/models/impacts/energy_resources/energy_consumption.py) | Custom wrapper with dynamic I/O from registry (~40 hard-coded args removed) | 4 | ✅ (4.C) |
| [direct_operating_costs.py](aeromaps/models/impacts/costs/airlines/direct_operating_costs.py) | Full DOC chain migrated (NonEnergySimple, NonEnergyComplex, Energy, CarbonTax+Sub+Tax, TotalDoc, TotalCost) | 4 | ✅ (4.E, 4.F.1–4.F.5) |
| [non_co2_emissions.py](aeromaps/models/impacts/emissions/non_co2_emissions.py) | Market dimension added to NOxEmissionIndexComplex; soot index market-driven | 4 | ✅ (4.B) |
| [co2_emissions.py](aeromaps/models/impacts/emissions/co2_emissions.py) | Custom wrapper migration; freight markets support; climate-specific _store_outputs | 4 | ✅ (4.D) |
| [fleet_abatement_cost.py](aeromaps/models/impacts/costs/efficiency_abatement_cost/fleet_abatement_cost.py) | Custom wrapper migration | 4 | ✅ (4.F.6) |
| [total_airline_cost_and_airfare.py](aeromaps/models/impacts/costs/airlines/total_airline_cost_and_airfare.py) | Custom wrapper migration (marginal cost function kept as AutoModel) | 4 | ✅ (4.F.5) |
| [aircraft_efficiency.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py) | FreightAircraftEfficiency market integration; PassengerAircraftEfficiencySimpleASK refactor; total energy type shares | 4 | ✅ |
| [others.py](aeromaps/models/impacts/others/others.py) | Audit — EmissionsPerRPK/RTK consume aggregate quantities only; no hard-coded market IDs | 4 | ✅ (no change needed) |
| [parameters.json](aeromaps/resources/data/parameters.json) | Remove ~40 per-market entries (moved to markets.yaml) | 5 |
| Tutorial notebooks + JSON | Migrate per-market entries, re-run | 5 |

### Deferred

- `aeromaps/plots/*` and `aeromaps/gui/*` — Phase 6.

## 6. Phased work plan

Each phase ends with notebooks passing before moving on.

### Phase Prep — Fleet model clean-up ✅ *(A/B/C done, D deferred)*

Standalone refactors on the fleet model that reduce Phase 3 complexity. Each step was verified by full DataFrame diff to confirm zero numerical change.

- **Prep A** ✅ `6a4df264` — Generic calibration loop in `_calibrate_reference_aircraft` (3 copy-pasted blocks → single parameterized loop).
- **Prep B** ✅ `9ada8844` + `47640c39` — Data-driven energy type handling in `fleet_performance.py` (`if/elif` → loop over energy types); subcategory-level per-energy-type values corrected to proper means rather than share-weighted contributions. Variable naming clarified. `hybridization_factor` split confined to energy consumption only; DOC and non-CO2 emissions treat hybrid-electric as its own category.
- **Prep C** ✅ `af31d25d` — Vectorized performance methods in `fleet_performance.py` (row-by-row `.at[]` loops → numpy array operations).
- **Prep D** ⏳ deferred — Unify 1/2/3+ subcategory branching in `_compute_single_aircraft_share` into a single N-subcategory algorithm. Can be folded into Phase 3 if risk is acceptable; safe to keep deferred.

### Phase 0 — Data model & registry ✅ *(done — `e5f9229e`)*

Landed:
- [`aeromaps/models/air_transport/markets/market.py`](aeromaps/models/air_transport/markets/market.py) — `Market` dataclass (id, name, traffic_type, traffic_unit, inputs).
- [`aeromaps/models/air_transport/markets/market_manager.py`](aeromaps/models/air_transport/markets/market_manager.py) — `MarketManager` with `from_yaml`, `get_all`, `get_ids`, `get(traffic_type=...)`, `add`, `__iter__`, `__len__`.
- [`aeromaps/resources/data/default_markets/markets.yaml`](aeromaps/resources/data/default_markets/markets.yaml) — 4 markets reproducing legacy numerics.

Not yet done (follow-up for Phase 2/3 when downstream validation is wired in): dedicated unit tests for the loader and schema validators (traffic_type whitelist, fleet.yaml cross-check, subcategory share sum).

### Phase Interface — Demo case "Custom Markets × Multi-Regions"

Delivers a user-driven mode end-to-end for a demo case (8 regions × 7 aircraft-subcategory markets from an Excel file), without modifying the legacy bottom-up/top-down paths. Coexists with Phases 1–5 which handle the full GEMSEO wiring.

Six chantiers, ordered **A → B & C → D → E → F**:

| # | Chantier | Key files | Purpose |
|---|----------|-----------|---------|
| A | Aircraft YAML schema extensions | `fleet_model.py`, `fleet_performance.py` | Add `share` (`AeroMapsCustomDataType`), `energy_per_ask_absolute`, `continuous_improvement_factor_energy` to aircraft cards. Add `_resolve_field` helper. Loader switched to `read_yaml_file`. Energy resolution order: absolute → relative → × factor. |
| B | Linear RPK growth model + elasticity | NEW `rpk_linear.py` | `RPKLinearGrowth` + `RPKLinearGrowthWithElasticity`: linear interpolation between RPK waypoints per market. No flow inversion — script converts ASK→RPK upstream. Reuses `aeromaps_interpolation_function`. |
| C | FleetModel share-decoupling | `fleet_model.py` | When aircraft cards carry `share: !AeroMapsCustomDataType`, skip S-curve (`_compute_single_aircraft_share` + `_compute_aircraft_share`); populate `aircraft_share` columns directly from interpolated user shares. Reference-aircraft get residual. |
| D | `FleetEvolutionFromShares` | `fleet_numeric.py` | Compute `aircraft_in_fleet = ceil(share/100 × ASK_market / ask_year_market(t))`. Productivity (`ask_year`) read at market level from `markets.yaml` `inputs.productivity.ask_year`. |
| E | Excel → YAML generator | `generate_regional_markets.py` | ASK→RPK conversion via `load_factor`; emit RPK waypoints + market-level `ask_year`; generate `aircraft_inventory.yaml` + `fleet.yaml` per region. |
| F | Demo notebook | `example_notebook.ipynb` | Multi-region parallel process using per-region `config.yaml`. |

**`markets.yaml` schema extensions** (new `inputs` blocks):
```yaml
inputs:
  growth:
    mode: linear_rpk            # NEW — else 'cagr' (default)
    rpk_waypoint_years:   [2019, 2025, 2050]
    rpk_waypoint_values:  [8.7e11, 9.5e11, 1.7e12]
  productivity:                 # NEW — market-level, not per-aircraft
    ask_year: !AeroMapsCustomDataType
      years: [2025, 2045]
      values: [3.0e8, 3.4e8]
```

**Aircraft YAML schema extensions** (new fields in `aircraft_inventory.yaml`):
```yaml
parameters:
  energy_per_ask_absolute: 0.85                       # NEW (alt. to consumption_evolution)
  continuous_improvement_factor_energy: !AeroMapsCustomDataType  # NEW
    years: [2025, 2050]
    values: [1.0, 0.85]
  share: !AeroMapsCustomDataType                      # NEW (bypasses S-curve)
    years: [2025, 2035, 2050]
    values: [0, 30, 50]
```

**New files:**
| Path | Purpose |
|------|---------|
| `aeromaps/models/air_transport/air_traffic/rpk_linear.py` | `RPKLinearGrowth` + `RPKLinearGrowthWithElasticity` |
| `data/<REGION>/{markets,aircraft_inventory,fleet,config}.yaml` | Generated per-region inputs (demo only) |

**Modified files:**
| File | Change |
|------|--------|
| `fleet_model.py` | A: new dataclass fields, `_resolve_field`, loader. C: share-decoupling mode switch. |
| `fleet_performance.py` | A: energy resolution order (absolute vs relative + continuous improvement factor). |
| `fleet_numeric.py` | D: `FleetEvolutionFromShares` alongside `FleetEvolution`. |
| `models.py` | B+C+D: builder selection for linear RPK and user-driven fleet variants. |
| `generate_regional_markets.py` | E: ASK→RPK, market productivity, aircraft cards. |
| `example_notebook.ipynb` | F: restructure. |

**Open questions:**
1. Reference-aircraft share in user-driven fleet mode: residual (`100 - Σ`, proposed default) vs require user to fully specify.
2. Load factor as `AeroMapsCustomDataType` vs simple `{year: value}` dict.

**Consequences for later phases:**
- Phase 1: must flatten `inputs.growth.rpk_waypoint_*` and `inputs.productivity.ask_year`.
- Phase 2: can reuse `RPKLinearGrowth`/`RPKLinearGrowthWithElasticity` as reference per-market disciplines.
- Phase 3: share-decoupling (C) and `FleetEvolutionFromShares` (D) already iterate over markets; Phase 3 extends this to the S-curve path.

**Exit:** Demo notebook runs end-to-end for 8 regions × 7 markets. Legacy notebooks unaffected.

### Phase 1 — Process integration ✅ *(done — `70aae1bf`, `0f31098c`, + naming fix)*

Landed:
- `models.markets.markets_data_file` added to [config.yaml](aeromaps/resources/data/config.yaml).
- [`_initialize_markets()`](aeromaps/core/process.py#L962) — loads `markets.yaml` via `MarketManager.from_yaml`, stores as `self.markets`, flattens each market's `inputs` into `self.parameters` under `<market_id>_<leaf_key>` names. Called from `setup_mda()` and `create_gemseo_scenario()` before `_initialize_disciplines()`, mirroring the energy carriers hook point. Early-returns when `models.markets` is absent from user config so legacy configs stay functional.
- YAML leaf keys renamed to eliminate ambiguity after flattening: `covid.{drop_start_year,end_year,end_year_reference_ratio}` → `covid.covid_*`; `measures.{final_impact,start_year,duration}` → `measures.measures_*`.
- 40 unit tests green; `01_run_a_basic_calculation` unaffected (it does not opt into `models.markets`).

**Known caveats to address in Phase 2:**
- **Phase 1 is a numerical no-op because legacy names in `parameters.json` remain authoritative for downstream consumers.** The YAML-derived names land as *additional* attributes on `self.parameters` that no discipline reads yet. The original Phase 1 commit message framed this as "flattener reproduces legacy names verbatim" — that is only true for the `initial` sub-group (`<market>_rpk_share_2019`, `<market>_energy_share_2019`). All other sub-groups emit new names that differ from `parameters.json` conventions. See §3.5.
- **COVID is now per-market** (previously global). Legacy `covid_rpk_drop_start_year`, `covid_end_year_passenger`, `covid_end_year_reference_rpk_ratio` remain the authoritative values consumed by today's disciplines.
- `MarketManager.from_yaml` does not yet validate `traffic_type`/`traffic_unit` or cross-check against `fleet.yaml`. Add when Phase 2/3 gives it a consumer.

**Not done (moved to Phase 2):**
- Audit LCA/climate for per-market dependencies.
- `AeroMAPSCustomModelWrapper` spike — not blocking for Phase 1 since `_initialize_markets` is pure data loading. To be done as the first chantier of Phase 2 on a real air-traffic discipline.

### Phase 2 — Air traffic disciplines ✅ *(done — `720c0f02`–`2b64fde3`)*

Landed:
- **`RPKMarket`**, **`RPKMeasuresMarket`**, **`RPKReferenceMarket`**, **`RPKAggregator`** — per-passenger-market RPK with optional measures and reference trajectories; aggregator emits the legacy `rpk` / `annual_growth_rate_passenger` / `cagr_rpk` / `prospective_evolution_rpk` names so downstream models are unaffected. All use `model_type="custom"` (I/O names built at `__init__` time; no `custom_setup` hook needed).
- **`RTKMarket`**, **`RTKReferenceMarket`** — per-freight-market RTK keeping legacy output names (`rtk`, `rtk_reference`, …) for full downstream compatibility. Only one freight market supported (raises if multiple are configured).
- **`ASKMarket`**, **`ASKAggregator`** — per-passenger-market ASK derived from `<mid>_rpk / (<mid>_load_factor / 100)`; aggregator emits legacy `ask`.
- **`LoadFactorMarket`**, **`LoadFactorAggregator`** — per-passenger-market load factor (quadratic model); aggregator recombines into global `load_factor` consumed by downstream disciplines.
- **`markets_factory.py`** — factory helpers (`create_market_rpk_models`, `create_market_rpk_aggregator`, `create_market_ask_models`, `create_market_load_factor_models`, `create_market_rtk_models`) that wire the `MarketManager` into discipline instantiation; optional sub-models (measures, reference) are only created when the corresponding YAML sub-group is present.
- **Deep defaults merge in `markets.yaml`** — a top-level `defaults.passenger` (and `defaults.freight`) block allows shared parameter values without repeating them for every market; `_initialize_markets()` deep-merges per-market inputs on top of the defaults.
- **Test notebook** (`12_default_markets_test/test_default_markets.ipynb`) — minimal end-to-end run using per-market traffic disciplines; validates the full `MarketManager` → traffic → ASK chain.

**Known caveats / deferred to Phase 5:**
- Legacy `LoadFactor`, legacy `RPK`/`RTK`/`ASK` classes still exist and are marked `PHASE-5-CLEANUP`; they are superseded but not yet deleted.
- COVID global-to-per-market rename (`covid_rpk_drop_start_year` → `<market>_covid_drop_start_year`) is realised in the new per-market models, but legacy global names in `parameters.json` are unchanged — will be cleaned up in Phase 5.
- `RTKMarket` keeps legacy output names (`rtk`, `rtk_reference`) to avoid touching downstream models before Phase 4. A multi-freight-market generalisation is deferred.
- LCA/climate audit for per-market dependencies still pending (carried forward to Phase 3/4 as context is needed from fleet outputs).

### Phase 3 — Fleet model market integration ✅ *(done — `c42d2a67`–`febffdb8`)*

Landed across six chantiers (2026-04-27/28):

- **3.A** `c42d2a67` — `fleet.yaml` schema migration: `categories:` top-level key replaced by `markets:` with `market_served:` field per entry (not `market:`); loader updated accordingly.
- **3.B** `c6a82996` — Calibration loop (`_calibrate_reference_aircraft`) now sourced from `MarketManager`; the hardcoded `CALIBRATION_CONFIG` tuples from Prep A are replaced by registry iteration.
- **3.C** `bb820059` — `FleetEvolution` migrated to custom wrapper with market-driven dispatch; `FleetModel` publishes market-level aggregates under market-templated output names.
- **3.D** `16ed74b9` — `fleet_assignment` audit: `market_id` plumbing through subcategory share computation; explicit first-subcategory reference handling.
- **3.E** `cec18670` — `FleetPerformanceMixin` verified for arbitrary market count via a 5-market smoke test; energy type loop from Prep B confirmed clean across all market × energy_type combinations.
- **3.F** `febffdb8` — Custom-market smoke test: 5-market `FleetModel` + `FleetEvolution` end-to-end; 73 tests passing total.

**Deferred (3.G / Prep D):** Unify 1/2/3+ subcategory branching in `_compute_single_aircraft_share` — explicitly out of scope for this run; owner-restricted (human or Opus only).

**Known pre-existing issues (not caused by Phase 3):**
- `AeroMAPSProcess()` constructor fails with `RuntimeError: Model 'nox_emission_index_complex' requires a pathways_manager` — pre-existing on branch.
- `recurring_costs.py` / `non_recurring_costs.py` pandas `TypeError` — pre-existing.
- Notebook 05 `outputs.json` numerical drift — inherited from earlier branch work.

**Exit:** fleet model driven by `MarketManager`; outputs under market-templated names; 73 tests green.

### Phase 4 — Downstream impacts (custom wrapper migration) ✅ *(done — `3f37e04d`–`3950aec3`)*

Landed across six labelled chantiers plus additional fixes and freight efficiency work (2026-04-28 → 2026-05-04):

- **4.A** `3f37e04d` — Markets injection hook in `process.py`; single `custom_setup()` call wired into the MDA build path.
- **4.B** `563fe331` + fix `96476591` — `NOxEmissionIndexComplex`: market-driven `custom_setup` + `compute`; soot emission index inputs made market-driven.
- **4.C** `36658ccb` + fixes `fc9bdf4f`, `1326dced` — `DropInFuelConsumption`: custom wrapper migration; documentation retained at class level.
- **4.D** `79fe0c8e` + fixes `73a4ba03`, `10639edc` — `CO2Emissions`: custom wrapper migration; freight markets wired correctly; documentation retained.
- **4.E** `8ea73e54` — `PassengerAircraftDocNonEnergyComplex`: custom wrapper migration.
- **4.F.1** `163c450b` — `PassengerAircraftDocNonEnergySimple`: custom wrapper migration.
- **4.F.2** `e0dde4ee` — `PassengerAircraftDocEnergy`: custom wrapper migration.
- **4.F.3** `780e4442` — `DocEnergyCarbonTax` + `DocEnergySubsidy` + `DocEnergyTax`: custom wrapper migration.
- **4.F.4** `42e659a0` — `PassengerAircraftTotalDoc`: custom wrapper migration.
- **4.F.5** `6d8dd777` + fix `7716ef7f` — `TotalAirlineCostAndAirfare`: custom wrapper migration; marginal cost function kept as `AutoModel` (no market dimension there).
- **4.F.6** `b34c078a` — `FleetAbatementCost`: custom wrapper migration.
- **Freight efficiency** `87199974`, `56696515` — `FreightAircraftEfficiency` significantly refactored for market-driven operation; `PassengerAircraftEfficiencySimpleASK` and `FreightAircraftEfficiency` cleaned up with `_store_outputs`; total energy type shares (whole-simulation, not per market) added to aircraft efficiency.
- **Post-F fixes** `3d0cff55`, `7f782c58`, `a3ed83b3` — Various fixes: explicit variable names replacing abbreviations, pre-existing bug on carbon tax offset lowering removed (exposed by refactoring), misc corrections.
- **RTK/RPK aggregator enhancements** `5d860e0d` — `RTKMarket` aggregator and reference models added; input naming conventions unified across markets; DOC and fleet abatement cost minor fixes.
- **CO2 / base enhancements** `6042ae0b` — `_store_outputs` enhanced for climate-specific outputs; CO2Emissions storage updated.
- **Documentation** `fb3fa39a` — Doc classes documentation improved; variables made more explicit.
- **Notebook investigation** `3950aec3` — Numerical diffs in `01_basic` notebook explained: DOC non-energy lowering was a pre-existing bug now fixed; annual growth rate difference in COVID years is a known computation-mode difference, not a regression.

**`EmissionsPerRPK` / `EmissionsPerRTK` / `DropinFuelConsumptionLiterPerPax100km` ([others.py](aeromaps/models/impacts/others/others.py)):** audited — these consume aggregate `co2_emissions_passenger` / `co2_emissions_freight` / `rtk` / `rpk` quantities only; no hard-coded market IDs; no custom wrapper needed.

**Known caveats / deferred to Phase 5:**
- PHASE-5-CLEANUP markers remain in [rpk.py](aeromaps/models/air_transport/air_traffic/rpk.py), [rtk.py](aeromaps/models/air_transport/air_traffic/rtk.py), [ask.py](aeromaps/models/air_transport/air_traffic/ask.py), [load_factor.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/load_factor/load_factor.py) — legacy monolithic classes kept for backwards compatibility.
- Per-market entries in `parameters.json` still exist; removal is Phase 5 work.
- `operations_abatement_cost.py` uses no market IDs (operates on aggregate fuel consumption); no migration needed.

**Exit:** 73 tests green; zero hard-coded `short_range`/`medium_range`/`long_range` market IDs in live model code (only in commented-out dead code in `direct_operating_costs.py`).

### Phase 5 — Migration & cleanup ✅ *(done — `1b3ff875`–`183b3867`)*

Landed across several commits (2026-05-13 → 2026-05-26):

- **`1b3ff875`** — Elasticity model fixed for new market standard; now a separate model in `rpk_markets` (passes a suffix to conventional RPK model when run with elasticity to produce `rpk_no_elast` instead of `RPK`).
- **`4cdf025d`** — Test config and GUI updated.
- **`f089a850`** — Basic notebooks updated with new output names and values; consistent across the suite (minor evolutions due to naming changes and the more correct COVID growth-rate computation).
- **`4e36e982`** — Simplified freight efficiency model that works with efficiency gains; outputs audited and documented in §3.5.1. `markets.yaml` `default.freight` extended with simplified efficiency parameters.
- **`d8044960`** — **Legacy monolithic classes removed**: deleted `aeromaps/models/air_transport/air_traffic/rpk.py` (622 lines), `rtk.py` (237 lines), `ask.py` (94 lines), and the legacy class in `load_factor.py`. Per-market entries pruned from [parameters.json](aeromaps/resources/data/parameters.json) (~80 lines removed). Pre-removal snapshot kept in [parameters_phase5_removed_reference.json](aeromaps/resources/data/parameters_phase5_removed_reference.json) for reference.
- **`5ef43e2d`** — Reference outputs regenerated across all tutorials. `freight_energy_share_2019` added as partitioning input since it is no longer in `parameters.yaml`. `HANDOFF_PHASE5_MARKETS_YAML.md` retired.
- **`d0cc26d3`** — Custom markets tutorial notebook brought up to date (data folder, config, custom `markets.yaml` / `fleet.yaml` / `aircraft_inventory.yaml`).
- **`183b3867`** — Voila notebook GUI (`graphical_user_interface.py`) migrated to market-prefixed parameter names (~73/-159 lines): renamed 68 active legacy parameter writes (`cagr_passenger_<range>_*` → `<range>_cagr_*`, `rpk_<range>_measures_*` → `<range>_measures_*`, `energy_per_ask_<range>_dropin_fuel_gain` → `<range>_energy_per_ask_dropin_fuel_gain`, `hydrogen_final_market_share_<range>` → `<range>_hydrogen_final_market_share`, `hydrogen_introduction_year_<range>` → `<range>_hydrogen_introduction_year`); applied the 1-to-3 split for `load_factor_end_year`; deleted commented-out widget dead code (`w_growth_*_range_percent`, `w_grouped_market`, the `if self.w_grouped_market.value` branching). Fleet preset writes via `process.fleet.categories["..."]` left as-is (display-name based; resolves to default 4 markets).

**Known caveats:**
- `data_information.csv` — not yet audited/updated. Filed as Phase 5 follow-up (or Phase 6 if GUI displays it).
- New "Defining your own markets" tutorial is now `tutorials/12_custom_markets_and_fleet/` per `d0cc26d3`. Title/index entry kept consistent with surrounding tutorials.

**Exit:** test suite green, single source of truth, no legacy compatibility shims, no remaining `PHASE-5-CLEANUP` markers in live model code.

### Phase 6 — Plots & GUI 🚧 *(WIP — GUI rename done; plot fixes in progress)*

**GUI** — completed in `183b3867` as part of Phase 5 cleanup (see above). All 68 active legacy parameter writes renamed; commented-out widget dead code deleted; `load_factor_end_year` global→per-market split applied at the two write sites. Scope: rename-only, keeping the 3-range UX for the default 4-market scenario. Fleet preset writes left as-is.

**Plots** — partial; resumed after merging `main` into `fleet-refactoring` (merge commit `303572d3`). The merge brought in a heavily restructured `aeromaps/plots/` tree (`single_scenario/` + `multi_scenario/` subdirs) and surfaced both stale legacy names and a separate pre-existing breakage from `main`.

Landed post-merge:

- **`31ca06cc`** — `aeromaps/tests/plots/test_multi_scenario_plots.py`: renamed legacy CAGR fixture parameters (`cagr_passenger_<range>_*`, `cagr_freight_*` → `<range>_cagr_*`, `freight_cagr_*`).
- **`68ab090b`** — `aeromaps/tests/core/test_process.py`: renamed `cagr_freight_reference_periods_values` → `freight_cagr_reference_periods_values`; dropped a pre-existing unused `os` import.
- **`0c70c3d8`** — **Prep:** revert of a broken rework of `aeromaps/plots/single_scenario/macc.py` introduced by `f3bb79d1` (on `main` lineage). That commit had (a) duplicated `class ShadowCarbonPrice` so two class objects bound the same module name (Python silently used the second — first 387 lines became dead), and (b) rewrote `ScenarioMACC.update()` with code referencing undefined names (`cumwidths_pos`, `maccneg_df`) — would `NameError` at runtime. This commit deletes the dead duplicate and restores `ScenarioMACC.update()` to the pre-`f3bb79d1` working body. ruff dropped from 12 errors to 0.
- **`44a33840`** — MACC aircraft bar colors now driven by `market_id` instead of display name. Module-level `_MARKET_AIRCRAFT_COLORS = {"short_range": "gold", "medium_range": "goldenrod", "long_range": "darkgoldenrod"}` + `_aircraft_color()` helper, falling back to `tab:gray` for custom markets. Replaces five `if category == "Short Range"` chains. Default 4-market scenario behavior unchanged.
- **`f2700625`** — **Prep:** fix pre-existing lint errors in `aeromaps/plots/single_scenario/costs.py` (a broken `AirfareEvolutionBreakdown._update_plot_elements` that referenced an out-of-scope `data` parameter — leftover from the pre-`d37cf7d7` `def update(self, data)` shape; 4 unused imports).
- **`23b1f9da`** — `DOCEvolutionCategory` rewritten to iterate `process.markets.get(traffic_type="passenger")` × the carrier table from `direct_operating_costs.py` (`dropin_fuel`, `hydrogen`, `electric`). Replaces 9 hard-coded `self.line_<sr|mr|lr><di|h|e>` attributes with a nested `self.lines[market_id][energy_type]` dict, and the static `required_outputs` with one computed from `MarketManager` in `__init__`. Default 4-market output identical; custom-market scenarios now plot correctly with no code change.

**Investigation outcomes (no code change needed):**
- `aeromaps/plots/multi_scenario/intensities.py` — only docstrings mention "freight"; correct prose.
- `aeromaps/plots/single_scenario/indicators.py` — `FreightKayaFactorsPlot` uses `co2_emissions_freight`, still emitted by `co2_emissions.py` as the freight-traffic-type aggregate.
- `aeromaps/plots/single_scenario/macc.py` — the remaining `*_freight_dropin/hydrogen/electric` references are aggregates across the freight traffic_type (emitted by `fleet_abatement_cost.py` / `operations_abatement_cost.py`), not "the freight market"; still authoritative.
- `tests/test_fleet_*.py` — `short_range`/`medium_range`/`long_range` references in these files are market IDs of the default markets, not legacy names; no action.
- `aeromaps/resources/data/outputs.json` — last touched 2025-07-04; stale snapshot only written when a user explicitly calls `process.write_json()`. No regeneration on each run; user-refreshable when desired.

**Still deferred (Phase 6 follow-up):**
- Audit single_scenario / multi_scenario plots for any remaining hard-coded `<range>`-suffixed outputs that should iterate `MarketManager` (e.g. anything stacked or split per passenger market beyond the DOC plot).
- Decide whether the GUI should expose a "custom markets" mode beyond the 3-range default layout, or stay pinned to default markets.
- `data_information.csv` audit (carried over from Phase 5).

## 7. Risks

| # | Risk | Mitigation |
|---|------|------------|
| 1 | GEMSEO dynamic grammar with custom wrapper | Phase 2 spike (first chantier): prototype `RPK` end-to-end with `AeroMAPSCustomModelWrapper` — confirms grammar before rolling to the rest |
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
| Registry class named `MarketManager` (not `MarketRegistry`) | Matches existing `EnergyCarrierManager` sibling in the codebase |
| Market-as-prefix flattened names (`<market>_<leaf>`) | Chosen 2026-04-24 after Phase 1 review: simplest to emit from the generic flattener; legacy `parameters.json` inconsistency (prefix/infix/suffix) was a strong signal to standardise. Downstream models rename during Phase 2/4 |
| Sub-group keys dropped by flattener; ambiguous leaves carry group name in YAML | Keeps the flattener trivial; documentation stays close to the data (`measures_start_year` self-describes) |
| COVID promoted to per-market | Enables regional COVID profiles; cost is trivial since YAML authoring supports repetition. Legacy global COVID names coexist until Phase 2 rewires them |

## 10. PR scope (2026-05-26)

This branch (`fleet-refactoring`) is ready to PR against `main`. Captured here so the scope doesn't drift.

### In scope for the PR

- Phases 0–5 in full (data model, process integration, air-traffic disciplines, fleet model, downstream impacts via `AeroMAPSCustomModelWrapper`, legacy class removal, `parameters.json` pruning, tutorial notebooks, reference outputs).
- Phase 6 — GUI rename pass (`183b3867`) and the post-merge plot fixes (`31ca06cc`, `68ab090b`, `0c70c3d8`, `44a33840`, `f2700625`, `23b1f9da`).
- **`macc.py` fix carries to `main` via this PR.** The broken state on `main` (duplicate `ShadowCarbonPrice` + undefined names in `ScenarioMACC.update()`) was introduced by `f3bb79d1` on the `main` lineage and surfaced when `main` was merged into this branch. Reverted in `0c70c3d8` here; treat that commit as the canonical version when the PR lands. Worth flagging in the PR description so reviewers don't re-introduce the duplicate class during conflict resolution.

### Explicitly out of scope (deferred or excluded)

- **Phase Interface** ("Custom Markets × Multi-Regions" demo, chantiers A–F) — separate PR. The schema extensions, linear-RPK growth model, share-decoupling, and Excel→YAML generator land independently.
- **Prep D** (unify 1/2/3+ subcategory branching in `_compute_single_aircraft_share`) — not implemented; risk vs. payoff judged not worth it. The current 1/2/3+ branching is fine for the foreseeable market shapes.
- **`MarketManager` validators** (`traffic_type` / `traffic_unit` whitelist, `fleet.yaml` cross-check, subcategory share sum) — not essential; can be added on demand if a real misconfiguration causes a confusing failure.
- **`data_information.csv` audit** — severely outdated and worth a dedicated pass; will be filed as a separate issue rather than diagnosed here.

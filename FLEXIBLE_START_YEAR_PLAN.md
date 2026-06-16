# Plan — Make `prospection_start_year` flexible (code-only)

**Status :** Draft | **Updated :** 2026-05-28

## Context

Today, `prospection_start_year = 2020` is effectively hard-coded throughout the engine via repeated `.loc[2019]`, `.loc[2020]` and `(k - 2019)` constructs, plus parameter names like `*_2019` / `*_2020`. The user wants to be able to change `prospection_start_year` (e.g. to 2025) and have the simulation still run, **without** changing the other bounds (`historic_start_year=2000`, `climate_historic_start_year=1940`, `end_year=2050`).

Scope decisions (confirmed in plan-mode dialog):
- **Code-only flex.** Defaults stay at 2020. The user opts in by supplying their own JSON/YAML with extended `*_init` vectors and updated reference scalars. No new default data shipped.
- **Renaming.** `*_2019` parameters (encoding the pivot year in the name) get renamed to **`*_last_historical_year`**, with backward-compat aliases so existing user JSONs still load. (`_last_historical_year` is preferred over `_reference` to avoid clashing with the existing `_reference_periods` interpolation suffix already used across the codebase.)
- **COVID 2020 patches.** When `2020 < prospection_start_year`, the `.loc[2020] = …` patches are skipped silently. User-provided historic `*_init` data is expected to already reflect the observed 2020 drop.
- **Climate scope.** Generalize the `co2_emissions.loc[2019]` pivot in `carbon_offset.py`. Do **not** touch the climate historical CSV ([temperature_historical_dataset.csv](aeromaps/resources/climate_data/temperature_historical_dataset.csv)); the user extends it on their side if needed.

## Approach

Centralize the notion of "last historical year" = `prospection_start_year - 1` in one place, then mechanically replace the literal `2019` (pivot reads / quadratic anchor) and `2020` (COVID patches) across the models.

Three categories of change:
1. **Last-historical-year reads** (`.loc[2019]`, `(k - 2019)`) → expressed in terms of `prospection_start_year - 1`.
2. **COVID 2020 patches** (`.loc[2020, …] = …`) → wrapped in `if self.prospection_start_year <= 2020` so they become no-ops for later starts.
3. **`*_2019`-named parameters** (in `parameters.json` / `markets.yaml`) → renamed to `*_last_historical_year`, with a compatibility shim that reads either old or new name.

A length-validation guard is added at input load so users with mismatched `*_init` length get a clear error rather than an obscure pandas exception.

## Phases

### Phase A — Centralize the "last historical year" (single source of truth)

Add a derived attribute that every model can read uniformly.

- **[aeromaps/core/process.py](aeromaps/core/process.py)** — in `_initialize_years` (around line 1561), already builds the year ranges generically. No change needed here, but expose a convenience in the same hook:
  - In `_initialize_inputs` (around line 1605), after `Parameters` is loaded, set `self.parameters.last_historical_year = self.parameters.prospection_start_year - 1`.
- **[aeromaps/models/base.py](aeromaps/models/base.py)** — `AeroMAPSModel` already propagates `prospection_start_year`, `historic_start_year`, `end_year` (see line ~118). Add `self.last_historical_year` alongside, derived from `prospection_start_year - 1`. Every model can then use `self.last_historical_year` instead of literal `2019`.

This is **the** anchor used by Phases B–D.

### Phase B — Replace last-historical-year reads (`.loc[2019]`, `(k - 2019)`)

Mechanical substitution: `2019` → `self.last_historical_year` everywhere it means "last historic year / calibration anchor". Narrowed to non-COVID occurrences:

| File | What changes |
|------|---------------|
| [aeromaps/models/air_transport/aircraft_fleet_and_operations/load_factor/load_factor.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/load_factor/load_factor.py) | `load_factor_2019 = self.df.loc[2019, col]` → `… self.df.loc[self.last_historical_year, col]`. Quadratic `a * (k-2019)**2 + b * (k-2019) + load_factor_2019` → use `self.last_historical_year`. Rename local var `load_factor_2019` → `load_factor_lhy` (or similar). Same in `_parameters_load_factor_model` (replace literal `2019` with a parameter). |
| [aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py) | All `.loc[2019, …]` reads (lines ~160, ~511, ~891, ~1129) → `.loc[self.last_historical_year, …]`. Same for any `(k - 2019)` patterns. |
| [aeromaps/models/impacts/emissions/carbon_offset.py](aeromaps/models/impacts/emissions/carbon_offset.py) | `co2_emissions.loc[2019]` (lines 74, 80) → `co2_emissions.loc[self.last_historical_year]`. The DataFrame column name `carbon_offset_baseline_level_vs_2019` and the parameter names `carbon_offset_baseline_level_vs_2019_*` are handled in Phase D. |
| [aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py) | The `_calibrate_reference_aircraft` energy-per-ASK calibration block (around lines 914-921) uses `energy_consumption_init.loc[2019]` / `ask_init.loc[2019]` → `self.last_historical_year`. |
| [aeromaps/models/impacts/costs/efficiency_abatement_cost/fleet_abatement_cost.py](aeromaps/models/impacts/costs/efficiency_abatement_cost/fleet_abatement_cost.py) | Same pattern — `.loc[2019]` reads (lines 118, 121) → `self.last_historical_year`. |
| [aeromaps/models/air_transport/air_traffic/rpk.py](aeromaps/models/air_transport/air_traffic/rpk.py), [price_elasticity.py](aeromaps/models/air_transport/air_traffic/price_elasticity.py), [short_range_distribution.py](aeromaps/models/air_transport/air_traffic/short_range_distribution.py), [carbon_budget.py](aeromaps/models/sustainability_assessment/climate/carbon_budget.py) | Sweep for any remaining `2019` literals and apply the same substitution. |

`short_range_distribution.py:80` (`reference_years = [2019, 2030, 2040, end_year]`) — replace `2019` with `self.last_historical_year`; leave the intermediate waypoints alone.

### Phase C — Make COVID 2020 patches conditional

Three patches today unconditionally overwrite year 2020. Each must become a no-op when 2020 is no longer in the prospective window.

Pattern to apply in every site:
```python
if self.prospection_start_year <= 2020:
    self.df.loc[2020, col] = …  # COVID override
```

Sites:
- [load_factor.py:110](aeromaps/models/air_transport/aircraft_fleet_and_operations/load_factor/load_factor.py#L110) — `self.df.loc[2020, col] = covid_2020`.
- [aircraft_efficiency.py:160](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py#L160), [:511](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py#L511), [:891](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py#L891), [:1129](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py#L1129) — `self.df.loc[2020, …] = self.df.loc[2019, …] * (1 + covid_increase/100)` (the `2019` read is already covered by Phase B; just wrap in the guard).

The parameter names `covid_load_factor_2020`, `covid_energy_intensity_per_ask_increase_2020`, `covid_energy_intensity_per_rtk_increase_2020` are **kept as-is** — they really do describe a 2020 event, not a generic pivot. They remain in `markets.yaml` / `parameters.json` and are simply ignored when the guard short-circuits.

### Phase D — Rename `*_2019` parameters

Rename parameters whose `_2019` suffix encodes "last historical year" (not a real-world 2019 event). **No backward-compat aliases** — old configs are made to fail loudly via the rename guard (Phase E), not silently copied onto the new name.

Renames:

| Old name | New name |
|----------|----------|
| `world_co2_emissions_2019` | `world_co2_emissions_last_historical_year` |
| `carbon_offset_baseline_level_vs_2019_reference_periods` | `carbon_offset_baseline_level_vs_last_historical_year_reference_periods` |
| `carbon_offset_baseline_level_vs_2019_reference_periods_values` | `carbon_offset_baseline_level_vs_last_historical_year_reference_periods_values` |
| (column) `carbon_offset_baseline_level_vs_2019` | `carbon_offset_baseline_level_vs_last_historical_year` |
| `<mid>_rpk_share_2019` (markets.yaml) | `<mid>_rpk_share_last_historical_year` |
| `<mid>_energy_share_2019` (markets.yaml) | `<mid>_energy_share_last_historical_year` |
| `freight_energy_share_2019` | `freight_energy_share_last_historical_year` |
| `gdp_per_capita_2019` (elasticity models) | `gdp_per_capita_last_historical_year` |
| `total_seats_2019` (partitioning helper arg) | `total_seats_last_historical_year` |

> **Why no alias shim.** The input loader ([parameters.py:38](aeromaps/models/parameters.py#L38) `from_dict`) blindly `setattr`s every JSON/YAML key with no unknown-key validation, and models read these names with hard accesses against a default-populated `input_names`. So a bare rename would make a stale `_2019` key resolve silently to its default (e.g. share → 0%, or a NaN cascade) — wrong numbers, no crash. The Phase E guard converts that into a loud, self-documenting error instead. (Decision: Tier 1 raise-guard over a perpetual alias dict — same line count, no false-positive surface, no allowlist to maintain.)

Files touched by the rename (consumer side):
- [aeromaps/resources/data/parameters.json](aeromaps/resources/data/parameters.json) — rename keys.
- [aeromaps/resources/data/default_markets/markets.yaml](aeromaps/resources/data/default_markets/markets.yaml) — rename `rpk_share_2019` / `energy_share_2019` leaves.
- [aeromaps/models/impacts/emissions/carbon_offset.py](aeromaps/models/impacts/emissions/carbon_offset.py) — update input names + column name.
- [aeromaps/utils/functions.py](aeromaps/utils/functions.py) `compute_partitioning` / `create_partitioning` — rename local vars and output JSON keys (`other_float_data` keys).
- Any model that reads `<mid>_rpk_share_2019` / `<mid>_energy_share_2019` (fleet_model.py, ask.py, the freight share computation). Sweep with grep over the codebase.

**COVID names are NOT renamed.** `covid_load_factor_2020`, `covid_energy_intensity_per_ask_increase_2020`, `covid_energy_intensity_per_rtk_increase_2020` describe a fixed historical event.

### Phase E — Input validation (rename guard + length check)

#### E1 — Renamed-input guard (replaces the alias shim)

Make stale `_2019` configs fail loudly instead of resolving to silent defaults. In [aeromaps/core/process.py](aeromaps/core/process.py), define two small tables near the top of the module:

```python
# TODO(flex-start-year): delete this guard once downstream configs are migrated
# and a release cycle has passed (target: remove after 2026-12, or once no
# in-repo config and no known external scenario still carries a `_2019` key).
RENAMED_INPUTS = {
    "world_co2_emissions_2019": "world_co2_emissions_last_historical_year",
    "carbon_offset_baseline_level_vs_2019_reference_periods":
        "carbon_offset_baseline_level_vs_last_historical_year_reference_periods",
    "carbon_offset_baseline_level_vs_2019_reference_periods_values":
        "carbon_offset_baseline_level_vs_last_historical_year_reference_periods_values",
    "freight_energy_share_2019": "freight_energy_share_last_historical_year",
    "gdp_per_capita_2019": "gdp_per_capita_last_historical_year",
}
RENAMED_INPUT_SUFFIXES = {  # matched against any `<mid>_…` flattened key
    "_rpk_share_2019": "_rpk_share_last_historical_year",
    "_energy_share_2019": "_energy_share_last_historical_year",
}
```

In `_initialize_inputs`, after each user surface is loaded but **before** it is applied, scan the *raw user-supplied keys* (the `merged_data` dict at [process.py:1700](aeromaps/core/process.py#L1700), the single-file path at [:1716](aeromaps/core/process.py#L1716), and the flattened `markets.yaml` leaves). For any key matching `RENAMED_INPUTS` or ending in a `RENAMED_INPUT_SUFFIXES` entry, raise a `ValueError` naming the old key and its replacement, e.g.:

```
ValueError: input 'short_range_rpk_share_2019' was renamed to
'short_range_rpk_share_last_historical_year' (prospection_start_year is now flexible).
Update your config — no backward-compat alias is provided.
```

Scan only the keys the user actually supplied (not `parameters.__dict__`), so derived/intermediate attributes can't false-positive. This catches exactly the rename breakage; it is **not** a general unknown-key validator (that was the rejected Tier 2 — revisit separately if config-typo safety is ever wanted).

#### E2 — Input-length validation

Add a clear error when `*_init` vector lengths don't match `prospection_start_year - historic_start_year`.

- [aeromaps/utils/functions.py](aeromaps/utils/functions.py) `_dict_from_parameters_dict` (lines 89-103) — before the `pd.Series(value, index=new_index)` call, check `len(value) == new_index.stop - new_index.start`. If not, raise a `ValueError` naming the offending key, the expected length (`prospection_start_year - historic_start_year`), the actual length, and a hint that the user must extend the vector to match.

Same check on the vector inputs path in [process.py:1716-1733](aeromaps/core/process.py#L1716) when an `other_vector_data` list mismatches its declared `years` index, but that path already uses an explicit `years` array so the mismatch is more visible.

### Phase F — Verification

1. **Smoke test the default (regression).** Run the `01_basic` tutorial (per the user's testing-scope preference — full notebook suite is opt-in only):
   ```bash
   cd aeromaps/notebooks/tutorials/01_run_a_basic_calculation
   python -c "from aeromaps.utils.functions import compare_json_files; \
              compare_json_files('./data/reference/outputs.json', './data/outputs.json', rtol=1e-6, atol=0)"
   ```
   Expectation: zero diff (we're only renaming + parameterizing — math unchanged for `prospection_start_year == 2020`).
2. **Run pytest** (`pytest aeromaps/`) to catch any model-level regressions.
3. **Custom-scenario smoke test.** Create a minimal config with `prospection_start_year=2025`, 25-element `*_init` vectors (e.g. extrapolated from 2019 + flat 2020-2024), updated `*_last_historical_year` scalars, and run `AeroMAPSProcess.compute()` to end-of-pipeline. Confirm:
   - No exceptions at load time (Phase E gate passes).
   - `load_factor.loc[2020]` is taken from the user's historic `rpk_init/ask_init`, not from `covid_load_factor_2020` (Phase C guard).
   - `carbon_offset_baseline_level_vs_last_historical_year.loc[2024]` is the offset baseline (Phase B/D).
4. **Rename-guard smoke test.** Feed a config carrying an old `_2019` key (e.g. `short_range_rpk_share_2019`) and confirm `AeroMAPSProcess` raises the Phase E1 `ValueError` naming the new key — i.e. the failure is loud, not silent. Then confirm the migrated config (new names) produces outputs identical to the pre-rename baseline.

## Critical files (modify list)

- [aeromaps/core/process.py](aeromaps/core/process.py) — `last_historical_year` derivation + renamed-input guard (Phase E1, marked for removal once configs migrate).
- [aeromaps/models/base.py](aeromaps/models/base.py) — propagate `self.last_historical_year` to all models.
- [aeromaps/models/air_transport/aircraft_fleet_and_operations/load_factor/load_factor.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/load_factor/load_factor.py) — pivot generalization + COVID guard.
- [aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py) — heaviest file (Phase B + C combined).
- [aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py) — calibration anchor.
- [aeromaps/models/impacts/emissions/carbon_offset.py](aeromaps/models/impacts/emissions/carbon_offset.py) — pivot generalization + name rename.
- [aeromaps/models/impacts/costs/efficiency_abatement_cost/fleet_abatement_cost.py](aeromaps/models/impacts/costs/efficiency_abatement_cost/fleet_abatement_cost.py) — `.loc[2019]` reads + COVID guard.
- [aeromaps/utils/functions.py](aeromaps/utils/functions.py) — length validation + `compute_partitioning` rename.
- [aeromaps/resources/data/parameters.json](aeromaps/resources/data/parameters.json), [aeromaps/resources/data/default_markets/markets.yaml](aeromaps/resources/data/default_markets/markets.yaml) — rename keys (with alias shim covering older user files).

## Open points to revisit during implementation

1. **Tutorial / publication notebooks.** Out of scope here; they keep their hard-coded year arrays unless the user later asks.
2. **Climate historical CSV extension.** Out of scope; the user supplies an extended CSV if they want `prospection_start_year > 2020` with climate models.

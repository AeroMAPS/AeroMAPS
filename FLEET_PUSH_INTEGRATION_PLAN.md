# Push fleet model — integration status

**Status:** Phases 1–6 done; review-driven simplification + growth-profile port applied;
Phase 7 dropped by decision. The push demo runs end-to-end. Only remaining: a full
`pytest aeromaps/` re-run (Phase 8). | **Updated:** 2026-06-30 | **Branch:** `fleet_paco_models`

---

## What it is

Paco's delivery-driven (**"push"**) fleet engine is the inverse of AeroMAPS' S-curve
bottom-up `FleetModel`: instead of assigning market shares from an S-curve, it drives the
fleet from aircraft **deliveries** and lets retirement + utilisation curves determine the
surviving fleet, then sums energy bottom-up. It is integrated as a **selectable
`AeroMAPSModel`** that emits the same downstream bridge as the other efficiency models and
also surfaces its native per-type fleet counts/deliveries — **coexisting** with the
top-down / bottom-up paths (those are untouched).

The engine is editable (the author is a colleague), so we made its I/O behave like a
conventional AeroMAPS model rather than wrapping a black box.

## How it's wired now

- **Engine** — [`fleet_model_push.py`](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model_push.py)
  `market_process()`: a pure, side-effect-free function. ASK is **always injected** (no
  internal CAGR); pivot/horizon come from `last_historical_year` / `end_year`; on
  infeasible demand it **raises `ValueError`** (legacy fail-loud — see notes).
- **Wrapper** — [`aircraft_efficiency_fleet_push.py`](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency_fleet_push.py)
  `PassengerAircraftEfficiencyFleetPush` (`model_type="custom"`): exposes `self.markets` +
  `custom_setup()` (so `process.py` injects `MarketManager` and calls setup), loads the
  static inputs once (`_load_push_engine_inputs`, `lru_cache`), runs the engine per segment
  with `ask_{mid}` injected, and emits the **efficiency bridge (a)** + **fleet bridge (b)**.
  It caches the per-segment age-resolved engine arrays in `self._engine_results` and exposes
  a **`plot()`** method (mirrors `FleetModel.plot()`).
- **Plots** — [`fleet_model_push_visualisations.py`](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model_push_visualisations.py):
  pure matplotlib helpers (`visu_fleet_array`, `visu_retirements_array`,
  `visu_retirement_age`, `visu_energy_intensity`) called by `plot()`. Not in the
  `SingleScenarioPlot` registry — the retirement/age charts need the engine's internal
  `(periods, age, type)` arrays that the flat output columns sum away.
- **Selection** — `models_efficiency_push` dict in [`core/models.py`](aeromaps/core/models.py)
  (mirrors `models_efficiency_top_down`, swaps in the push passenger-efficiency entry).
- **Markets + growth** — [`default_markets/markets_push.yaml`](aeromaps/resources/data/default_markets/markets_push.yaml):
  TP/RJ/NB/WB as passenger markets (+ freight), 2024 RPK/energy shares from the calibration
  Excel, and each segment's **growth profile** (`inputs.growth.cagr_reference_periods[_values]`)
  ported from the legacy engine — so the AeroMAPS demand chain injects the ASK trajectory the
  fleet was calibrated against.

### Bridge contract (what the wrapper emits)
**(a) Efficiency bridge** — mirrors `PassengerAircraftEfficiencySimpleShares`, per passenger
market `mid` and energy type `et`: `energy_per_ask_without_operations_{mid}_{et}` (MJ/ASK,
full `[historic_start_year, end_year]`) and `ask_{mid}_{et}_share`. **Drop-in only:**
`dropin_fuel` carries 100 %; `hydrogen`/`electric` shares are 0 and their energy columns
mirror drop-in so downstream relative-intensity reads stay finite. History (≤ pivot) is
spliced exactly like `SimpleShares`.

**(b) Fleet bridge** — mirrors `SimpleFleetCount`: `"{market.name}: Aircraft In Fleet"`
(per-segment total), `{mid}:{type}:aircraft_in_fleet` (per-type count), and
`{mid}:{type}:aircraft_deliveries` (per-type deliveries — the push model's distinguishing
state).

## Locked decisions

1. **Segments = AeroMAPS markets.** TP/RJ/NB/WB are passenger markets; AeroMAPS demand runs
   per segment. Freight stays on the simple/separate efficiency path.
2. **Input layer = hybrid.** Per-type calibration Excel kept as static reference (loaded once);
   scenario knobs (age sensibilities, new-aircraft cards, in-production profiles) are
   YAML/GEMSEO inputs. Full Excel→YAML migration deferred.
3. **ASK injected from AeroMAPS**, always — the engine has no internal growth profile.
4. **Coexist, not replace** — additive `models_efficiency_push`; default paths untouched.
5. **Output scope = bridge + fleet** (drop-in only; H2/electric and bottom-up cost tier out of v1).
6. ~~Keep a standalone demo.~~ **Reversed** — no standalone path; the engine runs only as the
   `AeroMAPSModel`. Exercise it via the process + `model.plot()`.
7. **Capacity guard stays a `raise`** ("we don't care if it fails the sim"). Phase 7
   robustness/softening is therefore dropped.
8. **Plots as a model `.plot()` method**, not registry plots (mirrors `FleetModel.plot()`).
9. **Growth lives in the markets config**, not the engine. `default_market_param.yaml` keeps
   only the age sensibilities.

## Key technical notes (the non-obvious bits)

- **Engine year-alignment trap.** With the injected `ask_series` (length `modeled_periods+1`,
  indexed `[pivot … horizon]`), `ask_volumes[t]` / `aircraft_seats_volumes[t]` ↔ year
  `pivot + t` (t=0 = pivot); `deliveries[k]` ↔ year `pivot + 1 + k`. The engine's returned
  `years` axis is **off-by-one and not used**. The wrapper sets horizon = `end_year + 1` and
  builds the engine's production-profile axis directly from `[last_historical_year+1 … end_year+1]`.
  Per-type count = `aircraft_seats_volumes[t].sum(axis=0) / seats_array`.
- **2024 pivot is mandatory.** The fleet Excel columns are 1980→2024, so the historical fleet
  axis only aligns when pivot = 2024. `custom_setup` hard-guards `last_historical_year == 2024`
  (i.e. `prospection_start_year == 2025`).
- **Growth-profile port + leveling anchoring.** The legacy per-segment `reference_growth` was
  moved into `markets_push.yaml` as `cagr_reference_periods[_values]`. Two conversion gotchas:
  AeroMAPS `aeromaps_leveling_function` anchors a value **from** its breakpoint whereas Paco
  anchored it **up to** the breakpoint (so periods shift +1y and the last must land on
  `end_year`); and AeroMAPS rates are **percent** (Paco used fractions, ×100). Verified: the
  resulting per-year `annual_growth_rate_rpk_{mid}` matches Paco's rates exactly.
- **The former TP-2029 raise is resolved.** It was never an engine bug: the flat-3 % default
  demand grew TP past its calibrated capacity right before `new_gen_TP`'s 2030 EIS, tripping
  the *pre-loop* guard (the convergence loop itself still met demand via temporary-parking
  compensation). Porting the real profile (TP flat to 2035) removes the overtake, so the
  calibrated demo runs clean. The `raise` is still armed — it's just not tripped.
- **MDA caveat.** Because the guard `raise`s, a transient infeasible ASK during an MDA
  iteration with feedback would abort the whole solve. Latent only — the demo runs feed-forward.

## Commit history

Baseline = annotated tag **`push-integration-start`**; every commit is prefixed
`push-integ:` (`git log --grep '^push-integ' --oneline`).

| Commit | What it did |
|---|---|
| `1efbc824` | **Phase 1.** `markets_push.yaml` (TP/RJ/NB/WB + freight); 2024 shares Excel-sourced via `generate_push_markets.py`. |
| `47cd19a2` | **Phase 2.** Pure, ASK-injectable, calendar-parametrized `market_process`. |
| `725924a3` | **Phases 3–4.** Wrapper + `models_efficiency_push`; drop-in efficiency bridge. |
| `740aa3b8` | 2024-pivot guard + self-contained demo notebook. |
| `d3ddc836` | **Phase 5.** Fleet-count & deliveries outputs (+ interim registry plots, later removed). |
| `db806b07` | **Review simplification.** Single injected-ASK path; rename wrapper; restore legacy `raise`; plots → `model.plot()`. |
| `a0874813` | Drop engine debug print; fix demo notebook nested model lookup. |
| `1a979a5c` | **Growth port.** Legacy profiles → markets config; decouple engine from `reference_growth`; demo `end_year` 2050→2070. Resolves the TP-2029 raise. |

## Remaining

- **Phase 8** — full `pytest aeromaps/` + confirm zero regression on default paths. (Last
  full run: 126 passed before the plot consolidation; `test_single_scenario_plots.py` 63
  passed after. A full re-run is still owed.) The push demo itself is verified end-to-end:
  `compute()` runs to 2070 without raising, growth rates match Paco's, `model.plot()` renders
  the full per-segment chart set.

## How to run / inspect

- Demo: [`push_fleet_model.ipynb`](aeromaps/notebooks/custom_workflow/push_fleet_model/push_fleet_model.ipynb)
  (`data/config_push_2025.yaml` → `markets_push.yaml` + `models_efficiency_push`, pivot 2025,
  `end_year` 2070). Prints per-segment energy/ASK + fleet-count tables, calls `model.plot()`,
  and demonstrates the 2024-pivot guard.
- In any config: `models.standards: [..., models_efficiency_push]` +
  `models.markets.markets_data_file: default_markets/markets_push.yaml`, with a **2025-pivot**
  scenario (historic `*_init` vectors over 2000–2024, e.g. tutorial-13's `inputs_2025.json`).

## Dev note (this sandbox)

Committing `.ipynb` needs a filter override — the local `filter.nbstripout.clean` points to a
missing conda python. Strip first (`poetry run python -m nbstripout <nb>`) and commit with
`git -c filter.nbstripout.clean="$POETRY_PY -m nbstripout" …`. Ruff also lints notebook cells.

## Later (out of v1 scope)

- **Energy types** — add H2/electric to the inventory + split `et` shares (today drop-in only).
- **Full Excel→YAML migration** — fold the static calibration Excel into config / a regenerable generator.
- **Bottom-up cost tier** — feed the `:aircraft_share` second tier (consumed by `FleetEvolution`)
  from per-type deliveries, plus the cost/non-CO₂ bridges, if the push model is ever used with
  the bottom-up cost path.

## Critical files

- [`fleet_model_push.py`](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model_push.py) — pure engine (`market_process`): ASK injected, calendar un-hardcoded, legacy `raise`. No standalone path.
- [`fleet_model_push_calculations.py`](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model_push_calculations.py) — `fleet_content` / solver helpers (unchanged).
- [`fleet_model_push_visualisations.py`](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model_push_visualisations.py) — matplotlib helpers for `plot()`.
- [`aircraft_efficiency_fleet_push.py`](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency_fleet_push.py) — the wrapper: bridges, engine-array cache, `plot()`.
- [`core/models.py`](aeromaps/core/models.py) — `models_efficiency_push`.
- [`core/process.py`](aeromaps/core/process.py#L1614) — custom wiring (`markets` + `custom_setup`); no change needed.
- [`default_markets/markets_push.yaml`](aeromaps/resources/data/default_markets/markets_push.yaml) — push markets profile + per-segment growth.
- [`default_fleet_push/*.yaml`](aeromaps/resources/data/default_fleet_push/) + calibration Excel — engine inputs (`default_market_param.yaml` now holds only age sensibilities).

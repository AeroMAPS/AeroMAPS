# Plan — Finalize the integration of Paco's "push" fleet model

**Status :** Active | **Updated :** 2026-06-29 | **Branch cible :** `fleet_paco_models`

## Context

Paco's delivery-driven ("push") fleet-renewal engine is the inverse of AeroMAPS'
existing S-curve bottom-up `FleetModel`: instead of assigning market shares from an
S-curve, it drives the fleet from aircraft **deliveries** and lets retirement +
utilisation curves determine the surviving fleet, then sums energy bottom-up.
Today `market_process` is still a standalone-style routine (Excel I/O, prints,
matplotlib, `raise` on infeasible demand). The goal is to turn it into a selectable
`AeroMAPSModel` that emits the same downstream bridge as the other efficiency
models **and** surfaces its native per-type fleet counts/deliveries, **coexisting**
with the bottom-up path (decision locked — see [[fleet-push-integration]]).

**The model itself is editable** (the author is a colleague). We use that latitude
to make its inputs/outputs behave like a conventional AeroMAPS model rather than
wrapping a black box: `market_process` is refactored into a pure, side-effect-free
engine, and the input layer is partially migrated to AeroMAPS config (see Decision
#2 / #5 below).

### Where things stand on the branches (changed since the first draft)

The original draft targeted `custom_workflow` and treated "land the push code there"
as Phase 0. **That is now inverted.** Current topology:

- **`fleet_paco_models` (HOME — current branch)** carries **all three** workstreams:
  the push engine (`fleet_model_push*.py` + `resources/data/default_fleet_push/*.yaml`
  + calibration Excel), the markets system (`MarketManager`, `default_markets/markets.yaml`),
  and flexible start year (`last_historical_year`). It is +203 vs `main` and fully
  contains `main`. **It has cherry-picked every custom_workflow module the integration
  needs.**
- **`custom_workflow`** has markets + flex-start but **none of the push code** (only
  this plan doc). The two branches diverge (`custom_workflow` +24 / `fleet_paco_models`
  +26), with recent load-factor + "dummy pax/freight market" notebook work on
  `custom_workflow`.

So **Phase 0 is reconciliation, not landing** (see below). All integration work lands
on `fleet_paco_models`.

### Two completed workstreams that de-risk this (both present on the home branch)

1. **Flexible `prospection_start_year`** — `AeroMAPSModel.last_historical_year` is a
   first-class attribute and `*_2019` inputs were renamed `*_last_historical_year`.
   This is what lets Paco's engine legitimately pivot on **2024** (its Excel
   calibration year) instead of forcing a 2020 COVID pivot: a scenario with
   `prospection_start_year = 2025` reads its pivot from `last_historical_year`.
   **The engine must stop hard-coding 2024/2025 and read these attributes** (Phase 2).
2. **Markets / Phase Interface** (`MarketManager`, Excel→inputs generator,
   share-decoupling mode, time-varying `ask_year`). This established (a) the
   **custom-model wiring contract** in `process.py` — any model exposing both a
   `self.markets` attribute and a `custom_setup()` method gets `MarketManager`
   injected and `custom_setup()` called
   ([process.py custom wiring](aeromaps/core/process.py#L1614)); (b) the exact
   **bridge contract** the push wrapper must emit; (c) the **Excel→YAML generator
   pattern** we reuse for sourcing Paco's per-segment inputs.

### Locked decisions (recap + 2026-06-29 confirmations)

1. **Segments = AeroMAPS markets.** Paco's TP/RJ/NB/WB become passenger markets via a
   new `markets.yaml` profile; **AeroMAPS demand (RPK growth/elasticity) runs per
   segment**. Freight kept separate (passenger push is class-partitioned; freight stays
   on the simple/separate efficiency path — consistent with the recent "dummy
   pax/freight market" isolation).
2. **Input layer = Hybrid** *(confirmed 2026-06-29)*. Keep the per-type **calibration
   Excel as static reference**, loaded once in `custom_setup` (historical 2024 fleet:
   per-type ASK/MJ/distance/seats + fleet counts). Expose the **scenario knobs as
   YAML/GEMSEO inputs** (per-segment age sensitivities; new-aircraft cards: EIS,
   efficiency, seats, renewal rate, time-to-market; in-production production profiles).
   ASK is injected from AeroMAPS (Decision #3). Full Excel→YAML migration is deferred
   to "Later".
3. **ASK injected from AeroMAPS** from v1; drop Paco's internal CAGR growth profile.
4. **Coexist, not replace** — a new `models_efficiency_push` dict in `core/models.py`.
5. **Output scope = bridge + fleet** *(confirmed 2026-06-29)*. v1 emits the per-segment
   energy/ASK bridge (drop-in only) **and** the push model's native per-type/per-segment
   **fleet counts + deliveries** as AeroMAPS outputs (mirroring `SimpleFleetCount`'s
   naming). H2/electric and the bottom-up cost tier stay out of v1.
6. **Keep the standalone demo** (`python fleet_model_push.py`) working behind a flag, so
   the colleague can still exercise the engine with its own CAGR + Excel + matplotlib.

### Bridge contract — what the wrapper must emit

**(a) Efficiency bridge** — mirrors `PassengerAircraftEfficiencySimpleShares` /
`PassengerAircraftEfficiencyComplex`
([aircraft_efficiency.py:99-102](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py#L99)):
per passenger market `mid` and energy type `et`:
- `energy_per_ask_without_operations_{mid}_{et}` — MJ/ASK series (full
  `[historic_start_year, end_year]` index).
- `ask_{mid}_{et}_share` — % ASK split by energy type.

v1 is **drop-in only**: `et = dropin_fuel` carries 100 %, `hydrogen`/`electric`
shares are 0 and their `energy_per_ask` columns mirror drop-in so downstream
relative-intensity reads stay finite.

**(b) Fleet bridge** (Decision #5) — mirrors `SimpleFleetCount`
([fleet_numeric.py:326-329](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_numeric.py#L326)):
- `"{market.name}: Aircraft In Fleet"` — per-segment total fleet count series.
- `aircraft_in_fleet_value_dict` — per-type fleet counts keyed by aircraft name.
- per-type **deliveries** series (new output; the push model's distinguishing state).

## Tracking the integration work

Real integration work starts at the annotated tag **`push-integration-start`** (placed
on the commit that carries this refreshed plan). Everything after it is the push
integration:

- `git log push-integration-start..HEAD` — enumerate all integration commits since the
  baseline.
- Every integration commit is prefixed **`push-integ:`** → list them with
  `git log --grep '^push-integ'`.

## Current state & blockers

The push code is already co-located with markets + flex-start on the home branch, so
the remaining work is **wiring + de-side-effecting the engine**, not porting:

- **`market_process` has side effects.** It prints (`temporary aircraft parking`,
  `reso bug`, `Computing fleet composition…`), holds the `raise ValueError("not enough
  aircraft…")` capacity guard, and `fleet_process` drives matplotlib. The engine must
  become a **pure function** (arrays in, arrays out) so `compute()` can call it and the
  standalone demo keeps the I/O/plots.
- **ASK is not yet injected.** `market_process(total_asks, …)` takes `total_asks` as a
  single base-year scalar and grows it internally
  (`yearly_traffic = total_asks * np.exp(growth_rates_cum)`,
  [fleet_model_push.py:291-297](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model_push.py#L291)).
  Decision #3 replaces this with the AeroMAPS-provided per-segment ASK series.
- **Pivot/horizon hard-coded to 2024/2025.** `growth_rates = (market_growth[0][0] -
  2024) * …`, `years = np.arange(2025, market_growth[0][-1] + 1)`,
  `eis = (delivery_params[ac,0] - 2025)`
  ([fleet_model_push.py:291-298,363](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model_push.py#L291)),
  and Excel `*_2024` columns. Must be aligned to `last_historical_year` (pivot) and
  `[prospection_start_year, end_year]`; history spliced over
  `[historic_start_year, last_historical_year]`.
- **Inputs are Excel + bespoke YAML.** Three Excel files
  (`aircraft_type_key_parameters.xlsx`, `agg_fleet_end_2024.xlsx`,
  `other_parameters.xlsx`) + four `default_fleet_push/*.yaml`. Per Decision #2 the
  scenario YAMLs become AeroMAPS config/GEMSEO inputs; the calibration Excel stays as
  static reference loaded once in `custom_setup`.
- **Capacity guard aborts the solve.** `raise ValueError` / `print('temporary aircraft
  parking')` in the convergence loop is an MDA-robustness risk under feedback.

## Phases

### Phase 0 — Reconcile the home branch

`fleet_paco_models` is the integration home and already carries push + markets +
flex-start.

- Reconcile `custom_workflow`'s recent work (load-factor model, "dummy pax/freight
  market" notebook) into `fleet_paco_models` as needed (user-driven cherry-pick/merge).
- Re-confirm clean import (no Excel/matplotlib side effects on import — the `__main__`
  guard is already in place) and that `python fleet_model_push.py` still runs standalone.
- **Acceptance:** `git ls-files | grep push` lists the three modules + four
  `default_fleet_push/*.yaml`; `pytest aeromaps/` green; `01_basic` unchanged.

### Phase 1 — `markets.yaml` push profile (TP/RJ/NB/WB) + per-segment inputs

Author a **new** market profile (don't mutate `default_markets/markets.yaml`)
describing Paco's segments as passenger markets, plus the existing freight market.

- Per segment (`narrow_body`, `wide_body`, `regional_jet`, `turboprop` — choose ids that
  map cleanly to the engine's `NB/WB/RJ/TP`): `name`, `traffic_type: passenger`,
  `traffic_unit: RPK`, and `inputs.initial` with `rpk_share_last_historical_year` +
  `energy_share_last_historical_year` (**renamed** keys — old `_2019` keys now raise).
- **Source the per-segment shares from Paco's Excel**, reusing the Phase-Interface
  generator pattern: `aircraft_type_key_parameters.xlsx` has 2024 ASK + `MJ_fuel_ask`
  per type → aggregate to segment via `default_aircraft_classification.yaml`
  (`calculate_stats_by_market` already does this), derive RPK shares (and energy shares
  from `MJ_fuel_ask × ASK`). With flexible start year the pivot is
  `last_historical_year = 2024`, so these are **2024** shares — consistent, no 2019
  back-cast.
- Keep `demand.model: cagr` (or the scenario's choice) — the generic RPK→ASK chain runs
  on the four segments and produces the `ask_{mid}` series Phase 2 consumes.
- **Acceptance:** a process built on this profile initializes `MarketManager` with the
  four segments + freight and no missing-input errors.

### Phase 2 — Refactor `market_process` into a pure, injectable engine

Make the engine callable from `compute()` without side effects, ASK-injected, and
year-agnostic.

- **De-side-effect:** remove prints / matplotlib / `raise` from `market_process`; return
  arrays only. Move the demo's plotting + the standalone CAGR projection into the
  `fleet_process` / `__main__` path (kept behind the standalone flag, Decision #6).
- **Inject ASK:** accept a full per-year ASK series (indexed by year) and use it directly
  as `yearly_traffic` instead of `total_asks * np.exp(growth_rates_cum)`. Keep the CAGR
  path behind a flag for standalone use.
- **Un-hardcode the calendar:** replace literal `2024`/`2025` with the engine's pivot
  (`last_historical_year`) and projection bounds (`[prospection_start_year, end_year]`),
  passed in by the wrapper; relabel Excel `*_2024` reads as the last-historical-year
  calibration.
- Soften the capacity guard here (full robustness in Phase 7): return a feasibility
  signal instead of raising.
- **Acceptance:** feeding a known ASK series reproduces it inside `ask_volumes`;
  energy/ASK is invariant to the (now unused) growth profile; no stdout, no plots when
  called as a library.

### Phase 3 — Input layer (Hybrid)

Split Paco's inputs per Decision #2.

- **Static reference (Excel, loaded once in `custom_setup`):** per-type 2024 ASK /
  `MJ_fuel_ask` / `adj_distance_aircraft_year` / `average_seats`
  (`aircraft_type_key_parameters.xlsx`), starting fleet counts
  (`agg_fleet_end_2024.xlsx`), `other_parameters.xlsx`. Paths under
  `resources/data/default_fleet_push/` (move the calibration Excel there so the model
  ships its inputs as resources rather than reaching into `utils/calibration_notebooks/`).
- **Scenario knobs (YAML/GEMSEO inputs):** per-segment `age_utilisation_sensib` /
  `age_retirement_sensib`; new-aircraft cards (`intro_year`, `energy_efficiency`,
  `seats`, `renewal_rate`, `time_to_market`, `production_duration`, `ret_year_delay`);
  in-production `production_profile` points. Surface these so a scenario can tune the
  fleet without editing Excel; the engine's `reference_growth` CAGR becomes obsolete
  (ASK is injected).
- **Acceptance:** changing a new-aircraft EIS/efficiency in config (not Excel) changes
  the bridge; the static Excel is read exactly once per process build.

### Phase 4 — Wrap as `PassengerAircraftEfficiencyFleetPush(AeroMAPSModel)`

New model class (`model_type="custom"`) following the wiring contract: expose
`self.markets` + a `custom_setup()` so the loader injects `MarketManager` and calls
setup ([process.py custom wiring](aeromaps/core/process.py#L1614)).

- `custom_setup()` builds dynamic `input_names`/`output_names` from `self.markets`
  (passenger markets only): inputs `ask_{mid}` + the scenario knobs (Phase 3) + the
  `{mid}_*_last_historical_year` calibration scalars used for the history splice; outputs
  the efficiency bridge (a) and the fleet bridge (b).
- `compute()`:
  1. Load the static Excel + configs once (Phase 3).
  2. Per segment, pull the AeroMAPS `ask_{mid}` series, call the Phase-2 engine, get
     `ask_volumes` + `energy_consumption` (+ `fleet`/`deliveries` for Phase 5).
  3. `energy_per_ask[mid] = energy_consumption / ask_volumes` over the projection.
  4. **History splice** over `[historic_start_year, last_historical_year]` using the same
     construction as `SimpleShares`
     ([aircraft_efficiency.py:142-146](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py#L142)):
     `energy_consumption_per_ask_init.loc[idx_hist] × energy_share / rpk_share`.
  5. Route 100 % to `dropin_fuel`; emit the bridge columns.
- **Acceptance:** outputs finite over the full `[historic_start_year, end_year]` index;
  drop-in share == 100 % everywhere; a process using this model reaches end-of-pipeline.

### Phase 5 — Fleet-count & deliveries outputs + plots migration

Surface the push model's native fleet state (Decision #5) and move its plots into the
AeroMAPS plotting system.

- From the engine's per-type `aircraft_seats_volumes` / `fleet_content` and `deliveries`,
  emit per-segment `"{market.name}: Aircraft In Fleet"`, the per-type
  `aircraft_in_fleet_value_dict`, and per-type deliveries — mirroring `SimpleFleetCount`
  output naming ([fleet_numeric.py:326-329](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_numeric.py#L326))
  so existing fleet-count plots/consumers pick them up.
- **Migrate `fleet_model_push_visualisations.py`** (today bespoke matplotlib:
  `visu_fleet_array`, `visu_retirements_array`, `visu_retirement_age`,
  `visu_energy_intensity`) into the AeroMAPS plot system as `SingleScenarioPlot`
  subclasses in [aeromaps/plots/single_scenario_plot.py](aeromaps/plots/single_scenario_plot.py),
  each declaring `required_outputs` (the Phase-5 fleet outputs + the efficiency bridge)
  and a `create_plot()` — so the push fleet/energy-intensity charts render from process
  outputs like every other AeroMAPS plot, not from in-engine `plt` calls. This is also
  what lets Phase 2 strip plotting out of the engine cleanly (the demo `__main__` path
  can call these new plot classes too).
- **Acceptance:** per-segment fleet totals are positive and continuous across the pivot;
  sum of per-type counts == segment total; the migrated plots render from a finished
  process with no matplotlib calls inside the engine.

### Phase 6 — Model selection (`models_efficiency_push`)

Add a new dict in [core/models.py](aeromaps/core/models.py) parallel to
`models_efficiency_top_down` ([line 163](aeromaps/core/models.py#L163)) and
`_bottom_up` ([line 201](aeromaps/core/models.py#L201)), swapping the passenger
efficiency entry for `PassengerAircraftEfficiencyFleetPush` (+ the fleet-count entry
from Phase 5) and keeping the shared operations / emission-index / energy-intensity
models. Wire a top-level process group that references it.

- **Acceptance:** selecting the push group builds a valid process; the other groups are
  byte-for-byte unchanged (regression on `models_efficiency_bottom_up`).

### Phase 7 — Robustness for the MDA

- Convert the `fleet_content` capacity guard from `raise ValueError` / unconditional
  prints into a bounded, logged fallback (cap deliveries / clamp) so a transient
  infeasible ASK during MDA iterations doesn't abort the solve.
- Guard the empty-market / zero-ASK case (NaN intensity) — reuse the `traffic == 0`
  masking from [[empty-market-nan-robustness]].
- Replace remaining prints with `logging` at debug level.
- **Acceptance:** an MDA run with feedback converges; no NaN propagation; no console spam.

### Phase 8 — Validation

1. `01_basic` regression (default path untouched) — zero diff.
2. `pytest aeromaps/`.
3. A dedicated push-profile smoke notebook/scenario: build the process on the Phase-1
   profile, run to end-of-pipeline, sanity-check per-segment energy/ASK + fleet-count
   trajectories against Paco's standalone output (same configs ⇒ same numbers when ASK
   is fed the engine's own CAGR series).

## Later (out of v1 scope)

- **Energy types.** Add H2/electric to Paco's inventory + split `et` shares (today
  drop-in only).
- **Full Excel→YAML migration.** Fold the static calibration Excel into the AeroMAPS
  config / a regenerable generator (Decision #2 keeps it as Excel for v1).
- **Bottom-up cost tier.** Feed the `:aircraft_share` second tier consumed by
  `FleetEvolution` ([fleet_assignment.py]) from Paco's per-type deliveries, and add the
  cost/non-CO2 bridges (`doc_non_energy`, `emission_index_{nox,soot}` per market) if the
  push model is ever used with the bottom-up cost path.

## Critical files

- `aeromaps/models/.../fleet/fleet_model_push.py` — `market_process` refactor: pure
  engine, ASK injection, un-hardcode pivot/horizon (Phases 2-3).
- `aeromaps/models/.../fleet/fleet_model_push_calculations.py` — `fleet_content`
  capacity-guard robustness (Phase 7).
- `aeromaps/models/.../fleet/fleet_model_push_visualisations.py` →
  [aeromaps/plots/single_scenario_plot.py](aeromaps/plots/single_scenario_plot.py) —
  migrate bespoke matplotlib plots to `SingleScenarioPlot` subclasses (Phase 5).
- `aeromaps/models/.../fleet/aircraft_efficiency.py` (or new `fleet_push_model.py`) — the
  `PassengerAircraftEfficiencyFleetPush` wrapper (Phases 4-5).
- [aeromaps/core/models.py](aeromaps/core/models.py) — `models_efficiency_push` (Phase 6).
- [aeromaps/core/process.py](aeromaps/core/process.py#L1614) — custom wiring already
  supports the `markets` + `custom_setup` contract; no change expected.
- `aeromaps/resources/data/default_markets/` — new TP/RJ/NB/WB push market profile
  (Phase 1).
- `aeromaps/resources/data/default_fleet_push/*.yaml` + the calibration Excel (to be
  moved here) — inputs (Phases 1, 3).

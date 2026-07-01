# Plan — Finalize the integration of Paco's "push" fleet model

**Status :** Draft | **Updated :** 2026-06-23 | **Branch cible :** `custom_workflow`

## Context

Paco's delivery-driven ("push") fleet-renewal engine is the inverse of AeroMAPS'
existing S-curve bottom-up `FleetModel`: instead of assigning market shares from an
S-curve, it drives the fleet from aircraft **deliveries** and lets retirement +
utilisation curves determine the surviving fleet, then sums energy bottom-up.
Today it is a standalone script. The goal is to turn it into a selectable
`AeroMAPSModel` that emits the same downstream bridge as the other efficiency
models, **coexisting** with the bottom-up path (decision locked — see
[[fleet-push-integration]]).

Two workstreams completed since the integration was scoped now de-risk it:

1. **Flexible `prospection_start_year`** (`FLEXIBLE_START_YEAR_PLAN.md`, merged —
   commits `31f30c79`…`919ba6fe`). `AeroMAPSModel.last_historical_year` is now a
   first-class attribute and `*_2019` inputs were renamed `*_last_historical_year`.
   This is what lets Paco's engine legitimately start in **2024/2025** instead of
   forcing a 2020 pivot: a scenario with `prospection_start_year = 2025` no longer
   triggers the COVID patches and reads its pivot from `last_historical_year`.
2. **Phase Interface** (`MultiRegionalProcess`, Excel→inputs generator,
   share-decoupling mode, time-varying `ask_year` — commits `3841a124`…`81220638`).
   This established (a) the **custom-model wiring contract** in `process.py`, (b) the
   exact **bridge contract** the push model must emit, and (c) the **Excel→YAML
   generator pattern** we reuse for sourcing Paco's per-segment inputs.

### Locked decisions (recap)

1. **Segments = AeroMAPS markets.** Paco's TP/RJ/NB/WB become passenger markets via a
   new `markets.yaml` profile (freight kept separate).
2. **ASK injected from AeroMAPS** from v1; drop Paco's internal CAGR.
3. **Coexist, not replace** — a new `models_efficiency_push` dict in `core/models.py`.
4. **Keep Excel inputs** as official resources under `resources/data/default_fleet_push/`.

### Bridge contract (what the wrapper must emit)

Mirrors `PassengerAircraftEfficiencySimpleShares`
([aircraft_efficiency.py:99-102](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py#L99)):
per passenger market `mid` and energy type `et`:
- `energy_per_ask_without_operations_{mid}_{et}` — MJ/ASK series.
- `ask_{mid}_{et}_share` — % ASK split by energy type.

v1 is **drop-in only**: `et = dropin_fuel` carries 100 %, `hydrogen`/`electric`
shares are 0 (and their `energy_per_ask` columns mirror drop-in so downstream
relative-intensity reads stay finite).

## Current state & blockers

- **The push code is NOT on `custom_workflow`.** It lives on `fleet_paco_models`
  (the three `fleet_model_push*.py` + `resources/data/default_fleet_push/*.yaml`).
  Topology today: `custom_workflow` is +193 vs `main`; `fleet_paco_models` is +187
  vs `main`; they diverge (`fleet_paco_models` is +18 / −12 vs `custom_workflow`).
  My "Step B" (`cff77bb5 avoid runnig fleet_model_push on import` — the `__main__`
  guard) is on the paco branch. **Phase 0 below must land the push code on
  `custom_workflow` before any wiring.**
- The paco-branch engine already has the helper refactor (`_load_yaml`,
  `_build_aircraft_to_market_mapping`, `calculate_stats_by_market`, `fleet_process`,
  `market_process`) and the import guard. So importability (old "Step B") is done.
- **ASK is not yet injected.** `market_process(total_asks, …)` takes `total_asks` as a
  single base-year scalar and grows it internally
  (`yearly_traffic = total_asks * np.exp(growth_rates_cum)`,
  [fleet_model_push.py:~300]). Decision #2 requires replacing this with the
  AeroMAPS-provided ASK series.
- **Horizon is hard-coded** `years = np.arange(2025, market_growth[0][-1] + 1)`.
  Must be clipped/aligned to `[prospection_start_year, end_year]` and history spliced
  over `[historic_start_year, last_historical_year]`.
- The capacity guard in `fleet_content` raises `ValueError` / prints "temporary
  aircraft parking" repeatedly in the standalone run → MDA-robustness risk.

## Phases

### Phase 0 — Land the push code on `custom_workflow`

Bring the three modules + config dir onto the working branch, reconciled with the
flexible-start-year rename and the current efficiency bridge.

- Rebase/merge `fleet_paco_models` onto `custom_workflow` (user-driven — the
  "rebases" already mentioned). Conflicts will be in `core/models.py` (model-dict
  block) and possibly `aircraft_efficiency.py` imports; the push `.py` files
  themselves are additive.
- After landing, re-confirm clean import (no side effects) and that
  `python fleet_model_push.py` still runs standalone.
- **Acceptance:** `git ls-files | grep push` lists the three modules + four
  `default_fleet_push/*.yaml`; `pytest aeromaps/` green; `01_basic` unchanged.

### Phase 1 — `markets.yaml` push profile (TP/RJ/NB/WB) + per-segment inputs

Author a **new** market profile (don't mutate the default 4-market file) describing
Paco's segments as passenger markets, plus the existing freight market.

- Per segment (`narrow_body`, `wide_body`, `regional_jet`, `turboprop`):
  `name`, `traffic_type: passenger`, `traffic_unit: RPK`, and
  `inputs.initial` with `rpk_share_last_historical_year` +
  `energy_share_last_historical_year` (note the **renamed** keys — Phase D of the
  flex-start work; old `_2019` keys now raise).
- **Source the per-segment shares from Paco's Excel**, reusing the Phase-Interface
  generator pattern: Paco's `aircraft_type_key_parameters.xlsx` has 2024 ASK per
  type → aggregate to segment via `default_aircraft_classification.yaml`, derive RPK
  shares (and energy shares from `MJ_fuel_ask × ASK`). With flexible start year the
  pivot is `last_historical_year = 2024`, so these are **2024** shares — consistent,
  no 2019 back-cast needed.
- Keep `demand.model: cagr` (or whatever the scenario uses) — the generic RPK→ASK
  chain runs on the segments and produces the `ask_{mid}` series Phase 2 consumes.
- **Acceptance:** a process built on this profile initializes markets
  (`MarketManager`) with the four segments + freight and no missing-input errors.

### Phase 2 — Inject AeroMAPS ASK into `market_process`

Replace Paco's internal CAGR projection with the AeroMAPS ASK series.

- Add an injected-ASK path to `market_process`: accept a full per-year ASK series
  (`ask_series` indexed by year) and use it directly as `yearly_traffic` instead of
  `total_asks * np.exp(growth_rates_cum)`. Keep the CAGR path behind a flag for
  standalone use (so `python fleet_model_push.py` still works without AeroMAPS).
- Align the engine's year axis to `[prospection_start_year, end_year]` rather than
  the growth-profile span; the wrapper passes the bounds.
- **Acceptance:** feeding a known ASK series reproduces it inside the engine's
  `ask_volumes`; energy/ASK is invariant to the (now unused) growth profile.

### Phase 3 — Wrap as `PassengerAircraftEfficiencyFleetPush(AeroMAPSModel)`

New model class in `aircraft_efficiency.py` (or a sibling `fleet_push_model.py`),
`model_type="custom"`, following the `process.py` wiring contract
([process.py:1614-1641](aeromaps/core/process.py#L1614)): expose a `self.markets`
attribute + a `custom_setup()` method so the loader injects `MarketManager` and calls
setup.

- `custom_setup()` builds dynamic `input_names`/`output_names` from
  `self.markets` (passenger markets only): inputs `ask_{mid}` (+
  `energy_consumption_per_ask_init` equivalent and the
  `{mid}_*_last_historical_year` calibration scalars used for the splice); outputs
  the bridge contract above.
- `compute()`:
  1. Load Paco's configs + Excel (paths from `default_fleet_push/`), once.
  2. For each market, pull the AeroMAPS `ask_{mid}` series, call `market_process`
     (Phase 2 injected path), get `ask_volumes` + `energy_consumption`.
  3. `energy_per_ask[mid] = energy_consumption / ask_volumes` over the projection.
  4. **History splice** over `[historic_start_year, last_historical_year]` using the
     same construction as `SimpleShares`
     ([aircraft_efficiency.py:136-143](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py#L136)):
     `energy_consumption_per_ask_init.loc[lhy] × energy_share / rpk_share`.
  5. Route 100 % to `dropin_fuel`; emit the bridge columns.
- **Acceptance:** outputs are finite over the full `[historic_start_year, end_year]`
  index; drop-in share == 100 % everywhere; a process using this model reaches
  end-of-pipeline.

### Phase 4 — Model selection (`models_efficiency_push`)

Add a new dict in [core/models.py](aeromaps/core/models.py) parallel to
`models_efficiency_top_down` (line 162) and `_bottom_up` (line 200), swapping the
passenger efficiency entry for `PassengerAircraftEfficiencyFleetPush` and keeping the
shared operations / emission-index / energy-intensity models. Wire a top-level
process group that references it (mirroring `models_simple` /the existing groups).

- **Acceptance:** selecting the push group builds a valid process; the other groups
  are byte-for-byte unchanged (regression on `models_efficiency_bottom_up`).

### Phase 5 — Robustness for the MDA

- Convert the `fleet_content` capacity guard from `raise ValueError` /
  unconditional prints into a bounded, logged fallback (cap deliveries / clamp) so a
  transient infeasible ASK during MDA iterations doesn't abort the solve.
- Guard the empty-market / zero-ASK case (NaN intensity) — reuse the
  `traffic == 0` masking established in [[empty-market-nan-robustness]].
- Silence per-iteration prints (use logging at debug level).
- **Acceptance:** an MDA run with feedback converges; no NaN propagation; no console
  spam.

### Phase 6 — Validation

1. `01_basic` regression (default path untouched) — zero diff.
2. `pytest aeromaps/`.
3. A dedicated push-profile smoke notebook/scenario: build the process on the
   Phase-1 profile, run to end-of-pipeline, sanity-check per-segment energy/ASK
   trajectories against Paco's standalone output (same configs ⇒ same numbers when
   ASK is fed the engine's own CAGR series).

## Later (out of v1 scope)

- **Energy types.** Add H2/electric to Paco's inventory + split `et` shares
  (today drop-in only).
- **Per-aircraft tier.** Feed the `:aircraft_share` second tier consumed by
  `FleetEvolution` ([fleet_numeric.py]) from Paco's per-type deliveries.
- **Excel I/O consolidation.** Fold `default_fleet_push/` Excel into the broader
  Excel-interface goal (a generator like the Phase-Interface one, so the YAML/Excel
  inputs are regenerable).
- **Cost/non-CO2 bridges.** `doc_non_energy`, `emission_index_{nox,soot}` per market
  if the push model is ever used with the bottom-up cost path.

## Critical files

- `aeromaps/models/.../fleet/fleet_model_push.py` — ASK injection + horizon (Phase 2).
- `aeromaps/models/.../fleet/fleet_model_push_calculations.py` — capacity-guard
  robustness (Phase 5).
- `aeromaps/models/.../fleet/aircraft_efficiency.py` (or new `fleet_push_model.py`) —
  the `AeroMAPSModel` wrapper (Phase 3).
- [aeromaps/core/models.py](aeromaps/core/models.py) — `models_efficiency_push` (Phase 4).
- [aeromaps/core/process.py](aeromaps/core/process.py) — already supports the custom
  wiring (1614-1641); no change expected.
- `aeromaps/resources/data/default_markets/` — new push market profile (Phase 1).
- `aeromaps/resources/data/default_fleet_push/*.yaml` + the calibration Excel — inputs.

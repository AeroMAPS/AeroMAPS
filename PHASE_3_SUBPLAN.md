# Phase 3 — Fleet Model Market Integration: Sub-plan for Delegated Execution

**Branch:** `fleet-refactoring`
**Status (snapshot 2026-04-27):**
- Phases 0–2 ✅: `MarketManager` wired into `AeroMAPSProcess`; per-market RPK/RTK/ASK/LoadFactor disciplines exist; defaults deep-merge in `markets.yaml` works.
- Prep A/B/C ✅: calibration loop already a single `for` over `CALIBRATION_CONFIG` (still hardcoded tuples); energy types data-driven; performance methods vectorised.
- Prep D ⏳ deferred (1/2/3+ subcategory branching in [fleet_assignment.py:74-233](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_assignment.py#L74-L233)).
- `FleetModel` built at [process.py:1504](aeromaps/core/process.py#L1504) — does **not** yet receive `MarketManager`.

---

## Phase 3 goal (recap)

Make `FleetModel` driven by `MarketManager`. Internal DataFrame column prefixes (`"Short Range:..."`) are **left untouched** — renaming those is Phase 4 scope (downstream `AeroMAPSCustomModelWrapper` migration). Phase 3 stops at: (a) fleet.yaml uses market ids; (b) calibration sourced from `MarketManager`; (c) `fleet_numeric.py` no longer has `if category == "Short Range"`; (d) the bottom-up notebook ([05_use_fleet_models/examples_fleet.ipynb](aeromaps/notebooks/tutorials/05_use_fleet_models/examples_fleet.ipynb)) still produces identical numerics.

**Out of scope for Phase 3** (do **not** do these — they belong in Phase 4):
- Renaming DataFrame columns from display name (`"Short Range"`) to market id (`short_range`).
- Migrating `PassengerAircraftEfficiencySimpleShares` (top-down efficiency model, ~40 args). Even though plan §5 listed it under Phase 3, it follows the Phase 4 `AeroMAPSCustomModelWrapper` recipe, not the bottom-up fleet flow.
- Migrating `non_co2_emissions.py`, `direct_operating_costs.py`, `energy_consumption.py`, etc.

---

## Chantier ordering & dependencies

```
3.A (schema)  ─►  3.B (calibration)  ─►  3.D (assignment loop)  ─►  3.E (perf verify)
       │                                       │
       └────►  3.C (fleet_numeric custom wrap) ─┘
                                                                 ─►  3.F (smoke test)
```

3.A must land first. 3.B and 3.C are independent of each other and can run in any order after 3.A. 3.D / 3.E are mostly verification + light loop refactor. 3.F is the integration check.

### Regression gating (deliberately light)

Branch state — much of the wider notebook suite is currently broken because of in-flight refactor work; **do not block chantier completion on notebook regressions**. Default gate per chantier:

1. `python -m pytest tests/ -x --no-header -q` — must pass.
2. `python -c "from aeromaps.core.process import AeroMAPSProcess; AeroMAPSProcess()"` — must import + instantiate without error.
3. Chantier-specific *targeted* check (listed in each section below). Often this is "instantiate `FleetModel`, run `.compute()`, assert column X exists".

Notebook smoke tests (`--nbmake`) are **opt-in only**, listed as "Optional verification" per chantier. Agents should run them and *report* the result but not fail the chantier when the failure is unrelated (e.g. a downstream model that is still on the legacy plumbing).

---

## Chantier 3.A — fleet.yaml schema migration: `categories:` → `market_served:`

**Goal:** key the top-level fleet structure by `market_id` (a reference into `markets.yaml`), look up display name from `MarketManager`, validate cross-consistency.

**Naming note:** the top-level YAML key in `fleet.yaml` is **`market_served:`**, *not* `markets:`. Reason: `markets:` would clash with the top-level `markets.yaml` semantics (where the file *is* the market definitions); inside `fleet.yaml` we are declaring "which markets this fleet serves and how", so `market_served:` is more honest and avoids confusion when reading either file in isolation.

**Files to modify:**
- [aeromaps/resources/data/default_fleet/fleet.yaml](aeromaps/resources/data/default_fleet/fleet.yaml) — replace `categories:` block (lines 52–77) with a `market_served:` block. Keep `subcategories:` block unchanged.
- [aeromaps/resources/data/default_fleet/fleet_no_new_aircraft.yaml](aeromaps/resources/data/default_fleet/fleet_no_new_aircraft.yaml) — same migration.
- [aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py) — `_build_fleet_from_yaml` (lines 730–784) reads `market_served:` instead of `categories:`. Each entry has `market: <id>` + `parameters` + `subcategories:` (no `name` field — pulled from `MarketManager`).
- `FleetModel.__init__` (line 989) and `Fleet.__init__` (line 441) accept `markets: MarketManager` and `markets_data: dict` kwargs.
- [aeromaps/core/process.py:1504](aeromaps/core/process.py#L1504) — pass `markets=self.markets, markets_data=self.markets_data` when constructing `FleetModel(fleet=self.fleet)`.

**Target YAML shape:**
```yaml
# fleet.yaml
market_served:
  - market: short_range          # id reference into markets.yaml
    parameters:
      life: 25
      limit: 2
    calibration_subcategory: sr_conventional_nb   # NEW (consumed by 3.B)
    subcategories:
      - sr_conventional_nb
      - sr_regional_tp
      - sr_hydrogen_nb
  - market: medium_range
    parameters: { life: 25, limit: 2 }
    calibration_subcategory: mr_conventional_nb
    subcategories: [mr_conventional_nb]
  - market: long_range
    parameters: { life: 25, limit: 2 }
    calibration_subcategory: lr_conventional_wb
    subcategories: [lr_conventional_wb]

subcategories:
  # unchanged
  ...
```

**Validation to add (in `_build_fleet_from_yaml`):**
1. Every `market:` id in fleet.yaml's `market_served` must exist in `self.markets` (when `self.markets` is provided). Raise `KeyError` listing the offenders.
2. Every passenger market in `self.markets` must have a `market_served` entry. Raise `KeyError` listing missing ones.
3. Subcategory share sum already validated by `_check_shares()` — keep it.

**Internal API:**
- `Category.name` continues to hold the human-readable display ("Short Range"), populated from `self.markets.get_all()[i].name`. **Do not** change `category.name` to be the id — DataFrame columns and downstream consumers still rely on the display string. That rename is Phase 4.
- Add a `Category.market_id` attribute to make the link explicit (used by 3.B and 3.C).

**Acceptance gate:**
- `python -m pytest tests/ -x` passes.
- `python -c "from aeromaps.core.process import AeroMAPSProcess; p = AeroMAPSProcess(); p.setup_mda()"` succeeds (default config, default fleet+markets).
- Targeted: instantiate `Fleet` from the new YAML, assert `len(fleet.categories) == 3` and `category.market_id` set on each.

**Optional verification (agent reports outcome but does not block):**
- `python -m pytest --nbmake aeromaps/notebooks/tutorials/05_use_fleet_models/examples_fleet.ipynb -x` — currently expected to pass on `fleet-refactoring` HEAD; if it still passes after the chantier, great. If it fails, agent should diff the failure against pre-change to decide whether the regression is in-scope.

**Effort:** Low | **Risk:** Low–Medium | **Estimated diff:** ~150 lines.

---

## Chantier 3.B — Calibration loop sourced from `MarketManager`

**Goal:** replace `CALIBRATION_CONFIG` (hardcoded tuples at [fleet_model.py:875-894](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py#L875-L894)) with iteration over `self.markets.get(traffic_type="passenger")`.

**Pre-req:** 3.A landed (so `self.markets` and `Category.market_id` exist on `Fleet`).

**Files to modify:**
- [fleet_model.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py) `_calibrate_reference_aircraft` (lines 869–950).

**Refactor:**
```python
def _calibrate_reference_aircraft(self):
    if self.parameters is None or self.markets is None:
        return
    for market in self.markets.get(traffic_type="passenger"):
        mid = market.id
        cat_name = market.name
        # Calibration subcategory is declared in fleet.yaml (3.A added the field)
        sub_id = self._calibration_subcategory_for(mid)  # helper added in 3.A
        sub_name = self._subcategory_display_name(sub_id)  # lookup
        subcat = self._get_subcategory(cat_name, sub_name)
        if subcat is None:
            continue
        energy_share_param = f"{mid}_energy_share_2019"
        rpk_share_param   = f"{mid}_rpk_share_2019"
        # ... same body as before, parametrised on (cat_name, mid, energy/rpk param names)
```

**Acceptance gate:**
- `python -m pytest tests/test_fleet_model_regression.py -x` passes if it covers calibration (and the wider `pytest tests/ -x`).
- Targeted: build a `Fleet` post-3.A, call `_calibrate_reference_aircraft()`, assert `entry_into_service_year` is set on each market's reference subcategory and that the value matches the legacy result for the default 4-market scenario (use a one-off pickle fixture if needed; agent may generate it from the pre-change branch state).

**Effort:** Low | **Risk:** Medium (calibration affects EIS year, downstream of S-curve). | **Estimated diff:** ~30 lines.

---

## Chantier 3.C — `fleet_numeric.py`: market iteration via custom wrapper *(lower-criticality)*

**Criticality note:** `FleetEvolution` produces fleet-counting outputs (aircraft in fleet, production, disposal) that feed reporting/plots more than the core energy/cost flow. If this chantier blocks, it can be parked without halting 3.B / 3.D / 3.E.

**Goal:** kill the hardcoded `if category == "Short Range"` dispatch (lines 47–56) and the per-market aggregation block (lines 144–178). The new `FleetEvolution` becomes a `model_type="custom"` discipline that consumes `<mid>_ask` / `<mid>_rpk` for all passenger markets.

**Pre-req:** 3.A landed (so `FleetEvolution` can receive a `markets` ref via `fleet_model.fleet.markets`). 3.C is independent of 3.B.

**Files to modify:**
- [fleet_numeric.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_numeric.py) — switch `FleetEvolution` to `model_type="custom"`. Build `input_names` / `output_names` in `__init__` using `markets.get(traffic_type="passenger")`. Replace the typed `compute(self, ask_short_range, ...)` signature with `compute(self, input_data) -> dict`.
- [aeromaps/core/models.py:377](aeromaps/core/models.py#L377) — `FleetEvolution("fleet_numeric")` instantiation needs the `markets` registry. Easiest path: convert this entry from a static instance to a builder that takes `process.markets`. Or have `FleetModel` instantiate `FleetEvolution` itself (it already holds `self.fleet.markets`).

**Pattern reference:** `RPKAggregator` in [aeromaps/models/air_transport/air_traffic/rpk_market.py](aeromaps/models/air_transport/air_traffic/rpk_market.py) — same recipe (`model_type="custom"`, dynamic I/O names, dict in / dict out).

**Output keys to keep stable** (downstream consumers depend on them):
- `<aircraft_full_name>:aircraft_ask`, `:aircraft_rpk`, `:aircraft_in_fleet`, `:aircraft_in_fleet_covid_levelling`, `:aircraft_in_out` — unchanged.
- `"Short Range: Aircraft Production"`, `"Short Range: Aircraft Disposal"` (and Medium/Long) — keep using `category.name` (display) as prefix. Same for new user-defined markets: prefix is the market's display `name`. Loop over markets to build them.

**Acceptance gate:**
- `python -m pytest tests/ -x` passes.
- Targeted: build `AeroMAPSProcess`, run `setup_mda()` then `compute()`. After compute, assert that each passenger market produced its `"<display_name>: Aircraft Production"` and `"<display_name>: Aircraft Disposal"` columns in `fleet_model.df`.

**Optional verification:** notebook 05 — agent reports outcome but does not block on it.

**Effort:** Medium | **Risk:** Medium (first GEMSEO custom-wrapper migration in the fleet stack). | **Estimated diff:** ~120 lines.

---

## Chantier 3.D — `fleet_assignment.py`: market iteration audit

**Goal:** the mixin already iterates `self.fleet.categories.values()` — verify behaviour is preserved with the new `Category` objects (post 3.A) for arbitrary numbers of markets and that `category.market_id` is now plumbed where it would be useful.

**Pre-req:** 3.A landed.

**Files to modify:**
- [fleet_assignment.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_assignment.py) — small touch-ups only. **Do not** combine with Prep D unless explicitly authorised (Prep D is high-risk per plan §4.1).

**Acceptance gate:**
- `python -m pytest tests/ -x` passes.
- Targeted: instantiate `Fleet` with the new market-served structure, run `_compute_single_aircraft_share()` + `_compute_aircraft_share()`, assert no `KeyError`s and that `<display_name>:<sub>:<aircraft>:single_aircraft_share` columns are produced for every (market, subcategory, aircraft) tuple.

**Effort:** Low | **Risk:** Low. | **Estimated diff:** ~20 lines.

---

## Chantier 3.E — `fleet_performance.py`: market iteration audit + custom-market smoke

**Goal:** verify all `for category in self.fleet.categories.values()` loops in [fleet_performance.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_performance.py) work for an arbitrary number of markets (the loops are already generic post-Prep B/C).

**Files to modify:** likely none — this is mostly verification. If anything breaks for a 5-market test scenario, fix the offending site.

**Acceptance gate:**
- `python -m pytest tests/ -x` passes.
- Targeted: run a 5-market `Fleet` through `FleetPerformanceMixin` methods and assert the per-market `share:<energy_type>` columns exist for every market.
- The 5-market scenario lives in chantier 3.F's fixture; 3.E may be sequenced after 3.F if cleaner.

**Effort:** Low | **Risk:** Low. | **Estimated diff:** 0–50 lines.

---

## Chantier 3.F — Custom-market smoke test (test asset)

**Goal:** add a notebook or pytest fixture that exercises `FleetModel` against a non-default `markets.yaml` with 5 markets (split short-range into `regional` + `mainline`, for instance) and confirms the bottom-up fleet runs without hardcoded breakage.

**Files to modify:**
- New: `aeromaps/notebooks/tutorials/13_phase3_custom_markets/{markets.yaml, fleet.yaml, config.yaml, test_phase3.ipynb}` OR
- Preferred (lower-risk, faster CI): new `tests/test_fleet_custom_markets.py` building a process programmatically with a 5-market scenario.

**Acceptance gate:**
- New `tests/test_fleet_custom_markets.py` passes.
- `python -m pytest tests/ -x` passes (whole suite green including the new test).

**Optional verification:** notebook 05 — agent reports outcome but does not block on it.

**Effort:** Medium | **Risk:** Low. | **Estimated diff:** ~150 lines (mostly fixture data).

---

## Chantier 3.G (optional, after 3.A–F land) — Prep D fold-in

If 3.A–F land cleanly, fold Prep D in as a separate chantier on top: unify 1/2/3+ subcategory branching in `_compute_single_aircraft_share` ([fleet_assignment.py:74-233](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_assignment.py#L74-L233)). High risk per plan §4.1 — **do not** delegate to a non-Opus agent. Owner: human or Opus only.

---

## Files NOT touched in Phase 3 (Phase 4 territory)

Do not let agents stray into:
- [aircraft_efficiency.py](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/aircraft_efficiency.py) — top-down models, Phase 4.
- [non_co2_emissions.py](aeromaps/models/impacts/emissions/non_co2_emissions.py), [direct_operating_costs.py](aeromaps/models/impacts/costs/airlines/direct_operating_costs.py), [energy_consumption.py](aeromaps/models/impacts/energy_resources/energy_consumption.py), [total_airline_cost_and_airfare.py](aeromaps/models/impacts/costs/airlines/total_airline_cost_and_airfare.py), [fleet_abatement_cost.py](aeromaps/models/impacts/costs/efficiency_abatement_cost/fleet_abatement_cost.py), [co2_emissions.py](aeromaps/models/impacts/emissions/co2_emissions.py).
- `parameters.json` cleanup — Phase 5.
- DataFrame column prefix rename — Phase 4.

---

## Standard agent prompt template (per chantier)

```
You are executing Chantier 3.X of /Users/a.salgas/PycharmProjects/AeroMAPS/PHASE_3_SUBPLAN.md.

Read PHASE_3_SUBPLAN.md, then execute ONLY the section "Chantier 3.X". Do NOT modify
any file marked "do not touch" in section "Files NOT touched in Phase 3". Do NOT migrate
downstream models. If you are unsure whether a change is in scope, stop and report
instead of guessing.

Acceptance gate (must pass before committing):
  python -m pytest tests/ -x --no-header -q
  python -c "from aeromaps.core.process import AeroMAPSProcess; AeroMAPSProcess()"
  + the chantier-specific targeted check in the subplan.

Notebook --nbmake checks are OPTIONAL: run them if listed under "Optional verification",
report the outcome, but DO NOT fail the chantier on a notebook regression that is
unrelated to your changes (much of the suite is currently broken on this branch).

If the acceptance gate passes:
  - Stage your changes (git add of the files you modified — never `git add -A`).
  - Commit with message: "Phase 3.X — <one-line summary>" (no Claude attribution required).
  - Do NOT push.
If the gate fails: stop, leave changes unstaged, and report what failed.

When done, summarise (≤200 words):
  - Files changed (with line counts).
  - Tests run + result.
  - Anything noticed that is out of scope (do not fix, just flag).
  - Commit SHA if a commit was made.
```

The user reviews each commit afterwards. Chantiers MUST be run sequentially (3.A first; 3.B/3.C/3.D after 3.A; 3.E and 3.F last). Never run two chantiers concurrently — they touch overlapping files.

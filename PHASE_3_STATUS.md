# Phase 3 — Execution Status (Final)

**Branch:** `fleet-refactoring`
**Run dates:** 2026-04-27 (3.A–3.C), 2026-04-28 (3.D–3.F)
**Status:** ✅ Complete — all six chantiers landed. No push performed.

---

## Landed

| Chantier | Commit     | Summary                                                                                       |
|----------|------------|-----------------------------------------------------------------------------------------------|
| 3.A      | c42d2a67   | `fleet.yaml` schema migration: `categories:` → `market_served:`                               |
| 3.B      | c6a82996   | Calibration loop sourced from `MarketManager`                                                 |
| 3.C      | bb820059   | `FleetEvolution` migrated to custom wrapper with market-driven dispatch                       |
| 3.D      | 16ed74b9   | `fleet_assignment` audit: `market_id` plumbing + explicit first-subcategory ref               |
| 3.E      | cec18670   | `FleetPerformanceMixin` verified for arbitrary market count via 5-market smoke test           |
| 3.F      | febffdb8   | Custom-market smoke test: 5-market `FleetModel` + `FleetEvolution` end-to-end                 |

Each commit passed the chantier's acceptance gate (`pytest tests/ -x` + the targeted check). Test count progression:

- After 3.A–3.C: 40 passing.
- After 3.D: 48 passing (8 new in `tests/test_fleet_assignment_market_iteration.py`).
- After 3.E: 55 passing (7 new in `tests/test_fleet_performance_market_iteration.py`).
- After 3.F: 73 passing (18 new in `tests/test_fleet_custom_markets.py`).

## Not landed

None — all chantiers in scope of this run are committed.

3.G (Prep D fold-in) was explicitly out-of-scope for this run per the subplan: "do not delegate to a non-Opus agent". Owner: human or Opus only.

## Flags raised by agents (out of scope, not fixed)

Repeatedly observed across the run, all flagged as pre-existing on this branch:

1. **`AeroMAPSProcess()` constructor fails** at `setup_mda()` with
   `RuntimeError: Model 'nox_emission_index_complex' requires a pathways_manager`.
   The acceptance gate's bare-import line still passes; this was present before any
   Phase 3 work and is unrelated.
2. **`recurring_costs.py` and `non_recurring_costs.py`** have a pre-existing
   `pandas.Series.rename()` / newer-pandas `TypeError`. Listed under "Files NOT
   touched in Phase 3"; left alone.
3. **Notebook 05 (`examples_fleet.ipynb`) `--nbmake` regression:** failure is in
   `outputs.json` numerical comparison, traced to earlier load-factor parameter
   additions on this branch — not caused by Phase 3 chantiers. Per subplan,
   notebook regressions are non-blocking on this branch.
4. **`outputs.json` for notebook 05** has unstaged modifications inherited from
   prior commits on `fleet-refactoring`; no Phase 3 chantier staged it. Still
   unstaged at end of run.
5. **`_compute_single_aircraft_share` 1/2/3+ subcategory branching** ([fleet_assignment.py:74-233](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_assignment.py#L74-L233))
   is the Prep D / Chantier 3.G unification work — high-risk, explicitly deferred
   to a human or Opus owner.
6. **`PerformanceWarning` in `_compute_mean_doc_non_energy`** — DataFrame
   fragmentation from repeated column assignment (in `fleet_performance.py`).
   Pre-existing pattern; would belong to a separate performance-cleanup chantier.
7. **NaN at year 2019 in `ask_aircraft_value_dict` / `rpk_aircraft_value_dict`** —
   pre-existing characteristic of `FleetEvolution`: the series spans
   `covid_start_year-1 .. end_year` but `fleet_model.df` only covers from
   `prospection_start_year`. The 3.F test asserts over the prospection window
   only.

## Working-tree state at end of run

- Unstaged: `aeromaps/notebooks/tutorials/05_use_fleet_models/data/outputs.json` (inherited drift, pre-Phase 3).
- This file (`PHASE_3_STATUS.md`) — untracked.
- No other modifications.

## Next steps

- Human review of commits c42d2a67…febffdb8.
- If Phase 3 is accepted, branch is ready to push at the user's discretion.
- 3.G (Prep D fold-in) remains optional follow-up; owner-restricted.

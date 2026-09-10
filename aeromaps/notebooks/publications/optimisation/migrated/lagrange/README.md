# Lagrange multipliers of the ReFuelEU blending-mandate optimisation

Self-contained exploratory analysis. Nothing here is imported by the paper
notebooks; deleting this folder does not affect `../01_optimisation_runs.ipynb`
or `../02_results.ipynb`.

## What is here

| | |
|---|---|
| `extract_multipliers.py` | reads the stored `.hdf` problems, recovers the multipliers, converts to €/tCO2, €/GJ, €/EJ |
| `validate_multipliers.py` | aggregate envelope checks (multiplier vs finite difference of the optimal objective) |
| `validate_pointwise.py` | per-run trust flags: secant bracket + gradient consistency |
| `envelope_direct.py` | ground truth: re-optimises at budget ±0.01 and differences the objective |
| `robustness_multipliers.py` | active-set tolerance sweep |
| `plot_multipliers.py` | the two figures |
| `recompute_gradients.py` | repairs missing gradients at a stored optimum without re-running |
| `tcac_decomposition.py`, `compare_fuel_mac.py` | shadow price vs a static fuel MAC |
| `rerun_tight.py`, `queue_sweeps.sh`, `sweep_status.sh` | the tight re-sweep and its throttled launcher |
| `REPORT.md` | the long write-up — **partly superseded, see its header** |

## Two sweeps

`../results/` is the paper's own sweep and is **not** written to by anything here.
`results_tight/` is a re-run of all 55 optimisations with `ftol_abs=1e-8`,
`kkt_tol_rel=1e-6`, otherwise identical (same warm-start continuation down the
budget ladder). Select one with an environment variable:

```bash
poetry run python extract_multipliers.py                              # ../results  -> ./
AEROMAPS_LAGRANGE_RESULTS=results_tight poetry run python extract_multipliers.py   # -> analysis_tight/
```

Then `validate_multipliers.py`, `validate_pointwise.py`, `plot_multipliers.py`
with the same variable. Outputs never collide.

## What this analysis does and does not support

**Supported.** The multipliers are correct. Six direct re-optimisation checks
agree with the extracted λ to within 0.4 %, once the comparison is made against
a *one-sided* derivative. Complementary slackness is exact on all 46 feasible
runs and the KKT residual is at machine precision after the active set is
identified from stationarity rather than from a fixed tolerance.

**Not supported.** Using λ to compare scenarios at equal carbon budget is
fragile. λ is a one-sided derivative, and at a budget where a constraint enters
the active set the two sides can differ by 44 % (measured: 15 % biomass at
budget 2.6 — 339.5 tightening, 235.8 loosening). Cases sitting on a kink are
then not comparable with cases that are not, and the apparent inversion of the
biomass ordering at budget 2.6 is an artefact of exactly that. The ordering is
strictly intuitive — more biomass, lower shadow price — at all six budgets from
3.8 to 2.8, and breaks only where the 15 % case meets its blend ceiling.

A comparison of "constraint intensity" across scenarios would be better built on
quantities that are continuous across active-set changes — the total cost of
each budget, or the binding-constraint map by year — than on λ.

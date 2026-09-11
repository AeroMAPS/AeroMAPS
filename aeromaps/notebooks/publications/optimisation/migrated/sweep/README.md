# Overnight sweep — one parameter at a time, plus the regenerated Figure 9 surface

Two things live here. Blocks **A–D** are one-parameter sensitivities held at a single
carbon budget; block **E** re-runs the paper's carbon-budget × biomass ladder, which the
model changes below have made stale.

## The framing

Every run of blocks A–D meets the same absolute budget: the cumulative 2020–2050 CO2 of
**ReFuelEU (linear) at ε_P = −0.9**, computed once and held fixed.

| | |
|---|---|
| budget, EU perimeter | **3.8656495 GtCO2** |
| as a share of the world aviation budget | **3.122636344 %** |

The constraint takes a share, but a share *is* an absolute budget here: when it is active
it pins `cumulative_co2_emissions[2050] = gross_carbon_budget_2050 × share / 100`, and both
factors on the right are exogenous. Verified across the elasticity runs — C2050 identical
to six significant figures while C2025 moved by 0.6 %.

Aviation's biomass allocation is a round **10 %**, not the reverse-engineered 9.90 %.

## Two corrections, and why every run was redone

Both are in the model, not the sweep, so blocks A–E were all re-run under them.

1. **The ramp-up volume branch is an increment.** Eq. 12 is
   `E_t ≤ max{E_{t-1}(1+τ)^Δt, E_{t-1} + ΔE·Δt}`. The code read the second branch as an
   absolute ceiling, `ΔE·Δt`, which is wrong twice over: it let a pathway starting from
   zero jump straight to one period's allowance, and once `E_{t-1}` exceeded that
   allowance the branch could never be the max again, so the limit silently became a pure
   rate constraint. The correction only ever loosens; every stored optimum stayed
   feasible under it.
2. **Mandates step in 2025.** They used to ramp linearly from 2020, which burned
   0.0598 EJ of biofuel over 2021–2024 inside the ReFuelEU run that *defines* the budget,
   abating 4.06 MtCO2 there and tightening the budget by 0.105 %. The budget moves from
   3.8615905850 to 3.8656495 GtCO2. The step and fossil references are unchanged, as they
   should be.

The two changes cancel exactly wherever the volume branch never bound: the budget grew by
the same 4.06 MtCO2 that the 2025 step adds to 2021–2024 in every run. So `rate_39`,
`vol_0_4` and `r_15` came back where they were, while everything the volume branch
constrained moved.

## Solver settings

The ftol stop is **off** (`FTOL = 0.0`); the KKT residual is the intended convergence
criterion, with `max_iter` as the backstop. GEMSEO's xtol stop is still live, and three
seeded runs — `rate_39`, `vol_0_4`, `r_15` — ended on it rather than on KKT; see
`summary.csv`. The first two match their previous KKT-certified objectives at the same
active set, to 4e-08 and 5e-06. `vol_0_4` did not, so it was re-run from a cold start as a
check: that converged on KKT in 39 evaluations to within 8e-04 percentage points of the
seeded design. "The objective stopped moving" is not an
optimality test, and a warm start close to the optimum often leaves the objective flat
on the first trial step: at
`ftol_abs=1e-8` that stopped `r_3_2` after four evaluations without it having moved at
all. The paper's own default, `ftol_abs=1e-3`, is looser still and shifted mandate shares
by up to 11.8 percentage points on the carbon-budget sweep.

## Running it

```
poetry run python preflight.py                  # budget, ReFuelEU feasibility, checks 3 and 4
poetry run python run_references.py             # 8 matched fossil-BAU references
poetry run python run_batch.py --jobs 3         # blocks A-D, 14 optimisations, resumable
poetry run python run_block_e.py --jobs 4 --seed ../lagrange/results_tight
                                                # block E, 55 optimisations, resumable
poetry run python collect.py                    # the three analysis tables
poetry run python plot_elasticity.py            # block A figure
poetry run python plot_sensitivities.py         # blocks B, B', C, D and the summary
poetry run python status.py                     # where blocks A-D have got to
poetry run python run_block_e.py --status       # where block E has got to
```

Each run is a subprocess whose whole output — GEMSEO's logger, the SLSQP progress bar,
any traceback — goes to `logs/<run_id>.log`, in the same format as the paper's own run
logs.

**Seeding.** With `previous_optima.csv` present, every run of blocks A–D starts from the
previous sweep's optimum for that same run, so none depends on another and all fourteen run
in parallel. `AEROMAPS_SEED=0` restores the old order, where `base` runs alone first and
the rest warm-start from it. Block E's `--seed DIR` does the same per rung; without it,
each case is a continuation chain down the ladder and runs one rung at a time. A seed is
only a start point: every run still has to meet the KKT criterion from there, and a run
that stops on anything else is flagged in `summary.csv`.

## Why the references exist

`cumulative_total_surplus_loss_discounted` is measured against 2019 unit economics applied
to the exogenous traffic trajectory, not against a no-policy scenario. Unit costs fall over
the horizon, so it is **negative for every scenario here** — fossil BAU included, at
−194 bn€. Only differences against a reference are policy costs, and the reference has to
share the run's parameters: the discount rate rescales the whole series and the elasticity
moves the traffic it is summed over. `run_reference_map.csv` says which reference each run
is measured against.

## Preflight findings

1. **The budget** is above.
2. **ReFuelEU-linear violates G5 in 2035** (+0.207): it needs biofuel to grow at
   25.4 %/yr, to 0.276 EJ, against a cap of 0.244 EJ — the volume branch, 0.089 EJ plus
   one period's 0.155 EJ capacity addition, which is now the more permissive of the two.
   Before the correction the violation was +0.352. It is feasible in four of the nine cap combinations of blocks
   B/B' — at 39 %/yr, and at 0.4 EJ/yr. Under the IEA NZE rate the binding constraint is
   not biofuel at all but *electrofuel in 2050*, violated by 0.96. So the iso-emissions
   comparison is not like-for-like at baseline settings; see
   `preflight_refueleu_feasibility.csv`.
3. **The ε = −1 branch is continuous** (1.03e-07 across −0.999 / −1.0 / −1.001).
4. **The 2019-technology reference is not elasticity-invariant** — rebound 1.046 at
   ε = −0.6 to 1.101 at ε = −1.4. Not a second anchor: all three consumers now read the
   single `initial_airfare_per_rpk`. It is that "2019 technology" is not "2019 prices" —
   fares fall from 0.1218 to 0.0859 against a 0.0924 anchor, so the multiplier is not 1.
   `rpk_no_elasticity` *is* exactly invariant and is the right decomposition reference.

## What the sweep found

- **Dedicated-wind electrofuel moves the mandate furthest** of any defensible parameter:
  53.2 → 90.4 % of the blend, electrofuel 13.9 → 49.2 %. Before the correction it moved
  2050 by nothing at all — the old ceiling had been capping electrofuel's growth once it
  was established, and G6 was binding in 2045 and 2050. Discounted at the objective's own
  rate, late wind electrofuel undercuts *early* biofuel (from 2037 it is cheaper than
  biofuel was in 2025), so the optimiser holds 2030 biofuel at 2 % against 10 % and buys
  the abatement back after 2040. It never undercuts biofuel in the same year.
- **Ramp-up limits come next.** They move the 2050 mandate from 52.8 % to 62.8 %, against
  51.9–55.8 % across ε = −0.6…−1.4. A tighter ramp cannot abate early, and against a
  *cumulative* budget that means it must end higher, not lower.
- **Biofuel is biomass-capped in every run from 2045**, at 39–44 % of the blend. Most runs
  reach the cap by 2040; the ones that defer abatement — dedicated wind, 15 %, the two
  tight ramps — get there later. Past the cap every adjustment lands on electrofuel.
- **Elasticity raises the required mandate rather than lowering it.** Fares sit below the
  2019 anchor until 2046–2048, so the demand response *adds* traffic for most of the
  horizon and only suppresses it at the end: cumulative RPK exceeds fixed demand's by
  0.77 % at ε = −0.6 and 1.24 % at −1.4, even as 2050 RPK falls (2.388 → 2.333 Tpkm).
  Against a cumulative budget the early traffic has to be paid for later.
- **The discount rate is mechanical between 3.2 and 7 %, and decisive at 15 %.** At 3.2 %
  the optimum is bit-identical to the baseline: it sits on a *vertex* — ten active
  constraints in ten dimensions — and the objective only picks which vertex. At 15 % the
  vertex breaks and the mandate goes to 92 % of the blend, because 2050 costs are
  discounted by a factor of 66. The reported policy cost falls to 18.5 bn€ while the
  realised cost per tonne *rises*: it is the only run whose 2020–2050 average is positive,
  +11 EUR/tCO2 against the baseline's −30.

The realised cost per tonne is measured against the objective's own counterfactual — 2019
technology on the no-elasticity traffic, whose emissions are
`co2_emissions_last_historical_year_technology_baseline3` — so it is negative for most of
the horizon: against a world that froze in 2019 the scenario is both cheaper and cleaner.

## Files

| | |
|---|---|
| `run_batch.py` | blocks A–D: the matrix, the runner, the driver |
| `run_block_e.py` | block E: the budget ladder for all five cases |
| `run_references.py` | matched fossil-BAU references |
| `preflight.py` | the four preflight checks |
| `collect.py` | `sweep_by_year.csv`, `sweep_summary.csv`, `sweep_constraints.csv` |
| `status.py` | one-screen progress for blocks A–D |
| `plot_elasticity.py`, `plot_sensitivities.py` | the five figures |
| `efuel_dedicated_wind.csv` | the block C pathway trajectories |

Run outputs (`results/`, `results_e/`) and `logs/` are gitignored — about 215 MB, all of
it regenerable. The CSVs carry every number quoted above.

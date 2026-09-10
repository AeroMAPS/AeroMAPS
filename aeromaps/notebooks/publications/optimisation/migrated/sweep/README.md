# Overnight sweep — one parameter at a time, plus the regenerated Figure 9 surface

Two things live here. Blocks **A–D** are one-parameter sensitivities held at a single
carbon budget; block **E** re-runs the paper's carbon-budget × biomass ladder, which the
model changes below have made stale.

## The framing

Every run of blocks A–D meets the same absolute budget: the cumulative 2020–2050 CO2 of
**ReFuelEU (linear) at ε_P = −0.9**, computed once and held fixed.

| | |
|---|---|
| budget, EU perimeter | **3.8615905850 GtCO2** |
| as a share of the world aviation budget | **3.119357596 %** |

The constraint takes a share, but a share *is* an absolute budget here: when it is active
it pins `cumulative_co2_emissions[2050] = gross_carbon_budget_2050 × share / 100`, and both
factors on the right are exogenous. Verified across the elasticity runs — C2050 identical
to six significant figures while C2025 moved by 0.6 %.

Aviation's biomass allocation is a round **10 %**, not the reverse-engineered 9.90 %.

## Solver settings

The ftol stop is **off** (`FTOL = 0.0`); the KKT residual is the only convergence
criterion, with `max_iter` as the backstop. "The objective stopped moving" is not an
optimality test, and every run warm-starts from the baseline optimum where a
one-parameter change often leaves the objective flat on the first trial step: at
`ftol_abs=1e-8` that stopped `r_3_2` after four evaluations without it having moved at
all. The paper's own default, `ftol_abs=1e-3`, is looser still and shifted mandate shares
by up to 11.8 percentage points on the carbon-budget sweep.

## Running it

```
poetry run python preflight.py                  # budget, ReFuelEU feasibility, checks 3 and 4
poetry run python run_references.py             # 8 matched fossil-BAU references
poetry run python run_batch.py --jobs 3         # blocks A-D, 14 optimisations, resumable
poetry run python run_block_e.py --jobs 3       # block E, 55 optimisations, resumable
poetry run python collect.py                    # the three analysis tables
poetry run python plot_elasticity.py            # block A figure
poetry run python plot_sensitivities.py         # blocks B, B', C, D and the summary
poetry run python status.py                     # where blocks A-D have got to
poetry run python run_block_e.py --status       # where block E has got to
```

Each run is a subprocess whose whole output — GEMSEO's logger, the SLSQP progress bar,
any traceback — goes to `logs/<run_id>.log`, in the same format as the paper's own run
logs. `base` is a barrier: it runs alone because everything else warm-starts from it.

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
2. **ReFuelEU-linear violates G5 in 2035** (+0.352): it needs biofuel to grow at 25.4 %/yr
   against the 20 %/yr cap. It is feasible in four of the nine cap combinations of blocks
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

- **Ramp-up limits dominate.** Across defensible parameter ranges they move the required
  2050 mandate from 52.8 % to 70.9 %, against 57.2–61.9 % for the whole elasticity range.
  A tighter ramp cannot abate early, and against a *cumulative* budget that means it must
  end higher, not lower.
- **Biofuel is biomass-capped in every single run.** It saturates near 39–41 % by 2040 and
  barely moves between scenarios. Every adjustment the optimiser makes lands on
  electrofuel.
- **Dedicated-wind electrofuel changes nothing about the schedule.** Its abatement cost
  roughly halves — the grid pathway abates *nothing* before 2028, since it emits more than
  the kerosene it replaces — and with G4 dropped entirely it still enters no earlier than
  2040 and moves 2050 by 0.9 pp. The driver is cost ordering against biofuel, not carbon
  intensity.
- **Elasticity raises the required mandate rather than lowering it.** Fares sit below the
  2019 anchor until 2044, so the demand response *adds* traffic for most of the horizon
  and only suppresses it at the end: cumulative RPK rises with |ε| (+0.60 % to +0.90 %)
  even as 2050 RPK falls (2.357 → 2.264 Tpkm). Against a cumulative budget the early
  traffic has to be paid for later.
- **The discount rate is mechanical between 3.2 and 7 %, and decisive at 15 %.** At 3.2 %
  the optimum is bit-identical to the baseline: it sits on a *vertex* — ten active
  constraints in ten dimensions — and the objective only picks which vertex. At 15 % the
  vertex breaks and the mandate goes to 92 % of the blend, because 2050 costs are
  discounted by a factor of 66. The reported policy cost falls to 18.5 bn€ while the
  realised cost per tonne *rises* to 442 EUR: at that rate the objective stops measuring
  what the policy costs.

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

# Step 0 — results

Run: `poetry run python step0_checks.py` (8 plain MDAs, ~20 s total).
Tables: `step0_check1_calibration.csv`, `step0_check2_branch.csv`.

## Check 2 — the eps = -1 branch: **PASS**

`scenario_cost.py:501` branches on `price_elasticity == -1` and the log branch is
reached. Surplus is continuous across the switch:

| eps | branch | area_loss 2050 [M€] |
|---|---|---|
| -0.999 | power | 1.8734023e10 |
| **-1.000** | **log** | **1.8750540e10** |
| -1.001 | power | 1.8767053e10 |

The log value sits 1.03e-07 (relative) from the midpoint of its two power-branch
neighbours. No discontinuity, no mis-set branch selector.

Caveat, not a failure: the selector is an exact float comparison (`== -1`), so it
only fires on a value that is exactly -1.0. That is fine for the five sweep
values, which are literals.

## Check 1 — elasticity-invariance of the calibration point: **FAIL**

2019-technology reference (drop-in efficiency gain set to 0, no mandate), five
elasticities. Traffic does **not** coincide: spread reaches **5.1 % by 2050**.

### The beta(t) recalibration is not the cause

`rpk_no_elasticity`, the exogenous anchor Q0(t) that beta is built from, is
**exactly** identical across all five elasticities — max absolute difference
`0.000e+00`. beta(t) = P / Q0(t)^(1/eps) is therefore doing what the paper says.

### The cause is that the model has three anchor prices, and two of them disagree

| what | anchored at | value |
|---|---|---|
| inverse supply function (`total_airline_cost_and_airfare.py:392`) | `initial_airfare_per_rpk` | 0.09236379 (2019) |
| traffic response (`rpk_market.py:598`) | `initial_airfare_per_rpk` | 0.09236379 (2019) |
| surplus beta (`scenario_cost.py:497`) | `airfare_per_rpk[2025]` | **0.09058 – 0.09071** |

Supply and demand are anchored on one price, as the code comment intends. The
surplus integral is not: it is anchored on the scenario's *computed* 2025 fare,
which sits 1.8–2.4 % below the 2019 anchor.

### Consequence: the elasticity is already active in the base year

The multiplier is `(airfare / initial_airfare)^eps`, which equals 1 only when the
fare equals the anchor. It does not, so at 2025 — the first projected year —
traffic is already above Q0 by an eps-dependent amount:

| eps | fare2025 / anchor | multiplier at 2025 | rpk/rpk0 at 2025 |
|---|---|---|---|
| -0.6 | 0.980698 | 1.011763 | 1.011763 |
| -0.9 | 0.981245 | 1.017186 | 1.017186 |
| -1.4 | 0.982095 | 1.025617 | 1.025617 |

The measured `rpk/rpk0` matches `(fare/anchor)^eps` to six decimals, which
confirms the mechanism rather than inferring it.

So every run in the sweep would start from a different base-year traffic, by
+1.2 % (eps=-0.6) to +2.6 % (eps=-1.4). That is a **calibration rebound, not a
policy response**, and it scales with the parameter being swept.

The same mismatch is present in the paper's existing optimisation runs:
`opt_main_2_6` has `airfare_per_rpk[2025] = 0.09012` against the 0.09236 anchor,
a 2.4 % gap.

### How much does it matter

At 2050 the policy-driven demand loss in a tight-budget run is ~11 % (B15 @ 2.6,
relative to `rpk_no_elasticity`). The base-year rebound at eps=-0.9 is ~1.7 %.
So roughly 15 % of the apparent demand response is calibration offset rather
than cost response. Not fatal, but too large to leave unstated in a section whose
headline is the size of the demand channel.

---

# Remedy applied: anchor the surplus beta on the shared reference price

`scenario_cost.py` now computes

    beta = initial_airfare_per_rpk / rpk_no_elasticity**(1/eps)

instead of using `airfare_per_rpk[2025]`. All three anchors — inverse supply,
traffic response, welfare curve — are now the same 2019 price, so the demand
curve used for welfare is the demand curve used for traffic, and the calibration
no longer depends on which scenario is being evaluated.

## Verification: the change does exactly this and nothing else

Diffing every output of two runs, before against after:

| run | outputs bit-identical | changed | largest change outside the surplus family |
|---|---|---|---|
| 2019 reference (uncoupled) | 567 | 4 | **0.000e+00** |
| ReFuelEU (full MDA) | 437 | 4 real + 130 at 1e-14 | 4.6e-14 |

The four are `area_loss`, `area_loss_discounted`, `cumulative_total_surplus_loss`
and `..._discounted`. `area_loss` scales by a single constant — min ratio = max
ratio = `initial_airfare / airfare[2025]` to 8 decimals (1.01911376 and
1.02461440 respectively). The 1e-14 residue in the coupled run is MDA
convergence noise: the discipline no longer consumes `airfare_per_rpk`, so the
solve order shifts slightly.

Check 2 still passes after the change (1.048e-07).

## Check 1 still fails, by design of this remedy

Traffic is untouched — the 5.148e-02 spread is unchanged to every digit. The
base-year rebound (+1.2 % at eps=-0.6 to +2.6 % at eps=-1.4) remains, because it
comes from the *traffic* anchor being a 2019 price while the model's own 2025
fare sits ~2 % below it. Mitigation for the sweep: decompose against
`rpk_no_elasticity`, which is exactly elasticity-invariant (0.000e+00), and
report the rebound per elasticity as a stated offset.

## Consequence: the paper's existing optimisation runs are now stale

The surplus loss **is** the optimisation objective, so re-anchoring beta changes
it. At the stored optima:

| run | beta factor | surplus share of objective | objective change |
|---|---|---|---|
| opt_main_2_6 | 1.0249 | 90.5 % | +2.25 % |
| opt_main_3_0 | 1.0249 | 14.9 % | -0.37 % |
| opt_B15_2_6 | 1.0249 | 98.0 % | +2.44 % |
| opt_B5_2_6 | 1.0249 | 85.7 % | +2.13 % |
| opt_pess_2_6 | **1.0211** | 85.1 % | +1.79 % |

Two things to note. The factor differed *between cases* (1.0249 vs 1.0211 for
pess) because it was built from each scenario's own fare — that is the
comparability defect this fixes. And the surplus share of the objective ranges
from 15 % to 98 % across the budget ladder, so the reweighting is not uniform:
the optimum moves, by different amounts at different budgets.

So `../results/` and `../lagrange/results_tight/` were produced under the old
calibration. They are not wrong, but they are no longer consistent with the
model, and would need re-running before the article quotes both them and
anything from this folder.

# Second model change: the eps = 0 limit

`TotalSurplusLoss` is on the discipline chain whichever objective is selected, so
the eps -> 0 anchor hit `ZeroDivisionError` on `1/price_elasticity`. Added the
limit: at zero elasticity demand is vertical, Q = Q0, and the area between them
is zero. The surplus branch is now three-way (0, -1, otherwise).

A `cost` objective was also added to `optimisation_runs.setup_optimisation` — the
airline-cost term of the surplus objective on its own, which is what the
published problem reduces to when demand cannot respond. Same constraint set and
scaling, so the two are comparable. Additive: no existing path changes.

> **Status.** Written against `../results/` before the tight re-sweep and before
> the active-set fix in `extract_multipliers.py`. Superseded in three places:
> §4/§5 treat `opt_B15_2_6` as a suspect multiplier — direct measurement since
> showed it is a correct one-sided derivative at a kink (339.5 tightening vs
> 235.8 loosening); the KKT-residual tier in §4 predates identifying the active
> set from stationarity, which closes every feasible run to ~1e-15; and the
> blend-completeness ceiling is now 99.999 %, not 100 %. Current numbers live in
> `analysis_tight/`. See `README.md`.

# Lagrange multipliers of the ReFuelEU optimisation — extraction and validation

Diagnostic run over the stored optimisation histories in `results/`. The
optimisation problem was not modified and no run was re-executed.

Regenerate with, in order:

```
poetry run python extract_multipliers.py     # -> lagrange_multipliers.csv
poetry run python validate_multipliers.py    # -> validation_*.csv (aggregate)
poetry run python validate_pointwise.py      # -> validation_run_quality.csv (per-run)
poetry run python robustness_multipliers.py  # -> robustness_*.csv
poetry run python compare_fuel_mac.py        # -> shadow_price_vs_fuel_mac.csv
poetry run python plot_multipliers.py        # -> fig_*.png
```

---

## 1. The API actually found

GEMSEO **6.2.0**, `gemseo/algos/lagrange_multipliers.py`:

```python
LagrangeMultipliers(opt_problem).compute(x_vect, ineq_tolerance=1e-6, rcond=-1)
  -> dict[str, tuple[list[str], ndarray]]
     # keys: "lower_bounds", "upper_bounds", "inequality", "equality"
```

Also `get_multipliers_arrays()` (per-constraint arrays with the zeros filled
in), and the attributes `kkt_residual` and `constraint_violation`.

It is the post-optimal KKT least-squares that was expected: `rhs = -∇f(x*)ᵀ`,
`lhs` the active-constraint Jacobian transposed, solved with
`scipy.optimize.nnls` when no equality constraint is active — which is this
problem — and falling back to `lsq_linear` with bounds otherwise. SciPy's SLSQP
returns nothing itself.

Three things differ from what the docs suggest and matter in use:

- `x_vect` must be **unnormalised**. The class normalises internally if the
  problem asks for it.
- **`rcond` is accepted and never used.** It appears in the signature and in the
  docstring; the body never references it. Passing it does nothing.
- The class docstring states `λ_ℓ ≤ 0` for lower bounds. The implementation
  folds the sign into the Jacobian (`lb_jac_act *= -1`) before calling `nnls`,
  which cannot return a negative, so **every returned multiplier is ≥ 0**,
  lower-bound multipliers included. The docstring contradicts the code.

**Sign convention:** `g(x) ≤ 0`, all multipliers ≥ 0, returned in four separate
categories.

**Normalisation:** nothing to undo. The runs set `normalize_design_space=False`
and the restored problems report `expects_normalized_inputs == False`. Even had
they not, design-space normalisation cancels for *constraint* multipliers —
objective and constraint Jacobians are taken with respect to the same variable —
though it would not cancel for design-variable **bound** multipliers, which get
an explicit `norm_factor`.

What does have to be undone is the **objective scaling applied in
`setup_optimisation`**: `problem.objective = problem.objective * 1e-10`. The
stored objective is literally named
`1e-10*cumulative_total_surplus_loss_discounted_obj`, and the scale is parsed
back off that name rather than hard-coded. The min-CO2 runs carry a different
scale (`10*`) and a different objective entirely.

**A units correction.** `cumulative_total_surplus_loss_discounted_obj` is
documented `[M€]` in `scenario_cost.py`, but it is computed as `€/RPK × RPK`
with `rpk` in RPK, so it is **euros**. `f_opt = 8.82` at scale `1e-10` is
8.82e10 € = 88.2 Bn€, which is the right order for the published figure. The
`[M€]` docstrings on the cumulative surplus and airline-cost terms are stale.

## 2. Re-running was not needed

The HDF database stores, at the optimum, the objective gradient and all 26
constraint Jacobians. The only obstacle is that
`OptimizationProblem.from_hdf` calls `set_pt_from_database` for the objective
but **omits it for the constraints**, leaving a restored problem unable to
evaluate its own constraints. Applying that same supported call to the
constraints is enough to run GEMSEO's own `LagrangeMultipliers` entirely
offline.

**53 of 55 runs recovered.** Two cannot be:

| Run | Why |
|---|---|
| `opt_B15_2_2` | nearest gradient-bearing iterate is 2.6e-2 from `x_opt` |
| `opt_B15_2_4` | nearest gradient-bearing iterate is 9.7e-3 from `x_opt` |

SLSQP reports as `x_opt` the best-objective iterate, which is not always one it
differentiated: a run stopping on `ftol_abs` right after a line-search step
leaves that step ungradiented. These two would need re-running with identical
settings. `opt_pess_2_0` looked like the same failure but its gradient sits
1.1e-13 away — an exact-hash miss, not a different point — so it is recovered.
The distance is recorded on every row (`x_eval_distance_from_x_opt`) and the
threshold is explicit; nothing sits near it.

**Coverage.** 53 runs = 5 cases × (10 budget levels + 1 min-CO2), less the two
above. Of these, **44 are feasible** and 9 are not (see §4). The min-CO2 runs
are extracted but their multipliers are carbon, not money, and live in
`lambda_gtco2_per_unit_g` with the euro columns left empty.

One gap against the brief: the migrated `CASES` has no run labelled
*no new aircraft*. The closest is `pess` ("Low efficiency", 0.91 %/yr instead of
1.35 %/yr drop-in gain). I have **not** assumed these are the same thing — if
Section 4.4 is a distinct scenario, it is not in `results/`.

## 3. The aggregation is a true `max` (Step 1)

`constraints_rte._ramp_up_violation`:

```python
rate_cap   = previous * (1 + rate) ** dt      # depends on the design variables
volume_cap = volume * dt * EJ_PER_YEAR_TO_MJ  # a constant
cap = max(rate_cap, volume_cap)
out.append((current - cap) / volume_cap)
```

No KS, no p-norm — **a plain Python `max`**, so the constraint is non-smooth at
a switching point and there is exactly one multiplier per (fuel, year), not one
per branch.

The aggregate multiplier **can** be attributed, because the two branches are
distinguishable after the fact: `ramp_branch_active` recomputes both caps at the
stored optimum and records which one won. The attribution is safe as long as the
optimum is not sitting *at* the switch, where neither the multiplier nor the
finite-difference gradient is well defined. No run in the set sits there — the
two caps differ by a wide margin wherever a ramp constraint binds.

The distinction has real consequences, because the two branches respond to
different bounds. If the **volume** branch binds, `∂f/∂volume = -λ/volume` and
relaxing the rate does nothing. If the **rate** branch binds, `∂f/∂volume = 0`
exactly — the volume cap is not what is holding the system back — and the
meaningful derivative is with respect to `τ`. Both are in the CSV as separate
columns, and one of them is always exactly zero.

**Baseline (`opt_main_2_6`) active branches:**

| Constraint | 2030 | 2035 | 2040 | 2045 | 2050 |
|---|---|---|---|---|---|
| G5 biofuel | **volume, binding** | **rate, binding** | rate, slack | rate, slack | rate, slack |
| G6 electrofuel | volume, slack | volume, slack | **rate, binding** | **rate, binding** | rate, slack |

So for electrofuel, "the value of relaxing industrial deployment speed" is a
**rate** value in both years it binds; relaxing the 0.2 EJ/yr volume cap would
buy nothing there. For biofuel it is a volume value in 2030 and a rate value in
2035. Reporting a single "ramp-up shadow price" without that split would be
wrong.

## 4. Validation (Step 4)

### Sign and complementary slackness

On the **44 feasible runs the audit is clean**: zero negative multipliers, zero
nonzero multipliers on inactive constraints, zero active constraints with a zero
multiplier.

Every apparent violation traced to a run that **terminated infeasible**. Nine
runs, all at the tightest budgets, have `g_G1 > 0` by 4 % to 34 % — the carbon
budget is below what the system can physically reach, and SLSQP stopped either
on max-iterations or on a positive directional derivative. A point that is not
feasible is not a KKT point, so its "multipliers" are not shadow prices. They
are extracted and kept, but flagged `run_feasible = False`, and every downstream
figure and check excludes them. This is a physical result (an infeasible budget),
not a numerical defect.

| Case | Infeasible budgets (world share, %) |
|---|---|
| B5 | 2.0, 2.2, 2.4 |
| B75 | 2.0, 2.2 |
| pess | 2.0, 2.2 |
| main | 2.0 |
| B15 | 2.0 |

### Envelope check 1 — carbon budget

Numerical `d f*/d(budget share)` along each case's sweep, against
`-λ_G1/B · dB/d(share)`. Nothing in the finite difference uses a multiplier.

| Form | median abs. error | within 15 % |
|---|---|---|
| pointwise derivative | 4.5 % | 31/39 |
| integral (trapezoid) | **3.4 %** | 32/34 |

**Passes.**

### Envelope check 2 — biomass

`d f*/d(biomass share)` at constant budget across B5/B75/main/B15, against
`-Σₜ λ_G3,ₜ / share`. The multipliers summed are the **discounted** ones,
matching the discounted objective.

| Form | median abs. error |
|---|---|
| pointwise derivative | 24.7 % |
| integral, all intervals | 16.0 % |
| integral, intervals where G3 binds | **16.0 %** |

**Above the brief's 10–15 % threshold.** Rather than stop there, I chased the
cause, because a 16 % scatter and a 16 % bias mean very different things:

- **Not grid coarseness.** Coarsening the well-resolved budget axis to a 4-point
  grid leaves its error at 2.9 % — it does not reproduce 16 %.
- **Not quadrature error.** Replacing the trapezoid with exact integration of a
  cubic through all four predicted derivatives makes it *worse* (22 %), and the
  errors alternate in sign.
- **Not a units, normalisation or discounting bug.** Regressing observed against
  predicted through the origin:

| Check | n | slope | bias | R² | residual scatter |
|---|---|---|---|---|---|
| G1 / carbon budget | 34 | 0.9920 | **−0.80 %** | 0.898 | 9.6 % |
| G3 / biomass | 18 | 0.9672 | **−3.28 %** | 0.914 | 17.8 % |

A units or normalisation error would move the slope off 1 and push every point
the same way. Both slopes sit on 1. **The multipliers are unbiased; the 16 % is
scatter.**

Its source is visible in the data: the biomass axis has only four points, the
envelope derivative changes ~55 % per interval (against ~15 % on the budget
axis), and the **active set changes at nearly every grid point** —
`n_active_G3` runs 4 → 3 → 3 → 2 along a single budget row. `d f*/d(biomass)` is
piecewise-smooth with kinks *between* the samples, and no quadrature scheme
recovers that from four samples. The grid cannot validate λ_G3 more tightly than
this; that is a limit of the available runs, not evidence against the numbers.

### Envelope check 3 — direct measurement, and the subdifferential (the authority)

Checks 1 and 2 infer the derivative from the sweep grid, whose 0.2 spacing in the
budget share cannot resolve it. ``envelope_direct.py`` measures it instead: move
the bound by ±0.01 share points and re-optimise from the stored optimum, so both
points are on the same branch. The perturbed solves use **tight** solver settings
(``ftol=1e-8``, ``kkt_tol_rel=1e-6``); with the published ``ftol_abs=0.001`` the
objective moves only ~0.5 scaled units across the perturbation and the reference
inherits the very defect it is meant to measure.

The essential refinement is to keep the two one-sided secants apart rather than
averaging them. The optimum is a **vertex** - see §7 - so the active set changes
as the bound moves and `f*` is piecewise smooth. At a kink there is no
derivative, only a subdifferential ``[right, left]``, and a central difference is
the mean of two different one-sided slopes, which nothing is obliged to equal.

| Run | right | λ_G1 | left | kink | λ in subdiff | rel. KKT |
|---|---|---|---|---|---|---|
| `opt_main_2_6` | 228.8 | **229.0** | 229.1 | 0.1 % | yes | 1e-16 |
| `opt_main_2_8` | 188.5 | **211.2** | 275.5 | 37.5 % | yes | 2e-16 |
| `opt_B15_2_6` | 235.7 | **338.5** | 339.5 | 36.1 % | yes | 4e-15 |
| `opt_B5_3_4` | 172.9 | **196.6** | 175.8 | 1.6 % | **no** | 0.091 |
| `opt_main_3_0` | 178.5 | **209.8** | 181.6 | 1.7 % | **no** | 0.079 |

The split is exactly the KKT residual:

* **Well-converged (residual ~1e-16): λ_G1 is correct, 3 of 3.** Exact where `f*`
  is smooth (229.0 against 229.1/228.8), and a valid one-sided derivative where
  it kinks. `opt_B15_2_6` reproduces its *left* derivative to **0.3 %**.
* **Under-converged (residual ~0.08-0.09): λ_G1 is wrong by 12-17 %, 2 of 2**, and
  `f*` is smooth there (kink ~1.6 %), so the error is real rather than a
  one-sided-derivative artefact.

So the relative KKT residual is a reliable predictor of multiplier error, the
trust flags of the previous section separate the two groups correctly, and the
re-run set of §8 is justified on measurement rather than on principle.

**`opt_B15_2_6` was never broken.** Its λ is a legitimate one-sided derivative at
a 36 % kink; the shadow price really is discontinuous there. The anomaly that
prompted this whole investigation - 15 % biomass pricing above 9.9 % at a budget
share of 2.6 - is the marginal abatement cost curve **stepping across an
active-set change**, which is a result about the system, not a numerical fault.
It should be drawn as a step, not excluded.

### Pointwise checks — added after an anomaly was spotted in Figure 1

### Pointwise checks — added after an anomaly was spotted in Figure 1

The aggregate statistics above are necessary but **not sufficient**: a single bad
run barely moves a median. Figure 1 originally showed the 15 %-biomass case with
a *higher* shadow carbon price than the 9.9 % case at a budget of 2.6, which is
backwards — more biomass must make abatement cheaper. Two pointwise tests were
added, and they locate the fault exactly.

**Bracket test.** The optimal objective is convex and decreasing in the budget,
so the point derivative at a grid node must lie between the secant slopes either
side. For `opt_B15_2_6` the secants are 266 and 197 €/tCO₂ while λ_G1 reports
**338.5** — outside its own neighbours' bracket, so it cannot be right.
Infeasible neighbours are excluded, since they are not on the optimal-value
curve.

**Gradient-consistency test.** The surplus objective is the *same* function in
every run — only the budget constraint changes — so a gradient stored at one
run's optimum can be tested against the objective *value* at a neighbouring
run's optimum, with no re-run. Across the whole set the stored gradients are
excellent: **median error 0.0 %, typically 0.05 %**. The sole exception is the
interval touching `opt_B15_2_6` (−2.3 %, and −4.9 % on the other side before the
missing-gradient runs were excluded). Blame is attributed by exoneration: a run
sitting in a passing interval has a demonstrably working gradient, which leaves
`opt_B15_2_6` as the only culprit.

**What `opt_B15_2_6` actually is.** The first diagnosis - that the bad gradient
caused the error - was wrong, and three candidate causes were eliminated by
direct test rather than by argument:

| Hypothesis | Test | Outcome |
|---|---|---|
| Share-clipping corrupts the gradient | inward differencing (+0.04 % vs -2.34 % forward) | λ **unchanged** at 338.5 |
| MDA residual floor | `max_mda_iter` 50 -> 400 | f identical to 10 dp, λ **unchanged** |
| Degenerate active set | LP over the near-null space | exactly determined, identifiable to **±3 %** |

The clipping is real - a forward step on either 2050 share does cross the
renormalisation, and the whole forward/backward discrepancy sits in those two
components - but it is not causal: the clip perturbs the objective and the
constraints in the same directions, so the errors cancel in the KKT solve. The
MDA correlation looked stronger still (B15's log carries 27 non-convergence
warnings against zero for B5 and B75, at exactly the four defective budgets) and
is also not causal, since raising the iteration cap changes nothing at the
optimum. Both are recorded here as red herrings because both looked conclusive.

**The bracket test's premise fails on this run.** ``envelope_direct.py`` measures
`d f*/d(budget)` the only way that settles it: move the bound by ±0.01 share
points and re-optimise from the stored optimum, so the two points are on the
same branch. The result:

| quantity | €2020/tCO₂ |
|---|---|
| direct measurement (ground truth) | **287.6** |
| λ_G1 from the KKT solve | 338.5 (**+17.7 %**) |
| secant bracket from the 0.2-spaced grid | [197, 266] |

The ground truth is itself **outside** the bracket, so `f*` is not convex there
and the bracket test cannot be applied. The reason is structural:
`opt_B15_2_6` is the only run in the set where the blend-completeness constraint
binds - drop-in shares sum to exactly 100 % - so its optimum sits at a
non-smooth corner, in a different regime from its neighbours. λ there is a
one-sided derivative at a kink.

So the error is **+17.7 %, not 46 %**: worse than the ~1-3 % of a well-behaved
run, but a real multiplier at a genuine KKT point rather than a broken number.
**Treat the bracket test as a screen, not a proof** - it flags runs worth
investigating, and a flag is not by itself a verdict.

**Result.** With the four screened runs excluded, the shadow price is
**monotone decreasing in biomass share at every budget**, which is the behaviour
the economics requires and was the reason the anomaly was worth chasing. (The
one apparent exception, main vs B15 at a budget share of 3.8, is the two runs
agreeing to eight significant figures: biomass has stopped binding for both, so
extra biomass buys nothing.)

| Tier | Runs | Meaning |
|---|---|---|
| trustworthy | 20 / 39 | feasible, KKT residual < 1e-2, passes both pointwise tests |
| imprecise | 15 | passes both tests but stopped on `ftol_abs` (KKT residual 1e-2 … 0.11) |
| screened out | 3 | `opt_B5_3_4`, `opt_B75_3_2`, `opt_main_3_0` - all under-converged; two measured 12-17 % wrong against ground truth |
| kinked but valid | 1 | `opt_B15_2_6` - a one-sided derivative at a 36 % kink, correct to 0.3 %; plot as a step |

## 5. Noise (Step 5)

**Active-set tolerance.** Swept over `1e-10 … 1e-1` on the baseline. The
multiplier set is **identical across five orders of magnitude, `1e-6` to `1e-1`**.
It only changes at `≤ 1e-8`, where G6-2040 (`|g| = 2.6e-8`) is misclassified as
inactive and drops out; λ_G1 then jumps by +17.5 % and the rest shift. The run's
own tolerance, `1e-4`, sits in the middle of the stable plateau. Not a source of
noise here.

**Convergence.** Median 20 design points and 19 gradient evaluations per run.
The relative KKT residual (‖residual‖ / ‖∇f‖) is essentially zero for most runs
— median **9.9e-16** — but **19 of 44 feasible runs exceed 1e-2**, up to 0.114.
Every one of them terminated on `ftol_abs`, and they cluster at the **loose**
budgets (3.0–3.8). `ftol_abs = 0.001` on an objective of order 1–30 stops those
runs before stationarity is reached, so their active-constraint gradients cannot
cancel ∇f to better than 1–11 %. This is the dominant noise source and it lines
up with where the biomass check was worst.

**Finite-difference step.** Not varied — honestly, because it cannot be. The step
(`1e-6`, recorded in every HDF) is baked into every stored gradient, so changing
it requires re-running. The envelope checks bound the same error from outside
without a re-run.

## 6. What is publishable

**Trustworthy:**

- **λ_G1, the shadow carbon price, on the 20 runs flagged `trustworthy`.**
  Validated against an independent finite difference at −0.80 % bias with 9.6 %
  scatter, stable across five orders of magnitude of active-set tolerance, and
  passing the bracket and gradient-consistency tests. Baseline
  **229 €2020/tCO₂**; **96–411 €/tCO₂** across the grid. Use
  `validation_run_quality.csv` to filter — **do not use the raw λ_G1 column
  unfiltered**, because `opt_B15_2_6` is wrong by 46 % and would invert the
  biomass ordering.
- **The qualitative structure of the annual multipliers** — which constraints
  bind when, which branch of the ramp-up `max` is active, and the ordering
  between them. This comes straight from stored constraint values and is not
  sensitive to any of the above.

**Usable with a stated caveat:**

- **λ_G3 / λ_G4 (biomass, electricity) as a curve or an aggregate.** Unbiased to
  3.3 %, but individually scattered at ~18 %. Quote them to two significant
  figures at most (baseline biomass 16–24 €/GJ, electricity 9.2 €/GJ ≈ 33 €/MWh),
  and do not build an argument on a year-on-year difference of less than ~20 %.
- **λ_G5 / λ_G6 (ramp-up).** Never validated independently — there is no sweep
  over the ramp-up bounds to differentiate along, so the envelope test cannot be
  run at all. They satisfy stationarity and complementary slackness, and their
  branch attribution is solid, but they rest on the KKT solve alone. Present as
  indicative.

**Not publishable:**

- **Anything from the 9 infeasible runs.** No KKT point, so no shadow price.
- **Any multiplier from the 19 feasible runs with relative KKT residual > 1e-2**
  at better than ~10 % precision. These are the loose-budget runs; the right fix
  is a tighter `ftol_abs` and a re-run, not post-processing.
- **`opt_B15_2_2` and `opt_B15_2_4`** — no gradient at the optimum.

**Cheapest thing that would improve this:** re-run the sweep with a tighter
`ftol_abs`. That would fix the 19 high-residual runs, likely recover the two
missing-gradient runs, and probably pull the biomass check inside 10 %. Adding
intermediate biomass shares would do the rest, by resolving the active-set
switches that currently fall between grid points.

## 7. How to read the shadow carbon price

**It prices a stock, not a flow.** G1 caps *cumulative* CO2 over 2025-2050 and
treats a tonne in 2030 as identical to a tonne in 2050, so the whole window
carries **one** multiplier. λ_G1 is therefore the present value, in 2020 euros,
of the welfare loss avoided per extra tonne allowed *anywhere* in the window.
It is not a year-2030 or year-2050 carbon price, which is why the
`_undiscounted_year` column is empty for G1: there is no single year to
undiscount to.

Note the asymmetry that makes this easy to misread: the **numerator is
discounted** (the objective is discounted surplus loss) and the **denominator is
not** (tonnes of CO2 are physical and undated).

**Converting to a year-t price.** Because the constraint is a stock and the
objective is discounted, the first-order condition equates *discounted* marginal
abatement costs across years, so the implied year-t price is
`λ (1+r)^(t-2020)` - rising at 4.5 %/yr, the standard Hotelling path. That
identity holds only in years where the budget is the sole binding constraint.

**It is not the marginal fuel's abatement cost.** Four structural reasons, and
`compare_fuel_mac.py` shows all of them at once for the baseline:

| Year | Biofuel MAC | Electrofuel MAC | λ_G1 implied | ratio | binding |
|---|---|---|---|---|---|
| 2030 | 380 | 2554 | 356 | 0.9 | G5 |
| 2035 | 380 | 1234 | 443 | 1.2 | G5 |
| 2040 | 380 | 1009 | 552 | 1.5 | G3+G6 |
| 2045 | 380 | 874 | 688 | 1.8 | G3+G6 |
| 2050 | 380 | 762 | 858 | 2.3 | G3+G4 |

(€2020/tCO₂; fuel MACs are `(MFSP_alt − MFSP_kero)/(EF_kero − EF_alt)`, carbon
tax excluded to avoid circularity.)

1. **Rationing.** While only the ramp-up binds (2030-2035) λ tracks the biofuel
   MAC to within ~10 %. From 2040 the biomass constraint binds, biofuel is
   capped, and λ leaves the cheap fuel behind - 2.3× by 2050.
2. **Demand response is part of the abatement.** The objective is *total surplus
   loss*, so abatement comes from flying less as well as switching fuel. By 2050
   λ (858) exceeds even the electrofuel MAC (762), because electricity and both
   ramp constraints bind too and the marginal tonne comes from traffic
   reduction - a welfare cost that appears in no fuel MAC.
3. **Welfare, not cost.** λ prices consumer-surplus loss plus airline cost
   increase; a fuel MAC is a pure cost ratio.
4. **System-wide and intertemporal.** Relaxing the budget re-optimises the whole
   trajectory; a fuel MAC is partial-equilibrium and single-year.

So λ_G1 is the **sector's system marginal abatement cost given every other
binding constraint**, and it should be compared with a social cost of carbon or
a policy carbon-price trajectory - not with a fuel's break-even price.

**The other multipliers are flow prices.** G3-G6 are enforced *per year*, so
each year carries its own multiplier and there is no Hotelling relation between
them; their `_undiscounted_year` columns are the meaningful ones for comparison
with year-dated costs.

## 8. Practical notes for re-running

**Disable GEMSEO's execution statistics before running sweeps in parallel.**
``ExecutionStatistics`` takes a shared-memory ``multiprocessing.Value`` per
discipline; macOS allows ``kern.sysv.shmmni=32`` segments system-wide and
``shmseg=8`` per process. One sweep of 106 disciplines fits. Five in parallel do
not, and the failure surfaces as ``OSError: [Errno 28] No space left on
device`` - on a disk with half a terabyte free, which makes it easy to
misdiagnose. ``aeromaps.core.gemseo.disable_gemseo_execution_statistics()``
replaces the shared memory with plain attributes and must be called before any
discipline is built. ``MultiRegionalProcess`` does this for itself;
``AeroMAPSProcess`` does not, so a script driving the plain process has to call
it.

**Convergence settings.** ``rerun_tight.py`` re-runs a sweep with
``ftol_abs=ftol_rel=1e-8``, ``kkt_tol_rel=1e-6`` and ``max_iter=200``, into
``results_tight/`` so the published histories are untouched. It changes solver
settings only. ``kkt_tol_rel`` is the one that matters for this exercise: GEMSEO
leaves it at ``inf``, and it makes SLSQP stop on the KKT residual - the quantity
that governs multiplier quality - instead of on objective stagnation.

**What does *not* need re-running.** The nine infeasible runs (every requested
budget is below its case's floor, computed from the min-CO2 runs: B5 2.48 %,
pess 2.40 %, B75 2.30 %, main 2.15 %, B15 2.12 % of the world budget), and the
two missing-gradient runs, which ``recompute_gradients.py`` repairs at the
stored optimum in ~20 s each instead of ~730 s.

## Output files

| File | Contents |
|---|---|
| `lagrange_multipliers.csv` | tidy table, 1373 rows — one per (run, constraint, year) |
| `validation_budget_envelope*.csv` | envelope check 1, pointwise and integral |
| `validation_biomass_envelope*.csv` | envelope check 2 |
| `validation_regression.csv` | bias-vs-scatter regression |
| `validation_slackness.csv` | sign / complementary-slackness audit |
| `validation_run_quality.csv` | **per-run trust flags — filter λ_G1 on this** |
| `validation_gradient_consistency.csv` | stored-gradient quality, per interval |
| `envelope_direct.csv` | `d f*/d(budget)` measured by re-optimising at a perturbed bound |
| `recomputed_gradients.csv` | gradients repaired at the stored optimum, no re-run |
| `robustness_tolerance_sweep.csv` | active-set tolerance sweep |
| `robustness_convergence.csv` | per-run iterations, KKT residual, termination |
| `shadow_price_vs_fuel_mac.csv` | λ_G1 against fuel-level abatement costs |
| `fig_shadow_price_vs_budget.png` | Figure 1 — marginal abatement cost curve |
| `fig_shadow_price_vs_time.png` | Figure 2 — annual shadow prices, baseline |

Both discounting conventions are in the table and never mixed: columns ending
`_discounted2020` are derivatives of the optimiser's own discounted objective;
`_undiscounted_year` multiplies by `(1+r)^(t−2020)`, r = 4.5 %. G1's
undiscounted column is empty by construction — it is a cumulative constraint
with no single year to undiscount to.

# Step 1 — fuel clearing: what works, what was measured, where this departs from the brief

Branch `feat/fuel-clearing-step1`, off the rebased spike
(`spike/unified-mda-global-discipline` on `optimisation/refueleu-migration-and-mda-dedup`).

Companion documents: [`INVENTORY.md`](INVENTORY.md) answers §2.3 and carries the
detail behind most of what follows.

---

## Status against §6

| criterion | state |
|---|---|
| `_setup_unified_mda` fix merged, with a test | **Already on this base** — `a27bd252`. No work needed (§1.1) |
| `INVENTORY.md` and the reference input set | **Done** |
| Kernel, tests 3.3.a–3.3.i green | **Done** — 21 tests, plus 3.3.j timings |
| New mode operational; current mode untouched; first coupled run | **Not started** (J4–J5) |
| Measurements 4.5.1 and 4.5.2, with figures | **Not started**. The 3.3.f figure exists |

Existing suite: **277 passed** (6 min 49 s), unmodified. Nothing in shared code has
been touched yet, so that is expected rather than reassuring — the guard-rail that
matters is the one after J4.

---

## 1. What changed under the brief

The brief was written against `fix/mda-convergence-strictness` @ `b74b8e12`, which is
45 commits behind the branch this work sits on.

**1.1 §2.1's blocking fix is already done.** At `b74b8e12` line 707 the unified MDA
chain really is built with `tolerance=1e-5` and no `max_mda_iter`. On this base it is
`1e-10 / 200`, landed by `a27bd252 fix(multi-regional): apply the unified_mda settings
that 3bdbfb8c only claimed`, with its test and its CHANGELOG correction. `80fcbeda`
also took the NaN flag out of the coupling vector and the clip out of `RPKElasticity`.
So the one piece of shared-code work the week planned for does not exist, and J1 was
the inventory and the bench alone.

**1.2 §2.2's gate is half-failed.** #158 (kerosene selectivity) is merged. **#157 is
still open** against `main`. Its content is present on this branch line and has since
been extended, so this is a procedural blocker, not a capability gap — flagged, not
treated as a stop, on the decision to branch from the rebased spike.

**1.3 `cvxpy` was not a dependency**, and neither was a parquet engine. Both went into
the **test group**, not core and not an extra: the mode is opt-in, and the default
mode must not make every AeroMAPS install carry a convex solver. The kernel imports
cvxpy lazily with an install hint. This needs revisiting when the mode ships.

---

## 2. The finding that changes what step 1 can claim

**The optimisation mode's ramp-up cannot be reproduced by a convex program.**

There is no ramp-up constraint in the core library at all —
`aeromaps/models/optimisation/constraints/energy_constraint.py` is commented out top
to bottom. The live one is per publication, `constraints_rte.py:130`, paper Eq. (12):

```
E_t  ≤  max{ E_{t-1}·(1+τ)^dt ,  E_{t-1} + dE·dt }
```

on volumes in MJ, at 5-year enforcement years. `q ≤ max(affine, affine)` describes a
**union of two convex sets**. It is not a tolerance problem; the feasible set is the
wrong shape. This is the trap `saf_market_skeleton.py` flags in D2(b) and that
`test_rampup.py` exists to demonstrate — the brief supplied both files, and the
collision with its own §3.1 input table went unnoticed.

The brief's `"relative"` form is the convex outer relaxation of Eq. 12:
`seed + (1+g)q_{t-1} ≥ max{(1+τ)q_{t-1}, q_{t-1}+dE·dt}` when `seed ≈ dE·dt, g ≈ τ`.
So the market is **strictly more permissive** than the optimisation's ramp-up, by the
smaller branch, and the two modes differ again in annual versus enforcement-year
enforcement.

Both forms are implemented; `"relative"` is the default. The gap is a quantified
divergence to report, not something to resolve silently. It does not affect test
3.3.c, which runs with the ramp-up deliberately loose.

---

## 3. The bench

Two regions differing only in traffic growth (3.0 % and 4.5 % CAGR), `unified_mda`,
two drop-in pathways — `hefa_fog` (sustainable) and `fossil_kerosene` (the residual
default) — shares fixed, top-down cost throughout. No hydrogen or electric pathway,
which side-steps the multi-type question for step 1.

**Departure from §2.4, deliberate:** `hefa_fog`'s mandate is **ReFuelEU Aviation's
obligation as a step** (2 % 2025, 6 % 2030, 20 % 2035, 34 % 2040, 42 % 2045, 70 %
2050), not the share the default 13-pathway config gives it. There, its shape comes
from five other sustainable pathways competing for feedstock; lifted out alone it
peaked at 4.8 % in 2030 and collapsed to 0.17 % by 2040, so the ramp-up never bound,
the buy-out never engaged, and measurement 4.5.2 would have had nothing to sweep.

### 3.1 What the reference measures

**The energy balance closes at machine precision** — max relative gap between
`Σ_p E_p` and `energy_consumption_dropin_fuel` is 0 (region A) and 1.15e-16
(region B). That is the number the market's own closure step is entitled to; a
correction materially larger is an error, not rounding.

**`q_init` for the sustainable pathway is zero**, and the current mode records it as
`NaN` rather than `0.0`. See §4.

**The step obligation binds hard.** Year-on-year growth of sustainable volume needed
to comply, region A: ∞ (from zero) in 2025, then +202 %, +233 %, +70 %, +24 %, +66 %
at the step years, against about +1 % between them. Any plausible ramp-up is violated
at every step and slack everywhere else. **The reference allocation is therefore not
itself ramp-up-feasible**, which is why 3.3.c must run with the ramp-up loose — as the
brief already specifies, though for a different reason than it gives.

**The cost of entry is a constant.** `hefa_fog_mean_mfsp` is flat at 0.02317 EUR/MJ
across every prospective year: the top-down cost has no volume dependence and, per
BRIEF3, there is no learning anywhere in `aeromaps/`. Every price dynamic the market
produces on this bench comes from the saturation term and the duals, never from the
supply curve moving. This bounds what measurement 4.5.1 can show and should be stated
in any write-up of it.

---

## 4. Decision 9 versus §4.2's bit-identity guard

Measured on the reference, over the 20 historical years, per region:
`hefa_fog_energy_consumption` and `hefa_fog_share_dropin_fuel` are **NaN in all 20**.
The cause is the mandate share being undefined before `prospection_start_year`, so
`share/100 × demand` carries the NaN into the volume. It does not propagate —
`dropin_fuel_mean_mfsp` is finite throughout, because `EnergyCarriersMeans` fills
before it weights — and `fossil_kerosene`, as the residual, is unaffected.

Decision 9 says the market emits zeros, never NaN. §4.2 says a reference run must be
identical bit for bit. **Both cannot hold on those two columns.**

Resolution taken: decision 9 wins, and the reproduction test compares historical years
with `NaN` treated as `0.0` on the reference side. `metadata.json` names the exact
columns (`historical_nan_columns`) so the comparison stays specific instead of
widening a tolerance everywhere. §4.2's actual guard — that the *current* mode is
unchanged — is untouched, since nothing in the market mode alters `EnergyUseChoice`.

---

## 5. The kernel

`aeromaps/models/impacts/generic_energy_model/fuel_clearing/kernel.py`. A pure
function: numpy in, numpy out, no AeroMAPS import, no state. cvxpy + Clarabel, one
solve over every region, pathway and prospective year.

### 5.1 Two things the analytic case settled

**The equality's dual is negated, and only the equality's.** cvxpy forms
`L = f + λ'(Sq − D)` for `Sq == D`, so `dL/dD = −λ`: the shadow price of demand is
minus the reported dual. The mandate and ramp-up inequalities need no flip. Before the
fix the energy price came out as −0.012 against an expected +0.012 — a plausible
number with the wrong sign, which is exactly why the brief insisted this be pinned by
the analytic case rather than read off documentation.

**Dual accuracy is not the solver tolerance.** Measured on the analytic case:

| `solver_tolerance` | energy price | compliance price | volume | status |
|---|---|---|---|---|
| 1e-7 | 2.7e-6 | 2.1e-4 | 1.1e-5 | optimal |
| **1e-9** (default) | 3.9e-9 | **2.2e-5** | 1.5e-8 | optimal |
| 1e-11 | 1.4e-11 | 1.2e-7 | 2.7e-11 | optimal |
| 1e-13 | — | — | — | `optimal_inaccurate`, refused |

All figures relative. The compliance price is consistently the weakest: it sits on the
curved power cone. At the brief's suggested 1e-9 it carries about 1e-5 relative error,
which is what the test tolerances are set from. The `optimal_inaccurate` refusal works
as specified.

### 5.2 Departures from §3.1

- **`demand_init` added** (R,). `"share_increment"` compares `q_t/D_t` against
  `q_{t-1}/D_{t-1}`, which is undefined at `t = 0` without the previous year's demand.
  The brief's input table has `q_init` but no demand counterpart. Required for that
  form only, and validated.
- **`residual_pathway` added.** §3.2's exact-closure step says to recompute "the
  kerosene" as `D − Σ others`, but the kernel only knows `is_sustainable`. Inferred
  when exactly one pathway is non-sustainable, required explicitly otherwise —
  mirroring `EnergyUseChoice`, where exactly one `default` per aircraft type is
  mandatory.
- **`average_cost` promoted to an output.** §3.1 lists it only inside `rent`, but it
  is what `market_mfsp` blends at `w = 0`, so it is worth reading directly.
- **`mandate_share` is a fraction, not a percentage**, and a percentage is rejected at
  the door. AeroMAPS uses percent throughout, so the discipline converts at the
  boundary; a silent factor of 100 here would be very hard to see downstream.

### 5.3 Tests

21 tests, all green, 11 s. 3.3.a–3.3.j plus input-hygiene cases.

**A note on tolerances.** Three tests failed on first run for the same wrong reason:
absolute MJ tolerances (`atol=1.0`) on quantities of order 1e13 MJ. Clarabel at 1e-9
on a problem scaled to max-demand-equals-one leaves about 1e4 MJ of noise, so
`atol=1.0` asserts on the solver's last bit. Volume comparisons now take their floor
from `max(demand) * 1e-7`. The same error in the other direction produced a rent
assertion of `abs=1e-3` on a quantity where a 4.6e-11 price error shows up as 371 in
currency; rent is now judged against revenue.

**Test 3.3.f was rewritten after it was found to pass trivially.** With the tight
ramp-up the module uses elsewhere, the ramp-up binds before the mandate does, the
volume stops responding, the buy-out covers the entire gap and the compliance price
sits flat on the buy-out across the whole sweep. A flat curve satisfies any continuity
bound while testing nothing. It now runs in the regime where the mandate sets the
volume, and tests continuity by **refinement** rather than against a magic constant:
halving the sweep step must roughly halve the largest jump between neighbours.
Measured ratios, over 100 → 200 points:

| `n` | 2 | 8 | 16 |
|---|---|---|---|
| ratio | 0.498 | 0.497 | 0.551 |

0.5 is what a continuous function gives; a genuine step would stay near 1.

One real discontinuity was found and is excluded from that test on purpose: at a
100 % mandate, kerosene is driven out of the mix entirely, the energy balance changes
character and the price moves by a real step (7.2× the sweep step at `n = 2`). That is
a property of the market, not a defect.

### 5.4 Sensitivities, and where the formulation stops solving

`sensitivity.py` sweeps each major parameter around a baseline that binds
(`n=4`, `γ=1`, `g=0.30/yr`, `w=0`, buy-out 0.05, discount 4 %, capacity 2.5× the
obligation). Region A, 2050 delivered price:

| parameter | swept over | spread in delivered price |
|---|---|---|
| pricing weight `w` | 0 → 1 | **37.3 %** |
| stiffness `n` | 1 → 16 | **15.9 %** |
| ramp-up `g` | 0.10 → 1.20 /yr | 3.8 % |
| intensity `γ` | 0 → 4 | 0.4 % |
| buy-out | 0.02 → 0.30 | 0.0 % |
| discount rate | 0 → 0.08 | 0.0 % |

`w` dominates, which is the point of decision 10 — it is a scenario lever, not a
calibration constant. The buy-out and the discount rate leave the *delivered price*
untouched at this baseline, although the buy-out sets the compliance price wherever it
binds; they move the policy cost, not the fuel bill.

**`γ`'s 0.4 % is misleading in isolation**, and the `(γ, n)` map explains why: at
`w = 0` and `n = 4`, γ from 0.25 to 1 moves the uplift only 0 → 0.4 %, because
`q/K ≈ 0.8` and `(q/K)^4` is already small. At `n = 1` the same γ range moves it
4 → 16 %. The two saturation parameters are not separable.

**Capacity sized on the obligation is undersized once the market anticipates.** With
1.25× headroom and a binding ramp-up, pre-building pushes `q/K` to **1.97** between
steps. Saturation then disciplines the pre-building — with `γ = 1` the market builds
less far ahead (peak `q/K` 1.29 rather than 1.97) — but the bench needed 2.5× headroom
before the sweeps would run.

**Half the `(γ, n)` grid does not solve.** 18 of 36 cells fail outright: everything
with `n ≥ 4` above `γ = 1`, and everything with `n ≥ 8` above `γ = 0.25`. This is not a
tolerance trade-off — Clarabel fails at 1e-9, 1e-8, 1e-7, 1e-6 and 1e-5 alike on
`γ = 1, n = 8`. **The brief's measurement 4.5.1 grid is `n ∈ {2,4,6,8,12,16}`, most of
which is unreachable at a saturation intensity that does anything.** Either the grid
shrinks to `n ≤ 2` at useful `γ`, or the power term needs reformulating (rescaling
`q/K`, or building the cone by hand rather than through `cp.power`) before 4.5.1 can
run as written. This is the step-1 analogue of the convexity ceiling the spike found in
the MDA, and it should be settled before J4's measurements, not during them.

### 5.5 Measured timings (3.3.j)

| case | solve |
|---|---|
| 2 regions × 2 pathways × 31 years (the bench) | 0.030 s |
| 9 regions × 10 pathways × 35 years (synthetic) | 0.51 s |

At 0.03 s per solve, a 200-iteration MDA spends about 6 s in the market. The 9×10×35
case at 0.5 s per solve would be 100 s per MDA, which is usable but not free — worth
knowing before the regional extension.

### 5.6 Figures

Regenerate all three with `poetry run python -m fuel_clearing_step1.figures`.

**`figures/reproduction.png`** — test 3.3.c drawn on the real bench. The market lands
on the reference allocation in both regions; the residual stays below **1e-8 of
drop-in demand** everywhere, an order of magnitude under the solver noise floor.

**`figures/rampup_regimes.png`** — a plausible ramp-up against the ReFuelEU steps, at
`g ∈ {15, 30, 60, 120} %/yr`. This is the most informative result so far, and it
confirms the behaviour §3.2 predicted:

**Perfect foresight builds ahead of the obligation.** At `g = 15 %/yr`, region A:

| year | 2029 | 2033 | 2034 | 2035 | 2039 | 2044 | 2049 |
|---|---|---|---|---|---|---|---|
| obligation | 2 % | 6 % | 6 % | 20 % | 20 % | 34 % | 42 % |
| built | **4.5 %** | **11.7 %** | **14.1 %** | 17.1 % | **28.9 %** | **36.0 %** | **59.9 %** |

The market holds more than it owes in every year between steps, because the ramp-up
cannot take it from 6 % to 20 % in the year the step arrives. Sustainable fuel is more
expensive here and discounting penalises early spend, so it builds the minimum needed
and no more. This is a result, not a bug — and it is exactly why a ramp-up checked
*after* the fact has no purchase in this mode (decision 3).

**The buy-out is needed once**, at the 2035 step and only at `g = 15 %/yr`: 2.94 % of
demand, where 17.1 % was built against 20 % required. The compliance price is **zero**
in every year where the market is ahead (the mandate is slack), positive where it
binds exactly, and pinned to the buy-out at 0.05 EUR/MJ in 2035.

**`figures/pricing_vs_current.png`** — the market's delivered price against the current
mode's `{at}_mean_mfsp`, which is the quantity that reaches the DOC, the airfare and
therefore the demand loop. The allocation is held fixed across all curves, so every
difference is the **pricing rule** and not a different set of volumes.

Two results:

**The bridge holds exactly.** At `w = 0` with saturation off, the market's delivered
price equals the current mode's to **6.9e-9** relative, across both regions and every
year. That is decision 10's claim, verified on the real chain's numbers rather than
asserted.

**`w` is inert only when nothing is scarce.** With `γ = 0` **and the ramp-up slack**,
`w = 0` and `w = 1` give the same delivered price to **1.1e-8** — not merely close,
the same number. With a flat marginal cost and no binding constraint, `λ_E = c_k` and
`λ_M = c_s − c_k`, so the sustainable pathway's marginal price is exactly `c_s`, which
is also its average cost, and decision 10's blend has two identical endpoints.

⚠️ **An earlier version of this section said "inert unless the saturation term is
active", which is wrong.** Scarcity from the *ramp-up* does the same job. Measured at
`γ = 0`, varying only the ramp-up limit:

| `g` per year | 0.10 | 0.20 | 0.30 | 0.60 | 1.20 | loose |
|---|---|---|---|---|---|---|
| `w=1` vs `w=0` | **+137 %** | +64 % | +32 % | +26 % | 8e-11 | 4e-11 |

When the ramp-up binds, the mandate cannot be met by building more now, so `λ_M` rises
above `c_s − c_k` toward the buy-out, the marginal price leaves the average cost, and
`w` becomes live with no saturation at all.

The correct statement is: **`w` is live wherever there is scarcity rent, from either
source.** For measurement 4.5.1 this still means `n` and `w` are not independent axes,
but the inert region is smaller than "γ = 0" — it is "nothing binds".

With saturation on (`γ = 1`, `n = 4`, capacity tracking the build-out at 1.25×), region A:

| | 2025 | 2030 | 2035 | 2040 | 2045 | 2050 |
|---|---|---|---|---|---|---|
| `w = 0` uplift | +0.3 % | +0.9 % | +2.6 % | +4.0 % | +4.8 % | +6.7 % |
| `w = 1` uplift | +1.4 % | +4.3 % | +13.1 % | +20.2 % | +23.8 % | +33.5 % |

The first row is the saturation markup — a cost the current mode has no concept of.
The second adds the inframarginal rent that marginal pricing passes to the consumer.
A 33 % difference in the price that drives the demand loop is not a detail, and it is
the reason `w` is a scenario lever rather than a calibration constant.

**`figures/sensitivity_oat.png`** and **`figures/saturation_map.png`** — §5.4.

**`figures/price_continuity.png`** — the compliance price against a mandate multiplier
at `n ∈ {2, 4, 8, 16}`, beside the unmet obligation. The curves steepen with `n` and
all pass through a common point where `q/K = 1`, since `(q/K)^n` is 1 there for every
`n`. A hard capacity cap is the `n → ∞` limit of that family, which is what decision 5
rejected.

---

## 6. Decision 6 is "top-down **for now**", and the guard should say why

The brief's ground for excluding bottom-up is "the bottom-up model reads volumes:
a volume → price → volume loop". That is true but it is not the real obstacle, and
taking it as the reason would point future work in the wrong direction.

**A loop is not the problem.** AeroMAPS closes loops for a living, and the kernel
already carries a volume-dependent cost *inside* the program: the saturation term
`c(1 + γ(q/K)^n)` is a marginal cost rising with quantity, and its integral is convex.
Volume-dependent cost is fine. What matters is the *direction*.

**What bottom-up actually does with volume** (`bottom_up/cost.py:245-288`): the mean
MFSP is a vintage-weighted average, `share_v = needed_capacity_v / (consumption +
unused)`, with each vintage's cost driven by `eis_capex` read off its EIS year. Per
BRIEF3 and confirmed here by grep, **there is no learning anywhere in `aeromaps/`** —
no capacity → cost feedback at all. So the dependence is a *mix effect*, not a supply
curve.

**And a mix effect runs the wrong way.** Where `eis_capex` declines with EIS year — the
usual scenario assumption — growing faster raises the share of cheaper new vintages, so
**average cost falls as volume rises**. A decreasing average cost makes the cost
integral concave, the program non-convex, and the duals stop being prices. That is the
thing iteration cannot fix, and it is what the guard is really protecting. (In the one
committed bottom-up config, `tested_configs/data/energy_carriers_data.yaml`, `eis_capex`
is flat, so the effect is absent there — but the structure admits a declining series and
real scenarios use them.)

Two routes when it is wanted, both real:

1. **MDA around the solve, not inside it.** Freeze `c` per iteration, keep the kernel
   convex, let Gauss-Seidel close volume → cost → volume. Cheap to build. The costs are
   specific: the answer becomes a fixed point that can depend on the starting point,
   which is exactly what decision 2 bought by using a solver; the duals become
   multipliers of a program whose own parameters are outputs, so they stop measuring
   the marginal cost of the system; and it adds a feedback to the SCC that the spike
   already measured a convexity ceiling on.
2. **Put the vintages in the program.** Make capacity a decision variable with its own
   annuity, so the vintage structure is explicit and the cost stays convex. This is
   what `saf_market_skeleton.py`'s D1/D2 already describe, and it is decision 4
   reopened — it needs a capex that is not *already* inside the cost, which is exactly
   why step 1 froze `K` against a top-down full cost.

This is structurally the same problem as the skeleton's NOTE-WACC: "une MDA autour du
solve, pas un solve unique". Route 2 is the principled one.

**Action:** the guard stays, but its message should name the concavity, not the loop,
so whoever hits it knows which of the two routes they are choosing between. Written up
here rather than implemented, since the guard itself lands with J4.

---

## 7. Open, in priority order

1. **J4–J5**: the `FuelClearing` global discipline, the mode, the coupled run, and
   measurements 4.5.1 and 4.5.2. The landing spot exists and is documented —
   `_load_global_models` uses `fuel_market` as its worked example.
2. **Mode-flag plumbing** (INVENTORY §7). `EnergyUseChoice` is regional and
   unconditional; the market is global. Recommended: one
   `regionalisation.fuel_market` key propagated to `AeroMAPSProcess` as a keyword
   beside `optimisation=False`, rather than repeated in every region's config.
3. **Multi-type guard** (INVENTORY §4). The new mode must raise, not silently
   under-serve, if a hydrogen or electric pathway is declared.
4. **Ramp-up form for the headline comparison** (§2). Both are relaxations of Eq. 12
   in different directions.

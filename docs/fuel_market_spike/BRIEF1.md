# Brief 1 — where the domain exit comes from, and what shape the divergence has

**Verdict, one sentence.** The NaN is a **repairable artefact** — the solver's
acceleration extrapolates the price coupling out of the physical domain, and one
non-total operation in `RPKElasticity` turns that into NaN — but repairing it only
**moves** the convergence boundary (γ\* from between 4 and 8, to between 8 and 10 at
`stiffness=0.3`); beyond the new boundary the iteration is a genuine bounded limit
cycle, so a structural limit remains.

All measurements below are on the Step-2 scenario
(`spike_unified_mda/scenario/regionalisation_spike.yaml`), `tolerance=1e-10`,
`MDAGaussSeidel`, 2 regions, 109 strongly coupled disciplines. The diagnosis was made
with nothing in `aeromaps/` modified — every fix measured as a probe wrapper on live
discipline instances. **Fixes 1–3 have since been implemented for real; see § 4.1.**

---

## 1. What produces the NaN

### 1.1 The exact line

`aeromaps/models/air_transport/air_traffic/rpk_market.py:547`

```python
multiplier.loc[proj] = (airfare_per_rpk.loc[proj] / airfare_init) ** price_elasticity
```

`airfare_per_rpk` goes **negative**, and a negative base to a fractional exponent is
not a real number. Measured at the first occurrence (`stiffness=0.3, gamma=8`,
`Alternate2Delta`, `RPKElasticity.compute()` call #15):

```
initial_airfare_per_rpk = 0.09236379319842411      price_elasticity = -0.9
airfare_per_rpk  min=-2.11219  max=0.109381        all finite: True
airfare_per_rpk  negative in 10 projection years   exactly zero in 0

  year          airfare            ratio     ratio**elast
  2041       -0.0226504         -0.24523              nan
  2050         -2.11219         -22.8681              nan

reproduction in isolation:
  python: (-0.24523010755770264) ** (-0.9) = (-3.3696897415710243-1.0948785672303982j)
  numpy : np.float64(-0.24523010755770264) ** -0.9 = nan
```

Python returns a complex number; numpy on a `float64` array returns `nan` silently.
That is the whole mechanism. It is **not** a division by zero, not a log of a
negative, not an overflow — `airfare_per_rpk` is exactly zero in **zero** years.

The origin probe confirms this is the *first* source, not a symptom. In the
`0.3 / 8` accelerated run there are **750** finite→non-finite transitions across the
chain; **58** of them are *manufactured* (the discipline's own inputs were all
finite). The earliest, by a margin of hundreds of discipline executions, is
`region_A_RPKElasticity` at execution 878, on `rpk` / `elasticity_factor` /
`rpk_<market>`, from year 2041. Everything else — `ASKMarket`, the energy chain,
the emissions chain — is downstream propagation.

### 1.2 Why the airfare is negative — and it is not the cost models' invention

The full path. Every step is linear in the carbon tax and none of them clamps.

| # | where | what happens |
|---|---|---|
| 1 | `spike_market_models.py`, `SpikeFuelMarket.compute` | `price = base * (1 + stiffness·ratio^gamma)`, and `ratio ≥ 0` always, so **the emitted price is never below `base_price`**. Measured over the whole run: `min(emitted) = 150.0` EUR/t exactly, `n_negative = 0`. **The market model is total.** |
| 2 | GEMSEO `Alternate2Delta` | takes the last 3 iterates and solves an **unconstrained** least-squares extrapolation (`gemseo/algos/sequence_transformer/acceleration/alternate_2_delta.py`). It has no notion of variable bounds. The value **received** downstream first goes negative at exchange *k*=6: **−163 057 EUR/t** over 15 projection years. |
| 3 | `SpikeMarketCarbonTax` | passes it straight through to `carbon_tax`. |
| 4 | `generic_energy_model/bottom_up/cost.py:662` | `pathway_unit_carbon_tax = carbon_tax * emission_factor` — linear, unclamped. |
| 5 | `direct_operating_costs.py:559` | `doc_carbon_tax_lowering_offset_per_ask_mean = global_mean * carbon_remaining_ratio`. **Measured `carbon_remaining_ratio = 1.0` exactly** (`carbon_offset = 0` in this scenario), so the offset ratio is *not* the culprit — I checked it specifically. |
| 6 | `total_airline_cost_and_airfare.py:226` | `total_cost_per_ask = ... + total_extra_tax_per_ask` → **negative**. |
| 7 | `total_airline_cost_and_airfare.py:90` | `airfare_per_rpk = airfare_per_ask / (load_factor / 100)` → −2.11 EUR/RPK. |
| 8 | `rpk_market.py:547` | → **NaN**. |

Cost decomposition at 2050, on the first negative `total_cost_per_ask` [EUR/ASK]:

```
doc_non_energy_per_ask_mean                            0.0330444
doc_energy_per_ask_mean                                0.0266674
indirect_operating_cost_per_ask                        0.028
doc_carbon_tax_lowering_offset_per_ask_mean           -1.88295      <-- the negative tax
(all other terms exactly 0)
---------------------------------------------------  ----------
total_cost_per_ask                                    -1.79523
```

**Reading of the brief's three priority suspects.** The elasticity model in
`rpk_market.py` is right — but it is where the NaN is *manufactured*, not where the
absurd value is *created*. The ad-hoc supply function is exonerated: it is total and
its floor holds. The `direct_operating_costs.py` chain is exonerated as a *source* —
its fault is the opposite one, that it is perfectly linear in the carbon tax and so
transmits a non-physical negative price without complaint to the one operation that
cannot take it.

**A 50 000 EUR/t price is indeed numerically unremarkable.** With plain
Gauss-Seidel the chain runs 200 iterations at prices up to 2.8 × 10⁷ EUR/t and
produces **zero** non-finite values. The NaN requires a *negative* price, and only
the accelerator produces one.

### 1.3 Secondary sources

With the price bounded, `RPKElasticity` *still* manufactures the NaN in the far-above
case, because `airfare_per_rpk` is itself an accelerated coupling — bounding the
price does not bound the airfare. Beyond that, and only later (execution 19 664 vs
5 818), a second family appears: `NOxEmissionIndex`, `SootEmissionIndex`,
`H2OEmissionIndex`, `SulfurEmissionIndex`, `EnergyCarriersMeanLHV`.

> **Correction, made while implementing the fixes.** I first read these five as
> share-weighted means going 0/0 as energy volumes collapse. They are not. Each does
> `origin_valid_years = origin_cumulative_share.replace(0, np.nan)` and multiplies by
> it — the NaN is a **deliberate sparsity marker** for "nothing of this kind is present
> this year", not an accidental division. Changing it would be a semantics change, not
> a robustness fix, so they were left alone. The genuine `0/0` sites are the
> ASK-weighted means in `direct_operating_costs.py`, and there are **six** of them, not
> the four this report first claimed.

The same non-total pattern exists in three more places, all raising a cost-chain
output to a fractional power:

- `price_and_income_elasticity.py:166,169` — `price_usd ** self.price_elast`
- `price_elasticity_logistic_income.py:204` — `(doc_net_energy_per_rpk_delayed / price_ref_eur) ** self.price_elast`
- `price_and_income_elasticity.py:165` — `(gdp_per_capita - covid_shift) ** self.income_elast` (a subtraction inside the base)

The first two are the same exposure as `rpk_market.py:547`, and worse in one respect:
their base is `doc_net_energy_per_rpk_mean`, which is **net of subsidy** and can
therefore go negative in a perfectly legitimate scenario, with no accelerator involved.

---

## 2. Is the divergence asymptotic or transient?

### 2.1 The three trajectories — plain Gauss-Seidel, no accelerator

![p_k trajectories](brief1_out/pk_trajectories.png)

| `gamma` | position | outcome | shape of `p_k` |
|---|---|---|---|
| 4 | below the boundary | converged, 68 it, residual 8.05e-11 | damped oscillation → 643.04 |
| 8 | just above | not converged, residual 3.74 | **bit-exact period-6 limit cycle** from *k*≈17 |
| 16 | far above | not converged, residual 7.37 | **bit-exact period-6 limit cycle** from *k*≈11 |

The cycles, repeating to the last printed digit for the remaining ~180 iterations:

```
gamma=8    150.594  151.815  151.740  13515.4  11067.3  11148.9   (repeat)
gamma=16   150      150      150      4.8425e6 2.6444e6 2.7034e6  (repeat)
```

**`p_k` does not grow monotonically.** It is bounded, strictly positive and finite
for all 200 iterations. The map is self-limiting at both ends: the market floors at
`base_price` when demand collapses, and demand collapses when the price explodes.

So **neither of the brief's two branches applies verbatim.** The answer is a third
shape: a bounded, non-contracting map with an **unstable fixed point** and a stable
periodic orbit around it. That matters for the reading — a limit cycle is a genuine
loop-gain problem (the fixed point repels), but it is *not* a numerical blow-up, and
it never needs to produce a NaN.

### 2.2 The wide price bound — 0.1× to 20× the fossil reference

`base_price = 150` EUR/t, so the bound is [15, 3000]. Acceleration on.

![domain exit](brief1_out/domain_exit.png)

| case | saturating iterations | non-finite | final residual | verdict |
|---|---|---|---|---|
| `0.3 / 8` | *k* = 0–8 and 17, then **releases for 183 iterations** | **0** | 9.27e-08, still falling | **transient excursion** |
| `0.3 / 16` | *k* = 0 … 201, continuously | 274 events from *k*=65 | 1.386 | **asymptotic** |

The `0.3 / 8` row is the brief's "bound binds at iterations 1–3, then releases"
signature, just with a longer transient than anticipated.

### 2.3 The totality fix, measured

The candidate fix (**T1**): make the multiplier *defined and saturating for any
airfare* by clipping `airfare / initial_airfare` into [0.1, 20] before the power, so
the demand response saturates at [20⁻⁰·⁹, 0.1⁻⁰·⁹] ≈ [0.065, 7.9] instead of
returning NaN (ratio < 0) or exploding (ratio → 0). **T2** is the same wide bound on
the cleared price. Applied as probe wrappers only.

| case | fix | status | iters | residual | NaN | price 2050 | rpk 2050 | clip last active |
|---|---|---|---|---|---|---|---|---|
| 0.3 / 8 | T1 | **converged** | 252 | 7.09e-11 | **0** | 1652.29 | 3.10079e13 | *k*=50 of 252 |
| 0.3 / 8 | T1+T2 | **converged** | 231 | 5.80e-11 | **0** | 1652.29 | 3.10079e13 | *k*=17 of 231 |
| 0.3 / 10 | T1 | not conv | 400 | 2.00e+00 | 0 | — | — | to the end |
| 0.3 / 12 | T1 | not conv | 400 | 2.01e+01 | 0 | — | — | to the end |
| 0.3 / 16 | T1 | not conv | 300 | 1.63e+00 | 0 | — | — | to the end |
| 0.3 / 16 | T1+T2 | not conv | 300 | 1.70e+00 | 0 | — | — | to the end |
| 3 / 8 | T1 | not conv | 300 | 7.97e-01 | 0 | — | — | to the end |
| 3 / 8 | T1+T2 | not conv | 300 | 1.88e-01 | 0 | — | — | to the end |

Two things to take from this table.

1. **The fix eliminates NaN in 8 runs out of 8.** Every case that previously
   "converged on NaN" now either converges honestly or fails honestly. That alone is
   worth the change, independently of the boundary.
2. **`0.3 / 8` is a real solution, not an artefact of the clip.** Three independent
   routes — T1 alone, T1+T2, and the price bound alone — all land on
   `price_2050 = 1652.29`, `rpk_2050 = 3.10079e13`, and in the T1-only run **the clip
   is inactive from iteration 50 to 252**. A converged point at which the guard does
   not bind is a fixed point of the *unmodified* problem.

**The boundary moves and stays.** At `stiffness = 0.3`: γ\* was between 4 and 8
(with γ=8 a silent NaN); it is now between **8 and 10**. Roughly a doubling — real,
useful, and not a removal.

---

## 3. The ~1.85 elasticity boundary — I could not reproduce it

Sweeping `|price_elasticity|` at the `RPKElasticity` input, plain Gauss-Seidel:

| supply curve | values tried | result |
|---|---|---|
| `stiffness=0.3, gamma=1` (nominal) | 0.9, 1.5, **1.85**, 2.5, 4, 6, 8, 12, 16, 24, 32, 48 | **all converge** (22 → 63 → 46 iterations) |
| `stiffness=0.3, gamma=4` | 0.9, 1.5, **1.85**, 2.5, 4 | **all converge** (68 → 83 → 70 iterations) |

No NaN, no non-finite price, at any value. The iteration count *peaks* at |ε|≈24 and
then falls again, because raising the elasticity **moves the fixed point**: demand
collapses, the demand ratio falls, and the local supply exponent
`γ·s·x^γ / (1 + s·x^γ)` falls with it. The loop gain is evaluated at the moving fixed
point and never crosses 1 for γ=1.

Two consequences:

- I have no measurement supporting a boundary at |ε| ≈ 1.85, in this scenario, at
  either supply curve. **Where does the 1.85 come from?** If it was measured on a
  different configuration (a different `demand.model`, the logistic-income variant, a
  real regional scenario rather than the spike), say so and I will re-run there.
- It is a caveat on § 4's rule of thumb in `RAPPORT.md`. "`élasticité-prix × exposant
  local de la courbe d'offre < 1`" holds at a *fixed* operating point, but it is not a
  bound on the elasticity at a fixed supply curve, because the operating point is a
  function of the elasticity. The convexity γ remains the parameter that actually
  moves the boundary.

---

## 4. Totality fixes: the list, and what they cost

Ordered by value per hour. **Fixes 1 and 3 are implemented** on
`fix/mda-convergence-strictness` — see § 4.1. Fix 2 was deliberately deferred and
fix 4 is not done.

| # | fix | where | est. |
|---|---|---|---|
| 1 | Clip the airfare ratio into a wide band before the fractional power, so the multiplier is defined and saturating for any airfare. | `rpk_market.py:547` | **~1 h** incl. a regression test |
| 2 | *Deferred by decision.* Same treatment for the two sibling demand models, whose base (`doc_net_energy_per_rpk_mean`) is net of subsidy and can go negative *without* an accelerator. The exposure is real but neither model is in the spike's loop, so it was left alone. | `price_and_income_elasticity.py:166,169`, `price_elasticity_logistic_income.py:204` | **~1–2 h**, still open |
| 3 | Mask the ASK-weighted means where the total ASK is zero (`ask_weighted_doc_sum / ask_total` is guarded only against "no markets", not against zero ASK). | `direct_operating_costs.py`, **six** sites | **~half a day** |
| 4 | *Optional, bigger.* Bound the coupling variables at the solver level so the accelerator cannot leave the domain at all. GEMSEO's sequence transformers take no bounds, so this is a custom transformer or a post-transform clamp. | `aeromaps/core/gemseo.py` | **1–2 days**, and an architectural commitment |

Fix 1 is the one that buys the boundary move; 1–3 together are what "make the
downstream models total" means concretely. Fix 4 is the principled version and can
wait for evidence that 1–3 are not enough.

### 4.1 What was implemented, and what it measures

Three commits on `fix/mda-convergence-strictness`, each cherry-pickable on its own
(they touch only `models/`, disjoint from that branch's `core/` changes):

| commit | scope |
|---|---|
| `4ecfcac3` `fix(demand)` | a **local** bound on `RPKElasticity` — `AIRFARE_BOUNDS_RELATIVE` as a class constant, applied inline, plus a warning when it engages |
| `1bf59554` `fix(costs)` | `_ask_weighted_mean` in `direct_operating_costs.py`, all six sites |
| `b7dc252d` `docs` | CHANGELOG |

The bound is local to the one model that needs it — no shared helper, and the two
sibling demand models are untouched.

**Verified on the real chain**, spike scenario, `Alternate2Delta`, no probe wrappers:

| case | before | after |
|---|---|---|
| `0.3 / 4` | converged, 38 it, price 643.041 | **unchanged**, 38 it, price 643.041 |
| `0.3 / 8` | "converged" on NaN, price `nan` | **converged**, 258 it, residual 6.37e-11, price **1652.29**, rpk **3.10079e13** |
| `0.3 / 16`, `3 / 8` | "converged" on NaN | fail honestly: *did not converge*, 0 NaN |

`0.3 / 8` lands on exactly the price and RPK the probe predicted. **The full test suite
is green (196 passed) and unchanged** — the evidence that the bound is inactive on every
shipped scenario.

### 4.2 The bound announces itself

The bound only ever fires on a value outside the physical domain, so it warns when it
does, naming the years, the band and the airfare it replaced. On the real `0.3 / 8` run
it fires **74 times** across 258 iterations and two regions, then goes quiet well before
convergence. The first one is the diagnosis of § 1 restated by the model itself:

```
[RPK Elasticity Model: rpk_elasticity Warning]
airfare_per_rpk left the [0.00923638, 1.84728] EUR/RPK band in 10 year(s) (2041-2050) and was bounded.
Worst year 2050: -2.11219 -> 0.00923638 EUR/RPK.
The elasticity multiplier saturates there instead of returning NaN. A bound still active
at convergence means the solution is not trustworthy.
```

That last line is the operative one: a bound that is still binding when the residual
goes under tolerance means the answer sits on the guard, not on a solution.

### 4.3 The no-traffic mean is not zero

§ 4's first version proposed holding the ASK-weighted DOC means at **zero** in a year
where no market has any traffic. That was wrong, and is not what was implemented: there
is no *zero* cost per ASK where there is no traffic, and reporting one invents a number
that was never computed.

What is undefined in such a year is only the **weighting**. The quantity being averaged
is an intensity, not a volume — each market's cost per ASK is still perfectly well
defined, because the per-market energy shares are exogenous sigmoids rather than
ASK-derived ratios (`aircraft_efficiency.py:227`). So those years take the **unweighted
mean of the per-market intensities**, which is the limit of the weighted mean as every
weight goes to zero together.

Years where only *some* markets are empty need nothing special: those markets already
carry zero weight, which is correct. A pre-existing NaN is left alone — this resolves an
undefined weighting, it does not fill in missing data.

---

## 5. Reproducing

```bash
# 1. what manufactures the NaN, and where
python -m spike_unified_mda.brief1_probe origin --stiffness 0.3 --gamma 8 --accelerated
python -m spike_unified_mda.brief1_pinpoint 0.3 8        # the exact operand
python -m spike_unified_mda.brief1_decompose 0.3 8       # the cost decomposition

# 2. the shape of the divergence
python -m spike_unified_mda.brief1_traj --cases 0.3,4 0.3,8 0.3,16          # plain GS
python -m spike_unified_mda.brief1_traj --cases 0.3,8 0.3,16 --accel --bound

# 3. what a totality fix buys
python -m spike_unified_mda.brief1_totality
python -m spike_unified_mda.brief1_elasticity                      # the 1.85 question
python -m spike_unified_mda.brief1_second_source 0.3 16            # remaining sources

python -m spike_unified_mda.brief1_plot                            # the two figures
```

Raw logs and per-iteration CSVs are in `spike_unified_mda/brief1_out/`.

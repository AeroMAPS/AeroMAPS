# Brief 2 — the analytical demand slope, and what it costs

**Verdict, one sentence.** `dD/dp_SAF` **can** be extracted analytically and in
closed form; the chain is four multiplicative stages plus **one** feedback loop, and
the resulting expression reproduces the converged MDA's own response to a SAF price
shock to **0.000 %** on the reference case — but the four-stage product *as written in
the brief* is short by 3.8–5.2 %, because the "supply function" is not a pass-through
coefficient at all: its incidence lives entirely in a quantity term that the open-loop
product cannot see.

Two structural findings fall out of the trace and matter more than the formula:

1. **`d alpha / d p_SAF` is identically zero everywhere in the current code.** Blend
   shares come from `EnergyUseChoice`, which reads exogenous `mandate_share` /
   `mandate_quantity`. There is no buy-out, no intensity standard, no voluntary
   demand, no price-responsive pathway selection anywhere in `aeromaps/`. The
   endogenous-`alpha` case the brief anticipates is not a case the code can currently
   be in — except through one volume channel described in § 4.2.
2. **Fuel subsidies and fuel excise taxes never reached the airfare** — fixed since,
   see the note at the head of § 6. They were computed and entered the *reporting*
   total (`doc_total_per_ask_mean`), but `PassengerAircraftTotalCost` — the model that
   feeds the airfare — did not read them. This bit the `cagr_elasticity` path only:
   `RPKElasticity` is the one demand model that responds to `airfare_per_rpk`. The two
   price-coupled models (`constant_elasticity`, `logistic_income`) read
   `doc_net_energy_per_rpk_mean` instead, which has always netted the subsidy and the
   fuel tax, so they were never affected (§ 6).

All measurements are on the Step-2 spike scenario with `DemandSlope` wired in
(`spike_unified_mda/scenario/regionalisation_spike_slope.yaml`), 2 regions,
`price_elasticity = -0.9`, `models_operation_cost_top_down_feedback`, `tolerance=1e-10`.
Nothing under `aeromaps/` was modified.

---

## 1. The chain, link by link

Cost-feedback mode (`global.demand.model: cagr_elasticity` +
`models_operation_cost_top_down_feedback`) is the only configuration in which the
loop exists. `PassengerAircraftSimpleAirfare` and `TotalAirlineCostNoElast` are *not*
instantiated in that mode — `core/models.py:375-394` swaps them for
`PassengerAircraftMarginalCost` and `TotalAirlineCost`.

| # | variable | file | functional form |
|---|---|---|---|
| 0 | `{p}_mean_mfsp` | `generic_energy_model/top_down/cost.py:191-328` | `p_mfsp = mfsp_without_resource + Σ_k (resource_cost_k · specific_consumption_k) + Σ_proc proc_cost` |
| 1 | `dropin_fuel_mean_mfsp` | `common/energy_carriers_means.py:211` | `Σ_i share_i/100 · p_i` — **an average, over the drop-in pathways** |
| 2 | `doc_energy_per_ask_{m}_{et}` | `costs/airlines/direct_operating_costs.py:375` | `energy_per_ask_{m,et} · mfsp_{et}` (zeros mapped to NaN) |
| 3 | `doc_energy_per_ask_{m}_mean` | `direct_operating_costs.py:380-392` | `Σ_et doc_{m,et}·ask_share_{m,et}/100` |
| 4 | `doc_energy_per_ask_mean` | `direct_operating_costs.py:395-409` | `Σ_m doc_{m}·ask_m / Σ_m ask_m` |
| 5 | `total_cost_per_ask_without_extra_tax` | `total_airline_cost_and_airfare.py:213` | sum of 7 per-ASK terms, `doc_energy_per_ask_mean` among them, **additively** |
| 6 | `total_cost_per_rpk_without_extra_tax` | `total_airline_cost_and_airfare.py:228` | `/ (load_factor/100)` |
| 7 | `airfare_per_rpk` | `total_airline_cost_and_airfare.py:336-364` | the supply function, § 2 |
| 8 | `rpk` | `air_traffic/rpk_market.py:593` | `rpk_no_elasticity · (airfare_per_rpk / airfare_init)^ε` |

Two things the table makes visible, and both matter:

* the **carbon tax does not travel this path**. It enters as
  `doc_carbon_tax_lowering_offset_per_ask_mean` into `total_extra_tax_per_ask`
  (`:222`), which is added to the airfare *after* the supply function (`:362`). So the
  carbon tax passes through the airline at **1.0**, while a fuel-cost shock passes
  through at **< 1** (§ 2). The two shocks are not equivalent, and the difference is
  not a modelling choice anyone made — it is a consequence of where the sum is taken.
* everything from link 2 to link 6 is **linear in `mfsp`** with no threshold, so
  stages 3 and 4 of the brief's chain are exact, not local. Measured: relative gap
  between analytic and finite-difference **1e-11 or better** for both (§ 7).

---

## 2. The supply function — located, and it is not a pass-through

`PassengerAircraftMarginalCost.compute`,
`aeromaps/models/impacts/costs/airlines/total_airline_cost_and_airfare.py:286-376`.
It is an **inverse market-level supply function, linear in quantity**, calibrated so
that it reproduces the observed 2019 price at the observed 2019 quantity. Verbatim:

```python
intial_total_cost_per_rpk_without_extra_tax = total_cost_per_rpk_without_extra_tax[
    self.prospection_start_year - 1
]                                                  # C0, a SCALAR, one base year
initial_price_per_rpk_corrected = 0.09236379319842411   # p0, hard-coded

b = 2 * intial_total_cost_per_rpk_without_extra_tax - initial_price_per_rpk_corrected
a = 2 * (initial_price_per_rpk_corrected
         - intial_total_cost_per_rpk_without_extra_tax) / rpk_no_elasticity

marginal_cost_per_rpk = a * rpk + b + total_cost_per_rpk_without_extra_tax - C0
airfare_per_rpk = marginal_cost_per_rpk + total_extra_tax_per_rpk
```

In symbols, writing `C(t)` for `total_cost_per_rpk_without_extra_tax`, `T(t)` for
`total_extra_tax_per_rpk`, `D(t)` for `rpk` and `D_ne(t)` for `rpk_no_elasticity`:

```
P(t) = a(t)·D(t) + b + C(t) − C0 + T(t)
a(t) = 2(p0 − C0)/D_ne(t)          b = 2·C0 − p0
```

Sanity check on the calibration: at `D = D_ne` and `C = C0` it returns
`2(p0−C0) + 2C0 − p0 = p0`. It is a linear supply curve pinned through the base-year
point, with slope set so that the base-year markup is recovered.

### 2.1 The partial derivative is exactly 1

```
∂P/∂C |_D = 1
```

There is no pass-through coefficient in this model. The airline passes 100 % of a
cost shock at fixed quantity. **The incidence is not in a coefficient — it is in the
`a·D` term**: the supply curve slopes up, so when the shock destroys demand, the
price falls back along the curve. That is the second stage of incidence the brief
asks about, and it is only visible once the loop is closed.

### 2.2 The equilibrium pass-through

Close the loop `P → D → P`. With `η ≡ dD/dP` (stage 1, § 3):

```
dP = a·dD + dC        dD = η·dP
⇒  dP/dC = 1/(1 − a·η)          absorbed by the airline = −a·η/(1 − a·η)
```

`a·η` is the loop gain. It has a compact interpretation. With
`μ ≡ (p0 − C0)/p0`, the base-year markup:

```
a·η = 2·ε·μ · (D/D_ne)·(p0/P)      →   2·ε·μ  at the calibration point
```

so, near calibration, **the airline absorbs `2|ε|μ / (1 + 2|ε|μ)` of any fuel-cost
shock**. On the reference case `C0 = 0.089862 €/RPK`, `p0 = 0.092364 €/RPK`, hence
`μ = 2.71 %`, and with `ε = −0.9`:

| year | loop gain `a·η` | pass-through `1/(1−aη)` | absorbed |
|---|---|---|---|
| 2025 | −0.0508 | 0.9516 | 4.84 % |
| 2030 | −0.0523 | 0.9503 | 4.97 % |
| 2035 | −0.0485 | 0.9537 | 4.63 % |
| 2040 | −0.0460 | 0.9560 | 4.40 % |
| 2045 | −0.0413 | 0.9603 | 3.97 % |
| 2050 | −0.0381 | 0.9633 | 3.67 % |

The measured `Δairfare/Δtotal_cost` on two converged MDA runs agrees to **1e-6**
relative (§ 7). The number is small because the calibrated markup is small: the
airline's ability to absorb is 2.7 % of the fare, and the elasticity halves nothing.
**Do not read this as a robust economic result** — it is a mechanical consequence of
`p0` and `C0`, and § 5.2 lists what happens if the scenario moves `C0` above `p0`.

---

## 3. Stage 1 — the elasticity

`RPKElasticity.compute`, `rpk_market.py:521-607`. Global (one multiplier for every
market), clamped to 1 up to and including the latest `covid_end_year`:

```
D(t) = D_ne(t) · (P(t)/P_init)^ε         for t ≥ elasticity_start
D(t) = D_ne(t)                            otherwise
η(t) ≡ dD/dP = ε · D(t)/P(t)              (P_init cancels)
```

`elasticity_start = max_m(covid_end_year_m) + 1`, floored at `prospection_start_year`
— 2025 on the reference case. **Before that year the slope is identically zero, not
small**: the demand a market module would be handed is exogenous there, and any
optimisation must treat it as such.

---

## 4. `dD/dp_SAF`, derived

Define `p_SAF` as the €/MJ selling price of the non-fossil drop-in blend and
`α` as its share of drop-in energy. Then, collecting §§ 1–3:

```
                            ┌ stage 1 ┐ ┌ 2 ┐ ┌─── stage 3 ───┐ ┌── stage 4 ──┐
dD/dp_SAF |open loop   =   (ε·D/P)  ×   1   ×  (Ē·100/LF)      ×  dα-term

dD/dp_SAF |closed loop =   open loop  /  (1 − a·η)

  Ē(t)  = Σ_m energy_per_ask_{m,dropin} · ask_share_{m,dropin}/100 · ask_m / Σ_m ask_m   [MJ/ASK]
  κ(t)  = Ē·100/LF                                                                       [MJ/RPK]
  a(t)  = 2(p0 − C0)/D_ne(t)
  η(t)  = ε·D(t)/P(t)
```

### 4.1 Exogenous `alpha` — the only case the code currently supports

```
d mfsp_mean/d p_SAF = α
```

The second term of the brief's dilution identity vanishes, and

```
s(t) = ε·D(t)/P(t) · κ(t) · α(t) / (1 − a(t)·η(t))
```

This is what `DemandSlope` computes, and it is exact to machine precision against the
MDA (§ 7).

### 4.2 Endogenous `alpha` — where it could come from, and it is not price

I traced every producer of `{pathway}_share_{aircraft_type}`. All of them are
`EnergyUseChoice` (`common/energy_use_choice.py:129-300`), and it has exactly two
regimes:

* **`mandate_type: "share"`** — `pathway_consumption = mandate_share/100 · E`
  (`:250-254`), so `α = mandate_share/100`, an exogenous series.
  `dα/dp_SAF = 0` exactly.
* **`mandate_type: "quantity"`** — `pathway_consumption = mandate_quantity`, so
  `α = Q/E`. Here `α` **is** endogenous, but through the *volume* `E`, not through
  the price: `dα/dp_SAF = −(Q/E²)·(dE/dp_SAF)`, and `dE/dp_SAF` is itself
  proportional to `dD/dp_SAF`. That closes a *second* loop, and it has the opposite
  sign to the first — a price rise cuts demand, cuts `E`, and *raises* the mandated
  fraction, raising the mean price further. It is destabilising, and it is a real
  configuration, not a hypothetical.

There is no third regime. `grep -rn "buy_out\|buyout\|intensity_standard\|voluntary"`
over `aeromaps/` returns nothing. Under a binding *share* mandate the brief's second
term is zero not by economic argument but because nothing in the code can produce it.

If a price-responsive blend is added later, the extra term the brief writes is exactly
right and slots into stage 4:

```
d mfsp_mean/d p_SAF = α + (p_SAF − p_fossil)·dα/dp_SAF
```

and it is not a small correction on this scenario: `p_SAF − p_fossil` runs from
0.026 €/MJ (2025) to 0.057 €/MJ (2050) against `mfsp_mean` of 0.013 → 0.052 €/MJ. A
blend share that moved by 0.01 per €/MJ would contribute as much as a 5-point change
in `α` itself.

---

## 5. Nonlinearities between price and total cost

The chain is linear in `mfsp` all the way from link 2 to link 6 — no thresholds, no
saturation, no discontinuity. The nonlinearities are all *elsewhere*, and these are
the ones that bound the validity of a local slope.

**5.1 The power law and its domain (Brief 1's finding).** `rpk_market.py:593` raises
`P/P_init` to a fractional power. `η = εD/P` is a valid local derivative only while
`P > 0`; the multiplier is not merely steep but **not a real number** for `P < 0`, and
`P` does go negative on stiff scenarios. On `fix/mda-convergence-strictness` the guard
now lives upstream: `RPKElasticity.AIRFARE_BOUNDS_RELATIVE` clips the airfare to
`[0.1, 20]×` the reference before the power. The band is inactive at any converged
solution, so the measurements below are unchanged — but `DemandSlope` should mirror the
saturation and return **zero** slope wherever the clip is active, which it does not yet
do.

**5.2 `a` flips sign if `C0 > p0`.** `a = 2(p0 − C0)/D_ne` with `p0` **hard-coded** at
`0.09236379319842411` and `C0` read from the scenario's own base year. A scenario
whose base-year cost exceeds that constant gets a *downward*-sloping supply curve,
`a·η > 0`, and a pass-through `1/(1−aη) > 1` — amplification instead of absorption,
and divergence at `a·η → 1`. On the reference case the margin is thin: `μ = 2.71 %`.

**5.3 `p0` is hard-coded and `initial_airfare_per_rpk` is not read.**
`PassengerAircraftMarginalCost` hard-codes `p0` at `:341`; `RPKElasticity` reads
`initial_airfare_per_rpk` from `markets.yaml`. They are equal in every shipped config
and nothing enforces it. Changing the YAML alone silently decalibrates the supply
curve against the elasticity reference.

**5.4 The carbon-tax offset ratio.** `PassengerAircraftDocEnergyCarbonTax` scales the
tax by `carbon_remaining_ratio = (co2_emissions − carbon_offset)/co2_emissions`, and
`co2_emissions` is proportional to demand. Whenever the carbon tax is nonzero this is
a *second* feedback loop that the four-stage chain does not contain. Measured: with
the spike's market loop live (`stiffness=0.3`, `base_price=150 €/tCO₂`), the
closed-loop formula is off by **1.6–3.0 %** instead of 0.000 % (§ 7.3).

**5.5 Load factor is exogenous.** `LoadFactorMarket`
(`aircraft_fleet_and_operations/load_factor/load_factor.py:56`) reads `rpk_init` /
`ask_init`, the *uncoupled* historical series, not `rpk`. `∂LF/∂p_SAF = 0`. It scales
the slope through `κ = Ē·100/LF` but adds no loop.

**5.6 `energy.replace(0, np.NaN)`** at `direct_operating_costs.py:375` and
`valid_years = cumulative_share.replace(0, np.nan)` at `energy_carriers_means.py:290`
make the derivative undefined, not zero, on empty energy types and empty markets.
Same family as the empty-market NaN issue: a market with zero traffic contributes
`NaN`, not `0`, to `Ē`.

**5.7 The clamp at `elasticity_start`.** § 3: the slope steps from 0 to its full value
between 2024 and 2025. Not a modelling error, but a discontinuity a solver will find.

---

## 6. `*_marginal_net_mfsp` — computed, never consumed

> **Status.** The subsidy/tax half of this section was fixed in `eeaf5159` on
> `fix/mda-convergence-strictness`: energy taxes now join the extra-tax wedge, energy
> subsidies became their own `total_subsidy_per_*` category, and both reach the fare
> through `PassengerAircraftMarginalCost`. The `*_marginal_net_mfsp` half below stands.
> Line citations in this report are against the spike branch and have shifted.

`EnergyCarriersMeans` produces, per aircraft type and per (aircraft type, energy
origin), the most expensive pathway's net MFSP of the year
(`energy_carriers_means.py:252-260, 280, 316`). Searching the whole repository:

* **no model reads it** — the only `.py` hit outside the producer is the spike's own
  brief-1 CSV logs;
* **no plot reads it** — `aeromaps/plots/` uses pathway-level `{p.name}_net_mfsp`, never
  the `*_marginal_net_mfsp` aggregates;
* it appears only in serialised results (`resources/data/outputs.json` and the
  publication result JSONs), i.e. it is written out and never read back.

It is dead weight in the grammar today. It is also, notably, **the quantity the brief's
whole premise wants**: the chain prices energy at the *average* MFSP, so a market
module that clears on a marginal price is talking to a chain that responds to an
average. Wiring `*_marginal_net_mfsp` into the DOC would change the meaning of every
existing cost result, so it is a decision, not a fix.

**A second, larger gap found while looking.** `EnergyCarriersMeans` also produces
`{aircraft_type}_mean_net_mfsp` (MFSP net of subsidy, tax and carbon tax) and
`{aircraft_type}_mean_net_mfsp_without_carbon_tax` — likewise read by **nothing**.
`PassengerAircraftDocEnergy` prices energy at the **gross** `{aircraft_type}_mean_mfsp`
(`direct_operating_costs.py:331-333`). Subsidies and fuel taxes *are* turned into
per-ASK DOC by `PassengerAircraftDocEnergySubsidy` / `…Tax` (`:571`, `:699`), and
`PassengerAircraftTotalDoc` nets them into the reporting series
`doc_total_per_ask_mean` and `doc_net_energy_per_rpk_mean` (`:1185-1205`) — but
`PassengerAircraftTotalCost`, the model that actually feeds the airfare, did not read
them. **A SAF subsidy therefore moved the reported cost and not the fare.**

The scope of that is narrower than it first looks, and worth stating precisely.
`airfare_per_rpk` is consumed by exactly one demand model, `RPKElasticity`
(`cagr_elasticity`). The other two price-coupled models — `RPKPriceIncomeElasticity`
and `RPKLogisticIncomePriceElasticity` — take their price signal from
`doc_net_energy_per_rpk_mean`, which `PassengerAircraftTotalDoc` has always built as
`energy + carbon tax − subsidy + energy tax`. Those two therefore always saw the
subsidy, and a finite-difference check on `config_elasticity_demand` confirms it:
a 0.005 EUR/MJ SAF subsidy lifts RPK by 1.1 % (2030) to 4.5 % (2050), with the fare
*rising* because higher demand pushes the `a·rpk` supply term up — not a sign error,
just a demand curve drawn against the energy price rather than against the fare.

So the bug was real but confined to the `cagr_elasticity` path — which is precisely
the path this brief's slope is derived on.

---

## 7. `DemandSlope`, and the finite-difference validation

### 7.1 The discipline

`spike_unified_mda/scenario/demand_slope_model.py` — a regional
`AeroMAPSModel`, `model_type="custom"`, namespaced by
`apply_namespace_to_disciplines` like `SpikeFuelDemand`, so it publishes

```
{region}:fuel_demand_slope              [RPK per (EUR/MJ)]     the closed-loop slope s
{region}:fuel_demand_slope_open_loop    [RPK per (EUR/MJ)]     the four-stage product alone
{region}:saf_blend_share                                        α
{region}:dropin_energy_per_rpk          [MJ/RPK]                κ
{region}:airfare_cost_passthrough                               1/(1 − a·η)
```

It reads only converged coupling variables (`rpk`, `airfare_per_rpk`,
`rpk_no_elasticity`, `load_factor`, `total_cost_per_rpk_without_extra_tax`, the
per-market ASK/energy split and the SAF pathway shares) and writes nothing anyone
consumes, so it sits **outside** the SCC and costs one extra discipline execution per
MDA — not per iteration. It builds its own grammar in `custom_setup()` from the
injected `MarketManager` and `PathwaysManager`; the SAF set is "drop-in pathways whose
`energy_origin` is not `fossil`", not a hard-coded list.

### 7.2 Validation — clean case

`p_SAF` is shocked by adding `δ` to `{pathway}_mean_mfsp_without_resource` of every
SAF drop-in pathway, which is a purely additive term of `{pathway}_mean_mfsp`
(`top_down/cost.py:191`), so the shock is exactly `δ` on `p_SAF` by construction. Both
runs are converged MDAs (`residual ≈ 1.4e-11`); the comparison is a **central**
difference at `δ = 1e-5 €/MJ`.

```
=== region_A ===                       [RPK per (EUR/MJ)]
  year   alpha    s analytic     s numeric   rel.gap  open-loop gap
  2025   0.030   -2.8169e+12   -2.8169e+12    -0.00%          5.08%
  2030   0.060   -5.9934e+12   -5.9934e+12    -0.00%          5.23%
  2035   0.200   -1.9179e+13   -1.9179e+13    -0.00%          4.85%
  2040   0.340   -3.1836e+13   -3.1836e+13    -0.00%          4.60%
  2045   0.520   -4.5145e+13   -4.5145e+13    -0.00%          4.13%
  2050   0.700   -5.8225e+13   -5.8225e+13    -0.00%          3.81%

worst relative gap, analytic vs numeric: 0.000%     (region_B: same gaps, larger |s|)
```

Stage by stage, forward difference at the same `δ` (`brief2_chain.py`):

| stage | quantity | worst relative gap |
|---|---|---|
| 4 | `d mfsp_mean/d p_SAF` = `α` | 3e-11 |
| 3 | `d total_cost_per_rpk/d mfsp_mean` = `κ` | 3e-11 |
| 2 | `d airfare/d total_cost` = `1/(1−aη)` | 2e-6 |
| 1 | `d RPK/d airfare` = `ε·D/P` | 4e-5 |

Stages 4 and 3 are exact because the chain is linear in `mfsp`. Stages 2 and 1 carry
only forward-difference truncation: the end-to-end gap falls **0.35 % → 0.04 % →
0.00 %** as `δ` goes `1e-3 → 1e-4 → 1e-5`, first order, which is the signature of
truncation rather than of a missing term.

The **open-loop** column is the brief's four-stage product with no closing. It is
short by **3.8–5.2 %**, and that number is § 2.2's absorbed fraction, exactly.

### 7.3 Validation — with the spike's market loop live

Turning the spike fuel market back on (`stiffness=0.3`, `base_price=150 €/tCO₂`, which
routes demand into `carbon_tax`) adds the § 5.4 loop:

```
  year    s analytic     s numeric   rel.gap    open-loop gap
  2025   -2.0602e+12   -2.0054e+12     2.73%            6.50%
  2035   -1.5052e+13   -1.4628e+13     2.90%            6.78%
  2050   -5.3081e+13   -5.2224e+13     1.64%            5.16%

worst relative gap: 3.018%
```

Both errors have the same sign: the formula overstates the response because it omits a
second damping loop. The four-stage chain is a **lower bound on the damping**, always.

### 7.4 What this costs

Cheap, and the cheapness is the point. The slope needs no Jacobian, no adjoint and no
extra MDA: every ingredient is already a converged output. One extra discipline,
`O(n_markets)` arithmetic, outside the SCC. The expensive part is not computing `s` —
it is that `s` is only exact under §§ 4.1 and 5.4, i.e. exogenous blend share and no
demand-dependent carbon tax. Handing a market module a slope that is 3 % wrong is
fine; handing it one that is 3 % wrong *without saying so* is not, which is why
`DemandSlope` publishes `fuel_demand_slope_open_loop` and
`airfare_cost_passthrough` alongside `fuel_demand_slope`.

---

## 8. Reproducing

```bash
# stage-by-stage decomposition, analytic vs finite difference
python spike_unified_mda/brief2_chain.py --delta 1e-5
python spike_unified_mda/brief2_chain.py --delta 1e-3   # shows FD truncation, not error
python spike_unified_mda/brief2_chain.py --delta 1e-5 --stiffness 0.3 --base-price 150

# the DemandSlope discipline against a central difference
python spike_unified_mda/brief2_validate.py --central
python spike_unified_mda/brief2_validate.py --central --stiffness 0.3 --base-price 150
```

The scenario variant that wires `DemandSlope` in is
`spike_unified_mda/scenario/regionalisation_spike_slope.yaml` (region configs
`config_slope.yaml`). Brief 1's scenario, `regionalisation_spike.yaml`, is untouched,
so its discipline-execution indices still hold. Captured logs are in
`spike_unified_mda/brief2_out/`.

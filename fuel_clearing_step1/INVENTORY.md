# INVENTORY — what the fuel market has to plug into

Answers to §2.3 of the step-1 brief, measured on
`feat/fuel-clearing-step1` @ `993fc9f2` (spike, rebased onto
`optimisation/refueleu-migration-and-mda-dedup`).

Read §0 first: four of the brief's premises no longer hold on this base.

> **Updated 2026-09-23.** §0–§8 are the inventory as measured before the mode existed and
> are left as written. §9's questions are now answered in place. **§10 describes the
> interface as built** — what `FuelClearing` reads, emits and can be configured with — and
> **§11 what each step-2 option would add to it** ([`REPORT.md`](REPORT.md) §12).

---

## 0. Premises of the brief that have changed

**0.1 — The blocking fix of §2.1 is already done.** The brief describes
`_setup_unified_mda` building its chain with `tolerance=1e-5` and no
`max_mda_iter`. That was true at the base it names (`b74b8e12`, line 707). On this
base [`multi_regional_process.py:708-719`](../aeromaps/core/multi_regional_process.py#L708-L719)
reads `tolerance=1e-10, max_mda_iter=200`, landed by `a27bd252 fix(multi-regional):
apply the unified_mda settings that 3bdbfb8c only claimed`. The test and the
CHANGELOG correction came with it. **No work required.**

Related, from the same range: `80fcbeda` took the NaN flag out of the coupling
vector (masks now travel beside it, `freeze_nan_masks_after_first_sweep`) and the
clip out of `RPKElasticity`, replacing it with declared coupling bounds
(`apply_coupling_bounds`). Decision 9 ("zeros, never NaN") is therefore enforced by
the solver layer now, not only by convention.

**0.2 — The §2.2 gate is half-failed.** PR #158 (kerosene selectivity) is **merged**
(2026-09-01). PR #157 is **still open** against `main`. Its *content* is present on
this branch line and has since been extended, so the gate is procedural, not a
capability gap. Flagged rather than treated as a stop, per the decision to branch
from the rebased spike.

**0.3 — `cvxpy` was not a dependency.** Added to the `test` group (not core, not an
extra) as `cvxpy = "^1.5"`; resolves to 1.7.5 with `CLARABEL` available. Deliberately
not a core dependency: the mode is opt-in and the default mode must not make every
install carry a convex solver. The kernel imports it lazily. Revisit when the mode
ships.

**0.4 — Bench scripts suppress warnings.** Confirmed: ten scripts under
`spike_unified_mda/` call `warnings.filterwarnings("ignore")` at import. Any script
written this week must call `warnings.resetwarnings()` — several of the invariants
below are guarded by `warnings.warn` and nothing else.

---

## 1. The ramp-up constraint used by the optimisation

**Neither of the two forms the brief offers matches it.**

There is **no ramp-up constraint in the core model library at all**.
[`aeromaps/models/optimisation/constraints/energy_constraint.py`](../aeromaps/models/optimisation/constraints/energy_constraint.py)
is commented out in its entirety, top to bottom. The live constraint lives per
publication; the current one is
[`constraints_rte.py:130`](../aeromaps/notebooks/publications/optimisation/migrated/constraints_rte.py#L130),
`_ramp_up_violation`, paper Eq. (12):

```
E_t  ≤  max{ E_{t-1}·(1+τ)^dt ,  E_{t-1} + dE·dt }
```

| question | answer |
|---|---|
| shares or volumes? | **volumes**, `generic_{p}_energy_consumption`, in MJ |
| relative growth or share increment? | **neither** — the *least constraining of* a relative rate branch and an absolute volume-addition branch |
| limit values | `rate_ramp_up_constraint_{biofuel,electrofuel}` (τ, relative) and `volume_ramp_up_constraint_{…}` (dE, EJ/year → `×1e12` to MJ) |
| seed | none. The volume branch `E_{t-1} + dE·dt` plays that role: it is what lets a pathway leave zero |
| enforced where? | only at `*_use_growth_constraint_enforcement_years`, on a 5- or 10-year lookback (`dt`), **not annually** |
| normalisation | `(current − cap) / (volume·dt)` — constant w.r.t. the design variables, so a violation of 1.0 means "one period of capacity additions too many" in every year |

### 1.1 Why the market cannot reproduce it, and what to do instead

`q ≤ max(affine, affine)` describes a **union of two convex sets**, which is not
convex. Feeding it to Clarabel is not a tolerance problem — the feasible set is the
wrong shape. This is exactly the trap `saf_market_skeleton.py` flags in D2(b) ("ne
PAS écrire `max(seed, g*K)`") and that `test_rampup.py` exists to demonstrate.

The brief's `"relative"` form is the convex surrogate:

```
q_t  ≤  seed + (1+g)·q_{t-1}          (a sum, one affine constraint)
```

With `seed ≈ dE·dt` and `g ≈ τ` it is a genuine **outer relaxation** — since
`seed + (1+g)q_{t-1} ≥ max{(1+τ)q_{t-1}, q_{t-1}+dE·dt}`, every point Eq. 12 admits
is admitted, plus a margin. So the market is strictly more permissive than the
optimisation's ramp-up, by the amount of the smaller branch.

Two consequences for the week:

- Test 3.3.c (reproduction) is unaffected — it runs with a deliberately loose
  ramp-up, so neither form binds.
- Measurement 4.5.2 sweeps the mandate until the ramp-up *does* bind. There the two
  modes are answering slightly different questions, and the report must say so
  rather than present the market's ramp-up as "the same constraint".

**Recommendation:** implement both `rampup_form` values as the brief specifies (the
kernel takes it as a parameter anyway), default to `"relative"`, and record the
max-vs-sum gap as a known, quantified divergence instead of resolving it silently.
The annual-vs-enforcement-year difference is the second half of that gap and is
independent of the form.

---

## 2. The fuel-share decision variables, and how the ramp-up attaches

[`optimisation_runs.py:296-312`](../aeromaps/notebooks/publications/optimisation/migrated/optimisation_runs.py#L296-L312):

```
generic_electrofuel_mandate_share_values_optim   size 5, bounds [EPSILON_SHARE, 100]
generic_biofuel_mandate_share_values_optim       size 5, bounds [2, 100]
```

Five reference-year shares per pathway, not a full year vector. The chain:

```
*_values_optim (5)  →  ReducedMandate  →  *_mandate_share_values (full yaml vector)
                    →  yaml interpolation  →  {p}_mandate_share (series)
                    →  EnergyUseChoice  →  {p}_energy_consumption (MJ)
                    →  _ramp_up_violation  →  constraint rows
```

**The ramp-up does not attach to the design variables.** It attaches to the
*resulting volumes*, several disciplines downstream, and is evaluated after the MDA
has converged. The optimiser has a lever on it only because it controls the shares
that produce those volumes.

This is precisely the ground for decision 3. In the market mode the volumes are the
output of the solve — there is no upstream share left to move — so a constraint
checked on the output has nothing acting on it. It has to be inside the program.

---

## 3. `EnergyUseChoice` outputs and their consumers

Already established by
[`BRIEF3.md`](../docs/fuel_market_spike/BRIEF3.md) §1 and not re-derived here.
Summary for the default 13-pathway config: **86 outputs in 9 families; 47 read by a
model, 3 by a plot only, 36 dead.**

| family | count | unit | consumer |
|---|---|---|---|
| A `{p}_energy_consumption` | 13 | MJ | massic shares, scenario cost, per-pathway env/cost/capacity/abatement |
| B `{p}_share_total_energy` | 13 | % | dead |
| C `{p}_share_{aircraft_type}` | 13 | % | `energy_carriers_means` |
| D `{origin}_share_total_energy` | 3 | % | plot only |
| E `{p}_share_{origin}` | 13 | % | dead |
| F `{origin}_share_{aircraft_type}` | 6 | % | 3 of 6 → `drop_in_fuel_detailed_consumption` |
| G `{aircraft_type}_share_{origin}` | 6 | % | dead |
| H `{aircraft_type}_{origin}_energy_consumption` | 6 | MJ | 5 of 6 → `non_co2_emissions` |
| I `{p}_share_{aircraft_type}_{origin}` | 13 | % | `energy_carriers_means` |

Plus three hard-coded fallbacks emitted as zeros when no matching pathway exists
([`energy_use_choice.py:120-127`](../aeromaps/models/impacts/generic_energy_model/common/energy_use_choice.py#L120-L127)):
`biomass_share_dropin_fuel`, `electricity_share_dropin_fuel`,
`fossil_share_dropin_fuel`.

**What the market must emit:** family A is algebraically sufficient — every share
family is A divided by a total. But `EnergyCarriersMeans` consumes **shares, not
volumes** (`mean X = Σ_p share_p/100 × X_p`), so the market discipline has to emit
the live share families too, under the same names and units. Deriving them from A
inside `FuelClearing` is the obvious route.

### 3.1 The invariant that nothing checks

```
Σ_pathways  {p}_energy_consumption  ≡  energy_consumption_{aircraft_type}
```

`EnergyUseChoice` closes this **by construction**: the `default` pathway is a
residual that absorbs whatever is left
([`energy_use_choice.py:304-309`](../aeromaps/models/impacts/generic_energy_model/common/energy_use_choice.py#L304-L309)).
Nothing downstream re-derives or renormalises. `EnergyCarriersMeans` multiplies by
`cumulative_share.replace(0, np.nan)` but never divides by it, so a share sum of
50 % yields a mean that is 50 % of the truth, with a `warnings.warn` as the only
guard.

BRIEF3 §2.2 measured it: a 50 % gap moves `dropin_fuel_mean_co2_emission_factor`
from 78.85 to 17.25 gCO₂/MJ, and `co2_emissions` then multiplies that by the *full*
fleet-side energy. CO₂ falls 78 % with no error raised.

This is what decision 11 ("échecs bruyants") is protecting, and what §4.3's
post-convergence assertion must check. It is also why §3.2's exact-closure step
(recompute kerosene as `D − Σ others`) exists — and why that step must raise when
the correction exceeds solver tolerance rather than absorb a real imbalance.

---

## 4. The total energy demand the market reads

**It is not one variable.** `EnergyUseChoice` reads one hard budget per aircraft
type ([`energy_use_choice.py:144-148`](../aeromaps/models/impacts/generic_energy_model/common/energy_use_choice.py#L144-L148)):

| variable | producer |
|---|---|
| `energy_consumption_dropin_fuel` | `DropInFuelConsumption` ([`energy_consumption.py:206`](../aeromaps/models/impacts/energy_resources/energy_consumption.py#L206)) |
| `energy_consumption_hydrogen` | `HydrogenConsumption` |
| `energy_consumption_electric` | `ElectricConsumption` |
| `energy_consumption` | `EnergyConsumption` — denominator of families B and D only |

An aircraft type present in the carriers yaml but absent from the fleet output
raises `KeyError` with an explicit message.

**Consequence for step 1.** One sustainable fuel plus kerosene means the market
lives on `dropin_fuel` alone, so the kernel's `demand` (R×T) is
`energy_consumption_dropin_fuel`. §4.2's "`EnergyUseChoice` is not instantiated"
therefore only holds if the config declares **no** hydrogen or electric pathway —
otherwise those types lose their allocator. This needs an explicit guard at mode
setup, not an assumption. The step-1 bench config has drop-in only.

---

## 5. How historical years are treated

**They are not treated at all.** `EnergyUseChoice` has no
`prospection_start_year` branch; it computes across the full
`historic_start_year..end_year` index and inherits whatever
`energy_consumption_{type}` and the yaml-interpolated mandates carry there.

### 5.1 Measured: the current mode emits NaN there, not zero

On the reference run (§8), over the 20 historical years 2000–2019, per region:

| column | NaN years |
|---|---|
| `hefa_fog_energy_consumption` | 20 |
| `hefa_fog_share_dropin_fuel` | 20 |

Everything else is clean, and the NaN does **not** propagate —
`dropin_fuel_mean_mfsp` is finite throughout, because `EnergyCarriersMeans` fills
before it weights. The cause is the mandate share series being undefined before
`prospection_start_year`, so `share/100 × demand` carries the NaN into the volume.
`fossil_kerosene`, as the residual default, is unaffected: it absorbs the whole
demand.

**This puts decision 9 in direct conflict with §4.2's guard-rail.** Decision 9 says
the market emits zeros, never NaN. §4.2 says a reference run must be identical *bit
for bit* before and after the branch. Both cannot hold on these two columns: the
market will write `0.0` where the current mode writes `NaN`.

The conflict is only apparent if the *market mode* is asked to reproduce the current
mode's historical years exactly. It does not affect §4.2's actual guard, which is
that the **current mode** is unchanged — that still holds, because nothing in the
market mode touches `EnergyUseChoice`.

**Recommendation:** the market emits zeros (decision 9 wins), and the reproduction
test compares historical years with `NaN` treated as `0.0` on the reference side.
Record it as a known, bounded difference rather than widening the tolerance
everywhere. The fixture's `historical_nan_columns` names the exact columns so the
test can be specific instead of blanket.

### 5.2 Where the copied values come from

"Recopiées à l'identique" needs a source. Two options:

1. **Reuse the allocation.** Keep `EnergyUseChoice`'s three-pass logic for historical
   years and run the kernel only on the prospective slice. Bit-identical to the
   current mode by construction, which is what §4.2's guard-rail asks for.
2. **Read the reference.** Copy from the fixture. Simpler, but ties the mode to a
   file and drifts the moment the fleet side changes.

**Recommendation: option 1**, factored into a helper both models call. The precedent
is `SpikeMarketCarbonTax`, which does exactly this with
`slice(self.prospection_start_year, self.end_year)`
([`spike_market_models.py:138`](../spike_unified_mda/scenario/spike_market_models.py#L138)).

Note this brushes the flexible-start-year work: the slice must read
`prospection_start_year` off the model, never a literal 2020.

---

## 6. The global-discipline pattern, and whether the market needs `pathways_manager`

The hook exists and is documented with `fuel_market` as its worked example
([`multi_regional_process.py:514-620`](../aeromaps/core/multi_regional_process.py#L514-L620)).

```yaml
regionalisation:
  execution_mode: unified_mda
  global_models:
    customs:
      fuel_market: "models/fuel_market.py::FuelMarket"
```

`_wrap_global_model` injects `model.regions` and `model.global_namespace`, then calls
`custom_setup()`, then `_initialize_df()` a second time so `_coupling_defaults` is
rebuilt against the final region list. `separate_processes` raises if any global
model is declared, which is the correct guard.

**Does the market need `pathways_manager`? No — and it cannot have it.** The guard the
brief asks about (`pathways_manager`/`custom_setup` → `NotImplementedError`) is on
`_wrap_top_level_model` ([`:461-470`](../aeromaps/core/multi_regional_process.py#L461-L470)),
the *other* path. `_wrap_global_model` has no such guard, but it also never injects
`pathways_manager` — it only rejects `climate_historical_data`. So the pathway list
must come through `configuration_data`, exactly as the brief anticipates.

Reference implementation to follow:
[`spike_market_models.py::SpikeFuelMarket`](../spike_unified_mda/scenario/spike_market_models.py) —
`model_type="custom"`, empty grammar in `__init__`, real grammar built in
`custom_setup()` from `self.regions`, own YAML, `_initialize_df()` overridden to seed
`_coupling_defaults`.

---

## 7. How AeroMAPS defines a mode of use today

Two precedents, both a **single config string with a behaviour-preserving default**:

| axis | key | default | read at |
|---|---|---|---|
| solve vs optimise | `gemseo_settings["scenario_type"]` | `"MDA"` | [`process.py:544`](../aeromaps/core/process.py#L544) |
| region coupling | `regionalisation.execution_mode` | `"separate_processes"` | [`multi_regional_process.py:201`](../aeromaps/core/multi_regional_process.py#L201) |

The new mode should follow that shape: one key, default off.

**The complication.** `EnergyUseChoice` is a **regional** model, instantiated
unconditionally in
[`process.py:1765-1770`](../aeromaps/core/process.py#L1765-L1770) via
`AviationEnergyCarriersFactory.instantiate_energy_carriers_models`. The market is a
**global** model. So the flag has to reach two places: each regional process (to skip
the allocator) and the regionalisation config (to add the global discipline).

`_create_regional_processes` ([`:325`](../aeromaps/core/multi_regional_process.py#L325))
builds each region with `AeroMAPSProcess(configuration_file=…, custom_models=…,
optimisation=False)` — no override channel beyond `custom_models`.

**Recommendation:** declare `regionalisation.fuel_market: true` once, and propagate it
to `AeroMAPSProcess` as a new keyword alongside `optimisation=False`, which is the
existing precedent for a process-level behaviour flag. One source of truth, and the
regional configs stay untouched. The alternative — repeating the flag in every
region's config — cannot be kept consistent and would let a region silently run the
wrong allocator.

Decision 6's guard (`cost_model != "top-down"` → raise) sits naturally in the same
place, since `cost_model` is per pathway
([`process.py:1730`](../aeromaps/core/process.py#L1730)) and must be checked across
all of them at mode setup. It is a "for now", not an exclusion — see
[`REPORT.md`](REPORT.md) §6 for what actually blocks bottom-up (a vintage **mix**
effect that makes average cost *fall* with volume, hence a concave cost integral) and
the two routes out.

---

## 8. The reference run (§2.4)

Scenario: [`scenario/regionalisation.yaml`](scenario/regionalisation.yaml), two
regions differing only in traffic growth (region A 3.0 %, region B 4.5 % CAGR),
`unified_mda`, shares fixed, every pathway top-down.

Two drop-in pathways only
([`scenario/energy_carriers_step1.yaml`](scenario/energy_carriers_step1.yaml),
extracted verbatim from the default carriers file): `hefa_fog` (sustainable, share
mandate) and `fossil_kerosene` (fossil, `default: True`, the residual).
No hydrogen and no electric pathway, which side-steps the §4 multi-type guard for
step 1.

Exported by [`export_reference.py`](export_reference.py) to
`aeromaps/tests/fixtures/fuel_clearing/{reference.parquet,metadata.json}`:
102 rows (2 regions × 51 years, 2000–2050), demand, per-pathway volumes and MFSP,
per-pathway share, aircraft-type mean MFSP.

### 8.1 What the reference measures

**Energy balance closes at machine precision.** Max relative gap between
`Σ_p {p}_energy_consumption` and `energy_consumption_dropin_fuel` is **0** (region A)
and **1.15e-16** (region B) — an absolute gap of 2.0e-3 MJ against a ~1e13 MJ demand.
This is the number §3.2's exact-closure step is entitled to: a correction materially
larger than this is an error, not rounding.

**`q_init` for the sustainable pathway is zero.** The last historical year (2019)
has `hefa_fog_energy_consumption = NaN`, coerced to `0.0` in the fixture per §5.1.
So the bench starts the ramp-up from a standing start — which is exactly the
zero-lock case test 3.3.e exists to document: under the `"relative"` form,
`q_t ≤ seed + (1+g)·q_{t-1}` with `q_init = 0` and `seed = 0` pins the pathway at
zero for all time. **`rampup_seed` is not optional on this bench.**

**`hefa_fog_mean_mfsp` is flat at 0.02317 EUR/MJ** across every prospective year.
The top-down cost carries no volume dependence and, per BRIEF3, no learning
anywhere. The market's cost of entry is therefore a *constant* in this bench: every
price dynamic it produces comes from the saturation term and the duals, not from the
supply curve moving. Worth stating plainly in the report, because it bounds what
measurement 4.5.1 can show.

`dropin_fuel_mean_mfsp` nonetheless rises 0.0073 → 0.0198 EUR/MJ over 2020–2050,
entirely through the mix shifting towards the more expensive pathway.

### 8.2 The mandate trajectory

`hefa_fog`'s share is **ReFuelEU Aviation's SAF obligation, as a step** — each level
holds until the next begins (`method: previous`), which is how the regulation reads
and how the migrated optimisation work treats the 2025 obligation:

```
2020  0 %    2025  2 %    2030  6 %    2035  20 %    2040  34 %    2045  42 %    2050  70 %
```

It replaces the share the default 13-pathway config gives `hefa_fog`, whose shape
there comes from five other sustainable pathways competing for feedstock; lifted out
alone it peaked at 4.8 % in 2030 and collapsed to 0.17 % by 2040, so the ramp-up
never bound and the buy-out never engaged.

**The step years bind hard**, which is the point. Year-on-year growth of the
sustainable volume required to meet the obligation, region A:

| year | 2025 | 2030 | 2035 | 2040 | 2045 | 2050 |
|---|---|---|---|---|---|---|
| required growth | ∞ (from 0) | +202 % | +233 % | +70 % | +24 % | +66 % |

Between steps, growth tracks demand at about +1 %/year. So any ramp-up limit of a
plausible size (τ of order 20–30 %/year) is violated at every step year and slack
everywhere else. That is what gives tests 3.3.d and 3.3.f, and measurement 4.5.2,
their dynamic range — and it means the *reference* allocation is itself not
ramp-up-feasible. Test 3.3.c must therefore run with the ramp-up deliberately loose,
exactly as the brief specifies, or it would be asking the market to reproduce an
allocation its own constraints forbid.

The 2025 step starting from zero is the zero-lock case again: `q_init = 0`, and no
`rampup_seed` means no sustainable fuel ever.

---

## 9. Open questions this inventory raises

1. **Ramp-up form** — `relative` and `share_increment` are both relaxations of the
   live Eq. 12, in different directions. Which one goes in the report's headline
   comparison? (§1.1)  *Resolved for the bench: implement both, default `relative`.*
2. **Historical years** — option 1 or option 2? (§5)  *Resolved: the residual pathway
   carries the historical budget and every other pathway emits zero, never NaN
   (decision 9; `REPORT.md` §4).*
3. **Mode flag plumbing** — new `AeroMAPSProcess` keyword, or per-region config? (§7)
   *Resolved: one key, `regionalisation.fuel_market`, default off, propagated as a
   process keyword and refused outside `unified_mda`.*
4. **Multi-type guard** — hard error when the new mode meets a hydrogen or electric
   pathway, or fall back to `EnergyUseChoice` for those types only? (§4)  *Resolved: hard
   error, raised by `FuelClearing._collect_pathways` at setup.*

---

## 10. The interface as built

`FuelClearing`
([`fuel_clearing.py`](../aeromaps/models/impacts/generic_energy_model/fuel_clearing/fuel_clearing.py))
is a **global** discipline: its grammar is written in `{region}:variable` terms and it
reads every region in one call. It calls the kernel
([`kernel.py`](../aeromaps/models/impacts/generic_energy_model/fuel_clearing/kernel.py),
a pure numpy-in/numpy-out function) once per MDA sweep.

### 10.1 Declaring it

```yaml
regionalisation:
  execution_mode: "unified_mda"          # the mode is refused elsewhere
  fuel_market: true                      # replaces EnergyUseChoice in every region
  mda_tolerance: 1.0e-7                  # ~100x solver_tolerance -- REPORT §8.7
  mda_max_iter: 200
  global_models:
    standards: [models_fuel_market]
    settings:
      fuel_clearing:                     # top-level keys: every pathway but the residual
        pricing_weight: 1.0
        demand_elasticity: 0.5
        buyout_price: 0.30
        pathways:                        # per-pathway overrides
          hefa_fog: {capacity_limit: 2.0e12}
```

### 10.2 What it reads, per region

| variable | role |
|---|---|
| `energy_consumption_dropin_fuel` | the demand the market clears (MJ) |
| `energy_consumption` | denominator of two share families only |
| `{p}_net_mfsp` | **decision** cost — what the buyer faces, carbon tax and subsidies included |
| `{p}_mean_mfsp` | **publication** basis — gross, so `DirectOperatingCosts` adds the carbon tax once |
| `{p}_mandate_share` | %, on every eligible pathway; **summed** into one obligation per region |

### 10.3 What it emits, per region

| variable | meaning |
|---|---|
| `{p}_energy_consumption` | volume per pathway — replaces `EnergyUseChoice`'s |
| share families | same names as `EnergyUseChoice`, from the shared `derive_share_families` |
| `{p}_market_mfsp` | the price paid for pathway `p`, gross basis; `EnergyCarriersMeans` weights it by volume into `dropin_fuel_mean_mfsp`. At `w = 1` that average is exactly `λ_E + m·λ_M` (`REPORT.md` §11.8) |
| `fuel_market_energy_price` | λ_E, **net** basis |
| `fuel_market_compliance_price` | λ_M, **net** basis — the basis differs from `{p}_market_mfsp` (`REPORT.md` §8.9) |
| `fuel_market_unmet_obligation` | volume released through the buy-out (MJ) |

### 10.4 Settings

| key | default | what it does |
|---|---|---|
| `pricing_weight` (w) | 0.0 | share of the scarcity rent charged to airlines: 0 = average cost, 1 = marginal price |
| `discount_rate` | 0.04 | discounting inside the objective |
| `buyout_price` | 1e3 | penalty per MJ of unmet obligation; caps λ_M |
| `rampup_limit`, `rampup_seed_share`, `rampup_form` | 1e3, 1.0, `relative` | growth limit on eligible production (loose by default) |
| `capacity_limit` | inf | **hard** ceiling on production (MJ/yr); dual = scarcity rent. New 2026-09-23 |
| `capacity`, `saturation_intensity` (γ), `saturation_stiffness` (n) | inf, 0, 4 | **soft** saturation: cost bends as output nears `capacity` |
| `demand_elasticity` (η) | 0.0 | slope of the linearised demand the market prices against; a convergence device, inert at the fixed point (`REPORT.md` §11.10). Required for `w > 0` |
| `proximal_weight` | 0.0 | volume anchor; kept, off — it cannot fix a pinned primal (`REPORT.md` §8.6) |
| `solver_tolerance` | 1e-9 | Clarabel tolerance; `mda_tolerance` must sit ~100x above it |
| `demand_seed`, `cost_seed` | 1e13, 0.02 | initial values for the coupled inputs, first sweep only |

The **residual pathway is exempt** from the top-level `capacity`, `capacity_limit` and
`saturation_intensity`: a global scarcity setting reaching kerosene is almost never what
was meant (`REPORT.md` §8.9). Naming it under `pathways:` still works.

### 10.5 Guards at setup

`dropin_fuel` pathways only; top-down costs only (decision 6); exactly one `default`
pathway (the residual); at least one pathway with `mandate_type: share`; `unified_mda`
only.

### 10.6 Computed but not published

Available in `ClearingOutputs` and, with `record_trace = True`, in the discipline's
per-sweep `trace` — but not in the grammar, so not reachable from a scenario's outputs:

- `capacity_price` (rent per unit at a binding cap), `rampup_price`, `marginal_price`,
  `average_cost`, `rent`;
- `demand_adjustment` — the coupling loop's convergence measure;
- `active_signature` — which constraints are tight, for diagnosing flips.

### 10.7 In the kernel, not reachable from a scenario

- **The sub-mandate** (`submandate_share`, `is_submandated`, its own buy-out) and its
  dual λ_S — exercised by `policy_cases.py` only.
- **Region-specific eligibility** — the kernel takes `(R, P)`; the discipline passes one
  list for all regions.
- **Per-region and per-year capacities** — the kernel takes `(R, P, T)`; the settings
  give one number per pathway.
- The operating-point elasticity diagnostic (`compute_elasticity`).

---

## 11. What the step-2 options would add to the interface

Each corresponds to a section of `REPORT.md` §12; none is implemented.

### 11.1 Demand inside the kernel (§12.2, diagnostics D1–D2)

New inputs per region, all **upstream of the fuel-price loop** — which is the condition:
an input that depends on the fuel price would recreate the loop the change removes.

| input | from | to check |
|---|---|---|
| `rpk_no_elasticity` | `RPKAggregator` (`_no_elasticity` suffix) | — |
| `price_elasticity`, `initial_airfare_per_rpk` | `markets.yaml` | — |
| the year the elasticity starts | max of `{market}_covid_end_year` + 1 | before it demand is vertical, so kinks remain there |
| airline supply calibration: base-year cost per RPK, non-fuel cost per RPK by year | `PassengerAircraftMarginalCost`'s inputs | that non-fuel costs do not depend on RPK in the top-down chain |
| extra taxes and subsidies per RPK | same | where the carbon tax sits — inside or outside the supply function |
| drop-in MJ per RPK | energy intensity and load factor | exogenous in top-down; **not** under fleet-push |
| freight and other drop-in energy | energy models | price-elastic or fixed? |

New outputs: the RPK and airfare the market cleared at, for the one-sweep consistency
check against AeroMAPS's own chain.

### 11.2 Capacity variable (§12.3, D3)

Per pathway, the `BottomUpCost` inputs: `{p}_eis_capex`, `{p}_eis_fixed_opex`,
`{p}_eis_variable_opex`, `{p}_eis_plant_lifespan`, `{p}_eis_construction_time`,
`{p}_eis_plant_load_factor`, `private_discount_rate`, resource costs. For top-down
pathways, one new parameter — the capex share of the MFSP — plus lifespan and load factor.
New output: `{p}_energy_production_commissioned`, which `BottomUpCost` already reads, so it
can report costs and vintages downstream.

### 11.3 Several obligations per region (§12.4)

A list per region instead of a summed share — each with a name, a share trajectory, its
eligible pathways and its own buy-out — and one published dual per obligation,
`fuel_market_{obligation}_price`. The same list carries region-specific eligibility, and
later GHG-intensity standards, emissions caps and budgeted subsidies.

### 11.4 One global pool (§12.5, D5)

> **2026-09-24: built in the kernel, not in the discipline** — REPORT.md §13. What was
> built matches the paragraph below except in naming: the supply variable is the existing
> `q` (production), the draw is `draws`, the outputs are `supply`, `net_flow` and
> `pool_price`. The discipline needs, beyond the outputs listed here, a **use-side cost**
> input per region (the carbon tax on use, split out of `{p}_net_mfsp`) and a rule for which
> fuel is traded where the market leaves it open (REPORT §13.5).

No new AeroMAPS inputs for fuel. The kernel gains two variables per region, pathway and
year: what the region **supplies** to the pool (its production, bound by its own capacity
and feedstock) and what it **draws** (its consumption, where its obligations apply), with
one pool balance per pathway. New outputs: each region's net flow per pathway, and one pool
price per pathway in the global namespace. A feedstock pool, the long-run target, adds the
same pair for each feedstock and needs the resource availability AeroMAPS already carries
per region.

## 12. Flows between regions (`FuelTrade`, REPORT §14-15)

Built 2026-09-24 as a stand-in for the market's flow logic, to test the plumbing. Two
modes, named by `regionalisation.fuel_trade` (`true` is refused: the two wire the regions
differently).

| | `matrix` (§14) | `pool` (§15) |
|---|---|---|
| declare | `fuel_trade: matrix` + `models_fuel_trade`; the matrix under `global_models.settings.fuel_trade.sourcing` | `fuel_trade: pool` + `models_fuel_trade`; every non-default drop-in pathway of every region declares `supply: {energy_offered: ...}` (MJ), zero included |
| what decides what a region burns | its own `EnergyUseChoice` (mandates) | the pool: its demand share of every pathway's world offer; fossil kerosene fills the rest. `EnergyUseChoice` is **not instantiated** |
| reads, per region | `{p}_energy_consumption` | `energy_consumption_dropin_fuel`, `energy_consumption`, `{p}_energy_offered` |
| reads, per region, both | `carbon_tax`; `{p}_mean_co2_emission_factor`, `_mean_mfsp`, `_net_mfsp_without_carbon_tax`, `_mean_unit_subsidy`, `_mean_unit_tax` (the maker's own) | same |
| emits, per region, both | `{p}_energy_production`, `{p}_energy_net_export`; `{p}_delivered_{value}` for the five values above plus `mean_unit_carbon_tax` and `net_mfsp` | same |
| emits, per region, pool only | — | `{p}_energy_consumption` and every share family (`derive_share_families`, as `FuelClearing`); `{p}_energy_unused` |
| emits, global | `overall:{p}_energy_flow_{from}_to_{to}`, traded pathways, every ordered pair | same, pooled pathways; `overall:{p}_pool_use_rate` per pathway and `overall:fuel_pool_use_rate` all together |
| optional setting | — | `eligibility: {pathway: {region: false}}` (§15.10): may a region burn a pathway; eligible by default; the default pathway cannot be excluded |
| read downstream | `{p}_energy_production` by `TopDownEnvironmental` (feedstock); `{p}_delivered_*` by `EnergyCarriersMeans`, `NonDiscountedScenarioCost`, and `TopDownEnvironmental` for its CO2 total | same |
| refused | `separate_processes`; flag without model or model without flag; bottom-up pathways; a pathway-specific carbon tax (`{p}_carbon_tax`) | the same, plus: with `fuel_market`; any setting but `eligibility`; aircraft types other than drop-in; not exactly one default pathway; a missing or negative offer; excluding the default pathway |

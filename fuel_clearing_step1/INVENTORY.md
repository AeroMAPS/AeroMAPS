# INVENTORY — what the fuel market has to plug into

Answers to §2.3 of the step-1 brief, measured on
`feat/fuel-clearing-step1` @ `993fc9f2` (spike, rebased onto
`optimisation/refueleu-migration-and-mda-dedup`).

Read §0 first: four of the brief's premises no longer hold on this base.

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
all of them at mode setup.

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
`Σ_p {p}_energy_consumption` and `energy_consumption_dropin_fuel` is
**1.59e-16** (region A) and **1.23e-16** (region B) — absolute gaps of 2.0e-3 and
9.8e-4 MJ against a ~1e13 MJ demand. This is the number §3.2's exact-closure step
is entitled to: a correction materially larger than this is an error, not rounding.

**`q_init` for the sustainable pathway is zero.** The last historical year (2019)
has `hefa_fog_energy_consumption = NaN`, coerced to `0.0` in the fixture per §5.1.
So the bench starts the ramp-up from a standing start — which is exactly the
zero-lock case test 3.3.e exists to document: under the `"relative"` form,
`q_t ≤ seed + (1+g)·q_{t-1}` with `q_init = 0` and `seed = 0` pins the pathway at
zero for all time. **`rampup_seed` is not optional on this bench.**

**`hefa_fog_mean_mfsp` is flat at 0.02317 EUR/MJ** across every prospective year,
against a `dropin_fuel_mean_mfsp` that declines from 0.0121 to 0.0120. The top-down
cost carries no volume dependence and, per BRIEF3, no learning anywhere. The market's
cost of entry is therefore a constant in this bench, and all price dynamics come
from the saturation term and the duals — worth stating plainly in the report, since
it bounds what measurement 4.5.1 can show.

### 8.2 A caveat on the mandate trajectory

`hefa_fog`'s share was taken verbatim from the default 13-pathway config, where its
shape is set by the five other sustainable pathways competing for feedstock. In
isolation it is non-monotonic:

```
2020  0.00 %     2030  4.80 %  (peak)     2040  0.17 %  (trough)     2050  0.25 %
```

Faithful to the source, but a poor step-1 reference: a mandate that collapses after
2030 never makes the ramp-up bind, leaves the buy-out slack at zero, and gives
measurement 4.5.2 nothing to sweep against. See the open question in §9.

---

## 9. Open questions this inventory raises

1. **Ramp-up form** — `relative` and `share_increment` are both relaxations of the
   live Eq. 12, in different directions. Which one goes in the report's headline
   comparison? (§1.1)
2. **Historical years** — option 1 or option 2? (§5)
3. **Mode flag plumbing** — new `AeroMAPSProcess` keyword, or per-region config? (§7)
4. **Multi-type guard** — hard error when the new mode meets a hydrogen or electric
   pathway, or fall back to `EnergyUseChoice` for those types only? (§4)

# Brief 3 — I/O contract for replacing `EnergyUseChoice`

**Verdict, one sentence.** A market module can replace the mandate mechanism by
producing **exactly one family of variables — `{pathway}_energy_consumption`, in MJ,
for every pathway** — because all 85 other `EnergyUseChoice` outputs are shares
algebraically derivable from that family plus the fleet-side energy totals; but it
must reproduce **one invariant the mandate mechanism enforces structurally and
nothing downstream checks**: `Σ_pathways E_p = energy_consumption_{aircraft_type}`,
exactly, every year, for every aircraft type. Breaking it does not raise — it
silently rescales CO₂ and fuel cost by the size of the gap (§ 2, measured: drop-in
emission factor falls 78.9 → 17.3 gCO₂/MJ on a 50 % gap, with a `warnings.warn`).

Three structural findings fall out of the trace and matter more than the variable list:

1. **Vintaging is real but myopic and has no build lead time.** `BottomUpCapacity`
   builds exactly this year's shortfall, available this year. `eis_construction_time`
   exists only in the *cost* model, where it spreads capex backwards over
   `year-construction_time : year` and enters the NPV annualisation. Physical
   availability is instantaneous (§ 3.2).
2. **There is no learning anywhere in `aeromaps/`.** Zero occurrences of
   `learning`, `experience curve`, `NOAK/FOAK`, or any capacity→cost feedback.
   All cost decline is exogenous, read off a year-indexed `eis_capex` series keyed on
   the vintage's EIS year (§ 3.4).
3. **`*_marginal_net_mfsp` is computed and consumed by nothing.** Not a model, not a
   plot — it exists only as a column in `outputs.json`. The average/marginal split
   the brief anticipates is currently 100 % average: `dropin_fuel_mean_mfsp` is the
   single price that reaches the airfare and therefore the demand loop (§ 5).

Measurements are on `aeromaps/tests/tested_configs/config_basic.yaml` (default energy
carriers: 13 pathways, 86 `EnergyUseChoice` outputs). Nothing under `aeromaps/` was
modified; the § 2 experiment runs against a copied config.

---

## 1. Inventory of `EnergyUseChoice` outputs, and who consumes them

`common/energy_use_choice.py` declares its grammar in `__init__` from
`pathways_manager`. For the default config (13 pathways: 7 drop-in, 5 hydrogen,
1 electric; 3 energy origins: biomass, fossil, electricity) that is **86 outputs in
9 families**. 47 are read by another model; 3 more only by a plot; **36 are dead**.

### 1.1 The families

| # | family | count | unit | read by |
|---|--------|-------|------|---------|
| A | `{pathway}_energy_consumption` | 13 | MJ | `energy_carriers_massic_shares`, `non_discounted_scenario_cost`, `{pathway}_{top_down\|bottom_up}_unit_environmental`, `{pathway}_bottom_up_capacity`, `{pathway}_bottom_up_unit_cost`, `{pathway}_abatement_effective` |
| B | `{pathway}_share_total_energy` | 13 | % | — dead |
| C | `{pathway}_share_{aircraft_type}` | 13 | % | `energy_carriers_means` |
| D | `{energy_origin}_share_total_energy` | 3 | % | plot only (`plots/single_scenario/aircraft_energy.py:448`) |
| E | `{pathway}_share_{energy_origin}` | 13 | % | — dead |
| F | `{energy_origin}_share_{aircraft_type}` | 6 | % | 3 of 6 → `drop_in_fuel_detailed_consumption` |
| G | `{aircraft_type}_share_{energy_origin}` | 6 | % | — dead |
| H | `{aircraft_type}_{energy_origin}_energy_consumption` | 6 | MJ | 5 of 6 → `non_co2_emissions` |
| I | `{pathway}_share_{aircraft_type}_{energy_origin}` | 13 | % | `energy_carriers_means` |

13×5 + 3 + 6×3 = 86. ✓

The three members of F that matter are hard-coded as *mandatory* outputs at
`energy_use_choice.py:117-123`, emitted as zeros when no such pathway exists:
`biomass_share_dropin_fuel`, `electricity_share_dropin_fuel`, `fossil_share_dropin_fuel`.
The one dead member of H is `electric_electricity_energy_consumption` — `NonCO2Emissions`
loops over `["dropin_fuel", "hydrogen"]` only (`non_co2_emissions.py:967`).

### 1.2 The four chains, end to end

**Chain 1 — MFSP means → airfare → demand.** This is the only chain that closes a loop.

```
{p}_energy_consumption ─┐
                        ├─► (nothing: EnergyCarriersMeans uses shares, not volumes)
{p}_share_{type}        ┴─► energy_carriers_means
{p}_share_{type}_{origin}      │  mean X = Σ_p  share_p/100 × X_p       (no renormalisation)
                               ▼
        {type}_mean_mfsp, {type}_mean_net_mfsp, {type}_mean_net_mfsp_without_carbon_tax,
        {type}_mean_carbon_tax_supplement, {type}_marginal_net_mfsp,
        {type}_mean_unit_{subsidy,tax,carbon_tax}, {type}_mean_co2_emission_factor
                               │
        dropin_fuel_mean_mfsp ─┴─► passenger_aircraft_doc_energy       (doc_energy_per_ask_*)
        {type}_mean_unit_carbon_tax ─► passenger_aircraft_doc_energy_carbon_tax
        {type}_mean_unit_subsidy    ─► passenger_aircraft_doc_energy_subsidy
        {type}_mean_unit_tax        ─► passenger_aircraft_doc_energy_tax
                               │
                               ▼  PassengerAircraftTotalDoc → TotalAirlineCost →
                                  PassengerAircraftMarginalCost → airfare → elasticity → RPK
```

Per-origin means (`{type}_{origin}_mean_*`, 54 variables) are consumed by **nothing**.

**Chain 2 — emissions.**

```
{p}_share_{type}  ─► energy_carriers_means ─► {type}_mean_co2_emission_factor
                                                   │
    energy_consumption_{type}  (fleet side) ───────┴─► co2_emissions
                                    CO2 = Σ_type  EF_type × energy_consumption_type

{p}_energy_consumption ─► energy_carriers_massic_shares ─► {p}_mass_consumption,
                                                           {p}_massic_share_{type}[_{origin}]
                                                   │
        ├─► energy_carriers_mean_lhv       ─► {type}_{origin}_mean_lhv
        ├─► {nox,soot,h2o,sulfur}_emission_index ─► {type}_{origin}_mean_emission_index_*
        ├─► fuel_effect_correction_contrails (non_co2.py, advanced only)
        └─► LCA (`{p}_mass_consumption`, referenced by name from the LCA yaml)
                                                   ▼
        {type}_{origin}_energy_consumption  ─► non_co2_emissions ─► soot/h2o/nox/sulfur
```

**Chain 3 — pathway-level costs and resources.** `{p}_energy_consumption` is the
volume that drives every per-pathway model: `TopDown/BottomUpEnvironmental` (resource
consumption, `{p}_mean_co2_emission_factor`), `TopDown/BottomUpCost`
(`{p}_mean_mfsp`, `{p}_net_mfsp`, `{p}_net_mfsp_without_carbon_tax`,
`{p}_mean_unit_{tax,subsidy,carbon_tax}`), `BottomUpCapacity`, `EnergyAbatementEffective`.

**Chain 4 — scenario indicators.** `non_discounted_scenario_cost` reads
`{p}_mean_mfsp`, `{p}_net_mfsp`, `{p}_energy_consumption` for every pathway →
`non_discounted_energy_expenses`, `non_discounted_net_energy_expenses`. It also
hard-codes the pathway name `fossil_kerosene` (`scenario_cost.py:63, 126-135`) to
build the BAU and full-kerosene counterfactuals; if no pathway is literally named
`fossil_kerosene` it falls back to printed constants (88.7 gCO₂/MJ, 0.0139 €/MJ).

### 1.3 Inputs `EnergyUseChoice` reads

| variable | producer |
|----------|----------|
| `energy_consumption_dropin_fuel` | `DropInFuelConsumption` (`energy_resources/energy_consumption.py:12`) |
| `energy_consumption_hydrogen` | `HydrogenConsumption` (`:382`) |
| `energy_consumption_electric` | `ElectricConsumption` (`:560`) |
| `energy_consumption` | `EnergyConsumption` (`:738`) — denominator of family B/D only |
| `{p}_mandate_share` \| `{p}_mandate_quantity` | exogenous, from `energy_carriers_data.yaml` |

`energy_consumption_{aircraft_type}` is the **hard budget**. The aircraft type key
comes from `pathways_manager.get_all_types("aircraft_type")`; an unsupported value
raises a `KeyError` with an explicit message (`energy_use_choice.py:144-148`).

---

## 2. The `default` pathway as balancing item

### 2.1 What it does

`compute()` runs three passes per aircraft type
(`energy_use_choice.py:151-300`):

1. **quantity mandates** — `{p}_mandate_quantity` taken literally; if their sum
   exceeds the type's demand, all are scaled by a common
   `remaining / total_quantity` factor and a per-pathway `warnings.warn` lists the
   modified years.
2. **share mandates** — `{p}_mandate_share/100 × energy_consumption`; same
   homogeneous down-scaling against the *residual* budget, same warning.
3. **the default pathway takes `remaining_energy_consumption`, whatever it is.**

So the default is a residual, not a decision. Three consequences:

- **The energy balance is closed by construction.** `Σ_p E_p ≡ energy_consumption_{type}`
  always, and therefore `Σ_p share_p ≡ 100 %`.
- **The default can never go negative,** because passes 1 and 2 clip against the
  remaining budget before it is reached.
- **Exactly one default per aircraft type is mandatory.** Zero → `ValueError`
  ("It is mandatory to define a default … pathway"); more than one → `ValueError`.
  Both fire only when that type's consumption is non-zero and non-NaN.

### 2.2 What breaks if a market determines it explicitly

Nothing downstream re-derives or renormalises. `EnergyCarriersMeans` computes
`mean X = Σ_p (share_p / 100) × X_p` and multiplies by
`valid_years = cumulative_share.replace(0, np.nan)` — which nulls years with *zero*
consumption but does **not** divide by the cumulative share. A share sum of 50 %
yields a mean that is 50 % of the truth. The only guard is a `warnings.warn`
("AeroMAPS internal error: sum of pathway shares for … is not equal to 100 %").

Measured. Copy the default carriers yaml, give `fossil_kerosene` (the drop-in
default) a flat 50 % share mandate, run `config_basic`:

| 2035 | baseline | default given a mandate |
|------|----------|--------------------------|
| `Σ_p {p}_energy_consumption` (drop-in) | 1.224e13 MJ | **6.120e12 MJ** |
| `energy_consumption_dropin_fuel` | 1.224e13 MJ | 1.224e13 MJ |
| `Σ_p {p}_share_dropin_fuel` | 100.0 % | **50.0 %** |
| `dropin_fuel_mean_co2_emission_factor` | 78.85 gCO₂/MJ | **17.25 gCO₂/MJ** |
| `dropin_fuel_mean_mfsp` | 0.02060 €/MJ | **0.00721 €/MJ** |

`co2_emissions` then multiplies 17.25 by the *full* 1.224e13 MJ, because the total
comes from the fleet side, not from the pathway sum. Half the fuel disappears from
the pathway accounting and CO₂ falls by 78 %, with warnings only.

The reason a mandate on the default is even reachable is a latent bug at
`energy_use_choice.py:59-75`:

```python
if pathway.default:
    # default pathway does not use any mandate even if defined
    pass                      # ← no-op; falls through
if pathway.mandate_type == "quantity":     # ← not elif, not guarded on default
```

The comment states the intent; the code does not implement it. The default's mandate
input is declared, `pathways_manager.get(aircraft_type=…, mandate_type=…)` returns the
default alongside the others, it is served in pass 1 or 2, `remaining` is decremented
by its own mandate, and then pass 3 **overwrites** its `_energy_consumption` with the
residual. The mandated volume is subtracted from the budget and then thrown away.

### 2.3 The other, unrelated meaning of `default: True`

`FuelEffectCorrectionContrails` (`air_transport/.../non_co2/non_co2.py:198-216`) uses
the drop-in default pathway as the **reference fuel for soot**:

```python
default_pathway = self.pathways_manager.get(aircraft_type=aircraft_type, default=True)[0]
default_emission_index_number_particles = input_data[f"{default_pathway.name}_emission_index_particles_number"]
relative_particles_number += share_p/100 * sqrt(EI_particles_p / default_EI_particles)
```

A market module that stops using `default` as a balancing item must still keep the
flag (or provide another reference-fuel designation), or contrail forcing loses its
normalisation. This is a second, independent responsibility riding on one boolean.

### 2.4 Index contract, easy to get wrong

The zero-consumption branch (`:302-308`) emits
`pd.RangeIndex(historic_start_year, end_year+1)`. The normal branch inherits
`energy_consumption.index`. A market module must emit the **same** index in both
cases; downstream `_custom_series_addition` and `.loc[year:year+lifespan-1]` slicing
tolerate misalignment silently by filling NaN.

---

## 3. State of vintaging in `bottom_up/`

### 3.1 What a vintage is

`BottomUpCapacity` (`bottom_up/production_capacity.py`) reconstructs a commissioning
history from the consumption trajectory alone:

```python
for year in years:
    missing = energy_required[year] - energy_produced[year]
    if missing <= 0:  energy_unused[year] = missing
    else:
        required_capacity = missing / plant_load_factor          # MJ/yr nameplate
        plant_building_scenario[year] += required_capacity
        plant_available_scenario.loc[year : year+lifespan-1] += required_capacity
        energy_produced.loc[year : year+lifespan-1]         += missing
```

A vintage is `(commissioning year, capacity)`, alive for `lifespan` years, then gone —
whereupon the loop rebuilds. `plant_load_factor` is
`min(eis_plant_load_factor, {resource}_load_factor …)`. Outputs:
`{p}_plant_building_scenario` (additions), `{p}_energy_production_commissioned`
(the served shortfall), `{p}_plant_operating_capacity`, `{p}_energy_unused`
(overcapacity, sign-flipped on export), and `{p}_{process}_plant_building_scenario`.

**Pre-history back-cast.** Because consumption before `historic_start_year` is
unknown but pre-existing plants retire *during* the scenario, the model synthesises a
virtual demand series from `{p}_technology_introduction_year` /
`_technology_introduction_volume` at a CAGR fitted to hit
`energy_required[historic_start_year]` (`:127-147`). Missing either input while
`energy_required[historic_start_year] > 1e-9` raises `ValueError`.

### 3.2 Build lead time: absent from the physics

`eis_construction_time` (default **3** years) appears **only** in `BottomUpCost`, twice:

- inside `_spread_capital`, as the NPV of a uniform construction outlay discounted at
  `private_discount_rate`;
- spreading `{p}_capex_cost` over `.loc[year - construction_time : year]` — i.e.
  *backwards* from commissioning, a retrospective cash-flow attribution.

`BottomUpCapacity` never reads it. **Capacity commissioned in year *y* serves demand
in year *y*.** A market module that wants investment to respond to price with a lag
must add that lag itself; there is no hook.

### 3.3 Capex annualisation and lifetime

`BottomUpCost._spread_capital` (`bottom_up/cost.py:679-714`):

```
r ≠ 0:  term = 1/(1+r)
        NPV_capex      = capex/T_c · (1 - term^T_c)/(1 - term)
        NPV_production = term^T_c · (1 - term^L)/(1 - term)
        unit_capex     = NPV_capex / NPV_production
r = 0:  unit_capex     = capex / L
```
then `/= load_factor`. `r = private_discount_rate` (scalar), `L = eis_plant_lifespan`
(default 25), `T_c = eis_construction_time` (default 3). All three via
`_get_value_for_year`, so all three may be year-indexed on the **EIS year**.

Each vintage carries a cost trajectory `vintage_mfsp` over `year … year+L-1`:
`unit_capex + fixed_opex + variable_opex + Σ_resources price_r(t)·specific_consumption
+ Σ_processes (…)`. Resource prices vary *within* the vintage's life, held at the last
value beyond `end_year`. Aggregation to the annual mean is production-weighted:

```python
relative_share = needed_capacity / (energy_consumption + energy_unused)
{p}_mean_mfsp[y] = Σ_vintages  vintage_mfsp_v[y] × relative_share_v[y]
```

Per-vintage EIS values are exported for the waterfall plots:
`{p}_vintage_unit_{capex,fixed_opex,variable_opex}`,
`{p}_excluding_processes_{r}_vintage_unit_cost`, `{p}_{proc}_vintage_unit_*`,
`{p}_vintage_eis_co2_emission_factor`, `{p}_vintage_eis_carbon_tax`. Consumed by
`plots/single_scenario/costs_generic.py` only.

**Known distortion.** `{p}_energy_production_commissioned` is sliced to
`prospection_start_year : end_year` before export (`production_capacity.py:222-224`),
so `BottomUpCost` never iterates the back-cast virtual vintages. For a pathway with
pre-existing capacity, `Σ_v relative_share_v < 1` in the early years and
`{p}_mean_mfsp` under-weights accordingly. The environmental model has the same shape.

### 3.4 Learning: nothing

```
grep -rniE 'learning|experience.curve|noak|foak|scale.effect' --include='*.py' --include='*.yaml' .
→ no matches
```

There is no capacity→cost feedback of any kind: `{p}_plant_building_scenario`,
`{p}_plant_operating_capacity` and the cumulative-deployment quantities they imply are
read by no cost model. Cost decline is exogenous only, through year-indexed
`eis_capex` / `eis_fixed_opex` / `eis_variable_opex` (`!AeroMapsCustomDataType`,
interpolated over scenario years) evaluated at each vintage's EIS year — and in every
shipped bottom-up config those series are flat constants
(`notebooks/tutorials/04_use_bottom_up_fuel_models/data/energy_carriers_data-full_BU.yaml`).

A learning curve is therefore a **new** coupling
(`{p}_plant_building_scenario` → cumulative capacity → `eis_capex`), and it would close
a loop that does not exist today: capacity currently depends on cost only through
whatever exogenous mandate set the volume.

---

## 4. Resources: `*_availability_global` and `*_aviation_allocated_share`

**Purely indicative. Nothing physical is constrained by them anywhere in `aeromaps/`.**

`EnergyResourceConsumption` (one instance per resource) sums pathway demand and
divides:

```python
{r}_total_consumption                          = Σ_p {p}_{r}_total_consumption
{r}_total_necessary_with_selectivity           = Σ_p {p}_{r}_total_mobilised_with_selectivity
{r}_consumed_global_share                      = total_consumption / {r}_availability_global × 100
{r}_necessary_global_share_with_selectivity    = total_necessary  / {r}_availability_global × 100
{r}_consumed_aviation_allocated_share          = total_consumption / (availability_global × allocated_share/100) × 100
```

`OverallResourcesConsumption` repeats the aggregation per `origin`
(biomass / electricity / …), adding `{origin}_availability_global`,
`{origin}_availability_aviation_allocated`, `{origin}_overall_aviation_allocated_share`.

Both are **inputs** (exogenous yaml `specifications`), never outputs of a model, and
no model reads the resulting shares. Consumers, exhaustively:

| consumer | kind |
|----------|------|
| `plots/single_scenario/sustainability_assessment.py` | reporting |
| `gui/graphical_user_interface.py` | sets the *inputs* from GUI sliders |
| `notebooks/tutorials/09_optimise_a_scenario/custom_constraints.py`, `publications/{tsas_2025,ecats_2026}/energy_constraints.py` | user-supplied optimisation constraints, `(share − 100)/100 ≤ 0` |

That last row is the one exception worth noting: in an *optimisation* process, the
share becomes a constraint the optimiser sees — but that is user code in a notebook,
not a model, and it acts on the design variables (mandate trajectories), not on the
allocation itself. In a plain MDA run, exceeding availability by 400 % produces a
plot with a line above 100 % and nothing else.

`{r}_load_factor` is different — it *is* read, by `BottomUpCapacity` and
`BottomUpCost`, where it caps the plant load factor. And `{p}_kerosene_selectivity`
scales resource *mobilisation* (`resource_consumption / selectivity`) to account for
the non-aviation co-products, feeding only the `*_with_selectivity` reporting family.

**Implication for a market module.** If scarcity is to bind — a rising supply curve, a
binding biomass cap, resource rent — none of that machinery exists to be reused. The
availability numbers are curated and per-resource, so they are the natural data source,
but the market module must consume them itself and close the constraint itself.

---

## 5. Average versus marginal pricing

### 5.1 What exists

Three price levels per pathway, from `TopDownCost` / `BottomUpCost`:

| variable | content |
|----------|---------|
| `{p}_mean_mfsp` | production cost, levelised, incl. resources and processes. No policy. |
| `{p}_net_mfsp_without_carbon_tax` | `mean_mfsp + mean_unit_tax − mean_unit_subsidy` |
| `{p}_net_mfsp` | `+ mean_unit_carbon_tax` (= `carbon_tax/1000 × EF/1000`) |
| `{p}_marginal_mfsp` | **bottom-up only**: per year, the max `vintage_mfsp` over vintages alive that year |

`EnergyCarriersMeans` aggregates to aircraft type and to (type, origin):

```python
mean_X            = Σ_p  share_p/100 × X_p                    # average
marginal_net_mfsp = max_p  net_mfsp_p                          # marginal = most expensive pathway in use
```

Note the definitional weakness: the "marginal" price is the max over **all** pathways
of that type, including pathways with zero share that year — `net_mfsp_p` is reindexed
and `fillna(0)`-ed, so a pathway that is not deployed still competes for the max as
long as its cost series is defined. It is a cost-envelope, not a market-clearing price.

### 5.2 Where each is consumed

**`{type}_mean_mfsp` — the price that matters.**

| consumer | file | effect |
|----------|------|--------|
| `passenger_aircraft_doc_energy` | `costs/airlines/direct_operating_costs.py:359-361` | `doc_energy_per_ask_{market}_{type} = energy_per_ask × mean_mfsp` → `doc_energy_per_ask_mean` → `PassengerAircraftTotalDoc` → `TotalAirlineCost` → `PassengerAircraftMarginalCost` → airfare → **elasticity → RPK** |

`{p}_mean_mfsp` and `{p}_net_mfsp` additionally feed `non_discounted_scenario_cost`
(reporting totals). Tax, subsidy and carbon-tax components reach the airfare through
*separate* DOC models (`…doc_energy_carbon_tax`, `…doc_energy_subsidy`,
`…doc_energy_tax`) reading `{type}_mean_unit_{carbon_tax,subsidy,tax}` — so the
decomposition, not `net_mfsp`, is what crosses into the cost chain.

**`{type}_marginal_net_mfsp` and `{type}_{origin}_marginal_net_mfsp` — consumed by nothing.**

```
grep -rln 'marginal_net_mfsp' .
→ energy_carriers_means.py (the producer)
→ **/outputs.json  (dumped results only)
→ spike_unified_mda/…  (this spike)
```

No model, no plot, no notebook analysis. Same for `{p}_marginal_mfsp` from
`BottomUpCost`. Also unconsumed: all 54 `{type}_{origin}_mean_*` variables, plus
`{type}_mean_net_mfsp`, `{type}_mean_net_mfsp_without_carbon_tax` and
`{type}_mean_carbon_tax_supplement`.

### 5.3 What this means for producer rent

Today the model cannot say anything about producer rent, and not for want of a
variable name: **the average price is what airlines pay.** Every MJ is billed at
`Σ_p share_p × mfsp_p`, so an infra-marginal biofuel plant earns exactly its own
levelised cost and rent is identically zero by construction. The marginal price is
computed and discarded.

Switching to marginal pricing is therefore a **one-line change in one consumer** —
`passenger_aircraft_doc_energy` reading `{type}_marginal_net_mfsp` instead of
`{type}_mean_mfsp` — and a **large change in meaning**: the gap
`(marginal − mean) × E_type` becomes producer rent, which then has to be attributed
(to whom? taxed? recycled?) and which no existing model accounts for. The market
module should emit both, plus the rent explicitly, rather than leaving it as a
subtraction downstream consumers may or may not perform:

```
{type}_mean_mfsp          €/MJ   average production cost (what the mean chain expects today)
{type}_marginal_net_mfsp  €/MJ   clearing price
{type}_producer_rent      €      (p_clearing − Σ_p share_p·mfsp_p) × energy_consumption_{type}
```

Note also that `EnergyCarriersMeans` currently computes both from the same share
weights, so if a market module supplies prices directly it should either write
`{type}_mean_mfsp` itself or keep supplying `{p}_share_{type}` in a form that makes
the existing weighted sum come out right.

---

## 6. The contract

### 6.1 Mandatory — a market module must emit these

| variable | unit | index | invariant |
|----------|------|-------|-----------|
| `{p}_energy_consumption`, ∀ pathway | MJ | `historic_start_year … end_year` | `Σ_{p ∈ type} E_p = energy_consumption_{type}` **exactly**, ∀ year, ∀ aircraft_type; `E_p ≥ 0` |
| `{p}_share_{aircraft_type}` | % | idem | `E_p / energy_consumption_{type} × 100`; `Σ = 100` |
| `{p}_share_{aircraft_type}_{energy_origin}` | % | idem | `E_p / Σ_{p' ∈ (type,origin)} E_{p'} × 100`; `Σ = 100` per (type, origin) |
| `{aircraft_type}_{energy_origin}_energy_consumption` | MJ | idem | `Σ_{p ∈ (type,origin)} E_p` |
| `biomass_share_dropin_fuel`, `electricity_share_dropin_fuel`, `fossil_share_dropin_fuel` | % | idem | zeros if the origin is absent; `Σ = 100` |

Five families, all algebraic in the first. Emit the same index whether or not the type
has demand; use `0.0`, not NaN, for absent pathways — `EnergyCarriersMeans` treats a
zero cumulative share as "no demand this year" and nulls the mean.

### 6.2 Must be preserved even though `EnergyUseChoice` will be gone

- **One `default: True` pathway per aircraft type** — the contrail soot reference
  (§ 2.3). Either keep the flag or give `FuelEffectCorrectionContrails` an explicit
  `reference_pathway` setting.
- **A pathway literally named `fossil_kerosene`** if BAU/full-kerosene counterfactuals
  are to remain meaningful (`scenario_cost.py:126-135`).
- **Aircraft types restricted to `dropin_fuel` / `hydrogen` / `electric`** —
  `EnergyCarriersMeans`, `NonCO2Emissions`, `CO2Emissions` and the four DOC-energy
  models all hard-code that list.

### 6.3 Safe to drop

The 36 dead outputs (families B, E, G, and the unconsumed members of F and H) and,
if the aircraft-energy "All types" plot is adjusted, the 3 in family D. Nothing reads
them.

### 6.4 What the market module must supply that no current variable carries

- **A binding scarcity signal.** Availability is diagnostic only (§ 4); enforcing it
  is new work.
- **A build lead time** on physical capacity (§ 3.2).
- **A clearing price and the rent it implies** (§ 5.3).
- **Any endogenous cost decline** (§ 3.4) — and note this closes a genuinely new MDA
  loop (deployment → capex → price → deployment), which is exactly the kind of loop
  the § 2 balance invariant will be stressed by. The residual-item trick that
  guarantees closure today does not survive contact with a market that sets every
  volume; the invariant has to become an explicit constraint the market solves,
  and it is worth asserting rather than warning.

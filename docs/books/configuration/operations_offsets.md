# Operations and offsets

Two generic modules describe the operational improvements and the carbon
offsetting of a scenario as lists of named entries. Each is optional: without
its block, the simple models and their `parameters.json` inputs apply.

Status labels are defined on the [section index](index.md#how-to-read-the-parameter-tables).
Both files are strict: a missing input of a declared channel or mode stops the
run with a *Missing required names* error.

## Operations

| | |
|---|---|
| Packaged default | [`default_operations/operations_data.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/default_operations/operations_data.yaml): the three operational pillars of the DESTINATION 2050 roadmap (2025 edition) |
| Entry config key | `models.operations.operations_model_data_file` |
| Active | When the `models.operations` block is in your config. |
| Replaces | The simple models `operations_logistic` / `operations_interpolation` and `operations_contrails_simple`. Their `parameters.json` inputs (`operations_final_gain`, `operations_contrails_final_gain`…) are no longer read. |

Each top-level entry is an **operational concept** with one or two
**channels**:

```yaml
airline_operations:
  name: "airline_operations"
  category: "airline_operations"
  inputs:
    fuel_efficiency:
      gain: !AeroMapsCustomDataType       # [%] reduction of the energy per ASK
        years: [2020, 2030, 2040, 2050]
        values: [0.0, 3.5, 4.3, 4.7]
        method: linear

contrail_avoidance:
  name: "contrail_avoidance"
  category: "contrails"
  inputs:
    contrails:
      gain: !AeroMapsCustomDataType       # [%] reduction of the contrail climate impact
        years: [2020, 2035, 2050]
        values: [0.0, 30.0, 60.0]
        method: linear
      overconsumption: !AeroMapsCustomDataType   # [%] fuel penalty of avoidance
        years: [2020, 2050]
        values: [0.0, 0.5]
        method: linear
```

| Key | Status | Unit | Description |
|---|---|---|---|
| `name` | Required | — | Same value as the entry key (an error otherwise). |
| `category` | Optional | — | Concepts of the same category are summed in the outputs and plots. |
| `inputs` | Required | — | One or both channels below. |
| `inputs.fuel_efficiency.gain` | Required in the `fuel_efficiency` channel | % | Reduction of the energy per ASK. |
| `inputs.contrails.gain` | Required in the `contrails` channel | % | Reduction of the contrail climate impact. |
| `inputs.contrails.overconsumption` | Required in the `contrails` channel | % | Fuel-burn increase caused by contrail avoidance. Use `0.0` for none. |

The gains of the concepts **compose multiplicatively**, for instance two 10 %
fuel-efficiency gains give 19 %, not 20 %. They only apply from the
prospection start year. See
[the operations documentation](../documentation_airtransport.md#operational-concepts).

## Offsets

| | |
|---|---|
| Packaged default | [`default_offsets/offsets_data.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/default_offsets/offsets_data.yaml): two illustrative schemes, CORSIA-like and removals |
| Entry config key | `models.offsets.offsets_model_data_file` |
| Active | When the `models.offsets` block is in your config. |
| Replaces | The simple models `level_carbon_offset`, `residual_carbon_offset`, `manual_carbon_offset`, `carbon_offset` and the single-price cost model. Their `parameters.json` inputs (`corsia_reference_year`, `carbon_offset_baseline_*`, `residual_carbon_offset_share_*`, `manual_carbon_offset_*`, `carbon_offset_price_*`) are no longer read. |

Each top-level entry is an **offsetting scheme** with a quantity rule and a
price:

```yaml
corsia:
  name: "corsia"
  category: "offsets"
  inputs:
    quantity:
      mode: "level"
      reference_year: 2019
      baseline_level_vs_reference_year: !AeroMapsCustomDataType   # [%]
        years: [2020, 2050]
        values: [85.0, 85.0]
        method: linear
      coverage: !AeroMapsCustomDataType                            # [%]
        years: [2020, 2023, 2024, 2027, 2050]
        values: [0.0, 0.0, 50.0, 60.0, 60.0]
        method: linear
    economics:
      price: !AeroMapsCustomDataType                               # [EUR/tCO2]
        years: [2020, 2024, 2035, 2050]
        values: [20.0, 20.0, 60.0, 60.0]
        method: linear
```

| Key | Status | Unit | Description |
|---|---|---|---|
| `name` | Required | — | Same value as the entry key (an error otherwise). |
| `category` | Optional | — | Schemes of the same category are summed in the outputs. |
| `inputs.quantity.mode` | Required | — | `level`, `share_of_residual` or `quantity` (an error otherwise). |
| `inputs.economics.price` | Required | €/tCO₂ | Price of the scheme, held at its nearest value outside its reference years. |

Mode-specific keys, all **Required** for their mode and ignored otherwise:

| Mode | Key | Unit | Quantity offset each year |
|---|---|---|---|
| `level` | `reference_year` | year | Emissions above a baseline, times the coverage: `max(0, E − level × E(reference_year)) × coverage`. Same rule as CORSIA. |
| `level` | `baseline_level_vs_reference_year` | % | Baseline as a share of the reference-year emissions. |
| `level` | `coverage` | % | Share of the emissions in the scheme's scope. |
| `share_of_residual` | `share` | % | Share of the emissions left after the `level` schemes. |
| `quantity` | `amount` | MtCO₂ | Prescribed quantity. |

`level` schemes are applied first, then `share_of_residual` schemes on what
remains, then `quantity` schemes. Offsetting only applies from the prospection
start year. A warning is raised if the residual shares add up to more than
100 %, or if more than the emissions is offset.

The total offset is the sum of the schemes; its price is the
quantity-weighted mean of the scheme prices. Each scheme's quantity also
appears as a sub-lever of the offsetting lever in the CO₂ decomposition. See
[the impacts documentation](../documentation_impacts.md#carbon-offset-per-scheme).

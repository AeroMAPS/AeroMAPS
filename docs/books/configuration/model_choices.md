# Model choices and the parameters they need

AeroMAPS is assembled from interchangeable models. Each choice decides which
parameters are read, and the parameters of a model you did not select are
ignored, in most cases **without any warning**. This page lists, for every
choice, what you must provide and what stops being read.

Status labels are defined on the [section index](index.md#how-to-read-the-parameter-tables).

## Where each choice is made

| Choice | Where | Options |
|---|---|---|
| Passenger aircraft efficiency | `models.standards` | top-down, top-down with interpolated operations, bottom-up fleet, push fleet |
| Freight aircraft efficiency | `models.standards` | indexed on passenger efficiency (default), own gain curve |
| Airline operating costs | `models.standards` | top-down, bottom-up, and their `_feedback` variants |
| Contrails and fuel properties | `models.standards` | with or without fuel effect |
| Passenger demand | markets file, `global.demand.model` | `cagr`, `cagr_elasticity`, `constant_elasticity`, `logistic_income` |
| Load factor | markets file, `global.load_factor.model` | `quadratic`, `simple_interpolation` |
| Fuel pathway models | energy carriers file, per pathway | `environmental_model` and `cost_model`: `top-down` or `bottom-up` |
| Operational gains | presence of `models.operations` | simple (`parameters.json`) or generic (operations file) |
| Carbon offsetting | presence of `models.offsets` | simple (`parameters.json`) or generic (offsets file) |
| Climate model | climate file, `climate_model` | `FaIR`, `GWP*`, `IPCC`, `LWE` |
| Coupling between regions | `regionalisation.execution_mode` | `separate_processes`, `unified_mda` |

## Aircraft efficiency

One efficiency bundle per run. It decides how the fleet is described.

| Bundle | Fleet description read | Also needs | Not read |
|---|---|---|---|
| `models_efficiency_top_down` | Markets file: `efficiency_simple` of each passenger market (drop-in gain curve, hydrogen and electric introduction). | Markets `costs` if you use `models_operation_cost_top_down`. | The `models.fleet` files (if the block is present, the fleet model still runs but its results are not used). |
| `models_efficiency_top_down_interp` | Same as top-down. | Same as top-down. | Same as top-down. The operational gain follows `operations_gain_reference_years[_values]` (interpolated) instead of the logistic curve of `operations_final_gain`, `operations_start_year`, `operations_duration`. |
| `models_efficiency_bottom_up` | `models.fleet`: aircraft inventory and fleet files. | The markets `initial` shares, used to calibrate the reference aircraft. | Markets `efficiency_simple`. |
| `models_efficiency_bottom_up_simple_freight` | Same as bottom-up, plus the freight market's `efficiency_simple` gain curve. | Same as bottom-up. | Passenger `efficiency_simple`. |
| `models_efficiency_push` | `models.fleet_push` files (the packaged ones if the block is absent). | Passenger markets named after the engine segments (`TP`, `RJ`, `NB`, `WB`), and a scenario whose last historical year is 2024. See [Push fleet](fleet_push.md). | Markets `efficiency_simple`, `models.fleet` files. |

Alternative energy aircraft enter the fleet differently in each case:

- **Top-down**: through `hydrogen_final_market_share`,
  `hydrogen_introduction_year`, `electric_final_market_share` and
  `electric_introduction_year` in the markets file.
- **Bottom-up**: through aircraft whose `energy_type` is `HYDROGEN`,
  `ELECTRIC` or `HYBRID_ELECTRIC` in the aircraft inventory.

As soon as an aircraft type consumes energy, the energy carriers file must
contain exactly one `default: True` pathway for it (see [Energy](energy.md)).

## Freight efficiency

| Freight model | Selected by | Reads |
|---|---|---|
| `FreightAircraftEfficiency` (default) | every efficiency bundle except the one below | No freight-specific parameter: freight energy per RTK follows the passenger drop-in efficiency, starting from the freight market's `energy_share_last_historical_year`. |
| `FreightAircraftEfficiencySimple` | `models_efficiency_bottom_up_simple_freight` | The freight market's `efficiency_simple`: `energy_per_rtk_dropin_fuel_gain_reference_years[_values]`. |

## Operating costs

| Bundle | Non-energy operating cost from | Not read |
|---|---|---|
| `models_operation_cost_top_down` | Markets `costs` of each passenger market. | Aircraft `doc_non_energy_base` / `doc_non_energy_evolution`. |
| `models_operation_cost_bottom_up` | Aircraft inventory: `doc_non_energy_base` or `doc_non_energy_evolution`. Needs the bottom-up fleet. | Markets `costs`, except `doc_non_energy_per_ask_dropin_fuel_init`, which `models_abatements_cost` still reads. |
| `*_feedback` variants | Same as above. | Same as above. The airfare is built from the marginal cost instead of the average cost; used in price-feedback and optimisation studies. |

Match the cost bundle to the efficiency bundle: top-down with top-down,
bottom-up with bottom-up.

## Abatement costs

The carbon abatement costs of fleet, operations and fuel levers are measured
against a reference fuel.

| What you select | Also needs |
|---|---|
| `models_abatements_cost` | The bottom-up fleet, markets `costs.doc_non_energy_per_ask_dropin_fuel_init`, and one energy pathway with `abatement_cost_reference: True` (usually fossil kerosene). |
| `models_abatements_cost_simplified` | One energy pathway with `abatement_cost_reference: True`. |
| `abatement_cost: True` on a pathway | `cost_model: bottom-up` on that pathway, one pathway with `abatement_cost_reference: True`, and the `exogenous_carbon_price_*` and `social_discount_rate` inputs (in the packaged `parameters.json`). |

The packaged energy carriers file has no reference pathway: add
`abatement_cost_reference: True` to `fossil_kerosene` before selecting an
abatement bundle, or the run fails with *Missing required names:
cac_reference_co2_emission_factor, cac_reference_mfsp*.

## Contrails and fuel properties

| Bundle | Reads | Not read |
|---|---|---|
| `models_energy_without_fuel_effect` | — | `emission_index.particles_number` of the pathways. |
| `models_energy_with_fuel_effect` | `emission_index.particles_number` of every drop-in pathway, relative to the **default** drop-in pathway; `contrails_relative_effect_hydrogen_wrt_kerosene` (`parameters.json`) for hydrogen. | — |

!!! warning
    With the fuel effect, the particle number of each drop-in pathway is divided
    by that of the default drop-in pathway. Give the default pathway a non-zero
    `particles_number`.

## Passenger demand

Set in the markets file under `global.demand.model`. Freight traffic always
follows its CAGR, whatever the choice.

| `demand.model` | Models built | Reads | Not read |
|---|---|---|---|
| `cagr` (default) | `RPKMarket` per market | Passenger `growth` (CAGR). | `global.elasticity`. |
| `cagr_elasticity` | `RPKMarket` + `RPKElasticity` | Passenger `growth`; `global.elasticity.price_elasticity` and `initial_airfare_per_rpk`. | — |
| `constant_elasticity` | `RPKPriceIncomeElasticity` + `SocioeconomicDrivers` | Income and price elasticities and socio-economic trajectories (population, GDP per capita), which the packaged `parameters.json` does **not** provide: supply them in `data.inputs.json_inputs_file`. | Passenger `growth`, `global.elasticity`. |
| `logistic_income` | `RPKLogisticIncomePriceElasticity` + `SocioeconomicDrivers` | Same as above, with a logistic income trend. | Passenger `growth`, `global.elasticity`. |

The three price-coupled modes read the airline cost chain, so they need an
operating-cost bundle in `models.standards`. The scenario
`resources/scenarios/icao_ltag_coupled_wctr` is a complete example of all four
modes. `elasticity.use_elasticity: true` is a legacy alias for
`cagr_elasticity`, used only when `demand.model` is absent.

## Load factor

Set in the markets file under `global.load_factor.model`.

| `load_factor.model` | Reads (per passenger market) | Not read |
|---|---|---|
| `quadratic` (default) | `load_factor_end_year`, `covid_load_factor_2020` | `load_factor_reference_years[_values]` |
| `simple_interpolation` | `load_factor_reference_years`, `load_factor_reference_years_values`, `covid_load_factor_2020` | `load_factor_end_year` |

## Fuel pathway models

Each pathway of the energy carriers file chooses an `environmental_model` and
a `cost_model`, independently. The two families read different keys: the
top-down ones read averages (`mean_*`), the bottom-up ones read the
characteristics of the plants commissioned each year (`eis_*`, for *entry into
service*).

| Pathway setting | Pathway keys read | Process keys read | Resource keys read |
|---|---|---|---|
| `environmental_model: top-down` | `mean_co2_emission_factor_without_resource`, `resource_specific_consumption`, `kerosene_selectivity` | `mean_co2_emission_factor_without_resource`, `resource_specific_consumption` | `co2_emission_factor` |
| `environmental_model: bottom-up` | `eis_co2_emission_factor_without_resource`, `eis_resource_specific_consumption`, `eis_plant_lifespan`, `kerosene_selectivity` | `eis_co2_emission_factor_without_resource`, `eis_resource_specific_consumption` | `co2_emission_factor` |
| `cost_model: top-down` | `mean_mfsp_without_resource`, `mean_unit_subsidy_without_resource`, `mean_unit_tax_without_resource`, `resource_specific_consumption` | `mean_mfsp_without_resource`, `mean_unit_subsidy_without_resource`, `mean_unit_tax_without_resource`, `resource_specific_consumption` | `cost`, `subsidy`, `tax` |
| `cost_model: bottom-up` | `eis_capex`, `eis_fixed_opex`, `eis_variable_opex`, `eis_construction_time`, `eis_plant_lifespan`, `eis_plant_load_factor`, `eis_resource_specific_consumption`, `mean_unit_subsidy_without_resource`, `mean_unit_tax_without_resource` | `eis_capex`, `eis_fixed_opex`, `eis_variable_opex`, `eis_construction_time`, `eis_plant_lifespan`, `eis_plant_load_factor`, `eis_resource_specific_consumption` | `cost` (resource `subsidy` and `tax` are not read) |
| either model `bottom-up` (plant capacity) | `eis_plant_load_factor`, `eis_plant_lifespan`, `technology_introduction_year`, `technology_introduction_volume` | `load_factor` | — |
| `abatement_cost: True` | Needs `cost_model: bottom-up` (error otherwise); `environmental_model: bottom-up` recommended (warning otherwise). Another pathway must carry `abatement_cost_reference: True`. | — | — |

A pathway may mix the two families, for instance a top-down environmental
model with a bottom-up cost model. It then needs the keys of both rows,
including both `resource_specific_consumption` and
`eis_resource_specific_consumption`.

!!! danger "Keys of the other family are accepted and ignored"
    The energy files are checked for misspelled keys and keys in the wrong
    block, but **not** against the model chosen for the pathway. A
    `mean_mfsp_without_resource` on a `cost_model: bottom-up` pathway passes the
    check and has no effect on the results. After switching a pathway from
    top-down to bottom-up, rename its keys.

Every pathway, whatever its models, reads `lhv`, `emission_index` and its
`mandate`. See [Energy](energy.md) for the full key reference.

## Operational gains and offsetting

Declaring the block of a generic module replaces the simple models and makes
their `parameters.json` inputs inactive.

| Without the block (simple models) | With the block (generic module) |
|---|---|
| **Operations**: `operations_final_gain`, `operations_start_year`, `operations_duration` (or `operations_gain_reference_years[_values]` with `models_efficiency_top_down_interp`), and `operations_contrails_final_gain`, `operations_contrails_final_overconsumption`, `operations_contrails_start_year`, `operations_contrails_duration`, all in `parameters.json`. | `models.operations`: one entry per operational concept in the operations file. The `parameters.json` inputs on the left are no longer read. |
| **Offsets**: `corsia_reference_year`, `carbon_offset_baseline_*`, `residual_carbon_offset_share_reference_years[_values]`, `manual_carbon_offset_reference_years[_values]` and the single price `carbon_offset_price_reference_years[_values]`, all in `parameters.json`. | `models.offsets`: one entry per offsetting scheme, each with its own quantity rule and price. The `parameters.json` inputs on the left are no longer read. |

See [Operations and offsets](operations_offsets.md).

## Climate model

The climate file names the model; the settings it accepts depend on it.

| `climate_model` | `model_settings` | Species settings that differ |
|---|---|---|
| `FaIR` (default) | `rcp`: `RCP26`, `RCP45` (default), `RCP60`, `RCP85` | `Soot` and `Sulfur` take no `sensitivity_rf`. |
| `GWP*` | `tcre` (default 0.00045) | `NOx - CH4 decrease and induced` takes `sensitivity_rf` instead of `ch4_loss_per_nox`. |
| `IPCC` | none | — |
| `LWE` | `tcre` (default 0.00045) | — |

A setting that the chosen model does not know is **ignored** (only an
INFO-level log line). See [Climate](climate.md).

## Coupling between regions

| `execution_mode` | Use when | Constraint |
|---|---|---|
| `separate_processes` (default) | Regions are independent: each is solved alone, then aggregated. | `global_models` cannot be used. |
| `unified_mda` | Regions are coupled (shared fuel market, global feedback…). | Slower: one multidisciplinary analysis over all regions. |

See [Multi-region studies](regionalisation.md).

## Consistency checklist

Before running a modified configuration, check that:

- `models.standards` holds one bundle per slot, and the efficiency and
  operating-cost bundles are both top-down or both bottom-up.
- `models.energy` is declared, and every aircraft type that consumes
  energy has exactly one `default: True` pathway.
- every non-default pathway has a `mandate` block, and the default
  pathways have none.
- each pathway only carries the keys of its own `environmental_model` and
  `cost_model`.
- with a bottom-up fleet, every passenger market of the markets file is
  served by a category of `fleet.yaml`.
- with `demand.model` set to a price-coupled mode, the socio-economic
  inputs are supplied and an operating-cost bundle is selected.
- with `models.operations` or `models.offsets`, you no longer edit the
  matching `parameters.json` entries expecting an effect.
- the climate settings match the chosen `climate_model`.

# Energy

The generic energy model describes the fuels aircraft burn. Each **energy
pathway** (fossil kerosene, HEFA, e-fuel, electrolytic hydrogen…) supplies one
aircraft type, consumes **resources** (biomass, electricity, CO₂…) directly
and through **processes** (electrolysis, liquefaction…), and gets a share of
the demand through a **mandate**. The model computes each pathway's energy
consumption, emission factor, cost and resource use.

| | |
|---|---|
| Packaged defaults | [`default_energy_carriers/`](https://github.com/AeroMAPS/AeroMAPS/tree/main/aeromaps/resources/data/default_energy_carriers): `energy_carriers_data.yaml`, `resources_data.yaml`, `processes_data.yaml` (all pathways top-down) |
| Entry config keys | `models.energy.energy_carriers_model_data_file`, `resources_model_data_file`, `processes_model_data_file` |
| Active | When the `models.energy` block is in your config. **Required in practice**: the energy and cost bundles need it. |
| Models driven | Per pathway: `TopDownEnvironmental` or `BottomUpEnvironmental`, `TopDownCost` or `BottomUpCost`, `BottomUpCapacity`, abatement-cost models. For all pathways: `EnergyUseChoice` (mandates), `EnergyCarriersMeans`, `EnergyCarriersMeanLHV`. Per resource: `EnergyResourceConsumption`. |
| Worked example | Tutorial 04 (`notebooks/tutorials/04_use_bottom_up_fuel_models`): bottom-up pathways |

Status labels are defined on the [section index](index.md#how-to-read-the-parameter-tables).

!!! danger "In the energy files, optional often means zero"
    Most pathway, process and resource values are **optional for the code**:
    when one is absent, the model uses a default instead of stopping. For
    shares, lifetimes or load factors the default is neutral. For emission
    factors, costs and specific consumptions **the default is zero**: a
    pathway without `mean_co2_emission_factor_without_resource` is carbon
    free, and one without `mean_mfsp_without_resource` is free of charge. The
    run completes and the results look plausible.

    The tables below mark these keys **Zero if absent**. Provide them unless
    zero is really what you mean, and check the pathway's outputs
    (`<pathway>_mean_co2_emission_factor`, `<pathway>_mean_mfsp`) after any
    change.

## How the three files fit together

```
energy_carriers_data.yaml                resources_data.yaml
hefa_fog:                                hefa_fog_biomass:
  aircraft_type: dropin_fuel               specifications:
  inputs:                                    co2_emission_factor …
    technical:                               cost …
      resource_names: [hefa_fog_biomass] ─►
      resource_specific_consumption:     processes_data.yaml
        hefa_fog_biomass: 1.14           electrolysis:
      processes_names: [electrolysis]  ─►  inputs:
                                             technical:
                                               resource_names: [grid_electricity] ─► (resources)
```

A pathway's emission factor (and, likewise, its cost) is the sum of:

1. its own value (`mean_co2_emission_factor_without_resource`, or `eis_…`
   in bottom-up);
2. for each resource it uses directly: specific consumption × the resource's
   `co2_emission_factor`;
3. for each process: the process's own value, plus its specific consumption
   of each resource × that resource's value.

Where you put an emission or a cost (pathway, process or resource) is your
choice, but put it in **one** place only, or it is counted twice.

The entry name (the YAML key) must be identical to its `name` field in the
three files: the models refer to entries by key and build parameter names from
`name`, so a mismatch silently disconnects them.

### How the demand is split between pathways

For each aircraft type (`dropin_fuel`, `hydrogen`, `electric`) that consumes
energy, each year:

1. pathways with a **quantity** mandate get their quantity;
2. pathways with a **share** mandate get their share of the aircraft type's
   **total** energy;
3. the single **default** pathway gets what is left.

If the mandates exceed the demand, they are scaled down uniformly and a
warning lists the years concerned. Exactly one `default: True` pathway is
required per aircraft type that consumes energy (an error names the type
otherwise). An aircraft type that consumes nothing needs no pathway.

## `energy_carriers_data.yaml`

One entry per pathway. Top-level keys:

| Key | Status | Default | Description |
|---|---|---|---|
| `name` | Required | — | Same value as the entry key. |
| `environmental_model` | Required | — | `top-down` or `bottom-up`. Decides which keys are read, see [Model choices](model_choices.md#fuel-pathway-models). |
| `cost_model` | Required | — | `top-down` or `bottom-up`. |
| `aircraft_type` | Required | — | `dropin_fuel`, `hydrogen` or `electric`. |
| `energy_origin` | Required | — | Free label (`fossil`, `biomass`, `electricity`…) used to group results. Keep `fossil`, `biomass` and `electricity` for drop-in fuels: several outputs (for example `biomass_share_dropin_fuel`) use them. |
| `default` | Optional | `False` | `True` for the pathway that completes the demand of its aircraft type. |
| `abatement_cost` | Optional | `False` | `True` computes the pathway's carbon abatement cost. Needs `cost_model: bottom-up`; `environmental_model: bottom-up` recommended. |
| `abatement_cost_reference` | Optional | `False` | `True` on the reference pathway of abatement costs (usually fossil kerosene). Needed by `abatement_cost` pathways and by the `models_abatements_cost` bundle. |
| `compute_all_years` | Optional, bottom-up only | `False` | Computes the vintage values every year, even when no plant is commissioned. Avoids gaps in abatement-cost curves. |
| `inputs` | Required | — | The blocks below. |
| `outputs` | Optional | — | Not used. |

### `inputs.mandate`

| Key | Status | Unit | Description |
|---|---|---|---|
| `mandate_type` | Required for every non-default pathway; **absent** on the default pathway | — | `share` or `quantity`. |
| `mandate_share` | Required with `share` | % | Share of the aircraft type's total energy. |
| `mandate_quantity` | Required with `quantity` | MJ | Energy supplied per year. |

A mandate is a quantity curve: before its first reference year it is zero
(see [Time series](loading.md#time-series-aeromapscustomdatatype)).

!!! warning "Mandates and the default pathway"
    - A non-default pathway **without** a `mandate` block makes the run fail
      (`KeyError: '<pathway>_energy_consumption'`). To keep a pathway in the
      file without deploying it, give it a zero share.
    - Do **not** give the default pathway a mandate. It is not ignored: it is
      counted as a share mandate before the default takes the remainder, and
      the corresponding energy is lost (the pathways no longer add up to the
      demand; an *AeroMAPS internal error* warning is raised).

### `inputs.technical`

| Key | Model | Status | Default | Unit | Description |
|---|---|---|---|---|---|
| `lhv` | all | Required | — | MJ/kg | Lower heating value. Converts energy to mass (mass shares, non-CO₂ emissions). For electricity, any non-zero value (the packaged file uses 1). |
| `resource_names` | all | Optional | `[]` | — | Resources consumed directly by the pathway. |
| `resource_specific_consumption` | top-down | Zero if absent | — | resource unit / MJ | One entry per resource of `resource_names`. A resource listed without consumption is not consumed. |
| `eis_resource_specific_consumption` | bottom-up | Zero if absent | — | resource unit / MJ | Same, for the plants commissioned each year. |
| `processes_names` | all | Optional | `[]` | — | Processes used by the pathway, from the processes file. |
| `kerosene_selectivity` | all | Optional | 1.0 | — | Share of a plant's output that is jet fuel. Only scales the resources *mobilised* (outputs `*_mobilised_with_selectivity` and the availability check), not the pathway's cost or emissions. |
| `eis_plant_lifespan` | bottom-up | Optional | 25 | years | Plant lifetime. |
| `eis_plant_load_factor` | bottom-up | Optional | 1.0 | — | Plant load factor. Sizes the capacity to build and spreads fixed costs. |
| `technology_introduction_year` | bottom-up | Required if the pathway already produces in the historic start year | — | year | First plant, used to rebuild the historical capacity. |
| `technology_introduction_volume` | bottom-up | same | — | MJ | Production of that first plant. |
| `plant_lifespan`, `plant_load_factor` | top-down | Optional | — | — | Accepted for compatibility; not used by the top-down calculations. |

### `inputs.environmental`

| Key | Model | Status | Unit | Description |
|---|---|---|---|---|
| `mean_co2_emission_factor_without_resource` | top-down | **Zero if absent** | gCO₂/MJ | Emission factor of the pathway itself, excluding what its resources and processes bring. |
| `eis_co2_emission_factor_without_resource` | bottom-up | **Zero if absent** | gCO₂/MJ | Same, for the plants commissioned each year. |
| `emission_index.h2o` | all | Required | kg/kg fuel | Water vapour. |
| `emission_index.nox` | all | Required | kg/kg fuel | NOx. |
| `emission_index.soot` | all | Required | kg/kg fuel | Soot. |
| `emission_index.sulfur` | all | Required | kg/kg fuel | Sulfur. |
| `emission_index.particles_number` | drop-in | Only with `models_energy_with_fuel_effect` | #/kg fuel | Particle number. Read relative to the default drop-in pathway, which must have a non-zero value. |

### `inputs.economics`

| Key | Model | Status | Unit | Description |
|---|---|---|---|---|
| `mean_mfsp_without_resource` | top-down | **Zero if absent** | €/MJ | Minimum fuel selling price of the pathway itself, excluding resources and processes. |
| `eis_capex` | bottom-up | **Zero if absent** | €/(MJ/yr) | Investment per unit of annual production capacity. |
| `eis_fixed_opex` | bottom-up | **Zero if absent** | €/(MJ/yr)/yr | Fixed operating cost per unit of capacity and per year. |
| `eis_variable_opex` | bottom-up | **Zero if absent** | €/MJ | Variable operating cost. |
| `eis_construction_time` | bottom-up | Optional (3) | years | Construction time, over which the investment is spread. |
| `mean_unit_subsidy_without_resource` | both | Optional (0) | €/MJ | Subsidy per MJ. |
| `mean_unit_tax_without_resource` | both | Optional (0) | €/MJ | Tax per MJ. |

The carbon tax is not set here: it applies to every pathway through the
`carbon_tax` inputs and the pathway's emission factor.

## `resources_data.yaml`

One entry per resource:

| Key | Status | Default | Description |
|---|---|---|---|
| `name` | Required | — | Same value as the entry key. |
| `origin` | Optional | `unknown` | Free label grouping the resources in the consumption outputs. |
| `specifications` | Required | — | Table below. |

The unit of a resource is the one its specific consumptions use: MJ for an
energy resource, kg for CO₂ (`co2_dac` in the packaged file), and so on.
Every per-unit value below is per unit of resource.

| Key | Read by | Status | Unit | Description |
|---|---|---|---|---|
| `co2_emission_factor` | both environmental models | **Zero if absent** | gCO₂/unit | Emissions of the resource itself. |
| `cost` | both cost models | **Zero if absent** | €/unit | Price of the resource. |
| `subsidy` | top-down cost | Optional (0) | €/unit | Not read by bottom-up cost models. |
| `tax` | top-down cost | Optional (0) | €/unit | Not read by bottom-up cost models. |
| `availability.global` | resource accounting | Optional | unit/yr | World availability. Enables the `<resource>_consumed_global_share` outputs. |
| `availability.aviation_allocated_share` | resource accounting | Optional, needs `global` | % | Share of the world availability allocated to aviation. Given without `global`, the run fails. |
| `load_factor` | — | Do not use | — | Accepted by the file check, but currently has no effect, and a plain number makes bottom-up runs fail. |

Availability is only compared with consumption: it does not cap the
production of a pathway.

## `processes_data.yaml`

One entry per process, with `name` (Required, same as the key) and three
input blocks. Specific consumptions are per MJ of fuel produced by the pathway
that uses the process.

| Block | Key | Model | Status | Unit |
|---|---|---|---|---|
| `technical` | `resource_names` | all | Optional | — |
| `technical` | `resource_specific_consumption` | top-down | **Zero if absent** | resource unit / MJ |
| `technical` | `eis_resource_specific_consumption` | bottom-up | **Zero if absent** | resource unit / MJ |
| `technical` | `eis_plant_lifespan` | bottom-up cost | Optional (25) | years |
| `technical` | `eis_plant_load_factor` | bottom-up cost | Optional (1.0) | — |
| `technical` | `load_factor` | bottom-up capacity | Optional (1.0) | — |
| `environmental` | `mean_co2_emission_factor_without_resource` | top-down | **Zero if absent** | gCO₂/MJ |
| `environmental` | `eis_co2_emission_factor_without_resource` | bottom-up | **Zero if absent** | gCO₂/MJ |
| `economics` | `mean_mfsp_without_resource` | top-down | **Zero if absent** | €/MJ |
| `economics` | `mean_unit_subsidy_without_resource`, `mean_unit_tax_without_resource` | top-down | Optional (0) | €/MJ |
| `economics` | `eis_capex` | bottom-up | **Zero if absent** | €/(MJ/yr) |
| `economics` | `eis_fixed_opex` | bottom-up | **Zero if absent** | €/(MJ/yr)/yr |
| `economics` | `eis_variable_opex` | bottom-up | **Zero if absent** | €/MJ |
| `economics` | `eis_construction_time` | bottom-up | Optional (3) | years |

A process inherits the model of the pathway that uses it: a top-down pathway
reads the `mean_*` keys of its processes, a bottom-up one the `eis_*` keys.

## What is checked when the files are loaded

| Checked (the run stops with a message) | Not checked |
|---|---|
| A misspelled key, or a key no energy model reads. | A key that is simply absent (see *Zero if absent*). |
| A key in the wrong block (for example `lhv` under `economics`). | A key of the other model family (a `mean_*` key on a bottom-up pathway is accepted and ignored). |
| A specific consumption for a resource the entry does not list in `resource_names`. | Units and orders of magnitude. |
| A `mandate_type` other than `share` or `quantity`. | Whether an emission or a cost is counted in two places. |
| Missing `lhv` or `emission_index` species, or a missing default pathway (at run time). | — |

## Examples

### A top-down pathway

A new drop-in pathway with a blending mandate, using an existing resource:

```yaml
ft_forestry:
  name: "ft_forestry"
  environmental_model: "top-down"
  cost_model: "top-down"
  aircraft_type: "dropin_fuel"
  energy_origin: "biomass"
  default: False
  inputs:
    mandate:
      mandate_type: "share"
      mandate_share: !AeroMapsCustomDataType
        years: [2020, 2030, 2050]
        values: [0.0, 1.0, 10.0]
        method: linear
    technical:
      resource_names: ["ft_others_biomass"]
      resource_specific_consumption:
        ft_others_biomass: 2.17          # MJ of biomass per MJ of fuel
      lhv: 44
    environmental:
      mean_co2_emission_factor_without_resource: !AeroMapsCustomDataType
        years: []
        values: [12.0]                   # gCO2/MJ
      emission_index:
        h2o: 1.231
        nox: 0.01514
        sulfur: 0.0
        soot: 6.0e-06
        particles_number: 8.0e+13
    economics:
      mean_mfsp_without_resource: !AeroMapsCustomDataType
        years: [2020, 2050]
        values: [0.035, 0.025]           # EUR/MJ
```

The resource `ft_others_biomass` has no `co2_emission_factor` nor `cost` in
the packaged resources file: all emissions and costs of this pathway are
carried by the pathway itself, which is a valid choice.

### The same pathway, bottom-up

Only the model keys change; metadata, mandate, `lhv` and emission indices stay:

```yaml
ft_forestry:
  name: "ft_forestry"
  environmental_model: "bottom-up"
  cost_model: "bottom-up"
  aircraft_type: "dropin_fuel"
  energy_origin: "biomass"
  default: False
  inputs:
    mandate:
      mandate_type: "share"
      mandate_share: !AeroMapsCustomDataType
        years: [2020, 2030, 2050]
        values: [0.0, 1.0, 10.0]
        method: linear
    technical:
      resource_names: ["ft_others_biomass"]
      eis_resource_specific_consumption:
        ft_others_biomass: 2.17
      lhv: 44
      eis_plant_lifespan: 25
      eis_plant_load_factor: 0.9
    environmental:
      eis_co2_emission_factor_without_resource: !AeroMapsCustomDataType
        years: []
        values: [12.0]
      emission_index:
        h2o: 1.231
        nox: 0.01514
        sulfur: 0.0
        soot: 6.0e-06
        particles_number: 8.0e+13
    economics:
      eis_capex: !AeroMapsCustomDataType
        years: [2020, 2050]              # start at the prospection start year
        values: [0.10, 0.06]             # EUR per MJ/yr of capacity
      eis_fixed_opex: !AeroMapsCustomDataType
        years: []
        values: [0.004]                  # EUR per MJ/yr of capacity, per year
      eis_variable_opex: !AeroMapsCustomDataType
        years: []
        values: [0.006]                  # EUR/MJ
      eis_construction_time: 3
```

### A quantity mandate

Replace the `mandate` block to impose volumes instead of a share:

```yaml
    mandate:
      mandate_type: "quantity"
      mandate_quantity: !AeroMapsCustomDataType
        years: [2025, 2035, 2050]
        values: [0.0, 5.0e+10, 2.0e+11]  # MJ per year
        method: linear
```

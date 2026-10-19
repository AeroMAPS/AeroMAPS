# Entry config and loading rules

This page covers **how configuration files are loaded, merged and resolved**,
every key of the entry config, and the time-series format shared by all data
files. Status labels (**Required**, **Optional**, **Zero if absent**,
**Only with …**) are defined on the [section index](index.md#how-to-read-the-parameter-tables).

## Loading rules

These behaviours are not visible in a config file, yet they decide where every
value ultimately comes from. They are implemented in
[`AeroMAPSProcess`](../../api/aeromaps.core.process.md).

### Your file is merged onto the packaged default

AeroMAPS first loads the packaged
[`resources/data/config.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/config.yaml),
then **recursively merges your file on top of it**. Nested mappings are merged
key by key, so you only write the keys you want to change.

!!! warning "Lists replace, they do not extend"
    A scalar or a list in your file fully replaces the default. In particular,
    a `models.standards:` list **replaces** the default list: name every bundle
    you want, not only the extra ones.

### A model block is active only if it is in your file

The merge fills in paths, but whether a model is switched on is decided by
**your** file alone: the energy, climate, fleet, operations, offsets and LCA
models are only built if their block appears in your entry config. Remove a
block to switch the model off. Two exceptions:

- `models.markets` is always loaded; the packaged markets file is used when
  the block is absent.
- `models.fleet_push` files are read whenever the `models_efficiency_push`
  bundle is selected; the block is only needed to point to other files.

### Relative paths are resolved against the config file

Every path in your entry config is resolved **relative to the directory that
contains it**, not to the working directory. Absolute paths are used as they
are. A project laid out as

```
my_study/
├── config.yaml
└── data/
    ├── parameters.json
    └── energy_carriers.yaml
```

uses `json_inputs_file: "./data/parameters.json"` wherever you launch Python
from.

### The `default` keyword

The literal value `default` for a data-file key resolves that file from the
**installed package** (relative to `resources/data/`) instead of relative to
your config:

```yaml
models:
  climate:
    climate_model_data_file: default   # packaged default_climate_models/climate_model_fair.yaml
```

Use it when AeroMAPS is `pip`-installed and you do not want to copy the
packaged files into your project.

!!! note "Missing files warn, they do not crash"
    If a resolved path does not exist, AeroMAPS logs a warning naming the
    config key instead of raising at once. Check the log if a model behaves as
    if its file were empty.

### Values from data files override `parameters.json`

The data files are flattened into scalar and time-series parameters named
`<entry>_<key>` (for example `hefa_fog_mandate_share`,
`short_range_load_factor_end_year`). They are applied **after** the JSON inputs,
so a data-file value silently wins over a same-named entry of
`parameters.json`.

## Entry config reference

### `data.inputs`

| Key | Status | Description |
|---|---|---|
| `json_inputs_file` | Optional | Scenario parameters (scalars and year-indexed vectors), applied on top of the packaged `parameters.json`. May be a **list** of files, merged in order; a key defined in several files keeps the last value and logs a warning. |
| `partitioning_data_file` | Optional | Year-indexed inputs used to partition a global scenario into a sub-scope (region, market segment…). Holds `other_float_data`, `other_vector_data` and an optional `climate_data` block. See tutorial 03. |
| `partitioning_climate_data_file` | Optional | CSV of historical temperature data. Default: the packaged `temperature_historical_dataset.csv`. |
| `csv_data_information_file` | Optional | Units and descriptions of the inputs, used for display and export. |

### `data.outputs`

| Key | Status | Description |
|---|---|---|
| `json_outputs_file` | Optional | Written by `process.write_json()`. Missing directories are created. |
| `excel_outputs_file` | Optional | Written by `process.write_excel()`. |

### `models.standards`

A list of **model bundles**, each the name of a `models_*` dictionary in
[`aeromaps/core/models.py`](../../api/aeromaps.core.models.md). An unknown name
raises a `ValueError` listing the available bundles. Pick **one bundle per
slot**:

| Slot | Bundles | Notes |
|---|---|---|
| Traffic | `models_traffic` | Always. The per-market RPK, RTK, ASK and load-factor models are added automatically from the [markets file](markets.md). |
| Aircraft efficiency | `models_efficiency_top_down`, `models_efficiency_top_down_interp`, `models_efficiency_bottom_up`, `models_efficiency_bottom_up_simple_freight`, `models_efficiency_push` | Decides which fleet description is read. See [Model choices](model_choices.md#aircraft-efficiency). |
| Energy | `models_energy_without_fuel_effect`, `models_energy_with_fuel_effect` | Need the `models.energy` block. The fuel-effect variant scales contrails with each fuel's particle emissions. |
| Emissions | `models_emissions` | CO₂ and non-CO₂ emissions. |
| Offsets | `models_offset` | Simple offset models; replaced by the generic module when `models.offsets` is declared. |
| Energy cost | `models_energy_cost` | Carbon tax, discounted and non-discounted scenario costs. |
| Operating cost | `models_operation_cost_top_down`, `models_operation_cost_bottom_up`, `models_operation_cost_top_down_feedback`, `models_operation_cost_bottom_up_feedback` | Must match the efficiency choice. See [Model choices](model_choices.md#operating-costs). |
| Optional extras | `models_sustainability`, `models_production_cost`, `models_abatements_cost`, `models_abatements_cost_simplified`, `models_fleet_count_simple` | `models_production_cost` and `models_abatements_cost` need the bottom-up fleet; `models_abatements_cost_simplified` is the top-down counterpart of the latter. Both abatement bundles need an energy pathway flagged `abatement_cost_reference: True`. See [Model choices](model_choices.md#abatement-costs). |

`default_models_top_down` and `default_models_bottom_up` bundle a coherent
full set; do not list them together with the bundles they already contain.

!!! warning "`models.energy` is required in practice"
    Every energy and cost bundle reads the outputs of the generic energy
    model. Without a `models.energy` block the run fails with a long
    *Missing required names* list (`dropin_fuel_mean_mfsp`,
    `biomass_share_dropin_fuel`…). Declare the block, with `default` values if
    you do not customise the fuels.

### `models.customs`

Loads your own model classes from Python files:

```yaml
models:
  customs:
    my_custom_model: "./models/my_model.py::MyModelClass"
    another_model: "./models/another.py"   # class name inferred as AnotherModel
```

- The path is resolved relative to the config file.
- `::ClassName` is optional; without it the class name is the CamelCase of the
  key (`another_model` → `AnotherModel`).
- Custom models are added on top of the standard bundles, so a custom model
  can replace a standard one by reusing its name.

### Model data-file blocks

Each block points to the data file(s) of one model family. Every path accepts
`default`.

| Block | Keys | Page |
|---|---|---|
| `markets` | `markets_data_file` | [Markets and demand](markets.md) |
| `fleet` | `aircraft_inventory_model_data_file`, `fleet_model_data_file` | [Bottom-up fleet](fleet.md) |
| `fleet_push` | `classification_data_file`, `market_param_data_file`, `in_production_inventory_file`, `new_aircraft_inventory_file`, `aircraft_parameters_file`, `fleet_snapshot_file` | [Push fleet](fleet_push.md) |
| `energy` | `energy_carriers_model_data_file`, `resources_model_data_file`, `processes_model_data_file` | [Energy](energy.md) |
| `climate` | `climate_model_data_file` | [Climate](climate.md) |
| `operations` | `operations_model_data_file` | [Operations and offsets](operations_offsets.md) |
| `offsets` | `offsets_model_data_file` | [Operations and offsets](operations_offsets.md) |
| `life_cycle_assessment` | `lca_model_data_file`, `split_by`, `methods` | [below](#life-cycle-assessment) |

!!! note "Declare the three energy files together"
    Inside the `energy` block, an omitted `energy_carriers_model_data_file`
    falls back to the packaged pathways, but an omitted resources or processes
    file is simply not read. Pathways that use a resource or a process then
    fail. List the three keys.

### Life Cycle Assessment

| Key | Status | Description |
|---|---|---|
| `lca_model_data_file` | Required | `.json`: the built-in default LCA model. `.yaml`/`.yml`: a custom LCA model (needs `pip install aeromaps[lca]`). `#tmp`: reuse the model compiled earlier in the same session (faster). |
| `split_by` | Optional | Grouping of the LCA results, for example `phase`. |
| `methods` | Optional | List of LCIA methods (default model only). |

See tutorial 07 for a custom LCA model.

## Time series: `!AeroMapsCustomDataType`

Year-dependent values in the data files are written with a custom tag:

```yaml
mandate_share: !AeroMapsCustomDataType
  years:  [2020, 2030, 2040, 2050]
  values: [0.0,  1.0,  2.0,  3.0]
  method: linear              # optional
  positive_constraint: false  # optional
```

| Field | Status | Description |
|---|---|---|
| `years` | Required | Reference years, increasing. May be empty: the first value then applies to every year. |
| `values` | Required | One value per year (or a single value when `years` is empty). |
| `method` | Optional | Interpolation between reference years, any `scipy.interpolate.interp1d` kind: `linear` (default), `nearest`, `previous`, `next`, `quadratic`, `cubic`. |
| `positive_constraint` | Optional | `true` clips interpolated values below zero to zero. Default `false`. |

How the curve is extended outside its reference years:

- **After the last year**: the last value is held constant up to the end year.
- **Before the first year**: it depends on what the curve describes.
    - A **property** of a fuel, resource or process (cost, MFSP, subsidy, tax,
      emission factor, heating value, selectivity) is held flat at its first
      value.
    - Anything else, a mandate for instance, **starts at its first year**
      (with a warning) and is absent, so zero, before it.
- A curve whose first year is earlier than the prospection start year is
  simply extended backwards.

!!! warning "Start bottom-up `eis_*` curves at the prospection start year"
    The bottom-up energy inputs (`eis_capex`, `eis_variable_opex`,
    `eis_co2_emission_factor_without_resource`…) are not treated as properties.
    If such a curve starts after the prospection start year, plants built in
    the earlier years get the model default, which is **zero** for costs and
    emission factors. Give these curves a first year at or before the
    prospection start year, or use `years: []` for a constant.

A plain number (`lhv: 44`) is a constant for all years.

### Lists in the markets file

The markets file uses two list conventions, recognisable by their suffix:

- `*_reference_periods` with `*_reference_periods_values`: **piecewise
  constant**. `N` period boundaries carry `N − 1` values, for example
  `cagr_reference_periods: [2020, 2030, 2050]` with
  `cagr_reference_periods_values: [3.0, 2.5]` (3 % per year until 2030, then
  2.5 %). Start the first period at the prospection start year. An empty
  period list with one value is a constant.
- `*_reference_years` with `*_reference_years_values`: **interpolated
  points**, one value per year. An empty year list with one value is a
  constant.

## Recommended project layout

```
my_study/
├── config.yaml              # entry config: overrides only
├── parameters.json          # scenario inputs (optional)
└── data/
    ├── markets.yaml         # only if you change the markets
    ├── fleet.yaml           # only with a bottom-up fleet
    └── energy_carriers.yaml # only if you change the fuels
```

Keep the entry config minimal: rely on the merge and on `default`, so that
your files only track the values you actually changed.

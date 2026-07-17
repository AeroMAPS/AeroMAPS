# Configuration files

AeroMAPS is driven by a small set of human-readable configuration files. This
page is the reference for **how those files are loaded, merged and resolved**,
and **what every key means**.

A fully-commented, copy-paste template is shipped with the package at
[`aeromaps/resources/data/example_config.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/example_config.yaml).
Start from it rather than from scratch.

---

## 1. The big picture

There are **two tiers** of configuration:

1. **The entry config** — a single YAML file (conventionally `config.yaml`) that
   you pass to the process:

    ```python
    from aeromaps import create_process

    process = create_process(configuration_file="data/config.yaml")
    process.compute()
    ```

    It declares *which* input/output files to use, *which* models to run, and
    *where* each model's own data file lives.

2. **Sub-config data files** referenced from the entry config — the parameter
   set, the fleet definition, the energy-carrier / resource / process
   pathways, the climate model, the LCA model, and (for multi-region studies)
   the per-region configs. Each is documented in
   [section 4](#4-sub-config-files-reference).

```
config.yaml  (entry config)
├── data.inputs.json_inputs_file        → parameters.json
├── data.inputs.partitioning_data_file  → partitioning_inputs.json
├── data.outputs.json_outputs_file      → outputs.json
└── models
    ├── climate.climate_model_data_file → default_climate_models/climate_model_fair.yaml
    ├── fleet.fleet_model_data_file      → default_fleet/fleet.yaml
    ├── energy.*_model_data_file         → default_energy_carriers/*.yaml
    ├── life_cycle_assessment.*          → default_lca/default_lca_model.json
    └── standards / customs              → model bundles to load
```

---

## 2. Loading semantics (read this first)

These three behaviours are not obvious from a config file alone, yet they
determine where every value ultimately comes from: your file is merged onto a
packaged default, relative paths resolve against the config file (not the
working directory), and the literal `default` keyword switches resolution to
the installed package. They are implemented in
[`AeroMAPSProcess`](../api/aeromaps.core.process.md).

### 2.1 Deep merge onto the packaged default

Your config is **not** read in isolation. AeroMAPS first loads the packaged
default [`resources/data/config.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/config.yaml),
then **recursively merges your file on top of it**. You therefore only need to
specify the keys you want to *override* — anything you omit keeps its default
value.

The merge is dict-aware: nested mappings are merged key-by-key, but a scalar or
list in your file fully replaces the default (lists are **not** concatenated).

!!! warning "`models.standards` is replaced, not extended"
    Because `standards` is a list, providing your own `standards:` block
    **replaces** the default list entirely. List every bundle you want, not just
    the extra ones.

### 2.2 Relative paths are resolved against the config file

Every path in your entry config is resolved **relative to the directory
containing that config file**, *not* the current working directory. So a project
laid out as:

```
my_study/
├── config.yaml
└── data/
    ├── parameters.json
    └── fleet.yaml
```

uses `json_inputs_file: "./data/parameters.json"` regardless of where you launch
Python from. Absolute paths are also accepted and used as-is.

### 2.3 The `default` keyword

Setting any model data-file value to the literal string `default` makes AeroMAPS
resolve it from the **installed package** (relative to `resources/data/`) instead
of relative to your config:

```yaml
models:
  climate:
    climate_model_data_file: default   # → packaged default_climate_models/climate_model_fair.yaml
```

Use this when AeroMAPS is `pip`-installed and you don't want to copy the default
data files into your project. It is the mechanism the GUI config relies on.

!!! note "Missing files warn, they don't crash"
    If a resolved path does not exist, AeroMAPS logs a warning naming the
    offending config key rather than raising immediately. Check your logs if a
    model behaves as if a file were empty.

---

## 3. The entry config — key reference

Below is every section of the entry config. See
[`example_config.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/example_config.yaml)
for the same content as a ready-to-edit template.

### 3.1 `data.inputs`

| Key | Required | Description |
|---|---|---|
| `json_inputs_file` | yes | Scenario parameters (scalars and year-indexed vectors). See [parameters](#parametersjson). |
| `partitioning_data_file` | no | Year-indexed inputs used to partition a global scenario into a sub-scope (region, market segment…). Holds `other_float_data`, `other_vector_data`, and an optional `climate_data` block. |
| `partitioning_climate_data_file` | no | CSV of historical temperature data; falls back to the packaged `temperature_historical_dataset.csv`. |
| `csv_data_information_file` | no | Metadata (units, descriptions) describing the inputs, used for display/export. |

### 3.2 `data.outputs`

| Key | Required | Description |
|---|---|---|
| `json_outputs_file` | no | Destination for `process.write_json()`. Directories are created if missing. |
| `excel_outputs_file` | no | Destination for `process.write_excel()`. |

### 3.3 `models.standards`

A **list of model bundles** to load. Each entry must match a `models_*`
dictionary defined in [`aeromaps/core/models.py`](../api/aeromaps.core.models.md).
An unknown name raises a `ValueError` that lists the available bundles.

Commonly used bundles:

| Bundle | Purpose |
|---|---|
| `models_traffic` | Air-traffic demand (RPK/RTK/ASK). |
| `models_traffic_constant_elasticities` / `models_traffic_cost_feedback` | Variants with price-elastic demand. |
| `models_efficiency_top_down` / `models_efficiency_bottom_up` | Aircraft efficiency, top-down (aggregated fleet-wise figures) vs bottom-up (explicit per-aircraft fleet with market shares). |
| `models_energy_without_fuel_effect` / `models_energy_with_fuel_effect` | Energy consumption models. |
| `models_emissions` | CO₂ and non-CO₂ emissions. |
| `models_offset` | Carbon offsetting. |
| `models_sustainability` | Sustainability / carbon-budget assessment. |
| `models_operation_cost_top_down` / `models_operation_cost_bottom_up` | Operation cost, top-down (aggregated cost interpolated from data) vs bottom-up (plant-specific cost estimated based on CAPEX and OPEX). |
| `models_energy_cost`, `models_production_cost`, `models_abatements_cost` | Other cost models. |

Convenience aggregates `default_models_top_down` and `default_models_bottom_up`
bundle a coherent full set. Choosing the *top-down* vs *bottom-up* efficiency and
operation-cost bundles must be consistent with the fleet block (see
[fleet](#fleet)).

### 3.4 `models.customs` (optional)

Load your own model classes from external Python files:

```yaml
models:
  customs:
    my_custom_model: "./models/my_model.py::MyModelClass"
    another_model: "./models/another.py"   # class name inferred as AnotherModel
```

- Path is resolved relative to the config file.
- `::ClassName` is optional; if omitted, the class name is the CamelCase of the
  model key (`another_model` → `AnotherModel`).
- Custom models are merged on top of the standard bundles, so a custom model can
  override a standard one by reusing its name.

### 3.5 `models.<climate|fleet|energy|life_cycle_assessment>`

Each block points to that model's own data file. **A model is only initialised if
its block is present in *your* config** (the merge fills paths, but presence is
checked against the user file) — this is how you switch a model on or off.

```yaml
models:
  climate:
    climate_model_data_file: "./default_climate_models/climate_model_fair.yaml"

  fleet:
    aircraft_inventory_model_data_file: "./default_fleet/aircraft_inventory.yaml"
    fleet_model_data_file: "./default_fleet/fleet.yaml"

  energy:
    energy_carriers_model_data_file: "./default_energy_carriers/energy_carriers_data.yaml"
    resources_model_data_file: "./default_energy_carriers/resources_data.yaml"
    processes_model_data_file: "./default_energy_carriers/processes_data.yaml"

  life_cycle_assessment:
    lca_model_data_file: "./default_lca/default_lca_model.json"
    split_by: phase
```

LCA-specific keys:

| Key | Description |
|---|---|
| `lca_model_data_file` | `.json` → built-in default LCA model; `.yaml`/`.yml` → custom LCA model (requires `pip install aeromaps[lca]`); `#tmp` → reuse the model compiled earlier in the same session (faster). |
| `split_by` | Optional grouping of LCA results, e.g. `phase`. |
| `methods` | Optional list of LCIA methods (default model only). |

---

## 4. Sub-config files reference

### parameters.json

The scenario's input values. Two shapes coexist:

- **scalars** — a single number (e.g. a growth rate).
- **year-indexed vectors** — given as a `!AeroMapsCustomDataType` block (see
  [section 5](#5-the-aeromapscustomdatatype-tag)) or as an explicit list.

### fleet

`fleet_model_data_file` and `aircraft_inventory_model_data_file` describe the
bottom-up fleet. The fleet file is a list of `subcategories`, each with a market
`share` and a set of `aircraft`/`reference_aircraft`:

```yaml
subcategories:
  - id: sr_conventional_nb
    name: "SR conventional narrow-body"
    share: 20.0                     # % of its category's traffic
    reference_aircraft:
      old_ref: sr_conventional_nb_old
      recent_ref: sr_conventional_nb_recent
    aircraft:
      - sr_nb_2035                  # entry-into-service scenarios, defined in aircraft_inventory
      - sr_nb_2045
```

Only meaningful when a *bottom-up* efficiency bundle is selected in
`models.standards`. Use [`fleet_no_new_aircraft.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/default_fleet/fleet_no_new_aircraft.yaml)
as a frozen-technology baseline.

### energy carriers / resources / processes

These three files define the generic energy model. Each ships with a **fully
annotated example block at the top of the file** showing every available field —
read those headers directly:

- [`energy_carriers_data.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/default_energy_carriers/energy_carriers_data.yaml)
  — fuel pathways: `environmental_model`/`cost_model` (`top-down` vs `bottom-up`),
  `aircraft_type`, `energy_origin`, a `mandate` (`share` or `volume`), technical
  data (LHV, resource consumption, processes), and emission factors.
- [`resources_data.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/default_energy_carriers/resources_data.yaml)
  — raw resources: emission factor, availability, cost, subsidies.
- [`processes_data.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/default_energy_carriers/processes_data.yaml)
  — conversion processes: resource consumption, emission factor, economics.

A carrier flagged `default: True` is used to satisfy any unspecified demand and
its `mandate` is ignored.

### climate

`climate_model_data_file` selects the climate model. Four are packaged in
[`default_climate_models/`](https://github.com/AeroMAPS/AeroMAPS/tree/main/aeromaps/resources/data/default_climate_models):
`climate_model_fair.yaml` (FaIR, the default), `climate_model_gwpstar.yaml`
(GWP\*), `climate_model_ipcc.yaml`, `climate_model_lwe.yaml`. Each declares a
`climate_model` name and per-species `species_settings` (sensitivities,
ERF/RF ratios, efficacies).

### regionalisation (multi-region studies)

For multi-region runs use `MultiRegionalProcess` with an entry config that
contains a top-level `regionalisation` block instead of (or alongside) the
single-scenario keys. See the worked example in
[tutorial 11](https://github.com/AeroMAPS/AeroMAPS/tree/main/aeromaps/notebooks/tutorials/11_multi_regional_two_regions).

```yaml
regionalisation:
  execution_mode: "unified_mda"      # or "separate_processes" (default)
  global_namespace: "overall"        # prefix for aggregated outputs

  regions:
    EU_DOM:
      config_file: "data/region_eu_dom/config.yaml"   # a normal entry config per region
    EU_INT:
      config_file: "data/region_eu_int/config.yaml"

  # Optional: models run on aggregated global data (same structure as a region's
  # models block: standards / customs).
  # top_level_models:
  #   standards: [ ... ]

  aggregation:
    sum:                              # outputs summed across regions
      - co2_emissions_including_energy
      - rpk
      - ask
    weighted_average:                 # outputs averaged, weighted by another output
      - variable: load_factor
        weight_by: ask
```

| Key | Description |
|---|---|
| `execution_mode` | `separate_processes` (default; scalable, runs each region independently then aggregates) or `unified_mda` (one MDAChain over all regions; needed when regions are coupled). |
| `global_namespace` | Prefix for aggregated outputs, e.g. `overall:co2_emissions`. |
| `regions.<ID>.config_file` | Path (relative to this file) to that region's standalone entry config. |
| `aggregation.sum` | Output names to add across regions. |
| `aggregation.weighted_average` | Each entry: a `variable` averaged across regions, `weight_by` another output. |
| `top_level_models` | Optional models run on the aggregated global data. |

Regional outputs are namespaced: `process.data["vector_outputs"]["EU_DOM:co2_emissions"]`
and `["overall:co2_emissions"]`.

---

## 5. The `!AeroMapsCustomDataType` tag

Throughout the data files, time series are written with a custom YAML tag:

```yaml
mandate_share: !AeroMapsCustomDataType
  years:  [2020, 2030, 2040, 2050]
  values: [0.0,  1.0,  2.0,  3.0]
  method: linear            # interpolation between the given years
```

AeroMAPS interpolates `values` over the simulation years using `method`. This is
how every year-indexed input (parameters, mandates, emission factors, costs…) is
expressed. A bare scalar (`lhv: 44`) is a constant for all years.

---

## 6. Recommended project layout

```
my_study/
├── config.yaml              # entry config (overrides only)
├── parameters.json          # scenario inputs
└── data/
    ├── fleet.yaml           # only if using a bottom-up fleet
    └── energy_carriers.yaml # only if customising pathways
```

Keep the entry config minimal: rely on the deep-merge and the `default` keyword
so you only track the values you actually change.

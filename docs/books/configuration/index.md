# Configuration files

An AeroMAPS run is described by a set of YAML files. This section explains
which files exist, which models each one drives, and, for every parameter,
whether you must provide it, may leave it out, or should know that leaving it
out silently means zero.

A fully commented template ships with the package:
[`example_config.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/example_config.yaml).
Start from it, and from the packaged default data files in
[`aeromaps/resources/data/`](https://github.com/AeroMAPS/AeroMAPS/tree/main/aeromaps/resources/data),
rather than from scratch.

## The files at a glance

Everything starts from one **entry config** (conventionally `config.yaml`),
passed to the process:

```python
from aeromaps import create_process

process = create_process(configuration_file="config.yaml")
process.compute()
```

The entry config selects the model bundles to run (`models.standards`) and
points to one data file per model family. Each family has its own page:

| Data file (packaged default) | Declared in the entry config under | Active when | Page |
|---|---|---|---|
| `default_markets/markets.yaml` | `models.markets` | always (the default file is used if the block is absent) | [Markets and demand](markets.md) |
| `default_fleet/aircraft_inventory.yaml`, `default_fleet/fleet.yaml` | `models.fleet` | the block is in your config | [Bottom-up fleet](fleet.md) |
| `default_fleet_push/*.yaml` (+ 2 calibration workbooks) | `models.fleet_push` | `models_efficiency_push` is in `models.standards` | [Push fleet](fleet_push.md) |
| `default_energy_carriers/energy_carriers_data.yaml`, `resources_data.yaml`, `processes_data.yaml` | `models.energy` | the block is in your config (required in practice) | [Energy](energy.md) |
| `default_climate_models/climate_model_*.yaml` | `models.climate` | the block is in your config | [Climate](climate.md) |
| `default_operations/operations_data.yaml` | `models.operations` | the block is in your config | [Operations and offsets](operations_offsets.md) |
| `default_offsets/offsets_data.yaml` | `models.offsets` | the block is in your config | [Operations and offsets](operations_offsets.md) |
| `default_lca/default_lca_model.json` | `models.life_cycle_assessment` | the block is in your config | [Entry config](loading.md#life-cycle-assessment) |
| one entry config per region | top-level `regionalisation` | you use a multi-region process | [Multi-region studies](regionalisation.md) |

Two other pages apply to all files:

- [Entry config and loading rules](loading.md): how files are merged and
  resolved, every key of the entry config, and the `!AeroMapsCustomDataType`
  time-series format.
- [Model choices and the parameters they need](model_choices.md): the
  associations between a model you select and the parameters it reads. **Read
  it before editing a data file**: many parameters are only read when a given
  model is selected.

!!! warning "A block in the packaged default config does not activate anything"
    Model blocks are activated by their presence in **your** entry config. The
    packaged `config.yaml` lists every block, but it only fills in paths: to
    switch on the energy, climate, fleet, operations, offsets or LCA models,
    declare their block in your own file (the value `default` is enough). The
    markets block is the only one that is always loaded.

## How to read the parameter tables

Every page lists the keys of its file with a **status**:

| Status | Meaning |
|---|---|
| **Required** | The run stops with an error if the key is missing. |
| **Optional** | Safe to leave out. The default stated in the table applies and is neutral. |
| **Zero if absent** | May be left out, but then counts as 0: no cost, no emission, no consumption. Provide it unless 0 is really what you mean. |
| **Only with …** | Read only when the named model or option is selected. Otherwise it is ignored, usually without any warning. |

!!! danger "Why “Zero if absent” matters"
    Most files fail loudly when a key is missing: the run stops with a
    *Missing required names* error that names it. The **energy files** are
    the exception. Their models read most pathway, process and resource
    inputs with a zero default, so a missing emission factor is a carbon-free
    fuel and a missing cost is a free one. The run completes and the results
    look plausible, but they are wrong. The energy files are checked for
    misspelled keys when they are loaded, but a key that is simply absent
    cannot be told apart from a deliberate zero.

## Where to start

- **Run the defaults and change a few numbers**: copy the default data file
  you want to change next to your entry config, point the matching block to it
  and edit values. Keep every other block on `default`.
- **Switch a model** (top-down to bottom-up fleet, another demand model, a
  bottom-up fuel pathway…): read [Model choices](model_choices.md) first, then
  the page of the file concerned.
- **Add an entry** (a market, a fuel pathway, an aircraft, an offsetting
  scheme…): each page ends with a minimal example of a new entry.

# Multi-region studies

A multi-region study runs one AeroMAPS scenario per region and aggregates
them. It is driven by an entry config that contains a top-level
`regionalisation` block. Each region is described by its own, ordinary entry
config, with its own markets, fleet, energy and parameter files.

| | |
|---|---|
| Entry config key | top-level `regionalisation` |
| Process | `create_process` returns a `MultiRegionalProcess` when the block is present. |
| Worked example | Tutorial 11 (`notebooks/tutorials/11_multi_regional_two_regions`) |

Status labels are defined on the [section index](index.md#how-to-read-the-parameter-tables).

```yaml
regionalisation:
  execution_mode: "separate_processes"   # or "unified_mda"
  global_namespace: "overall"

  regions:
    EU_DOM:
      config_file: "data/region_eu_dom/config.yaml"
    EU_INT:
      config_file: "data/region_eu_int/config.yaml"

  aggregation:
    sum:
      - co2_emissions_including_energy
      - rpk
      - ask
    weighted_average:
      - variable: load_factor
        weight_by: ask

  # top_level_models:      # optional: models run on the aggregated data
  #   standards: [ ... ]
  #   customs: { ... }

  # global_models:         # optional, unified_mda only: models coupling the regions
  #   customs:
  #     fuel_market: "models/fuel_market.py::FuelMarket"
```

| Key | Status | Default | Description |
|---|---|---|---|
| `regions` | Required | — | One entry per region, keyed by the region id. At least one region. |
| `regions.<id>.config_file` | Required | — | Path, relative to this file, of the region's entry config. |
| `execution_mode` | Optional | `separate_processes` | `separate_processes` solves each region independently, then aggregates; it scales well. `unified_mda` solves all regions in one multidisciplinary analysis; needed when regions are coupled. |
| `global_namespace` | Optional | `overall` | Prefix of the aggregated outputs. |
| `aggregation.sum` | Optional | `[]` | Outputs added across regions. |
| `aggregation.weighted_average` | Optional | `[]` | Outputs averaged across regions: each entry gives the `variable` and the output to `weight_by`. |
| `top_level_models` | Optional | — | Models run on the aggregated data, with the same `standards` / `customs` structure as a region's `models` block. |
| `global_models` | Optional, `unified_mda` only | — | Models that read and write regional variables, closing loops between regions (for example a shared fuel market). |

Outputs are namespaced by region and by the global namespace:
`process.data["vector_outputs"]["EU_DOM:co2_emissions"]` and
`["overall:co2_emissions"]`.

!!! note "Each region config is complete on its own"
    A region config follows every rule of the previous pages: it is merged
    onto the packaged default config, its paths are relative to its own
    directory, and its model blocks are activated by their presence in that
    region file.

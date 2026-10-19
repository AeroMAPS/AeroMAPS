# Climate

The climate file selects the simple climate model used to turn CO₂ and
non-CO₂ emissions into effective radiative forcing and temperature change, and
tunes its parameters. The models are provided by
[AeroCM](https://github.com/AeroMAPS/AeroCM).

| | |
|---|---|
| Packaged defaults | [`default_climate_models/`](https://github.com/AeroMAPS/AeroMAPS/tree/main/aeromaps/resources/data/default_climate_models): `climate_model_fair.yaml` (FaIR, the default), `climate_model_gwpstar.yaml`, `climate_model_ipcc.yaml`, `climate_model_lwe.yaml` |
| Entry config key | `models.climate.climate_model_data_file` |
| Active | When the `models.climate` block is in your config. |
| Model driven | `ClimateModel` |
| Worked example | Tutorial 06 (`notebooks/tutorials/06_use_climate_models`) |

Status labels are defined on the [section index](index.md#how-to-read-the-parameter-tables).
Every setting is **Optional**: AeroCM fills in its default for anything you
leave out, so a file may contain only the values you change.

## Structure

```yaml
climate_model: "FaIR"        # FaIR, GWP*, IPCC or LWE

species_settings:            # optional, per species, per setting
  Contrails:
    sensitivity_rf: 2.23e-12
    ratio_erf_rf: 0.42
    efficacy_erf: 1.0

model_settings:              # optional, depends on climate_model
  rcp: "RCP45"
```

| Key | Status | Default | Description |
|---|---|---|---|
| `climate_model` | Optional | `FaIR` | `FaIR`, `GWP*`, `IPCC` or `LWE`. |
| `species_settings` | Optional | AeroCM defaults | Per-species settings. A species you list only overrides the settings you give for it. |
| `model_settings` | Optional | AeroCM defaults | Settings of the model itself (table below). |

!!! warning "Unknown settings and species are ignored without error"
    A setting written for another model (a `tcre` with FaIR, a
    `ch4_loss_per_nox` with GWP\*) has no effect, and neither has a misspelled
    species name (`Contrail` instead of `Contrails`): the run completes with
    the defaults, with at most an INFO-level log line. Copy species and
    setting names from the tables below or from the packaged files.

## `species_settings`

Species names are written exactly as below. Settings:
`sensitivity_rf` (radiative forcing per unit of emission or distance),
`ratio_erf_rf` (effective to plain radiative forcing ratio) and
`efficacy_erf` (efficacy of the effective forcing).

| Species | Settings accepted by every model | Model-specific |
|---|---|---|
| `CO2` | `ratio_erf_rf` | — |
| `Contrails` | `sensitivity_rf`, `ratio_erf_rf`, `efficacy_erf` | — |
| `NOx - ST O3 increase` | `sensitivity_rf`, `ratio_erf_rf`, `efficacy_erf` | — |
| `NOx - CH4 decrease and induced` | `ratio_erf_rf`, `efficacy_erf` | `ch4_loss_per_nox` (FaIR, IPCC, LWE) or `sensitivity_rf` (GWP\*) |
| `H2O` | `sensitivity_rf`, `ratio_erf_rf`, `efficacy_erf` | — |
| `Soot` | `ratio_erf_rf`, `efficacy_erf` | `sensitivity_rf` (GWP\*, IPCC, LWE; not FaIR) |
| `Sulfur` | `ratio_erf_rf`, `efficacy_erf` | `sensitivity_rf` (GWP\*, IPCC, LWE; not FaIR) |

The packaged files list the default values of each model.

## `model_settings`

| `climate_model` | Settings | Default |
|---|---|---|
| `FaIR` | `rcp`: background scenario, `RCP26`, `RCP45`, `RCP60` or `RCP85` | `RCP45` |
| `GWP*` | `tcre`: transient climate response to cumulative emissions [K/GtCO₂] | `0.00045` |
| `LWE` | `tcre` | `0.00045` |
| `IPCC` | none | — |

## Related inputs elsewhere

- The contrail effect of fuel properties is enabled by the
  `models_energy_with_fuel_effect` bundle and the `particles_number` emission
  index of each pathway (see [Model choices](model_choices.md#contrails-and-fuel-properties)).
- Contrail avoidance through operations is declared in the
  [operations file](operations_offsets.md).

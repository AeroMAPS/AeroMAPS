# Push fleet

The push fleet model is a delivery-driven fleet-renewal engine. Starting from
the end-2024 world fleet, it delivers aircraft according to production
profiles, retires them with age, and computes the energy per ASK of each
segment. The passenger ASK computed by the demand models is injected as the
traffic the fleet must serve.

| | |
|---|---|
| Packaged defaults | [`default_fleet_push/`](https://github.com/AeroMAPS/AeroMAPS/tree/main/aeromaps/resources/data/default_fleet_push): four YAML files, plus two calibration workbooks produced by the fleet calibration notebook |
| Entry config keys | `models.fleet_push.*` (six keys, below) |
| Active | When `models_efficiency_push` is in `models.standards`. The `models.fleet_push` block is only needed to point to other files; without it the packaged files are used. |
| Model driven | `PassengerAircraftEfficiencyFleetPush` |
| Worked example | Tutorial 14 (`notebooks/tutorials/14_push_fleet_model`) |

Status labels are defined on the [section index](index.md#how-to-read-the-parameter-tables).
Every field listed on this page is **Required**: a missing one stops the run
when the files are loaded.

## Requirements on the rest of the configuration

!!! warning "The push engine constrains the whole scenario"
    - **The last historical year must be 2024** (`prospection_start_year:
      2025`): the engine is calibrated on the end-2024 fleet and stops at build
      time otherwise. The historical `*_init` vectors must then run to 2024;
      tutorial 13 provides such an input file (`inputs_2025.json`).
    - **The passenger markets are the engine segments**: `TP` (turboprops),
      `RJ` (regional jets), `NB` (narrow-bodies) and `WB` (wide-bodies). Use a
      markets file such as tutorial 14's `markets_push.yaml`; their growth
      drives the ASK injected into the engine.
    - **Drop-in fuel only**: the current version routes 100 % of the ASK to
      drop-in aircraft. Hydrogen and electric aircraft are not modelled.
    - The run stops if the delivered fleet cannot serve the injected traffic
      in some year: increase production or renewal rates.

## Entry config keys

| Key | File | Content |
|---|---|---|
| `classification_data_file` | `default_aircraft_classification.yaml` | Maps each ICAO aircraft type to a segment. |
| `market_param_data_file` | `default_market_param.yaml` | Age sensitivities per segment. |
| `in_production_inventory_file` | `default_in_production_aircraft_inventory.yaml` | Aircraft types in production at the pivot year. |
| `new_aircraft_inventory_file` | `default_new_aircraft_inventory.yaml` | Future aircraft types. |
| `aircraft_parameters_file` | `aircraft_type_key_parameters.xlsx` | Per-type parameters of the existing fleet (seats, energy per ASK, distance). Produced by the calibration notebook in `utils/calibration_notebooks/`. |
| `fleet_snapshot_file` | `agg_fleet_end_2024.xlsx` | Age-resolved fleet at the end of 2024. Produced by the same notebook. |

## `default_aircraft_classification.yaml`

```yaml
aircraft_types:
- A20N : 'NB'
- AT72 : 'TP'
- B77W : 'WB'
```

One entry per ICAO type found in the calibration workbooks, mapped to a
segment id (`TP`, `RJ`, `NB` or `WB`). A type missing from the list is left
out of every segment.

## `default_market_param.yaml`

```yaml
markets:
  NB:
    age_utilisation_sensib: -0.01
    age_retirement_sensib: 0.19
```

| Key | Unit | Description |
|---|---|---|
| `age_utilisation_sensib` | 1/yr | Decay of aircraft utilisation with age (exponential rate; negative means older aircraft fly less). |
| `age_retirement_sensib` | 1/yr | Slope of the retirement propensity with age. |

One block per segment.

## `default_in_production_aircraft_inventory.yaml`

Aircraft types still delivered after the pivot year, per segment:

```yaml
markets:
  NB:
    current_aircraft_types:
      - name: "current_gen_NB_SR"
        energy_efficiency: 1.0
        seats: 150
        ret_year_delay: 0
        reference_production_points:
        - year: 2025
          value: 150
        - year: 2033
          value: 200
        - year: 2040
          value: 0
```

| Key | Unit | Description |
|---|---|---|
| `name` | — | Type name, used in output names. |
| `energy_efficiency` | MJ/ASK | Energy per ASK of the type. |
| `seats` | seats | Seats per aircraft. |
| `ret_year_delay` | years | Shift of the retirement age, scaled by `age_retirement_sensib`. `0` for none. |
| `reference_production_points` | aircraft/yr | Delivery profile: `year` / `value` points, interpolated linearly. End it with `0` when production stops. |

## `default_new_aircraft_inventory.yaml`

Future aircraft types, per segment:

```yaml
markets:
  NB:
    new_aircraft_types:
      - name: "new_gen_NB_SR"
        intro_year: 2030
        production_duration: 20
        energy_efficiency: 0.65
        seats: 150
        renewal_rate: 0.4
        time_to_market: 8
        ret_year_delay: 0
```

| Key | Unit | Description |
|---|---|---|
| `name` | — | Type name, used in output names. |
| `intro_year` | year | First delivery year. |
| `production_duration` | years | Length of the production run. |
| `energy_efficiency` | MJ/ASK | Energy per ASK of the type. |
| `seats` | seats | Seats per aircraft. |
| `renewal_rate` | — | Share of the segment traffic at the end of the production run that the deliveries of this type are sized to carry. |
| `time_to_market` | years | Ramp-up time of the delivery curve. |
| `ret_year_delay` | years | Shift of the retirement age, scaled by `age_retirement_sensib`. |

Types of a segment are independent: their deliveries add up.

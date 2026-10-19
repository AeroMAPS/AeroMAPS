# Bottom-up fleet

The bottom-up fleet model describes each passenger market as a set of aircraft
families. In each family, the aircraft in service are progressively replaced
by new aircraft along S-curves, and the fleet's energy, emissions and costs
follow from the mix. Two files describe it: the **aircraft inventory** (what
each aircraft is) and the **fleet** (how aircraft are grouped and renewed).

| | |
|---|---|
| Packaged defaults | [`default_fleet/aircraft_inventory.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/default_fleet/aircraft_inventory.yaml), [`default_fleet/fleet.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/default_fleet/fleet.yaml), and [`fleet_no_new_aircraft.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/default_fleet/fleet_no_new_aircraft.yaml), a frozen-technology baseline |
| Entry config keys | `models.fleet.aircraft_inventory_model_data_file`, `models.fleet.fleet_model_data_file` |
| Active | When the `models.fleet` block is in your config. |
| Read by | `models_efficiency_bottom_up` (and `_simple_freight`), `models_operation_cost_bottom_up`, `models_production_cost`, `models_abatements_cost`. With a top-down efficiency bundle the files are not used. |

Status labels are defined on the [section index](index.md#how-to-read-the-parameter-tables).
Unlike the energy files, the fleet files are strict: an unknown parameter
name is rejected when the file is loaded, and a missing required value stops
the run.

## How the two files fit together

```
fleet.yaml                                  aircraft_inventory.yaml
categories:  one per passenger market
  - market_served: short_range
    subcategories: [sr_conventional_nb, …]
subcategories:  aircraft families
  - id: sr_conventional_nb
    share: 20.0                 (% of the market)
    reference_aircraft:
      old_ref: sr_conventional_nb_old    ──►  reference_aircraft: id …_old
      recent_ref: sr_conventional_nb_recent ► reference_aircraft: id …_recent
    aircraft: [sr_nb_2035, …]           ──►  aircraft: id sr_nb_2035 …
```

- A **category** serves one market of the [markets file](markets.md). Every
  passenger market must be served by exactly one category; freight markets
  are not part of the fleet file.
- A **subcategory** is an aircraft family holding a fixed share of its
  market. It is benchmarked against two in-service **reference aircraft**
  (an old and a recent generation) and lists the **new aircraft** that
  replace them, in entry-into-service order.
- The reference aircraft of the `calibration_subcategory` are **calibrated**
  so that the fleet reproduces the market's last-historical-year energy
  share (from the markets file). The calibration moves the entry-into-service
  year of the recent reference, and its `energy_per_ask` in some cases.

## `aircraft_inventory.yaml`

Two lists, `reference_aircraft` and `aircraft`. Every entry has:

| Key | Status | Description |
|---|---|---|
| `id` | Required | Identifier referenced from `fleet.yaml`. |
| `name` | Optional (reference) / Required (new aircraft) | Display name. |
| `energy_type` | Optional, new aircraft only | `DROP_IN_FUEL` (default), `HYDROGEN`, `ELECTRIC` or `HYBRID_ELECTRIC`. Decides which energy carriers the aircraft consumes. |
| `parameters` | Required | Table below. |

### Performance parameters: absolute or relative

The four performance metrics are given, **for each new aircraft and each
metric independently**, in exactly one of two modes. Setting both, or
neither, is an error.

| Absolute key | Relative key | Unit (absolute / relative) | Read by |
|---|---|---|---|
| `energy_per_ask` | `consumption_evolution` | MJ/ASK / % vs the recent reference | efficiency |
| `emission_index_nox` | `nox_evolution` | see note / % | NOx emissions |
| `emission_index_soot` | `soot_evolution` | see note / % | soot emissions |
| `doc_non_energy_base` | `doc_non_energy_evolution` | €/ASK / % | bottom-up operating costs |

In relative mode, the absolute value is `recent_reference × (1 + evolution / 100)`,
computed from the **static** value of the recent reference.

!!! note "Emission indices are relative"
    The fleet NOx and soot indices are only used as ratios: the fleet average
    is divided by its last-historical-year value and scales the emission
    indices of the fuels (see [Energy](energy.md)). Use consistent units
    across aircraft; the packaged values are per kg of fuel.

Reference aircraft always use the absolute keys.

### Other parameters

| Key | Applies to | Status | Unit | Description |
|---|---|---|---|---|
| `entry_into_service_year` | both | Required | year | Start of the aircraft's S-curve. For the recent reference of the calibration subcategory it is overwritten by the calibration. |
| `energy_per_ask`, `emission_index_nox`, `emission_index_soot`, `doc_non_energy_base` | reference | Required | as above | Absolute performance of the reference aircraft. |
| `continuous_improvement_factor_energy` | both | Optional | multiplier | `!AeroMapsCustomDataType` applied to `energy_per_ask` each year (1.0 when absent). A relatively defined aircraft does **not** inherit its reference's factor: give it its own to keep a constant gap. |
| `hybridization_factor` | both | Optional | 0–1 | Share of electric energy. Default 0. Only meaningful with `energy_type: HYBRID_ELECTRIC`. |
| `share` | both | Optional | % | `!AeroMapsCustomDataType` fleet share. Setting it on **any** card switches the whole fleet to *share-decoupling* mode: S-curves and calibration are bypassed, and every card of the fleet then needs a `share`. |
| `ask_year` | both | Only with `models_production_cost` | ASK/yr | ASK produced per aircraft per year (fleet size). |
| `rc_cost` | both | Only with `models_production_cost` | € | Recurring (unit manufacturing) cost. |
| `nrc_cost` | both | Only with `models_production_cost` | € | Non-recurring (development) cost. |
| `cruise_altitude` | both | Optional | m | Informative, not used in calculations. |
| `oew` | both | Optional | t | Operational empty weight. Informative, not used in calculations. |

## `fleet.yaml`

### `subcategories`

| Key | Status | Description |
|---|---|---|
| `id` | Required | Identifier referenced from `categories`. |
| `name` | Required | Display name, used in output names. |
| `share` | Required | Share of the category's traffic [%]. The shares of a category must add up to 100 % (± 0.1). |
| `reference_aircraft.old_ref` | Required | Id of the old in-service reference in the inventory. |
| `reference_aircraft.recent_ref` | Required | Id of the recent in-service reference. |
| `aircraft` | Optional | Ids of the new aircraft, in entry-into-service order. Omit for a family without new aircraft. |

### `categories`

| Key | Status | Description |
|---|---|---|
| `market_served` | Required | Id of a passenger market of the markets file. An unknown id, or a passenger market served by no category, is an error. |
| `subcategories` | Required | Subcategory ids. An entry may also be a mapping (`{id: …, share: …}`) that overrides fields of the subcategory for this category only. |
| `parameters.life` | Required | Average operational life of the aircraft [years]. Sets the S-curve slope. |
| `parameters.limit` | Optional | Share below which an aircraft's share is set to zero [%]. Default 2. |
| `calibration_subcategory` | Optional with one subcategory, required in practice with several | Subcategory whose reference aircraft are calibrated. With a single subcategory it is used automatically; with several and no value, calibration is skipped with a warning and the fleet looks too efficient in the medium term. |

## Example: add a new aircraft

Declare it in the inventory, relative to the recent reference of its family:

```yaml
aircraft:
  - id: mr_nb_2040_open_rotor
    name: "MR open-rotor narrow-body 2040"
    energy_type: DROP_IN_FUEL
    parameters:
      entry_into_service_year: 2040
      consumption_evolution: -30.0     # % vs mr_conventional_nb_recent
      nox_evolution: -10.0
      soot_evolution: 0.0
      doc_non_energy_evolution: 5.0
      ask_year: 352000000.0            # needed with models_production_cost
      rc_cost: 65000000.0
      nrc_cost: 12000000000.0
```

then list it in its subcategory, in entry-into-service order:

```yaml
subcategories:
  - id: mr_conventional_nb
    name: "MR conventional narrow-body"
    share: 100.0
    reference_aircraft:
      old_ref: mr_conventional_nb_old
      recent_ref: mr_conventional_nb_recent
    aircraft:
      - mr_nb_2035
      - mr_nb_2040_open_rotor
      - mr_nb_2045
```

A hydrogen or electric aircraft also needs a `default: True` hydrogen or
electric pathway in the [energy carriers file](energy.md).

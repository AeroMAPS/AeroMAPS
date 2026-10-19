# Markets and demand

The markets file splits air traffic into **markets**: passenger segments
measured in RPK, freight segments measured in RTK. Each market carries its
own share of traffic and energy, growth, COVID recovery, load factor and,
with the top-down models, its own efficiency and cost assumptions. The file
also selects the passenger demand model and the load-factor model.

| | |
|---|---|
| Packaged default | [`default_markets/markets.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/default_markets/markets.yaml): `short_range`, `medium_range`, `long_range` (passenger) and `freight` |
| Entry config key | `models.markets.markets_data_file` |
| Active | Always. The packaged file is used when the block is absent. |
| Models driven | Per market: `RPKMarket` (or a price-coupled demand model), `RPKMeasuresMarket`, `RPKReferenceMarket`, `ASKMarket`, a load-factor model, `RTKMarket`, `RTKReferenceMarket`; plus the aggregators. Also read by the efficiency, cost and fleet models. |

Status labels are defined on the [section index](index.md#how-to-read-the-parameter-tables).

## Structure

```yaml
global:            # optional: model selectors and settings shared by all markets
  demand:
    model: cagr
  load_factor:
    model: quadratic
  elasticity: {...}

defaults:          # optional: input templates, one per traffic type
  passenger:
    inputs: {...}
  freight:
    inputs: {...}

short_range:       # one block per market; the YAML key is the market id
  name: "Short Range"
  traffic_type: passenger
  traffic_unit: RPK
  inputs:
    initial: {...}
    costs: {...}
```

**Market ids** (`short_range`, `freight`…) are the YAML keys. They are
referenced by the fleet file (`market_served`), by the push fleet (segment
names) and appear in output names (`rpk_short_range`, `load_factor_freight`…).

**Inputs are grouped** (`initial`, `growth`, `covid`…) for readability only.
Each leaf becomes a parameter named `<market_id>_<key>`, for example
`short_range_load_factor_end_year`.

**`defaults` are merged into every market** of the same `traffic_type` before
the market's own values: a key set on the market wins, lists are replaced as a
whole, and a sub-group absent from both stays absent.

## `global`

| Key | Status | Default | Description |
|---|---|---|---|
| `demand.model` | Optional | `cagr` | Passenger demand model: `cagr`, `cagr_elasticity`, `constant_elasticity` or `logistic_income`. Each mode reads different inputs, see [Model choices](model_choices.md#passenger-demand). |
| `load_factor.model` | Optional | `quadratic` | Load-factor model: `quadratic` or `simple_interpolation`, see [Model choices](model_choices.md#load-factor). |
| `elasticity.price_elasticity` | Only with `cagr_elasticity` | — | Price elasticity of demand [-], applied to all passenger markets: RPK is multiplied by `(airfare / initial_airfare) ** price_elasticity`. |
| `elasticity.initial_airfare_per_rpk` | Only with `cagr_elasticity`, optional | built-in 2019 value | Reference airfare [€/RPK]. |
| `elasticity.use_elasticity` | Optional (legacy) | `false` | `true` selects `cagr_elasticity` when `demand.model` is absent. |

!!! warning "Other `global` entries override `parameters.json`"
    Any other mapping placed under `global` is flattened **without** a market
    prefix and silently replaces a same-named entry of `parameters.json`. Only
    put there what you mean to override.

## Market entry

| Key | Status | Description |
|---|---|---|
| `name` | Required | Display name, used in plots and fleet categories. |
| `traffic_type` | Required | `passenger` or `freight`. Selects the `defaults` template and the models built for the market. |
| `traffic_unit` | Optional | `RPK` or `RTK`. Informative. |
| `inputs` | Required | The sub-groups below. |

## Inputs

Every sub-group below is **Required** for every market of the given traffic
type unless stated otherwise, either in the market entry or through
`defaults`. A missing one stops the run with a *Missing required names* error
that lists the parameters. The packaged `defaults` block provides all of them
except `initial` and `costs`, which are set per market.

### `initial`: last-historical-year split

| Key | Applies to | Status | Unit | Description |
|---|---|---|---|---|
| `rpk_share_last_historical_year` | passenger | Required | % | Share of the total passenger RPK in the last historical year. |
| `rtk_share_last_historical_year` | freight | Required | % | Share of the total RTK in the last historical year. |
| `energy_share_last_historical_year` | all | Required | % | Share of the total energy consumption in the last historical year. Calibrates the efficiency of the market. |

!!! warning "Shares must add up to 100 %"
    Three sums are checked when the file is loaded, each to 100 % ± 0.2: the
    RPK shares over passenger markets, the RTK shares over freight markets,
    and the energy shares over **all** markets. Adding or removing a market
    means re-balancing the others.

### `growth`: traffic growth

| Key | Status | Unit | Description |
|---|---|---|---|
| `cagr_reference_periods` | Required, passenger: only with `cagr` and `cagr_elasticity` | years | Period boundaries. Empty for a single constant rate. |
| `cagr_reference_periods_values` | same | %/yr | Compound annual growth rate of each period (one value fewer than boundaries, or one value with empty periods). |

See [Lists in the markets file](loading.md#lists-in-the-markets-file) for the
piecewise-constant convention.

### `covid`: COVID drop and recovery

| Key | Status | Unit | Description |
|---|---|---|---|
| `covid_drop_start_year` | Required | % | Traffic drop in the COVID start year (`covid_start_year` in `parameters.json`, 2020), relative to the year before. `66.0` means −66 %. |
| `covid_end_year` | Required | year | Year by which traffic reaches the ratio below. |
| `covid_end_year_reference_ratio` | Required | % | Traffic in `covid_end_year` relative to the pre-COVID level. `100.0` means full recovery. |

The recovery only shapes prospective years: when the historical data already
covers the COVID years, these keys have no effect on them.

### `reference`: counterfactual traffic

| Key | Status | Unit | Description |
|---|---|---|---|
| `reference_cagr_reference_periods` | Required | years | Period boundaries of the reference (counterfactual) growth. |
| `reference_cagr_reference_periods_values` | Required | %/yr | Reference growth rate per period. |

The reference traffic is the counterfactual used to isolate the effect of
demand in the CO₂ decomposition (lever) outputs and plots.

### `measures`: demand-reduction measures (passenger)

| Key | Status | Unit | Description |
|---|---|---|---|
| `measures_final_impact` | Required | % | Final reduction of the market's RPK. `0.0` disables the measures. |
| `measures_start_year` | Required | year | Start of the S-shaped ramp. |
| `measures_duration` | Required | years | Duration of the ramp. |

### `load_factor`: load factor (passenger)

| Key | Status | Unit | Description |
|---|---|---|---|
| `covid_load_factor_2020` | Required | % | Load factor in 2020. |
| `load_factor_end_year` | Only with `load_factor.model: quadratic` | % | Load factor reached in the end year. |
| `load_factor_reference_years` | Only with `load_factor.model: simple_interpolation` | years | Interpolation points. |
| `load_factor_reference_years_values` | Only with `load_factor.model: simple_interpolation` | % | Load factor at each point. |

### `efficiency_simple`: top-down efficiency

**Passenger markets**, **only with** `models_efficiency_top_down` or
`models_efficiency_top_down_interp`. Ignored with a bottom-up or push fleet.

| Key | Unit | Description |
|---|---|---|
| `energy_per_ask_dropin_fuel_gain_reference_years` | years | Interpolation points of the annual efficiency gain. Empty for a constant gain. |
| `energy_per_ask_dropin_fuel_gain_reference_years_values` | %/yr | Annual reduction of the energy per ASK of drop-in aircraft. |
| `hydrogen_final_market_share` | % of ASK | Final share of hydrogen aircraft. `0.0` for none. |
| `hydrogen_introduction_year` | year | Entry into service of hydrogen aircraft. The share follows an S-curve over `fleet_renewal_duration` (`parameters.json`, 25 years). |
| `electric_final_market_share` | % of ASK | Final share of electric aircraft. |
| `electric_introduction_year` | year | Entry into service of electric aircraft. |
| `relative_energy_per_ask_hydrogen_wrt_dropin_reference_years` | years | Interpolation points. |
| `relative_energy_per_ask_hydrogen_wrt_dropin_reference_years_values` | ratio | Energy per ASK of hydrogen aircraft divided by that of drop-in aircraft. |
| `relative_energy_per_ask_electric_wrt_dropin_reference_years` | years | Interpolation points. |
| `relative_energy_per_ask_electric_wrt_dropin_reference_years_values` | ratio | Same for electric aircraft. |

**Freight markets**, **only with** `models_efficiency_bottom_up_simple_freight`:

| Key | Unit | Description |
|---|---|---|
| `energy_per_rtk_dropin_fuel_gain_reference_years` | years | Interpolation points. |
| `energy_per_rtk_dropin_fuel_gain_reference_years_values` | %/yr | Annual reduction of the energy per RTK. |

### `costs`: top-down operating costs (passenger)

**Only with** `models_operation_cost_top_down` (or its `_feedback` variant).
`doc_non_energy_per_ask_dropin_fuel_init` is also read by
`models_abatements_cost`.

| Key | Unit | Description |
|---|---|---|
| `doc_non_energy_per_ask_dropin_fuel_init` | €/ASK | Non-energy direct operating cost of drop-in aircraft in the last historical year. Market-specific: set it on each market. |
| `doc_non_energy_per_ask_dropin_fuel_gain` | %/yr | Annual change of that cost. |
| `relative_doc_non_energy_per_ask_hydrogen_wrt_dropin` | ratio | Hydrogen aircraft cost divided by drop-in aircraft cost. |
| `relative_doc_non_energy_per_ask_electric_wrt_dropin` | ratio | Same for electric aircraft. |

## Links with other files

- **Bottom-up fleet**: every passenger market must be served by one category
  of `fleet.yaml` (`market_served: <market_id>`), otherwise loading fails. The
  `initial` shares calibrate the reference aircraft. See [Bottom-up fleet](fleet.md).
- **Push fleet**: the passenger markets must be the engine segments `TP`,
  `RJ`, `NB` and `WB`. See [Push fleet](fleet_push.md).
- **Multi-region studies**: each region has its own markets file, declared in
  its own entry config.

## Example: add a market

Split the long-range market into a long-range and an ultra-long-range one.
Shares are re-balanced so that each sum stays at 100 %; all other inputs come
from `defaults`.

```yaml
long_range:
  name: "Long Range"
  traffic_type: passenger
  traffic_unit: RPK
  inputs:
    initial:
      rpk_share_last_historical_year: 30.2     # was 37.7
      energy_share_last_historical_year: 25.81 # was 32.81
    costs:
      doc_non_energy_per_ask_dropin_fuel_init: 0.024725

ultra_long_range:
  name: "Ultra Long Range"
  traffic_type: passenger
  traffic_unit: RPK
  inputs:
    initial:
      rpk_share_last_historical_year: 7.5
      energy_share_last_historical_year: 7.0
    costs:
      doc_non_energy_per_ask_dropin_fuel_init: 0.0235
    growth:                                    # overrides defaults for this market only
      cagr_reference_periods: []
      cagr_reference_periods_values: [3.5]
```

With a bottom-up fleet, also add a category serving `ultra_long_range` to
`fleet.yaml`.

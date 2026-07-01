# Phase Interface — Excel → multi-region AeroMAPS scenario

**Status:** implemented | **Companion to:** `REFACTOR_MARKETS_PLAN.md` (Phase Interface row)

Delivers the demo the user-defined-markets refactor was built for: turn the partner workbook
[`aeromaps_custom_inputs.xlsx`](aeromaps/notebooks/custom_workflow/11_custom_markets_multi_regions/custom_data_excel/aeromaps_custom_inputs.xlsx)
into a runnable **8-region × 7-market × 4-generation** scenario (plus a global freight market),
without touching the default scenarios.

## Context

The market refactor (Phases 0–6) made markets user-defined, the bottom-up fleet market-driven, and
the prospection start year flexible. What was missing was the *interface*: a way to drive AeroMAPS from
an external regional/generation workbook. Each Excel sheet is one variable to instantiate — per market,
4 aircraft **generations** with explicit per-year **shares**, an **energy type**, a base **energy/ASK**
(`e_ask_ref`), a per-year **efficiency delta** (`delta_e_ask_genX`) and **productivity**
(`fleet_productivity_*_genX`); freight is a single WORLD block.

## Decisions (locked with the user)

| # | Decision |
|---|----------|
| Architecture | Extend the bottom-up fleet model (not a new standalone efficiency model). |
| Start year | 2025; the 2019/COVID period is historic and inert via the flexible start year. |
| Fleet counts | Build the productivity-based `aircraft_in_fleet` now. |
| Freight | Single global freight via the simplified top-down freight model. |
| Fleet mapping | Per market one subcategory: **GEN1→old_reference, GEN2→recent_reference** (both drop-in), **GEN3/GEN4→new aircraft**. All four shares fed directly (share-decoupling); S-curve + base-year calibration skipped. |
| Per-year efficiency | Implement `continuous_improvement_factor_energy` (base `e_ask_ref` × yearly `delta_e`). |

## What was implemented (6 commits)

**Model code** — additive, gated on new card fields; default scenarios unchanged (26 core tests green
after each step):

- **`continuous_improvement_factor_energy`** ([`fleet_model.py`](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py),
  [`fleet_performance.py`](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_performance.py)) —
  optional per-year `!AeroMapsCustomDataType` multiplier applied to the resolved absolute `energy_per_ask`
  at the single energy compute site; absent → all-ones (no-op).
- **Share-decoupling mode** ([`fleet_model.py`](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_model.py),
  [`fleet_assignment.py`](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_assignment.py)) —
  a per-year `share` series on any card flips the fleet off the S-curve: `FleetModel.compute` writes the
  `aircraft_share` columns directly (`_compute_decoupled_aircraft_share`) and base-year reference
  calibration is skipped (reference `energy_per_ask` is given absolutely).
- **Time-varying `ask_year`** ([`fleet_numeric.py`](aeromaps/models/air_transport/aircraft_fleet_and_operations/fleet/fleet_numeric.py)) —
  `aircraft_in_fleet = ceil(aircraft_ask / ask_year)` now accepts `ask_year` as a scalar (unchanged) or a
  per-year series (productivity 2025→2045, interpolated + clamped).
- **Two standards groups** ([`models.py`](aeromaps/core/models.py)) —
  `models_efficiency_bottom_up_simple_freight` (bottom-up passenger + `FreightAircraftEfficiencySimple`)
  and `models_fleet_numeric` (standalone `FleetEvolution` for fleet counts without the flaky cost models).

**Demo** — in [`11_custom_markets_multi_regions/`](aeromaps/notebooks/custom_workflow/11_custom_markets_multi_regions/):

- **Generator** ([`generate_regional_markets.py`](aeromaps/notebooks/custom_workflow/11_custom_markets_multi_regions/generate_regional_markets.py))
  reads the workbook and writes per region `markets.yaml`, `fleet.yaml`, `aircraft_inventory.yaml`,
  `config.yaml`, `inputs_2025.json`, plus the top-level `regionalisation.yaml`. The workbook path is an
  argument (`python generate_regional_markets.py [path/to/workbook.xlsx]`, default = bundled workbook;
  also `main(excel_path=…)`). Scalar lists are emitted inline (`[2025, 2026, …]`) for readable YAML.
- **Multi-regional process.** The scenario runs as one `MultiRegionalProcess` via
  `create_multi_regional_process("regionalisation.yaml")` (`separate_processes` mode): it executes every
  region's config and exposes per-region (`<region>:<var>`) and aggregated (`overall:<var>`) outputs.
  `regionalisation.yaml` lists the regions and the `aggregation:` rules (sum + load-factor weighted by
  ASK). Per-region detail beyond the aggregated variables is read from
  `process.regional_processes[<region>]`.
- **Notebook** ([`example_notebook.ipynb`](aeromaps/notebooks/custom_workflow/11_custom_markets_multi_regions/example_notebook.ipynb))
  generates inputs, runs the multi-regional process, and plots global/per-region RPK, per-market energy
  intensity, per-generation fleet counts, and a continent-grouped per-region CO₂ mitigation waterfall
  (using `<region>:co2_emissions_including_*` / `<region>:carbon_offset`). Runs end-to-end (nbconvert,
  0 errors).

## Key mechanics

- **GEN → fleet mapping.** GEN1/GEN2 (always drop-in per `energy_type_gen`) map to the subcategory's
  `old_reference`/`recent_reference`; GEN3/GEN4 are new aircraft carrying their own `energy_type`. Result
  is exactly "4 generations and nothing else" while reusing all reference scaffolding.
- **Aircraft cards.** `energy_per_ask` ← `e_ask_ref` (absolute mode); `continuous_improvement_factor_energy`
  ← `1 + delta_e/100`; `ask_year` ← `fleet_productivity` (2025/2045); `share` ← `fleet_shares_genX`.
- **2025 anchor.** `prospection_start_year = 2026` so the workbook "2025" columns are the last reference
  year; COVID is automatically inert; historic `*_init` vectors are synthesised at the required length.
- **CAGR hack.** The partner's single ASK CAGR (2025→2045, "compute end value then linear in between") is
  converted to AeroMAPS' growth-rate convention: build the linear ASK ramp → ASK→RPK via the per-year load
  factor → emit the per-year RPK growth rates as `cagr_reference_periods` / `..._values`.
- **Freight.** The single WORLD freight block is distributed across regions by ASK share (one freight
  market per region, identical efficiency curve), so the per-region sum equals one global freight market.

## How to run

```bash
cd aeromaps/notebooks/custom_workflow/11_custom_markets_multi_regions
python generate_regional_markets.py          # per-region inputs + regionalisation.yaml from the workbook
# then open example_notebook.ipynb and run all cells (or):
jupyter nbconvert --to notebook --execute --inplace example_notebook.ipynb
```

```python
from aeromaps import create_multi_regional_process
process = create_multi_regional_process("regionalisation.yaml")
process.compute()
vo = process.data["vector_outputs"]      # has <region>:<var> and overall:<var> columns
```

## Verified

One region and the full 8-region notebook run through `create_process` + `compute`. Confirmed:
per-market `energy_per_ask` falls over time (improvement factor); hydrogen/electric ASK split flows
(e.g. NBS GEN4 → hydrogen); 28 `aircraft_in_fleet` columns (7 markets × 4 generations); per-region CO2
decomposition columns present.

## Known limitations / deferred

- **Workbook now holds realistic, AeroMAPS-anchored data** (not the original `1234.x`/`12.x` stubs),
  built reproducibly by
  [`custom_data_excel/build_workbook.py`](aeromaps/notebooks/custom_workflow/11_custom_markets_multi_regions/custom_data_excel/build_workbook.py):
  energy intensity ≈ 0.34–1.25 MJ/ASK, productivity ≈ 0.9–9.5 ×10⁸ ASK/ac/yr, growth ≈ 2–4.5 %/yr,
  LF 83→89 %, traffic in absolute ASK/RTK (global ≈ 1.15×10¹³ ASK). End-to-end magnitudes are now
  realistic: global RPK 10→19 ×10¹² (2026→2050), energy ≈ 11.5 EJ, CO₂ ≈ 1.0 Gt — matching real
  aviation. Region/market split and gen-share trajectories are plausible but illustrative (shares are
  region-uniform; energy type is per gen×market, identical across regions per the workbook layout).
- **All four generations improve over time** — `continuous_improvement_factor_energy` is now also a
  field on `ReferenceAircraftParameters` and is applied to the old/recent reference energy at the same
  compute site, so GEN1/GEN2 carry their own per-year `delta_e_ask_genX` factor just like GEN3/GEN4
  (absent → constant base, so default scenarios are unchanged).
- **Freight is per region, not "once".** Distributed by ASK share because the impacts pipeline requires a
  freight market per process (it needs `rtk`) and a zero-RTK placeholder hits the empty-market NaN issue.
  Numerically identical to one global market (uniform efficiency curve).
- **CO2 waterfall.** The per-region waterfall uses the decomposition columns AeroMAPS emits
  (`co2_emissions_including_{aircraft_efficiency,operations,load_factor,energy}`, `carbon_offset`). The
  BAU frozen-technology baseline **is** available as `co2_emissions_last_historical_year_technology`
  (flexible-start rename of the old `…_2019technology`), so the top "frozen 2025 tech" wedge can be drawn;
  only the `no_ng` fleet-renewal-only counterfactual remains a custom output (the `*_renewal_only`
  fleet-level series exist but are not yet aggregated to a CO₂ column).
- **`nbstripout` git filter** points at a stale conda env (`AeroMAPS_V1`), which fails on `.ipynb`
  staging; fix the path in `.git/config` for clean notebook commits.

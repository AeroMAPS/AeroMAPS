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
  `config.yaml`, `inputs_2025.json`.
- **Notebook** ([`example_notebook.ipynb`](aeromaps/notebooks/custom_workflow/11_custom_markets_multi_regions/example_notebook.ipynb))
  generates inputs, builds + computes one process per region, aggregates, and plots. Runs end-to-end
  (nbconvert, 0 errors).

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
python generate_regional_markets.py          # regenerate per-region inputs from the workbook
# then open example_notebook.ipynb and run all cells (or):
jupyter nbconvert --to notebook --execute --inplace example_notebook.ipynb
```

## Verified

One region and the full 8-region notebook run through `create_process` + `compute`. Confirmed:
per-market `energy_per_ask` falls over time (improvement factor); hydrogen/electric ASK split flows
(e.g. NBS GEN4 → hydrogen); 28 `aircraft_in_fleet` columns (7 markets × 4 generations); per-region CO2
decomposition columns present.

## Known limitations / deferred

- **Placeholder data.** The committed workbook holds dummy values (e.g. `cagr_rtk_freight = 1234`), so
  absolute magnitudes — freight especially — are not meaningful. The structure and code paths are correct.
- **GEN1/GEN2 do not improve over time** — reference aircraft keep a constant base `e_ask_ref`; only
  GEN3/GEN4 carry the per-year improvement factor. Extending it to references is a small follow-up.
- **Freight is per region, not "once".** Distributed by ASK share because the impacts pipeline requires a
  freight market per process (it needs `rtk`) and a zero-RTK placeholder hits the empty-market NaN issue.
  Numerically identical to one global market (uniform efficiency curve).
- **CO2 waterfall.** The per-region waterfall in the notebook uses the decomposition columns AeroMAPS
  emits (`co2_emissions_including_{aircraft_efficiency,operations,load_factor,energy}`, `carbon_offset`).
  The BAU "2019 technology" baseline and the `no_ng` (fleet-renewal-only) counterfactual from the
  multi-regional app are *custom* outputs not present in base AeroMAPS, so the "Fleet Renewal" / "Future
  Aircraft" wedges are not shown.
- **`nbstripout` git filter** points at a stale conda env (`AeroMAPS_V1`), which fails on `.ipynb`
  staging; fix the path in `.git/config` for clean notebook commits.

# Provenance for the retrospective counterfactual

No file is fetched or vendored here. Every series this analysis reads already
exists in the repository, and this note records which one and why.

## Observed traffic and the Kaya factors

`aeromaps/resources/historical_data/world_air_transport_traffic_1929_2024.csv`

A4A/ICAO world totals, `;`-delimited, 1929-2024. Provenance is documented in
that directory's own `SOURCES.md`. Four columns matter here, and together they
span the whole Kaya chain the frozen baseline needs:

| Column | Role |
|---|---|
| `rpk` | driver when load factor, gauge and fuel-side intensity are all frozen |
| `ask` | driver when load factor is left free |
| `total_aircraft_distance` | driver when load factor and average gauge are both left free |
| `load_factor` | the recovery R2 allows under frozen technology |

`aircraft_departures` is read only so that mean stage length is derivable; the
counterfactual does not use it directly, because stage length is already inside
aircraft-km.

## Observed CO2

Two sources, spliced, because neither covers 1990 to 2024.

- `aeromaps/resources/climate_data/historical_data_from_klower.csv`, column
  `CO2 [Mt/yr]`, 1940-2018. Well-to-wake; multiplied by the 0.8320 scope factor
  to reach the tank-to-wake basis the reports headline.
- `../../../3rd_edition_full/data_outputs/s1-TTW.json`, `co2_emissions_passenger`
  plus `co2_emissions_freight`, 2000-2050. This is Part A's committed
  reproduction, read and never written.

The same file also carries a `CO2_AeroMAPS [Mt/yr]` column for 2000-2018, which
is Kloewer put on the coverage basis AeroMAPS models. Its ratio to Kloewer's own
series is near-constant over that overlap, so it supports an alternative splice
in which the seam is removed. Both splices are reported: the default reproduces
the published 14.6 Gt and leaves a 7.8 % step at the seam, the alternative
removes the step and moves the 1990 anchor.

## Jet fuel price

`aeromaps/notebooks/publications/wctr_2026/data/eia_jet_fuel_prices.csv`

FRED series `MJFUELUSGULF`, US Gulf Coast kerosene-type jet fuel spot price,
monthly 1990-04 to 2026-03, averaged to calendar years. 1990 is partial, which
is left as it is: R1 compares the counterfactual fare with the observed fare
*within the same year*, so the price level cancels and no deflator is needed.

## The 2050 anchors

Both are read from Part A's committed outputs, in `3rd_edition_full/data_outputs/`:

- `s1-TTW.json` `rpk` at 2050, for extending the frozen line to the figure's own
  ~5,200 Mt endpoint;
- `t0-TTW.json`, passenger plus freight at 2050, for the figure's "2050
  emissions without additional efforts" of about 2,400 Mt.

## Parameters

`../../params_elasticity.yaml` holds the elasticity, the pass-through and the
fuel cost share. It is the only place any of the three is set.

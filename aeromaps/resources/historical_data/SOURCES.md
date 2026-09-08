# Historical world air transport traffic — provenance

`world_air_transport_traffic_1929_2024.csv` is generated from the raw A4A/ICAO
export by `build_historical_traffic.py`. Re-running that script against a newer
export refreshes the dataset in one command.

## Source

**Airlines for America (A4A), *World Airlines Traffic and Capacity*** —
<https://www.airlines.org/dataset/world-airlines-traffic-and-capacity/>

A4A compiles the series from ICAO totals for world scheduled commercial
aviation. Raw file kept alongside as
`raw_a4a_traffic_and_operations_1929_present.csv` (UTF-16LE, tab-separated,
U+202F thousands separator, decimal comma).

## Columns

| Column | Unit | Source column | Coverage |
|---|---|---|---|
| `year` | — | Year | 1929–2024 |
| `aircraft_departures` | departures/yr | Aircraft Departures (000) | 1960–2024 |
| `total_aircraft_distance` | km/yr | Aircraft KMs (mils) | 1929–2024 |
| `passengers` | pax/yr | Passengers (mils) | 1945–2024 |
| `rpk` | RPK/yr | RPKs (mils) | 1929–2024 |
| `ask` | ASK/yr | ASKs (mils) | 1950–2024 |
| `load_factor` | % | PLF | 1950–2024 |
| `freight_tonnes` | t/yr | Freight Tonnes (mils) | 1969–2024 |
| `rtk` | RTK/yr | Cargo RTKs (mils) | 1945–2024 |

Blank cells mean the source has no value for that year; they are never
interpolated here.

`load_factor` is redundant — it reproduces `100 * rpk / ask` to within
**0.050 pp** across all 75 years that carry it (worst case 1963). It is retained
as a cross-check only and must not be used as an independent input.

## Differences from the AeroMAPS defaults this supersedes

The previous history lived in `resources/data/partitioning_inputs.json`
(`other_vector_data`, **2000–2019 only**) and `resources/data/vector_inputs.csv`.
A4A is already the upstream source of that data, so this is a vintage refresh
and an extension, not a change of source.

**Aircraft distance is identical.** `total_aircraft_distance_init` for 2000 is
2.5982e10 km, exactly A4A's 25,982 million km. The 1940–1999 leg in
`climate_data/historical_data_from_klower.csv` (`distance [million km]`) is the
same series.

**2005–2019 agrees closely** — maximum absolute deviation over that span:

| Column | max deviation | year |
|---|---|---|
| `rpk` | 0.25 % | 2019 |
| `ask` | 0.23 % | 2019 |
| `total_aircraft_distance` | 0.47 % | 2017 |
| `passengers` | 0.35 % | 2011 |
| `freight_tonnes` | 1.62 % | 2013 |
| `rtk` | **6.33 %** | 2013 |

**2000–2004 carries a source revision.** A4A has since revised the early 2000s
upward: `rpk` is +5.39 % in 2000 and 2001, decaying to +0.55 % by 2004 and
+0.14 % by 2005. `ask` behaves the same way (+5.09 % worst, 2001). This is A4A
restating its own history, not a definitional difference.

**`rtk` differs systematically and is the one column to treat with care.** A4A
"Cargo RTKs" runs consistently *above* the stored `rtk_init` — +13.1 % (2000),
+3.2 % (2005), +2.5 % (2010), +4.2 % (2015), +2.7 % (2019). A persistent offset
of this shape is not explained by vintage revision and most likely reflects a
scope difference (mail included in cargo RTK, or scheduled vs total). Until it
is resolved, code extending `rtk_init` with A4A values should rescale onto the
existing level using the 2015–2019 overlap rather than splicing raw values, so
that no step discontinuity is introduced at the join.

**2020–2024 is entirely new.** AeroMAPS previously held no observed data past
2019 and *simulated* the COVID period. Observed 2024 is 9.098e12 RPK at 83.2 %
load factor, against 8.854e12 and 84.18 % in the pre-existing simulation.

**Aircraft departures are entirely new** — no departures series existed in
AeroMAPS. Mean stage length (`total_aircraft_distance / aircraft_departures`)
runs 980 km/departure in 1990, 1,076 in 2000, 1,467 in 2019 and 1,569 in 2024.

**Energy consumption is not in this source.** `energy_consumption_init` retains
its existing provenance; values beyond 2019 are taken from the ATAG *Waypoint
2050* 3rd-edition series. Because that series is also the object of study in the
accompanying critique, the post-2019 historical leg is partly endogenous to the
work that consumes it — both companion papers state this explicitly.

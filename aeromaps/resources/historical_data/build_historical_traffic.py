"""
build_historical_traffic
========================
Convert the raw A4A/ICAO "World Airlines Traffic and Capacity" export into the
tidy historical series consumed by AeroMAPS.

The raw export is awkward on three counts, all handled here so that refreshing
the dataset with a new vintage is a single command:

* UTF-16LE encoded, with a BOM;
* tab-separated, with the year column carrying a leading BOM on the header row;
* European number formatting -- U+202F (narrow no-break space) as the thousands
  separator and a comma as the decimal separator, plus a trailing '%' on the
  passenger load factor.

Units are converted to SI-consistent AeroMAPS conventions on the way out
(see SOURCES.md for the per-column provenance and the differences against the
defaults this dataset supersedes).

Usage
-----
    python build_historical_traffic.py [raw_csv] [output_csv]
"""

import csv
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_RAW = HERE / "raw_a4a_traffic_and_operations_1929_present.csv"
DEFAULT_OUT = HERE / "world_air_transport_traffic_1929_2024.csv"

# Raw column -> (tidy column, multiplier to reach the AeroMAPS unit).
# The raw header order is fixed by the source export.
COLUMNS = [
    ("Aircraft Departures (000)", "aircraft_departures", 1e3),
    ("Aircraft KMs (mils)", "total_aircraft_distance", 1e6),  # -> km
    ("Passengers (mils)", "passengers", 1e6),
    ("RPKs (mils)", "rpk", 1e6),  # -> RPK
    ("ASKs (mils)", "ask", 1e6),  # -> ASK
    ("PLF", "load_factor", 1.0),  # -> %
    ("Freight Tonnes (mils)", "freight_tonnes", 1e6),  # -> t
    ("Cargo RTKs (mils)", "rtk", 1e6),  # -> RTK
]

# U+202F narrow no-break space, U+00A0 no-break space and plain spaces all show
# up as thousands separators across vintages of this export.
_STRIP = re.compile(r"[  \s%]")


def parse_number(raw):
    """Parse one European-formatted cell; return None when the source is blank."""
    cleaned = _STRIP.sub("", raw).replace(",", ".")
    return float(cleaned) if cleaned else None


def read_raw(path):
    """Read the raw export into {year: {tidy_column: value_in_aeromaps_units}}."""
    text = Path(path).read_bytes().decode("utf-16")
    rows = [r for r in csv.reader(io.StringIO(text), delimiter="\t") if r and r[0].strip()]

    header = [h.strip().lstrip("﻿") for h in rows[0]]
    expected = ["Year"] + [raw_name for raw_name, _, _ in COLUMNS]
    if header != expected:
        raise ValueError(f"Unexpected raw header.\n  expected: {expected}\n  found:    {header}")

    data = {}
    for row in rows[1:]:
        year = int(parse_number(row[0]))
        values = {}
        for (_, name, factor), cell in zip(COLUMNS, row[1:]):
            value = parse_number(cell)
            values[name] = None if value is None else value * factor
        data[year] = values
    return data


def write_tidy(data, path):
    """Write the tidy CSV, oldest year first, ';'-delimited to match AeroMAPS."""
    names = [name for _, name, _ in COLUMNS]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["year"] + names)
        for year in sorted(data):
            row = data[year]
            writer.writerow(
                [year] + ["" if row[n] is None else repr(row[n]) for n in names]
            )
    return len(data)


def main(argv):
    raw_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_RAW
    out_path = Path(argv[2]) if len(argv) > 2 else DEFAULT_OUT

    data = read_raw(raw_path)
    n = write_tidy(data, out_path)

    years = sorted(data)
    print(f"wrote {out_path} ({n} years, {years[0]}-{years[-1]})")
    for _, name, _ in COLUMNS:
        present = [y for y in years if data[y][name] is not None]
        print(f"  {name:<26} {present[0]}-{present[-1]}  ({len(present)} values)")

    # The load factor is redundant with rpk/ask; verify rather than trust it.
    worst = max(
        (
            (abs(100 * data[y]["rpk"] / data[y]["ask"] - data[y]["load_factor"]), y)
            for y in years
            if data[y]["load_factor"] and data[y]["ask"]
        ),
        default=(0.0, None),
    )
    print(f"  load_factor vs rpk/ask: max deviation {worst[0]:.3f} pp (year {worst[1]})")


if __name__ == "__main__":
    main(sys.argv)

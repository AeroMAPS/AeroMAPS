"""
extend_partitioning_inputs
==========================
Extend the observed period in ``resources/data/partitioning_inputs.json``
(``other_vector_data``) from 2019 to 2023, so that scenarios can run with
``prospection_start_year = 2024`` against real data rather than a simulated
COVID recovery.

Sources, per column
-------------------
``rpk_init``, ``ask_init``, ``pax_init``, ``freight_init``,
``total_aircraft_distance_init``
    Spliced directly from the A4A/ICAO tidy dataset. These agree with the
    incumbent 2005-2019 values to within 0.5 %, so no level correction is
    needed at the join (see SOURCES.md).

``rtk_init``
    A4A "Cargo RTKs" runs systematically above the stored series (+2.5 % to
    +13 %), a persistent offset that vintage revision does not explain and that
    most likely reflects a scope difference (mail, or scheduled vs total).
    Rather than splice raw values and introduce a step, A4A is rescaled onto the
    incumbent level by the mean stored/A4A ratio over the 2015-2019 overlap.

``energy_consumption_init``
    Not present in the A4A source. Taken as the ATAG *Waypoint 2050* 3rd-edition
    energy intensity (MJ per ASK) multiplied by the **observed** A4A capacity, so
    the intensity comes from ATAG while the traffic level stays consistent with
    the rest of the extended history. Because the ATAG series is also the object
    of study in the accompanying critique, this makes the post-2019 historical
    leg partly endogenous to the work consuming it; both companion papers state
    this explicitly.

Both ``partitioning_inputs.json`` and ``parameters.json`` carry a copy of these
historic series -- ``parameters.json`` is validated first at load time, so both
must be extended together or the run fails on a length check. This script writes
both from the same computed values so they cannot drift apart.

The script is idempotent: it rewrites the extended years from source each run.

Usage
-----
    python extend_partitioning_inputs.py [--check]

``--check`` reports what would change without writing.
"""

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[2]

TIDY_CSV = HERE / "world_air_transport_traffic_1929_2024.csv"
PARTITIONING = REPO / "aeromaps" / "resources" / "data" / "partitioning_inputs.json"
PARAMETERS = REPO / "aeromaps" / "resources" / "data" / "parameters.json"
ATAG_S1 = (
    REPO
    / "aeromaps/notebooks/scenarios/02_atag_waypoint2050/3rd_edition_full/data_outputs/s1.json"
)

LAST_INCUMBENT_YEAR = 2019
NEW_LAST_YEAR = 2023
OVERLAP = range(2015, 2020)  # used to calibrate the rtk level correction

# tidy column -> partitioning key, for the columns spliced without correction
DIRECT = {
    "rpk": "rpk_init",
    "ask": "ask_init",
    "passengers": "pax_init",
    "freight_tonnes": "freight_init",
    "total_aircraft_distance": "total_aircraft_distance_init",
}


def load_tidy():
    with open(TIDY_CSV, encoding="utf-8") as f:
        return {
            int(r["year"]): {k: (float(v) if v else None) for k, v in r.items() if k != "year"}
            for r in csv.DictReader(f, delimiter=";")
        }


def atag_energy_intensity():
    """ATAG 3rd-edition energy per ASK [MJ/ASK], keyed by year."""
    v = json.loads(ATAG_S1.read_text())["vector_outputs"]
    # vector_outputs are indexed from historic_start_year (2000)
    return {2000 + i: e / a for i, (e, a) in enumerate(zip(v["energy_consumption"], v["ask"]))}


def build(check=False):
    tidy = load_tidy()
    doc = json.loads(PARTITIONING.read_text())
    ov = doc["other_vector_data"]
    idx = {y: i for i, y in enumerate(ov["years"])}

    # Level correction for rtk, calibrated on the overlap.
    ratios = [ov["rtk_init"][idx[y]] / tidy[y]["rtk"] for y in OVERLAP]
    rtk_factor = sum(ratios) / len(ratios)

    intensity = atag_energy_intensity()

    new_years = [y for y in range(LAST_INCUMBENT_YEAR + 1, NEW_LAST_YEAR + 1)]
    added = {}
    for y in new_years:
        row = tidy[y]
        values = {key: row[col] for col, key in DIRECT.items()}
        values["rtk_init"] = row["rtk"] * rtk_factor
        values["energy_consumption_init"] = intensity[y] * row["ask"]
        added[y] = values

    if check:
        print(f"rtk level correction (stored/A4A, {OVERLAP.start}-{OVERLAP.stop - 1}): {rtk_factor:.4f}")
        print(f"incumbent years: {ov['years'][0]}-{ov['years'][-1]}")
        print(f"would add: {new_years}")
        for y in new_years:
            print(f"  {y}: " + "  ".join(f"{k}={v:.4e}" for k, v in sorted(added[y].items())))
        return

    # Drop any previously appended years, then re-append from source (idempotent).
    keep = [i for i, y in enumerate(ov["years"]) if y <= LAST_INCUMBENT_YEAR]
    for key in list(ov):
        ov[key] = [ov[key][i] for i in keep]

    for y in new_years:
        ov["years"].append(y)
        for key, value in added[y].items():
            ov[key].append(value)

    PARTITIONING.write_text(json.dumps(doc, indent=4, ensure_ascii=False) + "\n")

    # parameters.json holds a second copy of the same series and is length-checked
    # on load, so it must carry exactly the same years.
    params = json.loads(PARAMETERS.read_text())
    n_incumbent = LAST_INCUMBENT_YEAR - params["historic_start_year"] + 1
    for key in set(DIRECT.values()) | {"rtk_init", "energy_consumption_init"}:
        if key not in params:
            continue
        params[key] = params[key][:n_incumbent] + [added[y][key] for y in new_years]
    PARAMETERS.write_text(json.dumps(params, indent=4, ensure_ascii=False) + "\n")

    print(f"extended other_vector_data to {ov['years'][0]}-{ov['years'][-1]} "
          f"({len(ov['years'])} years); rtk level correction {rtk_factor:.4f}")
    print(f"mirrored {len(new_years)} years into parameters.json "
          f"(now {len(params['rpk_init'])} values per historic series)")


if __name__ == "__main__":
    build(check="--check" in sys.argv)

"""
extend_atag_baseline
====================
Extend the observed period of the **ATAG third-edition scenarios** from 2019 to
2023, so they run with ``prospection_start_year = 2024`` against real data rather
than a simulated COVID recovery.

The extended series are written into each third-edition scenario's own
``*_inputs.json``, **not** into ``resources/data/parameters.json``. They were
originally written into the packaged defaults, which silently re-baselined every
other scenario in the repository: all 52 committed publication outputs and the
five tutorial reference fixtures still carry the 20-year incumbent series, so
none of them had ever been regenerated against the change. A scenario that wants
a different baseline states it in its own inputs file, which is what the second
edition already does for ``prospection_start_year`` and what the coupled-demand
scenario already does for ``rpk_init``.

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

The incumbent 2000-2019 leg is read from the packaged ``parameters.json`` and the
rtk level correction is calibrated against ``partitioning_inputs.json``; both are
read only, never written. The length check lives in
``aeromaps.utils.functions._dict_from_parameters_dict``, which requires each
``*_init`` vector to hold exactly ``prospection_start_year - historic_start_year``
values and reads both bounds from the dict it is validating. It is therefore
per-document, not cross-file: a 24-entry scenario series against a 20-entry
default is fine, provided the scenario states both bounds itself.

The script is idempotent: it rewrites the extended years from source each run.

Usage
-----
    python extend_atag_baseline.py [--check]

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
ATAG = REPO / "aeromaps" / "notebooks" / "scenarios" / "02_atag_waypoint2050"
ATAG_S1 = ATAG / "3rd_edition_full" / "data_outputs" / "s1.json"

# The third-edition scenarios, the only ones that take the extended baseline. The
# second edition deliberately stays on its 2020 baseline and says so in its own
# inputs files. The coupled-demand scenario is included: it already carried
# rpk_init and both year bounds, but drew the other six series from the defaults,
# so on its own it would run 2020-2023 with no observed capacity and FaIR would
# be handed NaN emissions.
TARGETS = (
    [
        ATAG / "3rd_edition_full" / "data_inputs" / f"{s}_inputs.json"
        for s in ("s1", "s2", "t0", "t1", "t2", "t3", "t4")
    ]
    + [ATAG / "3rd_edition_light" / "data_inputs" / f"{s}_inputs.json" for s in ("s0", "s1", "s2")]
    + [ATAG / "3rd_edition_full_coupled_demand" / "data_inputs" / "s1_inputs.json"]
)

# The coupled-demand scenario supplies its own historical RPK, an AR6-consistent
# series that runs up to 3 % away from the A4A one across 2000-2019. That is a
# deliberate scenario choice, so this script fills its six missing series and
# leaves rpk_init to it.
KEEP_EXISTING = {
    ATAG / "3rd_edition_full_coupled_demand" / "data_inputs" / "s1_inputs.json": {"rpk_init"},
}

PROSPECTION_START_YEAR = 2024
LAST_INCUMBENT_YEAR = 2019
NEW_LAST_YEAR = 2023
OVERLAP = range(2015, 2020)  # used to calibrate the rtk level correction

# tidy column -> parameter key, for the columns spliced without correction
DIRECT = {
    "rpk": "rpk_init",
    "ask": "ask_init",
    "passengers": "pax_init",
    "freight_tonnes": "freight_init",
    "total_aircraft_distance": "total_aircraft_distance_init",
}
SERIES = sorted(set(DIRECT.values()) | {"rtk_init", "energy_consumption_init"})


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


def added_years():
    """The 2020-2023 values, per series, computed from source."""
    tidy = load_tidy()
    ov = json.loads(PARTITIONING.read_text())["other_vector_data"]
    idx = {y: i for i, y in enumerate(ov["years"])}

    # Level correction for rtk, calibrated on the overlap.
    ratios = [ov["rtk_init"][idx[y]] / tidy[y]["rtk"] for y in OVERLAP]
    rtk_factor = sum(ratios) / len(ratios)

    intensity = atag_energy_intensity()
    added = {}
    for year in range(LAST_INCUMBENT_YEAR + 1, NEW_LAST_YEAR + 1):
        row = tidy[year]
        values = {key: row[col] for col, key in DIRECT.items()}
        values["rtk_init"] = row["rtk"] * rtk_factor
        values["energy_consumption_init"] = intensity[year] * row["ask"]
        added[year] = values
    return added, rtk_factor


def extended_block():
    """The full 2000-2023 series plus the prospection start year, ready to stamp."""
    added, rtk_factor = added_years()
    params = json.loads(PARAMETERS.read_text())
    n_incumbent = LAST_INCUMBENT_YEAR - params["historic_start_year"] + 1
    years = sorted(added)
    # historic_start_year travels with the vectors: _dict_from_parameters_dict
    # validates len(vector) == prospection_start_year - historic_start_year and
    # reads both bounds from the same dict, so a scenario that declares its own
    # history must declare the window it spans. The coupled-demand scenario
    # already does exactly this.
    block = {
        "historic_start_year": params["historic_start_year"],
        "prospection_start_year": PROSPECTION_START_YEAR,
    }
    for key in SERIES:
        block[key] = params[key][:n_incumbent] + [added[y][key] for y in years]
    return block, added, rtk_factor


def build(check=False):
    block, added, rtk_factor = extended_block()
    years = sorted(added)

    if check:
        print(
            f"rtk level correction (stored/A4A, {OVERLAP.start}-{OVERLAP.stop - 1}): {rtk_factor:.4f}"
        )
        print(f"would write {years[0]}-{years[-1]} into {len(TARGETS)} scenario inputs files")
        for year in years:
            print(f"  {year}: " + "  ".join(f"{k}={v:.4e}" for k, v in sorted(added[year].items())))
        stale = [
            t
            for t in TARGETS
            if any(
                json.loads(t.read_text()).get(k) != v
                for k, v in block.items()
                if k not in KEEP_EXISTING.get(t, set())
            )
        ]
        print(
            f"out of date: {len(stale)}"
            + ("".join(f"\n  {t.relative_to(ATAG)}" for t in stale) if stale else "")
        )
        return

    for target in TARGETS:
        doc = json.loads(target.read_text())
        keep = KEEP_EXISTING.get(target, set())
        doc.update({k: v for k, v in block.items() if k not in keep})
        target.write_text(json.dumps(doc, indent=4).replace("\n", "\r\n") + "\r\n", newline="")
        print(f"stamped {target.relative_to(ATAG)}")
    print(
        f"{len(TARGETS)} scenario inputs now observed through {NEW_LAST_YEAR}, "
        f"prospection start {PROSPECTION_START_YEAR}; rtk level correction {rtk_factor:.4f}"
    )


if __name__ == "__main__":
    build(check="--check" in sys.argv)

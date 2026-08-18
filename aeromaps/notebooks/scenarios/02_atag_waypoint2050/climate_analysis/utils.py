"""
utils
=====
Shared loading and styling for the ATAG *Waypoint 2050* climate analysis
notebooks.

The scenario results are read straight from the committed
``<edition>/data_outputs/<scenario>.json`` files, so the notebooks are pure
post-processing and do not need to re-run the model. Two blocks are used:

``climate_outputs``
    Serialized as bare lists covering ``climate_historic_start_year`` to
    ``end_year`` (1940-2050 in these scenarios), with no year index of their
    own -- :func:`load_climate` restores the index.

``vector_outputs``
    Serialized over ``historic_start_year`` to ``end_year`` (2000-2050). The
    start year is read back from the file rather than assumed, so the loader
    survives a change of the prospection boundary.

Both loaders return a DataFrame indexed by year.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

# 02_atag_waypoint2050/
BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[3]
OBSERVED = REPO / "aeromaps" / "resources" / "historical_data" / (
    "world_air_transport_traffic_1929_2024.csv"
)

CLIMATE_HISTORIC_START_YEAR = 1940


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def _read(edition, scenario):
    path = BASE / edition / "data_outputs" / f"{scenario}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No committed results for {edition}/{scenario} at {path}. "
            "Run the edition notebook first."
        )
    return json.loads(path.read_text())


def load_climate(edition, scenario):
    """Climate outputs for one scenario, indexed 1940-2050."""
    block = _read(edition, scenario)["climate_outputs"]
    n = len(next(iter(block.values())))
    index = pd.RangeIndex(
        CLIMATE_HISTORIC_START_YEAR, CLIMATE_HISTORIC_START_YEAR + n, name="year"
    )
    return pd.DataFrame(block, index=index)


def load_vectors(edition, scenario):
    """Vector outputs for one scenario, indexed from the historic start year.

    The start year is derived from the file's own ``float_inputs`` where
    available so that the loader keeps working if the prospection boundary
    moves; otherwise it is inferred from the series length against the climate
    block's end year.
    """
    data = _read(edition, scenario)
    block = data["vector_outputs"]
    n = len(next(iter(block.values())))

    start = data.get("float_inputs", {}).get("historic_start_year")
    if start is None:
        n_climate = len(next(iter(data["climate_outputs"].values())))
        end_year = CLIMATE_HISTORIC_START_YEAR + n_climate - 1
        start = end_year - n + 1
    start = int(start)

    return pd.DataFrame(block, index=pd.RangeIndex(start, start + n, name="year"))


def load_observed():
    """The A4A/ICAO observed traffic series, indexed by year.

    Blank cells in the source stay as NaN -- they are years the source does not
    cover, never interpolated.
    """
    rows = list(csv.DictReader(OBSERVED.open(encoding="utf-8"), delimiter=";"))
    frame = pd.DataFrame(rows)
    frame["year"] = frame["year"].astype(int)
    frame = frame.set_index("year")
    return frame.apply(pd.to_numeric, errors="coerce")


# --------------------------------------------------------------------------
# Mechanism grouping and styling
# --------------------------------------------------------------------------
# The climate module resolves twelve forcing mechanisms, which is well past the
# number of hues a reader can hold apart. They are grouped into five families
# for plotting -- the four NOx terms sum to a single net NOx contribution, and
# soot and sulfur to a single aerosol term -- with the full twelve-way split
# reported in the tables instead.

MECHANISM_GROUPS = {
    "co2": ("CO$_2$", ["co2"]),
    "contrails": ("Contrails", ["contrails"]),
    "nox": ("NO$_x$ (net)", [
        "nox_short_term_o3_increase",
        "nox_long_term_o3_decrease",
        "nox_ch4_decrease",
        "nox_stratospheric_water_vapor_decrease",
    ]),
    "h2o": ("H$_2$O", ["h2o"]),
    "aerosol": ("Aerosols (soot + sulfur)", ["soot", "sulfur"]),
}

# Categorical slots 1-5 of the validated reference palette, assigned in fixed
# order. Never cycled: a sixth family would be folded in, not given a new hue.
COLORS = {
    "co2": "#2a78d6",
    "contrails": "#eb6834",
    "nox": "#1baf7a",
    "h2o": "#eda100",
    "aerosol": "#e87ba4",
}

INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#8a8981"
GRID = "#e3e2dd"

# Scenario naming differs between editions: the third edition swapped its two
# scenarios relative to the second, so analogous scenarios must be paired
# explicitly rather than by name. Asserted in the comparison notebook.
ANALOGOUS = {
    ("3rd_edition_full", "s1"): ("2nd_edition_full", "s2"),
    ("3rd_edition_full", "s2"): ("2nd_edition_full", "s1"),
}


def temperature(df, group):
    """Aviation-attributable temperature for one mechanism group [K]."""
    cols = [f"temperature_increase_from_{m}_from_aviation" for m in MECHANISM_GROUPS[group][1]]
    return df[cols].sum(axis=1)


def erf(df, group):
    """Effective radiative forcing for one mechanism group [W/m2]."""
    return df[[f"{m}_erf" for m in MECHANISM_GROUPS[group][1]]].sum(axis=1)


def style_axes(ax, ylabel=None, xlabel="Year"):
    """Recessive grid and axes, so the data carries the chart."""
    ax.set_axisbelow(True)
    ax.grid(True, color=GRID, linewidth=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9, length=0)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK_SECONDARY, fontsize=9)
    if xlabel:
        ax.set_xlabel(xlabel, color=INK_SECONDARY, fontsize=9)
    return ax


# Contrail avoidance is switched off in every ATAG configuration
# (operations_contrails_start_year = 2101), matching the reports' own scope.
# Stated on every figure that shows a contrail contribution.
CONTRAIL_NOTE = (
    "Contrail avoidance is disabled in all scenarios "
    "(operations_contrails_start_year = 2101), matching the reports' scope."
)

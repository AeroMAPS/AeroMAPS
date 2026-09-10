"""Block A: what price elasticity does to the cost-optimal path at a fixed carbon budget.

Four panels, one line per elasticity. Every run here meets the same absolute cumulative
budget -- 3.8616 GtCO2 over 2020-2050, the ReFuelEU-linear number -- so the panels show
*how* each elasticity gets there, not whether it does.

The elasticity is an ordered quantity, so the series take a single-hue sequential ramp
from light (fixed demand) to dark (-1.4) rather than five unrelated colours; the
baseline -0.9 is drawn heavier. Panel (a) carries the exogenous trajectory as a grey
dashed reference, because the crossing of the two is the mechanism the other panels
inherit: fares sit below the 2019 anchor until 2044, so demand response *adds* traffic
for most of the horizon and only suppresses it at the end.

Usage:  poetry run python plot_elasticity.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

YEARS = list(range(2000, 2051))
ANCHOR = 0.09236379319842411

# Ordered light -> dark on |eps|. A sequential ramp, not a categorical palette: the
# variable is ordered, and reading the panels means reading that order off the ink.
CASES = [
    ("fixed demand", "fixed_demand", "#c6dbef"),
    ("-0.6", "eps_m0_6", "#9ecae1"),
    ("-0.8", "eps_m0_8", "#4292c6"),
    ("-0.9 (baseline)", "base", "#2171b5"),
    ("-1.4", "eps_m1_4", "#08306b"),
]
INK, MUTED, GRID = "#1a1a1a", "#6b6b6b", "#e2e2e2"
SPAN = slice(2020, 2050)


def series(run, key):
    vectors = json.load(open(HERE / "results" / f"{run}.json"))["vector_outputs"]
    return pd.Series(vectors[key], index=YEARS) if key in vectors else None


def main():
    """Block A on the shared six-panel layout, plus the traffic inset it needs."""
    from plot_sensitivities import six_panels

    cases = [
        (label, run, colour, "-", 2.4 if run == "base" else 1.7) for label, run, colour in CASES
    ]

    def notes(axes):
        (traffic, _, mac), (biofuel, electrofuel, _) = axes

        reference = series("base", "rpk_no_elasticity")
        traffic.plot(
            reference.loc[SPAN].index,
            reference.loc[SPAN] / 1e12,
            color=MUTED,
            lw=1.4,
            ls=(0, (5, 3)),
            zorder=1,
        )

        # The elasticity spread is under 1.5 % of a trajectory that grows fivefold, so
        # on the full axis the lines lie on top of one another. The inset carries the
        # last years at their own scale, where the ordering is the point: 2050 traffic
        # falls as |eps| rises, even though cumulative traffic rises.
        zoom = traffic.inset_axes([0.56, 0.09, 0.42, 0.40])
        zoom.grid(True, color=GRID, lw=0.6)
        zoom.set_axisbelow(True)
        for side in ("top", "right"):
            zoom.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            zoom.spines[side].set_color(MUTED)
        zoom.tick_params(colors=MUTED, labelsize=7)
        zoom.plot(
            reference.loc[2044:2050].index,
            reference.loc[2044:2050] / 1e12,
            color=MUTED,
            lw=1.2,
            ls=(0, (5, 3)),
            zorder=1,
        )
        for label, run, colour in CASES:
            rpk = series(run, "rpk")
            zoom.plot(
                rpk.loc[2044:2050].index,
                rpk.loc[2044:2050] / 1e12,
                color=colour,
                lw=2.4 if run == "base" else 1.7,
            )
        zoom.set_title("2044-2050, enlarged", fontsize=7.5, color=MUTED, pad=3)

        fare = series("base", "airfare_per_rpk")
        crossing = next(y for y in range(2025, 2051) if fare.loc[y] > ANCHOR)
        traffic.axvline(crossing, color=MUTED, lw=0.9, ls=":", zorder=0)
        traffic.annotate(
            f"fare crosses the\n2019 anchor, {crossing}",
            xy=(crossing, 0.9),
            xytext=(crossing - 1.5, 0.86),
            textcoords=("data", "axes fraction"),
            ha="right",
            fontsize=8.5,
            color=MUTED,
        )
        traffic.annotate(
            "exogenous\n(no price response)",
            xy=(2032, reference.loc[2032] / 1e12),
            xytext=(2029, 0.10),
            textcoords=("data", "axes fraction"),
            ha="center",
            fontsize=8.5,
            color=MUTED,
            arrowprops=dict(
                arrowstyle="-", color=MUTED, lw=0.8, connectionstyle="angle3,angleA=0,angleB=90"
            ),
        )
        biofuel.annotate(
            "biomass-capped: near-identical\nacross elasticities",
            xy=(2043, 39.6),
            xytext=(2022, 0.80),
            textcoords=("data", "axes fraction"),
            fontsize=8.5,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )
        electrofuel.annotate(
            "the whole adjustment\nhappens here",
            xy=(2049, 19.5),
            xytext=(2022, 0.62),
            textcoords=("data", "axes fraction"),
            fontsize=8.5,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )
        mac.annotate(
            "a cheaper way to abate:\nflights that do not happen",
            xy=(2048, 372),
            xytext=(2021.5, 0.72),
            textcoords=("data", "axes fraction"),
            fontsize=8.5,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )

    six_panels(
        cases,
        "Cost-optimal path to the same carbon budget, by price elasticity",
        "Blocks A and A'. Case main, biomass 10 %, cumulative 2020-2050 CO2 fixed at "
        "3.8616 GtCO2 (ReFuelEU linear) in every run.",
        "price elasticity",
        "fig_elasticity_panels",
        annotate=notes,
    )


if __name__ == "__main__":
    main()

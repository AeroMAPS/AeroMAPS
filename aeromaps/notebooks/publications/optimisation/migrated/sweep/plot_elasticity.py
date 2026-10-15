"""Block A: what price elasticity does to the cost-optimal path at a fixed carbon budget.

Four panels, one line per elasticity. Every run here meets the same absolute cumulative
budget -- 3.8656 GtCO2 over 2020-2050, the ReFuelEU-linear number -- so the panels show
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

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import dataset as D  # noqa: E402
import paper_style as style  # noqa: E402

YEARS = list(range(2000, 2051))
ANCHOR = 0.09236379319842411

# Ordered light -> dark on |eps|. A sequential ramp, not a categorical palette: the
# variable is ordered, and reading the panels means reading that order off the ink.
# Purple, the hue price elasticity has in the summary figure -- navy is the carbon budget.
CASES = [
    (label, run, colour)
    for (label, run), colour in zip(
        [
            ("fixed demand", "fixed_demand"),
            ("-0.6", "eps_m0_6"),
            ("-0.8", "eps_m0_8"),
            ("-0.9 (baseline)", "base"),
            ("-1.4", "eps_m1_4"),
        ],
        style.ramp(style.SEQUENTIAL_PURPLE, 5),
    )
]
INK, MUTED, GRID = style.INK, style.MUTED, style.GRID
SPAN = slice(2019, 2050)  # as in plot_sensitivities: anchored on 2019


def series(run, key):
    vectors = D.outputs(run)
    return pd.Series(vectors[key], index=YEARS) if key in vectors else None


def main():
    """Block A on the shared six-panel layout, plus the traffic inset it needs."""
    from plot_sensitivities import sensitivity_panels

    cases = [
        (label, run, colour, "-", 2.4 if run == "base" else 1.7) for label, run, colour in CASES
    ]

    def notes(axes):
        (traffic, _, _), (biofuel, electrofuel, _), _ = axes

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
        style.inset_frame(zoom)
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
        zoom.set_title("Zoom: 2044-2050", fontsize=style.SMALL_SIZE, fontweight="normal", pad=4)

        fare = series("base", "airfare_per_rpk")
        crossing = next(y for y in range(2025, 2051) if fare.loc[y] > ANCHOR)
        traffic.axvline(crossing, color=MUTED, lw=0.9, ls=":", zorder=0)
        traffic.annotate(
            f"fare crosses the\n2019 anchor, {crossing}",
            xy=(crossing, 0.9),
            xytext=(crossing - 1.5, 0.86),
            textcoords=("data", "axes fraction"),
            ha="right",
            fontsize=style.SMALL_SIZE,
            color=MUTED,
        )
        traffic.annotate(
            "exogenous\n(no price response)",
            xy=(2032, reference.loc[2032] / 1e12),
            xytext=(2029, 0.10),
            textcoords=("data", "axes fraction"),
            ha="center",
            fontsize=style.SMALL_SIZE,
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
            fontsize=style.SMALL_SIZE,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )
        electrofuel.annotate(
            "the whole adjustment\nhappens here",
            xy=(2049, 15.0),
            xytext=(2022, 0.62),
            textcoords=("data", "axes fraction"),
            fontsize=style.SMALL_SIZE,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )

    sensitivity_panels(
        cases,
        "Cost-optimal path to the same carbon budget, by price elasticity",
        "Blocks A and A'. Case main, biomass 10 %, cumulative 2020-2050 CO2 fixed at "
        "3.8656 GtCO2 (ReFuelEU linear) in every run.",
        "Price elasticity",
        "fig_elasticity_panels",
        annotate=notes,
    )


if __name__ == "__main__":
    main()

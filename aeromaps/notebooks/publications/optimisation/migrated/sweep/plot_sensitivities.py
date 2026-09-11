"""Blocks B, B', C and D: four figures, plus the cross-block summary.

Block A has its own script; this covers the rest of the night's runs. All of them
share the layout that worked there -- traffic, residual CO2, and the two mandates --
so the blocks can be read against one another.

Colour follows the job the variable does. Blocks B, B' and D vary a parameter *around*
a baseline, which is a diverging encoding: warm for tighter than baseline, cool for
looser, and the baseline itself neutral. Block C is a two-point contrast and takes two
categorical hues. Within blocks B and B', the rate and volume families are separated
by line style rather than by hue, so the diverging order stays readable across both.

Usage:  poetry run python plot_sensitivities.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

YEARS = list(range(2000, 2051))
SPAN = slice(2020, 2050)
PROSPECTION_START_YEAR = 2020  # the year the objective discounts to
INK, MUTED, GRID = "#1a1a1a", "#6b6b6b", "#e2e2e2"

# Diverging around the baseline: tighter is warm, looser is cool, baseline neutral.
TIGHTER_2, TIGHTER_1 = "#b2182b", "#ef8a62"
NEUTRAL = "#4d4d4d"
LOOSER_1, LOOSER_2 = "#67a9cf", "#2166ac"


def outputs(run):
    return json.load(open(HERE / "results" / f"{run}.json"))["vector_outputs"]


def discount_rate(run):
    """The run's own ``social_discount_rate``, so Block D runs discount at their rate."""
    return json.load(open(HERE / "results" / f"{run}.json"))["float_inputs"]["social_discount_rate"]


def discount_factor(run):
    """1 / (1+r)^(t - 2020), the factor the objective applies, on the full year index."""
    rate = discount_rate(run)
    return pd.Series(
        [1.0 / (1.0 + rate) ** (year - PROSPECTION_START_YEAR) for year in YEARS], index=YEARS
    )


def series(run, key):
    vectors = outputs(run)
    return pd.Series(vectors[key], index=YEARS) if key in vectors else None


def realised_abatement_cost(run):
    """What the scenario pays per tonne it abates, year by year, on the objective's basis.

    Both halves are measured against the *same* counterfactual the objective uses: the
    last-historical-year technological level flown at the baseline traffic growth.

    * Numerator ``area_loss + total_airline_cost_increase`` -- exactly the pair that
      ``cumulative_total_surplus_loss`` sums, undiscounted and un-cumulated.
      ``total_airline_cost_increase`` is measured against
      ``total_cost_per_rpk[2019] * rpk_no_elasticity``, and ``area_loss`` integrates the
      demand curve from ``rpk`` up to ``rpk_no_elasticity``, so the reference state is
      "2019 unit cost, baseline traffic" for both terms.
    * Denominator ``co2_emissions_last_historical_year_technology_baseline3`` minus what
      the run emits. That series is ``rpk_reference`` (which is ``rpk_no_elasticity``,
      verified identical) at frozen 2019 energy-per-ASK, load factor and emission
      factor -- the emissions of that very same reference state.

    An earlier version differenced both halves against the run's matched fossil BAU
    instead. That is self-consistent too, but it answers a different question -- what the
    *mandate alone* costs, holding the efficiency and operational improvements fixed --
    and it is not the objective's basis. It also reported 261-366 EUR/tCO2 where this
    reads -253 to +8, because the fossil BAU already contains every non-fuel improvement
    and so credits the scenario with only 90 MtCO2 of 2050 abatement against this
    baseline's 204.

    The sign is informative rather than a defect: through most of the period the scenario
    is both cheaper and cleaner than a world that froze in 2019, so the cost per tonne is
    negative. It turns positive only once the mandate is carrying the abatement on its
    own.

    This is a realised average, not a marginal cost: the whole scenario divided by the
    whole abatement, so it is not comparable with the per-fuel figures in the Block C
    panel, which are marginal against fossil kerosene.
    """
    area = series(run, "area_loss")
    if area is None:  # the no-feedback formulation has no surplus term
        area = pd.Series(0.0, index=YEARS)
    cost = area + series(run, "total_airline_cost_increase")

    baseline = series(run, "co2_emissions_last_historical_year_technology_baseline3")
    emitted = series(run, "co2_emissions_passenger") + series(run, "co2_emissions_freight")
    abated = (baseline - emitted) * 1e6  # MtCO2 -> tCO2
    return cost / abated.where(abated > 0)


def _frame(axis):
    axis.grid(True, color=GRID, lw=0.7)
    axis.set_axisbelow(True)
    for side in ("top", "right"):
        axis.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axis.spines[side].set_color(MUTED)
    axis.tick_params(colors=MUTED, labelsize=9)


PANELS = [
    ("a. Air traffic", "RPK  [trillion pkm]"),
    ("b. Residual CO2 emissions", "annual  [MtCO2]"),
    ("c. Cost per tonne of CO2 abated", "EUR/tCO2 vs frozen-2019 baseline"),
    ("d. Biofuel mandate", "share of drop-in blend  [%]"),
    ("e. Electrofuel mandate", "share of drop-in blend  [%]"),
    ("f. Alternative fuel consumed", "biofuel + electrofuel  [EJ/yr]"),
]


def six_panels(cases, title, subtitle, legend_title, stem, annotate=None, ncol=5):
    """cases: (label, run, colour, linestyle, width). Returns the axes grid.

    The same six panels for every block, so the blocks can be read against each other:
    what happened to traffic and emissions, what it cost per tonne, and the two mandates
    plus the physical volume they imply.
    """
    figure, axes = plt.subplots(2, 3, figsize=(15.5, 8.0), sharex=True)
    for axis in axes.ravel():
        _frame(axis)
    (traffic, emissions, mac), (biofuel, electrofuel, volume) = axes

    for label, run, colour, style, width in cases:
        kwargs = dict(color=colour, lw=width, ls=style)
        rpk = series(run, "rpk").loc[SPAN]
        traffic.plot(rpk.index, rpk / 1e12, **kwargs)

        co2 = (series(run, "co2_emissions_passenger") + series(run, "co2_emissions_freight")).loc[
            SPAN
        ]
        emissions.plot(co2.index, co2, **kwargs)

        cost = realised_abatement_cost(run).loc[SPAN]
        mac.plot(cost.index, cost, **kwargs)

        for axis, key in [
            (biofuel, "generic_biofuel_mandate_share"),
            (electrofuel, "generic_electrofuel_mandate_share"),
        ]:
            data = series(run, key).loc[SPAN]
            axis.plot(data.index, data, **kwargs)

        aaf = (
            series(run, "generic_biofuel_energy_consumption")
            + series(run, "generic_electrofuel_energy_consumption")
        ).loc[SPAN]
        volume.plot(aaf.index, aaf / 1e12, **kwargs)

    if annotate:
        annotate(axes)

    for axis, (panel_title, ylabel) in zip(axes.ravel(), PANELS):
        axis.set_title(panel_title, loc="left", fontsize=10.5, color=INK, pad=8)
        axis.set_ylabel(ylabel, fontsize=9, color=MUTED)

    handles = [Line2D([], [], color=c, lw=w, ls=s, label=name) for name, _, c, s, w in cases]
    figure.legend(
        handles=handles,
        title=legend_title,
        loc="lower center",
        ncol=ncol,
        frameon=False,
        fontsize=9,
        title_fontsize=9,
        bbox_to_anchor=(0.5, -0.005),
    )
    figure.suptitle(title, x=0.006, ha="left", fontsize=13, color=INK)
    figure.text(0.006, 0.935, subtitle, ha="left", fontsize=9, color=MUTED)
    figure.tight_layout(rect=(0, 0.05, 1, 0.925))
    for suffix in ("png", "pdf"):
        figure.savefig(HERE / f"{stem}.{suffix}", dpi=200, bbox_inches="tight")
    print(f"wrote {stem}.png / .pdf")
    return axes


# --------------------------------------------------------------------------- #


def ramp_up():
    cases = [
        ("volume 0.1 EJ/yr", "vol_0_1", TIGHTER_2, (0, (5, 2)), 1.8),
        ("rate 11.8 %/yr", "rate_11_8", TIGHTER_1, "-", 1.8),
        ("baseline: 20 %/yr, 0.2 EJ/yr", "base", NEUTRAL, "-", 2.4),
        ("rate 39 %/yr", "rate_39", LOOSER_1, "-", 1.8),
        ("volume 0.4 EJ/yr", "vol_0_4", LOOSER_2, (0, (5, 2)), 1.8),
    ]

    def notes(axes):
        (_, _, mac), (biofuel, electrofuel, _) = axes
        electrofuel.annotate(
            "a tighter ramp cannot abate early,\nso it must end higher:\n29.6 % against 13.5 %",
            xy=(2050, 29.0),
            xytext=(2022, 0.72),
            textcoords=("data", "axes fraction"),
            fontsize=8.5,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )
        biofuel.annotate(
            "biomass still caps biofuel\nin every variant",
            xy=(2046, 40.5),
            xytext=(2022, 0.78),
            textcoords=("data", "axes fraction"),
            fontsize=8.5,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )

    six_panels(
        cases,
        "Industrial ramp-up limits set the mandate, not the carbon budget",
        "Blocks B and B'. Case main, eps -0.9, biomass 10 %, same 3.8656 GtCO2 budget. "
        "Rate variants solid, volume variants dashed; warm is tighter than baseline, cool looser.",
        "ramp-up limit",
        "fig_rampup_panels",
        annotate=notes,
    )


def abatement_cost(run, pathway_name, discounted=True):
    """EUR per tCO2 abated against fossil kerosene, year by year, discounted to 2020.

    (MFSP_fuel - MFSP_kerosene) / (EF_kerosene - EF_fuel), in EUR/MJ over gCO2/MJ,
    scaled to EUR/tCO2. Both pathways carry zero resource cost and zero resource
    emissions in this configuration, so the "without_resource" series are the totals.

    The numerator is discounted at the run's own ``social_discount_rate`` and the tonnes
    are not, which is exactly the trade-off the optimiser faces: the objective is a
    *discounted* sum of costs, while G1 caps an *undiscounted* cumulative sum of
    emissions. A tonne abated in 2050 relieves the budget by the same amount as a tonne
    abated in 2030, but the euros that buy it are worth 1/(1.045)^30 = 0.27 of a 2030
    euro. Undiscounted, this panel says electrofuel is dearer than biofuel in every year
    and the schedule looks arbitrary; discounted, the two curves are directly rankable
    and cheap-but-late competes with dear-but-early on the optimiser's own terms.

    Where the denominator is not positive the fuel abates nothing -- it emits at or
    above kerosene -- and no cost per tonne exists. Those years come back as NaN and
    break the line rather than being drawn as a huge or negative number.
    """
    fuel_price = series(run, f"{pathway_name}_mean_mfsp_without_resource")
    fuel_factor = series(run, f"{pathway_name}_mean_co2_emission_factor_without_resource")
    kerosene_price = series(run, "fossil_kerosene_mean_mfsp_without_resource")
    kerosene_factor = series(run, "fossil_kerosene_mean_co2_emission_factor_without_resource")

    abated = kerosene_factor - fuel_factor  # gCO2 per MJ
    premium = fuel_price - kerosene_price  # EUR per MJ
    cost = (premium / abated.where(abated > 0)) * 1e6
    return cost * discount_factor(run) if discounted else cost


def pathway():
    """Block C: the inputs that were swapped, what they cost per tonne, and the output.

    Panels (a) and (b) are the swapped inputs, (c) turns them into an abatement cost,
    and the bottom row is what the optimiser did with them. Putting the three side by
    side is the argument: the pathway is transformed, its abatement cost falls by 40 % or
    more, and the optimiser defers early biofuel to buy the abatement back with it later.
    """
    figure, axes = plt.subplots(2, 3, figsize=(15.5, 8.0))
    for axis in axes.ravel():
        _frame(axis)
    (factor, price, mac), (electrofuel, consumed, biofuel) = axes

    cases = [
        ("baseline (grid electricity)", "base", NEUTRAL, "-", 2.2),
        ("dedicated wind, no electricity limit", "efuel_wind", "#1b7837", "-", 2.2),
    ]

    for label, run, colour, style, width in cases:
        kwargs = dict(color=colour, lw=width, ls=style)
        ef = series(run, "generic_electrofuel_mean_co2_emission_factor_without_resource")
        factor.plot(ef.loc[SPAN].index, ef.loc[SPAN], **kwargs)
        mfsp = series(run, "generic_electrofuel_mean_mfsp_without_resource")
        price.plot(mfsp.loc[SPAN].index, mfsp.loc[SPAN] * 1000, **kwargs)
        cost = abatement_cost(run, "generic_electrofuel").loc[SPAN]
        mac.plot(cost.index, cost, **kwargs)
        mandate = series(run, "generic_electrofuel_mandate_share").loc[SPAN]
        electrofuel.plot(mandate.index, mandate, **kwargs)
        energy = series(run, "generic_electrofuel_energy_consumption").loc[SPAN]
        consumed.plot(energy.index, energy / 1e12, **kwargs)
        bio = series(run, "generic_biofuel_mandate_share").loc[SPAN]
        biofuel.plot(bio.index, bio, **kwargs)

    # The biofuel *cost* curve is identical in both runs -- same MFSP, same emission
    # factor, verified -- so one line serves for both. What the two runs do with it is
    # not identical at all: see panel (f). Discounted, biofuel also competes with itself
    # at every other date, which is why the dotted line slopes.
    biofuel_mac = abatement_cost("base", "generic_biofuel").loc[SPAN]
    mac.plot(biofuel_mac.index, biofuel_mac, color="#8c510a", lw=2.0, ls=(0, (1, 1.4)))

    kerosene = series("base", "fossil_kerosene_mean_co2_emission_factor_without_resource")
    factor.axhline(kerosene.loc[2050], color=MUTED, lw=1.0, ls=(0, (4, 3)))
    factor.annotate("fossil kerosene, 88.7", xy=(2029, 95), fontsize=8.5, color=MUTED)
    factor.set_yscale("log")

    biofuel_price = series("base", "generic_biofuel_mean_mfsp_without_resource")
    price.axhline(biofuel_price.loc[2050] * 1000, color=MUTED, lw=1.0, ls=(0, (4, 3)))
    price.annotate("biofuel, 37.4", xy=(2022, 39.5), fontsize=8.5, color=MUTED)

    # The year the baseline pathway starts abating anything at all.
    baseline_ef = series("base", "generic_electrofuel_mean_co2_emission_factor_without_resource")
    first = next(y for y in range(2020, 2051) if baseline_ef.loc[y] < kerosene.loc[y])
    mac.axvline(first, color=MUTED, lw=0.9, ls=":")
    mac.annotate(
        f"baseline electrofuel abates\nnothing before {first}: it emits\nmore than the kerosene it replaces",
        xy=(first, 0.55),
        xytext=(2031.5, 0.79),
        textcoords=("data", "axes fraction"),
        fontsize=8.5,
        color=MUTED,
    )
    mac.annotate(
        "biofuel",
        xy=(2033, biofuel_mac.loc[2033]),
        xytext=(2032, 0.06),
        textcoords=("data", "axes fraction"),
        fontsize=9,
        color="#8c510a",
    )
    # Discounted, the interesting comparison is across dates, not within one: biofuel is
    # flat at 380 EUR/tCO2 undiscounted, so its discounted curve decays, and the question
    # is whether late electrofuel undercuts early biofuel. Clip to the band where that is
    # legible; the first electrofuel years run off the top and are covered by the note.
    mac.set_ylim(0, 1200)

    for axis, panel_title, ylabel in [
        (factor, "a. INPUT: electrofuel emission factor", "gCO2/MJ  [log scale]"),
        (price, "b. INPUT: electrofuel production cost", "EUR/GJ"),
        (
            mac,
            "c. Discounted cost per tonne of CO2 abated",
            "EUR(2020)/tCO2 vs fossil kerosene",
        ),
        (electrofuel, "d. OUTPUT: electrofuel mandate", "share of drop-in blend  [%]"),
        (consumed, "e. OUTPUT: electrofuel consumed", "EJ/yr"),
        (biofuel, "f. OUTPUT: biofuel mandate", "share of drop-in blend  [%]"),
    ]:
        axis.set_title(panel_title, loc="left", fontsize=10.5, color=INK, pad=8)
        axis.set_ylabel(ylabel, fontsize=9, color=MUTED)

    handles = [Line2D([], [], color=c, lw=w, ls=s, label=name) for name, _, c, s, w in cases]
    handles.append(
        Line2D(
            [],
            [],
            color="#8c510a",
            lw=2.0,
            ls=(0, (1, 1.4)),
            label="biofuel (same cost curve in both runs)",
        )
    )
    figure.legend(
        handles=handles,
        title="pathway",
        loc="lower center",
        ncol=3,
        frameon=False,
        fontsize=9,
        title_fontsize=9,
        bbox_to_anchor=(0.5, -0.005),
    )
    figure.suptitle(
        "Dedicated-wind electrofuel cuts the abatement cost by 40 % or more, and the "
        "optimiser rebuilds the schedule around it",
        x=0.006,
        ha="left",
        fontsize=13,
        color=INK,
    )
    figure.text(
        0.006,
        0.935,
        "Block C. Both input trajectories are swapped and G4, the shared electricity "
        "allocation, is dropped entirely rather than relaxed. Electrofuel reaches 49 % of "
        "the blend against 14 %, and early biofuel is held back to pay for it.",
        ha="left",
        fontsize=9,
        color=MUTED,
    )
    figure.tight_layout(rect=(0, 0.055, 1, 0.925))
    for suffix in ("png", "pdf"):
        figure.savefig(HERE / f"fig_pathway_panels.{suffix}", dpi=200, bbox_inches="tight")
    print("wrote fig_pathway_panels.png / .pdf")


def discount():
    cases = [
        ("3.2 %", "r_3_2", TIGHTER_1, "-", 3.4),
        ("4.5 % (baseline)", "base", NEUTRAL, (0, (4, 2)), 2.0),
        ("7 %", "r_7", LOOSER_1, "-", 2.0),
        ("15 % (extreme)", "r_15", LOOSER_2, "-", 2.2),
    ]

    def notes(axes):
        (_, _, mac), (_, electrofuel, _) = axes
        electrofuel.annotate(
            "3.2 % and 4.5 % are the *same design*:\nthe optimum sits on a vertex of the feasible\n"
            "set and the objective only picks which vertex",
            xy=(2047, 12.0),
            xytext=(2021.5, 0.72),
            textcoords=("data", "axes fraction"),
            fontsize=8.5,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )
        electrofuel.annotate(
            "at 15 % the vertex breaks: 2050 costs are\ndiscounted by 66x, so abatement is deferred\n"
            "wholesale to a nearly synthetic 2050 blend",
            xy=(2050, 46.0),
            xytext=(2021.5, 0.44),
            textcoords=("data", "axes fraction"),
            fontsize=8.5,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )

    six_panels(
        cases,
        "Discount rate: mechanical between 3.2 and 7 %, decisive at 15 %",
        "Block D. The 3.2 % line is drawn heavier with the baseline dashed over it, because "
        "the two designs are identical to every digit.",
        "social discount rate",
        "fig_discount_panels",
        annotate=notes,
        ncol=4,
    )


# Named tests, grouped by the parameter they vary. The block letters of the brief are
# an index, not a label -- a reader should not have to hold "B'" in their head to know
# they are looking at a ramp-up volume.
GROUPS = [
    (
        "Price elasticity",
        "#2166ac",
        [
            ("fixed_demand", "fixed demand"),
            ("eps_m0_6", "-0.6"),
            ("eps_m0_8", "-0.8"),
            ("base", "-0.9  BASELINE"),
            ("eps_m1_0", "-1.0"),
            ("eps_m1_4", "-1.4"),
        ],
    ),
    (
        "Ramp-up rate",
        "#b2182b",
        [
            ("rate_11_8", "11.8 %/yr  (IEA NZE)"),
            ("rate_39", "39 %/yr  (wind/PV)"),
        ],
    ),
    (
        "Ramp-up volume",
        "#ef8a62",
        [
            ("vol_0_1", "0.1 EJ/yr"),
            ("vol_0_4", "0.4 EJ/yr"),
        ],
    ),
    (
        "Electrofuel pathway",
        "#1b7837",
        [
            ("efuel_wind", "dedicated wind"),
        ],
    ),
    (
        "Discount rate",
        "#8c6d31",
        [
            ("r_3_2", "3.2 %"),
            ("r_7", "7 %"),
            ("r_15", "15 %  (extreme)"),
        ],
    ),
]


def summary():
    frame = pd.read_csv(HERE / "sweep_summary.csv").set_index("run")

    # Lay the rows out with a header row per group. Rotated labels in the margin were
    # the first attempt and they collide: a one-row group has no vertical room for its
    # own name. A header row costs one slot and reads at a glance.
    rows, ticks, labels, styles, separators = [], [], [], [], []
    y = 0.0
    for index, (group, colour, members) in enumerate(GROUPS):
        if index:
            separators.append(y - 0.5)
            y += 0.6
        ticks.append(y)
        labels.append(group.upper())
        styles.append((colour, "bold", 8.5))
        y += 1.0
        for run, label in members:
            if run not in frame.index:
                continue
            rows.append((y, run, label, colour, group))
            ticks.append(y)
            labels.append(f"   {label}")
            styles.append((INK if run != "base" else colour, "normal", 9))
            y += 1.0

    figure, axes = plt.subplots(1, 3, figsize=(13.5, 6.4), sharey=True)
    metrics = [
        ("aaf_share_2050", "2050 AAF mandate  [% of blend]", "a. Required alternative fuel"),
        ("policy_cost_bnEUR", "vs matched fossil BAU  [bn EUR]", "b. Policy cost"),
        ("rpk_2050_Tpkm", "2050 RPK  [trillion pkm]", "c. Traffic"),
    ]
    for axis, (column, xlabel, title) in zip(axes, metrics):
        _frame(axis)
        axis.grid(axis="y", visible=False)
        baseline = frame.loc["base", column]
        axis.axvline(baseline, color=MUTED, lw=0.9, ls=":", zorder=0)
        for boundary in separators:
            axis.axhline(boundary, color=GRID, lw=1.0, zorder=0)
        for y, run, label, colour, group in rows:
            value = frame.loc[run, column]
            is_baseline = run == "base"
            axis.plot([baseline, value], [y, y], color=colour, lw=1.2, alpha=0.45, zorder=1)
            axis.plot(
                value,
                y,
                "o",
                color="white" if is_baseline else colour,
                ms=8,
                zorder=2,
                markeredgecolor=colour,
                markeredgewidth=2.0 if is_baseline else 1.4,
            )
        axis.set_xlabel(xlabel, fontsize=9, color=MUTED)
        axis.set_title(title, loc="left", fontsize=11, color=INK, pad=8)

    axes[0].set_yticks(ticks)
    axes[0].set_yticklabels(labels)
    for text, (colour, weight, size) in zip(axes[0].get_yticklabels(), styles):
        text.set_color(colour)
        text.set_fontweight(weight)
        text.set_fontsize(size)
    axes[0].invert_yaxis()

    figure.suptitle(
        "What each sensitivity moves, against the baseline",
        x=0.006,
        ha="left",
        fontsize=13,
        color=INK,
    )
    figure.text(
        0.006,
        0.930,
        "Fourteen optimisations, all meeting the same 3.8656 GtCO2 budget. Dotted line "
        "and hollow marker are the baseline; policy cost is measured against a fossil "
        "BAU run sharing the run's elasticity and discount rate.",
        ha="left",
        fontsize=9,
        color=MUTED,
    )
    figure.tight_layout(rect=(0, 0.01, 1, 0.905))
    for suffix in ("png", "pdf"):
        figure.savefig(HERE / f"fig_sensitivity_summary.{suffix}", dpi=200, bbox_inches="tight")
    print("wrote fig_sensitivity_summary.png / .pdf")


if __name__ == "__main__":
    ramp_up()
    pathway()
    discount()
    summary()

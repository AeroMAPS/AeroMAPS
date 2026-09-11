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
# Every time axis starts in 2019: the last historical year, and the state the objective,
# the airfare anchor and the frozen-2019 emissions baseline are all measured against.
# Starting in 2020 would open every panel on the COVID year instead.
SPAN = slice(2019, 2050)
YEAR_TICKS = [2019, 2025, 2030, 2035, 2040, 2045, 2050]
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


def alternative_fuel(run, key):
    """A mandate share or alternative-fuel volume, with 2019 at zero.

    The model computes these only over the prospective period, so 2019 comes back NaN
    and the line would start a year after every other panel. Zero is not an assumption:
    there was no mandate in 2019, and the model's own 2020 value is zero.
    """
    data = series(run, key).copy()
    if pd.isna(data.loc[2019]):
        data.loc[2019] = 0.0
    return data


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
    ("g. Airfare", "EUR cents per RPK"),
    ("h. Direct operating cost", "EUR cents per ASK"),
    ("i. Energy direct operating cost", "EUR cents per ASK"),
]

# The airfare the demand curve, the supply curve and the surplus are all anchored on --
# optimisation_runs.initial_airfare_per_rpk, in euro cents.
AIRFARE_ANCHOR_CENTS = 9.236379319842411

# What the cost row plots, in euro cents. Airfare is per RPK and the two DOCs per ASK, as
# the model computes them; energy DOC is one component of DOC, alongside the non-energy
# DOC and the carbon tax.
COST_ROW = [
    "airfare_per_rpk",
    "doc_total_per_ask_mean",
    "doc_energy_per_ask_mean",
]


def _cost_row(row, cases):
    """Airfare, DOC and energy DOC for every case, on three axes, in euro cents.

    Each axis is scaled to 2023-2050. 2020 is the COVID year -- load factor collapsed, so
    every cost per seat or per passenger jumps -- and it is identical in every case, so on
    an axis that includes it the part that differs between cases is a sliver. The 2020
    value is written at the top edge where it leaves the axis rather than dropped.
    """
    for axis, key in zip(row, COST_ROW):
        shown = []
        for _, run, colour, style, width in cases:
            data = series(run, key).loc[SPAN] * 100  # EUR -> euro cents
            axis.plot(data.index, data, color=colour, lw=width, ls=style)
            shown.append(data)
        tail = pd.concat([data.loc[2023:] for data in shown])
        low, high = tail.min(), tail.max()
        if key == "airfare_per_rpk":
            low, high = min(low, AIRFARE_ANCHOR_CENTS), max(high, AIRFARE_ANCHOR_CENTS)
        pad = 0.08 * (high - low)
        axis.set_ylim(low - pad, high + pad)
        covid = shown[0].loc[2020]
        if covid > high + pad:
            axis.annotate(
                f"2020 (COVID): {covid:.2f}, off scale",
                xy=(2020, high + pad),
                xytext=(4, -4),
                textcoords="offset points",
                va="top",
                fontsize=8,
                color=MUTED,
            )

    airfare = row[0]
    airfare.axhline(AIRFARE_ANCHOR_CENTS, color=MUTED, lw=0.9, ls=":", zorder=0)
    airfare.annotate(
        "2019 anchor",
        xy=(2050, AIRFARE_ANCHOR_CENTS),
        xytext=(0, -3),
        textcoords="offset points",
        ha="right",
        va="top",
        fontsize=8,
        color=MUTED,
    )


def sensitivity_panels(cases, title, subtitle, legend_title, stem, annotate=None, ncol=5):
    """cases: (label, run, colour, linestyle, width). Returns the 3 x 3 axes grid.

    The same nine panels for every block, so the blocks can be read against each other:
    what happened to traffic and emissions, what it cost per tonne, the two mandates plus
    the physical volume they imply, and what passengers and airlines pay for it -- the
    airfare, the direct operating cost, and the energy part of that cost.
    """
    figure, axes = plt.subplots(3, 3, figsize=(15.5, 11.5), sharex=True)
    for axis in axes.ravel():
        _frame(axis)
    (traffic, emissions, mac), (biofuel, electrofuel, volume), cost_row = axes

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
            data = alternative_fuel(run, key).loc[SPAN]
            axis.plot(data.index, data, **kwargs)

        aaf = (
            alternative_fuel(run, "generic_biofuel_energy_consumption")
            + alternative_fuel(run, "generic_electrofuel_energy_consumption")
        ).loc[SPAN]
        volume.plot(aaf.index, aaf / 1e12, **kwargs)

    _cost_row(cost_row, cases)
    for axis in axes.ravel():
        axis.set_xticks(YEAR_TICKS)

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
    # Same offsets in inches as the two-row layout had, on a taller figure.
    figure.text(0.006, 0.955, subtitle, ha="left", fontsize=9, color=MUTED)
    figure.tight_layout(rect=(0, 0.035, 1, 0.948))
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
        (_, _, mac), (biofuel, electrofuel, _), _ = axes
        electrofuel.annotate(
            "a tighter ramp cannot abate early,\nso it must end higher:\n22.4 % against 13.5 %",
            xy=(2050, 22.0),
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

    sensitivity_panels(
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
    figure, axes = plt.subplots(3, 3, figsize=(15.5, 11.5))
    for axis in axes.ravel():
        _frame(axis)
    (factor, price, mac), (electrofuel, consumed, biofuel), cost_row = axes

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
        mandate = alternative_fuel(run, "generic_electrofuel_mandate_share").loc[SPAN]
        electrofuel.plot(mandate.index, mandate, **kwargs)
        energy = alternative_fuel(run, "generic_electrofuel_energy_consumption").loc[SPAN]
        consumed.plot(energy.index, energy / 1e12, **kwargs)
        bio = alternative_fuel(run, "generic_biofuel_mandate_share").loc[SPAN]
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
    _cost_row(cost_row, cases)
    for axis in axes.ravel():
        axis.set_xticks(YEAR_TICKS)

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
        *[(axis, *panel) for axis, panel in zip(cost_row, PANELS[6:])],
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
        0.955,
        "Block C. Both input trajectories are swapped and G4, the shared electricity "
        "allocation, is dropped entirely rather than relaxed. Electrofuel reaches 49 % of "
        "the blend against 14 %, and early biofuel is held back to pay for it.",
        ha="left",
        fontsize=9,
        color=MUTED,
    )
    figure.tight_layout(rect=(0, 0.038, 1, 0.948))
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
        (_, _, mac), (_, electrofuel, _), _ = axes
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

    sensitivity_panels(
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
# --------------------------------------------------------------------------- #
# The summary: every sensitivity, blocks A-E, against one baseline
# --------------------------------------------------------------------------- #

# Each row names its JSON relative to this folder, because the rows come from two
# places: blocks A-D in results/, and the carbon-budget ladder, the other cases at the
# central budget and the fossil BAU in results_e/.
BASELINE_ROW = ("results/base.json", "ReFuelEU budget, 10 % biomass, eps -0.9, r 4.5 %")

SUMMARY_GROUPS = [
    (
        "Reference",
        INK,
        [("results_e/fossil_main.json", "fossil BAU, no mandate")],
    ),
    (
        "Carbon budget  (% of world budget)",
        "#762a83",
        [
            ("results_e/opt_main_3_8.json", "3.8 %"),
            ("results_e/opt_main_3_4.json", "3.4 %"),
            ("results_e/opt_main_3_0.json", "3.0 %"),
            ("results_e/opt_main_2_6.json", "2.6 %"),
            ("results_e/opt_main_2_2.json", "2.2 %"),
        ],
    ),
    (
        "Biomass allocated to aviation",
        "#35978f",
        [
            ("results_e/opt_B5_refueleu.json", "5 %"),
            ("results_e/opt_B75_refueleu.json", "7.5 %"),
            ("results_e/opt_B15_refueleu.json", "15 %"),
        ],
    ),
    (
        "Technology",
        "#5e5e5e",
        [("results_e/opt_pess_refueleu.json", "efficiency gain 0.91 %/yr")],
    ),
    (
        "Price elasticity",
        "#2166ac",
        [
            ("results/fixed_demand.json", "fixed demand"),
            ("results/eps_m0_6.json", "-0.6"),
            ("results/eps_m0_8.json", "-0.8"),
            ("results/eps_m1_0.json", "-1.0"),
            ("results/eps_m1_4.json", "-1.4"),
        ],
    ),
    (
        "Ramp-up rate",
        "#b2182b",
        [
            ("results/rate_11_8.json", "11.8 %/yr  (IEA NZE)"),
            ("results/rate_39.json", "39 %/yr  (wind/PV)"),
        ],
    ),
    (
        "Ramp-up volume",
        "#ef8a62",
        [
            ("results/vol_0_1.json", "0.1 EJ/yr"),
            ("results/vol_0_4.json", "0.4 EJ/yr"),
        ],
    ),
    (
        "Electrofuel pathway",
        "#1b7837",
        [("results/efuel_wind.json", "dedicated wind")],
    ),
    (
        "Discount rate",
        "#8c6d31",
        [
            ("results/r_3_2.json", "3.2 %  †"),
            ("results/r_7.json", "7 %  †"),
            ("results/r_15.json", "15 %  (extreme)  †"),
        ],
    ),
]


def _surplus_loss(vectors):
    """The objective, cumulative discounted total surplus loss to 2050, in bn EUR.

    The fixed-demand run uses the no-feedback chain, which does not report it. Its
    equivalent is exact rather than approximate: the model sums discounted area_loss
    plus the 2026-2050 discounted airline cost increase, and with traffic equal to the
    reference traffic area_loss is identically zero. The reconstruction matches the
    reported value to six decimals on the elastic runs.
    """
    if "cumulative_total_surplus_loss_discounted" in vectors:
        return vectors["cumulative_total_surplus_loss_discounted"][-1] / 1e9
    airline = vectors["cumulative_total_airline_cost_increase_discounted"]
    return (airline[YEARS.index(2050)] - airline[YEARS.index(2025)]) / 1e9


SUMMARY_METRICS = [
    ("a. Cumulative surplus loss", "discounted, 2020-2050  [bn EUR]", _surplus_loss),
    (
        "b. Cumulative CO2 emissions",
        "2020-2050  [GtCO2]",
        lambda v: v["cumulative_co2_emissions"][YEARS.index(2050)],
    ),
    (
        "c. CO2 emissions in 2050",
        "[MtCO2/yr]",
        lambda v: v["co2_emissions_passenger"][-1] + v["co2_emissions_freight"][-1],
    ),
    ("d. Traffic in 2050", "[trillion RPK]", lambda v: v["rpk"][-1] / 1e12),
    (
        "e. Biofuel mandate, 2035",
        "[% of drop-in blend]",
        lambda v: v["generic_biofuel_mandate_share"][YEARS.index(2035)],
    ),
    (
        "f. Biofuel mandate, 2050",
        "[% of drop-in blend]",
        lambda v: v["generic_biofuel_mandate_share"][-1],
    ),
    (
        "g. Electrofuel mandate, 2035",
        "[% of drop-in blend]",
        lambda v: v["generic_electrofuel_mandate_share"][YEARS.index(2035)],
    ),
    (
        "h. Electrofuel mandate, 2050",
        "[% of drop-in blend]",
        lambda v: v["generic_electrofuel_mandate_share"][-1],
    ),
]
MANDATE_PANELS = slice(4, 8)  # drawn on one shared scale, so the four read against each other


def _summary_row(path):
    """(metric values, status) for one row; status is 'ok', 'missing' or 'infeasible'.

    Feasibility is read from the optimisation history, not assumed from the JSON: an
    infeasible run still writes one, holding its last iterate, and that is not a result.
    A reference MDA has no history and no constraints to violate.
    """
    json_path = HERE / path
    if not json_path.exists():
        return None, "missing"
    hdf = json_path.with_suffix(".hdf")
    if hdf.exists():
        sys.path.insert(0, str(HERE.parent))
        import optimisation_runs as R

        run = R.read_run(hdf)
        if run is None or not run["feasible"]:
            return None, "infeasible"
    vectors = json.load(open(json_path))["vector_outputs"]
    return [metric(vectors) for _, _, metric in SUMMARY_METRICS], "ok"


def summary():
    """Every sensitivity against one baseline, on eight quantities.

    Blocks A-D vary one parameter at the ReFuelEU-equivalent budget. The carbon-budget
    group is block E's main ladder; the biomass and technology groups are the other
    block E cases re-optimised at that same central budget, so every group except the
    carbon budget shares the baseline's cumulative emissions.
    """
    baseline, _ = _summary_row(BASELINE_ROW[0])

    rows, ticks, labels, styles, separators = [], [], [], [], []
    y = 0.0
    ticks.append(y)
    labels.append(f"BASELINE   {BASELINE_ROW[1]}")
    styles.append((INK, "bold", 8.5))
    rows.append((y, baseline, NEUTRAL, True))
    y += 1.0
    for group, colour, members in SUMMARY_GROUPS:
        separators.append(y - 0.5)
        y += 0.6
        ticks.append(y)
        labels.append(group.upper())
        styles.append((colour, "bold", 8.5))
        y += 1.0
        for path, label in members:
            values, status = _summary_row(path)
            note = {"ok": "", "missing": "   (not on disk)", "infeasible": "   (infeasible)"}
            ticks.append(y)
            labels.append(f"   {label}{note[status]}")
            styles.append((INK if status == "ok" else MUTED, "normal", 9))
            if values is not None:
                rows.append((y, values, colour, False))
            y += 1.0

    figure, axes = plt.subplots(2, 4, figsize=(18.0, 17.0), sharey=True)
    flat = axes.ravel()
    mandate_top = max(max(values[i] for _, values, _, _ in rows) for i in range(8)[MANDATE_PANELS])
    for index, (axis, (title, xlabel, _)) in enumerate(zip(flat, SUMMARY_METRICS)):
        _frame(axis)
        axis.grid(axis="y", visible=False)
        axis.axvline(baseline[index], color=MUTED, lw=0.9, ls=":", zorder=0)
        for boundary in separators:
            axis.axhline(boundary, color=GRID, lw=1.0, zorder=0)
        for y, values, colour, is_baseline in rows:
            value = values[index]
            axis.plot([baseline[index], value], [y, y], color=colour, lw=1.2, alpha=0.45)
            axis.plot(
                value,
                y,
                "o",
                color="white" if is_baseline else colour,
                ms=7,
                zorder=2,
                markeredgecolor=colour,
                markeredgewidth=2.0 if is_baseline else 1.3,
            )
        if index in range(8)[MANDATE_PANELS]:
            axis.set_xlim(-2, mandate_top * 1.06)
        axis.set_xlabel(xlabel, fontsize=9, color=MUTED)
        axis.set_title(title, loc="left", fontsize=11, color=INK, pad=8)

    for axis in axes[:, 0]:
        axis.set_yticks(ticks)
        axis.set_yticklabels(labels)
        for text, (colour, weight, size) in zip(axis.get_yticklabels(), styles):
            text.set_color(colour)
            text.set_fontweight(weight)
            text.set_fontsize(size)
    axes[0, 0].invert_yaxis()

    figure.suptitle(
        "Every sensitivity against one baseline",
        x=0.006,
        ha="left",
        fontsize=14,
        color=INK,
    )
    figure.text(
        0.006,
        0.968,
        "Every optimisation outside the carbon-budget group is held to the ReFuelEU-equivalent "
        "budget, 3.8656 GtCO2 over 2020-2050, which is why panel b is a single line for them. "
        "Dotted line and hollow marker: the baseline.\n"
        "Panel a is the objective, discounted to 2020 at each run's own rate; the runs marked "
        "† use a different rate, so their level is not comparable with the rest.",
        ha="left",
        va="top",
        fontsize=9,
        color=MUTED,
    )
    figure.tight_layout(rect=(0, 0.0, 1, 0.945))
    for suffix in ("png", "pdf"):
        figure.savefig(HERE / f"fig_sensitivity_summary.{suffix}", dpi=200, bbox_inches="tight")
    print("wrote fig_sensitivity_summary.png / .pdf")


if __name__ == "__main__":
    ramp_up()
    pathway()
    discount()
    summary()

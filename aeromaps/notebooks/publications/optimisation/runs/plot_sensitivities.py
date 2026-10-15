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

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

HERE = Path(__file__).resolve().parent
FIGURES = HERE.parent / "figures"  # every figure of the paper, beside 02_results' own
FIGURES.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from helpers import dataset as D  # noqa: E402
from helpers import paper_style as style  # noqa: E402

# The paper's house style, so these figures match the notebook's whether they are drawn
# from it or from the command line.
style.apply()

YEARS = list(range(2000, 2051))
# Every time axis starts in 2019: the last historical year, and the state the objective,
# the airfare anchor and the frozen-2019 emissions baseline are all measured against.
# Starting in 2020 would open every panel on the COVID year instead.
SPAN = slice(2019, 2050)
YEAR_TICKS = [2019, 2025, 2030, 2035, 2040, 2045, 2050]
PROSPECTION_START_YEAR = 2020  # the year the objective discounts to
INK, MUTED, GRID = style.INK, style.MUTED, style.GRID

# Diverging around the baseline: tighter is warm, looser is cool, baseline neutral.
TIGHTER_2, TIGHTER_1 = style.RED, style.RED_LIGHT
NEUTRAL = style.NEUTRAL
LOOSER_1, LOOSER_2 = style.NAVY_LIGHT, style.NAVY


def outputs(run):
    return D.outputs(run)


def discount_rate(run):
    """The run's own ``social_discount_rate``, so Block D runs discount at their rate."""
    return D.discount_rate(run)


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


def _frame(axis, grid="y"):
    style.tidy(axis, grid=grid)


PANELS = [
    ("a. Traffic", "Traffic (trillion RPK)"),
    ("b. Residual CO$_2$ emissions", "Emissions (MtCO$_2$/yr)"),
    ("c. Cost per tonne of CO$_2$ abated", "Cost vs frozen 2019 (€/tCO$_2$)"),
    ("d. Biofuel mandate", "Biofuel share (%)"),
    ("e. Electrofuel mandate", "Electrofuel share (%)"),
    ("f. Alternative fuel consumed", "Biofuel + electrofuel (EJ/yr)"),
    ("g. Airfare", "Airfare (€ cents/RPK)"),
    ("h. Direct operating cost", "Cost (€ cents/ASK)"),
    ("i. Energy direct operating cost", "Cost (€ cents/ASK)"),
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
        for _, run, colour, dash, width in cases:
            data = series(run, key).loc[SPAN] * 100  # EUR -> euro cents
            axis.plot(data.index, data, color=colour, lw=width, ls=dash)
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
                fontsize=style.SMALL_SIZE - 1,
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
        fontsize=style.SMALL_SIZE - 1,
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

    for label, run, colour, dash, width in cases:
        kwargs = dict(color=colour, lw=width, ls=dash)
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
        axis.set_title(panel_title)
        axis.set_ylabel(ylabel)

    handles = [Line2D([], [], color=c, lw=w, ls=s, label=name) for name, _, c, s, w in cases]
    figure.legend(
        handles=handles,
        title=legend_title,
        loc="lower center",
        ncol=ncol,
        frameon=False,
        bbox_to_anchor=(0.5, -0.005),
    )
    figure.suptitle(title, x=0.006, ha="left")
    # Same offsets in inches as the two-row layout had, on a taller figure.
    figure.text(0.006, 0.955, subtitle, ha="left", fontsize=style.SMALL_SIZE, color=MUTED)
    figure.tight_layout(rect=(0, 0.035, 1, 0.948))
    for suffix in ("png", "pdf"):
        figure.savefig(FIGURES / f"{stem}.{suffix}", dpi=200, bbox_inches="tight")
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
            fontsize=style.SMALL_SIZE,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )
        biofuel.annotate(
            "biomass still caps biofuel\nin every variant",
            xy=(2046, 40.5),
            xytext=(2022, 0.78),
            textcoords=("data", "axes fraction"),
            fontsize=style.SMALL_SIZE,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )

    sensitivity_panels(
        cases,
        "Industrial ramp-up limits set the mandate, not the carbon budget",
        "Blocks B and B'. Case main, eps -0.9, biomass 10 %, same 3.8656 GtCO2 budget. "
        "Rate variants solid, volume variants dashed; warm is tighter than baseline, cool looser.",
        "Ramp-up limit",
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
        ("dedicated wind, no electricity limit", "efuel_wind", style.TEAL, "-", 2.2),
    ]

    for label, run, colour, dash, width in cases:
        kwargs = dict(color=colour, lw=width, ls=dash)
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
    mac.plot(biofuel_mac.index, biofuel_mac, color=style.BIOFUEL, lw=2.0, ls=(0, (1, 1.4)))

    kerosene = series("base", "fossil_kerosene_mean_co2_emission_factor_without_resource")
    factor.axhline(kerosene.loc[2050], color=MUTED, lw=1.0, ls=(0, (4, 3)))
    factor.annotate("fossil kerosene, 88.7", xy=(2029, 95), fontsize=style.SMALL_SIZE, color=MUTED)
    factor.set_yscale("log")

    biofuel_price = series("base", "generic_biofuel_mean_mfsp_without_resource")
    price.axhline(biofuel_price.loc[2050] * 1000, color=MUTED, lw=1.0, ls=(0, (4, 3)))
    price.annotate("biofuel, 37.4", xy=(2022, 39.5), fontsize=style.SMALL_SIZE, color=MUTED)

    # The year the baseline pathway starts abating anything at all.
    baseline_ef = series("base", "generic_electrofuel_mean_co2_emission_factor_without_resource")
    first = next(y for y in range(2020, 2051) if baseline_ef.loc[y] < kerosene.loc[y])
    mac.axvline(first, color=MUTED, lw=0.9, ls=":")
    mac.annotate(
        f"baseline electrofuel abates\nnothing before {first}: it emits\nmore than the kerosene it replaces",
        xy=(first, 0.55),
        xytext=(2031.5, 0.79),
        textcoords=("data", "axes fraction"),
        fontsize=style.SMALL_SIZE,
        color=MUTED,
    )
    mac.annotate(
        "biofuel",
        xy=(2033, biofuel_mac.loc[2033]),
        xytext=(2032, 0.06),
        textcoords=("data", "axes fraction"),
        fontsize=style.SMALL_SIZE,
        color=style.BIOFUEL,
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
        (factor, "a. Input: electrofuel emission factor", "Emission factor (gCO$_2$/MJ, log)"),
        (price, "b. Input: electrofuel production cost", "Production cost (€/GJ)"),
        (
            mac,
            "c. Discounted cost per tonne of CO$_2$ abated",
            "Cost vs kerosene (€ 2020/tCO$_2$)",
        ),
        (electrofuel, "d. Output: electrofuel mandate", "Electrofuel share (%)"),
        (consumed, "e. Output: electrofuel consumed", "Consumption (EJ/yr)"),
        (biofuel, "f. Output: biofuel mandate", "Biofuel share (%)"),
        *[(axis, *panel) for axis, panel in zip(cost_row, PANELS[6:])],
    ]:
        axis.set_title(panel_title)
        axis.set_ylabel(ylabel)

    handles = [Line2D([], [], color=c, lw=w, ls=s, label=name) for name, _, c, s, w in cases]
    handles.append(
        Line2D(
            [],
            [],
            color=style.BIOFUEL,
            lw=2.0,
            ls=(0, (1, 1.4)),
            label="biofuel (same cost curve in both runs)",
        )
    )
    figure.legend(
        handles=handles,
        title="Pathway",
        loc="lower center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, -0.005),
    )
    figure.suptitle(
        "Dedicated-wind electrofuel cuts the abatement cost by 40 % or more, and the "
        "optimiser rebuilds the schedule around it",
        x=0.006,
        ha="left",
    )
    figure.text(
        0.006,
        0.955,
        "Block C. Both input trajectories are swapped and G4, the shared electricity "
        "allocation, is dropped entirely rather than relaxed. Electrofuel reaches 49 % of "
        "the blend against 14 %, and early biofuel is held back to pay for it.",
        ha="left",
        fontsize=style.SMALL_SIZE,
        color=MUTED,
    )
    figure.tight_layout(rect=(0, 0.038, 1, 0.948))
    for suffix in ("png", "pdf"):
        figure.savefig(FIGURES / f"fig_pathway_panels.{suffix}", dpi=200, bbox_inches="tight")
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
            fontsize=style.SMALL_SIZE,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )
        electrofuel.annotate(
            "at 15 % the vertex breaks: 2050 costs are\ndiscounted by 66x, so abatement is deferred\n"
            "wholesale to a nearly synthetic 2050 blend",
            xy=(2050, 46.0),
            xytext=(2021.5, 0.44),
            textcoords=("data", "axes fraction"),
            fontsize=style.SMALL_SIZE,
            color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8),
        )

    sensitivity_panels(
        cases,
        "Discount rate: mechanical between 3.2 and 7 %, decisive at 15 %",
        "Block D. The 3.2 % line is drawn heavier with the baseline dashed over it, because "
        "the two designs are identical to every digit.",
        "Social discount rate",
        "fig_discount_panels",
        annotate=notes,
        ncol=4,
    )


# Named tests, grouped by the parameter they vary. The block letters are an index, not
# a label -- a reader should not have to hold "B'" in their head to know
# they are looking at a ramp-up volume.
# --------------------------------------------------------------------------- #
# The summary: every sensitivity, blocks A-E, against one baseline
# --------------------------------------------------------------------------- #

# Each row names its JSON relative to this folder, because the rows come from two
# places: blocks A-D in results_sensitivities/, and the carbon-budget ladder and the other
# cases at the central budget in results_carbon_biomass_grid/. The fossil BAU is not a row: it is a reference rather
# than a sensitivity, and it stretched every axis until the sensitivities were unreadable.
BASELINE_ROW = ("results_sensitivities/base.json", "Baseline")

SUMMARY_GROUPS = [
    (
        "Carbon budget",
        style.NAVY,
        [
            ("results_carbon_biomass_grid/opt_main_3_8.json", "3.8 %"),
            ("results_carbon_biomass_grid/opt_main_3_4.json", "3.4 %"),
            ("results_carbon_biomass_grid/opt_main_3_0.json", "3.0 %"),
            ("results_carbon_biomass_grid/opt_main_2_6.json", "2.6 %"),
            ("results_carbon_biomass_grid/opt_main_2_2.json", "2.2 %"),
        ],
    ),
    (
        "Biomass allocation",
        style.GREEN,
        [
            ("results_carbon_biomass_grid/opt_B5_refueleu.json", "5 %"),
            ("results_carbon_biomass_grid/opt_B75_refueleu.json", "7.5 %"),
            ("results_carbon_biomass_grid/opt_B15_refueleu.json", "15 %"),
        ],
    ),
    (
        "Technology",
        style.DARK_GREY,
        [("results_carbon_biomass_grid/opt_pess_refueleu.json", "efficiency +0.91 %/yr")],
    ),
    (
        "Price elasticity",
        style.PURPLE,
        [
            ("results_sensitivities/fixed_demand.json", "fixed demand"),
            ("results_sensitivities/eps_m0_6.json", "\u22120.6"),
            ("results_sensitivities/eps_m0_8.json", "\u22120.8"),
            ("results_sensitivities/eps_m1_0.json", "\u22121.0"),
            ("results_sensitivities/eps_m1_4.json", "\u22121.4"),
        ],
    ),
    (
        "Ramp-up rate",
        style.RED,
        [
            ("results_sensitivities/rate_11_8.json", "11.8 %/yr  (IEA NZE)"),
            ("results_sensitivities/rate_39.json", "39 %/yr  (wind/PV)"),
        ],
    ),
    (
        "Ramp-up volume",
        style.ORANGE,
        [
            ("results_sensitivities/vol_0_1.json", "0.1 EJ/yr"),
            ("results_sensitivities/vol_0_4.json", "0.4 EJ/yr"),
        ],
    ),
    (
        "Electrofuel pathway",
        style.TEAL,
        [("results_sensitivities/efuel_wind.json", "dedicated wind")],
    ),
    (
        "Discount rate",
        style.OCHRE,
        [
            ("results_sensitivities/r_3_2.json", "3.2 % †"),
            ("results_sensitivities/r_7.json", "7 % †"),
            ("results_sensitivities/r_15.json", "15 % †"),
        ],
    ),
]


def _surplus_loss(vectors):
    """The objective, cumulative discounted total surplus loss to 2050, in bn EUR.

    NaN for the fixed-demand run, which leaves its row empty in that panel. The
    no-feedback chain does not report the objective, and what could be rebuilt from it --
    the 2026-2050 discounted airline cost increase alone -- has no travel term, so it is
    not the same quantity as the elastic rows.
    """
    if "cumulative_total_surplus_loss_discounted" not in vectors:
        return float("nan")
    return vectors["cumulative_total_surplus_loss_discounted"][-1] / 1e9


def _mandate(pathway):
    """(2035, 2050) mandate share of one pathway: the pair a mandate panel draws."""
    key = f"generic_{pathway}_mandate_share"
    return lambda v: (v[key][YEARS.index(2035)], v[key][-1])


# Mandates first -- they are what the optimiser chooses -- then what follows from them.
# A mandate metric returns a (2035, 2050) pair and is drawn as a wide ring and a dot; the
# others return one number. Cumulative CO2 is not here: it is the constraint, identical in
# every run outside the carbon-budget group, whose rows already name it.
#
# Each entry is (title, x label, key, metric). The key is drawn under the panel with the
# panel's own markers and says what period a marker stands for.
SUMMARY_MANDATES = [
    ("a. Biofuel", "Mandate share (%)", ["2035", "2050"], _mandate("biofuel")),
    ("b. Electrofuel", "Mandate share (%)", ["2035", "2050"], _mandate("electrofuel")),
]
SUMMARY_OUTCOMES = [
    ("c. Surplus loss", "Loss (Bn \u20ac, discounted)", ["Cumulative to 2050"], _surplus_loss),
    (
        "d. CO$_2$ emissions",
        "Emissions (MtCO$_2$/yr)",
        ["2050"],
        lambda v: v["co2_emissions_passenger"][-1] + v["co2_emissions_freight"][-1],
    ),
    ("e. Traffic", "Traffic (trillion RPK)", ["2050"], lambda v: v["rpk"][-1] / 1e12),
]
SUMMARY_METRICS = SUMMARY_MANDATES + SUMMARY_OUTCOMES

# Half a page of an Elsevier journal: 190 mm is the double-column width. Saved at exactly
# this size, so the font sizes below are the printed ones (Elsevier asks for 7 pt or more).
SUMMARY_FIGSIZE = (190 / 25.4, 128 / 25.4)
SUMMARY_FONT = 7.0


def _summary_row(path):
    """(metric values, status) for one row; status is 'ok', 'missing' or 'infeasible'.

    Feasibility is read from the optimisation history, not assumed from the outputs: an
    infeasible run still writes them, holding its last iterate, and that is not a result.
    A reference MDA has no history and no constraints to violate.
    """
    run = Path(path).stem
    if not D.exists(run):
        return None, "missing"
    if D.feasible(run) is False:
        return None, "infeasible"
    vectors = D.outputs(run)
    return [metric(vectors) for *_, metric in SUMMARY_METRICS], "ok"


def summary():
    """Every sensitivity against one baseline: the two mandates, then three outcomes.

    Blocks A-D vary one parameter at the ReFuelEU-equivalent budget. The carbon-budget
    group is block E's main ladder; the biomass and technology groups are the other
    block E cases re-optimised at that same central budget, so every group except the
    carbon budget shares the baseline's cumulative emissions.

    One row of panels, so a run reads straight across from what the optimiser chose to
    what came of it. Sized for print, so it carries no title or note of its own: those
    belong to the article's caption.
    """
    baseline, _ = _summary_row(BASELINE_ROW[0])

    rows, ticks, labels, styles, separators = [], [], [], [], []
    y = 0.0
    ticks.append(y)
    labels.append(BASELINE_ROW[1])
    styles.append((INK, "bold"))
    rows.append((y, baseline, NEUTRAL))
    y += 1.0
    for group, colour, members in SUMMARY_GROUPS:
        separators.append(y - 0.5)
        y += 0.5
        ticks.append(y)
        labels.append(group)
        styles.append((colour, "bold"))
        y += 1.0
        for path, label in members:
            values, status = _summary_row(path)
            note = {"ok": "", "missing": "  (not on disk)", "infeasible": "  (infeasible)"}
            ticks.append(y)
            labels.append(f"{label}{note[status]}")
            styles.append((INK if status == "ok" else MUTED, "normal"))
            if values is not None:
                rows.append((y, values, colour))
            y += 1.0

    mandates = range(len(SUMMARY_MANDATES))
    mandate_top = max(max(values[i]) for _, values, _ in rows for i in mandates)

    # Sized for print, so the type is set here rather than taken from the house scale.
    with plt.rc_context({"font.size": SUMMARY_FONT, "legend.framealpha": 0}):
        figure = plt.figure(figsize=SUMMARY_FIGSIZE, layout="constrained")
        figure.get_layout_engine().set(w_pad=0.04, h_pad=0.02, wspace=0.03)
        grid = figure.add_gridspec(1, len(SUMMARY_METRICS))
        axes = []
        for column in range(len(SUMMARY_METRICS)):
            axes.append(figure.add_subplot(grid[0, column], sharey=axes[0] if axes else None))

        marker = {"ms": 4, "zorder": 2, "markeredgewidth": 0.9}
        # The first year of a pair is a wide ring, so that the usual dot sits inside it,
        # and both still read, where the two years coincide.
        ring = {**marker, "ms": 7, "color": "white"}
        for index, (axis, (title, xlabel, key, _)) in enumerate(zip(axes, SUMMARY_METRICS)):
            _frame(axis, grid="x")
            axis.tick_params(labelsize=SUMMARY_FONT, length=2.5, width=0.6, pad=2)
            axis.tick_params(axis="y", length=0, labelleft=index == 0)
            axis.grid(axis="x", lw=0.5)
            for boundary in separators:
                axis.axhline(boundary, color=GRID, lw=0.7, zorder=0)
            if index in mandates:
                for reference in baseline[index]:
                    axis.axvline(reference, color=MUTED, lw=0.7, ls=":", zorder=0)
                # One stem per year, each from the baseline's value for that year, so a
                # stem means the same here as in the outcome panels: the deviation.
                stem = {"lw": 0.9, "alpha": 0.45, "solid_capstyle": "butt"}
                for y, values, colour in rows:
                    for reference, value in zip(baseline[index], values[index]):
                        axis.plot([reference, value], [y, y], color=colour, **stem)
                    early, late = values[index]
                    axis.plot(early, y, "o", markeredgecolor=colour, **ring)
                    dot = {**marker, "zorder": 3}
                    axis.plot(late, y, "o", color=colour, markeredgecolor=colour, **dot)
                axis.set_xlim(-4, max(mandate_top * 1.06, 63))
                axis.set_xticks(range(0, 61, 20))
            else:
                axis.axvline(baseline[index], color=MUTED, lw=0.7, ls=":", zorder=0)
                for y, values, colour in rows:
                    value = values[index]
                    axis.plot([baseline[index], value], [y, y], color=colour, lw=0.9, alpha=0.45)
                    axis.plot(value, y, "o", color=colour, markeredgecolor=colour, **marker)
                # Round steps keep the first tick away from the left edge. A label that
                # overhangs the axis makes the layout open a wider gap before that panel.
                axis.xaxis.set_major_locator(MaxNLocator(nbins=6, steps=[1, 2, 5, 10]))
            axis.set_xlabel(xlabel, fontsize=SUMMARY_FONT, labelpad=2)
            dot = {**marker, "color": MUTED, "markeredgecolor": MUTED}
            key_styles = [{**ring, "markeredgecolor": MUTED}, dot][-len(key) :]
            axis.legend(
                [Line2D([], [], ls="none", marker="o", **style) for style in key_styles],
                key,
                loc="upper center",
                bbox_to_anchor=(0.5, -0.075),
                ncol=len(key),
                frameon=False,
                fontsize=SUMMARY_FONT,
                labelcolor=MUTED,
                handletextpad=0.1,
                columnspacing=1.2,
                borderpad=0,
                borderaxespad=0,
            )
            axis.set_title(title, fontsize=SUMMARY_FONT + 1, pad=4)

        axes[0].set_yticks(ticks)
        axes[0].set_yticklabels(labels)
        for text, (colour, weight) in zip(axes[0].get_yticklabels(), styles):
            text.set_color(colour)
            text.set_fontweight(weight)
        axes[0].set_ylim(-0.9, ticks[-1] + 0.9)
        axes[0].invert_yaxis()

        # The layout sizes each gap to that panel's own tick labels and key, which leaves
        # them a millimetre apart. Take its outer extent and space the panels evenly.
        figure.canvas.draw()
        boxes = [axis.get_position() for axis in axes]
        figure.set_layout_engine("none")
        width = boxes[0].width
        gap = (boxes[-1].x1 - boxes[0].x0 - len(axes) * width) / (len(axes) - 1)
        for index, (axis, box) in enumerate(zip(axes, boxes)):
            axis.set_position([boxes[0].x0 + index * (width + gap), box.y0, width, box.height])

        # No bbox_inches="tight": it would crop the page to the artwork and the printed
        # width would no longer be the 190 mm the font sizes assume.
        for suffix in ("png", "pdf"):
            figure.savefig(FIGURES / f"fig_sensitivity_summary.{suffix}", dpi=300)
    print("wrote fig_sensitivity_summary.png / .pdf")


if __name__ == "__main__":
    ramp_up()
    pathway()
    discount()
    summary()

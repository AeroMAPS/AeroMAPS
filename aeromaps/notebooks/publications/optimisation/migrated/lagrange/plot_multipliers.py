"""Step 6: the two prototype figures.

Figure 1 is the sector's marginal abatement cost curve, derived from the
multipliers rather than assumed: lambda_G1 in EUR/tCO2 against the carbon
budget, one line per biomass allocation, with the independent finite-difference
estimate of the same quantity overlaid.

Figure 2 is the baseline run's annual multipliers against time. The points are
plotted as markers and deliberately not joined across an active-set switch: a
constraint that stops binding has a multiplier of exactly zero, and a line
through that would invent a transition the optimum does not have.

Biomass allocation is an ordered quantity, so it is encoded on a single-hue
ordinal ramp rather than as unrelated categories. The low-efficiency case is
not a point on that axis - it changes the technology roadmap, not the biomass
share - so it carries its own hue and its own legend entry.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from extract_multipliers import CASES, OPTIM_YEARS, OUT

BASELINE = "opt_main_2_6"

# Ordinal ramp for the biomass axis (validated: monotone L, single hue,
# light end clears the surface), plus one categorical hue for the case that
# is not on that axis.
BIOMASS_RAMP = {5.0: "#86b6ef", 7.5: "#3987e5", 9.9: "#256abf", 15.0: "#0d366b"}
OFF_AXIS_COLOR = "#eb6834"
SERIES_COLORS = ("#2a78d6", "#eb6834")

TEXT_PRIMARY, TEXT_SECONDARY, GRID = "#0b0b0b", "#52514e", "#d9d8d3"


def _style(ax):
    ax.set_facecolor("#fcfcfb")
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.9)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.xaxis.label.set_color(TEXT_SECONDARY)
    ax.yaxis.label.set_color(TEXT_SECONDARY)


def figure_shadow_price_vs_budget(table, envelope, quality):
    """lambda_G1 against the carbon budget, with the finite-difference check.

    The runs are not of uniform quality, and a point can fail the bracket screen
    for two quite different reasons. Direct measurement (``envelope_direct.py``)
    separates them:

    * **under-converged** - relative KKT residual above 1e-2. Measured 12-17 %
      wrong against ground truth on a smooth part of the curve, so genuinely
      wrong: excluded and marked.
    * **kinked** - well converged, but the active set changes at that budget, so
      `f*` has no derivative there and λ is a one-sided one. Measured correct to
      0.3 %. It stays on the curve, marked as the step it is.

    A point that merely stopped on ``ftol_abs`` while still passing the screen is
    imprecise rather than wrong, and stays as a hollow marker.
    """
    g1 = table[
        (table.constraint == "G1")
        & table.run_feasible
        & table.carbon_budget_share_world_pct.notna()
    ].drop_duplicates("run")
    flags = quality.set_index("run")
    # A failed screen means "wrong" only when the run is also under-converged.
    # On a converged run it means the optimal-value function kinks there, and
    # direct measurement shows lambda is then a valid one-sided derivative.
    failed = {
        run: (row.in_bracket is False) or bool(row.gradient_suspect)
        for run, row in flags.iterrows()
    }
    converged = flags.kkt_converged.to_dict()
    degenerate = dict(zip(g1.run, g1.blend_degenerate))
    g1 = g1.assign(
        consistent=[
            not (degenerate.get(r, False) or (failed.get(r, False) and not converged.get(r, True)))
            for r in g1.run
        ],
        precise=[bool(converged.get(r, True)) for r in g1.run],
        kinked=[
            failed.get(r, False) and converged.get(r, True) and not degenerate.get(r, False)
            for r in g1.run
        ],
        degenerate=[bool(degenerate.get(r, False)) for r in g1.run],
    )

    fig, ax = plt.subplots(figsize=(7.8, 5.2))
    _style(ax)

    order = sorted(
        g1.case.unique(),
        key=lambda c: (CASES[c]["efficiency_gain"] != 1.35, CASES[c]["biomass_share"]),
    )
    for case in order:
        block = g1[g1.case == case].sort_values("carbon_budget_share_world_pct")
        on_axis = CASES[case]["efficiency_gain"] == 1.35
        colour = BIOMASS_RAMP[CASES[case]["biomass_share"]] if on_axis else OFF_AXIS_COLOR
        keep = block[block.consistent]
        ax.plot(
            keep.carbon_budget_share_world_pct,
            keep.shadow_price_eur_per_tco2_discounted2020,
            linewidth=2,
            color=colour,
            linestyle="-" if on_axis else "--",
            label=CASES[case]["label"],
            zorder=3,
        )
        firm = keep[keep.precise & ~keep.kinked]
        loose = keep[~keep.precise]
        kinked = keep[keep.kinked]
        ax.scatter(
            firm.carbon_budget_share_world_pct,
            firm.shadow_price_eur_per_tco2_discounted2020,
            s=42,
            color=colour,
            zorder=4,
        )
        ax.scatter(
            loose.carbon_budget_share_world_pct,
            loose.shadow_price_eur_per_tco2_discounted2020,
            s=42,
            facecolor="#fcfcfb",
            edgecolor=colour,
            linewidth=1.8,
            zorder=4,
        )
        # A well-converged point where the active set changes: λ is a valid
        # one-sided derivative, so the curve genuinely steps here.
        ax.scatter(
            kinked.carbon_budget_share_world_pct,
            kinked.shadow_price_eur_per_tco2_discounted2020,
            s=95,
            marker="D",
            facecolor=colour,
            edgecolor="#fcfcfb",
            linewidth=1.6,
            zorder=6,
        )
        for _, row in kinked.iterrows():
            ax.annotate(
                "active-set step",
                (row.carbon_budget_share_world_pct, row.shadow_price_eur_per_tco2_discounted2020),
                textcoords="offset points",
                xytext=(9, -2),
                fontsize=7.5,
                color=TEXT_SECONDARY,
            )
        # The independent finite-difference estimate, in the case's own colour so
        # it can be matched to its line.
        check = envelope[envelope.case == case]
        ax.scatter(
            check.carbon_budget_share_world_pct,
            check.findiff_price_eur_per_tco2,
            s=22,
            marker="_",
            color=colour,
            linewidth=1.6,
            zorder=5,
        )
        # Excluded points, shown rather than quietly dropped.
        drop = block[~block.consistent & ~block.degenerate]
        bad = block[block.degenerate]
        # The blend-completeness constraint exactly active drives residual fossil
        # kerosene to floating-point zero, and the model's share arithmetic to
        # 0/0. The KKT system is satisfied, but outside the model's valid domain.
        ax.scatter(
            bad.carbon_budget_share_world_pct,
            bad.shadow_price_eur_per_tco2_discounted2020,
            s=80,
            marker="s",
            facecolor="none",
            edgecolor=colour,
            linewidth=2.0,
            zorder=6,
        )
        for _, row in bad.iterrows():
            ax.annotate(
                "blend saturated\n(degenerate)",
                (row.carbon_budget_share_world_pct, row.shadow_price_eur_per_tco2_discounted2020),
                textcoords="offset points",
                xytext=(9, -4),
                fontsize=7.5,
                color=TEXT_SECONDARY,
            )
        ax.scatter(
            drop.carbon_budget_share_world_pct,
            drop.shadow_price_eur_per_tco2_discounted2020,
            s=64,
            marker="x",
            color=colour,
            linewidth=1.8,
            zorder=6,
        )
        for _, row in drop.iterrows():
            ax.annotate(
                "excluded",
                (row.carbon_budget_share_world_pct, row.shadow_price_eur_per_tco2_discounted2020),
                textcoords="offset points",
                xytext=(7, 4),
                fontsize=7.5,
                color=TEXT_SECONDARY,
            )

    ax.set_xlabel("Aviation carbon budget, share of world budget (%)")
    ax.set_ylabel("Shadow carbon price (€2020/tCO$_2$, discounted)")
    ax.set_title(
        "Marginal abatement cost, derived from the carbon-budget multiplier",
        color=TEXT_PRIMARY,
        fontsize=12,
        pad=10,
        loc="left",
    )
    handles, labels = ax.get_legend_handles_labels()
    # Only advertise the marker categories that actually have a point on the
    # figure; an entry with nothing behind it reads as missing data.
    present = {
        "KKT residual < 1e-12": bool((g1.precise & ~g1.kinked & g1.consistent).any()),
        "stopped on ftol_abs": bool((~g1.precise).any()),
        "active-set step (valid)": bool(g1.kinked.any()),
        "blend saturated (degenerate)": bool(g1.degenerate.any()),
        "under-converged (excluded)": bool((~g1.consistent & ~g1.degenerate).any()),
    }
    extra = [
        plt.Line2D(
            [],
            [],
            marker="o",
            color=TEXT_SECONDARY,
            linestyle="none",
            markersize=6,
            label="KKT residual < 1e-12",
        ),
        plt.Line2D(
            [],
            [],
            marker="o",
            markerfacecolor="#fcfcfb",
            markeredgecolor=TEXT_SECONDARY,
            color=TEXT_SECONDARY,
            linestyle="none",
            markersize=6,
            label="stopped on ftol_abs",
        ),
        plt.Line2D(
            [],
            [],
            marker="_",
            color=TEXT_SECONDARY,
            linestyle="none",
            markersize=9,
            label="finite-difference check",
        ),
        plt.Line2D(
            [],
            [],
            marker="D",
            color=TEXT_SECONDARY,
            linestyle="none",
            markersize=6,
            label="active-set step (valid)",
        ),
        plt.Line2D(
            [],
            [],
            marker="s",
            markerfacecolor="none",
            markeredgecolor=TEXT_SECONDARY,
            color=TEXT_SECONDARY,
            linestyle="none",
            markersize=7,
            label="blend saturated (degenerate)",
        ),
        plt.Line2D(
            [],
            [],
            marker="x",
            color=TEXT_SECONDARY,
            linestyle="none",
            markersize=7,
            label="under-converged (excluded)",
        ),
    ]
    extra = [h for h in extra if present.get(h.get_label(), True)]
    ax.legend(
        handles=handles + extra,
        frameon=False,
        fontsize=8.5,
        labelcolor=TEXT_SECONDARY,
        ncol=2,
        loc="upper right",
    )
    fig.tight_layout()
    fig.savefig(OUT / "fig_shadow_price_vs_budget.png", dpi=200, facecolor="#fcfcfb")
    plt.close(fig)


def figure_shadow_price_vs_time(table: pd.DataFrame, run: str = BASELINE):
    """The baseline run's annual multipliers, by year, without smoothing.

    Two panels rather than one: the resource multipliers and the ramp-up
    multipliers are per GJ of different things and do not belong on a shared
    axis. Under each panel a strip records which constraint binds in which
    year, so the active set can be read off directly and lined up with the
    constraint figure in the paper.
    """
    block = table[table.run == run]
    panels = [
        (
            "Resource availability",
            [("G3", "Biomass (G3)"), ("G4", "Electricity (G4)")],
            "shadow_price_eur_per_gj_discounted2020",
            "€2020 per GJ of allocated resource",
        ),
        (
            "Deployment ramp-up",
            [("G5", "Biofuel (G5)"), ("G6", "Electrofuel (G6)")],
            "shadow_price_eur_per_gj_of_cap_discounted2020",
            "€2020 per GJ of relaxed cap",
        ),
    ]
    fig = plt.figure(figsize=(7.8, 9.0))
    # A spacer row between the two groups: without it the lower panel's title
    # and legend, which sit above its axes, land on the upper panel's strip.
    grid = fig.add_gridspec(5, 1, height_ratios=[6, 1.15, 1.5, 6, 1.15], hspace=0.14)
    slots = [(0, 1), (3, 4)]

    for panel_index, (title, families, column, ylabel) in enumerate(panels):
        main_slot, strip_slot = slots[panel_index]
        ax = fig.add_subplot(grid[main_slot])
        strip = fig.add_subplot(grid[strip_slot], sharex=ax)
        _style(ax)

        for series_index, ((family, label), colour) in enumerate(zip(families, SERIES_COLORS)):
            rows = block[block.constraint == family].sort_values("year")
            # Dodge the two series slightly: otherwise the slack markers, which
            # all sit at exactly zero, land on top of each other.
            offset = (series_index - 0.5) * 0.9
            active = rows[rows.active]
            slack = rows[~rows.active]
            ax.scatter(
                active.year + offset, active[column], s=80, color=colour, zorder=4, label=label
            )
            ax.scatter(
                slack.year + offset,
                np.zeros(len(slack)),
                s=46,
                facecolor="none",
                edgecolor=colour,
                linewidth=1.4,
                zorder=3,
            )
            for _, row in active.iterrows():
                ax.annotate(
                    f"{row[column]:,.0f}",
                    (row.year + offset, row[column]),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                    fontsize=8.5,
                    color=TEXT_SECONDARY,
                )
            # Binding-status strip, one row per constraint.
            y = len(families) - 1 - series_index
            for _, row in rows.iterrows():
                binding = bool(row.active)
                strip.add_patch(
                    plt.Rectangle(
                        (row.year - 1.9, y + 0.16),
                        3.8,
                        0.68,
                        facecolor=colour if binding else "none",
                        edgecolor=colour,
                        linewidth=1.1,
                        alpha=1.0 if binding else 0.45,
                    )
                )
                if binding and family in ("G5", "G6"):
                    # Which side of the max() is binding decides what relaxing
                    # the bound would even mean, so it is labelled in place.
                    strip.annotate(
                        row.ramp_branch_active,
                        (row.year, y + 0.5),
                        ha="center",
                        va="center",
                        fontsize=7.5,
                        color="#ffffff",
                        zorder=5,
                    )

        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(title, color=TEXT_PRIMARY, fontsize=11, loc="left", pad=26)
        # Headroom for the value labels above the highest marker.
        top = max(ax.get_ylim()[1], block[column].max() * 1.20)
        ax.set_ylim(bottom=-0.06 * top, top=top)
        ax.legend(
            frameon=False,
            fontsize=9,
            labelcolor=TEXT_SECONDARY,
            ncol=2,
            loc="lower left",
            bbox_to_anchor=(0, 1.005),
            handletextpad=0.4,
            columnspacing=1.6,
        )
        plt.setp(ax.get_xticklabels(), visible=False)

        strip.set_ylim(0, len(families))
        strip.set_xlim(2027.5, 2052.5)
        strip.set_yticks([i + 0.5 for i in range(len(families))])
        strip.set_yticklabels(
            [lbl.split(" (")[0] for lbl, _ in [(f[1], f[0]) for f in families]][::-1], fontsize=8
        )
        strip.set_facecolor("#fcfcfb")
        for side in ("top", "right", "left", "bottom"):
            strip.spines[side].set_visible(False)
        strip.tick_params(axis="y", length=0, colors=TEXT_SECONDARY)
        strip.tick_params(axis="x", colors=TEXT_SECONDARY, labelsize=9)
        strip.grid(False)
        if panel_index == 0:
            plt.setp(strip.get_xticklabels(), visible=False)
        strip.set_xticks(OPTIM_YEARS)

    strip.set_xlabel("Constraint enforcement year", color=TEXT_SECONDARY, fontsize=9)
    fig.suptitle(
        f"Annual shadow prices at the optimum — {run}\n"
        "filled = binding, hollow = slack (multiplier exactly zero)",
        color=TEXT_PRIMARY,
        fontsize=11.5,
        x=0.012,
        ha="left",
        y=0.985,
    )
    fig.savefig(
        OUT / "fig_shadow_price_vs_time.png", dpi=200, facecolor="#fcfcfb", bbox_inches="tight"
    )
    plt.close(fig)


if __name__ == "__main__":
    table = pd.read_csv(OUT / "lagrange_multipliers.csv")
    envelope = pd.read_csv(OUT / "validation_budget_envelope.csv")
    quality = pd.read_csv(OUT / "validation_run_quality.csv")
    figure_shadow_price_vs_budget(table, envelope, quality)
    figure_shadow_price_vs_time(table)
    print("wrote fig_shadow_price_vs_budget.png and fig_shadow_price_vs_time.png")

"""Figures that explain the model rather than report a result.

Usage::

    poetry run python -m fuel_clearing_step1.report.explanatory

Three drawings for the LaTeX report. None of them runs the kernel: they are the shapes
the formulation is built out of, drawn from the same formulas the kernel uses, so that a
reader can see *why* each choice was forced before seeing what it produced.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
FIGURES = HERE / "figures"

COST = "#1f5f8b"
RENT = "#a93226"
GOOD = "#2f6b4f"
MUTED = "#6b7280"


def saturation_shape():
    """Marginal against average cost, and the rent between them, versus utilisation."""
    utilisation = np.linspace(0, 1.6, 400)
    figure, axes = plt.subplots(1, 2, figsize=(11.0, 3.9), constrained_layout=True)

    gamma = 1.0
    for n, style in zip((1, 2, 4, 16), ("-", "--", "-.", ":")):
        axes[0].plot(
            utilisation,
            1 + gamma * utilisation**n,
            style,
            color=COST,
            linewidth=1.6,
            label=f"n = {n}",
        )
    axes[0].axvline(1.0, color="0.75", linestyle=":", linewidth=1.2)
    axes[0].annotate(
        "q = K",
        xy=(1.0, 0.2),
        xytext=(4, 0),
        textcoords="offset points",
        fontsize=8,
        color="0.45",
    )
    axes[0].set_xlabel("utilisation  q / K")
    axes[0].set_ylabel("marginal cost / c")
    axes[0].set_title(
        r"Soft saturation: $c\,(1+\gamma (q/K)^n)$" "\nn controls when it bites, not how hard",
        fontsize=9.5,
    )
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].set_ylim(0.8, 3.2)

    n = 4
    marginal = 1 + gamma * utilisation**n
    average = 1 + gamma / (n + 1) * utilisation**n
    axes[1].plot(utilisation, marginal, "-", color=RENT, linewidth=1.8, label="marginal cost")
    axes[1].plot(utilisation, average, "-", color=GOOD, linewidth=1.8, label="average cost")
    axes[1].fill_between(utilisation, average, marginal, color=RENT, alpha=0.12)
    axes[1].annotate(
        "inframarginal rent\n(the gap w interpolates across)",
        xy=(1.25, 0.5 * (marginal[-90] + average[-90])),
        xytext=(-150, -6),
        textcoords="offset points",
        fontsize=8.5,
        color="0.35",
    )
    axes[1].axvline(1.0, color="0.75", linestyle=":", linewidth=1.2)
    axes[1].set_xlabel("utilisation  q / K")
    axes[1].set_ylabel("cost / c")
    axes[1].set_title(
        "Marginal against average, at n = 4\n" r"$w=0$ charges the lower curve, $w=1$ the upper",
        fontsize=9.5,
    )
    axes[1].legend(frameon=False, fontsize=8)
    axes[1].set_ylim(0.8, 3.2)

    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.set_xlim(0, 1.6)
    FIGURES.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURES / "explain_saturation.png", dpi=200)
    plt.close(figure)
    print("wrote explain_saturation.png")


def rampup_shape():
    """Why the published ramp-up cannot go into a convex program, drawn."""
    # Schematic: tau is exaggerated against the bench's 20-30 %/yr so the kink sits in
    # the middle of the frame and the geometry is legible. The shape is what matters.
    previous = np.linspace(0, 1.2, 400)
    tau, increment = 1.20, 0.60

    rate = (1 + tau) * previous
    volume = previous + increment
    eq12 = np.maximum(rate, volume)
    relaxed = increment + (1 + tau) * previous

    figure, axes = plt.subplots(1, 2, figsize=(11.0, 3.9), constrained_layout=True)

    axes[0].plot(
        previous, rate, "--", color=MUTED, linewidth=1.4, label=r"rate branch $(1+\tau)q_{t-1}$"
    )
    axes[0].plot(
        previous, volume, ":", color=MUTED, linewidth=1.6, label=r"volume branch $q_{t-1}+\Delta E$"
    )
    axes[0].plot(previous, eq12, "-", color=RENT, linewidth=2.2, label="Eq. (12): the max")
    axes[0].plot(
        previous, relaxed, "-", color=COST, linewidth=1.8, label="convex relaxation: the sum"
    )
    axes[0].set_xlabel(r"previous year's volume  $q_{t-1}$")
    axes[0].set_ylabel(r"allowed  $q_t$")
    axes[0].set_title(
        "The published limit is the MORE PERMISSIVE of two rules\n"
        r"(schematic: $\tau$ exaggerated so the kink is visible)",
        fontsize=9.5,
    )
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")

    # Why it is not convex, shown rather than asserted: take two admissible points,
    # one on each branch of the max, and the straight line between them leaves the set.
    kink = increment / tau
    axes[1].fill_between(previous, 0, eq12, color=RENT, alpha=0.13, label="admitted by Eq. (12)")
    axes[1].plot(previous, eq12, "-", color=RENT, linewidth=2.2)

    xa, xb = 0.05, 1.2
    ya, yb = np.interp(xa, previous, eq12), np.interp(xb, previous, eq12)
    axes[1].plot([xa, xb], [ya, yb], "-", color="#111", linewidth=1.5, zorder=5)
    axes[1].plot([xa, xb], [ya, yb], "o", color="#111", markersize=5, zorder=6)
    chord_x = np.linspace(xa, xb, 200)
    chord_y = ya + (yb - ya) * (chord_x - xa) / (xb - xa)
    boundary = np.interp(chord_x, previous, eq12)
    axes[1].fill_between(
        chord_x,
        boundary,
        chord_y,
        where=chord_y > boundary,
        color="#111",
        alpha=0.22,
    )
    axes[1].annotate(
        "two admissible points,\nbut the line between them\nis NOT admissible",
        xy=(0.52, 0.5 * (np.interp(0.52, chord_x, chord_y) + np.interp(0.52, previous, eq12))),
        xytext=(46, -54),
        textcoords="offset points",
        fontsize=8.5,
        color="#111",
        ha="center",
        arrowprops=dict(arrowstyle="->", color="#111", linewidth=0.9),
    )
    axes[1].axvline(kink, color="0.7", linestyle=":", linewidth=1.2)
    axes[1].set_xlabel(r"previous year's volume  $q_{t-1}$")
    axes[1].set_ylabel(r"allowed  $q_t$")
    axes[1].set_title(
        "That is why it cannot be handed to a convex solver\n"
        "the region under a max of two lines is not a convex set",
        fontsize=9.5,
    )

    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.set_xlim(0, 1.2)
        axis.set_ylim(0, 2.9)
    FIGURES.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURES / "explain_rampup.png", dpi=200)
    plt.close(figure)
    print("wrote explain_rampup.png")


def chain_shape():
    """Where the market sits, and which loop w closes."""
    figure, axis = plt.subplots(figsize=(11.0, 4.3))
    axis.set_xlim(0, 100)
    axis.set_ylim(0, 44)
    axis.axis("off")

    def box(x, y, w, h, label, colour, bold=False):
        axis.add_patch(
            plt.Rectangle(
                (x, y), w, h, facecolor=colour, edgecolor="#333", linewidth=1.1, alpha=0.85
            )
        )
        axis.text(
            x + w / 2,
            y + h / 2,
            label,
            ha="center",
            va="center",
            fontsize=8.6,
            weight="bold" if bold else "normal",
            color="white" if bold else "#111",
        )

    def arrow(x1, y1, x2, y2, label="", colour="#333", style="-|>", offset=(0, 4)):
        axis.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle=style, color=colour, linewidth=1.3),
        )
        if label:
            axis.text(
                (x1 + x2) / 2 + offset[0],
                (y1 + y2) / 2 + offset[1],
                label,
                ha="center",
                fontsize=7.8,
                color=colour,
            )

    box(2, 26, 17, 8, "fleet & traffic\n(RPK, ASK)", "#dbe4ea")
    box(23, 26, 17, 8, "energy demand\n$D_{r,t}$  [MJ]", "#dbe4ea")
    box(
        44,
        24,
        20,
        12,
        "FUEL MARKET\nconvex program\n$q_{r,p,t}$,  $\\lambda$",
        "#a93226",
        bold=True,
    )
    box(68, 26, 15, 8, "shares\n$\\times$ pathway", "#dbe4ea")
    box(68, 12, 15, 8, "mean price\n$\\overline{\\mathrm{mfsp}}$", "#dbe4ea")
    box(44, 4, 20, 8, "airline cost\n$\\rightarrow$ airfare", "#dbe4ea")
    box(23, 4, 17, 8, "demand\nelasticity", "#dbe4ea")
    box(2, 14, 17, 8, "pathway costs\n$c_{r,p,t}$", "#e7e0c8")

    arrow(19, 30, 23, 30)
    arrow(40, 30, 44, 30, "$D$")
    arrow(19, 18, 44, 27, "$c$ (net of tax)", colour="#7a6a2a", offset=(0, 5))
    arrow(64, 31, 68, 31, "$q$")
    arrow(75.5, 26, 75.5, 20, "")
    arrow(64, 27, 68, 18, "$\\mathrm{mfsp}^{\\mathrm{mkt}}$", offset=(3, -6))
    arrow(68, 14, 64, 9, "")
    arrow(44, 8, 40, 8)
    arrow(23, 8, 10.5, 8)
    arrow(10.5, 8, 10.5, 26, "", colour="#a93226")
    axis.text(
        11.5,
        17,
        "the loop $w$ closes",
        fontsize=8.4,
        color="#a93226",
        rotation=90,
        va="center",
    )

    axis.text(
        50,
        40,
        "At $w=0$ the airline pays the AVERAGE cost — a function of volumes.\n"
        "At $w=1$ it pays the MARGINAL price — a function of the duals.",
        ha="center",
        fontsize=9.2,
        color="#111",
    )
    axis.text(
        2,
        0.5,
        "Shaded red: the discipline added by this work. Everything else is existing AeroMAPS.",
        fontsize=7.8,
        color="0.4",
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURES / "explain_chain.png", dpi=200, bbox_inches="tight")
    plt.close(figure)
    print("wrote explain_chain.png")


if __name__ == "__main__":
    saturation_shape()
    rampup_shape()
    chain_shape()

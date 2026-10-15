"""One look for every figure of the ReFuelEU optimisation paper.

Imported by `02_results.ipynb`, `equilibriums.ipynb` and the plotting scripts in
`sweep/`, so a figure drawn from the notebook and the same figure drawn from the command
line come out identical, and two figures set side by side in the article share their
colours, their type and the way their axes are drawn.

    from helpers import paper_style as style
    style.apply()

What it settles:

* **Palette.** The four colours of the published figures, plus the few more the newer
  figures need, and the ramps built on them. Colour follows meaning across figures: a
  fuel keeps its hue, and so does a reference scenario.
* **Type.** One family and one scale -- panel titles, axis labels, then everything
  secondary (ticks, legends, annotations).
* **Axes.** Open at the top and right, the remaining frame muted, a light rule across the
  value axis only. Images keep their full frame: see `image_frame`.
* **Panels.** A multi-panel figure names each panel "a. Title", bold, flush left. A
  single-panel figure carries no title: that is the caption's job.
* **Labels.** "Quantity (unit)", units in parentheses, no "Year" under a time axis.
"""

from __future__ import annotations

import string

import matplotlib as mpl
import matplotlib.colors as mcolors
import numpy as np

# --- Palette --------------------------------------------------------------------------
# The four colours of the published figures.
RED, NAVY, YELLOW, GREEN = "#cb3629", "#092054", "#efbd40", "#7e9b59"
BLUE = NAVY
# The supply models of `supply.pdf`, by the letter the article gives them.
SUPPLY_MODELS = {"A": RED, "B": NAVY, "C": YELLOW, "D": GREEN}

# Further hues, for figures with more than four categories. Chosen to sit with the four
# above -- the same muted saturation -- and to stay apart from them.
PURPLE, TEAL, ORANGE, OCHRE = "#7b4f9d", "#2f8f8a", "#e08a4f", "#b5852a"

# Lighter steps of the two anchor colours, for a parameter varied either side of a
# baseline: warm is tighter, cool is looser, the baseline neutral.
RED_LIGHT, NAVY_LIGHT = "#e8998d", "#7f97c6"

# Neutrals: text, the muted frame and secondary text, grid rules, envelopes.
INK, MUTED, GRID, PALE = "#1a1a1a", "#6b6b6b", "#e2e2e2", "#cccccc"
NEUTRAL = "#4d4d4d"  # a baseline curve
DARK_GREY = "#555555"  # the fossil BAU
GREY = "lightgrey"

# Colour by meaning, the same in every figure.
BIOFUEL, ELECTROFUEL, FOSSIL = GREEN, NAVY, RED
REFUELEU, OPTIMUM, BAU = RED, GREEN, DARK_GREY


def _cmap(name, colours):
    return mcolors.LinearSegmentedColormap.from_list(name, colours)


# Sequential, light to the anchor colour. Navy is the carbon budget wherever it is a
# colour scale; the light end is dark enough for a thin line to read on white.
SEQUENTIAL_NAVY = _cmap("paper_navy", ["#cfdcf0", "#5b84c4", NAVY])
SEQUENTIAL_GREEN = _cmap("paper_green", ["#f4f7ee", GREEN, "#31471f"])
SEQUENTIAL_PURPLE = _cmap("paper_purple", ["#dccdea", PURPLE, "#3a1f57"])
# For a filled heatmap, which starts from white rather than from a readable line colour.
HEAT_NAVY = _cmap("paper_heat_navy", ["#ffffff", "#5b84c4", NAVY])
# Diverging, navy to red through near-white, the two ends at matching depth.
DIVERGING = _cmap(
    "paper_diverging",
    [
        (0.0, NAVY),
        (0.28, "#5b84c4"),
        (0.5, "#f7f7f7"),
        (0.72, RED_LIGHT),
        (0.9, RED),
        (1.0, "#8f2318"),
    ],
)


def ramp(cmap, count, low=0.0, high=1.0):
    """`count` hex colours evenly spaced along `cmap`, light to dark."""
    return [mcolors.to_hex(cmap(x)) for x in np.linspace(low, high, count)]


# Entry-into-service ramps: hue is the fuel, lightness the year (light = early). Both
# stay dark enough at the light end to be drawn as the figure's leading curve.
BIOFUEL_RAMP = [GREEN, "#64803f", "#49622b", "#2f431a"]
ELECTROFUEL_RAMP = ["#8ea6d6", "#5b7fc0", "#2f4f96", NAVY]

# --- Type -----------------------------------------------------------------------------
# One scale. A figure saved at its printed size (the sensitivity summary, the abatement
# curves) sets its own, smaller sizes instead: these are for figures drawn large and
# scaled down by the page.
FONT_FAMILY = ["Arial", "Helvetica", "DejaVu Sans"]
TITLE_SIZE = 12  # panel titles
LABEL_SIZE = 11  # axis labels, colourbar labels
SMALL_SIZE = 9  # ticks, legends, annotations
SUPTITLE_SIZE = 14

RC = {
    # Type. Mathtext in the text font, so CO$_2$ does not switch face mid-label; fonts
    # embedded as TrueType, which production can edit.
    "font.family": "sans-serif",
    "font.sans-serif": FONT_FAMILY,
    "mathtext.default": "regular",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.size": SMALL_SIZE,
    "text.color": INK,
    "axes.titlesize": TITLE_SIZE,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.titlepad": 8,
    "axes.titlecolor": INK,
    "axes.labelsize": LABEL_SIZE,
    "axes.labelcolor": INK,
    "xtick.labelsize": SMALL_SIZE,
    "ytick.labelsize": SMALL_SIZE,
    "xtick.labelcolor": INK,
    "ytick.labelcolor": INK,
    "legend.fontsize": SMALL_SIZE,
    "legend.title_fontsize": SMALL_SIZE,
    "figure.titlesize": SUPTITLE_SIZE,
    "figure.titleweight": "bold",
    # Axes: open frame, muted, a rule across the value axis only.
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": MUTED,
    "axes.linewidth": 0.8,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.bottom": True,
    "ytick.left": True,
    "xtick.major.size": 3.5,
    "ytick.major.size": 3.5,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "grid.linestyle": "-",
    "grid.alpha": 1.0,
    # Legends: no box, but an opaque ground so the rules do not run through the text.
    "legend.frameon": True,
    "legend.fancybox": False,
    "legend.facecolor": "white",
    "legend.edgecolor": "none",
    "legend.framealpha": 0.9,
    "lines.linewidth": 1.8,
}


def apply():
    """Set the paper's rcParams. Call once, before the first figure."""
    mpl.rcParams.update(RC)


# --- Axes -----------------------------------------------------------------------------
def _flat(axes):
    for group in axes:
        yield from np.ravel(group) if isinstance(group, (np.ndarray, list, tuple)) else [group]


def tidy(*axes, grid="y"):
    """The line-plot frame, on axes that were styled otherwise or drawn before `apply`.

    Open at the top and right, the rest muted, and a rule across `grid` only -- "y" for
    anything plotted against time, "x" for a dot plot read along its rows. Takes loose
    axes or whatever `plt.subplots` returned, in any mix.
    """
    for ax in _flat(axes):
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_visible(True)
            ax.spines[side].set_color(MUTED)
        ax.tick_params(color=MUTED, labelcolor=INK)
        # Clear both first: a grid already on for both axes keeps the other direction
        # when only one is restyled.
        ax.grid(False)
        ax.grid(True, axis=grid, color=GRID, lw=0.8)
        ax.set_axisbelow(True)


def image_frame(*axes):
    """The frame for an image -- a heatmap or a surface: all four sides, no rules.

    Half a frame drawn round an image reads as a broken one rather than as a light touch.
    """
    for ax in _flat(axes):
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(MUTED)
        ax.tick_params(color=MUTED, labelcolor=INK)
        ax.grid(False)


def inset_frame(ax, size=SMALL_SIZE - 1.5):
    """The frame for an inset: boxed on an opaque ground, so it reads as its own plot."""
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(MUTED)
        spine.set_linewidth(0.8)
    ax.set_facecolor("white")
    ax.tick_params(color=MUTED, labelcolor=INK, labelsize=size, length=2.5)
    ax.grid(False)
    ax.grid(True, axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)


# --- Panels ---------------------------------------------------------------------------
def panel_title(ax, letter, title, **kwargs):
    """Name one panel of a multi-panel figure: "a. Title", bold and flush left."""
    return ax.set_title(f"{letter}. {title}", loc="left", fontweight="bold", **kwargs)


def letter_panels(axes, titles, **kwargs):
    """Name the panels a, b, c... in reading order."""
    for letter, ax, title in zip(string.ascii_lowercase, _flat([axes]), titles):
        panel_title(ax, letter, title, **kwargs)

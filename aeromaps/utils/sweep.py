"""Run a scenario over a grid of lever settings, and draw the result.

A named scenario communicates a narrative while hiding its sensitivity; a sweep
exposes the sensitivity while losing the narrative. This module is the machinery
for the second: build every combination of a set of lever axes, reduce each run to
the series worth keeping, and persist the lot as one tidy frame.

The caller owns what a cell *means*. It passes the axes, a ``build(cell)`` that
returns a computed-ready process, and an ``extract(process, cell)`` that reduces
one run to a tidy frame. Nothing here knows what a lever is, which is what lets
the same runner serve a different study.

Each process is discarded as soon as it is reduced, so peak memory is one process
regardless of grid size.
"""

import itertools
from pathlib import Path

import pandas as pd


def grid(axes):
    """Every combination of the lever axes, in a stable order.

    Parameters
    ----------
    axes : mapping
        Axis name to its levels. Insertion order fixes the cell tuple order, and
        therefore the column order of the tidy frame.
    """
    return list(itertools.product(*axes.values()))


def run_grid(cells, build, extract, progress=True, label=None):
    """Compute every cell and concatenate the reduced results.

    Parameters
    ----------
    cells : sequence of tuple
        The grid, normally from :func:`grid`.
    build : callable
        ``build(cell)`` returning a process ready for ``compute()``.
    extract : callable
        ``extract(process, cell)`` returning a tidy frame for that run.
    progress : bool, optional
        Print one line per cell. A sweep is long enough that silence is worse
        than noise.
    label : callable, optional
        ``label(cell)`` for the progress line; defaults to joining the cell.
    """
    cells = list(cells)
    label = label or (lambda cell: " ".join(str(part) for part in cell))
    results = []
    for index, cell in enumerate(cells, start=1):
        if progress:
            print(f"[{index:3d}/{len(cells)}] {label(cell)}", flush=True)
        process = build(cell)
        process.compute()
        results.append(extract(process, cell))
        del process
    return pd.concat(results, ignore_index=True)


def write_results(tidy, path):
    """Persist a sweep as a gzipped tidy CSV.

    Gzipped CSV rather than parquet: it is a fraction of the raw size and, unlike
    parquet, needs nothing beyond the standard library, so committed results stay
    readable in a default environment.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tidy.to_csv(path, index=False, compression="gzip")
    return path


def read_results(path):
    """Read a persisted sweep."""
    return pd.read_csv(Path(path))


def tidy_to_wide(tidy, cell_keys, derived=None):
    """One row per (cell, year), with each variable as a column.

    Parameters
    ----------
    derived : mapping, optional
        Column name to ``f(frame)``, evaluated in order, for quantities computed
        from the stored ones rather than stored themselves. Intensities belong
        here: storing a ratio invites it to disagree with its own numerator.
    """
    frame = tidy.pivot_table(
        index=list(cell_keys) + ["year"], columns="variable", values="value"
    ).reset_index()
    for name, function in (derived or {}).items():
        frame[name] = function(frame)
    return frame


def summarise(tidy, cell_keys, year):
    """One row per cell: every variable at a single year."""
    snapshot = tidy[tidy["year"] == year]
    return snapshot.pivot_table(
        index=list(cell_keys), columns="variable", values="value"
    ).reset_index()


def plot_grid(
    frame,
    cell_keys,
    panels,
    color_by,
    first_year=None,
    alpha=0.18,
    figsize=(11, 12),
    highlight=None,
    highlight_styles=None,
    suptitle=None,
    colors=None,
):
    """Every cell as one translucent line, over several metrics.

    One line per cell at low opacity, so the density of the bundle carries the
    message rather than any single trajectory. That is the right reading when the
    cells do not form a single ordered family, which is exactly when an envelope
    would mislead by implying they do.

    Parameters
    ----------
    frame : DataFrame
        Wide-form results, from :func:`tidy_to_wide`.
    panels : sequence of tuple
        ``(column, title, ylabel, scale)`` per panel. Laid out two to a row, with
        the last cell of the grid left free for the legend.
    color_by : str
        Which axis separates the colours; the others vary within each colour.
    highlight : mapping, optional
        ``{name: cell}`` drawn on top in black, for cases that must be locatable
        inside the spread they belong to -- a study's own published scenarios,
        say. The caller supplies these because "published" is not a property this
        module can know.
    highlight_styles : mapping, optional
        ``{name: linestyle}`` for those overlays.
    """
    import matplotlib.pyplot as plt

    from aeromaps.plots.multi_scenario_plot import DEFAULT_COLORS

    cell_keys = list(cell_keys)
    if color_by not in cell_keys:
        raise ValueError(f"color_by must be one of {cell_keys}, got {color_by!r}")
    if first_year is not None:
        frame = frame[frame["year"] >= first_year]

    palette = colors or DEFAULT_COLORS
    levels = sorted(frame[color_by].unique())
    level_colors = {level: palette[index % len(palette)] for index, level in enumerate(levels)}

    highlight = highlight or {}
    highlight_styles = highlight_styles or {}

    rows = -(-(len(panels) + 1) // 2)  # room for the legend in the last cell
    figure, axes = plt.subplots(rows, 2, figsize=figsize, layout="constrained")
    axes = axes.ravel()
    for spare in axes[len(panels) :]:
        spare.axis("off")

    by_name = {tuple(cell): name for name, cell in highlight.items()}
    color_index = cell_keys.index(color_by)

    for axis, (column, title, ylabel, scale) in zip(axes, panels):
        for cell, group in frame.groupby(cell_keys, sort=False):
            group = group.sort_values("year")
            axis.plot(
                group["year"],
                group[column] * scale,
                color=level_colors[cell[color_index]],
                linewidth=1.0,
                alpha=alpha,
                zorder=1,
            )
        # Highlights last, so they sit above the bundle.
        for cell, name in by_name.items():
            group = frame
            for key, value in zip(cell_keys, cell):
                group = group[group[key] == value]
            if group.empty:
                continue
            group = group.sort_values("year")
            axis.plot(
                group["year"],
                group[column] * scale,
                color="black",
                linewidth=2.0,
                linestyle=highlight_styles.get(name, "-"),
                zorder=5,
                label=name,
            )
        axis.set_title(title)
        axis.set_ylabel(ylabel)
        axis.set_xlabel("Year")
        axis.grid(True, alpha=0.3)

    handles = [
        plt.Line2D([], [], color=level_colors[level], linewidth=2, label=f"{color_by} = {level}")
        for level in levels
    ]
    handles += [
        plt.Line2D(
            [],
            [],
            color="black",
            linewidth=2,
            linestyle=highlight_styles.get(name, "-"),
            label=name,
        )
        for name in sorted(highlight)
    ]
    axes[-1].legend(handles=handles, loc="center", frameon=False, fontsize=11)
    if suptitle:
        figure.suptitle(suptitle)
    return figure

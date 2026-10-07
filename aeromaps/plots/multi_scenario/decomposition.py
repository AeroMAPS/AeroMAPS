"""Mitigation-wedge decomposition across several scenarios, one panel each.

A wedge chart cannot be overlaid the way a line chart can, since two filled
stacks would hide each other, so the comparison is drawn as a row of panels on a
shared vertical axis. That shared axis is the point: it makes the distance
between scenarios readable as a distance rather than requiring the reader to
compare two independently scaled charts.
"""

import matplotlib.pyplot as plt

from aeromaps.plots.single_scenario.decomposition import wedge_fills
from aeromaps.utils.decomposition import (
    DEFAULT_COLORS,
    DEFAULT_LABELS,
    mitigation_wedges,
)


class MitigationWedgeComparison:
    """One decomposition panel per scenario, sharing a vertical axis.

    This does not inherit ``MultiScenarioPlot``: that base class is built for
    overlaying series on a single axis, with grouping, envelopes and a shared
    legend, none of which apply to a stack of filled bands. What it shares with
    the rest of the comparison plots is the constructor contract, so it is
    constructed and used the same way.

    Parameters
    ----------
    processes : dict
        Scenario name to process or results view. Panel order follows insertion
        order, so the caller controls it.
    anchors : sequence, optional
        Counterfactual scenarios bounding the technology pillar, shared by every
        panel. Passing them once is deliberate: anchors that differed per panel
        would make the wedges incomparable across the row.
    """

    def __init__(
        self,
        processes,
        anchors=(),
        start_year=2024,
        colors=None,
        labels=None,
        fig=None,
        axes=None,
        legend=True,
        figsize=None,
        sharey=True,
    ):
        if not isinstance(processes, dict):
            processes = {getattr(p, "name", str(i)): p for i, p in enumerate(processes)}
        self.processes = processes
        self.anchors = tuple(anchors)
        self.start_year = start_year
        self.colors = {**DEFAULT_COLORS, **(colors or {})}
        self.labels = {**DEFAULT_LABELS, **(labels or {})}

        count = len(processes)
        if fig is not None and axes is not None:
            self.fig, self.axes = fig, list(axes)
        else:
            figsize = figsize or (5.2 * count, 4.2)
            self.fig, axes_array = plt.subplots(
                1, count, figsize=figsize, sharey=sharey, layout="constrained"
            )
            self.axes = list(axes_array) if count > 1 else [axes_array]

        self.create_plot()
        if legend:
            # One legend for the row. The pillars are the same in every panel, so
            # repeating it per panel would cover the bands it describes.
            handles, names = self.axes[0].get_legend_handles_labels()
            location = legend if isinstance(legend, str) else "upper right"
            self.axes[-1].legend(handles, names, loc=location, fontsize=7, framealpha=0.9)

    def create_plot(self):
        fills = wedge_fills(len(self.anchors))
        for ax, (name, process) in zip(self.axes, self.processes.items()):
            years, boundaries = mitigation_wedges(
                process, anchors=self.anchors, start_year=self.start_year
            )
            for upper, lower, key, labelled in fills:
                ax.fill_between(
                    years,
                    boundaries[upper],
                    boundaries[lower],
                    color=self.colors[key],
                    label=self.labels[key] if labelled else None,
                    linewidth=0,
                )

            historic = years < self.start_year
            prospective = years >= self.start_year - 1
            ax.plot(
                years[historic],
                boundaries[-2][historic],
                color="black",
                linewidth=2.4,
                label="Historical combustion CO$_2$",
                zorder=5,
            )
            ax.plot(
                years[prospective],
                boundaries[-1][prospective],
                color="#8e44ad",
                linestyle="--",
                linewidth=2,
                label="Net CO$_2$ emissions (projection)",
                zorder=5,
            )
            if self.anchors:
                ax.plot(
                    years[prospective],
                    boundaries[0][prospective],
                    color="black",
                    linestyle=":",
                    linewidth=1.4,
                    label="Frozen-technology baseline",
                    zorder=5,
                )

            ax.set_title(name)
            ax.set_xlim(years[0], years[-1])
            ax.set_xlabel("Year")
            ax.grid(alpha=0.3)

        self.axes[0].set_ylabel("Annual CO$_2$ emissions [MtCO$_2$]")

"""Mitigation-wedge decomposition of one scenario's CO2 trajectory."""

from aeromaps.plots.single_scenario_plot import SingleScenarioPlot, plot_1_x, plot_1_y
from aeromaps.utils.decomposition import (
    DEFAULT_COLORS,
    DEFAULT_LABELS,
    mitigation_wedges,
)


def wedge_fills(anchor_count):
    """(upper, lower, key, labelled) for each band, top to bottom.

    ``mitigation_wedges`` returns the anchors first, then the scenario's own
    post-technology trajectory, the alternative-aircraft boundary, the
    post-operations one, the gross trajectory and the net one. So the technology
    pillar is however many anchor gaps there are plus the alternative-aircraft
    band, and everything below it is fixed.

    The technology pillar is drawn in two pieces carrying one legend entry, which
    is why the second piece is unlabelled: splitting the band in two in the legend
    would imply two levers where the roadmap names one.
    """
    if anchor_count >= 2:
        # Only the outermost pair is fleet renewal; any further anchors and the
        # alternative-aircraft band all belong to next generation technology.
        bands = [(0, 1, "fleet_renewal", True)]
        bands += [(i, i + 1, "next_generation", i == 1) for i in range(1, anchor_count)]
        bands.append((anchor_count, anchor_count + 1, "next_generation", False))
    elif anchor_count == 1:
        bands = [(0, 1, "technology", True), (1, 2, "technology", False)]
    else:
        bands = [(0, 1, "technology", True)]

    base = anchor_count + 1
    bands += [
        (base, base + 1, "operations", True),
        (base + 1, base + 2, "fuel", True),
        (base + 2, base + 3, "market_based", True),
    ]
    return bands


class MitigationWedgeDecomposition(SingleScenarioPlot):
    """Annual CO2 decomposed into the pillars a decarbonisation roadmap names.

    Parameters
    ----------
    anchors : sequence, optional
        Counterfactual scenarios bounding the technology pillar from above,
        outermost first. ``(frozen, renewal_only)`` gives the fleet-renewal and
        next-generation split; see ``aeromaps.utils.decomposition``.
    start_year : int, optional
        Year the energy split is measured against, and where the projection is
        drawn from. Defaults to 2024.
    colors, labels : dict, optional
        Overrides for the pillar palette and names, merged over the defaults.
    """

    required_outputs = [
        "co2_emissions_including_energy",
        "co2_emissions_including_aircraft_efficiency",
        "co2_emissions_including_load_factor",
        "carbon_offset",
        "energy_consumption_dropin_fuel",
        "dropin_fuel_mean_co2_emission_factor",
        "co2_per_energy_mean",
    ]

    def __init__(
        self,
        process,
        anchors=(),
        start_year=2024,
        colors=None,
        labels=None,
        title=None,
        figsize=None,
        **kwargs,
    ):
        # Set before super().__init__, which calls create_plot() on the way out.
        self.anchors = tuple(anchors)
        self.start_year = start_year
        self.colors = {**DEFAULT_COLORS, **(colors or {})}
        self.labels = {**DEFAULT_LABELS, **(labels or {})}
        self.title = title
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_1_x, plot_1_y)

    def create_plot(self):
        years, boundaries = mitigation_wedges(
            self.process, anchors=self.anchors, start_year=self.start_year
        )

        for upper, lower, key, labelled in wedge_fills(len(self.anchors)):
            self.ax.fill_between(
                years,
                boundaries[upper],
                boundaries[lower],
                color=self.colors[key],
                label=self.labels[key] if labelled else None,
                linewidth=0,
            )

        historic = years < self.start_year
        # One year of overlap, so the observed and projected lines meet rather
        # than leaving a gap at the handover.
        prospective = years >= self.start_year - 1

        self.ax.plot(
            years[historic],
            boundaries[-2][historic],
            color="black",
            linewidth=2.4,
            label="Historical combustion CO$_2$",
            zorder=5,
        )
        self.ax.plot(
            years[prospective],
            boundaries[-1][prospective],
            color="#8e44ad",
            linestyle="--",
            linewidth=2,
            label="Net CO$_2$ emissions (projection)",
            zorder=5,
        )
        if self.anchors:
            self.ax.plot(
                years[prospective],
                boundaries[0][prospective],
                color="black",
                linestyle=":",
                linewidth=1.4,
                label="Frozen-technology baseline",
                zorder=5,
            )

        self.ax.set_xlim(years[0], years[-1])
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Annual CO$_2$ emissions [MtCO$_2$]")
        self.ax.grid(alpha=0.3)
        if self.title:
            self.ax.set_title(self.title)
        self.ax.legend(loc="upper left", fontsize=7, framealpha=0.9)

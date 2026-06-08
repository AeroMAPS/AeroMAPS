"""Multi-scenario comparison plots for fuel supply and production.

All plots discover energy carriers dynamically via ``pathways_manager``.
"""

from aeromaps.plots.single_scenario_plot import plot_1_x

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


# ---------------------------------------------------------------------------
# Drop-in fuel supply breakdown (one subplot per scenario, stacked by origin)
# ---------------------------------------------------------------------------

class DropInSupplyBreakdownPlot(MultiScenarioPlot):
    """
    Compare drop-in fuel supply breakdown across scenarios.

    Shows a stacked area per scenario with one band per energy origin
    (fossil, biomass, electricity, …) for the ``dropin_fuel`` aircraft type.
    Origins are discovered from ``pathways_manager``.
    """

    required_outputs = []

    def _get_default_figsize(self):
        n = len(self.scenario_data)
        return (plot_1_x, max(4, 3 * n))

    def create_plot(self):
        scenario_items = list(self.scenario_data.items())
        n_scenarios = len(scenario_items)

        self.fig.clear()
        axes = self.fig.subplots(n_scenarios, 1, squeeze=False)

        if self.pathways_manager is not None:
            energy_origins = self.pathways_manager.get_all_types("energy_origin")
        else:
            energy_origins = []

        for idx, (scenario_name, data) in enumerate(scenario_items):
            ax = axes[idx, 0]
            years = data["years"]
            df = data["df"]

            stack_data, stack_labels, stack_colors = [], [], []
            fallback_idx = 0

            for origin in energy_origins:
                pathways = self.pathways_manager.get(
                    aircraft_type="dropin_fuel", energy_origin=origin
                )
                origin_energy = self._aggregate_pathways_energy(df, years, pathways)
                if origin_energy is not None and origin_energy.sum() > 0:
                    stack_data.append(origin_energy * 1e-12)
                    stack_labels.append(self._readable_label(origin))
                    stack_colors.append(self._get_origin_color(origin, fallback_idx))
                    fallback_idx += 1

            if stack_data:
                ax.stackplot(years, *stack_data, labels=stack_labels,
                             colors=stack_colors, alpha=0.8)
                ax.legend(loc="upper left", fontsize=9)
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, "No drop-in fuel data available",
                        ha="center", va="center", transform=ax.transAxes)

            ax.set_ylabel("Energy [EJ]", fontsize=10)
            ax.set_title(scenario_name, fontsize=11, fontweight="bold")
            if idx == n_scenarios - 1:
                ax.set_xlabel("Year", fontsize=12)

        self.fig.suptitle("Drop-in Fuel Supply Breakdown", fontsize=14, y=0.995)
        self.axes = axes

    def _update_plot_elements(self):
        self.fig.clear()
        self.create_plot()


# ---------------------------------------------------------------------------
# Single-line comparison plots (per aircraft type / energy origin)
# ---------------------------------------------------------------------------

class _PathwayAggregateComparisonPlot(MultiScenarioPlot):
    """Shared base for plots that sum a pathway-filtered energy column.

    Subclasses set ``pathway_filter`` (dict passed to
    ``pathways_manager.get``) and the usual ``y_label``/title configuration.
    Scenarios with no matching pathway columns plot as a flat zero line
    (``_aggregate_pathways_energy`` returns zeros in that case).
    """

    required_outputs = []
    pathway_filter = {}

    def _scenario_xy(self, scenario_name, data):
        pathways = (self.pathways_manager.get(**self.pathway_filter)
                    if self.pathways_manager is not None else [])
        energy = self._aggregate_pathways_energy(data["df"], data["years"], pathways)
        return data["years"], energy * 1e-12


class HydrogenSupplyComparisonPlot(_PathwayAggregateComparisonPlot):
    """Compare total hydrogen energy consumption across scenarios."""

    pathway_filter = {"aircraft_type": "hydrogen"}

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Hydrogen Energy Consumption [EJ]")
        self.ax.set_title("Hydrogen (LH2) Supply Comparison")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)


class ElectricSupplyComparisonPlot(_PathwayAggregateComparisonPlot):
    """Compare total electric/battery energy consumption across scenarios."""

    pathway_filter = {"aircraft_type": "electric"}

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Electric Energy Consumption [EJ]")
        self.ax.set_title("Electric / Battery Supply Comparison")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)


class BiofuelProductionComparisonPlot(_PathwayAggregateComparisonPlot):
    """Compare total biofuel (biomass-origin) energy across scenarios."""

    pathway_filter = {"energy_origin": "biomass"}

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Biofuel Production [EJ]")
        self.ax.set_title("Biofuel Production Comparison")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)


class ElectrofuelProductionComparisonPlot(_PathwayAggregateComparisonPlot):
    """Compare total electrofuel (electricity-origin drop-in) energy across scenarios."""

    pathway_filter = {"aircraft_type": "dropin_fuel", "energy_origin": "electricity"}

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Electrofuel Production [EJ]")
        self.ax.set_title("Electrofuel Production Comparison")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)


# ---------------------------------------------------------------------------
# Biofuel mix (per-pathway breakdown, one subplot per scenario)
# ---------------------------------------------------------------------------

class BiofuelMixComparisonPlot(MultiScenarioPlot):
    """
    Compare biofuel pathway mix across scenarios.

    Creates one subplot per scenario with a stacked area showing individual
    biomass-origin drop-in pathways (HEFA, FT, ATJ, …).
    """

    required_outputs = []

    # Palette cycled across individual biofuel pathways
    _PATHWAY_COLORS = [
        '#2ca02c', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22',
        '#17becf', '#9467bd', '#d62728', '#ff7f0e', '#1f77b4',
    ]

    def _get_default_figsize(self):
        n = len(self.scenario_data)
        return (plot_1_x, max(4, 3 * n))

    def create_plot(self):
        scenario_items = list(self.scenario_data.items())
        n_scenarios = len(scenario_items)

        self.fig.clear()
        axes = self.fig.subplots(n_scenarios, 1, squeeze=False)

        if self.pathways_manager is not None:
            bio_pathways = self.pathways_manager.get(
                aircraft_type="dropin_fuel", energy_origin="biomass"
            )
        else:
            bio_pathways = []

        for idx, (scenario_name, data) in enumerate(scenario_items):
            ax = axes[idx, 0]
            years = data["years"]
            df = data["df"]

            stack_data, stack_labels, stack_colors = [], [], []

            for p_idx, pathway in enumerate(bio_pathways):
                col = f"{pathway.name}_energy_consumption"
                if col in df.columns:
                    values = df.loc[years, col].fillna(0) * 1e-12
                    if values.sum() > 0:
                        stack_data.append(values)
                        stack_labels.append(self._readable_label(pathway.name))
                        stack_colors.append(
                            self._PATHWAY_COLORS[p_idx % len(self._PATHWAY_COLORS)]
                        )

            if stack_data:
                ax.stackplot(years, *stack_data, labels=stack_labels,
                             colors=stack_colors, alpha=0.8)
                ax.legend(loc="upper left", fontsize=9, ncol=2)
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, "No biofuel pathway data available",
                        ha="center", va="center", transform=ax.transAxes)

            ax.set_ylabel("Biofuel Production [EJ]", fontsize=10)
            ax.set_title(scenario_name, fontsize=11, fontweight="bold")
            if idx == n_scenarios - 1:
                ax.set_xlabel("Year", fontsize=12)

        self.fig.suptitle("Biofuel Mix Comparison Across Scenarios", fontsize=14, y=0.995)
        self.axes = axes

    def _update_plot_elements(self):
        self.fig.clear()
        self.create_plot()

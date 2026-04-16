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
# Single-line comparison plots for a given aircraft type
# ---------------------------------------------------------------------------

class HydrogenSupplyComparisonPlot(MultiScenarioPlot):
    """Compare total hydrogen energy consumption across scenarios."""

    required_outputs = []

    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            years = data["years"]
            df = data["df"]

            if self.pathways_manager is not None:
                pathways = self.pathways_manager.get(aircraft_type="hydrogen")
                hydrogen = self._aggregate_pathways_energy(df, years, pathways)
            else:
                hydrogen = None

            if hydrogen is not None:
                self.ax.plot(
                    years, hydrogen * 1e-12,
                    label=scenario_name,
                    color=style["color"],
                    linestyle=style["linestyle"],
                    linewidth=2,
                )

        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Hydrogen Energy Consumption [EJ]")
        self.ax.set_title("Hydrogen (LH2) Supply Comparison")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


class ElectricSupplyComparisonPlot(MultiScenarioPlot):
    """Compare total electric/battery energy consumption across scenarios."""

    required_outputs = []


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            years = data["years"]
            df = data["df"]

            if self.pathways_manager is not None:
                pathways = self.pathways_manager.get(aircraft_type="electric")
                electric = self._aggregate_pathways_energy(df, years, pathways)
            else:
                electric = None

            if electric is not None:
                self.ax.plot(
                    years, electric * 1e-12,
                    label=scenario_name,
                    color=style["color"],
                    linestyle=style["linestyle"],
                    linewidth=2,
                )

        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Electric Energy Consumption [EJ]")
        self.ax.set_title("Electric / Battery Supply Comparison")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


# ---------------------------------------------------------------------------
# Aggregate by energy origin across all aircraft types
# ---------------------------------------------------------------------------

class BiofuelProductionComparisonPlot(MultiScenarioPlot):
    """Compare total biofuel (biomass-origin) energy across scenarios."""

    required_outputs = []


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            years = data["years"]
            df = data["df"]

            if self.pathways_manager is not None:
                pathways = self.pathways_manager.get(energy_origin="biomass")
                biofuel = self._aggregate_pathways_energy(df, years, pathways)
            else:
                biofuel = None

            if biofuel is not None:
                self.ax.plot(
                    years, biofuel * 1e-12,
                    label=scenario_name,
                    color=style["color"],
                    linestyle=style["linestyle"],
                    linewidth=2,
                )

        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Biofuel Production [EJ]")
        self.ax.set_title("Biofuel Production Comparison")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


class ElectrofuelProductionComparisonPlot(MultiScenarioPlot):
    """Compare total electrofuel (electricity-origin drop-in) energy across scenarios."""

    required_outputs = []


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            years = data["years"]
            df = data["df"]

            if self.pathways_manager is not None:
                pathways = self.pathways_manager.get(
                    aircraft_type="dropin_fuel", energy_origin="electricity"
                )
                efuel = self._aggregate_pathways_energy(df, years, pathways)
            else:
                efuel = None

            if efuel is not None:
                self.ax.plot(
                    years, efuel * 1e-12,
                    label=scenario_name,
                    color=style["color"],
                    linestyle=style["linestyle"],
                    linewidth=2,
                )

        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Electrofuel Production [EJ]")
        self.ax.set_title("Electrofuel Production Comparison")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


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

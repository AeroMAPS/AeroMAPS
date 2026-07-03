"""Multi-scenario comparison plots for energy consumption."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot
from aeromaps.plots.single_scenario_plot import plot_1_x


class EnergyConsumptionComparisonPlot(MultiScenarioPlot):
    """Compare total energy consumption across multiple scenarios."""

    required_outputs = ["energy_consumption"]
    column_name = "energy_consumption"
    y_scale = 1e-12  # convert to EJ

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Total Energy Consumption [EJ]")
        self.ax.set_title("Energy Consumption Comparison Across Scenarios")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class EnergyMixComparisonPlot(MultiScenarioPlot):
    """
    Compare energy mix across scenarios.

    Creates one subplot per scenario showing a stacked area of energy by
    origin (fossil, biomass, electricity, …).  Energy origins and their
    columns are discovered dynamically from ``pathways_manager``.
    """

    # Columns are dynamic — no static required_outputs
    required_outputs = []

    def _get_default_figsize(self):
        n_scenarios = len(self.scenario_data)
        return (plot_1_x, max(4, 3 * n_scenarios))

    def create_plot(self):
        scenario_items = list(self.scenario_data.items())
        n_scenarios = len(scenario_items)

        self.fig.clear()
        axes = self.fig.subplots(n_scenarios, 1, squeeze=False)

        # Determine common x-limits from prospective_years
        all_min, all_max = None, None
        for _, data in scenario_items:
            yrs = data.get("prospective_years") or data.get("years")
            if yrs is not None and len(yrs) > 0:
                if all_min is None or yrs[0] < all_min:
                    all_min = yrs[0]
                if all_max is None or yrs[-1] > all_max:
                    all_max = yrs[-1]

        # Discover energy origins from pathways_manager
        if self.pathways_manager is not None:
            energy_origins = self.pathways_manager.get_all_types("energy_origin")
        else:
            energy_origins = []

        for idx, (scenario_name, data) in enumerate(scenario_items):
            ax = axes[idx, 0]
            years = data["years"]
            df = data["df"]

            stack_data = []
            stack_labels = []
            stack_colors = []
            fallback_idx = 0

            for origin in energy_origins:
                pathways = self.pathways_manager.get(energy_origin=origin)
                origin_energy = self._aggregate_pathways_energy(df, years, pathways)
                if origin_energy is not None and origin_energy.sum() > 0:
                    stack_data.append(origin_energy * 1e-12)
                    stack_labels.append(self._readable_label(origin))
                    stack_colors.append(self._get_origin_color(origin, fallback_idx))
                    fallback_idx += 1

            if stack_data:
                ax.stackplot(
                    years, *stack_data, labels=stack_labels, colors=stack_colors, alpha=0.8
                )
                ax.legend(loc="upper left", fontsize=9)
                ax.grid(True, alpha=0.3)
            else:
                ax.text(
                    0.5,
                    0.5,
                    "No energy data available",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )

            ax.set_ylabel("Energy [EJ]", fontsize=10)
            ax.set_title(scenario_name, fontsize=11, fontweight="bold")
            if all_min is not None:
                ax.set_xlim(all_min, all_max)
            if idx == n_scenarios - 1:
                ax.set_xlabel("Year", fontsize=12)

        self.fig.suptitle("Energy Mix Comparison Across Scenarios", fontsize=14, y=0.995)
        self.axes = axes

    def _update_plot_elements(self):
        self.fig.clear()
        self.create_plot()

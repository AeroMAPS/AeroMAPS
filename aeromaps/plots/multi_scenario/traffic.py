"""Multi-scenario comparison plots for air traffic."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class RPKComparisonPlot(MultiScenarioPlot):
    """Compare Revenue Passenger Kilometers across multiple scenarios."""

    required_outputs = ["rpk"]
    column_name = "rpk"
    y_scale = 1e-12  # convert to trillion pkm

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Revenue Passenger Kilometers [trillion pkm]", fontsize=12)
        self.ax.set_title("RPK Comparison Across Scenarios", fontsize=14)
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class LoadFactorComparisonPlot(MultiScenarioPlot):
    """Compare aircraft load factor across multiple scenarios."""

    required_outputs = ["load_factor"]
    column_name = "load_factor"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Load Factor [%]", fontsize=12)
        self.ax.set_title("Load Factor Comparison Across Scenarios", fontsize=14)
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(0, 100)

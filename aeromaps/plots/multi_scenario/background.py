"""Multi-scenario comparison plots for the background scenario drivers.

These are the quantities a scenario takes from its socioeconomic pathway rather
than computes: population, income per capita and the exogenous carbon price. They
belong beside the other comparison plots so that a figure mixing drivers with
results can draw every panel through the same code path, and therefore share the
grouping, colour and envelope behaviour.
"""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class PopulationComparisonPlot(MultiScenarioPlot):
    """Compare population across multiple scenarios."""

    required_outputs = ["population"]
    column_name = "population"
    y_scale = 1e-9  # convert to billions

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Population [billion]", fontsize=12)
        self.ax.set_title("Population Comparison Across Scenarios", fontsize=14)
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class GDPPerCapitaComparisonPlot(MultiScenarioPlot):
    """Compare income per capita across multiple scenarios."""

    required_outputs = ["gdp_per_capita"]
    column_name = "gdp_per_capita"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("GDP per capita [USD]", fontsize=12)
        self.ax.set_title("GDP per Capita Comparison Across Scenarios", fontsize=14)
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class CarbonPriceComparisonPlot(MultiScenarioPlot):
    """Compare the exogenous carbon price trajectory across multiple scenarios."""

    required_outputs = ["exogenous_carbon_price_trajectory"]
    column_name = "exogenous_carbon_price_trajectory"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Carbon price [USD/tCO2]", fontsize=12)
        self.ax.set_title("Carbon Price Comparison Across Scenarios", fontsize=14)
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)

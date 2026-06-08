"""Multi-scenario comparison plots for intensity metrics."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class CO2PerRPKComparisonPlot(MultiScenarioPlot):
    """Compare CO2 emissions per passenger kilometer across scenarios."""

    required_outputs = ["co2_emissions_per_rpk"]
    column_name = "co2_emissions_per_rpk"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("CO2 per RPK [gCO2/RPK]", fontsize=12)
        self.ax.set_title("Carbon Intensity per Passenger Kilometer", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)


class CO2PerRTKComparisonPlot(MultiScenarioPlot):
    """Compare CO2 emissions per revenue tonne kilometer across scenarios."""

    required_outputs = ["co2_emissions_per_rtk"]
    column_name = "co2_emissions_per_rtk"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("CO2 per RTK [gCO2/RTK]", fontsize=12)
        self.ax.set_title("Carbon Intensity per Revenue Tonne Kilometer", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)


class EnergyPerASKComparisonPlot(MultiScenarioPlot):
    """Compare energy consumption per available seat kilometer across scenarios."""

    required_outputs = ["energy_per_ask_mean"]
    column_name = "energy_per_ask_mean"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Energy per ASK [MJ/ASK]", fontsize=12)
        self.ax.set_title("Energy Intensity per Available Seat Kilometer", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)


class EnergyPerRTKComparisonPlot(MultiScenarioPlot):
    """Compare energy consumption per revenue tonne kilometer across scenarios."""

    required_outputs = ["energy_per_rtk_mean"]
    column_name = "energy_per_rtk_mean"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Energy per RTK [MJ/RTK]", fontsize=12)
        self.ax.set_title("Energy Intensity per Revenue Tonne Kilometer", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)

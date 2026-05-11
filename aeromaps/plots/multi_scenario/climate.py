"""Multi-scenario comparison plots for climate metrics."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class TotalERFComparisonPlot(MultiScenarioPlot):
    """Compare total effective radiative forcing (ERF) across scenarios."""

    required_outputs = ["total_erf"]
    column_name = "total_erf"
    data_source = "df_climate"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Total Effective Radiative Forcing Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Total ERF [mW/m²]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class TemperatureIncreaseComparisonPlot(MultiScenarioPlot):
    """Compare temperature increase from aviation across scenarios."""

    required_outputs = ["temperature_increase_from_aviation"]
    column_name = "temperature_increase_from_aviation"
    data_source = "df_climate"
    y_scale = 1000  # convert from K to mK

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Temperature Increase from Aviation Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Temperature increase [mK]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class CO2ERFComparisonPlot(MultiScenarioPlot):
    """Compare CO2 effective radiative forcing across scenarios."""

    required_outputs = ["co2_erf"]
    column_name = "co2_erf"
    data_source = "df_climate"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("CO₂ Effective Radiative Forcing Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("CO₂ ERF [mW/m²]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class NonCO2ERFComparisonPlot(MultiScenarioPlot):
    """Compare non-CO2 ERF across scenarios (total minus CO2)."""

    required_outputs = ["total_erf", "co2_erf"]

    def _scenario_xy(self, scenario_name, data):
        df = data["df_climate"]
        x = data["years"]
        return x, df.loc[x, "total_erf"] - df.loc[x, "co2_erf"]

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Non-CO₂ Effective Radiative Forcing Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Non-CO₂ ERF [mW/m²]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)

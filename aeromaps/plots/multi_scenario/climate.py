"""Multi-scenario comparison plots for climate metrics."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class TotalERFComparisonPlot(MultiScenarioPlot):
    """Compare total effective radiative forcing (ERF) across scenarios."""

    required_outputs = ["total_erf"]


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            self.ax.plot(
                data["years"],
                data["df_climate"].loc[data["years"], "total_erf"],
                label=scenario_name,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2,
            )

        self.ax.set_title("Total Effective Radiative Forcing Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Total ERF [mW/m²]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


class TemperatureIncreaseComparisonPlot(MultiScenarioPlot):
    """Compare temperature increase from aviation across scenarios."""

    required_outputs = ["temperature_increase_from_aviation"]


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            self.ax.plot(
                data["years"],
                data["df_climate"].loc[data["years"], "temperature_increase_from_aviation"] * 1000,
                label=scenario_name,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2,
            )

        self.ax.set_title("Temperature Increase from Aviation Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Temperature increase [mK]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


class CO2ERFComparisonPlot(MultiScenarioPlot):
    """Compare CO2 effective radiative forcing across scenarios."""

    required_outputs = ["co2_erf"]


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            self.ax.plot(
                data["years"],
                data["df_climate"].loc[data["years"], "co2_erf"],
                label=scenario_name,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2,
            )

        self.ax.set_title("CO₂ Effective Radiative Forcing Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("CO₂ ERF [mW/m²]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


class NonCO2ERFComparisonPlot(MultiScenarioPlot):
    """Compare non-CO2 effective radiative forcing across scenarios (total minus CO2)."""

    required_outputs = ["total_erf", "co2_erf"]


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            df = data["df_climate"]
            years = data["years"]
            self.ax.plot(
                years,
                df.loc[years, "total_erf"] - df.loc[years, "co2_erf"],
                label=scenario_name,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2,
            )

        self.ax.set_title("Non-CO₂ Effective Radiative Forcing Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Non-CO₂ ERF [mW/m²]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()

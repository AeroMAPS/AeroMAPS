import matplotlib.pyplot as plt
import numpy as np

from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
from aeromaps.plots.single_scenario_plot import plot_3_x
from aeromaps.plots.single_scenario_plot import plot_3_y


class BiomassConsumptionPlot(SingleScenarioPlot):
    required_outputs = [
        "biomass_total_consumption",
    ]

    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        (self.line_biomass_consumption,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "biomass_total_consumption"] / 1e12,
            color="blue",
            linestyle="-",
            label="Aviation biomass consumption",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of biomass consumption\nfrom air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Biomass consumption [EJ]")
        
        self.ax.legend()
        self.ax.set_xlim(2020, self.years[-1])

    def _update_plot_elements(self):
        self.line_biomass_consumption.set_ydata(
            self.df.loc[self.prospective_years, "biomass_total_consumption"] / 1e12
        )


class ElectricityConsumptionPlot(SingleScenarioPlot):
    required_outputs = [
        "electricity_total_consumption",
    ]

    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        (self.line_electricity_consumption,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "electricity_total_consumption"] / 1e12,
            color="blue",
            linestyle="-",
            label="Aviation electricity consumption",
            linewidth=2,
        )

        (self.line_france_production_2019,) = self.ax.plot(
            self.prospective_years,
            np.ones(len(self.prospective_years)) * 537.7 * 3.6 / 1000,
            color="black",
            linestyle="--",
            label="France electricity production (2019)",
            linewidth=1,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of electricity consumption\nfrom air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Electricity consumption [EJ]")
        
        self.ax.legend()
        self.ax.set_xlim(2020, self.years[-1])

        # self.ax_twin = self.ax.twinx()
        # self.ax_twin.set_ylabel("Electricity consumption [TWh]")
        # function_ej_to_twh = lambda elec: elec * 1000 / 3.6
        # ymin, ymax = self.ax.get_ylim()
        # self.ax_twin.set_ylim((function_ej_to_twh(ymin), function_ej_to_twh(ymax)))
        # self.ax_twin.plot([], [])

    def _update_plot_elements(self):
        self.line_electricity_consumption.set_ydata(
            self.df.loc[self.prospective_years, "electricity_total_consumption"] / 1e12
        )

        self.line_france_production_2019.set_ydata(
            np.ones(len(self.prospective_years)) * 537.7 * 3.6 / 1000
        )

import matplotlib.pyplot as plt
import numpy as np
from .constants import plot_3_x, plot_3_y


class BiomassConsumptionPlot:
    def __init__(self, data):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_3_x, plot_3_y),
        )
        self.create_plot()

    def create_plot(self):
        (self.line_biomass_consumption,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "biomass_consumption"],
            color="blue",
            linestyle="-",
            label="Aviation biomass consumption",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of biomass consumption\nfrom air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Biomass consumption [EJ]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2020, 2050)

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, data):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.line_biomass_consumption.set_ydata(
            self.df.loc[self.prospective_years, "biomass_consumption"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class ElectricityConsumptionPlot:
    def __init__(self, data):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_3_x, plot_3_y),
        )
        self.create_plot()

    def create_plot(self):

        (self.line_electricity_consumption,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "electricity_consumption"],
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
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2020, 2050)

        # self.ax_twin = self.ax.twinx()
        # self.ax_twin.set_ylabel("Electricity consumption [TWh]")
        # function_ej_to_twh = lambda elec: elec * 1000 / 3.6
        # ymin, ymax = self.ax.get_ylim()
        # self.ax_twin.set_ylim((function_ej_to_twh(ymin), function_ej_to_twh(ymax)))
        # self.ax_twin.plot([], [])

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, data):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.line_electricity_consumption.set_ydata(
            self.df.loc[self.prospective_years, "electricity_consumption"]
        )

        self.line_france_production_2019.set_ydata(
            np.ones(len(self.prospective_years)) * 537.7 * 3.6 / 1000
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        # self.ax_twin.relim()
        # self.ax_twin.autoscale_view()
        self.fig.canvas.draw()

import matplotlib.pyplot as plt
import numpy as np
from .constants import plot_3_x, plot_3_y


class DropinFuelConsumptionLiterPerPAX100kmPlot:
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
        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "dropin_fuel_consumption_liter_per_pax_100km"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_fuel_consumption_l100km,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "dropin_fuel_consumption_liter_per_pax_100km"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of (drop-in) fuel consumption\nper passenger for air transport"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Fuel consumption per passenger [L/100km]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2000, 2050)

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

        self.line_fuel_consumption_l100km.set_ydata(
            self.df.loc[self.prospective_years, "dropin_fuel_consumption_liter_per_pax_100km"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class MeanLoadFactorPlot:
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
        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "load_factor"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_load_factor,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "load_factor"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of the aircraft load factor")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Aircraft load factor [%]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2000, 2050)

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

        self.line_load_factor.set_ydata(self.df.loc[self.prospective_years, "load_factor"])

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class MeanEnergyPerASKPlot:
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
        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "energy_per_ask_mean"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_energy_per_ask,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "energy_per_ask_mean"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of the mean energy consumed\nper Available Seat Kilometer (ASK)"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy per Available Seat Kilometer [MJ/ASK]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2000, 2050)

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

        self.line_energy_per_ask.set_ydata(
            self.df.loc[self.prospective_years, "energy_per_ask_mean"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class MeanEnergyPerRTKPlot:
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
        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "energy_per_rtk_mean"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_energy_per_rtk,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "energy_per_rtk_mean"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of the mean energy consumed\nper Revenue Tonne Kilometer (RTK)"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy per Revenue Tonne Kilometer [MJ/RTK]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2000, 2050)

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

        self.line_energy_per_rtk.set_ydata(
            self.df.loc[self.prospective_years, "energy_per_rtk_mean"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()

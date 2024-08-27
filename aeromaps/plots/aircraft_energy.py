import matplotlib.pyplot as plt
from .constants import plot_3_x, plot_3_y


class MeanFuelEmissionFactorPlot:
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
            self.df.loc[self.historic_years, "co2_per_energy_mean"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_fuel_emission_factor,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "co2_per_energy_mean"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of the mean emission factor\nof the air transport energy mix (gCO2-eq/MJ)"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Fuel emission factor [gCO2-eq/MJ]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(self.years[0], self.years[-1])

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

        self.line_fuel_emission_factor.set_ydata(
            self.df.loc[self.prospective_years, "co2_per_energy_mean"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class EmissionFactorPerFuelPlot:
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
        (self.line_biofuel_mean_emission_factor,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "biofuel_mean_emission_factor"],
            color="green",
            linestyle="-",
            label="Biofuel",
            linewidth=2,
        )

        (self.line_hydrogen_mean_emission_factor,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "liquid_hydrogen_mean_emission_factor"],
            color="blue",
            linestyle="-",
            label="Hydrogen",
            linewidth=2,
        )

        (self.line_electrofuel_emission_factor,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "electrofuel_emission_factor"],
            color="red",
            linestyle="-",
            label="Electrofuel",
            linewidth=2,
        )

        (self.line_kerosene_emission_factor,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "kerosene_emission_factor"],
            color="black",
            linestyle="-",
            label="Kerosene",
            linewidth=2,
        )

        (self.line_electricity_emission_factor,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "electricity_emission_factor"] / 3.6,
            color="purple",
            linestyle="-",
            label="Electricity",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of the CO2 emission factor\nof aviation fuels")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Fuel emission factor [gCO2-eq/MJ]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(self.prospective_years[0] + 1, self.prospective_years[-1])
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

        self.line_biofuel_mean_emission_factor.set_ydata(
            self.df.loc[self.prospective_years, "biofuel_mean_emission_factor"]
        )

        self.line_hydrogen_mean_emission_factor.set_ydata(
            self.df.loc[self.prospective_years, "liquid_hydrogen_mean_emission_factor"]
        )

        self.line_electrofuel_emission_factor.set_ydata(
            self.df.loc[self.prospective_years, "electrofuel_emission_factor"]
        )

        self.line_kerosene_emission_factor.set_ydata(
            self.df.loc[self.prospective_years, "kerosene_emission_factor"]
        )

        self.line_electricity_emission_factor.set_ydata(
            self.df.loc[self.prospective_years, "electricity_emission_factor"] / 3.6
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class ShareDropinFuelPlot:
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
        (self.line_biofuel_share,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "biofuel_share"],
            color="green",
            linestyle="-",
            label="Biofuel",
            linewidth=2,
        )

        (self.line_electrofuel_share,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "electrofuel_share"],
            color="blue",
            linestyle="-",
            label="Electrofuel",
            linewidth=2,
        )

        (self.line_kerosene_share,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "kerosene_share"],
            color="red",
            linestyle="-",
            label="Kerosene",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of the shares of drop-in fuels")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Share [%]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])

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

        self.line_biofuel_share.set_ydata(self.df.loc[self.prospective_years, "biofuel_share"])

        self.line_electrofuel_share.set_ydata(
            self.df.loc[self.prospective_years, "electrofuel_share"]
        )

        self.line_kerosene_share.set_ydata(self.df.loc[self.prospective_years, "kerosene_share"])

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class EnergyConsumptionPlot:
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
            self.df.loc[self.historic_years, "energy_consumption"] / 10**12,
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_energy_consumption,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "energy_consumption"] / 10**12,
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of the air transport\nenergy consumption")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy consumption [EJ]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(self.years[0], self.years[-1])

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

        self.line_energy_consumption.set_ydata(
            self.df.loc[self.prospective_years, "energy_consumption"] / 10**12
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()

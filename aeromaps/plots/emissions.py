import matplotlib.pyplot as plt
import numpy as np
from .constants import plot_3_x, plot_3_y


class CumulativeCO2EmissionsPlot:
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
        (self.line_cumulative_co2_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "cumulative_co2_emissions"],
            color="blue",
            linestyle="-",
            label="Cumulative CO2 emissions",
            linewidth=2,
        )

        (self.line_aviation_carbon_budget,) = self.ax.plot(
            self.prospective_years,
            np.ones(len(self.prospective_years)) * self.float_outputs["aviation_carbon_budget"],
            color="black",
            linestyle="--",
            label="Aviation carbon budget",
            linewidth=1,
        )

        self.ax.grid()
        self.ax.set_title(
            "Comparison of cumulative CO2 emissions from air transport\nwith allocated carbon budget (from 2019)"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Cumulative CO2 emissions [GtCO2]")
        self.ax.legend()
        self.ax = plt.gca()
        self.ax.set_xlim(2019, 2050)

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

        self.line_cumulative_co2_emissions.set_ydata(
            self.df.loc[self.prospective_years, "cumulative_co2_emissions"]
        )

        self.line_aviation_carbon_budget.set_ydata(
            np.ones(len(self.prospective_years)) * self.float_outputs["aviation_carbon_budget"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DirectH2OEmissionsPlot:
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
            self.df.loc[self.historic_years, "h2o_emissions"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_h2o_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "h2o_emissions"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of direct H2O emissions\nfrom air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Direct H2O emissions [MtH2O]")
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

        self.line_h2o_emissions.set_ydata(self.df.loc[self.prospective_years, "h2o_emissions"])

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DirectNOxEmissionsPlot:
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
            self.df.loc[self.historic_years, "nox_emissions"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_nox_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "nox_emissions"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of direct NOx emissions\nfrom air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Direct NOx emissions [MtNOx]")
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

        self.line_nox_emissions.set_ydata(self.df.loc[self.prospective_years, "nox_emissions"])

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DirectSulfurEmissionsPlot:
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
            self.df.loc[self.historic_years, "sulfur_emissions"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_sulfur_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "sulfur_emissions"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of direct sulfur emissions\nfrom air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Direct sulfur emissions [MtSO2]")
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

        self.line_sulfur_emissions.set_ydata(
            self.df.loc[self.prospective_years, "sulfur_emissions"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DirectSootEmissionsPlot:
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
            self.df.loc[self.historic_years, "soot_emissions"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_soot_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "soot_emissions"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of direct soot emissions\nfrom air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Direct soot emissions [MtBC]")
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

        self.line_soot_emissions.set_ydata(self.df.loc[self.prospective_years, "soot_emissions"])

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class CarbonOffsetPlot:
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
            self.df.loc[self.historic_years, "carbon_offset"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_carbon_offset,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "carbon_offset"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of carbon offset\nfrom air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Carbon offset [MtCO2]")
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

        self.line_carbon_offset.set_ydata(self.df.loc[self.prospective_years, "carbon_offset"])

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class CumulativeCarbonOffsetPlot:
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
        (self.line_cumulative_carbon_offset,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "cumulative_carbon_offset"],
            color="blue",
            linestyle="-",
            label="Cumulative carbon offset",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Cumulative carbon offset from air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Cumulative carbon offset [GtCO2]")
        self.ax.legend()
        self.ax = plt.gca()
        self.ax.set_xlim(2019, 2050)

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

        self.line_cumulative_carbon_offset.set_ydata(
            self.df.loc[self.prospective_years, "cumulative_carbon_offset"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()

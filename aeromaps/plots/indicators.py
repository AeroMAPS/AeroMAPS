import matplotlib.pyplot as plt
import numpy as np
from .constants import plot_3_x, plot_3_y


class MeanCO2PerRPKPlot:
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
            self.df.loc[self.historic_years, "co2_emissions_per_rpk"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_emissions_per_rpk,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "co2_emissions_per_rpk"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of CO2 emissions\nper passenger and per kilometer")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("CO2 emissions per RPK [gCO2/RPK]")
        self.ax.legend(loc=0, fontsize=10)
        self.ax.set_xlim(2000, 2050)
        self.ax.set_ylim(
            0,
        )

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

        self.line_emissions_per_rpk.set_ydata(
            self.df.loc[self.prospective_years, "co2_emissions_per_rpk"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class MeanCO2PerRTKPlot:
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
            self.df.loc[self.historic_years, "co2_emissions_per_rtk"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_emissions_per_rtk,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "co2_emissions_per_rtk"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of CO2 emissions\nper tonne and per kilometer")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("CO2 emissions per RTK [gCO2/RTK]")
        self.ax.legend(loc=0, fontsize=10)
        self.ax.set_xlim(2000, 2050)
        self.ax.set_ylim(
            0,
        )

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

        self.line_emissions_per_rtk.set_ydata(
            self.df.loc[self.prospective_years, "co2_emissions_per_rtk"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class PassengerKayaFactorsPlot:
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
        (self.line_co2,) = self.ax.plot(
            self.years,
            self.df["co2_emissions_passenger"] / self.df.loc[2000, "co2_emissions_passenger"],
            color="blue",
            linestyle="-",
            label="CO2",
            linewidth=3,
        )

        (self.line_rpk,) = self.ax.plot(
            self.years,
            self.df["rpk"] / self.df.loc[2000, "rpk"],
            color="red",
            linestyle="--",
            label="RPK",
            linewidth=2,
        )

        (self.line_energy_per_rpk,) = self.ax.plot(
            self.years,
            self.df["energy_per_ask_mean"]
            / self.df["load_factor"]
            / (self.df.loc[2000, "energy_per_ask_mean"] / self.df.loc[2000, "load_factor"]),
            color="gold",
            linestyle="--",
            label="E/ASK",
            linewidth=2,
        )

        (self.line_co2_per_energy,) = self.ax.plot(
            self.years,
            self.df["co2_per_energy_mean"] / self.df.loc[2000, "co2_per_energy_mean"],
            color="green",
            linestyle="--",
            label="CO2/E",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of the factors in the Kaya equation\nfor passenger air transport (historical until 2019)"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Reference to 2000 with logarithmic scale")
        self.ax.legend()
        ax = plt.gca()
        self.ax.set_xlim(2000, 2050)
        self.ax.set_yscale("log")

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

        self.line_co2.set_ydata(
            self.df["co2_emissions_passenger"] / self.df.loc[2000, "co2_emissions_passenger"]
        )

        self.line_rpk.set_ydata(self.df["rpk"] / self.df.loc[2000, "rpk"])

        self.line_energy_per_rpk.set_ydata(
            self.df["energy_per_ask_mean"]
            / self.df["load_factor"]
            / (self.df.loc[2000, "energy_per_ask_mean"] / self.df.loc[2000, "load_factor"])
        )

        self.line_co2_per_energy.set_ydata(
            self.df["co2_per_energy_mean"] / self.df.loc[2000, "co2_per_energy_mean"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class FreightKayaFactorsPlot:
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
        (self.line_co2,) = self.ax.plot(
            self.years,
            self.df["co2_emissions_freight"] / self.df.loc[2000, "co2_emissions_freight"],
            color="blue",
            linestyle="-",
            label="CO2",
            linewidth=3,
        )

        (self.line_rtk,) = self.ax.plot(
            self.years,
            self.df["rtk"] / self.df.loc[2000, "rtk"],
            color="red",
            linestyle="--",
            label="RTK",
            linewidth=2,
        )

        (self.line_energy_per_rtk,) = self.ax.plot(
            self.years,
            self.df["energy_per_rtk_mean"] / self.df.loc[2000, "energy_per_rtk_mean"],
            color="gold",
            linestyle="--",
            label="E/RTK",
            linewidth=2,
        )

        (self.line_co2_per_energy,) = self.ax.plot(
            self.years,
            self.df["co2_per_energy_mean"] / self.df.loc[2000, "co2_per_energy_mean"],
            color="green",
            linestyle="--",
            label="CO2/E",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of the factors in the Kaya equation\nfor freight air transport (historical until 2019)"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Reference to 2000 with logarithmic scale")
        self.ax.legend()
        ax = plt.gca()
        self.ax.set_xlim(2000, 2050)
        self.ax.set_yscale("log")

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

        self.line_co2.set_ydata(
            self.df["co2_emissions_freight"] / self.df.loc[2000, "co2_emissions_freight"]
        )

        self.line_rtk.set_ydata(self.df["rtk"] / self.df.loc[2000, "rtk"])

        self.line_energy_per_rtk.set_ydata(
            self.df["energy_per_rtk_mean"] / self.df.loc[2000, "energy_per_rtk_mean"]
        )

        self.line_co2_per_energy.set_ydata(
            self.df["co2_per_energy_mean"] / self.df.loc[2000, "co2_per_energy_mean"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class LeversOfActionDistributionPlot:
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
        if (
            self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
            - self.df.loc[2050, "cumulative_co2_emissions"]
            > 0
        ):
            if (
                self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
                - self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                >= 0
            ):
                sizes = [
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
                        - self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                        - self.df.loc[2050, "cumulative_co2_emissions_including_load_factor"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_including_load_factor"]
                        - self.df.loc[2050, "cumulative_co2_emissions_including_energy"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_including_energy"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                ]
                sizes = np.round(sizes, 3)
            else:
                sizes = [
                    0,
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                        - self.df.loc[2050, "cumulative_co2_emissions_including_load_factor"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_including_load_factor"]
                        - self.df.loc[2050, "cumulative_co2_emissions_including_energy"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_including_energy"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                ]
                sizes = np.round(sizes, 3)

            labels = (
                "Sufficiency " + str(round(sizes[0], 1)) + "%",
                "Efficiency " + str(round(sizes[1], 1)) + "%",
                "Energy " + str(round(sizes[2], 1)) + "%",
            )
            colors = "red", "gold", "yellowgreen"

            self.line_part_reduction_CO2 = self.ax.pie(
                sizes,
                colors=colors,
                shadow=False,
                startangle=90,
                counterclock=False,
            )

            self.ax.set_title(
                "Impact of the levers of action on the reduction\nof cumulative CO2 emissions compared\nto the"
                " baseline scenario\nShare display depends on lever order convention"
            )

            self.ax.legend(labels, loc="best")

            self.fig.canvas.header_visible = False
            self.fig.canvas.toolbar_position = "bottom"
            # self.fig.canvas.layout.width = "auto"
            # self.fig.canvas.layout.height = "auto"
            self.fig.tight_layout()

        else:
            sizes = [1, 0, 0]

            labels = ("", "Non-displayable graph           ", "    with these settings        ", "")
            colors = "white", "white", "white"

            self.line_part_reduction_CO2 = self.ax.pie(
                sizes,
                colors=colors,
                shadow=False,
                startangle=90,
                counterclock=False,
            )

            self.ax.set_title(
                "Impact of the levers of action on the reduction\nof cumulative CO2 emissions compared\nto the"
                " baseline scenario\nShare display depends on lever order convention"
            )

            self.ax.legend(labels, loc="center")

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

        if (
            self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
            - self.df.loc[2050, "cumulative_co2_emissions"]
            > 0
        ):

            if (
                self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
                - self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                >= 0
            ):
                sizes = [
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
                        - self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                        - self.df.loc[2050, "cumulative_co2_emissions_including_load_factor"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_including_load_factor"]
                        - self.df.loc[2050, "cumulative_co2_emissions_including_energy"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_including_energy"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology_baseline3"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                ]
                sizes = np.round(sizes, 3)
            else:
                sizes = [
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                        - self.df.loc[2050, "cumulative_co2_emissions_including_load_factor"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_including_load_factor"]
                        - self.df.loc[2050, "cumulative_co2_emissions_including_energy"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                    (
                        self.df.loc[2050, "cumulative_co2_emissions_including_energy"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    / (
                        self.df.loc[2050, "cumulative_co2_emissions_2019technology"]
                        - self.df.loc[2050, "cumulative_co2_emissions"]
                    )
                    * 100,
                ]
                sizes = np.round(sizes, 3)

            self.ax.clear()

            labels = (
                "Sufficiency " + str(round(sizes[0], 1)) + "%",
                "Efficiency " + str(round(sizes[1], 1)) + "%",
                "Energy " + str(round(sizes[2], 1)) + "%",
            )
            colors = "red", "gold", "yellowgreen"

            self.line_part_reduction_CO2 = self.ax.pie(
                sizes,
                colors=colors,
                shadow=False,
                startangle=90,
                counterclock=False,
            )

            self.ax.set_title(
                "Impact of the levers of action on the reduction\nof cumulative CO2 emissions compared\nto the"
                " baseline scenario\nShare display depends on lever order convention"
            )

            self.ax.legend(labels, loc="best")

            for collection in self.ax.collections:
                collection.remove()
            self.ax.relim()
            self.ax.autoscale_view()
            self.fig.canvas.draw()

        else:

            sizes = [1, 0, 0]

            self.ax.clear()

            labels = ("", "Non-displayable graph           ", "    with these settings        ", "")
            colors = "white", "white", "white"

            self.line_part_reduction_CO2 = self.ax.pie(
                sizes,
                colors=colors,
                shadow=False,
                startangle=90,
                counterclock=False,
            )

            self.ax.set_title(
                "Impact of the levers of action on the reduction\nof cumulative CO2 emissions compared\nto the"
                " baseline scenario\nShare display depends on lever order convention"
            )

            self.ax.legend(labels, loc="center")

            for collection in self.ax.collections:
                collection.remove()
            self.ax.relim()
            self.ax.autoscale_view()
            self.fig.canvas.draw()

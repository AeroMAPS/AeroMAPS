import matplotlib.pyplot as plt
import numpy as np
from .constants import plot_3_x, plot_3_y


class FinalEffectiveRadiativeForcingPlot:
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
        barWidth = 0.6
        chosen_year = 2050
        y1 = [
            self.df.loc[chosen_year, "total_erf"],
            self.df.loc[chosen_year, "contrails_erf"],
            self.df.loc[chosen_year, "aerosol_erf"],
            self.df.loc[chosen_year, "h2o_erf"],
            self.df.loc[chosen_year, "nox_erf"],
            self.df.loc[chosen_year, "co2_erf"],
        ]

        r = range(len(y1))
        self.line_composantes_RF = self.ax.barh(
            r,
            y1,
            height=barWidth,
            color=["red", "red", "deepskyblue", "red", "red"],
            edgecolor="black",
            # xerr=[xerr1, xerr2],
            capsize=5,
        )
        self.ax.set_yticks(r)
        self.ax.set_yticklabels(
            ["Total", "Contrails", "Aerosols", "Water vapour", "NOx", "$CO_2$"],
        )
        self.ax.set_title("Components of effective radiative forcing\nfrom air transport in 2050")
        self.ax.grid()
        self.ax.set_xlabel("Effective radiative forcing [$mW/m^2$]")

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

        chosen_year = 2050
        y1 = [
            self.df.loc[chosen_year, "total_erf"],
            self.df.loc[chosen_year, "contrails_erf"],
            self.df.loc[chosen_year, "aerosol_erf"],
            self.df.loc[chosen_year, "h2o_erf"],
            self.df.loc[chosen_year, "nox_erf"],
            self.df.loc[chosen_year, "co2_erf"],
        ]

        for rect, h in zip(self.line_composantes_RF, y1):
            rect.set_width(h)

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DistributionEffectiveRadiativeForcingPlot:
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
        (self.line_co2_erf_share,) = self.ax.plot(
            self.years,
            self.df["co2_erf"] / self.df["total_erf"] * 100,
            color="red",
            linestyle="-",
            label="CO2",
            linewidth=2,
        )

        (self.line_h2o_erf_share,) = self.ax.plot(
            self.years,
            self.df["h2o_erf"] / self.df["total_erf"] * 100,
            color="lightskyblue",
            linestyle="-",
            label="Water vapour",
            linewidth=2,
        )

        (self.line_nox_erf_share,) = self.ax.plot(
            self.years,
            self.df["nox_erf"] / self.df["total_erf"] * 100,
            color="yellowgreen",
            linestyle="-",
            label="NOx",
            linewidth=2,
        )

        (self.line_contrails_erf_share,) = self.ax.plot(
            self.years,
            self.df["contrails_erf"] / self.df["total_erf"] * 100,
            color="gold",
            linestyle="-",
            label="Contrails",
            linewidth=2,
        )

        (self.line_aerosol_erf_share,) = self.ax.plot(
            self.years,
            self.df["aerosol_erf"] / self.df["total_erf"] * 100,
            color="darkblue",
            linestyle="-",
            label="Aerosols",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of the distribution of effective radiative\nforcing from air transport (historical up to 2019)"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Share in %")
        self.ax.legend(loc=0)
        ax = plt.gca()
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

        self.line_co2_erf_share.set_ydata(self.df["co2_erf"] / self.df["total_erf"] * 100)

        self.line_h2o_erf_share.set_ydata(self.df["h2o_erf"] / self.df["total_erf"] * 100)

        self.line_nox_erf_share.set_ydata(self.df["nox_erf"] / self.df["total_erf"] * 100)

        self.line_contrails_erf_share.set_ydata(
            self.df["contrails_erf"] / self.df["total_erf"] * 100
        )

        self.line_aerosol_erf_share.set_ydata(self.df["aerosol_erf"] / self.df["total_erf"] * 100)

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class EquivalentEmissionsPlot:
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
            self.prospective_years,
            self.df.loc[self.prospective_years, "co2_emissions_smooth"],
            color="red",
            linestyle="-",
            label="CO2 emissions (smooth)",
            linewidth=2,
        )

        (self.line_nonco2,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "non_co2_equivalent_emissions"],
            color="blue",
            linestyle="-",
            label="Non-CO2 equivalent emissions",
            linewidth=2,
        )

        (self.line_total,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "total_equivalent_emissions"],
            color="black",
            linestyle="-",
            label="Total equivalent emissions",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of equivalent\nemissions from air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Annual equivalent emissions [MtCO2-we]")
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

        self.line_co2.set_ydata(self.df.loc[self.prospective_years, "co2_emissions_smooth"])

        self.line_nonco2.set_ydata(
            self.df.loc[self.prospective_years, "non_co2_equivalent_emissions"]
        )

        self.line_total.set_ydata(self.df.loc[self.prospective_years, "total_equivalent_emissions"])

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class CumulativeEquivalentEmissionsPlot:
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
            self.prospective_years,
            self.df.loc[self.prospective_years, "cumulative_co2_emissions_smooth"],
            color="red",
            linestyle="-",
            label="Cumulative CO2 emissions",
            linewidth=2,
        )

        (self.line_nonco2,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "cumulative_non_co2_equivalent_emissions"],
            color="blue",
            linestyle="-",
            label="Cumulative non-CO2 equivalent emissions",
            linewidth=2,
        )

        (self.line_total,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "cumulative_total_equivalent_emissions"],
            color="black",
            linestyle="-",
            label="Cumulative total equivalent emissions",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of cumulative equivalent\nemissions from air transport (from 2019)"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Cumulative equivalent emissions [GtCO2-we]")
        self.ax = plt.gca()
        self.ax.legend()
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

        self.line_co2.set_ydata(
            self.df.loc[self.prospective_years, "cumulative_co2_emissions_smooth"]
        )

        self.line_nonco2.set_ydata(
            self.df.loc[self.prospective_years, "cumulative_non_co2_equivalent_emissions"]
        )

        self.line_total.set_ydata(
            self.df.loc[self.prospective_years, "cumulative_total_equivalent_emissions"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class EquivalentEmissionsRatioPlot:
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
        (self.line_coef,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "total_co2_equivalent_emissions_ratio"],
            color="blue",
            linestyle="-",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of the coefficient to obtain annual\nequivalent emissions from aviation\nvia those of CO2"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Coefficient Total/CO2 [-]")
        self.ax = plt.gca()
        # self.ax.legend()
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

        self.line_coef.set_ydata(
            self.df.loc[self.prospective_years, "total_co2_equivalent_emissions_ratio"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class TemperatureIncreaseFromAirTransportPlot:
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
            self.years,
            np.zeros(len(self.years)),
            color="tomato",
            linestyle="-",
            linewidth=1,
        )

        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "temperature_increase_from_aviation"] * 1000,
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_temperature,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "temperature_increase_from_aviation"] * 1000,
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.fill_between(
            self.years,
            self.df["temperature_increase_from_co2_from_aviation"] * 1000,
            np.zeros(len(self.years)),
            color="tomato",
            label="CO2",
        )

        self.ax.fill_between(
            self.years,
            self.df["temperature_increase_from_aviation"] * 1000,
            self.df["temperature_increase_from_co2_from_aviation"] * 1000,
            color="#FFBE85",
            label="Non-CO2",
        )

        self.ax.grid()
        self.ax.set_title("Evolution of temperature increase\nfrom air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Temperature increase [mK]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(self.years[0], self.years[-1])
        # self.ax.set_ylim(0,)

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

        self.line_temperature.set_ydata(
            self.df.loc[self.prospective_years, "temperature_increase_from_aviation"] * 1000
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.fill_between(
            self.years,
            self.df["temperature_increase_from_co2_from_aviation"] * 1000,
            np.zeros(len(self.years)),
            color="tomato",
            label="CO2",
        )

        self.ax.fill_between(
            self.years,
            self.df["temperature_increase_from_aviation"] * 1000,
            self.df["temperature_increase_from_co2_from_aviation"] * 1000,
            color="#FFBE85",
            label="Non-CO2",
        )

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()

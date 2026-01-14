import matplotlib.pyplot as plt
import numpy as np
from .constants import plot_3_x, plot_3_y


class FinalEffectiveRadiativeForcingPlot:
    def __init__(self, process):
        data = process.data
        self.df_climate = data["climate_outputs"]
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
        chosen_year = self.years[-1]
        y1 = [
            self.df_climate.loc[chosen_year, "total_erf"],
            self.df_climate.loc[chosen_year, "contrails_erf"],
            self.df_climate.loc[chosen_year, "aerosol_erf"],
            self.df_climate.loc[chosen_year, "h2o_erf"],
            self.df_climate.loc[chosen_year, "nox_erf"],
            self.df_climate.loc[chosen_year, "co2_erf"],
        ]

        if self.df_climate.loc[chosen_year, "aerosol_erf"] < 0:
            aerosol_color = "deepskyblue"
        else:
            aerosol_color = "red"

        r = range(len(y1))
        self.line_composantes_RF = self.ax.barh(
            r,
            y1,
            height=barWidth,
            color=["red", "red", aerosol_color, "red", "red"],
            edgecolor="black",
            # xerr=[xerr1, xerr2],
            capsize=5,
        )
        self.ax.set_yticks(r)
        self.ax.set_yticklabels(
            ["Total", "Contrails", "Aerosols", "Water vapour", "NOx", "$CO_2$"],
        )
        self.ax.set_title(
            "Components of effective radiative forcing\nfrom air transport for the final year"
        )
        self.ax.grid()
        self.ax.set_xlabel("Effective radiative forcing [$mW/m^2$]")

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, data):
        self.df_climate = data["climate_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        chosen_year = self.years[-1]
        y1 = [
            self.df_climate.loc[chosen_year, "total_erf"],
            self.df_climate.loc[chosen_year, "contrails_erf"],
            self.df_climate.loc[chosen_year, "aerosol_erf"],
            self.df_climate.loc[chosen_year, "h2o_erf"],
            self.df_climate.loc[chosen_year, "nox_erf"],
            self.df_climate.loc[chosen_year, "co2_erf"],
        ]

        for rect, h in zip(self.line_composantes_RF, y1):
            rect.set_width(h)

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DistributionEffectiveRadiativeForcingPlot:
    def __init__(self, process):
        data = process.data
        self.df_climate = data["climate_outputs"]
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
            self.df_climate.loc[self.years, "co2_erf"]
            / self.df_climate.loc[self.years, "total_erf"]
            * 100,
            color="red",
            linestyle="-",
            label="CO2",
            linewidth=2,
        )

        (self.line_h2o_erf_share,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "h2o_erf"]
            / self.df_climate.loc[self.years, "total_erf"]
            * 100,
            color="lightskyblue",
            linestyle="-",
            label="Water vapour",
            linewidth=2,
        )

        (self.line_nox_erf_share,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "nox_erf"]
            / self.df_climate.loc[self.years, "total_erf"]
            * 100,
            color="yellowgreen",
            linestyle="-",
            label="NOx",
            linewidth=2,
        )

        (self.line_contrails_erf_share,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "contrails_erf"]
            / self.df_climate.loc[self.years, "total_erf"]
            * 100,
            color="gold",
            linestyle="-",
            label="Contrails",
            linewidth=2,
        )

        (self.line_aerosol_erf_share,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "aerosol_erf"]
            / self.df_climate.loc[self.years, "total_erf"]
            * 100,
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
        self.ax.set_xlim(self.years[0], self.years[-1])

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, data):
        self.df_climate = data["climate_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.line_co2_erf_share.set_ydata(
            self.df_climate.loc[self.years, "co2_erf"]
            / self.df_climate.loc[self.years, "total_erf"]
            * 100
        )

        self.line_h2o_erf_share.set_ydata(
            self.df_climate.loc[self.years, "h2o_erf"]
            / self.df_climate.loc[self.years, "total_erf"]
            * 100
        )

        self.line_nox_erf_share.set_ydata(
            self.df_climate.loc[self.years, "nox_erf"]
            / self.df_climate.loc[self.years, "total_erf"]
            * 100
        )

        self.line_contrails_erf_share.set_ydata(
            self.df_climate.loc[self.years, "contrails_erf"]
            / self.df_climate.loc[self.years, "total_erf"]
            * 100
        )

        self.line_aerosol_erf_share.set_ydata(
            self.df_climate.loc[self.years, "aerosol_erf"]
            / self.df_climate.loc[self.years, "total_erf"]
            * 100
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class TemperatureIncreaseFromAirTransportPlot:
    def __init__(self, process):
        data = process.data
        self.df_climate = data["climate_outputs"]
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
            self.df_climate.loc[self.historic_years, "temperature_increase_from_aviation"] * 1000,
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_temperature,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "temperature_increase_from_aviation"]
            * 1000,
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000,
            np.zeros(len(self.years)),
            color="tomato",
            label="CO2",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "temperature_increase_from_aviation"] * 1000,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000,
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
        self.df_climate = data["climate_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.line_temperature.set_ydata(
            self.df_climate.loc[self.prospective_years, "temperature_increase_from_aviation"] * 1000
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000,
            np.zeros(len(self.years)),
            color="tomato",
            label="CO2",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "temperature_increase_from_aviation"] * 1000,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000,
            color="#FFBE85",
            label="Non-CO2",
        )

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DetailedTemperatureIncreaseFromAirTransportPlot:
    def __init__(self, process):
        data = process.data
        self.df_climate = data["climate_outputs"]
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
            self.df_climate.loc[self.historic_years, "temperature_increase_from_aviation"] * 1000,
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_temperature,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "temperature_increase_from_aviation"]
            * 1000,
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000,
            np.zeros(len(self.years)),
            color="deepskyblue",
            label="CO₂",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
            ]
            * 1000,
            color="blueviolet",
            label="NOx - Heating",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
            ]
            * 1000,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[self.years, "temperature_increase_from_h2o_from_aviation"] * 1000,
            color="royalblue",
            label="H₂O",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[self.years, "temperature_increase_from_h2o_from_aviation"] * 1000,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[self.years, "temperature_increase_from_h2o_from_aviation"] * 1000
            + self.df_climate.loc[self.years, "temperature_increase_from_contrails_from_aviation"]
            * 1000,
            color="forestgreen",
            label="Contrails",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[
                self.years, "temperature_increase_from_nox_long_term_o3_decrease_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_ch4_decrease_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[
                self.years,
                "temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation",
            ]
            * 1000,
            np.zeros(len(self.years)),
            color="gold",
            label="NOx - Cooling",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[
                self.years, "temperature_increase_from_nox_long_term_o3_decrease_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_ch4_decrease_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[
                self.years,
                "temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation",
            ]
            * 1000,
            self.df_climate.loc[
                self.years, "temperature_increase_from_nox_long_term_o3_decrease_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_ch4_decrease_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[
                self.years,
                "temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation",
            ]
            * 1000
            + self.df_climate.loc[self.years, "temperature_increase_from_soot_from_aviation"] * 1000
            + self.df_climate.loc[self.years, "temperature_increase_from_sulfur_from_aviation"]
            * 1000,
            color="tomato",
            label="Aerosols",
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
        self.df_climate = data["climate_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.line_temperature.set_ydata(
            self.df_climate.loc[self.prospective_years, "temperature_increase_from_aviation"] * 1000
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
            ]
            * 1000,
            color="blueviolet",
            label="NOx - Heating",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
            ]
            * 1000,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[self.years, "temperature_increase_from_h2o_from_aviation"] * 1000,
            color="royalblue",
            label="H₂O",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[self.years, "temperature_increase_from_h2o_from_aviation"] * 1000,
            self.df_climate.loc[self.years, "temperature_increase_from_co2_from_aviation"] * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[self.years, "temperature_increase_from_h2o_from_aviation"] * 1000
            + self.df_climate.loc[self.years, "temperature_increase_from_contrails_from_aviation"]
            * 1000,
            color="forestgreen",
            label="Contrails",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[
                self.years, "temperature_increase_from_nox_long_term_o3_decrease_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_ch4_decrease_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[
                self.years,
                "temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation",
            ]
            * 1000,
            np.zeros(len(self.years)),
            color="gold",
            label="NOx - Cooling",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[
                self.years, "temperature_increase_from_nox_long_term_o3_decrease_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_ch4_decrease_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[
                self.years,
                "temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation",
            ]
            * 1000,
            self.df_climate.loc[
                self.years, "temperature_increase_from_nox_long_term_o3_decrease_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[
                self.years, "temperature_increase_from_nox_ch4_decrease_from_aviation"
            ]
            * 1000
            + self.df_climate.loc[
                self.years,
                "temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation",
            ]
            * 1000
            + self.df_climate.loc[self.years, "temperature_increase_from_soot_from_aviation"] * 1000
            + self.df_climate.loc[self.years, "temperature_increase_from_sulfur_from_aviation"]
            * 1000,
            color="tomato",
            label="Aerosols",
        )

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()

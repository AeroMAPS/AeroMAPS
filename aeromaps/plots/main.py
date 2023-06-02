import matplotlib.pyplot as plt
import numpy as np
from .constants import plot_1_x, plot_1_y


class AirTransportCO2EmissionsPlot:
    def __init__(self, data):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_1_x, plot_1_y),
        )
        self.create_plot()

    def create_plot(self):
        (self.line_co2_emissions_including_technology,) = self.ax.plot(
            self.years,
            self.df["co2_emissions_including_aircraft_efficiency"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_emissions_including_operations,) = self.ax.plot(
            self.years,
            self.df["co2_emissions_including_operations"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_emissions_including_load_factor,) = self.ax.plot(
            self.years,
            self.df["co2_emissions_including_load_factor"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_emissions_including_energy,) = self.ax.plot(
            self.years,
            self.df["co2_emissions_including_energy"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "co2_emissions"],
            color="black",
            linestyle="-",
            label="Historical emissions",
            linewidth=3,
            zorder=4,
        )

        (self.line_co2_emissions_no_action,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "co2_emissions_2019technology_baseline3"],
            color="black",
            linestyle="--",
            label="Emissions at 2019 technological level - Baseline of 3% growth",
            linewidth=2,
            zorder=1,
        )

        (self.line_co2_emissions_including_sobriety,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "co2_emissions_2019technology"],
            color="red",
            linestyle="-",
            label="Emissions at 2019 technological level - Projections",
            linewidth=3,
            zorder=2,
        )

        (self.line_co2_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "co2_emissions"],
            color="green",
            linestyle="-",
            label="Emissions including all levers of action - Projections",
            linewidth=3,
            zorder=3,
        )

        # Fill between
        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_2019technology"],
            self.df["co2_emissions_including_aircraft_efficiency"],
            color="gold",
            label="Aircraft efficiency",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_aircraft_efficiency"],
            self.df["co2_emissions_including_operations"],
            color="orange",
            label="Fleet operations",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_operations"],
            self.df["co2_emissions_including_load_factor"],
            color="grey",
            label="Aircraft load factor",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_load_factor"],
            self.df["co2_emissions_including_energy"],
            color="yellowgreen",
            label="Aircraft energy",
        )
        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_energy"],
            self.df["co2_emissions"],
            color="lightskyblue",
            label="Other measures",
        )

        self.ax.grid()
        self.ax.set_title("Evolution of annual CO2 emissions from air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Annual CO2 emissions [MtCO2]")
        ax = plt.gca()
        self.ax.legend(loc=2)
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

        self.line_co2_emissions_including_technology.set_ydata(
            self.df["co2_emissions_including_aircraft_efficiency"]
        )

        self.line_co2_emissions_including_operations.set_ydata(
            self.df["co2_emissions_including_operations"]
        )

        self.line_co2_emissions_including_load_factor.set_ydata(
            self.df["co2_emissions_including_load_factor"]
        )

        self.line_co2_emissions_including_energy.set_ydata(
            self.df["co2_emissions_including_energy"]
        )

        self.line_co2_emissions_including_sobriety.set_ydata(
            self.df.loc[self.prospective_years, "co2_emissions_2019technology"]
        )

        self.line_co2_emissions.set_ydata(self.df.loc[self.prospective_years, "co2_emissions"])

        self.ax.collections.clear()

        # Fill between
        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_2019technology"],
            self.df["co2_emissions_including_aircraft_efficiency"],
            color="gold",
            label="Reduction of consumption",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_aircraft_efficiency"],
            self.df["co2_emissions_including_operations"],
            color="orange",
            label="Flight and ground operations",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_operations"],
            self.df["co2_emissions_including_load_factor"],
            color="grey",
            label="Aircraft load factor",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_load_factor"],
            self.df["co2_emissions_including_energy"],
            color="yellowgreen",
            label="Energy",
        )
        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_energy"],
            self.df["co2_emissions"],
            color="lightskyblue",
            label="Other measures",
        )

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class AirTransportClimateImpactsPlot:
    def __init__(self, data):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_1_x, plot_1_y),
        )
        self.create_plot()

    def create_plot(self):
        (self.line_co2_erf,) = self.ax.plot(
            self.years,
            self.df["co2_erf"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_h2o_erf,) = self.ax.plot(
            self.years,
            self.df["co2_h2o_erf"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_h2o_nox_erf,) = self.ax.plot(
            self.years,
            self.df["co2_h2o_nox_erf"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_h2o_nox_contrails_erf,) = self.ax.plot(
            self.years,
            self.df["co2_h2o_nox_contrails_erf"],
            linestyle="None",
        )

        (self.line_aerosol_erf,) = self.ax.plot(
            self.years,
            self.df["aerosol_erf"],
            linestyle="None",
        )

        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "total_erf"],
            color="black",
            linestyle="-",
            label="Net ERF - History",
            linewidth=4,
        )

        (self.line_total_erf,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "total_erf"],
            color="green",
            linestyle="-",
            label="Net ERF - Projections",
            linewidth=4,
        )

        # Fill between
        self.ax.fill_between(
            self.years,
            np.zeros(len(self.years)),
            self.df["co2_erf"],
            color="red",
            label="CO2",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_erf"],
            self.df["co2_h2o_erf"],
            color="lightskyblue",
            label="H2O",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_h2o_erf"],
            self.df["co2_h2o_nox_erf"],
            color="yellowgreen",
            label="NOx",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_h2o_nox_erf"],
            self.df["co2_h2o_nox_contrails_erf"],
            color="gold",
            label="Contrails",
        )

        self.ax.fill_between(
            self.years,
            np.zeros(len(self.years)),
            self.df["aerosol_erf"],
            color="darkblue",
            label="Aerosols",
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of climate impacts (via effective radiative forcing) from air transport"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Effective radiative forcing [mW/m²]")
        self.ax.legend(loc=2)
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

        self.line_co2_erf.set_ydata(self.df["co2_erf"])

        self.line_co2_h2o_erf.set_ydata(self.df["co2_h2o_erf"])

        self.line_co2_h2o_nox_erf.set_ydata(self.df["co2_h2o_nox_erf"])

        self.line_co2_h2o_nox_contrails_erf.set_ydata(self.df["co2_h2o_nox_contrails_erf"])

        self.line_aerosol_erf.set_ydata(self.df["aerosol_erf"])

        self.line_total_erf.set_ydata(self.df.loc[self.prospective_years, "total_erf"])

        self.ax.collections.clear()

        # Fill between
        self.ax.fill_between(
            self.years,
            np.zeros(len(self.years)),
            self.df["co2_erf"],
            color="red",
            label="CO2",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_erf"],
            self.df["co2_h2o_erf"],
            color="lightskyblue",
            label="H2O",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_h2o_erf"],
            self.df["co2_h2o_nox_erf"],
            color="yellowgreen",
            label="NOx",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_h2o_nox_erf"],
            self.df["co2_h2o_nox_contrails_erf"],
            color="gold",
            label="Contrails",
        )

        self.ax.fill_between(
            self.years,
            np.zeros(len(self.years)),
            self.df["aerosol_erf"],
            color="darkblue",
            label="Aerosols",
        )

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()

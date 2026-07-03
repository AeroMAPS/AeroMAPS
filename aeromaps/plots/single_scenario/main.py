import matplotlib.pyplot as plt
import numpy as np

from aeromaps.models.impacts.emissions.co2_emissions import aircraft_efficiency_lever_names
from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
from aeromaps.plots.single_scenario_plot import plot_1_x
from aeromaps.plots.single_scenario_plot import plot_1_y


class AirTransportCO2EmissionsPlot(SingleScenarioPlot):
    required_outputs = [
        "co2_emissions_2019technology",
        "co2_emissions_including_aircraft_efficiency",
        "co2_emissions_including_load_factor",
        "co2_emissions_including_energy",
        "co2_emissions_2019technology_baseline3",
        "carbon_offset",
        "co2_emissions",
    ]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_1_x, plot_1_y)

    def create_plot(self):
        (self.line_co2_emissions_including_sobriety,) = self.ax.plot(
            self.years,
            self.df["co2_emissions_2019technology"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_emissions_including_technology,) = self.ax.plot(
            self.years,
            self.df["co2_emissions_including_aircraft_efficiency"],
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
            self.df_climate.loc[self.historic_years, "co2_emissions"],
            color="black",
            linestyle="-",
            label="Historical emissions",
            linewidth=3,
            zorder=4,
        )

        (self.line_co2_emissions_no_action,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "co2_emissions_2019technology_baseline3"],
            color="red",
            linestyle="-",
            label="Emissions at 2019 technological level with trend air traffic growth",
            linewidth=3,
            zorder=3,
        )

        (self.line_co2_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "co2_emissions"],
            color="green",
            linestyle="-",
            label="Projected emissions including all levers of action",
            linewidth=3,
            zorder=3,
        )

        (self.line_co2_emissions_offset,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "co2_emissions"]
            - self.df.loc[self.prospective_years, "carbon_offset"],
            color="grey",
            linestyle="--",
            label="Projected emissions including all levers of action and offsetting",
            linewidth=2,
            zorder=3,
        )

        # Fill between

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_2019technology_baseline3"],
            self.df["co2_emissions_2019technology"],
            color="lightskyblue",
            label="Demand/supply side management",
        )

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
            self.df["co2_emissions_including_load_factor"],
            color="orange",
            label="Fleet operations and load factor",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_load_factor"],
            self.df_climate.loc[self.years, "co2_emissions"],
            color="yellowgreen",
            label="Aircraft energy",
        )

        plt.rc("hatch", linewidth=4)
        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_emissions"],
            self.df_climate.loc[self.years, "co2_emissions"] - self.df["carbon_offset"],
            color="white",
            facecolor="silver",
            hatch="//",
            label="Carbon offset",
        )

        self.ax.grid()
        self.ax.set_title("Evolution of annual CO₂ emissions from air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Annual CO₂ emissions [MtCO₂]")
        self.ax.legend(loc=2)
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_co2_emissions_including_sobriety.set_ydata(
            self.df["co2_emissions_2019technology"]
        )

        self.line_co2_emissions_including_technology.set_ydata(
            self.df["co2_emissions_including_aircraft_efficiency"]
        )

        self.line_co2_emissions_including_load_factor.set_ydata(
            self.df["co2_emissions_including_load_factor"]
        )

        self.line_co2_emissions_including_energy.set_ydata(
            self.df["co2_emissions_including_energy"]
        )

        self.line_co2_emissions.set_ydata(
            self.df_climate.loc[self.prospective_years, "co2_emissions"]
        )

        self.line_co2_emissions_offset.set_ydata(
            self.df_climate.loc[self.prospective_years, "co2_emissions"]
            - self.df.loc[self.prospective_years, "carbon_offset"]
        )

        for collection in self.ax.collections:
            collection.remove()

        # Fill between
        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_2019technology_baseline3"],
            self.df["co2_emissions_2019technology"],
            color="lightskyblue",
            label="Demand/supply side management",
        )

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
            self.df["co2_emissions_including_load_factor"],
            color="orange",
            label="Fleet operations and load factor",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_load_factor"],
            self.df_climate.loc[self.years, "co2_emissions"],
            color="yellowgreen",
            label="Aircraft energy",
        )

        plt.rc("hatch", linewidth=4)
        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_emissions"],
            self.df_climate.loc[self.years, "co2_emissions"] - self.df["carbon_offset"],
            color="white",
            facecolor="silver",
            hatch="//",
            label="Carbon offset",
        )
        self.fig.canvas.draw()


class AirTransportCO2EmissionsDetailedPlot(SingleScenarioPlot):
    """
    Variant of AirTransportCO2EmissionsPlot where the "Aircraft efficiency" and
    "Aircraft energy" levers of action are decomposed into sub-levers: fleet
    renewal and each new aircraft of the fleet for the efficiency lever, and each
    energy pathway for the energy lever.

    Requires the bottom-up fleet model and the generic energy models, together
    with the DetailedCo2EmissionsPerAircraft and DetailedCo2EmissionsPerPathway
    models.
    """

    required_outputs = [
        "co2_emissions_2019technology",
        "co2_emissions_including_aircraft_efficiency",
        "co2_emissions_including_load_factor",
        "co2_emissions_including_energy",
        "co2_emissions_2019technology_baseline3",
        "carbon_offset",
        "co2_emissions",
        "co2_emissions_lever_efficiency_fleet_renewal",
        "co2_emissions_lever_efficiency_freight",
        "co2_emissions_lever_efficiency_other",
        "co2_emissions_lever_energy_other",
    ]

    # Colormap used per energy origin for the energy pathway sub-levers
    ENERGY_ORIGIN_COLORMAPS = {
        "biomass": plt.cm.Greens,
        "electricity": plt.cm.Blues,
        "fossil": plt.cm.Reds,
    }
    ENERGY_ORIGIN_FALLBACK_COLORMAP = plt.cm.Purples

    # Bands whose absolute contribution never exceeds this value [MtCO2] are not
    # drawn nor referenced in the legend (their thickness would not be visible)
    NEGLIGIBLE_BAND_THRESHOLD = 1e-3

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_1_x, plot_1_y)

    def _efficiency_bands(self):
        """Return the (label, column, color) list of the aircraft efficiency sub-levers."""
        fleet = self.process.fleet_model.fleet
        lever_names = aircraft_efficiency_lever_names(fleet)

        aircraft_columns = []
        for (category_name, _, aircraft_name), column in lever_names.items():
            if column in self.df.columns:
                aircraft_columns.append((f"{aircraft_name} ({category_name})", column))

        aircraft_colors = plt.cm.YlOrBr(np.linspace(0.25, 0.75, max(len(aircraft_columns), 1)))

        bands = [("Fleet renewal", "co2_emissions_lever_efficiency_fleet_renewal", "gold")]
        for (label, column), color in zip(aircraft_columns, aircraft_colors):
            bands.append((label, column, color))
        bands.append(("Freight fleet", "co2_emissions_lever_efficiency_freight", "tan"))
        bands.append(("Traffic mix and others", "co2_emissions_lever_efficiency_other", "wheat"))
        return bands

    def _energy_bands(self):
        """Return the (label, column, color) list of the energy pathway sub-levers."""
        pathways_by_origin = {}
        for pathway in self.pathways_manager.get_all():
            column = f"co2_emissions_lever_energy_{pathway.name}"
            if column in self.df.columns:
                pathways_by_origin.setdefault(pathway.energy_origin, []).append(
                    (pathway.name, column)
                )

        bands = []
        for energy_origin, pathways in pathways_by_origin.items():
            colormap = self.ENERGY_ORIGIN_COLORMAPS.get(
                energy_origin, self.ENERGY_ORIGIN_FALLBACK_COLORMAP
            )
            colors = colormap(np.linspace(0.4, 0.8, len(pathways)))
            for (pathway_name, column), color in zip(pathways, colors):
                label = pathway_name.replace("_", " ").title()
                bands.append((label, column, color))
        bands.append(("Other energy effects", "co2_emissions_lever_energy_other", "darkseagreen"))
        return bands

    def _plot_sub_lever_bands(self, upper, bands):
        """Stack sub-lever bands downwards from the given upper curve.

        Negligible bands are subtracted but not drawn, so that the legend only
        references visible bands.
        """
        for label, column, color in bands:
            values = self.df.loc[self.years, column].fillna(0)
            lower = upper - values
            if values.abs().max() > self.NEGLIGIBLE_BAND_THRESHOLD:
                self.ax.fill_between(self.years, upper, lower, color=color, label=label)
            upper = lower
        return upper

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df_climate.loc[self.historic_years, "co2_emissions"],
            color="black",
            linestyle="-",
            label="Historical emissions",
            linewidth=3,
            zorder=4,
        )

        (self.line_co2_emissions_no_action,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "co2_emissions_2019technology_baseline3"],
            color="red",
            linestyle="-",
            label="Emissions at 2019 technological level with trend air traffic growth",
            linewidth=3,
            zorder=3,
        )

        (self.line_co2_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "co2_emissions"],
            color="green",
            linestyle="-",
            label="Projected emissions including all levers of action",
            linewidth=3,
            zorder=3,
        )

        (self.line_co2_emissions_offset,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "co2_emissions"]
            - self.df.loc[self.prospective_years, "carbon_offset"],
            color="grey",
            linestyle="--",
            label="Projected emissions including all levers of action and offsetting",
            linewidth=2,
            zorder=3,
        )

        self._draw_fills()

        self.ax.grid()
        self.ax.set_title(
            "Evolution of annual CO₂ emissions from air transport - Detailed levers of action"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Annual CO₂ emissions [MtCO₂]")
        self.ax.legend(loc=2, fontsize=6, ncols=2)
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _draw_fills(self):
        # Demand/supply side management
        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_2019technology_baseline3"],
            self.df["co2_emissions_2019technology"],
            color="lightskyblue",
            label="Demand/supply side management",
        )

        # Aircraft efficiency sub-levers
        upper = self.df.loc[self.years, "co2_emissions_2019technology"]
        self._plot_sub_lever_bands(upper, self._efficiency_bands())

        # Fleet operations and load factor
        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_aircraft_efficiency"],
            self.df["co2_emissions_including_load_factor"],
            color="orange",
            label="Fleet operations and load factor",
        )

        # Aircraft energy sub-levers
        upper = self.df.loc[self.years, "co2_emissions_including_load_factor"]
        self._plot_sub_lever_bands(upper, self._energy_bands())

        # Carbon offset
        plt.rc("hatch", linewidth=4)
        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_emissions"],
            self.df_climate.loc[self.years, "co2_emissions"] - self.df["carbon_offset"],
            color="white",
            facecolor="silver",
            hatch="//",
            label="Carbon offset",
        )

    def _update_plot_elements(self):
        self.line_co2_emissions_no_action.set_ydata(
            self.df.loc[self.prospective_years, "co2_emissions_2019technology_baseline3"]
        )

        self.line_co2_emissions.set_ydata(
            self.df_climate.loc[self.prospective_years, "co2_emissions"]
        )

        self.line_co2_emissions_offset.set_ydata(
            self.df_climate.loc[self.prospective_years, "co2_emissions"]
            - self.df.loc[self.prospective_years, "carbon_offset"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self._draw_fills()
        self.fig.canvas.draw()


class AirTransportClimateImpactsPlot(SingleScenarioPlot):
    required_outputs = [
        "co2_erf",
        "co2_h2o_erf",
        "co2_h2o_nox_erf",
        "co2_h2o_nox_contrails_erf",
        "aerosol_erf",
        "total_erf",
    ]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_1_x, plot_1_y)

    def create_plot(self):
        (self.line_co2_erf,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "co2_erf"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_h2o_erf,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_erf"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_h2o_nox_erf,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_nox_erf"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_h2o_nox_contrails_erf,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_nox_contrails_erf"],
            linestyle="None",
        )

        (self.line_aerosol_erf,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "aerosol_erf"],
            linestyle="None",
        )

        self.ax.plot(
            self.historic_years,
            self.df_climate.loc[self.historic_years, "total_erf"],
            color="black",
            linestyle="-",
            label="Net ERF - History",
            linewidth=4,
        )

        (self.line_total_erf,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "total_erf"],
            color="green",
            linestyle="-",
            label="Net ERF - Projections",
            linewidth=4,
        )

        # Fill between
        self.ax.fill_between(
            self.years,
            np.zeros(len(self.years)),
            self.df_climate.loc[self.years, "co2_erf"],
            color="tomato",
            label="CO2",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_erf"],
            self.df_climate.loc[self.years, "co2_h2o_erf"],
            color="lightskyblue",
            label="H2O",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_erf"],
            self.df_climate.loc[self.years, "co2_h2o_nox_erf"],
            color="yellowgreen",
            label="NOx",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_nox_erf"],
            self.df_climate.loc[self.years, "co2_h2o_nox_contrails_erf"],
            color="gold",
            label="Contrails",
        )

        self.ax.fill_between(
            self.years,
            np.zeros(len(self.years)),
            self.df_climate.loc[self.years, "aerosol_erf"],
            color="darkblue",
            label="Aerosols",
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of climate impacts (via effective radiative forcing) from air transport"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Effective radiative forcing [W/m²]")
        self.ax.legend(loc=2)
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_co2_erf.set_ydata(self.df_climate.loc[self.years, "co2_erf"])

        self.line_co2_h2o_erf.set_ydata(self.df_climate.loc[self.years, "co2_h2o_erf"])

        self.line_co2_h2o_nox_erf.set_ydata(self.df_climate.loc[self.years, "co2_h2o_nox_erf"])

        self.line_co2_h2o_nox_contrails_erf.set_ydata(
            self.df_climate.loc[self.years, "co2_h2o_nox_contrails_erf"]
        )

        self.line_aerosol_erf.set_ydata(self.df_climate.loc[self.years, "aerosol_erf"])

        self.line_total_erf.set_ydata(self.df_climate.loc[self.prospective_years, "total_erf"])

        for collection in self.ax.collections:
            collection.remove()

        # Fill between
        self.ax.fill_between(
            self.years,
            np.zeros(len(self.years)),
            self.df_climate.loc[self.years, "co2_erf"],
            color="tomato",
            label="CO2",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_erf"],
            self.df_climate.loc[self.years, "co2_h2o_erf"],
            color="lightskyblue",
            label="H2O",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_erf"],
            self.df_climate.loc[self.years, "co2_h2o_nox_erf"],
            color="yellowgreen",
            label="NOx",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_nox_erf"],
            self.df_climate.loc[self.years, "co2_h2o_nox_contrails_erf"],
            color="gold",
            label="Contrails",
        )

        self.ax.fill_between(
            self.years,
            np.zeros(len(self.years)),
            self.df_climate.loc[self.years, "aerosol_erf"],
            color="darkblue",
            label="Aerosols",
        )
        self.fig.canvas.draw()

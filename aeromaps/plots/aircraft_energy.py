import random
import matplotlib.pyplot as plt
from ipywidgets import widgets, interact

from .constants import plot_3_x, plot_3_y


class MeanFuelEmissionFactorPlot:
    def __init__(self, process):
        data = process.data
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
    def __init__(self, process):
        data = process.data
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
            self.df.loc[self.prospective_years, "dropin_fuel_biomass_mean_co2_emission_factor"],
            color="green",
            linestyle="-",
            label="Biofuel",
            linewidth=2,
        )

        (self.line_hydrogen_mean_emission_factor,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "hydrogen_mean_co2_emission_factor"],
            color="blue",
            linestyle="-",
            label="Hydrogen",
            linewidth=2,
        )

        (self.line_electrofuel_emission_factor,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "dropin_fuel_electricity_mean_co2_emission_factor"],
            color="red",
            linestyle="-",
            label="Electrofuel",
            linewidth=2,
        )

        (self.line_kerosene_emission_factor,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "fossil_kerosene_co2_emission_factor"],
            color="black",
            linestyle="-",
            label="Kerosene",
            linewidth=2,
        )

        (self.line_electricity_emission_factor,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "electric_mean_co2_emission_factor"],
            color="purple",
            linestyle="-",
            label="Direct Electricity",
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
            self.df.loc[self.prospective_years, "dropin_fuel_biomass_mean_co2_emission_factor"]
        )

        self.line_hydrogen_mean_emission_factor.set_ydata(
            self.df.loc[self.prospective_years, "hydrogen_mean_co2_emission_factor"]
        )

        self.line_electrofuel_emission_factor.set_ydata(
            self.df.loc[self.prospective_years, "dropin_fuel_electricity_mean_co2_emission_factor"]
        )

        self.line_kerosene_emission_factor.set_ydata(
            self.df.loc[self.prospective_years, "fossil_kerosene_co2_emission_factor"]
        )

        self.line_electricity_emission_factor.set_ydata(
            self.df.loc[self.prospective_years, "electric_mean_co2_emission_factor"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class ShareFuelPlot:
    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]
        self.pathways_manager = process.pathways_manager

        self.fig, self.ax = plt.subplots(
            figsize=(plot_3_x, plot_3_y),
        )

        self.plot_interact()
        self.create_plot()

    def plot_interact(self):
        ac_type_widget = widgets.Dropdown(
            options=self.pathways_manager.get_all_types("aircraft_type") + ["All Types"],
            description="Aircraft Type:",
        )

        energy_origin_widget = widgets.Dropdown(
            options=["All types"] + self.pathways_manager.get_all_types("energy_origin"),
            description="Energy origin:",
        )
        interact(self.update, aircraft_type=ac_type_widget, energy_origin=energy_origin_widget)

    def create_plot(self):
        pass

    def update(self, aircraft_type, energy_origin):
        self.ax.cla()

        color_mapping = {
            "biomass": "green",
            "electricity": "blue",
            "fossil": "red",
        }
        valid_markers = ["o", "s", "D", "^", "v", "<", ">", "p", "*", "h", "H", "+", "x", "X", "d"]

        # focus on a type of aircraft energy
        if energy_origin == "All types" and aircraft_type != "All Types":
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                color = color_mapping.get(energy_origin, "grey")
                self.ax.plot(
                    self.df.loc[
                        self.prospective_years[0] :, f"{energy_origin}_share_{aircraft_type}"
                    ].index,
                    self.df.loc[
                        self.prospective_years[0] :, f"{energy_origin}_share_{aircraft_type}"
                    ],
                    linestyle="-",
                    color=color,
                    label=f"Total {energy_origin}-based",
                    linewidth=2,
                )
                for pathway in self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    marker = random.choice(valid_markers)
                    valid_markers.remove(marker)
                    self.ax.plot(
                        self.df.loc[
                            self.prospective_years[0] :, f"{pathway.name}_share_{aircraft_type}"
                        ].index,
                        self.df.loc[
                            self.prospective_years[0] :, f"{pathway.name}_share_{aircraft_type}"
                        ],
                        linestyle="--",
                        color=color,
                        marker=marker,
                        markersize=4,
                        label=pathway.name,
                        linewidth=1,
                    )
            self.ax.grid()
            self.ax.set_title(f"Evolution of the {aircraft_type}-aircraft fuel blend")
            self.ax.set_xlabel("Year")
            self.ax.set_ylabel(
                f"Share of production pathways in {aircraft_type}-aircraft fuel blend [%]"
            )
            # self.ax = plt.gca()
            self.ax.legend(title="Pathway shares")

        # Focus on an energy origin
        elif energy_origin != "All types" and aircraft_type == "All Types":
            for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
                self.ax.plot(
                    self.df.loc[
                        self.prospective_years[0] :, f"{aircraft_type}_share_{energy_origin}"
                    ].index,
                    self.df.loc[
                        self.prospective_years[0] :, f"{aircraft_type}_share_{energy_origin}"
                    ],
                    linestyle="-",
                    label=f"Total {aircraft_type}-aircraft type",
                    linewidth=2,
                )
                for pathway in self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    marker = random.choice(valid_markers)
                    valid_markers.remove(marker)
                    self.ax.plot(
                        self.df.loc[
                            self.prospective_years[0] :, f"{pathway.name}_share_{energy_origin}"
                        ].index,
                        self.df.loc[
                            self.prospective_years[0] :, f"{pathway.name}_share_{energy_origin}"
                        ],
                        linestyle="--",
                        marker=marker,
                        markersize=4,
                        label=pathway.name,
                        linewidth=1,
                    )
            self.ax.grid()
            self.ax.set_title(f"Evolution of the {energy_origin}-based fuel blend")
            self.ax.set_xlabel("Year")
            self.ax.set_ylabel(f"Share of pathways in {energy_origin}-based fuel blend [%]")
            # self.ax = plt.gca()
            self.ax.legend(title="Pathway shares")

        # Detailed view of a specific aircraft type and energy origin
        elif energy_origin != "All types" and aircraft_type != "All Types":
            # color = color_mapping.get(energy_origin, "grey")
            for pathway in self.pathways_manager.get(
                aircraft_type=aircraft_type, energy_origin=energy_origin
            ):
                marker = random.choice(valid_markers)
                valid_markers.remove(marker)
                self.ax.plot(
                    self.df.loc[
                        self.prospective_years[0] :,
                        f"{pathway.name}_share_{aircraft_type}_{energy_origin}",
                    ].index,
                    self.df.loc[
                        self.prospective_years[0] :,
                        f"{pathway.name}_share_{aircraft_type}_{energy_origin}",
                    ],
                    linestyle="--",
                    label=pathway.name,
                    linewidth=2,
                )
            self.ax.grid()
            self.ax.set_title(
                f"Evolution of the {aircraft_type}-aircraft type, {energy_origin}-based fuel blend"
            )
            self.ax.set_xlabel("Year")
            self.ax.set_ylabel(
                f"Share of pathways in {aircraft_type}-aircraft type, {energy_origin}-based energy use [%]"
            )
            # self.ax = plt.gca()
            self.ax.legend(title="Pathway shares")

        # Overall view of all aircraft types and energy origins
        elif energy_origin == "All types" and aircraft_type == "All Types":
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                color = color_mapping.get(energy_origin, "grey")
                self.ax.plot(
                    self.df.loc[
                        self.prospective_years[0] :, f"{energy_origin}_share_total_energy"
                    ].index,
                    self.df.loc[self.prospective_years[0] :, f"{energy_origin}_share_total_energy"],
                    linestyle="-",
                    color=color,
                    label=f"Total {energy_origin}-based",
                    linewidth=2,
                )
            for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
                self.ax.plot(
                    self.df.loc[
                        self.prospective_years[0] :, f"energy_consumption_{aircraft_type}"
                    ].index,
                    self.df.loc[self.prospective_years[0] :, f"energy_consumption_{aircraft_type}"]
                    / self.df.loc[self.prospective_years[0] :, "energy_consumption"]
                    * 100,
                    linestyle="--",
                    label=f"Total {aircraft_type}-aircraft type",
                    linewidth=2,
                )

            self.ax.grid()
            self.ax.set_title("Evolution of the overall fuel blend")
            self.ax.set_xlabel("Year")
            self.ax.set_ylabel("Share of aircraft/energy categories in total energy use [%]")
            # self.ax = plt.gca()
            self.ax.legend(title="Aircraft/energy categories shares")

        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])
        self.ax.set_ylim(-10, 110)

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()


class EnergyConsumptionPlot:
    def __init__(self, process):
        data = process.data
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

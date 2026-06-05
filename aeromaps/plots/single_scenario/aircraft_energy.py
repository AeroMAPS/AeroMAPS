import random

import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import widgets
from ipywidgets import interact
from matplotlib.lines import Line2D

from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
from aeromaps.plots.single_scenario_plot import plot_1_x
from aeromaps.plots.single_scenario_plot import plot_1_y
from aeromaps.plots.single_scenario_plot import plot_3_x
from aeromaps.plots.single_scenario_plot import plot_3_y


class MeanFuelEmissionFactorPlot(SingleScenarioPlot):
    required_outputs = [
        "co2_per_energy_mean",
    ]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

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
        
        self.ax.legend()
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_fuel_emission_factor.set_ydata(
            self.df.loc[self.prospective_years, "co2_per_energy_mean"]
        )


class EmissionFactorPerFuelCategory(SingleScenarioPlot):
    required_outputs = [
        "dropin_fuel_biomass_mean_co2_emission_factor",
        "hydrogen_mean_co2_emission_factor",
        "dropin_fuel_electricity_mean_co2_emission_factor",
        "fossil_kerosene_mean_co2_emission_factor",
        "electric_mean_co2_emission_factor",
    ]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

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
            self.df.loc[self.prospective_years, "fossil_kerosene_mean_co2_emission_factor"],
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
        
        self.ax.legend()
        self.ax.set_xlim(self.prospective_years[0] + 1, self.prospective_years[-1])

    def _update_plot_elements(self):
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
            self.df.loc[self.prospective_years, "fossil_kerosene_mean_co2_emission_factor"]
        )
        self.line_electricity_emission_factor.set_ydata(
            self.df.loc[self.prospective_years, "electric_mean_co2_emission_factor"]
        )


class EmissionFactorPerFuel(SingleScenarioPlot):
    # Dynamic columns based on pathways - no static required_outputs
    required_outputs = []

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_1_x, plot_1_y)

    def create_plot(self):
        pathways = self.process.pathways_manager.get_all()
        colors = plt.cm.get_cmap("tab20", len(pathways))
        aircraft_linestyles = {
            "dropin_fuel": "-",
            "hydrogen": "--",
            "electric": "-.",
        }
        dashed_line_needed = False
        used_labels = set()
        for i, p in enumerate(pathways):
            col = f"{p.name}_mean_co2_emission_factor"
            energy_col = f"{p.name}_energy_consumption"
            if col in self.df.columns and energy_col in self.df.columns:
                years = np.array(self.prospective_years)
                vals = self.df.loc[self.prospective_years, col].fillna(np.nan).values
                energy = self.df.loc[self.prospective_years, energy_col].fillna(0).values
                linestyle = aircraft_linestyles.get(getattr(p, "aircraft_type", ""), "solid")

                used_mask = energy > 1e-9
                color_used = colors(i)
                color_unused = "grey"
                linewidth = 2

                seg_start = 0
                current_used = used_mask[0]
                for idx in range(1, len(years)):
                    if used_mask[idx] != current_used:
                        seg_years = years[seg_start : idx + 1]
                        seg_vals = vals[seg_start : idx + 1]
                        if current_used:
                            label = p.name if p.name not in used_labels else None
                            self.ax.plot(
                                seg_years,
                                seg_vals,
                                color=color_used,
                                linewidth=linewidth,
                                linestyle=linestyle,
                                label=label,
                            )
                            if label:
                                used_labels.add(label)
                        else:
                            label = "Not used" if not dashed_line_needed else None
                            self.ax.plot(
                                seg_years,
                                seg_vals,
                                color=color_unused,
                                linewidth=1.5,
                                linestyle="dotted",
                                alpha=0.7,
                                label=label,
                            )
                            if label:
                                dashed_line_needed = True
                        seg_start = idx
                        current_used = used_mask[idx]
                seg_years = years[seg_start:]
                seg_vals = vals[seg_start:]
                if current_used:
                    label = p.name if p.name not in used_labels else None
                    self.ax.plot(
                        seg_years,
                        seg_vals,
                        color=color_used,
                        linewidth=linewidth,
                        linestyle=linestyle,
                        label=label,
                    )
                    if label:
                        used_labels.add(label)
                else:
                    label = "Not used" if not dashed_line_needed else None
                    self.ax.plot(
                        seg_years,
                        seg_vals,
                        color=color_unused,
                        linewidth=1.5,
                        linestyle="dotted",
                        alpha=0.7,
                        label=label,
                    )
                    if label:
                        dashed_line_needed = True

        handles, labels = self.ax.get_legend_handles_labels()
        # Remove duplicate "Not used"
        seen = set()
        new_handles = []
        new_labels = []
        for ha, lb in zip(handles, labels):
            if lb not in seen:
                new_handles.append(ha)
                new_labels.append(lb)
                seen.add(lb)
        # Add "Not used" if needed and not present
        if dashed_line_needed and "Not used" not in new_labels:
            new_handles.append(
                Line2D(
                    [0],
                    [0],
                    color="grey",
                    linestyle="dotted",
                    linewidth=1.5,
                    alpha=0.7,
                    label="Not used",
                )
            )
            new_labels.append("Not used")
        self.ax.set_title("CO2 emission factor by fuel")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("CO2 emission factor [gCO2-eq/MJ]")
        self.ax.legend(new_handles, new_labels)
        self.ax.grid(True)

    def _update_plot_elements(self):
        self.ax.cla()
        self.create_plot()


class ShareFuelPlot(SingleScenarioPlot):
    # Dynamic columns based on pathways - no static required_outputs
    required_outputs = []

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)
        self.pathways_manager = self.process.pathways_manager
        self.plot_interact()

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def plot_interact(self):
        ac_type_widget = widgets.Dropdown(
            options=self.pathways_manager.get_all_types("aircraft_type") + ["All Types"],
            description="Aircraft Type:",
        )

        energy_origin_widget = widgets.Dropdown(
            options=["All types"] + self.pathways_manager.get_all_types("energy_origin"),
            description="Energy origin:",
        )
        interact(self._on_interact_change, aircraft_type=ac_type_widget, energy_origin=energy_origin_widget)

    def create_plot(self):
        pass

    def _update_plot_elements(self):
        pass

    def _on_interact_change(self, aircraft_type, energy_origin):
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
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
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
                    for pathway in pathways:
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
            # 
            self.ax.legend(title="Pathway shares")

        # Focus on an energy origin
        elif energy_origin != "All types" and aircraft_type == "All Types":
            for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
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
                    for pathway in pathways:
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
            # 
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
            # 
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
            # 
            self.ax.legend(title="Aircraft/energy categories shares")

        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])
        self.ax.set_ylim(-10, 110)


class EnergyConsumptionPlot(SingleScenarioPlot):
    required_outputs = [
        "energy_consumption",
    ]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

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
        
        self.ax.legend()
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_energy_consumption.set_ydata(
            self.df.loc[self.prospective_years, "energy_consumption"] / 10**12
        )

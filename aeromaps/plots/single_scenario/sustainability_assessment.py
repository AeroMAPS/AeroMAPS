import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from .constants import plot_2_x, plot_2_y


class CarbonBudgetAssessmentPlot:
    def __init__(self, process):
        data = process.data
        self.parameters = data["float_inputs"]
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_2_x, plot_2_y),
        )
        self.create_plot()

    def create_plot(self):
        # Data to plot
        aviation_carbon_budget = float(self.float_outputs["aviation_carbon_budget"])
        cumulative_carbon_offset = float(self.df.loc[2050, "cumulative_carbon_offset"])
        global_cumulative_co2_emissions_2050 = float(self.df.loc[2050, "cumulative_co2_emissions"])
        world_carbon_budget = float(self.float_outputs["gross_carbon_budget_2050"])
        aviation_carbon_budget_allocated_share = float(
            self.parameters["aviation_carbon_budget_allocated_share"]
        )

        # Plot
        size = 0.3
        outer_vals = [
            global_cumulative_co2_emissions_2050,
            world_carbon_budget - global_cumulative_co2_emissions_2050,
        ]
        inner_vals = [
            aviation_carbon_budget,
            cumulative_carbon_offset,
            world_carbon_budget - aviation_carbon_budget - cumulative_carbon_offset,
        ]

        color = "skyblue"

        if global_cumulative_co2_emissions_2050 <= aviation_carbon_budget:
            color = "green"
        outer_colors = [color, "white"]
        inner_colors = ["grey", "silver", "white"]
        inner_hatches = [None, "/", None]

        self.wedges_out, _ = self.ax.pie(
            outer_vals,
            radius=1,
            colors=outer_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        self.wedges_in, _ = self.ax.pie(
            inner_vals,
            radius=1 - size,
            colors=inner_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
            hatch=inner_hatches,
        )

        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

        self.ax.set(
            aspect="equal",
            title="Estimated climate impact of aviation until 2050\nPresented as a % of the world carbon budget\n(WCB) 2050",
        )

        wedges = [self.wedges_out[0], self.wedges_in[0]]
        texts = [
            str(round(global_cumulative_co2_emissions_2050, 1))
            + " GtCO₂\ncorresponding to\n "
            + str(round(global_cumulative_co2_emissions_2050 / world_carbon_budget * 100, 1))
            + "% of WCB",
            str(round(aviation_carbon_budget_allocated_share, 1))
            + "% of WCB\ni.e.\n"
            + str(round(aviation_carbon_budget, 1))
            + " GtCO₂",
        ]

        p = wedges[0]
        text = texts[0]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        self.ax.annotate(
            text,
            xy=(x, y),
            xytext=(1.2 * np.sign(x), 1.1 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        p = wedges[1]
        text = texts[1]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1 - 45
        y = np.sin(np.deg2rad(ang)) * 0.7
        x = np.cos(np.deg2rad(ang)) * 0.00001
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle, "facecolor": "black"})
        self.ax.annotate(
            text,
            xy=(-x, y),
            xytext=(1.2 * np.sign(x), 2.0 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        legend_elements = [
            Patch(
                facecolor=color,
                label="Cumulative CO₂ emissions of aviation\nbetween 2020 and 2050",
            ),
            Patch(
                color="grey",
                label="Carbon budget 2050 allocated to aviation",
            ),
            Patch(
                facecolor="silver",
                hatch="/",
                label="Cumulative aviation carbon offset",
            ),
        ]

        self.ax.legend(handles=legend_elements, loc="center", bbox_to_anchor=[0.5, -0.12])

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        # self.fig.set_tight_layout(True)

        self.fig.tight_layout()

    def update(self, data):
        self.parameters = data["float_inputs"]
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.ax.clear()

        aviation_carbon_budget = float(self.float_outputs["aviation_carbon_budget"])
        cumulative_carbon_offset = float(self.df.loc[2050, "cumulative_carbon_offset"])
        global_cumulative_co2_emissions_2050 = float(self.df.loc[2050, "cumulative_co2_emissions"])
        world_carbon_budget = float(self.float_outputs["gross_carbon_budget_2050"])
        aviation_carbon_budget_allocated_share = float(
            self.parameters["aviation_carbon_budget_allocated_share"]
        )

        # Plot
        size = 0.3
        outer_vals = [
            global_cumulative_co2_emissions_2050,
            world_carbon_budget - global_cumulative_co2_emissions_2050,
        ]
        inner_vals = [
            aviation_carbon_budget,
            cumulative_carbon_offset,
            world_carbon_budget - aviation_carbon_budget - cumulative_carbon_offset,
        ]

        color = "skyblue"

        if global_cumulative_co2_emissions_2050 <= aviation_carbon_budget:
            color = "green"
        outer_colors = [color, "white"]
        inner_colors = ["grey", "silver", "white"]
        inner_hatches = [None, "/", None]

        self.wedges_out, _ = self.ax.pie(
            outer_vals,
            radius=1,
            colors=outer_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        self.wedges_in, _ = self.ax.pie(
            inner_vals,
            radius=1 - size,
            colors=inner_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
            hatch=inner_hatches,
        )

        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

        self.ax.set(
            aspect="equal",
            title="Estimated climate impact of aviation until 2050\nPresented as a % of the world carbon budget\n(WCB) 2050",
        )

        wedges = [self.wedges_out[0], self.wedges_in[0]]
        texts = [
            str(round(global_cumulative_co2_emissions_2050, 1))
            + " GtCO₂\ncorresponding to\n "
            + str(round(global_cumulative_co2_emissions_2050 / world_carbon_budget * 100, 1))
            + "% of WCB",
            str(round(aviation_carbon_budget_allocated_share, 1))
            + "% of WCB\ni.e.\n"
            + str(round(aviation_carbon_budget, 1))
            + " GtCO₂",
        ]

        p = wedges[0]
        text = texts[0]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        self.ax.annotate(
            text,
            xy=(x, y),
            xytext=(1.2 * np.sign(x), 1.1 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        p = wedges[1]
        text = texts[1]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1 - 45
        y = np.sin(np.deg2rad(ang)) * 0.7
        x = np.cos(np.deg2rad(ang)) * 0.00001
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle, "facecolor": "black"})
        self.ax.annotate(
            text,
            xy=(-x, y),
            xytext=(1.2 * np.sign(x), 2.0 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        legend_elements = [
            Patch(
                color=color,
                label="Cumulative CO₂ emissions of aviation\nbetween 2020 and 2050",
            ),
            Patch(
                color="grey",
                label="Carbon budget 2050 allocated to aviation",
            ),
            Patch(
                facecolor="silver",
                hatch="/",
                label="Cumulative aviation carbon offset",
            ),
        ]

        self.ax.legend(handles=legend_elements, loc="center", bbox_to_anchor=[0.5, -0.12])

        self.fig.canvas.draw()


class TemperatureTargetAssessmentPlot:
    def __init__(self, process):
        data = process.data
        self.parameters = data["float_inputs"]
        self.df = data["vector_outputs"]
        self.df_climate = data["climate_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_2_x, plot_2_y),
        )
        self.create_plot()

    def create_plot(self):
        # Data to plot
        aviation_temperature_target = float(
            self.float_outputs["aviation_temperature_target"]
        )
        aviation_temperature_change = float(
            self.df_climate.loc[self.prospective_years[-1], "temperature_increase_from_aviation"]
        ) - float(
            self.df_climate.loc[self.prospective_years[0], "temperature_increase_from_aviation"]
        )
        world_temperature_target = float(
            self.float_outputs["world_temperature_target"]
        )
        aviation_temperature_target_allocated_share = float(
            self.parameters["aviation_temperature_target_allocated_share"]
        )

        # Plot
        size = 0.3
        if aviation_temperature_change > 0:
            outer_vals = [
                aviation_temperature_change,
                world_temperature_target - aviation_temperature_change,
            ]
        else:
            outer_vals = [
                world_temperature_target + aviation_temperature_change,
                -aviation_temperature_change,
            ]
        inner_vals = [
            aviation_temperature_target,
            world_temperature_target
            - aviation_temperature_target
        ]

        color = "skyblue"

        if aviation_temperature_change <= aviation_temperature_target:
            color = "green"
        if aviation_temperature_change > 0:
            outer_colors = [color, "white"]
        else:
            outer_colors = ["white", color]
        inner_colors = ["grey", "white"]
        inner_hatches = [None, None]

        self.wedges_out, _ = self.ax.pie(
            outer_vals,
            radius=1,
            colors=outer_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        self.wedges_in, _ = self.ax.pie(
            inner_vals,
            radius=1 - size,
            colors=inner_colors,
            hatch=inner_hatches,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

        self.ax.set(
            aspect="equal",
            title="Estimated climate impact of aviation until 2050\nPresented as a % of the remaining world\ntemperature target (RTT)",
        )

        wedges = [self.wedges_out[0], self.wedges_in[0]]
        texts = [
            str(round(1000*aviation_temperature_change, 0))
            + " m°C\ncorresponding to\n "
            + str(
                round(
                    aviation_temperature_change
                    / world_temperature_target
                    * 100,
                    1,
                )
            )
            + "% of RTT",
            str(round(aviation_temperature_target_allocated_share, 1))
            + "% of RTT\ni.e.\n"
            + str(round(1000*aviation_temperature_target, 0))
            + " m°C",
        ]

        p = wedges[0]
        text = texts[0]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        self.ax.annotate(
            text,
            xy=(x, y),
            xytext=(1.2 * np.sign(x), 1.1 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        p = wedges[1]
        text = texts[1]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1 - 45
        y = np.sin(np.deg2rad(ang)) * 0.7
        x = np.cos(np.deg2rad(ang)) * 0.00001
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle, "facecolor": "black"})
        self.ax.annotate(
            text,
            xy=(-x, y),
            xytext=(1.2 * np.sign(x), 2.0 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        legend_elements = [
            Patch(
                color=color,
                label="Temperature change induced by aviation\nbetween 2020 and 2050",
            ),
            Patch(
                color="grey",
                label="Remaining temperature target allocated\nto aviation",
            ),
        ]

        self.ax.legend(handles=legend_elements, loc="center", bbox_to_anchor=[0.5, -0.12])

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        # self.fig.set_tight_layout(True)

        self.fig.tight_layout()

    def update(self, data):
        self.parameters = data["float_inputs"]
        self.df = data["vector_outputs"]
        self.df_climate = data["climate_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.ax.clear()

        # Data to plot
        aviation_temperature_target = float(
            self.float_outputs["aviation_temperature_target"]
        )
        aviation_temperature_change = float(
            self.df_climate.loc[self.prospective_years[-1], "temperature_increase_from_aviation"]
        ) - float(
            self.df_climate.loc[self.prospective_years[0], "temperature_increase_from_aviation"]
        )
        world_temperature_target = float(
            self.float_outputs["world_temperature_target"]
        )
        aviation_temperature_target_allocated_share = float(
            self.parameters["aviation_temperature_target_allocated_share"]
        )

        # Plot
        size = 0.3
        if aviation_temperature_change > 0:
            outer_vals = [
                aviation_temperature_change,
                world_temperature_target - aviation_temperature_change,
            ]
        else:
            outer_vals = [
                world_temperature_target + aviation_temperature_change,
                -aviation_temperature_change,
            ]
        inner_vals = [
            aviation_temperature_target,
            world_temperature_target
            - aviation_temperature_target
        ]

        color = "skyblue"

        if aviation_temperature_change <= aviation_temperature_target:
            color = "green"
        if aviation_temperature_change > 0:
            outer_colors = [color, "white"]
        else:
            outer_colors = ["white", color]
        inner_colors = ["grey", "white"]
        inner_hatches = [None, None]

        self.wedges_out, _ = self.ax.pie(
            outer_vals,
            radius=1,
            colors=outer_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        self.wedges_in, _ = self.ax.pie(
            inner_vals,
            radius=1 - size,
            colors=inner_colors,
            hatch=inner_hatches,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

        self.ax.set(
            aspect="equal",
            title="Estimated climate impact of aviation until 2050\nPresented as a % of the remaining world\ntemperature target (RTT)",
        )

        wedges = [self.wedges_out[0], self.wedges_in[0]]
        texts = [
            str(round(1000*aviation_temperature_change, 0))
            + " m°C\ncorresponding to\n "
            + str(
                round(
                    aviation_temperature_change
                    / world_temperature_target
                    * 100,
                    1,
                )
            )
            + "% of RTT",
            str(round(aviation_temperature_target_allocated_share, 1))
            + "% of RTT\ni.e.\n"
            + str(round(1000*aviation_temperature_target, 0))
            + " m°C",
        ]

        p = wedges[0]
        text = texts[0]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        self.ax.annotate(
            text,
            xy=(x, y),
            xytext=(1.2 * np.sign(x), 1.1 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        p = wedges[1]
        text = texts[1]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1 - 45
        y = np.sin(np.deg2rad(ang)) * 0.7
        x = np.cos(np.deg2rad(ang)) * 0.00001
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle, "facecolor": "black"})
        self.ax.annotate(
            text,
            xy=(-x, y),
            xytext=(1.2 * np.sign(x), 2.0 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        legend_elements = [
            Patch(
                color=color,
                label="Temperature change induced by aviation\nbetween 2020 and 2050",
            ),
            Patch(
                color="grey",
                label="Remaining temperature target allocated\nto aviation",
            ),
        ]

        self.ax.legend(handles=legend_elements, loc="center", bbox_to_anchor=[0.5, -0.12])

        self.fig.canvas.draw()


class BiomassResourceBudgetAssessmentPlot:
    def __init__(self, process):
        data = process.data
        self.parameters = data["float_inputs"]
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_2_x, plot_2_y),
        )
        self.create_plot()

    def create_plot(self):
        # Data to plot
        # CAUTION: This plot is not generic - oriented, although made compatible (ie, works only if "biomass" in resource conf file)
        aviation_available_biomass = (
            float(self.df["biomass_availability_aviation_allocated"][2050]) / 1e12
        )
        biomass_consumption = self.df["biomass_total_consumption"] / 1e12
        biomass_consumption_end_year = float(biomass_consumption[self.prospective_years[-1]])
        available_biomass_total = float(self.df["biomass_availability_global"][2050]) / 1e12
        aviation_biomass_allocated_share = float(
            self.df["biomass_overall_aviation_allocated_share"][2050]
        )

        # Plot
        size = 0.3
        outer_vals = [
            biomass_consumption_end_year,
            available_biomass_total - biomass_consumption_end_year,
        ]
        inner_vals = [
            aviation_available_biomass,
            available_biomass_total - aviation_available_biomass,
        ]

        color = "skyblue"

        if biomass_consumption_end_year <= aviation_available_biomass:
            color = "green"
        outer_colors = [color, "white"]
        inner_colors = ["grey", "white"]

        self.wedges_out, _ = self.ax.pie(
            outer_vals,
            radius=1,
            colors=outer_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        self.wedges_in, _ = self.ax.pie(
            inner_vals,
            radius=1 - size,
            colors=inner_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

        self.ax.set(
            aspect="equal",
            title="Estimated biomass consumption of aviation in 2050\nPresented as a % of the available biomass\n(AB) in 2050",
        )

        wedges = [self.wedges_out[0], self.wedges_in[0]]
        texts = [
            str(round(biomass_consumption_end_year, 1))
            + " EJ\ncorresponding to\n "
            + str(round(biomass_consumption_end_year / available_biomass_total * 100, 1))
            + "% of AB",
            str(round(aviation_biomass_allocated_share, 1))
            + "% of AB\ni.e.\n"
            + str(round(aviation_available_biomass, 1))
            + " EJ",
        ]

        p = wedges[0]
        text = texts[0]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        self.ax.annotate(
            text,
            xy=(x, y),
            xytext=(1.2 * np.sign(x), 1.1 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        p = wedges[1]
        text = texts[1]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1 - 45
        y = np.sin(np.deg2rad(ang)) * 0.7
        x = np.cos(np.deg2rad(ang)) * 0.00001
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle, "facecolor": "black"})
        self.ax.annotate(
            text,
            xy=(-x, y),
            xytext=(1.2 * np.sign(x), 2.0 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        legend_elements = [
            Patch(
                color=color,
                label="Biomass consumption of aviation in 2050",
            ),
            Patch(
                color="grey",
                label="Biomass resources allocated to aviation",
            ),
        ]

        self.ax.legend(handles=legend_elements, loc="center", bbox_to_anchor=[0.5, -0.12])

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        # self.fig.set_tight_layout(True)

        self.fig.tight_layout()

    def update(self, data):
        self.parameters = data["float_inputs"]
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.ax.clear()

        # CAUTION: This plot is not generic - oriented, although made compatible (ie, works only if "biomass" in resource conf file)
        aviation_available_biomass = (
            float(self.df["biomass_availability_aviation_allocated"][2050]) / 1e12
        )
        biomass_consumption = self.df["biomass_total_consumption"] / 1e12
        biomass_consumption_end_year = float(biomass_consumption[self.prospective_years[-1]])
        available_biomass_total = float(self.df["biomass_availability_global"][2050]) / 1e12
        aviation_biomass_allocated_share = float(
            self.df["biomass_overall_aviation_allocated_share"][2050]
        )

        # Plot
        size = 0.3
        outer_vals = [
            biomass_consumption_end_year,
            available_biomass_total - biomass_consumption_end_year,
        ]
        inner_vals = [
            aviation_available_biomass,
            available_biomass_total - aviation_available_biomass,
        ]

        color = "skyblue"

        if biomass_consumption_end_year <= aviation_available_biomass:
            color = "green"
        outer_colors = [color, "white"]
        inner_colors = ["grey", "white"]

        self.wedges_out, _ = self.ax.pie(
            outer_vals,
            radius=1,
            colors=outer_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        self.wedges_in, _ = self.ax.pie(
            inner_vals,
            radius=1 - size,
            colors=inner_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

        self.ax.set(
            aspect="equal",
            title="Estimated biomass consumption of aviation in 2050\nPresented as a % of the available biomass\n(AB) in 2050",
        )

        wedges = [self.wedges_out[0], self.wedges_in[0]]
        texts = [
            str(round(biomass_consumption_end_year, 1))
            + " EJ\ncorresponding to\n "
            + str(round(biomass_consumption_end_year / available_biomass_total * 100, 1))
            + "% of AB",
            str(round(aviation_biomass_allocated_share, 1))
            + "% of AB\ni.e.\n"
            + str(round(aviation_available_biomass, 1))
            + " EJ",
        ]

        p = wedges[0]
        text = texts[0]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        self.ax.annotate(
            text,
            xy=(x, y),
            xytext=(1.2 * np.sign(x), 1.1 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        p = wedges[1]
        text = texts[1]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1 - 45
        y = np.sin(np.deg2rad(ang)) * 0.7
        x = np.cos(np.deg2rad(ang)) * 0.00001
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle, "facecolor": "black"})
        self.ax.annotate(
            text,
            xy=(-x, y),
            xytext=(1.2 * np.sign(x), 2.0 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        legend_elements = [
            Patch(
                color=color,
                label="Biomass consumption of aviation in 2050",
            ),
            Patch(
                color="grey",
                label="Biomass resources allocated to aviation",
            ),
        ]

        self.ax.legend(handles=legend_elements, loc="center", bbox_to_anchor=[0.5, -0.12])

        self.fig.canvas.draw()


class ElectricityResourceBudgetAssessmentPlot:
    def __init__(self, process):
        data = process.data
        self.parameters = data["float_inputs"]
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_2_x, plot_2_y),
        )
        self.create_plot()

    def create_plot(self):
        # Data to plot (updated to new input format)
        aviation_available_electricity = float(
            self.df["electricity_availability_aviation_allocated"][2050] / 1e12
        )
        electricity_consumption = self.df["electricity_total_consumption"] / 1e12
        electricity_consumption_end_year = float(
            electricity_consumption[self.prospective_years[-1]]
        )
        available_electricity = float(self.df["electricity_availability_global"][2050]) / 1e12
        aviation_electricity_allocated_share = float(
            self.df["electricity_overall_aviation_allocated_share"][2050]
        )

        # Plot
        size = 0.3
        outer_vals = [
            electricity_consumption_end_year,
            available_electricity - electricity_consumption_end_year,
        ]
        inner_vals = [
            aviation_available_electricity,
            available_electricity - aviation_available_electricity,
        ]

        color = "skyblue"

        if electricity_consumption_end_year <= aviation_available_electricity:
            color = "green"
        outer_colors = [color, "white"]
        inner_colors = ["grey", "white"]

        self.wedges_out, _ = self.ax.pie(
            outer_vals,
            radius=1,
            colors=outer_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        self.wedges_in, _ = self.ax.pie(
            inner_vals,
            radius=1 - size,
            colors=inner_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

        self.ax.set(
            aspect="equal",
            title="Estimated electricity consumption of aviation in 2050\nPresented as a % of the available elecltricity\n(AE) in 2050",
        )

        wedges = [self.wedges_out[0], self.wedges_in[0]]
        texts = [
            str(round(electricity_consumption_end_year, 1))
            + " EJ\ncorresponding to\n "
            + str(round(electricity_consumption_end_year / available_electricity * 100, 1))
            + "% of AE",
            str(round(aviation_electricity_allocated_share, 1))
            + "% of AE\ni.e.\n"
            + str(round(aviation_available_electricity, 1))
            + " EJ",
        ]

        p = wedges[0]
        text = texts[0]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        self.ax.annotate(
            text,
            xy=(x, y),
            xytext=(1.2 * np.sign(x), 1.1 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        p = wedges[1]
        text = texts[1]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1 - 45
        y = np.sin(np.deg2rad(ang)) * 0.7
        x = np.cos(np.deg2rad(ang)) * 0.00001
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle, "facecolor": "black"})
        self.ax.annotate(
            text,
            xy=(-x, y),
            xytext=(1.2 * np.sign(x), 2.0 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        legend_elements = [
            Patch(
                color=color,
                label="Electricity consumption of aviation in 2050",
            ),
            Patch(
                color="grey",
                label="Electricity resources allocated to aviation",
            ),
        ]

        self.ax.legend(handles=legend_elements, loc="center", bbox_to_anchor=[0.5, -0.12])

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        # self.fig.set_tight_layout(True)

        self.fig.tight_layout()

    def update(self, data):
        self.parameters = data["float_inputs"]
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.ax.clear()

        # Data to plot (updated to new input format)
        aviation_available_electricity = (
            float(self.df["electricity_availability_aviation_allocated"][2050]) / 1e12
        )
        electricity_consumption = self.df["electricity_total_consumption"] / 1e12
        electricity_consumption_end_year = float(
            electricity_consumption[self.prospective_years[-1]]
        )
        available_electricity = float(self.df["electricity_availability_global"][2050]) / 1e12
        aviation_electricity_allocated_share = float(
            self.df["electricity_overall_aviation_allocated_share"][2050]
        )

        # Plot
        size = 0.3
        outer_vals = [
            electricity_consumption_end_year,
            available_electricity - electricity_consumption_end_year,
        ]
        inner_vals = [
            aviation_available_electricity,
            available_electricity - aviation_available_electricity,
        ]

        color = "skyblue"

        if electricity_consumption_end_year <= aviation_available_electricity:
            color = "green"
        outer_colors = [color, "white"]
        inner_colors = ["grey", "white"]

        self.wedges_out, _ = self.ax.pie(
            outer_vals,
            radius=1,
            colors=outer_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        self.wedges_in, _ = self.ax.pie(
            inner_vals,
            radius=1 - size,
            colors=inner_colors,
            startangle=90,
            wedgeprops=dict(width=size, edgecolor="k", alpha=0.8),
        )

        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

        self.ax.set(
            aspect="equal",
            title="Estimated electricity consumption of aviation in 2050\nPresented as a % of the available elecltricity\n(AE) in 2050",
        )

        wedges = [self.wedges_out[0], self.wedges_in[0]]
        texts = [
            str(round(electricity_consumption_end_year, 1))
            + " EJ\ncorresponding to\n "
            + str(round(electricity_consumption_end_year / available_electricity * 100, 1))
            + "% of AE",
            str(round(aviation_electricity_allocated_share, 1))
            + "% of AE\ni.e.\n"
            + str(round(aviation_available_electricity, 1))
            + " EJ",
        ]

        p = wedges[0]
        text = texts[0]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        self.ax.annotate(
            text,
            xy=(x, y),
            xytext=(1.2 * np.sign(x), 1.1 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        p = wedges[1]
        text = texts[1]

        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1 - 45
        y = np.sin(np.deg2rad(ang)) * 0.7
        x = np.cos(np.deg2rad(ang)) * 0.00001
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle, "facecolor": "black"})
        self.ax.annotate(
            text,
            xy=(-x, y),
            xytext=(1.2 * np.sign(x), 2.0 * y),
            horizontalalignment=horizontalalignment,
            **kw,
        )

        legend_elements = [
            Patch(
                color=color,
                label="Electricity consumption of aviation in 2050",
            ),
            Patch(
                color="grey",
                label="Electricity resources allocated to aviation",
            ),
        ]

        self.ax.legend(handles=legend_elements, loc="center", bbox_to_anchor=[0.5, -0.12])

        self.fig.canvas.draw()


class MultidisciplinaryAssessmentPlot:
    def __init__(self, process):
        data = process.data
        self.parameters = data["float_inputs"]
        self.df = data["vector_outputs"]
        self.df_climate = data["climate_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_2_x, plot_2_y), subplot_kw={"projection": "polar"}
        )
        self.create_plot()

    def create_plot(self):
        # Carbon budget
        gross_carbon_budget = float(self.float_outputs["gross_carbon_budget_2050"])
        aviation_carbon_budget = float(self.float_outputs["aviation_carbon_budget"])
        cumulative_co2_emissions = float(self.df.loc[2050, "cumulative_co2_emissions"])

        # Biomass (new input format)
        available_biomass_total = self.df["biomass_availability_global"][2050] / 1e12
        aviation_available_biomass = self.df["biomass_availability_aviation_allocated"][2050] / 1e12
        biomass_consumption_end_year = float(
            self.df["biomass_total_consumption"][self.prospective_years[-1]] / 1e12
        )

        # Electricity (new input format)
        available_electricity_total = self.df["electricity_availability_global"][2050] / 1e12
        aviation_available_electricity = (
            self.df["electricity_availability_aviation_allocated"][2050] / 1e12
        )
        electricity_consumption_end_year = float(
            self.df["electricity_total_consumption"][self.prospective_years[-1]] / 1e12
        )

        # Temperature
        world_temperature_target = float(
            self.float_outputs["world_temperature_target"]
        )
        aviation_temperature_target = float(
            self.float_outputs["aviation_temperature_target"]
        )
        aviation_temperature_change = float(
            self.df_climate.loc[self.prospective_years[-1], "temperature_increase_from_aviation"]
        ) - float(
            self.df_climate.loc[self.prospective_years[0], "temperature_increase_from_aviation"]
        )

        categories = [
            "Climate",
            "CO₂",
            "Biomass",
            "Electricity",
        ]

        budgets = [
            aviation_temperature_target / world_temperature_target * 100,
            aviation_carbon_budget / gross_carbon_budget * 100,
            aviation_available_biomass / available_biomass_total * 100,
            aviation_available_electricity / available_electricity_total * 100,
        ]

        consumptions = [
            np.max(
                [aviation_temperature_change / world_temperature_target * 100, 0]
            ),
            cumulative_co2_emissions / gross_carbon_budget * 100,
            biomass_consumption_end_year / available_biomass_total * 100,
            electricity_consumption_end_year / available_electricity_total * 100,
        ]

        df_plot = pd.DataFrame(
            list(zip(categories, consumptions, budgets)),
            columns=["Category", "Consumption share", "Budget share"],
        )

        lowerLimit = 0

        # Compute max and min in the dataset
        max = df_plot[["Consumption share", "Budget share"]].max().max() + lowerLimit

        # Let's compute heights: they are a conversion of each item value in those new coordinates
        # In our example, 0 in the dataset will be converted to the lowerLimit (10)
        # The maximum will be converted to the upperLimit (100)
        slope = (max - lowerLimit) / max
        heights_consumption = slope * df_plot["Consumption share"] + lowerLimit
        heights_budget = slope * df_plot["Budget share"] + lowerLimit

        # # Compute the width of each bar. In total we have 2*Pi = 360°
        width = 2 * np.pi / len(df_plot.index) - 0.2
        #
        # # Compute the angle each bar is centered on:
        angles = np.linspace(np.pi / 4, (2 + 1 / 4) * np.pi, len(df_plot), endpoint=False)
        # Draw bars

        self.multidisciplinary_bars_plot = self.ax.bar(
            x=angles,
            height=heights_consumption,
            width=width,
            bottom=lowerLimit,
            linewidth=0,
            color="orange",
            edgecolor="none",
            alpha=0.4,
            label="Impacts",
        )

        self.multidisciplinary_bars_plot = self.ax.bar(
            x=angles,
            height=heights_consumption,
            width=width,
            bottom=lowerLimit,
            linewidth=2,
            color="none",
            edgecolor="orange",
            alpha=1,
        )

        self.multidisciplinary_bars_plot = self.ax.bar(
            x=angles,
            height=heights_budget,
            width=width,
            bottom=lowerLimit,
            linewidth=0,
            color="green",
            edgecolor="none",
            alpha=0.4,
            label="Budgets",
        )

        self.multidisciplinary_bars_plot = self.ax.bar(
            x=angles,
            height=heights_budget,
            width=width,
            bottom=lowerLimit,
            linewidth=2,
            color="none",
            edgecolor="green",
            alpha=1,
        )

        self.ax.set_xticks(angles)
        self.ax.set_xticklabels(df_plot["Category"], size=10, zorder=11)

        def percentage_formatter(x, pos):
            return f"{x:.0f}%"

        self.ax.set_rlabel_position(90)

        # Apply the custom tick formatter to the radial axis
        self.ax.yaxis.set_major_formatter(mticker.FuncFormatter(percentage_formatter))

        self.ax.grid(axis="x")
        self.ax.set_title(
            "Scenario impacts and allocated budgets\nPresented as a % of world budgets", y=1.05
        )

        for tick in self.ax.xaxis.get_major_ticks():
            tick.set_pad(10)

        self.ax.legend(loc="lower center", bbox_to_anchor=[0.5, -0.15], ncol=2)

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        # Set the labels
        # self.fig.set_tight_layout(True)

        self.fig.tight_layout()

    def update(self, data):
        self.parameters = data["float_inputs"]
        self.df = data["vector_outputs"]
        self.df_climate = data["climate_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.ax.clear()

        gross_carbon_budget = float(self.float_outputs["gross_carbon_budget_2050"])
        aviation_carbon_budget = float(self.float_outputs["aviation_carbon_budget"])
        cumulative_co2_emissions = float(self.df.loc[2050, "cumulative_co2_emissions"])

        # Biomass (new input format)
        available_biomass_total = self.df["biomass_availability_global"][2050] / 1e12
        aviation_available_biomass = self.df["biomass_availability_aviation_allocated"][2050] / 1e12
        biomass_consumption_end_year = float(
            self.df["biomass_total_consumption"][self.prospective_years[-1]] / 1e12
        )

        # Electricity (new input format)
        available_electricity_total = self.df["electricity_availability_global"][2050] / 1e12
        aviation_available_electricity = (
            self.df["electricity_availability_aviation_allocated"][2050] / 1e12
        )
        electricity_consumption_end_year = float(
            self.df["electricity_total_consumption"][self.prospective_years[-1]] / 1e12
        )

        # Temperature
        world_temperature_target = float(
            self.float_outputs["world_temperature_target"]
        )
        aviation_temperature_target = float(
            self.float_outputs["aviation_temperature_target"]
        )
        aviation_temperature_change = float(
            self.df_climate.loc[self.prospective_years[-1], "temperature_increase_from_aviation"]
        ) - float(
            self.df_climate.loc[self.prospective_years[0], "temperature_increase_from_aviation"]
        )

        categories = [
            "Climate",
            "CO₂",
            "Biomass",
            "Electricity",
        ]

        budgets = [
            aviation_temperature_target / world_temperature_target * 100,
            aviation_carbon_budget / gross_carbon_budget * 100,
            aviation_available_biomass / available_biomass_total * 100,
            aviation_available_electricity / available_electricity_total * 100,
        ]

        consumptions = [
            np.max(
                [aviation_temperature_change / world_temperature_target * 100, 0]
            ),
            cumulative_co2_emissions / gross_carbon_budget * 100,
            biomass_consumption_end_year / available_biomass_total * 100,
            electricity_consumption_end_year / available_electricity_total * 100,
        ]

        df_plot = pd.DataFrame(
            list(zip(categories, consumptions, budgets)),
            columns=["Category", "Consumption share", "Budget share"],
        )

        lowerLimit = 0

        # Compute max and min in the dataset
        max = df_plot[["Consumption share", "Budget share"]].max().max() + lowerLimit

        # Let's compute heights: they are a conversion of each item value in those new coordinates
        # In our example, 0 in the dataset will be converted to the lowerLimit (10)
        # The maximum will be converted to the upperLimit (100)
        slope = (max - lowerLimit) / max
        heights_consumption = slope * df_plot["Consumption share"] + lowerLimit
        heights_budget = slope * df_plot["Budget share"] + lowerLimit

        # # Compute the width of each bar. In total we have 2*Pi = 360°
        width = 2 * np.pi / len(df_plot.index) - 0.2
        #
        # # Compute the angle each bar is centered on:
        angles = np.linspace(np.pi / 4, (2 + 1 / 4) * np.pi, len(df_plot), endpoint=False)
        # Draw bars

        self.multidisciplinary_bars_plot = self.ax.bar(
            x=angles,
            height=heights_consumption,
            width=width,
            bottom=lowerLimit,
            linewidth=0,
            color="orange",
            edgecolor="none",
            alpha=0.4,
            label="Impacts",
        )

        self.multidisciplinary_bars_plot = self.ax.bar(
            x=angles,
            height=heights_consumption,
            width=width,
            bottom=lowerLimit,
            linewidth=2,
            color="none",
            edgecolor="orange",
            alpha=1,
        )

        self.multidisciplinary_bars_plot = self.ax.bar(
            x=angles,
            height=heights_budget,
            width=width,
            bottom=lowerLimit,
            linewidth=0,
            color="green",
            edgecolor="none",
            alpha=0.4,
            label="Budgets",
        )

        self.multidisciplinary_bars_plot = self.ax.bar(
            x=angles,
            height=heights_budget,
            width=width,
            bottom=lowerLimit,
            linewidth=2,
            color="none",
            edgecolor="green",
            alpha=1,
        )

        self.ax.set_xticks(angles)
        self.ax.set_xticklabels(df_plot["Category"], size=10, zorder=11)

        def percentage_formatter(x, pos):
            return f"{x:.0f}%"

        self.ax.set_rlabel_position(90)

        # Apply the custom tick formatter to the radial axis
        self.ax.yaxis.set_major_formatter(mticker.FuncFormatter(percentage_formatter))

        self.ax.grid(axis="x")
        self.ax.set_title(
            "Scenario impacts and allocated budgets\nPresented as a % of world budgets", y=1.05
        )

        for tick in self.ax.xaxis.get_major_ticks():
            tick.set_pad(10)

        self.ax.legend(loc="lower center", bbox_to_anchor=[0.5, -0.15], ncol=2)

        self.fig.canvas.draw()

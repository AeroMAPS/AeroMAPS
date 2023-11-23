import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .constants import plot_2_x, plot_2_y


class CarbonBudgetAssessmentPlot:
    def __init__(self, data):
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
            title="Estimated climate impact of aviation until 2050\nPresented as a % of the world carbon budget\n(WCB) 2050",
        )

        wedges = [self.wedges_out[0], self.wedges_in[0]]
        texts = [
            str(round(global_cumulative_co2_emissions_2050, 1))
            + " GtCO2\ncorresponding to\n "
            + str(round(global_cumulative_co2_emissions_2050 / world_carbon_budget * 100, 1))
            + "% of WCB",
            str(round(aviation_carbon_budget_allocated_share, 1))
            + "% of WCB\ni.e.\n"
            + str(round(aviation_carbon_budget, 1))
            + " GtCO2",
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
            Line2D(
                [0],
                [0],
                color=color,
                lw=6,
                label="Cumulative CO2 emissions of aviation\nbetween 2020 and 2050",
            ),
            Line2D(
                [0],
                [0],
                color="grey",
                lw=6,
                label="Carbon budget 2050 allocated to aviation",
            ),
            Line2D(
                [0],
                [0],
                color="silver",
                lw=6,
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
            title="Estimated climate impact of aviation until 2050\nPresented as a % of the world carbon budget\n(WCB) 2050",
        )

        wedges = [self.wedges_out[0], self.wedges_in[0]]
        texts = [
            str(round(global_cumulative_co2_emissions_2050, 1))
            + " GtCO2\ncorresponding to\n "
            + str(round(global_cumulative_co2_emissions_2050 / world_carbon_budget * 100, 1))
            + "% of WCB",
            str(round(aviation_carbon_budget_allocated_share, 1))
            + "% of WCB\ni.e.\n"
            + str(round(aviation_carbon_budget, 1))
            + " GtCO2",
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
            Line2D(
                [0],
                [0],
                color=color,
                lw=6,
                label="Cumulative CO2 emissions of aviation\nbetween 2020 and 2050",
            ),
            Line2D(
                [0],
                [0],
                color="grey",
                lw=6,
                label="Carbon budget 2050 allocated to aviation",
            ),
            Line2D(
                [0],
                [0],
                color="grey",
                lw=6,
                label="Cumulative aviation carbon offset",
            ),
        ]

        self.ax.legend(handles=legend_elements, loc="center", bbox_to_anchor=[0.5, -0.12])

        self.fig.canvas.draw()


class EquivalentCarbonBudgetAssessmentPlot:
    def __init__(self, data):
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
        aviation_equivalent_carbon_budget = float(
            self.float_outputs["aviation_equivalent_carbon_budget"]
        )
        cumulative_carbon_offset = float(self.df.loc[2050, "cumulative_carbon_offset"])
        global_cumulative_equivalent_emissions_2050 = float(
            self.df.loc[2050, "cumulative_total_equivalent_emissions"]
        )
        world_equivalent_carbon_budget = float(
            self.float_outputs["equivalent_gross_carbon_budget_2050"]
        )
        aviation_equivalent_carbon_budget_allocated_share = float(
            self.parameters["aviation_equivalentcarbonbudget_allocated_share"]
        )

        # Plot
        size = 0.3
        if global_cumulative_equivalent_emissions_2050 > 0:
            outer_vals = [
                global_cumulative_equivalent_emissions_2050,
                world_equivalent_carbon_budget - global_cumulative_equivalent_emissions_2050,
            ]
        else:
            outer_vals = [
                world_equivalent_carbon_budget + global_cumulative_equivalent_emissions_2050,
                -global_cumulative_equivalent_emissions_2050,
            ]
        inner_vals = [
            aviation_equivalent_carbon_budget,
            cumulative_carbon_offset,
            world_equivalent_carbon_budget
            - aviation_equivalent_carbon_budget
            - cumulative_carbon_offset,
        ]

        color = "skyblue"

        if global_cumulative_equivalent_emissions_2050 <= aviation_equivalent_carbon_budget:
            color = "green"
        if global_cumulative_equivalent_emissions_2050 > 0:
            outer_colors = [color, "white"]
        else:
            outer_colors = ["white", color]
        inner_colors = ["grey", "silver", "white"]

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
            title="Estimated climate impact of aviation until 2050\nPresented as a % of the equivalent world carbon\nbudget (EWCB) 2050",
        )

        wedges = [self.wedges_out[0], self.wedges_in[0]]
        texts = [
            str(round(global_cumulative_equivalent_emissions_2050, 1))
            + " GtCO2-we\ncorresponding to\n "
            + str(
                round(
                    global_cumulative_equivalent_emissions_2050
                    / world_equivalent_carbon_budget
                    * 100,
                    1,
                )
            )
            + "% of EWCB",
            str(round(aviation_equivalent_carbon_budget_allocated_share, 1))
            + "% of EWCB\ni.e.\n"
            + str(round(aviation_equivalent_carbon_budget, 1))
            + " GtCO2-we",
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
            Line2D(
                [0],
                [0],
                color=color,
                lw=6,
                label="Cumulative equivalent emissions of aviation\nbetween 2020 and 2050",
            ),
            Line2D(
                [0],
                [0],
                color="grey",
                lw=6,
                label="Equivalent carbon budget 2050 allocated\nto aviation",
            ),
            Line2D(
                [0],
                [0],
                color="silver",
                lw=6,
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

        # Data to plot
        aviation_equivalent_carbon_budget = float(
            self.float_outputs["aviation_equivalent_carbon_budget"]
        )
        cumulative_carbon_offset = float(self.df.loc[2050, "cumulative_carbon_offset"])
        global_cumulative_equivalent_emissions_2050 = float(
            self.df.loc[2050, "cumulative_total_equivalent_emissions"]
        )
        world_equivalent_carbon_budget = float(
            self.float_outputs["equivalent_gross_carbon_budget_2050"]
        )
        aviation_equivalent_carbon_budget_allocated_share = float(
            self.parameters["aviation_equivalentcarbonbudget_allocated_share"]
        )

        # Plot
        size = 0.3
        if global_cumulative_equivalent_emissions_2050 > 0:
            outer_vals = [
                global_cumulative_equivalent_emissions_2050,
                world_equivalent_carbon_budget - global_cumulative_equivalent_emissions_2050,
            ]
        else:
            outer_vals = [
                world_equivalent_carbon_budget + global_cumulative_equivalent_emissions_2050,
                -global_cumulative_equivalent_emissions_2050,
            ]
        inner_vals = [
            aviation_equivalent_carbon_budget,
            cumulative_carbon_offset,
            world_equivalent_carbon_budget
            - aviation_equivalent_carbon_budget
            - cumulative_carbon_offset,
        ]

        color = "skyblue"

        if global_cumulative_equivalent_emissions_2050 <= aviation_equivalent_carbon_budget:
            color = "green"
        if global_cumulative_equivalent_emissions_2050 > 0:
            outer_colors = [color, "white"]
        else:
            outer_colors = ["white", color]
        inner_colors = ["grey", "silver", "white"]

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
            title="Estimated climate impact of aviation until 2050\nPresented as a % of the equivalent world carbon\nbudget (EWCB) 2050",
        )

        wedges = [self.wedges_out[0], self.wedges_in[0]]
        texts = [
            str(round(global_cumulative_equivalent_emissions_2050, 1))
            + " GtCO2-we\ncorresponding to\n "
            + str(
                round(
                    global_cumulative_equivalent_emissions_2050
                    / world_equivalent_carbon_budget
                    * 100,
                    1,
                )
            )
            + "% of EWCB",
            str(round(aviation_equivalent_carbon_budget_allocated_share, 1))
            + "% of EWCB\ni.e.\n"
            + str(round(aviation_equivalent_carbon_budget, 1))
            + " GtCO2-we",
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
            Line2D(
                [0],
                [0],
                color=color,
                lw=6,
                label="Cumulative equivalent emissions of aviation\nbetween 2020 and 2050",
            ),
            Line2D(
                [0],
                [0],
                color="grey",
                lw=6,
                label="Equivalent carbon budget 2050 allocated\nto aviation",
            ),
            Line2D(
                [0],
                [0],
                color="silver",
                lw=6,
                label="Cumulative aviation carbon offset",
            ),
        ]

        self.ax.legend(handles=legend_elements, loc="center", bbox_to_anchor=[0.5, -0.12])

        self.fig.canvas.draw()


class EquivalentCarbonBudgetAssessmentPlotOld:
    def __init__(self, data):
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
        barWidth = 0.6

        y1 = [
            self.df.loc[2050, "cumulative_total_equivalent_emissions"],
            self.float_outputs["aviation_equivalent_carbon_budget"],
        ]
        r = range(len(y1))
        self.line_carbon_budget = self.ax.bar(r, y1, width=barWidth, color=["grey" for i in y1])

        i = 0
        for rect, h in zip(self.line_carbon_budget, y1):
            rect.set_height(h)
            if i == 0:
                if y1[i] < y1[i + 1]:
                    rect.set_color("green")
                else:
                    rect.set_color("skyblue")
            i += 1

        self.ax.set_xticks(r)
        self.ax.set_xticklabels(
            [
                "Equivalent cumulative\nemissions",
                "Aviation equivalent\naviation carbon\nbudget 2050",
            ],
        )
        self.ax.set_title(
            "Estimated climate impact of aviation until 2050\nPresented in relation to equivalent\ncarbon budget for aviation"
        )
        self.ax.set_ylabel("Equivalent cumulative emissions\nbetween 2020 and 2050 [GtCO2-we]")

        self.ax2 = self.ax.twinx()

        ymin, ymax = self.ax.get_ylim()
        self.ax2.set_ylim([ymin, ymax])
        new_labels = [
            round(float(self.float_outputs["equivalent_carbon_budget_consumed_share"]), 1),
            round(self.parameters["aviation_equivalentcarbonbudget_allocated_share"], 1),
        ]

        self.ax2.set_yticks([y1[0], float(y1[1])])
        self.ax2.set_yticklabels(new_labels)
        self.ax2.set_ylabel("Share of the world equivalent\ncarbon budget [%]")

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, data):
        self.parameters = data["float_inputs"]
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        y1 = [
            self.df.loc[2050, "cumulative_total_equivalent_emissions"],
            self.float_outputs["aviation_equivalent_carbon_budget"],
        ]
        i = 0
        for rect, h in zip(self.line_carbon_budget, y1):
            rect.set_height(h)
            if i == 0:
                if y1[i] < y1[i + 1]:
                    rect.set_color("green")
                else:
                    rect.set_color("skyblue")
            i += 1

        self.ax.relim()
        self.ax.autoscale_view()

        ymin, ymax = self.ax.get_ylim()
        self.ax2.set_ylim([ymin, ymax])
        new_labels = [
            round(float(self.float_outputs["equivalent_carbon_budget_consumed_share"]), 1),
            round(self.parameters["aviation_equivalentcarbonbudget_allocated_share"], 1),
        ]
        self.ax2.set_yticks([y1[0], float(y1[1])])
        self.ax2.set_yticklabels(new_labels)

        self.fig.canvas.draw()


class BiomassResourceBudgetAssessmentPlot:
    def __init__(self, data):
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
        aviation_available_biomass = float(self.float_outputs["aviation_available_biomass"])
        biomass_consumption_end_year = float(self.float_outputs["biomass_consumption_end_year"])
        available_biomass_total = float(self.float_outputs["available_biomass_total"])
        aviation_biomass_allocated_share = float(
            self.parameters["aviation_biomass_allocated_share"]
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
            Line2D(
                [0],
                [0],
                color=color,
                lw=6,
                label="Biomass consumption of aviation in 2050",
            ),
            Line2D(
                [0],
                [0],
                color="grey",
                lw=6,
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

        aviation_available_biomass = float(self.float_outputs["aviation_available_biomass"])
        biomass_consumption_end_year = float(self.float_outputs["biomass_consumption_end_year"])
        available_biomass_total = float(self.float_outputs["available_biomass_total"])
        aviation_biomass_allocated_share = float(
            self.parameters["aviation_biomass_allocated_share"]
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
            Line2D(
                [0],
                [0],
                color=color,
                lw=6,
                label="Biomass consumption of aviation in 2050",
            ),
            Line2D(
                [0],
                [0],
                color="grey",
                lw=6,
                label="Biomass resources allocated to aviation",
            ),
        ]

        self.ax.legend(handles=legend_elements, loc="center", bbox_to_anchor=[0.5, -0.12])

        self.fig.canvas.draw()


class ElectricityResourceBudgetAssessmentPlot:
    def __init__(self, data):
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
        aviation_available_electricity = float(self.float_outputs["aviation_available_electricity"])
        electricity_consumption_end_year = float(
            self.float_outputs["electricity_consumption_end_year"]
        )
        available_electricity = float(self.parameters["available_electricity"])
        aviation_electricity_allocated_share = float(
            self.parameters["aviation_electricity_allocated_share"]
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
            Line2D(
                [0],
                [0],
                color=color,
                lw=6,
                label="Electricity consumption of aviation in 2050",
            ),
            Line2D(
                [0],
                [0],
                color="grey",
                lw=6,
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

        aviation_available_electricity = float(self.float_outputs["aviation_available_electricity"])
        electricity_consumption_end_year = float(
            self.float_outputs["electricity_consumption_end_year"]
        )
        available_electricity = float(self.parameters["available_electricity"])
        aviation_electricity_allocated_share = float(
            self.parameters["aviation_electricity_allocated_share"]
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
            Line2D(
                [0],
                [0],
                color=color,
                lw=6,
                label="Electricity consumption of aviation in 2050",
            ),
            Line2D(
                [0],
                [0],
                color="grey",
                lw=6,
                label="Electricity resources allocated to aviation",
            ),
        ]

        self.ax.legend(handles=legend_elements, loc="center", bbox_to_anchor=[0.5, -0.12])

        self.fig.canvas.draw()


class MultidisciplinaryAssessmentPlot:
    def __init__(self, data):
        self.parameters = data["float_inputs"]
        self.df = data["vector_outputs"]
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

        # Biomass
        available_biomass_total = self.float_outputs["available_biomass_total"]
        aviation_available_biomass = self.float_outputs["aviation_available_biomass"]
        biomass_consumption_end_year = self.float_outputs["biomass_consumption_end_year"]

        # Electricity
        available_electricity_total = self.parameters["available_electricity"]
        aviation_available_electricity = self.float_outputs["aviation_available_electricity"]
        electricity_consumption_end_year = self.float_outputs["electricity_consumption_end_year"]

        # Effective radiative forcing
        equivalent_gross_carbon_budget = float(
            self.float_outputs["equivalent_gross_carbon_budget_2050"]
        )
        aviation_equivalent_carbon_budget = float(
            self.float_outputs["aviation_equivalent_carbon_budget"]
        )
        cumulative_total_equivalent_emissions = float(
            self.df.loc[2050, "cumulative_total_equivalent_emissions"]
        )

        categories = [
            "Climate\n(Total)",
            "Climate\n(CO2)",
            "Biomass",
            "Electricity",
        ]

        budgets = [
            aviation_equivalent_carbon_budget / equivalent_gross_carbon_budget * 100,
            aviation_carbon_budget / gross_carbon_budget * 100,
            aviation_available_biomass / available_biomass_total * 100,
            aviation_available_electricity / available_electricity_total * 100,
        ]

        consumptions = [
            np.max(
                [cumulative_total_equivalent_emissions / equivalent_gross_carbon_budget * 100, 0]
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
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.ax.clear()

        gross_carbon_budget = float(self.float_outputs["gross_carbon_budget_2050"])
        aviation_carbon_budget = float(self.float_outputs["aviation_carbon_budget"])
        cumulative_co2_emissions = float(self.df.loc[2050, "cumulative_co2_emissions"])

        # Biomass
        available_biomass_total = self.float_outputs["available_biomass_total"]
        aviation_available_biomass = self.float_outputs["aviation_available_biomass"]
        biomass_consumption_end_year = self.float_outputs["biomass_consumption_end_year"]

        # Electricity
        available_electricity_total = self.parameters["available_electricity"]
        aviation_available_electricity = self.float_outputs["aviation_available_electricity"]
        electricity_consumption_end_year = self.float_outputs["electricity_consumption_end_year"]

        # Effective radiative forcing
        equivalent_gross_carbon_budget = float(
            self.float_outputs["equivalent_gross_carbon_budget_2050"]
        )
        aviation_equivalent_carbon_budget = float(
            self.float_outputs["aviation_equivalent_carbon_budget"]
        )
        cumulative_total_equivalent_emissions = float(
            self.df.loc[2050, "cumulative_total_equivalent_emissions"]
        )

        categories = [
            "Climate\n(Total)",
            "Climate\n(CO2)",
            "Biomass",
            "Electricity",
        ]

        budgets = [
            aviation_equivalent_carbon_budget / equivalent_gross_carbon_budget * 100,
            aviation_carbon_budget / gross_carbon_budget * 100,
            aviation_available_biomass / available_biomass_total * 100,
            aviation_available_electricity / available_electricity_total * 100,
        ]

        consumptions = [
            np.max(
                [cumulative_total_equivalent_emissions / equivalent_gross_carbon_budget * 100, 0]
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

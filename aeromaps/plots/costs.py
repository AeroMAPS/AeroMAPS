# @Time : 15/06/2023 09:06
# @Author : a.salgas
# @File : costs.py
# @Software: PyCharm
import warnings

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

from .constants import plot_3_x, plot_3_y


class ScenarioEnergyCapitalPlot:
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
        # mine
        colors = [
            "#ee9b00",
            "#ffbf47",
            "#bb3e03",
            "#0c9e30",
            "#097223",
            "#828782",
            "#52F752",
            "#0ABAFF",
            "#8CAAB6",
            "#0ABAFF",
            "#8CAAB6",
            "#87AE87",
        ]

        self.annual_energy_invest = self.ax.stackplot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "plant_building_cost_hefa_fog"].fillna(0),
            self.df.loc[self.prospective_years, "plant_building_cost_hefa_others"].fillna(0),
            self.df.loc[self.prospective_years, "plant_building_cost_atj"].fillna(0),
            self.df.loc[self.prospective_years, "plant_building_cost_ft_others"].fillna(0),
            self.df.loc[self.prospective_years, "plant_building_cost_ft_msw"].fillna(0),
            self.df.loc[self.prospective_years, "electrofuel_plant_building_cost"].fillna(0),
            self.df.loc[self.prospective_years, "electrolysis_plant_building_cost"].fillna(0),
            self.df.loc[self.prospective_years, "gas_ccs_plant_building_cost"].fillna(0),
            self.df.loc[self.prospective_years, "gas_plant_building_cost"].fillna(0),
            self.df.loc[self.prospective_years, "coal_ccs_plant_building_cost"].fillna(0),
            self.df.loc[self.prospective_years, "coal_plant_building_cost"].fillna(0),
            self.df.loc[self.prospective_years, "liquefaction_plant_building_cost"].fillna(0),
            colors=colors,
            lw=0.5,
            edgecolor="black",
        )

        self.ax.grid(axis="y")
        self.ax.set_title("Annual investment per pathway (w/o fossil)")
        self.ax.set_xlabel("Year")
        self.ax.set_xlim(2020, max(self.prospective_years) - 1)
        self.ax.set_ylabel("Annual Capital Investment [M€]")
        # self.ax = plt.gca()

        legend = self.ax.legend(
            [
                "Bio - HEFA FOG",
                "Bio - HEFA Others",
                "Bio - Alcohol to Jet",
                "Bio - FT Others",
                "Bio - FT Municipal Waste",
                "Electrofuel",
                "$H_2$ - Electrolysis",
                "$H_2$ - Gas + CCS",
                "$H_2$ - Gas",
                "$H_2$ - Coal + CCS",
                "$H_2$ - Coal",
                "(L-)$H_2$ (Liquefaction)",
            ],
            loc="upper left",
            prop={"size": 7},
        )

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, data):
        self.df = data["vector_outputs"]
        self.ax.clear()

        colors = [
            "#ee9b00",
            "#ffbf47",
            "#bb3e03",
            "#0c9e30",
            "#097223",
            "#828782",
            "#52F752",
            "#0ABAFF",
            "#8CAAB6",
            "#0ABAFF",
            "#8CAAB6",
            "#87AE87",
        ]

        self.annual_energy_invest = self.ax.stackplot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "plant_building_cost_hefa_fog"].fillna(0),
            self.df.loc[self.prospective_years, "plant_building_cost_hefa_others"].fillna(0),
            self.df.loc[self.prospective_years, "plant_building_cost_atj"].fillna(0),
            self.df.loc[self.prospective_years, "plant_building_cost_ft_others"].fillna(0),
            self.df.loc[self.prospective_years, "plant_building_cost_ft_msw"].fillna(0),
            self.df.loc[self.prospective_years, "electrofuel_plant_building_cost"].fillna(0),
            self.df.loc[self.prospective_years, "electrolysis_plant_building_cost"].fillna(0),
            self.df.loc[self.prospective_years, "gas_ccs_plant_building_cost"].fillna(0),
            self.df.loc[self.prospective_years, "gas_plant_building_cost"].fillna(0),
            self.df.loc[self.prospective_years, "coal_ccs_plant_building_cost"].fillna(0),
            self.df.loc[self.prospective_years, "coal_plant_building_cost"].fillna(0),
            self.df.loc[self.prospective_years, "liquefaction_plant_building_cost"].fillna(0),
            colors=colors,
            lw=0.5,
            edgecolor="black",
        )

        self.ax.grid(axis="y")
        self.ax.set_title("Annual investment per pathway (w/o fossil)")
        self.ax.set_xlabel("Year")
        self.ax.set_xlim(2020, max(self.prospective_years) - 1)
        self.ax.set_ylabel("Annual Capital Investment [M€]")

        legend = self.ax.legend(
            [
                "Bio - HEFA FOG",
                "Bio - HEFA Others",
                "Bio - Alcohol to Jet",
                "Bio - FT Others",
                "Bio - FT Municipal Waste",
                "Electrofuel",
                "$H_2$ - Electrolysis",
                "$H_2$ - Gas + CCS",
                "$H_2$ - Gas",
                "$H_2$ - Coal + CCS",
                "$H_2$ - Coal",
                "(L-)$H_2$ (Liquefaction)",
            ],
            loc="upper left",
            prop={"size": 7},
        )

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class ScenarioEnergyExpensesPlot:
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
        # mine
        colors = [
            "#2A3438",
            "#2A3438",
            "#ee9b00",
            "#ee9b00",
            "#ffbf47",
            "#ffbf47",
            "#bb3e03",
            "#bb3e03",
            "#0c9e30",
            "#0c9e30",
            "#097223",
            "#097223",
            "#828782",
            "#828782",
            "#52F752",
            "#52F752",
            "#0ABAFF",
            "#0ABAFF",
            "#8CAAB6",
            "#8CAAB6",
            "#0ABAFF",
            "#0ABAFF",
            "#8CAAB6",
            "#8CAAB6",
            "#87AE87",
        ]

        self.annual_energy_expenses = self.ax.stackplot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "kerosene_cost"].fillna(0),
            self.df.loc[self.prospective_years, "kerosene_carbon_tax_cost"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_cost_hefa_fog"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_fog"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_cost_hefa_others"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_others"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_cost_atj"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_carbon_tax_atj"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_cost_ft_others"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_others"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_cost_ft_msw"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_msw"].fillna(0),
            self.df.loc[self.prospective_years, "electrofuel_total_cost"].fillna(0),
            self.df.loc[self.prospective_years, "electrofuel_carbon_tax"].fillna(0),
            self.df.loc[self.prospective_years, "electrolysis_h2_total_cost"].fillna(0),
            self.df.loc[self.prospective_years, "electrolysis_h2_carbon_tax"].fillna(0),
            self.df.loc[self.prospective_years, "gas_ccs_h2_total_cost"].fillna(0),
            self.df.loc[self.prospective_years, "gas_ccs_h2_carbon_tax"].fillna(0),
            self.df.loc[self.prospective_years, "gas_h2_total_cost"].fillna(0),
            self.df.loc[self.prospective_years, "gas_h2_carbon_tax"].fillna(0),
            self.df.loc[self.prospective_years, "coal_ccs_h2_total_cost"].fillna(0),
            self.df.loc[self.prospective_years, "coal_ccs_h2_carbon_tax"].fillna(0),
            self.df.loc[self.prospective_years, "coal_h2_total_cost"].fillna(0),
            self.df.loc[self.prospective_years, "coal_h2_carbon_tax"].fillna(0),
            self.df.loc[self.prospective_years, "liquefaction_h2_total_cost"].fillna(0)
            + self.df.loc[self.prospective_years, "transport_h2_total_cost"].fillna(0),
            colors=colors,
            lw=0.5,
            edgecolor="black",
        )

        self.ax.grid(axis="y")
        self.ax.set_title("Annual energy expenses per pathway")
        self.ax.set_ylabel("Energy expenses [M€]")

        primary_legend_entries = [
            "Fossil Kerosene",
            "_nolegend_",
            "Bio - HEFA FOG",
            "_nolegend_",
            "Bio - HEFA Others",
            "_nolegend_",
            "Bio - Alcohol to Jet",
            "_nolegend_",
            "Bio - FT Others",
            "_nolegend_",
            "Bio - FT MSW",
            "_nolegend_",
            "Electrofuel",
            "_nolegend_",
            "Electrolysis $H_2$ ",
            "_nolegend_",
            "Gas CCS $H_2$ ",
            "_nolegend_",
            "Gas $H_2$ ",
            "_nolegend_",
            "Coal CCS $H_2$ ",
            "_nolegend_",
            "Coal $H_2$ ",
            "_nolegend_",
            "$H_2$ liq. & transport",
        ]

        stacks = self.annual_energy_expenses

        hatches = [
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
        ]
        for stack, hatch in zip(stacks, hatches):
            stack.set_hatch(hatch)

        self.ax.set_xlim(2020, 2050)

        # TODO : correct warnings
        warnings.filterwarnings("ignore")

        primary_legend = self.ax.legend(primary_legend_entries, loc="upper left", prop={"size": 7})
        self.ax.add_artist(primary_legend)

        warnings.resetwarnings()
        warnings.simplefilter("ignore", DeprecationWarning)

        # Create hatch legend manually
        hatch_patch = mpatches.Patch(facecolor="white", hatch="||", edgecolor="black")
        self.ax.legend(
            handles=[hatch_patch], labels=["Carbon Tax"], loc="upper right", prop={"size": 7}
        )

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):

        self.df = df_data["vector_outputs"]

        self.ax.clear()

        colors = [
            "#2A3438",
            "#2A3438",
            "#ee9b00",
            "#ee9b00",
            "#ffbf47",
            "#ffbf47",
            "#bb3e03",
            "#bb3e03",
            "#0c9e30",
            "#0c9e30",
            "#097223",
            "#097223",
            "#828782",
            "#828782",
            "#52F752",
            "#52F752",
            "#0ABAFF",
            "#0ABAFF",
            "#8CAAB6",
            "#8CAAB6",
            "#0ABAFF",
            "#0ABAFF",
            "#8CAAB6",
            "#8CAAB6",
            "#87AE87",
        ]

        self.annual_energy_expenses = self.ax.stackplot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "kerosene_cost"].fillna(0),
            self.df.loc[self.prospective_years, "kerosene_carbon_tax_cost"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_cost_hefa_fog"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_fog"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_cost_hefa_others"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_others"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_cost_atj"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_carbon_tax_atj"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_cost_ft_others"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_others"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_cost_ft_msw"].fillna(0),
            self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_msw"].fillna(0),
            self.df.loc[self.prospective_years, "electrofuel_total_cost"].fillna(0),
            self.df.loc[self.prospective_years, "electrofuel_carbon_tax"].fillna(0),
            self.df.loc[self.prospective_years, "electrolysis_h2_total_cost"].fillna(0),
            self.df.loc[self.prospective_years, "electrolysis_h2_carbon_tax"].fillna(0),
            self.df.loc[self.prospective_years, "gas_ccs_h2_total_cost"].fillna(0),
            self.df.loc[self.prospective_years, "gas_ccs_h2_carbon_tax"].fillna(0),
            self.df.loc[self.prospective_years, "gas_h2_total_cost"].fillna(0),
            self.df.loc[self.prospective_years, "gas_h2_carbon_tax"].fillna(0),
            self.df.loc[self.prospective_years, "coal_ccs_h2_total_cost"].fillna(0),
            self.df.loc[self.prospective_years, "coal_ccs_h2_carbon_tax"].fillna(0),
            self.df.loc[self.prospective_years, "coal_h2_total_cost"].fillna(0),
            self.df.loc[self.prospective_years, "coal_h2_carbon_tax"].fillna(0),
            self.df.loc[self.prospective_years, "liquefaction_h2_total_cost"].fillna(0)
            + self.df.loc[self.prospective_years, "transport_h2_total_cost"].fillna(0),
            colors=colors,
            lw=0.5,
            edgecolor="black",
        )

        self.ax.grid(axis="y")
        self.ax.set_title("Annual energy expenses per pathway")
        self.ax.set_ylabel("Energy expenses [M€]")

        primary_legend_entries = [
            "Fossil Kerosene",
            "_nolegend_",
            "Bio - HEFA FOG",
            "_nolegend_",
            "Bio - HEFA Others",
            "_nolegend_",
            "Bio - Alcohol to Jet",
            "_nolegend_",
            "Bio - FT Others",
            "_nolegend_",
            "Bio - FT MSW",
            "_nolegend_",
            "Electrofuel",
            "_nolegend_",
            "Electrolysis $H_2$ ",
            "_nolegend_",
            "Gas CCS $H_2$ ",
            "_nolegend_",
            "Gas $H_2$ ",
            "_nolegend_",
            "Coal CCS $H_2$ ",
            "_nolegend_",
            "Coal $H_2$ ",
            "_nolegend_",
            "$H_2$ liq. & transport",
        ]

        stacks = self.annual_energy_expenses

        hatches = [
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
            "||",
            "",
        ]
        for stack, hatch in zip(stacks, hatches):
            stack.set_hatch(hatch)

        self.ax.set_xlim(2020, 2050)

        warnings.filterwarnings("ignore")

        primary_legend = self.ax.legend(primary_legend_entries, loc="upper left", prop={"size": 7})
        self.ax.add_artist(primary_legend)

        warnings.resetwarnings()

        # Create hatch legend manually
        hatch_patch = mpatches.Patch(facecolor="white", hatch="||", edgecolor="black")
        self.ax.legend(
            handles=[hatch_patch], labels=["Carbon Tax"], loc="upper right", prop={"size": 7}
        )

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class ScenarioEnergyCarbonTaxPlot:
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
        (self.line_energy_expenses,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "non_discounted_energy_expenses"],
            label="Scenario energy expenses",
            linestyle="-",
            color="#0c9e30",
        )

        (self.line_energy_expenses_carb_tax,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "non_discounted_energy_expenses"]
                + self.df.loc[self.prospective_years, "kerosene_carbon_tax_cost"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_fog"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_others"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_atj"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_others"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_msw"]
                + self.df.loc[self.prospective_years, "electrolysis_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "gas_ccs_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "gas_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "coal_ccs_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "coal_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "electrofuel_carbon_tax"]
            ),
            label="Scenario energy expenses incl. carbon tax",
            linestyle="--",
            color="#0c9e30",
        )
        (self.line_bau_energy_expenses,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "non_discounted_BAU_energy_expenses"],
            label="Business as usual energy expenses",
            linestyle="-",
            color="#2A3438",
        )
        (self.line_bau_energy_expenses_carbon_tax,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "non_discounted_BAU_energy_expenses"]
                + self.df.loc[self.prospective_years, "kerosene_carbon_tax_BAU"]
            ),
            label="Business as usual energy expenses incl. carbon tax",
            linestyle="--",
            color="#2A3438",
        )

        self.ax.grid(axis="y")
        self.ax.legend(loc="upper left")
        self.ax.set_title("Annual energy expenses per pathway")
        self.ax.set_ylabel("Energy expenses [M€]")
        self.ax = plt.gca()

        self.ax.set_xlim(2020, 2050)
        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        self.df = df_data["vector_outputs"]

        self.line_energy_expenses.set_ydata(
            self.df.loc[self.prospective_years, "non_discounted_energy_expenses"]
        )

        self.line_energy_expenses_carb_tax.set_ydata(
            (
                self.df.loc[self.prospective_years, "non_discounted_energy_expenses"]
                + self.df.loc[self.prospective_years, "kerosene_carbon_tax_cost"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_fog"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_others"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_atj"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_others"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_msw"]
                + self.df.loc[self.prospective_years, "electrolysis_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "gas_ccs_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "gas_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "coal_ccs_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "coal_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "electrofuel_carbon_tax"]
            )
        )

        self.line_bau_energy_expenses.set_ydata(
            self.df.loc[self.prospective_years, "non_discounted_BAU_energy_expenses"]
        )

        self.line_bau_energy_expenses_carbon_tax.set_ydata(
            (
                self.df.loc[self.prospective_years, "non_discounted_BAU_energy_expenses"]
                + self.df.loc[self.prospective_years, "kerosene_carbon_tax_BAU"]
            )
        )

        for collection in self.ax.collections:
            collection.remove()
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class ScenarioEnergyUnitCostPlot:
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
        (self.line_kerosene_price,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "kerosene_market_price"] / 35.3,
            color="#2A3438",
            linestyle="-",
            label="Fossil Kerosene",
            linewidth=2,
        )

        (self.line_biofuel_hefa_fog_mfsp,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "biofuel_hefa_fog_mfsp"] / 35.3,
            color="#097223",
            linestyle="-",
            label="Bio - HEFA FOG",
            linewidth=2,
        )

        (self.line_biofuel_hefa_others_mfsp,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "biofuel_hefa_others_mfsp"] / 35.3,
            color="#097223",
            linestyle=":",
            label="Bio - HEFA Others",
            linewidth=2,
        )

        (self.line_biofuel_atj_mfsp,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "biofuel_atj_mfsp"] / 35.3,
            color="#097223",
            linestyle="--",
            label="Bio - Alcohol to Jet",
            linewidth=2,
        )
        (self.line_biofuel_ft_others_mfsp,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "biofuel_ft_others_mfsp"] / 35.3,
            color="#097223",
            linestyle="-.",
            label="Bio - FT Others",
            linewidth=2,
        )

        (self.line_biofuel_ft_msw_mfsp,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "biofuel_ft_msw_mfsp"] / 35.3,
            color="#097223",
            linestyle=(0, (5, 10)),
            label="Bio - FT MSW",
            linewidth=2,
        )

        (self.line_electrofuel_mfsp,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "electrofuel_avg_cost_per_l"] / 35.3,
            color="#828782",
            linestyle="-",
            label="Electrofuel",
            linewidth=2,
        )

        (self.line_hydrogen_electrolysis_mfsp,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_electrolysis"] / 119.93,
            color="#0075A3",
            linestyle="-",
            label="Hydrogen - Electrolysis",
            linewidth=2,
        )

        (self.line_hydrogen_gas_ccs_mfsp,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_gas_ccs"] / 119.93,
            color="#0075A3",
            linestyle=":",
            label="Hydrogen - Gas CSS",
            linewidth=2,
        )

        (self.line_hydrogen_gas_mfsp,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_gas"] / 119.93,
            color="#0075A3",
            linestyle="--",
            label="Hydrogen - Gas",
            linewidth=2,
        )

        (self.line_hydrogen_coal_ccs_mfsp,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_coal_ccs"] / 119.93,
            color="#0075A3",
            linestyle="-.",
            label="Hydrogen - Coal CCS",
            linewidth=2,
        )

        (self.line_hydrogen_coal_mfsp,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_coal"] / 119.93,
            color="#0075A3",
            linestyle=(0, (5, 10)),
            label="Hydrogen Coal",
            linewidth=2,
        )

        self.ax.grid(axis="y")
        self.ax.set_title("MFSP per pathway (kerosene: market price)")
        self.ax.set_ylabel("MFSP [€/MJ]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2020, 2050)
        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        self.df = df_data["vector_outputs"]

        self.line_kerosene_price.set_ydata(
            (self.df.loc[self.prospective_years, "kerosene_market_price"]) / 35.3,
        )
        self.line_biofuel_hefa_fog_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "biofuel_hefa_fog_mfsp"]) / 35.3,
        )
        self.line_biofuel_hefa_others_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "biofuel_hefa_others_mfsp"]) / 35.3,
        )
        self.line_biofuel_atj_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "biofuel_atj_mfsp"]) / 35.3,
        )
        self.line_biofuel_ft_others_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "biofuel_ft_others_mfsp"]) / 35.3,
        )
        self.line_biofuel_ft_msw_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "biofuel_ft_msw_mfsp"]) / 35.3,
        )
        self.line_electrofuel_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "electrofuel_avg_cost_per_l"]) / 35.3,
        )
        self.line_hydrogen_electrolysis_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_electrolysis"]) / 119.93,
        )
        self.line_hydrogen_gas_ccs_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_gas_ccs"]) / 119.93,
        )
        self.line_hydrogen_gas_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_gas"]) / 119.93,
        )
        self.line_hydrogen_coal_ccs_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_coal_ccs"]) / 119.93,
        )
        self.line_hydrogen_coal_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_coal"]) / 119.93,
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class ScenarioEnergyUnitCostWithCarbonTaxPlot:
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
        ## With carbon tax

        (self.line_kerosene_price,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "kerosene_market_price"]
                + self.df.loc[self.prospective_years, "kerosene_price_supplement_carbon_tax"]
            )
            / 35.3,
            color="#2A3438",
            linestyle="-",
            label="Fossil Kerosene",
            linewidth=2,
        )

        (self.line_biofuel_hefa_fog_mfsp,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "biofuel_hefa_fog_mfsp"]
                + self.df.loc[self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_hefa_fog"]
            )
            / 35.3,
            color="#097223",
            linestyle="-",
            label="Bio - HEFA FOG",
            linewidth=2,
        )

        (self.line_biofuel_hefa_others_mfsp,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "biofuel_hefa_others_mfsp"]
                + self.df.loc[
                    self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_hefa_others"
                ]
            )
            / 35.3,
            color="#097223",
            linestyle=":",
            label="Bio - HEFA Others",
            linewidth=2,
        )

        (self.line_biofuel_atj_mfsp,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "biofuel_atj_mfsp"]
                + self.df.loc[self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_atj"]
            )
            / 35.3,
            color="#097223",
            linestyle="--",
            label="Bio - Alcohol to Jet",
            linewidth=2,
        )
        (self.line_biofuel_ft_others_mfsp,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "biofuel_ft_others_mfsp"]
                + self.df.loc[
                    self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_ft_others"
                ]
            )
            / 35.3,
            color="#097223",
            linestyle="-.",
            label="Bio - FT Others",
            linewidth=2,
        )

        (self.line_biofuel_ft_msw_mfsp,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "biofuel_ft_msw_mfsp"]
                + self.df.loc[self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_ft_msw"]
            )
            / 35.3,
            color="#097223",
            linestyle=(0, (5, 10)),
            label="Bio - FT MSW",
            linewidth=2,
        )

        (self.line_electrofuel_mfsp,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "electrofuel_avg_cost_per_l"]
                + self.df.loc[self.prospective_years, "electrofuel_mfsp_carbon_tax_supplement"]
            )
            / 35.3,
            color="#828782",
            linestyle="-",
            label="Electrofuel",
            linewidth=2,
        )

        (self.line_hydrogen_electrolysis_mfsp,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_electrolysis"]
                + self.df.loc[self.prospective_years, "electrolysis_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
            color="#0075A3",
            linestyle="-",
            label="Hydrogen - Electrolysis",
            linewidth=2,
        )

        (self.line_hydrogen_gas_ccs_mfsp,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_gas_ccs"]
                + self.df.loc[self.prospective_years, "gas_ccs_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
            color="#0075A3",
            linestyle=":",
            label="Hydrogen - Gas CSS",
            linewidth=2,
        )

        (self.line_hydrogen_gas_mfsp,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_gas"]
                + +self.df.loc[self.prospective_years, "gas_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
            color="#0075A3",
            linestyle="--",
            label="Hydrogen - Gas",
            linewidth=2,
        )

        (self.line_hydrogen_coal_ccs_mfsp,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_coal_ccs"]
                + self.df.loc[self.prospective_years, "coal_ccs_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
            color="#0075A3",
            linestyle="-.",
            label="Hydrogen - Coal CCS",
            linewidth=2,
        )

        (self.line_hydrogen_coal_mfsp,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_coal"]
                + self.df.loc[self.prospective_years, "coal_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
            color="#0075A3",
            linestyle=(0, (5, 10)),
            label="Hydrogen Coal",
            linewidth=2,
        )

        self.ax.grid(axis="y")
        self.ax.set_title("MFSP per pathway incl. carbon tax")
        self.ax.set_ylabel("MFSP [€/MJ]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2020, 2050)
        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        self.df = df_data["vector_outputs"]

        self.line_kerosene_price.set_ydata(
            (
                self.df.loc[self.prospective_years, "kerosene_market_price"]
                + self.df.loc[self.prospective_years, "kerosene_price_supplement_carbon_tax"]
            )
            / 35.3,
        )
        self.line_biofuel_hefa_fog_mfsp.set_ydata(
            (
                self.df.loc[self.prospective_years, "biofuel_hefa_fog_mfsp"]
                + self.df.loc[self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_hefa_fog"]
            )
            / 35.3,
        )
        self.line_biofuel_hefa_others_mfsp.set_ydata(
            (
                self.df.loc[self.prospective_years, "biofuel_hefa_others_mfsp"]
                + self.df.loc[
                    self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_hefa_others"
                ]
            )
            / 35.3,
        )
        self.line_biofuel_atj_mfsp.set_ydata(
            (
                self.df.loc[self.prospective_years, "biofuel_atj_mfsp"]
                + self.df.loc[self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_atj"]
            )
            / 35.3,
        )
        self.line_biofuel_ft_others_mfsp.set_ydata(
            (
                self.df.loc[self.prospective_years, "biofuel_ft_others_mfsp"]
                + self.df.loc[
                    self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_ft_others"
                ]
            )
            / 35.3,
        )
        self.line_biofuel_ft_msw_mfsp.set_ydata(
            (
                self.df.loc[self.prospective_years, "biofuel_ft_msw_mfsp"]
                + self.df.loc[self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_ft_msw"]
            )
            / 35.3,
        )
        self.line_electrofuel_mfsp.set_ydata(
            (
                self.df.loc[self.prospective_years, "electrofuel_avg_cost_per_l"]
                + self.df.loc[self.prospective_years, "electrofuel_mfsp_carbon_tax_supplement"]
            )
            / 35.3,
        )
        self.line_hydrogen_electrolysis_mfsp.set_ydata(
            (
                self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_electrolysis"]
                + self.df.loc[self.prospective_years, "electrolysis_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
        )
        self.line_hydrogen_gas_ccs_mfsp.set_ydata(
            (
                self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_gas_ccs"]
                + self.df.loc[self.prospective_years, "gas_ccs_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
        )
        self.line_hydrogen_gas_mfsp.set_ydata(
            (
                self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_gas"]
                + self.df.loc[self.prospective_years, "gas_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
        )
        self.line_hydrogen_coal_ccs_mfsp.set_ydata(
            (
                self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_coal_ccs"]
                + self.df.loc[self.prospective_years, "coal_ccs_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
        )
        self.line_hydrogen_coal_mfsp.set_ydata(
            (
                self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_coal"]
                + self.df.loc[self.prospective_years, "coal_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DiscountEffect:
    def __init__(self, data):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.float_inputs = data["float_inputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_3_x, plot_3_y),
        )
        self.create_plot()

    def create_plot(self):
        (self.line_non_discounted,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "non_discounted_energy_expenses"],
            color="#2A3438",
            linestyle="-",
            label="Non-discounted expenses",
            linewidth=2,
        )

        (self.line_discounted,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "discounted_energy_expenses"],
            color="red",
            linestyle="-",
            label="Discounted expenses at r={}%".format(self.float_inputs["social_discount_rate"]),
            linewidth=2,
        )

        self.ax.grid(axis="y")
        self.ax.set_title("Total (energy) expenses (M€)")
        self.ax.set_ylabel("M€ / year")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2020, 2050)
        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        self.df = df_data["vector_outputs"]

        self.line_non_discounted.set_ydata(
            self.df.loc[self.prospective_years, "non_discounted_energy_expenses"]
        )

        self.line_discounted.set_ydata(
            self.df.loc[self.prospective_years, "discounted_energy_expenses"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DropInMACC:
    # TODO do the same for LH2?
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
        # Select year at which the MACC is plotted
        year = 2050

        # create a dataframe for the various pathways
        # (usage: sorting the values by increasing carbon abatement cost)

        pathways = [
            "Bio - HEFA FOG",
            "Bio - HEFA Others",
            "Bio - Alcohol to Jet",
            "Bio - FT MSW",
            "Bio - FT Others",
            "Electrofuel",
        ]

        # Abatement potential in MtCO2e
        abatement_potential = [
            elt / 1000000
            for elt in [
                self.df.abatement_potential_hefa_fog[year],
                self.df.abatement_potential_hefa_others[year],
                self.df.abatement_potential_atj[year],
                self.df.abatement_potential_ft_msw[year],
                self.df.abatement_potential_ft_others[year],
                self.df.abatement_potential_electrofuel[year],
            ]
        ]

        # Energy available in EJ
        energy_avail = [
            elt / 1000000000000
            for elt in [
                self.df.energy_avail_hefa_fog[year],
                self.df.energy_avail_hefa_others[year],
                self.df.energy_avail_atj[year],
                self.df.energy_avail_ft_msw[year],
                self.df.energy_avail_ft_others[year],
                self.df.energy_avail_electrofuel[year],
            ]
        ]

        # carbon abatement cost in (€/tCO2e)
        carbon_abatement_cost = [
            self.df.carbon_abatement_cost_hefa_fog[year],
            self.df.carbon_abatement_cost_hefa_others[year],
            self.df.carbon_abatement_cost_atj[year],
            self.df.carbon_abatement_cost_ft_msw[year],
            self.df.carbon_abatement_cost_ft_others[year],
            self.df.carbon_abatement_cost_electrofuel[year],
        ]

        colors = ["#ee9b00", "#ffbf47", "#bb3e03", "#097223", "#0c9e30", "#828782"]

        macc_df = pd.DataFrame(
            data=[abatement_potential, energy_avail, carbon_abatement_cost, colors],
            columns=pathways,
            index=["abatement_potential", "energy_avail", "carbon_abatement_cost", "colors"],
        )

        macc_df = macc_df.transpose().sort_values(by="carbon_abatement_cost")

        macc_df = macc_df[macc_df["abatement_potential"] > 0]

        heights = macc_df["carbon_abatement_cost"].to_list()
        names = macc_df.index.to_list()
        heights.insert(0, 0)
        heights.append(heights[-1])

        # MAx potential MACC
        widths_potential = macc_df["abatement_potential"].to_list()
        widths_potential.insert(0, 0)
        widths_potential.append(widths_potential[-1])

        colors = macc_df["colors"].to_list()

        self.macc_curve = self.ax.step(
            np.cumsum(widths_potential) - widths_potential,
            heights,
            where="post",
            color="#335C67",
            label="Marginal abatement cost",
            linewidth=1.5,
        )

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_potential) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [
                    (np.cumsum(widths_potential)[i], 0),
                    (np.cumsum(widths_potential)[i], heights[i + 1]),
                    (np.cumsum(widths_potential)[i + 1], heights[i + 1]),
                    (np.cumsum(widths_potential)[i + 1], 0),
                ],
                closed=True,
                color=colors[i],
                alpha=0.5,
            )
            self.ax.add_patch(polygon)

        fuel = macc_df.energy_avail.to_list()
        fuel.insert(0, 0)
        widths_potential.pop()
        self.ax2 = self.ax.twinx()
        self.ax2.plot(
            np.cumsum(widths_potential),
            np.cumsum(fuel),
            color="#9E2A2B",
            linestyle=":",
            label="Energy potential",
            marker="x",
        )

        self.ax2.axhline(
            y=self.df.energy_consumption_dropin_fuel[year] / 1e12
            - self.df.energy_consumption_kerosene[year] / 1e12,
            color="black",
            linewidth=1,
            linestyle="-.",
        )
        self.ax2.text(
            0,
            1.02
            * (
                self.df.energy_consumption_dropin_fuel[year] / 1e12
                - self.df.energy_consumption_kerosene[year] / 1e12
            ),
            "Air transport sustainable drop-in fuels use, 2050",
        )

        self.ax2.axhline(
            y=self.df.energy_consumption_dropin_fuel[year] / 1e12,
            color="black",
            linewidth=1,
            linestyle="-",
        )
        self.ax2.text(
            0,
            1.02 * (self.df.energy_consumption_dropin_fuel[year] / 1e12),
            "Air transport total drop-in fuels use, 2050",
        )

        self.ax.grid(True, which="both", ls=":")
        self.ax.set_ylabel("Carbon Abatement Cost (€/t$\mathregular{CO_2}$)")
        self.ax2.set_ylabel("Energy potential under current allocation (EJ)")
        self.ax.set_xlabel("$\mathregular{CO_2}$ abatted (Mt)")

        for i in range(len(widths_potential) - 1):
            self.ax.text(np.cumsum(widths_potential)[i] + 10, heights[i + 1] - 50, names[i])

        self.ax.legend(
            fancybox=True,
            shadow=True,
            loc="lower left",
            bbox_to_anchor=[0.00, -0.2],
            prop={"size": 8},
        )
        self.ax2.legend(
            fancybox=True,
            shadow=True,
            loc="lower right",
            bbox_to_anchor=[1, -0.2],
            prop={"size": 8},
        )

        self.ax.set_title("Marginal abatement cost curve for drop-in fuels")

        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        self.df = df_data["vector_outputs"]
        self.float_outputs = df_data["float_outputs"]
        self.years = df_data["years"]["full_years"]
        self.historic_years = df_data["years"]["historic_years"]
        self.prospective_years = df_data["years"]["prospective_years"]

        self.ax.cla()
        self.ax2.cla()

        # Select year at which the MACC is plotted
        year = 2050

        # create a dataframe for the various pathways
        # (usage: sorting the values by increasing carbon abatement cost)

        pathways = [
            "Bio - HEFA FOG",
            "Bio - HEFA Others",
            "Bio - Alcohol to Jet",
            "Bio - FT MSW",
            "Bio - FT Others",
            "Electrofuel",
        ]

        # Abatement potential in MtCO2e
        abatement_potential = [
            elt / 1000000
            for elt in [
                self.df.abatement_potential_hefa_fog[year],
                self.df.abatement_potential_hefa_others[year],
                self.df.abatement_potential_atj[year],
                self.df.abatement_potential_ft_msw[year],
                self.df.abatement_potential_ft_others[year],
                self.df.abatement_potential_electrofuel[year],
            ]
        ]

        # Energy available in EJ
        energy_avail = [
            elt / 1000000000000
            for elt in [
                self.df.energy_avail_hefa_fog[year],
                self.df.energy_avail_hefa_others[year],
                self.df.energy_avail_atj[year],
                self.df.energy_avail_ft_msw[year],
                self.df.energy_avail_ft_others[year],
                self.df.energy_avail_electrofuel[year],
            ]
        ]

        # carbon abatement cost in (€/tCO2e)
        carbon_abatement_cost = [
            self.df.carbon_abatement_cost_hefa_fog[year],
            self.df.carbon_abatement_cost_hefa_others[year],
            self.df.carbon_abatement_cost_atj[year],
            self.df.carbon_abatement_cost_ft_msw[year],
            self.df.carbon_abatement_cost_ft_others[year],
            self.df.carbon_abatement_cost_electrofuel[year],
        ]

        colors = ["#ee9b00", "#ffbf47", "#bb3e03", "#097223", "#0c9e30", "#828782"]

        macc_df = pd.DataFrame(
            data=[abatement_potential, energy_avail, carbon_abatement_cost, colors],
            columns=pathways,
            index=["abatement_potential", "energy_avail", "carbon_abatement_cost", "colors"],
        )

        macc_df = macc_df.transpose().sort_values(by="carbon_abatement_cost")

        macc_df = macc_df[macc_df["abatement_potential"] > 0]

        heights = macc_df["carbon_abatement_cost"].to_list()
        names = macc_df.index.to_list()
        heights.insert(0, 0)
        heights.append(heights[-1])

        # MAx potential MACC
        widths_potential = macc_df["abatement_potential"].to_list()
        widths_potential.insert(0, 0)
        widths_potential.append(widths_potential[-1])

        colors = macc_df["colors"].to_list()

        self.macc_curve = self.ax.step(
            np.cumsum(widths_potential) - widths_potential,
            heights,
            where="post",
            color="#335C67",
            label="Marginal abatement cost",
            linewidth=1.5,
        )

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_potential) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [
                    (np.cumsum(widths_potential)[i], 0),
                    (np.cumsum(widths_potential)[i], heights[i + 1]),
                    (np.cumsum(widths_potential)[i + 1], heights[i + 1]),
                    (np.cumsum(widths_potential)[i + 1], 0),
                ],
                closed=True,
                color=colors[i],
                alpha=0.5,
            )
            self.ax.add_patch(polygon)

        fuel = macc_df.energy_avail.to_list()
        fuel.insert(0, 0)
        widths_potential.pop()

        self.ax2.plot(
            np.cumsum(widths_potential),
            np.cumsum(fuel),
            color="#9E2A2B",
            linestyle=":",
            label="Energy potential",
            marker="x",
        )

        self.ax2.axhline(
            y=self.df.energy_consumption_dropin_fuel[year] / 1e12
            - self.df.energy_consumption_kerosene[year] / 1e12,
            color="black",
            linewidth=1,
            linestyle="-.",
        )
        self.ax2.text(
            0,
            1.02
            * (
                self.df.energy_consumption_dropin_fuel[year] / 1e12
                - self.df.energy_consumption_kerosene[year] / 1e12
            ),
            "Air transport sustainable drop-in fuels use, 2050",
        )

        self.ax2.axhline(
            y=self.df.energy_consumption_dropin_fuel[year] / 1e12,
            color="black",
            linewidth=1,
            linestyle="-",
        )
        self.ax2.text(
            0,
            1.02 * (self.df.energy_consumption_dropin_fuel[year] / 1e12),
            "Air transport total drop-in fuels use, 2050",
        )

        self.ax.grid(True, which="both", ls=":")
        self.ax.set_ylabel("Carbon Abatement Cost (€/t$\mathregular{CO_2}$)")
        self.ax2.set_ylabel("Energy potential under current allocation (EJ)")
        self.ax.set_xlabel("$\mathregular{CO_2}$ abatted (Mt)")

        for i in range(len(widths_potential) - 1):
            self.ax.text(np.cumsum(widths_potential)[i] + 10, heights[i + 1] - 50, names[i])

        self.fig.tight_layout()
        self.fig.canvas.draw()


class DOCEvolutionBreakdown:
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
            self.prospective_years,
            np.zeros(len(self.prospective_years)),
            color="royalblue",
            linestyle="-",
            linewidth=1,
        )

        (self.line_total,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_mean"],
            color="blue",
            linestyle="-",
            label="Total DOC",
            linewidth=2,
        )

        (self.line_total_adjusted,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            color="blue",
            linestyle="--",
            label="Total DOC adjusted of offset",
            linewidth=2,
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            np.zeros(len(self.prospective_years)),
            color="royalblue",
            label="Non-energy",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            color="cornflowerblue",
            label="Energy",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            color="lightsteelblue",
            label="Carbon tax",
        )

        self.ax.grid()
        self.ax.set_title("Direct Operating Costs breakdown")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Direct Operating Costs [€/ASK]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])
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

        for collection in self.ax.collections:
            collection.remove()

        self.line_total.set_ydata(self.df.loc[self.prospective_years, "doc_total_per_ask_mean"])

        self.line_total_adjusted.set_ydata(
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            np.zeros(len(self.prospective_years)),
            color="royalblue",
            label="Non-energy",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            color="cornflowerblue",
            label="Energy",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            color="lightsteelblue",
            label="Carbon tax",
        )
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DOCEvolutionCategory:
    def __init__(self, data):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.float_inputs = data["float_inputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_3_x, plot_3_y),
        )
        self.create_plot()

    def create_plot(self):

        (self.line_srdi,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_short_range_dropin_fuel"],
            linestyle="-",
            label="Short range-D.in",
            linewidth=2,
        )

        (self.line_mrdi,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_medium_range_dropin_fuel"],
            linestyle="-",
            label="Medium range-D.in",
            linewidth=2,
        )

        (self.line_lrdi,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_long_range_dropin_fuel"],
            linestyle="-",
            label="Long range-D.in",
            linewidth=2,
        )

        (self.line_srh,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_short_range_hydrogen"],
            linestyle="-",
            label="Short range-H2",
            linewidth=2,
        )

        (self.line_mrh,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_medium_range_hydrogen"],
            linestyle="-",
            label="Medium range-H2",
            linewidth=2,
        )

        (self.line_lrh,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_long_range_hydrogen"],
            linestyle="-",
            label="Long range-H2",
            linewidth=2,
        )

        (self.line_tot,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_mean"],
            color="red",
            linestyle="-",
            label="Fleet average",
            linewidth=2,
        )

        self.ax.grid(axis="y")
        self.ax.set_title("Average direct operating cost by aircraft category")
        self.ax.set_ylabel("€ / ASK")
        self.ax = plt.gca()
        self.ax.legend(title="Direct Operating Cost")
        self.ax.set_xlim(2020, 2050)
        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):

        for collection in self.ax.collections:
            collection.remove()

        self.df = df_data["vector_outputs"]

        self.line_lrh.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_long_range_hydrogen"]
        )

        self.line_lrdi.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_long_range_dropin_fuel"]
        )

        self.line_mrh.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_medium_range_hydrogen"]
        )

        self.line_mrdi.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_medium_range_dropin_fuel"]
        )

        self.line_srh.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_short_range_hydrogen"]
        )

        self.line_srdi.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_short_range_dropin_fuel"]
        )

        self.line_tot.set_ydata(self.df.loc[self.prospective_years, "doc_total_per_ask_mean"])

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class AirfareEvolutionBreakdown:
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
            self.prospective_years,
            np.zeros(len(self.prospective_years)),
            color="royalblue",
            linestyle="-",
            linewidth=1,
        )

        (self.line_total_lowering_offset,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"],
            color="grey",
            linestyle="-",
            label="Total adjusted DOC & NOC",
            linewidth=2,
        )

        (self.line_doc_total,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_mean"],
            color="blue",
            linestyle="--",
            label="Total DOC without adjustment",
            linewidth=2,
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            np.zeros(len(self.prospective_years)),
            color="royalblue",
            label="Non-energy",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            color="cornflowerblue",
            label="Energy",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            color="lightsteelblue",
            label="Carbon tax adjusted of offset",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            color="silver",
            label="Carbon offset",
        )

        self.ax.grid()
        self.ax.set_title("Direct and Non Operating Costs breakdown")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Direct and Non Operating Costs [€/ASK]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])
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

        for collection in self.ax.collections:
            collection.remove()

        self.line_total_lowering_offset.set_ydata(
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
        )

        self.line_doc_total.set_ydata(self.df.loc[self.prospective_years, "doc_total_per_ask_mean"])

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            np.zeros(len(self.prospective_years)),
            color="royalblue",
            label="Non-energy",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            color="cornflowerblue",
            label="Energy",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            color="lightsteelblue",
            label="Carbon tax",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            color="silver",
            label="Carbon offset",
        )

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()

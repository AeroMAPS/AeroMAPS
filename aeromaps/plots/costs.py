# @Time : 15/06/2023 09:06
# @Author : a.salgas
# @File : costs.py
# @Software: PyCharm
import warnings

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from ipywidgets import interact, Dropdown
from matplotlib.ticker import FuncFormatter

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

        self.ax.set_xlim(2020, self.years[-1])

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

        self.ax.set_xlim(2020, self.years[-1])

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

        self.ax.set_xlim(2020, self.years[-1])
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
            self.df.loc[self.prospective_years, "electrofuel_mean_mfsp_litre"] / 35.3,
            color="#828782",
            linestyle="-",
            label="Electrofuel",
            linewidth=2,
        )

        (self.line_hydrogen_electrolysis_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "electrolysis_h2_mean_mfsp_kg"] +
             self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
             + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
             ) / 119.93,
            color="#0075A3",
            linestyle="-",
            label="Hydrogen - Electrolysis",
            linewidth=2,
        )

        (self.line_hydrogen_gas_ccs_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "gas_ccs_h2_mean_mfsp_kg"] +
             self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
             + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
             ) / 119.93,
            color="#0075A3",
            linestyle=":",
            label="Hydrogen - Gas CSS",
            linewidth=2,
        )

        (self.line_hydrogen_gas_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "gas_h2_mean_mfsp_kg"] +
             self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
             + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
             ) / 119.93,
            color="#0075A3",
            linestyle="--",
            label="Hydrogen - Gas",
            linewidth=2,
        )

        (self.line_hydrogen_coal_ccs_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "coal_ccs_h2_mean_mfsp_kg"] +
             self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
             + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
             ) / 119.93,
            color="#0075A3",
            linestyle="-.",
            label="Hydrogen - Coal CCS",
            linewidth=2,
        )

        (self.line_hydrogen_coal_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "coal_h2_mean_mfsp_kg"] +
             self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
             + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
             ) / 119.93,
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
        self.ax.set_xlim(2020, self.years[-1])
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
            (self.df.loc[self.prospective_years, "electrofuel_mean_mfsp_litre"]) / 35.3,
        )
        self.line_hydrogen_electrolysis_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "electrolysis_h2_mean_mfsp_kg"] +
             self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
             + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
             ) / 119.93,
        )
        self.line_hydrogen_gas_ccs_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "gas_ccs_h2_mean_mfsp_kg"] +
             self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
             + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
             ) / 119.93,
        )
        self.line_hydrogen_gas_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "gas_h2_mean_mfsp_kg"] +
             self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
             + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
             ) / 119.93,
        )
        self.line_hydrogen_coal_ccs_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "coal_ccs_h2_mean_mfsp_kg"] +
             self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
             + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
             ) / 119.93,
        )
        self.line_hydrogen_coal_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "coal_h2_mean_mfsp_kg"] +
             self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
             + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
             ) / 119.93,
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
                    self.df.loc[self.prospective_years, "electrofuel_mean_mfsp_litre"]
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
                    self.df.loc[self.prospective_years, "electrolysis_h2_mean_mfsp_kg"] +
                    self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
                    + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
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
                    self.df.loc[self.prospective_years, "gas_ccs_h2_mean_mfsp_kg"] +
                    self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
                    + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
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
                    self.df.loc[self.prospective_years, "gas_h2_mean_mfsp_kg"] +
                    self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
                    + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
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
                    self.df.loc[self.prospective_years, "coal_ccs_h2_mean_mfsp_kg"] +
                    self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
                    + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
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
                    self.df.loc[self.prospective_years, "coal_h2_mean_mfsp_kg"] +
                    self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
                    + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
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
        self.ax.set_xlim(2020, self.years[-1])
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
                    self.df.loc[self.prospective_years, "electrofuel_mean_mfsp_litre"]
                    + self.df.loc[self.prospective_years, "electrofuel_mfsp_carbon_tax_supplement"]
            )
            / 35.3,
        )
        self.line_hydrogen_electrolysis_mfsp.set_ydata(
            (
                    self.df.loc[self.prospective_years, "electrolysis_h2_mean_mfsp_kg"] +
                    self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
                    + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
                    + self.df.loc[self.prospective_years, "electrolysis_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
        )
        self.line_hydrogen_gas_ccs_mfsp.set_ydata(
            (
                    self.df.loc[self.prospective_years, "gas_ccs_h2_mean_mfsp_kg"] +
                    self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
                    + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
                    + self.df.loc[self.prospective_years, "gas_ccs_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
        )
        self.line_hydrogen_gas_mfsp.set_ydata(
            (
                    self.df.loc[self.prospective_years, "gas_h2_mean_mfsp_kg"] +
                    self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
                    + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
                    + self.df.loc[self.prospective_years, "gas_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
        )
        self.line_hydrogen_coal_ccs_mfsp.set_ydata(
            (
                    self.df.loc[self.prospective_years, "coal_ccs_h2_mean_mfsp_kg"] +
                    self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
                    + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
                    + self.df.loc[self.prospective_years, "coal_ccs_h2_mfsp_carbon_tax_supplement"]
            )
            / 119.93,
        )
        self.line_hydrogen_coal_mfsp.set_ydata(
            (
                    self.df.loc[self.prospective_years, "coal_h2_mean_mfsp_kg"] +
                    self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]
                    + self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"]
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
        self.ax.set_xlim(2020, self.years[-1])
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
        year = self.years[-1]

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
            "Air transport sustainable drop-in fuels use, final year",
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
            "Air transport total drop-in fuels use, final year",
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
        year = self.years[-1]

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
            "Air transport sustainable drop-in fuels use, final year",
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
            "Air transport total drop-in fuels use, final year",
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
        self.ax.set_xlim(2020, self.years[-1])
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

        (self.line_total_airfare,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "operational_profit_per_ask"],
            color="grey",
            linestyle="-",
            label="Airfare",
            linewidth=2,
        )

        (self.line_total_lowering_offset,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            color="blue",
            linestyle="-",
            label="Total DOC (Carbon tax not including offsets)",
            linewidth=2,
        )

        (self.line_doc_total,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_mean"],
            color="blue",
            linestyle="--",
            label="Total DOC (Carbon tax applied to all direct emissions)",
            linewidth=2,
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            np.zeros(len(self.prospective_years)),
            color="#004CA3",
            alpha=0.8,
            label="DOC Non-energy",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            color="#0077FF",
            alpha=0.8,
            label="DOC Energy",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            color="#5CA8FF",
            alpha=0.8,
            label="Carbon tax (not including offsets)",
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
            color="#848482",
            alpha=0.8,
            label="Carbon offset",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"],
            color="#FF8800",
            alpha=0.8,
            label="Indirect-Operating Costs",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"],
            color="#FFAA00",
            alpha=0.8,
            label="Non-Operating Costs",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"],
            color="#FFD000",
            alpha=0.8,
            label="Passenger Tax",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"]
            + self.df.loc[self.prospective_years, "operational_profit_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"],
            color="#FFEA00",
            alpha=0.8,
            label="Operating Profit",
        )

        self.ax.grid()
        self.ax.set_title("Airfare breakdown")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Airfare [€/ASK]")
        self.ax = plt.gca()
        self.ax.legend(fontsize="8")
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

        self.line_total_airfare.set_ydata(
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "operational_profit_per_ask"]
        )

        self.line_total_lowering_offset.set_ydata(
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
        )

        self.line_doc_total.set_ydata(self.df.loc[self.prospective_years, "doc_total_per_ask_mean"])

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            np.zeros(len(self.prospective_years)),
            color="#004CA3",
            alpha=0.8,
            label="DOC Non-energy",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            color="#0077FF",
            alpha=0.8,
            label="DOC Energy",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            color="#5CA8FF",
            alpha=0.8,
            label="Carbon tax (not including offsets)",
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
            color="#848482",
            alpha=0.8,
            label="Carbon offset",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"],
            color="#FF8800",
            alpha=0.8,
            label="Indirect-Operating Costs",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"],
            color="#FFAA00",
            alpha=0.8,
            label="Non-Operating Costs",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"],
            color="#FFD000",
            alpha=0.8,
            label="Passenger Tax",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"]
            + self.df.loc[self.prospective_years, "operational_profit_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"],
            color="#FFEA00",
            alpha=0.8,
            label="Operating Profit",
        )

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class GeneralMACC:
    def __init__(self, data, fleet_model):
        self.df = data["vector_outputs"]
        self.fleet_model = fleet_model
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_3_x, plot_3_y),
        )
        self.create_plot_data()
        self.plot_interact()

    def plot_interact(self):
        interact(self.update, year=(2020, 2050, 1))

    def create_plot_data(self):
        self.macc_dict = {}

        for year in range(2020, 2050 + 1):
            name = []
            vol = []
            cost = []
            colors = []
            for category, sets in self.fleet_model.all_aircraft_elements.items():
                for aircraft_var in sets:
                    if hasattr(aircraft_var, "parameters"):
                        aircraft_var_name = aircraft_var.parameters.full_name
                    else:
                        aircraft_var_name = aircraft_var.full_name

                    vol.append(
                        self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_carbon_abatement_volume"
                        ]
                        / 1000000
                    )
                    cost.append(
                        self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_carbon_abatement_cost"
                        ]
                    )
                    if category == "Short Range":
                        colors.append("gold")
                    elif category == "Medium Range":
                        colors.append("goldenrod")
                    else:
                        colors.append("darkgoldenrod")
                    name.append(aircraft_var_name.split(":")[-1])

            name.extend(
                [
                    el
                    for el in [
                    "Bio - HEFA FOG",
                    "Bio - HEFA Others",
                    "Bio - Alcohol to Jet",
                    "Bio - FT MSW",
                    "Bio - FT Others",
                    "H2C",
                    "H2CCCS",
                    "H2G",
                    "H2GCCS",
                    "H2E",
                    "Electrofuel",
                    "OPS",
                    "LF",
                ]
                ]
            )

            # Abatement effective in MtCO2e
            vol.extend(
                [
                    elt / 1000000
                    for elt in [
                    self.df.abatement_effective_hefa_fog[year],
                    self.df.abatement_effective_hefa_others[year],
                    self.df.abatement_effective_atj[year],
                    self.df.abatement_effective_ft_msw[year],
                    self.df.abatement_effective_ft_others[year],
                    self.df.abatement_effective_hydrogen_coal[year],
                    self.df.abatement_effective_hydrogen_coal_ccs[year],
                    self.df.abatement_effective_hydrogen_gas[year],
                    self.df.abatement_effective_hydrogen_gas_ccs[year],
                    self.df.abatement_effective_hydrogen_electrolysis[year],
                    self.df.abatement_effective_electrofuel[year],
                    self.df.operations_abatement_effective[year],
                    self.df.load_factor_abatement_effective[year],
                ]
                ]
            )

            # carbon abatement cost in (€/tCO2e)
            cost.extend(
                [
                    el
                    for el in [
                    self.df.carbon_abatement_cost_hefa_fog[year],
                    self.df.carbon_abatement_cost_hefa_others[year],
                    self.df.carbon_abatement_cost_atj[year],
                    self.df.carbon_abatement_cost_ft_msw[year],
                    self.df.carbon_abatement_cost_ft_others[year],
                    self.df.carbon_abatement_cost_h2_coal[year],
                    self.df.carbon_abatement_cost_h2_coal_ccs[year],
                    self.df.carbon_abatement_cost_h2_gas[year],
                    self.df.carbon_abatement_cost_h2_gas_ccs[year],
                    self.df.carbon_abatement_cost_h2_electrolysis[year],
                    self.df.carbon_abatement_cost_electrofuel[year],
                    self.df.operations_abatement_cost[year],
                    self.df.load_factor_abatement_cost[year],
                ]
                ]
            )

            colors.extend(
                [
                    el
                    for el in [
                    "yellowgreen",
                    "yellowgreen",
                    "yellowgreen",
                    "yellowgreen",
                    "yellowgreen",
                    "yellowgreen",
                    "yellowgreen",
                    "yellowgreen",
                    "yellowgreen",
                    "yellowgreen",
                    "yellowgreen",
                    "orange",
                    "orange",
                ]
                ]
            )

            macc_df = pd.DataFrame(
                data=[vol, cost, colors],
                columns=name,
                index=["abatement_effective", "carbon_abatement_cost", "colors"],
            )

            macc_df = macc_df.transpose().sort_values(by="carbon_abatement_cost")

            self.macc_dict[year] = macc_df

        # maccneg_df = macc_df[macc_df["abatement_effective"] < 0]
        # maccpos_df = macc_df[macc_df["abatement_effective"] > 0]
        #
        # ##### POS ######
        #
        # heights_pos = maccpos_df["carbon_abatement_cost"].to_list()
        # names_pos = maccpos_df.index.to_list()
        # heights_pos.insert(0, 0)
        # heights_pos.append(heights_pos[-1])
        #
        # # # MAx effective maccpos
        # widths_effective_pos = maccpos_df["abatement_effective"].to_list()
        # widths_effective_pos.insert(0, 0)
        # widths_effective_pos.append(widths_effective_pos[-1])
        #
        # colors_pos = maccpos_df["colors"].to_list()
        #
        # maccpos_curve = self.ax.step(
        #     np.cumsum(widths_effective_pos) - widths_effective_pos,
        #     heights_pos,
        #     where="post",
        #     color="#335C67",
        #     label="Marginal abatement cost",
        #     linewidth=1,
        # )
        #
        # for i in range(len(widths_effective_pos) - 2):
        #     x_position = (np.cumsum(widths_effective_pos)[i] + np.cumsum(widths_effective_pos)[i + 1]) / 2
        #     y_position = min(2000 - 10, heights_pos[i + 1] + 5)
        #     self.ax.text(x_position, y_position, f'{names_pos[i]}\n {int(heights_pos[i + 1])}', rotation=0, size=8,
        #             ha='center', va='center')
        #
        # # Fill under the step plot with different colors for each step
        # for i in range(0, (len(widths_effective_pos) - 2)):
        #     # Create a polygon for each step
        #     polygon = plt.Polygon(
        #         [
        #             (np.cumsum(widths_effective_pos)[i], 0),
        #             (np.cumsum(widths_effective_pos)[i], heights_pos[i + 1]),
        #             (np.cumsum(widths_effective_pos)[i + 1], heights_pos[i + 1]),
        #             (np.cumsum(widths_effective_pos)[i + 1], 0),
        #         ],
        #         closed=True,
        #         alpha=1,
        #         facecolor=colors_pos[i],
        #         edgecolor="#335C67",
        #         linewidth=1,
        #         linestyle="--",
        #     )
        #     self.ax.add_patch(polygon)
        #
        # ##### NEG #####
        #
        # heights_neg = maccneg_df["carbon_abatement_cost"].to_list()
        # names_neg = maccneg_df.index.to_list()
        #
        # heights_neg.append(0)
        # heights_neg.insert(0, heights_neg[0])
        #
        # # # MAx effective maccneg
        # widths_effective_neg = maccneg_df["abatement_effective"].to_list()
        #
        # widths_effective_neg.insert(0, 0)
        # widths_effective_neg.append(0)
        #
        # colors_neg = maccneg_df["colors"].to_list()
        #
        # maccneg_curve = self.ax.step(
        #     np.cumsum(widths_effective_neg)[-1]
        #     - np.cumsum(widths_effective_neg)
        #     + widths_effective_neg,
        #     heights_neg,
        #     where="post",
        #     color="#335C67",
        #     label="Marginal emission cost",
        #     linewidth=1,
        # )
        #
        # for i in range(len(widths_effective_neg) - 2):
        #     x_position = np.cumsum(widths_effective_neg)[-1] - (
        #             np.cumsum(widths_effective_neg)[i] + np.cumsum(widths_effective_neg)[i + 1]) / 2
        #     y_position = max(-2000 + 10,heights_neg[i + 1]+ 5)
        #     self.ax.text(x_position, y_position, f'{names_neg[i]}\n {int(heights_neg[i + 1])}', rotation=0, size=8,
        #                  ha='center', va='center')
        #
        # # Fill under the step plot with different colors for each step
        # for i in range(0, (len(widths_effective_neg) - 2)):
        #     # Create a polygon for each step
        #     polygon = plt.Polygon(
        #         [
        #             (np.cumsum(widths_effective_neg)[-1] - np.cumsum(widths_effective_neg)[i], 0),
        #             (
        #                 np.cumsum(widths_effective_neg)[-1] - np.cumsum(widths_effective_neg)[i],
        #                 heights_neg[i + 1],
        #             ),
        #             (
        #                 np.cumsum(widths_effective_neg)[-1] - np.cumsum(widths_effective_neg)[i + 1],
        #                 heights_neg[i + 1],
        #             ),
        #             (np.cumsum(widths_effective_neg)[-1] - np.cumsum(widths_effective_neg)[i + 1], 0),
        #         ],
        #         closed=True,
        #         alpha=1,
        #         facecolor=colors_neg[i],
        #         edgecolor="#335C67",
        #         linewidth=1,
        #         linestyle="--",
        #     )
        #     self.ax.add_patch(polygon)
        #
        # self.ax.set_ylabel("Carbon Abatement Cost (€/t$\mathregular{CO_2}$)")
        # self.ax.set_xlabel("$\mathregular{CO_2}$ abatted (Mt)")
        #
        # self.ax.axhline(0, color="black", linestyle="--", linewidth=2)
        #
        # self.ax.axvline(0, color="black", linestyle="--", linewidth=2)
        #
        # legend_patches_1 = [
        #     mpatches.Patch(color="gold", alpha=1, label="Short-Range Efficiency"),
        #     mpatches.Patch(color="goldenrod", alpha=1, label="Medium-Range Efficiency"),
        #     mpatches.Patch(color="darkgoldenrod", alpha=1, label="Long-Range Efficiecny"),
        #     mpatches.Patch(color="yellowgreen", alpha=1, label="Energy"),
        #     mpatches.Patch(color="orange", alpha=1, label="Operations"),
        # ]
        #
        # self.ax.add_artist(self.ax.legend(handles=legend_patches_1, title="Type of lever", loc="upper right"))
        #
        # self.ax.set_xlim(np.cumsum(widths_effective_neg)[-1] - 50, np.cumsum(widths_effective_pos)[-1] + 50)
        # self.ax.set_ylim(max(-2000, min(min(heights_pos), min(heights_neg)) - 50),
        #                  min(2000, max(max(heights_neg), max(heights_pos)) + 50))
        #
        # self.ax.axvspan(xmin=self.ax.get_xlim()[0], xmax=0, facecolor="red", alpha=0.1, clip_on=True)
        # self.ax.axvspan(xmin=0, xmax=self.ax.get_xlim()[1], facecolor="blue", alpha=0.1, clip_on=True)
        #
        # legend_patches = [
        #     mpatches.Patch(
        #         color="red",
        #         alpha=0.1,
        #         label="Extra emissions zone\nnegative abatement costs are\nassociated with extra costs",
        #     ),
        #     mpatches.Patch(color="blue", alpha=0.1, label="Carbon abatement zone"),
        # ]
        #
        # self.ax.legend(handles=legend_patches, loc="upper left")
        #
        # self.ax.grid()
        # plt.show()
        #
        # self.ax.set_title("Marginal abatement cost curve for drop-in fuels")
        #
        # # #
        # self.fig.canvas.header_visible = False
        # self.fig.canvas.toolbar_position = "bottom"
        # # self.fig.canvas.layout.width = "auto"
        # # self.fig.canvas.layout.height = "auto"
        # self.fig.tight_layout()

    def update(self, year):
        self.ax.cla()

        macc_df = self.macc_dict[year]

        maccneg_df = macc_df[macc_df["abatement_effective"] < 0]
        maccpos_df = macc_df[macc_df["abatement_effective"] > 0]

        ##### POS ######

        heights_pos = maccpos_df["carbon_abatement_cost"].to_list()
        names_pos = maccpos_df.index.to_list()
        heights_pos.insert(0, 0)
        heights_pos.append(heights_pos[-1])

        # # MAx effective maccpos
        widths_effective_pos = maccpos_df["abatement_effective"].to_list()
        widths_effective_pos.insert(0, 0)
        widths_effective_pos.append(widths_effective_pos[-1])

        cumwidths_effective_pos = np.cumsum(widths_effective_pos)

        colors_pos = maccpos_df["colors"].to_list()

        maccpos_curve = self.ax.step(
            cumwidths_effective_pos - widths_effective_pos,
            heights_pos,
            where="post",
            color="#335C67",
            label="Marginal abatement cost",
            linewidth=1,
        )

        for i in range(len(widths_effective_pos) - 2):
            x_position = (cumwidths_effective_pos[i] + cumwidths_effective_pos[i + 1]) / 2
            y_position = min(2000 - 10, heights_pos[i + 1] + 5)
            self.ax.text(
                x_position,
                y_position,
                f"{names_pos[i]}\n {int(heights_pos[i + 1])}",
                rotation=0,
                size=8,
                ha="center",
                va="center",
            )

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_effective_pos) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [
                    (cumwidths_effective_pos[i], 0),
                    (cumwidths_effective_pos[i], heights_pos[i + 1]),
                    (cumwidths_effective_pos[i + 1], heights_pos[i + 1]),
                    (cumwidths_effective_pos[i + 1], 0),
                ],
                closed=True,
                alpha=1,
                facecolor=colors_pos[i],
                edgecolor="#335C67",
                linewidth=1,
                linestyle="--",
            )
            self.ax.add_patch(polygon)

        ##### NEG #####

        heights_neg = maccneg_df["carbon_abatement_cost"].to_list()
        names_neg = maccneg_df.index.to_list()

        heights_neg.append(0)
        heights_neg.insert(0, heights_neg[0])

        # # MAx effective maccneg
        widths_effective_neg = maccneg_df["abatement_effective"].to_list()

        widths_effective_neg.insert(0, 0)
        widths_effective_neg.append(0)

        cumwidths_effective_neg = np.cumsum(widths_effective_neg)

        colors_neg = maccneg_df["colors"].to_list()

        maccneg_curve = self.ax.step(
            cumwidths_effective_neg[-1] - cumwidths_effective_neg + widths_effective_neg,
            heights_neg,
            where="post",
            color="#335C67",
            label="Marginal emission cost",
            linewidth=1,
        )

        for i in range(len(widths_effective_neg) - 2):
            x_position = (
                    cumwidths_effective_neg[-1]
                    - (cumwidths_effective_neg[i] + cumwidths_effective_neg[i + 1]) / 2
            )
            y_position = max(-2000 + 10, heights_neg[i + 1] + 5)
            self.ax.text(
                x_position,
                y_position,
                f"{names_neg[i]}\n {int(heights_neg[i + 1])}",
                rotation=0,
                size=8,
                ha="center",
                va="center",
            )

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_effective_neg) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [
                    (cumwidths_effective_neg[-1] - cumwidths_effective_neg[i], 0),
                    (
                        cumwidths_effective_neg[-1] - cumwidths_effective_neg[i],
                        heights_neg[i + 1],
                    ),
                    (
                        cumwidths_effective_neg[-1] - cumwidths_effective_neg[i + 1],
                        heights_neg[i + 1],
                    ),
                    (cumwidths_effective_neg[-1] - cumwidths_effective_neg[i + 1], 0),
                ],
                closed=True,
                alpha=1,
                facecolor=colors_neg[i],
                edgecolor="#335C67",
                linewidth=1,
                linestyle="--",
            )
            self.ax.add_patch(polygon)

        self.ax.set_ylabel("Carbon Abatement Cost (€/t$\mathregular{CO_2}$)")
        self.ax.set_xlabel("$\mathregular{CO_2}$ abatted (Mt)")

        self.ax.axhline(0, color="black", linestyle="--", linewidth=2)

        self.ax.axvline(0, color="black", linestyle="--", linewidth=2)

        legend_patches_1 = [
            mpatches.Patch(color="gold", alpha=1, label="Short-Range Efficiency"),
            mpatches.Patch(color="goldenrod", alpha=1, label="Medium-Range Efficiency"),
            mpatches.Patch(color="darkgoldenrod", alpha=1, label="Long-Range Efficiecny"),
            mpatches.Patch(color="yellowgreen", alpha=1, label="Energy"),
            mpatches.Patch(color="orange", alpha=1, label="Operations"),
        ]

        self.ax.add_artist(
            self.ax.legend(handles=legend_patches_1, title="Type of lever", loc="upper right")
        )

        self.ax.set_xlim(cumwidths_effective_neg[-1] - 50, cumwidths_effective_pos[-1] + 50)
        self.ax.set_ylim(
            max(-2000, min(min(heights_pos), min(heights_neg)) - 50),
            min(2000, max(max(heights_neg), max(heights_pos)) + 50),
        )

        self.ax.axvspan(
            xmin=self.ax.get_xlim()[0], xmax=0, facecolor="red", alpha=0.1, clip_on=True
        )
        self.ax.axvspan(
            xmin=0, xmax=self.ax.get_xlim()[1], facecolor="blue", alpha=0.1, clip_on=True
        )

        legend_patches = [
            mpatches.Patch(
                color="red",
                alpha=0.1,
                label="Extra emissions zone\nnegative abatement costs are\nassociated with extra costs",
            ),
            mpatches.Patch(color="blue", alpha=0.1, label="Carbon abatement zone"),
        ]

        self.ax.legend(handles=legend_patches, loc="upper left")

        self.ax.grid()
        self.ax.set_title("Marginal abatement cost curve for drop-in fuels")
        self.fig.tight_layout()
        self.fig.canvas.draw()



class DetailledMFSPBreakdownPerPathway:
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
        self.ax2 = self.ax.twinx()
        self.create_plot()
        self.plot_interact()

    def plot_interact(self):
        interact(self.update, pathway=[('Bio - HEFA Fog', 'hefa_fog'),
                                       ('Bio - HEFA Others', 'hefa_others'),
                                       ('Bio - FT MSW','ft_msw'),
                                       ('Bio - FT Others', 'ft_others'),
                                       ('Bio - ATJ','atj'),
                                       ('LH2 - Electrolysis','electrolysis_h2'),
                                       ('LH2 - Gas CCS','gas_ccs_h2'),
                                       ('LH2 - Gas','gas_h2'),
                                       ('LH2 - Coal CCS','coal_ccs_h2'),
                                       ('LH2 - Coal','coal_h2'),
                                       ('E-fuel','electrofuel'),
                                       ])

    def create_plot(self):
        pass

    def update(self, pathway):
        self.ax.cla()
        self.ax2.cla()


        if pathway in ['hefa_fog','hefa_others','ft_msw','ft_others','atj']:

            capex_val = self.df.loc[self.prospective_years, "biofuel_"+pathway+"_mfsp"] * self.df.loc[
                self.prospective_years, "biofuel_mean_capex_share_"+pathway] / 100
            opex_val = self.df.loc[self.prospective_years, "biofuel_"+pathway+"_mfsp"] * self.df.loc[
                self.prospective_years, "biofuel_mean_var_opex_share_"+pathway] / 100
            feedstock_val = self.df.loc[self.prospective_years, "biofuel_"+pathway+"_mfsp"] * self.df.loc[
                self.prospective_years, "biofuel_mean_feedstock_share_"+pathway] / 100
            carbon_tax_val = self.df.loc[self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_"+pathway]
            kerosene_val = self.df.loc[self.prospective_years, "kerosene_market_price"]
            kerosene_tax_val = self.df.loc[self.prospective_years, "kerosene_price_supplement_carbon_tax"]

            self.ax.fill_between(
                self.prospective_years,
                capex_val,
                np.zeros(len(self.prospective_years)),
                color="#277DA1",
                label="Capex",edgecolor='#212529', linewidth=0.5
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val,
                capex_val,
                color="#4D908E",
                label="Opex",edgecolor='#212529', linewidth=0.5
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val + feedstock_val,
                capex_val + opex_val,
                color="#90BE6D",
                label="Feedstock",edgecolor='#212529', linewidth=0.5
            )

            (self.line_total,) = self.ax.plot(
                self.prospective_years,
                capex_val + opex_val + feedstock_val,
                color="#43AA8B",
                linestyle="-",
                label="Total mean MFSP",
                linewidth=2,
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val + feedstock_val + carbon_tax_val,
                capex_val + opex_val + feedstock_val,
                color="white",
                facecolor="#9066D4",
                hatch="//",
                label="Carbon Tax",edgecolor='#212529', linewidth=0.5
            )

            (self.line_tax,) = self.ax.plot(
                self.prospective_years,
                capex_val + opex_val + feedstock_val + carbon_tax_val,
                color="#6414E5",
                linestyle="--",
                label="Total mean MFSP + carbon tax",
                linewidth=2,
            )

            (self.line_fossil,) = self.ax.plot(
                self.prospective_years,
                kerosene_val,
                color="black",
                linestyle="-",
                label="Fossil kerosene",
                linewidth=2,
            )

            (self.line_fossil_plus_tax,) = self.ax.plot(
                self.prospective_years,
                kerosene_val + kerosene_tax_val,
                color="black",
                linestyle="--",
                label="Fossil kerosene + carbon tax",
                linewidth=2,
            )

            self.ax.grid()
            self.ax.set_title("MFSP breakdown")
            self.ax.set_xlabel("Year")
            self.ax.set_ylabel("MFSP [€/L]")

            self.ax.set_ylim(0, None)
            self.ax2.set_ylim(self.ax.get_ylim()[0] / (self.float_inputs["lhv_kerosene"]*self.float_inputs["density_kerosene"]),
                              self.ax.get_ylim()[1] / (self.float_inputs["lhv_kerosene"]*self.float_inputs["density_kerosene"]))

            # Move the label for the second y-axis to the right
            self.ax2.yaxis.set_label_position("right")
            self.ax2.set_ylabel("MFSP [€/MJ]")

        elif pathway == 'electrofuel':

            capex_val = self.df.loc[self.prospective_years, "electrofuel_mean_mfsp_litre"] * self.df.loc[
                self.prospective_years, "electrofuel_mean_capex_share"] / 100
            opex_val = self.df.loc[self.prospective_years, "electrofuel_mean_mfsp_litre"] * self.df.loc[
                self.prospective_years, "electrofuel_mean_opex_share"] / 100
            energy_val = self.df.loc[self.prospective_years, "electrofuel_mean_mfsp_litre"] * self.df.loc[
                self.prospective_years, "electrofuel_mean_elec_share"] / 100
            co2_feed_val = self.df.loc[self.prospective_years, "electrofuel_mean_mfsp_litre"] * self.df.loc[
                self.prospective_years, "electrofuel_mean_co2_share"] / 100
            carbon_tax_val = self.df.loc[self.prospective_years, "electrofuel_mfsp_carbon_tax_supplement"]
            kerosene_val = self.df.loc[self.prospective_years, "kerosene_market_price"]
            kerosene_tax_val = self.df.loc[self.prospective_years, "kerosene_price_supplement_carbon_tax"]

            self.ax.fill_between(
                self.prospective_years,
                capex_val,
                np.zeros(len(self.prospective_years)),
                color="#277DA1",
                label="Capex",edgecolor='#212529', linewidth=0.5
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val,
                capex_val,
                color="#4D908E",
                label="Opex",edgecolor='#212529', linewidth=0.5
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val + energy_val,
                capex_val + opex_val,
                color="#90BE6D",
                label="Energy",edgecolor='#212529', linewidth=0.5
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val + energy_val + co2_feed_val,
                capex_val + opex_val + energy_val,
                color="#540b0e",
                label="CO2 Feed", edgecolor='#212529', linewidth=0.5
            )

            (self.line_total,) = self.ax.plot(
                self.prospective_years,
                capex_val + opex_val + energy_val + co2_feed_val,
                color="#43AA8B",
                linestyle="-",
                label="Total mean MFSP",
                linewidth=2,
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val + energy_val + co2_feed_val + carbon_tax_val,
                capex_val + opex_val + energy_val + co2_feed_val,
                color="white",
                facecolor="#9066D4",
                hatch="//",
                label="Carbon Tax",edgecolor='#212529', linewidth=0.5
            )

            (self.line_tax,) = self.ax.plot(
                self.prospective_years,
                capex_val + opex_val + energy_val + co2_feed_val + carbon_tax_val,
                color="#6414E5",
                linestyle="--",
                label="Total mean MFSP + carbon tax",
                linewidth=2,
            )

            (self.line_fossil,) = self.ax.plot(
                self.prospective_years,
                kerosene_val,
                color="black",
                linestyle="-",
                label="Fossil kerosene",
                linewidth=2,
            )

            (self.line_fossil_plus_tax,) = self.ax.plot(
                self.prospective_years,
                kerosene_val + kerosene_tax_val,
                color="black",
                linestyle="--",
                label="Fossil kerosene + carbon tax",
                linewidth=2,
            )

            self.ax.grid()
            self.ax.set_title("MFSP breakdown")
            self.ax.set_xlabel("Year")
            self.ax.set_ylabel("MFSP [€/L]")

            self.ax.set_ylim(0, None)
            self.ax2.set_ylim(self.ax.get_ylim()[0] / (self.float_inputs["lhv_kerosene"]*self.float_inputs["density_kerosene"]),
                              self.ax.get_ylim()[1] / (self.float_inputs["lhv_kerosene"]*self.float_inputs["density_kerosene"]))

            # Move the label for the second y-axis to the right
            self.ax2.yaxis.set_label_position("right")
            self.ax2.set_ylabel("MFSP [€/MJ]")


        elif pathway in ['electrolysis_h2','gas_ccs_h2','gas_h2','coal_ccs_h2','coal_h2']:
            capex_val = self.df.loc[self.prospective_years, pathway+"_mean_mfsp_kg"] * self.df.loc[
                self.prospective_years, pathway+"_mean_capex_share"] / 100
            opex_val = self.df.loc[self.prospective_years, pathway+"_mean_mfsp_kg"] * self.df.loc[
                self.prospective_years, pathway+"_mean_opex_share"] / 100

            if pathway == 'electrolysis_h2':
                energy_val = self.df.loc[self.prospective_years, pathway+"_mean_mfsp_kg"] * self.df.loc[
                    self.prospective_years, pathway+"_mean_elec_share"] / 100
            else:
                energy_val = self.df.loc[self.prospective_years, pathway + "_mean_mfsp_kg"] * self.df.loc[
                    self.prospective_years, pathway + "_mean_fuel_cost_share"] / 100

            if pathway in ['gas_ccs_h2','coal_ccs_h2']:
                ccs_val = self.df.loc[self.prospective_years, pathway + "_mean_mfsp_kg"] * self.df.loc[
                    self.prospective_years, pathway + "_mean_ccs_cost_share"] / 100

            else:
                ccs_val = 0

            liquefaction_capex_val = self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"] * self.df.loc[
                self.prospective_years, "liquefaction_h2_mean_capex_share"] / 100
            liquefaction_opex_val = self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"] * self.df.loc[
                self.prospective_years, "liquefaction_h2_mean_opex_share"] / 100
            liquefaction_energy_val = self.df.loc[self.prospective_years, "liquefaction_h2_mean_mfsp_kg"] * self.df.loc[
                    self.prospective_years, "liquefaction_h2_mean_elec_share"] / 100

            transport =  self.df.loc[self.prospective_years, "transport_h2_cost_per_kg"]


            carbon_tax_val = self.df.loc[self.prospective_years, pathway+"_mfsp_carbon_tax_supplement"]
            kerosene_val = self.df.loc[self.prospective_years, "kerosene_market_price"]
            kerosene_tax_val = self.df.loc[self.prospective_years, "kerosene_price_supplement_carbon_tax"]

            self.ax.fill_between(
                self.prospective_years,
                capex_val,
                np.zeros(len(self.prospective_years)),
                color="#277DA1",
                label="Hydrogen Capex",edgecolor='#212529', linewidth=0.5
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val,
                capex_val,
                color="#4D908E",
                label="Hydrogen Opex",edgecolor='#212529', linewidth=0.5
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val + energy_val,
                capex_val + opex_val,
                color="#90BE6D",
                label="Hydrogen Energy",edgecolor='#212529', linewidth=0.5
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val + energy_val + ccs_val,
                capex_val + opex_val + energy_val,
                color="#F94144",
                label="Hydrogen CCS",edgecolor='#212529', linewidth=0.5
            )

            (self.line_total,) = self.ax.plot(
                self.prospective_years,
                capex_val + opex_val + energy_val + ccs_val,
                color="#43AA8B",
                linestyle="-",
                label="Hydrogen Mean MFSP",
                linewidth=2,
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val + energy_val + ccs_val + liquefaction_capex_val,
                capex_val + opex_val + energy_val +ccs_val,
                color="#F9C74F",
                label="Liquefaction Capex",edgecolor='#212529', linewidth=0.5
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val + energy_val + ccs_val + liquefaction_capex_val+liquefaction_opex_val,
                capex_val + opex_val + energy_val + ccs_val+ liquefaction_capex_val,
                color="#F9844A",
                label="Liquefaction Opex",edgecolor='#212529', linewidth=0.5
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val + energy_val + ccs_val + liquefaction_capex_val + liquefaction_opex_val +liquefaction_energy_val,
                capex_val + opex_val + energy_val + ccs_val + liquefaction_capex_val ++ liquefaction_opex_val,
                color="#F8961E",
                label="Liquefaction Energy",edgecolor='#212529', linewidth=0.5
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val + energy_val + ccs_val + liquefaction_capex_val + liquefaction_opex_val + liquefaction_energy_val +transport,
                capex_val + opex_val + energy_val + ccs_val + liquefaction_capex_val + + liquefaction_opex_val + liquefaction_energy_val,
                color="#C9A690",
                label="Transport",edgecolor='#212529', linewidth=0.5
            )

            (self.line_total_full,) = self.ax.plot(
                self.prospective_years,
                capex_val + opex_val + energy_val + ccs_val + liquefaction_capex_val + liquefaction_opex_val + liquefaction_energy_val + transport,
                color="#253C78",
                linestyle="-",
                label="Mean MFSP incl. L+T",
                linewidth=2,
            )

            self.ax.fill_between(
                self.prospective_years,
                capex_val + opex_val + energy_val + ccs_val + liquefaction_capex_val + liquefaction_opex_val + liquefaction_energy_val + transport + carbon_tax_val,
                capex_val + opex_val + energy_val + ccs_val + liquefaction_capex_val + liquefaction_opex_val + liquefaction_energy_val + transport,
                color="white",
                facecolor="#9066D4",
                hatch="//",
                label="Carbon Tax",edgecolor='#212529', linewidth=0.5
            )

            (self.line_tax,) = self.ax.plot(
                self.prospective_years,
                capex_val + opex_val + energy_val + ccs_val + liquefaction_capex_val + liquefaction_opex_val + liquefaction_energy_val + transport + carbon_tax_val,
                color="#6414E5",
                linestyle="--",
                label="Total Mean MFSP + carbon tax",
                linewidth=2,
            )

            (self.line_fossil,) = self.ax.plot(
                self.prospective_years,
                kerosene_val / (self.float_inputs["lhv_kerosene"]*self.float_inputs["density_kerosene"]) * self.float_inputs["lhv_hydrogen"],
                color="black",
                linestyle="-",
                label="Fossil kerosene",
                linewidth=2,
            )

            (self.line_fossil_plus_tax,) = self.ax.plot(
                self.prospective_years,
                (kerosene_val + kerosene_tax_val) / (self.float_inputs["lhv_kerosene"]*self.float_inputs["density_kerosene"]) * self.float_inputs["lhv_hydrogen"],
                color="black",
                linestyle="--",
                label="Fossil kerosene + carbon tax",
                linewidth=2,
            )

            self.ax.grid()
            self.ax.set_title("MFSP breakdown")
            self.ax.set_xlabel("Year")
            self.ax.set_ylabel("Hydrogen MFSP [€/Kg]")

            self.ax.set_ylim(0, None)
            self.ax2.set_ylim(self.ax.get_ylim()[0]/self.float_inputs["lhv_hydrogen"], self.ax.get_ylim()[1]/self.float_inputs["lhv_hydrogen"])

            # Move the label for the second y-axis to the right
            self.ax2.yaxis.set_label_position("right")
            self.ax2.set_ylabel("MFSP [€/MJ]")

        # Reversing legend entries
        handles, labels = self.ax.get_legend_handles_labels()
        self.ax.legend(handles[::-1], labels[::-1])
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        self.fig.tight_layout()
        self.fig.tight_layout()
        self.fig.canvas.draw()

# @Time : 15/06/2023 09:06
# @Author : a.salgas
# @File : costs.py
# @Software: PyCharm

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
        colors = ['#ee9b00', '#ffbf47',
                  '#bb3e03', '#0c9e30', '#097223',
                  '#828782', '#52F752', '#0ABAFF',
                  '#8CAAB6', '#0ABAFF', '#8CAAB6', '#87AE87'
                  ]

        columns = ['plant_building_cost_hefa_fog',
                   'plant_building_cost_hefa_others',
                   'plant_building_cost_atj',
                   'plant_building_cost_ft_others',
                   'plant_building_cost_ft_msw',
                   'electrofuel_plant_building_cost',
                   'electrolysis_plant_building_cost',
                   'gas_ccs_plant_building_cost',
                   'gas_plant_building_cost',
                   'coal_ccs_plant_building_cost',
                   'coal_plant_building_cost',
                   'liquefaction_plant_building_cost',
                   ]

        data_to_plot = self.df.loc[self.prospective_years, columns]
        bottom = None  # Initialize bottom positions for stacking

        for col, color in zip(data_to_plot.columns, colors):
            if bottom is None:
                self.bar_annual_investment = self.ax.bar(data_to_plot.index, data_to_plot[col], label=col, color=color)
                bottom = data_to_plot[col]
            else:
                self.bar_annual_investment = self.ax.bar(data_to_plot.index, data_to_plot[col], label=col, color=color,
                                                         bottom=bottom)
                bottom += data_to_plot[col]

        tick_interval = 5
        min_year = min(data_to_plot.index)
        max_year = max(data_to_plot.index)
        ticks = range(min_year, max_year + 1, tick_interval)
        self.ax.set_xticks(ticks)
        self.ax.set_xticklabels(ticks, rotation=45)
        self.ax.grid(axis='y')
        self.ax.set_title("Annual investment per pathway (w/o fossil)")
        self.ax.set_xlabel("Year")
        self.ax.set_xlim(2020, max(self.prospective_years))
        self.ax.set_ylabel("Annual Capital Investment [M€]")
        self.ax = plt.gca()
        legend = self.ax.legend([
            'Bio - HEFA FOG',
            'Bio - HEFA Others',
            'Bio - Alcohol to Jet',
            'Bio - FT Others',
            'Bio - FT Municipal Waste',
            'Electrofuel',
            '$H_2$ - Electrolysis',
            '$H_2$ - Gas + CCS',
            '$H_2$ - Gas',
            '$H_2$ - Coal + CCS',
            '$H_2$ - Coal',
            '(L-)$H_2$ (Liquefaction)'
        ])
        legend.set_title('Pathways', prop={'size': 12})

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        self.fig.canvas.layout.width = "auto"
        self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        # TODO Bien tester le update qui est une création directe de chatgpt...
        self.df = df_data["vector_outputs"]

        columns = ['plant_building_cost_hefa_fog',
                   'plant_building_cost_hefa_others',
                   'plant_building_cost_atj',
                   'plant_building_cost_ft_others',
                   'plant_building_cost_ft_msw',
                   'electrofuel_plant_building_cost',
                   'electrolysis_plant_building_cost',
                   'gas_ccs_plant_building_cost',
                   'gas_plant_building_cost',
                   'coal_ccs_plant_building_cost',
                   'coal_plant_building_cost',
                   'liquefaction_plant_building_cost',
                   ]

        data_to_plot = self.df.loc[self.prospective_years, columns]

        for bar, col in zip(self.bar_annual_investment, data_to_plot.columns):
            bar.set_height(data_to_plot[col])

        self.ax.collections.clear()

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
        colors = ['#2A3438', '#2A3438', '#ee9b00', '#ee9b00', '#ffbf47', '#ffbf47',
                  '#bb3e03', '#bb3e03', '#0c9e30', '#0c9e30', '#097223', '#097223',
                  '#828782', '#828782', '#52F752', '#52F752', '#0ABAFF', '#0ABAFF',
                  '#8CAAB6', '#8CAAB6', '#0ABAFF', '#0ABAFF', '#8CAAB6', '#8CAAB6',
                  '#87AE87']

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
            self.df.loc[self.prospective_years, "liquefaction_h2_total_cost"].fillna(0) + self.df.loc[
                self.prospective_years, "transport_h2_total_cost"].fillna(0),

            colors=colors,
        )

        self.ax.grid(axis='y')
        self.ax.set_title("Annual energy expenses per pathway")
        self.ax.set_ylabel("Energy expenses [M€]")
        self.ax = plt.gca()

        primary_legend_entries = [
            'Fossil Kerosene',
            '_nolegend_',
            'Bio - HEFA FOG',
            '_nolegend_',
            'Bio - HEFA Others',
            '_nolegend_',
            'Bio - Alcohol to Jet',
            '_nolegend_',
            'Bio - FT Others',
            '_nolegend_',
            'Bio - FT Municipal Waste',
            '_nolegend_',
            'Electrofuel',
            '_nolegend_',
            'Electrolysis $H_2$ ',
            '_nolegend_',
            'Gas CCS $H_2$ ',
            '_nolegend_',
            'Gas $H_2$ ',
            '_nolegend_',
            'Coal CCS $H_2$ ',
            '_nolegend_',
            'Coal $H_2$ ',
            '_nolegend_',
            'Hydrogen Logistics*'

        ]

        stacks = self.annual_energy_expenses

        hatches = ["", "//", "", "//", "", "//", "", "//", "", "//", "", "//", "", "//", "", "//", "", "//", "", "//",
                   "", "//", "", "//", ""]
        for stack, hatch in zip(stacks, hatches):
            stack.set_hatch(hatch)

        self.ax.set_xlim(2020, 2050)

        primary_legend = self.ax.legend(primary_legend_entries, title='Pathways', loc='upper left')
        self.ax.add_artist(primary_legend)

        # Create hatch legend manually
        hatch_patch = mpatches.Patch(facecolor='white', hatch='//', edgecolor='black')
        self.ax.legend(handles=[hatch_patch], labels=['Carbon Tax'], loc='upper right')

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        self.fig.canvas.layout.width = "auto"
        self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        # TODO a tester

        self.df = df_data["vector_outputs"]

        self.annual_energy_expenses.set_ydata(
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
            self.df.loc[self.prospective_years, "liquefaction_h2_total_cost"].fillna(0) + self.df.loc[
                self.prospective_years, "transport_h2_total_cost"].fillna(0),
        )

        self.ax.collections.clear()

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
            label='Scenario energy expenses',
            linestyle='-',
            color='#0c9e30'
        )

        (self.line_energy_expenses_carb_tax,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "non_discounted_energy_expenses"] +
             self.df.loc[self.prospective_years, "kerosene_carbon_tax_cost"] +
             self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_fog"] +
             self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_others"] +
             self.df.loc[self.prospective_years, "biofuel_carbon_tax_atj"] +
             self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_others"] +
             self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_msw"] +
             self.df.loc[self.prospective_years, "electrolysis_h2_carbon_tax"] +
             self.df.loc[self.prospective_years, "gas_ccs_h2_carbon_tax"] +
             self.df.loc[self.prospective_years, "gas_h2_carbon_tax"] +
             self.df.loc[self.prospective_years, "coal_ccs_h2_carbon_tax"] +
             self.df.loc[self.prospective_years, "coal_h2_carbon_tax"] +
             self.df.loc[self.prospective_years, "electrofuel_carbon_tax"]
             ),
            label='Scenario energy expenses incl. carbon tax',
            linestyle='--',
            color='#0c9e30'
        )
        (self.line_bau_energy_expenses,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "non_discounted_BAU_energy_expenses"],
            label='Business as usual energy expenses',
            linestyle='-',
            color='#2A3438'
        )
        (self.line_bau_energy_expenses_carbon_tax,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "non_discounted_BAU_energy_expenses"] +
             self.df.loc[self.prospective_years, "kerosene_carbon_tax_BAU"]),
            label='Business as usual energy expenses incl. carbon tax',
            linestyle='--',
            color='#2A3438'
        )

        self.ax.grid(axis='y')
        self.ax.legend(loc='upper left')
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
            (self.df.loc[self.prospective_years, "non_discounted_energy_expenses"] +
             self.df.loc[self.prospective_years, "kerosene_carbon_tax_cost"] +
             self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_fog"] +
             self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_others"] +
             self.df.loc[self.prospective_years, "biofuel_carbon_tax_atj"] +
             self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_others"] +
             self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_msw"] +
             self.df.loc[self.prospective_years, "electrolysis_h2_carbon_tax"] +
             self.df.loc[self.prospective_years, "gas_ccs_h2_carbon_tax"] +
             self.df.loc[self.prospective_years, "gas_h2_carbon_tax"] +
             self.df.loc[self.prospective_years, "coal_ccs_h2_carbon_tax"] +
             self.df.loc[self.prospective_years, "coal_h2_carbon_tax"] +
             self.df.loc[self.prospective_years, "electrofuel_carbon_tax"]
             )
        )

        self.line_bau_energy_expenses.set_ydata(
            self.df.loc[self.prospective_years, "non_discounted_BAU_energy_expenses"]
        )

        self.line_bau_energy_expenses_carbon_tax.set_ydata(
            (self.df.loc[self.prospective_years, "non_discounted_BAU_energy_expenses"] +
             self.df.loc[self.prospective_years, "kerosene_carbon_tax_BAU"])
        )

        self.ax.collections.clear()

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

        self.ax.grid(axis='y')
        self.ax.set_title("MFSP per pathway (kerosene: market price)")
        self.ax.set_ylabel("MFSP [€/MJ]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2020, 2050)
        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        self.fig.canvas.layout.width = "auto"
        self.fig.canvas.layout.height = "auto"
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

        self.ax.collections.clear()

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
            (self.df.loc[self.prospective_years, "kerosene_market_price"] + self.df.loc[
                self.prospective_years, "kerosene_price_supplement_carbon_tax"]) / 35.3,
            color="#2A3438",
            linestyle="-",
            label="Fossil Kerosene",
            linewidth=2,
        )

        (self.line_biofuel_hefa_fog_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "biofuel_hefa_fog_mfsp"] + self.df.loc[
                self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_hefa_fog"]) / 35.3,
            color="#097223",
            linestyle="-",
            label="Bio - HEFA FOG",
            linewidth=2,
        )

        (self.line_biofuel_hefa_others_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "biofuel_hefa_others_mfsp"] + self.df.loc[
                self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_hefa_others"]) / 35.3,
            color="#097223",
            linestyle=":",
            label="Bio - HEFA Others",
            linewidth=2,
        )

        (self.line_biofuel_atj_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "biofuel_atj_mfsp"] + self.df.loc[
                self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_atj"]) / 35.3,
            color="#097223",
            linestyle="--",
            label="Bio - Alcohol to Jet",
            linewidth=2,
        )
        (self.line_biofuel_ft_others_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "biofuel_ft_others_mfsp"] + self.df.loc[
                self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_ft_others"]) / 35.3,
            color="#097223",
            linestyle="-.",
            label="Bio - FT Others",
            linewidth=2,
        )

        (self.line_biofuel_ft_msw_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "biofuel_ft_msw_mfsp"] + self.df.loc[
                self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_ft_msw"]) / 35.3,
            color="#097223",
            linestyle=(0, (5, 10)),
            label="Bio - FT MSW",
            linewidth=2,
        )

        (self.line_electrofuel_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "electrofuel_avg_cost_per_l"] + self.df.loc[
                self.prospective_years, "electrofuel_mfsp_carbon_tax_supplement"]) / 35.3,
            color="#828782",
            linestyle="-",
            label="Electrofuel",
            linewidth=2,
        )

        (self.line_hydrogen_electrolysis_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_electrolysis"] + self.df.loc[
                self.prospective_years, "electrolysis_h2_mfsp_carbon_tax_supplement"]) / 119.93,
            color="#0075A3",
            linestyle="-",
            label="Hydrogen - Electrolysis",
            linewidth=2,
        )

        (self.line_hydrogen_gas_ccs_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_gas_ccs"] + self.df.loc[
                self.prospective_years, "gas_ccs_h2_mfsp_carbon_tax_supplement"]) / 119.93,
            color="#0075A3",
            linestyle=":",
            label="Hydrogen - Gas CSS",
            linewidth=2,
        )

        (self.line_hydrogen_gas_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_gas"] + + self.df.loc[
                self.prospective_years, "gas_h2_mfsp_carbon_tax_supplement"]) / 119.93,
            color="#0075A3",
            linestyle="--",
            label="Hydrogen - Gas",
            linewidth=2,
        )

        (self.line_hydrogen_coal_ccs_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_coal_ccs"] + self.df.loc[
                self.prospective_years, "coal_ccs_h2_mfsp_carbon_tax_supplement"]) / 119.93,
            color="#0075A3",
            linestyle="-.",
            label="Hydrogen - Coal CCS",
            linewidth=2,
        )

        (self.line_hydrogen_coal_mfsp,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_coal"] + self.df.loc[
                self.prospective_years, "coal_h2_mfsp_carbon_tax_supplement"]) / 119.93,
            color="#0075A3",
            linestyle=(0, (5, 10)),
            label="Hydrogen Coal",
            linewidth=2,
        )

        self.ax.grid(axis='y')
        self.ax.set_title("MFSP per pathway incl. carbon tax")
        self.ax.set_ylabel("MFSP [€/MJ]")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2020, 2050)
        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        self.fig.canvas.layout.width = "auto"
        self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        self.df = df_data['vector_outputs']

        self.line_kerosene_price.set_ydata(
            (self.df.loc[self.prospective_years, "kerosene_market_price"] + self.df.loc[
                self.prospective_years, "kerosene_price_supplement_carbon_tax"]) / 35.3,
        )
        self.line_biofuel_hefa_fog_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "biofuel_hefa_fog_mfsp"] + self.df.loc[
                self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_hefa_fog"]) / 35.3,
        )
        self.line_biofuel_hefa_others_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "biofuel_hefa_others_mfsp"] + self.df.loc[
                self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_hefa_others"]) / 35.3,
        )
        self.line_biofuel_atj_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "biofuel_atj_mfsp"] + self.df.loc[
                self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_atj"]) / 35.3,
        )
        self.line_biofuel_ft_others_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "biofuel_ft_others_mfsp"] + self.df.loc[
                self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_ft_others"]) / 35.3,
        )
        self.line_biofuel_ft_msw_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "biofuel_ft_msw_mfsp"] + self.df.loc[
                self.prospective_years, "biofuel_mfsp_carbon_tax_supplement_ft_msw"]) / 35.3,
        )
        self.line_electrofuel_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "electrofuel_avg_cost_per_l"] + self.df.loc[
                self.prospective_years, "electrofuel_mfsp_carbon_tax_supplement"]) / 35.3,
        )
        self.line_hydrogen_electrolysis_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_electrolysis"] + self.df.loc[
                self.prospective_years, "electrolysis_h2_mfsp_carbon_tax_supplement"]) / 119.93,
        )
        self.line_hydrogen_gas_ccs_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_gas_ccs"] + self.df.loc[
                self.prospective_years, "gas_ccs_h2_mfsp_carbon_tax_supplement"]) / 119.93,
        )
        self.line_hydrogen_gas_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_gas"] + self.df.loc[
                self.prospective_years, "gas_h2_mfsp_carbon_tax_supplement"]) / 119.93,
        )
        self.line_hydrogen_coal_ccs_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_coal_ccs"] + self.df.loc[
                self.prospective_years, "coal_ccs_h2_mfsp_carbon_tax_supplement"]) / 119.93,
        )
        self.line_hydrogen_coal_mfsp.set_ydata(
            (self.df.loc[self.prospective_years, "h2_avg_cost_per_kg_coal"] + self.df.loc[
                self.prospective_years, "coal_h2_mfsp_carbon_tax_supplement"]) / 119.93,
        )

        self.ax.collections.clear()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DiscountEffect():
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
            label="Discounted expenses",
            linewidth=2,
        )

        self.ax.grid(axis='y')
        self.ax.set_title("Total (energy) expenses (M€)")
        self.ax.set_ylabel("M€ / year")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2020, 2050)
        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        self.fig.canvas.layout.width = "auto"
        self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        self.df = df_data["vector_outputs"]

        self.line_non_discounted.set_ydata(
            self.df.loc[self.prospective_years, "non_discounted_energy_expenses"]
        )

        self.line_discounted.set_ydata(
            self.df.loc[self.prospective_years, "discounted_energy_expenses"]
        )

        self.ax.collections.clear()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DropInMACC():
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

        pathways = ["Bio - HEFA FOG",
                    "Bio - HEFA Others",
                    "Bio - Alcohol to Jet",
                    "Bio - FT MSW",
                    "Bio - FT Others",
                    "Electrofuel"]

        # Abatement potential in MtCO2e
        abatement_potential = [elt / 1000000 for elt in
                               [self.df.abatement_potential_hefa_fog[year],
                                self.df.abatement_potential_hefa_others[year],
                                self.df.abatement_potential_atj[year],
                                self.df.abatement_potential_ft_msw[year],
                                self.df.abatement_potential_ft_others[year],
                                self.df.abatement_potential_electrofuel[year]]]

        # Energy available in EJ
        energy_avail = [elt / 1000000000000 for elt in [self.df.energy_avail_hefa_fog[year],
                                                        self.df.energy_avail_hefa_others[year],
                                                        self.df.energy_avail_atj[year],
                                                        self.df.energy_avail_ft_msw[year],
                                                        self.df.energy_avail_ft_others[year],
                                                        self.df.energy_avail_electrofuel[year]]]

        # carbon abatement cost in (€/tCO2e)
        carbon_abatement_cost = [self.df.carbon_abatement_cost_hefa_fog[year],
                                 self.df.carbon_abatement_cost_hefa_others[year],
                                 self.df.carbon_abatement_cost_atj[year],
                                 self.df.carbon_abatement_cost_ft_msw[year],
                                 self.df.carbon_abatement_cost_ft_others[year],
                                 self.df.electrofuel_abatement_cost[year]
                                 ]

        colors = ['#ee9b00', '#ffbf47',
                  '#bb3e03', '#097223', '#0c9e30', '#828782']

        macc_df = pd.DataFrame(data=[abatement_potential, energy_avail, carbon_abatement_cost, colors],
                               columns=pathways, index=['abatement_potential', 'energy_avail',
                                                        'carbon_abatement_cost', 'colors'])

        macc_df = macc_df.transpose().sort_values(by='carbon_abatement_cost')

        heights = macc_df['carbon_abatement_cost'].to_list()
        names = macc_df.index.to_list()
        heights.insert(0, 0)
        heights.append(heights[-1])

        # MAx potential MACC
        widths_potential = macc_df['abatement_potential'].to_list()
        widths_potential.insert(0, 0)
        widths_potential.append(widths_potential[-1])

        colors=macc_df['colors'].to_list()

        self.macc_curve = self.ax.step(np.cumsum(widths_potential) - widths_potential, heights, 'g', where='post', color="#335C67",
                label="Marginal abatement cost", linewidth=1.5)

        # Fill under the step plot with different colors for each step
        for i in range(0,(len(widths_potential) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon([(np.cumsum(widths_potential)[i], 0), (np.cumsum(widths_potential)[i], heights[i+1]),
                                   (np.cumsum(widths_potential)[i + 1], heights[i+1]),
                                   (np.cumsum(widths_potential)[i + 1], 0)],
                                  closed=True, color=colors[i], alpha=0.5)
            self.ax.add_patch(polygon)

        fuel = macc_df.energy_avail.to_list()
        fuel.insert(0, 0)
        widths_potential.pop()
        self.ax2 = self.ax.twinx()
        self.ax2.plot(np.cumsum(widths_potential), np.cumsum(fuel), color="#9E2A2B", linestyle=':', label="Energy potential",
                 marker='x')

        self.ax2.axhline(y=self.df.energy_consumption_dropin_fuel[year] / 1e12 -
                      self.df.energy_consumption_kerosene[year] / 1e12, color='black',
                    linewidth=1, linestyle='-.')
        self.ax2.text(0, self.df.energy_consumption_dropin_fuel[year] / 1e12 -
                      self.df.energy_consumption_kerosene[year] / 1e12 + 2, 'Air transport alternative drop-in fuels use, 2050')

        self.ax.grid(True, which="both", ls=':')
        self.ax.set_ylabel('Carbon Abatement Cost (€/t$\mathregular{CO_2}$)')
        self.ax2.set_ylabel('Energy potential under current allocation (EJ)')
        self.ax.set_xlabel('$\mathregular{CO_2}$ abatted (Mt)')

        self.ax.grid(True, which="both", ls=':')
        self.ax.set_ylabel('Carbon Abatement Cost (€/t$\mathregular{CO_2}$)')
        self.ax.set_xlabel('$\mathregular{CO_2}$ abatted (Mt)')


        self.ax.text(np.cumsum(widths_potential)[0] + 10, heights[1] - 50, names[0])
        self.ax.text(np.cumsum(widths_potential)[1] + 10, heights[2] + 18, names[1])
        self.ax.text(np.cumsum(widths_potential)[2] + 10, heights[3] - 50, names[2])
        self.ax.text(np.cumsum(widths_potential)[3] + 10, heights[4] - 50, names[3])
        self.ax.text(np.cumsum(widths_potential)[4] + 10, heights[5] - 50, names[4])
        self.ax.text(np.cumsum(widths_potential)[5] + 10, heights[6] - 50, names[5])

        self.fig.legend(fancybox=True, shadow=True, loc='upper left')

        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        self.fig.canvas.layout.width = "auto"
        self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        self.df = df_data["vector_outputs"]
        self.float_outputs = df_data["float_outputs"]
        self.years = df_data["years"]["full_years"]
        self.historic_years = df_data["years"]["historic_years"]
        self.prospective_years = df_data["years"]["prospective_years"]

        # Select year at which the MACC is plotted
        year = 2050

        # create a dataframe for the various pathways
        # (usage: sorting the values by increasing carbon abatement cost)

        pathways = ["Bio - HEFA FOG",
                    "Bio - HEFA Others",
                    "Bio - Alcohol to Jet",
                    "Bio - FT MSW",
                    "Bio - FT Others",
                    "Electrofuel"]

        # Abatement potential in MtCO2e
        abatement_potential = [elt / 1000000 for elt in
                               [self.df.abatement_potential_hefa_fog[year],
                                self.df.abatement_potential_hefa_others[year],
                                self.df.abatement_potential_atj[year],
                                self.df.abatement_potential_ft_msw[year],
                                self.df.abatement_potential_ft_others[year],
                                self.df.abatement_potential_electrofuel[year]]]

        # Energy available in EJ
        energy_avail = [elt / 1000000000000 for elt in [self.df.energy_avail_hefa_fog[year],
                                                        self.df.energy_avail_hefa_others[year],
                                                        self.df.energy_avail_atj[year],
                                                        self.df.energy_avail_ft_msw[year],
                                                        self.df.energy_avail_ft_others[year],
                                                        self.df.energy_avail_electrofuel[year]]]

        # carbon abatement cost in (€/tCO2e)
        carbon_abatement_cost = [self.df.carbon_abatement_cost_hefa_fog[year],
                                 self.df.carbon_abatement_cost_hefa_others[year],
                                 self.df.carbon_abatement_cost_atj[year],
                                 self.df.carbon_abatement_cost_ft_msw[year],
                                 self.df.carbon_abatement_cost_ft_others[year],
                                 self.df.electrofuel_abatement_cost[year]
                                 ]

        colors = ['#ee9b00', '#ffbf47',
                  '#bb3e03', '#097223', '#0c9e30', '#828782']

        macc_df = pd.DataFrame(data=[abatement_potential, energy_avail, carbon_abatement_cost, colors],
                               columns=pathways, index=['abatement_potential', 'energy_avail',
                                                        'carbon_abatement_cost', 'colors'])

        macc_df = macc_df.transpose().sort_values(by='carbon_abatement_cost')

        heights = macc_df['carbon_abatement_cost'].to_list()
        names = macc_df.index.to_list()
        heights.insert(0, 0)
        heights.append(heights[-1])

        # MAx potential MACC
        widths_potential = macc_df['abatement_potential'].to_list()
        widths_potential.insert(0, 0)
        widths_potential.append(widths_potential[-1])

        colors = macc_df['colors'].to_list()

        self.macc_curve = self.ax.step(np.cumsum(widths_potential) - widths_potential, heights, 'g', where='post',
                                       color="#335C67",
                                       label="Marginal abatement cost", linewidth=1.5)

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_potential) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [(np.cumsum(widths_potential)[i], 0), (np.cumsum(widths_potential)[i], heights[i + 1]),
                 (np.cumsum(widths_potential)[i + 1], heights[i + 1]),
                 (np.cumsum(widths_potential)[i + 1], 0)],
                closed=True, color=colors[i], alpha=0.5)
            self.ax.add_patch(polygon)

        fuel = macc_df.energy_avail.to_list()
        fuel.insert(0, 0)
        widths_potential.pop()
        self.ax2 = self.ax.twinx()
        self.ax2.plot(np.cumsum(widths_potential), np.cumsum(fuel), color="#9E2A2B", linestyle=':',
                      label="Energy potential",
                      marker='x')

        self.ax2.axhline(y=self.df.energy_consumption_dropin_fuel[year] / 1e12 -
                           self.df.energy_consumption_kerosene[year] / 1e12, color='black',
                         linewidth=1, linestyle='-.')
        self.ax2.text(0, self.df.energy_consumption_dropin_fuel[year] / 1e12 -
                      self.df.energy_consumption_kerosene[year] / 1e12 + 2,
                      'Air transport alternative drop-in fuels use, 2050')

        self.ax.grid(True, which="both", ls=':')
        self.ax.set_ylabel('Carbon Abatement Cost (€/t$\mathregular{CO_2}$)')
        self.ax2.set_ylabel('Energy potential under current allocation (EJ)')
        self.ax.set_xlabel('$\mathregular{CO_2}$ abatted (Mt)')

        self.ax.grid(True, which="both", ls=':')
        self.ax.set_ylabel('Carbon Abatement Cost (€/t$\mathregular{CO_2}$)')
        self.ax.set_xlabel('$\mathregular{CO_2}$ abatted (Mt)')

        self.ax.text(np.cumsum(widths_potential)[0] + 10, heights[1] - 50, names[0])
        self.ax.text(np.cumsum(widths_potential)[1] + 10, heights[2] + 18, names[1])
        self.ax.text(np.cumsum(widths_potential)[2] + 10, heights[3] - 50, names[2])
        self.ax.text(np.cumsum(widths_potential)[3] + 10, heights[4] - 50, names[3])
        self.ax.text(np.cumsum(widths_potential)[4] + 10, heights[5] - 50, names[4])
        self.ax.text(np.cumsum(widths_potential)[5] + 10, heights[6] - 50, names[5])

        self.ax.collections.clear()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()





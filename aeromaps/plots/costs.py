# @Time : 15/06/2023 09:06
# @Author : a.salgas
# @File : costs.py
# @Software: PyCharm

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

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
                  '#828782',  '#52F752',  '#0ABAFF',
                  '#8CAAB6', '#0ABAFF', '#8CAAB6', '#00BBE0'
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

        self.bar_annual_investment = (self.df.loc[self.prospective_years, columns].plot.bar(
            stacked=True,
            width=0.8,
            ax=self.ax,
            color=colors))

        self.ax.grid(axis='y')
        self.ax.set_title("Annual investment per pathway (w/o fossil)")
        space_tick = 5
        self.ax.set_xlabel("Year")
        ticks = self.ax.xaxis.get_ticklocs()
        ticklabels = [l.get_text() for l in self.ax.xaxis.get_ticklabels()]
        self.ax.xaxis.set_ticks(ticks[::space_tick])
        self.ax.xaxis.set_ticklabels(ticklabels[::space_tick])
        self.ax.set_ylabel("Annual Capital Investment [M€]")
        self.ax = plt.gca()
        self.ax.legend([
            'Bio - HEFA FOG',
            'Bio - HEFA Others',
            'Bio - Alcohol to Jet',
            'Bio - FT Others',
            'Bio - FT Municipal Waste',
            'Electrofuel',
            'LH2 (Electrolysis)',
            'LH2 (Liquefaction)'
        ])
        # self.ax.set_xlim(2020, 2050)
        #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        # TODO a refaire plus proprement que juste dupliquer si possible?
        self.data = df_data

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

        colors = ['#ee9b00', '#ffbf47', '#bb3e03', '#0c9e30', '#097223', '#828782', '#0075A3', '#00BBE0', ]

        self.bar_annual_investment = self.data.loc[range(2020, 2050 + 1), columns].plot.bar(
            stacked=True,
            width=0.8,
            ax=self.ax,
            color=colors
        )

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
        #TODO a tester

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

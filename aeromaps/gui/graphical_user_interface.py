import os
import os.path as pth
import matplotlib
import ipywidgets as widgets
import markdown as md
from aeromaps.core.process import DATA_FOLDER, EXCEL_DATA_FILE
from IPython.display import display, HTML, Javascript
import matplotlib.pyplot as plt
import pandas as pd
from ipydatagrid import DataGrid

from aeromaps.gui.plots import plot_1, plot_2, plot_3
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model import (
    AircraftParameters,
    Aircraft,
    SubcategoryParameters,
    SubCategory,
)

# matplotlib.use("Agg")
font = {"size": 8}
matplotlib.rc("font", **font)


def make_box_layout():
    return widgets.Layout(
        display="flex",
        border="solid 1px black",
        margin="0px 10px 10px 0px",
        padding="5px 5px 5px 5px",
        width="auto",
        align_center="center",
    )


class GraphicalUserInterface(widgets.VBox):
    def __init__(self, process):
        super().__init__()
        # TODO: make these private attributes
        self.process = process

        self._data_files = {}
        self._load_data(EXCEL_DATA_FILE)

        # Initialization of data tabs outputs
        self.w_data_information_df = None
        self.w_vector_inputs_df = None
        self.w_float_inputs_df = None
        self.w_vector_outputs_df = None
        self.w_float_outputs_df = None

        self.w_figure_output = widgets.Button(
            description="Download figures",
            disabled=False,
            button_style="",  # 'success', 'info', 'warning', 'danger' or ''
            tooltip="Download figures",
            icon="download",
        )
        self.w_figure_output.layout.width = "max-content"
        self.w_figure_output.on_click(self._download_figures)

        self.w_language = widgets.Dropdown(
            options=["English"],
            value="English",
            # description="Language:"
        )
        self.w_language.layout.width = "max-content"
        self.w_language.layout.object_position = "right"
        self.w_language.observe(self._build_ui, "value")

        self._build_ui()
        self.update(None)

    def _build_ui(self, change=None):

        # Initialization of graph output
        self.out1 = None
        self.out2 = None
        self.out3 = None

        # Initialization of plots
        self.plots1 = None
        self.plots2 = None
        self.plots3 = None

        self._create_widgets()

        self._create_graphs()

        self._create_dataframe_tabs()

        self.build_tab()

    def build_tab(self):
        self.tabs = widgets.Tab()
        self.tabs.observe(self._update_dataframe_tabs)

        self.tab1 = widgets.VBox([self.graphs, self.controls])
        self.tab1.layout = make_box_layout()

        self.tab2 = widgets.VBox(
            [widgets.VBox([self.w_file_output, self.download_output]), self.df_tabs]
        )

        if self.w_language.value == "English":
            FILE_PATH = pth.join(pth.dirname(__file__), "resources/aboutAeroMAPS_en.md")
            f = open(FILE_PATH, "r", encoding="utf-8")
        else:
            FILE_PATH = pth.join(pth.dirname(__file__), "resources/aboutAeroMAPS_fr.md")
            f = open(FILE_PATH, "r", encoding="utf-8")
        html = str(md.markdown(f.read()))
        f.close()
        string = rf"{html}"
        self.tab3 = widgets.HTMLMath(value=string)

        self.tabs.children = [self.tab1, self.tab2, self.tab3]

        en_tabs = ["Simulator", "Data", "About AeroMAPS"]
        fr_tabs = ["Simulateur", "Données", "À propos d'AeroMAPS"]

        if self.w_language.value == "Français":
            tabs = fr_tabs
        else:
            tabs = en_tabs
        for i, tab in enumerate(tabs):
            self.tabs.set_title(i, tab)

        dummy = widgets.HTML(value="")
        dummy.layout.width = "100%"
        language = widgets.HBox([dummy, self.w_language])
        language.layout.object_position = "right"
        language.layout.display = "flex"
        language.layout.width = "100%"

        # add to children
        self.children = [language, self.tabs]

    def _create_dataframe_tabs(self, change=None):
        # Data information
        datagrid = DataGrid(self.process.data_information_df, selection_mode="cell")
        datagrid.auto_fit_columns = True
        self.w_data_information_df = datagrid

        # Vector inputs
        datagrid = DataGrid(self.process.vector_inputs_df, selection_mode="cell")
        datagrid.auto_fit_columns = True
        self.w_vector_inputs_df = datagrid

        # Parameters
        datagrid = DataGrid(self.process.float_inputs_df, selection_mode="cell")
        datagrid.auto_fit_columns = True
        self.w_float_inputs_df = datagrid

        # Vector Outputs
        datagrid = DataGrid(self.process.vector_outputs_df, selection_mode="cell")
        datagrid.auto_fit_columns = True
        self.w_vector_outputs_df = datagrid

        # Float Outputs
        datagrid = DataGrid(self.process.float_outputs_df, selection_mode="cell")
        datagrid.auto_fit_columns = True
        self.w_float_outputs_df = datagrid

        # All tabs
        self.df_tabs = widgets.Tab()
        self.df_tabs.children = [
            self.w_data_information_df,
            self.w_vector_inputs_df,
            self.w_float_inputs_df,
            self.w_vector_outputs_df,
            self.w_float_outputs_df,
        ]

        self.df_tabs.set_title(0, "Data Information")
        self.df_tabs.set_title(1, "Vector Inputs")
        self.df_tabs.set_title(2, "Float Inputs")
        self.df_tabs.set_title(3, "Vector Outputs")
        self.df_tabs.set_title(4, "Float Outputs")

    def _update_dataframe_tabs(self, change=None):
        # Data information
        self.w_data_information_df.data = self.process.data_information_df

        # Vector inputs
        self.w_vector_inputs_df.data = self.process.vector_inputs_df

        # Parameters
        self.w_float_inputs_df.data = self.process.float_inputs_df

        # Vector Outputs
        self.w_vector_outputs_df.data = self.process.vector_outputs_df

        # Float Outputs
        self.w_float_outputs_df.data = self.process.float_outputs_df

    def _create_widgets(self):
        # TODO: Convert to french
        plot_1_list = list(plot_1.keys())
        # Define the widgets to use
        self.graph1 = widgets.Dropdown(
            options=plot_1_list,
            value=plot_1_list[0],
            disabled=False,
        )
        self.graph1.layout.width = "max-content"
        self.graph1.observe(self._create_graph_1_en, "value")
        self.graph1.observe(self._create_graph_2_en, "value")

        plot_2_list = list(plot_2.keys())
        self.graph2 = widgets.Dropdown(
            options=plot_2_list,
            value=plot_2_list[0],
            disabled=False,
        )
        self.graph2.layout.width = "max-content"
        self.graph2.observe(self._create_graph_2_en, "value")

        plot_3_list = list(plot_3.keys())
        self.graph3 = widgets.Dropdown(
            options=plot_3_list,
            value=plot_3_list[0],
        )
        self.graph3.layout.width = "max-content"
        self.graph3.observe(self._create_graph_3_en, "value")

        # Scenario mode
        self.w_action_scenarios = widgets.Dropdown(
            options=[
                "Example scenario",
            ],
            value="Example scenario",
            description="",
            layout={"align_center": "center", "width": "initial"},
        )
        self.w_action_scenarios.observe(self._update_scenario_infos, "value")
        self.w_action_scenarios.observe(self.update, "value")

        # Discovery mode

        # Air traffic

        self.w_growth_short_range_percent = widgets.FloatSlider(
            min=-7,
            max=7,
            step=0.1,
            value=3.0,
            description="Short Range",
            description_tooltip="Annual air traffic growth (RPK) in percent (%) for Passenger Short Range market\n"
            "The default value of 3.0% corresponds to the aviation industry's projections",
        )
        self.w_growth_short_range_percent.observe(self.update, "value")

        self.w_growth_medium_range_percent = widgets.FloatSlider(
            min=-7,
            max=7,
            step=0.1,
            value=3.0,
            description="Medium Range",
            description_tooltip="Annual air traffic growth (RPK) in percent (%) for Passenger Medium Range market\n"
            "The default value of 3.0% corresponds to the aviation industry's projections",
        )
        self.w_growth_medium_range_percent.observe(self.update, "value")

        self.w_growth_long_range_percent = widgets.FloatSlider(
            min=-7,
            max=7,
            step=0.1,
            value=3.0,
            description="Long Range",
            description_tooltip="Annual air traffic growth (RPK) in percent (%) for Passenger Long Range market\n"
            "The default value of 3.0% corresponds to the aviation industry's projections",
        )
        self.w_growth_long_range_percent.observe(self.update, "value")

        self.w_growth_freight_percent = widgets.FloatSlider(
            min=-7,
            max=7,
            step=0.1,
            value=3.0,
            description="Freight",
            description_tooltip="Annual air traffic growth (RTK) in percent (%) for Freight market\n"
            "The default value of 3.0% corresponds to the aviation industry's projections",
        )
        self.w_growth_freight_percent.observe(self.update, "value")

        self.w_grouped_market = widgets.Checkbox(
            value=False,
            description="Assuming similar market evolutions",
            layout={"width": "max-content"},
        )
        self.w_grouped_market.observe(self.update, "value")

        self.w_short_range_reduction = widgets.Checkbox(
            value=False,
            description="Reduction of Short Range flights (modal shift, ban)",
            layout={"width": "max-content"},
        )
        self.w_short_range_reduction.observe(self.update, "value")

        self.w_social_measure = widgets.Checkbox(
            value=False,
            description="Halving the number of 'frequent flyer' flights",
            layout={"width": "max-content"},
        )
        self.w_social_measure.observe(self.update, "value")

        # Energy intensity

        self.w_aircraft_efficiency = widgets.SelectionSlider(
            options=["Renewal", "Trend", "Accelerated", "Ambitious"],
            value="Trend",
            description="Aircraft efficiency",
            description_tooltip="Improvement of aircraft energy efficiency (more efficient engines, lighter aircraft, "
            "aerodynamics, innovative architectures...)\n- Renewal: continuation of the fleet renewal with the current "
            "more recent aircraft\n- Trend: integration of new more efficient aircraft with the "
            "historical fleet turnover speed (trend basis of around 1.0% per year)\n- Accelerated: "
            "trend scenario with an accelerated fleet turnover\n- Ambitious: accelerated "
            "scenario with more efficient aircraft",
        )
        self.w_aircraft_efficiency.observe(self.update, "value")

        self.w_load_factor = widgets.SelectionSlider(
            options=["Constant", "Unambitious", "Trend", "Ambitious", "Very ambitious"],
            value="Trend",
            description="Load factor",
            description_tooltip="Improvement of fleet aircraft load factor (ratio between the number of passengers "
            "and the number of seats)\n- Constant: stagnation at the 2019 level at around 82%\n"
            "- Unambitious: achieving a load factor in 2050 of 85%\n"
            "- Trend: achieving a load factor in 2050 of 89%\n"
            "- Ambitious: achieving a load factor in 2050 of 92%\n"
            "- Very ambitious: achieving a load factor in 2050 of 95%",
        )
        self.w_load_factor.observe(self.update, "value")

        self.w_operations = widgets.SelectionSlider(
            options=["Constant", "Pessimistic", "Realistic", "Optimistic"],
            value="Constant",
            description="Operations",
            description_tooltip="Improvement of operations in the air (optimised trajectories, air traffic management"
            "...)\n and on the ground (taxiing, energy use of airport infrastructures...)\n"
            "- Constant: no change in operations\n"
            "- Pessimistic: marginal improvement in operations (4% in 2050)\n"
            "- Realistic: development of improved operations (8% in 2050)\n"
            "- Optimistic: generalisation of improved operations (12% in 2050)",
        )
        self.w_operations.observe(self.update, "value")

        self.w_turboprop = widgets.Checkbox(
            value=False,
            description="Turboprop for Short and Medium Range flights",
        )
        self.w_turboprop.observe(self.update, "value")

        self.w_contrails_avoidance = widgets.Checkbox(
            value=False,
            description="Contrails avoidance strategies",
            layout={"width": "max-content"},
        )
        self.w_contrails_avoidance.observe(self.update, "value")

        # Carbon intensity

        self.w_energy_mix = widgets.SelectionSlider(
            options=["Kerosene", "Biofuel", "Electrofuel", "ReFuelEU"],
            value="Kerosene",
            description="Energy mix",
            description_tooltip="Drop-in fuels used into the fleet until 2050\n"
            "- Kerosene: exclusive use of fossil kerosene\n"
            "- Biofuel: exclusive use of biofuel with deployment starting in 2025\n"
            "- Electrofuel: exclusive use of electrofuel with deployment starting in 2030\n"
            "- ReFuelEU: balanced energy mix relying mainly on electrofuels and biofuels,\n"
            "   based on ReFuelEU targets",
        )
        self.w_energy_mix.observe(self.update, "value")

        self.w_hydrogen_aircraft = widgets.SelectionSlider(
            options=["Absence", "Limited", "Moderate", "Ambitious"],
            value="Absence",
            description="Hydrogen aircraft",
            description_tooltip="Deployment of hydrogen aircraft into the fleet\n"
            "- Absence: not deployed\n"
            "- Limited: late deployment from 2040 and limited to short-range\n"
            "- Moderate: deployment from 2035 and limited to short-range\n"
            "- Ambitious: large deployment from 2035",
        )
        self.w_hydrogen_aircraft.observe(self.update, "value")

        self.w_biofuel_production = widgets.SelectionSlider(
            options=["High-carbon", "Current", "Low-carbon"],
            value="Current",
            description="Biofuel production",
            description_tooltip="Biomass production characteristics\n"
            "- High-carbon: characteristics based on the AtJ pathway with dedicated crops\n"
            "- Current: current characteristics based on the HEFA pathway with used cooking oils\n"
            "- Low-carbon: low-carbon characteristics based on FT pathway with residues",
        )
        self.w_biofuel_production.observe(self.update, "value")

        self.w_hydrogen_production = widgets.SelectionSlider(
            options=["Current", "Gas without CCS", "Gas with CCS", "Electrolysis"],
            value="Current",
            description="Hydrogen production",
            description_tooltip="Hydrogen production characteristics\n"
            "- Current: current characteristics mainly based on gas and coal pathways without "
            "carbon capture and storage\n"
            "- Gas without CCS: characteristics based on gas pathway without carbon capture and "
            "storage\n"
            "- Gas with CCS: characteristics based on gas pathway with carbon capture and storage\n"
            "- Electrolysis: characteristics based on electrolysis pathways (CO2 emission factor "
            "depending on electricity CO2 emission factor)",
        )
        self.w_hydrogen_production.observe(self.update, "value")

        self.w_electricity_production = widgets.SelectionSlider(
            options=[
                "High-carbon",
                "Current",
                "Medium-carbon",
                "Low-carbon",
                "Dedicated low-carbon",
            ],
            value="Current",
            description="Electricity production",
            description_tooltip="Electricity production characteristics in terms of CO2 emission factor\n"
            "- High-carbon: electricity from coal (1100 gCO2/kWh)\n"
            "- Current: current world grid electricity (429 gCO2/kWh)\n"
            "- Medium-carbon: transition to a medium-carbon grid electricity (240 gCO2/kWh)\n"
            "- Low-carbon: transition to a low-carbon grid electricity (70 gCO2/kWh)\n"
            "- Dedicated low-carbon: dedicated electricity from renewable (20 gCO2/kWh)",
        )
        self.w_electricity_production.observe(self.update, "value")

        # Climate and energy

        self.w_temperature = widgets.SelectionSlider(
            options=["+1.5°C", "+1.6°C", "+1.7°C", "+1.8°C", "+1.9°C", "+2.0°C"],
            value="+1.8°C",
            description="Temperature target",
            description_tooltip="Target temperature to limit global warming\n"
            "The values correspond to the low and high ranges of the Paris Agreement\n"
            "The default value corresponds to an arbitrary choice from SBTi",
        )
        self.w_temperature.observe(self.update, "value")

        self.w_success_percentage = widgets.SelectionSlider(
            options=["17%", "33%", "50%", "67%", "83%"],
            value="67%",
            description="Chances of success",
            description_tooltip="Changes of success for achieving the desired climate target\n"
            "This represents to the percentile considered for the TCRE coefficient used in "
            "climate sciences\n"
            "The default value corresponds to an arbitrary choice from SBTi\n"
            "The value of 50% allows considering median values",
        )
        self.w_success_percentage.observe(self.update, "value")

        self.w_cdr = widgets.SelectionSlider(
            options=["Undeveloped", "Slightly developed", "Developed", "Highly developed"],
            value="Undeveloped",
            description="Carbon dioxide removal",
            description_tooltip="Use of Carbon Dioxide Removal (CDR)\n"
            "CDR corresponds to a process in which CO2 is removed from atmosphere and stored\n"
            "This can be based on natural processes (afforestation, reforestation...) or on "
            "technical processes\n (bioenergy with carbon capture and storage, direct air capture "
            "with carbon storage...)\n"
            "The large-scale deployment of these technologies remains uncertain\n"
            "- Undeveloped: no CDR over 2020-2100\n"
            "- Slightly developed: 285 GtCO2 of cumulative negative CO2 emissions over 2020-2100\n"
            "- Developed: 527 GtCO2 of cumulative negative CO2 emissions over 2020-2100\n"
            "- Highly developed: 733 GtCO2 of cumulative negative CO2 emissions over 2020-2100\n",
        )
        self.w_cdr.observe(self.update, "value")

        self.w_biomass_available = widgets.SelectionSlider(
            options=[
                "Very pessimistic",
                "Pessimistic",
                "Realistic",
                "Optimistic",
                "Very optimistic",
            ],
            value="Realistic",
            description="Biomass availability",
            description_tooltip="Biomass available in 2050 in the form of different resources\n"
            "(waste, agricultural and forest residues, energy crops, algae)\n"
            "- Very pessimistic: total amount of 37 EJ\n"
            "- Pessimistic: total amount of 100 EJ\n"
            "- Realistic: total amount of 164 EJ\n"
            "- Optimistic: total amount of 302 EJ\n"
            "- Very optimistic: total amount of 557 EJ",
        )
        self.w_biomass_available.observe(self.update, "value")

        self.w_electricity_available = widgets.SelectionSlider(
            options=["Current", "Pessimistic", "Realistic", "Optimistic", "Very optimistic"],
            value="Realistic",
            description="Electricity availability",
            description_tooltip="Electricity available in 2050\n"
            "- Current: current total amount of 100 EJ\n"
            "- Pessimistic: total amount of 150 EJ\n"
            "- Realistic: total amount of 200 EJ\n"
            "- Optimistic: total amount of 250 EJ\n"
            "- Very optimistic: total amount of 300 EJ",
        )
        self.w_electricity_available.observe(self.update, "value")

        # Allocations

        self.w_carbon_budget_allocation = widgets.SelectionSlider(
            options=["2.3%", "2.6%", "3.4%", "6.8%"],
            value="2.6%",
            description="Carbon budget",
            description_tooltip="Share of the world carbon budget allocated to aviation\nThe term allocation here "
            "refers to the result of complex mechanisms of negotiation, \ncompetition, "
            "arbitration and regulation for access to resources\n- 2.3%: share consumed in the "
            "ambitious ICAO LTAG scenario for +2.0°C\n- 2.6%: grandfathering approach "
            "(current share of CO2 emissions)\n- 3.4%: share consumed in the IEA ETP 2014 scenario"
            "\n- 6.8%: share consumed in the ambitious ICAO LTAG scenario for +1.5°C",
        )
        self.w_carbon_budget_allocation.observe(self.update, "value")

        self.w_equivalent_carbon_budget_allocation = widgets.SelectionSlider(
            options=["0%", "3.8%", "5.1%", "15%"],
            value="5.1%",
            description="Equivalent carbon budget",
            description_tooltip="Share of the world equivalent carbon budget allocated to aviation\nThe term "
            "allocation here refers to the result of complex mechanisms of negotiation, \n"
            "competition, arbitration and regulation for access to resources\n- 0%: share "
            "equivalent to a stabilization of the climate impact of aviation at 2019 levels\n"
            "- 3.8%: grandfathering approach (historical share of climate impacts over 1750-2018)\n"
            "- 5.1%: grandfathering approach (recent share of climate impacts over 2000-2018)\n"
            "- 15%: share consumed in terms of remaining temperature increase in the BAU scenario "
            "\n   for +1.8°C from Klower et al. (2021)",
        )
        self.w_equivalent_carbon_budget_allocation.observe(self.update, "value")

        self.w_biomass_allocation = widgets.SelectionSlider(
            options=["0%", "2.3%", "7.5%", "14.7%"],
            value="2.3%",
            description="Biomass",
            description_tooltip="Share of the world biomass resources allocated to aviation\nThe term allocation here "
            "refers to the result of complex mechanisms of negotiation, \ncompetition, "
            "arbitration and regulation for access to resources\n- 0%: no biomass resources are "
            "dedicated to aviation\n- 2.3%: grandfathering approach "
            "(current share of energy consumption)\n- 7.5%: grandfathering approach "
            "(current share of oil consumption)\n- 14.7%: share consumed in the IEA Net Zero 2050 "
            "scenario, corresponding to 15 EJ",
        )
        self.w_biomass_allocation.observe(self.update, "value")

        self.w_electricity_allocation = widgets.SelectionSlider(
            options=["0%", "2.3%", "7.5%", "15.0%"],
            value="2.3%",
            description="Electricity",
            description_tooltip="Share of the world electricity resources allocated to aviation\nThe term allocation "
            "here refers to the result of complex mechanisms of negotiation, \ncompetition, "
            "arbitration and regulation for access to resources\n- 0%: no electricity resources "
            "are dedicated to aviation\n- 2.3%: grandfathering approach "
            "(current share of energy consumption)\n- 7.5%: grandfathering approach "
            "(current share of oil consumption)\n- 15.0%: share consumed in an ambitious "
            "electricity-based scenario using\n   Hydrogen-powered aviation report data",
        )
        self.w_electricity_allocation.observe(self.update, "value")

        # Others (under construction)

        self.w_economic_use = widgets.Checkbox(
            value=False,
            description="Carbon offsetting at 2019 level",
            layout={"width": "max-content"},
        )
        self.w_economic_use.observe(self.update, "value")

        # Aviation

        air_traffic = widgets.VBox(
            [
                widgets.VBox(
                    [widgets.HTML(value="<i>Air traffic</i>")],
                    layout={"align_items": "center"},
                ),
                widgets.VBox(
                    [
                        self.w_grouped_market,
                        self.w_growth_short_range_percent,
                        self.w_growth_medium_range_percent,
                        self.w_growth_long_range_percent,
                        self.w_growth_freight_percent,
                        self.w_short_range_reduction,
                        self.w_social_measure,
                    ]
                ),
            ]
        )

        energy_intensity = widgets.VBox(
            [
                widgets.VBox(
                    [widgets.HTML(value="<i>Aircraft fleet and operations</i>")],
                    layout={"align_items": "center"},
                ),
                widgets.VBox(
                    [
                        self.w_aircraft_efficiency,
                        self.w_operations,
                        self.w_load_factor,
                        self.w_turboprop,
                        self.w_contrails_avoidance,
                    ]
                ),
            ]
        )

        carbon_intensity = widgets.VBox(
            [
                widgets.VBox(
                    [widgets.HTML(value="<i>Aircraft energy</i>")],
                    layout={"align_items": "center"},
                ),
                widgets.VBox(
                    [
                        self.w_energy_mix,
                        self.w_hydrogen_aircraft,
                        self.w_biofuel_production,
                        self.w_hydrogen_production,
                        self.w_electricity_production,
                    ]
                ),
            ]
        )

        self.aviation = widgets.VBox(
            [
                widgets.HTML(value="<b>Aviation settings</b>"),
                widgets.HBox([air_traffic, energy_intensity, carbon_intensity]),
            ],
            layout={"align_items": "center"},
        )
        self.aviation.layout.display = "flex"
        self.aviation.layout.width = "58%"

        # Environment

        climate_energy = widgets.VBox(
            [
                widgets.VBox(
                    [widgets.HTML(value="<i>Climate & Energy</i>")],
                    layout={"align_items": "center"},
                ),
                widgets.VBox(
                    [
                        self.w_temperature,
                        self.w_success_percentage,
                        self.w_cdr,
                        self.w_biomass_available,
                        self.w_electricity_available,
                    ]
                ),
            ]
        )

        allocations = widgets.VBox(
            [
                widgets.VBox(
                    [widgets.HTML(value="<i>Allocations</i>")],
                    layout={"align_items": "center"},
                ),
                widgets.VBox(
                    [
                        self.w_carbon_budget_allocation,
                        self.w_equivalent_carbon_budget_allocation,
                        self.w_biomass_allocation,
                        self.w_electricity_allocation,
                    ]
                ),
            ]
        )

        self.environment = widgets.VBox(
            [
                widgets.HTML(value="<b>Environmental settings</b>"),
                widgets.HBox([climate_energy, allocations]),
            ],
            layout={"align_items": "center"},
        )
        self.environment.layout.display = "flex"
        self.environment.layout.width = "38%"

        self.w_file_input = widgets.FileUpload(
            accept=".xlsx",  # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
            multiple=False,  # True to accept multiple files upload else False
        )
        self.w_file_input.observe(self._upload_file, "value")

        self.w_file_delete = widgets.Button(
            description="Delete",
            disabled=False,
            button_style="warning",  # 'success', 'info', 'warning', 'danger' or ''
            tooltip="Delete the selected file",
            icon="delete",
        )

        self.w_file_output = widgets.Button(
            description="Download",
            disabled=False,
            button_style="",  # 'success', 'info', 'warning', 'danger' or ''
            tooltip="Download impacts",
            icon="download",
        )

        self.download_output = widgets.Output()

        self.w_file_output.on_click(self._download_results)

        self.w_figure_download = widgets.Button(
            description="Download",
            disabled=False,
            button_style="",  # 'success', 'info', 'warning', 'danger' or ''
            tooltip="Download figures",
            icon="download",
        )

        self.w_figure_download.on_click(self._download_figures)

        self.w_expert_select_file = widgets.Select(
            options=self._data_files.keys(),
            value=next(iter(self._data_files)),
            # rows=10,
            description="Fichiers :",
            disabled=False,
        )
        self.w_expert_select_file.observe(self.update, "value")

        self.w_reset_manual = widgets.Button(
            description="Reset",
            disabled=False,
            button_style="",  # 'success', 'info', 'warning', 'danger' or ''
            tooltip="Reset manual",
            icon="reset",
        )

        self.w_file_in_out = widgets.VBox(
            [widgets.HBox([self.w_file_input, self.w_file_delete]), self.w_expert_select_file]
        )

        self.w_accordion = widgets.Accordion(
            children=[
                widgets.Label("Make your first scenario with sliders"),
                widgets.VBox(
                    [
                        widgets.Label("Choose directly a scenario"),
                        self.w_action_scenarios,
                    ]
                ),
                widgets.VBox(
                    [
                        widgets.Label("Create detailed scenarios"),
                        widgets.HTML(
                            value="<p style='padding: 10px; border: 3px solid black;'><a "
                            "href=https://mybinder.org/v2/gh/AeroMAPS/AeroMAPS/HEAD?labpath=aeromaps%2Fnotebooks%2Fbasic_example.ipynb "
                            "target='_blank'> <b>Jupyter Notebooks</b></a></p>",
                        ),
                    ]
                ),
            ]
        )
        self.w_accordion.set_title(0, "Discovery")
        self.w_accordion.set_title(1, "Scenarios")
        self.w_accordion.set_title(2, "Advanced")

        self.w_accordion.observe(self.update, "selected_index")
        self.w_accordion.observe(self._mode_deactivate, "selected_index")
        self.w_accordion.observe(self._update_scenario_infos, "selected_index")

        scenarios = widgets.VBox([widgets.HTML(value="<b>Modes of use</b>"), self.w_accordion])

        scenarios.layout.display = "flex"
        scenarios.layout.align_items = "center"
        scenarios.layout.width = "15%"

        self.controls = widgets.HBox([scenarios, self.aviation, self.environment])
        self.controls.layout = make_box_layout()
        self.controls.layout.align_items = "flex-start"

    def _update_scenario_infos(self, change=True):
        desc = ""
        title = ""
        if self.w_accordion.selected_index == 1:
            if self.w_language.value == "English":
                title = "Description of the Scenarios mode"
                if self.w_action_scenarios.value == "Example scenario":
                    desc = (
                        "This mode allows displaying scenarios that have already been defined and parameterized. "
                        "However, this mode is under construction in order to establish an exhaustive scenario "
                        "database. An example is nevertheless provided, based on a scenario published in an "
                        "<u><a href='https://arc.aiaa.org/doi/abs/10.2514/6.2023-2328' target='_blank'>academic "
                        "paper</a></u>."
                    )

            children = list(self.controls.children)

            w_desc = widgets.VBox(
                [widgets.HTML(value="<b>" + title + "</b>"), widgets.HTML(value=desc)],
                layout={"align_items": "center"},
            )
            w_desc.layout.display = "flex"
            w_desc.layout.width = "60%"
            w_desc.layout.align_center = "center"
            children[1] = w_desc
            children[2] = self.environment
            self.controls.children = tuple(children)

        elif self.w_accordion.selected_index == 2:
            if self.w_language.value == "English":
                title = "Description of the Advanced mode"
                desc = (
                    "This mode allows manipulating in detail the AeroMAPS framework using Jupyter Notebooks. "
                    "For directly using it, click on the 'Jupyter Notebooks' button on the left of the screen. "
                    "For a thorough use, you can also directly access the code source on a "
                    " <u><a href='https://github.com/AeroMAPS/AeroMAPS' target='_blank'>GitHub repository</a></u>."
                )

            children = list(self.controls.children)

            w_desc = widgets.VBox(
                [widgets.HTML(value="<b>" + title + "</b>"), widgets.HTML(value=desc)],
                layout={"align_items": "center"},
            )
            w_desc.layout.display = "flex"
            w_desc.layout.width = "60%"
            w_desc.layout.align_center = "center"
            w_desc_blank = widgets.VBox(
                [widgets.HTML(""), widgets.HTML(value="")],
                layout={"align_items": "center"},
            )
            children[1] = w_desc
            children[2] = w_desc_blank
            self.controls.children = tuple(children)

        else:
            children = list(self.controls.children)
            children[1] = self.aviation
            children[2] = self.environment
            self.controls.children = tuple(children)

    def _mode_deactivate(self, change=None):
        pass

    def _upload_file(self, change=None):
        data = self.w_file_input.value
        file_name = list(data.keys())[0]
        # if file_name not in self._data_files:
        parts = file_name.split(".")
        if ".xlsx" in file_name and parts[-1] == "xlsx":
            file_data = data[file_name]
            file_path = pth.join(DATA_FOLDER, file_name)
            with open(file_path, "w+b") as i:
                i.write(file_data["content"])
            self._load_data(file_name)
            data.pop(file_name)
            os.remove(file_path)

            # Adding filename to available data files
            # self._data_filenames.append(file_name)
            self.w_expert_select_file.options = self._data_files.keys()

    def _create_graphs(self):
        self._create_graph_1_en(None)
        self._create_graph_2_en(None)
        self._create_graph_3_en(None)

        self._create_graph12_output()

    def _create_graph_1_en(self, change):
        # TODO: convert to french
        if self.out1:
            plt.close(fig=self.fig1.fig)
            self.out1.clear_output(wait=True)
        else:
            self.out1 = widgets.Output()
        with self.out1:
            plt.ioff()
            self.fig1 = plot_1[self.graph1.value](self.process.data)
            display(self.fig1.fig.canvas)

    def _create_graph_2_en(self, change):
        # TODO: convert to french
        if self.out2:
            plt.close(fig=self.fig2.fig)
            self.out2.clear_output(wait=True)
        else:
            self.out2 = widgets.Output()
        with self.out2:
            plt.ioff()
            self.fig2 = plot_2[self.graph2.value](self.process.data)
            display(self.fig2.fig.canvas)

    def _create_graph_3_en(self, change):
        # TODO: convert to french
        if self.out3:
            plt.close(fig=self.fig3.fig)
            self.out3.clear_output(wait=True)
        else:
            self.out3 = widgets.Output()
        with self.out3:
            plt.ioff()
            self.fig3 = plot_3[self.graph3.value](self.process.data)
            display(self.fig3.fig.canvas)

    def _create_graph12_output(self):
        if self.w_language.value == "English":
            desc = (
                '<p align="center"> The simulated scenario can be set using <b>Aviation settings</b>.'
                "<br>The world environmental budget can be set using <b>Environmental settings</b>.</p>"
            )
        else:
            desc = (
                '<p align="center"> Le scénario simulé peut être réglée via les <b>Réglages Aviation</b>.'
                "<br>Le budget environnemental mondial peut être réglé via les <b>Réglages Environnement</b>.</p>"
            )

        fig1 = widgets.VBox([self.graph1, self.out1])
        fig1.layout = make_box_layout()
        fig1.layout.width = "50%"
        fig2 = widgets.VBox(
            [
                self.graph2,
                self.out2,
                widgets.HTML(value=desc),
            ]
        )
        fig2.layout = make_box_layout()
        fig2.layout.width = "25%"
        fig3 = widgets.VBox([self.graph3, self.out3])
        fig3.layout = make_box_layout()
        fig3.layout.width = "25%"

        self.graphs = widgets.HBox([fig1, fig2, fig3])
        self.graphs.layout = widgets.Layout(width="auto", display="flex")

    def update(self, change):
        self._update_controls()
        self.process.compute()
        self.process.compute()
        self._update_plots()

    def _update_controls(self):

        # DISCOVERY

        # Traffic
        if self.w_grouped_market.value == False:
            self.process.parameters.cagr_passenger_short_range_reference_periods_values = [
                self.w_growth_short_range_percent.value
            ]
            self.process.parameters.cagr_passenger_medium_range_reference_periods_values = [
                self.w_growth_medium_range_percent.value
            ]
            self.process.parameters.cagr_passenger_long_range_reference_periods_values = [
                self.w_growth_long_range_percent.value
            ]
            self.process.parameters.cagr_freight_reference_periods_values = [
                self.w_growth_freight_percent.value
            ]
            self.w_growth_medium_range_percent.disabled = False
            self.w_growth_long_range_percent.disabled = False
            self.w_growth_freight_percent.disabled = False
        else:
            self.process.parameters.cagr_passenger_short_range_reference_periods_values = [
                self.w_growth_short_range_percent.value
            ]
            self.process.parameters.cagr_passenger_medium_range_reference_periods_values = [
                self.w_growth_short_range_percent.value
            ]
            self.process.parameters.cagr_passenger_long_range_reference_periods = [
                self.w_growth_short_range_percent.value
            ]
            self.process.parameters.cagr_freight_reference_periods = [
                self.w_growth_short_range_percent.value
            ]
            self.w_growth_medium_range_percent.disabled = True
            self.w_growth_medium_range_percent.value = self.w_growth_short_range_percent.value
            self.w_growth_long_range_percent.disabled = True
            self.w_growth_long_range_percent.value = self.w_growth_short_range_percent.value
            self.w_growth_freight_percent.disabled = True
            self.w_growth_freight_percent.value = self.w_growth_short_range_percent.value

        if self.w_short_range_reduction.value == False and self.w_social_measure.value == False:
            self.process.parameters.rpk_short_range_measures_final_impact = 0.0
            self.process.parameters.rpk_medium_range_measures_final_impact = 0.0
            self.process.parameters.rpk_long_range_measures_final_impact = 0.0
            self.process.parameters.rpk_short_range_measures_start_year = 2051
            self.process.parameters.rpk_medium_range_measures_start_year = 2051
            self.process.parameters.rpk_long_range_measures_start_year = 2051
            self.process.parameters.rpk_short_range_measures_duration = 5.0
            self.process.parameters.rpk_medium_range_measures_duration = 5.0
            self.process.parameters.rpk_long_range_measures_duration = 5.0
        elif self.w_short_range_reduction.value == True and self.w_social_measure.value == False:
            self.process.parameters.rpk_short_range_measures_final_impact = 50.0
            self.process.parameters.rpk_medium_range_measures_final_impact = 0.0
            self.process.parameters.rpk_long_range_measures_final_impact = 0.0
            self.process.parameters.rpk_short_range_measures_start_year = 2025
            self.process.parameters.rpk_medium_range_measures_start_year = 2051
            self.process.parameters.rpk_long_range_measures_start_year = 2051
            self.process.parameters.rpk_short_range_measures_duration = 5.0
            self.process.parameters.rpk_medium_range_measures_duration = 5.0
            self.process.parameters.rpk_long_range_measures_duration = 5.0
        elif self.w_short_range_reduction.value == False and self.w_social_measure.value == True:
            self.process.parameters.rpk_short_range_measures_final_impact = 25.0
            self.process.parameters.rpk_medium_range_measures_final_impact = 25.0
            self.process.parameters.rpk_long_range_measures_final_impact = 25.0
            self.process.parameters.rpk_short_range_measures_start_year = 2025
            self.process.parameters.rpk_medium_range_measures_start_year = 2025
            self.process.parameters.rpk_long_range_measures_start_year = 2025
            self.process.parameters.rpk_short_range_measures_duration = 5.0
            self.process.parameters.rpk_medium_range_measures_duration = 5.0
            self.process.parameters.rpk_long_range_measures_duration = 5.0
        else:
            self.process.parameters.rpk_short_range_measures_final_impact = 62.5
            self.process.parameters.rpk_medium_range_measures_final_impact = 25.0
            self.process.parameters.rpk_long_range_measures_final_impact = 25.0
            self.process.parameters.rpk_short_range_measures_start_year = 2025
            self.process.parameters.rpk_medium_range_measures_start_year = 2025
            self.process.parameters.rpk_long_range_measures_start_year = 2025
            self.process.parameters.rpk_short_range_measures_duration = 5.0
            self.process.parameters.rpk_medium_range_measures_duration = 5.0
            self.process.parameters.rpk_long_range_measures_duration = 5.0

        # Energy intensity

        # Fleet renewal: sliders links
        if self.w_aircraft_efficiency.value == "Renewal":
            self.w_hydrogen_aircraft.value = "Absence"
            self.w_hydrogen_aircraft.disabled = True
            self.w_turboprop.value = False
            self.w_turboprop.disabled = True
        else:
            self.w_hydrogen_aircraft.disabled = False
            self.w_turboprop.disabled = False

        # Fleet renewal: sliders settings

        if self.w_aircraft_efficiency.value == "Renewal":
            self.process.fleet._build_default_fleet(add_examples_aircraft_and_subcategory=False)
            self.process.fleet.categories["Short Range"].parameters.life = 25
            self.process.fleet.categories["Medium Range"].parameters.life = 25
            self.process.fleet.categories["Long Range"].parameters.life = 25

        elif self.w_aircraft_efficiency.value == "Trend" and self.w_turboprop.value == False:
            self.process.fleet._build_default_fleet(add_examples_aircraft_and_subcategory=False)
            short_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2035,
                consumption_evolution=-20.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            short_range_aircraft1 = Aircraft(
                "New Short-range Aircraft 1",
                parameters=short_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Short Range"].subcategories[0].add_aircraft(
                aircraft=short_range_aircraft1
            )
            short_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2045,
                consumption_evolution=-35.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            short_range_aircraft2 = Aircraft(
                "New Short-range Aircraft 2",
                parameters=short_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Short Range"].subcategories[0].add_aircraft(
                aircraft=short_range_aircraft2
            )
            medium_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2035,
                consumption_evolution=-20.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            medium_range_aircraft1 = Aircraft(
                "New Medium-range Aircraft 1",
                parameters=medium_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Medium Range"].subcategories[0].add_aircraft(
                aircraft=medium_range_aircraft1
            )
            medium_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2045,
                consumption_evolution=-35.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            medium_range_aircraft2 = Aircraft(
                "New Medium-range Aircraft 2",
                parameters=medium_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Medium Range"].subcategories[0].add_aircraft(
                aircraft=medium_range_aircraft2
            )
            long_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2035,
                consumption_evolution=-20.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            long_range_aircraft1 = Aircraft(
                "New Short-range Aircraft 1",
                parameters=long_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Long Range"].subcategories[0].add_aircraft(
                aircraft=long_range_aircraft1
            )
            long_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2045,
                consumption_evolution=-35.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            long_range_aircraft2 = Aircraft(
                "New Long-range Aircraft 2",
                parameters=long_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Long Range"].subcategories[0].add_aircraft(
                aircraft=long_range_aircraft2
            )

            self.process.fleet.categories["Short Range"].parameters.life = 25
            self.process.fleet.categories["Medium Range"].parameters.life = 25
            self.process.fleet.categories["Long Range"].parameters.life = 25

        elif self.w_aircraft_efficiency.value == "Accelerated" and self.w_turboprop.value == False:
            self.process.fleet._build_default_fleet(add_examples_aircraft_and_subcategory=False)
            short_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2035,
                consumption_evolution=-20.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            short_range_aircraft1 = Aircraft(
                "New Short-range Aircraft 1",
                parameters=short_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Short Range"].subcategories[0].add_aircraft(
                aircraft=short_range_aircraft1
            )
            short_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2045,
                consumption_evolution=-35.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            short_range_aircraft2 = Aircraft(
                "New Short-range Aircraft 2",
                parameters=short_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Short Range"].subcategories[0].add_aircraft(
                aircraft=short_range_aircraft2
            )
            medium_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2035,
                consumption_evolution=-20.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            medium_range_aircraft1 = Aircraft(
                "New Medium-range Aircraft 1",
                parameters=medium_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Medium Range"].subcategories[0].add_aircraft(
                aircraft=medium_range_aircraft1
            )
            medium_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2045,
                consumption_evolution=-35.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            medium_range_aircraft2 = Aircraft(
                "New Medium-range Aircraft 2",
                parameters=medium_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Medium Range"].subcategories[0].add_aircraft(
                aircraft=medium_range_aircraft2
            )
            long_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2035,
                consumption_evolution=-20.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            long_range_aircraft1 = Aircraft(
                "New Short-range Aircraft 1",
                parameters=long_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Long Range"].subcategories[0].add_aircraft(
                aircraft=long_range_aircraft1
            )
            long_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2045,
                consumption_evolution=-35.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            long_range_aircraft2 = Aircraft(
                "New Long-range Aircraft 2",
                parameters=long_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Long Range"].subcategories[0].add_aircraft(
                aircraft=long_range_aircraft2
            )

            self.process.fleet.categories["Short Range"].parameters.life = 20
            self.process.fleet.categories["Medium Range"].parameters.life = 20
            self.process.fleet.categories["Long Range"].parameters.life = 20

        elif self.w_aircraft_efficiency.value == "Ambitious" and self.w_turboprop.value == False:
            self.process.fleet._build_default_fleet(add_examples_aircraft_and_subcategory=False)
            short_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2030,
                consumption_evolution=-15.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            short_range_aircraft1 = Aircraft(
                "New Short-range Aircraft 1",
                parameters=short_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Short Range"].subcategories[0].add_aircraft(
                aircraft=short_range_aircraft1
            )
            short_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2040,
                consumption_evolution=-40.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            short_range_aircraft2 = Aircraft(
                "New Short-range Aircraft 2",
                parameters=short_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Short Range"].subcategories[0].add_aircraft(
                aircraft=short_range_aircraft2
            )
            medium_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2030,
                consumption_evolution=-15.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            medium_range_aircraft1 = Aircraft(
                "New Medium-range Aircraft 1",
                parameters=medium_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Medium Range"].subcategories[0].add_aircraft(
                aircraft=medium_range_aircraft1
            )
            medium_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2040,
                consumption_evolution=-40.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            medium_range_aircraft2 = Aircraft(
                "New Medium-range Aircraft 2",
                parameters=medium_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Medium Range"].subcategories[0].add_aircraft(
                aircraft=medium_range_aircraft2
            )
            long_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2030,
                consumption_evolution=-15.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            long_range_aircraft1 = Aircraft(
                "New Short-range Aircraft 1",
                parameters=long_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Long Range"].subcategories[0].add_aircraft(
                aircraft=long_range_aircraft1
            )
            long_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2040,
                consumption_evolution=-40.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            long_range_aircraft2 = Aircraft(
                "New Long-range Aircraft 2",
                parameters=long_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Long Range"].subcategories[0].add_aircraft(
                aircraft=long_range_aircraft2
            )

            self.process.fleet.categories["Short Range"].parameters.life = 20
            self.process.fleet.categories["Medium Range"].parameters.life = 20
            self.process.fleet.categories["Long Range"].parameters.life = 20

        elif self.w_aircraft_efficiency.value == "Trend" and self.w_turboprop.value == True:
            self.process.fleet._build_default_fleet(add_examples_aircraft_and_subcategory=False)
            short_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2035,
                consumption_evolution=-35.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=10.0,
                cruise_altitude=6000.0,
            )
            short_range_aircraft1 = Aircraft(
                "New Short-range Aircraft 1",
                parameters=short_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Short Range"].subcategories[0].add_aircraft(
                aircraft=short_range_aircraft1
            )
            short_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2045,
                consumption_evolution=-45.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=10.0,
                cruise_altitude=6000.0,
            )
            short_range_aircraft2 = Aircraft(
                "New Short-range Aircraft 2",
                parameters=short_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Short Range"].subcategories[0].add_aircraft(
                aircraft=short_range_aircraft2
            )
            medium_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2035,
                consumption_evolution=-35.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=10.0,
                cruise_altitude=6000.0,
            )
            medium_range_aircraft1 = Aircraft(
                "New Medium-range Aircraft 1",
                parameters=medium_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Medium Range"].subcategories[0].add_aircraft(
                aircraft=medium_range_aircraft1
            )
            medium_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2045,
                consumption_evolution=-45.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=10.0,
                cruise_altitude=6000.0,
            )
            medium_range_aircraft2 = Aircraft(
                "New Medium-range Aircraft 2",
                parameters=medium_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Medium Range"].subcategories[0].add_aircraft(
                aircraft=medium_range_aircraft2
            )
            long_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2035,
                consumption_evolution=-20.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            long_range_aircraft1 = Aircraft(
                "New Short-range Aircraft 1",
                parameters=long_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Long Range"].subcategories[0].add_aircraft(
                aircraft=long_range_aircraft1
            )
            long_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2045,
                consumption_evolution=-35.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            long_range_aircraft2 = Aircraft(
                "New Long-range Aircraft 2",
                parameters=long_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Long Range"].subcategories[0].add_aircraft(
                aircraft=long_range_aircraft2
            )

            self.process.fleet.categories["Short Range"].parameters.life = 25
            self.process.fleet.categories["Medium Range"].parameters.life = 25
            self.process.fleet.categories["Long Range"].parameters.life = 25

        elif self.w_aircraft_efficiency.value == "Accelerated" and self.w_turboprop.value == True:
            self.process.fleet._build_default_fleet(add_examples_aircraft_and_subcategory=False)
            short_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2035,
                consumption_evolution=-35.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=10.0,
                cruise_altitude=6000.0,
            )
            print(short_range_aircraft1_params)
            short_range_aircraft1 = Aircraft(
                "New Short-range Aircraft 1",
                parameters=short_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Short Range"].subcategories[0].add_aircraft(
                aircraft=short_range_aircraft1
            )
            short_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2045,
                consumption_evolution=-45.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=10.0,
                cruise_altitude=6000.0,
            )
            short_range_aircraft2 = Aircraft(
                "New Short-range Aircraft 2",
                parameters=short_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Short Range"].subcategories[0].add_aircraft(
                aircraft=short_range_aircraft2
            )
            medium_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2035,
                consumption_evolution=-35.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=10.0,
                cruise_altitude=6000.0,
            )
            medium_range_aircraft1 = Aircraft(
                "New Medium-range Aircraft 1",
                parameters=medium_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Medium Range"].subcategories[0].add_aircraft(
                aircraft=medium_range_aircraft1
            )
            medium_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2045,
                consumption_evolution=-45.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=10.0,
                cruise_altitude=6000.0,
            )
            medium_range_aircraft2 = Aircraft(
                "New Medium-range Aircraft 2",
                parameters=medium_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Medium Range"].subcategories[0].add_aircraft(
                aircraft=medium_range_aircraft2
            )
            long_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2035,
                consumption_evolution=-20.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            long_range_aircraft1 = Aircraft(
                "New Short-range Aircraft 1",
                parameters=long_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Long Range"].subcategories[0].add_aircraft(
                aircraft=long_range_aircraft1
            )
            long_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2045,
                consumption_evolution=-35.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            long_range_aircraft2 = Aircraft(
                "New Long-range Aircraft 2",
                parameters=long_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Long Range"].subcategories[0].add_aircraft(
                aircraft=long_range_aircraft2
            )

            self.process.fleet.categories["Short Range"].parameters.life = 20
            self.process.fleet.categories["Medium Range"].parameters.life = 20
            self.process.fleet.categories["Long Range"].parameters.life = 20

        elif self.w_aircraft_efficiency.value == "Ambitious" and self.w_turboprop.value == True:
            self.process.fleet._build_default_fleet(add_examples_aircraft_and_subcategory=False)
            short_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2030,
                consumption_evolution=-30.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=10.0,
                cruise_altitude=6000.0,
            )
            short_range_aircraft1 = Aircraft(
                "New Short-range Aircraft 1",
                parameters=short_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Short Range"].subcategories[0].add_aircraft(
                aircraft=short_range_aircraft1
            )
            short_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2040,
                consumption_evolution=-50.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=10.0,
                cruise_altitude=6000.0,
            )
            short_range_aircraft2 = Aircraft(
                "New Short-range Aircraft 2",
                parameters=short_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Short Range"].subcategories[0].add_aircraft(
                aircraft=short_range_aircraft2
            )
            medium_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2030,
                consumption_evolution=-30.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=10.0,
                cruise_altitude=6000.0,
            )
            medium_range_aircraft1 = Aircraft(
                "New Medium-range Aircraft 1",
                parameters=medium_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Medium Range"].subcategories[0].add_aircraft(
                aircraft=medium_range_aircraft1
            )
            medium_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2040,
                consumption_evolution=-50.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=10.0,
                cruise_altitude=6000.0,
            )
            medium_range_aircraft2 = Aircraft(
                "New Medium-range Aircraft 2",
                parameters=medium_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Medium Range"].subcategories[0].add_aircraft(
                aircraft=medium_range_aircraft2
            )
            long_range_aircraft1_params = AircraftParameters(
                entry_into_service_year=2030,
                consumption_evolution=-15.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            long_range_aircraft1 = Aircraft(
                "New Short-range Aircraft 1",
                parameters=long_range_aircraft1_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Long Range"].subcategories[0].add_aircraft(
                aircraft=long_range_aircraft1
            )
            long_range_aircraft2_params = AircraftParameters(
                entry_into_service_year=2040,
                consumption_evolution=-40.0,
                nox_evolution=0.0,
                soot_evolution=0.0,
                doc_non_energy_evolution=0.0,
                cruise_altitude=12000.0,
            )
            long_range_aircraft2 = Aircraft(
                "New Long-range Aircraft 2",
                parameters=long_range_aircraft2_params,
                energy_type="DROP_IN_FUEL",
            )
            self.process.fleet.categories["Long Range"].subcategories[0].add_aircraft(
                aircraft=long_range_aircraft2
            )

            self.process.fleet.categories["Short Range"].parameters.life = 20
            self.process.fleet.categories["Medium Range"].parameters.life = 20
            self.process.fleet.categories["Long Range"].parameters.life = 20

        # Hydrogen
        if self.w_turboprop.value == False:
            if self.w_hydrogen_aircraft.value == "Limited":
                self.process.fleet.categories["Short Range"].subcategories[
                    0
                ].parameters.share = 50.0
                sr_subcat_params = SubcategoryParameters(share=50.0)
                sr_subcat_hydrogen = SubCategory("SR hydrogen", parameters=sr_subcat_params)
                self.process.fleet.categories["Short Range"].add_subcategory(
                    subcategory=sr_subcat_hydrogen
                )
                short_range_aircraft_hydrogen_params = AircraftParameters(
                    entry_into_service_year=2040,
                    consumption_evolution=0.0,
                    nox_evolution=0.0,
                    soot_evolution=-100.0,
                    doc_non_energy_evolution=10.0,
                    cruise_altitude=12000.0,
                )
                short_range_aircraft_hydrogen = Aircraft(
                    "New Short-range Hydrogen Aircraft",
                    parameters=short_range_aircraft_hydrogen_params,
                    energy_type="HYDROGEN",
                )
                self.process.fleet.categories["Short Range"].subcategories[1].add_aircraft(
                    aircraft=short_range_aircraft_hydrogen
                )
            elif self.w_hydrogen_aircraft.value == "Moderate":
                self.process.fleet.categories["Short Range"].subcategories[
                    0
                ].parameters.share = 50.0
                sr_subcat_params = SubcategoryParameters(share=50.0)
                sr_subcat_hydrogen = SubCategory("SR hydrogen", parameters=sr_subcat_params)
                self.process.fleet.categories["Short Range"].add_subcategory(
                    subcategory=sr_subcat_hydrogen
                )
                short_range_aircraft_hydrogen_params = AircraftParameters(
                    entry_into_service_year=2035,
                    consumption_evolution=0.0,
                    nox_evolution=0.0,
                    soot_evolution=-100.0,
                    doc_non_energy_evolution=10.0,
                    cruise_altitude=12000.0,
                )
                short_range_aircraft_hydrogen = Aircraft(
                    "New Short-range Hydrogen Aircraft",
                    parameters=short_range_aircraft_hydrogen_params,
                    energy_type="HYDROGEN",
                )
                self.process.fleet.categories["Short Range"].subcategories[1].add_aircraft(
                    aircraft=short_range_aircraft_hydrogen
                )
            elif self.w_hydrogen_aircraft.value == "Ambitious":
                self.process.fleet.categories["Short Range"].subcategories[
                    0
                ].parameters.share = 50.0
                sr_subcat_params = SubcategoryParameters(share=50.0)
                sr_subcat_hydrogen = SubCategory("SR hydrogen", parameters=sr_subcat_params)
                self.process.fleet.categories["Short Range"].add_subcategory(
                    subcategory=sr_subcat_hydrogen
                )
                short_range_aircraft_hydrogen_params = AircraftParameters(
                    entry_into_service_year=2035,
                    consumption_evolution=-15.0,
                    nox_evolution=0.0,
                    soot_evolution=-100.0,
                    doc_non_energy_evolution=10.0,
                    cruise_altitude=12000.0,
                )
                short_range_aircraft_hydrogen = Aircraft(
                    "New Short-range Hydrogen Aircraft",
                    parameters=short_range_aircraft_hydrogen_params,
                    energy_type="HYDROGEN",
                )
                self.process.fleet.categories["Short Range"].subcategories[1].add_aircraft(
                    aircraft=short_range_aircraft_hydrogen
                )
                self.process.fleet.categories["Medium Range"].subcategories[
                    0
                ].parameters.share = 50.0
                mr_subcat_params = SubcategoryParameters(share=50.0)
                mr_subcat_hydrogen = SubCategory("SR hydrogen", parameters=mr_subcat_params)
                self.process.fleet.categories["Medium Range"].add_subcategory(
                    subcategory=mr_subcat_hydrogen
                )
                medium_range_aircraft_hydrogen_params = AircraftParameters(
                    entry_into_service_year=2035,
                    consumption_evolution=-15.0,
                    nox_evolution=0.0,
                    soot_evolution=-100.0,
                    doc_non_energy_evolution=10.0,
                    cruise_altitude=12000.0,
                )
                medium_range_aircraft_hydrogen = Aircraft(
                    "New Medium-range Hydrogen Aircraft",
                    parameters=medium_range_aircraft_hydrogen_params,
                    energy_type="HYDROGEN",
                )
                self.process.fleet.categories["Medium Range"].subcategories[1].add_aircraft(
                    aircraft=medium_range_aircraft_hydrogen
                )
        elif self.w_turboprop.value == True:
            if self.w_hydrogen_aircraft.value == "Limited":
                self.process.fleet.categories["Short Range"].subcategories[
                    0
                ].parameters.share = 50.0
                sr_subcat_params = SubcategoryParameters(share=50.0)
                sr_subcat_hydrogen = SubCategory("SR hydrogen", parameters=sr_subcat_params)
                self.process.fleet.categories["Short Range"].add_subcategory(
                    subcategory=sr_subcat_hydrogen
                )
                short_range_aircraft_hydrogen_params = AircraftParameters(
                    entry_into_service_year=2040,
                    consumption_evolution=-15.0,
                    nox_evolution=0.0,
                    soot_evolution=-100.0,
                    doc_non_energy_evolution=20.0,
                    cruise_altitude=6000.0,
                )
                short_range_aircraft_hydrogen = Aircraft(
                    "New Short-range Hydrogen Aircraft",
                    parameters=short_range_aircraft_hydrogen_params,
                    energy_type="HYDROGEN",
                )
                self.process.fleet.categories["Short Range"].subcategories[1].add_aircraft(
                    aircraft=short_range_aircraft_hydrogen
                )
            elif self.w_hydrogen_aircraft.value == "Moderate":
                self.process.fleet.categories["Short Range"].subcategories[
                    0
                ].parameters.share = 50.0
                sr_subcat_params = SubcategoryParameters(share=50.0)
                sr_subcat_hydrogen = SubCategory("SR hydrogen", parameters=sr_subcat_params)
                self.process.fleet.categories["Short Range"].add_subcategory(
                    subcategory=sr_subcat_hydrogen
                )
                short_range_aircraft_hydrogen_params = AircraftParameters(
                    entry_into_service_year=2035,
                    consumption_evolution=-15.0,
                    nox_evolution=0.0,
                    soot_evolution=-100.0,
                    doc_non_energy_evolution=20.0,
                    cruise_altitude=6000.0,
                )
                short_range_aircraft_hydrogen = Aircraft(
                    "New Short-range Hydrogen Aircraft",
                    parameters=short_range_aircraft_hydrogen_params,
                    energy_type="HYDROGEN",
                )
                self.process.fleet.categories["Short Range"].subcategories[1].add_aircraft(
                    aircraft=short_range_aircraft_hydrogen
                )
            elif self.w_hydrogen_aircraft.value == "Ambitious":
                self.process.fleet.categories["Short Range"].subcategories[
                    0
                ].parameters.share = 50.0
                sr_subcat_params = SubcategoryParameters(share=50.0)
                sr_subcat_hydrogen = SubCategory("SR hydrogen", parameters=sr_subcat_params)
                self.process.fleet.categories["Short Range"].add_subcategory(
                    subcategory=sr_subcat_hydrogen
                )
                short_range_aircraft_hydrogen_params = AircraftParameters(
                    entry_into_service_year=2035,
                    consumption_evolution=-30.0,
                    nox_evolution=0.0,
                    soot_evolution=-100.0,
                    doc_non_energy_evolution=20.0,
                    cruise_altitude=6000.0,
                )
                short_range_aircraft_hydrogen = Aircraft(
                    "New Short-range Hydrogen Aircraft",
                    parameters=short_range_aircraft_hydrogen_params,
                    energy_type="HYDROGEN",
                )
                self.process.fleet.categories["Short Range"].subcategories[1].add_aircraft(
                    aircraft=short_range_aircraft_hydrogen
                )
                self.process.fleet.categories["Medium Range"].subcategories[
                    0
                ].parameters.share = 50.0
                mr_subcat_params = SubcategoryParameters(share=50.0)
                mr_subcat_hydrogen = SubCategory("SR hydrogen", parameters=mr_subcat_params)
                self.process.fleet.categories["Medium Range"].add_subcategory(
                    subcategory=mr_subcat_hydrogen
                )
                medium_range_aircraft_hydrogen_params = AircraftParameters(
                    entry_into_service_year=2035,
                    consumption_evolution=-30.0,
                    nox_evolution=0.0,
                    soot_evolution=-100.0,
                    doc_non_energy_evolution=20.0,
                    cruise_altitude=6000.0,
                )
                medium_range_aircraft_hydrogen = Aircraft(
                    "New Medium-range Hydrogen Aircraft",
                    parameters=medium_range_aircraft_hydrogen_params,
                    energy_type="HYDROGEN",
                )
                self.process.fleet.categories["Medium Range"].subcategories[1].add_aircraft(
                    aircraft=medium_range_aircraft_hydrogen
                )

        # Load factor
        if self.w_load_factor.value == "Constant":
            self.process.parameters.load_factor_end_year = 82.4
        elif self.w_load_factor.value == "Unambitious":
            self.process.parameters.load_factor_end_year = 85
        elif self.w_load_factor.value == "Trend":
            self.process.parameters.load_factor_end_year = 89
        elif self.w_load_factor.value == "Ambitious":
            self.process.parameters.load_factor_end_year = 92
        elif self.w_load_factor.value == "Very ambitious":
            self.process.parameters.load_factor_end_year = 95

        if self.w_operations.value == "Constant":
            self.process.parameters.operations_final_gain = 0
            self.process.parameters.operations_start_year = 2025
            self.process.parameters.operations_duration = 20
        elif self.w_operations.value == "Pessimistic":
            self.process.parameters.operations_final_gain = 4
            self.process.parameters.operations_start_year = 2025
            self.process.parameters.operations_duration = 20
        elif self.w_operations.value == "Realistic":
            self.process.parameters.operations_final_gain = 8
            self.process.parameters.operations_start_year = 2025
            self.process.parameters.operations_duration = 20
        elif self.w_operations.value == "Optimistic":
            self.process.parameters.operations_final_gain = 12
            self.process.parameters.operations_start_year = 2025
            self.process.parameters.operations_duration = 20
        elif self.w_operations.value == "Idealistic":
            self.process.parameters.operations_final_gain = 16
            self.process.parameters.operations_start_year = 2025
            self.process.parameters.operations_duration = 20

        if self.w_contrails_avoidance.value == True:
            self.process.parameters.operations_contrails_final_gain = 59.4  # [%]
            self.process.parameters.operations_contrails_final_overconsumption = 0.014  # [%]
            self.process.parameters.operations_contrails_start_year = 2030
            self.process.parameters.operations_contrails_duration = 15.0
        else:
            self.process.parameters.operations_contrails_final_gain = 0.0  # [%]
            self.process.parameters.operations_contrails_final_overconsumption = 0.0  # [%]
            self.process.parameters.operations_contrails_start_year = 2051
            self.process.parameters.operations_contrails_duration = 15.0

        # Carbon intensity
        if self.w_energy_mix.value == "Kerosene":
            self.process.parameters.biofuel_share_reference_years = [2020, 2030, 2040, 2050]
            self.process.parameters.biofuel_share_reference_years_values = [0.0, 0.0, 0.0, 0.0]
            self.process.parameters.electrofuel_share_reference_years = [2020, 2030, 2040, 2050]
            self.process.parameters.electrofuel_share_reference_years_values = [0.0, 0.0, 0.0, 0.0]
        elif self.w_energy_mix.value == "Biofuel":
            self.process.parameters.biofuel_share_reference_years = [2020, 2030, 2040, 2050]
            self.process.parameters.biofuel_share_reference_years_values = [0.0, 4.0, 30.0, 100.0]
            self.process.parameters.electrofuel_share_reference_years = [2020, 2030, 2040, 2050]
            self.process.parameters.electrofuel_share_reference_years_values = [0.0, 0.0, 0.0, 0.0]
        elif self.w_energy_mix.value == "Electrofuel":
            self.process.parameters.biofuel_share_reference_years = [2020, 2030, 2040, 2050]
            self.process.parameters.biofuel_share_reference_years_values = [0.0, 0.0, 0.0, 0.0]
            self.process.parameters.electrofuel_share_reference_years = [2020, 2030, 2040, 2050]
            self.process.parameters.electrofuel_share_reference_years_values = [
                0.0,
                0.0,
                25.0,
                100.0,
            ]
        elif self.w_energy_mix.value == "ReFuelEU":
            self.process.parameters.biofuel_share_reference_years = [2020, 2030, 2040, 2050]
            self.process.parameters.biofuel_share_reference_years_values = [0.0, 4.8, 24.0, 35.0]
            self.process.parameters.electrofuel_share_reference_years = [2020, 2030, 2040, 2050]
            self.process.parameters.electrofuel_share_reference_years_values = [
                0.0,
                1.2,
                10.0,
                35.0,
            ]

        if self.w_biofuel_production.value == "Current":
            self.process.parameters.biofuel_hefa_fog_share_reference_years = []
            self.process.parameters.biofuel_hefa_fog_share_reference_years_values = [100]
            self.process.parameters.biofuel_hefa_others_share_reference_years = []
            self.process.parameters.biofuel_hefa_others_share_reference_years_values = [0.0]
            self.process.parameters.biofuel_ft_others_share_reference_years = []
            self.process.parameters.biofuel_ft_others_share_reference_years_values = [0.0]
            self.process.parameters.biofuel_ft_msw_share_reference_years = []
            self.process.parameters.biofuel_ft_msw_share_reference_years_values = [0.0]
        elif self.w_biofuel_production.value == "High-carbon":
            self.process.parameters.biofuel_hefa_fog_share_reference_years = []
            self.process.parameters.biofuel_hefa_fog_share_reference_years_values = [0.0]
            self.process.parameters.biofuel_hefa_others_share_reference_years = []
            self.process.parameters.biofuel_hefa_others_share_reference_years_values = [0.0]
            self.process.parameters.biofuel_ft_others_share_reference_years = []
            self.process.parameters.biofuel_ft_others_share_reference_years_values = [0.0]
            self.process.parameters.biofuel_ft_msw_share_reference_years = []
            self.process.parameters.biofuel_ft_msw_share_reference_years_values = [0.0]
        elif self.w_biofuel_production.value == "Low-carbon":
            self.process.parameters.biofuel_hefa_fog_share_reference_years = []
            self.process.parameters.biofuel_hefa_fog_share_reference_years_values = [0.0]
            self.process.parameters.biofuel_hefa_others_share_reference_years = []
            self.process.parameters.biofuel_hefa_others_share_reference_years_values = [0.0]
            self.process.parameters.biofuel_ft_others_share_reference_years = []
            self.process.parameters.biofuel_ft_others_share_reference_years_values = [100.0]
            self.process.parameters.biofuel_ft_msw_share_reference_years = []
            self.process.parameters.biofuel_ft_msw_share_reference_years_values = [0.0]

        if self.w_hydrogen_production.value == "Current":
            self.process.parameters.hydrogen_electrolysis_share_reference_years = []
            self.process.parameters.hydrogen_electrolysis_share_reference_years_values = [2]
            self.process.parameters.hydrogen_gas_ccs_share_reference_years = []
            self.process.parameters.hydrogen_gas_ccs_share_reference_years_values = [0]
            self.process.parameters.hydrogen_coal_ccs_share_reference_years = []
            self.process.parameters.hydrogen_coal_ccs_share_reference_years_values = [0]
            self.process.parameters.hydrogen_gas_share_reference_years = []
            self.process.parameters.hydrogen_gas_share_reference_years_values = [71]
        elif self.w_hydrogen_production.value == "Gas without CCS":
            self.process.parameters.hydrogen_electrolysis_share_reference_years = []
            self.process.parameters.hydrogen_electrolysis_share_reference_years_values = []
            self.process.parameters.hydrogen_gas_ccs_share_reference_years = []
            self.process.parameters.hydrogen_gas_ccs_share_reference_years_values = [0]
            self.process.parameters.hydrogen_coal_ccs_share_reference_years = []
            self.process.parameters.hydrogen_coal_ccs_share_reference_years_values = [0]
            self.process.parameters.hydrogen_gas_share_reference_years = []
            self.process.parameters.hydrogen_gas_share_reference_years_values = [100]
        elif self.w_hydrogen_production.value == "Gas with CCS":
            self.process.parameters.hydrogen_electrolysis_share_reference_years = [2020, 2030, 2050]
            self.process.parameters.hydrogen_electrolysis_share_reference_years_values = [2, 0, 0]
            self.process.parameters.hydrogen_gas_ccs_share_reference_years = [
                2020,
                2030,
                2040,
                2050,
            ]
            self.process.parameters.hydrogen_gas_ccs_share_reference_years_values = [0, 30, 70, 100]
            self.process.parameters.hydrogen_coal_ccs_share_reference_years = []
            self.process.parameters.hydrogen_coal_ccs_share_reference_years_values = [0]
            self.process.parameters.hydrogen_gas_share_reference_years = [2020, 2030, 2040, 2050]
            self.process.parameters.hydrogen_gas_share_reference_years_values = [71, 70, 30, 0]
        elif self.w_hydrogen_production.value == "Electrolysis":
            self.process.parameters.hydrogen_electrolysis_share_reference_years = [
                2020,
                2030,
                2040,
                2050,
            ]
            self.process.parameters.hydrogen_electrolysis_share_reference_years_values = [
                2,
                30,
                50,
                100,
            ]
            self.process.parameters.hydrogen_gas_ccs_share_reference_years = [
                2020,
                2030,
                2040,
                2050,
            ]
            self.process.parameters.hydrogen_gas_ccs_share_reference_years_values = [0, 20, 30, 0]
            self.process.parameters.hydrogen_coal_ccs_share_reference_years = []
            self.process.parameters.hydrogen_coal_ccs_share_reference_years_values = [0]
            self.process.parameters.hydrogen_gas_share_reference_years = [2020, 2030, 2040, 2050]
            self.process.parameters.hydrogen_gas_share_reference_years_values = [71, 50, 20, 0]

        if self.w_electricity_production.value == "High-carbon":
            self.process.parameters.electricity_emission_factor_reference_years = []
            self.process.parameters.electricity_emission_factor_reference_years_values = [1100.0]
        elif self.w_electricity_production.value == "Current":
            self.process.parameters.electricity_emission_factor_reference_years = []
            self.process.parameters.electricity_emission_factor_reference_years_values = [429.0]
        elif self.w_electricity_production.value == "Medium-carbon":
            self.process.parameters.electricity_emission_factor_reference_years = [
                2020,
                2030,
                2040,
                2050,
            ]
            self.process.parameters.electricity_emission_factor_reference_years_values = [
                429,
                300,
                240,
                240,
            ]
        elif self.w_electricity_production.value == "Low-carbon":
            self.process.parameters.electricity_emission_factor_reference_years = [
                2020,
                2030,
                2040,
                2050,
            ]
            self.process.parameters.electricity_emission_factor_reference_years_values = [
                429,
                200,
                120,
                70,
            ]
        elif self.w_electricity_production.value == "Dedicated low-carbon":
            self.process.parameters.electricity_emission_factor_reference_years = []
            self.process.parameters.electricity_emission_factor_reference_years_values = [20.0]

        # SCENARIOS
        if self.w_accordion.selected_index == 1:
            if self.w_action_scenarios.value == "Example scenario":
                # Traffic
                self.process.parameters.cagr_passenger_short_range_reference_periods_values = [3.0]
                self.process.parameters.cagr_passenger_medium_range_reference_periods_values = [3.0]
                self.process.parameters.cagr_passenger_long_range_reference_periods_values = [3.0]
                self.process.parameters.cagr_freight_reference_periods_values = [3.0]
                #  RPK measures
                self.process.parameters.rpk_short_range_measures_final_impact = 0.0
                self.process.parameters.rpk_medium_range_measures_final_impact = 0.0
                self.process.parameters.rpk_long_range_measures_final_impact = 0.0
                self.process.parameters.rpk_short_range_measures_start_year = 2051
                self.process.parameters.rpk_medium_range_measures_start_year = 2051
                self.process.parameters.rpk_long_range_measures_start_year = 2051
                self.process.parameters.rpk_short_range_measures_duration = 5.0
                self.process.parameters.rpk_medium_range_measures_duration = 5.0
                self.process.parameters.rpk_long_range_measures_duration = 5.0
                # Efficiency
                self.process.parameters.load_factor_end_year = 89
                self.process.parameters.energy_per_ask_short_range_dropin_fuel_gain = 1.5
                self.process.parameters.energy_per_ask_medium_range_dropin_fuel_gain = 1.5
                self.process.parameters.energy_per_ask_long_range_dropin_fuel_gain = 1.5
                self.process.parameters.hydrogen_final_market_share_short_range = 50.0  # [%]
                self.process.parameters.hydrogen_introduction_year_short_range = 2035
                self.process.parameters.hydrogen_final_market_share_medium_range = 0.0  # [%]
                self.process.parameters.hydrogen_introduction_year_medium_range = 2051
                self.process.parameters.hydrogen_final_market_share_long_range = 0.0  # [%]
                self.process.parameters.hydrogen_introduction_year_long_range = 2051
                self.process.parameters.fleet_renewal_duration = 20.0
                self.process.parameters.operations_final_gain = 12.0
                self.process.parameters.operations_start_year = 2020
                self.process.parameters.operations_duration = 20.0
                # Contrails
                self.process.parameters.operations_contrails_final_gain = 0.0  # [%]
                self.process.parameters.operations_contrails_final_overconsumption = 0.0  # [%]
                self.process.parameters.operations_contrails_start_year = 2051
                self.process.parameters.operations_contrails_duration = 15.0
                # Fuels
                self.process.parameters.biofuel_share_reference_years = [2020, 2030, 2040, 2050]
                self.process.parameters.biofuel_share_reference_years_values = [
                    0.0,
                    4.0,
                    24.0,
                    35.0,
                ]
                self.process.parameters.electrofuel_share_reference_years = [2020, 2030, 2040, 2050]
                self.process.parameters.electrofuel_share_reference_years_values = [
                    0.0,
                    2,
                    13.0,
                    50.0,
                ]
                self.process.parameters.biofuel_hefa_fog_share_reference_years = []
                self.process.parameters.biofuel_hefa_fog_share_reference_years_values = [0.7]
                self.process.parameters.biofuel_hefa_others_share_reference_years = []
                self.process.parameters.biofuel_hefa_others_share_reference_years_values = [3.8]
                self.process.parameters.biofuel_ft_others_share_reference_years = []
                self.process.parameters.biofuel_ft_others_share_reference_years_values = [76.3]
                self.process.parameters.biofuel_ft_msw_share_reference_years = []
                self.process.parameters.biofuel_ft_msw_share_reference_years_values = [7.4]
                self.process.parameters.electricity_emission_factor_reference_years = [
                    2020,
                    2030,
                    2040,
                    2050,
                ]
                self.process.parameters.electricity_emission_factor_reference_years_values = [
                    429.0,
                    160.0,
                    60.0,
                    20.0,
                ]
                self.process.parameters.hydrogen_electrolysis_share_reference_years = []
                self.process.parameters.hydrogen_electrolysis_share_reference_years_values = [100]
                self.process.parameters.hydrogen_gas_ccs_share_reference_years = []
                self.process.parameters.hydrogen_gas_ccs_share_reference_years_values = [0]
                self.process.parameters.hydrogen_coal_ccs_share_reference_years = []
                self.process.parameters.hydrogen_coal_ccs_share_reference_years_values = [0]
                self.process.parameters.hydrogen_gas_share_reference_years = []
                self.process.parameters.hydrogen_gas_share_reference_years_values = [0]

        # DISCOVERY AND SCENARIOS
        # Environment
        if self.w_temperature.value == "+1.5°C":
            if self.w_success_percentage.value == "17%":
                self.process.parameters.net_carbon_budget = 900
            elif self.w_success_percentage.value == "33%":
                self.process.parameters.net_carbon_budget = 650
            elif self.w_success_percentage.value == "50%":
                self.process.parameters.net_carbon_budget = 500
            elif self.w_success_percentage.value == "67%":
                self.process.parameters.net_carbon_budget = 400
            elif self.w_success_percentage.value == "83%":
                self.process.parameters.net_carbon_budget = 300
        elif self.w_temperature.value == "+1.6°C":
            if self.w_success_percentage.value == "17%":
                self.process.parameters.net_carbon_budget = 1200
            elif self.w_success_percentage.value == "33%":
                self.process.parameters.net_carbon_budget = 850
            elif self.w_success_percentage.value == "50%":
                self.process.parameters.net_carbon_budget = 650
            elif self.w_success_percentage.value == "67%":
                self.process.parameters.net_carbon_budget = 550
            elif self.w_success_percentage.value == "83%":
                self.process.parameters.net_carbon_budget = 400
        elif self.w_temperature.value == "+1.7°C":
            if self.w_success_percentage.value == "17%":
                self.process.parameters.net_carbon_budget = 1450
            elif self.w_success_percentage.value == "33%":
                self.process.parameters.net_carbon_budget = 1050
            elif self.w_success_percentage.value == "50%":
                self.process.parameters.net_carbon_budget = 850
            elif self.w_success_percentage.value == "67%":
                self.process.parameters.net_carbon_budget = 700
            elif self.w_success_percentage.value == "83%":
                self.process.parameters.net_carbon_budget = 550
        elif self.w_temperature.value == "+1.8°C":
            if self.w_success_percentage.value == "17%":
                self.process.parameters.net_carbon_budget = 1750
            elif self.w_success_percentage.value == "33%":
                self.process.parameters.net_carbon_budget = 1250
            elif self.w_success_percentage.value == "50%":
                self.process.parameters.net_carbon_budget = 1000
            elif self.w_success_percentage.value == "67%":
                self.process.parameters.net_carbon_budget = 850
            elif self.w_success_percentage.value == "83%":
                self.process.parameters.net_carbon_budget = 650
        elif self.w_temperature.value == "+1.9°C":
            if self.w_success_percentage.value == "17%":
                self.process.parameters.net_carbon_budget = 2000
            elif self.w_success_percentage.value == "33%":
                self.process.parameters.net_carbon_budget = 1450
            elif self.w_success_percentage.value == "50%":
                self.process.parameters.net_carbon_budget = 1200
            elif self.w_success_percentage.value == "67%":
                self.process.parameters.net_carbon_budget = 1000
            elif self.w_success_percentage.value == "83%":
                self.process.parameters.net_carbon_budget = 800
        elif self.w_temperature.value == "+2.0°C":
            if self.w_success_percentage.value == "17%":
                self.process.parameters.net_carbon_budget = 2300
            elif self.w_success_percentage.value == "33%":
                self.process.parameters.net_carbon_budget = 1700
            elif self.w_success_percentage.value == "50%":
                self.process.parameters.net_carbon_budget = 1350
            elif self.w_success_percentage.value == "67%":
                self.process.parameters.net_carbon_budget = 1150
            elif self.w_success_percentage.value == "83%":
                self.process.parameters.net_carbon_budget = 900

        if self.w_cdr.value == "Undeveloped":
            self.process.parameters.carbon_dioxyde_removal_2100 = 0
        elif self.w_cdr.value == "Slightly developed":
            self.process.parameters.carbon_dioxyde_removal_2100 = 285
        elif self.w_cdr.value == "Developed":
            self.process.parameters.carbon_dioxyde_removal_2100 = 527
        elif self.w_cdr.value == "Highly developed":
            self.process.parameters.carbon_dioxyde_removal_2100 = 733

        if self.w_biomass_available.value == "Very pessimistic":
            self.process.parameters.waste_biomass = 9
            self.process.parameters.crops_biomass = 8
            self.process.parameters.forest_residues_biomass = 5
            self.process.parameters.agricultural_residues_biomass = 10
            self.process.parameters.algae_biomass = 5
        elif self.w_biomass_available.value == "Pessimistic":
            self.process.parameters.waste_biomass = 10
            self.process.parameters.crops_biomass = 37
            self.process.parameters.forest_residues_biomass = 15
            self.process.parameters.agricultural_residues_biomass = 30
            self.process.parameters.algae_biomass = 8
        elif self.w_biomass_available.value == "Realistic":
            self.process.parameters.waste_biomass = 12
            self.process.parameters.crops_biomass = 63
            self.process.parameters.forest_residues_biomass = 17
            self.process.parameters.agricultural_residues_biomass = 57
            self.process.parameters.algae_biomass = 15
        elif self.w_biomass_available.value == "Optimistic":
            self.process.parameters.waste_biomass = 20
            self.process.parameters.crops_biomass = 109
            self.process.parameters.forest_residues_biomass = 39
            self.process.parameters.agricultural_residues_biomass = 103
            self.process.parameters.algae_biomass = 31
        elif self.w_biomass_available.value == "Very optimistic":
            self.process.parameters.waste_biomass = 27
            self.process.parameters.crops_biomass = 217
            self.process.parameters.forest_residues_biomass = 59
            self.process.parameters.agricultural_residues_biomass = 204
            self.process.parameters.algae_biomass = 50

        if self.w_electricity_available.value == "Current":
            self.process.parameters.available_electricity = 100
        elif self.w_electricity_available.value == "Pessimistic":
            self.process.parameters.available_electricity = 150
        elif self.w_electricity_available.value == "Realistic":
            self.process.parameters.available_electricity = 200
        elif self.w_electricity_available.value == "Optimistic":
            self.process.parameters.available_electricity = 250
        elif self.w_electricity_available.value == "Very optimistic":
            self.process.parameters.available_electricity = 300

        # Allocations
        if self.w_carbon_budget_allocation.value == "2.3%":
            self.process.parameters.aviation_carbon_budget_allocated_share = 2.3
        elif self.w_carbon_budget_allocation.value == "2.6%":
            self.process.parameters.aviation_carbon_budget_allocated_share = 2.6
        elif self.w_carbon_budget_allocation.value == "3.4%":
            self.process.parameters.aviation_carbon_budget_allocated_share = 3.4
        elif self.w_carbon_budget_allocation.value == "6.8%":
            self.process.parameters.aviation_carbon_budget_allocated_share = 6.8

        if self.w_equivalent_carbon_budget_allocation.value == "0%":
            self.process.parameters.aviation_equivalentcarbonbudget_allocated_share = 0.0
        elif self.w_equivalent_carbon_budget_allocation.value == "3.8%":
            self.process.parameters.aviation_equivalentcarbonbudget_allocated_share = 3.8
        elif self.w_equivalent_carbon_budget_allocation.value == "5.1%":
            self.process.parameters.aviation_equivalentcarbonbudget_allocated_share = 5.1
        elif self.w_equivalent_carbon_budget_allocation.value == "15%":
            self.process.parameters.aviation_equivalentcarbonbudget_allocated_share = 15

        if self.w_biomass_allocation.value == "0%":
            self.process.parameters.aviation_biomass_allocated_share = 0.0
        elif self.w_biomass_allocation.value == "2.3%":
            self.process.parameters.aviation_biomass_allocated_share = 2.3
        elif self.w_biomass_allocation.value == "7.5%":
            self.process.parameters.aviation_biomass_allocated_share = 7.5
        elif self.w_biomass_allocation.value == "14.7%":
            self.process.parameters.aviation_biomass_allocated_share = 14.7

        if self.w_electricity_allocation.value == "0%":
            self.process.parameters.aviation_electricity_allocated_share = 0.0
        elif self.w_electricity_allocation.value == "2.3%":
            self.process.parameters.aviation_electricity_allocated_share = 2.3
        elif self.w_electricity_allocation.value == "7.5%":
            self.process.parameters.aviation_electricity_allocated_share = 7.5
        elif self.w_electricity_allocation.value == "15.0%":
            self.process.parameters.aviation_electricity_allocated_share = 15.0

    def _update_plots(self):
        self.fig1.update(self.process.data)
        self.fig2.update(self.process.data)
        self.fig3.update(self.process.data)

    def _download_results(self, change=None):
        self.process.write_excel()
        if self.download_output:
            self.download_output.clear_output(wait=True)
        else:
            self.download_output = widgets.Output()
        file_name = "data.xlsx"
        file_path = "/resources/data/" + file_name

        self._trigger_download(file_path, file_name, self.download_output)
        # os.remove(filepath)

    def _trigger_download(self, filepath, filename, output):
        js_code = f"""
            var a = document.createElement('a');
            a.setAttribute('download', '{filename}');
            a.setAttribute('href', '{filepath}');
            a.click()
        """
        with output:
            display(HTML(f"<script>{js_code}</script>"))

    def _load_data(self, filename: str = EXCEL_DATA_FILE):
        file_path = pth.join(DATA_FOLDER, filename)
        vector_outputs_df = pd.read_excel(
            file_path, sheet_name="Vector Outputs", index_col=0, engine="openpyxl"
        )
        float_outputs_df = pd.read_excel(
            file_path, sheet_name="Float Outputs", index_col=0, engine="openpyxl"
        )
        data = {
            "Vector Outputs": vector_outputs_df,
            "Float Outputs": float_outputs_df,
        }

        self._data_files[filename] = data

    def _download_figures(self, change=None):
        FOLDER_PATH = pth.join(pth.dirname(__file__), "../../src", "impacts")
        self.fig1.fig.savefig(pth.join(FOLDER_PATH, "fig1.pdf"))
        self.fig2.fig.savefig(pth.join(FOLDER_PATH, "fig2.pdf"))
        self.fig3.fig.savefig(pth.join(FOLDER_PATH, "fig3.pdf"))

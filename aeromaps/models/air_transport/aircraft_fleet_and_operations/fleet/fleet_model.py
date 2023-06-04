import copy

import numpy as np
from dataclasses import dataclass

import pandas as pd
import ipydatagrid as dg
from ipydatagrid import TextRenderer
from ipytree import Tree, Node
import matplotlib.pyplot as plt

import ipywidgets as ipw
from IPython.display import clear_output, display

from aeromaps.models.base import LogisticFunctionYearSeries, AeromapsModel
from aeromaps.models.air_transport.constants import EnergyTypes

AIRCRAFT_COLUMNS = [
    "Name",
    "EIS Year",
    "Consumption gain [%]",
    "NOx gain [%]",
    "Soot gain [%]",
    "Energy Type",
]
SUBCATEGORY_COLUMNS = ["Name", "Share [%]"]


@dataclass
class AircraftParameters:
    entry_into_service_year: float = None
    consumption_gain: float = None
    nox_gain: float = None
    soot_gain: float = None


@dataclass
class ReferenceAircraftParameters:
    energy_per_ask: float = None
    emission_index_nox: float = None
    emission_index_soot: float = None
    entry_into_service_year: float = None


@dataclass
class SubcategoryParameters:
    share: float = None


@dataclass
class CategoryParameters:
    life: float
    limit: float = 2


class FleetModel(AeromapsModel):
    def __init__(self, name="fleet_model", fleet=None, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.fleet = fleet

    def compute(
        self,
    ):

        # Single aircraft share computation (for obtaining the main plot on fleet renewal)
        for category in self.fleet.categories.values():

            limit = 2
            life_base = 25
            parameter_base = np.log(100 / limit - 1) / (life_base / 2)
            parameter_renewal = np.log(100 / limit - 1) / (category.parameters.life / 2)

            for i, subcategory in reversed(subcategory.items()):

                if dernière:

                    for aircraft in subcategory.aircraft.values():
                        single_aircraft_share = self._compute(
                            float(category.parameters.life),
                            float(aircraft.parameters.entry_into_service_year),
                            float(subcategory.parameters.share),
                        )
                        var_name = (
                                category.name
                                + ":"
                                + subcategory.name
                                + ":"
                                + aircraft.name
                                + ":single_aircraft_share"
                        )
                        self.df[var_name] = single_aircraft_share

                elif autres:

                    for aircraft in subcategory.aircraft.values():
                        single_aircraft_share = single_aircraft_share_precedent + self._compute(
                            float(category.parameters.life),
                            float(aircraft.parameters.entry_into_service_year),
                            float(subcategory.parameters.share),
                        )
                        var_name = (
                                category.name
                                + ":"
                                + subcategory.name
                                + ":"
                                + aircraft.name
                                + ":single_aircraft_share"
                        )
                        self.df[var_name] = single_aircraft_share


                elif i == list(subcategory.aircraft.keys())[-1]:

                    # Reference recent aircraft
                    year_ref_recent_begin = (
                        subcategory.recent_reference_aircraft.entry_into_service_year
                    )
                    year_ref_recent_base = year_ref_recent_begin + life_base / 2
                    year_ref_recent = (
                        self.prospection_start_year
                        - parameter_base
                        / parameter_renewal
                        * (self.prospection_start_year - year_ref_recent_base)
                    )
                    ref_recent_single_aircraft_share = single_aircraft_share_precedent + self._compute(
                        float(category.parameters.life),
                        float(year_ref_recent),
                        100.0-float(single_aircraft_share_precedent),
                        recent=True,
                    )
                    var_name = (
                        category.name
                        + ":"
                        + subcategory.name
                        + ":"
                        + "recent_reference:single_aircraft_share"
                    )
                    self.df[var_name] = ref_recent_single_aircraft_share

                    # Reference old aircraft
                    ref_old_single_aircraft_share = 100
                    var_name = (
                        category.name
                        + ":"
                        + subcategory.name
                        + ":"
                        + "old_reference:single_aircraft_share"
                    )
                    self.df[var_name] = ref_old_single_aircraft_share

                    # New aircraft
                    for aircraft in subcategory.aircraft.values():
                        single_aircraft_share = single_aircraft_share_precedent + self._compute(
                            float(category.parameters.life),
                            float(aircraft.parameters.entry_into_service_year),
                            100.0 - float(single_aircraft_share_precedent),
                        )
                        var_name = (
                            category.name
                            + ":"
                            + subcategory.name
                            + ":"
                            + aircraft.name
                            + ":single_aircraft_share"
                        )
                        self.df[var_name] = single_aircraft_share


        # Aircraft share computation
        for category in self.fleet.categories.values():
            # TODO: handling of subcategory

            for subcategory in category.subcategories.values():
                # TODO: verify aircraft order

                if (
                    subcategory == "Conventional narrow-body"
                    or subcategory == "Conventional wide-body"
                ):
                    ref_recent_single_aircraft_share = self.df[
                        category.name
                        + ":"
                        + subcategory.name
                        + ":"
                        + "recent_reference:single_aircraft_share"
                    ]

                    next_aircraft_single_share = self.df[
                        category.name
                        + ":"
                        + subcategory.name
                        + ":"
                        + subcategory.aircraft[0].name
                        + ":single_aircraft_share"
                    ]
                    var_name = (
                        category.name
                        + ":"
                        + subcategory.name
                        + ":"
                        + "recent_reference:aircraft_share"
                    )
                    ref_recent_aircraft_share = (
                        ref_recent_single_aircraft_share - next_aircraft_single_share
                    )
                    self.df[var_name] = ref_recent_aircraft_share

                    # Reference old aircraft
                    ref_old_aircraft_share = 100 - ref_recent_single_aircraft_share
                    var_name = (
                        category.name
                        + ":"
                        + subcategory.name
                        + ":"
                        + "old_reference:aircraft_share"
                    )
                    self.df[var_name] = ref_old_aircraft_share

                    subcat_consumption_per_ask = (
                        subcategory.old_reference_aircraft.energy_per_ask
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.energy_per_ask
                        * ref_recent_aircraft_share
                        / 100
                    )

                else:
                    subcat_consumption_per_ask = 0.0


                for i, aircraft in reversed(subcategory.aircraft.items()):
                    if i == list(subcategory.aircraft.keys())[-1]:
                        aircraft_share = self.df[
                            category.name
                            + ":"
                            + subcategory.name
                            + ":"
                            + aircraft.name
                            + ":single_aircraft_share"
                        ]

                        var_name = (
                            category.name
                            + ":"
                            + subcategory.name
                            + ":"
                            + aircraft.name
                            + ":aircraft_share"
                        )

                        self.df[var_name] = aircraft_share
                    else:

                        single_aircraft_share = self.df[
                            category.name
                            + ":"
                            + subcategory.name
                            + ":"
                            + aircraft.name
                            + ":single_aircraft_share"
                        ]
                        single_aircraft_share_n1 = self.df[
                            category.name
                            + ":"
                            + subcategory.name
                            + ":"
                            + subcategory.aircraft[i + 1].name
                            + ":single_aircraft_share"
                        ]

                        var_name = (
                            category.name
                            + ":"
                            + subcategory.name
                            + ":"
                            + aircraft.name
                            + ":aircraft_share"
                        )
                        aircraft_share = single_aircraft_share - single_aircraft_share_n1
                        self.df[var_name] = aircraft_share

                    subcat_consumption_per_ask += (
                        subcategory.recent_reference_aircraft.energy_per_ask
                        * (1 - float(aircraft.parameters.consumption_gain) / 100)
                        * aircraft_share
                        / 100
                    )


                    # Dedicated calculations for drop-in fuel and hydrogen

                    ## Initial share
                    subcategory_dropin_share = 100.0
                    subcategory_hydrogen_share = 0.0
                    # Initial energy consumption
                    subcategory_dropin_consumption_per_ask = copy.copy(subcat_consumption_per_ask)
                    subcategory_hydrogen_consumption_per_ask = 0.0

                    if aircraft.energy_type == "DROP_IN_FUEL":
                        subcategory_dropin_share += self.df[
                            category.name
                            + ":"
                            + subcategory.name
                            + ":"
                            + aircraft.name
                            + ":aircraft_share"
                        ]

                        subcategory_dropin_consumption_per_ask += (
                            subcategory.recent_reference_aircraft.energy_per_ask
                            * (1 - float(aircraft.parameters.consumption_gain) / 100)
                            * aircraft_share
                            / 100
                        )

                    if aircraft.energy_type == "HYDROGEN":
                        subcategory_hydrogen_share += self.df[
                            category.name
                            + ":"
                            + subcategory.name
                            + ":"
                            + aircraft.name
                            + ":aircraft_share"
                        ]

                        subcategory_hydrogen_consumption_per_ask += (
                            subcategory.recent_reference_aircraft.energy_per_ask
                            * (1 - float(aircraft.parameters.consumption_gain) / 100)
                            * aircraft_share
                            / 100
                        )

                # Share of drop-in fuel aircraft in subcategory
                self.df[
                    category.name + ":" + subcategory.name + ":share:dropin_fuel"
                ] = subcategory_dropin_share

                # Share of hydrogen aircraft in subcategory
                self.df[
                    category.name + ":" + subcategory.name + ":share:hydrogen"
                ] = subcategory_hydrogen_share

                # Mean energy consumption per subcategory
                self.df[
                    category.name + ":" + subcategory.name + ":energy_consumption"
                ] = subcat_consumption_per_ask

                # Mean energy consumption per subcategory (dropin aircraft)
                self.df[
                    category.name + ":" + subcategory.name + ":energy_consumption:dropin_fuel"
                ] = subcategory_dropin_consumption_per_ask

                # Mean energy consumption per subcategory (hydrogen aircraft)
                self.df[
                    category.name + ":" + subcategory.name + ":energy_consumption:hydrogen"
                ] = subcategory_hydrogen_consumption_per_ask

                # Mean energy consumption per category
                var_name = category.name + ":energy_consumption"
                if var_name in self.df:
                    # Mean
                    # self.df[category.name + ":energy_consumption"] += subcat_consumption_per_ask / (
                    #    subcategory.parameters.share / 100
                    # )
                    # Dropin
                    self.df[category.name + ":share:dropin_fuel"] += subcategory_dropin_share
                    # Hydrogen
                    self.df[category.name + ":share:hydrogen"] += subcategory_hydrogen_share
                else:
                    # Mean
                    # self.df[category.name + ":energy_consumption"] = subcat_consumption_per_ask / (
                    #    subcategory.parameters.share / 100
                    # )
                    # Dropin
                    self.df[category.name + ":share:dropin_fuel"] = subcategory_dropin_share
                    # Hydrogen
                    self.df[category.name + ":share:hydrogen"] = subcategory_hydrogen_share

            for subcategory in category.subcategories.values():
                # TODO: verify aircraft order
                # Mean energy consumption per category
                var_name = category.name + ":energy_consumption:dropin_fuel"
                if var_name in self.df:
                    self.df[category.name + ":energy_consumption:dropin_fuel"] += self.df[
                        category.name + ":" + subcategory.name + ":energy_consumption:dropin_fuel"
                    ] / (self.df[category.name + ":share:dropin_fuel"] / 100)
                    self.df[category.name + ":energy_consumption:hydrogen"] += self.df[
                        category.name + ":" + subcategory.name + ":energy_consumption:hydrogen"
                    ] / (self.df[category.name + ":share:hydrogen"] / 100)
                else:
                    self.df[category.name + ":energy_consumption:dropin_fuel"] = self.df[
                        category.name + ":" + subcategory.name + ":energy_consumption:dropin_fuel"
                    ] / (self.df[category.name + ":share:dropin_fuel"] / 100)
                    self.df[category.name + ":energy_consumption:hydrogen"] = self.df[
                        category.name + ":" + subcategory.name + ":energy_consumption:hydrogen"
                    ] / (self.df[category.name + ":share:hydrogen"] / 100)

            # Mean consumption
            self.df[category.name + ":energy_consumption"] = self.df[
                category.name + ":energy_consumption:dropin_fuel"
            ] / (self.df[category.name + ":share:dropin_fuel"] / 100) + self.df[
                category.name + ":energy_consumption:hydrogen"
            ] / (
                self.df[category.name + ":share:hydrogen"] / 100
            )

        var_name = "global_fleet:energy_consumption"

        # Mean energy consumption for the global fleet
        # Thomas : à supprimer ( carASK variables) une fois les modèles validés
        self.df[var_name] = self.df["Short Range" + ":energy_consumption"] * 0.272
        self.df[var_name] += self.df["Medium Range" + ":energy_consumption"] * 0.351
        self.df[var_name] += self.df["Long Range" + ":energy_consumption"] * 0.377

    def plot(self):
        x = np.linspace(self.prospection_start_year, self.end_year, len(self.df.index))

        categories = list(self.fleet.categories.values())

        f, axs = plt.subplots(2, len(categories), figsize=(20, 10))

        for i, category in enumerate(categories):
            # Top plot
            ax = axs[0, i]
            off_set = 100
            for j, subcategory in category.subcategories.items():
                # if j > 0:
                off_set -= subcategory.parameters.share
                # Old aircraft
                old_aircraft = 100 * np.ones(len(x)) * subcategory.parameters.share / 100 + off_set
                ax.fill_between(x, old_aircraft, label="old_reference" + subcategory.name)

                # Recent aircraft
                var_name = (
                    category.name
                    + ":"
                    + subcategory.name
                    + ":"
                    + "recent_reference:single_aircraft_share"
                )
                share_value = self.df[var_name] * subcategory.parameters.share / 100 + off_set
                ax.fill_between(
                    x,
                    share_value,
                    label="recent_reference " + subcategory.name,
                )

                # New aircraft
                for aircraft in subcategory.aircraft.values():
                    var_name = (
                        category.name
                        + ":"
                        + subcategory.name
                        + ":"
                        + aircraft.name
                        + ":single_aircraft_share"
                    )
                    share_value = self.df[var_name] * subcategory.parameters.share / 100 + off_set
                    ax.fill_between(
                        x,
                        share_value,
                        label=aircraft.name,
                    )

            ax.set_xlim(self.prospection_start_year, self.end_year)
            ax.set_ylim(0, 100)
            ax.legend(loc="upper left", prop={"size": 8})
            ax.set_xlabel("Year")
            ax.set_ylabel("Share in fleet [%]")
            ax.set_title(categories[i].name)

            # Bottom plot
            ax = axs[1, i]
            ax.plot(x, self.df[category.name + ":energy_consumption"])

            ax.set_xlim(self.prospection_start_year, self.end_year)
            ax.set_xlabel("Year")
            ax.set_ylabel("Fleet mean energy consumption")
            # ax.set_title(categories[i].name)

        plt.plot()
        plt.savefig("fleet_renewal.pdf")

    def _compute(self, life, entry_into_service_year, share, recent=False):
        x = np.linspace(self.prospection_start_year, self.end_year, len(self.df.index))

        # Intermediate variable for S-shaped function
        limit = 2
        growth_rate = np.log(100 / limit - 1) / (life / 2)

        if not recent:
            midpoint_year = entry_into_service_year + life / 2
        else:
            midpoint_year = entry_into_service_year

        y_share = share / (1 + np.exp(-growth_rate * (x - midpoint_year)))
        y_share_max = 100 / (1 + np.exp(-growth_rate * (x - midpoint_year)))

        y = np.where(y_share < limit, 0.0, y_share_max)
        return y


class Aircraft(object):
    def __init__(
        self,
        name: str = None,
        parameters: AircraftParameters = None,
        energy_type="DROP_IN_FUEL",
    ):
        self.name = name
        if parameters is None:
            parameters = AircraftParameters()
        self.parameters = parameters
        self.energy_type = energy_type

    def from_dataframe_row(self, row):
        self.name = row[AIRCRAFT_COLUMNS[0]]
        self.parameters.entry_into_service_year = row[AIRCRAFT_COLUMNS[1]]
        self.parameters.consumption_gain = row[AIRCRAFT_COLUMNS[2]]
        self.parameters.nox_gain = row[AIRCRAFT_COLUMNS[3]]
        self.parameters.soot_gain = row[AIRCRAFT_COLUMNS[4]]
        self.energy_type = row[AIRCRAFT_COLUMNS[5]]

        return self


class SubCategory(object):
    def __init__(self, name: str = None, parameters: SubcategoryParameters = None):
        self.name = name
        if parameters is None:
            parameters = SubcategoryParameters()
        self.parameters = parameters
        self.aircraft = {}
        self.old_reference_aircraft = ReferenceAircraftParameters()
        self.recent_reference_aircraft = ReferenceAircraftParameters()

        self._setup_datagrid()

        self._setup_ui()

    def add_aircraft(self, change=None, aircraft: Aircraft = None):

        if aircraft is None:
            aircraft_data = np.array(
                [
                    "New aircraft",
                    2025,
                    5.0,
                    10.0,
                    10.0,
                    "DROP_IN_FUEL",
                ]
            ).reshape((1, len(AIRCRAFT_COLUMNS)))
        else:
            aircraft_data = np.array(
                [
                    aircraft.name,
                    aircraft.parameters.entry_into_service_year,
                    aircraft.parameters.consumption_gain,
                    aircraft.parameters.nox_gain,
                    aircraft.parameters.soot_gain,
                    aircraft.energy_type,
                ]
            ).reshape((1, len(AIRCRAFT_COLUMNS)))

        # Add aircraft to grid
        current_grid_df = self.datagrid.data
        if len(current_grid_df) == 0:
            new_index = 0
        else:
            new_index = current_grid_df.index[-1] + 1

        current_grid_df = self.datagrid.data
        additional_row = pd.DataFrame(
            columns=current_grid_df.columns,
            index=[new_index],
            data=aircraft_data,
        )

        self.datagrid.data = pd.concat([self.datagrid.data, additional_row], ignore_index=True)

        # TODO: see if we avoid this when aircraft is directly provided
        self._update_parameters_from_grid()

    def remove_aircraft(self, change=None, aircraft_name: str = None):

        current_grid_df = self.datagrid.data

        if aircraft_name is not None:
            index_to_remove = current_grid_df.index[
                current_grid_df[AIRCRAFT_COLUMNS[0]] == aircraft_name
            ].tolist()
        else:
            selected_cells = self.datagrid.selected_cells

            index_to_remove = []
            for cell in selected_cells:
                row_index = cell["r"]
                if row_index not in index_to_remove:
                    index_to_remove.append(row_index)

        self.datagrid.data = current_grid_df.drop(index=index_to_remove)

        self._update_parameters_from_grid()

    def compute(self):
        for aircraft in self.aircraft:
            aircraft.compute()

    def from_dataframe_row(self, row):
        self.name = row[SUBCATEGORY_COLUMNS[0]]
        self.parameters.share = row[SUBCATEGORY_COLUMNS[1]]

        return self

    def _setup_datagrid(self):

        df = pd.DataFrame(columns=AIRCRAFT_COLUMNS)

        self.datagrid = dg.DataGrid(df, selection_mode="cell", editable=True)
        self.datagrid.auto_fit_columns = True

    def _setup_ui(self):
        button_add_row = ipw.Button(
            description="Add Aircraft", style=ipw.ButtonStyle(button_color="darkgreen")
        )
        button_remove_row = ipw.Button(
            description="Remove Aircraft", style=ipw.ButtonStyle(button_color="darkred")
        )

        button_add_row.on_click(self.add_aircraft)
        button_remove_row.on_click(self.remove_aircraft)

        self.datagrid.on_cell_change(self._update_parameters_from_grid)

        self.ui = ipw.VBox([ipw.HBox([button_add_row, button_remove_row]), self.datagrid])
        self.ui.layout.width = "600px"
        self.datagrid.auto_fit_columns = True

    def _update_parameters_from_grid(self, change=None):
        self.aircraft = {}
        current_grid_df = self.datagrid.data

        for index, row in current_grid_df.iterrows():
            aircraft = Aircraft()
            # self.aircraft[row["Name"]] = aircraft.from_dataframe_row(row)
            self.aircraft[int(index)] = aircraft.from_dataframe_row(row)


class Category(object):
    def __init__(self, name, parameters: CategoryParameters):
        self.name = name
        self.parameters = parameters
        self.subcategories = {}
        self.total_shares = 100

        self._setup_datagrid()

        self._setup_ui()

    def _compute(self):
        self._check_shares()
        if self.subcategories:
            for subcategory in self.subcategories.values():
                subcategory.compute()

    def add_subcategory(self, change=None, subcategory: SubCategory = None):

        if subcategory is None:
            subcategory_data = np.array(
                [
                    "New subcategory",
                    0.0,
                ]
            ).reshape((1, len(SUBCATEGORY_COLUMNS)))
        else:
            subcategory_data = np.array(
                [
                    subcategory.name,
                    subcategory.parameters.share,
                ]
            ).reshape((1, len(SUBCATEGORY_COLUMNS)))

        # Add subcategory to grid
        current_grid_df = self.datagrid.data
        if len(current_grid_df) == 0:
            new_index = 0
        else:
            new_index = current_grid_df.index[-1] + 1

        additional_row = pd.DataFrame(
            columns=current_grid_df.columns,
            index=[new_index],
            data=subcategory_data,
        )

        if subcategory is not None:
            self.subcategories[new_index] = subcategory
        else:
            # TODO: can we really have several rows?
            for index, row in additional_row.iterrows():
                subcategory = SubCategory()
                self.subcategories[new_index] = subcategory.from_dataframe_row(row)

        self.datagrid.data = pd.concat([self.datagrid.data, additional_row], ignore_index=True)
        self.datagrid.auto_fit_columns = True

    def remove_subcategory(self, change=None, subcategory_name: str = None):

        current_grid_df = self.datagrid.get_visible_data()

        if subcategory_name is not None:
            index_to_remove = current_grid_df.index[
                current_grid_df[SUBCATEGORY_COLUMNS[0]] == subcategory_name
            ].tolist()
        else:
            selected_cells = self.datagrid.selected_cells

            index_to_remove = []
            for cell in selected_cells:
                row_index = cell["r"]
                if row_index not in index_to_remove:
                    index_to_remove.append(row_index)

        # Remove and reset index
        for index in index_to_remove:
            self.subcategories.pop(index)
        self.subcategories = {
            i: self.subcategories[k] for i, k in enumerate(sorted(self.subcategories.keys()))
        }
        self.datagrid.data = current_grid_df.drop(index=index_to_remove)
        self.datagrid.auto_fit_columns = True

    def _setup_datagrid(self):

        df = pd.DataFrame(columns=SUBCATEGORY_COLUMNS)

        self.datagrid = dg.DataGrid(df, selection_mode="cell", editable=True)
        self.datagrid.auto_fit_columns = True
        self.datagrid.on_cell_change(self._update)

    def _setup_ui(self):
        self.button_add_row = ipw.Button(
            description="Add Subcategory", style=ipw.ButtonStyle(button_color="darkgreen")
        )
        self.button_remove_row = ipw.Button(
            description="Remove Subcategory", style=ipw.ButtonStyle(button_color="darkred")
        )

        self.button_add_row.on_click(self.add_subcategory)
        self.button_remove_row.on_click(self.remove_subcategory)
        self.datagrid.on_cell_change(self._update)

        self.ui = ipw.VBox([ipw.HBox([self.button_add_row, self.button_remove_row]), self.datagrid])
        self.ui.layout.width = "600px"

    def _update(self, change=None):
        self._update_parameters_from_grid()
        # self.total_shares = np.sum(
        #     [share for share in self.subcategories.values().parameters.share]
        # )
        for subcategory in self.subcategories.values():
            subcategory._update_parameters_from_grid()

    def _check_shares(self):
        self._update()
        if not np.isclose(self.total_shares, 100.0, atol=0.1):
            raise UserWarning(
                "Total shares for category %s are %f instead of 100%",
                (self.name, self.total_shares),
            )

    def _update_parameters_from_grid(self):
        current_grid_df = self.datagrid.data

        for index, row in current_grid_df.iterrows():
            self.subcategories[index].from_dataframe_row(row)


class Fleet(object):
    def __init__(
        self,
        short_range: Category = None,
        medium_range: Category = None,
        long_range: Category = None,
        build_default_fleet=True,
    ):
        if not build_default_fleet:
            self.categories = {
                short_range.name: short_range,
                medium_range.name: medium_range,
                long_range.name: long_range,
            }
        else:
            self.categories = {}

        # Build default fleet
        if build_default_fleet:
            self._build_default_fleet()

        # Initialize
        self.ui = None

        # Setup tree
        self.tree = Tree(stripes=True)
        self.tree.observe(self._update)
        self._setup_tree()

        # Take first category as default
        self.selected_item = list(self.categories.values())[0]

        # Setup user interface
        self._setup_ui()

    def compute(self):
        for cat in self.categories.values():
            cat._compute()

    def _setup_tree(self):
        for name, category in self.categories.items():
            category.button_add_row.observe(self._update)
            category.button_remove_row.observe(self._update)
            node = Node(name)
            subcategory_names = []
            for name, subcategory in category.subcategories.items():
                subcategory_names.append(subcategory.name)
            for name in subcategory_names:
                subnode = Node(name)
                node.add_node(subnode)
            self.tree.add_node(node)

    def _update_tree(self):
        for cat_node in list(self.tree.nodes):
            subcat_nodes = list(cat_node.nodes)
            subcategory_names = [
                subcategory.name
                for index, subcategory in self.categories[cat_node.name].subcategories.items()
            ]
            # Remove old nodes
            for node in subcat_nodes:
                if node.name not in subcategory_names:
                    cat_node.remove_node(node)

            subcategory_node_names = [node.name for node in list(cat_node.nodes)]

            # Add new nodes
            for name in subcategory_names:
                if name not in subcategory_node_names:
                    subnode = Node(name)
                    cat_node.add_node(subnode)

    def _update(self, change=None):
        if self.tree.selected_nodes:
            selected_node_name = list(self.tree.selected_nodes)[0].name
        else:
            selected_node_name = self.tree.nodes[0].name

        self.selected_item = self._find_category_or_subcategory(selected_node_name)
        self._update_tree()
        self._update_ui()

    def _find_category_or_subcategory(self, selected_node_name):
        for name, category in self.categories.items():
            if category.name == selected_node_name:
                return category
            else:
                for index, subcategory in category.subcategories.items():
                    if subcategory.name == selected_node_name:
                        return subcategory

    def _setup_ui(self):
        self.ui = ipw.HBox([self.tree, self.selected_item.ui])

    def _update_ui(self):
        if self.ui is not None:
            self.ui.children = (self.tree, self.selected_item.ui)
            if isinstance(self.selected_item, Category):
                self.selected_item.button_add_row.on_click(self._update)
                self.selected_item.button_remove_row.on_click(self._update)
                self.selected_item.datagrid.on_cell_change(self._update)

    def _build_default_fleet(self):
        # Short range narrow-body
        aircraft_params = AircraftParameters(
            entry_into_service_year=2035, consumption_gain=15.0, nox_gain=30.0, soot_gain=30.0
        )

        sr_nb_aircraft_1 = Aircraft(
            "New Narrow-body 1", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        aircraft_params = AircraftParameters(
            entry_into_service_year=2045, consumption_gain=30.0, nox_gain=30.0, soot_gain=30.0
        )

        sr_nb_aircraft_2 = Aircraft(
            "New Narrow-body 2", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        # Short range regional turboprop
        aircraft_params = AircraftParameters(
            entry_into_service_year=2035, consumption_gain=15.0, nox_gain=30.0, soot_gain=30.0
        )

        sr_tp_aircraft_1 = Aircraft(
            "New Regional turboprop 1",
            parameters=aircraft_params,
            energy_type="DROP_IN_FUEL",
        )

        aircraft_params = AircraftParameters(
            entry_into_service_year=2045, consumption_gain=30.0, nox_gain=30.0, soot_gain=30.0
        )

        sr_tp_aircraft_2 = Aircraft(
            "New Regional turboprop 2",
            parameters=aircraft_params,
            energy_type="DROP_IN_FUEL",
        )

        # Short range regional turbofan
        aircraft_params = AircraftParameters(
            entry_into_service_year=2035, consumption_gain=15.0, nox_gain=30.0, soot_gain=30.0
        )

        sr_tf_aircraft_1 = Aircraft(
            "New Regional turbofan 1",
            parameters=aircraft_params,
            energy_type="DROP_IN_FUEL",
        )

        aircraft_params = AircraftParameters(
            entry_into_service_year=2045, consumption_gain=30.0, nox_gain=30.0, soot_gain=30.0
        )

        sr_tf_aircraft_2 = Aircraft(
            "New Regional turbofan 2",
            parameters=aircraft_params,
            energy_type="DROP_IN_FUEL",
        )

        # Medium range
        aircraft_params = AircraftParameters(
            entry_into_service_year=2035, consumption_gain=15.0, nox_gain=30.0, soot_gain=30.0
        )

        mr_aircraft_1 = Aircraft(
            "New Medium-range 1", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        aircraft_params = AircraftParameters(
            entry_into_service_year=2045, consumption_gain=30.0, nox_gain=30.0, soot_gain=30.0
        )

        mr_aircraft_2 = Aircraft(
            "New Medium-range 2", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        # Long range
        aircraft_params = AircraftParameters(
            entry_into_service_year=2035, consumption_gain=15.0, nox_gain=30.0, soot_gain=30.0
        )

        lr_aircraft_1 = Aircraft(
            "New Long-range 1", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        aircraft_params = AircraftParameters(
            entry_into_service_year=2045, consumption_gain=30.0, nox_gain=30.0, soot_gain=30.0
        )

        lr_aircraft_2 = Aircraft(
            "New Long-range 2", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        # Short range narrow-body
        subcat_params = SubcategoryParameters(share=100.0)
        sr_nb_cat = SubCategory("Conventional narrow-body", parameters=subcat_params)
        # Reference aircraft
        # Old
        sr_nb_cat.old_reference_aircraft.entry_into_service_year = 1970
        sr_nb_cat.old_reference_aircraft.energy_per_ask = 110.8 / 73.2 * 0.824  # [MJ/ASK]
        sr_nb_cat.old_reference_aircraft.emission_index_nox = 0.01514
        sr_nb_cat.old_reference_aircraft.emission_index_soot = 3e-5

        # Recent
        sr_nb_cat.recent_reference_aircraft.entry_into_service_year = 2007.13
        sr_nb_cat.recent_reference_aircraft.energy_per_ask = 84.2 / 73.2 * 0.824  # [MJ/ASK]
        sr_nb_cat.recent_reference_aircraft.emission_index_nox = 0.01514
        sr_nb_cat.recent_reference_aircraft.emission_index_soot = 3e-5

        sr_nb_cat.add_aircraft(aircraft=sr_nb_aircraft_1)
        sr_nb_cat.add_aircraft(aircraft=sr_nb_aircraft_2)

        # Short range regional turboprop
        subcat_params = SubcategoryParameters(share=0.0)
        sr_rp_cat = SubCategory("Regional turboprop", parameters=subcat_params)
        # Reference aircraft
        # Old
        sr_rp_cat.old_reference_aircraft.entry_into_service_year = 1970
        sr_rp_cat.old_reference_aircraft.energy_per_ask = 101.2 / 73.2 * 0.824  # [MJ/ASK]
        sr_rp_cat.old_reference_aircraft.emission_index_nox = 0.01514
        sr_rp_cat.old_reference_aircraft.emission_index_soot = 3e-5

        # Recent
        sr_rp_cat.recent_reference_aircraft.entry_into_service_year = 2005
        sr_rp_cat.recent_reference_aircraft.energy_per_ask = 101.2 / 73.2 * 0.824  # [MJ/ASK]
        sr_rp_cat.recent_reference_aircraft.emission_index_nox = 0.01514
        sr_rp_cat.recent_reference_aircraft.emission_index_soot = 3e-5

        sr_rp_cat.add_aircraft(aircraft=sr_tp_aircraft_1)
        sr_rp_cat.add_aircraft(aircraft=sr_tp_aircraft_2)

        # Short range regional turbofan
        subcat_params = SubcategoryParameters(share=0.0)
        sr_tf_cat = SubCategory("Regional turbofan", parameters=subcat_params)
        # Reference aircraft
        # Old
        sr_tf_cat.old_reference_aircraft.entry_into_service_year = 1970
        sr_tf_cat.old_reference_aircraft.energy_per_ask = 192.9 / 73.2 * 0.824  # [MJ/ASK]
        sr_tf_cat.old_reference_aircraft.emission_index_nox = 0.01514
        sr_tf_cat.old_reference_aircraft.emission_index_soot = 3e-5

        # Recent
        sr_tf_cat.recent_reference_aircraft.entry_into_service_year = 2000
        sr_tf_cat.recent_reference_aircraft.energy_per_ask = 192.9 / 73.2 * 0.824  # [MJ/ASK]
        sr_tf_cat.recent_reference_aircraft.emission_index_nox = 0.01514
        sr_tf_cat.recent_reference_aircraft.emission_index_soot = 3e-5

        sr_tf_cat.add_aircraft(aircraft=sr_tf_aircraft_1)
        sr_tf_cat.add_aircraft(aircraft=sr_tf_aircraft_2)

        # Short range
        cat_params = CategoryParameters(
            ask0=1e6, growth_rates={2030: 2.0, 2040: 2.0, 2050: 2.0}, life=25
        )
        sr_cat = Category("Short Range", parameters=cat_params)
        sr_cat.add_subcategory(subcategory=sr_nb_cat)
        # sr_cat.add_subcategory(subcategory=sr_rp_cat)
        # sr_cat.add_subcategory(subcategory=sr_tf_cat)

        # Medium range
        subcat_params = SubcategoryParameters(share=100.0)
        mr_subcat = SubCategory("Conventional narrow-body", parameters=subcat_params)
        # Reference aircraft
        # Old
        mr_subcat.old_reference_aircraft.entry_into_service_year = 1970
        mr_subcat.old_reference_aircraft.energy_per_ask = 81.4 / 73.2 * 0.824  # [MJ/ASK]
        mr_subcat.old_reference_aircraft.emission_index_nox = 0.01514
        mr_subcat.old_reference_aircraft.emission_index_soot = 3e-5

        # Recent
        mr_subcat.recent_reference_aircraft.entry_into_service_year = 2010.35
        mr_subcat.recent_reference_aircraft.energy_per_ask = 62.0 / 73.2 * 0.824  # [MJ/ASK]
        mr_subcat.recent_reference_aircraft.emission_index_nox = 0.01514
        mr_subcat.recent_reference_aircraft.emission_index_soot = 3e-5

        mr_subcat.add_aircraft(aircraft=mr_aircraft_1)
        mr_subcat.add_aircraft(aircraft=mr_aircraft_2)

        cat_params = CategoryParameters(
            ask0=1e6, growth_rates={2030: 2.0, 2040: 2.0, 2050: 2.0}, life=25
        )
        mr_cat = Category(name="Medium Range", parameters=cat_params)
        mr_cat.add_subcategory(subcategory=mr_subcat)

        # Long range
        subcat_params = SubcategoryParameters(share=100.0)
        lr_subcat = SubCategory("Conventional wide-body", parameters=subcat_params)
        # Reference aircraft
        # Old
        lr_subcat.old_reference_aircraft.entry_into_service_year = 1970
        lr_subcat.old_reference_aircraft.energy_per_ask = 96.65 / 73.2 * 0.824  # [MJ/ASK]
        lr_subcat.old_reference_aircraft.emission_index_nox = 0.01514
        lr_subcat.old_reference_aircraft.emission_index_soot = 3e-5

        # Recent
        lr_subcat.recent_reference_aircraft.entry_into_service_year = 2009.36
        lr_subcat.recent_reference_aircraft.energy_per_ask = 73.45 / 73.2 * 0.824  # [MJ/ASK]
        lr_subcat.recent_reference_aircraft.emission_index_nox = 0.01514
        lr_subcat.recent_reference_aircraft.emission_index_soot = 3e-5

        lr_subcat.add_aircraft(aircraft=lr_aircraft_1)
        lr_subcat.add_aircraft(aircraft=lr_aircraft_2)

        cat_params = CategoryParameters(
            ask0=1e6, growth_rates={2030: 2.0, 2040: 2.0, 2050: 2.0}, life=25
        )
        lr_cat = Category("Long Range", parameters=cat_params)
        lr_cat.add_subcategory(subcategory=lr_subcat)

        self.categories[sr_cat.name] = sr_cat
        self.categories[mr_cat.name] = mr_cat
        self.categories[lr_cat.name] = lr_cat

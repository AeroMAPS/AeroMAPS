import numpy as np
from dataclasses import dataclass
import warnings

import pandas as pd
import ipydatagrid as dg
from ipytree import Tree, Node
import matplotlib.pyplot as plt

import ipywidgets as ipw

from aeromaps.models.base import AeromapsModel

AIRCRAFT_COLUMNS = [
    "Name",
    "EIS Year",
    "Consumption evolution [%]",
    "NOx evolution [%]",
    "Soot evolution [%]",
    "Non-Energy DOC evolution [%]",
    "Cruise altitude [m]",
    "Energy Type",
]
SUBCATEGORY_COLUMNS = ["Name", "Share [%]"]


@dataclass
class AircraftParameters:
    entry_into_service_year: float = None
    consumption_evolution: float = None
    nox_evolution: float = None
    soot_evolution: float = None
    doc_non_energy_evolution: float = None
    cruise_altitude: float = None


@dataclass
class ReferenceAircraftParameters:
    energy_per_ask: float = None
    emission_index_nox: float = None
    emission_index_soot: float = None
    doc_non_energy_base: float = None
    entry_into_service_year: float = None
    cruise_altitude: float = None


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

        # TODO : correct warnings
        warnings.filterwarnings("ignore")

        # Start from empty dataframe
        self.df = self.df.filter([])

        # Compute single aircraft shares
        self._compute_single_aircraft_share()

        # Compute aircraft shares
        self._compute_aircraft_share()

        # Compute energy consumption and share per subcategory with respect to energy type
        self._compute_energy_consumption_and_share_wrt_energy_type()

        # Compute non energy direct operating costs (DOC) and share per subcategory with respect to energy type
        self._compute_doc_non_energy()

        # Compute non-CO2 (NOx and soot) emission index and share per subcategory with respect to energy type
        self._compute_non_co2_emission_index()

        # Compute mean energy consumption per category with respect to energy type
        self._compute_mean_energy_consumption_per_category_wrt_energy_type()

        # Compute mean non energy direct operating cost (DOC) per category with respect to energy type
        self._compute_mean_doc_non_energy()

        # Compute mean non-CO2 emission index per category with respect to energy type
        self._compute_mean_non_co2_emission_index()

        warnings.resetwarnings()
        warnings.simplefilter("ignore", DeprecationWarning)

    def _compute_energy_consumption_and_share_wrt_energy_type(self):
        # Energy consumption calculations for drop-in fuel and hydrogen
        for category in self.fleet.categories.values():
            # Reference aircraft information
            ref_old_aircraft_share = self.df[
                category.name
                + ":"
                + category.subcategories[0].name
                + ":"
                + "old_reference:aircraft_share"
            ]
            ref_recent_aircraft_share = self.df[
                category.name
                + ":"
                + category.subcategories[0].name
                + ":"
                + "recent_reference:aircraft_share"
            ]

            recent_reference_aircraft_energy_consumption = category.subcategories[
                0
            ].recent_reference_aircraft.energy_per_ask

            for i, subcategory in category.subcategories.items():
                # Initialization
                if i == 0:
                    self.df[category.name + ":" + subcategory.name + ":energy_consumption"] = (
                        subcategory.old_reference_aircraft.energy_per_ask
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.energy_per_ask
                        * ref_recent_aircraft_share
                        / 100
                    )
                    # Initial energy consumption
                    self.df[
                        category.name + ":" + subcategory.name + ":energy_consumption:dropin_fuel"
                    ] = self.df[category.name + ":" + subcategory.name + ":energy_consumption"]
                    self.df[
                        category.name + ":" + subcategory.name + ":energy_consumption:hydrogen"
                    ] = 0.0
                    # Initial shares
                    self.df[category.name + ":" + subcategory.name + ":share:total"] = (
                        ref_old_aircraft_share + ref_recent_aircraft_share
                    )
                    self.df[category.name + ":" + subcategory.name + ":share:dropin_fuel"] = (
                        ref_old_aircraft_share + ref_recent_aircraft_share
                    )
                    self.df[category.name + ":" + subcategory.name + ":share:hydrogen"] = 0.0

                else:
                    self.df[category.name + ":" + subcategory.name + ":energy_consumption"] = 0.0
                    # Initial energy consumption
                    self.df[
                        category.name + ":" + subcategory.name + ":energy_consumption:dropin_fuel"
                    ] = self.df[category.name + ":" + subcategory.name + ":energy_consumption"]
                    self.df[
                        category.name + ":" + subcategory.name + ":energy_consumption:hydrogen"
                    ] = self.df[category.name + ":" + subcategory.name + ":energy_consumption"]
                    # Initial shares
                    self.df[category.name + ":" + subcategory.name + ":share:total"] = 0.0
                    self.df[category.name + ":" + subcategory.name + ":share:dropin_fuel"] = 0.0
                    self.df[category.name + ":" + subcategory.name + ":share:hydrogen"] = 0.0

                for aircraft in subcategory.aircraft.values():

                    for k in self.df.index:

                        if (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":"
                                + aircraft.name
                                + ":aircraft_share",
                            ]
                            != 0.0
                        ):

                            self.df.loc[
                                k, category.name + ":" + subcategory.name + ":share:total"
                            ] += self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":"
                                + aircraft.name
                                + ":aircraft_share",
                            ]

                            self.df.loc[
                                k, category.name + ":" + subcategory.name + ":energy_consumption"
                            ] += (
                                recent_reference_aircraft_energy_consumption
                                * (1 + float(aircraft.parameters.consumption_evolution) / 100)
                                * self.df.loc[
                                    k,
                                    category.name
                                    + ":"
                                    + subcategory.name
                                    + ":"
                                    + aircraft.name
                                    + ":aircraft_share",
                                ]
                                / 100
                            )

                            if aircraft.energy_type == "DROP_IN_FUEL":
                                self.df.loc[
                                    k, category.name + ":" + subcategory.name + ":share:dropin_fuel"
                                ] += (
                                    self.df.loc[
                                        k,
                                        category.name
                                        + ":"
                                        + subcategory.name
                                        + ":"
                                        + aircraft.name
                                        + ":aircraft_share",
                                    ]
                                    # / self.df.loc[
                                    #     k, category.name + ":" + subcategory.name + ":share:total"
                                    # ]
                                    # * 100
                                )
                                self.df.loc[
                                    k,
                                    category.name
                                    + ":"
                                    + subcategory.name
                                    + ":energy_consumption:dropin_fuel",
                                ] += (
                                    recent_reference_aircraft_energy_consumption
                                    * (1 + float(aircraft.parameters.consumption_evolution) / 100)
                                    * self.df.loc[
                                        k,
                                        category.name
                                        + ":"
                                        + subcategory.name
                                        + ":"
                                        + aircraft.name
                                        + ":aircraft_share",
                                    ]
                                    / 100
                                )

                            if aircraft.energy_type == "HYDROGEN":
                                self.df.loc[
                                    k, category.name + ":" + subcategory.name + ":share:hydrogen"
                                ] += (
                                    self.df.loc[
                                        k,
                                        category.name
                                        + ":"
                                        + subcategory.name
                                        + ":"
                                        + aircraft.name
                                        + ":aircraft_share",
                                    ]
                                    # / self.df.loc[
                                    #     k, category.name + ":" + subcategory.name + ":share:total"
                                    # ]
                                    # * 100
                                )
                                self.df.loc[
                                    k,
                                    category.name
                                    + ":"
                                    + subcategory.name
                                    + ":energy_consumption:hydrogen",
                                ] += (
                                    recent_reference_aircraft_energy_consumption
                                    * (1 + float(aircraft.parameters.consumption_evolution) / 100)
                                    * self.df.loc[
                                        k,
                                        category.name
                                        + ":"
                                        + subcategory.name
                                        + ":"
                                        + aircraft.name
                                        + ":aircraft_share",
                                    ]
                                    / 100
                                )

                # Energy shares per category
                var_name = category.name + ":share:dropin_fuel"
                if var_name in self.df:
                    # Dropin
                    self.df[category.name + ":share:dropin_fuel"] += self.df[
                        category.name + ":" + subcategory.name + ":share:dropin_fuel"
                    ]
                else:
                    # Dropin
                    self.df[category.name + ":share:dropin_fuel"] = self.df[
                        category.name + ":" + subcategory.name + ":share:dropin_fuel"
                    ]

                var_name = category.name + ":share:hydrogen"
                if var_name in self.df:
                    # Hydrogen
                    self.df[category.name + ":share:hydrogen"] += self.df[
                        category.name + ":" + subcategory.name + ":share:hydrogen"
                    ]
                else:
                    # Hydrogen
                    self.df[category.name + ":share:hydrogen"] = self.df[
                        category.name + ":" + subcategory.name + ":share:hydrogen"
                    ]

    def _compute_doc_non_energy(self):
        # Non-energy DOC calculations for drop-in fuel and hydrogen
        for category in self.fleet.categories.values():
            # Reference aircraft information
            ref_old_aircraft_share = self.df[
                category.name
                + ":"
                + category.subcategories[0].name
                + ":"
                + "old_reference:aircraft_share"
            ]
            ref_recent_aircraft_share = self.df[
                category.name
                + ":"
                + category.subcategories[0].name
                + ":"
                + "recent_reference:aircraft_share"
            ]

            recent_reference_aircraft_doc_non_energy = category.subcategories[
                0
            ].recent_reference_aircraft.doc_non_energy_base

            for i, subcategory in category.subcategories.items():
                # Initialization
                if i == 0:
                    self.df[category.name + ":" + subcategory.name + ":doc_non_energy"] = (
                        subcategory.old_reference_aircraft.doc_non_energy_base
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.doc_non_energy_base
                        * ref_recent_aircraft_share
                        / 100
                    )
                    # Initial energy consumption
                    self.df[
                        category.name + ":" + subcategory.name + ":doc_non_energy:dropin_fuel"
                    ] = self.df[category.name + ":" + subcategory.name + ":doc_non_energy"]
                    self.df[
                        category.name + ":" + subcategory.name + ":doc_non_energy:hydrogen"
                    ] = 0.0
                    # Initial shares
                    # self.df[category.name + ":" + subcategory.name + ":share:total"] = (
                    #     ref_old_aircraft_share + ref_recent_aircraft_share
                    # )
                    # self.df[category.name + ":" + subcategory.name + ":share:dropin_fuel"] = (
                    #     ref_old_aircraft_share + ref_recent_aircraft_share
                    # )
                    # self.df[category.name + ":" + subcategory.name + ":share:hydrogen"] = 0.0

                else:
                    self.df[category.name + ":" + subcategory.name + ":doc_non_energy"] = 0.0
                    # Initial energy consumption
                    self.df[
                        category.name + ":" + subcategory.name + ":doc_non_energy:dropin_fuel"
                    ] = self.df[category.name + ":" + subcategory.name + ":doc_non_energy"]
                    self.df[
                        category.name + ":" + subcategory.name + ":doc_non_energy:hydrogen"
                    ] = self.df[category.name + ":" + subcategory.name + ":doc_non_energy"]
                    # Initial shares
                    # self.df[category.name + ":" + subcategory.name + ":share:total"] = 0.0
                    # self.df[category.name + ":" + subcategory.name + ":share:dropin_fuel"] = 0.0
                    # self.df[category.name + ":" + subcategory.name + ":share:hydrogen"] = 0.0

                for aircraft in subcategory.aircraft.values():

                    for k in self.df.index:

                        if (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":"
                                + aircraft.name
                                + ":aircraft_share",
                            ]
                            != 0.0
                        ):

                            # self.df.loc[
                            #     k, category.name + ":" + subcategory.name + ":share:total"
                            # ] += self.df.loc[
                            #     k,
                            #     category.name
                            #     + ":"
                            #     + subcategory.name
                            #     + ":"
                            #     + aircraft.name
                            #     + ":aircraft_share",
                            # ]

                            self.df.loc[
                                k, category.name + ":" + subcategory.name + ":doc_non_energy"
                            ] += (
                                recent_reference_aircraft_doc_non_energy
                                * (1 + float(aircraft.parameters.doc_non_energy_evolution) / 100)
                                * self.df.loc[
                                    k,
                                    category.name
                                    + ":"
                                    + subcategory.name
                                    + ":"
                                    + aircraft.name
                                    + ":aircraft_share",
                                ]
                                / 100
                            )

                            if aircraft.energy_type == "DROP_IN_FUEL":
                                # self.df.loc[
                                #     k, category.name + ":" + subcategory.name + ":share:dropin_fuel"
                                # ] += (
                                #     self.df.loc[
                                #         k,
                                #         category.name
                                #         + ":"
                                #         + subcategory.name
                                #         + ":"
                                #         + aircraft.name
                                #         + ":aircraft_share",
                                #     ]
                                #     # / self.df.loc[
                                #     #     k, category.name + ":" + subcategory.name + ":share:total"
                                #     # ]
                                #     # * 100
                                # )
                                self.df.loc[
                                    k,
                                    category.name
                                    + ":"
                                    + subcategory.name
                                    + ":doc_non_energy:dropin_fuel",
                                ] += (
                                    recent_reference_aircraft_doc_non_energy
                                    * (
                                        1
                                        + float(aircraft.parameters.doc_non_energy_evolution) / 100
                                    )
                                    * self.df.loc[
                                        k,
                                        category.name
                                        + ":"
                                        + subcategory.name
                                        + ":"
                                        + aircraft.name
                                        + ":aircraft_share",
                                    ]
                                    / 100
                                )

                            if aircraft.energy_type == "HYDROGEN":
                                # self.df.loc[
                                #     k, category.name + ":" + subcategory.name + ":share:hydrogen"
                                # ] += (
                                #     self.df.loc[
                                #         k,
                                #         category.name
                                #         + ":"
                                #         + subcategory.name
                                #         + ":"
                                #         + aircraft.name
                                #         + ":aircraft_share",
                                #     ]
                                #     # / self.df.loc[
                                #     #     k, category.name + ":" + subcategory.name + ":share:total"
                                #     # ]
                                #     # * 100
                                # )
                                self.df.loc[
                                    k,
                                    category.name
                                    + ":"
                                    + subcategory.name
                                    + ":doc_non_energy:hydrogen",
                                ] += (
                                    recent_reference_aircraft_doc_non_energy
                                    * (
                                        1
                                        + float(aircraft.parameters.doc_non_energy_evolution) / 100
                                    )
                                    * self.df.loc[
                                        k,
                                        category.name
                                        + ":"
                                        + subcategory.name
                                        + ":"
                                        + aircraft.name
                                        + ":aircraft_share",
                                    ]
                                    / 100
                                )

                # # Energy shares per category
                # var_name = category.name + ":share:dropin_fuel"
                # if var_name in self.df:
                #     # Dropin
                #     self.df[category.name + ":share:dropin_fuel"] += self.df[
                #         category.name + ":" + subcategory.name + ":share:dropin_fuel"
                #     ]
                # else:
                #     # Dropin
                #     self.df[category.name + ":share:dropin_fuel"] = self.df[
                #         category.name + ":" + subcategory.name + ":share:dropin_fuel"
                #     ]
                #
                # var_name = category.name + ":share:hydrogen"
                # if var_name in self.df:
                #     # Hydrogen
                #     self.df[category.name + ":share:hydrogen"] += self.df[
                #         category.name + ":" + subcategory.name + ":share:hydrogen"
                #     ]
                # else:
                #     # Hydrogen
                #     self.df[category.name + ":share:hydrogen"] = self.df[
                #         category.name + ":" + subcategory.name + ":share:hydrogen"
                #     ]

    def _compute_non_co2_emission_index(self):
        # Non-CO2 (NOx and soot) emission index calculations for drop-in fuel and hydrogen
        for category in self.fleet.categories.values():
            # Reference aircraft information
            ref_old_aircraft_share = self.df[
                category.name
                + ":"
                + category.subcategories[0].name
                + ":"
                + "old_reference:aircraft_share"
            ]
            ref_recent_aircraft_share = self.df[
                category.name
                + ":"
                + category.subcategories[0].name
                + ":"
                + "recent_reference:aircraft_share"
            ]

            recent_reference_aircraft_emission_index_nox = category.subcategories[
                0
            ].recent_reference_aircraft.emission_index_nox
            recent_reference_aircraft_emission_index_soot = category.subcategories[
                0
            ].recent_reference_aircraft.emission_index_soot

            for i, subcategory in category.subcategories.items():
                # Initialization
                if i == 0:
                    self.df[category.name + ":" + subcategory.name + ":emission_index_nox"] = (
                        subcategory.old_reference_aircraft.emission_index_nox
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.emission_index_nox
                        * ref_recent_aircraft_share
                        / 100
                    )
                    self.df[category.name + ":" + subcategory.name + ":emission_index_soot"] = (
                        subcategory.old_reference_aircraft.emission_index_soot
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.emission_index_soot
                        * ref_recent_aircraft_share
                        / 100
                    )
                    # Initial emission index
                    self.df[
                        category.name + ":" + subcategory.name + ":emission_index_nox:dropin_fuel"
                    ] = self.df[category.name + ":" + subcategory.name + ":emission_index_nox"]
                    self.df[
                        category.name + ":" + subcategory.name + ":emission_index_nox:hydrogen"
                    ] = 0.0
                    self.df[
                        category.name + ":" + subcategory.name + ":emission_index_soot:dropin_fuel"
                    ] = self.df[category.name + ":" + subcategory.name + ":emission_index_soot"]
                    self.df[
                        category.name + ":" + subcategory.name + ":emission_index_soot:hydrogen"
                    ] = 0.0

                else:
                    self.df[category.name + ":" + subcategory.name + ":emission_index_nox"] = 0.0
                    self.df[category.name + ":" + subcategory.name + ":emission_index_soot"] = 0.0
                    # Initial emission index
                    self.df[
                        category.name + ":" + subcategory.name + ":emission_index_nox:dropin_fuel"
                    ] = self.df[category.name + ":" + subcategory.name + ":emission_index_nox"]
                    self.df[
                        category.name + ":" + subcategory.name + ":emission_index_nox:hydrogen"
                    ] = self.df[category.name + ":" + subcategory.name + ":emission_index_nox"]
                    self.df[
                        category.name + ":" + subcategory.name + ":emission_index_soot:dropin_fuel"
                    ] = self.df[category.name + ":" + subcategory.name + ":emission_index_soot"]
                    self.df[
                        category.name + ":" + subcategory.name + ":emission_index_soot:hydrogen"
                    ] = self.df[category.name + ":" + subcategory.name + ":emission_index_soot"]

                for aircraft in subcategory.aircraft.values():

                    for k in self.df.index:

                        if (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":"
                                + aircraft.name
                                + ":aircraft_share",
                            ]
                            != 0.0
                        ):

                            self.df.loc[
                                k, category.name + ":" + subcategory.name + ":emission_index_nox"
                            ] += (
                                recent_reference_aircraft_emission_index_nox
                                * (1 + float(aircraft.parameters.nox_evolution) / 100)
                                * self.df.loc[
                                    k,
                                    category.name
                                    + ":"
                                    + subcategory.name
                                    + ":"
                                    + aircraft.name
                                    + ":aircraft_share",
                                ]
                                / 100
                            )

                            self.df.loc[
                                k, category.name + ":" + subcategory.name + ":emission_index_soot"
                            ] += (
                                recent_reference_aircraft_emission_index_soot
                                * (1 + float(aircraft.parameters.soot_evolution) / 100)
                                * self.df.loc[
                                    k,
                                    category.name
                                    + ":"
                                    + subcategory.name
                                    + ":"
                                    + aircraft.name
                                    + ":aircraft_share",
                                ]
                                / 100
                            )

                            if aircraft.energy_type == "DROP_IN_FUEL":
                                self.df.loc[
                                    k,
                                    category.name
                                    + ":"
                                    + subcategory.name
                                    + ":emission_index_nox:dropin_fuel",
                                ] += (
                                    recent_reference_aircraft_emission_index_nox
                                    * (1 + float(aircraft.parameters.nox_evolution) / 100)
                                    * self.df.loc[
                                        k,
                                        category.name
                                        + ":"
                                        + subcategory.name
                                        + ":"
                                        + aircraft.name
                                        + ":aircraft_share",
                                    ]
                                    / 100
                                )
                                self.df.loc[
                                    k,
                                    category.name
                                    + ":"
                                    + subcategory.name
                                    + ":emission_index_soot:dropin_fuel",
                                ] += (
                                    recent_reference_aircraft_emission_index_soot
                                    * (1 + float(aircraft.parameters.soot_evolution) / 100)
                                    * self.df.loc[
                                        k,
                                        category.name
                                        + ":"
                                        + subcategory.name
                                        + ":"
                                        + aircraft.name
                                        + ":aircraft_share",
                                    ]
                                    / 100
                                )

                            if aircraft.energy_type == "HYDROGEN":
                                self.df.loc[
                                    k,
                                    category.name
                                    + ":"
                                    + subcategory.name
                                    + ":emission_index_nox:hydrogen",
                                ] += (
                                    recent_reference_aircraft_emission_index_nox
                                    * (1 + float(aircraft.parameters.nox_evolution) / 100)
                                    * self.df.loc[
                                        k,
                                        category.name
                                        + ":"
                                        + subcategory.name
                                        + ":"
                                        + aircraft.name
                                        + ":aircraft_share",
                                    ]
                                    / 100
                                )

    def _compute_mean_energy_consumption_per_category_wrt_energy_type(self):
        for category in self.fleet.categories.values():
            # Mean energy consumption per category
            # Initialization
            self.df[category.name + ":energy_consumption:dropin_fuel"] = 0.0
            self.df[category.name + ":energy_consumption:hydrogen"] = 0.0
            # Calculation
            for subcategory in category.subcategories.values():
                # TODO: verify aircraft order
                for k in self.df.index:
                    if self.df.loc[k, category.name + ":share:dropin_fuel"] != 0.0:
                        self.df.loc[
                            k, category.name + ":energy_consumption:dropin_fuel"
                        ] += self.df.loc[
                            k,
                            category.name
                            + ":"
                            + subcategory.name
                            + ":energy_consumption:dropin_fuel",
                        ] / (
                            self.df.loc[k, category.name + ":share:dropin_fuel"] / 100
                        )
                    else:
                        self.df.loc[k, category.name + ":energy_consumption:dropin_fuel"] = 0.0

                    if self.df.loc[k, category.name + ":share:hydrogen"] != 0.0:
                        self.df.loc[
                            k, category.name + ":energy_consumption:hydrogen"
                        ] += self.df.loc[
                            k,
                            category.name + ":" + subcategory.name + ":energy_consumption:hydrogen",
                        ] / (
                            self.df.loc[k, category.name + ":share:hydrogen"] / 100
                        )
                    else:
                        self.df.loc[k, category.name + ":energy_consumption:hydrogen"] = 0.0

            # Mean consumption
            for k in self.df.index:
                self.df.loc[k, category.name + ":energy_consumption"] = self.df.loc[
                    k, category.name + ":energy_consumption:dropin_fuel"
                ] * (self.df.loc[k, category.name + ":share:dropin_fuel"] / 100) + self.df.loc[
                    k, category.name + ":energy_consumption:hydrogen"
                ] * (
                    self.df.loc[k, category.name + ":share:hydrogen"] / 100
                )
        # Mean energy consumption for the global fleet
        # Considering fixed category distribution in 2019
        # var_name = "global_fleet:energy_consumption"
        # self.df[var_name] = self.df["Short Range" + ":energy_consumption"] * 0.272
        # self.df[var_name] += self.df["Medium Range" + ":energy_consumption"] * 0.351
        # self.df[var_name] += self.df["Long Range" + ":energy_consumption"] * 0.377

    def _compute_mean_doc_non_energy(self):
        for category in self.fleet.categories.values():
            # Mean non energy DOC per category
            # Initialization
            self.df[category.name + ":doc_non_energy:dropin_fuel"] = 0.0
            self.df[category.name + ":doc_non_energy:hydrogen"] = 0.0
            # Calculation
            for subcategory in category.subcategories.values():
                # TODO: verify aircraft order
                for k in self.df.index:
                    if self.df.loc[k, category.name + ":share:dropin_fuel"] != 0.0:
                        self.df.loc[
                            k, category.name + ":doc_non_energy:dropin_fuel"
                        ] += self.df.loc[
                            k,
                            category.name + ":" + subcategory.name + ":doc_non_energy:dropin_fuel",
                        ] / (
                            self.df.loc[k, category.name + ":share:dropin_fuel"] / 100
                        )
                    else:
                        self.df.loc[k, category.name + ":doc_non_energy:dropin_fuel"] = 0.0

                    if self.df.loc[k, category.name + ":share:hydrogen"] != 0.0:
                        self.df.loc[k, category.name + ":doc_non_energy:hydrogen"] += self.df.loc[
                            k,
                            category.name + ":" + subcategory.name + ":doc_non_energy:hydrogen",
                        ] / (self.df.loc[k, category.name + ":share:hydrogen"] / 100)
                    else:
                        self.df.loc[k, category.name + ":doc_non_energy:hydrogen"] = 0.0

            # Mean non energy DOC
            for k in self.df.index:
                self.df.loc[k, category.name + ":doc_non_energy"] = self.df.loc[
                    k, category.name + ":doc_non_energy:dropin_fuel"
                ] * (self.df.loc[k, category.name + ":share:dropin_fuel"] / 100) + self.df.loc[
                    k, category.name + ":doc_non_energy:hydrogen"
                ] * (
                    self.df.loc[k, category.name + ":share:hydrogen"] / 100
                )

    def _compute_mean_non_co2_emission_index(self):

        for category in self.fleet.categories.values():
            # Mean non-CO2 emission index per category
            # Initialization
            self.df[category.name + ":emission_index_nox:dropin_fuel"] = 0.0
            self.df[category.name + ":emission_index_nox:hydrogen"] = 0.0
            self.df[category.name + ":emission_index_soot:dropin_fuel"] = 0.0
            self.df[category.name + ":emission_index_soot:hydrogen"] = 0.0
            # Calculation
            for subcategory in category.subcategories.values():
                # TODO: verify aircraft order
                for k in self.df.index:
                    if self.df.loc[k, category.name + ":share:dropin_fuel"] != 0.0:
                        self.df.loc[
                            k, category.name + ":emission_index_nox:dropin_fuel"
                        ] += self.df.loc[
                            k,
                            category.name
                            + ":"
                            + subcategory.name
                            + ":emission_index_nox:dropin_fuel",
                        ] / (
                            self.df.loc[k, category.name + ":share:dropin_fuel"] / 100
                        )
                        self.df.loc[
                            k, category.name + ":emission_index_soot:dropin_fuel"
                        ] += self.df.loc[
                            k,
                            category.name
                            + ":"
                            + subcategory.name
                            + ":emission_index_soot:dropin_fuel",
                        ] / (
                            self.df.loc[k, category.name + ":share:dropin_fuel"] / 100
                        )
                    else:
                        self.df.loc[k, category.name + ":emission_index_nox:dropin_fuel"] = 0.0
                        self.df.loc[k, category.name + ":emission_index_soot:dropin_fuel"] = 0.0

                    if self.df.loc[k, category.name + ":share:hydrogen"] != 0.0:
                        self.df.loc[
                            k, category.name + ":emission_index_nox:hydrogen"
                        ] += self.df.loc[
                            k,
                            category.name + ":" + subcategory.name + ":emission_index_nox:hydrogen",
                        ] / (
                            self.df.loc[k, category.name + ":share:hydrogen"] / 100
                        )
                        self.df.loc[
                            k, category.name + ":emission_index_soot:hydrogen"
                        ] += self.df.loc[
                            k,
                            category.name
                            + ":"
                            + subcategory.name
                            + ":emission_index_soot:hydrogen",
                        ] / (
                            self.df.loc[k, category.name + ":share:hydrogen"] / 100
                        )
                    else:
                        self.df.loc[k, category.name + ":emission_index_nox:hydrogen"] = 0.0
                        self.df.loc[k, category.name + ":emission_index_soot:hydrogen"] = 0.0

            # Mean emission index
            for k in self.df.index:
                self.df.loc[k, category.name + ":emission_index_nox"] = self.df.loc[
                    k, category.name + ":emission_index_nox:dropin_fuel"
                ] * (self.df.loc[k, category.name + ":share:dropin_fuel"] / 100) + self.df.loc[
                    k, category.name + ":emission_index_nox:hydrogen"
                ] * (
                    self.df.loc[k, category.name + ":share:hydrogen"] / 100
                )
                self.df.loc[k, category.name + ":emission_index_soot"] = self.df.loc[
                    k, category.name + ":emission_index_soot:dropin_fuel"
                ] * (self.df.loc[k, category.name + ":share:dropin_fuel"] / 100) + self.df.loc[
                    k, category.name + ":emission_index_soot:hydrogen"
                ] * (
                    self.df.loc[k, category.name + ":share:hydrogen"] / 100
                )

    def _compute_aircraft_share(self):
        # Aircraft share computation
        for category in self.fleet.categories.values():
            # TODO: handling of subcategory

            for key, subcategory in reversed(category.subcategories.items()):
                # TODO: verify aircraft order
                for i, aircraft in reversed(subcategory.aircraft.items()):
                    if (i == list(subcategory.aircraft.keys())[-1]) and (
                        key == list(category.subcategories.keys())[-1]
                    ):
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

                    elif (i == list(subcategory.aircraft.keys())[-1]) and (
                        key != list(category.subcategories.keys())[-1]
                    ):
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
                            + category.subcategories[key + 1].name
                            + ":"
                            + category.subcategories[key + 1].aircraft[0].name
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

            # For a category
            ref_recent_single_aircraft_share = self.df[
                category.name
                + ":"
                + category.subcategories[0].name
                + ":"
                + "recent_reference:single_aircraft_share"
            ]
            if subcategory.aircraft:
                next_aircraft_single_share = self.df[
                    category.name
                    + ":"
                    + category.subcategories[0].name
                    + ":"
                    + subcategory.aircraft[0].name
                    + ":single_aircraft_share"
                ]
            else:
                next_aircraft_single_share = 0.0
            var_name = (
                category.name
                + ":"
                + category.subcategories[0].name
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
                + category.subcategories[0].name
                + ":"
                + "old_reference:aircraft_share"
            )
            self.df[var_name] = ref_old_aircraft_share
        # Dedicated calculation for drop-in fuel and hydrogen
        # if aircraft.energy_type == "DROP_IN_FUEL":
        #     self.df[category.name
        #             + ":"
        #             + subcategory.name
        #             + ":share:dropin_fuel"] = aircraft_share
        #
        # if aircraft.energy_type == "HYDROGEN":
        #     self.df[category.name
        #             + ":"
        #             + subcategory.name
        #             + ":"
        #             + ":share:hydrogen"] = aircraft_share

    def _compute_single_aircraft_share(self):
        # Single aircraft share computation (for obtaining the main plot on fleet renewal)
        for category in self.fleet.categories.values():

            limit = 2
            life_base = 25
            parameter_base = np.log(100 / limit - 1) / (life_base / 2)
            parameter_renewal = np.log(100 / limit - 1) / (category.parameters.life / 2)

            if len(category.subcategories.values()) == 1:
                subcategory = list(category.subcategories.values())[0]
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
                ref_recent_single_aircraft_share = self._compute(
                    float(category.parameters.life),
                    float(year_ref_recent),
                    # Should always be 100% as there is only one subcategory
                    float(subcategory.parameters.share),
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
                    single_aircraft_share = self._compute(
                        float(category.parameters.life),
                        float(aircraft.parameters.entry_into_service_year),
                        # Should always be 100% as there is only one subcategory
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

            elif len(category.subcategories.values()) == 2:

                # We start with last subcategory
                subcategory = list(category.subcategories.values())[-1]

                for i, aircraft in subcategory.aircraft.items():
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
                    if i == 0:
                        oldest_single_aircraft_share = single_aircraft_share

                # We now use the first subcategory
                subcategory = list(category.subcategories.values())[0]

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
                ref_recent_single_aircraft_share = oldest_single_aircraft_share + self._compute(
                    float(category.parameters.life),
                    float(year_ref_recent),
                    100 - oldest_single_aircraft_share,
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
                    single_aircraft_share = oldest_single_aircraft_share + self._compute(
                        float(category.parameters.life),
                        float(aircraft.parameters.entry_into_service_year),
                        100 - oldest_single_aircraft_share,
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

            # If more than two subcategories
            else:
                for key, subcategory in reversed(category.subcategories.items()):
                    # Last subcategory
                    if key == list(category.subcategories.keys())[-1]:
                        for i, aircraft in subcategory.aircraft.items():
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
                            if i == 0:
                                oldest_single_aircraft_share = single_aircraft_share
                    # Initial subcategory
                    elif key == list(category.subcategories.keys())[0]:
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
                        ref_recent_single_aircraft_share = (
                            oldest_single_aircraft_share
                            + self._compute(
                                float(category.parameters.life),
                                float(year_ref_recent),
                                100 - oldest_single_aircraft_share,
                                recent=True,
                            )
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
                            single_aircraft_share = oldest_single_aircraft_share + self._compute(
                                float(category.parameters.life),
                                float(aircraft.parameters.entry_into_service_year),
                                100 - oldest_single_aircraft_share,
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

                    else:
                        for i, aircraft in subcategory.aircraft.items():
                            single_aircraft_share = oldest_single_aircraft_share + self._compute(
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
                            if i == 0:
                                new_oldest_single_aircraft_share = single_aircraft_share
                        oldest_single_aircraft_share = new_oldest_single_aircraft_share
        return subcategory

    def plot(self):
        x = np.linspace(
            self.prospection_start_year,
            self.end_year,
            self.end_year - self.prospection_start_year + 1,
        )

        categories = list(self.fleet.categories.values())

        f, axs = plt.subplots(2, len(categories), figsize=(20, 10))

        for i, category in enumerate(categories):
            # Top plot
            ax = axs[0, i]

            # Initial subcategory
            subcategory = category.subcategories[0]
            # Old reference aircraft
            var_name = (
                category.name + ":" + subcategory.name + ":" + "old_reference:single_aircraft_share"
            )
            ax.fill_between(
                x,
                self.df.loc[self.prospection_start_year : self.end_year, var_name],
                label=subcategory.name + " - Old reference aircraft",
            )

            # Recent reference aircraft
            var_name = (
                category.name
                + ":"
                + subcategory.name
                + ":"
                + "recent_reference:single_aircraft_share"
            )
            ax.fill_between(
                x,
                self.df.loc[self.prospection_start_year : self.end_year, var_name],
                label=subcategory.name + " - Recent reference aircraft",
            )

            for j, subcategory in category.subcategories.items():

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
                    ax.fill_between(
                        x,
                        self.df.loc[self.prospection_start_year : self.end_year, var_name],
                        label=subcategory.name + " - " + aircraft.name,
                    )

            ax.set_xlim(self.prospection_start_year, self.end_year)
            ax.set_ylim(0, 100)
            ax.legend(loc="upper left", prop={"size": 8})
            ax.set_xlabel("Year")
            ax.set_ylabel("Share in fleet [%]")
            ax.set_title(categories[i].name)

            # Bottom plot
            ax = axs[1, i]
            ax.plot(
                x,
                self.df.loc[
                    self.prospection_start_year : self.end_year,
                    category.name + ":energy_consumption",
                ],
            )

            ax.set_xlim(self.prospection_start_year, self.end_year)
            ax.set_xlabel("Year")
            ax.set_ylabel("Fleet mean energy consumption [MJ/ASK]")
            # ax.set_title(categories[i].name)

        plt.plot()
        # plt.savefig("fleet_renewal.pdf")

    def _compute(self, life, entry_into_service_year, share, recent=False):
        x = np.linspace(
            self.historic_start_year, self.end_year, self.end_year - self.historic_start_year + 1
        )

        # Intermediate variable for S-shaped function
        limit = 2
        growth_rate = np.log(100 / limit - 1) / (life / 2)

        if not recent:
            midpoint_year = entry_into_service_year + life / 2
        else:
            midpoint_year = entry_into_service_year

        y_share = share / (1 + np.exp(-growth_rate * (x - midpoint_year)))
        y_share_max = 100 / (1 + np.exp(-growth_rate * (x - midpoint_year)))

        y = np.where(y_share_max < limit, 0.0, y_share)
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
        self.parameters.consumption_evolution = row[AIRCRAFT_COLUMNS[2]]
        self.parameters.nox_evolution = row[AIRCRAFT_COLUMNS[3]]
        self.parameters.soot_evolution = row[AIRCRAFT_COLUMNS[4]]
        self.parameters.doc_non_energy_evolution = row[AIRCRAFT_COLUMNS[5]]
        self.parameters.cruise_altitude = row[AIRCRAFT_COLUMNS[6]]
        self.energy_type = row[AIRCRAFT_COLUMNS[7]]

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
                    12000.0,
                    "DROP_IN_FUEL",
                ]
            ).reshape((1, len(AIRCRAFT_COLUMNS)))
        else:
            aircraft_data = np.array(
                [
                    aircraft.name,
                    aircraft.parameters.entry_into_service_year,
                    aircraft.parameters.consumption_evolution,
                    aircraft.parameters.nox_evolution,
                    aircraft.parameters.soot_evolution,
                    aircraft.parameters.doc_non_energy_evolution,
                    aircraft.parameters.cruise_altitude,
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
        self.ui.layout.width = "1200px"
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
        add_examples_aircraft_and_subcategory=True,
    ):
        self.categories = {}

        # Build default fleet
        self._build_default_fleet(
            add_examples_aircraft_and_subcategory=add_examples_aircraft_and_subcategory
        )

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
        self.ui.layout

    def _update_ui(self):
        if self.ui is not None:
            self.ui.children = (self.tree, self.selected_item.ui)
            if isinstance(self.selected_item, Category):
                self.selected_item.button_add_row.on_click(self._update)
                self.selected_item.button_remove_row.on_click(self._update)
                self.selected_item.datagrid.on_cell_change(self._update)

    def _build_default_fleet(self, add_examples_aircraft_and_subcategory=True):
        # Short range narrow-body
        aircraft_params = AircraftParameters(
            entry_into_service_year=2035,
            consumption_evolution=-15.0,
            nox_evolution=0.0,
            soot_evolution=0.0,
            doc_non_energy_evolution=0.0,
            cruise_altitude=12000.0,
        )

        sr_nb_aircraft_1 = Aircraft(
            "New Short-range Narrow-body 1", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        aircraft_params = AircraftParameters(
            entry_into_service_year=2045,
            consumption_evolution=-30.0,
            nox_evolution=0.0,
            soot_evolution=0.0,
            doc_non_energy_evolution=0.0,
            cruise_altitude=12000.0,
        )

        sr_nb_aircraft_2 = Aircraft(
            "New Short-range Narrow-body 2", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        # Short range regional turboprop
        aircraft_params = AircraftParameters(
            entry_into_service_year=2030,
            consumption_evolution=-20.0,
            nox_evolution=0.0,
            soot_evolution=0.0,
            doc_non_energy_evolution=0.0,
            cruise_altitude=6000.0,
        )

        sr_tp_aircraft_1 = Aircraft(
            "New Regional turboprop 1",
            parameters=aircraft_params,
            energy_type="DROP_IN_FUEL",
        )

        aircraft_params = AircraftParameters(
            entry_into_service_year=2045,
            consumption_evolution=-35.0,
            nox_evolution=0.0,
            soot_evolution=0.0,
            doc_non_energy_evolution=0.0,
            cruise_altitude=6000.0,
        )

        sr_tp_aircraft_2 = Aircraft(
            "New Regional turboprop 2",
            parameters=aircraft_params,
            energy_type="DROP_IN_FUEL",
        )

        # Short range regional turbofan
        aircraft_params = AircraftParameters(
            entry_into_service_year=2035,
            consumption_evolution=-15.0,
            nox_evolution=0.0,
            soot_evolution=0.0,
            doc_non_energy_evolution=0.0,
            cruise_altitude=12000.0,
        )

        sr_tf_aircraft_1 = Aircraft(
            "New Regional turbofan 1",
            parameters=aircraft_params,
            energy_type="DROP_IN_FUEL",
        )

        aircraft_params = AircraftParameters(
            entry_into_service_year=2045,
            consumption_evolution=-30.0,
            nox_evolution=0.0,
            soot_evolution=0.0,
            doc_non_energy_evolution=0.0,
            cruise_altitude=12000.0,
        )

        sr_tf_aircraft_2 = Aircraft(
            "New Regional turbofan 2",
            parameters=aircraft_params,
            energy_type="DROP_IN_FUEL",
        )

        # Short range hydrogen aircraft

        aircraft_params = AircraftParameters(
            entry_into_service_year=2035,
            consumption_evolution=10.0,
            nox_evolution=0.0,
            soot_evolution=-100.0,
            doc_non_energy_evolution=10.0,
            cruise_altitude=12000.0,
        )

        sr_aircraft_hydrogen = Aircraft(
            "New Short-range hydrogen", parameters=aircraft_params, energy_type="HYDROGEN"
        )

        # Medium range
        aircraft_params = AircraftParameters(
            entry_into_service_year=2035,
            consumption_evolution=-15.0,
            nox_evolution=0.0,
            soot_evolution=0.0,
            doc_non_energy_evolution=0.0,
            cruise_altitude=12000.0,
        )

        mr_aircraft_1 = Aircraft(
            "New Medium-range narrow-body 1", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        aircraft_params = AircraftParameters(
            entry_into_service_year=2045,
            consumption_evolution=-30.0,
            nox_evolution=0.0,
            soot_evolution=0.0,
            doc_non_energy_evolution=0.0,
            cruise_altitude=12000.0,
        )

        mr_aircraft_2 = Aircraft(
            "New Medium-range narrow-body 2", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        # Long range
        aircraft_params = AircraftParameters(
            entry_into_service_year=2035,
            consumption_evolution=-15.0,
            nox_evolution=0.0,
            soot_evolution=0.0,
            doc_non_energy_evolution=0.0,
            cruise_altitude=12000.0,
        )

        lr_aircraft_1 = Aircraft(
            "New Long-range wide-body 1", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        aircraft_params = AircraftParameters(
            entry_into_service_year=2045,
            consumption_evolution=-30.0,
            nox_evolution=0.0,
            soot_evolution=0.0,
            doc_non_energy_evolution=0.0,
            cruise_altitude=12000.0,
        )

        lr_aircraft_2 = Aircraft(
            "New Long-range wide-body 2", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        # Short range narrow-body
        if add_examples_aircraft_and_subcategory:
            subcat_params = SubcategoryParameters(share=20.0)
        else:
            subcat_params = SubcategoryParameters(share=100.0)
        sr_nb_cat = SubCategory("SR conventional narrow-body", parameters=subcat_params)
        # Reference aircraft
        # Old
        sr_nb_cat.old_reference_aircraft.entry_into_service_year = 1970
        sr_nb_cat.old_reference_aircraft.energy_per_ask = 110.8 / 73.2 * 0.824  # [MJ/ASK]
        sr_nb_cat.old_reference_aircraft.emission_index_nox = 0.01514
        sr_nb_cat.old_reference_aircraft.emission_index_soot = 3e-5
        sr_nb_cat.old_reference_aircraft.doc_non_energy_base = 0.045
        sr_nb_cat.old_reference_aircraft.cruise_altitude = 12000.0

        # Recent
        sr_nb_cat.recent_reference_aircraft.entry_into_service_year = 2007.13
        sr_nb_cat.recent_reference_aircraft.energy_per_ask = 84.2 / 73.2 * 0.824  # [MJ/ASK]
        sr_nb_cat.recent_reference_aircraft.emission_index_nox = 0.01514
        sr_nb_cat.recent_reference_aircraft.emission_index_soot = 3e-5
        sr_nb_cat.recent_reference_aircraft.doc_non_energy_base = 0.045
        sr_nb_cat.recent_reference_aircraft.cruise_altitude = 12000.0

        if add_examples_aircraft_and_subcategory:
            sr_nb_cat.add_aircraft(aircraft=sr_nb_aircraft_1)
            sr_nb_cat.add_aircraft(aircraft=sr_nb_aircraft_2)

        # Short range hydrogen aircraft
        if add_examples_aircraft_and_subcategory:
            subcat_params = SubcategoryParameters(share=50.0)
            sr_subcat_hydrogen = SubCategory(
                "SR hydrogen conventional narrow-body", parameters=subcat_params
            )

        if add_examples_aircraft_and_subcategory:
            sr_subcat_hydrogen.add_aircraft(aircraft=sr_aircraft_hydrogen)

        # Short range regional turboprop
        if add_examples_aircraft_and_subcategory:
            subcat_params = SubcategoryParameters(share=30.0)
            sr_rp_cat = SubCategory("SR regional turboprop", parameters=subcat_params)
        # Reference aircraft
        # Old
        # sr_rp_cat.old_reference_aircraft.entry_into_service_year = 1970
        # sr_rp_cat.old_reference_aircraft.energy_per_ask = 101.2 / 73.2 * 0.824  # [MJ/ASK]
        # sr_rp_cat.old_reference_aircraft.emission_index_nox = 0.01514
        # sr_rp_cat.old_reference_aircraft.emission_index_soot = 3e-5
        # sr_rp_cat.old_reference_aircraft.cruise_altitude = 6000.0

        # Recent
        # sr_rp_cat.recent_reference_aircraft.entry_into_service_year = 2005
        # sr_rp_cat.recent_reference_aircraft.energy_per_ask = 101.2 / 73.2 * 0.824  # [MJ/ASK]
        # sr_rp_cat.recent_reference_aircraft.emission_index_nox = 0.01514
        # sr_rp_cat.recent_reference_aircraft.emission_index_soot = 3e-5
        # sr_rp_cat.recent_reference_aircraft.cruise_altitude = 6000.0

        if add_examples_aircraft_and_subcategory:
            sr_rp_cat.add_aircraft(aircraft=sr_tp_aircraft_1)
            sr_rp_cat.add_aircraft(aircraft=sr_tp_aircraft_2)

        # Short range regional turbofan
        subcat_params = SubcategoryParameters(share=0.0)
        sr_tf_cat = SubCategory("SR regional turbofan", parameters=subcat_params)
        # Reference aircraft
        # Old
        # sr_tf_cat.old_reference_aircraft.entry_into_service_year = 1970
        # sr_tf_cat.old_reference_aircraft.energy_per_ask = 192.9 / 73.2 * 0.824  # [MJ/ASK]
        # sr_tf_cat.old_reference_aircraft.emission_index_nox = 0.01514
        # sr_tf_cat.old_reference_aircraft.emission_index_soot = 3e-5
        # sr_tf_cat.old_reference_aircraft.cruise_altitude = 12000.0

        # Recent
        # sr_tf_cat.recent_reference_aircraft.entry_into_service_year = 2000
        # sr_tf_cat.recent_reference_aircraft.energy_per_ask = 192.9 / 73.2 * 0.824  # [MJ/ASK]
        # sr_tf_cat.recent_reference_aircraft.emission_index_nox = 0.01514
        # sr_tf_cat.recent_reference_aircraft.emission_index_soot = 3e-5
        # sr_tf_cat.recent_reference_aircraft.cruise_altitude = 12000.0

        # sr_tf_cat.add_aircraft(aircraft=sr_tf_aircraft_1)
        # sr_tf_cat.add_aircraft(aircraft=sr_tf_aircraft_2)

        # Short range
        cat_params = CategoryParameters(life=25)
        sr_cat = Category("Short Range", parameters=cat_params)
        sr_cat.add_subcategory(subcategory=sr_nb_cat)
        if add_examples_aircraft_and_subcategory:
            sr_cat.add_subcategory(subcategory=sr_rp_cat)
            sr_cat.add_subcategory(subcategory=sr_subcat_hydrogen)
        # sr_cat.add_subcategory(subcategory=sr_tf_cat)

        # Medium range
        subcat_params = SubcategoryParameters(share=100.0)
        mr_subcat = SubCategory("MR conventional narrow-body", parameters=subcat_params)
        # Reference aircraft
        # Old
        mr_subcat.old_reference_aircraft.entry_into_service_year = 1970
        mr_subcat.old_reference_aircraft.energy_per_ask = 81.4 / 73.2 * 0.824  # [MJ/ASK]
        mr_subcat.old_reference_aircraft.emission_index_nox = 0.01514
        mr_subcat.old_reference_aircraft.emission_index_soot = 3e-5
        mr_subcat.old_reference_aircraft.doc_non_energy_base = 0.028
        mr_subcat.old_reference_aircraft.cruise_altitude = 12000.0

        # Recent
        mr_subcat.recent_reference_aircraft.entry_into_service_year = 2010.35
        mr_subcat.recent_reference_aircraft.energy_per_ask = 62.0 / 73.2 * 0.824  # [MJ/ASK]
        mr_subcat.recent_reference_aircraft.emission_index_nox = 0.01514
        mr_subcat.recent_reference_aircraft.emission_index_soot = 3e-5
        mr_subcat.recent_reference_aircraft.doc_non_energy_base = 0.028
        mr_subcat.recent_reference_aircraft.cruise_altitude = 12000.0

        if add_examples_aircraft_and_subcategory:
            mr_subcat.add_aircraft(aircraft=mr_aircraft_1)
            mr_subcat.add_aircraft(aircraft=mr_aircraft_2)

        cat_params = CategoryParameters(life=25)
        mr_cat = Category(name="Medium Range", parameters=cat_params)
        mr_cat.add_subcategory(subcategory=mr_subcat)

        # Long range
        subcat_params = SubcategoryParameters(share=100.0)
        lr_subcat = SubCategory("LR conventional wide-body", parameters=subcat_params)
        # Reference aircraft
        # Old
        lr_subcat.old_reference_aircraft.entry_into_service_year = 1970
        lr_subcat.old_reference_aircraft.energy_per_ask = 96.65 / 73.2 * 0.824  # [MJ/ASK]
        lr_subcat.old_reference_aircraft.emission_index_nox = 0.01514
        lr_subcat.old_reference_aircraft.emission_index_soot = 3e-5
        lr_subcat.old_reference_aircraft.doc_non_energy_base = 0.023
        lr_subcat.old_reference_aircraft.cruise_altitude = 12000.0

        # Recent
        lr_subcat.recent_reference_aircraft.entry_into_service_year = 2009.36
        lr_subcat.recent_reference_aircraft.energy_per_ask = 73.45 / 73.2 * 0.824  # [MJ/ASK]
        lr_subcat.recent_reference_aircraft.emission_index_nox = 0.01514
        lr_subcat.recent_reference_aircraft.emission_index_soot = 3e-5
        lr_subcat.recent_reference_aircraft.doc_non_energy_base = 0.023
        lr_subcat.recent_reference_aircraft.cruise_altitude = 12000.0

        if add_examples_aircraft_and_subcategory:
            lr_subcat.add_aircraft(aircraft=lr_aircraft_1)
            lr_subcat.add_aircraft(aircraft=lr_aircraft_2)

        cat_params = CategoryParameters(life=25)
        lr_cat = Category("Long Range", parameters=cat_params)
        lr_cat.add_subcategory(subcategory=lr_subcat)

        self.categories[sr_cat.name] = sr_cat
        self.categories[mr_cat.name] = mr_cat
        self.categories[lr_cat.name] = lr_cat

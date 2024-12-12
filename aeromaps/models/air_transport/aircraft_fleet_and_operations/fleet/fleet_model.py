import numpy as np
from dataclasses import dataclass
import warnings

import pandas as pd
import ipydatagrid as dg
from ipytree import Tree, Node
import matplotlib.pyplot as plt

import ipywidgets as ipw

from aeromaps.models.base import AeroMAPSModel

AIRCRAFT_COLUMNS = [
    "Name",
    "EIS Year",
    "Consumption evolution [%]",
    "NOx evolution [%]",
    "Soot evolution [%]",
    "Non-Energy DOC evolution [%]",
    "Cruise altitude [m]",
    "Energy type",
    "Hybridization factor",
    "Average ASK per year",
    "Manufacturing Cost [M€]",
    "Non Recurring Costs [M€]",
    "Operational Empty Weight [t]",
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
    hybridization_factor: float = 0.0
    ask_year: float = None
    nrc_cost: float = None
    rc_cost: float = None
    oew: float = None
    full_name: str = None


@dataclass
class ReferenceAircraftParameters:
    energy_per_ask: float = None
    emission_index_nox: float = None
    emission_index_soot: float = None
    doc_non_energy_base: float = None
    entry_into_service_year: float = None
    cruise_altitude: float = None
    hybridization_factor: float = 0.0
    ask_year: float = None
    nrc_cost: float = None
    rc_cost: float = None
    oew: float = None
    full_name: str = None


@dataclass
class SubcategoryParameters:
    share: float = None


@dataclass
class CategoryParameters:
    life: float
    limit: float = 2


class FleetModel(AeroMAPSModel):
    def __init__(self, name="fleet_model", fleet=None, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.fleet = fleet

    def compute(
        self,
    ):
        # Start from empty dataframe (necessary for multiple runs of the model)
        self.df = pd.DataFrame(index=self.df.index)

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

    def _compute_single_aircraft_share(self):
        temp_dict = {}

        for category in self.fleet.categories.values():
            limit = 2
            life_base = 25
            parameter_base = np.log(100 / limit - 1) / (life_base / 2)
            parameter_renewal = np.log(100 / limit - 1) / (category.parameters.life / 2)

            if len(category.subcategories) == 1:
                subcategory = list(category.subcategories.values())[0]
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
                    float(subcategory.parameters.share),
                    recent=True,
                )
                temp_dict[
                    f"{category.name}:{subcategory.name}:recent_reference:single_aircraft_share"
                ] = ref_recent_single_aircraft_share

                ref_old_single_aircraft_share = 100
                temp_dict[
                    f"{category.name}:{subcategory.name}:old_reference:single_aircraft_share"
                ] = ref_old_single_aircraft_share

                for aircraft in subcategory.aircraft.values():
                    single_aircraft_share = self._compute(
                        float(category.parameters.life),
                        float(aircraft.parameters.entry_into_service_year),
                        float(subcategory.parameters.share),
                    )
                    temp_dict[
                        f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                    ] = single_aircraft_share

            elif len(category.subcategories) == 2:
                subcategory = list(category.subcategories.values())[-1]
                for i, aircraft in subcategory.aircraft.items():
                    single_aircraft_share = self._compute(
                        float(category.parameters.life),
                        float(aircraft.parameters.entry_into_service_year),
                        float(subcategory.parameters.share),
                    )
                    temp_dict[
                        f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                    ] = single_aircraft_share
                    if i == 0:
                        oldest_single_aircraft_share = single_aircraft_share

                subcategory = list(category.subcategories.values())[0]
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
                temp_dict[
                    f"{category.name}:{subcategory.name}:recent_reference:single_aircraft_share"
                ] = ref_recent_single_aircraft_share

                ref_old_single_aircraft_share = 100
                temp_dict[
                    f"{category.name}:{subcategory.name}:old_reference:single_aircraft_share"
                ] = ref_old_single_aircraft_share

                for aircraft in subcategory.aircraft.values():
                    single_aircraft_share = oldest_single_aircraft_share + self._compute(
                        float(category.parameters.life),
                        float(aircraft.parameters.entry_into_service_year),
                        100 - oldest_single_aircraft_share,
                    )
                    temp_dict[
                        f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                    ] = single_aircraft_share

            else:
                for key, subcategory in reversed(category.subcategories.items()):
                    if key == list(category.subcategories.keys())[-1]:
                        for i, aircraft in subcategory.aircraft.items():
                            single_aircraft_share = self._compute(
                                float(category.parameters.life),
                                float(aircraft.parameters.entry_into_service_year),
                                float(subcategory.parameters.share),
                            )
                            temp_dict[
                                f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                            ] = single_aircraft_share
                            if i == 0:
                                oldest_single_aircraft_share = single_aircraft_share

                    elif key == list(category.subcategories.keys())[0]:
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
                        temp_dict[
                            f"{category.name}:{subcategory.name}:recent_reference:single_aircraft_share"
                        ] = ref_recent_single_aircraft_share

                        ref_old_single_aircraft_share = 100
                        temp_dict[
                            f"{category.name}:{subcategory.name}:old_reference:single_aircraft_share"
                        ] = ref_old_single_aircraft_share

                        for aircraft in subcategory.aircraft.values():
                            single_aircraft_share = oldest_single_aircraft_share + self._compute(
                                float(category.parameters.life),
                                float(aircraft.parameters.entry_into_service_year),
                                100 - oldest_single_aircraft_share,
                            )
                            temp_dict[
                                f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                            ] = single_aircraft_share

                    else:
                        for i, aircraft in subcategory.aircraft.items():
                            single_aircraft_share = oldest_single_aircraft_share + self._compute(
                                float(category.parameters.life),
                                float(aircraft.parameters.entry_into_service_year),
                                float(subcategory.parameters.share),
                            )
                            temp_dict[
                                f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                            ] = single_aircraft_share
                            if i == 0:
                                new_oldest_single_aircraft_share = single_aircraft_share
                        oldest_single_aircraft_share = new_oldest_single_aircraft_share

        final_dict = {
            key: np.array(values) if isinstance(values, list) else values
            for key, values in temp_dict.items()
        }

        final_df = pd.DataFrame(final_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

    def _compute_aircraft_share(self):
        temp_dict = {}

        for category in self.fleet.categories.values():
            for key, subcategory in reversed(category.subcategories.items()):
                for i, aircraft in reversed(subcategory.aircraft.items()):
                    subcategory_key = f"{category.name}:{subcategory.name}:{aircraft.name}"

                    if (i == list(subcategory.aircraft.keys())[-1]) and (
                        key == list(category.subcategories.keys())[-1]
                    ):
                        aircraft_share = self.df[f"{subcategory_key}:single_aircraft_share"].values
                    elif (i == list(subcategory.aircraft.keys())[-1]) and (
                        key != list(category.subcategories.keys())[-1]
                    ):
                        single_aircraft_share = self.df[
                            f"{subcategory_key}:single_aircraft_share"
                        ].values
                        single_aircraft_share_n1 = self.df[
                            f"{category.name}:{category.subcategories[key + 1].name}:{category.subcategories[key + 1].aircraft[0].name}:single_aircraft_share"
                        ].values
                        aircraft_share = single_aircraft_share - single_aircraft_share_n1
                    else:
                        single_aircraft_share = self.df[
                            f"{subcategory_key}:single_aircraft_share"
                        ].values
                        single_aircraft_share_n1 = self.df[
                            f"{category.name}:{subcategory.name}:{subcategory.aircraft[i + 1].name}:single_aircraft_share"
                        ].values
                        aircraft_share = single_aircraft_share - single_aircraft_share_n1

                    temp_dict[f"{subcategory_key}:aircraft_share"] = aircraft_share

            ref_recent_single_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:recent_reference:single_aircraft_share"
            ].values

            if subcategory.aircraft:
                next_aircraft_single_share = self.df[
                    f"{category.name}:{category.subcategories[0].name}:{subcategory.aircraft[0].name}:single_aircraft_share"
                ].values
            else:
                next_aircraft_single_share = np.zeros_like(ref_recent_single_aircraft_share)

            ref_recent_aircraft_share = (
                ref_recent_single_aircraft_share - next_aircraft_single_share
            )
            temp_dict[
                f"{category.name}:{category.subcategories[0].name}:recent_reference:aircraft_share"
            ] = ref_recent_aircraft_share

            ref_old_aircraft_share = 100 - ref_recent_single_aircraft_share
            temp_dict[
                f"{category.name}:{category.subcategories[0].name}:old_reference:aircraft_share"
            ] = ref_old_aircraft_share

        final_dict = {
            key: np.array(values) if isinstance(values, list) else values
            for key, values in temp_dict.items()
        }

        final_df = pd.DataFrame(final_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

    def _compute_energy_consumption_and_share_wrt_energy_type(self):
        temp_dict = {}

        for category in self.fleet.categories.values():
            ref_old_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:old_reference:aircraft_share"
            ].values
            ref_recent_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:recent_reference:aircraft_share"
            ].values

            recent_reference_aircraft_energy_consumption = category.subcategories[
                0
            ].recent_reference_aircraft.energy_per_ask

            for i, subcategory in category.subcategories.items():
                subcategory_key = f"{category.name}:{subcategory.name}"

                if i == 0:
                    initial_energy_consumption = (
                        subcategory.old_reference_aircraft.energy_per_ask
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.energy_per_ask
                        * ref_recent_aircraft_share
                        / 100
                    )
                    initial_share = ref_old_aircraft_share + ref_recent_aircraft_share
                else:
                    initial_energy_consumption = np.zeros_like(ref_old_aircraft_share)
                    initial_share = np.zeros_like(ref_old_aircraft_share)

                temp_dict[f"{subcategory_key}:energy_consumption"] = (
                    initial_energy_consumption.copy()
                )
                temp_dict[f"{subcategory_key}:energy_consumption:dropin_fuel"] = (
                    initial_energy_consumption.copy()
                )
                temp_dict[f"{subcategory_key}:energy_consumption:hydrogen"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:energy_consumption:electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:energy_consumption:hybrid_electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:share:total"] = initial_share.copy()
                temp_dict[f"{subcategory_key}:share:dropin_fuel"] = initial_share.copy()
                temp_dict[f"{subcategory_key}:share:hydrogen"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:share:electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:share:hybrid_electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )

                for aircraft in subcategory.aircraft.values():
                    aircraft_share = self.df[
                        f"{subcategory_key}:{aircraft.name}:aircraft_share"
                    ].values

                    energy_consumption = (
                        recent_reference_aircraft_energy_consumption
                        * (1 + float(aircraft.parameters.consumption_evolution) / 100)
                        * aircraft_share
                        / 100
                    )

                    temp_dict[f"{subcategory_key}:share:total"] += aircraft_share
                    temp_dict[f"{subcategory_key}:energy_consumption"] += energy_consumption

                    if aircraft.energy_type == "DROP_IN_FUEL":
                        temp_dict[f"{subcategory_key}:share:dropin_fuel"] += aircraft_share
                        temp_dict[f"{subcategory_key}:energy_consumption:dropin_fuel"] += (
                            energy_consumption
                        )

                    if aircraft.energy_type == "HYDROGEN":
                        temp_dict[f"{subcategory_key}:share:hydrogen"] += aircraft_share
                        temp_dict[f"{subcategory_key}:energy_consumption:hydrogen"] += (
                            energy_consumption
                        )

                    if aircraft.energy_type == "ELECTRIC":
                        temp_dict[f"{subcategory_key}:share:electric"] += aircraft_share
                        temp_dict[f"{subcategory_key}:energy_consumption:electric"] += (
                            energy_consumption
                        )

                    if aircraft.energy_type == "HYBRID_ELECTRIC":
                        hybridization_factor = float(aircraft.parameters.hybridization_factor)
                        temp_dict[f"{subcategory_key}:share:dropin_fuel"] += (
                            1 - hybridization_factor
                        ) * aircraft_share
                        temp_dict[f"{subcategory_key}:share:electric"] += (
                            hybridization_factor * aircraft_share
                        )
                        temp_dict[f"{subcategory_key}:energy_consumption:hybrid_electric"] += (
                            energy_consumption
                        )
                        temp_dict[f"{subcategory_key}:energy_consumption:dropin_fuel"] += (
                            1 - hybridization_factor
                        ) * energy_consumption
                        temp_dict[f"{subcategory_key}:energy_consumption:electric"] += (
                            hybridization_factor * energy_consumption
                        )

                for energy_type in ["dropin_fuel", "hydrogen", "electric", "hybrid_electric"]:
                    category_share_key = f"{category.name}:share:{energy_type}"
                    subcategory_share_key = f"{subcategory_key}:share:{energy_type}"
                    if category_share_key in temp_dict:
                        temp_dict[category_share_key] += temp_dict[subcategory_share_key]
                    else:
                        temp_dict[category_share_key] = temp_dict[subcategory_share_key].copy()

        final_dict = {
            key: np.array(values) if isinstance(values, list) else values
            for key, values in temp_dict.items()
        }

        final_df = pd.DataFrame(final_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

    def _compute_doc_non_energy(self):
        temp_dict = {}

        for category in self.fleet.categories.values():
            ref_old_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:old_reference:aircraft_share"
            ].values
            ref_recent_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:recent_reference:aircraft_share"
            ].values

            recent_reference_aircraft_doc_non_energy = category.subcategories[
                0
            ].recent_reference_aircraft.doc_non_energy_base

            for i, subcategory in category.subcategories.items():
                subcategory_key = f"{category.name}:{subcategory.name}"

                if i == 0:
                    initial_doc_non_energy = (
                        subcategory.old_reference_aircraft.doc_non_energy_base
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.doc_non_energy_base
                        * ref_recent_aircraft_share
                        / 100
                    )
                else:
                    initial_doc_non_energy = np.zeros_like(ref_old_aircraft_share)

                temp_dict[f"{subcategory_key}:doc_non_energy"] = initial_doc_non_energy.copy()
                temp_dict[f"{subcategory_key}:doc_non_energy:dropin_fuel"] = (
                    initial_doc_non_energy.copy()
                )
                temp_dict[f"{subcategory_key}:doc_non_energy:hydrogen"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:doc_non_energy:electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:doc_non_energy:hybrid_electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )

                for aircraft in subcategory.aircraft.values():
                    aircraft_share = self.df[
                        f"{subcategory_key}:{aircraft.name}:aircraft_share"
                    ].values

                    doc_non_energy = (
                        recent_reference_aircraft_doc_non_energy
                        * (1 + float(aircraft.parameters.doc_non_energy_evolution) / 100)
                        * aircraft_share
                        / 100
                    )

                    temp_dict[f"{subcategory_key}:doc_non_energy"] += doc_non_energy

                    if aircraft.energy_type == "DROP_IN_FUEL":
                        temp_dict[f"{subcategory_key}:doc_non_energy:dropin_fuel"] += doc_non_energy

                    if aircraft.energy_type == "HYDROGEN":
                        temp_dict[f"{subcategory_key}:doc_non_energy:hydrogen"] += doc_non_energy

                    if aircraft.energy_type == "ELECTRIC":
                        temp_dict[f"{subcategory_key}:doc_non_energy:electric"] += doc_non_energy

                    if aircraft.energy_type == "HYBRID_ELECTRIC":
                        temp_dict[f"{subcategory_key}:doc_non_energy:hybrid_electric"] += (
                            doc_non_energy
                        )

            # Summing up doc_non_energy for categories
            for energy_type in ["dropin_fuel", "hydrogen", "electric", "hybrid_electric"]:
                category_doc_key = f"{category.name}:doc_non_energy:{energy_type}"
                subcategory_doc_key = f"{subcategory_key}:doc_non_energy:{energy_type}"
                if category_doc_key in temp_dict:
                    temp_dict[category_doc_key] += temp_dict[subcategory_doc_key]
                else:
                    temp_dict[category_doc_key] = temp_dict[subcategory_doc_key].copy()

        final_dict = {
            key: np.array(values) if isinstance(values, list) else values
            for key, values in temp_dict.items()
        }

        final_df = pd.DataFrame(final_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

    def _compute_non_co2_emission_index(self):
        # Non-CO2 (NOx and soot) emission index calculations for drop-in fuel and hydrogen
        for category in self.fleet.categories.values():
            # Reference aircraft information
            ref_old_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:old_reference:aircraft_share"
            ]
            ref_recent_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:recent_reference:aircraft_share"
            ]

            # Use the first subcategory's recent reference aircraft emission indices
            recent_reference_aircraft_emission_index_nox = category.subcategories[
                0
            ].recent_reference_aircraft.emission_index_nox
            recent_reference_aircraft_emission_index_soot = category.subcategories[
                0
            ].recent_reference_aircraft.emission_index_soot

            for i, subcategory in category.subcategories.items():
                subcategory_key = f"{category.name}:{subcategory.name}"
                if i == 0:
                    initial_nox = (
                        subcategory.old_reference_aircraft.emission_index_nox
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.emission_index_nox
                        * ref_recent_aircraft_share
                        / 100
                    )
                    initial_soot = (
                        subcategory.old_reference_aircraft.emission_index_soot
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.emission_index_soot
                        * ref_recent_aircraft_share
                        / 100
                    )
                else:
                    initial_nox = np.zeros_like(ref_old_aircraft_share)
                    initial_soot = np.zeros_like(ref_old_aircraft_share)

                # Initialize emission index columns
                self.df[f"{subcategory_key}:emission_index_nox"] = initial_nox
                self.df[f"{subcategory_key}:emission_index_soot"] = initial_soot
                self.df[f"{subcategory_key}:emission_index_nox:dropin_fuel"] = initial_nox.copy()
                self.df[f"{subcategory_key}:emission_index_nox:hydrogen"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                self.df[f"{subcategory_key}:emission_index_nox:electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                self.df[f"{subcategory_key}:emission_index_nox:hybrid_electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                self.df[f"{subcategory_key}:emission_index_soot:dropin_fuel"] = initial_soot.copy()
                self.df[f"{subcategory_key}:emission_index_soot:hydrogen"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                self.df[f"{subcategory_key}:emission_index_soot:electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                self.df[f"{subcategory_key}:emission_index_soot:hybrid_electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )

                for aircraft in subcategory.aircraft.values():
                    aircraft_share_key = f"{subcategory_key}:{aircraft.name}:aircraft_share"
                    if aircraft_share_key in self.df.columns:
                        for idx in self.df.index:
                            aircraft_share = self.df.at[idx, aircraft_share_key]
                            if aircraft_share != 0.0:
                                evolution_nox = 1 + float(aircraft.parameters.nox_evolution) / 100
                                evolution_soot = 1 + float(aircraft.parameters.soot_evolution) / 100

                                self.df.at[idx, f"{subcategory_key}:emission_index_nox"] += (
                                    recent_reference_aircraft_emission_index_nox
                                    * evolution_nox
                                    * aircraft_share
                                    / 100
                                )
                                self.df.at[idx, f"{subcategory_key}:emission_index_soot"] += (
                                    recent_reference_aircraft_emission_index_soot
                                    * evolution_soot
                                    * aircraft_share
                                    / 100
                                )

                                if aircraft.energy_type == "DROP_IN_FUEL":
                                    self.df.at[
                                        idx, f"{subcategory_key}:emission_index_nox:dropin_fuel"
                                    ] += (
                                        recent_reference_aircraft_emission_index_nox
                                        * evolution_nox
                                        * aircraft_share
                                        / 100
                                    )
                                    self.df.at[
                                        idx, f"{subcategory_key}:emission_index_soot:dropin_fuel"
                                    ] += (
                                        recent_reference_aircraft_emission_index_soot
                                        * evolution_soot
                                        * aircraft_share
                                        / 100
                                    )
                                elif aircraft.energy_type == "HYDROGEN":
                                    self.df.at[
                                        idx, f"{subcategory_key}:emission_index_nox:hydrogen"
                                    ] += (
                                        recent_reference_aircraft_emission_index_nox
                                        * evolution_nox
                                        * aircraft_share
                                        / 100
                                    )
                                elif aircraft.energy_type == "ELECTRIC":
                                    self.df.at[
                                        idx, f"{subcategory_key}:emission_index_nox:electric"
                                    ] += (
                                        recent_reference_aircraft_emission_index_nox
                                        * evolution_nox
                                        * aircraft_share
                                        / 100
                                    )
                                elif aircraft.energy_type == "HYBRID_ELECTRIC":
                                    self.df.at[
                                        idx, f"{subcategory_key}:emission_index_nox:hybrid_electric"
                                    ] += (
                                        recent_reference_aircraft_emission_index_nox
                                        * evolution_nox
                                        * aircraft_share
                                        / 100
                                    )
                                    self.df.at[
                                        idx,
                                        f"{subcategory_key}:emission_index_soot:hybrid_electric",
                                    ] += (
                                        recent_reference_aircraft_emission_index_soot
                                        * evolution_soot
                                        * aircraft_share
                                        / 100
                                    )

            # Aggregating results for each category
            temp_dict = {
                key: np.zeros_like(self.df.index, dtype=float)
                for key in [
                    f"{category.name}:emission_index_nox",
                    f"{category.name}:emission_index_soot",
                    f"{category.name}:emission_index_nox:dropin_fuel",
                    f"{category.name}:emission_index_nox:hydrogen",
                    f"{category.name}:emission_index_nox:electric",
                    f"{category.name}:emission_index_nox:hybrid_electric",
                    f"{category.name}:emission_index_soot:dropin_fuel",
                    f"{category.name}:emission_index_soot:hydrogen",
                    f"{category.name}:emission_index_soot:electric",
                    f"{category.name}:emission_index_soot:hybrid_electric",
                ]
            }

            for subcategory in category.subcategories.values():
                subcategory_key = f"{category.name}:{subcategory.name}"
                for idx in self.df.index:
                    for emission_type in ["nox", "soot"]:
                        for energy_type in [
                            "dropin_fuel",
                            "hydrogen",
                            "electric",
                            "hybrid_electric",
                        ]:
                            key = f"{subcategory_key}:emission_index_{emission_type}:{energy_type}"
                            if key in self.df.columns:
                                temp_dict[
                                    f"{category.name}:emission_index_{emission_type}:{energy_type}"
                                ][self.df.index.get_loc(idx)] += self.df.at[idx, key]

            # Final aggregation
            for idx in self.df.index:
                dropin_fuel_share = self.df.at[idx, f"{category.name}:share:dropin_fuel"]
                hydrogen_share = self.df.at[idx, f"{category.name}:share:hydrogen"]
                electric_share = self.df.at[idx, f"{category.name}:share:electric"]
                hybrid_electric_share = self.df.at[idx, f"{category.name}:share:hybrid_electric"]

                total_share = (
                    dropin_fuel_share + hydrogen_share + electric_share + hybrid_electric_share
                )
                if total_share > 0:
                    self.df.at[idx, f"{category.name}:emission_index_nox"] = (
                        temp_dict[f"{category.name}:emission_index_nox:dropin_fuel"][
                            self.df.index.get_loc(idx)
                        ]
                        * (dropin_fuel_share / 100)
                        + temp_dict[f"{category.name}:emission_index_nox:hydrogen"][
                            self.df.index.get_loc(idx)
                        ]
                        * (hydrogen_share / 100)
                        + temp_dict[f"{category.name}:emission_index_nox:electric"][
                            self.df.index.get_loc(idx)
                        ]
                        * (electric_share / 100)
                        + temp_dict[f"{category.name}:emission_index_nox:hybrid_electric"][
                            self.df.index.get_loc(idx)
                        ]
                        * (hybrid_electric_share / 100)
                    )
                    self.df.at[idx, f"{category.name}:emission_index_soot"] = (
                        temp_dict[f"{category.name}:emission_index_soot:dropin_fuel"][
                            self.df.index.get_loc(idx)
                        ]
                        * (dropin_fuel_share / 100)
                        + temp_dict[f"{category.name}:emission_index_soot:hydrogen"][
                            self.df.index.get_loc(idx)
                        ]
                        * (hydrogen_share / 100)
                        + temp_dict[f"{category.name}:emission_index_soot:electric"][
                            self.df.index.get_loc(idx)
                        ]
                        * (electric_share / 100)
                        + temp_dict[f"{category.name}:emission_index_soot:hybrid_electric"][
                            self.df.index.get_loc(idx)
                        ]
                        * (hybrid_electric_share / 100)
                    )

    def _compute_mean_energy_consumption_per_category_wrt_energy_type(self):
        for category in self.fleet.categories.values():
            # Mean energy consumption per category
            # Initialization
            self.df[category.name + ":energy_consumption:dropin_fuel"] = 0.0
            self.df[category.name + ":energy_consumption:hydrogen"] = 0.0
            self.df[category.name + ":energy_consumption:electric"] = 0.0
            self.df[category.name + ":energy_consumption:hybrid_electric"] = 0.0
            # Calculation
            for subcategory in category.subcategories.values():
                # TODO: verify aircraft order
                for k in self.df.index:
                    if self.df.loc[k, category.name + ":share:dropin_fuel"] != 0.0:
                        self.df.loc[k, category.name + ":energy_consumption:dropin_fuel"] += (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":energy_consumption:dropin_fuel",
                            ]
                            / (self.df.loc[k, category.name + ":share:dropin_fuel"] / 100)
                        )
                    else:
                        self.df.loc[k, category.name + ":energy_consumption:dropin_fuel"] = 0.0

                    if self.df.loc[k, category.name + ":share:hydrogen"] != 0.0:
                        self.df.loc[k, category.name + ":energy_consumption:hydrogen"] += (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":energy_consumption:hydrogen",
                            ]
                            / (self.df.loc[k, category.name + ":share:hydrogen"] / 100)
                        )
                    else:
                        self.df.loc[k, category.name + ":energy_consumption:hydrogen"] = 0.0

                    if self.df.loc[k, category.name + ":share:electric"] != 0.0:
                        self.df.loc[k, category.name + ":energy_consumption:electric"] += (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":energy_consumption:electric",
                            ]
                            / (self.df.loc[k, category.name + ":share:electric"] / 100)
                        )
                    else:
                        self.df.loc[k, category.name + ":energy_consumption:electric"] = 0.0

                    if self.df.loc[k, category.name + ":share:hybrid_electric"] != 0.0:
                        self.df.loc[k, category.name + ":energy_consumption:hybrid_electric"] += (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":energy_consumption:hybrid_electric",
                            ]
                            / (self.df.loc[k, category.name + ":share:hybrid_electric"] / 100)
                        )
                    else:
                        self.df.loc[k, category.name + ":energy_consumption:hybrid_electric"] = 0.0

            # Mean consumption
            for k in self.df.index:
                self.df.loc[k, category.name + ":energy_consumption"] = (
                    self.df.loc[k, category.name + ":energy_consumption:dropin_fuel"]
                    * (self.df.loc[k, category.name + ":share:dropin_fuel"] / 100)
                    + self.df.loc[k, category.name + ":energy_consumption:hydrogen"]
                    * (self.df.loc[k, category.name + ":share:hydrogen"] / 100)
                    + self.df.loc[k, category.name + ":energy_consumption:electric"]
                    * (self.df.loc[k, category.name + ":share:electric"] / 100)
                    + self.df.loc[k, category.name + ":energy_consumption:hybrid_electric"]
                    * (self.df.loc[k, category.name + ":share:hybrid_electric"] / 100)
                )

    def _compute_mean_doc_non_energy(self):
        for category in self.fleet.categories.values():
            # Mean non energy DOC per category
            # Initialization
            self.df[category.name + ":doc_non_energy:dropin_fuel"] = 0.0
            self.df[category.name + ":doc_non_energy:hydrogen"] = 0.0
            self.df[category.name + ":doc_non_energy:electric"] = 0.0
            self.df[category.name + ":doc_non_energy:hybrid_electric"] = 0.0
            # Calculation
            for subcategory in category.subcategories.values():
                # TODO: verify aircraft order
                for k in self.df.index:
                    if self.df.loc[k, category.name + ":share:dropin_fuel"] != 0.0:
                        self.df.loc[k, category.name + ":doc_non_energy:dropin_fuel"] += (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":doc_non_energy:dropin_fuel",
                            ]
                            / (self.df.loc[k, category.name + ":share:dropin_fuel"] / 100)
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

                    if self.df.loc[k, category.name + ":share:electric"] != 0.0:
                        self.df.loc[k, category.name + ":doc_non_energy:electric"] += self.df.loc[
                            k,
                            category.name + ":" + subcategory.name + ":doc_non_energy:electric",
                        ] / (self.df.loc[k, category.name + ":share:electric"] / 100)
                    else:
                        self.df.loc[k, category.name + ":doc_non_energy:electric"] = 0.0

                    if self.df.loc[k, category.name + ":share:hybrid_electric"] != 0.0:
                        self.df.loc[k, category.name + ":doc_non_energy:hybrid_electric"] += (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":doc_non_energy:hybrid_electric",
                            ]
                            / (self.df.loc[k, category.name + ":share:hybrid_electric"] / 100)
                        )
                    else:
                        self.df.loc[k, category.name + ":doc_non_energy:hybrid_electric"] = 0.0

            # Mean non energy DOC
            for k in self.df.index:
                self.df.loc[k, category.name + ":doc_non_energy"] = (
                    self.df.loc[k, category.name + ":doc_non_energy:dropin_fuel"]
                    * (self.df.loc[k, category.name + ":share:dropin_fuel"] / 100)
                    + self.df.loc[k, category.name + ":doc_non_energy:hydrogen"]
                    * (self.df.loc[k, category.name + ":share:hydrogen"] / 100)
                    + self.df.loc[k, category.name + ":doc_non_energy:electric"]
                    * (self.df.loc[k, category.name + ":share:electric"] / 100)
                    + self.df.loc[k, category.name + ":doc_non_energy:hybrid_electric"]
                    * (self.df.loc[k, category.name + ":share:hybrid_electric"] / 100)
                )

    def _compute_mean_non_co2_emission_index(self):
        temp_dict = {}

        for category in self.fleet.categories.values():
            category_name = category.name
            # Initialize temporary storage for each energy type
            for energy_type in ["dropin_fuel", "hydrogen", "electric", "hybrid_electric"]:
                temp_dict[f"{category_name}:emission_index_nox:{energy_type}"] = np.zeros(
                    len(self.df)
                )
                temp_dict[f"{category_name}:emission_index_soot:{energy_type}"] = np.zeros(
                    len(self.df)
                )

            for subcategory in category.subcategories.values():
                subcategory_key = f"{category_name}:{subcategory.name}"
                for k in self.df.index:
                    dropin_fuel_share = self.df.at[k, f"{category_name}:share:dropin_fuel"]
                    hydrogen_share = self.df.at[k, f"{category_name}:share:hydrogen"]
                    electric_share = self.df.at[k, f"{category_name}:share:electric"]
                    hybrid_electric_share = self.df.at[k, f"{category_name}:share:hybrid_electric"]

                    if dropin_fuel_share != 0.0:
                        temp_dict[f"{category_name}:emission_index_nox:dropin_fuel"][
                            k - self.df.index[0]
                        ] += self.df.at[k, f"{subcategory_key}:emission_index_nox:dropin_fuel"] / (
                            dropin_fuel_share / 100
                        )
                        temp_dict[f"{category_name}:emission_index_soot:dropin_fuel"][
                            k - self.df.index[0]
                        ] += self.df.at[k, f"{subcategory_key}:emission_index_soot:dropin_fuel"] / (
                            dropin_fuel_share / 100
                        )

                    if hydrogen_share != 0.0:
                        temp_dict[f"{category_name}:emission_index_nox:hydrogen"][
                            k - self.df.index[0]
                        ] += self.df.at[k, f"{subcategory_key}:emission_index_nox:hydrogen"] / (
                            hydrogen_share / 100
                        )
                        temp_dict[f"{category_name}:emission_index_soot:hydrogen"][
                            k - self.df.index[0]
                        ] += self.df.at[k, f"{subcategory_key}:emission_index_soot:hydrogen"] / (
                            hydrogen_share / 100
                        )

                    if electric_share != 0.0:
                        temp_dict[f"{category_name}:emission_index_nox:electric"][
                            k - self.df.index[0]
                        ] += self.df.at[k, f"{subcategory_key}:emission_index_nox:electric"] / (
                            electric_share / 100
                        )
                        temp_dict[f"{category_name}:emission_index_soot:electric"][
                            k - self.df.index[0]
                        ] += self.df.at[k, f"{subcategory_key}:emission_index_soot:electric"] / (
                            electric_share / 100
                        )

                    if hybrid_electric_share != 0.0:
                        temp_dict[f"{category_name}:emission_index_nox:hybrid_electric"][
                            k - self.df.index[0]
                        ] += self.df.at[
                            k, f"{subcategory_key}:emission_index_nox:hybrid_electric"
                        ] / (hybrid_electric_share / 100)
                        temp_dict[f"{category_name}:emission_index_soot:hybrid_electric"][
                            k - self.df.index[0]
                        ] += self.df.at[
                            k, f"{subcategory_key}:emission_index_soot:hybrid_electric"
                        ] / (hybrid_electric_share / 100)

            # Calculate mean emission index
            for k in self.df.index:
                self.df.at[k, f"{category_name}:emission_index_nox"] = (
                    temp_dict[f"{category_name}:emission_index_nox:dropin_fuel"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:dropin_fuel"] / 100)
                    + temp_dict[f"{category_name}:emission_index_nox:hydrogen"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:hydrogen"] / 100)
                    + temp_dict[f"{category_name}:emission_index_nox:electric"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:electric"] / 100)
                    + temp_dict[f"{category_name}:emission_index_nox:hybrid_electric"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:hybrid_electric"] / 100)
                )
                self.df.at[k, f"{category_name}:emission_index_soot"] = (
                    temp_dict[f"{category_name}:emission_index_soot:dropin_fuel"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:dropin_fuel"] / 100)
                    + temp_dict[f"{category_name}:emission_index_soot:hydrogen"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:hydrogen"] / 100)
                    + temp_dict[f"{category_name}:emission_index_soot:electric"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:electric"] / 100)
                    + temp_dict[f"{category_name}:emission_index_soot:hybrid_electric"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:hybrid_electric"] / 100)
                )

        final_dict = {
            key: np.array(values) if isinstance(values, list) else values
            for key, values in temp_dict.items()
        }

        final_df = pd.DataFrame(final_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

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
        self.parameters.hybridization_factor = row[AIRCRAFT_COLUMNS[8]]
        self.parameters.ask_year = row[AIRCRAFT_COLUMNS[9]]
        self.parameters.rc_cost = row[AIRCRAFT_COLUMNS[10]]
        self.parameters.nrc_cost = row[AIRCRAFT_COLUMNS[11]]
        self.parameters.oew = row[AIRCRAFT_COLUMNS[12]]

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
                    5.0,
                    12000.0,
                    "DROP_IN_FUEL",
                    1.0,
                    406000000.0,
                    80000000.0,
                    10000000000.0,
                    40.0,
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
                    aircraft.parameters.hybridization_factor,
                    aircraft.parameters.ask_year,
                    aircraft.parameters.rc_cost,
                    aircraft.parameters.nrc_cost,
                    aircraft.parameters.oew,
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
    def __init__(self, add_examples_aircraft_and_subcategory=True, parameters=None):
        self._categories = {}

        self.parameters = parameters
        # Build default fleet
        self._build_default_fleet(
            add_examples_aircraft_and_subcategory=add_examples_aircraft_and_subcategory,
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

        self.all_aircraft_elements = self.get_all_aircraft_elements()

    def compute(self):
        for cat in self.categories.values():
            cat._compute()

    @property
    def categories(self):
        return self._categories

    @categories.setter
    def categories(self, value):
        self._categories = value
        self.all_aircraft_elements = self.get_all_aircraft_elements()

    def get_all_aircraft_elements(self):
        all_aircraft_elements = {}

        for category in self.categories.values():
            aircraft_per_category = []

            subcategory = category.subcategories[0]

            # Reference aircraft information
            ref_old_aircraft_name = category.name + ":" + subcategory.name + ":" + "old_reference"

            subcategory.old_reference_aircraft.full_name = ref_old_aircraft_name

            aircraft_per_category.append(subcategory.old_reference_aircraft)

            ref_recent_aircraft_name = (
                category.name + ":" + subcategory.name + ":" + "recent_reference"
            )

            subcategory.recent_reference_aircraft.full_name = ref_recent_aircraft_name

            aircraft_per_category.append(subcategory.recent_reference_aircraft)

            for i, subcategory in category.subcategories.items():
                for aircraft in subcategory.aircraft.values():
                    aircraft_name = category.name + ":" + subcategory.name + ":" + aircraft.name
                    aircraft.parameters.full_name = aircraft_name
                    aircraft_per_category.append(aircraft)

            all_aircraft_elements[category.name] = aircraft_per_category

        return all_aircraft_elements

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
            ask_year=280000000.0,
            rc_cost=80000000.0,
            nrc_cost=10000000000.0,
            oew=40.0,
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
            ask_year=280000000.0,
            rc_cost=60000000.0,
            nrc_cost=10000000000.0,
            oew=40.0,
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
            ask_year=280000000.0,
            rc_cost=60000000.0,
            nrc_cost=10000000000.0,
            oew=15.0,
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
            ask_year=280000000.0,
            rc_cost=30000000.0,
            nrc_cost=5000000000.0,
            oew=15.0,
        )

        sr_tp_aircraft_2 = Aircraft(
            "New Regional turboprop 2",
            parameters=aircraft_params,
            energy_type="DROP_IN_FUEL",
        )

        # Short range regional turbofan
        # aircraft_params = AircraftParameters(
        #     entry_into_service_year=2035,
        #     consumption_evolution=-15.0,
        #     nox_evolution=0.0,
        #     soot_evolution=0.0,
        #     doc_non_energy_evolution=0.0,
        #     cruise_altitude=12000.0,
        #     ask_year=280000000.0,
        #     rc_cost=30000000.0,
        #     nrc_cost=5000000000.0,
        #     oew=15.0,
        # )

        # sr_tf_aircraft_1 = Aircraft(
        #     "New Regional turbofan 1",
        #     parameters=aircraft_params,
        #     energy_type="DROP_IN_FUEL",
        # )

        # aircraft_params = AircraftParameters(
        #     entry_into_service_year=2045,
        #     consumption_evolution=-30.0,
        #     nox_evolution=0.0,
        #     soot_evolution=0.0,
        #     doc_non_energy_evolution=0.0,
        #     cruise_altitude=12000.0,
        #     ask_year=280000000.0,
        #     rc_cost=40000000.0,
        #     nrc_cost=5000000000.0,
        #     oew=15.0,
        # )

        # sr_tf_aircraft_2 = Aircraft(
        #     "New Regional turbofan 2",
        #     parameters=aircraft_params,
        #     energy_type="DROP_IN_FUEL",
        # )

        # Short range hydrogen aircraft

        aircraft_params = AircraftParameters(
            entry_into_service_year=2035,
            consumption_evolution=10.0,
            nox_evolution=0.0,
            soot_evolution=-100.0,
            doc_non_energy_evolution=10.0,
            cruise_altitude=12000.0,
            ask_year=280000000.0,
            rc_cost=40000000.0,
            nrc_cost=5000000000.0,
            oew=40.0,
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
            ask_year=352000000.0,
            rc_cost=50000000.0,
            nrc_cost=10000000000.0,
            oew=40.0,
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
            ask_year=352000000.0,
            rc_cost=60000000.0,
            nrc_cost=10000000000.0,
            oew=40.0,
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
            ask_year=912000000.0,
            rc_cost=60000000.0,
            nrc_cost=10000000000.0,
            oew=130.0,
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
            ask_year=912000000.0,
            rc_cost=150000000.0,
            nrc_cost=25000000000.0,
            oew=130.0,
        )

        lr_aircraft_2 = Aircraft(
            "New Long-range wide-body 2", parameters=aircraft_params, energy_type="DROP_IN_FUEL"
        )

        # Short range
        cat_params = CategoryParameters(life=25)
        sr_cat = Category("Short Range", parameters=cat_params)

        # Short range narrow-body
        if add_examples_aircraft_and_subcategory:
            subcat_params = SubcategoryParameters(share=20.0)
        else:
            subcat_params = SubcategoryParameters(share=100.0)
        sr_nb_cat = SubCategory("SR conventional narrow-body", parameters=subcat_params)
        # Reference aircraft
        # Old
        sr_nb_cat.old_reference_aircraft.entry_into_service_year = (
            1970  # Not used: old iarcraft starts at 100
        )
        sr_nb_cat.old_reference_aircraft.energy_per_ask = 110.8 / 73.2 * 0.824  # [MJ/ASK]
        sr_nb_cat.old_reference_aircraft.emission_index_nox = 0.01514
        sr_nb_cat.old_reference_aircraft.emission_index_soot = 3e-5
        sr_nb_cat.old_reference_aircraft.doc_non_energy_base = 0.048375  # conversion of capital to 0.07 annuity factor (US based airlines very low) => factor of 1.075 (0.9+10% capital * 0.07/0.04)
        sr_nb_cat.old_reference_aircraft.cruise_altitude = 12000.0
        sr_nb_cat.old_reference_aircraft.ask_year = 280000000.0
        sr_nb_cat.old_reference_aircraft.rc_cost = 40000000.0
        sr_nb_cat.old_reference_aircraft.nrc_cost = 10000000000.0
        sr_nb_cat.old_reference_aircraft.oew = 37.0

        # Recent
        sr_nb_cat.recent_reference_aircraft.entry_into_service_year = 2007.13
        sr_nb_cat.recent_reference_aircraft.energy_per_ask = 84.2 / 73.2 * 0.824  # [MJ/ASK]
        sr_nb_cat.recent_reference_aircraft.emission_index_nox = 0.01514
        sr_nb_cat.recent_reference_aircraft.emission_index_soot = 3e-5
        sr_nb_cat.recent_reference_aircraft.doc_non_energy_base = 0.048375  # conversion of capital to 0.07 annuity factor (US based airlines very low) => factor of 1.075 (0.9+10% capital * 0.07/0.04)
        sr_nb_cat.recent_reference_aircraft.cruise_altitude = 12000.0
        sr_nb_cat.recent_reference_aircraft.ask_year = 280000000
        sr_nb_cat.recent_reference_aircraft.rc_cost = 40000000.0
        sr_nb_cat.recent_reference_aircraft.nrc_cost = 10000000000.0
        sr_nb_cat.recent_reference_aircraft.oew = 43.0

        mean_energy_init_ask_short_range = (
            self.parameters.energy_consumption_init[2019]
            * self.parameters.short_range_energy_share_2019
        ) / (self.parameters.ask_init[2019] * self.parameters.short_range_rpk_share_2019)

        share_recent_short_range = (
            mean_energy_init_ask_short_range - sr_nb_cat.old_reference_aircraft.energy_per_ask
        ) / (
            sr_nb_cat.recent_reference_aircraft.energy_per_ask
            - sr_nb_cat.old_reference_aircraft.energy_per_ask
        )

        lambda_short_range = np.log(100 / 2 - 1) / (sr_cat.parameters.life / 2)

        # nominal case where mean fleet energy is between old and recent aircraft performances
        if 1 > share_recent_short_range > 0:
            t0_mr = np.log(
                (1 - share_recent_short_range) / share_recent_short_range
            ) / lambda_short_range + (self.parameters.prospection_start_year - 1)

            t_eis_short_range = t0_mr - sr_cat.parameters.life / 2

        # case where mean fleet energy is lower than best aircraft => consider that all the fleet is composed of aircraft with mean fleet energy
        elif share_recent_short_range > 1:
            warnings.warn(
                "Warning Message - "
                + "Fleet Model: Short Range Aircraft: "
                + "Average initial short-range fleet energy per ASK is lower than default energy per ASK for the recent reference aircraft - "
                + "AeroMAPS is using initial short-range fleet energy per ASK as old and recent reference aircraft energy performances!"
            )

            t_eis_short_range = self.parameters.prospection_start_year - 1 - sr_cat.parameters.life
            sr_nb_cat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask_short_range
            sr_nb_cat.recent_reference_aircraft.energy_per_ask = mean_energy_init_ask_short_range

        # case where mean fleet energy is higher than worse aircraft => consider that old aircraft used mean energy and that the new aircraft is introduced at the beginning of the scenario
        else:
            t_eis_short_range = self.parameters.prospection_start_year
            sr_nb_cat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask_short_range

            warnings.warn(
                "Warning Message - "
                + "Fleet Model: Short Range Aircraft: "
                + "Average initial short-range fleet energy per ASK is higher than default energy per ASK for the old reference aircraft - "
                + "AeroMAPS is using initial short-range fleet energy per ASK as old aircraft energy performances. Recent reference aircraft is introduced on first prospective year"
            )

        sr_nb_cat.recent_reference_aircraft.entry_into_service_year = t_eis_short_range

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
        # subcat_params = SubcategoryParameters(share=0.0)
        # sr_tf_cat = SubCategory("SR regional turbofan", parameters=subcat_params)
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

        sr_cat.add_subcategory(subcategory=sr_nb_cat)
        if add_examples_aircraft_and_subcategory:
            sr_cat.add_subcategory(subcategory=sr_rp_cat)
            sr_cat.add_subcategory(subcategory=sr_subcat_hydrogen)
        # sr_cat.add_subcategory(subcategory=sr_tf_cat)

        # Medium range

        cat_params = CategoryParameters(life=25)
        mr_cat = Category(name="Medium Range", parameters=cat_params)

        subcat_params = SubcategoryParameters(share=100.0)
        mr_subcat = SubCategory("MR conventional narrow-body", parameters=subcat_params)
        # Reference aircraft
        # Old
        mr_subcat.old_reference_aircraft.entry_into_service_year = 1970
        mr_subcat.old_reference_aircraft.energy_per_ask = 81.4 / 73.2 * 0.824  # [MJ/ASK]
        mr_subcat.old_reference_aircraft.emission_index_nox = 0.01514
        mr_subcat.old_reference_aircraft.emission_index_soot = 3e-5
        mr_subcat.old_reference_aircraft.doc_non_energy_base = 0.0301  # conversion of capital to 0.07 annuity factor (US based airlines very low) => factor of 1.075 (0.9+10% capital * 0.07/0.04)
        mr_subcat.old_reference_aircraft.cruise_altitude = 12000.0
        mr_subcat.old_reference_aircraft.ask_year = 352000000.0
        mr_subcat.old_reference_aircraft.rc_cost = 60000000.0
        mr_subcat.old_reference_aircraft.nrc_cost = 10000000000.0
        mr_subcat.old_reference_aircraft.oew = 37.0

        # Recent
        mr_subcat.recent_reference_aircraft.entry_into_service_year = 2010.35
        mr_subcat.recent_reference_aircraft.energy_per_ask = 62.0 / 73.2 * 0.824  # [MJ/ASK]
        mr_subcat.recent_reference_aircraft.emission_index_nox = 0.01514
        mr_subcat.recent_reference_aircraft.emission_index_soot = 3e-5
        mr_subcat.recent_reference_aircraft.doc_non_energy_base = 0.0301  # conversion of capital to 0.07 annuity factor (US based airlines very low) => factor of 1.075 (0.9+10% capital * 0.07/0.04)
        mr_subcat.recent_reference_aircraft.cruise_altitude = 12000.0
        mr_subcat.recent_reference_aircraft.ask_year = 352000000.0
        mr_subcat.recent_reference_aircraft.rc_cost = 60000000.0
        mr_subcat.recent_reference_aircraft.nrc_cost = 10000000000.0
        mr_subcat.recent_reference_aircraft.oew = 43.0

        mean_energy_init_ask_medium_range = (
            self.parameters.energy_consumption_init[2019]
            * self.parameters.medium_range_energy_share_2019
        ) / (self.parameters.ask_init[2019] * self.parameters.medium_range_rpk_share_2019)

        share_recent_medium_range = (
            mean_energy_init_ask_medium_range - mr_subcat.old_reference_aircraft.energy_per_ask
        ) / (
            mr_subcat.recent_reference_aircraft.energy_per_ask
            - mr_subcat.old_reference_aircraft.energy_per_ask
        )

        lambda_medium_range = np.log(100 / 2 - 1) / (mr_cat.parameters.life / 2)

        if 1 > share_recent_medium_range > 0:
            t0_mr = np.log(
                (1 - share_recent_medium_range) / share_recent_medium_range
            ) / lambda_medium_range + (self.parameters.prospection_start_year - 1)

            t_eis_medium_range = t0_mr - mr_cat.parameters.life / 2

        # case where mean fleet energy is lower than best aircraft => consider that all the fleet is composed of aircraft with mean fleet energy
        elif share_recent_medium_range > 1:
            warnings.warn(
                "Warning Message - "
                + "Fleet Model: medium Range Aircraft: "
                + "Average initial medium-range fleet energy per ASK is lower than default energy per ASK for the recent reference aircraft - "
                + "AeroMAPS is using initial medium-range fleet energy per ASK as old and recent reference aircraft energy performances!"
            )

            t_eis_medium_range = self.parameters.prospection_start_year - 1 - sr_cat.parameters.life
            mr_subcat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask_medium_range
            mr_subcat.recent_reference_aircraft.energy_per_ask = mean_energy_init_ask_medium_range

        # case where mean fleet energy is higher than worse aircraft => consider that old aircraft used mean energy and that the new aircraft is introduced at the beginning of the scenario
        else:
            t_eis_medium_range = self.parameters.prospection_start_year
            mr_subcat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask_medium_range

            warnings.warn(
                "Warning Message - "
                + "Fleet Model: medium Range Aircraft: "
                + "Average initial medium-range fleet energy per ASK is higher than default energy per ASK for the old reference aircraft - "
                + "AeroMAPS is using initial medium-range fleet energy per ASK as old aircraft energy performances. Recent reference aircraft is introduced on first prospective year"
            )

        mr_subcat.recent_reference_aircraft.entry_into_service_year = t_eis_medium_range

        if add_examples_aircraft_and_subcategory:
            mr_subcat.add_aircraft(aircraft=mr_aircraft_1)
            mr_subcat.add_aircraft(aircraft=mr_aircraft_2)

        mr_cat.add_subcategory(subcategory=mr_subcat)

        # Long range
        cat_params = CategoryParameters(life=25)
        lr_cat = Category("Long Range", parameters=cat_params)

        subcat_params = SubcategoryParameters(share=100.0)
        lr_subcat = SubCategory("LR conventional wide-body", parameters=subcat_params)
        # Reference aircraft
        # Old
        lr_subcat.old_reference_aircraft.entry_into_service_year = 1970
        lr_subcat.old_reference_aircraft.energy_per_ask = 96.65 / 73.2 * 0.824  # [MJ/ASK]
        lr_subcat.old_reference_aircraft.emission_index_nox = 0.01514
        lr_subcat.old_reference_aircraft.emission_index_soot = 3e-5
        lr_subcat.old_reference_aircraft.doc_non_energy_base = 0.024725  # conversion of capital to 0.07 annuity factor (US based airlines very low) => factor of 1.075 (0.9+10% capital * 0.07/0.04)
        lr_subcat.old_reference_aircraft.cruise_altitude = 12000.0
        lr_subcat.old_reference_aircraft.ask_year = 912000000.0
        lr_subcat.old_reference_aircraft.rc_cost = 150000000.0
        lr_subcat.old_reference_aircraft.nrc_cost = 25000000000.0
        lr_subcat.old_reference_aircraft.oew = 135.0

        # Recent
        lr_subcat.recent_reference_aircraft.entry_into_service_year = 2009.36
        lr_subcat.recent_reference_aircraft.energy_per_ask = 73.45 / 73.2 * 0.824  # [MJ/ASK]
        lr_subcat.recent_reference_aircraft.emission_index_nox = 0.01514
        lr_subcat.recent_reference_aircraft.emission_index_soot = 3e-5
        lr_subcat.recent_reference_aircraft.doc_non_energy_base = 0.024725  # conversion of capital to 0.07 annuity factor (US based airlines very low) => factor of 1.075 (0.9+10% capital * 0.07/0.04)
        lr_subcat.recent_reference_aircraft.cruise_altitude = 12000.0
        lr_subcat.recent_reference_aircraft.ask_year = 912000000.0
        lr_subcat.recent_reference_aircraft.rc_cost = 150000000.0
        lr_subcat.recent_reference_aircraft.nrc_cost = 25000000000.0
        lr_subcat.recent_reference_aircraft.oew = 129.0

        mean_energy_init_ask_long_range = (
            self.parameters.energy_consumption_init[2019]
            * self.parameters.long_range_energy_share_2019
        ) / (self.parameters.ask_init[2019] * self.parameters.long_range_rpk_share_2019)

        share_recent_long_range = (
            mean_energy_init_ask_long_range - lr_subcat.old_reference_aircraft.energy_per_ask
        ) / (
            lr_subcat.recent_reference_aircraft.energy_per_ask
            - lr_subcat.old_reference_aircraft.energy_per_ask
        )

        lambda_long_range = np.log(100 / 2 - 1) / (lr_cat.parameters.life / 2)

        if 1 > share_recent_long_range > 0:
            t0_lr = np.log(
                (1 - share_recent_long_range) / share_recent_long_range
            ) / lambda_long_range + (self.parameters.prospection_start_year - 1)

            t_eis_long_range = t0_lr - lr_cat.parameters.life / 2

        # case where mean fleet energy is lower than best aircraft => consider that all the fleet is composed of aircraft with mean fleet energy
        elif share_recent_long_range > 1:
            warnings.warn(
                "Warning Message - "
                + "Fleet Model: long Range Aircraft: "
                + "Average initial long-range fleet energy per ASK is lower than default energy per ASK for the recent reference aircraft - "
                + "AeroMAPS is using initial long-range fleet energy per ASK as old and recent reference aircraft energy performances!"
            )

            t_eis_long_range = self.parameters.prospection_start_year - 1 - sr_cat.parameters.life
            lr_subcat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask_long_range
            lr_subcat.recent_reference_aircraft.energy_per_ask = mean_energy_init_ask_long_range

        # case where mean fleet energy is higher than worse aircraft => consider that old aircraft used mean energy and that the new aircraft is introduced at the beginning of the scenario
        else:
            t_eis_long_range = self.parameters.prospection_start_year
            lr_subcat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask_long_range

            warnings.warn(
                "Warning Message - "
                + "Fleet Model: long Range Aircraft: "
                + "Average initial long-range fleet energy per ASK is higher than default energy per ASK for the old reference aircraft - "
                + "AeroMAPS is using initial long-range fleet energy per ASK as old aircraft energy performances. Recent reference aircraft is introduced on first prospective year"
            )

        lr_subcat.recent_reference_aircraft.entry_into_service_year = t_eis_long_range

        if add_examples_aircraft_and_subcategory:
            lr_subcat.add_aircraft(aircraft=lr_aircraft_1)
            lr_subcat.add_aircraft(aircraft=lr_aircraft_2)

        lr_cat.add_subcategory(subcategory=lr_subcat)

        self.categories[sr_cat.name] = sr_cat
        self.categories[mr_cat.name] = mr_cat
        self.categories[lr_cat.name] = lr_cat

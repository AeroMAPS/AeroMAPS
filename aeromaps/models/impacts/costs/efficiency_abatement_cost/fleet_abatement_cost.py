# @Time : 05/02/2024 16:23
# @Author : a.salgas
# @File : fleet_abatement_cost.py
# @Software: PyCharm
import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel
from typing import Tuple


class FleetCarbonAbatementCosts(AeromapsModel):
    def __init__(self, name="fleet_abatement_cost", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = fleet_model

    def compute(
        self,
        ask_aircraft_value_dict: dict,
        rpk_aircraft_value_dict: dict,
        load_factor: pd.Series = pd.Series(dtype="float64"),
        doc_non_energy_per_ask_short_range_dropin_fuel_init: float = 0.0,
        doc_non_energy_per_ask_medium_range_dropin_fuel_init: float = 0.0,
        doc_non_energy_per_ask_long_range_dropin_fuel_init: float = 0.0,
        energy_per_ask_without_operations_short_range_dropin_fuel: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_ask_without_operations_medium_range_dropin_fuel: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_ask_without_operations_long_range_dropin_fuel: pd.Series = pd.Series(
            dtype="float64"
        ),
        kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
        kerosene_emission_factor: pd.Series = pd.Series(dtype="float64"),
        covid_energy_intensity_per_ask_increase_2020: float = 0.0,
            lhv_kerosene: float = 0.0,
            density_kerosene: float = 0.0,
    ) -> Tuple[dict, dict]:
        dummy_carbon_abatement_cost_aircraft_value_dict = {}
        dummy_carbon_abatement_volume_aircraft_value_dict = {}
        for category, sets in self.fleet_model.all_aircraft_elements.items():

            category_recent_reference = self.fleet_model.all_aircraft_elements[category][1]

            if category == "Short Range":
                category_reference_doc_ne = doc_non_energy_per_ask_short_range_dropin_fuel_init
                # Assumes 100% drop in at reference year. Sum with non drop in necessary otherwise.
                category_reference_energy = (
                    energy_per_ask_without_operations_short_range_dropin_fuel[
                        self.prospection_start_year - 1
                    ]
                )
            elif category == "Medium Range":
                category_reference_doc_ne = doc_non_energy_per_ask_medium_range_dropin_fuel_init
                category_reference_energy = (
                    energy_per_ask_without_operations_medium_range_dropin_fuel[
                        self.prospection_start_year - 1
                    ]
                )
            else:
                category_reference_doc_ne = doc_non_energy_per_ask_long_range_dropin_fuel_init
                category_reference_energy = (
                    energy_per_ask_without_operations_long_range_dropin_fuel[
                        self.prospection_start_year - 1
                    ]
                )

            # Calculating values of interest for each aircraft
            for aircraft_var in sets:
                # Check if it's a reference aircraft or a normal aircraft...
                if hasattr(aircraft_var, "parameters"):
                    aircraft_var_name = aircraft_var.parameters.full_name
                    aircraft_energy_delta_val = (
                        1 + float(aircraft_var.parameters.consumption_evolution) / 100
                    ) * category_recent_reference.energy_per_ask - category_reference_energy

                    aircraft_doc_ne_delta = (
                        (1 + float(aircraft_var.parameters.doc_non_energy_evolution) / 100)
                        * category_recent_reference.doc_non_energy_base
                        - category_reference_doc_ne
                    )

                else:
                    aircraft_var_name = aircraft_var.full_name
                    aircraft_energy_delta_val = (
                        aircraft_var.energy_per_ask - category_reference_energy
                    )
                    aircraft_doc_ne_delta = (
                        aircraft_var.doc_non_energy_base - category_reference_doc_ne
                    )

                # include covid energy per ask increase, applied indifferently to the whole fleet.
                # Initialisation of a uniform pd.series and modification of 2020 value.
                aircraft_energy_delta = pd.Series(
                    aircraft_energy_delta_val, index=self.fleet_model.df.index
                )

                # initialisation based on the same model transition than aircraft efficiency model, transitioning

                aircraft_energy_delta[2019] = 0  # start from reference

                aircraft_energy_delta[2020] = (
                    aircraft_energy_delta[2019]
                    * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)
                    + category_reference_energy * covid_energy_intensity_per_ask_increase_2020 / 100
                )

                # Assumption: 100% kerosene for cost calculation. Effect of SAFs/Hydrogen is accounted for downwards in
                # the calculation process. For instance a Hydrogen aircraft, that would consume more energy in this step
                # would result in negative abatement; even though the total lifecycle could actually reduce emissions.

                aircraft_carbon_abatement_cost = (
                    (
                        aircraft_energy_delta * kerosene_market_price / (lhv_kerosene * density_kerosene)
                        + aircraft_doc_ne_delta
                    )
                    / (-aircraft_energy_delta * kerosene_emission_factor)
                    * 1000000
                )  # €/ton

                # TODO use input dictionary if possible once implemented instead of looking in fleet model df + dummy output
                aircraft_pseudo_ask = (
                    self.fleet_model.df.loc[:, (aircraft_var_name + ":aircraft_rpk")]
                    / load_factor[self.prospection_start_year - 1]
                    * 100
                )

                aircraft_carbon_abatement_volume = -(
                    aircraft_pseudo_ask * aircraft_energy_delta * kerosene_emission_factor / 1000000
                )  # in tons

                cac_aircraft_var_name = aircraft_var_name + ":aircraft_carbon_abatement_cost"

                abatement_volume_aircraft_var_name = (
                    aircraft_var_name + ":aircraft_carbon_abatement_volume"
                )

                self.fleet_model.df = pd.concat(
                    [
                        self.fleet_model.df,
                        aircraft_carbon_abatement_cost.rename(cac_aircraft_var_name),
                    ],
                    axis=1,
                )

                self.fleet_model.df = pd.concat(
                    [
                        self.fleet_model.df,
                        aircraft_carbon_abatement_volume.rename(abatement_volume_aircraft_var_name),
                    ],
                    axis=1,
                )

                dummy_carbon_abatement_cost_aircraft_value_dict[aircraft_var_name] = aircraft_carbon_abatement_cost
                dummy_carbon_abatement_volume_aircraft_value_dict[aircraft_var_name] = aircraft_carbon_abatement_volume

        return (
            dummy_carbon_abatement_cost_aircraft_value_dict,
            dummy_carbon_abatement_volume_aircraft_value_dict,
        )

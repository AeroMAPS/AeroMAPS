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
        exogenous_carbon_price_trajectory: pd.Series = pd.Series(dtype="float64"),
        covid_energy_intensity_per_ask_increase_2020: float = 0.0,
        lhv_kerosene: float = 0.0,
        density_kerosene: float = 0.0,
        social_discount_rate: float = 0.0,
    ) -> Tuple[
        dict,
        dict,
        dict,
        dict
    ]:
        dummy_carbon_abatement_cost_aircraft_value_dict = {}
        dummy_specific_carbon_abatement_cost_aircraft_value_dict = {}
        dummy_generic_specific_carbon_abatement_cost_aircraft_value_dict = {}
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

                extra_cost_fuel = (
                    aircraft_energy_delta
                    * kerosene_market_price
                    / (lhv_kerosene * density_kerosene)
                )

                extra_emissions = (-aircraft_energy_delta * kerosene_emission_factor) / 1000000

                aircraft_carbon_abatement_cost = (
                    extra_cost_fuel + aircraft_doc_ne_delta
                ) / extra_emissions  # €/ton

                specific_cac_aircraft_var_name = (
                    aircraft_var_name + ":aircraft_specific_carbon_abatement_cost"
                )

                specific_cac_prime_aircraft_var_name = (
                    aircraft_var_name + ":aircraft_generic_specific_carbon_abatement_cost"
                )

                scac_vals = []
                scac_vals_prime = []
                for k in range(self.prospection_start_year, self.end_year + 1):

                    scac,scac_prime=    self._get_discounted_vals(
                            k,
                            social_discount_rate,
                            self.fleet_model.fleet.categories[category].parameters.life,
                            aircraft_doc_ne_delta,
                            extra_cost_fuel,
                            kerosene_market_price,
                            kerosene_emission_factor,
                            extra_emissions,
                            exogenous_carbon_price_trajectory
                        )
                    scac_vals.append(scac)
                    scac_vals_prime.append(scac_prime)


                scac_column = pd.DataFrame(
                    {specific_cac_aircraft_var_name: scac_vals},
                    index=range(self.prospection_start_year, self.end_year + 1),
                )

                scac_prime_column = pd.DataFrame(
                    {specific_cac_prime_aircraft_var_name: scac_vals_prime},
                    index=range(self.prospection_start_year, self.end_year + 1),
                )

                self.fleet_model.df = pd.concat([self.fleet_model.df, scac_column], axis=1)
                self.fleet_model.df = pd.concat([self.fleet_model.df, scac_prime_column], axis=1)

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

                dummy_carbon_abatement_cost_aircraft_value_dict[
                    aircraft_var_name
                ] = aircraft_carbon_abatement_cost
                dummy_carbon_abatement_volume_aircraft_value_dict[
                    aircraft_var_name
                ] = aircraft_carbon_abatement_volume

                dummy_specific_carbon_abatement_cost_aircraft_value_dict[
                    aircraft_var_name
                ] = scac_column

                dummy_generic_specific_carbon_abatement_cost_aircraft_value_dict[
                    aircraft_var_name
                ] = scac_prime_column

        return (
            dummy_carbon_abatement_cost_aircraft_value_dict,
            dummy_carbon_abatement_volume_aircraft_value_dict,
            dummy_specific_carbon_abatement_cost_aircraft_value_dict,
            dummy_generic_specific_carbon_abatement_cost_aircraft_value_dict,
        )

    def _get_discounted_vals(
        self,
        year,
        discount_rate,
        aircraft_life,
        extra_cost_non_fuel,
        extra_cost_fuel,
        kerosene_market_price,
        kerosene_emission_factor,
        emissions_reduction,
        exogenous_carbon_price_trajectory,
    ):

        discounted_cumul_cost = 0
        cumul_em = 0
        generic_discounted_cumul_em = 0
        for i in range(year, year + int(aircraft_life)):
            if i < (self.end_year + 1):
                discounted_cumul_cost += (
                    extra_cost_non_fuel
                    + extra_cost_fuel[year] * kerosene_market_price[i] / kerosene_market_price[year]
                ) / (1 + discount_rate) ** (i - year)
                cumul_em += (
                    emissions_reduction[year]
                    * kerosene_emission_factor[i]
                    / kerosene_emission_factor[year]
                )

                # discounting emissions for non-hotelling scc
                generic_discounted_cumul_em += (
                    emissions_reduction[year]
                    * kerosene_emission_factor[i]
                    / kerosene_emission_factor[year]
                    * exogenous_carbon_price_trajectory[i]
                    / exogenous_carbon_price_trajectory[year]
                    / (1 + discount_rate) ** (i - year)
                )
            else:
                discounted_cumul_cost += (
                    extra_cost_non_fuel
                    + extra_cost_fuel[year]
                    * kerosene_market_price[self.end_year]
                    / kerosene_market_price[year]
                ) / (1 + discount_rate) ** (i - year)
                cumul_em += (
                    emissions_reduction[year]
                    * kerosene_emission_factor[self.end_year]
                    / kerosene_emission_factor[year]
                )

                # discounting emissions for non-hotelling scc, keep last year scc growth rate as future scc growth rate
                future_scc_growth = (
                    exogenous_carbon_price_trajectory[self.end_year]
                    / exogenous_carbon_price_trajectory[self.end_year - 1]
                )

                generic_discounted_cumul_em += (
                    emissions_reduction[year]
                    * (kerosene_emission_factor[self.end_year]
                    / kerosene_emission_factor[year])
                    * (exogenous_carbon_price_trajectory[self.end_year]
                    / exogenous_carbon_price_trajectory[year]
                    * (future_scc_growth) ** (i - self.end_year))
                    / (1 + discount_rate) ** (i - year)
                )

        return (discounted_cumul_cost / cumul_em,
                discounted_cumul_cost / generic_discounted_cumul_em)

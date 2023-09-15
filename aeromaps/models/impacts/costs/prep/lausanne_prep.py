# @Time : 14/06/2023 09:20
# @Author : a.salgas
# @File : lausanne_prep.py
# @Software: PyCharm
from typing import Tuple

import numpy as np
import pandas as pd
from aeromaps.models.base import AeromapsModel


class AircraftASK(AeromapsModel):
    def __init__(self, name="aircraft_ask", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        ask_category: pd.Series = pd.Series(dtype="float64"),
        share_aircraft_type_in_category: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series]:
        return ask_category * share_aircraft_type_in_category


class ExistingAircraftAvailability(AeromapsModel):
    def __init__(self, name="existing_aircraft_availability", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        ask_aircraft_type: pd.Series = pd.Series(dtype="float64"),
        ask_per_aircraft_aircraft_type: float = 1.0,
        n_years_prod: float = 0.0,
        life_aircraft_type: float = 0.0,
        prod_cagr: float = 0.0,
    ) -> Tuple[pd.Series,]:

        n_aircraft_t0 = ask_aircraft_type[0] / ask_per_aircraft_aircraft_type

        indexes = ask_aircraft_type.index

        # Additional aircraft to be built per year
        aircraft_available_scenario = pd.Series(np.zeros(len(indexes)), indexes)

        x_0 = n_aircraft_t0 / ((1 - (1 + prod_cagr) ** n_years_prod) / (-prod_cagr))

        for i in range(0, n_years_prod):
            for j in range(0, life_aircraft_type - i):
                aircraft_available_scenario[j] += x_0 * (1 + prod_cagr) ** i
        return aircraft_available_scenario


class AircraftFactory(AeromapsModel):
    def __init__(self, name="aircraft_factory", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        aircraft_available_scenario: pd.Series = pd.Series(dtype="float64"),
        ask_aircraft_type: pd.Series = pd.Series(dtype="float64"),
        ask_per_aircraft_aircraft_type: float = 1.0,
        life_aircraft_type: float = 0.0,
    ) -> Tuple[pd.Series, pd.Series]:

        # define the aircraft demand scenario:
        # compute the number of aircraft to match the ask of the aircraft type, round to sup
        demand_scenario = np.ceil(ask_aircraft_type / ask_per_aircraft_aircraft_type)

        indexes = demand_scenario.index

        # Additional aircraft to be built per year
        aircraft_building_scenario = pd.Series(np.zeros(len(indexes)), indexes)

        # For each year of the demand scenario the demand is matched by the production
        for year in list(demand_scenario.index)[:-1]:
            # Aircraft missing in year n+1 must be supplied by aircraft built in year n
            if aircraft_available_scenario[year + 1] < demand_scenario[year + 1]:
                # Getting the necessary production
                missing_production = (
                    demand_scenario[year + 1] - aircraft_available_scenario[year + 1]
                )

                aircraft_building_scenario[year] = missing_production

                # When new aircraft availability ends: either at the end of plant life or the end of the scenario;
                end_bound = min(list(demand_scenario.index)[-1], year + life_aircraft_type)
                # Adding new plant production to future years and computing total cost associated
                for i in range(year + 1, end_bound + 1):
                    aircraft_available_scenario[i] = (
                        aircraft_available_scenario[i] + missing_production
                    )

        return (aircraft_building_scenario, aircraft_available_scenario)


class AircraftNRC(AeromapsModel):
    def __init__(self, name="aircraft_nrc", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        nrc_tot_aircraft_type: float = 0.0,
        development_time_aircraft_type: float = 0.0,
        entry_into_service_year: int = 0.0,
    ) -> Tuple[pd.Series(dtype="float64")]:
        costs = []
        years = []
        sigma = development_time_aircraft_type / 6.0  # Controls the spread of the distribution

        for i in range(1, development_time_aircraft_type + 1):
            year = entry_into_service_year - development_time_aircraft_type + i
            weight = np.exp(-0.5 * ((i - development_time_aircraft_type / 2) / sigma) ** 2)
            cost = round(nrc_tot_aircraft_type * weight)
            costs.append(cost)
            years.append(year)

        # Adjust the distributed costs to ensure their sum matches the total cost
        total_distributed_cost = sum(costs)
        scaling_factor = nrc_tot_aircraft_type / total_distributed_cost
        costs = [round(cost * scaling_factor) for cost in costs]
        nrc_distributed = pd.Series(costs, index=years)

        return nrc_distributed


class AircraftRC(AeromapsModel):
    def __init__(self, name="aircraft_nrc", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        aircraft_building_sceanrio: pd.Series = pd.Series(dtype="float64"),
        rc_cost_aircraft_type: float = 0.0,
    ) -> Tuple[pd.Series]:
        return aircraft_building_sceanrio * rc_cost_aircraft_type


class AircraftDropInDOC(AeromapsModel):
    def __init__(self, name="aircraft_dropin_doc", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_ask_aircraft_type: float = 0.0,
        doc_non_fuel_aircraft_type_ask: float = 0.0,
        ask_aircraft_type: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fog_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_mfsp: pd.Series = pd.Series(dtype="float64"),
        kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fog_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_share: pd.Series = pd.Series(dtype="float64"),
        electrofuel_avg_cost_per_l: pd.Series = pd.Series(dtype="float64"),
        biofuel_share: pd.Series = pd.Series(dtype="float64"),
        electrofuel_share: pd.Series = pd.Series(dtype="float64"),
        kerosene_share: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series(dtype="float64"), pd.Series(dtype="float64"), pd.Series(dtype="float64")]:
        fuel_lhv = 35.3
        doc_bio = (
            energy_ask_aircraft_type
            * (
                biofuel_hefa_fog_mfsp * biofuel_hefa_fog_share
                + biofuel_hefa_others_mfsp * biofuel_hefa_others_share
                + biofuel_atj_mfsp * biofuel_atj_share
                + biofuel_ft_msw_mfsp * biofuel_ft_msw_share
                + biofuel_ft_others_share * biofuel_ft_others_mfsp
            )
            * biofuel_share
            / fuel_lhv
        )
        doc_efuel = (
            energy_ask_aircraft_type * electrofuel_avg_cost_per_l * electrofuel_share / fuel_lhv
        )
        doc_kerosene = energy_ask_aircraft_type * kerosene_market_price * kerosene_share / fuel_lhv

        doc_energy_aircraft_type_ask = doc_kerosene + doc_efuel + doc_bio

        doc_energy_aircraft_type = doc_energy_aircraft_type_ask * ask_aircraft_type

        doc_non_fuel_ask_aircraft_type = doc_non_fuel_aircraft_type_ask * ask_aircraft_type

        return (
            doc_energy_aircraft_type,
            doc_non_fuel_ask_aircraft_type,
            doc_energy_aircraft_type_ask,
        )


class AircraftLh2DOC(AeromapsModel):
    def __init__(self, name="aircraft_lh2_doc", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_ask_aircraft_type: float = 0.0,
        doc_non_fuel_aircraft_type_ask: float = 0.0,
        ask_aircraft_type: pd.Series = pd.Series(dtype="float64"),
        h2_avg_cost_per_kg_electrolysis: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series(dtype="float64"), pd.Series(dtype="float64"), pd.Series(dtype="float64")]:
        hydrogen_specific_energy = 119.93  # MJ/kg

        doc_energy_aircraft_type_ask = (
            energy_ask_aircraft_type * h2_avg_cost_per_kg_electrolysis / hydrogen_specific_energy
        )

        doc_energy_aircraft_type = doc_energy_aircraft_type_ask * ask_aircraft_type

        doc_non_fuel_ask_aircraft_type = doc_non_fuel_aircraft_type_ask * ask_aircraft_type

        return (
            doc_energy_aircraft_type,
            doc_non_fuel_ask_aircraft_type,
            doc_energy_aircraft_type_ask,
        )

# @Time : 13/03/2023 10:46
# @Author : a.salgas
# @File : scenario_cost.py
# @Software: PyCharm

from typing import Tuple

import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class NonDiscountedScenarioCost(AeroMAPSModel):
    def __init__(self, name="non_discounted_scenario_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        kerosene_cost: pd.Series,
        biofuel_cost_hefa_fog: pd.Series,
        biofuel_cost_hefa_others: pd.Series,
        biofuel_cost_ft_others: pd.Series,
        biofuel_cost_ft_msw: pd.Series,
        biofuel_cost_atj: pd.Series,
        electrofuel_total_cost: pd.Series,
        total_hydrogen_supply_cost: pd.Series,
        electricity_direct_use_total_cost: pd.Series,
        co2_emissions_2019technology: pd.Series,
        co2_emissions_including_load_factor: pd.Series,
        kerosene_emission_factor: pd.Series,
        kerosene_market_price: pd.Series,
        density_kerosene: float,
        lhv_kerosene: float,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        # Compute the total energy expenses of the scenario
        non_discounted_energy_expenses = (
            kerosene_cost.fillna(0)
            + biofuel_cost_hefa_fog.fillna(0)
            + biofuel_cost_hefa_others.fillna(0)
            + biofuel_cost_ft_others.fillna(0)
            + biofuel_cost_ft_msw.fillna(0)
            + biofuel_cost_atj.fillna(0)
            + electrofuel_total_cost.fillna(0)
            + total_hydrogen_supply_cost.fillna(0)
            + electricity_direct_use_total_cost.fillna(0)
        )

        # Compute the business as usual energy expenses

        energy_consumption_full_kero = (
            co2_emissions_including_load_factor
            * 1e12
            / kerosene_emission_factor.loc[self.prospection_start_year - 1]
        )

        energy_consumption_BAU = (
            co2_emissions_2019technology
            * 1e12
            / kerosene_emission_factor.loc[self.prospection_start_year - 1]
        )

        non_discounted_BAU_energy_expenses = (
            energy_consumption_BAU
            / (density_kerosene * lhv_kerosene)
            * kerosene_market_price
            / 1000000
        )
        non_discounted_full_kero_energy_expenses = (
            energy_consumption_full_kero
            / (density_kerosene * lhv_kerosene)
            * kerosene_market_price
            / 1000000
        )

        self.df.loc[:, "non_discounted_energy_expenses"] = non_discounted_energy_expenses
        self.df.loc[:, "non_discounted_BAU_energy_expenses"] = non_discounted_BAU_energy_expenses
        self.df.loc[:, "non_discounted_full_kero_energy_expenses"] = (
            non_discounted_full_kero_energy_expenses
        )

        return (
            non_discounted_energy_expenses,
            non_discounted_full_kero_energy_expenses,
            non_discounted_BAU_energy_expenses,
        )


class DicountedScenarioCost(AeroMAPSModel):
    def __init__(self, name="discounted_scenario_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        social_discount_rate: float,
        kerosene_cost: pd.Series,
        biofuel_cost_hefa_fog: pd.Series,
        biofuel_cost_hefa_others: pd.Series,
        biofuel_cost_ft_others: pd.Series,
        biofuel_cost_ft_msw: pd.Series,
        biofuel_cost_atj: pd.Series,
        electrofuel_total_cost: pd.Series,
        total_hydrogen_supply_cost: pd.Series,
        electricity_direct_use_total_cost: pd.Series,
    ) -> pd.Series:
        for k in range(self.prospection_start_year, self.end_year + 1):
            # Compute the discounter at year k
            discount_k = (1 + social_discount_rate) ** (k - self.prospection_start_year)

            # Compute the discounted expenses for each energy pathway
            kerosene_discounted = kerosene_cost.fillna(0)[k] / discount_k
            biofuel_hefa_fog_discounted = biofuel_cost_hefa_fog.fillna(0)[k] / discount_k
            biofuel_hefa_others_discounted = biofuel_cost_hefa_others.fillna(0)[k] / discount_k
            biofuel_ft_others_discounted = biofuel_cost_ft_others.fillna(0)[k] / discount_k
            biofuel_ft_msw_discounted = biofuel_cost_ft_msw.fillna(0)[k] / discount_k
            biofuel_atj_discounted = biofuel_cost_atj.fillna(0)[k] / discount_k
            electrofuel_discounted = electrofuel_total_cost.fillna(0)[k] / discount_k
            hydrogen_discounted = total_hydrogen_supply_cost.fillna(0)[k] / discount_k
            electricity_direct_use_discounted = (
                electricity_direct_use_total_cost.fillna(0)[k] / discount_k
            )

            self.df.loc[k, "discounted_energy_expenses"] = (
                kerosene_discounted
                + biofuel_atj_discounted
                + biofuel_ft_msw_discounted
                + biofuel_ft_others_discounted
                + biofuel_hefa_others_discounted
                + biofuel_hefa_fog_discounted
                + electrofuel_discounted
                + hydrogen_discounted
                + electricity_direct_use_discounted
            )

        discounted_energy_expenses = self.df.loc[:, "discounted_energy_expenses"]

        return discounted_energy_expenses

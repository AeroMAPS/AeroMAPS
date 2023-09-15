# @Time : 13/03/2023 10:46
# @Author : a.salgas
# @File : scenario_cost.py
# @Software: PyCharm

from typing import Tuple

import pandas as pd
from aeromaps.models.base import AeromapsModel


class NonDiscountedScenarioCost(AeromapsModel):
    def __init__(self, name="non_discounted_scenario_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        kerosene_cost: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_hefa_fog: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_hefa_others: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_ft_others: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_ft_msw: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_atj: pd.Series = pd.Series(dtype="float64"),
        electrofuel_total_cost: pd.Series = pd.Series(dtype="float64"),
        total_hydrogen_supply_cost: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_premium_hefa_fog: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_premium_hefa_others: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_premium_ft_others: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_premium_ft_msw: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_premium_atj: pd.Series = pd.Series(dtype="float64"),
        h2_cost_premium_electrolysis: pd.Series = pd.Series(dtype="float64"),
        h2_cost_premium_gas_ccs: pd.Series = pd.Series(dtype="float64"),
        h2_cost_premium_gas: pd.Series = pd.Series(dtype="float64"),
        h2_cost_premium_coal_ccs: pd.Series = pd.Series(dtype="float64"),
        h2_cost_premium_coal: pd.Series = pd.Series(dtype="float64"),
        electrofuel_cost_premium: pd.Series = pd.Series(dtype="float64"),
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
        )

        # Compute the total cost premium compared to the "business as usual"
        non_discounted_energy_cost_premium = (
            biofuel_cost_premium_atj.fillna(0)
            + biofuel_cost_premium_ft_msw.fillna(0)
            + biofuel_cost_premium_ft_others.fillna(0)
            + biofuel_cost_premium_hefa_others.fillna(0)
            + biofuel_cost_premium_hefa_fog.fillna(0)
            + h2_cost_premium_electrolysis.fillna(0)
            + h2_cost_premium_gas_ccs.fillna(0)
            + h2_cost_premium_gas.fillna(0)
            + h2_cost_premium_coal_ccs.fillna(0)
            + h2_cost_premium_coal.fillna(0)
            + electrofuel_cost_premium.fillna(0)
        )

        # Compute the business as usual energy expenses
        non_discounted_BAU_energy_expenses = (
            non_discounted_energy_expenses - non_discounted_energy_cost_premium
        )

        self.df.loc[:, "non_discounted_energy_expenses"] = non_discounted_energy_expenses
        self.df.loc[:, "non_discounted_energy_cost_premium"] = non_discounted_energy_cost_premium
        self.df.loc[:, "non_discounted_BAU_energy_expenses"] = non_discounted_BAU_energy_expenses

        return (
            non_discounted_energy_expenses,
            non_discounted_energy_cost_premium,
            non_discounted_BAU_energy_expenses,
        )


class DicountedScenarioCost(AeromapsModel):
    def __init__(self, name="discounted_scenario_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        social_discount_rate: float = 0.0,
        kerosene_cost: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_hefa_fog: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_hefa_others: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_ft_others: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_ft_msw: pd.Series = pd.Series(dtype="float64"),
        biofuel_cost_atj: pd.Series = pd.Series(dtype="float64"),
        electrofuel_total_cost: pd.Series = pd.Series(dtype="float64"),
        total_hydrogen_supply_cost: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series]:

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

            self.df.loc[k, "discounted_energy_expenses"] = (
                kerosene_discounted
                + biofuel_atj_discounted
                + biofuel_ft_msw_discounted
                + biofuel_ft_others_discounted
                + biofuel_hefa_others_discounted
                + biofuel_hefa_fog_discounted
                + electrofuel_discounted
                + hydrogen_discounted
            )

        discounted_energy_expenses = self.df.loc[:, "discounted_energy_expenses"]

        return discounted_energy_expenses

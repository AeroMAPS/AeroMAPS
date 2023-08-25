# @Time : 13/03/2023 10:46
# @Author : a.salgas
# @File : scenario_cost.py
# @Software: PyCharm

from typing import Tuple

import numpy as np
import pandas as pd
from aeromaps.models.base import AeromapsModel

from scipy.interpolate import interp1d


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
            liquefaction_h2_total_cost: pd.Series = pd.Series(dtype="float64"),
            transport_h2_total_cost: pd.Series = pd.Series(dtype="float64"),
            electrofuel_cost_premium: pd.Series = pd.Series(dtype="float64"),

    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        # TODO add hydrogen and e-kero cost premiums
        print("Tha 1")

        non_discounted_energy_expenses = kerosene_cost \
                                         + biofuel_cost_hefa_fog \
                                         + biofuel_cost_hefa_others \
                                         + biofuel_cost_ft_others \
                                         + biofuel_cost_ft_msw \
                                         + biofuel_cost_atj \
                                         + electrofuel_total_cost \
                                         + total_hydrogen_supply_cost

        non_discounted_energy_cost_premium = biofuel_cost_premium_atj \
                                             + biofuel_cost_premium_ft_msw \
                                             + biofuel_cost_premium_ft_others \
                                             + biofuel_cost_premium_hefa_others \
                                             + biofuel_cost_premium_hefa_fog \
                                             + h2_cost_premium_electrolysis \
                                             + h2_cost_premium_gas_ccs \
                                             + h2_cost_premium_gas \
                                             + h2_cost_premium_coal_ccs \
                                             + h2_cost_premium_coal \
                                             + electrofuel_cost_premium

        print(total_hydrogen_supply_cost)

        non_discounted_BAU_energy_expenses = non_discounted_energy_expenses - non_discounted_energy_cost_premium

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
            kerosene_discounted = kerosene_cost[k] / (1 + social_discount_rate) ** (k - self.prospection_start_year)
            biofuel_hefa_fog_discounted = biofuel_cost_hefa_fog[k] / (1 + social_discount_rate) ** (
                    k - self.prospection_start_year)
            biofuel_hefa_others_discounted = biofuel_cost_hefa_others[k] / (1 + social_discount_rate) ** (
                    k - self.prospection_start_year)
            biofuel_ft_others_discounted = biofuel_cost_ft_others[k] / (1 + social_discount_rate) ** (
                    k - self.prospection_start_year)
            biofuel_ft_msw_discounted = biofuel_cost_ft_msw[k] / (1 + social_discount_rate) ** (
                    k - self.prospection_start_year)
            biofuel_atj_discounted = biofuel_cost_atj[k] / (1 + social_discount_rate) ** (
                    k - self.prospection_start_year)
            electrofuel_discounted = electrofuel_total_cost[k] / (1 + social_discount_rate) ** (
                    k - self.prospection_start_year)
            hydrogen_discounted = total_hydrogen_supply_cost[k] / (1 + social_discount_rate) ** (
                    k - self.prospection_start_year)

            # TODO add new pathways
            self.df.loc[k, "discounted_energy_expenses"] = kerosene_discounted \
                                                           + biofuel_atj_discounted \
                                                           + biofuel_ft_msw_discounted \
                                                           + biofuel_ft_others_discounted \
                                                           + biofuel_hefa_others_discounted \
                                                           + biofuel_hefa_fog_discounted \
                                                           + electrofuel_discounted \
                                                           + hydrogen_discounted

        discounted_energy_expenses = self.df.loc[:, "discounted_energy_expenses"]

        return discounted_energy_expenses

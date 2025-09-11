# @Time : 13/03/2023 10:46
# @Author : a.salgas
# @File : scenario_cost.py
# @Software: PyCharm

from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class NonDiscountedEnergyCost(AeroMAPSModel):
    def __init__(self, name="non_discounted_energy_cost", *args, **kwargs):
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


class DicountedEnergyCost(AeroMAPSModel):
    def __init__(self, name="discounted_energy_cost", *args, **kwargs):
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
    ) -> Tuple[pd.Series, float]:
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

        discounted_energy_expenses_obj = discounted_energy_expenses.cumsum()[self.end_year]

        return discounted_energy_expenses, discounted_energy_expenses_obj


class TotalAirlineCostNoElast(AeroMAPSModel):
    def __init__(self, name="total_airline_cost_no_elast", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        total_cost_per_rpk: pd.Series,
        rpk: pd.Series,
        social_discount_rate: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        float,
    ]:
        initial_airline_cost = total_cost_per_rpk[self.prospection_start_year - 1] * rpk
        total_airline_cost = total_cost_per_rpk * rpk
        total_airline_cost_increase = total_airline_cost - initial_airline_cost

        total_airline_cost_discounted = total_airline_cost / (1 + social_discount_rate) ** (
            self.df.index - self.prospection_start_year
        )

        total_airline_cost_increase_discounted = total_airline_cost_increase / (
            1 + social_discount_rate
        ) ** (self.df.index - self.prospection_start_year)

        cumulative_total_airline_cost = total_airline_cost.cumsum()
        cumulative_total_airline_cost_discounted = total_airline_cost_discounted.cumsum()

        cumulative_total_airline_cost_increase = total_airline_cost_increase.cumsum()
        cumulative_total_airline_cost_increase_discounted = (
            total_airline_cost_increase_discounted.cumsum()
        )

        self.df.loc[:, "total_airline_cost"] = total_airline_cost
        self.df.loc[:, "cumulative_total_airline_cost"] = cumulative_total_airline_cost
        self.df.loc[:, "cumulative_total_airline_cost_discounted"] = (
            cumulative_total_airline_cost_discounted
        )
        self.df.loc[:, "total_airline_cost_increase"] = total_airline_cost_increase
        self.df.loc[:, "cumulative_total_airline_cost_increase"] = (
            cumulative_total_airline_cost_increase
        )
        self.df.loc[:, "cumulative_total_airline_cost_increase_discounted"] = (
            cumulative_total_airline_cost_increase_discounted
        )

        cumulative_total_airline_cost_discounted_obj = (
            cumulative_total_airline_cost_increase_discounted[self.end_year]
            - cumulative_total_airline_cost_increase_discounted[2025]
        )

        return (
            total_airline_cost,
            cumulative_total_airline_cost,
            cumulative_total_airline_cost_discounted,
            cumulative_total_airline_cost_increase,
            cumulative_total_airline_cost_increase_discounted,
            cumulative_total_airline_cost_discounted_obj,
        )


class TotalAirlineCost(AeroMAPSModel):
    def __init__(self, name="total_airline_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        total_cost_per_rpk: pd.Series,
        rpk: pd.Series,
        rpk_no_elasticity: pd.Series,
        social_discount_rate: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        float,
    ]:
        initial_airline_cost = (
            total_cost_per_rpk[self.prospection_start_year - 1] * rpk_no_elasticity
        )
        total_airline_cost = total_cost_per_rpk * rpk
        total_airline_cost_increase = total_airline_cost - initial_airline_cost

        total_airline_cost_discounted = total_airline_cost / (1 + social_discount_rate) ** (
            self.df.index - self.prospection_start_year
        )

        total_airline_cost_increase_discounted = total_airline_cost_increase / (
            1 + social_discount_rate
        ) ** (self.df.index - self.prospection_start_year)

        cumulative_total_airline_cost = total_airline_cost.cumsum()
        cumulative_total_airline_cost_discounted = total_airline_cost_discounted.cumsum()

        cumulative_total_airline_cost_increase = total_airline_cost_increase.cumsum()
        cumulative_total_airline_cost_increase_discounted = (
            total_airline_cost_increase_discounted.cumsum()
        )

        self.df.loc[:, "total_airline_cost"] = total_airline_cost
        self.df.loc[:, "cumulative_total_airline_cost"] = cumulative_total_airline_cost
        self.df.loc[:, "cumulative_total_airline_cost_discounted"] = (
            cumulative_total_airline_cost_discounted
        )
        self.df.loc[:, "total_airline_cost_increase"] = total_airline_cost_increase
        self.df.loc[:, "cumulative_total_airline_cost_increase"] = (
            cumulative_total_airline_cost_increase
        )
        self.df.loc[:, "cumulative_total_airline_cost_increase_discounted"] = (
            cumulative_total_airline_cost_increase_discounted
        )

        cumulative_total_airline_cost_discounted_obj = (
            cumulative_total_airline_cost_increase_discounted[self.end_year]
            - cumulative_total_airline_cost_increase_discounted[2025]
        )

        return (
            total_airline_cost,
            cumulative_total_airline_cost,
            cumulative_total_airline_cost_discounted,
            cumulative_total_airline_cost_increase,
            cumulative_total_airline_cost_increase_discounted,
            cumulative_total_airline_cost_discounted_obj,
        )


# class TotalAirlineProfit(AeroMAPSModel):
#     def __init__(self, name="total_airline_profit", *args, **kwargs):
#         super().__init__(name, *args, **kwargs)
#
#     def compute(
#         self,
#         operational_profit_per_rpk: pd.Series,
#         rpk: pd.Series,
#         rpk_no_elasticity: pd.Series,
#         social_discount_rate: float,
#     ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series,]:
#
#
#         # TODO: to deprecate
#
#         total_airline_profit = operational_profit_per_rpk * rpk
#         cumulative_total_airline_profit = total_airline_profit.cumsum()
#         cumulative_total_airline_profit_discounted = cumulative_total_airline_profit / (
#             1 + social_discount_rate
#         ) ** (self.df.index - self.prospection_start_year)
#
#         airline_profit_loss = (
#             operational_profit_per_rpk[self.prospection_start_year - 1] * rpk_no_elasticity
#             - operational_profit_per_rpk * rpk
#         )
#         cumulative_airline_profit_loss = airline_profit_loss.cumsum()
#         cumulative_airline_profit_loss_discounted = cumulative_airline_profit_loss / (
#             1 + social_discount_rate
#         ) ** (self.df.index - self.prospection_start_year)
#
#         self.df.loc[:, "total_airline_profit"] = total_airline_profit
#         self.df.loc[:, "cumulative_total_airline_profit"] = cumulative_total_airline_profit
#         self.df.loc[
#             :, "cumulative_total_airline_profit_discounted"
#         ] = cumulative_total_airline_profit_discounted
#         self.df.loc[:, "airline_profit_loss"] = airline_profit_loss
#         self.df.loc[:, "cumulative_airline_profit_loss"] = cumulative_airline_profit_loss
#         self.df.loc[
#             :, "cumulative_airline_profit_loss_discounted"
#         ] = cumulative_airline_profit_loss_discounted
#
#         return (
#             total_airline_profit,
#             cumulative_total_airline_profit,
#             cumulative_total_airline_profit_discounted,
#             airline_profit_loss,
#             cumulative_airline_profit_loss,
#             cumulative_airline_profit_loss_discounted,
#         )


# class TotalTaxRevenue(AeroMAPSModel):
#    def __init__(self, name="total_tax_revenue", *args, **kwargs):
#        super().__init__(name, *args, **kwargs)

#    def compute(
#        self,
#        total_extra_tax_per_rpk: pd.Series,
#        rpk: pd.Series,
#       rpk_no_elasticity: pd.Series,
#        social_discount_rate: float,
#    ) -> Tuple[
#        pd.Series,
#        pd.Series,
#        pd.Series,
#        pd.Series,
#        pd.Series,
#        pd.Series,
#   ]:
#      total_tax_revenue = total_extra_tax_per_rpk * rpk
#     cumulative_total_tax_revenue = total_tax_revenue.cumsum()
#    cumulative_total_tax_revenue_discounted = cumulative_total_tax_revenue / (
#       1 + social_discount_rate
#  ) ** (self.df.index - self.prospection_start_year)
#
#       tax_revenue_loss = (
#          total_extra_tax_per_rpk[self.prospection_start_year - 1] * rpk_no_elasticity
#         - total_extra_tax_per_rpk * rpk
#    )
#   cumulative_tax_revenue_loss = tax_revenue_loss.cumsum()
#  cumulative_tax_revenue_loss_discounted = cumulative_tax_revenue_loss / (
#     1 + social_discount_rate
# ) ** (self.df.index - self.prospection_start_year)
#
#       self.df.loc[:, "total_tax_revenue"] = total_tax_revenue
#      self.df.loc[:, "cumulative_total_tax_revenue"] = cumulative_total_tax_revenue
#    self.df.loc[:, "cumulative_total_tax_revenue_discounted"] = (
##         cumulative_total_tax_revenue_discounted
#   )
#  self.df.loc[:, "tax_revenue_loss"] = tax_revenue_loss
#  self.df.loc[:, "cumulative_tax_revenue_loss"] = cumulative_tax_revenue_loss
# self.df.loc[:, "cumulative_tax_revenue_loss_discounted"] = (
#    cumulative_tax_revenue_loss_discounted
# )

#        return (
#           total_tax_revenue,
#          cumulative_total_tax_revenue,
#         cumulative_total_tax_revenue_discounted,
#        tax_revenue_loss,
#       cumulative_tax_revenue_loss,
#      cumulative_tax_revenue_loss_discounted,
# )


class TotalSurplusLoss(AeroMAPSModel):
    def __init__(self, name="total_surplus_loss", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        rpk: pd.Series,
        rpk_no_elasticity: pd.Series,
        cumulative_total_airline_cost_increase: pd.Series,
        cumulative_total_airline_cost_increase_discounted: pd.Series,
        airfare_per_rpk: pd.Series,
        price_elasticity: float,
        social_discount_rate: float,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, float]:
        # computation of demand function parameters: asummption => constant elasticity => P= beta * Q**(1/elasticity)
        beta = airfare_per_rpk[2025] / (rpk_no_elasticity ** (1 / price_elasticity))

        # Gloabl Surplus before removing total costs

        if price_elasticity == -1:
            # surplus delta extresssed by CS= beta * np.log(Qref/Qi)
            area_loss = beta * np.log(rpk_no_elasticity / rpk)

        else:
            # surplus delta expressed by
            # area_loss = (
            #     beta
            #     * (-1 / (1 + price_elasticity))
            #     * (
            #         rpk_no_elasticity ** (1 + 1 / price_elasticity)
            #         - rpk ** (1 + 1 / price_elasticity)
            #     )
            # )
            area_loss = (
                beta
                * (1 / (1 + 1 / price_elasticity))
                * (
                    rpk_no_elasticity ** (1 + 1 / price_elasticity)
                    - rpk ** (1 + 1 / price_elasticity)
                )
            )

        self.df.loc[:, "area_loss"] = area_loss

        area_loss_discounted = area_loss / (1 + social_discount_rate) ** (
            self.df.index - self.prospection_start_year
        )

        self.df.loc[:, "area_loss_discounted"] = area_loss_discounted

        cumulative_total_surplus_loss = area_loss.cumsum() + cumulative_total_airline_cost_increase
        cumulative_total_surplus_loss_discounted = (
            area_loss_discounted.cumsum()
            + cumulative_total_airline_cost_increase_discounted[self.end_year]
            - cumulative_total_airline_cost_increase_discounted[2025]
        )

        self.df.loc[:, "cumulative_total_surplus_loss"] = cumulative_total_surplus_loss
        self.df.loc[:, "cumulative_total_surplus_loss_discounted"] = (
            cumulative_total_surplus_loss_discounted
        )

        cumulative_total_surplus_loss_discounted_obj = cumulative_total_surplus_loss_discounted[
            self.end_year
        ]

        return (
            area_loss,
            cumulative_total_surplus_loss,
            cumulative_total_surplus_loss_discounted,
            cumulative_total_surplus_loss_discounted_obj,
        )


# class TotalWelfareLoss(AeroMAPSModel):
#     def __init__(self, name="total_welfare_loss", *args, **kwargs):
#         super().__init__(name, *args, **kwargs)
#
#     def compute(
#         self,
#         consumer_surplus_loss: pd.Series,
#         cumulative_total_surplus_loss: pd.Series,
#         cumulative_total_surplus_loss_discounted: pd.Series,
#         airline_profit_loss: pd.Series,
#         cumulative_airline_profit_loss: pd.Series,
#         cumulative_airline_profit_loss_discounted: pd.Series,
#         tax_revenue_loss: pd.Series,
#         cumulative_tax_revenue_loss: pd.Series,
#         cumulative_tax_revenue_loss_discounted: pd.Series,
#     ) -> Tuple[pd.Series, pd.Series, pd.Series,]:
#
#         # TODO: to deprecate
#
#         total_welfare_loss = consumer_surplus_loss + airline_profit_loss + tax_revenue_loss
#         cumulative_total_welfare_loss = (
#             cumulative_total_surplus_loss
#             + cumulative_airline_profit_loss
#             + cumulative_tax_revenue_loss
#         )
#         cumulative_total_welfare_loss_discounted = (
#             cumulative_total_surplus_loss_discounted
#             + cumulative_airline_profit_loss_discounted
#             + cumulative_tax_revenue_loss_discounted
#         )
#
#         self.df.loc[:, "total_welfare_loss"] = total_welfare_loss
#         self.df.loc[:, "cumulative_total_welfare_loss"] = cumulative_total_welfare_loss
#         self.df.loc[
#             :, "cumulative_total_welfare_loss_discounted"
#         ] = cumulative_total_welfare_loss_discounted
#
#         return (
#             total_welfare_loss,
#             cumulative_total_welfare_loss,
#             cumulative_total_welfare_loss_discounted,
#         )

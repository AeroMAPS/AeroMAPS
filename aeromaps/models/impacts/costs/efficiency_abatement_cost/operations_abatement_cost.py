# @Time : 06/02/2024 15:12
# @Author : a.salgas
# @File : operations_abatement_cost.py
# @Software: PyCharm
from typing import Tuple

import pandas as pd
from aeromaps.models.base import AeromapsModel, AeromapsInterpolationFunction


class OperationsAbatementCost(AeromapsModel):
    def __init__(self, name="operations_abatement_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        operational_efficiency_cost_non_energy_per_ask: pd.Series = pd.Series(dtype="float64"),
        operations_gain: pd.Series = pd.Series(dtype="float64"),
        kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
        kerosene_emission_factor: pd.Series = pd.Series(dtype="float64"),
        ask: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_mean_without_operations: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_mean: pd.Series = pd.Series(dtype="float64"),
        rpk: pd.Series = pd.Series(dtype="float64"),
        load_factor: pd.Series = pd.Series(dtype="float64"),
        load_factor_cost_non_energy_per_ask: pd.Series = pd.Series(dtype="float64"),
        social_discount_rate: float = 0.0,
        operations_duration: float = 0.0,
        operations_start_year: float = 0.0,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:

        fuel_lhv = 35.3

        emissions_reduction_operations = (
            energy_per_ask_mean_without_operations
            * operations_gain
            / 100
            * kerosene_emission_factor
            / 1000000
        )

        extra_cost_operations_non_fuel = operational_efficiency_cost_non_energy_per_ask

        extra_cost_operations_fuel = (
            -energy_per_ask_mean_without_operations
            * operations_gain
            / 100
            * kerosene_market_price
            / fuel_lhv
        )

        operations_abatement_cost = (
            extra_cost_operations_non_fuel + extra_cost_operations_fuel
        ) / emissions_reduction_operations

        self.df.loc[:, "operations_abatement_cost"] = operations_abatement_cost
        self.df.loc[:, "operations_abatement_effective"] = (
            emissions_reduction_operations
            * rpk
            / load_factor.loc[self.prospection_start_year - 1]
            * 100
        )

        # Definition of a specific abatement cost, comparable to a hotelling growth carbon value.
        # Discount the costs/benefits over the horizon necessary to deploy the incremental gains of a year
        for k in range(int(operations_start_year), self.end_year + 1):
            self.df.loc[k, "operations_specific_abatement_cost"] = self._get_discounted_vals(
                k,
                social_discount_rate,
                operations_duration,
                extra_cost_operations_non_fuel,
                extra_cost_operations_fuel,
                kerosene_market_price,
                emissions_reduction_operations,
            )

        operations_specific_abatement_cost = self.df["operations_specific_abatement_cost"]

        energy_per_rpk_base = (
            energy_per_ask_mean / load_factor.loc[self.prospection_start_year - 1] * 100
        )
        energy_per_rpk_real = energy_per_ask_mean / load_factor * 100

        emissions_reduction_load_factor = (
            (energy_per_rpk_base - energy_per_rpk_real) * kerosene_emission_factor / 1000000
        )
        extra_cost_load_factor_fuel = (
            -(energy_per_rpk_base - energy_per_rpk_real) * kerosene_market_price / fuel_lhv
        )
        extra_cost_load_factor_non_fuel = load_factor_cost_non_energy_per_ask

        load_factor_abatement_cost = (
            extra_cost_load_factor_fuel + extra_cost_load_factor_non_fuel
        ) / emissions_reduction_load_factor

        self.df.loc[:, "load_factor_abatement_cost"] = load_factor_abatement_cost
        self.df.loc[:, "load_factor_abatement_effective"] = emissions_reduction_load_factor * rpk

        # Definition of a specific abatement cost, comparable to a hotelling growth carbon value.
        # Discount the costs/benefits over the scenario temporal span.
        # Caution: the longer the scenario, the lower the specific abatement cost
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "load_factor_specific_abatement_cost"] = self._get_discounted_vals(
                k,
                social_discount_rate,
                self.end_year - self.prospection_start_year,
                extra_cost_load_factor_non_fuel,
                extra_cost_load_factor_fuel,
                kerosene_market_price,
                emissions_reduction_load_factor,
            )

        load_factor_specific_abatement_cost = self.df["load_factor_specific_abatement_cost"]

        print(load_factor_abatement_cost, load_factor_specific_abatement_cost)

        return (
            operations_abatement_cost,
            operations_specific_abatement_cost,
            load_factor_abatement_cost,
            load_factor_specific_abatement_cost,
        )

    def _get_discounted_vals(
        self,
        year,
        discount_rate,
        operations_duration,
        extra_cost_non_fuel,
        extra_cost_fuel,
        kerosene_market_price,
        emissions_reduction,
    ):

        discounted_cumul_cost = 0
        cumul_em = 0
        for i in range(year, year + int(operations_duration)):
            if i < (self.end_year + 1):
                discounted_cumul_cost += (
                    extra_cost_non_fuel[year]
                    + extra_cost_fuel[year] * kerosene_market_price[i] / kerosene_market_price[year]
                ) / (1 + discount_rate) ** (i - year)
                cumul_em += emissions_reduction[year]
            else:
                discounted_cumul_cost += (
                    extra_cost_non_fuel[year]
                    + extra_cost_fuel[year]
                    * kerosene_market_price[self.end_year]
                    / kerosene_market_price[year]
                ) / (1 + discount_rate) ** (i - year)
                cumul_em += emissions_reduction[year]

        return discounted_cumul_cost / cumul_em

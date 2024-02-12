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
        operational_efficiency_cost_non_energy_per_ask: pd.Series = pd.Series(
            dtype="float64"
        ),
        operations_gain: pd.Series = pd.Series(dtype="float64"),
        kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
        kerosene_emission_factor: pd.Series = pd.Series(dtype="float64"),
        ask: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_mean_without_operations: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_mean: pd.Series = pd.Series(dtype="float64"),
        rpk: pd.Series = pd.Series(dtype="float64"),
        load_factor: pd.Series = pd.Series(dtype="float64"),
        load_factor_cost_non_energy_per_ask: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[
        pd.Series,
        pd.Series
    ]:

        fuel_lhv = 35.3

        emissions_reduction_operations = (
            energy_per_ask_mean_without_operations
            * operations_gain / 100
            * kerosene_emission_factor
            / 1000000
        )

        extra_cost_operations = (
                operational_efficiency_cost_non_energy_per_ask
                - energy_per_ask_mean_without_operations
                * operations_gain / 100
                * kerosene_market_price
                / fuel_lhv
        )

        operations_abatement_cost = extra_cost_operations / emissions_reduction_operations

        self.df.loc[:, "operations_abatement_cost"] = operations_abatement_cost
        self.df.loc[:, "operations_abatement_effective"] = emissions_reduction_operations * rpk / load_factor.loc[self.prospection_start_year-1] * 100

        energy_per_rpk_base = energy_per_ask_mean / load_factor.loc[self.prospection_start_year - 1] * 100
        energy_per_rpk_real = energy_per_ask_mean / load_factor * 100

        emissions_reduction_load_factor = (
                (energy_per_rpk_base - energy_per_rpk_real)
                * kerosene_emission_factor
                / 1000000
        )
        extra_cost_load_factor = (
                load_factor_cost_non_energy_per_ask
                - (energy_per_rpk_base - energy_per_rpk_real)
                * kerosene_market_price
                / fuel_lhv
        )

        load_factor_abatement_cost = extra_cost_load_factor / emissions_reduction_load_factor


        self.df.loc[:, "load_factor_abatement_cost"] = load_factor_abatement_cost
        self.df.loc[:, "load_factor_abatement_effective"] = emissions_reduction_load_factor * rpk

        return (
            operations_abatement_cost,
            load_factor_abatement_cost
        )





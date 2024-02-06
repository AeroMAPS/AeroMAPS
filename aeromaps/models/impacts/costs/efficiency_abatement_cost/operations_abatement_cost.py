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
        operational_efficiency_cost_per_ask: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_without_operations_short_range_dropin_fuel: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_ask_without_operations_medium_range_dropin_fuel: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_ask_without_operations_long_range_dropin_fuel: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_ask_without_operations_short_range_hydrogen: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_ask_without_operations_medium_range_hydrogen: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_ask_without_operations_long_range_hydrogen: pd.Series = pd.Series(
            dtype="float64"
        ),
        operations_gain: pd.Series = pd.Series(dtype="float64"),
        kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
        kerosene_emission_factor: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series]:

        energy_per_ask_without_operations_total = (
            energy_per_ask_without_operations_short_range_dropin_fuel
            + energy_per_ask_without_operations_medium_range_dropin_fuel
            + energy_per_ask_without_operations_long_range_dropin_fuel
            + energy_per_ask_without_operations_short_range_hydrogen
            + energy_per_ask_without_operations_medium_range_hydrogen
            + energy_per_ask_without_operations_long_range_hydrogen
        )
        fuel_lhv = 35.3

        emissions_reduction_operations = (
            energy_per_ask_without_operations_total
            * operations_gain
            * kerosene_emission_factor
            / 1000000
        )
        extra_cost_operations = (
            operational_efficiency_cost_per_ask
            - energy_per_ask_without_operations_total
            * operations_gain
            * kerosene_market_price
            / fuel_lhv
        )

        operations_abatement_cost = extra_cost_operations / emissions_reduction_operations

        self.df.loc[:, "operations_abatement_cost"] = operations_abatement_cost

        return operations_abatement_cost

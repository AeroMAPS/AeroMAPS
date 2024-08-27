# @Time : 31/05/2024 11:01
# @Author : a.salgas
# @File : electricity_direct_use.py
# @Software: PyCharm
from typing import Tuple

import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class ElectricityDirectUse(AeroMAPSModel):
    def __init__(self, name="electricity_direct_use", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_electric: pd.Series,
        electricity_emission_factor: pd.Series,
        electricity_market_price: pd.Series,
        carbon_tax: pd.Series,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        electricity_direct_use_total_cost = (
            energy_consumption_electric
            * electricity_market_price
            / 3.6  # kWh to MJ
            / 1000000
        )
        self.df.loc[:, "electricity_direct_use_total_cost"] = electricity_direct_use_total_cost

        electricity_direct_use_carbon_tax = (
            energy_consumption_electric
            * electricity_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )

        self.df.loc[:, "electricity_direct_use_carbon_tax"] = electricity_direct_use_carbon_tax

        electricity_direct_use_carbon_tax_kWh = (
            carbon_tax * electricity_emission_factor / 1000000 * 3.6
        )

        self.df.loc[:, "electricity_direct_use_carbon_tax_kWh"] = (
            electricity_direct_use_carbon_tax_kWh
        )

        return (
            electricity_direct_use_total_cost,
            electricity_direct_use_carbon_tax,
            electricity_direct_use_carbon_tax_kWh,
        )

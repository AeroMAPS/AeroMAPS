# @Time : 27/02/2023 17:19
# @Author : a.salgas
# @File : market_prices.py
# @Software: PyCharm

from typing import Tuple

import numpy as np
import pandas as pd
from aeromaps.models.base import AeromapsModel

from scipy.interpolate import interp1d


class ElectricityCost(AeromapsModel):
    def __init__(self, name="electricity_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            electricity_cost_2020: float = 0.0,
            electricity_cost_2030: float = 0.0,
            electricity_cost_2040: float = 0.0,
            electricity_cost_2050: float = 0.0,
    ) -> Tuple[pd.Series]:
        """LCOE"""
        # FT MSW
        reference_values_electricity = [
            electricity_cost_2020,
            electricity_cost_2030,
            electricity_cost_2040,
            electricity_cost_2050
        ]

        reference_years = [2020, 2030, 2040, 2050]

        electricity_price_function = interp1d(
            reference_years, reference_values_electricity, kind="quadratic"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[
                k, "electricity_market_price"
            ] = electricity_price_function(k)

        electricity_market_price = self.df.loc[:, "electricity_market_price"]

        return (
            electricity_market_price
        )


class Co2Cost(AeromapsModel):
    def __init__(self, name="co2_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            co2_cost_2020: float = 0.0,
            co2_cost_2030: float = 0.0,
            co2_cost_2040: float = 0.0,
            co2_cost_2050: float = 0.0,
    ) -> Tuple[pd.Series]:
        """LCOE"""
        # FT MSW
        reference_values_co2 = [
            co2_cost_2020,
            co2_cost_2030,
            co2_cost_2040,
            co2_cost_2050
        ]

        reference_years = [2020, 2030, 2040, 2050]

        co2_price_function = interp1d(
            reference_years, reference_values_co2, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[
                k, "co2_market_price"
            ] = co2_price_function(k)

        co2_market_price = self.df.loc[:, "co2_market_price"]

        return (
            co2_market_price
        )


class KerosenePrice(AeromapsModel):
    def __init__(self, name="kerosene_market_price", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            kerosene_price_2020: float = 0.0,
            kerosene_price_2030: float = 0.0,
            kerosene_price_2040: float = 0.0,
            kerosene_price_2050: float = 0.0,
    ) -> Tuple[pd.Series]:

        # FT MSW
        reference_values_kerosene = [
            kerosene_price_2020,
            kerosene_price_2030,
            kerosene_price_2040,
            kerosene_price_2050
        ]

        reference_years = [2020, 2030, 2040, 2050]

        kerosene_price_function = interp1d(
            reference_years, reference_values_kerosene, kind="quadratic"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[
                k, "kerosene_market_price"
            ] = kerosene_price_function(k)


        kerosene_market_price = self.df.loc[:, "kerosene_market_price"]

        return (
            kerosene_market_price
        )


class KeroseneCost(AeromapsModel):
    def __init__(self, name="kerosene_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            kerosene_market_price: pd.Series=pd.Series(dtype="float64"),
            energy_consumption_kerosene: pd.Series=pd.Series(dtype="float64")
    ) -> Tuple[pd.Series]:

        # kerosene_market_price €/L

        fuel_lhv = 35.3

        kerosene_cost = energy_consumption_kerosene / fuel_lhv * kerosene_market_price / 1000000
        #M€

        self.df.loc[:, 'kerosene_cost'] = kerosene_cost

        return (
            kerosene_cost
        )
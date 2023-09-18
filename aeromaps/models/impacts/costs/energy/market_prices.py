# @Time : 27/02/2023 17:19
# @Author : a.salgas
# @File : market_prices.py
# @Software: PyCharm

from typing import Tuple

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

        reference_values_electricity = [
            electricity_cost_2020,
            electricity_cost_2030,
            electricity_cost_2040,
            electricity_cost_2050,
        ]

        reference_years = [2020, 2030, 2040, 2050]

        electricity_price_function = interp1d(
            reference_years, reference_values_electricity, kind="quadratic"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "electricity_market_price"] = electricity_price_function(k)

        electricity_market_price = self.df.loc[:, "electricity_market_price"]

        return electricity_market_price


class CoalCost(AeromapsModel):
    def __init__(self, name="coal_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        coal_cost_2020: float = 0.0,
        coal_cost_2030: float = 0.0,
        coal_cost_2040: float = 0.0,
        coal_cost_2050: float = 0.0,
    ) -> Tuple[pd.Series]:

        reference_values_coal = [coal_cost_2020, coal_cost_2030, coal_cost_2040, coal_cost_2050]

        reference_years = [2020, 2030, 2040, 2050]

        coal_price_function = interp1d(reference_years, reference_values_coal, kind="quadratic")
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "coal_market_price"] = coal_price_function(k)

        coal_market_price = self.df.loc[:, "coal_market_price"]

        return coal_market_price


class GasCost(AeromapsModel):
    def __init__(self, name="gas_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        gas_cost_2020: float = 0.0,
        gas_cost_2030: float = 0.0,
        gas_cost_2040: float = 0.0,
        gas_cost_2050: float = 0.0,
    ) -> Tuple[pd.Series]:

        reference_values_gas = [gas_cost_2020, gas_cost_2030, gas_cost_2040, gas_cost_2050]

        reference_years = [2020, 2030, 2040, 2050]

        gas_price_function = interp1d(reference_years, reference_values_gas, kind="quadratic")
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "gas_market_price"] = gas_price_function(k)

        gas_market_price = self.df.loc[:, "gas_market_price"]

        return gas_market_price


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

        reference_values_co2 = [co2_cost_2020, co2_cost_2030, co2_cost_2040, co2_cost_2050]

        reference_years = [2020, 2030, 2040, 2050]

        co2_price_function = interp1d(reference_years, reference_values_co2, kind="linear")
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "co2_market_price"] = co2_price_function(k)

        co2_market_price = self.df.loc[:, "co2_market_price"]

        return co2_market_price


class Co2Tax(AeromapsModel):
    def __init__(self, name="co2_tax", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        co2_tax_2020: float = 0.0,
        co2_tax_2030: float = 0.0,
        co2_tax_2040: float = 0.0,
        co2_tax_2050: float = 0.0,
    ) -> Tuple[pd.Series]:

        reference_values_co2 = [co2_tax_2020, co2_tax_2030, co2_tax_2040, co2_tax_2050]

        reference_years = [2020, 2030, 2040, 2050]

        co2_price_function = interp1d(reference_years, reference_values_co2, kind="linear")
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "carbon_tax"] = co2_price_function(k)

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "carbon_tax"] = 5.0

        carbon_tax = self.df.loc[:, "carbon_tax"]

        return carbon_tax


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

        reference_values_kerosene = [
            kerosene_price_2020,
            kerosene_price_2030,
            kerosene_price_2040,
            kerosene_price_2050,
        ]

        reference_years = [2020, 2030, 2040, 2050]

        kerosene_price_function = interp1d(
            reference_years, reference_values_kerosene, kind="quadratic"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "kerosene_market_price"] = kerosene_price_function(k)

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "kerosene_market_price"] = self.df.loc[2020, "kerosene_market_price"]

        kerosene_market_price = self.df.loc[:, "kerosene_market_price"]

        return kerosene_market_price


class KeroseneCost(AeromapsModel):
    def __init__(self, name="kerosene_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
        energy_consumption_kerosene: pd.Series = pd.Series(dtype="float64"),
        kerosene_emission_factor: pd.Series = pd.Series(dtype="float64"),
        carbon_tax: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        # kerosene_market_price €/L

        # fuel lower heating value in MJ/L at 15 degrees
        fuel_lhv = 35.3

        kerosene_cost = energy_consumption_kerosene / fuel_lhv * kerosene_market_price / 1000000
        # M€

        # Compute the carbon tax(M€)

        # Kerosene EF is in GCO2e/MJ ; energy consumption in MJ; carbon tax in €/tCO2e ==> conversion in M€

        kerosene_carbon_tax_cost = (
            carbon_tax * kerosene_emission_factor / 1000000 * energy_consumption_kerosene / 1000000
        )

        # Price per litter supplement due to carbon tax [€/L]

        kerosene_price_supplement_carbon_tax = (
            kerosene_carbon_tax_cost / energy_consumption_kerosene * 1000000 * fuel_lhv
        )

        self.df.loc[:, "kerosene_cost"] = kerosene_cost
        self.df.loc[:, "kerosene_carbon_tax_cost"] = kerosene_carbon_tax_cost
        self.df.loc[
            :, "kerosene_price_supplement_carbon_tax"
        ] = kerosene_price_supplement_carbon_tax

        return (kerosene_cost, kerosene_carbon_tax_cost, kerosene_price_supplement_carbon_tax)


class KeroseneBAUCost(AeromapsModel):
    def __init__(self, name="kerosene_BAU_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
        non_discounted_BAU_energy_expenses: pd.Series = pd.Series(dtype="float64"),
        kerosene_emission_factor: pd.Series = pd.Series(dtype="float64"),
        carbon_tax: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        # kerosene_market_price €/L
        # fuel lower heating value in MJ/L at 15 degrees
        fuel_lhv = 35.3

        # Quantity of kerosene used in BAU (virtual)

        kerosene_consumption_BAU = (
            non_discounted_BAU_energy_expenses / kerosene_market_price * 1000000 * fuel_lhv
        )

        # Carbon tax that would be paid in BAU

        kerosene_carbon_tax_BAU = (
            kerosene_consumption_BAU * carbon_tax * kerosene_emission_factor / 1000000 / 1000000
        )

        self.df.loc[:, "kerosene_carbon_tax_BAU"] = kerosene_carbon_tax_BAU

        return kerosene_carbon_tax_BAU

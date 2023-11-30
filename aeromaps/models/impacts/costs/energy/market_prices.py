# @Time : 27/02/2023 17:19
# @Author : a.salgas
# @File : market_prices.py
# @Software: PyCharm

from typing import Tuple

import pandas as pd
from aeromaps.models.base import AeromapsModel, InterpolationAeromapsFunction

from scipy.interpolate import interp1d


class ElectricityCost(AeromapsModel):
    def __init__(self, name="electricity_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electricity_cost_reference_years: list = [],
        electricity_cost_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:
        """LCOE"""

        if len(electricity_cost_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "electricity_market_price"] = electricity_cost_reference_years_values
        else:
            electricity_cost_function = interp1d(
                electricity_cost_reference_years,
                electricity_cost_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "electricity_market_price"] = electricity_cost_function(k)

        electricity_market_price = self.df.loc[:, "electricity_market_price"]

        return electricity_market_price


class CoalCost(AeromapsModel):
    def __init__(self, name="coal_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        coal_cost_reference_years: list = [],
        coal_cost_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        coal_market_price = InterpolationAeromapsFunction(
            self, coal_cost_reference_years, coal_cost_reference_years_values
        )
        self.df.loc[:, "coal_market_price"] = coal_market_price

        return coal_market_price


class GasCost(AeromapsModel):
    def __init__(self, name="gas_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        gas_cost_reference_years: list = [],
        gas_cost_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        gas_market_price = InterpolationAeromapsFunction(
            self, gas_cost_reference_years, gas_cost_reference_years_values
        )
        self.df.loc[:, "gas_market_price"] = gas_market_price

        return gas_market_price


class Co2Cost(AeromapsModel):
    def __init__(self, name="co2_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        co2_cost_reference_years: list = [],
        co2_cost_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        if len(co2_cost_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "co2_market_price"] = co2_cost_reference_years_values
        else:
            co2_cost_function = interp1d(
                co2_cost_reference_years,
                co2_cost_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "co2_market_price"] = co2_cost_function(k)

        co2_market_price = self.df.loc[:, "co2_market_price"]

        return co2_market_price


class CarbonTax(AeromapsModel):
    def __init__(self, name="carbon_tax", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        carbon_tax_reference_years: list = [],
        carbon_tax_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "carbon_tax"] = 5.0

        if len(carbon_tax_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "carbon_tax"] = carbon_tax_reference_years_values
        else:
            carbon_tax_function = interp1d(
                carbon_tax_reference_years,
                carbon_tax_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "carbon_tax"] = carbon_tax_function(k)

        carbon_tax = self.df.loc[:, "carbon_tax"]

        return carbon_tax


class KerosenePrice(AeromapsModel):
    def __init__(self, name="kerosene_market_price", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        kerosene_price_reference_years: list = [],
        kerosene_price_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        if len(kerosene_price_reference_years) == 0:
            for k in range(self.historic_start_year, self.prospection_start_year):
                self.df.loc[k, "kerosene_market_price"] = kerosene_price_reference_years_values
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "kerosene_market_price"] = kerosene_price_reference_years_values
        else:
            kerosene_price_function = interp1d(
                kerosene_price_reference_years,
                kerosene_price_reference_years_values,
                kind="linear",
            )
            for k in range(self.historic_start_year, self.prospection_start_year):
                self.df.loc[k, "kerosene_market_price"] = kerosene_price_reference_years_values[0]
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "kerosene_market_price"] = kerosene_price_function(k)

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

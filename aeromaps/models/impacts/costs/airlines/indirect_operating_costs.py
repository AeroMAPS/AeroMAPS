# @Time : 04/01/2024 15:20
# @Author : a.salgas
# @File : indirect_operating_costs.py
# @Software: PyCharm

from typing import Tuple
import pandas as pd
from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class PassengerAircraftIndirectOpCosts(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_ioc", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        ioc_reference_years: list,
        ioc_reference_years_values: list,
    ) -> pd.Series:
        # Simple computation of airline indirect-operating costs (NOC)

        ioc_prospective = AeromapsInterpolationFunction(
            self,
            ioc_reference_years,
            ioc_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "indirect_operating_cost_per_ask"] = ioc_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "indirect_operating_cost_per_ask"] = self.df.loc[
                self.prospection_start_year, "indirect_operating_cost_per_ask"
            ]
        indirect_operating_cost_per_ask = self.df["indirect_operating_cost_per_ask"]
        return indirect_operating_cost_per_ask


class PassengerAircraftNocCarbonOffset(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_noc_carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        carbon_offset: pd.Series,
        ask: pd.Series,
        carbon_offset_price_reference_years: list,
        carbon_offset_price_reference_years_values: list,
    ) -> Tuple[pd.Series, pd.Series]:
        carbon_offset_price_prospective = AeromapsInterpolationFunction(
            self,
            carbon_offset_price_reference_years,
            carbon_offset_price_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "carbon_offset_price"] = carbon_offset_price_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "carbon_offset_price"] = 0.0
        carbon_offset_price = self.df["carbon_offset_price"]

        noc_carbon_offset_per_ask = carbon_offset * carbon_offset_price * 10**6 / ask

        self.df.loc[:, "noc_carbon_offset_per_ask"] = noc_carbon_offset_per_ask

        return (carbon_offset_price, noc_carbon_offset_per_ask)

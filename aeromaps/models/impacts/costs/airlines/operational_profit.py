# @Time : 04/01/2024 15:21
# @Author : a.salgas
# @File : operational_margin.py
# @Software: PyCharm
import pandas as pd
from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class PassengerAircraftOperationalProfit(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_operational_profit", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        operational_profit_reference_years: list,
        operational_profit_reference_years_values: list,
    ) -> pd.Series:
        # Simple computation of airline non-operating costs (NOC)

        operational_profit_prospective = AeromapsInterpolationFunction(
            self,
            operational_profit_reference_years,
            operational_profit_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "operational_profit_per_ask"] = operational_profit_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "operational_profit_per_ask"] = self.df.loc[
                self.prospection_start_year, "operational_profit_per_ask"
            ]
        operational_profit_per_ask = self.df["operational_profit_per_ask"]
        return operational_profit_per_ask

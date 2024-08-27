# @Time : 03/04/2024 14:38
# @Author : a.salgas
# @File : exogneous_carbon_price.py
# @Software: PyCharm


import pandas as pd
from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class ExogenousCarbonPriceTrajectory(AeroMAPSModel):
    def __init__(self, name="exogenous_carbon_price_trajectory", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        exogenous_carbon_price_reference_years: list,
        exogenous_carbon_price_reference_years_values: list,
    ) -> pd.Series:
        exogenous_carbon_price_trajectory = AeromapsInterpolationFunction(
            self,
            exogenous_carbon_price_reference_years,
            exogenous_carbon_price_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "exogenous_carbon_price_trajectory"] = exogenous_carbon_price_trajectory
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "exogenous_carbon_price_trajectory"] = self.df.loc[
                self.prospection_start_year, "exogenous_carbon_price_trajectory"
            ]
        exogenous_carbon_price_trajectory = self.df["exogenous_carbon_price_trajectory"]

        return exogenous_carbon_price_trajectory

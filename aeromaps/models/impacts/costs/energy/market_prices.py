# @Time : 27/02/2023 17:19
# @Author : a.salgas
# @File : market_prices.py
# @Software: PyCharm

import pandas as pd
from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class CarbonTax(AeroMAPSModel):
    def __init__(self, name="carbon_tax", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        carbon_tax_reference_years: list,
        carbon_tax_reference_years_values: list,
    ) -> pd.Series:
        carbon_tax_prospective = AeromapsInterpolationFunction(
            self,
            carbon_tax_reference_years,
            carbon_tax_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "carbon_tax"] = carbon_tax_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "carbon_tax"] = 5.0
        carbon_tax = self.df["carbon_tax"]

        return carbon_tax

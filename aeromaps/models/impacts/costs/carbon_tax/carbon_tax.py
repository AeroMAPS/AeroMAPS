# @Time : 27/02/2023 17:19
# @Author : a.salgas
# @File : market_prices.py
# @Software: PyCharm
"""
carbon_tax
============
Module to compute carbon tax evolution over the years.
"""

import pandas as pd
from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function


class CarbonTax(AeroMAPSModel):
    """
    Class to compute carbon tax evolution over the years.

    Parameters
    ----------
    name : str
        Name of the model instance ('carbon_tax' by default).

    """

    def __init__(self, name="carbon_tax", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        carbon_tax_reference_years: list,
        carbon_tax_reference_years_values: list,
    ) -> pd.Series:
        """
        Execute the computation of carbon tax.

        Parameters
        ----------
        carbon_tax_reference_years
            Scenario years corresponding to interpolation values specified in carbon_tax_reference_years_values.
        carbon_tax_reference_years_values
            User-defined interpolation values for carbon tax [€/tCO2].

        Returns
        -------
        carbon_tax
            Annual carbon tax [€/tCO2].

        """
        carbon_tax_prospective = aeromaps_interpolation_function(
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

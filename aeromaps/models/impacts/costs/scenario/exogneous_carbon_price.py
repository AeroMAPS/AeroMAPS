# @Time : 03/04/2024 14:38
# @Author : a.salgas
# @File : exogneous_carbon_price.py
# @Software: PyCharm
"""
exogenous_carbon_price
===============================
Module to compute exogenous carbon price trajectory.
"""

import pandas as pd
from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function


class ExogenousCarbonPriceTrajectory(AeroMAPSModel):
    """
    Class to compute exogenous carbon price trajectory.

    Parameters
    ----------
    name : str, optional
        Name of the model instance (default is "exogenous_carbon_price_trajectory").
    """

    def __init__(self, name="exogenous_carbon_price_trajectory", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        exogenous_carbon_price_reference_years: list,
        exogenous_carbon_price_reference_years_values: list,
    ) -> pd.Series:
        """
        Execute the computation of exogenous carbon price trajectory.

        Parameters
        ----------
        exogenous_carbon_price_reference_years
            List of years for which exogenous carbon price values are provided [years].
        exogenous_carbon_price_reference_years_values
            List of exogenous carbon price values corresponding to the reference years [€/tCO2].

        Returns
        -------
        exogenous_carbon_price_trajectory
            Exogenous carbon price trajectory [€/tCO2].

        """
        exogenous_carbon_price_trajectory = aeromaps_interpolation_function(
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

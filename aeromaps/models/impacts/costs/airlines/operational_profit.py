"""
operational_profit
===============

Simple module for computing airline operational profit per ASK and per RPK.

Warning
-------
This module is a simple implementation that uses user-defined values for airline operational profit, not a market instance.
"""

# @Time : 04/01/2024 15:21
# @Author : a.salgas
# @File : operational_margin.py
# @Software: PyCharm
import pandas as pd
from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function
from typing import Tuple


class PassengerAircraftOperationalProfit(AeroMAPSModel):
    """Compute airline operational profit per ASK and per RPK using user defined values.

    Parameters
    ----------
    name
        Model instance name ('passenger_aircraft_operational_profit' by default).
    """

    def __init__(self, name="passenger_aircraft_operational_profit", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        operational_profit_reference_years: list,
        operational_profit_reference_years_values: list,
        ask: pd.Series,
        rpk: pd.Series,
    ) -> Tuple[pd.Series, pd.Series]:
        """Execute computation of operational profit per ASK and per RPK by interpolation.

        Parameters
        ----------
        operational_profit_reference_years
            Reference years for airline operating profits [yr].
        operational_profit_reference_years_values
            Reference years values for airline operating profits [€/ASK].
        ask
            Available seat kilometers [ASK].
        rpk
            Revenue passenger kilometers [RPK].

        Returns
        -------
        operational_profit_per_ask
            Values for airlines operating profits per ASK [€/ASK].
        operational_profit_per_rpk
            Values for airlines operating profits per RPK [€/RPK].
        """
        # Simple computation of airline non-operating costs (NOC)

        operational_profit_prospective = aeromaps_interpolation_function(
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

        operational_profit_per_rpk = operational_profit_per_ask * ask / rpk
        return (operational_profit_per_ask, operational_profit_per_rpk)

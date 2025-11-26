"""
indirect_operating_costs
===============

Module to compute indirect operating cost (IOC) and offsets cost.
"""

# @Time : 04/01/2024 15:20
# @Author : a.salgas
# @File : indirect_operating_costs.py
# @Software: PyCharm

from typing import Tuple
import pandas as pd
from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function


class PassengerAircraftIndirectOpCosts(AeroMAPSModel):
    """Interpolate indirect operating cost (IOC) per ASK.

    Parameters
    ----------
    name
        Model instance name ('passenger_aircraft_ioc' by default).
    """

    def __init__(self, name="passenger_aircraft_ioc", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        ioc_reference_years: list,
        ioc_reference_years_values: list,
    ) -> pd.Series:
        """Compute indirect operating cost per ASK by interpolation.

        Parameters
        ----------
        ioc_reference_years
            Reference years for airline indirect-operating costs [yr].
        ioc_reference_years_values
            Reference years values for airline indirect-operating costs per ASK [€/ASK].

        Returns
        -------
        indirect_operating_cost_per_ask
            Values for airlines indirect-operating costs per ASK [€/ASK].
        """
        # Simple computation of airline indirect-operating costs (NOC)

        ioc_prospective = aeromaps_interpolation_function(
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
    """Compute carbon offset costs.

    Parameters
    ----------
    name
        Model instance name ('passenger_aircraft_noc_carbon_offset' by default).

    TODO: MOVE TO INDIRECT OPERATING COSTS MODULE
    """

    def __init__(self, name="passenger_aircraft_noc_carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        carbon_offset: pd.Series,
        ask: pd.Series,
        carbon_offset_price_reference_years: list,
        carbon_offset_price_reference_years_values: list,
    ) -> Tuple[pd.Series, pd.Series]:
        """Interpolates carbon offset cost and derives carbon offset cost per ASK.

        Parameters
        ----------
        carbon_offset
            Total annual carbon offset [MtCO₂].
        ask
            Total available seat kilometers [ASK].
        carbon_offset_price_reference_years
            Reference years for the share of remaining CO2 emissions offset [yr].
        carbon_offset_price_reference_years_values
            Share of remaining CO2 emissions offset for the reference years [€/tCO₂].

        Returns
        -------
        carbon_offset_price
            Share of remaining CO2 emissions offset [€/tCO₂].
        noc_carbon_offset_per_ask
            Non-operating cost per ASK due to carbon offset [€/ASK].
        """
        carbon_offset_price_prospective = aeromaps_interpolation_function(
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

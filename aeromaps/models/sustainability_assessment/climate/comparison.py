"""
comparison
==========
This module contains classes to compute the share of carbon budget and temperature target consumed by aviation.
"""
import pandas as pd
import warnings
from aeromaps.models.base import AeroMAPSModel


class CarbonBudgetConsumedShare(AeroMAPSModel):
    """
    This class computes the share of carbon budget consumed by aviation.

    Parameters
    ----------
    name : str
        Name of the model instance ('carbon_budget_consumed_share' by default).
    """
    def __init__(self, name="carbon_budget_consumed_share", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        cumulative_co2_emissions: pd.Series,
        gross_carbon_budget_2050: float,
    ) -> float:
        """
        Carbon budget consumption share calculation.

        Parameters
        ----------
        cumulative_co2_emissions : pd.Series
            Cumulative CO2 emissions from aviation over time [GtCO2].
        gross_carbon_budget_2050 : float
            Gross carbon budget allocated to aviation over 2020-2050 [GtCO2].

        Returns
        -------
        carbon_budget_consumed_share : float
            Share of carbon budget consumed by aviation up to 2050 (%).
        """

        year = 2050
        if self.end_year < 2050:
            warnings.warn("End year is before 2050, carbon budget consumed share may be underestimated.")
            year = self.end_year
        # TODO: handle case where prospection_start_year used in cumulative_co2_emissions differs from 2020.

        carbon_budget_consumed_share = (
            cumulative_co2_emissions.loc[year] / gross_carbon_budget_2050 * 100
        )

        self.float_outputs["carbon_budget_consumed_share"] = carbon_budget_consumed_share

        return carbon_budget_consumed_share


class TemperatureTargetConsumedShare(AeroMAPSModel):
    """
    This class computes the share of temperature target consumed by aviation.

    Parameters
    ----------
    name : str
        Name of the model instance ('temperature_target_consumed_share' by default).
    """
    def __init__(self, name="temperature_target_consumed_share", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        historical_temperature_increase: float,
        temperature_target: float,
        temperature_increase_from_aviation: pd.Series,
    ) -> float:
        """
        Temperature target consumption share calculation.

        Parameters
        ----------
        historical_temperature_increase : float
            Historical temperature increase before prospection_start_year (°C).
        temperature_target : float
            Global temperature target (°C) at end year of simulation.
        temperature_increase_from_aviation : pd.Series
            Temperature increase from aviation over time (°C).

        Returns
        -------
        temperature_target_consumed_share : float
            Share of temperature target consumed by aviation up to end year (%).
        """

        temperature_target_consumed_share = (
            (temperature_increase_from_aviation.loc[self.end_year] -
            temperature_increase_from_aviation.loc[self.prospection_start_year]) / (
                         temperature_target - historical_temperature_increase) * 100
             )

        self.float_outputs["temperature_target_consumed_share"] = temperature_target_consumed_share

        return temperature_target_consumed_share
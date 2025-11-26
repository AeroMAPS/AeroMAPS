"""
comparison

=============
Module to compute carbon budget consumed share and equivalent carbon budget consumed share.
"""

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class CarbonBudgetConsumedShare(AeroMAPSModel):
    """
    This class computes the consumed share of the carbon budget.

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
        cumulative_co2_emissions
            Cumulative CO2 emissions from all commercial air transport [GtCO2].
        gross_carbon_budget_2050
            World gross carbon budget until 2050 [GtCO2].

        Returns
        -------
        carbon_budget_consumed_share
            Share of carbon budget consumed by aviation over 2020-2050 [%].
        """

        carbon_budget_consumed_share = (
            cumulative_co2_emissions.loc[self.end_year] / gross_carbon_budget_2050 * 100
        )

        self.float_outputs["carbon_budget_consumed_share"] = carbon_budget_consumed_share

        return carbon_budget_consumed_share


class EquivalentCarbonBudgetConsumedShare(AeroMAPSModel):
    """
    This class computes the consumed share of the equivalent carbon budget.

    Parameters
    ----------
    name : str
        Name of the model instance ('equivalent_carbon_budget_consumed_share' by default).
    """

    def __init__(self, name="equivalent_carbon_budget_consumed_share", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        cumulative_total_equivalent_emissions: pd.Series,
        equivalent_gross_carbon_budget_2050: float,
    ) -> float:
        """
        Equivalent Carbon budget consumption share calculation.

        Parameters
        ----------
        cumulative_total_equivalent_emissions
            Cumulative equivalent emissions for all climate effects from all commercial air transport [GtCO2-we].
        equivalent_gross_carbon_budget_2050
            World equivalent gross carbon budget until 2050 [GtCO2-we].

        Returns
        -------
        equivalent_carbon_budget_consumed_share
            Share of equivalent carbon budget consumed by aviation over 2020-2050 [%].
        """

        equivalent_carbon_budget_consumed_share = (
            cumulative_total_equivalent_emissions.loc[self.end_year]
            / equivalent_gross_carbon_budget_2050
            * 100
        )

        self.float_outputs["equivalent_carbon_budget_consumed_share"] = (
            equivalent_carbon_budget_consumed_share
        )

        return equivalent_carbon_budget_consumed_share

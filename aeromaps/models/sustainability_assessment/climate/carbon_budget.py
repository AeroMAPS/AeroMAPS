"""
carbon_budgets
================
This module contains models to compute gross carbon budget related metrics.
"""

from typing import Tuple
from scipy.optimize import fsolve
from aeromaps.models.base import AeroMAPSModel


class GrossCarbonBudget(AeroMAPSModel):
    """
    This class computes gross carbon budget related metrics.

    Parameters
    ----------
    name : str
        Name of the model instance ('gross_carbon_budget' by default).
    """

    def __init__(self, name="gross_carbon_budget", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        net_carbon_budget: float,
        carbon_dioxyde_removal_2100: float,
        world_co2_emissions_carbon_budget_reference_year: float,
        aviation_carbon_budget_allocated_share: float,
        carbon_budget_reference_year: int,
    ) -> Tuple[float, float, float]:
        """
        Gross carbon budget.

        Parameters
        ----------
        net_carbon_budget
            Considered (net) carbon budget [GtCO2].
        carbon_dioxyde_removal_2100
            Cumulative Carbon Dioxide Removal (CDR) over reference_year-2100 [GtCO2].
        world_co2_emissions_carbon_budget_reference_year
            World CO2 emissions in the carbon budget reference year [GtCO2].
        aviation_carbon_budget_allocated_share
            Share of the carbon budget allocated to aviation over reference_year-2050 [%].
        carbon_budget_reference_year
            Fixed reference year the budget is measured from (default 2019). The
            geometric decline is summed from this year to the 2100 / 2050 horizons.
        """

        gross_carbon_budget = net_carbon_budget + carbon_dioxyde_removal_2100

        # Geometric-sum exponents: years from the reference year to each horizon.
        # ref=2019 -> 82 (to 2100) and 32 (to 2050), matching the previous hardcodes.
        n_years_to_2100 = 2100 - carbon_budget_reference_year + 1
        n_years_to_2050 = 2050 - carbon_budget_reference_year + 1

        data = [
            gross_carbon_budget,
            world_co2_emissions_carbon_budget_reference_year,
            n_years_to_2100,
        ]

        average_co2_emissions_decline_rate = float(
            fsolve(self._compute_average_co2_emissions_decline_rate, -0.02, args=data)
        )
        gross_carbon_budget_2050 = (
            world_co2_emissions_carbon_budget_reference_year
            * (
                (1 - average_co2_emissions_decline_rate)
                - (1 - average_co2_emissions_decline_rate) ** n_years_to_2050
            )
            / average_co2_emissions_decline_rate
        )

        aviation_carbon_budget = (
            aviation_carbon_budget_allocated_share / 100 * gross_carbon_budget_2050
        )

        self.float_outputs["gross_carbon_budget"] = gross_carbon_budget
        self.float_outputs["gross_carbon_budget_2050"] = gross_carbon_budget_2050
        self.float_outputs["aviation_carbon_budget"] = aviation_carbon_budget

        return gross_carbon_budget, gross_carbon_budget_2050, aviation_carbon_budget

    @staticmethod
    def _compute_average_co2_emissions_decline_rate(x, data):
        """
        Equation to solve to find the average CO2 emissions decline rate (to adjust gross carbon budget to a given year)
        """
        gross_carbon_budget, world_co2_emissions_carbon_budget_reference_year, n_years_to_2100 = (
            data
        )
        return (
            (1 - x) - (1 - x) ** n_years_to_2100
        ) / x - gross_carbon_budget / world_co2_emissions_carbon_budget_reference_year

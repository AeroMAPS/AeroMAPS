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
        world_co2_emissions_2019: float,
        aviation_carbon_budget_allocated_share: float,
    ) -> Tuple[float, float, float]:
        """
        Gross carbon budget.

        Parameters
        ----------
        net_carbon_budget
            Considered (net) carbon budget [GtCO2].
        carbon_dioxyde_removal_2100
            Cumulative Carbon Dioxide Removal (CDR) over 2020-2100 [GtCO2].
        world_co2_emissions_2019
            World CO2 emissions in 2019 [GtCO2].
        aviation_carbon_budget_allocated_share
            Share of the carbon budget allocated to aviation over 2020-2050 [%].
        """

        gross_carbon_budget = net_carbon_budget + carbon_dioxyde_removal_2100

        data = [gross_carbon_budget, world_co2_emissions_2019]

        average_co2_emissions_decline_rate = float(
            fsolve(self._compute_average_co2_emissions_decline_rate, -0.02, args=data)
        )
        gross_carbon_budget_2050 = (
            world_co2_emissions_2019
            * (
                (1 - average_co2_emissions_decline_rate)
                - (1 - average_co2_emissions_decline_rate) ** 32
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
        gross_carbon_budget, world_co2_emissions_2019 = data
        return ((1 - x) - (1 - x) ** 82) / x - gross_carbon_budget / world_co2_emissions_2019

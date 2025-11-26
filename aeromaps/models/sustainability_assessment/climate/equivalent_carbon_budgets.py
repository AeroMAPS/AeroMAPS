"""
equivalent_carbon_budgets

===========================
Module to compute equivalent gross carbon budget and aviation equivalent carbon budget.
"""

from typing import Tuple
from scipy.optimize import fsolve


from aeromaps.models.base import AeroMAPSModel


class EquivalentGrossCarbonBudget(AeroMAPSModel):
    """
    This class computes equivalent gross carbon budget and aviation equivalent carbon budget.

    Parameters
    ----------
    name : str
        Name of the model instance ('equivalent_gross_carbon_budget' by default).
    """

    def __init__(self, name="equivalent_gross_carbon_budget", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        gross_carbon_budget: float,
        T_nonCO2: float,
        tcre_coefficient: float,
        world_ghg_emissions_2019: float,
        aviation_equivalentcarbonbudget_allocated_share: float,
    ) -> Tuple[float, float, float]:
        """
        Gross equivalent carbon budget.

        Parameters
        ----------
        gross_carbon_budget
            World gross carbon budget [GtCO2].
        T_nonCO2
            Characteristic temperature for integrating non-CO2 effects into gross carbon budget calculation [°C].
        tcre_coefficient
            Transient Climate Response to cumulative Emissions of carbon dioxide coefficient [°C/GtCO2].
        world_ghg_emissions_2019
            World GHG emissions in 2019 [GtCO2e].
        aviation_equivalentcarbonbudget_allocated_share
            Share of the equivalent carbon budget allocated to aviation over 2020-2050 [%].

        Returns
        -------
        equivalent_gross_carbon_budget
            World equivalent gross carbon budget [GtCO2e].
        equivalent_gross_carbon_budget_2050
            World equivalent gross carbon budget until 2050 [GtCO2e].
        aviation_equivalent_carbon_budget
            Allocated equivalent carbon budget for aviation over 2020-2050 [GtCO2e].
        """

        equivalent_gross_carbon_budget = gross_carbon_budget + T_nonCO2 / tcre_coefficient

        data = [equivalent_gross_carbon_budget, world_ghg_emissions_2019]

        average_ghg_emissions_decline_rate = float(
            fsolve(self._compute_average_ghg_emissions_decline_rate, -0.02, args=data)
        )
        equivalent_gross_carbon_budget_2050 = (
            world_ghg_emissions_2019
            * (
                (1 - average_ghg_emissions_decline_rate)
                - (1 - average_ghg_emissions_decline_rate) ** 32
            )
            / average_ghg_emissions_decline_rate
        )

        aviation_equivalent_carbon_budget = (
            aviation_equivalentcarbonbudget_allocated_share
            / 100
            * equivalent_gross_carbon_budget_2050
        )

        self.float_outputs["equivalent_gross_carbon_budget"] = equivalent_gross_carbon_budget
        self.float_outputs["equivalent_gross_carbon_budget_2050"] = (
            equivalent_gross_carbon_budget_2050
        )
        self.float_outputs["aviation_equivalent_carbon_budget"] = aviation_equivalent_carbon_budget

        return (
            equivalent_gross_carbon_budget,
            equivalent_gross_carbon_budget_2050,
            aviation_equivalent_carbon_budget,
        )

    @staticmethod
    def _compute_average_ghg_emissions_decline_rate(x, data):
        equivalent_gross_carbon_budget, world_ghg_emissions_2019 = data
        return (
            (1 - x) - (1 - x) ** 82
        ) / x - equivalent_gross_carbon_budget / world_ghg_emissions_2019

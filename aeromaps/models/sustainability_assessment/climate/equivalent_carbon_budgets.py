from typing import Tuple
from scipy.optimize import fsolve


from aeromaps.models.base import AeromapsModel


class EquivalentGrossCarbonBudget(AeromapsModel):
    def __init__(self, name="equivalent_gross_carbon_budget", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        gross_carbon_budget: float = 0.0,
        T_nonCO2: float = 0.0,
        TCRE: float = 0.0,
        world_ghg_emissions_2019: float = 0.0,
        aviation_equivalentcarbonbudget_allocated_share: float = 0.0,
    ) -> Tuple[float, float, float]:
        """Gross equivalent carbon budget."""

        equivalent_gross_carbon_budget = gross_carbon_budget + T_nonCO2 / TCRE

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
        self.float_outputs[
            "equivalent_gross_carbon_budget_2050"
        ] = equivalent_gross_carbon_budget_2050
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

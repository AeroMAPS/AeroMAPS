from typing import Tuple
from scipy.optimize import fsolve

from aeromaps.models.base import AeromapsModel


class GrossCarbonBudget(AeromapsModel):
    def __init__(self, name="gross_carbon_budget", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        net_carbon_budget: float = 0.0,
        carbon_dioxyde_removal_2100: float = 0.0,
        world_co2_emissions_2019: float = 0.0,
        aviation_carbon_budget_allocated_share: float = 0.0,
    ) -> Tuple[float, float, float]:
        """Gross carbon budget."""

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
        gross_carbon_budget, world_co2_emissions_2019 = data
        return ((1 - x) - (1 - x) ** 82) / x - gross_carbon_budget / world_co2_emissions_2019

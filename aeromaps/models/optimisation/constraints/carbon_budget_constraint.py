# @Time : 03/10/2024 14:06
# @Author : a.salgas
# @File : carbon_budget_constraint.py
# @Software: PyCharm
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class CarbonBudgetConstraint(AeroMAPSModel):
    def __init__(self, name="carbon_budget_constraint", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        gross_carbon_budget_2050: float,
        aviation_carbon_budget_objective: float,
        cumulative_co2_emissions: pd.Series,
    ) -> float:
        """Carbon budget consumption share calculation."""
        cumulative_emissions = (
            cumulative_co2_emissions.loc[2050] - cumulative_co2_emissions.loc[2025]
        )
        adjusted_carbon_budget_2050 = (
            gross_carbon_budget_2050 * aviation_carbon_budget_objective / 100
            - cumulative_co2_emissions.loc[2025]
        )

        aviation_carbon_budget_constraint = (
            +(cumulative_emissions - adjusted_carbon_budget_2050) / adjusted_carbon_budget_2050
        )

        self.float_outputs["aviation_carbon_budget_constraint"] = aviation_carbon_budget_constraint

        return aviation_carbon_budget_constraint

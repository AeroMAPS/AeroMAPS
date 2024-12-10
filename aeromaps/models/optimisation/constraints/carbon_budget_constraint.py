# @Time : 03/10/2024 14:06
# @Author : a.salgas
# @File : carbon_budget_constraint.py
# @Software: PyCharm
from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class CarbonBudgetConstraint(AeroMAPSModel):
    def __init__(self, name="carbon_budget_constraint", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        # carbon_budget_consumed_share: float,
        cumulative_co2_emissions: pd.Series,
        gross_carbon_budget_2050: float,
        aviation_carbon_budget_objective: float,
    ) -> float:
        """Carbon budget consumption share calculation."""

        carbon_budget_consumed_share_2050 = (
                cumulative_co2_emissions.loc[2050] / gross_carbon_budget_2050 * 100
        )

        aviation_carbon_budget_constraint = (
            +(carbon_budget_consumed_share_2050 - aviation_carbon_budget_objective)
            / aviation_carbon_budget_objective
        )

        self.float_outputs["aviation_carbon_budget_constraint"] = aviation_carbon_budget_constraint

        return aviation_carbon_budget_constraint

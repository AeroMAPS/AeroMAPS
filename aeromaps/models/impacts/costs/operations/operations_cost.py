# @Time : 06/02/2024 15:07
# @Author : a.salgas
# @File : operations_cost.py
# @Software: PyCharm
from typing import Tuple

import pandas as pd
from aeromaps.models.base import AeromapsModel, AeromapsInterpolationFunction


class OperationalEfficiencyCost(AeromapsModel):
    def __init__(self, name="operational_efficiency_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            operational_efficiency_cost_per_ask_reference_years: list = [],
            operational_efficiency_cost_per_ask_values: list = [],
    ) -> Tuple[pd.Series]:
        operational_efficiency_cost_per_ask = AeromapsInterpolationFunction(
            self, operational_efficiency_cost_per_ask_reference_years, operational_efficiency_cost_per_ask_values,
            model_name=self.name
        )
        self.df.loc[:, "operational_efficiency_cost_per_ask"] = operational_efficiency_cost_per_ask

        return operational_efficiency_cost_per_ask

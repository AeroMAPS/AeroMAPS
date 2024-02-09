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
        operational_efficiency_cost_non_energy_per_ask_reference_years: list = [],
        operational_efficiency_cost_non_energy_per_ask_values: list = [],
    ) -> Tuple[pd.Series]:
        operational_efficiency_cost_non_energy_per_ask = AeromapsInterpolationFunction(
            self,
            operational_efficiency_cost_non_energy_per_ask_reference_years,
            operational_efficiency_cost_non_energy_per_ask_values,
            model_name=self.name,
        )
        self.df.loc[:, "operational_efficiency_cost_non_energy_per_ask"] = operational_efficiency_cost_non_energy_per_ask

        return operational_efficiency_cost_non_energy_per_ask
    
    
class LoadFactorEfficiencyCost(AeromapsModel):
    def __init__(self, name="load_factor_efficiency_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        load_factor_cost_non_energy_per_ask_reference_years: list = [],
        load_factor_cost_non_energy_per_ask_values: list = [],
    ) -> Tuple[pd.Series]:
        load_factor_cost_non_energy_per_ask = AeromapsInterpolationFunction(
            self,
            load_factor_cost_non_energy_per_ask_reference_years,
            load_factor_cost_non_energy_per_ask_values,
            model_name=self.name,
        )
        self.df.loc[:, "load_factor_cost_non_energy_per_ask"] = load_factor_cost_non_energy_per_ask

        return load_factor_cost_non_energy_per_ask

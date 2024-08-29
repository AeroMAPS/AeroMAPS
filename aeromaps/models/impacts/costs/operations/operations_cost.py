# @Time : 06/02/2024 15:07
# @Author : a.salgas
# @File : operations_cost.py
# @Software: PyCharm

import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class OperationalEfficiencyCost(AeroMAPSModel):
    def __init__(self, name="operational_efficiency_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        operational_efficiency_cost_non_energy_per_ask_final_value: float,
        operations_final_gain: float,
        operations_gain: pd.Series,
    ) -> pd.Series:
        operational_efficiency_cost_non_energy_per_ask = (
            operational_efficiency_cost_non_energy_per_ask_final_value
            * operations_gain
            / operations_final_gain
        )
        self.df.loc[:, "operational_efficiency_cost_non_energy_per_ask"] = (
            operational_efficiency_cost_non_energy_per_ask
        )

        return operational_efficiency_cost_non_energy_per_ask


class LoadFactorEfficiencyCost(AeroMAPSModel):
    def __init__(self, name="load_factor_efficiency_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        load_factor_cost_non_energy_per_ask_final_value: float,
        load_factor_end_year: float,
        load_factor: pd.Series,
    ) -> pd.Series:
        load_factor_init = load_factor[self.prospection_start_year - 1]
        load_factor_cost_non_energy_per_ask = (
            load_factor_cost_non_energy_per_ask_final_value
            * (load_factor - load_factor_init)
            / (load_factor_end_year - load_factor_init)
        )
        self.df.loc[:, "load_factor_cost_non_energy_per_ask"] = load_factor_cost_non_energy_per_ask

        return load_factor_cost_non_energy_per_ask

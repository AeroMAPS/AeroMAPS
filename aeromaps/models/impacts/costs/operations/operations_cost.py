# @Time : 06/02/2024 15:07
# @Author : a.salgas
# @File : operations_cost.py
# @Software: PyCharm
"""
operations_costs
===============================
Module to compute aircraft operations costs.
"""

import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class OperationalEfficiencyCost(AeroMAPSModel):
    """
    Class to compute operational efficiency costs.

    Parameters
    --------------
    name : str
        Name of the model instance ('operational_efficiency_cost' by default).
    """

    def __init__(self, name="operational_efficiency_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        operational_efficiency_cost_non_energy_per_ask_final_value: float,
        operations_final_gain: float,
        operations_gain: pd.Series,
    ) -> pd.Series:
        """
        Execute the computation of operational efficiency costs.

        Parameters
        ----------
        operational_efficiency_cost_non_energy_per_ask_final_value
            Extra cost related to implementation of operational efficiency measures [€/ASK].
        operations_final_gain
            Final impact of operational improvements in terms of percentage reduction in fuel consumption per ASK [%].
        operations_gain
            Impact of operational improvements in terms of percentage reduction in fuel consumption per ASK [%].

        Returns
        -------
        operational_efficiency_cost_non_energy_per_ask
            Operational efficiency cost non-energy per ASK [€/ASK].
        """
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
    """
    Class to compute load factor efficiency costs.

    Parameters
    --------------
    name : str
        Name of the model instance ('load_factor_efficiency_cost' by default).
    """

    def __init__(self, name="load_factor_efficiency_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        load_factor_cost_non_energy_per_ask_final_value: float,
        load_factor_end_year: float,
        load_factor: pd.Series,
    ) -> pd.Series:
        """
        Execute the computation of load factor efficiency costs.

        Parameters
        ----------
        load_factor_cost_non_energy_per_ask_final_value
            Extra cost related to implementation of load factor efficiency measures [€/ASK].
        load_factor_end_year
            Load factor at the end of the prospection period [%].
        load_factor
            Mean aircraft load factor [%].

        Returns
        -------
        load_factor_cost_non_energy_per_ask
            Load factor efficiency cost non-energy per ASK [€/ASK].
        """
        load_factor_init = load_factor[self.prospection_start_year - 1]
        load_factor_cost_non_energy_per_ask = (
            load_factor_cost_non_energy_per_ask_final_value
            * (load_factor - load_factor_init)
            / (load_factor_end_year - load_factor_init)
        )
        self.df.loc[:, "load_factor_cost_non_energy_per_ask"] = load_factor_cost_non_energy_per_ask

        return load_factor_cost_non_energy_per_ask

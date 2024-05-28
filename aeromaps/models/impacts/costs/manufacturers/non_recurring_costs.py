# @Time : 05/02/2024 16:45
# @Author : a.salgas
# @File : non_recurring_costs.py
# @Software: PyCharm
import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from typing import Tuple


class NonRecurringCosts(AeroMAPSModel):
    def __init__(self, name="non_recurring_costs", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = fleet_model

    def compute(
        self,
        aircraft_in_out_value_dict: dict,
    ) -> Tuple[dict,]:
        nrc_aircraft_value_dict = {}
        for category, sets in self.fleet_model.fleet.all_aircraft_elements.items():

            # Calculating values of interest for each aircraft
            for aircraft_var in sets:
                # Check if it's a reference aircraft or a normal aircraft...
                if hasattr(aircraft_var, "parameters"):
                    aircraft_var_name = aircraft_var.parameters.full_name
                    nrc_cost = aircraft_var.parameters.nrc_cost
                    eis = int(aircraft_var.parameters.entry_into_service_year)
                else:
                    aircraft_var_name = aircraft_var.full_name
                    nrc_cost = aircraft_var.nrc_cost
                    eis = int(aircraft_var.entry_into_service_year)

                nrc_aircraft_var_name = aircraft_var_name + ":aircraft_non_recurring_costs"

                # TODO use dictionnary if possible once implementeed
                # nrc_aircraft_value = max(0.0, aircraft_in_out_value_dict[aircraft_var_name] * nrc_cost)
                # For now: direct use of fleet model df

                nrc_aircraft_value = self._compute_nrc(float(nrc_cost), 5, eis)

                self.fleet_model.df = pd.concat(
                    [
                        self.fleet_model.df,
                        nrc_aircraft_value.rename(nrc_aircraft_var_name),
                    ],
                    axis=1,
                )

                nrc_aircraft_value_dict[aircraft_var_name] = nrc_aircraft_value

        return (nrc_aircraft_value_dict,)

    def _compute_nrc(
        self,
        nrc_tot_aircraft_type,
        development_time_aircraft_type,
        entry_into_service_year,
    ):
        costs = []
        years = []
        sigma = development_time_aircraft_type / 6.0  # Controls the spread of the distribution

        for i in range(1, development_time_aircraft_type + 1):
            year = entry_into_service_year - development_time_aircraft_type + i
            weight = np.exp(-0.5 * ((i - development_time_aircraft_type / 2) / sigma) ** 2)
            cost = round(nrc_tot_aircraft_type * weight)
            costs.append(cost)
            years.append(year)

        # Adjust the distributed costs to ensure their sum matches the total cost
        total_distributed_cost = sum(costs)
        scaling_factor = nrc_tot_aircraft_type / total_distributed_cost
        costs = [round(cost * scaling_factor) for cost in costs]
        nrc_distributed = pd.Series(costs, index=years)

        # Keep only teh indexes that are within the scope of scenario range to
        # avoid adding out of range nrc (for old aircraft for instance)
        filtered_nrc_distributed = nrc_distributed[
            (nrc_distributed.index >= self.historic_start_year)
            & (nrc_distributed.index <= self.end_year)
        ]

        return filtered_nrc_distributed

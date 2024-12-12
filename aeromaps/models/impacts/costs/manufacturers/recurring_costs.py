# @Time : 02/02/2024 16:45
# @Author : a.salgas
# @File : recurring_costs.py
# @Software: PyCharm
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class RecurringCosts(AeroMAPSModel):
    def __init__(self, name="recurring_costs", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = fleet_model

    def compute(
        self,
        aircraft_in_out_value_dict: dict,
    ) -> dict:
        rc_aircraft_value_dict = {}
        for category, sets in self.fleet_model.fleet.all_aircraft_elements.items():
            # Calculating values of interest for each aircraft
            for aircraft_var in sets:
                # Check if it's a reference aircraft or a normal aircraft...
                if hasattr(aircraft_var, "parameters"):
                    aircraft_var_name = aircraft_var.parameters.full_name
                    rc_cost = aircraft_var.parameters.rc_cost
                else:
                    aircraft_var_name = aircraft_var.full_name
                    rc_cost = aircraft_var.rc_cost

                rc_aircraft_var_name = aircraft_var_name + ":aircraft_recurring_costs"

                # TODO use dictionary if possible once implemented
                # rc_aircraft_value = max(0.0, aircraft_in_out_value_dict[aircraft_var_name] * rc_cost)
                # For now: direct use of fleet model df
                rc_aircraft_value = self.fleet_model.df.loc[
                    :, (aircraft_var_name + ":aircraft_in_out")
                ] * float(rc_cost)
                rc_aircraft_value[rc_aircraft_value < 0] = 0

                self.fleet_model.df = pd.concat(
                    [
                        self.fleet_model.df,
                        rc_aircraft_value.rename(rc_aircraft_var_name),
                    ],
                    axis=1,
                )

                rc_aircraft_value_dict[aircraft_var_name] = rc_aircraft_value
        return rc_aircraft_value_dict

# @Time : 25/01/2024 16:45
# @Author : a.salgas
# @File : aircrfat_numbe.py
# @Software: PyCharm
from aeromaps.models.base import AeromapsModel
from typing import Tuple
import pandas as pd
import numpy as np

class FleetEvolution(AeromapsModel):
    def __init__(
        self, name="fleet_evolution", fleet_model=None, *args, **kwargs
    ):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = fleet_model

    def compute(
            self,
            ask_short_range: pd.Series = pd.Series(dtype="float64"),
            ask_medium_range: pd.Series = pd.Series(dtype="float64"),
            ask_long_range: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series]:

        for i, category in enumerate(self.fleet_model.fleet.categories.values()):

            if category.name == 'Short Range':
                category_ask = ask_short_range
            elif category.name == 'Medium Range':
                category_ask = ask_medium_range
            else:
                category_ask = ask_long_range


            subcategory = category.subcategories[0]
            # Old reference aircraft
            var_name_old = (
                    category.name + ":" + subcategory.name + ":" + "old_reference:aircraft_share"
            )
            ask_aircraft_var_name_old = (
                    category.name + ":" + subcategory.name + ":" + "old_reference:aircraft_ask"
            )
            aircraft_in_fleet_var_name_old = (
                    category.name + ":" + subcategory.name + ":" + "old_reference:aircraft_in_fleet"
            )

            aircraft_in_out_var_name_old = (
                    category.name + ":" + subcategory.name + ":" + "old_reference:aircraft_in_out"
            )

            ask_year_old =  subcategory.old_reference_aircraft.ask_year
            ask_aircraft_value_old = self.fleet_model.df.loc[2020:  2050, var_name_old]/100 * category_ask

            self.fleet_model.df.loc[
            :, ask_aircraft_var_name_old
            ] = ask_aircraft_value_old

            aircraft_in_fleet_value_old = np.ceil(ask_aircraft_value_old/ask_year_old)
            aircraft_in_out_value_old = aircraft_in_fleet_value_old.diff()

            self.fleet_model.df.loc[
            :, aircraft_in_fleet_var_name_old
            ] = aircraft_in_fleet_value_old

            self.fleet_model.df.loc[
            :, aircraft_in_out_var_name_old
            ] = aircraft_in_out_value_old


            # Recent reference aircraft
            var_name_recent = (
                    category.name + ":" + subcategory.name + ":" + "recent_reference:aircraft_share"
            )
            ask_aircraft_var_name_recent = (
                    category.name + ":" + subcategory.name + ":" + "recent_reference:aircraft_ask"
            )
            aircraft_in_fleet_var_name_recent = (
                    category.name + ":" + subcategory.name + ":" + "recent_reference:aircraft_in_fleet"
            )

            aircraft_in_out_var_name_recent = (
                    category.name + ":" + subcategory.name + ":" + "recent_reference:aircraft_in_out"
            )

            ask_year_recent = subcategory.recent_reference_aircraft.ask_year
            ask_aircraft_value_recent = self.fleet_model.df.loc[2020:  2050, var_name_recent] / 100 * category_ask

            self.fleet_model.df.loc[
            :, ask_aircraft_var_name_recent
            ] = ask_aircraft_value_recent

            aircraft_in_fleet_value_recent = np.ceil(ask_aircraft_value_recent / ask_year_recent)
            aircraft_in_out_value_recent = aircraft_in_fleet_value_recent.diff()

            self.fleet_model.df.loc[
            :, aircraft_in_fleet_var_name_recent
            ] = aircraft_in_fleet_value_recent

            self.fleet_model.df.loc[
            :, aircraft_in_out_var_name_recent
            ] = aircraft_in_out_value_recent


            for j, subcategory in category.subcategories.items():

                # New aircraft
                for aircraft in subcategory.aircraft.values():
                    var_name = (
                            category.name
                            + ":"
                            + subcategory.name
                            + ":"
                            + aircraft.name
                            + ":aircraft_share"
                    )
                    ask_aircraft_var_name = (
                            category.name
                            + ":"
                            + subcategory.name
                            + ":"
                            + aircraft.name
                            + ":aircraft_ask"
                    )

                    aircraft_in_fleet_var_name = (
                            category.name
                            + ":"
                            + subcategory.name
                            + ":"
                            + aircraft.name
                            + ":aircraft_in_fleet"
                    )

                    aircraft_in_out_var_name = (
                            category.name
                            + ":"
                            + subcategory.name
                            + ":"
                            + aircraft.name
                            + ":aircraft_in_out"
                    )

                    ask_year = aircraft.parameters.ask_year
                    ask_aircraft_value = self.fleet_model.df.loc[2020:  2050, var_name]/100 * category_ask
                    aircraft_in_fleet_value = np.ceil(ask_aircraft_value/float(ask_year))
                    aircraft_in_out_value = aircraft_in_fleet_value.diff()

                    self.fleet_model.df.loc[
                        :, ask_aircraft_var_name
                    ] = ask_aircraft_value

                    self.fleet_model.df.loc[
                    :, aircraft_in_fleet_var_name
                    ] = aircraft_in_fleet_value

                    self.fleet_model.df.loc[
                    :, aircraft_in_out_var_name
                    ] = aircraft_in_out_value


        #TODO handle the return => like "normal" variables, but with a variable number of them depending on fleet model output
        return ask_aircraft_value


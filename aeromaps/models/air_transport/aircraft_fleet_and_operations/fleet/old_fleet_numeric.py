# @Time : 25/01/2024 16:45
# @Author : a.salgas
# @File : aircrfat_numbe.py
# @Software: PyCharm
from aeromaps.models.base import AeromapsModel
from typing import Tuple
import pandas as pd
import numpy as np


class FleetEvolution(AeromapsModel):
    def __init__(self, name="fleet_numeric", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = fleet_model

    def compute(
        self,
        ask_short_range: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range: pd.Series = pd.Series(dtype="float64"),
        ask_long_range: pd.Series = pd.Series(dtype="float64"),
        covid_start_year: int = 0,
        covid_end_year: int = 0,
    ) -> Tuple[pd.Series]:

        for i, category in enumerate(self.fleet_model.fleet.categories.values()):

            if category.name == "Short Range":
                category_ask = ask_short_range
            elif category.name == "Medium Range":
                category_ask = ask_medium_range
            else:
                category_ask = ask_long_range

            # Caculation of virtual fleet demand assuming that manufacturers/airlines adapt their production to be ready for traffic catchup after covid.
            category_ask_covid_levelling = category_ask.copy()
            category_ask_pre_covid = category_ask.loc[covid_start_year - 1]
            category_ask_post_covid = category_ask.loc[covid_end_year]

            for year in range(covid_start_year, covid_end_year + 1):
                category_ask_covid_levelling.loc[year] = (
                    (category_ask_pre_covid - category_ask_post_covid) / (covid_start_year - 1)
                    - (covid_end_year)
                ) * (year - covid_start_year - 1) + category_ask_pre_covid

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

            aircraft_in_fleet_covid_levelling_var_name_old = (
                category.name
                + ":"
                + subcategory.name
                + ":"
                + "old_reference:aircraft_in_fleet_covid_levelling"
            )

            aircraft_in_out_var_name_old = (
                category.name + ":" + subcategory.name + ":" + "old_reference:aircraft_in_out"
            )

            ask_year_old = subcategory.old_reference_aircraft.ask_year
            ask_aircraft_value_old = (
                self.fleet_model.df.loc[2019:2050, var_name_old] / 100 * category_ask
            )
            ask_aircraft_value_old_covid_levelling = (
                self.fleet_model.df.loc[2019:2050, var_name_old]
                / 100
                * category_ask_covid_levelling
            )

            self.fleet_model.df.loc[:, ask_aircraft_var_name_old] = ask_aircraft_value_old

            aircraft_in_fleet_value_old = np.ceil(ask_aircraft_value_old / ask_year_old)
            aircraft_in_fleet_value_old_covid_levelling = np.ceil(
                ask_aircraft_value_old_covid_levelling / ask_year_old
            )
            aircraft_in_out_value_old = aircraft_in_fleet_value_old_covid_levelling.diff()

            self.fleet_model.df.loc[:, aircraft_in_fleet_var_name_old] = aircraft_in_fleet_value_old

            self.fleet_model.df.loc[
                :, aircraft_in_fleet_covid_levelling_var_name_old
            ] = aircraft_in_fleet_value_old_covid_levelling

            self.fleet_model.df.loc[:, aircraft_in_out_var_name_old] = aircraft_in_out_value_old

            # Recent reference aircraft
            aircraft_var = category.name + ":" + subcategory.name + ":" + "recent_reference"

            var_name_recent = (
                category.name + ":" + subcategory.name + ":" + "recent_reference:aircraft_share"
            )
            ask_aircraft_var_name_recent = (
                category.name + ":" + subcategory.name + ":" + "recent_reference:aircraft_ask"
            )

            aircraft_in_fleet_var_name_recent = (
                category.name + ":" + subcategory.name + ":" + "recent_reference:aircraft_in_fleet"
            )

            aircraft_in_fleet_covid_levelling_var_name_recent = (
                category.name
                + ":"
                + subcategory.name
                + ":"
                + "recent_reference:aircraft_in_fleet_covid_levelling"
            )

            aircraft_in_out_var_name_recent = (
                category.name + ":" + subcategory.name + ":" + "recent_reference:aircraft_in_out"
            )

            ask_year_recent = subcategory.recent_reference_aircraft.ask_year

            ask_aircraft_value_recent = (
                self.fleet_model.df.loc[2019:2050, var_name_recent] / 100 * category_ask
            )
            ask_aircraft_value_recent_covid_levelling = (
                self.fleet_model.df.loc[2019:2050, var_name_recent]
                / 100
                * category_ask_covid_levelling
            )

            self.fleet_model.df.loc[:, ask_aircraft_var_name_recent] = ask_aircraft_value_recent

            aircraft_in_fleet_value_recent = np.ceil(ask_aircraft_value_recent / ask_year_recent)
            aircraft_in_fleet_value_recent_covid_levelling = np.ceil(
                ask_aircraft_value_recent_covid_levelling / ask_year_recent
            )
            aircraft_in_out_value_recent = aircraft_in_fleet_value_recent_covid_levelling.diff()

            self.fleet_model.df.loc[
                :, aircraft_in_fleet_var_name_recent
            ] = aircraft_in_fleet_value_recent

            self.fleet_model.df.loc[
                :, aircraft_in_fleet_covid_levelling_var_name_recent
            ] = aircraft_in_fleet_value_recent_covid_levelling

            self.fleet_model.df.loc[
                :, aircraft_in_out_var_name_recent
            ] = aircraft_in_out_value_recent

            for j, subcategory in category.subcategories.items():

                # New aircraft
                for aircraft in subcategory.aircraft.values():
                    aicraft_var = category.name + ":" + subcategory.name + ":" + aircraft.name

                    share_var_name = aicraft_var + ":aircraft_share"
                    ask_aircraft_var_name = aicraft_var + ":aircraft_ask"

                    aircraft_in_fleet_var_name = aicraft_var + ":aircraft_in_fleet"

                    aircraft_in_fleet_covid_levelling_var_name = (
                        aicraft_var + ":aircraft_in_fleet_covid_levelling"
                    )

                    aircraft_in_out_var_name = aicraft_var + ":aircraft_in_out"

                    ask_year = aircraft.parameters.ask_year
                    ask_aircraft_value = (
                        self.fleet_model.df.loc[2019:2050, share_var_name] / 100 * category_ask
                    )
                    ask_aircraft_value_covid_levelling = (
                        self.fleet_model.df.loc[2019:2050, share_var_name]
                        / 100
                        * category_ask_covid_levelling
                    )

                    aircraft_in_fleet_value = np.ceil(ask_aircraft_value / float(ask_year))
                    aircraft_in_fleet_value_covid_levelling = np.ceil(
                        ask_aircraft_value_covid_levelling / float(ask_year)
                    )
                    aircraft_in_out_value = aircraft_in_fleet_value_covid_levelling.diff()

                    self.fleet_model.df.loc[:, ask_aircraft_var_name] = ask_aircraft_value

                    self.fleet_model.df.loc[:, aircraft_in_fleet_var_name] = aircraft_in_fleet_value

                    self.fleet_model.df.loc[
                        :, aircraft_in_fleet_covid_levelling_var_name
                    ] = aircraft_in_fleet_value_covid_levelling

                    self.fleet_model.df.loc[:, aircraft_in_out_var_name] = aircraft_in_out_value

        fleet_evolution_return = True
        # TODO handle the return => like "normal" variables, but with a variable number of them depending on fleet model output if we want to use them afterwards rather than this dummy return
        return fleet_evolution_return

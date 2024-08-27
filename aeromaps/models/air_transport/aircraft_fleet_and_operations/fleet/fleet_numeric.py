# @Time : 25/01/2024 16:45
# @Author : a.salgas
# @File : aircrfat_numbe.py
# @Software: PyCharm
from aeromaps.models.base import AeroMAPSModel
from typing import Tuple
import pandas as pd
import numpy as np


class FleetEvolution(AeroMAPSModel):
    def __init__(self, name="fleet_numeric", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = fleet_model

    def compute(
        self,
        ask_short_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_long_range: pd.Series,
        rpk_short_range: pd.Series,
        rpk_medium_range: pd.Series,
        rpk_long_range: pd.Series,
        covid_start_year: int,
        covid_end_year: int,
    ) -> Tuple[dict, dict, dict, dict, dict]:
        ask_aircraft_value_dict = {}
        rpk_aircraft_value_dict = {}
        aircraft_in_fleet_value_dict = {}
        aircraft_in_fleet_value_covid_levelling_dict = {}
        aircraft_in_out_value_dict = {}

        for category, sets in self.fleet_model.fleet.all_aircraft_elements.items():
            if category == "Short Range":
                category_ask = ask_short_range
                category_rpk = rpk_short_range
            elif category == "Medium Range":
                category_ask = ask_medium_range
                category_rpk = rpk_medium_range
            else:
                category_ask = ask_long_range
                category_rpk = rpk_long_range

            # Caculation of virtual fleet demand assuming that manufacturers/airlines adapt their production to be ready for traffic catchup after covid.
            category_ask_covid_levelling = category_ask.copy()
            category_ask_pre_covid = category_ask.loc[covid_start_year - 1]
            category_ask_post_covid = category_ask.loc[covid_end_year]

            for year in range(covid_start_year, covid_end_year + 1):
                category_ask_covid_levelling.loc[year] = (
                    (category_ask_pre_covid - category_ask_post_covid) / (covid_start_year - 1)
                    - (covid_end_year)
                ) * (year - covid_start_year - 1) + category_ask_pre_covid

            # Calculating values of interest for each aircraft
            for aircraft_var in sets:
                # Check if it's a reference aircraft or a normal aircraft...
                if hasattr(aircraft_var, "parameters"):
                    aircraft_var_name = aircraft_var.parameters.full_name
                    ask_year = aircraft_var.parameters.ask_year
                else:
                    aircraft_var_name = aircraft_var.full_name
                    ask_year = aircraft_var.ask_year

                share_var_name = aircraft_var_name + ":aircraft_share"
                ask_aircraft_var_name = aircraft_var_name + ":aircraft_ask"
                rpk_aircraft_var_name = aircraft_var_name + ":aircraft_rpk"

                aircraft_in_fleet_var_name = aircraft_var_name + ":aircraft_in_fleet"

                aircraft_in_fleet_covid_levelling_var_name = (
                    aircraft_var_name + ":aircraft_in_fleet_covid_levelling"
                )

                aircraft_in_out_var_name = aircraft_var_name + ":aircraft_in_out"

                ask_aircraft_value = (
                    self.fleet_model.df.loc[
                        self.prospection_start_year : self.end_year, share_var_name
                    ]
                    / 100
                    * category_ask
                )

                rpk_aircraft_value = (
                    self.fleet_model.df.loc[
                        self.prospection_start_year : self.end_year, share_var_name
                    ]
                    / 100
                    * category_rpk
                )

                ask_aircraft_value_covid_levelling = (
                    self.fleet_model.df.loc[
                        self.prospection_start_year : self.end_year, share_var_name
                    ]
                    / 100
                    * category_ask_covid_levelling
                )

                aircraft_in_fleet_value = np.ceil(ask_aircraft_value / float(ask_year))
                aircraft_in_fleet_value_covid_levelling = np.ceil(
                    ask_aircraft_value_covid_levelling / float(ask_year)
                )
                aircraft_in_out_value = aircraft_in_fleet_value_covid_levelling.diff()

                self.fleet_model.df = pd.concat(
                    [
                        self.fleet_model.df,
                        ask_aircraft_value.rename(ask_aircraft_var_name),
                        rpk_aircraft_value.rename(rpk_aircraft_var_name),
                        aircraft_in_fleet_value.rename(aircraft_in_fleet_var_name),
                        aircraft_in_fleet_value_covid_levelling.rename(
                            aircraft_in_fleet_covid_levelling_var_name
                        ),
                        aircraft_in_out_value.rename(aircraft_in_out_var_name),
                    ],
                    axis=1,
                )

                ask_aircraft_value_dict[aircraft_var_name] = ask_aircraft_value
                rpk_aircraft_value_dict[aircraft_var_name] = rpk_aircraft_value
                aircraft_in_fleet_value_dict[aircraft_var_name] = aircraft_in_fleet_value
                aircraft_in_fleet_value_covid_levelling_dict[aircraft_var_name] = (
                    aircraft_in_fleet_value_covid_levelling
                )
                aircraft_in_out_value_dict[aircraft_var_name] = aircraft_in_out_value
        return (
            ask_aircraft_value_dict,
            rpk_aircraft_value_dict,
            aircraft_in_fleet_value_dict,
            aircraft_in_fleet_value_covid_levelling_dict,
            aircraft_in_out_value_dict,
        )

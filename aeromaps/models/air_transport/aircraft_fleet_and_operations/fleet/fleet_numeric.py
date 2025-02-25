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
        covid_end_year_passenger: int,
        dummy_fleet_model_output: np.ndarray,
    ) -> Tuple[
        dict,
        dict,
        dict,
        dict,
        dict,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
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
            category_ask_post_covid = category_ask.loc[covid_end_year_passenger]

            for year in range(covid_start_year, covid_end_year_passenger + 1):
                category_ask_covid_levelling.loc[year] = (
                    (category_ask_pre_covid - category_ask_post_covid) / (covid_start_year - 1)
                    - (covid_end_year_passenger)
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

        # Aggregate results by range category and aircraft production vs. disposal
        # Filter columns and calculate sums for Short Range
        short_range_cols = filter_columns(
            self.fleet_model.df, "Short Range:", suffix=":aircraft_in_out"
        )
        df_short_range = self.fleet_model.df[short_range_cols]
        aircraft_production_short_range = self.fleet_model.df[
            "Short Range: Aircraft Production"
        ] = df_short_range.apply(sum_positive, axis=1)
        aircraft_disposal_short_range = self.fleet_model.df["Short Range: Aircraft Disposal"] = (
            df_short_range.apply(sum_negative, axis=1)
        )

        # Filter columns and calculate sums for Medium Range
        medium_range_cols = filter_columns(
            self.fleet_model.df, "Medium Range:", suffix=":aircraft_in_out"
        )
        df_medium_range = self.fleet_model.df[medium_range_cols]
        aircraft_production_medium_range = self.fleet_model.df[
            "Medium Range: Aircraft Production"
        ] = df_medium_range.apply(sum_positive, axis=1)
        aircraft_disposal_medium_range = self.fleet_model.df["Medium Range: Aircraft Disposal"] = (
            df_medium_range.apply(sum_negative, axis=1)
        )

        # Filter columns and calculate sums for Long Range
        long_range_cols = filter_columns(
            self.fleet_model.df, "Long Range:", suffix=":aircraft_in_out"
        )
        df_long_range = self.fleet_model.df[long_range_cols]
        aircraft_production_long_range = self.fleet_model.df["Long Range: Aircraft Production"] = (
            df_long_range.apply(sum_positive, axis=1)
        )
        aircraft_disposal_long_range = self.fleet_model.df["Long Range: Aircraft Disposal"] = (
            df_long_range.apply(sum_negative, axis=1)
        )

        return (
            ask_aircraft_value_dict,
            rpk_aircraft_value_dict,
            aircraft_in_fleet_value_dict,
            aircraft_in_fleet_value_covid_levelling_dict,
            aircraft_in_out_value_dict,
            aircraft_production_short_range,
            aircraft_disposal_short_range,
            aircraft_production_medium_range,
            aircraft_disposal_medium_range,
            aircraft_production_long_range,
            aircraft_disposal_long_range,
        )


def filter_columns(df, prefix, suffix):
    """
    Filters columns of a dataframe by prefix and suffix
    """
    return [col for col in df.columns if col.startswith(prefix) and col.endswith(suffix)]


def sum_positive(row):
    """
    Calculates the sum of positive values in a row of a dataframe
    """
    return row[row > 0].sum()


def sum_negative(row):
    """
    Calculates the absolute sum of negative values in a row of a dataframe
    """
    return abs(row[row < 0].sum())

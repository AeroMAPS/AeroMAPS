"""
price_elasticity
=============================

Module for computing air traffic (RPK) with price elasticity effects.
"""

from typing import Tuple
from numbers import Number

# import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import (
    AeroMAPSModel,
    aeromaps_leveling_function,
    # aeromaps_interpolation_function,
)


class RPKWithElasticity(AeroMAPSModel):
    """
    Class to compute Revenue Passenger Kilometers (RPK) with price elasticity and COVID-19 impact, considering exogenous growth rates by segment.

    Parameters
    ----------
    name
        Name of the model instance ('rpk_with_elasticity' by default).
    """

    def __init__(self, name="rpk_with_elasticity", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk_init: pd.Series,
        short_range_rpk_share_2019: float,
        medium_range_rpk_share_2019: float,
        long_range_rpk_share_2019: float,
        covid_start_year: Number,
        covid_rpk_drop_start_year: float,
        covid_end_year_passenger: Number,
        covid_end_year_reference_rpk_ratio: float,
        cagr_passenger_short_range_reference_periods: list,
        cagr_passenger_short_range_reference_periods_values: list,
        cagr_passenger_medium_range_reference_periods: list,
        cagr_passenger_medium_range_reference_periods_values: list,
        cagr_passenger_long_range_reference_periods: list,
        cagr_passenger_long_range_reference_periods_values: list,
        rpk_short_range_measures_impact: pd.Series,
        rpk_medium_range_measures_impact: pd.Series,
        rpk_long_range_measures_impact: pd.Series,
        airfare_per_rpk: pd.Series,
        price_elasticity: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
    ]:
        """
        Execute the computation of prospective air traffic.

        Parameters
        ----------
        rpk_init
            Historical number of Revenue Passenger Kilometer (RPK) over 2000-2019 [RPK].
        short_range_rpk_share_2019
            Share of RPK from short-range market in 2019 [%].
        medium_range_rpk_share_2019
            Share of RPK from medium-range market in 2019 [%].
        long_range_rpk_share_2019
            Share of RPK from long-range market in 2019 [%].
        covid_start_year
            Covid-19 start year [yr].
        covid_rpk_drop_start_year
            Drop in RPK due to Covid-19 for the start year [%].
        covid_end_year_passenger
            Covid-19 end year [yr].
        covid_end_year_reference_rpk_ratio
            Percentage of traffic level reached in Covid-19 end year compared with the one in Covid-19 start year [%].
        cagr_passenger_short_range_reference_periods
            Reference periods for the CAGR for passenger short-range market [yr].
        cagr_passenger_short_range_reference_periods_values
            CAGR for passenger short-range market for the reference periods [%].
        cagr_passenger_medium_range_reference_periods
            Reference periods for the CAGR for passenger medium-range market [yr].
        cagr_passenger_medium_range_reference_periods_values
            CAGR for passenger medium-range market for the reference periods [%].
        cagr_passenger_long_range_reference_periods
            Reference periods for the CAGR for passenger long-range market [yr].
        cagr_passenger_long_range_reference_periods_values
            CAGR for passenger long-range market for the reference periods [%].
        rpk_short_range_measures_impact
            Traffic reduction impact of specific measures for passenger short-range market [%].
        rpk_medium_range_measures_impact
            Traffic reduction impact of specific measures for passenger medium-range market [%].
        rpk_long_range_measures_impact
            Traffic reduction impact of specific measures for passenger long-range market [%].
        airfare_per_rpk
            Airfare per RPK [€/RPK].
        price_elasticity
            Price elasticity of demand [-].

        Returns
        -------
        rpk_short_range
            Number of Revenue Passenger Kilometer (RPK) for passenger short-range market [RPK].
        rpk_medium_range
            Number of Revenue Passenger Kilometer (RPK) for passenger medium-range market [RPK].
        rpk_long_range
            Number of Revenue Passenger Kilometer (RPK) for passenger long-range market [RPK].
        rpk
            Number of Revenue Passenger Kilometer (RPK) for total passenger air transport [RPK].
        rpk_no_elasticity
            RPKs without considering price elasticity [RPK].
        rpk_short_range_no_elasticity
            Short-range RPKs without considering price elasticity [RPK].
        rpk_medium_range_no_elasticity
            Medium-range RPKs without considering price elasticity [RPK].
        rpk_long_range_no_elasticity
            Long-range RPKs without considering price elasticity [RPK].
        annual_growth_rate_passenger_short_range
            Annual growth rate for short-range passengers [%/year].
        annual_growth_rate_passenger_medium_range
            Annual growth rate for medium-range passengers [%/year].
        annual_growth_rate_passenger_long_range
            Annual growth rate for long-range passengers [%/year].
        annual_growth_rate_passenger
            Annual growth rate for total passengers [%/year].
        cagr_rpk_short_range
            Air traffic CAGR over prospective_years for passenger short-range market [%].
        cagr_rpk_medium_range
            Air traffic CAGR over prospective_years for passenger medium-range market [%].
        cagr_rpk_long_range
            Air traffic CAGR over prospective_years for passenger long-range market [%].
        cagr_rpk
            Air traffic CAGR over prospective_years for total passenger market [%].
        prospective_evolution_rpk_short_range
            Evolution in percentage of Revenue Passenger Kilometer (RPK) for passenger short-range market between prospection_start_year and end_year [%].
        prospective_evolution_rpk_medium_range
            Evolution in percentage of Revenue Passenger Kilometer (RPK) for passenger medium-range market between prospection_start_year and end_year [%].
        prospective_evolution_rpk_long_range
            Evolution in percentage of Revenue Passenger Kilometer (RPK) for passenger long-range market between prospection_start_year and end_year [%].
        prospective_evolution_rpk
            Evolution in percentage of Revenue Passenger Kilometer (RPK) for total passenger market between prospection_start_year and end_year [%].
        """

        hist_index = range(self.historic_start_year, self.prospection_start_year)
        covid_years = range(covid_start_year, covid_end_year_passenger + 1)
        proj_years = range(covid_end_year_passenger + 1, self.end_year + 1)
        # all_years = range(self.historic_start_year, self.end_year + 1)

        self.df.loc[hist_index, "rpk_short_range"] = (
            short_range_rpk_share_2019 / 100 * rpk_init.loc[hist_index]
        )
        self.df.loc[hist_index, "rpk_medium_range"] = (
            medium_range_rpk_share_2019 / 100 * rpk_init.loc[hist_index]
        )
        self.df.loc[hist_index, "rpk_long_range"] = (
            long_range_rpk_share_2019 / 100 * rpk_init.loc[hist_index]
        )

        # Covid functions
        reference_years = [covid_start_year, covid_end_year_passenger]
        reference_values_covid = [
            1 - covid_rpk_drop_start_year / 100,
            covid_end_year_reference_rpk_ratio / 100,
        ]
        covid_function = interp1d(reference_years, reference_values_covid, kind="linear")
        covid_factors = pd.Series(
            [float(covid_function(k)) for k in covid_years], index=covid_years, dtype=float
        )

        # CAGR function
        ## Short range
        annual_growth_rate_passenger_short_range_prospective = aeromaps_leveling_function(
            self,
            cagr_passenger_short_range_reference_periods,
            cagr_passenger_short_range_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "annual_growth_rate_passenger_short_range"] = (
            annual_growth_rate_passenger_short_range_prospective
        )
        ## Medium range
        annual_growth_rate_passenger_medium_range_prospective = aeromaps_leveling_function(
            self,
            cagr_passenger_medium_range_reference_periods,
            cagr_passenger_medium_range_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "annual_growth_rate_passenger_medium_range"] = (
            annual_growth_rate_passenger_medium_range_prospective
        )
        ## Long range
        annual_growth_rate_passenger_long_range_prospective = aeromaps_leveling_function(
            self,
            cagr_passenger_long_range_reference_periods,
            cagr_passenger_long_range_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "annual_growth_rate_passenger_long_range"] = (
            annual_growth_rate_passenger_long_range_prospective
        )

        # Covid période vectorisée
        prev_short = self.df.loc[covid_start_year - 1, "rpk_short_range"]
        prev_medium = self.df.loc[covid_start_year - 1, "rpk_medium_range"]
        prev_long = self.df.loc[covid_start_year - 1, "rpk_long_range"]
        self.df.loc[covid_years, "rpk_short_range"] = prev_short * covid_factors
        self.df.loc[covid_years, "rpk_medium_range"] = prev_medium * covid_factors
        self.df.loc[covid_years, "rpk_long_range"] = prev_long * covid_factors

        # Prospective période vectorisée (hors covid)
        # Short
        growth_short = 1 + self.df.loc[proj_years, "annual_growth_rate_passenger_short_range"] / 100
        self.df.loc[proj_years, "rpk_short_range"] = (
            self.df.loc[covid_end_year_passenger, "rpk_short_range"] * growth_short.cumprod()
        )
        # Medium
        growth_medium = (
            1 + self.df.loc[proj_years, "annual_growth_rate_passenger_medium_range"] / 100
        )
        self.df.loc[proj_years, "rpk_medium_range"] = (
            self.df.loc[covid_end_year_passenger, "rpk_medium_range"] * growth_medium.cumprod()
        )
        # Long
        growth_long = 1 + self.df.loc[proj_years, "annual_growth_rate_passenger_long_range"] / 100
        self.df.loc[proj_years, "rpk_long_range"] = (
            self.df.loc[covid_end_year_passenger, "rpk_long_range"] * growth_long.cumprod()
        )

        rpk_short_range_no_elasticity = self.df["rpk_short_range"].copy()
        rpk_medium_range_no_elasticity = self.df["rpk_medium_range"].copy()
        rpk_long_range_no_elasticity = self.df["rpk_long_range"].copy()

        # rpk_no_elasticity
        self.df.loc[hist_index, "rpk_no_elasticity"] = rpk_init.loc[hist_index]
        self.df.loc[self.prospection_start_year : self.end_year, "rpk_no_elasticity"] = (
            self.df.loc[self.prospection_start_year : self.end_year, "rpk_short_range"].fillna(0)
            + self.df.loc[self.prospection_start_year : self.end_year, "rpk_medium_range"].fillna(0)
            + self.df.loc[self.prospection_start_year : self.end_year, "rpk_long_range"].fillna(0)
        )
        rpk_no_elasticity = self.df["rpk_no_elasticity"]

        self.df.loc[self.historic_start_year : covid_end_year_passenger, "rpk"] = (
            rpk_no_elasticity.loc[self.historic_start_year : covid_end_year_passenger]
        )

        airfare_init = 0.09236379319842411

        self.df.loc[covid_end_year_passenger + 1 : self.end_year, "rpk"] = (
            rpk_no_elasticity
            / (airfare_init**price_elasticity)
            * (
                airfare_per_rpk.loc[covid_end_year_passenger + 1 : self.end_year]
                ** price_elasticity
            )
        )

        # Répartition par segment vectorisée
        rpk_short_range = self.df["rpk_short_range"] * self.df["rpk"] / rpk_no_elasticity
        rpk_medium_range = self.df["rpk_medium_range"] * self.df["rpk"] / rpk_no_elasticity
        rpk_long_range = self.df["rpk_long_range"] * self.df["rpk"] / rpk_no_elasticity

        # TODO discuss if that should be considered for surplus destruction. I think so => not inlcluded in rpk_no_elasticity
        rpk_short_range = rpk_short_range * rpk_short_range_measures_impact
        rpk_medium_range = rpk_medium_range * rpk_medium_range_measures_impact
        rpk_long_range = rpk_long_range * rpk_long_range_measures_impact

        self.df.loc[:, "rpk_short_range"] = rpk_short_range
        self.df.loc[:, "rpk_medium_range"] = rpk_medium_range
        self.df.loc[:, "rpk_long_range"] = rpk_long_range

        # Total RPK vectorisé
        self.df.loc[hist_index, "rpk"] = rpk_init.loc[hist_index]
        self.df.loc[self.prospection_start_year : self.end_year, "rpk"] = (
            self.df.loc[self.prospection_start_year : self.end_year, "rpk_short_range"].fillna(0)
            + self.df.loc[self.prospection_start_year : self.end_year, "rpk_medium_range"].fillna(0)
            + self.df.loc[self.prospection_start_year : self.end_year, "rpk_long_range"].fillna(0)
        )
        rpk = self.df["rpk"]

        # Annual growth rates vectorisés
        idx_growth = range(self.historic_start_year + 1, self.end_year + 1)
        self.df.loc[idx_growth, "annual_growth_rate_passenger_short_range"] = (
            self.df["rpk_short_range"].loc[idx_growth].values
            / self.df["rpk_short_range"].shift(1).loc[idx_growth].values
            - 1
        ) * 100
        self.df.loc[idx_growth, "annual_growth_rate_passenger_medium_range"] = (
            self.df["rpk_medium_range"].loc[idx_growth].values
            / self.df["rpk_medium_range"].shift(1).loc[idx_growth].values
            - 1
        ) * 100
        self.df.loc[idx_growth, "annual_growth_rate_passenger_long_range"] = (
            self.df["rpk_long_range"].loc[idx_growth].values
            / self.df["rpk_long_range"].shift(1).loc[idx_growth].values
            - 1
        ) * 100
        self.df.loc[idx_growth, "annual_growth_rate_passenger"] = (
            self.df["rpk"].loc[idx_growth].values / self.df["rpk"].shift(1).loc[idx_growth].values
            - 1
        ) * 100

        annual_growth_rate_passenger_short_range = self.df[
            "annual_growth_rate_passenger_short_range"
        ]
        annual_growth_rate_passenger_medium_range = self.df[
            "annual_growth_rate_passenger_medium_range"
        ]
        annual_growth_rate_passenger_long_range = self.df["annual_growth_rate_passenger_long_range"]
        annual_growth_rate_passenger = self.df["annual_growth_rate_passenger"]

        # Compound Annual Growth Rate (CAGR)
        cagr_rpk_short_range = 100 * (
            (
                self.df.loc[self.end_year, "rpk_short_range"]
                / self.df.loc[self.prospection_start_year - 1, "rpk_short_range"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        cagr_rpk_medium_range = 100 * (
            (
                self.df.loc[self.end_year, "rpk_medium_range"]
                / self.df.loc[self.prospection_start_year - 1, "rpk_medium_range"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        cagr_rpk_long_range = 100 * (
            (
                self.df.loc[self.end_year, "rpk_long_range"]
                / self.df.loc[self.prospection_start_year - 1, "rpk_long_range"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        cagr_rpk = 100 * (
            (
                self.df.loc[self.end_year, "rpk"]
                / self.df.loc[self.prospection_start_year - 1, "rpk"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )

        # Prospective evolution of RPK (between prospection_start_year-1 and end_year)
        prospective_evolution_rpk_short_range = 100 * (
            self.df.loc[self.end_year, "rpk_short_range"]
            / self.df.loc[self.prospection_start_year - 1, "rpk_short_range"]
            - 1
        )
        prospective_evolution_rpk_medium_range = 100 * (
            self.df.loc[self.end_year, "rpk_medium_range"]
            / self.df.loc[self.prospection_start_year - 1, "rpk_medium_range"]
            - 1
        )
        prospective_evolution_rpk_long_range = 100 * (
            self.df.loc[self.end_year, "rpk_long_range"]
            / self.df.loc[self.prospection_start_year - 1, "rpk_long_range"]
            - 1
        )
        prospective_evolution_rpk = 100 * (
            self.df.loc[self.end_year, "rpk"] / self.df.loc[self.prospection_start_year - 1, "rpk"]
            - 1
        )

        self.float_outputs["cagr_rpk_short_range"] = cagr_rpk_short_range
        self.float_outputs["cagr_rpk_medium_range"] = cagr_rpk_medium_range
        self.float_outputs["cagr_rpk_long_range"] = cagr_rpk_long_range
        self.float_outputs["cagr_rpk"] = cagr_rpk
        self.float_outputs["prospective_evolution_rpk_short_range"] = (
            prospective_evolution_rpk_short_range
        )
        self.float_outputs["prospective_evolution_rpk_medium_range"] = (
            prospective_evolution_rpk_medium_range
        )
        self.float_outputs["prospective_evolution_rpk_long_range"] = (
            prospective_evolution_rpk_long_range
        )
        self.float_outputs["prospective_evolution_rpk"] = prospective_evolution_rpk

        return (
            rpk_short_range,
            rpk_medium_range,
            rpk_long_range,
            rpk,
            rpk_no_elasticity,
            rpk_short_range_no_elasticity,
            rpk_medium_range_no_elasticity,
            rpk_long_range_no_elasticity,
            annual_growth_rate_passenger_short_range,
            annual_growth_rate_passenger_medium_range,
            annual_growth_rate_passenger_long_range,
            annual_growth_rate_passenger,
            cagr_rpk_short_range,
            cagr_rpk_medium_range,
            cagr_rpk_long_range,
            cagr_rpk,
            prospective_evolution_rpk_short_range,
            prospective_evolution_rpk_medium_range,
            prospective_evolution_rpk_long_range,
            prospective_evolution_rpk,
        )

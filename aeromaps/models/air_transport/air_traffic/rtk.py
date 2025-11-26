"""
rtk
===

Module to compute freight traffic.
"""

from typing import Tuple
from numbers import Number

import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeroMAPSModel, aeromaps_leveling_function


class RTK(AeroMAPSModel):
    """
    Class to compute freight traffic considering COVID-19 impact and exogenous growth rates.

    Parameters
    ----------
    name : str
        Name of the model instance ('rtk' by default).
    """

    def __init__(self, name="rtk", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rtk_init: pd.Series,
        covid_start_year: Number,
        covid_rtk_drop_start_year: float,
        covid_end_year_freight: Number,
        covid_end_year_reference_rtk_ratio: float,
        cagr_freight_reference_periods: list,
        cagr_freight_reference_periods_values: list,
    ) -> Tuple[pd.Series, pd.Series, float, float]:
        """
        RTK calculation.

        Parameters
        ----------
        rtk_init
            Historical number of Revenue Tonne Kilometer (RTK) over 2000-2019 [RTK].
        covid_start_year
            Covid-19 start year [yr].
        covid_rtk_drop_start_year
            Drop in RTK due to Covid-19 for the start year [%].
        covid_end_year_freight
            Covid-19 end year [yr].
        covid_end_year_reference_rtk_ratio
            Percentage of cargo traffic level reached in Covid-19 end year compared with the one in Covid-19 start year [%].
        cagr_freight_reference_periods
            Reference periods for the CAGR for freight market [yr].
        cagr_freight_reference_periods_values
            CAGR for freight market for the reference periods [%].

        Returns
        -------
        rtk
            Number of Revenue Tonne Kilometer (RTK) for freight air transport [RTK].
        annual_growth_rate_freight
            Annual growth rate for freight [%/year].
        cagr_rtk
            Air traffic CAGR for freight market [%].
        prospective_evolution_rtk
            Evolution in percentage of Revenue Tonne Kilometer (RTK) for freight market between prospection_start_year and end_year [%].
        """

        # Initialization
        self.df.loc[self.prospection_start_year - 1, "rtk"] = rtk_init.loc[
            self.prospection_start_year - 1
        ]

        # Covid functions
        reference_years = [covid_start_year, covid_end_year_freight]
        reference_values_covid = [
            1 - covid_rtk_drop_start_year / 100,
            covid_end_year_reference_rtk_ratio / 100,
        ]
        covid_function = interp1d(reference_years, reference_values_covid, kind="linear")

        # CAGR function
        annual_growth_rate_freight_prospective = aeromaps_leveling_function(
            self,
            cagr_freight_reference_periods,
            cagr_freight_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "annual_growth_rate_freight"] = annual_growth_rate_freight_prospective

        # Main
        for k in range(covid_start_year, covid_end_year_freight + 1):
            self.df.loc[k, "rtk"] = self.df.loc[covid_start_year - 1, "rtk"] * covid_function(k)
        for k in range(covid_end_year_freight + 1, self.end_year + 1):
            self.df.loc[k, "rtk"] = self.df.loc[k - 1, "rtk"] * (
                1 + self.df.loc[k, "annual_growth_rate_freight"] / 100
            )

        # Historic values
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "rtk"] = rtk_init.loc[k]
        for k in range(self.historic_start_year + 1, self.prospection_start_year):
            self.df.loc[k, "annual_growth_rate_freight"] = (
                self.df.loc[k, "rtk"] / self.df.loc[k - 1, "rtk"] - 1
            ) * 100
        rtk = self.df["rtk"]
        annual_growth_rate_freight = self.df["annual_growth_rate_freight"]

        # Compound Annual Growth Rate (CAGR)
        cagr_rtk = 100 * (
            (
                self.df.loc[self.end_year, "rtk"]
                / self.df.loc[self.prospection_start_year - 1, "rtk"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )

        # Prospective evolution of RTK (between prospection_start_year-1 and end_year)
        prospective_evolution_rtk = 100 * (
            self.df.loc[self.end_year, "rtk"] / self.df.loc[self.prospection_start_year - 1, "rtk"]
            - 1
        )

        self.float_outputs["cagr_rtk"] = cagr_rtk
        self.float_outputs["prospective_evolution_rtk"] = prospective_evolution_rtk

        return (
            rtk,
            annual_growth_rate_freight,
            cagr_rtk,
            prospective_evolution_rtk,
        )


class RTKReference(AeroMAPSModel):
    """
    Class to compute reference Revenue Tonne Kilometers (RTK) with baseline air traffic growth.

    Parameters
    ----------
    name : str
        Name of the model instance ('rtk_reference' by default).
    """

    def __init__(self, name="rtk_reference", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rtk: pd.Series,
        reference_cagr_freight_reference_periods: list,
        reference_cagr_freight_reference_periods_values: list,
        covid_start_year: Number,
        covid_rtk_drop_start_year: float,
        covid_end_year_freight: Number,
        covid_end_year_reference_rtk_ratio: float,
    ) -> Tuple[pd.Series, pd.Series]:
        """
        RTK reference calculation.

        Parameters
        ----------
        rtk
            Number of Revenue Tonne Kilometer (RTK) for freight air transport [RTK].
        reference_cagr_freight_reference_periods
            Reference periods for the reference CAGR for freight market [yr].
        reference_cagr_freight_reference_periods_values
            Reference CAGR for freight market for the reference periods [%].
        covid_start_year
            Covid-19 start year [yr].
        covid_rtk_drop_start_year
            Drop in RTK due to Covid-19 for the start year [%].
        covid_end_year_freight
            Covid-19 end year [yr].
        covid_end_year_reference_rtk_ratio
            Percentage of traffic level reached in Covid-19 end year compared with the one in Covid-19 start year [%].

        Returns
        -------
        rtk_reference
            Number of Revenue Tonne Kilometer (RTK) for freight air transport with a baseline air traffic growth [RTK].
        reference_annual_growth_rate_freight
            Reference annual growth rate for freight market [%/year].
        """

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "rtk_reference"] = rtk.loc[k]

        covid_start_year = int(covid_start_year)
        covid_rtk_drop_start_year = int(covid_rtk_drop_start_year)
        covid_end_year_freight = int(covid_end_year_freight)
        covid_end_year_reference_rtk_ratio = int(covid_end_year_reference_rtk_ratio)

        self.df.loc[covid_start_year - 1, "rtk_reference"] = rtk.loc[covid_start_year - 1]

        # Covid functions
        reference_years = [covid_start_year, covid_end_year_freight]
        reference_values_covid = [
            1 - covid_rtk_drop_start_year / 100,
            covid_end_year_reference_rtk_ratio / 100,
        ]
        covid_function = interp1d(reference_years, reference_values_covid, kind="linear")

        # CAGR function
        reference_annual_growth_rate_freight = aeromaps_leveling_function(
            self,
            reference_cagr_freight_reference_periods,
            reference_cagr_freight_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "reference_annual_growth_rate_freight"] = (
            reference_annual_growth_rate_freight
        )

        # Main
        for k in range(covid_start_year, covid_end_year_freight + 1):
            self.df.loc[k, "rtk_reference"] = self.df.loc[
                covid_start_year - 1, "rtk_reference"
            ] * covid_function(k)
        for k in range(covid_end_year_freight + 1, self.end_year + 1):
            self.df.loc[k, "rtk_reference"] = self.df.loc[k - 1, "rtk_reference"] * (
                1 + self.df.loc[k, "reference_annual_growth_rate_freight"] / 100
            )

        rtk_reference = self.df["rtk_reference"]

        return (rtk_reference, reference_annual_growth_rate_freight)

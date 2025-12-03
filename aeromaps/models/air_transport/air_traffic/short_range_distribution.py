"""
short_range_distribution
===========================

Module to compute short-range aircraft shares when using simple efficiency models.

Warning
-------
Apparently, this module is not used in the current version of AeroMAPS.
"""

from typing import Tuple

import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeroMAPSModel


class ShortRangeDistribution(AeroMAPSModel):
    """
    Class to compute the market shares of short-range aircraft architectures when using simple aircraft efficiency model.

    Parameters
    ----------
    name : str
        Name of the model instance ('short_range_distribution' by default).
    """

    def __init__(self, name="short_range_distribution", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        short_range_basicturbofan_share_2019: float,
        short_range_basicturbofan_share_2030: float,
        short_range_basicturbofan_share_2040: float,
        short_range_basicturbofan_share_2050: float,
        short_range_regionalturboprop_share_2019: float,
        short_range_regionalturboprop_share_2030: float,
        short_range_regionalturboprop_share_2040: float,
        short_range_regionalturboprop_share_2050: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        """
        Short range distribution calculation.

        Parameters
        ----------
        short_range_basicturbofan_share_2019
            Share of narrow-body turbofan architectures in passenger short-range market in 2019 [%].
        short_range_basicturbofan_share_2030
            Share of narrow-body turbofan architectures in passenger short-range market in 2030 [%].
        short_range_basicturbofan_share_2040
            Share of narrow-body turbofan architectures in passenger short-range market in 2040 [%].
        short_range_basicturbofan_share_2050
            Share of narrow-body turbofan architectures in passenger short-range market in 2050 [%].
        short_range_regionalturboprop_share_2019
            Share of regional turboprop architectures in passenger short-range market in 2019 [%].
        short_range_regionalturboprop_share_2030
            Share of regional turboprop architectures in passenger short-range market in 2030 [%].
        short_range_regionalturboprop_share_2040
            Share of regional turboprop architectures in passenger short-range market in 2040 [%].
        short_range_regionalturboprop_share_2050
            Share of regional turboprop architectures in passenger short-range market in 2050 [%].

        Returns
        -------
        short_range_basicturbofan_share
            Share of narrow-body turbofan architectures in passenger short-range market [%].
        short_range_regionalturboprop_share
            Share of regional turboprop architectures in passenger short-range market [%].
        short_range_regionalturbofan_share
            Share of regional turbofan architectures in passenger short-range market [%].
        """

        reference_years = [2019, 2030, 2040, self.end_year]

        # Reference
        # "short_range_basicturbofan_share_2019": 88.4,
        # "short_range_regionalturboprop_share_2019": 2.5,
        # "short_range_regionalturbofan_share_2019": 9.1,

        # Basic Turbofan
        reference_values_basicturbofan = [
            short_range_basicturbofan_share_2019,
            short_range_basicturbofan_share_2030,
            short_range_basicturbofan_share_2040,
            short_range_basicturbofan_share_2050,
        ]
        short_range_basicturbofan_share_function = interp1d(
            reference_years, reference_values_basicturbofan, kind="linear"
        )
        for k in range(self.prospection_start_year - 1, self.end_year + 1):
            self.df.loc[k, "short_range_basicturbofan_share"] = (
                short_range_basicturbofan_share_function(k)
            )

        # Regional Turboprop
        reference_values_regionalturboprop = [
            short_range_regionalturboprop_share_2019,
            short_range_regionalturboprop_share_2030,
            short_range_regionalturboprop_share_2040,
            short_range_regionalturboprop_share_2050,
        ]
        short_range_regionalturboprop_share_function = interp1d(
            reference_years, reference_values_regionalturboprop, kind="linear"
        )
        for k in range(self.prospection_start_year - 1, self.end_year + 1):
            self.df.loc[k, "short_range_regionalturboprop_share"] = (
                short_range_regionalturboprop_share_function(k)
            )

        short_range_basicturbofan_share = self.df["short_range_basicturbofan_share"]
        short_range_regionalturboprop_share = self.df["short_range_regionalturboprop_share"]

        # Regional Turbofan
        short_range_regionalturbofan_share = (
            100 - short_range_basicturbofan_share - short_range_regionalturboprop_share
        )
        self.df.loc[:, "short_range_regionalturbofan_share"] = short_range_regionalturbofan_share

        return (
            short_range_basicturbofan_share,
            short_range_regionalturboprop_share,
            short_range_regionalturbofan_share,
        )


class RPKShortRange(AeroMAPSModel):
    """
    Class to compute RPK distribution for short-range market by aircraft architecture.

    Parameters
    ----------
    name : str
        Name of the model instance ('rpk_short_range' by default).
    """

    def __init__(self, name="rpk_short_range", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk_short_range: pd.Series,
        short_range_basicturbofan_share: pd.Series,
        short_range_regionalturboprop_share: pd.Series,
        short_range_regionalturbofan_share: pd.Series,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        float,
        float,
        float,
        float,
        float,
        float,
    ]:
        """
        RPK short range calculation.

        Parameters
        ----------
        rpk_short_range
            Number of Revenue Passenger Kilometer (RPK) for passenger short-range market [RPK].
        short_range_basicturbofan_share
            Share of narrow-body turbofan architectures in passenger short-range market [%].
        short_range_regionalturboprop_share
            Share of regional turboprop architectures in passenger short-range market [%].
        short_range_regionalturbofan_share
            Share of regional turbofan architectures in passenger short-range market [%].

        Returns
        -------
        rpk_short_range_basicturbofan
            RPK for short-range market from basic turbofan aircraft [RPK].
        rpk_short_range_regionalturboprop
            RPK for short-range market from regional turboprop aircraft [RPK].
        rpk_short_range_regionalturbofan
            RPK for short-range market from regional turbofan aircraft [RPK].
        cagr_rpk_short_range_basicturbofan
            Air traffic CAGR over prospective_years for short-range basic turbofan market [%].
        cagr_rpk_short_range_regionalturboprop
            Air traffic CAGR over prospective_years for short-range regional turboprop market [%].
        cagr_rpk_short_range_regionalturbofan
            Air traffic CAGR over prospective_years for short-range regional turbofan market [%].
        prospective_evolution_rpk_short_range_basicturbofan
            Evolution in percentage of RPK for short-range basic turbofan market between prospection_start_year and end_year [%].
        prospective_evolution_rpk_short_range_regionalturboprop
            Evolution in percentage of RPK for short-range regional turboprop market between prospection_start_year and end_year [%].
        prospective_evolution_rpk_short_range_regionalturbofan
            Evolution in percentage of RPK for short-range regional turbofan market between prospection_start_year and end_year [%].
        """

        rpk_short_range_basicturbofan = rpk_short_range * short_range_basicturbofan_share / 100
        rpk_short_range_regionalturboprop = (
            rpk_short_range * short_range_regionalturboprop_share / 100
        )
        rpk_short_range_regionalturbofan = (
            rpk_short_range * short_range_regionalturbofan_share / 100
        )

        self.df.loc[:, "rpk_short_range_basicturbofan"] = rpk_short_range_basicturbofan
        self.df.loc[:, "rpk_short_range_regionalturboprop"] = rpk_short_range_regionalturboprop
        self.df.loc[:, "rpk_short_range_regionalturbofan"] = rpk_short_range_regionalturbofan

        # Compound Annual Growth Rate (CAGR)
        cagr_rpk_short_range_basicturbofan = 100 * (
            (
                self.df.loc[self.end_year, "rpk_short_range_basicturbofan"]
                / self.df.loc[self.prospection_start_year - 1, "rpk_short_range_basicturbofan"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        cagr_rpk_short_range_regionalturboprop = 100 * (
            (
                self.df.loc[self.end_year, "rpk_short_range_regionalturboprop"]
                / self.df.loc[self.prospection_start_year - 1, "rpk_short_range_regionalturboprop"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        cagr_rpk_short_range_regionalturbofan = 100 * (
            (
                self.df.loc[self.end_year, "rpk_short_range_regionalturbofan"]
                / self.df.loc[self.prospection_start_year - 1, "rpk_short_range_regionalturbofan"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )

        # Prospective evolution of RPK (between prospection_start_year-1 and end_year)
        prospective_evolution_rpk_short_range_basicturbofan = 100 * (
            self.df.loc[self.end_year, "rpk_short_range_basicturbofan"]
            / self.df.loc[self.prospection_start_year - 1, "rpk_short_range_basicturbofan"]
            - 1
        )
        prospective_evolution_rpk_short_range_regionalturboprop = 100 * (
            self.df.loc[self.end_year, "rpk_short_range_regionalturboprop"]
            / self.df.loc[self.prospection_start_year - 1, "rpk_short_range_regionalturboprop"]
            - 1
        )
        prospective_evolution_rpk_short_range_regionalturbofan = 100 * (
            self.df.loc[self.end_year, "rpk_short_range_regionalturbofan"]
            / self.df.loc[self.prospection_start_year - 1, "rpk_short_range_regionalturbofan"]
            - 1
        )

        self.float_outputs["cagr_rpk_short_range_basicturbofan"] = (
            cagr_rpk_short_range_basicturbofan
        )
        self.float_outputs["cagr_rpk_short_range_regionalturboprop"] = (
            cagr_rpk_short_range_regionalturboprop
        )
        self.float_outputs["cagr_rpk_short_range_regionalturbofan"] = (
            cagr_rpk_short_range_regionalturbofan
        )
        self.float_outputs["prospective_evolution_rpk_short_range_basicturbofan"] = (
            prospective_evolution_rpk_short_range_basicturbofan
        )
        self.float_outputs["prospective_evolution_rpk_short_range_regionalturboprop"] = (
            prospective_evolution_rpk_short_range_regionalturboprop
        )
        self.float_outputs["prospective_evolution_rpk_short_range_regionalturbofan"] = (
            prospective_evolution_rpk_short_range_regionalturbofan
        )

        return (
            rpk_short_range_basicturbofan,
            rpk_short_range_regionalturboprop,
            rpk_short_range_regionalturbofan,
            cagr_rpk_short_range_basicturbofan,
            cagr_rpk_short_range_regionalturboprop,
            cagr_rpk_short_range_regionalturbofan,
            prospective_evolution_rpk_short_range_basicturbofan,
            prospective_evolution_rpk_short_range_regionalturboprop,
            prospective_evolution_rpk_short_range_regionalturbofan,
        )

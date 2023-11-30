from typing import Tuple

import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeromapsModel


class ShortRangeDistribution(AeromapsModel):
    def __init__(self, name="short_range_distribution", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        short_range_basicturbofan_share_2019: float = 0.0,
        short_range_basicturbofan_share_2030: float = 0.0,
        short_range_basicturbofan_share_2040: float = 0.0,
        short_range_basicturbofan_share_2050: float = 0.0,
        short_range_regionalturboprop_share_2019: float = 0.0,
        short_range_regionalturboprop_share_2030: float = 0.0,
        short_range_regionalturboprop_share_2040: float = 0.0,
        short_range_regionalturboprop_share_2050: float = 0.0,
    ) -> Tuple[pd.Series, pd.Series, pd.Series,]:
        """Short range distribution calculation."""

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
            self.df.loc[
                k, "short_range_basicturbofan_share"
            ] = short_range_basicturbofan_share_function(k)

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
            self.df.loc[
                k, "short_range_regionalturboprop_share"
            ] = short_range_regionalturboprop_share_function(k)

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


class RPKShortRange(AeromapsModel):
    def __init__(self, name="rpk_short_range", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk_short_range: pd.Series = pd.Series(dtype="float64"),
        short_range_basicturbofan_share: pd.Series = pd.Series(dtype="float64"),
        short_range_regionalturboprop_share: pd.Series = pd.Series(dtype="float64"),
        short_range_regionalturbofan_share: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series, float, float, float, float, float, float,]:
        """RPK short range calculation."""

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

        self.float_outputs[
            "cagr_rpk_short_range_basicturbofan"
        ] = cagr_rpk_short_range_basicturbofan
        self.float_outputs[
            "cagr_rpk_short_range_regionalturboprop"
        ] = cagr_rpk_short_range_regionalturboprop
        self.float_outputs[
            "cagr_rpk_short_range_regionalturbofan"
        ] = cagr_rpk_short_range_regionalturbofan
        self.float_outputs[
            "prospective_evolution_rpk_short_range_basicturbofan"
        ] = prospective_evolution_rpk_short_range_basicturbofan
        self.float_outputs[
            "prospective_evolution_rpk_short_range_regionalturboprop"
        ] = prospective_evolution_rpk_short_range_regionalturboprop
        self.float_outputs[
            "prospective_evolution_rpk_short_range_regionalturbofan"
        ] = prospective_evolution_rpk_short_range_regionalturbofan

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

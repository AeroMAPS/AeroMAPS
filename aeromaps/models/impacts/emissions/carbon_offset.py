from typing import Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeromapsModel


class LevelCarbonOffset(AeromapsModel):
    def __init__(self, name="level_carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
        carbon_offset_baseline_level_vs_2019: float = 0.0,
    ) -> pd.Series:

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "level_carbon_offset"] = 0.0

        for k in range(self.prospection_start_year, self.end_year + 1):
            if (
                co2_emissions.loc[k]
                > co2_emissions.loc[2019] * carbon_offset_baseline_level_vs_2019 / 100
            ):
                self.df.loc[k, "level_carbon_offset"] = (
                    co2_emissions.loc[k]
                    - co2_emissions.loc[2019] * carbon_offset_baseline_level_vs_2019 / 100
                )
            else:
                self.df.loc[k, "level_carbon_offset"] = 0.0

        level_carbon_offset = self.df["level_carbon_offset"]

        return level_carbon_offset


class ResidualCarbonOffset(AeromapsModel):
    def __init__(self, name="residual_carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
        level_carbon_offset: pd.Series = pd.Series(dtype="float64"),
        residual_carbon_offset_share_2020: float = 0.0,
        residual_carbon_offset_share_2030: float = 0.0,
        residual_carbon_offset_share_2040: float = 0.0,
        residual_carbon_offset_share_2050: float = 0.0,
    ) -> pd.Series:

        reference_years = [2020, 2030, 2040, self.parameters.end_year]
        reference_values_residual_carbon_offset_share = [
            residual_carbon_offset_share_2020,
            residual_carbon_offset_share_2030,
            residual_carbon_offset_share_2040,
            residual_carbon_offset_share_2050,
        ]
        residual_carbon_offset_share_function = interp1d(
            reference_years, reference_values_residual_carbon_offset_share, kind="linear"
        )
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "residual_carbon_offset_share"] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "residual_carbon_offset_share"] = residual_carbon_offset_share_function(
                k
            )

        for k in range(self.historic_start_year, self.end_year + 1):
            self.df.loc[k, "residual_carbon_offset"] = (
                self.df.loc[k, "residual_carbon_offset_share"]
                / 100
                * (co2_emissions.loc[k] - level_carbon_offset.loc[k])
            )

        residual_carbon_offset = self.df["residual_carbon_offset"]

        return residual_carbon_offset


class CarbonOffset(AeromapsModel):
    def __init__(self, name="carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        level_carbon_offset: pd.Series = pd.Series(dtype="float64"),
        residual_carbon_offset: pd.Series = pd.Series(dtype="float64"),
    ) -> pd.Series:

        carbon_offset = level_carbon_offset + residual_carbon_offset

        self.df.loc[:, "carbon_offset"] = carbon_offset

        return carbon_offset

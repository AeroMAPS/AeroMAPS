from typing import Tuple

import pandas as pd

from aeromaps.models.base import (
    AeromapsModel,
    AeromapsInterpolationFunction,
    AeromapsLevelingFunction,
)


class LevelCarbonOffset(AeromapsModel):
    def __init__(self, name="level_carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
        carbon_offset_baseline_level_vs_2019_reference_periods: list = [],
        carbon_offset_baseline_level_vs_2019_reference_periods_values: list = [],
    ) -> Tuple[pd.Series, pd.Series]:

        carbon_offset_baseline_level_vs_2019 = AeromapsLevelingFunction(
            self,
            carbon_offset_baseline_level_vs_2019_reference_periods,
            carbon_offset_baseline_level_vs_2019_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[
            :, "carbon_offset_baseline_level_vs_2019"
        ] = carbon_offset_baseline_level_vs_2019

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "level_carbon_offset"] = 0.0

        for k in range(self.prospection_start_year, self.end_year + 1):
            if (
                co2_emissions.loc[k]
                > co2_emissions.loc[2019]
                * self.df.loc[k, "carbon_offset_baseline_level_vs_2019"]
                / 100
            ):
                self.df.loc[k, "level_carbon_offset"] = (
                    co2_emissions.loc[k]
                    - co2_emissions.loc[2019]
                    * self.df.loc[k, "carbon_offset_baseline_level_vs_2019"]
                    / 100
                )
            else:
                self.df.loc[k, "level_carbon_offset"] = 0.0

        level_carbon_offset = self.df["level_carbon_offset"]

        return (carbon_offset_baseline_level_vs_2019, level_carbon_offset)


class ResidualCarbonOffset(AeromapsModel):
    def __init__(self, name="residual_carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
        level_carbon_offset: pd.Series = pd.Series(dtype="float64"),
        residual_carbon_offset_share_reference_years: list = [],
        residual_carbon_offset_share_reference_years_values: list = [],
    ) -> Tuple[pd.Series, pd.Series]:

        residual_carbon_offset_share_prospective = AeromapsInterpolationFunction(
            self,
            residual_carbon_offset_share_reference_years,
            residual_carbon_offset_share_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "residual_carbon_offset_share"] = residual_carbon_offset_share_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "residual_carbon_offset_share"] = 0.0
        residual_carbon_offset_share = self.df["residual_carbon_offset_share"]

        for k in range(self.historic_start_year, self.end_year + 1):
            self.df.loc[k, "residual_carbon_offset"] = (
                self.df.loc[k, "residual_carbon_offset_share"]
                / 100
                * (co2_emissions.loc[k] - level_carbon_offset.loc[k])
            )

        residual_carbon_offset = self.df["residual_carbon_offset"]

        return (residual_carbon_offset_share, residual_carbon_offset)


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


class CumulativeCarbonOffset(AeromapsModel):
    def __init__(self, name="cumulative_carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        carbon_offset: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series]:

        self.df.loc[self.prospection_start_year - 1, "cumulative_carbon_offset"] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "cumulative_carbon_offset"] = (
                self.df.loc[k - 1, "cumulative_carbon_offset"] + carbon_offset.loc[k] / 1000
            )

        cumulative_carbon_offset = self.df["cumulative_carbon_offset"]

        return cumulative_carbon_offset

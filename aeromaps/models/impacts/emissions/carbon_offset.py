"""
carbon_offset

===============================
Module to compute effects of carbon offsets.
"""

from typing import Tuple

import pandas as pd

from aeromaps.models.base import (
    AeroMAPSModel,
    aeromaps_interpolation_function,
    aeromaps_leveling_function,
)


class LevelCarbonOffset(AeroMAPSModel):
    """
    Class to compute carbon offset required to level emissions to offsetting targets compared to 2019 emissions.

    Parameters
    --------------
    name : str
        Name of the model instance ('level_carbon_offset' by default).
    """

    def __init__(self, name="level_carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions: pd.Series,
        carbon_offset_baseline_level_vs_2019_reference_periods: list,
        carbon_offset_baseline_level_vs_2019_reference_periods_values: list,
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Execute the computation of carbon offset required to level emissions.

        Parameters
        ----------
        co2_emissions
            CO2 emissions trajectory [MtCO2].
        carbon_offset_baseline_level_vs_2019_reference_periods
            Reference periods for the level of CO2 emissions relative to 2019 from which higher emissions are offset [years].
        carbon_offset_baseline_level_vs_2019_reference_periods_values
            Level of CO2 emissions relative to 2019 from which higher emissions are offset for the reference periods [%].

        Returns
        -------
        carbon_offset_baseline_level_vs_2019
            Level of CO2 emissions relative to 2019 from which higher emissions are offset [%].
        level_carbon_offset
            Annual carbon offset due to offsetting for a given level of emissions [MtCO2].

        """
        carbon_offset_baseline_level_vs_2019 = aeromaps_leveling_function(
            self,
            carbon_offset_baseline_level_vs_2019_reference_periods,
            carbon_offset_baseline_level_vs_2019_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "carbon_offset_baseline_level_vs_2019"] = (
            carbon_offset_baseline_level_vs_2019
        )

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


class ResidualCarbonOffset(AeroMAPSModel):
    """
    Class to compute carbon offset to match a share of residual emissions.

    Parameters
    --------------
    name : str
        Name of the model instance ('residual_carbon_offset' by default).
    """

    def __init__(self, name="residual_carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions: pd.Series,
        level_carbon_offset: pd.Series,
        residual_carbon_offset_share_reference_years: list,
        residual_carbon_offset_share_reference_years_values: list,
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Execute the computation of carbon offset to match a share of residual emissions.

        Parameters
        ----------
        co2_emissions
            CO2 emissions trajectory [MtCO2].
        level_carbon_offset
            Annual carbon offset due to offsetting for a given level of emissions [MtCO2].
        residual_carbon_offset_share_reference_years
            Reference years for the share of remaining CO2 emissions offset [years].
        residual_carbon_offset_share_reference_years_values
            Share of residual emissions to be offset for the reference years [%].

        Returns
        -------
        residual_carbon_offset_share
            Share of residual emissions to be offset [%].
        residual_carbon_offset
            Annual carbon offset due to offsetting of a given share of the remaining emissions [MtCO2].

        """
        residual_carbon_offset_share_prospective = aeromaps_interpolation_function(
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


class CarbonOffset(AeroMAPSModel):
    """
    Class to compute total carbon offset.

    Parameters
    --------------
    name : str
        Name of the model instance ('carbon_offset' by default).
    """

    def __init__(self, name="carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        level_carbon_offset: pd.Series,
        residual_carbon_offset: pd.Series,
    ) -> pd.Series:
        """
        Execute the computation of total carbon offset.

        Parameters
        ----------
        level_carbon_offset
            Annual carbon offset due to offsetting for a given level of emissions [MtCO2].
        residual_carbon_offset
            Annual carbon offset due to offsetting of a given share of the remaining emissions [MtCO2].

        Returns
        -------
        carbon_offset
            Total annual carbon offset [MtCO2].

        """
        carbon_offset = level_carbon_offset + residual_carbon_offset

        self.df.loc[:, "carbon_offset"] = carbon_offset

        return carbon_offset


class CumulativeCarbonOffset(AeroMAPSModel):
    """
    Class to compute cumulative carbon offset.

    Parameters
    --------------
    name : str
        Name of the model instance ('cumulative_carbon_offset' by default).
    """

    def __init__(self, name="cumulative_carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        carbon_offset: pd.Series,
    ) -> pd.Series:
        """
        Execute the computation of cumulative carbon offset.

        Parameters
        ----------
        carbon_offset
            Total annual carbon offset [MtCO2].

        Returns
        -------
        cumulative_carbon_offset
            Cumulative carbon offset from air transport [GtCO2].

        """
        self.df.loc[self.prospection_start_year - 1, "cumulative_carbon_offset"] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "cumulative_carbon_offset"] = (
                self.df.loc[k - 1, "cumulative_carbon_offset"] + carbon_offset.loc[k] / 1000
            )

        cumulative_carbon_offset = self.df["cumulative_carbon_offset"]

        return cumulative_carbon_offset

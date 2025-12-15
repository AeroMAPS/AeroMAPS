"""
atag_offset

===============================
Module to compute carbon offsets in ATAG scenarios.

It is assumed that residual emissions are capped at 2019 levels until 2035, then decline
linearly to net-zero by 2050. In practice offsets are calculated from the gap between
actual emissions and the target residual trajectory.
"""
from typing import Tuple

import pandas as pd

from aeromaps.models.base import (
    AeroMAPSModel,
    aeromaps_interpolation_function,
)


class ATAGOffset(AeroMAPSModel):
    """
    Class to compute carbon offsets in ATAG scenarios.

    It is assumed that residual emissions are capped at 2019 levels until 2035, then decline
    linearly to net-zero by 2050. In practice offsets are calculated from the gap between
    actual emissions and the target residual trajectory.

    Parameters
    --------------
    name : str
        Name of the model instance ('atag_offset' by default).
    """
    def __init__(self, name="atag_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(self, co2_emissions: pd.Series) -> Tuple[pd.Series, pd.Series]:
        co2_2019_value = co2_emissions.loc[2019]
        residual_co2_trajectory = aeromaps_interpolation_function(
            self,
            [co2_2019_value, co2_2019_value, 0.0],
            [2019, 2035, 2050],
            model_name=self.name,
        )

        for k in range(self.prospection_start_year, self.end_year + 1):
            if co2_emissions.loc[k] > residual_co2_trajectory.loc[k]:
                self.df.loc[k, "carbon_offset"] = (
                        co2_emissions.loc[k] - residual_co2_trajectory.loc[k]
                )
            else:
                self.df.loc[k, "carbon_offset"] = 0.0

        carbon_offset = self.df["carbon_offset"]

        self.df.loc[self.prospection_start_year - 1, "cumulative_carbon_offset"] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "cumulative_carbon_offset"] = (
                    self.df.loc[k - 1, "cumulative_carbon_offset"] + carbon_offset.loc[
                k] / 1000
            )

        cumulative_carbon_offset = self.df["cumulative_carbon_offset"]

        return carbon_offset, cumulative_carbon_offset

from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel


class EmissionsPerRPK(AeromapsModel):
    def __init__(self, name="emissions_per_rpk", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions_passenger: pd.Series = pd.Series(dtype="float64"),
        rpk: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series]:
        """CO2 emissions per Revenue Passenger Kilometer calculation."""

        self.df["co2_emissions_per_rpk"] = co2_emissions_passenger * 1e6 * 1e6 / rpk
        co2_emissions_per_rpk = self.df["co2_emissions_per_rpk"]

        return co2_emissions_per_rpk


class EmissionsPerRTK(AeromapsModel):
    def __init__(self, name="emissions_per_rpk", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions_freight: pd.Series = pd.Series(dtype="float64"),
        rtk: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series]:
        """CO2 emissions per Revenue Tonne Kilometer calculation."""

        self.df["co2_emissions_per_rtk"] = co2_emissions_freight * 1e6 * 1e6 / rtk
        co2_emissions_per_rtk = self.df["co2_emissions_per_rtk"]

        return co2_emissions_per_rtk

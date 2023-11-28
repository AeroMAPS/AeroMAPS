from typing import Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeromapsModel


class DropinFuelDistribution(AeromapsModel):
    def __init__(self, name="dropin_fuel_distribution", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        biofuel_share_reference_years: list = [],
        biofuel_share_reference_years_values: list = [],
        electrofuel_share_reference_years: list = [],
        electrofuel_share_reference_years_values: list = [],
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Fuel distribution calculation using interpolation functions"""

        # Biofuel
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "biofuel_share"] = 0
        if len(biofuel_share_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "biofuel_share"] = biofuel_share_reference_years_values
        else:
            biofuel_share_function = interp1d(
                biofuel_share_reference_years,
                biofuel_share_reference_years_values,
                kind="quadratic",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                if biofuel_share_function(k) <= 0:
                    self.df.loc[k, "biofuel_share"] = 0
                else:
                    self.df.loc[k, "biofuel_share"] = biofuel_share_function(k)
        biofuel_share = self.df["biofuel_share"]

        # Electrofuel
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "electrofuel_share"] = 0
        if len(electrofuel_share_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "electrofuel_share"] = electrofuel_share_reference_years_values
        else:
            electrofuel_share_function = interp1d(
                electrofuel_share_reference_years,
                electrofuel_share_reference_years_values,
                kind="quadratic",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                if electrofuel_share_function(k) <= 0:
                    self.df.loc[k, "electrofuel_share"] = 0
                else:
                    self.df.loc[k, "electrofuel_share"] = electrofuel_share_function(k)
        electrofuel_share = self.df["electrofuel_share"]

        # Kerosene
        kerosene_share = 100 - biofuel_share - electrofuel_share
        self.df.loc[:, "kerosene_share"] = kerosene_share

        return biofuel_share, electrofuel_share, kerosene_share

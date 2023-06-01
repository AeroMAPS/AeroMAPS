from typing import Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeromapsModel

# Vérifier l'appellation fuel ou drop-in fuel ou autre ?


class FuelDistribution(AeromapsModel):
    def __init__(self, name="aircraft_energy", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        biofuel_share_2020: float = 0.0,
        biofuel_share_2030: float = 0.0,
        biofuel_share_2040: float = 0.0,
        biofuel_share_2050: float = 0.0,
        electrofuel_share_2020: float = 0.0,
        electrofuel_share_2030: float = 0.0,
        electrofuel_share_2040: float = 0.0,
        electrofuel_share_2050: float = 0.0,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Fuel distribution calculation using interpolation functions"""

        reference_years = [2020, 2030, 2040, 2050]

        # Biofuel
        reference_values_biofuel = [
            biofuel_share_2020,
            biofuel_share_2030,
            biofuel_share_2040,
            biofuel_share_2050,
        ]
        biofuel_share_function = interp1d(
            reference_years, reference_values_biofuel, kind="quadratic"
        )
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "biofuel_share"] = 0
        for k in range(self.prospection_start_year, self.end_year + 1):
            if biofuel_share_function(k) <= 0:
                self.df.loc[k, "biofuel_share"] = 0
            else:
                self.df.loc[k, "biofuel_share"] = biofuel_share_function(k)

        # Electrofuel
        reference_values_electrofuel = [
            electrofuel_share_2020,
            electrofuel_share_2030,
            electrofuel_share_2040,
            electrofuel_share_2050,
        ]
        electrofuel_share_function = interp1d(
            reference_years, reference_values_electrofuel, kind="quadratic"
        )
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "electrofuel_share"] = 0
        for k in range(self.prospection_start_year, self.end_year + 1):
            if electrofuel_share_function(k) <= 0:
                self.df.loc[k, "electrofuel_share"] = 0
            else:
                self.df.loc[k, "electrofuel_share"] = electrofuel_share_function(k)

        biofuel_share = self.df["biofuel_share"]
        electrofuel_share = self.df["electrofuel_share"]

        # Kerosene
        kerosene_share = 100 - biofuel_share - electrofuel_share
        self.df.loc[:, "kerosene_share"] = kerosene_share

        return biofuel_share, electrofuel_share, kerosene_share

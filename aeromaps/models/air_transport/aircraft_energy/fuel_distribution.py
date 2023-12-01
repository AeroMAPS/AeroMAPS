from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeromapsModel, AeromapsInterpolationFunction


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
        biofuel_share_prospective = AeromapsInterpolationFunction(
            self,
            biofuel_share_reference_years,
            biofuel_share_reference_years_values,
            method="quadratic",
            positive_constraint=True,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_share"] = biofuel_share_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "biofuel_share"] = self.df.loc[
                self.prospection_start_year, "biofuel_share"
            ]
        biofuel_share = self.df["biofuel_share"]

        # Electrofuel
        electrofuel_share_prospective = AeromapsInterpolationFunction(
            self,
            electrofuel_share_reference_years,
            electrofuel_share_reference_years_values,
            method="quadratic",
            positive_constraint=True,
            model_name=self.name,
        )
        self.df.loc[:, "electrofuel_share"] = electrofuel_share_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "electrofuel_share"] = self.df.loc[
                self.prospection_start_year, "electrofuel_share"
            ]
        electrofuel_share = self.df["electrofuel_share"]

        # Kerosene
        kerosene_share = 100 - biofuel_share - electrofuel_share
        self.df.loc[:, "kerosene_share"] = kerosene_share

        return biofuel_share, electrofuel_share, kerosene_share

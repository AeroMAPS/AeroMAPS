from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function


class DropinFuelDistribution(AeroMAPSModel):
    def __init__(self, name="dropin_fuel_distribution", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        biofuel_share_reference_years: list,
        biofuel_share_reference_years_values: np.ndarray,
        electrofuel_share_reference_years: list,
        electrofuel_share_reference_years_values: np.ndarray,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Fuel distribution calculation using interpolation functions"""

        ######### MOD FOR OPTIM ###########

        # TODO remove if not optim // make generic
        #Reduce number of optim varaibales and fixes 2020 values to zero
        biofuel_share_reference_years_local = biofuel_share_reference_years.copy()
        biofuel_share_reference_years_local.insert(0,2020)
        biofuel_share_reference_years_values_local = np.insert(biofuel_share_reference_years_values,0,0)

        electrofuel_share_reference_years_local = electrofuel_share_reference_years.copy()
        electrofuel_share_reference_years_local.insert(0,2020)
        electrofuel_share_reference_years_values_local = np.insert(electrofuel_share_reference_years_values,0,0)



        ######### END MOD FOR OPTIM ###########

        # Biofuel
        biofuel_share_prospective = aeromaps_interpolation_function(
            self,
            biofuel_share_reference_years_local,
            biofuel_share_reference_years_values_local,
            method="linear",
            positive_constraint=True,
            model_name=self.name,
        )

        # rounding to a very high order to avoid numerical problems when computing atj share
        biofuel_share_prospective = np.round(biofuel_share_prospective, 15)

        self.df.loc[:, "biofuel_share"] = biofuel_share_prospective
        for k in range(self.other_data_start_year, self.prospection_start_year):
            self.df.loc[k, "biofuel_share"] = self.df.loc[
                self.prospection_start_year, "biofuel_share"
            ]
        biofuel_share = self.df["biofuel_share"]

        # Electrofuel
        electrofuel_share_prospective = aeromaps_interpolation_function(
            self,
            electrofuel_share_reference_years_local,
            electrofuel_share_reference_years_values_local,
            method="linear",
            positive_constraint=True,
            model_name=self.name,
        )

        # rounding to a very high order to avoid numerical problems when computing atj share
        electrofuel_share_prospective = np.round(electrofuel_share_prospective, 15)

        self.df.loc[:, "electrofuel_share"] = electrofuel_share_prospective
        for k in range(self.other_data_start_year, self.prospection_start_year):
            self.df.loc[k, "electrofuel_share"] = self.df.loc[
                self.prospection_start_year, "electrofuel_share"
            ]
        electrofuel_share = self.df["electrofuel_share"]

        # Kerosene
        kerosene_share = 100 - biofuel_share - electrofuel_share
        self.df.loc[:, "kerosene_share"] = kerosene_share

        return biofuel_share, electrofuel_share, kerosene_share

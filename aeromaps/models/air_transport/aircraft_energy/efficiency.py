from typing import Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeromapsModel, InterpolationAeromapsFunction


class BiofuelEfficiency(AeromapsModel):
    def __init__(self, name="biofuel_efficiency", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        biofuel_ft_efficiency_reference_years: list = [],
        biofuel_ft_efficiency_reference_years_values: list = [],
        biofuel_atj_efficiency_reference_years: list = [],
        biofuel_atj_efficiency_reference_years_values: list = [],
        biofuel_hefa_oil_efficiency_reference_years: list = [],
        biofuel_hefa_oil_efficiency_reference_years_values: list = [],
        biofuel_hefa_fuel_efficiency_reference_years: list = [],
        biofuel_hefa_fuel_efficiency_reference_years_values: list = [],
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """Biofuel production efficiency calculation using interpolation functions"""

        # FT
        biofuel_ft_efficiency = InterpolationAeromapsFunction(
            self, biofuel_ft_efficiency_reference_years, biofuel_ft_efficiency_reference_years_values
        )
        self.df.loc[:, "biofuel_ft_efficiency"] = biofuel_ft_efficiency

        # ATJ
        biofuel_atj_efficiency = InterpolationAeromapsFunction(
            self, biofuel_atj_efficiency_reference_years, biofuel_atj_efficiency_reference_years_values
        )
        self.df.loc[:, "biofuel_atj_efficiency"] = biofuel_atj_efficiency

        # HEFA OIL
        biofuel_hefa_oil_efficiency = InterpolationAeromapsFunction(
            self, biofuel_hefa_oil_efficiency_reference_years, biofuel_hefa_oil_efficiency_reference_years_values
        )
        self.df.loc[:, "biofuel_hefa_oil_efficiency"] = biofuel_hefa_oil_efficiency

        # HEFA FUEL
        biofuel_hefa_fuel_efficiency = InterpolationAeromapsFunction(
            self, biofuel_hefa_fuel_efficiency_reference_years, biofuel_hefa_fuel_efficiency_reference_years_values
        )
        self.df.loc[:, "biofuel_hefa_fuel_efficiency"] = biofuel_hefa_fuel_efficiency

        return (
            biofuel_ft_efficiency,
            biofuel_atj_efficiency,
            biofuel_hefa_oil_efficiency,
            biofuel_hefa_fuel_efficiency,
        )


class ElectricityBasedFuelEfficiency(AeromapsModel):
    def __init__(self, name="electricity_based_fuel_efficiency", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        electrolysis_efficiency_reference_years: list = [],
        electrolysis_efficiency_reference_years_values: list = [],
        liquefaction_efficiency_reference_years: list = [],
        liquefaction_efficiency_reference_years_values: list = [],
        electrofuel_hydrogen_efficiency_reference_years: list = [],
        electrofuel_hydrogen_efficiency_reference_years_values: list = [],
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Hydrogen and electrofuel production efficiency calculation using interpolation functions"""

        # Electrolysis
        electrolysis_efficiency = InterpolationAeromapsFunction(
            self, electrolysis_efficiency_reference_years, electrolysis_efficiency_reference_years_values
        )
        self.df.loc[:, "electrolysis_efficiency"] = electrolysis_efficiency

        # Liquefaction
        liquefaction_efficiency = InterpolationAeromapsFunction(
            self, liquefaction_efficiency_reference_years, liquefaction_efficiency_reference_years_values
        )
        self.df.loc[:, "liquefaction_efficiency"] = liquefaction_efficiency

        # Electrofuel from hydrogen
        electrofuel_hydrogen_efficiency = InterpolationAeromapsFunction(
            self, electrofuel_hydrogen_efficiency_reference_years, electrofuel_hydrogen_efficiency_reference_years_values
        )
        self.df.loc[:, "electrofuel_hydrogen_efficiency"] = electrofuel_hydrogen_efficiency

        return electrolysis_efficiency, liquefaction_efficiency, electrofuel_hydrogen_efficiency

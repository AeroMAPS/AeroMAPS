from typing import Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeromapsModel


class BiofuelEfficiency(AeromapsModel):
    def __init__(self, name="biofuel_efficiency", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        biofuel_ft_efficiency_2020: float = 0.0,
        biofuel_ft_efficiency_2050: float = 0.0,
        biofuel_atj_efficiency_2020: float = 0.0,
        biofuel_atj_efficiency_2050: float = 0.0,
        biofuel_hefa_oil_efficiency_2020: float = 0.0,
        biofuel_hefa_oil_efficiency_2050: float = 0.0,
        biofuel_hefa_fuel_efficiency_2020: float = 0.0,
        biofuel_hefa_fuel_efficiency_2050: float = 0.0,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """Biofuel production efficiency calculation using interpolation functions"""

        reference_years = [2020, self.end_year]

        # FT
        reference_values_ft = [
            biofuel_ft_efficiency_2020,
            biofuel_ft_efficiency_2050,
        ]
        biofuel_ft_efficiency_function = interp1d(
            reference_years, reference_values_ft, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "biofuel_ft_efficiency"] = biofuel_ft_efficiency_function(k)

        # ATJ
        reference_values_atj = [
            biofuel_atj_efficiency_2020,
            biofuel_atj_efficiency_2050,
        ]
        biofuel_atj_efficiency_function = interp1d(
            reference_years, reference_values_atj, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "biofuel_atj_efficiency"] = biofuel_atj_efficiency_function(k)

        # HEFA OIL
        reference_values_hefa_oil = [
            biofuel_hefa_oil_efficiency_2020,
            biofuel_hefa_oil_efficiency_2050,
        ]
        biofuel_hefa_oil_efficiency_function = interp1d(
            reference_years, reference_values_hefa_oil, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "biofuel_hefa_oil_efficiency"] = biofuel_hefa_oil_efficiency_function(k)

        # HEFA FUEL
        reference_values_hefa_fuel = [
            biofuel_hefa_fuel_efficiency_2020,
            biofuel_hefa_fuel_efficiency_2050,
        ]
        biofuel_hefa_fuel_efficiency_function = interp1d(
            reference_years, reference_values_hefa_fuel, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "biofuel_hefa_fuel_efficiency"] = biofuel_hefa_fuel_efficiency_function(
                k
            )

        biofuel_ft_efficiency = self.df["biofuel_ft_efficiency"]
        biofuel_atj_efficiency = self.df["biofuel_atj_efficiency"]
        biofuel_hefa_oil_efficiency = self.df["biofuel_hefa_oil_efficiency"]
        biofuel_hefa_fuel_efficiency = self.df["biofuel_hefa_fuel_efficiency"]

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
        electrolysis_efficiency_2020: float = 0.0,
        electrolysis_efficiency_2050: float = 0.0,
        liquefaction_efficiency_2020: float = 0.0,
        liquefaction_efficiency_2050: float = 0.0,
        electrofuel_hydrogen_efficiency_2020: float = 0.0,
        electrofuel_hydrogen_efficiency_2050: float = 0.0,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Hydrogen and electrofuel production efficiency calculation using interpolation functions"""

        reference_years = [2020, self.end_year]

        # Electrolysis
        reference_values_electrolysis = [
            electrolysis_efficiency_2020,
            electrolysis_efficiency_2050,
        ]
        electrolysis_efficiency_function = interp1d(
            reference_years, reference_values_electrolysis, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "electrolysis_efficiency"] = electrolysis_efficiency_function(k)

        # Liquefaction
        reference_values_liquefaction = [
            liquefaction_efficiency_2020,
            liquefaction_efficiency_2050,
        ]
        liquefaction_efficiency_function = interp1d(
            reference_years, reference_values_liquefaction, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "liquefaction_efficiency"] = liquefaction_efficiency_function(k)

        # Electrofuel from hydrogen
        reference_values_electrofuel_hydrogen = [
            electrofuel_hydrogen_efficiency_2020,
            electrofuel_hydrogen_efficiency_2050,
        ]
        electrofuel_hydrogen_efficiency_function = interp1d(
            reference_years, reference_values_electrofuel_hydrogen, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[
                k, "electrofuel_hydrogen_efficiency"
            ] = electrofuel_hydrogen_efficiency_function(k)

        electrolysis_efficiency = self.df["electrolysis_efficiency"]
        liquefaction_efficiency = self.df["liquefaction_efficiency"]
        electrofuel_hydrogen_efficiency = self.df["electrofuel_hydrogen_efficiency"]

        return electrolysis_efficiency, liquefaction_efficiency, electrofuel_hydrogen_efficiency

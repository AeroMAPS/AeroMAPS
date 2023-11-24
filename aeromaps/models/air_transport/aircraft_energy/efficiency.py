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
        if len(biofuel_ft_efficiency_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "biofuel_ft_efficiency"
                ] = biofuel_ft_efficiency_reference_years_values
        else:
            biofuel_ft_efficiency_function = interp1d(
                biofuel_ft_efficiency_reference_years,
                biofuel_ft_efficiency_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "biofuel_ft_efficiency"
                ] = biofuel_ft_efficiency_function(k)

        # ATJ
        if len(biofuel_atj_efficiency_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "biofuel_atj_efficiency"
                ] = biofuel_atj_efficiency_reference_years_values
        else:
            biofuel_atj_efficiency_function = interp1d(
                biofuel_atj_efficiency_reference_years,
                biofuel_atj_efficiency_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "biofuel_atj_efficiency"
                ] = biofuel_atj_efficiency_function(k)

        # HEFA OIL
        if len(biofuel_hefa_oil_efficiency_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "biofuel_hefa_oil_efficiency"
                ] = biofuel_hefa_oil_efficiency_reference_years_values
        else:
            biofuel_hefa_oil_efficiency_function = interp1d(
                biofuel_hefa_oil_efficiency_reference_years,
                biofuel_hefa_oil_efficiency_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "biofuel_hefa_oil_efficiency"
                ] = biofuel_hefa_oil_efficiency_function(k)

        # HEFA FUEL
        if len(biofuel_hefa_fuel_efficiency_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "biofuel_hefa_fuel_efficiency"
                ] = biofuel_hefa_fuel_efficiency_reference_years_values
        else:
            biofuel_hefa_fuel_efficiency_function = interp1d(
                biofuel_hefa_fuel_efficiency_reference_years,
                biofuel_hefa_fuel_efficiency_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "biofuel_hefa_fuel_efficiency"
                ] = biofuel_hefa_fuel_efficiency_function(k)

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
        electrolysis_efficiency_reference_years: list = [],
        electrolysis_efficiency_reference_years_values: list = [],
        liquefaction_efficiency_reference_years: list = [],
        liquefaction_efficiency_reference_years_values: list = [],
        electrofuel_hydrogen_efficiency_reference_years: list = [],
        electrofuel_hydrogen_efficiency_reference_years_values: list = [],
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Hydrogen and electrofuel production efficiency calculation using interpolation functions"""

        # Electrolysis
        if len(electrolysis_efficiency_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "electrolysis_efficiency"
                ] = electrolysis_efficiency_reference_years_values
        else:
            electrolysis_efficiency_function = interp1d(
                electrolysis_efficiency_reference_years,
                electrolysis_efficiency_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "electrolysis_efficiency"
                ] = electrolysis_efficiency_function(k)

        # Liquefaction
        if len(liquefaction_efficiency_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "liquefaction_efficiency"
                ] = liquefaction_efficiency_reference_years_values
        else:
            liquefaction_efficiency_function = interp1d(
                liquefaction_efficiency_reference_years,
                liquefaction_efficiency_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "liquefaction_efficiency"
                ] = liquefaction_efficiency_function(k)

        # Electrofuel from hydrogen
        if len(electrofuel_hydrogen_efficiency_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "electrofuel_hydrogen_efficiency"
                ] = electrofuel_hydrogen_efficiency_reference_years_values
        else:
            electrofuel_hydrogen_efficiency_function = interp1d(
                electrofuel_hydrogen_efficiency_reference_years,
                electrofuel_hydrogen_efficiency_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "electrofuel_hydrogen_efficiency"
                ] = electrofuel_hydrogen_efficiency_function(k)

        electrolysis_efficiency = self.df["electrolysis_efficiency"]
        liquefaction_efficiency = self.df["liquefaction_efficiency"]
        electrofuel_hydrogen_efficiency = self.df["electrofuel_hydrogen_efficiency"]

        return electrolysis_efficiency, liquefaction_efficiency, electrofuel_hydrogen_efficiency

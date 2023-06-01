from typing import Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeromapsModel


class BiofuelProduction(AeromapsModel):
    def __init__(self, name="biofuel_production", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        biofuel_hefa_fog_share_2020: float,
        biofuel_hefa_fog_share_2030: float,
        biofuel_hefa_fog_share_2040: float,
        biofuel_hefa_fog_share_2050: float,
        biofuel_hefa_others_share_2020: float,
        biofuel_hefa_others_share_2030: float,
        biofuel_hefa_others_share_2040: float,
        biofuel_hefa_others_share_2050: float,
        biofuel_ft_others_share_2020: float,
        biofuel_ft_others_share_2030: float,
        biofuel_ft_others_share_2040: float,
        biofuel_ft_others_share_2050: float,
        biofuel_ft_msw_share_2020: float,
        biofuel_ft_msw_share_2030: float,
        biofuel_ft_msw_share_2040: float,
        biofuel_ft_msw_share_2050: float,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Biomass production calculation using interpolation functions"""

        reference_years = [2020, 2030, 2040, 2050]

        # HEFA FOG
        reference_values_hefa_fog = [
            biofuel_hefa_fog_share_2020,
            biofuel_hefa_fog_share_2030,
            biofuel_hefa_fog_share_2040,
            biofuel_hefa_fog_share_2050,
        ]
        biofuel_hefa_fog_share_function = interp1d(
            reference_years, reference_values_hefa_fog, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "biofuel_hefa_fog_share"] = biofuel_hefa_fog_share_function(k)

        # HEFA OTHERS
        reference_values_hefa_others = [
            biofuel_hefa_others_share_2020,
            biofuel_hefa_others_share_2030,
            biofuel_hefa_others_share_2040,
            biofuel_hefa_others_share_2050,
        ]
        biofuel_hefa_others_share_function = interp1d(
            reference_years, reference_values_hefa_others, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "biofuel_hefa_others_share"] = biofuel_hefa_others_share_function(k)

        # FT OTHERS
        reference_values_ft_others = [
            biofuel_ft_others_share_2020,
            biofuel_ft_others_share_2030,
            biofuel_ft_others_share_2040,
            biofuel_ft_others_share_2050,
        ]
        biofuel_ft_others_share_function = interp1d(
            reference_years, reference_values_ft_others, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "biofuel_ft_others_share"] = biofuel_ft_others_share_function(k)

        # FT MSW
        reference_values_ft_msw = [
            biofuel_ft_msw_share_2020,
            biofuel_ft_msw_share_2030,
            biofuel_ft_msw_share_2040,
            biofuel_ft_msw_share_2050,
        ]
        biofuel_ft_msw_share_function = interp1d(
            reference_years, reference_values_ft_msw, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "biofuel_ft_msw_share"] = biofuel_ft_msw_share_function(k)

        biofuel_hefa_fog_share = self.df["biofuel_hefa_fog_share"]
        biofuel_hefa_others_share = self.df["biofuel_hefa_others_share"]
        biofuel_ft_others_share = self.df["biofuel_ft_others_share"]
        biofuel_ft_msw_share = self.df["biofuel_ft_msw_share"]

        # ATJ
        biofuel_atj_share = (
            100
            - biofuel_hefa_fog_share
            - biofuel_hefa_others_share
            - biofuel_ft_others_share
            - biofuel_ft_msw_share
        )
        self.df.loc[:, "biofuel_atj_share"] = biofuel_atj_share

        return (
            biofuel_hefa_fog_share,
            biofuel_hefa_others_share,
            biofuel_ft_others_share,
            biofuel_ft_msw_share,
            biofuel_atj_share,
        )


class HydrogenProduction(AeromapsModel):
    def __init__(self, name="hydrogen_production", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        hydrogen_electrolysis_share_2020: float = 0.0,
        hydrogen_electrolysis_share_2030: float = 0.0,
        hydrogen_electrolysis_share_2040: float = 0.0,
        hydrogen_electrolysis_share_2050: float = 0.0,
        hydrogen_gas_ccs_share_2020: float = 0.0,
        hydrogen_gas_ccs_share_2030: float = 0.0,
        hydrogen_gas_ccs_share_2040: float = 0.0,
        hydrogen_gas_ccs_share_2050: float = 0.0,
        hydrogen_coal_ccs_share_2020: float = 0.0,
        hydrogen_coal_ccs_share_2030: float = 0.0,
        hydrogen_coal_ccs_share_2040: float = 0.0,
        hydrogen_coal_ccs_share_2050: float = 0.0,
        hydrogen_gas_share_2020: float = 0.0,
        hydrogen_gas_share_2030: float = 0.0,
        hydrogen_gas_share_2040: float = 0.0,
        hydrogen_gas_share_2050: float = 0.0,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Hydrogen production calculation using interpolation functions"""

        reference_years = [2020, 2030, 2040, 2050]

        # Electrolysis
        reference_values_electrolysis = [
            hydrogen_electrolysis_share_2020,
            hydrogen_electrolysis_share_2030,
            hydrogen_electrolysis_share_2040,
            hydrogen_electrolysis_share_2050,
        ]
        hydrogen_electrolysis_share_function = interp1d(
            reference_years, reference_values_electrolysis, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "hydrogen_electrolysis_share"] = hydrogen_electrolysis_share_function(k)

        # Gas CCS
        reference_values_gas_ccs = [
            hydrogen_gas_ccs_share_2020,
            hydrogen_gas_ccs_share_2030,
            hydrogen_gas_ccs_share_2040,
            hydrogen_gas_ccs_share_2050,
        ]
        hydrogen_gas_ccs_share_function = interp1d(
            reference_years, reference_values_gas_ccs, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "hydrogen_gas_ccs_share"] = hydrogen_gas_ccs_share_function(k)

        # Coal CCS
        reference_values_coal_ccs = [
            hydrogen_coal_ccs_share_2020,
            hydrogen_coal_ccs_share_2030,
            hydrogen_coal_ccs_share_2040,
            hydrogen_coal_ccs_share_2050,
        ]
        hydrogen_coal_ccs_share_function = interp1d(
            reference_years, reference_values_coal_ccs, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "hydrogen_coal_ccs_share"] = hydrogen_coal_ccs_share_function(k)

        # Gas
        reference_values_gas = [
            hydrogen_gas_share_2020,
            hydrogen_gas_share_2030,
            hydrogen_gas_share_2040,
            hydrogen_gas_share_2050,
        ]
        hydrogen_gas_share_function = interp1d(reference_years, reference_values_gas, kind="linear")
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "hydrogen_gas_share"] = hydrogen_gas_share_function(k)

        hydrogen_electrolysis_share = self.df["hydrogen_electrolysis_share"]
        hydrogen_gas_ccs_share = self.df["hydrogen_gas_ccs_share"]
        hydrogen_coal_ccs_share = self.df["hydrogen_coal_ccs_share"]
        hydrogen_gas_share = self.df["hydrogen_gas_share"]

        # Coal
        hydrogen_coal_share = (
            100
            - hydrogen_electrolysis_share
            - hydrogen_gas_ccs_share
            - hydrogen_coal_ccs_share
            - hydrogen_gas_share
        )
        self.df.loc[:, "hydrogen_coal_share"] = hydrogen_coal_share

        return (
            hydrogen_electrolysis_share,
            hydrogen_gas_ccs_share,
            hydrogen_coal_ccs_share,
            hydrogen_gas_share,
            hydrogen_coal_share,
        )

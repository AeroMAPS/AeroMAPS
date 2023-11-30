from typing import Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeromapsModel, InterpolationAeromapsFunction


class BiofuelProduction(AeromapsModel):
    def __init__(self, name="biofuel_production", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        biofuel_hefa_fog_share_reference_years: list = [],
        biofuel_hefa_fog_share_reference_years_values: list = [],
        biofuel_hefa_others_share_reference_years: list = [],
        biofuel_hefa_others_share_reference_years_values: list = [],
        biofuel_ft_others_share_reference_years: list = [],
        biofuel_ft_others_share_reference_years_values: list = [],
        biofuel_ft_msw_share_reference_years: list = [],
        biofuel_ft_msw_share_reference_years_values: list = [],
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Biomass production calculation using interpolation functions"""

        # HEFA FOG
        biofuel_hefa_fog_share = InterpolationAeromapsFunction(
            self, biofuel_hefa_fog_share_reference_years, biofuel_hefa_fog_share_reference_years_values
        )
        self.df.loc[:, "biofuel_hefa_fog_share"] = biofuel_hefa_fog_share

        # HEFA OTHERS
        biofuel_hefa_others_share = InterpolationAeromapsFunction(
            self, biofuel_hefa_others_share_reference_years, biofuel_hefa_others_share_reference_years_values
        )
        self.df.loc[:, "biofuel_hefa_others_share"] = biofuel_hefa_others_share

        # FT OTHERS
        biofuel_ft_others_share = InterpolationAeromapsFunction(
            self, biofuel_ft_others_share_reference_years, biofuel_ft_others_share_reference_years_values
        )
        self.df.loc[:, "biofuel_ft_others_share"] = biofuel_ft_others_share

        # FT MSW
        biofuel_ft_msw_share = InterpolationAeromapsFunction(
            self, biofuel_ft_msw_share_reference_years, biofuel_ft_msw_share_reference_years_values
        )
        self.df.loc[:, "biofuel_ft_msw_share"] = biofuel_ft_msw_share

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
        hydrogen_electrolysis_share_reference_years: list = [],
        hydrogen_electrolysis_share_reference_years_values: list = [],
        hydrogen_gas_ccs_share_reference_years: list = [],
        hydrogen_gas_ccs_share_reference_years_values: list = [],
        hydrogen_coal_ccs_share_reference_years: list = [],
        hydrogen_coal_ccs_share_reference_years_values: list = [],
        hydrogen_gas_share_reference_years: list = [],
        hydrogen_gas_share_reference_years_values: list = [],
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Hydrogen production calculation using interpolation functions"""

        # Electrolysis
        hydrogen_electrolysis_share = InterpolationAeromapsFunction(
            self, hydrogen_electrolysis_share_reference_years, hydrogen_electrolysis_share_reference_years_values
        )
        self.df.loc[:, "hydrogen_electrolysis_share"] = hydrogen_electrolysis_share

        # Gas CCS
        hydrogen_gas_ccs_share = InterpolationAeromapsFunction(
            self, hydrogen_gas_ccs_share_reference_years, hydrogen_gas_ccs_share_reference_years_values
        )
        self.df.loc[:, "hydrogen_gas_ccs_share"] = hydrogen_gas_ccs_share

        # Coal CCS
        hydrogen_coal_ccs_share = InterpolationAeromapsFunction(
            self, hydrogen_coal_ccs_share_reference_years, hydrogen_coal_ccs_share_reference_years_values
        )
        self.df.loc[:, "hydrogen_coal_ccs_share"] = hydrogen_coal_ccs_share

        # Gas
        hydrogen_gas_share = InterpolationAeromapsFunction(
            self, hydrogen_gas_share_reference_years, hydrogen_gas_share_reference_years_values
        )
        self.df.loc[:, "hydrogen_gas_share"] = hydrogen_gas_share

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

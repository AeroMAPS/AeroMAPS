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
        if len(biofuel_hefa_fog_share_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "biofuel_hefa_fog_share"
                ] = biofuel_hefa_fog_share_reference_years_values
        else:
            biofuel_hefa_fog_share_function = interp1d(
                biofuel_hefa_fog_share_reference_years,
                biofuel_hefa_fog_share_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "biofuel_hefa_fog_share"] = biofuel_hefa_fog_share_function(k)

        # HEFA OTHERS
        if len(biofuel_hefa_others_share_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "biofuel_hefa_others_share"
                ] = biofuel_hefa_others_share_reference_years_values
        else:
            biofuel_hefa_others_share_function = interp1d(
                biofuel_hefa_others_share_reference_years,
                biofuel_hefa_others_share_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "biofuel_hefa_others_share"] = biofuel_hefa_others_share_function(k)

        # FT OTHERS
        if len(biofuel_ft_others_share_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "biofuel_ft_others_share"
                ] = biofuel_ft_others_share_reference_years_values
        else:
            biofuel_ft_others_share_function = interp1d(
                biofuel_ft_others_share_reference_years,
                biofuel_ft_others_share_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "biofuel_ft_others_share"] = biofuel_ft_others_share_function(k)

        # FT MSW
        if len(biofuel_ft_msw_share_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "biofuel_ft_msw_share"] = biofuel_ft_msw_share_reference_years_values
        else:
            biofuel_ft_msw_share_function = interp1d(
                biofuel_ft_msw_share_reference_years,
                biofuel_ft_msw_share_reference_years_values,
                kind="linear",
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
        if len(hydrogen_electrolysis_share_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "hydrogen_electrolysis_share"
                ] = hydrogen_electrolysis_share_reference_years_values
        else:
            hydrogen_electrolysis_share_function = interp1d(
                hydrogen_electrolysis_share_reference_years,
                hydrogen_electrolysis_share_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "hydrogen_electrolysis_share"
                ] = hydrogen_electrolysis_share_function(k)

        # Gas CCS
        if len(hydrogen_gas_ccs_share_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "hydrogen_gas_ccs_share"
                ] = hydrogen_gas_ccs_share_reference_years_values
        else:
            hydrogen_gas_ccs_share_function = interp1d(
                hydrogen_gas_ccs_share_reference_years,
                hydrogen_gas_ccs_share_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "hydrogen_gas_ccs_share"] = hydrogen_gas_ccs_share_function(k)

        # Coal CCS
        if len(hydrogen_coal_ccs_share_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[
                    k, "hydrogen_coal_ccs_share"
                ] = hydrogen_coal_ccs_share_reference_years_values
        else:
            hydrogen_coal_ccs_share_function = interp1d(
                hydrogen_coal_ccs_share_reference_years,
                hydrogen_coal_ccs_share_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "hydrogen_coal_ccs_share"] = hydrogen_coal_ccs_share_function(k)

        # Gas
        if len(hydrogen_gas_share_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "hydrogen_gas_share"] = hydrogen_gas_share_reference_years_values
        else:
            hydrogen_gas_share_function = interp1d(
                hydrogen_gas_share_reference_years,
                hydrogen_gas_share_reference_years_values,
                kind="linear",
            )
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

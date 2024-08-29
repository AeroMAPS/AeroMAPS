# @Time : 22/02/2023 16:01
# @Author : a.salgas
# @File : biofuel.py
# @Software: PyCharm
from typing import Tuple

import pandas as pd
from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class BiofuelCostSimple(AeroMAPSModel):
    def __init__(self, name="biofuel_cost_simple", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_biofuel: pd.Series,
        biofuel_hefa_fog_emission_factor: pd.Series,
        biofuel_hefa_others_emission_factor: pd.Series,
        biofuel_atj_emission_factor: pd.Series,
        biofuel_ft_msw_emission_factor: pd.Series,
        biofuel_ft_others_emission_factor: pd.Series,
        biofuel_hefa_fog_share: pd.Series,
        biofuel_hefa_others_share: pd.Series,
        biofuel_atj_share: pd.Series,
        biofuel_ft_msw_share: pd.Series,
        biofuel_ft_others_share: pd.Series,
        biofuel_hefa_fog_mfsp: pd.Series,
        biofuel_hefa_others_mfsp: pd.Series,
        biofuel_ft_others_mfsp: pd.Series,
        biofuel_ft_msw_mfsp: pd.Series,
        biofuel_atj_mfsp: pd.Series,
        carbon_tax: pd.Series,
        lhv_biofuel: float,
        density_biofuel: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        ### HEFA FOG

        biofuel_cost_hefa_fog = (
            biofuel_hefa_fog_mfsp
            / density_biofuel
            / lhv_biofuel
            * energy_consumption_biofuel
            * biofuel_hefa_fog_share
            / 100
            / 1e6
        )
        self.df.loc[:, "biofuel_cost_hefa_fog"] = biofuel_cost_hefa_fog

        biofuel_carbon_tax_hefa_fog = (
            energy_consumption_biofuel
            * biofuel_hefa_fog_share
            / 100
            * biofuel_hefa_fog_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        self.df.loc[:, "biofuel_carbon_tax_hefa_fog"] = biofuel_carbon_tax_hefa_fog

        biofuel_mfsp_carbon_tax_supplement_hefa_fog = (
            carbon_tax * biofuel_hefa_fog_emission_factor / 1000000 * lhv_biofuel * density_biofuel
        )
        self.df.loc[:, "biofuel_mfsp_carbon_tax_supplement_hefa_fog"] = (
            biofuel_mfsp_carbon_tax_supplement_hefa_fog
        )

        ### HEFA OTHERS
        biofuel_cost_hefa_others = (
            biofuel_hefa_others_mfsp
            / density_biofuel
            / lhv_biofuel
            * energy_consumption_biofuel
            * biofuel_hefa_others_share
            / 100
            / 1e6
        )
        self.df.loc[:, "biofuel_cost_hefa_others"] = biofuel_cost_hefa_others

        biofuel_carbon_tax_hefa_others = (
            energy_consumption_biofuel
            * biofuel_hefa_others_share
            / 100
            * biofuel_hefa_others_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        self.df.loc[:, "biofuel_carbon_tax_hefa_others"] = biofuel_carbon_tax_hefa_others

        biofuel_mfsp_carbon_tax_supplement_hefa_others = (
            carbon_tax
            * biofuel_hefa_others_emission_factor
            / 1000000
            * lhv_biofuel
            * density_biofuel
        )
        self.df.loc[:, "biofuel_mfsp_carbon_tax_supplement_hefa_others"] = (
            biofuel_mfsp_carbon_tax_supplement_hefa_others
        )

        ### FT OTHERS
        biofuel_cost_ft_others = (
            biofuel_ft_others_mfsp
            / density_biofuel
            / lhv_biofuel
            * energy_consumption_biofuel
            * biofuel_ft_others_share
            / 100
            / 1e6
        )
        self.df.loc[:, "biofuel_cost_ft_others"] = biofuel_cost_ft_others

        biofuel_carbon_tax_ft_others = (
            energy_consumption_biofuel
            * biofuel_ft_others_share
            / 100
            * biofuel_ft_others_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        self.df.loc[:, "biofuel_carbon_tax_ft_others"] = biofuel_carbon_tax_ft_others

        biofuel_mfsp_carbon_tax_supplement_ft_others = (
            carbon_tax * biofuel_ft_others_emission_factor / 1000000 * lhv_biofuel * density_biofuel
        )
        self.df.loc[:, "biofuel_mfsp_carbon_tax_supplement_ft_others"] = (
            biofuel_mfsp_carbon_tax_supplement_ft_others
        )

        ### FT MSW
        biofuel_cost_ft_msw = (
            biofuel_ft_msw_mfsp
            / density_biofuel
            / lhv_biofuel
            * energy_consumption_biofuel
            * biofuel_ft_msw_share
            / 100
            / 1e6
        )
        self.df.loc[:, "biofuel_cost_ft_msw"] = biofuel_cost_ft_msw

        biofuel_carbon_tax_ft_msw = (
            energy_consumption_biofuel
            * biofuel_ft_msw_share
            / 100
            * biofuel_ft_msw_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        self.df.loc[:, "biofuel_carbon_tax_ft_msw"] = biofuel_carbon_tax_ft_msw

        biofuel_mfsp_carbon_tax_supplement_ft_msw = (
            carbon_tax * biofuel_ft_msw_emission_factor / 1000000 * lhv_biofuel * density_biofuel
        )
        self.df.loc[:, "biofuel_mfsp_carbon_tax_supplement_ft_msw"] = (
            biofuel_mfsp_carbon_tax_supplement_ft_msw
        )

        ### ATJ
        biofuel_cost_atj = (
            biofuel_atj_mfsp
            / density_biofuel
            / lhv_biofuel
            * energy_consumption_biofuel
            * biofuel_atj_share
            / 100
            / 1e6
        )
        self.df.loc[:, "biofuel_cost_atj"] = biofuel_cost_atj

        biofuel_carbon_tax_atj = (
            energy_consumption_biofuel
            * biofuel_atj_share
            / 100
            * biofuel_atj_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        self.df.loc[:, "biofuel_carbon_tax_atj"] = biofuel_carbon_tax_atj

        biofuel_mfsp_carbon_tax_supplement_atj = (
            carbon_tax * biofuel_atj_emission_factor / 1000000 * lhv_biofuel * density_biofuel
        )
        self.df.loc[:, "biofuel_mfsp_carbon_tax_supplement_atj"] = (
            biofuel_mfsp_carbon_tax_supplement_atj
        )

        # MEAN tax
        biofuel_mean_carbon_tax_per_l = (
            biofuel_mfsp_carbon_tax_supplement_hefa_fog.fillna(0)
            * biofuel_hefa_fog_share.fillna(0)
            / 100
            + biofuel_mfsp_carbon_tax_supplement_hefa_others.fillna(0)
            * biofuel_hefa_others_share.fillna(0)
            / 100
            + biofuel_mfsp_carbon_tax_supplement_ft_others.fillna(0)
            * biofuel_ft_others_share.fillna(0)
            / 100
            + biofuel_mfsp_carbon_tax_supplement_ft_msw.fillna(0)
            * biofuel_ft_msw_share.fillna(0)
            / 100
            + biofuel_mfsp_carbon_tax_supplement_atj.fillna(0) * biofuel_atj_share.fillna(0) / 100
        )

        self.df.loc[:, "biofuel_mean_carbon_tax_per_l"] = biofuel_mean_carbon_tax_per_l

        return (
            biofuel_cost_hefa_fog,
            biofuel_carbon_tax_hefa_fog,
            biofuel_mfsp_carbon_tax_supplement_hefa_fog,
            biofuel_cost_hefa_others,
            biofuel_carbon_tax_hefa_others,
            biofuel_mfsp_carbon_tax_supplement_hefa_others,
            biofuel_cost_ft_others,
            biofuel_carbon_tax_ft_others,
            biofuel_mfsp_carbon_tax_supplement_ft_others,
            biofuel_cost_ft_msw,
            biofuel_carbon_tax_ft_msw,
            biofuel_mfsp_carbon_tax_supplement_ft_msw,
            biofuel_cost_atj,
            biofuel_carbon_tax_atj,
            biofuel_mfsp_carbon_tax_supplement_atj,
            biofuel_mean_carbon_tax_per_l,
        )


class BiofuelMfspSimple(AeroMAPSModel):
    def __init__(self, name="biofuel_mfsp_simple", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        biofuel_hefa_fog_mfsp_simple_reference_years: list,
        biofuel_hefa_fog_mfsp_simple_reference_years_values: list,
        biofuel_hefa_others_mfsp_simple_reference_years: list,
        biofuel_hefa_others_mfsp_simple_reference_years_values: list,
        biofuel_ft_others_mfsp_simple_reference_years: list,
        biofuel_ft_others_mfsp_simple_reference_years_values: list,
        biofuel_ft_msw_mfsp_simple_reference_years: list,
        biofuel_ft_msw_mfsp_simple_reference_years_values: list,
        biofuel_atj_mfsp_simple_reference_years: list,
        biofuel_atj_mfsp_simple_reference_years_values: list,
        biofuel_hefa_fog_share: pd.Series,
        biofuel_hefa_others_share: pd.Series,
        biofuel_ft_others_share: pd.Series,
        biofuel_ft_msw_share: pd.Series,
        biofuel_atj_share: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Biofuel MFSP (Minimal fuel selling price) estimates"""

        # HEFA FOG
        biofuel_hefa_fog_mfsp = AeromapsInterpolationFunction(
            self,
            biofuel_hefa_fog_mfsp_simple_reference_years,
            biofuel_hefa_fog_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_hefa_fog_mfsp"] = biofuel_hefa_fog_mfsp

        # HEFA OTHERS
        biofuel_hefa_others_mfsp = AeromapsInterpolationFunction(
            self,
            biofuel_hefa_others_mfsp_simple_reference_years,
            biofuel_hefa_others_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_hefa_others_mfsp"] = biofuel_hefa_others_mfsp

        # FT OTHERS
        biofuel_ft_others_mfsp = AeromapsInterpolationFunction(
            self,
            biofuel_ft_others_mfsp_simple_reference_years,
            biofuel_ft_others_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_ft_others_mfsp"] = biofuel_ft_others_mfsp

        # FT MSW
        biofuel_ft_msw_mfsp = AeromapsInterpolationFunction(
            self,
            biofuel_ft_msw_mfsp_simple_reference_years,
            biofuel_ft_msw_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_ft_msw_mfsp"] = biofuel_ft_msw_mfsp

        # ATJ
        biofuel_atj_mfsp = AeromapsInterpolationFunction(
            self,
            biofuel_atj_mfsp_simple_reference_years,
            biofuel_atj_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_atj_mfsp"] = biofuel_atj_mfsp

        # MEAN
        biofuel_mean_mfsp = (
            biofuel_hefa_fog_mfsp * biofuel_hefa_fog_share / 100
            + biofuel_hefa_others_mfsp * biofuel_hefa_others_share / 100
            + biofuel_ft_others_mfsp * biofuel_ft_others_share / 100
            + biofuel_ft_msw_mfsp * biofuel_ft_msw_share / 100
            + biofuel_atj_mfsp * biofuel_atj_share / 100
        )

        self.df.loc[:, "biofuel_mean_mfsp"] = biofuel_mean_mfsp

        # MARGINAL

        biofuel_marginal_mfsp = self.df.loc[
            :,
            [
                "biofuel_hefa_fog_mfsp",
                "biofuel_hefa_others_mfsp",
                "biofuel_ft_others_mfsp",
                "biofuel_ft_msw_mfsp",
                "biofuel_atj_mfsp",
            ],
        ].max(axis="columns")

        self.df.loc[:, "biofuel_marginal_mfsp"] = biofuel_marginal_mfsp

        return (
            biofuel_hefa_fog_mfsp,
            biofuel_hefa_others_mfsp,
            biofuel_ft_others_mfsp,
            biofuel_ft_msw_mfsp,
            biofuel_atj_mfsp,
            biofuel_mean_mfsp,
            biofuel_marginal_mfsp,
        )

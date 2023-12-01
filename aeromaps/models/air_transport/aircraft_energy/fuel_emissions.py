from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeromapsModel, AeromapsInterpolationFunction


class BiofuelEmissionFactor(AeromapsModel):
    def __init__(self, name="biofuel_emission_factor", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        biofuel_hefa_fog_emission_factor_reference_years: list = [],
        biofuel_hefa_fog_emission_factor_reference_years_values: list = [],
        biofuel_hefa_others_emission_factor_reference_years: list = [],
        biofuel_hefa_others_emission_factor_reference_years_values: list = [],
        biofuel_ft_others_emission_factor_reference_years: list = [],
        biofuel_ft_others_emission_factor_reference_years_values: list = [],
        biofuel_ft_msw_emission_factor_reference_years: list = [],
        biofuel_ft_msw_emission_factor_reference_years_values: list = [],
        biofuel_atj_emission_factor_reference_years: list = [],
        biofuel_atj_emission_factor_reference_years_values: list = [],
        biofuel_hefa_fog_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_share: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Biofuel CO2 emission factor calculation using interpolation functions"""

        # HEFA FOG
        biofuel_hefa_fog_emission_factor = AeromapsInterpolationFunction(
            self,
            biofuel_hefa_fog_emission_factor_reference_years,
            biofuel_hefa_fog_emission_factor_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_hefa_fog_emission_factor"] = biofuel_hefa_fog_emission_factor

        # HEFA OTHERS
        biofuel_hefa_others_emission_factor = AeromapsInterpolationFunction(
            self,
            biofuel_hefa_others_emission_factor_reference_years,
            biofuel_hefa_others_emission_factor_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_hefa_others_emission_factor"] = biofuel_hefa_others_emission_factor

        # FT OTHERS
        biofuel_ft_others_emission_factor = AeromapsInterpolationFunction(
            self,
            biofuel_ft_others_emission_factor_reference_years,
            biofuel_ft_others_emission_factor_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_ft_others_emission_factor"] = biofuel_ft_others_emission_factor

        # FT MSW
        biofuel_ft_msw_emission_factor = AeromapsInterpolationFunction(
            self,
            biofuel_ft_msw_emission_factor_reference_years,
            biofuel_ft_msw_emission_factor_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_ft_msw_emission_factor"] = biofuel_ft_msw_emission_factor

        # ATJ
        biofuel_atj_emission_factor = AeromapsInterpolationFunction(
            self,
            biofuel_atj_emission_factor_reference_years,
            biofuel_atj_emission_factor_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_atj_emission_factor"] = biofuel_atj_emission_factor

        # MEAN
        biofuel_mean_emission_factor = (
            biofuel_hefa_fog_emission_factor * biofuel_hefa_fog_share / 100
            + biofuel_hefa_others_emission_factor * biofuel_hefa_others_share / 100
            + biofuel_ft_others_emission_factor * biofuel_ft_others_share / 100
            + biofuel_ft_msw_emission_factor * biofuel_ft_msw_share / 100
            + biofuel_atj_emission_factor * biofuel_atj_share / 100
        )

        self.df.loc[:, "biofuel_mean_emission_factor"] = biofuel_mean_emission_factor

        return (
            biofuel_hefa_fog_emission_factor,
            biofuel_hefa_others_emission_factor,
            biofuel_ft_others_emission_factor,
            biofuel_ft_msw_emission_factor,
            biofuel_atj_emission_factor,
            biofuel_mean_emission_factor,
        )


class ElectricityEmissionFactor(AeromapsModel):
    def __init__(self, name="electricity_emission_factor", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        electricity_emission_factor_reference_years: list = [],
        electricity_emission_factor_reference_years_values: list = [],
    ) -> pd.Series:
        """Electricity CO2 emission factor calculation using interpolation function."""

        electricity_emission_factor = AeromapsInterpolationFunction(
            self,
            electricity_emission_factor_reference_years,
            electricity_emission_factor_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electricity_emission_factor"] = electricity_emission_factor

        return electricity_emission_factor


class HydrogenEmissionFactor(AeromapsModel):
    def __init__(self, name="hydrogen_emission_factor", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        electricity_emission_factor: pd.Series = pd.Series(dtype="float64"),
        electrolysis_efficiency: pd.Series = pd.Series(dtype="float64"),
        liquefaction_efficiency: pd.Series = pd.Series(dtype="float64"),
        hydrogen_gas_ccs_emission_factor: float = 0.0,
        hydrogen_coal_ccs_emission_factor: float = 0.0,
        hydrogen_gas_emission_factor: float = 0.0,
        hydrogen_coal_emission_factor: float = 0.0,
        hydrogen_electrolysis_share: pd.Series = pd.Series(dtype="float64"),
        hydrogen_gas_ccs_share: pd.Series = pd.Series(dtype="float64"),
        hydrogen_coal_ccs_share: pd.Series = pd.Series(dtype="float64"),
        hydrogen_gas_share: pd.Series = pd.Series(dtype="float64"),
        hydrogen_coal_share: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series]:
        """Hydrogen CO2 emission factor calculation."""

        hydrogen_electrolysis_emission_factor = (
            electricity_emission_factor / 3.6 / electrolysis_efficiency / liquefaction_efficiency
        )

        hydrogen_mean_emission_factor = (
            hydrogen_electrolysis_emission_factor * hydrogen_electrolysis_share / 100
            + hydrogen_gas_ccs_emission_factor * hydrogen_gas_ccs_share / 100
            + hydrogen_coal_ccs_emission_factor * hydrogen_coal_ccs_share / 100
            + hydrogen_gas_emission_factor * hydrogen_gas_share / 100
            + hydrogen_coal_emission_factor * hydrogen_coal_share / 100
        )

        self.df.loc[
            :, "hydrogen_electrolysis_emission_factor"
        ] = hydrogen_electrolysis_emission_factor
        self.df.loc[:, "hydrogen_mean_emission_factor"] = hydrogen_mean_emission_factor

        return hydrogen_electrolysis_emission_factor, hydrogen_mean_emission_factor


class ElectrofuelEmissionFactor(AeromapsModel):
    def __init__(self, name="electrofuel_emission_factor", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        electricity_emission_factor: pd.Series = pd.Series(dtype="float64"),
        electrolysis_efficiency: pd.Series = pd.Series(dtype="float64"),
        electrofuel_hydrogen_efficiency: pd.Series = pd.Series(dtype="float64"),
    ) -> pd.Series:
        """Electrofuel CO2 emission factor calculation."""

        electrofuel_emission_factor = (
            electricity_emission_factor
            / 3.6
            / electrolysis_efficiency
            / electrofuel_hydrogen_efficiency
        )

        self.df.loc[:, "electrofuel_emission_factor"] = electrofuel_emission_factor

        return electrofuel_emission_factor


class KeroseneEmissionFactor(AeromapsModel):
    def __init__(self, name="kerosene_emission_factor", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        kerosene_emission_factor_reference_years: list = [],
        kerosene_emission_factor_reference_years_values: list = [],
    ) -> pd.Series:
        """Kerosene CO2 emission factor calculation."""

        kerosene_emission_factor_prospective = AeromapsInterpolationFunction(
            self,
            kerosene_emission_factor_reference_years,
            kerosene_emission_factor_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "kerosene_emission_factor"] = kerosene_emission_factor_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "kerosene_emission_factor"] = self.df.loc[
                self.prospection_start_year, "kerosene_emission_factor"
            ]
        kerosene_emission_factor = self.df["kerosene_emission_factor"]

        return kerosene_emission_factor

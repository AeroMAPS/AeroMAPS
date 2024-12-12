from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class BiofuelEmissionFactor(AeroMAPSModel):
    def __init__(self, name="biofuel_emission_factor", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        biofuel_hefa_fog_emission_factor_reference_years: list,
        biofuel_hefa_fog_emission_factor_reference_years_values: list,
        biofuel_hefa_others_emission_factor_reference_years: list,
        biofuel_hefa_others_emission_factor_reference_years_values: list,
        biofuel_ft_others_emission_factor_reference_years: list,
        biofuel_ft_others_emission_factor_reference_years_values: list,
        biofuel_ft_msw_emission_factor_reference_years: list,
        biofuel_ft_msw_emission_factor_reference_years_values: list,
        biofuel_atj_emission_factor_reference_years: list,
        biofuel_atj_emission_factor_reference_years_values: list,
        biofuel_hefa_fog_share: pd.Series,
        biofuel_hefa_others_share: pd.Series,
        biofuel_ft_others_share: pd.Series,
        biofuel_ft_msw_share: pd.Series,
        biofuel_atj_share: pd.Series,
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


class ElectricityEmissionFactor(AeroMAPSModel):
    def __init__(self, name="electricity_emission_factor", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        electricity_emission_factor_reference_years: list,
        electricity_emission_factor_reference_years_values: list,
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


class HydrogenEmissionFactor(AeroMAPSModel):
    def __init__(self, name="hydrogen_emission_factor", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        electricity_emission_factor: pd.Series,
        electrolysis_efficiency: pd.Series,
        liquefaction_efficiency: pd.Series,
        gaseous_hydrogen_gas_ccs_emission_factor: float,
        gaseous_hydrogen_coal_ccs_emission_factor: float,
        gaseous_hydrogen_gas_emission_factor: float,
        gaseous_hydrogen_coal_emission_factor: float,
        hydrogen_electrolysis_share: pd.Series,
        hydrogen_gas_ccs_share: pd.Series,
        hydrogen_coal_ccs_share: pd.Series,
        hydrogen_gas_share: pd.Series,
        hydrogen_coal_share: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Hydrogen CO2 emission factor calculation."""

        liquid_hydrogen_electrolysis_emission_factor = (
            electricity_emission_factor / 3.6 / electrolysis_efficiency / liquefaction_efficiency
        )

        liquefaction_hydrogen_non_electrolysis_emission_factor = (
            electricity_emission_factor / 3.6 * (1 / liquefaction_efficiency - 1)
        )

        liquid_hydrogen_gas_ccs_emission_factor = (
            gaseous_hydrogen_gas_ccs_emission_factor
            + liquefaction_hydrogen_non_electrolysis_emission_factor
        )
        liquid_hydrogen_coal_ccs_emission_factor = (
            gaseous_hydrogen_coal_ccs_emission_factor
            + liquefaction_hydrogen_non_electrolysis_emission_factor
        )
        liquid_hydrogen_gas_emission_factor = (
            gaseous_hydrogen_gas_emission_factor
            + liquefaction_hydrogen_non_electrolysis_emission_factor
        )
        liquid_hydrogen_coal_emission_factor = (
            gaseous_hydrogen_coal_emission_factor
            + liquefaction_hydrogen_non_electrolysis_emission_factor
        )

        liquid_hydrogen_mean_emission_factor = (
            liquid_hydrogen_electrolysis_emission_factor * hydrogen_electrolysis_share / 100
            + liquid_hydrogen_gas_ccs_emission_factor * hydrogen_gas_ccs_share / 100
            + liquid_hydrogen_coal_ccs_emission_factor * hydrogen_coal_ccs_share / 100
            + liquid_hydrogen_gas_emission_factor * hydrogen_gas_share / 100
            + liquid_hydrogen_coal_emission_factor * hydrogen_coal_share / 100
        )

        self.df.loc[:, "liquid_hydrogen_electrolysis_emission_factor"] = (
            liquid_hydrogen_electrolysis_emission_factor
        )
        self.df.loc[:, "liquid_hydrogen_gas_ccs_emission_factor"] = (
            liquid_hydrogen_gas_ccs_emission_factor
        )
        self.df.loc[:, "liquid_hydrogen_coal_ccs_emission_factor"] = (
            liquid_hydrogen_coal_ccs_emission_factor
        )
        self.df.loc[:, "liquid_hydrogen_gas_emission_factor"] = liquid_hydrogen_gas_emission_factor
        self.df.loc[:, "liquid_hydrogen_coal_emission_factor"] = (
            liquid_hydrogen_coal_emission_factor
        )
        self.df.loc[:, "liquid_hydrogen_mean_emission_factor"] = (
            liquid_hydrogen_mean_emission_factor
        )

        return (
            liquid_hydrogen_electrolysis_emission_factor,
            liquid_hydrogen_gas_ccs_emission_factor,
            liquid_hydrogen_coal_ccs_emission_factor,
            liquid_hydrogen_gas_emission_factor,
            liquid_hydrogen_coal_emission_factor,
            liquid_hydrogen_mean_emission_factor,
        )


class ElectrofuelEmissionFactor(AeroMAPSModel):
    def __init__(self, name="electrofuel_emission_factor", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        electricity_emission_factor: pd.Series,
        electrolysis_efficiency: pd.Series,
        electrofuel_hydrogen_efficiency: pd.Series,
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


class KeroseneEmissionFactor(AeroMAPSModel):
    def __init__(self, name="kerosene_emission_factor", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        kerosene_emission_factor_reference_years: list,
        kerosene_emission_factor_reference_years_values: list,
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

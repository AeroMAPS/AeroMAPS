from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel


class BiomassConsumption(AeromapsModel):
    def __init__(self, name="biomass_consumption", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_biofuel: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fog_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_efficiency: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_efficiency: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_oil_efficiency: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fuel_efficiency: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, float]:
        """Biomass consumption calculation."""

        biomass_ft_consumption = (
            (biofuel_ft_others_share + biofuel_ft_msw_share)
            / 100
            * energy_consumption_biofuel
            / 10**12
            / biofuel_ft_efficiency
        )
        biomass_atj_consumption = (
            biofuel_atj_share / 100 * energy_consumption_biofuel / 10**12 / biofuel_atj_efficiency
        )
        biomass_hefa_fog_consumption = (
            biofuel_hefa_fog_share
            / 100
            * energy_consumption_biofuel
            / 10**12
            / biofuel_hefa_fuel_efficiency
        )
        biomass_hefa_others_consumption = (
            biofuel_hefa_others_share
            / 100
            * energy_consumption_biofuel
            / 10**12
            / biofuel_hefa_fuel_efficiency
            / biofuel_hefa_oil_efficiency
        )
        biomass_consumption = (
            biomass_ft_consumption
            + biomass_atj_consumption
            + biomass_hefa_fog_consumption
            + biomass_hefa_others_consumption
        )

        self.df.loc[:, "biomass_ft_consumption"] = biomass_ft_consumption
        self.df.loc[:, "biomass_atj_consumption"] = biomass_atj_consumption
        self.df.loc[:, "biomass_hefa_fog_consumption"] = biomass_hefa_fog_consumption
        self.df.loc[:, "biomass_hefa_others_consumption"] = biomass_hefa_others_consumption
        self.df.loc[:, "biomass_consumption"] = biomass_consumption

        biomass_consumption_end_year = self.df.loc[self.end_year, "biomass_consumption"]

        self.float_outputs["biomass_consumption_end_year"] = biomass_consumption_end_year

        return (
            biomass_ft_consumption,
            biomass_atj_consumption,
            biomass_hefa_fog_consumption,
            biomass_hefa_others_consumption,
            biomass_consumption,
            biomass_consumption_end_year,
        )


class ElectricityConsumption(AeromapsModel):
    def __init__(self, name="electricity_consumption", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        hydrogen_electrolysis_share: pd.Series = pd.Series(dtype="float64"),
        energy_consumption_hydrogen: pd.Series = pd.Series(dtype="float64"),
        energy_consumption_electrofuel: pd.Series = pd.Series(dtype="float64"),
        electrolysis_efficiency: float = 0.0,
        liquefaction_efficiency: float = 0.0,
        electrofuel_hydrogen_efficiency: float = 0.0,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, float]:
        """Electricity consumption calculation."""

        electricity_hydrogen_consumption = (
            hydrogen_electrolysis_share
            / 100
            * energy_consumption_hydrogen
            / 10**12
            / electrolysis_efficiency
            / liquefaction_efficiency
        )
        electricity_electrofuel_consumption = (
            energy_consumption_electrofuel
            / 10**12
            / electrolysis_efficiency
            / electrofuel_hydrogen_efficiency
        )
        electricity_consumption = (
            electricity_hydrogen_consumption + electricity_electrofuel_consumption
        )

        self.df.loc[:, "electricity_hydrogen_consumption"] = electricity_hydrogen_consumption
        self.df.loc[:, "electricity_electrofuel_consumption"] = electricity_electrofuel_consumption
        self.df.loc[:, "electricity_consumption"] = electricity_consumption

        electricity_consumption_end_year = self.df.loc[self.end_year, "electricity_consumption"]

        self.float_outputs["electricity_consumption_end_year"] = electricity_consumption_end_year

        return (
            electricity_hydrogen_consumption,
            electricity_electrofuel_consumption,
            electricity_consumption,
            electricity_consumption_end_year,
        )

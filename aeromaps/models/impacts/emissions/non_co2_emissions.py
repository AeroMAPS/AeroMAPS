from typing import Tuple
import pandas as pd

from aeromaps.models.base import AeromapsModel


class NOxEmissionIndex(AeromapsModel):
    def __init__(self, name="nox_emission_index", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        emission_index_nox_biofuel_2019: float = 0.0,
        emission_index_nox_electrofuel_2019: float = 0.0,
        emission_index_nox_kerosene_2019: float = 0.0,
        emission_index_nox_hydrogen_2019: float = 0.0,
        emission_index_nox_dropin_fuel_evolution: float = 0.0,
        emission_index_nox_hydrogen_evolution: float = 0.0,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """NOX emission index calculation."""

        # Initialization
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "emission_index_nox_biofuel"] = emission_index_nox_biofuel_2019
            self.df.loc[k, "emission_index_nox_electrofuel"] = emission_index_nox_electrofuel_2019
            self.df.loc[k, "emission_index_nox_kerosene"] = emission_index_nox_kerosene_2019
            self.df.loc[k, "emission_index_nox_hydrogen"] = emission_index_nox_hydrogen_2019

        # Calculation
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "emission_index_nox_biofuel"] = self.df.loc[
                k - 1, "emission_index_nox_biofuel"
            ] * (1 + emission_index_nox_dropin_fuel_evolution / 100)
            self.df.loc[k, "emission_index_nox_electrofuel"] = self.df.loc[
                k - 1, "emission_index_nox_electrofuel"
            ] * (1 + emission_index_nox_dropin_fuel_evolution / 100)
            self.df.loc[k, "emission_index_nox_kerosene"] = self.df.loc[
                k - 1, "emission_index_nox_kerosene"
            ] * (1 + emission_index_nox_dropin_fuel_evolution / 100)
            self.df.loc[k, "emission_index_nox_hydrogen"] = self.df.loc[
                k - 1, "emission_index_nox_hydrogen"
            ] * (1 + emission_index_nox_hydrogen_evolution / 100)

        emission_index_nox_biofuel = self.df["emission_index_nox_biofuel"]
        emission_index_nox_electrofuel = self.df["emission_index_nox_electrofuel"]
        emission_index_nox_kerosene = self.df["emission_index_nox_kerosene"]
        emission_index_nox_hydrogen = self.df["emission_index_nox_hydrogen"]

        return (
            emission_index_nox_biofuel,
            emission_index_nox_electrofuel,
            emission_index_nox_kerosene,
            emission_index_nox_hydrogen,
        )


class SootEmissionIndex(AeromapsModel):
    def __init__(self, name="nox_emission_index", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        emission_index_soot_biofuel_2019: float = 0.0,
        emission_index_soot_electrofuel_2019: float = 0.0,
        emission_index_soot_kerosene_2019: float = 0.0,
        emission_index_soot_hydrogen_2019: float = 0.0,
        emission_index_soot_dropin_fuel_evolution: float = 0.0,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """Soot emission index calculation."""

        # Initialization
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "emission_index_soot_biofuel"] = emission_index_soot_biofuel_2019
            self.df.loc[k, "emission_index_soot_electrofuel"] = emission_index_soot_electrofuel_2019
            self.df.loc[k, "emission_index_soot_kerosene"] = emission_index_soot_kerosene_2019
            self.df.loc[k, "emission_index_soot_hydrogen"] = emission_index_soot_hydrogen_2019

        # Calculation
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "emission_index_soot_biofuel"] = self.df.loc[
                k - 1, "emission_index_soot_biofuel"
            ] * (1 + emission_index_soot_dropin_fuel_evolution / 100)
            self.df.loc[k, "emission_index_soot_electrofuel"] = self.df.loc[
                k - 1, "emission_index_soot_electrofuel"
            ] * (1 + emission_index_soot_dropin_fuel_evolution / 100)
            self.df.loc[k, "emission_index_soot_kerosene"] = self.df.loc[
                k - 1, "emission_index_soot_kerosene"
            ] * (1 + emission_index_soot_dropin_fuel_evolution / 100)
            self.df.loc[k, "emission_index_soot_hydrogen"] = emission_index_soot_hydrogen_2019

        emission_index_soot_biofuel = self.df["emission_index_soot_biofuel"]
        emission_index_soot_electrofuel = self.df["emission_index_soot_electrofuel"]
        emission_index_soot_kerosene = self.df["emission_index_soot_kerosene"]
        emission_index_soot_hydrogen = self.df["emission_index_soot_hydrogen"]

        return (
            emission_index_soot_biofuel,
            emission_index_soot_electrofuel,
            emission_index_soot_kerosene,
            emission_index_soot_hydrogen,
        )


class NonCO2Emissions(AeromapsModel):
    def __init__(self, name="non_co2_emissions", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        emission_index_nox_biofuel: pd.Series = pd.Series(dtype="float64"),
        emission_index_nox_electrofuel: pd.Series = pd.Series(dtype="float64"),
        emission_index_nox_kerosene: pd.Series = pd.Series(dtype="float64"),
        emission_index_nox_hydrogen: pd.Series = pd.Series(dtype="float64"),
        emission_index_soot_biofuel: float = 0.0,
        emission_index_soot_electrofuel: float = 0.0,
        emission_index_soot_kerosene: float = 0.0,
        emission_index_soot_hydrogen: float = 0.0,
        emission_index_h2o_biofuel: float = 0.0,
        emission_index_h2o_electrofuel: float = 0.0,
        emission_index_h2o_kerosene: float = 0.0,
        emission_index_h2o_hydrogen: float = 0.0,
        emission_index_sulfur_biofuel: float = 0.0,
        emission_index_sulfur_electrofuel: float = 0.0,
        emission_index_sulfur_kerosene: float = 0.0,
        emission_index_sulfur_hydrogen: float = 0.0,
        lhv_kerosene: float = 0.0,
        lhv_biofuel: float = 0.0,
        lhv_electrofuel: float = 0.0,
        lhv_hydrogen: float = 0.0,
        energy_consumption_kerosene: pd.Series = pd.Series(dtype="float64"),
        energy_consumption_biofuel: pd.Series = pd.Series(dtype="float64"),
        energy_consumption_electrofuel: pd.Series = pd.Series(dtype="float64"),
        energy_consumption_hydrogen: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """Non-CO2 emissions calculation."""

        self.df["soot_emissions"] = (
            emission_index_soot_biofuel / 10**9 * energy_consumption_biofuel / lhv_biofuel
            + emission_index_soot_electrofuel
            / 10**9
            * energy_consumption_electrofuel
            / lhv_electrofuel
            + emission_index_soot_kerosene / 10**9 * energy_consumption_kerosene / lhv_kerosene
            + emission_index_soot_hydrogen / 10**9 * energy_consumption_hydrogen / lhv_hydrogen
        )
        self.df["h2o_emissions"] = (
            emission_index_h2o_biofuel / 10**9 * energy_consumption_biofuel / lhv_biofuel
            + emission_index_h2o_electrofuel
            / 10**9
            * energy_consumption_electrofuel
            / lhv_electrofuel
            + emission_index_h2o_kerosene / 10**9 * energy_consumption_kerosene / lhv_kerosene
            + emission_index_h2o_hydrogen / 10**9 * energy_consumption_hydrogen / lhv_hydrogen
        )
        self.df["nox_emissions"] = (
            emission_index_nox_biofuel / 10**9 * energy_consumption_biofuel / lhv_biofuel
            + emission_index_nox_electrofuel
            / 10**9
            * energy_consumption_electrofuel
            / lhv_electrofuel
            + emission_index_nox_kerosene / 10**9 * energy_consumption_kerosene / lhv_kerosene
            + emission_index_nox_hydrogen / 10**9 * energy_consumption_hydrogen / lhv_hydrogen
        )
        self.df["sulfur_emissions"] = (
            emission_index_sulfur_biofuel / 10**9 * energy_consumption_biofuel / lhv_biofuel
            + emission_index_sulfur_electrofuel
            / 10**9
            * energy_consumption_electrofuel
            / lhv_electrofuel
            + emission_index_sulfur_kerosene / 10**9 * energy_consumption_kerosene / lhv_kerosene
            + emission_index_sulfur_hydrogen / 10**9 * energy_consumption_hydrogen / lhv_hydrogen
        )

        soot_emissions = self.df["soot_emissions"]
        h2o_emissions = self.df["h2o_emissions"]
        nox_emissions = self.df["nox_emissions"]
        sulfur_emissions = self.df["sulfur_emissions"]

        return soot_emissions, h2o_emissions, nox_emissions, sulfur_emissions

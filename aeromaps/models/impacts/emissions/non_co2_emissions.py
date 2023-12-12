from typing import Tuple
import pandas as pd
from pandas import read_csv
import os.path as pth

from aeromaps.models.base import AeromapsModel
from aeromaps.resources import climate_data


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
        """NOx emission index calculation using simple method."""

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


class NOxEmissionIndexComplex(AeromapsModel):
    def __init__(self, name="nox_emission_index_complex", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = fleet_model

    def compute(
        self,
        emission_index_nox_biofuel_2019: float = 0.0,
        emission_index_nox_electrofuel_2019: float = 0.0,
        emission_index_nox_kerosene_2019: float = 0.0,
        emission_index_nox_hydrogen_2019: float = 0.0,
        ask_long_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        ask_short_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        ask_long_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        ask_short_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """NOx emission index calculation using fleet renewal models."""

        emission_index_nox_short_range_dropin_fuel = self.fleet_model.df[
            "Short Range:emission_index_nox:dropin_fuel"
        ]
        emission_index_nox_medium_range_dropin_fuel = self.fleet_model.df[
            "Medium Range:emission_index_nox:dropin_fuel"
        ]
        emission_index_nox_long_range_dropin_fuel = self.fleet_model.df[
            "Long Range:emission_index_nox:dropin_fuel"
        ]
        emission_index_nox_short_range_hydrogen = self.fleet_model.df[
            "Short Range:emission_index_nox:hydrogen"
        ]
        emission_index_nox_medium_range_hydrogen = self.fleet_model.df[
            "Medium Range:emission_index_nox:hydrogen"
        ]
        emission_index_nox_long_range_hydrogen = self.fleet_model.df[
            "Long Range:emission_index_nox:hydrogen"
        ]

        # Initialization
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "emission_index_nox_biofuel"] = emission_index_nox_biofuel_2019
            self.df.loc[k, "emission_index_nox_electrofuel"] = emission_index_nox_electrofuel_2019
            self.df.loc[k, "emission_index_nox_kerosene"] = emission_index_nox_kerosene_2019
            self.df.loc[k, "emission_index_nox_hydrogen"] = emission_index_nox_hydrogen_2019

        # Kerosene
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "emission_index_nox_kerosene"] = (
                emission_index_nox_short_range_dropin_fuel.loc[k]
                * ask_short_range_dropin_fuel.loc[k]
                + emission_index_nox_medium_range_dropin_fuel.loc[k]
                * ask_medium_range_dropin_fuel.loc[k]
                + emission_index_nox_long_range_dropin_fuel.loc[k]
                * ask_long_range_dropin_fuel.loc[k]
            ) / (
                ask_short_range_dropin_fuel.loc[k]
                + ask_medium_range_dropin_fuel.loc[k]
                + ask_long_range_dropin_fuel.loc[k]
            )

        # Electrofuel and biofuel
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "emission_index_nox_biofuel"] = (
                emission_index_nox_biofuel_2019
                / emission_index_nox_kerosene_2019
                * self.df.loc[k, "emission_index_nox_kerosene"]
            )
            self.df.loc[k, "emission_index_nox_electrofuel"] = (
                emission_index_nox_electrofuel_2019
                / emission_index_nox_kerosene_2019
                * self.df.loc[k, "emission_index_nox_kerosene"]
            )

        # Hydrogen
        for k in range(self.prospection_start_year, self.end_year + 1):
            if (
                ask_short_range_hydrogen.loc[k]
                + ask_medium_range_hydrogen.loc[k]
                + ask_long_range_hydrogen.loc[k]
                == 0
            ):
                self.df.loc[k, "emission_index_nox_hydrogen"] = self.df.loc[
                    k - 1, "emission_index_nox_hydrogen"
                ]
            else:
                self.df.loc[k, "emission_index_nox_hydrogen"] = (
                    emission_index_nox_short_range_hydrogen.loc[k] * ask_short_range_hydrogen.loc[k]
                    + emission_index_nox_medium_range_hydrogen.loc[k]
                    * ask_medium_range_hydrogen.loc[k]
                    + emission_index_nox_long_range_hydrogen.loc[k] * ask_long_range_hydrogen.loc[k]
                ) / (
                    ask_short_range_hydrogen.loc[k]
                    + ask_medium_range_hydrogen.loc[k]
                    + ask_long_range_hydrogen.loc[k]
                )

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
    def __init__(self, name="soot_emission_index", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        emission_index_soot_biofuel_2019: float = 0.0,
        emission_index_soot_electrofuel_2019: float = 0.0,
        emission_index_soot_kerosene_2019: float = 0.0,
        emission_index_soot_hydrogen_2019: float = 0.0,
        emission_index_soot_dropin_fuel_evolution: float = 0.0,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """Soot emission index calculation using simple method."""

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


class SootEmissionIndexComplex(AeromapsModel):
    def __init__(self, name="soot_emission_index_complex", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = fleet_model

    def compute(
        self,
        emission_index_soot_biofuel_2019: float = 0.0,
        emission_index_soot_electrofuel_2019: float = 0.0,
        emission_index_soot_kerosene_2019: float = 0.0,
        emission_index_soot_hydrogen_2019: float = 0.0,
        ask_long_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        ask_short_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        ask_long_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        ask_short_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """Soot emission index calculation using fleet renewal models."""

        emission_index_soot_short_range_dropin_fuel = self.fleet_model.df[
            "Short Range:emission_index_soot:dropin_fuel"
        ]
        emission_index_soot_medium_range_dropin_fuel = self.fleet_model.df[
            "Medium Range:emission_index_soot:dropin_fuel"
        ]
        emission_index_soot_long_range_dropin_fuel = self.fleet_model.df[
            "Long Range:emission_index_soot:dropin_fuel"
        ]
        emission_index_soot_short_range_hydrogen = self.fleet_model.df[
            "Short Range:emission_index_soot:hydrogen"
        ]
        emission_index_soot_medium_range_hydrogen = self.fleet_model.df[
            "Medium Range:emission_index_soot:hydrogen"
        ]
        emission_index_soot_long_range_hydrogen = self.fleet_model.df[
            "Long Range:emission_index_soot:hydrogen"
        ]

        # Initialization
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "emission_index_soot_biofuel"] = emission_index_soot_biofuel_2019
            self.df.loc[k, "emission_index_soot_electrofuel"] = emission_index_soot_electrofuel_2019
            self.df.loc[k, "emission_index_soot_kerosene"] = emission_index_soot_kerosene_2019
            self.df.loc[k, "emission_index_soot_hydrogen"] = emission_index_soot_hydrogen_2019

        # Kerosene
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "emission_index_soot_kerosene"] = (
                emission_index_soot_short_range_dropin_fuel.loc[k]
                * ask_short_range_dropin_fuel.loc[k]
                + emission_index_soot_medium_range_dropin_fuel.loc[k]
                * ask_medium_range_dropin_fuel.loc[k]
                + emission_index_soot_long_range_dropin_fuel.loc[k]
                * ask_long_range_dropin_fuel.loc[k]
            ) / (
                ask_short_range_dropin_fuel.loc[k]
                + ask_medium_range_dropin_fuel.loc[k]
                + ask_long_range_dropin_fuel.loc[k]
            )

        # Electrofuel and biofuel
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "emission_index_soot_biofuel"] = (
                emission_index_soot_biofuel_2019
                / emission_index_soot_kerosene_2019
                * self.df.loc[k, "emission_index_soot_kerosene"]
            )
            self.df.loc[k, "emission_index_soot_electrofuel"] = (
                emission_index_soot_electrofuel_2019
                / emission_index_soot_kerosene_2019
                * self.df.loc[k, "emission_index_soot_kerosene"]
            )

        # Hydrogen
        for k in range(self.prospection_start_year, self.end_year + 1):
            if (
                ask_short_range_hydrogen.loc[k]
                + ask_medium_range_hydrogen.loc[k]
                + ask_long_range_hydrogen.loc[k]
                == 0
            ):
                self.df.loc[k, "emission_index_soot_hydrogen"] = self.df.loc[
                    k - 1, "emission_index_soot_hydrogen"
                ]
            else:
                self.df.loc[k, "emission_index_soot_hydrogen"] = (
                    emission_index_soot_short_range_hydrogen.loc[k]
                    * ask_short_range_hydrogen.loc[k]
                    + emission_index_soot_medium_range_hydrogen.loc[k]
                    * ask_medium_range_hydrogen.loc[k]
                    + emission_index_soot_long_range_hydrogen.loc[k]
                    * ask_long_range_hydrogen.loc[k]
                ) / (
                    ask_short_range_hydrogen.loc[k]
                    + ask_medium_range_hydrogen.loc[k]
                    + ask_long_range_hydrogen.loc[k]
                )

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
        # Load dataset
        historical_dataset_path = pth.join(
            climate_data.__path__[0], "temperature_historical_dataset.csv"
        )
        historical_dataset_df = read_csv(historical_dataset_path, delimiter=";", header=None)
        self.historical_dataset = historical_dataset_df.values

    def compute(
        self,
        emission_index_nox_biofuel: pd.Series = pd.Series(dtype="float64"),
        emission_index_nox_electrofuel: pd.Series = pd.Series(dtype="float64"),
        emission_index_nox_kerosene: pd.Series = pd.Series(dtype="float64"),
        emission_index_nox_hydrogen: pd.Series = pd.Series(dtype="float64"),
        emission_index_soot_biofuel: pd.Series = pd.Series(dtype="float64"),
        emission_index_soot_electrofuel: pd.Series = pd.Series(dtype="float64"),
        emission_index_soot_kerosene: pd.Series = pd.Series(dtype="float64"),
        emission_index_soot_hydrogen: pd.Series = pd.Series(dtype="float64"),
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

        ## Initialization
        historical_nox_emissions_for_temperature = self.historical_dataset[:, 2]
        historical_h2o_emissions_for_temperature = self.historical_dataset[:, 3]
        historical_soot_emissions_for_temperature = self.historical_dataset[:, 4]
        historical_sulfur_emissions_for_temperature = self.historical_dataset[:, 5]

        # Calculation
        for k in range(self.climate_historic_start_year, self.historic_start_year):
            self.df_climate.loc[k, "soot_emissions"] = historical_soot_emissions_for_temperature[
                k - self.climate_historic_start_year
            ]
            self.df_climate.loc[k, "h2o_emissions"] = historical_h2o_emissions_for_temperature[
                k - self.climate_historic_start_year
            ]
            self.df_climate.loc[k, "nox_emissions"] = historical_nox_emissions_for_temperature[
                k - self.climate_historic_start_year
            ]
            self.df_climate.loc[
                k, "sulfur_emissions"
            ] = historical_sulfur_emissions_for_temperature[k - self.climate_historic_start_year]

        for k in range(self.historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "soot_emissions"] = (
                emission_index_soot_biofuel.loc[k]
                / 10**9
                * energy_consumption_biofuel.loc[k]
                / lhv_biofuel
                + emission_index_soot_electrofuel.loc[k]
                / 10**9
                * energy_consumption_electrofuel.loc[k]
                / lhv_electrofuel
                + emission_index_soot_kerosene.loc[k]
                / 10**9
                * energy_consumption_kerosene.loc[k]
                / lhv_kerosene
                + emission_index_soot_hydrogen.loc[k]
                / 10**9
                * energy_consumption_hydrogen.loc[k]
                / lhv_hydrogen
            )
            self.df_climate.loc[k, "h2o_emissions"] = (
                emission_index_h2o_biofuel
                / 10**9
                * energy_consumption_biofuel.loc[k]
                / lhv_biofuel
                + emission_index_h2o_electrofuel
                / 10**9
                * energy_consumption_electrofuel.loc[k]
                / lhv_electrofuel
                + emission_index_h2o_kerosene
                / 10**9
                * energy_consumption_kerosene.loc[k]
                / lhv_kerosene
                + emission_index_h2o_hydrogen
                / 10**9
                * energy_consumption_hydrogen.loc[k]
                / lhv_hydrogen
            )
            self.df_climate.loc[k, "nox_emissions"] = (
                emission_index_nox_biofuel.loc[k]
                / 10**9
                * energy_consumption_biofuel.loc[k]
                / lhv_biofuel
                + emission_index_nox_electrofuel.loc[k]
                / 10**9
                * energy_consumption_electrofuel.loc[k]
                / lhv_electrofuel
                + emission_index_nox_kerosene.loc[k]
                / 10**9
                * energy_consumption_kerosene.loc[k]
                / lhv_kerosene
                + emission_index_nox_hydrogen.loc[k]
                / 10**9
                * energy_consumption_hydrogen.loc[k]
                / lhv_hydrogen
            )
            self.df_climate.loc[k, "sulfur_emissions"] = (
                emission_index_sulfur_biofuel
                / 10**9
                * energy_consumption_biofuel.loc[k]
                / lhv_biofuel
                + emission_index_sulfur_electrofuel
                / 10**9
                * energy_consumption_electrofuel.loc[k]
                / lhv_electrofuel
                + emission_index_sulfur_kerosene
                / 10**9
                * energy_consumption_kerosene.loc[k]
                / lhv_kerosene
                + emission_index_sulfur_hydrogen
                / 10**9
                * energy_consumption_hydrogen.loc[k]
                / lhv_hydrogen
            )

        soot_emissions = self.df_climate.loc[:, "soot_emissions"]
        h2o_emissions = self.df_climate.loc[:, "h2o_emissions"]
        nox_emissions = self.df_climate.loc[:, "nox_emissions"]
        sulfur_emissions = self.df_climate.loc[:, "sulfur_emissions"]

        return soot_emissions, h2o_emissions, nox_emissions, sulfur_emissions

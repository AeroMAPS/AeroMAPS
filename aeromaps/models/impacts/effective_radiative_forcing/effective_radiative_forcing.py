from typing import Tuple
import pandas as pd
import numpy as np
from pandas import read_csv
import os.path as pth

from aeromaps.models.base import AeromapsModel, AbsoluteGlobalWarmingPotentialCO2Function
from aeromaps.resources import data


class ERF(AeromapsModel):
    def __init__(self, name="effective_radiative_forcing", *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        # Load dataset
        historical_dataset_path = pth.join(data.__path__[0], "temperature_historical_dataset.csv")
        historical_dataset_df = read_csv(historical_dataset_path, delimiter=";")
        self.historical_dataset = historical_dataset_df.values

    def compute(
        self,
        soot_emissions: pd.Series = pd.Series(dtype="float64"),
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
        h2o_emissions: pd.Series = pd.Series(dtype="float64"),
        nox_emissions: pd.Series = pd.Series(dtype="float64"),
        sulfur_emissions: pd.Series = pd.Series(dtype="float64"),
        erf_coefficient_contrails: float = 0.0,
        erf_coefficient_nox_short_term_o3_increase: float = 0.0,
        erf_coefficient_nox_long_term_o3_decrease: float = 0.0,
        erf_coefficient_nox_ch4_decrease: float = 0.0,
        erf_coefficient_nox_stratospheric_water_vapor_decrease: float = 0.0,
        erf_coefficient_soot: float = 0.0,
        erf_coefficient_h2o: float = 0.0,
        erf_coefficient_sulfur: float = 0.0,
        total_aircraft_distance: pd.Series = pd.Series(dtype="float64"),
        operations_contrails_gain: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
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
        """ERF calculation for the different climate impacts of aviation."""

        # GLOBAL
        h = 100  # Climate time horizon

        # HISTORICAL ERF BEFORE 2000

        ## Initialization
        historical_years_for_temperature = self.historical_dataset[:, 0]
        historical_co2_emissions_for_temperature = self.historical_dataset[:, 1]
        historical_nox_emissions_for_temperature = self.historical_dataset[:, 2]
        historical_h2o_emissions_for_temperature = self.historical_dataset[:, 3]
        historical_soot_emissions_for_temperature = self.historical_dataset[:, 4]
        historical_sulfur_emissions_for_temperature = self.historical_dataset[:, 5]
        historical_distance_for_temperature = self.historical_dataset[:, 6]

        ## CO2 ERF
        historical_annual_co2_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        for k in range(0, len(historical_years_for_temperature)):
            historical_annual_co2_erf_for_temperature[k] = (
                historical_co2_emissions_for_temperature[k]
                * AbsoluteGlobalWarmingPotentialCO2Function(h)
                / h
            )
        historical_co2_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        historical_co2_erf_for_temperature[0] = historical_annual_co2_erf_for_temperature[0]
        for k in range(1, len(historical_years_for_temperature)):
            historical_co2_erf_for_temperature[k] = (
                historical_co2_erf_for_temperature[k - 1]
                + historical_annual_co2_erf_for_temperature[k]
            )

        ## Contrails ERF
        historical_contrails_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        for k in range(0, len(historical_years_for_temperature)):
            historical_contrails_erf_for_temperature[k] = (
                historical_distance_for_temperature[k] * erf_coefficient_contrails
            )

        ## NOx ERF
        historical_n_emissions_for_temperature = (
            historical_nox_emissions_for_temperature * 14 / 46
        )  # Molar masses of N and NOx
        historical_nox_short_term_o3_increase_erf_for_temperature = np.zeros(
            len(historical_years_for_temperature)
        )
        historical_nox_long_term_o3_decrease_erf_for_temperature = np.zeros(
            len(historical_years_for_temperature)
        )
        historical_nox_ch4_decrease_erf_for_temperature = np.zeros(
            len(historical_years_for_temperature)
        )
        historical_nox_stratospheric_water_vapor_decrease_erf_for_temperature = np.zeros(
            len(historical_years_for_temperature)
        )
        for k in range(0, len(historical_years_for_temperature)):
            historical_nox_short_term_o3_increase_erf_for_temperature[k] = (
                historical_n_emissions_for_temperature[k]
                * erf_coefficient_nox_short_term_o3_increase
            )
            historical_nox_long_term_o3_decrease_erf_for_temperature[k] = (
                historical_n_emissions_for_temperature[k]
                * erf_coefficient_nox_long_term_o3_decrease
            )
            historical_nox_ch4_decrease_erf_for_temperature[k] = (
                historical_n_emissions_for_temperature[k] * erf_coefficient_nox_ch4_decrease
            )
            historical_nox_stratospheric_water_vapor_decrease_erf_for_temperature[k] = (
                historical_n_emissions_for_temperature[k]
                * erf_coefficient_nox_stratospheric_water_vapor_decrease
            )
        historical_nox_erf_for_temperature = (
            historical_nox_short_term_o3_increase_erf_for_temperature
            + historical_nox_long_term_o3_decrease_erf_for_temperature
            + historical_nox_ch4_decrease_erf_for_temperature
            + historical_nox_stratospheric_water_vapor_decrease_erf_for_temperature
        )

        ## Other ERF
        historical_h2o_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        historical_soot_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        historical_sulfur_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        for k in range(0, len(historical_years_for_temperature)):
            historical_h2o_erf_for_temperature[k] = (
                historical_h2o_emissions_for_temperature[k] * erf_coefficient_h2o
            )
            historical_soot_erf_for_temperature[k] = (
                historical_soot_emissions_for_temperature[k] * erf_coefficient_soot
            )
            historical_sulfur_erf_for_temperature[k] = (
                historical_sulfur_emissions_for_temperature[k] * erf_coefficient_sulfur
            )

        ## Total ERF
        historical_aerosol_erf_for_temperature = (
            historical_soot_erf_for_temperature + historical_sulfur_erf_for_temperature
        )
        historical_total_erf_for_temperature = (
            historical_co2_erf_for_temperature
            + historical_contrails_erf_for_temperature
            + historical_nox_erf_for_temperature
            + historical_h2o_erf_for_temperature
            + historical_aerosol_erf_for_temperature
        )
        self.historical_total_erf_for_temperature = historical_total_erf_for_temperature

        ## HISTORICAL ERF AFTER 2020 AND PROSPECTIVE

        # CO2
        self.df["annual_co2_erf"] = co2_emissions * AbsoluteGlobalWarmingPotentialCO2Function(h) / h

        self.df.loc[self.historic_start_year, "co2_erf"] = (
            historical_co2_erf_for_temperature[len(historical_years_for_temperature) - 2]
            + self.df.loc[self.historic_start_year, "annual_co2_erf"]
        )
        for k in range(self.historic_start_year + 1, self.end_year + 1):
            self.df.loc[k, "co2_erf"] = (
                self.df.loc[k - 1, "co2_erf"] + self.df.loc[k, "annual_co2_erf"]
            )

        annual_co2_erf = self.df["annual_co2_erf"]
        co2_erf = self.df["co2_erf"]

        # Contrails
        self.df["contrails_erf"] = (
            total_aircraft_distance
            * erf_coefficient_contrails
            * (1 - operations_contrails_gain / 100)
        )
        contrails_erf = self.df["contrails_erf"]

        # NOx
        n_emissions = nox_emissions * 14 / 46  # Molar masses of N and NOx
        # transcient_ch4_correction_factor = 0.79
        # correction_factor = (1.35 * 0.88) - Difference with Lee values and impact of non-commercial aviation
        self.df["nox_short_term_o3_increase_erf"] = (
            n_emissions * erf_coefficient_nox_short_term_o3_increase
        )
        self.df["nox_long_term_o3_decrease_erf"] = (
            n_emissions * erf_coefficient_nox_long_term_o3_decrease
        )
        self.df["nox_ch4_decrease_erf"] = n_emissions * erf_coefficient_nox_ch4_decrease
        self.df["nox_stratospheric_water_vapor_decrease_erf"] = (
            n_emissions * erf_coefficient_nox_stratospheric_water_vapor_decrease
        )
        nox_short_term_o3_increase_erf = self.df["nox_short_term_o3_increase_erf"]
        nox_long_term_o3_decrease_erf = self.df["nox_long_term_o3_decrease_erf"]
        nox_ch4_decrease_erf = self.df["nox_ch4_decrease_erf"]
        nox_stratospheric_water_vapor_decrease_erf = self.df[
            "nox_stratospheric_water_vapor_decrease_erf"
        ]
        nox_erf = (
            nox_short_term_o3_increase_erf
            + nox_long_term_o3_decrease_erf
            + nox_ch4_decrease_erf
            + nox_stratospheric_water_vapor_decrease_erf
        )
        self.df["nox_erf"] = nox_erf

        # Others
        self.df["soot_erf"] = soot_emissions * erf_coefficient_soot
        self.df["h2o_erf"] = h2o_emissions * erf_coefficient_h2o
        self.df["sulfur_erf"] = sulfur_emissions * erf_coefficient_sulfur
        soot_erf = self.df["soot_erf"]
        h2o_erf = self.df["h2o_erf"]
        sulfur_erf = self.df["sulfur_erf"]

        # Total
        self.df["aerosol_erf"] = soot_erf + sulfur_erf
        self.df["total_erf"] = co2_erf + contrails_erf + h2o_erf + nox_erf + soot_erf + sulfur_erf
        aerosol_erf = self.df["aerosol_erf"]
        total_erf = self.df["total_erf"]

        return (
            historical_co2_emissions_for_temperature,
            historical_annual_co2_erf_for_temperature,
            historical_co2_erf_for_temperature,
            historical_contrails_erf_for_temperature,
            historical_nox_short_term_o3_increase_erf_for_temperature,
            historical_nox_long_term_o3_decrease_erf_for_temperature,
            historical_nox_ch4_decrease_erf_for_temperature,
            historical_nox_stratospheric_water_vapor_decrease_erf_for_temperature,
            historical_nox_erf_for_temperature,
            historical_soot_erf_for_temperature,
            historical_h2o_erf_for_temperature,
            historical_sulfur_erf_for_temperature,
            annual_co2_erf,
            co2_erf,
            contrails_erf,
            nox_short_term_o3_increase_erf,
            nox_long_term_o3_decrease_erf,
            nox_ch4_decrease_erf,
            nox_stratospheric_water_vapor_decrease_erf,
            nox_erf,
            soot_erf,
            h2o_erf,
            sulfur_erf,
            aerosol_erf,
            total_erf,
        )


class ERFSimplifiedNox(AeromapsModel):
    def __init__(self, name="effective_radiative_forcing_simplified_nox", *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        # Load dataset
        historical_dataset_path = pth.join(data.__path__[0], "temperature_historical_dataset.csv")
        historical_dataset_df = read_csv(historical_dataset_path, delimiter=";")
        self.historical_dataset = historical_dataset_df.values

    def compute(
        self,
        soot_emissions: pd.Series = pd.Series(dtype="float64"),
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
        h2o_emissions: pd.Series = pd.Series(dtype="float64"),
        nox_emissions: pd.Series = pd.Series(dtype="float64"),
        sulfur_emissions: pd.Series = pd.Series(dtype="float64"),
        erf_coefficient_soot: float = 0.0,
        erf_coefficient_contrails: float = 0.0,
        erf_coefficient_h2o: float = 0.0,
        erf_coefficient_nox: float = 0.0,
        erf_coefficient_sulfur: float = 0.0,
        total_aircraft_distance: pd.Series = pd.Series(dtype="float64"),
        operations_contrails_gain: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
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
        """ERF calculation for the different climate impacts of aviation."""

        # GLOBAL
        h = 100  # Climate time horizon

        # HISTORICAL ERF BEFORE 2000

        ## Initialization
        historical_years_for_temperature = self.historical_dataset[:, 0]
        historical_co2_emissions_for_temperature = self.historical_dataset[:, 1]
        historical_nox_emissions_for_temperature = self.historical_dataset[:, 2]
        historical_h2o_emissions_for_temperature = self.historical_dataset[:, 3]
        historical_soot_emissions_for_temperature = self.historical_dataset[:, 4]
        historical_sulfur_emissions_for_temperature = self.historical_dataset[:, 5]
        historical_distance_for_temperature = self.historical_dataset[:, 6]

        ## CO2 ERF
        historical_annual_co2_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        for k in range(0, len(historical_years_for_temperature)):
            historical_annual_co2_erf_for_temperature[k] = (
                historical_co2_emissions_for_temperature[k]
                * AbsoluteGlobalWarmingPotentialCO2Function(h)
                / h
            )
        historical_co2_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        historical_co2_erf_for_temperature[0] = historical_annual_co2_erf_for_temperature[0]
        for k in range(1, len(historical_years_for_temperature)):
            historical_co2_erf_for_temperature[k] = (
                historical_co2_erf_for_temperature[k - 1]
                + historical_annual_co2_erf_for_temperature[k]
            )

        ## Contrails ERF
        historical_contrails_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        for k in range(0, len(historical_years_for_temperature)):
            historical_contrails_erf_for_temperature[k] = (
                historical_distance_for_temperature[k] * erf_coefficient_contrails
            )

        ## NOx ERF
        historical_n_emissions_for_temperature = (
            historical_nox_emissions_for_temperature * 14 / 46
        )  # Molar masses of N and NOx
        historical_nox_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        for k in range(0, len(historical_years_for_temperature)):
            historical_nox_erf_for_temperature[k] = (
                historical_n_emissions_for_temperature[k] * erf_coefficient_nox
            )

        ## Other ERF
        historical_h2o_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        historical_soot_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        historical_sulfur_erf_for_temperature = np.zeros(len(historical_years_for_temperature))
        for k in range(0, len(historical_years_for_temperature)):
            historical_h2o_erf_for_temperature[k] = (
                historical_h2o_emissions_for_temperature[k] * erf_coefficient_h2o
            )
            historical_soot_erf_for_temperature[k] = (
                historical_soot_emissions_for_temperature[k] * erf_coefficient_soot
            )
            historical_sulfur_erf_for_temperature[k] = (
                historical_sulfur_emissions_for_temperature[k] * erf_coefficient_sulfur
            )

        ## Total ERF
        historical_aerosol_erf_for_temperature = (
            historical_soot_erf_for_temperature + historical_sulfur_erf_for_temperature
        )
        historical_total_erf_for_temperature = (
            historical_co2_erf_for_temperature
            + historical_contrails_erf_for_temperature
            + historical_nox_erf_for_temperature
            + historical_h2o_erf_for_temperature
            + historical_aerosol_erf_for_temperature
        )
        self.historical_total_erf_for_temperature = historical_total_erf_for_temperature

        ## HISTORICAL ERF AFTER 2020 AND PROSPECTIVE

        # CO2
        self.df["annual_co2_erf"] = co2_emissions * AbsoluteGlobalWarmingPotentialCO2Function(h) / h

        self.df.loc[self.historic_start_year, "co2_erf"] = (
            historical_co2_erf_for_temperature[len(historical_years_for_temperature) - 2]
            + self.df.loc[self.historic_start_year, "annual_co2_erf"]
        )
        for k in range(self.historic_start_year + 1, self.end_year + 1):
            self.df.loc[k, "co2_erf"] = (
                self.df.loc[k - 1, "co2_erf"] + self.df.loc[k, "annual_co2_erf"]
            )

        annual_co2_erf = self.df["annual_co2_erf"]
        co2_erf = self.df["co2_erf"]

        # Contrails
        self.df["contrails_erf"] = (
            total_aircraft_distance
            * erf_coefficient_contrails
            * (1 - operations_contrails_gain / 100)
        )
        contrails_erf = self.df["contrails_erf"]

        # NOx
        self.df["nox_erf"] = nox_emissions * erf_coefficient_nox
        nox_erf = self.df["nox_erf"]

        # Others
        self.df["soot_erf"] = soot_emissions * erf_coefficient_soot
        self.df["h2o_erf"] = h2o_emissions * erf_coefficient_h2o
        self.df["sulfur_erf"] = sulfur_emissions * erf_coefficient_sulfur
        soot_erf = self.df["soot_erf"]
        h2o_erf = self.df["h2o_erf"]
        sulfur_erf = self.df["sulfur_erf"]

        # Total
        self.df["aerosol_erf"] = soot_erf + sulfur_erf
        self.df["total_erf"] = co2_erf + contrails_erf + h2o_erf + nox_erf + soot_erf + sulfur_erf
        aerosol_erf = self.df["aerosol_erf"]
        total_erf = self.df["total_erf"]

        return (
            historical_co2_emissions_for_temperature,
            historical_annual_co2_erf_for_temperature,
            historical_co2_erf_for_temperature,
            historical_contrails_erf_for_temperature,
            historical_nox_erf_for_temperature,
            historical_soot_erf_for_temperature,
            historical_h2o_erf_for_temperature,
            historical_sulfur_erf_for_temperature,
            annual_co2_erf,
            co2_erf,
            contrails_erf,
            soot_erf,
            h2o_erf,
            nox_erf,
            sulfur_erf,
            aerosol_erf,
            total_erf,
        )


class DetailedERF(AeromapsModel):
    def __init__(self, name="detailed_erf", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        co2_erf: pd.Series = pd.Series(dtype="float64"),
        contrails_erf: pd.Series = pd.Series(dtype="float64"),
        h2o_erf: pd.Series = pd.Series(dtype="float64"),
        nox_erf: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """ERF calculation for helping plot display."""

        self.df["co2_h2o_erf"] = co2_erf + h2o_erf
        self.df["co2_h2o_nox_erf"] = co2_erf + h2o_erf + nox_erf
        self.df["co2_h2o_nox_contrails_erf"] = co2_erf + h2o_erf + nox_erf + contrails_erf

        co2_h2o_erf = self.df["co2_h2o_erf"]
        co2_h2o_nox_erf = self.df["co2_h2o_nox_erf"]
        co2_h2o_nox_contrails_erf = self.df["co2_h2o_nox_contrails_erf"]

        return co2_h2o_erf, co2_h2o_nox_erf, co2_h2o_nox_contrails_erf

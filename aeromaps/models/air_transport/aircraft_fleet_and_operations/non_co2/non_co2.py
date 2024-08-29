from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class OperationsContrailsSimple(AeroMAPSModel):
    def __init__(self, name="operations_contrails_simple", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        operations_contrails_final_gain: float,
        operations_contrails_final_overconsumption: float,
        operations_contrails_start_year: int,
        operations_contrails_duration: float,
    ) -> Tuple[pd.Series, pd.Series]:
        """Operations contrails gain for ERF calculation."""

        transition_year = operations_contrails_start_year + operations_contrails_duration / 2
        operations_contrails_limit = 0.02 * operations_contrails_final_gain
        operations_parameter = np.log(100 / 2 - 1) / (operations_contrails_duration / 2)
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "operations_contrails_gain"] = 0
            self.df.loc[k, "operations_contrails_overconsumption"] = 0
        for k in range(self.prospection_start_year, self.end_year + 1):
            if (
                operations_contrails_final_gain
                / (1 + np.exp(-operations_parameter * (k - transition_year)))
                < operations_contrails_limit
            ):
                self.df.loc[k, "operations_contrails_gain"] = 0
                self.df.loc[k, "operations_contrails_overconsumption"] = 0
            else:
                self.df.loc[k, "operations_contrails_gain"] = operations_contrails_final_gain / (
                    1 + np.exp(-operations_parameter * (k - transition_year))
                )
                self.df.loc[k, "operations_contrails_overconsumption"] = (
                    operations_contrails_final_overconsumption
                    / (1 + np.exp(-operations_parameter * (k - transition_year)))
                )

        operations_contrails_gain = self.df["operations_contrails_gain"]
        operations_contrails_overconsumption = self.df["operations_contrails_overconsumption"]

        return operations_contrails_gain, operations_contrails_overconsumption


class FuelEffectCorrectionContrails(AeroMAPSModel):
    def __init__(self, name="fuel_effect_correction_contrails", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        total_aircraft_distance_dropin_fuel: pd.Series,
        total_aircraft_distance: pd.Series,
        total_aircraft_distance_hydrogen: pd.Series,
        total_aircraft_distance_electric: pd.Series,
        biofuel_share: pd.Series,
        electrofuel_share: pd.Series,
        kerosene_share: pd.Series,
        emission_index_number_particles_biofuel: float,
        emission_index_number_particles_electrofuel: float,
        emission_index_number_particles_kerosene: float,
        contrails_relative_effect_hydrogen_wrt_kerosene: float,
    ) -> pd.Series:
        """Fuel effect on contrails for ERF calculation."""

        fuel_effect_correction_contrails = (
            total_aircraft_distance_dropin_fuel
            / total_aircraft_distance
            * (
                kerosene_share
                / 100
                * np.sqrt(
                    emission_index_number_particles_kerosene
                    / emission_index_number_particles_kerosene
                )
                + biofuel_share
                / 100
                * np.sqrt(
                    emission_index_number_particles_biofuel
                    / emission_index_number_particles_kerosene
                )
                + electrofuel_share
                / 100
                * np.sqrt(
                    emission_index_number_particles_electrofuel
                    / emission_index_number_particles_kerosene
                )
            )
            + total_aircraft_distance_hydrogen
            / total_aircraft_distance
            * contrails_relative_effect_hydrogen_wrt_kerosene
            + total_aircraft_distance_electric / total_aircraft_distance * 0
        )
        self.df["fuel_effect_correction_contrails"] = fuel_effect_correction_contrails

        return fuel_effect_correction_contrails


class WithoutFuelEffectCorrectionContrails(AeroMAPSModel):
    def __init__(self, name="without_fuel_effect_correction_contrails", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        total_aircraft_distance: pd.Series,
    ) -> pd.Series:
        """Fuel effect on contrails for ERF calculation."""

        for k in range(self.historic_start_year, self.end_year + 1):
            self.df.loc[k, "fuel_effect_correction_contrails"] = 1

        fuel_effect_correction_contrails = self.df["fuel_effect_correction_contrails"]
        return fuel_effect_correction_contrails

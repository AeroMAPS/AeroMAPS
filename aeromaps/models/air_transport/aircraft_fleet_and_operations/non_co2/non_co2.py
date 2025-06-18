import warnings
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
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
        self.input_names = {}
        self.output_names = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            if aircraft_type == "dropin_fuel":
                for pathway in self.pathways_manager.get(
                    aircraft_type=aircraft_type,
                ):
                    self.input_names.update(
                        {
                            f"{pathway.name}_massic_share_{aircraft_type}": pd.Series([0.0]),
                            f"{pathway.name}_emission_index_particles_number": 0.0,
                        }
                    )
                self.input_names.update(
                    {
                        "total_aircraft_distance_dropin_fuel": pd.Series([0.0]),
                    }
                )
            elif aircraft_type == "hydrogen":
                self.input_names.update(
                    {
                        "contrails_relative_effect_hydrogen_wrt_kerosene": 0.0,
                        "total_aircraft_distance_hydrogen": pd.Series([0.0]),
                    }
                )
            elif aircraft_type == "electric":
                self.input_names.update(
                    {
                        "total_aircraft_distance_electric": pd.Series([0.0]),
                    }
                )
            else:
                warnings.warn(f"Aircraft type '{aircraft_type}' not supported.", UserWarning)

        self.input_names.update(
            {
                "total_aircraft_distance": pd.Series([0.0]),
            }
        )

        self.output_names.update(
            {
                "fuel_effect_correction_contrails": pd.Series([0.0]),
            }
        )

    def compute(self, input_data) -> dict:
        """Fuel effect on contrails for ERF calculation."""

        def default_series():
            return pd.Series(
                [0.0] * len(range(self.historic_start_year, self.end_year + 1)),
                index=range(self.historic_start_year, self.end_year + 1),
            )

        fuel_effect_correction_contrails = default_series()

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            if aircraft_type == "dropin_fuel":
                relative_particles_number = default_series()
                distance_share_dropin_fuel = (
                    input_data["total_aircraft_distance_dropin_fuel"]
                    / input_data["total_aircraft_distance"]
                )

                default_pathway = self.pathways_manager.get(
                    aircraft_type=aircraft_type, default=True
                )[0]
                default_emission_index_number_particles = input_data[
                    f"{default_pathway.name}_emission_index_particles_number"
                ]

                for pathway in self.pathways_manager.get(
                    aircraft_type=aircraft_type,
                ):
                    relative_particles_number += (
                        input_data[f"{pathway.name}_massic_share_{aircraft_type}"]
                        / 100
                        * np.sqrt(
                            input_data[f"{pathway.name}_emission_index_particles_number"]
                            / default_emission_index_number_particles
                        )
                    ).fillna(0)

                fuel_effect_correction_contrails += (
                    distance_share_dropin_fuel * relative_particles_number
                )
            elif aircraft_type == "hydrogen":
                fuel_effect_correction_contrails += (
                    input_data["total_aircraft_distance_hydrogen"]
                    / input_data["total_aircraft_distance"]
                    * input_data["contrails_relative_effect_hydrogen_wrt_kerosene"]
                )
            elif aircraft_type == "electric":
                pass
            else:
                warnings.warn(f"Aircraft type '{aircraft_type}' not supported.", UserWarning)

        output_data = {
            "fuel_effect_correction_contrails": fuel_effect_correction_contrails,
        }

        self._store_outputs(output_data)
        return output_data


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

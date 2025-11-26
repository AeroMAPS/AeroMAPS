"""
non_co2
===============

Module for computing non-CO2 climate effects related to aircraft operations,
including contrail-related adjustments and fuel-effect corrections used in ERF
calculations.
"""

import warnings
from typing import Tuple
from numbers import Number

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.utils.defaults import get_default_series


class OperationsContrailsSimple(AeroMAPSModel):
    """Simple operational model computing contrails gains for ERF calculation and overconsumption associated with contrail avoidance.

    Parameters
    ----------
    name
        Name of the model instance ('operations_contrails_simple' by default).
    """

    def __init__(self, name="operations_contrails_simple", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        operations_contrails_final_gain: float,
        operations_contrails_final_overconsumption: float,
        operations_contrails_start_year: Number,
        operations_contrails_duration: float,
    ) -> Tuple[pd.Series, pd.Series]:
        """Execute computation for contrails gains for ERF calculation and overconsumption associated with contrail avoidance.

        Parameters
        ----------
        operations_contrails_final_gain
            Final impact of contrail operational improvements in terms of percentage reduction in contrails climate impacts [%].
        operations_contrails_final_overconsumption
            Final impact of contrail operational improvements in terms of percentage increase in fuel consumption [%].
        operations_contrails_start_year
            Start year for implementing contrail operational improvements to reduce contrail climate impacts [yr].
        operations_contrails_duration
            Duration for implementing 98% of contrail operational improvements to reduce contrail climate impacts [yr].

        Returns
        -------
        operations_contrails_gain
            Impact of contrail operational improvements in terms of percentage reduction in contrails climate impacts [%].
        operations_contrails_overconsumption
            Impact of contrail operational improvements in terms of percentage increase in fuel consumption [%].
        """

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
    """Compute fuel-effect on contrails for ERF calculation.

    This custom model aggregates pathway-specific particle emission indices and
    distance shares to compute a correction applied to contrail
    forcing to reflect fuel/pathway effects.

    Parameters
    ----------
    name
        Name of the model instance ('fuel_effect_correction_contrails' by default).

    Attributes
    ----------
    pathways_manager
        EnergyCarrierManager instance managing the energy carriers pathways considered in the scenario.
    input_names
        Dictionary defining the expected input names for the model.
    output_names
        Dictionary defining the output names for the model.
    """

    def __init__(self, name="fuel_effect_correction_contrails", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
        """Setup input and output names for the model grammar, based on .yaml configuration of energy carriers."""
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
        """Execute the computation of fuel-effect correction for contrails ERF computation.

        Parameters
        ----------
        input_data
            Mapping of input series and scalars required by the model. Expected
            keys include pathway-specific massic shares of each aircraft consumption; particle emission
            indices, total aircraft distances travelled by aircraft type and overall total
            aircraft distance, and contrails_relative_effect_hydrogen_wrt_kerosene
            when hydrogen pathways are present.

        Returns
        -------
        output_data
            Dictionary with key 'fuel_effect_correction_contrails' containing a
            pd.Series multiplicative correction (dimensionless) for contrail
            forcing over the scenario.
        """

        fuel_effect_correction_contrails = get_default_series(
            self.historic_start_year, self.end_year
        )

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            if aircraft_type == "dropin_fuel":
                relative_particles_number = get_default_series(
                    self.historic_start_year, self.end_year
                )
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
    """Model returning a unitary correction (no fuel effect) for contrails.

    Parameters
    ----------
    name
        Name of the model instance ('without_fuel_effect_correction_contrails' by default).
    """

    def __init__(self, name="without_fuel_effect_correction_contrails", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        total_aircraft_distance: pd.Series,
    ) -> pd.Series:
        """Return a multiplicative correction equal to 1 for all years.

        Parameters
        ----------
        total_aircraft_distance
            Total distance travelled by aircraft (based on RPK traffic) [km].
            FIXME: this input is not used in the computation.

        Returns
        -------
        fuel_effect_correction_contrails
            Multiplicative multiplicative correction (dimensionless) for contrail
            forcing over the scenario, equal to 1 for all years.
        """

        for k in range(self.historic_start_year, self.end_year + 1):
            self.df.loc[k, "fuel_effect_correction_contrails"] = 1

        fuel_effect_correction_contrails = self.df["fuel_effect_correction_contrails"]
        return fuel_effect_correction_contrails

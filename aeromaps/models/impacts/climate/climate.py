from typing import Tuple

import numpy as np
import pandas as pd
import os.path as pth

from aeromaps.models.base import (
    AeroMAPSModel,
    GWPStarEquivalentEmissionsFunction,
    AbsoluteGlobalWarmingPotentialCO2Function,
    RunFair,
)
from aeromaps.resources.climate_data import RCP
from aerocm.climate_models.aviation_climate_simulation import AviationClimateSimulation


class ClimateModel(AeroMAPSModel):
    """
    Class to run a climate simulation for aviation emissions using one of the available climate models
    available in AeroCM.
    """

    def __init__(
            self,
            name="climate",
            climate_model: str = "",
            species_settings: dict | None = None,
            model_settings: dict | None = None,
            *args,
            **kwargs
    ):
        super().__init__(name=name, model_type="custom", *args, **kwargs)

        # --- Configuration ---
        self.climate_model = climate_model
        self.species_settings = species_settings
        self.model_settings = model_settings

        # --- Declare input names ---
        self.input_names = [
            "co2_emissions",
            "nox_emissions",
            "h2o_emissions",
            "sulfur_emissions",
            "soot_emissions",
            "total_aircraft_distance",
            "operations_contrails_gain",
            "fuel_effect_correction_contrails",
        ]

        # --- Declare output names ---
        # Mapping between AeroCM model keys and AeroMAPS variable names
        self.mapping = {
            "Total": "total",
            "CO2": "co2",
            "Non-CO2": "non_co2",
            "Contrails": "contrails",
            "NOx - ST O3 increase": "nox_short_term_o3_increase",
            "NOX - CH4 induced O3": "nox_long_term_o3_decrease",
            "NOX - CH4 decrease": "nox_ch4_decrease",
            "NOX - CH4 induced H2O": "nox_stratospheric_water_vapor_decrease",
            "H2O": "h2o",
            "Sulfur": "sulfur",
            "Soot": "soot",
            "Aerosols": "aerosol",
        }

        # Output names list
        self.output_names = []
        for aeromaps_name in self.mapping.values():
            # Temperature increase
            if aeromaps_name == "total":
                var_temp = "temperature_increase_from_aviation"
            else:
                var_temp = f"temperature_increase_from_{aeromaps_name}_from_aviation"
            self.output_names.append(var_temp)

            # Effective Radiative Forcing
            var_erf = f"{aeromaps_name}_erf"
            self.output_names.append(var_erf)

            # Radiative Forcing
            var_rf = f"{aeromaps_name}_rf"
            self.output_names.append(var_rf)

    def compute(self, input_data) -> dict:
        """Run the climate simulation for aviation emissions."""

        # --- Prepare species inventory (and converting to ndarray) ---
        species_inventory = {
            "CO2": input_data["co2_emissions"].to_numpy(),
            "Contrails": input_data["total_aircraft_distance"].to_numpy(),   # TODO: adjust with operations and fuel effect
            "NOx - ST O3 increase": input_data["nox_emissions"].to_numpy(),
            "NOx - CH4 decrease and induced": input_data["nox_emissions"].to_numpy(),
            "H2O": input_data["h2o_emissions"].to_numpy(),
            "Soot": input_data["soot_emissions"].to_numpy(),
            "Sulfur": input_data["sulfur_emissions"].to_numpy(),
        }

        # --- Run climate simulation ---
        results = AviationClimateSimulation(
            self.climate_model,
            self.climate_historic_start_year,
            self.end_year,
            species_inventory,
            self.species_settings,
            self.model_settings
        ).run()

        # --- Convert results from np.ndarray (list) to pd.Series ---
        for key in results.keys():
            for subkey in results[key].keys():
                results[key][subkey] = pd.Series(
                    results[key][subkey],
                    index=pd.RangeIndex(self.climate_historic_start_year, self.end_year + 1),
                )

        # --- Extract results (and store in climate dataframe) ---
        output_data = {}
        for key_in_results, aeromaps_name in self.mapping.items():
            # --- temperature ---
            temp = results[key_in_results]["temperature"]  # get result
            if aeromaps_name == "total":
                var_temp = "temperature_increase_from_aviation"  # create variable name
            else:
                var_temp = f"temperature_increase_from_{aeromaps_name}_from_aviation"  # create variable name
            self.df_climate[var_temp] = temp  # store in dataframe
            output_data[var_temp] = temp  # store in output dictionary

            # --- effective radiative forcing ---
            erf = results[key_in_results]["effective_radiative_forcing"]
            var_erf = f"{aeromaps_name}_erf"
            self.df_climate[var_erf] = erf
            output_data[var_erf] = erf

            # --- radiative forcing ---
            rf = results[key_in_results]["radiative_forcing"]
            var_rf = f"{aeromaps_name}_rf"
            self.df_climate[var_rf] = rf
            output_data[var_rf] = rf

        return output_data

    def _read_climate_configuration(self):
        """
        Read the climate configuration file and set parameters accordingly.
        """
        pass


class TemperatureGWPStar(AeroMAPSModel):
    def __init__(self, name="temperature_gwpstar", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        contrails_gwpstar_variation_duration: float,
        contrails_gwpstar_s_coefficient: float,
        nox_short_term_o3_increase_gwpstar_variation_duration: float,
        nox_short_term_o3_increase_gwpstar_s_coefficient: float,
        nox_long_term_o3_decrease_gwpstar_variation_duration: float,
        nox_long_term_o3_decrease_gwpstar_s_coefficient: float,
        nox_ch4_decrease_gwpstar_variation_duration: float,
        nox_ch4_decrease_gwpstar_s_coefficient: float,
        nox_stratospheric_water_vapor_decrease_gwpstar_variation_duration: float,
        nox_stratospheric_water_vapor_decrease_gwpstar_s_coefficient: float,
        soot_gwpstar_variation_duration: float,
        soot_gwpstar_s_coefficient: float,
        h2o_gwpstar_variation_duration: float,
        h2o_gwpstar_s_coefficient: float,
        sulfur_gwpstar_variation_duration: float,
        sulfur_gwpstar_s_coefficient: float,
        contrails_erf: pd.Series,
        nox_short_term_o3_increase_erf: pd.Series,
        nox_long_term_o3_decrease_erf: pd.Series,
        nox_ch4_decrease_erf: pd.Series,
        nox_stratospheric_water_vapor_decrease_erf: pd.Series,
        soot_erf: pd.Series,
        h2o_erf: pd.Series,
        sulfur_erf: pd.Series,
        co2_erf: pd.Series,
        total_erf: pd.Series,
        co2_emissions: pd.Series,
        tcre_coefficient: float,
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
        """Temperature calculation using equivalent emissions (with GWP* method) and TCRE."""

        # EQUIVALENT EMISSIONS

        ## Contrails
        contrails_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=contrails_erf,
            gwpstar_variation_duration=contrails_gwpstar_variation_duration,
            gwpstar_s_coefficient=contrails_gwpstar_s_coefficient,
        )
        self.df_climate["contrails_equivalent_emissions"] = contrails_equivalent_emissions

        ## NOx short-term O3 increase
        nox_short_term_o3_increase_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_short_term_o3_increase_erf,
            gwpstar_variation_duration=nox_short_term_o3_increase_gwpstar_variation_duration,
            gwpstar_s_coefficient=nox_short_term_o3_increase_gwpstar_s_coefficient,
        )
        self.df_climate["nox_short_term_o3_increase_equivalent_emissions"] = (
            nox_short_term_o3_increase_equivalent_emissions
        )

        ## NOx long-term O3 decrease
        nox_long_term_o3_decrease_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_long_term_o3_decrease_erf,
            gwpstar_variation_duration=nox_long_term_o3_decrease_gwpstar_variation_duration,
            gwpstar_s_coefficient=nox_long_term_o3_decrease_gwpstar_s_coefficient,
        )
        self.df_climate["nox_long_term_o3_decrease_equivalent_emissions"] = (
            nox_long_term_o3_decrease_equivalent_emissions
        )

        ## NOx CH4 decrease
        nox_ch4_decrease_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_ch4_decrease_erf,
            gwpstar_variation_duration=nox_ch4_decrease_gwpstar_variation_duration,
            gwpstar_s_coefficient=nox_ch4_decrease_gwpstar_s_coefficient,
        )
        self.df_climate["nox_ch4_decrease_equivalent_emissions"] = (
            nox_ch4_decrease_equivalent_emissions
        )

        ## NOx stratospheric water vapor decrease
        nox_stratospheric_water_vapor_decrease_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_stratospheric_water_vapor_decrease_erf,
            gwpstar_variation_duration=nox_stratospheric_water_vapor_decrease_gwpstar_variation_duration,
            gwpstar_s_coefficient=nox_stratospheric_water_vapor_decrease_gwpstar_s_coefficient,
        )
        self.df_climate["nox_stratospheric_water_vapor_decrease_equivalent_emissions"] = (
            nox_stratospheric_water_vapor_decrease_equivalent_emissions
        )

        ## Soot
        soot_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=soot_erf,
            gwpstar_variation_duration=soot_gwpstar_variation_duration,
            gwpstar_s_coefficient=soot_gwpstar_s_coefficient,
        )
        self.df_climate["soot_equivalent_emissions"] = soot_equivalent_emissions

        ## H2O
        h2o_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=h2o_erf,
            gwpstar_variation_duration=h2o_gwpstar_variation_duration,
            gwpstar_s_coefficient=h2o_gwpstar_s_coefficient,
        )
        self.df_climate["h2o_equivalent_emissions"] = h2o_equivalent_emissions

        ## Sulfur
        sulfur_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=sulfur_erf,
            gwpstar_variation_duration=sulfur_gwpstar_variation_duration,
            gwpstar_s_coefficient=sulfur_gwpstar_s_coefficient,
        )
        self.df_climate["sulfur_equivalent_emissions"] = sulfur_equivalent_emissions

        ## Total
        non_co2_equivalent_emissions = (
            contrails_equivalent_emissions
            + nox_short_term_o3_increase_equivalent_emissions
            + nox_long_term_o3_decrease_equivalent_emissions
            + nox_ch4_decrease_equivalent_emissions
            + nox_stratospheric_water_vapor_decrease_equivalent_emissions
            + soot_equivalent_emissions
            + h2o_equivalent_emissions
            + sulfur_equivalent_emissions
        )
        total_equivalent_emissions = co2_emissions + non_co2_equivalent_emissions
        self.df_climate["non_co2_equivalent_emissions"] = non_co2_equivalent_emissions
        self.df_climate["total_equivalent_emissions"] = total_equivalent_emissions

        ## Cumulative CO2, non-CO2 and total equivalent emissions (Gtwe)

        ### From 1940
        self.df_climate.loc[
            self.climate_historic_start_year, "historical_cumulative_co2_emissions"
        ] = co2_emissions.loc[self.climate_historic_start_year] / 1000
        self.df_climate.loc[
            self.climate_historic_start_year, "historical_cumulative_contrails_equivalent_emissions"
        ] = contrails_equivalent_emissions.loc[self.climate_historic_start_year] / 1000
        self.df_climate.loc[
            self.climate_historic_start_year,
            "historical_cumulative_nox_short_term_o3_increase_equivalent_emissions",
        ] = (
            nox_short_term_o3_increase_equivalent_emissions.loc[self.climate_historic_start_year]
            / 1000
        )
        self.df_climate.loc[
            self.climate_historic_start_year,
            "historical_cumulative_nox_long_term_o3_decrease_equivalent_emissions",
        ] = (
            nox_long_term_o3_decrease_equivalent_emissions.loc[self.climate_historic_start_year]
            / 1000
        )
        self.df_climate.loc[
            self.climate_historic_start_year,
            "historical_cumulative_nox_ch4_decrease_equivalent_emissions",
        ] = nox_ch4_decrease_equivalent_emissions.loc[self.climate_historic_start_year] / 1000
        self.df_climate.loc[
            self.climate_historic_start_year,
            "historical_cumulative_nox_stratospheric_water_vapor_decrease_equivalent_emissions",
        ] = (
            nox_stratospheric_water_vapor_decrease_equivalent_emissions.loc[
                self.climate_historic_start_year
            ]
            / 1000
        )
        self.df_climate.loc[
            self.climate_historic_start_year, "historical_cumulative_soot_equivalent_emissions"
        ] = soot_equivalent_emissions.loc[self.climate_historic_start_year] / 1000
        self.df_climate.loc[
            self.climate_historic_start_year, "historical_cumulative_h2o_equivalent_emissions"
        ] = h2o_equivalent_emissions.loc[self.climate_historic_start_year] / 1000
        self.df_climate.loc[
            self.climate_historic_start_year, "historical_cumulative_sulfur_equivalent_emissions"
        ] = sulfur_equivalent_emissions.loc[self.climate_historic_start_year] / 1000
        self.df_climate.loc[
            self.climate_historic_start_year, "historical_cumulative_non_co2_equivalent_emissions"
        ] = non_co2_equivalent_emissions[self.climate_historic_start_year] / 1000
        for k in range(self.climate_historic_start_year + 1, self.end_year + 1):
            self.df_climate.loc[k, "historical_cumulative_co2_emissions"] = (
                self.df_climate.loc[k - 1, "historical_cumulative_co2_emissions"]
                + co2_emissions.loc[k] / 1000
            )
            self.df_climate.loc[k, "historical_cumulative_contrails_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "historical_cumulative_contrails_equivalent_emissions"]
                + contrails_equivalent_emissions.loc[k] / 1000
            )
            self.df_climate.loc[
                k, "historical_cumulative_nox_short_term_o3_increase_equivalent_emissions"
            ] = (
                self.df_climate.loc[
                    k - 1, "historical_cumulative_nox_short_term_o3_increase_equivalent_emissions"
                ]
                + nox_short_term_o3_increase_equivalent_emissions.loc[k] / 1000
            )
            self.df_climate.loc[
                k, "historical_cumulative_nox_long_term_o3_decrease_equivalent_emissions"
            ] = (
                self.df_climate.loc[
                    k - 1, "historical_cumulative_nox_long_term_o3_decrease_equivalent_emissions"
                ]
                + nox_long_term_o3_decrease_equivalent_emissions.loc[k] / 1000
            )
            self.df_climate.loc[
                k, "historical_cumulative_nox_ch4_decrease_equivalent_emissions"
            ] = (
                self.df_climate.loc[
                    k - 1, "historical_cumulative_nox_ch4_decrease_equivalent_emissions"
                ]
                + nox_ch4_decrease_equivalent_emissions.loc[k] / 1000
            )
            self.df_climate.loc[
                k,
                "historical_cumulative_nox_stratospheric_water_vapor_decrease_equivalent_emissions",
            ] = (
                self.df_climate.loc[
                    k - 1,
                    "historical_cumulative_nox_stratospheric_water_vapor_decrease_equivalent_emissions",
                ]
                + nox_stratospheric_water_vapor_decrease_equivalent_emissions.loc[k] / 1000
            )
            self.df_climate.loc[k, "historical_cumulative_soot_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "historical_cumulative_soot_equivalent_emissions"]
                + soot_equivalent_emissions.loc[k] / 1000
            )
            self.df_climate.loc[k, "historical_cumulative_h2o_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "historical_cumulative_h2o_equivalent_emissions"]
                + h2o_equivalent_emissions.loc[k] / 1000
            )
            self.df_climate.loc[k, "historical_cumulative_sulfur_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "historical_cumulative_sulfur_equivalent_emissions"]
                + sulfur_equivalent_emissions.loc[k] / 1000
            )

            self.df_climate.loc[k, "historical_cumulative_non_co2_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "historical_cumulative_non_co2_equivalent_emissions"]
                + non_co2_equivalent_emissions.loc[k] / 1000
            )

        historical_cumulative_co2_emissions = self.df_climate["historical_cumulative_co2_emissions"]
        historical_cumulative_contrails_equivalent_emissions = self.df_climate[
            "historical_cumulative_contrails_equivalent_emissions"
        ]
        historical_cumulative_nox_short_term_o3_increase_equivalent_emissions = self.df_climate[
            "historical_cumulative_nox_short_term_o3_increase_equivalent_emissions"
        ]
        historical_cumulative_nox_long_term_o3_decrease_equivalent_emissions = self.df_climate[
            "historical_cumulative_nox_long_term_o3_decrease_equivalent_emissions"
        ]
        historical_cumulative_nox_ch4_decrease_equivalent_emissions = self.df_climate[
            "historical_cumulative_nox_ch4_decrease_equivalent_emissions"
        ]
        historical_cumulative_nox_stratospheric_water_vapor_decrease_equivalent_emissions = (
            self.df_climate[
                "historical_cumulative_nox_stratospheric_water_vapor_decrease_equivalent_emissions"
            ]
        )
        historical_cumulative_soot_equivalent_emissions = self.df_climate[
            "historical_cumulative_soot_equivalent_emissions"
        ]
        historical_cumulative_h2o_equivalent_emissions = self.df_climate[
            "historical_cumulative_h2o_equivalent_emissions"
        ]
        historical_cumulative_sulfur_equivalent_emissions = self.df_climate[
            "historical_cumulative_sulfur_equivalent_emissions"
        ]
        historical_cumulative_non_co2_equivalent_emissions = self.df_climate[
            "historical_cumulative_non_co2_equivalent_emissions"
        ]
        historical_cumulative_total_equivalent_emissions = (
            historical_cumulative_co2_emissions + historical_cumulative_non_co2_equivalent_emissions
        )
        self.df_climate["cumulative_total_equivalent_emissions"] = (
            historical_cumulative_total_equivalent_emissions
        )

        ### From 2020
        self.df_climate.loc[
            self.prospection_start_year - 1, "cumulative_non_co2_equivalent_emissions"
        ] = 0.0
        self.df_climate.loc[
            self.prospection_start_year - 1, "cumulative_total_equivalent_emissions"
        ] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df_climate.loc[k, "cumulative_non_co2_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "cumulative_non_co2_equivalent_emissions"]
                + non_co2_equivalent_emissions.loc[k] / 1000
            )
            self.df_climate.loc[k, "cumulative_total_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "cumulative_total_equivalent_emissions"]
                + total_equivalent_emissions.loc[k] / 1000
            )
        cumulative_non_co2_equivalent_emissions = self.df_climate[
            "cumulative_non_co2_equivalent_emissions"
        ]
        cumulative_total_equivalent_emissions = self.df_climate[
            "cumulative_total_equivalent_emissions"
        ]

        ## Share CO2/non-CO2
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "total_co2_equivalent_emissions_ratio"] = (
                total_equivalent_emissions.loc[k] / co2_emissions.loc[k]
            )
        total_co2_equivalent_emissions_ratio = self.df_climate[
            "total_co2_equivalent_emissions_ratio"
        ]

        co2_total_erf_ratio = co2_erf / total_erf * 100
        self.df_climate.loc[:, "co2_total_erf_ratio"] = co2_total_erf_ratio

        # TEMPERATURE

        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "temperature_increase_from_co2_from_aviation"] = (
                tcre_coefficient * historical_cumulative_co2_emissions.loc[k]
            )
            self.df_climate.loc[k, "temperature_increase_from_contrails_from_aviation"] = (
                tcre_coefficient * historical_cumulative_contrails_equivalent_emissions.loc[k]
            )
            self.df_climate.loc[
                k, "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
            ] = (
                tcre_coefficient
                * historical_cumulative_nox_short_term_o3_increase_equivalent_emissions.loc[k]
            )
            self.df_climate.loc[
                k, "temperature_increase_from_nox_long_term_o3_decrease_from_aviation"
            ] = (
                tcre_coefficient
                * historical_cumulative_nox_long_term_o3_decrease_equivalent_emissions.loc[k]
            )
            self.df_climate.loc[k, "temperature_increase_from_nox_ch4_decrease_from_aviation"] = (
                tcre_coefficient
                * historical_cumulative_nox_ch4_decrease_equivalent_emissions.loc[k]
            )
            self.df_climate.loc[
                k, "temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation"
            ] = (
                tcre_coefficient
                * historical_cumulative_nox_stratospheric_water_vapor_decrease_equivalent_emissions.loc[
                    k
                ]
            )
            self.df_climate.loc[k, "temperature_increase_from_soot_from_aviation"] = (
                tcre_coefficient * historical_cumulative_soot_equivalent_emissions.loc[k]
            )
            self.df_climate.loc[k, "temperature_increase_from_h2o_from_aviation"] = (
                tcre_coefficient * historical_cumulative_h2o_equivalent_emissions.loc[k]
            )
            self.df_climate.loc[k, "temperature_increase_from_sulfur_from_aviation"] = (
                tcre_coefficient * historical_cumulative_sulfur_equivalent_emissions.loc[k]
            )
            self.df_climate.loc[k, "temperature_increase_from_non_co2_from_aviation"] = (
                tcre_coefficient * historical_cumulative_non_co2_equivalent_emissions.loc[k]
            )
        temperature_increase_from_co2_from_aviation = self.df_climate[
            "temperature_increase_from_co2_from_aviation"
        ]
        temperature_increase_from_contrails_from_aviation = self.df_climate[
            "temperature_increase_from_contrails_from_aviation"
        ]
        temperature_increase_from_nox_short_term_o3_increase_from_aviation = self.df_climate[
            "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
        ]
        temperature_increase_from_nox_long_term_o3_decrease_from_aviation = self.df_climate[
            "temperature_increase_from_nox_long_term_o3_decrease_from_aviation"
        ]
        temperature_increase_from_nox_ch4_decrease_from_aviation = self.df_climate[
            "temperature_increase_from_nox_ch4_decrease_from_aviation"
        ]
        temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation = (
            self.df_climate[
                "temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation"
            ]
        )
        temperature_increase_from_h2o_from_aviation = self.df_climate[
            "temperature_increase_from_h2o_from_aviation"
        ]
        temperature_increase_from_soot_from_aviation = self.df_climate[
            "temperature_increase_from_soot_from_aviation"
        ]
        temperature_increase_from_sulfur_from_aviation = self.df_climate[
            "temperature_increase_from_sulfur_from_aviation"
        ]
        temperature_increase_from_non_co2_from_aviation = self.df_climate[
            "temperature_increase_from_non_co2_from_aviation"
        ]
        temperature_increase_from_aviation = (
            temperature_increase_from_co2_from_aviation
            + temperature_increase_from_non_co2_from_aviation
        )
        self.df_climate["temperature_increase_from_aviation"] = temperature_increase_from_aviation

        return (
            contrails_equivalent_emissions,
            nox_short_term_o3_increase_equivalent_emissions,
            nox_long_term_o3_decrease_equivalent_emissions,
            nox_ch4_decrease_equivalent_emissions,
            nox_stratospheric_water_vapor_decrease_equivalent_emissions,
            soot_equivalent_emissions,
            h2o_equivalent_emissions,
            sulfur_equivalent_emissions,
            non_co2_equivalent_emissions,
            cumulative_non_co2_equivalent_emissions,
            total_equivalent_emissions,
            cumulative_total_equivalent_emissions,
            total_co2_equivalent_emissions_ratio,
            co2_total_erf_ratio,
            temperature_increase_from_aviation,
            temperature_increase_from_co2_from_aviation,
            temperature_increase_from_non_co2_from_aviation,
            temperature_increase_from_contrails_from_aviation,
            temperature_increase_from_nox_short_term_o3_increase_from_aviation,
            temperature_increase_from_nox_long_term_o3_decrease_from_aviation,
            temperature_increase_from_nox_ch4_decrease_from_aviation,
            temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation,
            temperature_increase_from_h2o_from_aviation,
            temperature_increase_from_sulfur_from_aviation,
            temperature_increase_from_soot_from_aviation,
        )


class TemperatureSimpleGWPStar(AeroMAPSModel):
    def __init__(self, name="temperature_simple_gwpstar", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        total_erf: pd.Series,
        co2_erf: pd.Series,
        co2_emissions: pd.Series,
        tcre_coefficient: float,
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
    ]:
        """Temperature calculation using equivalent emissions (with simple and smooth GWP* method) and TCRE."""

        # EQUIVALENT EMISSIONS

        # Smooth on 5 years (except for extrem values)

        self.df_climate.loc[self.climate_historic_start_year, "total_erf_smooth"] = (
            total_erf.loc[self.climate_historic_start_year]
            + total_erf.loc[self.climate_historic_start_year + 1]
            + total_erf.loc[self.climate_historic_start_year + 2]
        ) / 3
        self.df_climate.loc[self.climate_historic_start_year, "co2_erf_smooth"] = (
            co2_erf.loc[self.climate_historic_start_year]
            + co2_erf.loc[self.climate_historic_start_year + 1]
            + co2_erf.loc[self.climate_historic_start_year + 2]
        ) / 3
        self.df_climate.loc[self.climate_historic_start_year, "co2_emissions_smooth"] = (
            co2_emissions.loc[self.climate_historic_start_year]
            + co2_emissions.loc[self.climate_historic_start_year + 1]
            + co2_emissions.loc[self.climate_historic_start_year + 2]
        ) / 3

        self.df_climate.loc[self.climate_historic_start_year + 1, "total_erf_smooth"] = (
            total_erf.loc[self.climate_historic_start_year]
            + total_erf.loc[self.climate_historic_start_year + 1]
            + total_erf.loc[self.climate_historic_start_year + 2]
            + total_erf.loc[self.climate_historic_start_year + 3]
        ) / 4
        self.df_climate.loc[self.climate_historic_start_year + 1, "co2_erf_smooth"] = (
            co2_erf.loc[self.climate_historic_start_year]
            + co2_erf.loc[self.climate_historic_start_year + 1]
            + co2_erf.loc[self.climate_historic_start_year + 2]
            + co2_erf.loc[self.climate_historic_start_year + 3]
        ) / 4
        self.df_climate.loc[self.climate_historic_start_year + 1, "co2_emissions_smooth"] = (
            co2_emissions.loc[self.climate_historic_start_year]
            + co2_emissions.loc[self.climate_historic_start_year + 1]
            + co2_emissions.loc[self.climate_historic_start_year + 2]
            + co2_emissions.loc[self.climate_historic_start_year + 3]
        ) / 4

        for k in range(self.climate_historic_start_year + 2, self.end_year - 1):
            self.df_climate.loc[k, "total_erf_smooth"] = (
                total_erf.loc[k - 2]
                + total_erf.loc[k - 1]
                + total_erf.loc[k]
                + total_erf.loc[k + 1]
                + total_erf.loc[k + 2]
            ) / 5
            self.df_climate.loc[k, "co2_erf_smooth"] = (
                co2_erf.loc[k - 2]
                + co2_erf.loc[k - 1]
                + co2_erf.loc[k]
                + co2_erf.loc[k + 1]
                + co2_erf.loc[k + 2]
            ) / 5
            self.df_climate.loc[k, "co2_emissions_smooth"] = (
                co2_emissions.loc[k - 2]
                + co2_emissions.loc[k - 1]
                + co2_emissions.loc[k]
                + co2_emissions.loc[k + 1]
                + co2_emissions.loc[k + 2]
            ) / 5

        self.df_climate.loc[self.end_year - 1, "total_erf_smooth"] = (
            total_erf.loc[self.end_year - 3]
            + total_erf.loc[self.end_year - 2]
            + total_erf.loc[self.end_year - 1]
            + total_erf.loc[self.end_year]
        ) / 4
        self.df_climate.loc[self.end_year - 1, "co2_erf_smooth"] = (
            co2_erf.loc[self.end_year - 3]
            + co2_erf.loc[self.end_year - 2]
            + co2_erf.loc[self.end_year - 1]
            + co2_erf.loc[self.end_year]
        ) / 4
        self.df_climate.loc[self.end_year - 1, "co2_emissions_smooth"] = (
            co2_emissions.loc[self.end_year - 3]
            + co2_emissions.loc[self.end_year - 2]
            + co2_emissions.loc[self.end_year - 1]
            + co2_emissions.loc[self.end_year]
        ) / 4

        self.df_climate.loc[self.end_year, "total_erf_smooth"] = (
            total_erf.loc[self.end_year - 2]
            + total_erf.loc[self.end_year - 1]
            + total_erf.loc[self.end_year]
        ) / 3
        self.df_climate.loc[self.end_year, "co2_erf_smooth"] = (
            co2_erf.loc[self.end_year - 2]
            + co2_erf.loc[self.end_year - 1]
            + co2_erf.loc[self.end_year]
        ) / 3
        self.df_climate.loc[self.end_year, "co2_emissions_smooth"] = (
            co2_emissions.loc[self.end_year - 2]
            + co2_emissions.loc[self.end_year - 1]
            + co2_emissions.loc[self.end_year]
        ) / 3

        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "non_co2_erf_smooth"] = (
                self.df_climate.loc[k, "total_erf_smooth"]
                - self.df_climate.loc[k, "co2_erf_smooth"]
            )

        total_erf_smooth = self.df_climate["total_erf_smooth"]
        co2_erf_smooth = self.df_climate["co2_erf_smooth"]
        co2_emissions_smooth = self.df_climate["co2_emissions_smooth"]
        non_co2_erf_smooth = self.df_climate["non_co2_erf_smooth"]

        # Equivalent emissions (Mtwe)

        ## DeltaF/Deltat
        gwpstar_variation_duration = 20
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            if k - self.climate_historic_start_year >= gwpstar_variation_duration:
                self.df_climate.loc[k, "non_co2_erf_smooth_variation"] = (
                    self.df_climate.loc[k, "non_co2_erf_smooth"]
                    - self.df_climate.loc[k - gwpstar_variation_duration, "non_co2_erf_smooth"]
                ) / gwpstar_variation_duration
            else:
                self.df_climate.loc[k, "non_co2_erf_smooth_variation"] = (
                    self.df_climate.loc[k, "non_co2_erf_smooth"] / gwpstar_variation_duration
                )
        non_co2_erf_smooth_variation = self.df_climate["non_co2_erf_smooth_variation"]

        ## Non-CO2 equivalent emissions
        climate_time_horizon = 100
        co2_agwp_h = AbsoluteGlobalWarmingPotentialCO2Function(climate_time_horizon)
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "non_co2_equivalent_emissions"] = (
                self.df_climate.loc[k, "non_co2_erf_smooth_variation"]
                * climate_time_horizon
                / co2_agwp_h
            )
        non_co2_equivalent_emissions = self.df_climate["non_co2_equivalent_emissions"]

        ## Total equivalent emissions
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "total_equivalent_emissions"] = (
                self.df_climate.loc[k, "non_co2_equivalent_emissions"]
                + self.df_climate.loc[k, "co2_emissions_smooth"]
            )
        total_equivalent_emissions = self.df_climate["total_equivalent_emissions"]

        ## Cumulative smooth CO2, non-CO2 and total equivalent emissions (Gtwe)

        ### From 1940
        self.df_climate.loc[
            self.climate_historic_start_year, "historical_cumulative_co2_emissions_smooth"
        ] = co2_emissions_smooth.loc[self.climate_historic_start_year] / 1000
        self.df_climate.loc[
            self.climate_historic_start_year, "historical_cumulative_non_co2_equivalent_emissions"
        ] = non_co2_equivalent_emissions[self.climate_historic_start_year] / 1000
        for k in range(self.climate_historic_start_year + 1, self.end_year + 1):
            self.df_climate.loc[k, "historical_cumulative_co2_emissions_smooth"] = (
                self.df_climate.loc[k - 1, "historical_cumulative_co2_emissions_smooth"]
                + co2_emissions_smooth.loc[k] / 1000
            )
            self.df_climate.loc[k, "historical_cumulative_non_co2_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "historical_cumulative_non_co2_equivalent_emissions"]
                + non_co2_equivalent_emissions.loc[k] / 1000
            )
        historical_cumulative_co2_emissions_smooth = self.df_climate[
            "historical_cumulative_co2_emissions_smooth"
        ]
        historical_cumulative_non_co2_equivalent_emissions = self.df_climate[
            "historical_cumulative_non_co2_equivalent_emissions"
        ]
        historical_cumulative_total_equivalent_emissions = (
            historical_cumulative_co2_emissions_smooth
            + historical_cumulative_non_co2_equivalent_emissions
        )
        self.df_climate["cumulative_total_equivalent_emissions"] = (
            historical_cumulative_total_equivalent_emissions
        )

        ### From 2020
        self.df_climate.loc[self.prospection_start_year - 1, "cumulative_co2_emissions_smooth"] = (
            0.0
        )
        self.df_climate.loc[
            self.prospection_start_year - 1, "cumulative_non_co2_equivalent_emissions"
        ] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df_climate.loc[k, "cumulative_co2_emissions_smooth"] = (
                self.df_climate.loc[k - 1, "cumulative_co2_emissions_smooth"]
                + co2_emissions_smooth.loc[k] / 1000
            )
            self.df_climate.loc[k, "cumulative_non_co2_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "cumulative_non_co2_equivalent_emissions"]
                + non_co2_equivalent_emissions.loc[k] / 1000
            )
        cumulative_co2_emissions_smooth = self.df_climate["cumulative_co2_emissions_smooth"]
        cumulative_non_co2_equivalent_emissions = self.df_climate[
            "cumulative_non_co2_equivalent_emissions"
        ]
        cumulative_total_equivalent_emissions = (
            cumulative_co2_emissions_smooth + cumulative_non_co2_equivalent_emissions
        )
        self.df_climate["cumulative_total_equivalent_emissions"] = (
            cumulative_total_equivalent_emissions
        )

        ## Share CO2/non-CO2
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "total_co2_equivalent_emissions_ratio"] = (
                total_equivalent_emissions.loc[k] / co2_emissions.loc[k]
            )
        total_co2_equivalent_emissions_ratio = self.df_climate[
            "total_co2_equivalent_emissions_ratio"
        ]

        co2_total_erf_ratio = co2_erf / total_erf * 100
        self.df_climate.loc[:, "co2_total_erf_ratio"] = co2_total_erf_ratio

        # TEMPERATURE

        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "temperature_increase_from_co2_from_aviation"] = (
                tcre_coefficient * historical_cumulative_co2_emissions_smooth.loc[k]
            )
            self.df_climate.loc[k, "temperature_increase_from_non_co2_from_aviation"] = (
                tcre_coefficient * historical_cumulative_non_co2_equivalent_emissions.loc[k]
            )
        temperature_increase_from_co2_from_aviation = self.df_climate[
            "temperature_increase_from_co2_from_aviation"
        ]
        temperature_increase_from_non_co2_from_aviation = self.df_climate[
            "temperature_increase_from_non_co2_from_aviation"
        ]

        temperature_increase_from_aviation = (
            temperature_increase_from_co2_from_aviation
            + temperature_increase_from_non_co2_from_aviation
        )
        self.df_climate["temperature_increase_from_aviation"] = temperature_increase_from_aviation

        return (
            total_erf_smooth,
            co2_erf_smooth,
            co2_emissions_smooth,
            cumulative_co2_emissions_smooth,
            non_co2_erf_smooth,
            non_co2_erf_smooth_variation,
            non_co2_equivalent_emissions,
            cumulative_non_co2_equivalent_emissions,
            total_equivalent_emissions,
            cumulative_total_equivalent_emissions,
            total_co2_equivalent_emissions_ratio,
            co2_total_erf_ratio,
            temperature_increase_from_aviation,
            temperature_increase_from_co2_from_aviation,
            temperature_increase_from_non_co2_from_aviation,
        )


class TemperatureFair(AeroMAPSModel):
    def __init__(self, name="temperature_fair", *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        # Load dataset
        rcp26_data_path = pth.join(RCP.__path__[0], "RCP26.csv")
        rcp26_data_df = pd.read_csv(rcp26_data_path)
        self.rcp26_data_df = rcp26_data_df
        rcp45_data_path = pth.join(RCP.__path__[0], "RCP45.csv")
        rcp45_data_df = pd.read_csv(rcp45_data_path)
        self.rcp45_data_df = rcp45_data_df
        rcp60_data_path = pth.join(RCP.__path__[0], "RCP60.csv")
        rcp60_data_df = pd.read_csv(rcp60_data_path)
        self.rcp60_data_df = rcp60_data_df
        rcp85_data_path = pth.join(RCP.__path__[0], "RCP85.csv")
        rcp85_data_df = pd.read_csv(rcp85_data_path)
        self.rcp85_data_df = rcp85_data_df

    def compute(
        self,
        co2_emissions: pd.Series,
        contrails_erf: pd.Series,
        nox_short_term_o3_increase_erf: pd.Series,
        nox_long_term_o3_decrease_erf: pd.Series,
        nox_ch4_decrease_erf: pd.Series,
        nox_stratospheric_water_vapor_decrease_erf: pd.Series,
        h2o_erf: pd.Series,
        sulfur_emissions: pd.Series,
        soot_emissions: pd.Series,
        nox_long_term_o3_decrease_gwpstar_variation_duration: float,
        nox_long_term_o3_decrease_gwpstar_s_coefficient: float,
        nox_ch4_decrease_gwpstar_variation_duration: float,
        nox_ch4_decrease_gwpstar_s_coefficient: float,
        nox_stratospheric_water_vapor_decrease_gwpstar_variation_duration: float,
        nox_stratospheric_water_vapor_decrease_gwpstar_s_coefficient: float,
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
    ]:
        """Temperature calculation using FaIR."""

        # SPECIES QUANTITIES
        species_quantities = np.zeros((11, self.end_year - 1765 + 1))
        rcp_data_df = self.rcp45_data_df

        ## CO2

        ### World CO2
        species_quantities[0] = (
            (
                rcp_data_df["FossilCO2"][0 : self.end_year - 1765 + 1].values
                + rcp_data_df["OtherCO2"][0 : self.end_year - 1765 + 1].values
            )
            * 44
            / 12
        )  # Conversion from GtC to GtCO2

        ### Aviation CO2
        species_quantities[1] = np.zeros(len(species_quantities[0]))
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            species_quantities[1][k - 1765] = (
                co2_emissions.loc[k] / 1000
            )  # Conversion from MtCO2 to GtCO2

        ### Aviation NOx - Long-term O3 decrease
        species_quantities[2] = np.zeros(len(species_quantities[0]))
        nox_long_term_o3_decrease_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_long_term_o3_decrease_erf,
            gwpstar_variation_duration=nox_long_term_o3_decrease_gwpstar_variation_duration,
            gwpstar_s_coefficient=nox_long_term_o3_decrease_gwpstar_s_coefficient,
        )
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            species_quantities[2][k - 1765] = (
                nox_long_term_o3_decrease_equivalent_emissions.loc[k] / 1000
            )  # Conversion from MtCO2-we to GtCO2-we

        ### Aviation NOx - CH4 decrease
        species_quantities[3] = np.zeros(len(species_quantities[0]))
        nox_ch4_decrease_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_ch4_decrease_erf,
            gwpstar_variation_duration=nox_ch4_decrease_gwpstar_variation_duration,
            gwpstar_s_coefficient=nox_ch4_decrease_gwpstar_s_coefficient,
        )
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            species_quantities[3][k - 1765] = (
                nox_ch4_decrease_equivalent_emissions.loc[k] / 1000
            )  # Conversion from MtCO2-we  to GtCO2-we

        ### Aviation NOx - Stratospheric water vapor decrease
        species_quantities[4] = np.zeros(len(species_quantities[0]))
        nox_stratospheric_water_vapor_decrease_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_stratospheric_water_vapor_decrease_erf,
            gwpstar_variation_duration=nox_stratospheric_water_vapor_decrease_gwpstar_variation_duration,
            gwpstar_s_coefficient=nox_stratospheric_water_vapor_decrease_gwpstar_s_coefficient,
        )
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            species_quantities[4][k - 1765] = (
                nox_stratospheric_water_vapor_decrease_equivalent_emissions.loc[k] / 1000
            )  # Conversion from MtCO2-we  to GtCO2-we

        ## World CH4
        species_quantities[5] = rcp_data_df["CH4"][
            0 : self.end_year - 1765 + 1
        ].values  # Unit: MtCH4

        ## Aviation contrails
        species_quantities[6] = np.zeros(len(species_quantities[0]))
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            species_quantities[6][k - 1765] = (
                contrails_erf.loc[k] / 1000
            )  # Conversion from mW/m² to W/m²

        ## Aviation NOx - Short-term O3 increase
        species_quantities[7] = np.zeros(len(species_quantities[0]))
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            species_quantities[7][k - 1765] = (
                nox_short_term_o3_increase_erf.loc[k] / 1000
            )  # Conversion from mW/m² to W/m²

        ## Aviation H2O
        species_quantities[8] = np.zeros(len(species_quantities[0]))
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            species_quantities[8][k - 1765] = h2o_erf.loc[k] / 1000  # Conversion from mW/m² to W/m²

        ## Aviation sulfur
        species_quantities[9] = np.zeros(len(species_quantities[0]))
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            species_quantities[9][k - 1765] = sulfur_emissions.loc[k]  # Unit: MtSO2

        ## Aviation soot
        species_quantities[10] = np.zeros(len(species_quantities[0]))
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            species_quantities[10][k - 1765] = soot_emissions.loc[k]  # Unit: MtBC

        # TEMPERATURE ESTIMATION

        ## Total temperature and forcing (world + aviation)
        total_temperature_list, total_forcing_list = RunFair(
            self,
            species_quantities,
        )
        ## Temperature increase due to aviation species
        total_temperature_without_co2_list, total_forcing_without_co2_list = RunFair(
            self,
            species_quantities,
            without="Aviation CO2",
        )
        temperature_increase_from_co2_from_aviation_list = (
            total_temperature_list - total_temperature_without_co2_list
        )
        co2_erf_list = 1000 * (total_forcing_list - total_forcing_without_co2_list)
        temperature_increase_from_contrails_from_aviation_list = (
            total_temperature_list
            - RunFair(
                self,
                species_quantities,
                without="Aviation contrails",
            )[0]
        )
        temperature_increase_from_nox_short_term_o3_increase_from_aviation_list = (
            total_temperature_list
            - RunFair(
                self,
                species_quantities,
                without="Aviation NOx ST O3 increase",
            )[0]
        )
        temperature_increase_from_nox_long_term_o3_decrease_from_aviation_list = (
            total_temperature_list
            - RunFair(
                self,
                species_quantities,
                without="Aviation NOx LT O3 decrease",
            )[0]
        )
        temperature_increase_from_nox_ch4_decrease_from_aviation_list = (
            total_temperature_list
            - RunFair(
                self,
                species_quantities,
                without="Aviation NOx CH4 decrease",
            )[0]
        )
        temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation_list = (
            total_temperature_list
            - RunFair(
                self,
                species_quantities,
                without="Aviation NOx H2O decrease",
            )[0]
        )
        temperature_increase_from_h2o_from_aviation_list = (
            total_temperature_list
            - RunFair(
                self,
                species_quantities,
                without="Aviation H2O",
            )[0]
        )
        temperature_increase_from_sulfur_from_aviation_list = (
            total_temperature_list
            - RunFair(
                self,
                species_quantities,
                without="Aviation sulfur",
            )[0]
        )
        temperature_increase_from_soot_from_aviation_list = (
            total_temperature_list
            - RunFair(
                self,
                species_quantities,
                without="Aviation soot",
            )[0]
        )
        # temperature_increase_from_aviation_list = total_temperature_list - RunFair(
        #     self,
        #     species_quantities,
        #     without="All aviation",
        # )

        ## List to dataframe
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "temperature_increase_from_co2_from_aviation"] = (
                temperature_increase_from_co2_from_aviation_list[k - 1765]
            )
            self.df_climate.loc[k, "co2_erf"] = co2_erf_list[k - 1765]
            self.df_climate.loc[k, "temperature_increase_from_contrails_from_aviation"] = (
                temperature_increase_from_contrails_from_aviation_list[k - 1765]
            )
            self.df_climate.loc[
                k, "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
            ] = temperature_increase_from_nox_short_term_o3_increase_from_aviation_list[k - 1765]
            self.df_climate.loc[
                k, "temperature_increase_from_nox_long_term_o3_decrease_from_aviation"
            ] = temperature_increase_from_nox_long_term_o3_decrease_from_aviation_list[k - 1765]
            self.df_climate.loc[k, "temperature_increase_from_nox_ch4_decrease_from_aviation"] = (
                temperature_increase_from_nox_ch4_decrease_from_aviation_list[k - 1765]
            )
            self.df_climate.loc[
                k, "temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation"
            ] = temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation_list[
                k - 1765
            ]
            self.df_climate.loc[k, "temperature_increase_from_h2o_from_aviation"] = (
                temperature_increase_from_h2o_from_aviation_list[k - 1765]
            )
            self.df_climate.loc[k, "temperature_increase_from_sulfur_from_aviation"] = (
                temperature_increase_from_sulfur_from_aviation_list[k - 1765]
            )
            self.df_climate.loc[k, "temperature_increase_from_soot_from_aviation"] = (
                temperature_increase_from_soot_from_aviation_list[k - 1765]
            )

        temperature_increase_from_co2_from_aviation = self.df_climate[
            "temperature_increase_from_co2_from_aviation"
        ]
        co2_erf = self.df_climate["co2_erf"]
        temperature_increase_from_contrails_from_aviation = self.df_climate[
            "temperature_increase_from_contrails_from_aviation"
        ]
        temperature_increase_from_nox_short_term_o3_increase_from_aviation = self.df_climate[
            "temperature_increase_from_nox_short_term_o3_increase_from_aviation"
        ]
        temperature_increase_from_nox_long_term_o3_decrease_from_aviation = self.df_climate[
            "temperature_increase_from_nox_long_term_o3_decrease_from_aviation"
        ]
        temperature_increase_from_nox_ch4_decrease_from_aviation = self.df_climate[
            "temperature_increase_from_nox_ch4_decrease_from_aviation"
        ]
        temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation = (
            self.df_climate[
                "temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation"
            ]
        )
        temperature_increase_from_h2o_from_aviation = self.df_climate[
            "temperature_increase_from_h2o_from_aviation"
        ]
        temperature_increase_from_sulfur_from_aviation = self.df_climate[
            "temperature_increase_from_sulfur_from_aviation"
        ]
        temperature_increase_from_soot_from_aviation = self.df_climate[
            "temperature_increase_from_soot_from_aviation"
        ]

        ## Temperature increase due to aviation
        temperature_increase_from_non_co2_from_aviation = (
            temperature_increase_from_contrails_from_aviation
            + temperature_increase_from_nox_short_term_o3_increase_from_aviation
            + temperature_increase_from_nox_long_term_o3_decrease_from_aviation
            + temperature_increase_from_nox_ch4_decrease_from_aviation
            + temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation
            + temperature_increase_from_h2o_from_aviation
            + temperature_increase_from_sulfur_from_aviation
            + temperature_increase_from_soot_from_aviation
        )
        temperature_increase_from_aviation = (
            temperature_increase_from_co2_from_aviation
            + temperature_increase_from_non_co2_from_aviation
        )

        self.df_climate["temperature_increase_from_non_co2_from_aviation"] = (
            temperature_increase_from_non_co2_from_aviation
        )
        self.df_climate["temperature_increase_from_aviation"] = temperature_increase_from_aviation

        return (
            temperature_increase_from_aviation,
            temperature_increase_from_co2_from_aviation,
            co2_erf,
            temperature_increase_from_non_co2_from_aviation,
            temperature_increase_from_contrails_from_aviation,
            temperature_increase_from_nox_short_term_o3_increase_from_aviation,
            temperature_increase_from_nox_long_term_o3_decrease_from_aviation,
            temperature_increase_from_nox_ch4_decrease_from_aviation,
            temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation,
            temperature_increase_from_h2o_from_aviation,
            temperature_increase_from_sulfur_from_aviation,
            temperature_increase_from_soot_from_aviation,
        )

import pandas as pd

from aeromaps.models.base import (
    AeroMAPSModel,
)
from aerocm.climate_models.aviation_climate_simulation import AviationClimateSimulation


class ClimateModel(AeroMAPSModel):
    """
    Class to run a climate simulation for aviation emissions using one of the available climate models
    available in AeroCM.

    Parameters
    ----------
    climate_model : str
        Name of the climate model to use (e.g., "LWE", "GWP*", "IPCC", etc.). See AeroCM documentation for available models.
    name : str, optional
        Name of the model when implemented in AeroMAPS, by default "climate".
    species_settings : dict | None, optional
        Dictionary containing species-specific settings for the climate model, by default None (which uses default settings from AeroCM).
    model_settings : dict | None, optional
        Dictionary containing model-wide settings for the climate model, by default None (which uses default settings from AeroCM).

    Attributes
    ----------
    climate_model : str
        Name of the climate model used to run the simulation.
    species_settings : dict | None
        Species-specific settings for the climate model.
    model_settings : dict | None
        Model settings for the climate model.
    mapping : dict
        Mapping between AeroCM output keys and AeroMAPS variable names.

    Notes
    -----
    This class is automatically implemented by the AeroMAPSProcess when a climate configuration file is provided
    through the 'PARAMETERS_CLIMATE_MODEL_FILE' key. The CLIMATE_MODEL_FILE should be a YAML file containing the keys
    'climate_model', 'species_settings', and 'model_settings'.

    The climate simulation is performed using the `AviationClimateSimulation` class from AeroCM.
    More details can be found on the AeroCM repository: https://github.com/AeroMAPS/AeroCM
    """

    def __init__(
            self,
            climate_model: str,
            name: str = "climate",
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
        """Run the climate simulation for aviation emissions.
        This method is a wrapper for the `AviationClimateSimulation` class from AeroCM.
        """

        # --- Prepare species inventory (and converting to ndarray) ---
        # Preprocess contrails
        idx1 = slice(self.climate_historic_start_year, self.end_year)
        self.df_climate.loc[idx1, "contrails_distance_corrected"] = (
                input_data["total_aircraft_distance"].loc[idx1]
        )
        idx2 = slice(self.historic_start_year, self.end_year)
        self.df_climate.loc[idx2, "contrails_distance_corrected"] = (
                input_data["total_aircraft_distance"].loc[idx2]
                * (1 - input_data["operations_contrails_gain"].loc[idx2] / 100)
                * input_data["fuel_effect_correction_contrails"].loc[idx2]
        )
        contrails_distance_corrected = self.df_climate["contrails_distance_corrected"]

        # Create species inventory dictionary
        species_inventory = {
            "CO2": input_data["co2_emissions"].to_numpy() * 1e9,  # convert from Mt to kg
            "Contrails": contrails_distance_corrected.to_numpy(),  # in km
            "NOx - ST O3 increase": input_data["nox_emissions"].to_numpy() * 1e9,  # in kg
            "NOx - CH4 decrease and induced": input_data["nox_emissions"].to_numpy() * 1e9,  # in kg
            "H2O": input_data["h2o_emissions"].to_numpy() * 1e9,  # in kg
            "Soot": input_data["soot_emissions"].to_numpy() * 1e9,  # in kg
            "Sulfur": input_data["sulfur_emissions"].to_numpy() * 1e9,  # in kg
        }

        # --- Run climate simulation ---
        results = AviationClimateSimulation(
            climate_model=self.climate_model,
            start_year=self.climate_historic_start_year,
            end_year=self.end_year,
            species_inventory=species_inventory,
            species_settings=self.species_settings,
            model_settings=self.model_settings
        ).run()

        # --- Convert back results from np.ndarray (list) to pd.Series ---
        for key in results.keys():
            for subkey in results[key].keys():
                results[key][subkey] = pd.Series(
                    results[key][subkey],
                    index=pd.RangeIndex(self.climate_historic_start_year, self.end_year + 1),
                )

        # --- Extract results, store in climate dataframe, and return outputs dict ---
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

        self.df_climate["temperature_increase_from_nox_from_aviation"] = self.df_climate[
                                                                             "temperature_increase_from_nox_short_term_o3_increase_from_aviation"] + \
                                                                         self.df_climate[
                                                                             "temperature_increase_from_nox_long_term_o3_decrease_from_aviation"] + \
                                                                         self.df_climate[
                                                                             "temperature_increase_from_nox_ch4_decrease_from_aviation"] + \
                                                                         self.df_climate[
                                                                             "temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation"]
        output_data["temperature_increase_from_nox_from_aviation"] = self.df_climate[
            "temperature_increase_from_nox_from_aviation"]
        self.df_climate["nox_erf"] = self.df_climate["nox_short_term_o3_increase_erf"] + self.df_climate[
            "nox_long_term_o3_decrease_erf"] + self.df_climate["nox_ch4_decrease_erf"] + self.df_climate[
                                         "nox_stratospheric_water_vapor_decrease_erf"]
        output_data["nox_erf"] = self.df_climate["nox_erf"]
        self.df_climate["nox_rf"] = self.df_climate["nox_short_term_o3_increase_rf"] + self.df_climate[
            "nox_long_term_o3_decrease_rf"] + self.df_climate["nox_ch4_decrease_rf"] + self.df_climate[
                                        "nox_stratospheric_water_vapor_decrease_rf"]
        output_data["nox_rf"] = self.df_climate["nox_rf"]

        ## ERF calculation for helping plot display
        # TODO: remove in the future
        self.df_climate["co2_h2o_erf"] = self.df_climate["co2_erf"] + self.df_climate["h2o_erf"]
        self.df_climate["co2_h2o_nox_erf"] = self.df_climate["co2_erf"] + self.df_climate["h2o_erf"] + self.df_climate["nox_erf"]
        self.df_climate["co2_h2o_nox_contrails_erf"] = self.df_climate["co2_erf"] + self.df_climate["h2o_erf"] + self.df_climate["nox_erf"] + self.df_climate["contrails_erf"]
        output_data["co2_h2o_erf"] = self.df_climate["co2_h2o_erf"]
        output_data["co2_h2o_nox_erf"] = self.df_climate["co2_h2o_nox_erf"]
        output_data["co2_h2o_nox_contrails_erf"] = self.df_climate["co2_h2o_nox_contrails_erf"]

        return output_data
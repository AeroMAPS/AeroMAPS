# Standard library imports
import logging
import os
from json import load, dump
from pathlib import Path
from typing import Union

# Third-party imports
import numpy as np
import pandas as pd

from gemseo import create_scenario


from gemseo.disciplines.scenario_adapters.mdo_scenario_adapter import MDOScenarioAdapter
from gemseo.mda.mda_chain import MDAChain


import xarray as xr
from copy import deepcopy
from gemseo import generate_n2_plot


# Local application imports
from aeromaps.models.base import AeroMAPSModel, AeroMapsCustomDataType
from aeromaps.core.gemseo import AeroMAPSAutoModelWrapper, AeroMAPSCustomModelWrapper
from aeromaps.core.models import default_models_top_down

from aeromaps.models.parameters import Parameters
from aeromaps.models.yaml_interpolator import YAMLInterpolator
from aeromaps.utils.functions import (
    _dict_to_df,
    flatten_dict,
)
from aeromaps.utils.yaml import read_yaml_file
from aeromaps.plots import available_plots, available_plots_fleet

# Fleet model imports
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model import (
    Fleet,
    FleetModel,
)

# Generic energy models imports
from aeromaps.models.impacts.generic_energy_model.common.energy_carriers_manager import (
    EnergyCarrierManager,
    EnergyCarrierMetadata,
)
from aeromaps.models.impacts.generic_energy_model.common.energy_carriers_factory import (
    AviationEnergyCarriersFactory,
)

# Climate model imports
from aeromaps.models.impacts.climate.climate import ClimateModel

# Settings
pd.options.display.max_rows = 150
pd.set_option("display.max_columns", 150)
pd.set_option("max_colwidth", 200)
pd.options.mode.chained_assignment = None

# Get the directory of the current script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the config.json file
DEFAULT_CONFIG_PATH = os.path.join(CURRENT_DIR, "config.json")

# Construct the path to the parameters.json file
DEFAULT_PARAMETERS_PATH = os.path.join(CURRENT_DIR, "..", "resources", "data", "parameters.json")

# Construct the path to the vector_inputs.csv file
DEFAULT_VECTOR_INPUTS_DATA_PATH = os.path.join(
    CURRENT_DIR, "..", "resources", "data", "vector_inputs.csv"
)

# Construct the path to the climate data .csv file
DEFAULT_CLIMATE_HISTORICAL_DATA_PATH = os.path.join(
    CURRENT_DIR, "..", "resources", "climate_data", "temperature_historical_dataset.csv"
)

# Construct the path to the energy carriers parameters default file
DEFAULT_ENERGY_CARRIERS_DATA_PATH = os.path.join(
    CURRENT_DIR, "..", "resources", "data", "default_energy_carriers", "energy_carriers_data.yaml"
)

DEFAULT_RESOURCES_DATA_PATH = os.path.join(
    CURRENT_DIR, "..", "resources", "data", "default_energy_carriers", "resources_data.yaml"
)

DEFAULT_PROCESSES_DATA_PATH = os.path.join(
    CURRENT_DIR, "..", "resources", "data", "default_energy_carriers", "processes_data.yaml"
)

DEFAULT_FLEET_DATA_PATH = os.path.join(CURRENT_DIR, "..", "resources", "data", "default_fleet")

DEFAULT_AIRCRAFT_INVENTORY_CONFIG_PATH = os.path.join(
    DEFAULT_FLEET_DATA_PATH, "aircraft_inventory.yaml"
)

DEFAULT_FLEET_CONFIG_PATH = os.path.join(DEFAULT_FLEET_DATA_PATH, "fleet.yaml")

DEFAULT_CLIMATE_MODEL_PATH = os.path.join(
    CURRENT_DIR, "..", "resources", "data", "default_climate_models", "climate_model_gwpstar.yaml"
)


class AeroMAPSProcess(object):
    def __init__(
        self,
        configuration_file=None,
        models=default_models_top_down,
        use_fleet_model=False,
        optimisation=False,
    ):
        self.configuration_file = (
            os.path.abspath(os.fspath(configuration_file))
            if configuration_file is not None
            else None
        )
        self._initialize_configuration()
        self.use_fleet_model = use_fleet_model

        # Recopy models to avoid shared state between instances.
        # For specific models that would be too heavy to deepcopy, set attribute `deepcopy_at_init` to False.
        # E.g., models that load large datasets that are read-only (c.f. LCA model).
        self.models = {
            k: deepcopy(v) if getattr(v, "deepcopy_at_init", True) else v for k, v in models.items()
        }

        # Initialize inputs
        self._initialize_inputs()

        self.common_setup()
        if not optimisation:
            self.setup_mda()
        else:
            self.setup_optimisation()

    def common_setup(self):
        self.disciplines = []
        self.data = {}
        self.json = {}
        self._initialize_data()

    def setup_mda(self):
        # Initialize energy carriers
        self._initialize_generic_energy()
        # Initialize climate model
        self._initialize_climate_model()
        self._initialize_disciplines()

        self.mda_chain = MDAChain(
            disciplines=self.disciplines,
            tolerance=1e-5,
            initialize_defaults=True,
            inner_mda_name="MDAGaussSeidel",
            log_convergence=True,
        )

    def setup_optimisation(self):
        self._initialize_gemseo_settings()

    def create_gemseo_scenario(self):
        self._initialize_generic_energy()
        self._initialize_climate_model()
        self._initialize_disciplines()

        self.scenario = create_scenario(
            disciplines=self.disciplines,
            objective_name=self.gemseo_settings["objective_name"],
            design_space=self.gemseo_settings["design_space"],
            scenario_type=self.gemseo_settings["scenario_type"],
            formulation_name=self.gemseo_settings["formulation"],
            main_mda_settings={
                "inner_mda_name": "MDAGaussSeidel",
                "max_mda_iter": 12,
                "initialize_defaults": True,
                "tolerance": 1e-4,
            },
            # grammar_type=self.gemseo_settings["grammar_type"],
            # input_data=self.input_data,
        )

    def create_gemseo_bilevel(self):
        # if no scenario is created raise an error create_gemseo_scenario needs to be called first
        if self.scenario is None:
            logging.warning(
                f"Inner scenario of the bilevel formulation was not fully defined. Creating it with the following settings:"
                f"Arguments used: disciplines={self.disciplines}, "
                f"objective_name={self.gemseo_settings['objective_name']}, "
                f"design_space={self.gemseo_settings['design_space']}, "
                f"scenario_type={self.gemseo_settings['scenario_type']}, "
                f"formulation_name={self.gemseo_settings['formulation']}"
            )
            self.create_gemseo_scenario()

        self.scenario.set_algorithm(self.gemseo_settings["algorithm_inner"])

        # dv_names = self.scenario.formulation.design_variables.keys()
        self.adapter = MDOScenarioAdapter(
            # TODO make generic --> ?
            self.scenario,
            input_names=self.gemseo_settings["doe_input_names"],
            output_names=self.gemseo_settings["doe_output_names"],
            reset_x0_before_opt=True,
            set_x0_before_opt=False,
        )

        self.scenario_adapted = create_scenario(
            self.adapter,
            formulation_name=self.gemseo_settings["formulation"],
            objective_name=self.gemseo_settings["objective_name_outer"],
            design_space=self.gemseo_settings["design_space_outer"],
            scenario_type="MDO",
        )

    def compute(self):
        input_data = self._pre_compute()
        if hasattr(self, "scenario") and self.scenario:
            if hasattr(self, "scenario_adapted") and self.scenario_adapted:
                print("Running bi-level MDO")
                # self.scenario.default_inputs.update(self.scenario.options)
                self.scenario_adapted.execute(self.gemseo_settings["algorithm_outer"])
            else:
                print("Running MDO")
                self.scenario.execute(self.gemseo_settings["algorithm"])
        else:
            if not hasattr(self, "mda_chain") or self.mda_chain is None:
                raise ValueError("MDA chain not created. Please call setup_mda() first.")
            else:
                print("Running MDA")
                self.mda_chain.execute(input_data=input_data)

        self._update_data_from_model()

    def get_dataframes(self):
        """Return all main DataFrames as a dictionary, generated on demand."""
        return {
            "data_information": self._get_data_information_df(),
            "vector_inputs": self._get_vector_inputs_df(),
            "float_inputs": self._get_float_inputs_df(),
            "str_inputs": self._get_str_inputs_df(),
            "vector_outputs": self._get_vector_outputs_df(),
            "float_outputs": self._get_float_outputs_df(),
            "climate_outputs": self._get_climate_outputs_df(),
            # Add more if needed
        }

    def get_json(self):
        """Return the model outputs as a JSON-serializable dictionary."""
        return self._data_to_json()

    def write_json(self, file_name=None):
        if (
            file_name is None
            and self.configuration_file is not None
            and "OUTPUTS_JSON_DATA_FILE" in self.config
        ):
            configuration_directory = os.path.dirname(self.configuration_file)
            new_output_file_path = os.path.join(
                configuration_directory, self.config["OUTPUTS_JSON_DATA_FILE"]
            )
            file_name = new_output_file_path
        elif file_name is None:
            file_name = self.config["OUTPUTS_JSON_DATA_FILE"]

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_name), exist_ok=True)

        # Retrieve the data from the model
        json_data = self.get_json()

        with open(file_name, "w", encoding="utf-8") as f:
            dump(json_data, f, ensure_ascii=False, indent=4)

    def write_excel(self, file_name=None):
        if file_name is None:
            file_name = self.config["EXCEL_DATA_FILE"]
        with pd.ExcelWriter(file_name) as writer:
            self._get_data_information_df().to_excel(writer, sheet_name="Data Information")
            self._get_vector_inputs_df().to_excel(writer, sheet_name="Vector Inputs")
            self._get_float_inputs_df().to_excel(writer, sheet_name="Float Inputs")
            self._get_str_inputs_df().to_excel(writer, sheet_name="String Inputs")
            self._get_vector_outputs_df().to_excel(writer, sheet_name="Vector Outputs")
            self._get_float_outputs_df().to_excel(writer, sheet_name="Float Outputs")
            self._get_climate_outputs_df().to_excel(writer, sheet_name="Climate Outputs")
            # self.lca_outputs_xarray.to_excel(writer, sheet_name="LCA Outputs")

    def generate_n2(self):
        generate_n2_plot(self.disciplines)

    def list_available_plots(self):
        return list(available_plots.keys())

    def list_float_inputs(self):
        return self.data["float_inputs"]

    def list_str_inputs(self):
        return self.data["str_inputs"]

    def plot(self, name, save=False, size_inches=None, remove_title=False):
        if name in available_plots_fleet:
            try:
                # todo: if we pass the process to the plot, fleet_model is no longer needed as an argument.
                fig = available_plots_fleet[name](self, self.fleet_model)
                if save:
                    if size_inches is not None:
                        fig.fig.set_size_inches(size_inches)
                    if remove_title:
                        fig.fig.gca().set_title("")
                    fig.fig.savefig(f"{name}.pdf", bbox_inches="tight")
            except AttributeError as e:
                raise NameError(
                    f"Plot {name} requires using bottom up fleet model. Original error: {e}"
                )
        elif name in available_plots:
            fig = available_plots[name](self)
            if save:
                if size_inches is not None:
                    fig.fig.set_size_inches(size_inches)
                if remove_title:
                    fig.fig.gca().set_title("")
                fig.fig.savefig(f"{name}.pdf", bbox_inches="tight")
        else:
            raise NameError(
                f"Plot {name} is not available. List of available plots: {list(available_plots.keys()), list(available_plots_fleet.keys())}"
            )
        return fig

    def _pre_compute(self):
        input_data = self.parameters.to_dict()
        if self.fleet is not None:
            # Necessary when user hard coded the fleet
            self.fleet_model.fleet.all_aircraft_elements = (
                self.fleet_model.fleet.get_all_aircraft_elements()
            )
            self.fleet_model.compute()

            # This is needed since fleet model is particular discipline
            input_data["dummy_fleet_model_output"] = np.array([1.0])

        # Initialize the dataframes witjh latest parameter values
        for disc in self.disciplines:
            disc.model._initialize_df()

        return input_data

    def _initialize_configuration(self):
        # Load the default configuration file
        with open(DEFAULT_CONFIG_PATH, "r") as f:
            self.config = load(f)
        # Update paths in the configuration file with absolute paths
        for key, value in self.config.items():
            self.config[key] = os.path.join(CURRENT_DIR, value)

        # Load the new configuration file
        if self.configuration_file is not None:
            with open(self.configuration_file, "r") as f:
                new_config = load(f)
                
            configuration_directory = os.path.dirname(self.configuration_file)
            # Replace the default configuration with the new configuration
            for key, value in new_config.items():
                if (
                    isinstance(value, str)
                    and not os.path.isabs(value)
                ):
                    value = os.path.normpath(os.path.join(configuration_directory, value))
                self.config[key] = value


    def _resolve_config_path(self, key: str, default_path: Union[Path, str]) -> Path:
        default_path_obj = Path(default_path)
        path_value = self.config.get(key)
        if not path_value or isinstance(path_value, list):
            return default_path_obj
        path_str = str(path_value)
        if os.path.isabs(path_str):
            resolved_path = Path(path_str)
            if resolved_path.exists():
                return resolved_path
            return default_path_obj

        base_dir = (
            os.path.dirname(self.configuration_file)
            if self.configuration_file is not None
            else CURRENT_DIR
        )
        resolved_path = Path(os.path.join(base_dir, path_str))
        if resolved_path.exists():
            return resolved_path
        else:
            print(
                "Resolved path ",
                path_value,
                " does not exist. Using default path:",
                default_path_obj,
            )
        return default_path_obj

    def _initialize_data(self):
        # Indexes
        self._initialize_years()

        self._initialize_climate_historical_data()

        # Inputs
        self.data["float_inputs"] = {}
        self.data["str_inputs"] = {}
        # TODO: explore the possibility of using a dataframe for vector inputs
        self.data["vector_inputs"] = {}

        # Outputs
        self.data["float_outputs"] = {}
        self.data["vector_outputs"] = pd.DataFrame(index=self.data["years"]["full_years"])
        self.data["climate_outputs"] = pd.DataFrame(index=self.data["years"]["climate_full_years"])
        self.data["lca_outputs"] = xr.DataArray()

    def _initialize_generic_energy(self):
        self._read_generic_resources_data()
        self._read_generic_process_data()
        self._instantiate_generic_energy_models()

    def _read_generic_resources_data(self):
        # Read the custom energy config file and instantiate each class
        if self.configuration_file is not None and "PARAMETERS_RESOURCES_DATA_FILE" in self.config:
            configuration_directory = os.path.dirname(self.configuration_file)
            resources_data_file_path = os.path.join(
                configuration_directory, self.config["PARAMETERS_RESOURCES_DATA_FILE"]
            )
        else:
            resources_data_file_path = DEFAULT_RESOURCES_DATA_PATH

        self.energy_resources_data = read_yaml_file(resources_data_file_path)

        # The first level of the yaml conf file contains all the pathways
        resources = list(self.energy_resources_data.keys())

        for resource in resources:
            resource_data = self.energy_resources_data[resource]
            if "name" not in resource_data:
                raise ValueError("The resource configuration file should contain its name")

            # Flatten the inputs dictionary and interpolate the necessary values

            flattened_yaml = flatten_dict(resource_data["specifications"], resource_data["name"])
            resource_data["specifications"] = self._convert_custom_data_types(flattened_yaml)

            self.parameters.from_dict(resource_data["specifications"])

            self.energy_resources_data[resource] = resource_data

    def _read_generic_process_data(self):
        # Read the custom energy config file and instantiate each class
        if self.configuration_file is not None and "PARAMETERS_PROCESSES_DATA_FILE" in self.config:
            configuration_directory = os.path.dirname(self.configuration_file)
            processes_data_path = os.path.join(
                configuration_directory, self.config["PARAMETERS_PROCESSES_DATA_FILE"]
            )
        else:
            processes_data_path = DEFAULT_PROCESSES_DATA_PATH

        self.energy_processes_data = read_yaml_file(processes_data_path)

        # The first level of the yaml conf file contains all the pathways
        processes = list(self.energy_processes_data.keys())

        for process in processes:
            process_data = self.energy_processes_data[process]
            if "name" not in process_data:
                raise ValueError("The process configuration file should contain its name")

            # Flatten the inputs dictionary and interpolate the necessary values

            inputs = process_data["inputs"]
            # Flatten the inputs dictionary and interpolate the necessary values
            for key, value in inputs.items():
                flattened_yaml = flatten_dict(value, process_data["name"])
                inputs[key] = self._convert_custom_data_types(flattened_yaml)
                # set data to parameters
                self.parameters.from_dict(inputs[key])

            process_data["inputs"] = inputs

            self.energy_processes_data[process] = process_data

    def _instantiate_generic_energy_models(self):
        # Read the custom energy config file and instantiate each class from it using the factory method
        # Add the instantiated classes to the models dictionary
        if (
            self.configuration_file is not None
            and "PARAMETERS_ENERGY_CARRIERS_DATA_FILE" in self.config
        ):
            configuration_directory = os.path.dirname(self.configuration_file)
            energy_carriers_data_file_path = os.path.join(
                configuration_directory, self.config["PARAMETERS_ENERGY_CARRIERS_DATA_FILE"]
            )
        else:
            energy_carriers_data_file_path = DEFAULT_ENERGY_CARRIERS_DATA_PATH

        self.energy_carriers_data = read_yaml_file(energy_carriers_data_file_path)

        # The first level of the yaml conf file contains all the pathways
        pathways = list(self.energy_carriers_data.keys())

        # create a metadata manager for the pathways to easily sort them later
        self.pathways_manager = EnergyCarrierManager()

        for pathway in pathways:
            pathway_data = self.energy_carriers_data[pathway]
            if "name" not in pathway_data:
                raise ValueError("The pathway configuration file should contain its name")
            if "inputs" not in pathway_data:
                raise ValueError("The pathway configuration file should contain inputs")
            self.pathways_manager.add(
                EnergyCarrierMetadata(
                    name=pathway,
                    aircraft_type=pathway_data.get("aircraft_type"),
                    default=pathway_data.get("default"),
                    mandate_type=pathway_data.get("inputs").get("mandate", {}).get("mandate_type"),
                    energy_origin=pathway_data.get("energy_origin"),
                    resources_used=pathway_data.get("inputs")
                    .get("technical", {})
                    .get("resource_names", []),
                    resources_used_processes={
                        el: (
                            list(
                                self.energy_processes_data.get(el, {})
                                .get("inputs", {})
                                .get("technical", {})
                                .get(f"{el}_resource_names", [])
                            )
                            or [None]
                        )[0]
                        for el in pathway_data.get("inputs", {})
                        .get("technical", {})
                        .get("processes_names", [])
                    },
                    cost_model=pathway_data.get("cost_model"),
                    environmental_model=pathway_data.get("environmental_model"),
                )
            )

            inputs = pathway_data["inputs"]
            # Flatten the inputs dictionary and interpolate the necessary values
            for key, value in inputs.items():
                flattened_yaml = flatten_dict(value, pathway_data["name"])
                inputs[key] = self._convert_custom_data_types(flattened_yaml)
                # set data to parameters
                self.parameters.from_dict(inputs[key])

            pathway_data["inputs"] = inputs

            self.energy_carriers_data[pathway] = pathway_data

            # Use the energy_carriers_factory to instantiate the adequate models based on the conf file and ad these to the models dictionary

            # TODO would it be simpler to pass the EnergyCarrierMetadata to the models?
            self.models.update(
                AviationEnergyCarriersFactory.create_carrier(
                    pathway,
                    self.energy_carriers_data,
                    self.energy_resources_data,
                    self.energy_processes_data,
                )
            )
        # Instantiate resources use models
        self.models.update(
            AviationEnergyCarriersFactory.instantiate_resource_consumption_models(
                self.energy_resources_data, self.pathways_manager
            )
        )

        # Instantiate the energy use choice model
        self.models.update(
            AviationEnergyCarriersFactory.instantiate_energy_carriers_models(
                self.energy_carriers_data, self.pathways_manager
            )
        )

    def _initialize_climate_model(self):
        """ Read the climate config file and instantiate ClimateModel accordingly.
        The config file should contain:
        - climate_model: str, name of the climate model to use
        - species_settings: dict, settings for each species
        - model_settings: dict, settings for the climate model
        Refer to the documentation of AeroCM for more details: https://github.com/AeroMAPS/AeroCM
        """
        if (
            self.configuration_file is not None
            and "PARAMETERS_CLIMATE_MODEL_FILE" in self.config
        ):
            configuration_directory = os.path.dirname(self.configuration_file)
            climate_model_file_path = os.path.join(
                configuration_directory, self.config["PARAMETERS_CLIMATE_MODEL_FILE"]
            )
        else:
            climate_model_file_path = DEFAULT_CLIMATE_MODEL_PATH

        climate_model_data = read_yaml_file(climate_model_file_path)
        self.models.update(
            {"climate_model": ClimateModel(
                name="climate_model",
                climate_model=climate_model_data.get("climate_model"),
                species_settings=climate_model_data.get("species_settings", {}),
                model_settings=climate_model_data.get("model_settings", {})
            )
            }
        )

    def _convert_custom_data_types(self, data):
        """
        This method reads the flattened yaml file. It does two principal things:
         - it instantiates interpolator models when encountering a custom data type, and add reference years and values to parameters
         - it converts the custom type to a normal series in the flattened yaml file so that generic energy models know the type of the interpolated inputs
        Returns the modified data
        """
        for key, value in data.items():
            if isinstance(value, AeroMapsCustomDataType):
                # add an interpolator model for each custom data type
                self.models.update({key: YAMLInterpolator(key, value)})
                self.parameters.from_dict(
                    {
                        f"{key}_years": value.years,
                        f"{key}_values": value.values,
                    }
                )
                # set a normal series to provide carrier model with the name/type result of the interpolation
                data[key] = pd.Series([0.0])  # initialize to future interpolation type.
        return data

    def _initialize_disciplines(self):
        if self.use_fleet_model:

            aircraft_inventory_path = self._resolve_config_path(
                "AIRCRAFT_INVENTORY_CONFIG_FILE",
                default_path=DEFAULT_AIRCRAFT_INVENTORY_CONFIG_PATH,
            )

            fleet_config_path = self._resolve_config_path(
                "FLEET_CONFIG_FILE",
                default_path=DEFAULT_FLEET_CONFIG_PATH,
            )
            self.fleet = Fleet(
                parameters=self.parameters,
                aircraft_inventory_path=aircraft_inventory_path,
                fleet_config_path=fleet_config_path,
            )
            self.fleet_model = FleetModel(fleet=self.fleet)
            self.fleet_model.parameters = self.parameters
            self.fleet_model._initialize_df()
        else:
            self.fleet = None

        def check_instance_in_dict(d):
            # todo rename that function as it is now clearly much more than just checking instance in dict... ;)
            for key, value in d.items():
                if isinstance(value, dict):
                    check_instance_in_dict(value)
                elif isinstance(value, AeroMAPSModel):
                    model = value
                    # TODO: check how to avoid providing all parameters
                    model.parameters = self.parameters
                    model._initialize_df()
                    if hasattr(model, "pathways_manager") and hasattr(model, "custom_setup"):
                        # TODO harmonise the way to pass the pathways manager with generic models
                        model.pathways_manager = self.pathways_manager
                        model.custom_setup()
                    if self.use_fleet_model and hasattr(model, "fleet_model"):
                        model.fleet_model = self.fleet_model
                    if hasattr(model, "climate_historical_data"):
                        model.climate_historical_data = self.climate_historical_data
                    if hasattr(model, "compute"):
                        if model.model_type == "custom":
                            model = AeroMAPSCustomModelWrapper(model=model)
                        else:
                            model = AeroMAPSAutoModelWrapper(model=model)
                        self.disciplines.append(model)
                    else:
                        print(model.name)
                else:
                    print(f"{key} is not an instance of AeroMAPSModel")

        check_instance_in_dict(self.models)

    def _initialize_years(self):
        # Years
        self.data["years"] = {}
        self.data["years"]["full_years"] = list(
            range(self.parameters.historic_start_year, self.parameters.end_year + 1)
        )
        self.data["years"]["climate_full_years"] = list(
            range(self.parameters.climate_historic_start_year, self.parameters.end_year + 1)
        )
        self.data["years"]["historic_years"] = list(
            range(
                self.parameters.historic_start_year,
                self.parameters.prospection_start_year,
            )
        )
        self.data["years"]["climate_historic_years"] = list(
            range(
                self.parameters.climate_historic_start_year,
                self.parameters.prospection_start_year,
            )
        )
        self.data["years"]["prospective_years"] = list(
            range(self.parameters.prospection_start_year - 1, self.parameters.end_year + 1)
        )

    def _initialize_inputs(self, use_defaults=True):
        self.parameters = Parameters()

        # First use main parameters.json as default values
        if use_defaults:
            self.parameters.read_json(file_name=DEFAULT_PARAMETERS_PATH)

        if self.configuration_file is not None and "PARAMETERS_JSON_DATA_FILE" in self.config:
            # If the alternative file is a list of json files
            if isinstance(self.config["PARAMETERS_JSON_DATA_FILE"], list):
                merged_data = {}
                new_input_file_path = []
                configuration_directory = os.path.dirname(self.configuration_file)
                for k in range(0, len(self.config["PARAMETERS_JSON_DATA_FILE"])):
                    new_input_file_path.append(
                        os.path.join(
                            configuration_directory, self.config["PARAMETERS_JSON_DATA_FILE"][k]
                        )
                    )
                for file in new_input_file_path:
                    with open(file, "r") as f:
                        data = load(f)
                        for key, value in data.items():
                            if key in merged_data:
                                print(
                                    f"Warning: '{key}' was given twice, only the last value was kept."
                                )
                            merged_data[key] = value
                self.parameters.read_json_direct(merged_data)
            # If the alternative file is a single json file
            else:
                configuration_directory = os.path.dirname(self.configuration_file)
                new_input_file_path = os.path.join(
                    configuration_directory, self.config["PARAMETERS_JSON_DATA_FILE"]
                )
                self.parameters.read_json(file_name=new_input_file_path)

        # Check if parameter is pd.Series and update index
        for key, value in self.parameters.__dict__.items():
            if isinstance(value, pd.Series):
                new_index = range(self.parameters.historic_start_year, self.parameters.end_year + 1)
                value = value.reindex(new_index, fill_value=np.nan)
                setattr(self.parameters, key, value)

        self._initialize_vector_inputs()
        # TODO clarify the role of _initialize_vector_inputs vs read_json_direct @Scott?
        # Format input vectors
        self._format_input_vectors()

    def _initialize_vector_inputs(self):
        if self.configuration_file is not None and "VECTOR_INPUTS_DATA_FILE" in self.config:
            configuration_directory = os.path.dirname(self.configuration_file)
            vector_inputs_data_file_path = os.path.join(
                configuration_directory, self.config["VECTOR_INPUTS_DATA_FILE"]
            )
        else:
            vector_inputs_data_file_path = DEFAULT_VECTOR_INPUTS_DATA_PATH

        # Read .csv with first line column names
        vector_inputs_df = pd.read_csv(vector_inputs_data_file_path, delimiter=";", header=0)
        # Generate pd.Series for each column with index the year stored in first column
        index = vector_inputs_df.iloc[:, 0].values
        for column in vector_inputs_df.columns[1:]:
            values = vector_inputs_df[column].values

            # TODO remove this: experiment to see if it works
            # TODO remove this TODO !
            # if column == "airfare_per_rpk":
            #     setattr(self.parameters, column, np.array(values))
            #
            # else:
            setattr(self.parameters, column, pd.Series(values, index=index))

    def _initialize_climate_historical_data(self):
        if self.configuration_file is not None and "PARAMETERS_CLIMATE_DATA_FILE" in self.config:
            configuration_directory = os.path.dirname(self.configuration_file)
            climate_historical_data_file_path = os.path.join(
                configuration_directory, self.config["PARAMETERS_CLIMATE_DATA_FILE"]
            )
        else:
            climate_historical_data_file_path = DEFAULT_CLIMATE_HISTORICAL_DATA_PATH

        historical_dataset_df = pd.read_csv(
            climate_historical_data_file_path, delimiter=";", header=None
        )
        self.climate_historical_data = historical_dataset_df.values

    def _initialize_gemseo_settings(self):
        self.scenario = None
        self.scenario_adapted = None
        self.gemseo_settings = {}

        # Mandatory settings
        self.gemseo_settings["design_space"] = None
        self.gemseo_settings["objective_name"] = None
        self.gemseo_settings["algorithm"] = None

        # Optional settings
        self.gemseo_settings["formulation"] = "MDF"
        self.gemseo_settings["scenario_type"] = "MDO"
        # self.gemseo_settings["grammar_type"] = Discipline.GrammarType.SIMPLE
        self.gemseo_settings["doe_input_names"] = None
        self.gemseo_settings["doe_output_names"] = None

    def _format_input_vectors(self):
        for field_name, field_value in self.parameters.__dict__.items():
            list_init = [
                "rpk_init",
                "ask_init",
                "rtk_init",
                "pax_init",
                "freight_init",
                "energy_consumption_init",
                "total_aircraft_distance_init",
            ]
            if field_name in list_init:
                new_size = self.parameters.end_year - self.parameters.historic_start_year + 1
                new_value = np.pad(
                    field_value.astype(float),
                    (0, new_size - field_value.size),
                    mode="constant",
                    constant_values=np.nan,
                )
                new_index = range(self.parameters.historic_start_year, self.parameters.end_year + 1)
                new_value = pd.Series(new_value, index=new_index)
                setattr(self.parameters, field_name, new_value)
            elif not isinstance(field_value, (float, int, list, str)):
                if (
                    field_value.size
                    == self.parameters.end_year - self.parameters.climate_historic_start_year + 1
                ):
                    index = range(
                        self.parameters.climate_historic_start_year, self.parameters.end_year + 1
                    )
                    new_value = pd.Series(field_value, index=index)
                    setattr(self.parameters, field_name, new_value)
                elif (
                    field_value.size
                    == self.parameters.end_year - self.parameters.historic_start_year + 1
                ):
                    index = range(self.parameters.historic_start_year, self.parameters.end_year + 1)
                    new_value = pd.Series(field_value, index=index)
                    setattr(self.parameters, field_name, new_value)
                else:
                    print(f"Field {field_name} has an unexpected size {field_value.size}")

    def _update_variables(self):
        self._update_data_from_model()

        self._update_dataframes_from_data()

        self._update_json_from_data()

    def _update_data_from_model(self):
        # Inputs: if we have and mda_cain (no optim), we get the inputs from there, else we get them from each discipline
        if hasattr(self, "mda_chain") and self.mda_chain:
            all_inputs = self.mda_chain.get_input_data()
        else:
            all_inputs = {}
            for discipline in self.disciplines:
                inputs = discipline.get_input_data()
                if isinstance(inputs, dict):
                    all_inputs.update(inputs)

        for name in all_inputs:
            try:
                value = getattr(self.parameters, name)
                if isinstance(value, (float, int)):
                    self.data["float_inputs"][name] = value
                elif isinstance(value, str):
                    self.data["str_inputs"][name] = value
                elif isinstance(value, list):
                    if all(isinstance(x, str) for x in value) and len(value) > 0:
                        self.data["str_inputs"][name] = value
                    else:
                        self.data["float_inputs"][name] = value
                else:
                    new_values = []
                    for val in value:
                        if not np.isnan(val):
                            new_values.append(val)
                    self.data["vector_inputs"][name] = new_values
            except AttributeError:
                pass

        # Outputs
        if self.data["vector_outputs"].columns.size == 0:
            first_computation = True
        else:
            first_computation = False

        # TODO: better to use _local_data?
        for disc in self.disciplines:
            if hasattr(disc.model, "df") and disc.model.df.columns.size != 0:
                if first_computation:
                    self.data["vector_outputs"] = pd.concat(
                        [self.data["vector_outputs"], disc.model.df], axis=1
                    )
                else:
                    self.data["vector_outputs"].update(disc.model.df)
            if hasattr(disc.model, "df_climate") and disc.model.df_climate.columns.size != 0:
                if first_computation:
                    self.data["climate_outputs"] = pd.concat(
                        [self.data["climate_outputs"], disc.model.df_climate], axis=1
                    )
                else:
                    self.data["climate_outputs"].update(disc.model.df_climate)
            if hasattr(disc.model, "xarray_lca") and disc.model.xarray_lca.size > 1:
                if first_computation:
                    self.data["lca_outputs"] = disc.model.xarray_lca
                else:
                    self.data["lca_outputs"].update(disc.model.xarray_lca)

            self.data["float_outputs"].update(disc.model.float_outputs)

    def _get_float_inputs_df(self):
        data = {
            "Name": self.data["float_inputs"].keys(),
            "Value": self.data["float_inputs"].values(),
        }
        return pd.DataFrame(data=data)

    def _get_str_inputs_df(self):
        data = {
            "Name": self.data["str_inputs"].keys(),
            "Value": self.data["str_inputs"].values(),
        }
        return pd.DataFrame(data=data)

    def _get_vector_inputs_df(self):
        df = _dict_to_df(self.data["vector_inputs"], orient="columns")
        df.sort_index(axis=1, inplace=True)
        return df

    def _get_float_outputs_df(self):
        data = {
            "Name": self.data["float_outputs"].keys(),
            "Value": self.data["float_outputs"].values(),
        }
        return pd.DataFrame(data=data)

    def _get_vector_outputs_df(self):
        df = self.data["vector_outputs"].copy()
        df.sort_index(axis=1, inplace=True)
        return df

    def _get_climate_outputs_df(self):
        df = self.data["climate_outputs"].copy()
        df.sort_index(axis=1, inplace=True)
        return df

    def _get_data_information_df(self):
        return self._read_data_information()

    def _data_to_json(self):
        def convert_values_from_array_to_list(d):
            for key, value in d.items():
                if isinstance(value, (pd.Series, np.ndarray)):
                    d[key] = list(value)
            return d

        # Create json data
        json_data = {}

        # Float inputs
        json_data["float_inputs"] = convert_values_from_array_to_list(self.data["float_inputs"])

        # String inputs
        json_data["str_inputs"] = convert_values_from_array_to_list(self.data["str_inputs"])

        # Vector inputs
        json_data["vector_inputs"] = convert_values_from_array_to_list(self.data["vector_inputs"])

        # Float outputs
        json_data["float_outputs"] = convert_values_from_array_to_list(self.data["float_outputs"])

        # Vector outputs
        json_data["vector_outputs"] = convert_values_from_array_to_list(
            self.data["vector_outputs"].to_dict("list")
        )

        # Climate outputs
        json_data["climate_outputs"] = convert_values_from_array_to_list(
            self.data["climate_outputs"].to_dict("list")
        )

        # LCA outputs --> convert to json is not supported yet
        # json_data["lca_outputs"] = convert_values_from_array_to_list(
        #    self.data["lca_outputs"].to_series().to_dict("list")
        # )

        return json_data

    def _read_data_information(self, file_name=None):
        if file_name is None:
            file_name = self.config["CSV_DATA_INFORMATION_FILE"]
        df = pd.read_csv(file_name, encoding="utf-8", sep=";")

        var_infos_df = pd.DataFrame()
        for data_type, variables in self.data.items():
            # FIXME: xarray no supported yet for excel data information
            if type(variables) is xr.DataArray:
                continue

            for variable in variables:
                # If the variable exists in the csv we extract the information
                if variable in df["Name"].values:
                    data = df.loc[df["Name"] == variable]
                    data["Type"] = data_type
                    var_infos_df = pd.concat([var_infos_df, data], ignore_index=True)

                # If not we create a new one with just the type as information
                else:
                    data = {
                        "Name": [variable],
                        "Type": [data_type],
                        "Unit": ["N/A"],
                        "Description": ["N/A"],
                    }
                    new_row = pd.DataFrame(data=data)
                    var_infos_df = pd.concat([var_infos_df, new_row], ignore_index=True)

        return var_infos_df

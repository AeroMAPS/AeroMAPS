"""High-level AeroMAPS process orchestration.

This module defines the main process class that orchestrates parameter
initialization, model instantiation, GEMSEO configuration, generic energy carrier handling, and data export for the
AeroMAPS framework.
"""

# Standard library imports
import logging
import os
from json import load, dump
from pathlib import Path
from typing import Union
import dill

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
from aeromaps.core import models as aeromaps_models

from aeromaps.models.parameters import Parameters
from aeromaps.models.yaml_interpolator import YAMLInterpolator
from aeromaps.utils.functions import (
    _dict_to_df,
    _flatten_dict,
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

# LCA models imports
# Check if LCA packages for custom model are installed
try:
    from aeromaps.models.impacts.life_cycle_assessment.life_cycle_assessment_custom import LifeCycleAssessmentCustom
    LCA_PACKAGES_INSTALLED = True
except ImportError:
    LCA_PACKAGES_INSTALLED = False
from aeromaps.models.impacts.life_cycle_assessment.life_cycle_assessment_default import LifeCycleAssessmentDefault

# Settings
pd.options.display.max_rows = 150
pd.set_option("display.max_columns", 150)
pd.set_option("max_colwidth", 200)
pd.options.mode.chained_assignment = None

# Get the directory of the current script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the default config.yaml file
DEFAULT_CONFIG_PATH = os.path.join(CURRENT_DIR, "..", "resources", "data", "config.yaml")

# Base directory for resources/data (used to resolve relative paths in config.yaml)
DEFAULT_RESOURCES_DATA_DIR = os.path.join(CURRENT_DIR, "..", "resources", "data")


class AeroMAPSProcess(object):
    """High-level AeroMAPS process driver.

    This class configures parameters, instantiates discipline models,
    builds GMESEO objects, handles generic energy carrier pathways, and manages input and output data
    structures for AeroMAPS studies.

    Parameters
    ----------
    configuration_file
        Path to a configuration JSON file overriding default settings.
    models
        Dictionary of model instances to be used in the process.
    optimisation
        Whether to configure GEMSEO for optimisation instead of a pure
        MDA chain.

    Attributes
    ----------
    configuration_file
        Path of the active configuration JSON file.
    models
        Dictionary of discipline and auxiliary models used in the
        process.
    parameters
        Central parameter container used by all models and disciplines.
    disciplines
        List of wrapped discipline objects used by GEMSEO or the MDA
        chain.
    data
        Dictionary storing structured inputs and outputs, including
        scalar, string, vector, climate, and LCA results.
    json
        Dictionary reserved for JSON-compatible representations of
        results.
    mda_chain
        GEMSEO MDAChain instance used when running pure MDA analyses.
    scenario
        GEMSEO scenario instance for conventional MDO.
    scenario_adapted
        GEMSEO scenario of scenario instance for the bilevel optimization
        problem.
    gemseo_settings
        Dictionary containing all GEMSEO-related configuration options.
    fleet
        Fleet instance when the bottom-up fleet model is activated, else
        None.
    fleet_model
        FleetModel instance wrapping the fleet when the bottom-up model
        is used.
    energy_resources_data
        Parsed configuration data for generic energy resources.
    energy_processes_data
        Parsed configuration data for generic energy processes.
    energy_carriers_data
        Parsed configuration data for aviation energy carrier pathways.
    pathways_manager
        EnergyCarrierManager instance describing available energy
        pathways.
    climate_historical_data
        Historical climate dataset used by climate-related models.
    """

    def __init__(
        self,
        configuration_file=None,
        custom_models=None,
        optimisation=False,
    ):
        """Initialize an AeroMAPSProcess instance.

        This method loads configuration settings, initializes parameters,
        deep-copies the provided models dictionary when needed, and
        performs the common setup. It then configures either an MDA chain
        or an optimization scenario depending on the specified mode.

        Parameters
        ----------
        configuration_file
            Path to a configuration YAML file overriding default
            settings.
        custom_models
            Dictionary of additional model instances to be merged with
            the standard models loaded from the configuration file's
            `models.standards` list. If None, only the standard models
            are used.
        optimisation
            Whether to configure GEMSEO for optimization instead of a
            pure MDA chain.
        """
        self.configuration_file = (
            os.path.abspath(os.fspath(configuration_file))
            if configuration_file is not None
            else None
        )
        self._initialize_configuration()

        # Load standard models from config
        standard_models = self._load_models_from_config()
        
        # Merge with user-provided models (user models override/extend standard models)
        if custom_models is not None:
            standard_models.update(custom_models)
        
        models = standard_models

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

    def _load_models_from_config(self):
        """Load models from the configuration file's standards and customs lists.

        This method reads the `models.standards` list from the configuration
        and retrieves corresponding model dictionaries from the aeromaps.core.models module.
        It also reads the `models.customs` dictionary to dynamically load custom model
        classes from user-specified Python files.

        Returns
        -------
        dict
            A dictionary containing all the models specified in the configuration.

        Raises
        ------
        ValueError
            If a model name from the config is not found in aeromaps.core.models.
        """
        standards = self._get_config_value("models", "standards", default=[])
        
        if not standards:
            # Fallback to default_models_top_down if no standards specified
            return aeromaps_models.default_models_top_down
        
        models = {}
        for model_name in standards:
            if hasattr(aeromaps_models, model_name):
                model_dict = getattr(aeromaps_models, model_name)
                models[model_name] = model_dict
            else:
                raise ValueError(
                    f"Model '{model_name}' specified in config.yaml is not found in "
                    f"aeromaps.core.models. Available models: {[name for name in dir(aeromaps_models) if name.startswith('models_')]}"
                )
        
        # Load custom models from config if specified
        customs = self._get_user_config_value("models", "customs", default=None)
        if customs is not None:
            custom_models = self._load_custom_models_from_config(customs)
            models.update(custom_models)
        
        return models

    def _load_custom_models_from_config(self, customs: dict) -> dict:
        """Load custom model classes from user-specified paths.

        This method dynamically imports and instantiates custom model classes
        specified in the configuration file.

        Parameters
        ----------
        customs
            Dictionary mapping model names to their paths in the format:
            "path/to/module.py::ClassName" or just "path/to/module.py"
            (in which case the class name is inferred from the model name).

        Returns
        -------
        dict
            Dictionary of instantiated custom models.

        Raises
        ------
        ValueError
            If the path format is invalid or the class cannot be found.
        ImportError
            If the module cannot be imported.
        """
        import importlib.util
        
        custom_models = {}
        
        for model_name, path_spec in customs.items():
            # Parse the path specification
            if "::" in path_spec:
                module_path, class_name = path_spec.rsplit("::", 1)
            else:
                module_path = path_spec
                # Convert model_name to CamelCase for class name
                class_name = "".join(word.capitalize() for word in model_name.split("_"))
            
            # Resolve the module path relative to the config file directory
            if not os.path.isabs(module_path):
                module_path = os.path.normpath(
                    os.path.join(self._config_base_dir, module_path)
                )
            
            if not os.path.exists(module_path):
                raise ValueError(
                    f"Custom model file not found: '{module_path}' "
                    f"(model: {model_name})"
                )
            
            # Dynamically import the module
            spec = importlib.util.spec_from_file_location(model_name, module_path)
            if spec is None or spec.loader is None:
                raise ImportError(
                    f"Cannot load module from '{module_path}' "
                    f"(model: {model_name})"
                )
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the class from the module
            if not hasattr(module, class_name):
                available_classes = [
                    name for name in dir(module) 
                    if not name.startswith("_") and isinstance(getattr(module, name), type)
                ]
                raise ValueError(
                    f"Class '{class_name}' not found in '{module_path}'. "
                    f"Available classes: {available_classes}"
                )
            
            model_class = getattr(module, class_name)
            
            # Instantiate the model
            custom_models[model_name] = model_class(name=model_name)
            
            logging.info(f"Loaded custom model '{model_name}' from '{module_path}'")
        
        return custom_models

    def common_setup(self):
        """Perform common setup steps independent of analysis type.

        This method initializes the disciplines list, the main data
        container, and JSON storage, and computes index structures and
        climate data. It also stores the flag indicating whether to add
        example aircraft and subcategories to the fleet.

        Warning
        ---------
        This method should be called only if end year was modified, otherwise it is called in __init__.

        """
        self.disciplines = []
        self.data = {}
        self.json = {}
        self._initialize_data()

    def setup_mda(self):
        """Configure the process for a standalone MDA chain.

        This method initializes generic energy inputs and disciplines,
        then builds a GEMSEO MDAChain with default convergence settings
        for multidisciplinary analysis execution of AeroMAPS.

        Warning
        ---------
        This method should be called only if end year was modified, otherwise it is called in __init__.
        """
        # Initialize energy carriers
        self._initialize_generic_energy()
        # Initialize climate model
        self._initialize_climate_model()
        # Initialize LCA model
        self._initialize_lca_model()
        # Initialize disciplines
        self._initialize_disciplines()

        self.mda_chain = MDAChain(
            disciplines=self.disciplines,
            tolerance=1e-5,
            initialize_defaults=True,
            inner_mda_name="MDAGaussSeidel",
            log_convergence=True,
        )

    def setup_optimisation(self):
        """Configure the process for GEMSEO-based optimization.

        This method initializes the internal GEMSEO settings dictionary
        so that optimization scenarios can be defined and executed later.
        """
        self._initialize_gemseo_settings()

    def create_gemseo_scenario(self):
        """Build a single-level GEMSEO MDO scenario.

        This method initializes generic energy inputs and disciplines,
        and then creates a GEMSEO scenario using the current
        ``gemseo_settings`` for objective, design space, scenario type,
        and formulation.
        """
        self._initialize_generic_energy()
        self._initialize_climate_model()
        self._initialize_lca_model()
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
        """Build a GEMSEO bilevel optimization formulation.

        This method wraps an inner GEMSEO scenario in an
        ``MDOScenarioAdapter`` and creates an outer scenario that
        optimizes over the adapter. If the inner scenario is not yet
        defined, it is created using the current ``gemseo_settings``.
        """
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
        """Run the configured analysis or optimization.

        This method prepares input data, then executes either a bilevel
        optimization, a single-level GEMSEO scenario, or an MDA chain
        depending on the current configuration. After execution, it
        updates the internal data structures with model outputs.
        """
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
        """Return all main DataFrames as a dictionary, generated on demand.

        This method generates and returns a dictionary of key DataFrames
        representing inputs, outputs, and climate-related quantities in a
        tabular form suitable for inspection or export.

        Returns
        -------
        dataframes
            Dictionary mapping DataFrame names to pandas DataFrame
            instances for data information, inputs, and outputs.
        """
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
        """
        Return the model outputs as a JSON-serializable dictionary.

        Returns
        -------
        json_data
            Dictionary containing JSON-compatible inputs and outputs.
        """
        return self._data_to_json()

    def write_json(self, file_name=None):
        """Write model inputs and outputs to a JSON file.

        This method builds the JSON-compatible data and writes it to
        disk, using either the provided file name or the path defined in
        the configuration.

        Parameters
        ----------
        file_name
            Path to the output JSON file. If None, the path from the
            configuration is used.
        """
        if file_name is None:
            file_name = self._resolve_config_path(
                "data", "outputs", "json_outputs_file",
                default_filename="outputs.json"
            )

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_name), exist_ok=True)

        # Retrieve the data from the model
        json_data = self.get_json()

        with open(file_name, "w", encoding="utf-8") as f:
            dump(json_data, f, ensure_ascii=False, indent=4)

    def write_excel(self, file_name=None):
        """Write main result tables to an Excel workbook.

        This method exports data information, inputs, and outputs into
        separate sheets of a single Excel file.

        Parameters
        ----------
        file_name
            Path to the output Excel file. If None, the path from the
            configuration is used.
        """
        if file_name is None:
            file_name = self._resolve_config_path(
                "data", "outputs", "excel_outputs_file",
                default_filename="data.xlsx"
            )
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
        """Generate an N2 diagram for the current disciplines.

        This method calls GEMSEO to create an N2 plot describing the
        coupling structure between the configured disciplines.
        """
        generate_n2_plot(self.disciplines)

    def list_available_plots(self):
        """List the names of supported plots.

        Returns
        -------
        plot_names
            List of strings identifying available plot functions.
        """
        return list(available_plots.keys())

    def list_float_inputs(self):
        """Return the current scalar input values.

        Returns
        -------
        float_inputs
            Dictionary of scalar input names and their values.
        """
        return self.data["float_inputs"]

    def list_str_inputs(self):
        """Return the current string input values.

        Returns
        -------
        str_inputs
            Dictionary of string input names and their values.
        """
        return self.data["str_inputs"]

    def plot(self, name, save=False, size_inches=None, remove_title=False):
        """Generate a predefined AeroMAPS plot.

        Depending on the plot name, this method uses either generic or
        fleet-specific plotting functions and optionally saves the figure
        to a PDF file.

        Parameters
        ----------
        name
            Identifier of the plot to generate, possible to obtain from list_available_plots().
        save
            Whether to save the generated plot as a PDF file.
        size_inches
            Optional figure size in inches as a tuple or list.
        remove_title
            Whether to remove the plot title before saving.

        Returns
        -------
        fig
            Object holding the created plot, as returned by the plot
            function.
        """
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
        """Prepare inputs and dependent models before execution.

        This method builds the input data dictionary from parameters,
        computes the fleet model if used, initializes discipline data
        frames, and returns the input mapping for the MDA chain or
        scenarios.

        Returns
        -------
        input_data
            Dictionary of input variable names and values for
            execution.
        """
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
        """Load and merge configuration settings.

        This method reads the default configuration YAML file, converts
        relative paths to absolute paths, and merges in overrides from
        the user-specified configuration file if provided.
        """
        # Load the default configuration file
        self._default_config = read_yaml_file(DEFAULT_CONFIG_PATH)
        self.config = deepcopy(self._default_config)
        
        # Set the base directory for resolving relative paths
        self._config_base_dir = DEFAULT_RESOURCES_DATA_DIR

        # Store user config separately to check what was explicitly set
        self._user_config = {}

        # Load the new configuration file and merge if provided
        if self.configuration_file is not None:
            self._user_config = read_yaml_file(self.configuration_file)
            self._config_base_dir = os.path.dirname(self.configuration_file)
            # Deep merge the new configuration into the default
            self._deep_merge_config(self.config, self._user_config)

    def _deep_merge_config(self, base: dict, override: dict) -> dict:
        """Recursively merge override config into base config.

        Parameters
        ----------
        base
            The base configuration dictionary to merge into.
        override
            The override configuration dictionary.

        Returns
        -------
        base
            The merged configuration dictionary.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge_config(base[key], value)
            else:
                base[key] = value
        return base

    def _get_config_value(self, *keys, default=None):
        """Get a value from the nested configuration dictionary.

        Parameters
        ----------
        *keys
            Sequence of keys to navigate the nested config.
        default
            Default value if the key path doesn't exist.

        Returns
        -------
        value
            The configuration value or the default.
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def _get_user_config_value(self, *keys, default=None):
        """Get a value from the user configuration dictionary only.

        This checks only the user-provided configuration, not the merged
        config with defaults. Use this to determine if a user explicitly
        set a value.

        Parameters
        ----------
        *keys
            Sequence of keys to navigate the nested config.
        default
            Default value if the key path doesn't exist.

        Returns
        -------
        value
            The user configuration value or the default.
        """
        value = self._user_config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def _get_default_config_value(self, *keys, default=None):
        """Get a value from the default (package) configuration dictionary.

        This checks only the default configuration from the package,
        not the merged config with user overrides.

        Parameters
        ----------
        *keys
            Sequence of keys to navigate the nested config.
        default
            Default value if the key path doesn't exist.

        Returns
        -------
        value
            The default configuration value or the default.
        """
        value = self._default_config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def _resolve_config_file_path(self, *keys, default_filename: str = None) -> Union[Path, None]:
        """Resolve a file path from nested config keys.

        Parameters
        ----------
        *keys
            Sequence of keys to navigate the nested config.
        default_filename
            Fallback filename if config key doesn't exist.

        Returns
        -------
        path
            Absolute path to the file, or None if not found.
        """
        path_value = self._get_config_value(*keys)
        if path_value is None or not isinstance(path_value, str):
            if default_filename is None:
                return None
            path_value = default_filename

        if os.path.isabs(path_value):
            return Path(path_value)

        return Path(os.path.normpath(os.path.join(self._config_base_dir, path_value)))

    def _resolve_config_path(self, *keys, default_filename: str = None) -> Union[Path, None]:
        """Resolve a config path with fallback to default.

        Parameters
        ----------
        *keys
            Sequence of keys to navigate the nested config.
        default_filename
            Fallback filename relative to resources/data.

        Returns
        -------
        path
            Resolved absolute path.
            
        Notes
        -----
        If the user specifies `"default"` as the value, the path will be resolved
        from the default configuration file (relative to the package's resources/data directory).
        This is useful when the package is installed via pip and relative paths would not work.
        """
        resolved_path = None
        
        # First check if user explicitly set this in their config
        user_value = self._get_user_config_value(*keys)
        if user_value is not None and isinstance(user_value, str):
            if user_value.lower() == "default":
                # User wants to use the default value from the package's config
                default_value = self._get_default_config_value(*keys)
                if default_value is not None and isinstance(default_value, str):
                    if os.path.isabs(default_value):
                        resolved_path = Path(default_value)
                    else:
                        resolved_path = Path(os.path.normpath(os.path.join(DEFAULT_RESOURCES_DATA_DIR, default_value)))
            elif os.path.isabs(user_value):
                resolved_path = Path(user_value)
            else:
                resolved_path = Path(os.path.normpath(os.path.join(self._config_base_dir, user_value)))
        
        # Check if value exists in merged config (from default config)
        elif (config_value := self._get_config_value(*keys)) is not None and isinstance(config_value, str):
            if os.path.isabs(config_value):
                resolved_path = Path(config_value)
            else:
                # Resolve relative to default resources/data directory
                resolved_path = Path(os.path.normpath(os.path.join(DEFAULT_RESOURCES_DATA_DIR, config_value)))
        
        # Fallback to default filename if provided
        elif default_filename is not None:
            resolved_path = Path(os.path.join(DEFAULT_RESOURCES_DATA_DIR, default_filename))
        
        # Warn if the resolved path doesn't exist
        if resolved_path is not None and not resolved_path.exists():
            config_key = ".".join(keys)
            logging.warning(
                f"Configuration file not found: '{resolved_path}' "
                f"(config key: {config_key}). Please check the path in your configuration file."
            )
        
        return resolved_path

    def _initialize_data(self):
        """Initialize core data containers and indices."""
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
        """Initialize generic energy resources, processes, and carriers.

        This method calls the internal methods to read resource and
        process data, and to instantiate the generic energy carrier models.
        Skipped if models.energy key is not present in the user configuration.
        """
        # Check if energy models should be used (key must be present in user config)
        energy_config = self._get_user_config_value("models", "energy", default=None)
        if energy_config is None:
            return
            
        self._read_generic_resources_data()
        self._read_generic_process_data()
        self._instantiate_generic_energy_models()

    def _read_generic_resources_data(self):
        """Read and process generic energy resources data.

        This method loads resource specifications from a YAML file,
        flattens nested inputs, converts custom data types, and updates
        parameters and internal resource metadata.
        """
        self.energy_resources_data = {}

        # Check if resources model data file is specified in config
        resources_config = self._get_user_config_value(
            "models", "energy", "resources_model_data_file", default=None)
        if resources_config is None:
            return

        resources_data_file_path = self._resolve_config_path(
            "models", "energy", "resources_model_data_file",
            default_filename="default_energy_carriers/resources_data.yaml"
        )

        self.energy_resources_data = read_yaml_file(str(resources_data_file_path))

        # The first level of the yaml conf file contains all the pathways
        resources = list(self.energy_resources_data.keys())

        for resource in resources:
            resource_data = self.energy_resources_data[resource]
            if "name" not in resource_data:
                raise ValueError("The resource configuration file should contain its name")

            # Flatten the inputs dictionary and interpolate the necessary values

            flattened_yaml = _flatten_dict(resource_data["specifications"], resource_data["name"])
            resource_data["specifications"] = self._convert_custom_data_types(flattened_yaml)

            self.parameters.from_dict(resource_data["specifications"])

            self.energy_resources_data[resource] = resource_data

    def _read_generic_process_data(self):
        """Read and process generic energy process data.

        This method loads process specifications from a YAML file,
        flattens nested inputs, converts custom data types, and updates
        parameters and internal process metadata.
        """
        self.energy_processes_data = {}

        # Check if processes model data file is specified in config
        processes_config = self._get_user_config_value(
            "models", "energy", "processes_model_data_file", default=None)
        if processes_config is None:
            return

        processes_data_path = self._resolve_config_path(
            "models", "energy", "processes_model_data_file",
            default_filename="default_energy_carriers/processes_data.yaml"
        )

        self.energy_processes_data = read_yaml_file(str(processes_data_path))

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
                flattened_yaml = _flatten_dict(value, process_data["name"])
                inputs[key] = self._convert_custom_data_types(flattened_yaml)
                # set data to parameters
                self.parameters.from_dict(inputs[key])

            process_data["inputs"] = inputs

            self.energy_processes_data[process] = process_data

    def _instantiate_generic_energy_models(self):
        """Instantiate generic energy carrier and resource models.

        This method reads energy carrier pathway configurations, builds
        carrier metadata, flattens and converts inputs, and uses the
        ``AviationEnergyCarriersFactory`` to create carrier, resource
        consumption, and choice models, which are added to the models
        dictionary.
        """
        energy_carriers_data_file_path = self._resolve_config_path(
            "models", "energy", "energy_carriers_model_data_file",
            default_filename="default_energy_carriers/energy_carriers_data.yaml"
        )

        self.energy_carriers_data = read_yaml_file(str(energy_carriers_data_file_path))

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
                flattened_yaml = _flatten_dict(value, pathway_data["name"])
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
        """Read the climate config file and instantiate ClimateModel accordingly.

        The config file should contain:
        - climate_model: str, name of the climate model to use
        - species_settings: dict, settings for each species
        - model_settings: dict, settings for the climate model
        Refer to the documentation of AeroCM for more details: https://github.com/AeroMAPS/AeroCM
        
        Skipped if models.climate key is not present in the user configuration.
        """
        # Check if climate model should be used (key must be present in user config)
        climate_config = self._get_user_config_value("models", "climate", default=None)
        if climate_config is None:
            return
            
        climate_model_file_path = self._resolve_config_path(
            "models", "climate", "climate_model_data_file",
            default_filename="../climate_data/climate_model_fair.yaml"
        )

        if climate_model_file_path and climate_model_file_path.exists():
            climate_model_data = read_yaml_file(str(climate_model_file_path))
            self.models.update(
                {"climate_model": ClimateModel(
                    name="climate_model",
                    climate_model=climate_model_data.get("climate_model", "FaIR"),
                    species_settings=climate_model_data.get("species_settings", {}),
                    model_settings=climate_model_data.get("model_settings", {})
                )}
            )

    def _initialize_lca_model(self):
        """Read the LCA config file and instantiate LCA model accordingly.

        The config file should contain:
        - lca_model_data_file: str, path to the LCA model to use (either json for default LCA model, or yaml for custom LCA model)
        - split_by: optional, settings for splitting LCA results by e.g. 'phase'

        Skipped if models.life_cycle_assessment key is not present in the user configuration.
        """

        # Check if LCA model should be used (key must be present in user config)
        lca_config = self._get_user_config_value("models", "life_cycle_assessment", default=None)
        if lca_config is None:
            return

        # Set up temporary file path for LCA model caching (for better performance within the same session)
        config_dir = Path(self.configuration_file).resolve().parent
        tmp_dir = config_dir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)  # create folder if needed
        lca_tmp_file_path = tmp_dir / "lca_tmp.pkl"

        # The user can specify to load the LCA model from a temporary file, e.g. if already compiled in the same session
        if lca_config.get("lca_model_data_file") == '#tmp':
            with open(lca_tmp_file_path, "rb") as f:
                lca_instance = dill.load(f)
            logging.info("Loaded LCA model from temporary file (precompiled from latest run in current session).")
            self.models.update(
                {"life_cycle_assessment": lca_instance}
            )
            return

        # Otherwise, read the LCA model file path from config
        lca_model_file_path = self._resolve_config_path(
            "models", "life_cycle_assessment", "lca_model_data_file",
            default_filename="../lca_data/default_lca_model.json"
        )
        if lca_model_file_path and lca_model_file_path.exists():
            # If json file, use the default LCA model class
            if lca_model_file_path.suffix.lower() == ".json":
                lca_instance = LifeCycleAssessmentDefault(
                        name="life_cycle_assessment",
                        json_file=str(lca_model_file_path),
                        split_by=self._get_config_value("models", "life_cycle_assessment", "split_by", default=None)
                    )
            # If yaml file, use the custom LCA model class
            elif lca_model_file_path.suffix.lower() in [".yaml", ".yml"]:
                if LCA_PACKAGES_INSTALLED is False:
                    raise ImportError(
                        "To use a custom LCA model, please install the optional dependencies: "
                        "pip install --upgrade aeromaps[lca]"
                    )
                lca_instance = LifeCycleAssessmentCustom(
                    name="life_cycle_assessment",
                    configuration_file=lca_model_file_path,
                    split_by=self._get_config_value("models", "life_cycle_assessment", "split_by", default=None)
                )
            else:
                raise ValueError(
                    "LCA model file must be either a .json (default LCA model) or .yaml/.yml (custom LCA model) file.")

            # Update the models dictionary
            self.models.update(
                {"life_cycle_assessment": lca_instance}
            )

            # Store the LCA model instance in a temporary file for faster loading in the same session
            with open(lca_tmp_file_path, "wb") as f:
                dill.dump(lca_instance, f)

    def _convert_custom_data_types(self, data):
        """Convert custom YAML data types and register interpolators.

        This method reads a flattened YAML mapping, instantiates
        interpolator models when encountering a custom data type, adds
        reference years and values to parameters, and converts the custom
        type to a normal series in the flattened YAML so that generic
        energy models receive interpolated input types.

        Parameters
        ----------
        data
            Flattened dictionary of configuration entries to inspect.

        Returns
        -------
        data_converted
            Modified dictionary with custom types converted to standard
            series values.
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
        """Wrap models as GEMSEO disciplines and configure coupling.

        This method optionally instantiates the bottom-up fleet model,
        assigns shared parameters and climate data to each AeroMAPS
        model, applies custom setups when needed, wraps models into
        GEMSEO discipline adapters, and stores them in the disciplines
        list.

        """
        # Check if fleet model should be used
        # Fleet model is enabled only if models.fleet key exists in user config and is a dict
        fleet_config = self._get_user_config_value("models", "fleet", default=None)
        use_fleet_model = isinstance(fleet_config, dict)
        
        if use_fleet_model:

            aircraft_inventory_path = self._resolve_config_path(
                "models", "fleet", "aircraft_inventory_model_data_file",
                default_filename="default_fleet/aircraft_inventory.yaml"
            )

            fleet_config_path = self._resolve_config_path(
                "models", "fleet", "fleet_model_data_file",
                default_filename="default_fleet/fleet.yaml"
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
                    if hasattr(self, "fleet_model"):
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
        """Initialize year index ranges for all time series.

        This method computes historic, climate historic, and prospective
        year ranges from the parameters and stores them in the data
        dictionary.
        """
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
        """Initialize model parameters from JSON and vector inputs.

        This method creates a parameters instance, reads default and
        optional configuration-specific JSON files, normalizes time
        series indices, and initializes and formats vector inputs.

        Parameters
        ----------
        use_defaults
            Whether to load the default parameters JSON file before
            applying configuration-specific overrides.
        """
        self.parameters = Parameters()

        # First use main parameters.json as default values (always from resources/data)
        default_params_path = Path(
            os.path.join(DEFAULT_RESOURCES_DATA_DIR, "parameters.json")
        )
        if use_defaults:
            self.parameters.read_json(file_name=str(default_params_path))

        # Load additional parameters from user configuration if provided
        # Use _get_user_config_value to check what the user explicitly set
        # (not the merged config which includes defaults)
        json_inputs_config = self._get_user_config_value("data", "inputs", "json_inputs_file")
        if self.configuration_file is not None and json_inputs_config is not None:
            # If the alternative file is a list of json files
            if isinstance(json_inputs_config, list):
                merged_data = {}
                for json_file in json_inputs_config:
                    file_path = os.path.join(self._config_base_dir, json_file)
                    with open(file_path, "r") as f:
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
                user_input_file_path = self._resolve_config_file_path(
                    "data", "inputs", "json_inputs_file"
                )
                if user_input_file_path:
                    self.parameters.read_json(file_name=str(user_input_file_path))

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
        """Load and register vector input time series from a JSON file.

        This method reads the vector inputs JSON file, converts each
        key into a pandas Series indexed by years, and attaches them as 
        attributes to the parameters object.
        
        The JSON file should contain a dictionary with:
        - "other_float_data": scalar values (stored as-is)
        - "other_vector_data": vector inputs indexed by years
        - "climate_data": handled separately by _initialize_climate_historical_data
        
        Example JSON format:
        {
            "other_float_data": {
                "short_range_energy_share_2019": 10.5,
                ...
            },
            "other_vector_data": {
                "years": [2000, 2001, ..., 2019],
                "rpk_init": [value_2000, value_2001, ..., value_2019],
                ...
            },
            "climate_data": {
                "years": [...],
                "co2_emissions": [...],
                ...
            }
        }
        """
        vector_inputs_data_file_path = self._resolve_config_path(
            "data", "inputs", "partitioning_data_file",
            default_filename="partitioning_data.json"
        )
        
        if vector_inputs_data_file_path is None:
            return

        # Read JSON file (utf-8-sig handles BOM if present)
        with open(vector_inputs_data_file_path, "r", encoding="utf-8-sig") as f:
            vector_inputs_data = load(f)
        
        # Store climate_data section for later use by _initialize_climate_historical_data
        if "climate_data" in vector_inputs_data:
            self._partitioned_climate_data = vector_inputs_data.pop("climate_data")
        
        # Process other_float_data section (scalar inputs)
        if "other_float_data" in vector_inputs_data:
            other_float_data = vector_inputs_data.pop("other_float_data")
            for param_name, value in other_float_data.items():
                setattr(self.parameters, param_name, value)
        
        # Process other_vector_data section (vector inputs with years index)
        if "other_vector_data" in vector_inputs_data:
            other_vector_data = vector_inputs_data.pop("other_vector_data")
            years_index = other_vector_data.pop("years", None)
            
            for param_name, value in other_vector_data.items():
                if isinstance(value, list) and years_index is not None:
                    setattr(self.parameters, param_name, pd.Series(value, index=years_index))
                else:
                    setattr(self.parameters, param_name, value)

    def _initialize_climate_historical_data(self):
        """Load the historical climate dataset.

        This method reads the configured climate data from either:
        - A "climate_data" section in the partitioning JSON file (if available)
        - A CSV file specified by partitioning_climate_data_file config key
        
        The data is stored as a NumPy array for climate-related models.
        """
        # Check if climate data was loaded from the partitioning JSON file
        if hasattr(self, "_partitioned_climate_data") and self._partitioned_climate_data is not None:
            climate_data = self._partitioned_climate_data
            self.climate_historical_data = np.column_stack([
                climate_data["years"],
                climate_data["co2_emissions"],
                climate_data["nox_emissions"],
                climate_data["h2o_emissions"],
                climate_data["soot_emissions"],
                climate_data["sulfur_emissions"],
                climate_data["distance"],
            ])
            return
        
        # Fallback to CSV file
        climate_historical_data_file_path = self._resolve_config_path(
            "data", "inputs", "partitioning_climate_data_file",
            default_filename="../climate_data/temperature_historical_dataset.csv"
        )

        historical_dataset_df = pd.read_csv(
            climate_historical_data_file_path, delimiter=";", header=None
        )
        self.climate_historical_data = historical_dataset_df.values

    def _initialize_gemseo_settings(self):
        """Initialize default GEMSEO configuration settings.

        This method resets GEMSEO scenario-related attributes and
        populates the settings dictionary with default values for design
        space, objective, algorithm, and formulation options.
        """
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
        """Normalize parameter vector shapes and indices.

        This method pads or reindexes selected initialization vectors and
        other time series so that they match the expected year ranges for
        historic and climate data in the parameters.
        """
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
        """Refresh data, DataFrames, and JSON cache from model results.

        This convenience method updates internal data structures from the
        discipline models, regenerates derived DataFrames, and rebuilds
        the JSON-compatible representation of inputs and outputs.
        """
        self._update_data_from_model()

        self._update_dataframes_from_data()

        self._update_json_from_data()

    def _update_data_from_model(self):
        """Update internal input and output data from disciplines.

        This method collects input values from the MDA chain or
        individual disciplines, categorizes them into scalar, string, and
        vector inputs, and aggregates all discipline outputs into shared
        vector, climate, and LCA output structures.
        """
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
                self.data["lca_outputs"] = disc.model.xarray_lca

            self.data["float_outputs"].update(disc.model.float_outputs)

    def _get_float_inputs_df(self):
        """Build a DataFrame of scalar input values.

        Returns
        -------
        float_inputs_df
            DataFrame with scalar input names and values.
        """
        data = {
            "Name": self.data["float_inputs"].keys(),
            "Value": self.data["float_inputs"].values(),
        }
        return pd.DataFrame(data=data)

    def _get_str_inputs_df(self):
        """Build a DataFrame of string input values.

        Returns
        -------
        str_inputs_df
            DataFrame with string input names and values.
        """
        data = {
            "Name": self.data["str_inputs"].keys(),
            "Value": self.data["str_inputs"].values(),
        }
        return pd.DataFrame(data=data)

    def _get_vector_inputs_df(self):
        """Build a DataFrame of vector input time series.

        Returns
        -------
        vector_inputs_df
            DataFrame with one column per vector input and years as
            index.
        """
        df = _dict_to_df(self.data["vector_inputs"], orient="columns")
        df.sort_index(axis=1, inplace=True)
        return df

    def _get_float_outputs_df(self):
        """Build a DataFrame of scalar output values.

        Returns
        -------
        float_outputs_df
            DataFrame with scalar output names and values.
        """
        data = {
            "Name": self.data["float_outputs"].keys(),
            "Value": self.data["float_outputs"].values(),
        }
        return pd.DataFrame(data=data)

    def _get_vector_outputs_df(self):
        """Build a DataFrame of vector output time series.

        Returns
        -------
        vector_outputs_df
            DataFrame with one column per vector output and years as
            index.
        """
        df = self.data["vector_outputs"].copy()
        df.sort_index(axis=1, inplace=True)
        return df

    def _get_climate_outputs_df(self):
        """Build a DataFrame of climate-related outputs.

        Returns
        -------
        climate_outputs_df
            DataFrame with climate output time series and years as
            index.
        """
        df = self.data["climate_outputs"].copy()
        df.sort_index(axis=1, inplace=True)
        return df

    def _get_data_information_df(self):
        """Build the consolidated data information table.

        Returns
        -------
        data_information_df
            DataFrame summarizing inputs and outputs with metadata from
            the data information CSV file.
        """
        return self._read_data_information()

    def _data_to_json(self):
        """Convert internal data structures into JSON-compatible containers.

        This method converts series and arrays into lists and returns a
        dictionary containing all main input and output categories.

        Returns
        -------
        json_data
            Dictionary with JSON-serializable inputs and outputs.
        """

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
        """Read and merge data descriptions from the information CSV file.

        This method scans the current inputs and outputs, looks up their
        metadata in the data information CSV file, and builds a
        consolidated table including type, unit, and description for each
        variable.

        Parameters
        ----------
        file_name
            Path to the data information CSV file. If None, the path
            from the configuration is used.

        Returns
        -------
        data_information_df
            DataFrame containing metadata for all current inputs and
            outputs.
        """
        if file_name is None:
            file_name = self._resolve_config_path(
                "data", "inputs", "csv_data_information_file",
                default_filename="data_information.csv"
            )
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

# Standard library imports
import os
from json import load, dump

# Third-party imports
import numpy as np
import pandas as pd

from gemseo import generate_n2_plot, create_scenario, create_mda
from gemseo.disciplines.scenario_adapters.mdo_scenario_adapter import MDOScenarioAdapter
from gemseo.mda.mda_chain import MDAChain
from gemseo.mda.gauss_seidel import MDAGaussSeidel
from gemseo.core.discipline import Discipline


# Local application imports
from aeromaps.models.base import AeroMAPSModel
from aeromaps.core.gemseo import AeroMAPSModelWrapper
from aeromaps.core.models import default_models_top_down
from aeromaps.models.parameters import Parameters
from aeromaps.utils.functions import _dict_to_df
from aeromaps.plots import available_plots, available_plots_fleet
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model import (
    Fleet,
    FleetModel,
)

# Settings
pd.options.display.max_rows = 150
pd.set_option("display.max_columns", 150)
pd.set_option("max_colwidth", 200)
pd.options.mode.chained_assignment = None

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the config.json file
default_config_path = os.path.join(current_dir, "config.json")

# Construct the path to the parameters.json file
default_parameters_path = os.path.join(current_dir, "..", "resources", "data", "parameters.json")

# Construct the path to the vector_inputs.csv file
default_vector_inputs_data_path = os.path.join(
    current_dir, "..", "resources", "data", "vector_inputs.csv"
)

# Construct the path to the climate data .csv file
default_climate_historical_data_path = os.path.join(
    current_dir, "..", "resources", "climate_data", "temperature_historical_dataset.csv"
)


class AeroMAPSProcess(object):
    def __init__(
        self,
        configuration_file: str = None,
        models: dict = default_models_top_down,
        use_fleet_model: bool = False,
        add_examples_aircraft_and_subcategory: bool = True,
    ):
        self.configuration_file = configuration_file
        self.use_fleet_model = use_fleet_model

        self.disciplines = []
        self.data = {}
        self.json = {}
        self.models = models

        self._initialization(add_examples_aircraft_and_subcategory)

    def _initialization(self, add_examples_aircraft_and_subcategory=True):
        # Initialize the configuration settings
        self._initialize_configuration()

        # Initialize the input data
        self._initialize_inputs()

        # Initialize the years data
        self._initialize_years()

        # Initialize the disciplines, optionally adding example aircraft and subcategories
        self._initialize_disciplines(add_examples_aircraft_and_subcategory)

        # Initialize the GEMSEO settings
        self._initialize_gemseo()

        # Initialize the data structures
        self._initialize_data()

        # TODO: check if we need to know inputs before computing
        # self._update_variables()

    def setup(self):
        # Initialize the default inputs of disciplines
        self._set_inputs()

        # # Create MDA chain
        self.mda_chain = MDAChain(
            disciplines=self.disciplines,
            grammar_type=Discipline.GrammarType.SIMPLE,
            tolerance=1e-6,
            initialize_defaults=True,
            inner_mda_name="MDAGaussSeidel",
            log_convergence=True,
        )

    def create_gemseo_scenario(self):
        # if no mda_chain is created raise an error setup needs to be called first
        if self.mda_chain is None:
            raise ValueError("MDA chain not created. Please call setup() first.")

        # Create GEMSEO process
        self.scenario = create_scenario(
            disciplines=self.mda_chain,
            formulation=self.gemseo_settings["formulation"],
            objective_name=self.gemseo_settings["objective_name"],
            design_space=self.gemseo_settings["design_space"],
            scenario_type=self.gemseo_settings["scenario_type"],
            grammar_type=self.gemseo_settings["grammar_type"],
            input_data=self.input_data,
        )

    def create_gemseo_doe(self):
        # if no scenario is created raise an error create_gemseo_scenario needs to be called first
        if self.scenario is None:
            raise ValueError(
                "GEMSEO scenario not created. Please call create_gemseo_scenario() first."
            )

        # dv_names = self.scenario.formulation.design_variables.keys()
        self.adapter = MDOScenarioAdapter(
            # TODO make generic
            self.scenario,
            input_names=self.gemseo_settings["doe_input_names"],
            output_names=self.gemseo_settings["doe_output_names"],
            grammar_type=self.gemseo_settings["grammar_type"],
            set_x0_before_opt=True,
        )

        self.scenario_doe = create_scenario(
            self.adapter,
            formulation=self.gemseo_settings["formulation"],
            objective_name=self.gemseo_settings["objective_name"],
            design_space=self.gemseo_settings["design_space"],
            scenario_type="DOE",
            grammar_type=self.gemseo_settings["grammar_type"],
        )

    def compute(self):
        # import time
        #
        # # Start the timer
        # start_time = time.time()

        self._pre_compute()
        # Time for _pre_compute
        # pre_compute_time = time.time()
        # print(f"Pre-compute time: {pre_compute_time - start_time} seconds")
        if self.scenario is not None:
            if self.scenario_doe is not None:
                print("Running DOE")
                self.scenario.default_inputs.update(self.scenario.options)
                self.scenario_doe.execute(
                    input_data={"algo": "CustomDOE", "algo_options": {"samples": self.samples}}
                )
            else:
                print("Running MDO")
                self.scenario.execute(input_data=self.scenario.options)
            print("Running MDA")
            self.mda_chain.execute(input_data=self.input_data)

        # # Time for compute
        # compute_time = time.time()
        # print(f"Compute time: {compute_time - pre_compute_time} seconds")

        self._post_compute()
        # # Time for _post_compute
        # post_compute_time = time.time()
        # print(f"Post-compute time: {post_compute_time - compute_time} seconds")

    def write_json(self, file_name=None):
        if file_name is None:
            file_name = self.config["OUTPUTS_JSON_DATA_FILE"]
        with open(file_name, "w", encoding="utf-8") as f:
            dump(self.json, f, ensure_ascii=False, indent=4)

    def write_excel(self, file_name=None):
        if file_name is None:
            file_name = self.config["EXCEL_DATA_FILE"]
        with pd.ExcelWriter(file_name) as writer:
            self.data_information_df.to_excel(writer, sheet_name="Data Information")
            self.vector_inputs_df.to_excel(writer, sheet_name="Vector Inputs")
            self.float_inputs_df.to_excel(writer, sheet_name="Float Inputs")
            self.vector_outputs_df.to_excel(writer, sheet_name="Vector Outputs")
            self.float_outputs_df.to_excel(writer, sheet_name="Float Outputs")
            self.climate_outputs_df.to_excel(writer, sheet_name="Climate Outputs")

    def generate_n2(self):
        generate_n2_plot(self.disciplines)

    def update_parameters(self):
        for name, model in self.models.items():
            model.parameters = self.parameters

    def list_available_plots(self):
        return list(available_plots.keys())

    def list_float_inputs(self):
        return self.data["float_inputs"]

    def plot(self, name, save=False, size_inches=None, remove_title=False):
        if name in available_plots_fleet:
            try:
                fig = available_plots_fleet[name](self.data, self.fleet_model)
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
            fig = available_plots[name](self.data)
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

    def _initialize_gemseo(self):
        self.scenario = None
        self.scenario_doe = None
        self.gemseo_settings = {}

        # Mandatory settings
        self.gemseo_settings["design_space"] = None
        self.gemseo_settings["objective_name"] = None

        # Optional settings
        self.gemseo_settings["formulation"] = "MDF"
        self.gemseo_settings["scenario_type"] = "MDO"
        self.gemseo_settings["grammar_type"] = Discipline.GrammarType.SIMPLE
        self.gemseo_settings["doe_input_names"] = None
        self.gemseo_settings["doe_output_names"] = None

    def _pre_compute(self):
        if self.fleet is not None:
            # Necessary when user hard coded the fleet
            self.fleet_model.fleet.all_aircraft_elements = (
                self.fleet_model.fleet.get_all_aircraft_elements()
            )
            self.fleet_model.compute()

        self.input_data.update(self._set_inputs())

        if self.fleet is not None:
            # This is needed since fleet model is particular discipline
            self.input_data["dummy_fleet_model_output"] = np.random.rand(1, 1)

    def _post_compute(self):
        self._update_variables()

        if self.configuration_file is not None and "OUTPUTS_JSON_DATA_FILE" in self.config:
            configuration_directory = os.path.dirname(self.configuration_file)
            new_output_file_path = os.path.join(
                configuration_directory, self.config["OUTPUTS_JSON_DATA_FILE"]
            )
            file_name = new_output_file_path
        else:
            file_name = None
        self.write_json(file_name=file_name)

    def _initialize_configuration(self):
        # Load the default configuration file
        with open(default_config_path, "r") as f:
            self.config = load(f)
        # Update paths in the configuration file with absolute paths
        for key, value in self.config.items():
            self.config[key] = os.path.join(current_dir, value)

        # Load the new configuration file
        if self.configuration_file is not None:
            with open(self.configuration_file, "r") as f:
                new_config = load(f)
            # Replace the default configuration with the new configuration
            for key, value in new_config.items():
                self.config[key] = value

    def _initialize_data(self):
        # Inputs
        self.data["float_inputs"] = {}
        # TODO: explore the possibility of using a dataframe for vector inputs
        self.data["vector_inputs"] = {}

        # Outputs
        self.data["float_outputs"] = {}
        self.data["vector_outputs"] = pd.DataFrame(index=self.data["years"]["full_years"])
        self.data["climate_outputs"] = pd.DataFrame(index=self.data["years"]["climate_full_years"])

    def _initialize_disciplines(self, add_examples_aircraft_and_subcategory=True):
        if self.use_fleet_model:
            self.fleet = Fleet(
                add_examples_aircraft_and_subcategory=add_examples_aircraft_and_subcategory,
                parameters=self.parameters,
            )
            self.fleet_model = FleetModel(fleet=self.fleet)
            self.fleet_model.parameters = self.parameters
            self.fleet_model._initialize_df()
        else:
            self.fleet = None

        def check_instance_in_dict(d):
            for key, value in d.items():
                if isinstance(value, dict):
                    check_instance_in_dict(value)
                elif isinstance(value, AeroMAPSModel):
                    model = value
                    # TODO: check how to avoid providing all parameters
                    model.parameters = self.parameters
                    model._initialize_df()
                    if self.use_fleet_model and hasattr(model, "fleet_model"):
                        model.fleet_model = self.fleet_model
                    if hasattr(model, "climate_historical_data"):
                        model.climate_historical_data = self.climate_historical_data
                    if hasattr(model, "compute"):
                        model = AeroMAPSModelWrapper(model=model)
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

    def _initialize_inputs(self):
        self.input_data = {}
        self._initialize_parameters()
        self._initialize_vector_inputs()
        self._initialize_climate_historical_data()

    def _initialize_parameters(self):
        self.parameters = Parameters()
        # First use main parameters.json as default values
        self.parameters.read_json(file_name=default_parameters_path)
        if self.configuration_file is not None and "PARAMETERS_JSON_DATA_FILE" in self.config:
            configuration_directory = os.path.dirname(self.configuration_file)
            new_input_file_path = os.path.join(
                configuration_directory, self.config["PARAMETERS_JSON_DATA_FILE"]
            )
            # If an alternative file is provided overwrite values
            if new_input_file_path != default_parameters_path:
                self.parameters.read_json(file_name=new_input_file_path)
        # TODO: think refactoring to a dedicated method
        # Check if parameter is pd.Series and update index
        for key, value in self.parameters.__dict__.items():
            if isinstance(value, pd.Series):
                new_index = range(self.parameters.historic_start_year, self.parameters.end_year + 1)
                value = value.reindex(new_index, fill_value=np.nan)
                setattr(self.parameters, key, value)

    def _initialize_vector_inputs(self):
        if self.configuration_file is not None and "VECTOR_INPUTS_DATA_FILE" in self.config:
            configuration_directory = os.path.dirname(self.configuration_file)
            vector_inputs_data_file_path = os.path.join(
                configuration_directory, self.config["VECTOR_INPUTS_DATA_FILE"]
            )
        else:
            vector_inputs_data_file_path = default_vector_inputs_data_path

        # Read .csv with first line column names
        vector_inputs_df = pd.read_csv(vector_inputs_data_file_path, delimiter=";", header=0)

        # Generate pd.Series for each column with index the year stored in first column
        for column in vector_inputs_df.columns:
            values = vector_inputs_df[column].values
            index = vector_inputs_df.iloc[:, 0].values
            setattr(self.parameters, column, pd.Series(values, index=index))

    def _initialize_climate_historical_data(self):
        if self.configuration_file is not None and "PARAMETERS_CLIMATE_DATA_FILE" in self.config:
            configuration_directory = os.path.dirname(self.configuration_file)
            climate_historical_data_file_path = os.path.join(
                configuration_directory, self.config["PARAMETERS_CLIMATE_DATA_FILE"]
            )
        else:
            climate_historical_data_file_path = default_climate_historical_data_path

        historical_dataset_df = pd.read_csv(
            climate_historical_data_file_path, delimiter=";", header=None
        )
        self.climate_historical_data = historical_dataset_df.values

    def _set_inputs(self):
        all_inputs = {}
        # self._format_input_vectors()
        # TODO: make this more efficient
        for disc in self.disciplines:
            disc.model.parameters = self.parameters
            disc.model._initialize_df()
            disc.update_defaults()

        all_inputs.update(self.parameters.__dict__)

        return all_inputs

    def _format_input_vectors(self):
        for field_name, field_value in self.parameters.__dict__.items():
            if not isinstance(field_value, (float, int, list)):
                new_size = self.parameters.end_year - self.parameters.historic_start_year + 1
                new_value = np.pad(
                    field_value,
                    (0, new_size - field_value.size),
                    mode="constant",
                    constant_values=np.nan,
                )
                new_index = range(self.parameters.historic_start_year, self.parameters.end_year + 1)
                new_value = pd.Series(new_value, index=new_index)
                setattr(self.parameters, field_name, new_value)

    def _update_variables(self):
        self._update_data_from_model()

        self._update_dataframes_from_data()

        self._update_json_from_data()

    def _update_data_from_model(self):
        # Inputs
        all_inputs = self.mda_chain.get_input_data()

        for name in all_inputs:
            try:
                value = getattr(self.parameters, name)
                if isinstance(value, (float, int, list)):
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

            self.data["float_outputs"].update(disc.model.float_outputs)

    def _update_dataframes_from_data(self):
        # Float parameters
        data = {
            "Name": self.data["float_inputs"].keys(),
            "Value": self.data["float_inputs"].values(),
        }
        self.float_inputs_df = pd.DataFrame(data=data)

        # Vector parameters
        self.vector_inputs_df = _dict_to_df(self.data["vector_inputs"], orient="columns")
        self.vector_inputs_df.sort_index(axis=1, inplace=True)

        # Float outputs df
        data = {
            "Name": self.data["float_outputs"].keys(),
            "Value": self.data["float_outputs"].values(),
        }
        self.float_outputs_df = pd.DataFrame(data=data)

        # Vector outputs dataframe
        self.vector_outputs_df = self.data["vector_outputs"]
        self.vector_outputs_df.sort_index(axis=1, inplace=True)

        # Vector climate dataframe
        self.climate_outputs_df = self.data["climate_outputs"]
        self.climate_outputs_df.sort_index(axis=1, inplace=True)

        # Variable information
        self._read_data_information()

    def _update_json_from_data(self):
        def convert_values_from_array_to_list(d):
            for key, value in d.items():
                if isinstance(value, (pd.Series, np.ndarray)):
                    d[key] = list(value)
            return d

        # Float inputs
        self.json["float_inputs"] = convert_values_from_array_to_list(self.data["float_inputs"])

        # Vector inputs
        self.json["vector_inputs"] = convert_values_from_array_to_list(self.data["vector_inputs"])

        # Float outputs
        self.json["float_outputs"] = convert_values_from_array_to_list(self.data["float_outputs"])

        # Vector outputs
        self.json["vector_outputs"] = convert_values_from_array_to_list(
            self.data["vector_outputs"].to_dict("list")
        )

        # Climate outputs
        self.json["climate_outputs"] = convert_values_from_array_to_list(
            self.data["climate_outputs"].to_dict("list")
        )

    def _read_data_information(self, file_name=None):
        if file_name is None:
            file_name = self.config["EXCEL_DATA_INFORMATION_FILE"]
        df = pd.read_csv(file_name, encoding="utf-8", sep=";")

        var_infos_df = pd.DataFrame()
        for data_type, variables in self.data.items():
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

        self.data_information_df = var_infos_df

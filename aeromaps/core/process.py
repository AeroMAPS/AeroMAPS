import os.path as pth
from json import dump
from dataclasses import fields
import numpy as np
import pandas as pd

pd.options.display.max_rows = 150
pd.set_option("display.max_columns", 150)
pd.set_option("max_colwidth", 200)
pd.options.mode.chained_assignment = None

from gemseo.core.discipline import MDODiscipline
from gemseo import generate_n2_plot, create_mda


from aeromaps.core.gemseo import AeromapsModelWrapper
from aeromaps.core.models import models_simple
from aeromaps.models.parameters import Parameters
from aeromaps.utils.functions import _dict_to_df
from aeromaps.plots import available_plots
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model import (
    Fleet,
    FleetModel,
)


DATA_FOLDER = pth.join(pth.dirname(__file__), "..", "resources", "data")

# Contains all data (parameters, inputs, outputs)
EXCEL_DATA_FILE = pth.join(DATA_FOLDER, "data.xlsx")
EXCEL_DATA_INFORMATION_FILE = pth.join(DATA_FOLDER, "data_information.csv")
# Contains parameters and inputs
PARAMETERS_JSON_DATA_FILE = pth.join(DATA_FOLDER, "parameters.json")
# Contains outputs
OUTPUTS_JSON_DATA_FILE = pth.join(DATA_FOLDER, "outputs.json")


class AeromapsProcess(object):
    def __init__(
        self,
        models=models_simple,
        use_fleet_model=False,
        add_examples_aircraft_and_subcategory=True,
    ):
        self.use_fleet_model = use_fleet_model
        self.models = models

        self.parameters = Parameters()
        self.parameters.read_json(file_name=PARAMETERS_JSON_DATA_FILE)

        self.setup(add_examples_aircraft_and_subcategory)

    def setup(self, add_examples_aircraft_and_subcategory=True):
        self.disciplines = []
        self.data = {}
        self.json = {}

        self._initialize_years()

        self._initialize_disciplines(
            add_examples_aircraft_and_subcategory=add_examples_aircraft_and_subcategory
        )
        # Create GEMSEO process
        self.process = create_mda(
            "MDAChain", disciplines=self.disciplines, grammar_type=MDODiscipline.GrammarType.SIMPLE
        )
        self._initialize_data()
        self._update_variables()

    def _initialize_data(self):
        # Inputs
        self.data["float_inputs"] = {}
        # TODO: explore the possibility of using a dataframe for vector inputs
        self.data["vector_inputs"] = {}

        # Outputs
        self.data["float_outputs"] = {}
        self.data["vector_outputs"] = pd.DataFrame(index=self.data["years"]["full_years"])

    def _initialize_disciplines(self, add_examples_aircraft_and_subcategory=True):
        for name, model in self.models.items():
            # TODO: check how to avoid providing all parameters
            model.parameters = self.parameters
            model._initialize_df()
            if hasattr(model, "compute"):
                model = AeromapsModelWrapper(model=model)
                self.disciplines.append(model)
            else:
                print(model.name)
        if self.use_fleet_model:
            self.fleet = Fleet(
                add_examples_aircraft_and_subcategory=add_examples_aircraft_and_subcategory
            )
            self.fleet_model = FleetModel(fleet=self.fleet)
            self.fleet_model.parameters = self.parameters
            self.fleet_model._initialize_df()
            self.models["passenger_aircraft_efficiency_complex"].fleet_model = self.fleet_model
            self.models["passenger_aircraft_doc_non_energy_complex"].fleet_model = self.fleet_model
            self.models["nox_emission_index_complex"].fleet_model = self.fleet_model
            self.models["soot_emission_index_complex"].fleet_model = self.fleet_model
        else:
            self.fleet = None

    def _initialize_years(self):
        # Years
        self.data["years"] = {}
        self.data["years"]["full_years"] = list(
            range(self.parameters.historic_start_year, self.parameters.end_year + 1)
        )
        self.data["years"]["historic_years"] = list(
            range(
                self.parameters.historic_start_year,
                self.parameters.prospection_start_year,
            )
        )
        self.data["years"]["prospective_years"] = list(
            range(self.parameters.prospection_start_year - 1, self.parameters.end_year + 1)
        )

    def compute(self):

        if self.fleet is not None:
            self.fleet_model.compute()
            self.models["passenger_aircraft_efficiency_complex"].fleet_model = self.fleet_model
            self.models["passenger_aircraft_doc_non_energy_complex"].fleet_model = self.fleet_model
            self.models["nox_emission_index_complex"].fleet_model = self.fleet_model
            self.models["soot_emission_index_complex"].fleet_model = self.fleet_model

        input_data = self._set_inputs()

        if self.fleet is not None:
            # This is needed since fleet model is particular discipline
            input_data["dummy_fleet_model_output"] = np.random.rand(1, 1)

        self.process.execute(input_data=input_data)

        self._update_variables()

        self.write_json()

    def write_json(self, file_name=OUTPUTS_JSON_DATA_FILE):
        with open(file_name, "w", encoding="utf-8") as f:
            dump(self.json, f, ensure_ascii=False, indent=4)

    def write_excel(self, file_name=EXCEL_DATA_FILE):

        with pd.ExcelWriter(file_name) as writer:
            self.data_information_df.to_excel(writer, sheet_name="Data Information")
            self.vector_inputs_df.to_excel(writer, sheet_name="Vector Inputs")
            self.float_inputs_df.to_excel(writer, sheet_name="Float Inputs")
            self.vector_outputs_df.to_excel(writer, sheet_name="Vector Outputs")
            self.float_outputs_df.to_excel(writer, sheet_name="Float Outputs")

    def generate_n2(self):
        generate_n2_plot(self.disciplines)

    def update_parameters(self):
        for name, model in self.models.items():
            model.parameters = self.parameters

    def list_available_plots(self):
        return list(available_plots.keys())

    def list_float_inputs(self):
        return self.data["float_inputs"]

    def plot(self, name, save=False):

        if name in available_plots:
            fig = available_plots[name](self.data)
            if save:
                fig.fig.savefig(f"{name}.pdf")
        else:
            raise NameError(
                f"Plot {name} is not available. List of available plots: {list(available_plots.keys())}"
            )
        return fig

    def _set_inputs(self):

        all_inputs = {}
        self._format_input_vectors()
        # TODO: make this more efficient
        for disc in self.disciplines:
            disc.model.parameters = self.parameters
            disc.model._initialize_df()
            disc.update_defaults()
            all_inputs.update(disc.default_inputs)

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
                setattr(self.parameters, field_name, new_value)

    def _update_variables(self):

        self._update_data_from_model()

        self._update_dataframes_from_data()

        self._update_json_from_data()

    def _update_data_from_model(self):

        # Inputs
        all_inputs = self.process.get_input_data_names()

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
            except:
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

                    # self.data["vector_outputs"] = self.data["vector_outputs"].merge(disc.model.df)
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

    def _read_data_information(self):
        df = pd.read_csv(EXCEL_DATA_INFORMATION_FILE, encoding="utf-8", sep=";")

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

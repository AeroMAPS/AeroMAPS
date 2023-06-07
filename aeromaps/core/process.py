import os.path as pth
from json import dump

import numpy as np
import pandas as pd

pd.options.display.max_rows = 150
pd.set_option("display.max_columns", 150)
pd.set_option("max_colwidth", 200)
pd.options.mode.chained_assignment = None

from gemseo.core.discipline import MDODiscipline
from gemseo import generate_n2_plot, create_mda


from aeromaps.core.gemseo import AeromapsModelWrapper
from aeromaps.core.models import models_simple, year_parameters
from aeromaps.models.parameters import all_parameters
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
        self, models=models_simple, parameters=all_parameters, read_json=False, fleet=False
    ):
        self.models = models
        self.parameters = parameters
        self.disciplines = []
        self.data = {}
        self.json = {}

        # Read parameters
        if read_json:
            self.parameters = self.parameters.read_json(file_name=PARAMETERS_JSON_DATA_FILE)

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

        for name, model in self.models.items():
            model.parameters = self.parameters
            if hasattr(model, "compute"):
                model = AeromapsModelWrapper(model=model)
                self.disciplines.append(model)
            else:
                print(model.name)

        if fleet:
            self.fleet = Fleet()
            self.fleet_model = FleetModel(fleet=self.fleet, year_parameters=year_parameters)
            self.models["passenger_aircraft_efficiency_complex"].fleet_model = self.fleet_model
        else:
            self.fleet = None

        self.process = create_mda(
            "MDAChain", disciplines=self.disciplines, grammar_type=MDODiscipline.GrammarType.SIMPLE
        )

        self._update_variables()

    def compute(self):
        if self.fleet is not None:
            self.fleet_model.compute()
            self.models["passenger_aircraft_efficiency_complex"].fleet_model = self.fleet_model

        input_data = self._set_inputs()

        self.process.execute(input_data=input_data)

        self._update_variables()

        self.write_json()

    def write_data(self):
        self.write_json()
        self.write_excel()

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

    def plot(self, name):

        if name in available_plots:
            fig = available_plots[name](self.data)
        else:
            raise NameError(
                f"Plot {name} is not available. List of available plots: {list(available_plots.keys())}"
            )
        return fig

    def _set_inputs(self):

        all_inputs = {}
        # TODO: make this more efficient
        for disc in self.disciplines:
            disc.model.parameters = self.parameters
            disc.update_defaults()
            all_inputs.update(disc.default_inputs)

        return all_inputs

    def _update_variables(self):

        self._update_data_from_model()

        self._update_dataframes_from_data()

        self._update_json_from_data()

    def _update_data_from_model(self):
        # Inputs
        all_inputs = self.process.get_input_data_names()
        float_inputs = {}
        vector_inputs = {}

        for name in all_inputs:
            try:
                value = getattr(self.parameters, name)
                if isinstance(value, (float, int)):
                    float_inputs[name] = value
                else:
                    new_values = []
                    for val in value:
                        if not np.isnan(val):
                            new_values.append(val)
                    vector_inputs[name] = new_values
            except:
                pass

        self.data["float_inputs"] = float_inputs
        self.data["vector_inputs"] = vector_inputs

        # Outputs
        # TODO: can this be more efficient?
        float_outputs = {}
        vector_outputs = pd.DataFrame(index=self.data["years"]["full_years"])

        # TODO: better to use _local_data?
        for disc in self.disciplines:
            if hasattr(disc.model, "df"):
                vector_outputs = pd.concat([vector_outputs, disc.model.df], axis=1)
            float_outputs.update(disc.model.float_outputs)

        self.data["float_outputs"] = float_outputs
        self.data["vector_outputs"] = vector_outputs

    def _update_dataframes_from_data(self):

        # Float parameters
        data = {
            "Name": self.data["float_inputs"].keys(),
            "Value": self.data["float_inputs"].values(),
        }
        self.float_inputs_df = pd.DataFrame(data=data)

        # Vector parameters
        historic_years = list(
            range(
                self.parameters.historic_start_year,
                self.parameters.prospection_start_year,
            )
        )

        self.vector_inputs_df = _dict_to_df(self.data["vector_inputs"], orient="columns")
        self.vector_inputs_df.index = historic_years
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

# import os.path

# import pandas as pd
import yaml

from aeromaps.models.base import AeroMAPSModel
# from typing import Tuple


class AviationEnergyCarriers(AeroMAPSModel):
    """
    Generic model for aviation energy carriers, relying on user's description of the carriers in teh configuration file.
    """

    def __init__(
        self,
        name: str = "aviation_energy_carriers",
        configuration_file="../../../resources/data/energy_carriers_data.yaml",
        *args,
        **kwargs,
    ):
        super().__init__(
            name=name,
            model_type="custom",  # inputs/outputs are defined in __init__ rather than auto generated from compute() signature
            *args,
            **kwargs,
        )

        # Fill in explicit inputs and outputs with default values
        # self.input_names = {'input1': np.array([0.0]), 'input2': np.array([0.0])}
        # self.output_names = {'output1': np.array([0.0]), 'output2': np.array([0.0])}

        # Read configuration file that contains user-defined data.
        self.configuration_file = configuration_file
        self.configuration_data = self.read_yaml_file()  # read and process configuration file

        # Update inputs and outputs (name + default value) with user-defined data
        if "input_names" in self.configuration_data:
            for key, val in self.configuration_data["input_names"].items():
                self.input_names[key] = val
        if "output_names" in self.configuration_data:
            for key, val in self.configuration_data["output_names"].items():
                self.output_names[key] = val

    def compute(self, input_data) -> dict:
        # Get input data
        input1 = input_data["input1"]
        input2 = input_data["input2"]

        # Initialize output data
        output_data = {}

        # perform computation on explicit inputs and add to output data
        output_1 = input1 + input2
        output_2 = input1 * input2
        output_data["output_1"] = output_1
        output_data["output_1"] = output_2

        # perform computation on any input
        for i, input in input_data:
            output = input_data[input] ** 2  # any computation
            output_data[f"output_{i}"] = output  # add to output data

        # return output data
        return {name: output_data[name] for name in self.output_names}

    def read_yaml_file(self):
        """Example function to read a YAML file and returns its contents as a dictionary."""
        try:
            with open(self.configuration_file, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"Error reading YAML file: {e}")
            return {}


class AviationEnergyCarriersO(AeroMAPSModel):
    def __init__(
        self,
        name: str = "aviation_energy_carriers",
        # TODO make this flexible to handle custom file paths
        energy_carriers_data_file_path="../../../resources/data/energy_carriers_data.yaml",
        *args,
        **kwargs,
    ):
        # Call the parent class constructor
        super().__init__(name=name, *args, **kwargs)

        with open(energy_carriers_data_file_path, "r") as file:
            self.energy_carriers_data = yaml.load(file, Loader=yaml.FullLoader)

        # Initialize dictionaries for parameters and auto inputs
        # self.params_dict = dict()
        self.auto_inputs = dict()

        # Populate the dictionaries with data from energy carriers
        def flatten_params(prefix, params):
            for param_name, param_value in params.items():
                if isinstance(param_value, dict):
                    flatten_params(f"{prefix}_{param_name}", param_value)
                else:
                    full_param_name = f"{prefix}_{param_name}"
                    # self.params_dict[full_param_name] = param_value
                    self.auto_inputs[full_param_name] = type(param_value)

        for pathway, params in self.energy_carriers_data.items():
            full_name = params.get("name", pathway)
            flatten_params(full_name, params)

        # Add param dict to the self.parameters json
        # Populate the auto outputs tuple containing all the outputs of all the pathways
        # TODO can't do auto inputs without auto outputs...

        # self.auto_outputs = {"zz8zz": float}
        # print(self.auto_outputs)

    def compute(self, **kwargs) -> float:
        # print the inputs

        print(kwargs)
        # TODO: unable to mix yaml inputs with other standards AeroMAPS inputs as grammar is handeld by  auto inputs.
        zz8zz = 0.0

        # self.float_outputs["zz8zz"] = zz8zz
        # loop on pathways somehow
        self._pathway_environmental_analysis()
        self._pathway_economic_analysis()

        return zz8zz

    def _pathway_environmental_analysis(self, **kwargs):
        # Function that computes energy carriers environmental impacts
        # Ressource consumption
        # GHG emissions combining ressource emmission and other if specified

        return

    def _pathway_economic_analysis(self, **kwargs):
        # Would replace pathway_computation() in the current implementation
        # Function that computes energy carriers mfsp + invest
        # Split between complex and simple modes here ?

        # As currently, call mfsp for each year based on production needs => _compute_pathway_year_mfsp

        return

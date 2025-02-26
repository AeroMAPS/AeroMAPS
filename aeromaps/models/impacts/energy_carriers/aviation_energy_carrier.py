# import os.path

# import pandas as pd
import yaml

from aeromaps.utils.functions import read_yaml_file, flatten_dict
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
        self.input_names = {}
        self.output_names = {}

        # Read configuration file that contains user-defined data.
        self.configuration_file = configuration_file
        self.configuration_data = read_yaml_file(
            configuration_file
        )  # read and process configuration file

        if "inputs" in self.configuration_data:
            flattened_inputs = flatten_dict(self.configuration_data["inputs"])
            for key, val in flattened_inputs.items():
                self.input_names[key] = val

        if "outputs" in self.configuration_data:
            for key, val in self.configuration_data["outputs"].items():
                self.output_names[key] = val

    #

    def compute(self, input_data) -> dict:
        # Get input data
        # input1 = input_data["input1"]
        # input2 = input_data["input2"]

        # Initialize output data
        output_data = {}

        print(input_data)

        # perform computation on explicit inputs and add to output data
        output_1 = 1.0
        output_2 = 2.0
        output_data["output_1"] = output_1
        output_data["output_1"] = output_2

        # perform computation on any input

        # return output data
        return {name: output_data[name] for name in self.output_names}


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

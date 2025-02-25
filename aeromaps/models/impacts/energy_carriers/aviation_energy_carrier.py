# import os.path

# import pandas as pd
import yaml

from aeromaps.models.base import AeroMAPSModel
# from typing import Tuple


class AviationEnergyCarriers(AeroMAPSModel):
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

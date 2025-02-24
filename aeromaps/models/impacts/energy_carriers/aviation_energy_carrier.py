import pandas as pd
import yaml

from aeromaps.models.base import AeroMAPSModel
from typing import Tuple


class AviationEnergyCarriers(AeroMAPSModel):
    def __init__(
        self,
        name: str = "aviation_energy_carriers",
        energy_input_file_path=None,
        *args,
        **kwargs,
    ):
        # Call the parent class constructor
        super().__init__(name=name, *args, **kwargs)

        with open(energy_input_file_path, "r") as file:
            self.energy_carriers_data = yaml.load(file, Loader=yaml.FullLoader)

        # Initialize dictionaries for parameters and auto inputs
        self.params_dict = dict()
        self.auto_inputs = dict()

        # Populate the dictionaries with data from energy carriers
        for pathway, params in self.energy_carriers_data.items():
            for param_name, param_value in params.items():
                full_param_name = f"{pathway}_{param_name}"
                self.params_dict[full_param_name] = param_value
                self.auto_inputs[full_param_name] = type(param_value)

        # Add the auto-generated outputs to the AeroMAPSModel
        self.auto_outputs = dict()

        print(self.params_dict)

    def compute(self, **kwargs) -> Tuple[pd.Series, ...]:
        print(self.params_dict, self.auto_inputs)
        return tuple()

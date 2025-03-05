import numpy as np

from aeromaps.utils.functions import flatten_dict
from aeromaps.models.base import AeroMAPSModel


class TopDownUnitCost(AeroMAPSModel):
    """
    Top down unit cost model for energy carriers.
    It subtracts subsidies from user provided mfsp and adds taxes to it.
    """

    def __init__(
        self,
        name,
        configuration_data,
        *args,
        **kwargs,
    ):
        super().__init__(
            name=name,
            model_type="custom",
            # inputs/outputs are defined in __init__ rather than auto generated from compute() signature
            *args,
            **kwargs,
        )

        # Fill in explicit inputs and outputs with default values
        self.input_names = {}

        if "name" not in configuration_data:
            raise ValueError("The pathway configuration file should contain its name")

        self.pathway_name = configuration_data["name"]

        if "inputs" not in configuration_data:
            raise ValueError("The pathway configuration file should contain inputs")

        flattened_inputs = flatten_dict(configuration_data["inputs"], configuration_data["name"])
        for key, val in flattened_inputs.items():
            self.input_names[key] = val

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names = {self.pathway_name + "_net_mfsp": np.NaN}

    def compute(self, input_data) -> dict:
        # Get standard names for inputs
        # Mandatory inputs
        if self.pathway_name + "_mfsp" not in input_data:
            raise ValueError(
                f"Mandatory input {self.pathway_name + '_mfsp'} is missing in input_data"
            )
        pathway_mfsp = input_data[self.pathway_name + "_mfsp"]

        # Optional inputs
        # Subsidies and taxes

        pathway_subsidies = 0
        pathway_tax = 0
        if self.pathway_name + "_mfsp_subsidy" in input_data:
            pathway_subsidies = input_data[self.pathway_name + "_mfsp_subsidy"]
        if self.pathway_name + "_mfsp_tax" in input_data:
            pathway_tax = input_data[self.pathway_name + "_mfsp_tax"]

        # Actual computation

        # Calculate the unit cost
        pathway_net_mfsp = pathway_mfsp - pathway_subsidies + pathway_tax

        # Store the results in the float_outputs dictionary
        self.float_outputs[self.pathway_name + "_net_mfsp"] = pathway_net_mfsp

        return {
            self.pathway_name + "_net_mfsp": pathway_net_mfsp,
        }

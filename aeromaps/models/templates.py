"""
Template classes to implement models in AeroMAPS.
"""

import pandas as pd
from aeromaps.models.base import AeroMAPSModel
import numpy as np
from aeromaps.utils.yaml import read_yaml_file
from typing import Tuple


class CustomTemplate(AeroMAPSModel):
    """
    AeroMAPS model template to be used as a starting point for custom models.
    The compute() method of custom models does not need to explicitly define inputs,
    and outputs can be of varying size.
    However, inputs and outputs must be defined in the __init__ method using input_names and output_names dictionaries.

    Parameters
    ----------
    name : str
        Name of the model instance ('custom_template' by default).
    configuration_file : str
        Path to a configuration file (YAML) that contains user-defined input and output names and
        default values.

    Attributes
    ----------
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.
    """

    def __init__(
        self,
        name: str = "custom_template",
        configuration_file: str = None,
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
        self.input_names = {"input1": np.array([0.0]), "input2": np.array([0.0])}
        self.output_names = {"output1": np.array([0.0]), "output2": np.array([0.0])}

        # Read configuration file that contains user-defined data.
        self.configuration_file = configuration_file
        self.configuration_data = read_yaml_file(
            configuration_file
        )  # read and process configuration file

        # Update inputs and outputs (name + default value) with user-defined data
        if "input_names" in self.configuration_data:
            for key, val in self.configuration_data["input_names"].items():
                self.input_names[key] = val
        if "output_names" in self.configuration_data:
            for key, val in self.configuration_data["output_names"].items():
                self.output_names[key] = val

    def compute(self, input_data) -> dict:
        """
        Compute the outputs based on the inputs.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.

        """
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


class AutoTemplate(AeroMAPSModel):
    """
    AeroMAPS model template to be used as a starting point for auto models.
    Auto models do not require definition of inputs and outputs in __init__ method.
    Inputs and outputs are auto generated from compute() method signature.
    Therefore, the compute() method must explicitly define inputs and outputs.

    Parameters
    ----------
    name : str
        Name of the model instance ('auto_template' by default).
    """

    def __init__(
        self,
        name: str = "auto_template",
        *args,
        **kwargs,
    ):
        super().__init__(
            name=name,
            model_type="auto",  # inputs/outputs are auto generated from compute() signature
            *args,
            **kwargs,
        )

    def compute(self, input1, input2) -> Tuple[pd.Series, float]:
        """
        Compute the outputs based on the inputs.

        Parameters
        ----------
        input1
            First input variable.
        input2
            Second input variable.

        Returns
        -------
        output1
            First output variable.
        output2
            Second output variable.

        """
        output_1 = input1 * input2
        output_2 = input2**2

        return output_1, output_2

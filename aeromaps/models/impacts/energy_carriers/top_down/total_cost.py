from aeromaps.utils.functions import flatten_dict
from aeromaps.models.base import AeroMAPSModel


class TopDownTotalCost(AeroMAPSModel):
    """
    Generic model for aviation energy carriers, relying on user's description of the carriers in the configuration file.
    Actual models inherits from this class and implement the compute method.
    TODO: Create a method in process.py that instanciates a class per carrier. Or create it here?
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
        self.output_names = {}

        if "name" not in configuration_data:
            raise ValueError("The pathway configuration file should contain its name")
        if "inputs" not in configuration_data:
            raise ValueError("The pathway configuration file should contain inputs")

        flattened_inputs = flatten_dict(configuration_data["inputs"], configuration_data["name"])
        for key, val in flattened_inputs.items():
            self.input_names[key] = val

        flattened_outputs = flatten_dict(configuration_data["outputs"], configuration_data["name"])
        if "outputs" in configuration_data:
            for key, val in flattened_outputs.items():
                self.output_names[key] = val

    def compute(self, input_data) -> dict:
        return {}

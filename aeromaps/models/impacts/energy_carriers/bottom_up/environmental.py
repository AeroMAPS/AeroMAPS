from aeromaps.utils.functions import read_yaml_file, flatten_dict
from aeromaps.models.base import AeroMAPSModel


class AviationEnergyCarriers(AeroMAPSModel):
    """
    Generic model for aviation energy carriers, relying on user's description of the carriers in the configuration file.
    Actual models inherits from this class and implement the compute method.
    TODO: Create a method in process.py that instanciates a class per carrier. Or create it here?
    """

    def __init__(
        self,
        name,
        configuration_file,
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

        # To adapt to several pathways if needed
        pathway = list(self.configuration_data.keys())
        self.configuration_data = self.configuration_data[pathway[0]]

        if "name" not in self.configuration_data:
            raise ValueError("The pathway configuration file should contain its name")
        if "inputs" not in self.configuration_data:
            raise ValueError("The pathway configuration file should contain inputs")

        flattened_inputs = flatten_dict(
            self.configuration_data["inputs"], self.configuration_data["name"]
        )
        for key, val in flattened_inputs.items():
            self.input_names[key] = val

        flattened_outputs = flatten_dict(
            self.configuration_data["outputs"], self.configuration_data["name"]
        )
        if "outputs" in self.configuration_data:
            for key, val in flattened_outputs.items():
                self.output_names[key] = val

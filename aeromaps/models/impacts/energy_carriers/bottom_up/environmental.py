from aeromaps.models.base import AeroMAPSModel


class BottomUpEnvironmental(AeroMAPSModel):
    """
    Generic model for aviation energy carriers, relying on user's description of the carriers in the configuration file.
    Actual models inherits from this class and implement the compute method.
    """

    def __init__(
        self,
        name,
        configuration_data,
        resources_data,
        processs_data,
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

        self.pathway_name = configuration_data["name"]

        # Get the inputs from the configuration file: two options
        # 1. All inputs of a certain category in the yaml file
        for key, val in configuration_data.get("inputs").get("environmental", {}).items():
            # TODO initialize with zeros instead of actual val?
            self.input_names[key] = val
        for key, val in configuration_data.get("inputs").get("technical", {}).items():
            # TODO initialize with zeros instead of actual val?
            self.input_names[key] = val

    def compute(self, input_data) -> dict:
        return {}

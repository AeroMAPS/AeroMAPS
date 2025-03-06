from aeromaps.models.base import AeroMAPSModel


class TopDownTotalCost(AeroMAPSModel):
    """
    Top down total cost model for energy carriers.
    Takes outputs from unit costs and
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
        # Get the name of the pathway
        self.pathway_name = configuration_data["name"]

        # Get the inputs from the configuration file
        for key, val in configuration_data["inputs"].items():
            self.input_names[key] = val

        # Fill and initialize inputs not defined in the yaml file (either user inputs or other models outputs)
        self.input_names.update({})

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names = {}

    def compute(self, input_data) -> dict:
        # Get standard names for inputs
        # Mandatory inputs

        return {
            self.pathway_name + "_total_cost": 0.0,
        }

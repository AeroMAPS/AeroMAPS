from aeromaps.models.base import AeroMAPSModel


class EnergyResource(AeroMAPSModel):
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
        # Get the name of the resource
        self.resource_name = configuration_data["name"]

        # Get the inputs from the configuration file
        for key, val in configuration_data["specifications"].items():
            self.input_names[key] = val  # --> Initialize with blanks?

        # print("In the balnk init", self.input_names)

    def compute(self, input_data) -> dict:
        # print("In the blank compute", input_data)
        # Why ? Problem with The custom data type is that their interpolated values
        # should be transferred to gemseo variable space if they are needed by other functions.

        return {}

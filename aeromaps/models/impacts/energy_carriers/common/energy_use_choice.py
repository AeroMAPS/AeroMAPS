import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class EnergyUseChoice(AeroMAPSModel):
    """
    Central model to define volume and share consumption of each energy carrier considered
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

        # TODO is there a better way to do this?
        # Store model metadata in an attribute
        self.pathways_metadata = configuration_data

        # Get the inputs from the configuration file
        self.input_names = {}

        for key, val in configuration_data.items():
            self.pathways_keys.append(configuration_data[key]["name"])
            self.input_names.update(configuration_data[key]["usage"])

        # Fill and initialize inputs not defined in the yaml file (either user inputs or other models outputs)
        self.input_names.update(
            {
                "energy_consumption_dropin_fuel": pd.Series([0.0]),
                "energy_consumption_hydrogen": pd.Series([0.0]),
                "energy_consumption_electric": pd.Series([0.0]),
                # TODO discuss relevance of keeping that outside of the yaml: pros: simpler yaml reading. cons: logic?
                # TODO rename to something like "target share"
                "biofuel_share": pd.Series([0.0]),
                "electrofuel_share": pd.Series([0.0]),
            }
        )

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        # self.output_names = {
        #     key + "_consumption": pd.Series([0.0]) for key in configuration_data.keys()
        # }
        # self.output_names.update(
        #     {
        #         "biofuel_real_share": pd.Series([0.0]),
        #         "electrofuel_real_share": pd.Series([0.0]),
        #     }
        # )

    def compute(self, input_data) -> dict:
        # Get inputs from the configuration file

        return {}

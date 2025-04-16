import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class TopDownUnitEnvironmental(AeroMAPSModel):
    """
    Generic model for aviation energy carriers, relying on user's description of the carriers in the configuration file.
    Actual models inherits from this class and implement the compute method.
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

        # TODO find a better way to get the resource inputs ?
        self.resource_keys = [
            key[len(self.pathway_name + "_resource_specific_consumption_") :]
            for key in configuration_data["inputs"].keys()
            if key.startswith(self.pathway_name + "_resource_specific_consumption_")
        ]

        for key in self.resource_keys:
            self.input_names[key + "_load_factor"] = pd.Series([0.0])
            self.input_names[key + "_co2_emission_factor"] = pd.Series([0.0])
            self.output_names[self.pathway_name + "_co2_emission_factor_" + key] = pd.Series([0.0])

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names = {
            self.pathway_name + "_co2_emission_factor": pd.Series([0.0]),
        }

    def compute(self, input_data) -> dict:
        output_data = {}

        co2_emission_factor = input_data[
            self.pathway_name + "_co2_emission_factor_without_resource"
        ]

        for key in self.resource_keys:
            specific_consumption = input_data[
                self.pathway_name + "_resource_specific_consumption_" + key
            ]
            unit_emissions = input_data[key + "_co2_emission_factor"]

            # get resource emission per unit of energy
            co2_emission_factor_ressource = specific_consumption * unit_emissions
            output_data[self.pathway_name + "_co2_emission_factor_" + key] = (
                co2_emission_factor_ressource
            )
            co2_emission_factor = co2_emission_factor + co2_emission_factor_ressource

            # Store the total CO2 emission factor in the dataframe
        output_data[self.pathway_name + "_co2_emission_factor"] = co2_emission_factor

        self._store_outputs(output_data)

        return output_data

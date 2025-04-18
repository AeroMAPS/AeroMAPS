import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class TopDownUnitEnvironmental(AeroMAPSModel):
    """
    Generic model for aviation energy carriers, relying on user's description of the carriers in the configuration file.
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
        # TODO separate econ and environmental inputs
        for key, val in configuration_data["inputs"].items():
            self.input_names[key] = val

        self.input_names[self.pathway_name + "_energy_consumption"] = pd.Series([0.0])

        # TODO find a better way to get the resource inputs ?
        self.resource_keys = [
            key[len(self.pathway_name + "_resource_specific_consumption_") :]
            for key in configuration_data["inputs"].keys()
            if key.startswith(self.pathway_name + "_resource_specific_consumption_")
        ]

        for key in self.resource_keys:
            self.input_names[key + "_co2_emission_factor"] = pd.Series([0.0])
            self.output_names[self.pathway_name + "_co2_emission_factor_" + key] = pd.Series([0.0])
            self.output_names[self.pathway_name + "_total_consumption_" + key] = pd.Series([0.0])
            self.output_names[self.pathway_name + "_total_consumption_with_selectivity_" + key] = (
                pd.Series([0.0])
            )

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names = {
            self.pathway_name + "_co2_emission_factor": pd.Series([0.0]),
            self.pathway_name + "_total_co2_emissions": pd.Series([0.0]),
        }

    def compute(self, input_data) -> dict:
        output_data = {}

        co2_emission_factor = input_data[
            self.pathway_name + "_co2_emission_factor_without_resource"
        ]

        # Get the total energy consumption of the pathway
        energy_consumption = input_data[self.pathway_name + "_energy_consumption"]

        # Pathway selectivity
        pathway_kerosene_selectivity = input_data[self.pathway_name + "_kerosene_selectivity"]

        for key in self.resource_keys:
            specific_consumption = input_data[
                self.pathway_name + "_resource_specific_consumption_" + key
            ]
            ressource_consumption = energy_consumption * specific_consumption
            ressource_required_with_selectivity = (
                ressource_consumption / pathway_kerosene_selectivity
            )

            output_data[self.pathway_name + "_total_consumption_" + key] = ressource_consumption
            output_data[self.pathway_name + "_total_consumption_with_selectivity_" + key] = (
                ressource_required_with_selectivity
            )

            unit_emissions = input_data[key + "_co2_emission_factor"]
            # get resource emission per unit of energy
            co2_emission_factor_ressource = specific_consumption * unit_emissions
            output_data[self.pathway_name + "_co2_emission_factor_" + key] = (
                co2_emission_factor_ressource
            )
            co2_emission_factor = co2_emission_factor + co2_emission_factor_ressource

        # Store the total CO2 emission factor in the dataframe
        output_data[self.pathway_name + "_co2_emission_factor"] = co2_emission_factor

        # Calculate the total CO2 emissions
        total_co2_emissions = energy_consumption * co2_emission_factor
        output_data[self.pathway_name + "_total_co2_emissions"] = total_co2_emissions

        self._store_outputs(output_data)

        return output_data

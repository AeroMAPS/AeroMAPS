import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class TopDownCost(AeroMAPSModel):
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
        # Get the name of the pathway
        self.pathway_name = configuration_data["name"]

        # Get the inputs from the configuration file: two options
        # 1. All inputs of a certain category in the yaml file
        for key, val in configuration_data.get("inputs").get("economics").items():
            # TODO initialize with zeros instead of actual val?
            self.input_names[key] = val
        for key, val in configuration_data.get("inputs").get("technical").items():
            # TODO initialize with zeros instead of actual val?
            self.input_names[key] = val

        # 2. Set individual inputs, coming either from other models or from the yaml as well
        self.input_names.update(
            {
                "carbon_tax": pd.Series([0.0]),
                self.pathway_name + "_co2_emission_factor": pd.Series([0.0]),
                self.pathway_name + "_energy_consumption": pd.Series([0.0]),
            }
        )

        # 3. Getting resources is a bit more complex as we need to get necessary resources for the pathway
        self.resource_keys = (
            configuration_data.get("inputs")
            .get("technical")
            .get(f"{self.pathway_name}_resource_names", [])
        )
        # Adding resources-linked inputs and outputs
        for key in self.resource_keys:
            self.input_names[key + "_cost"] = pd.Series([0.0])
            self.input_names[key + "_subsidy"] = pd.Series([0.0])
            self.input_names[key + "_tax"] = pd.Series([0.0])
            self.output_names[self.pathway_name + "_unit_cost_" + key] = pd.Series([0.0])
            self.output_names[self.pathway_name + "_unit_tax_" + key] = pd.Series([0.0])
            self.output_names[self.pathway_name + "_unit_subsidy_" + key] = pd.Series([0.0])

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names.update(
            {
                self.pathway_name + "_net_mfsp_without_carbon_tax": pd.Series([0.0]),
                self.pathway_name + "_net_mfsp": pd.Series([0.0]),
                self.pathway_name + "_mfsp": pd.Series([0.0]),
                self.pathway_name + "_unit_tax": pd.Series([0.0]),
                self.pathway_name + "_unit_carbon_tax": pd.Series([0.0]),
                self.pathway_name + "_unit_subsidy": pd.Series([0.0]),
            }
        )

    def compute(self, input_data) -> dict:
        # Get inputs from the configuration file
        # Mandatory inputs
        output_data = {}

        if self.pathway_name + "_mfsp_without_resource" not in input_data:
            raise ValueError(
                f"Mandatory input {self.pathway_name + '_mfsp_without_resource'} is missing in input_data"
            )

        pathway_mfsp_without_resource = input_data[self.pathway_name + "_mfsp_without_resource"]
        pathway_mfsp = pathway_mfsp_without_resource.copy()

        pathway_unit_subsidy_without_resource = input_data[
            self.pathway_name + "_unit_subsidy_without_resource"
        ]
        pathway_unit_subsidy = pathway_unit_subsidy_without_resource.copy()

        pathway_unit_tax_without_resource = input_data[
            self.pathway_name + "_unit_tax_without_resource"
        ]
        pathway_unit_tax = pathway_unit_tax_without_resource.copy()

        for key in self.resource_keys:
            specific_consumption = input_data[
                self.pathway_name + "_resource_specific_consumption_" + key
            ]
            mfsp_ressource = input_data[key + "_cost"] * specific_consumption
            pathway_mfsp += mfsp_ressource
            output_data[self.pathway_name + "_unit_cost_" + key] = mfsp_ressource

            subsidy_ressource = input_data[key + "_subsidy"] * specific_consumption
            pathway_unit_subsidy += subsidy_ressource
            output_data[self.pathway_name + "_unit_subsidy_" + key] = subsidy_ressource

            tax_ressource = input_data[key + "_tax"] * specific_consumption
            pathway_unit_tax += tax_ressource
            output_data[self.pathway_name + "_unit_tax_" + key] = tax_ressource

        pathway_net_mfsp_without_carbon_tax = pathway_mfsp - pathway_unit_subsidy + pathway_unit_tax

        # Handle possible differential carbon_tax
        if self.pathway_name + "_carbon_tax" in input_data:
            carbon_tax = input_data[self.pathway_name + "_carbon_tax"]
        else:
            carbon_tax = input_data["carbon_tax"]

        emission_factor = input_data[self.pathway_name + "_co2_emission_factor"]
        pathway_unit_carbon_tax = carbon_tax * emission_factor
        output_data[self.pathway_name + "_unit_carbon_tax"] = pathway_unit_carbon_tax

        pathway_net_mfsp = pathway_net_mfsp_without_carbon_tax + pathway_unit_carbon_tax

        output_data.update(
            {
                self.pathway_name
                + "_net_mfsp_without_carbon_tax": pathway_net_mfsp_without_carbon_tax,
                self.pathway_name + "_net_mfsp": pathway_net_mfsp,
                self.pathway_name + "_mfsp": pathway_mfsp,
                self.pathway_name + "_unit_tax": pathway_unit_tax,
                self.pathway_name + "_unit_subsidy": pathway_unit_subsidy,
            }
        )

        # Store the results in the df
        self._store_outputs(output_data)

        return output_data

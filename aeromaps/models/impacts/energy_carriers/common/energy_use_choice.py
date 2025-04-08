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

        print(configuration_data)

        # TODO add fuel type in there

        # Get the inputs from the configuration file
        self.input_names = configuration_data
        # Fill and initialize inputs not defined in the yaml file (either user inputs or other models outputs)
        self.input_names.update(
            {
                # TODO change enrgy_consumption
            }
        )

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names = {
            self.pathway_name + "_consumption": pd.Series([0.0]),
        }

    def compute(self, input_data) -> dict:
        # Get inputs from the configuration file
        # Mandatory inputs

        if self.pathway_name + "_mfsp" not in input_data:
            raise ValueError(
                f"Mandatory input {self.pathway_name + '_mfsp'} is missing in input_data"
            )
        pathway_mfsp = input_data[self.pathway_name + "_mfsp"]

        # Optional inputs
        # Subsidies and taxes

        pathway_subsidies = 0
        pathway_tax = 0
        if self.pathway_name + "_mfsp_subsidy" in input_data:
            pathway_subsidies = input_data[self.pathway_name + "_mfsp_subsidy"]
        if self.pathway_name + "_mfsp_tax" in input_data:
            pathway_tax = input_data[self.pathway_name + "_mfsp_tax"]

        # Get other inputs

        # Handle possible differential carbon_tax
        if self.pathway_name + "_carbon_tax" in input_data:
            carbon_tax = input_data[self.pathway_name + "_carbon_tax"]
        else:
            carbon_tax = input_data["carbon_tax"]

        # Actual computation

        # Calculate the unit cost. TODO convert everything into series.
        pathway_net_mfsp_without_carbon_tax = pathway_mfsp - pathway_subsidies + pathway_tax

        # Calculate the unit cost including the carbon tax
        emission_factor = input_data[self.pathway_name + "_emission_factor"]
        pathway_net_mfsp = pathway_net_mfsp_without_carbon_tax + emission_factor * carbon_tax

        # Store the results in the df
        self.df.loc[:, self.pathway_name + "_net_mfsp_without_carbon_tax"] = (
            pathway_net_mfsp_without_carbon_tax
        )
        self.df.loc[:, self.pathway_name + "_net_mfsp"] = pathway_net_mfsp

        return {
            self.pathway_name + "_net_mfsp_without_carbon_tax": pathway_net_mfsp_without_carbon_tax,
            self.pathway_name + "_net_mfsp": pathway_net_mfsp,
        }

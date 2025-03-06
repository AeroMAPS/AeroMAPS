import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class TopDownUnitCost(AeroMAPSModel):
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

        # Get the inputs from the configuration file
        for key, val in configuration_data["inputs"].items():
            self.input_names[key] = val

        # Fill and initialize inputs not defined in the yaml file (either user inputs or other models outputs)
        self.input_names.update(
            {
                "carbon_tax": pd.Series([0.0]),
                self.pathway_name + "_emission_factor": pd.Series([0.0]),
            }
        )

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names = {
            self.pathway_name + "_net_mfsp_without_carbon_tax": pd.Series([0.0]),
            self.pathway_name + "_net_mfsp": pd.Series([0.0]),
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

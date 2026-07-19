"""
cost

=====
Module to compute offsetting mechanism costs using the top-down techno-economic model.
"""

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class OffsettingTopDownCost(AeroMAPSModel):
    """
    Top down unit cost model for offsetting mechanisms.
    It subtracts subsidies from user provided unit cost and adds taxes to it,
    then computes the total cost of the mechanism based on the carbon offset quantity.

    Parameters
    ----------
    name : str
        Name of the model instance ('f"{mechanism_name}_top_down_unit_cost"' by default).
    configuration_data : dict
        Configuration data for the offsetting mechanism from the config file.

    Attributes
    ----------
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.
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
        # Get the name of the mechanism
        self.mechanism_name = configuration_data["name"]

        # Get the inputs from the configuration file: all inputs of the economics category in the yaml file
        for key, val in (configuration_data.get("inputs").get("economics") or {}).items():
            self.input_names[key] = val

        # Set individual inputs coming from other models
        self.input_names.update(
            {
                f"{self.mechanism_name}_carbon_offset": pd.Series([0.0]),
            }
        )

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names.update(
            {
                f"{self.mechanism_name}_net_unit_cost": pd.Series([0.0]),
                f"{self.mechanism_name}_carbon_offset_cost": pd.Series([0.0]),
                f"{self.mechanism_name}_carbon_offset_subsidy": pd.Series([0.0]),
                f"{self.mechanism_name}_carbon_offset_tax": pd.Series([0.0]),
            }
        )

    def compute(self, input_data) -> dict:
        """
        Compute the top-down cost for the offsetting mechanism.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.
        """
        output_data = {}

        optional_null_series = pd.Series(
            0.0, index=range(self.historic_start_year, self.end_year + 1)
        )

        # Usage of get -> useful to set null values to optional inputs
        # Mean unit cost of the mechanism [€/tCO2]
        mechanism_unit_cost = input_data.get(
            f"{self.mechanism_name}_mean_unit_cost", optional_null_series.copy()
        )
        mechanism_unit_subsidy = input_data.get(
            f"{self.mechanism_name}_mean_unit_subsidy", optional_null_series.copy()
        )
        mechanism_unit_tax = input_data.get(
            f"{self.mechanism_name}_mean_unit_tax", optional_null_series.copy()
        )

        # Avoiding adding nans if subsidies and taxes defined for a shorter period of time than the unit cost
        mechanism_net_unit_cost = mechanism_unit_cost.add(
            -mechanism_unit_subsidy, fill_value=0
        ).add(mechanism_unit_tax, fill_value=0)

        # Carbon offset of the mechanism [MtCO2], computed by the offsettings use choice model
        mechanism_carbon_offset = input_data[f"{self.mechanism_name}_carbon_offset"].fillna(0)

        # Total cost of the mechanism [M€]: MtCO2 x €/tCO2 = M€
        mechanism_carbon_offset_cost = (
            mechanism_net_unit_cost.reindex(mechanism_carbon_offset.index).fillna(0)
            * mechanism_carbon_offset
        )
        mechanism_carbon_offset_subsidy = (
            mechanism_unit_subsidy.reindex(mechanism_carbon_offset.index).fillna(0)
            * mechanism_carbon_offset
        )
        mechanism_carbon_offset_tax = (
            mechanism_unit_tax.reindex(mechanism_carbon_offset.index).fillna(0)
            * mechanism_carbon_offset
        )

        output_data.update(
            {
                f"{self.mechanism_name}_net_unit_cost": mechanism_net_unit_cost,
                f"{self.mechanism_name}_carbon_offset_cost": mechanism_carbon_offset_cost,
                f"{self.mechanism_name}_carbon_offset_subsidy": mechanism_carbon_offset_subsidy,
                f"{self.mechanism_name}_carbon_offset_tax": mechanism_carbon_offset_tax,
            }
        )

        # Store the results in the df
        self._store_outputs(output_data)

        return output_data

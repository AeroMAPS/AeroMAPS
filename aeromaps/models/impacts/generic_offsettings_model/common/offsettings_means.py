"""
offsettings_means

=====================
Module to compute aggregate offsettings metrics (total cost, mean price, per-category costs).
"""

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class OffsettingsMeans(AeroMAPSModel):
    """
    Model to compute aggregate metrics of the offsetting mechanisms:
    total carbon offsetting cost, mean carbon offset price and per-category costs.

    Parameters
    ----------
    name : str
        Name of the model instance ('offsettings_means' by default).
    configuration_data : dict
        Configuration data for the offsettings models.
    offsettings_manager : OffsettingMechanismManager
        Manager containing all offsetting mechanisms metadata.

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
        offsettings_manager,
        *args,
        **kwargs,
    ):
        super().__init__(
            name=name,
            model_type="custom",
            *args,
            **kwargs,
        )

        # get offsettings manager to easily access mechanisms metadata (=NO VARIABLES)
        self.offsettings_manager = offsettings_manager

        self.input_names = {
            "carbon_offset": pd.Series([0.0]),
        }
        for mechanism in self.offsettings_manager.get_all():
            self.input_names[f"{mechanism.name}_carbon_offset"] = pd.Series([0.0])
            self.input_names[f"{mechanism.name}_carbon_offset_cost"] = pd.Series([0.0])

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names = {
            "carbon_offset_total_cost": pd.Series([0.0]),
            "carbon_offset_mean_price": pd.Series([0.0]),
        }
        for category in self.offsettings_manager.get_all_types("category"):
            self.output_names[f"{category}_carbon_offset_cost"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        Compute the aggregate offsettings metrics based on each mechanism carbon offset and cost.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from
            yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.
        """
        output_data = {}

        full_index = pd.RangeIndex(start=self.historic_start_year, stop=self.end_year + 1)

        # Total carbon offsetting cost [M€]
        carbon_offset_total_cost = sum(
            input_data[f"{mechanism.name}_carbon_offset_cost"].reindex(full_index).fillna(0)
            for mechanism in self.offsettings_manager.get_all()
        )
        output_data["carbon_offset_total_cost"] = carbon_offset_total_cost

        # Mean carbon offset price [€/tCO2]: M€ / MtCO2 = €/tCO2
        carbon_offset = input_data["carbon_offset"].reindex(full_index).fillna(0)
        output_data["carbon_offset_mean_price"] = carbon_offset_total_cost / carbon_offset.replace(
            0, np.nan
        )

        # Per-category costs [M€]
        for category in self.offsettings_manager.get_all_types("category"):
            output_data[f"{category}_carbon_offset_cost"] = sum(
                input_data[f"{mechanism.name}_carbon_offset_cost"].reindex(full_index).fillna(0)
                for mechanism in self.offsettings_manager.get(category=category)
            )

        # Add all output data in self.df and self.float_outputs
        self._store_outputs(output_data)

        return output_data

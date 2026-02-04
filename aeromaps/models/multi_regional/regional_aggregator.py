"""
Regional aggregation model for multi-regional AeroMAPS scenarios.

This module provides the RegionalAggregator model that aggregates outputs from
multiple regional AeroMAPS processes into global metrics. The aggregation rules
are configurable via a YAML file.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any

from aeromaps.models.base import AeroMAPSModel


class RegionalAggregator(AeroMAPSModel):
    """
    Aggregates outputs from multiple regional AeroMAPS processes into global metrics.

    This model reads aggregation configuration from a YAML structure that specifies:
    - Which metrics to aggregate
    - The aggregation operation (sum, weighted_average, etc.)
    - For weighted averages, which variable to use as weight

    The model dynamically builds its input/output grammars based on the configuration
    and the list of regions.

    Parameters
    ----------
    name
        Name of the model instance.
    regions
        List of region identifiers (e.g., ["FR", "DE", "UK"]).
    aggregation_config
        Dictionary specifying aggregation rules. Expected structure:
        {
            "sum": ["co2_emissions", "rpk", "energy_consumption", ...],
            "weighted_average": [
                {"variable": "load_factor", "weight_by": "rpk"},
                {"variable": "energy_per_rpk", "weight_by": "rpk"},
                ...
            ]
        }
    global_namespace
        Namespace prefix for global outputs (default: "overall").
    parameters
        AeroMAPS process parameters object (optional, for year indexing).

    Attributes
    ----------
    regions
        List of region identifiers.
    aggregation_config
        The aggregation configuration dictionary.
    global_namespace
        Prefix for global output variables.
    sum_variables
        List of variables to aggregate by summation.
    weighted_avg_configs
        List of weighted average configurations.

    Examples
    --------
    >>> aggregator = RegionalAggregator(
    ...     name="Aggregator",
    ...     regions=["FR", "DE"],
    ...     aggregation_config={
    ...         "sum": ["co2_emissions", "rpk"],
    ...         "weighted_average": [
    ...             {"variable": "load_factor", "weight_by": "rpk"}
    ...         ]
    ...     }
    ... )
    """

    def __init__(
        self,
        name: str,
        regions: List[str],
        aggregation_config: Dict[str, Any],
        global_namespace: str = "overall",
        parameters=None,
    ):
        super().__init__(name=name, parameters=parameters, model_type="custom")

        self.regions = regions
        self.aggregation_config = aggregation_config
        self.global_namespace = global_namespace

        # Parse aggregation config
        self.sum_variables = aggregation_config.get("sum", [])
        self.weighted_avg_configs = aggregation_config.get("weighted_average", [])

        # Build input and output names dynamically
        self._build_grammars()

    def _build_grammars(self):
        """Build input and output grammars based on aggregation configuration."""
        self.input_names = {}
        self.output_names = {}

        # For sum aggregation: need {region}:{variable} for each region
        for var in self.sum_variables:
            for region in self.regions:
                key = f"{region}:{var}"
                self.input_names[key] = pd.Series(dtype=float)

            # Output: {global_namespace}:{variable}
            output_key = f"{self.global_namespace}:{var}"
            self.output_names[output_key] = pd.Series(dtype=float)

        # For weighted average: need both the variable and the weight
        for config in self.weighted_avg_configs:
            var = config["variable"]
            weight = config["weight_by"]

            for region in self.regions:
                # Need the variable
                var_key = f"{region}:{var}"
                if var_key not in self.input_names:
                    self.input_names[var_key] = pd.Series(dtype=float)

                # Need the weight variable
                weight_key = f"{region}:{weight}"
                if weight_key not in self.input_names:
                    self.input_names[weight_key] = pd.Series(dtype=float)

            # Output: {global_namespace}:{variable}
            output_key = f"{self.global_namespace}:{var}"
            if output_key not in self.output_names:
                self.output_names[output_key] = pd.Series(dtype=float)

    def compute(self, input_data: dict) -> dict:
        """
        Aggregate regional outputs into global metrics.

        Parameters
        ----------
        input_data
            Dictionary containing namespaced regional outputs.
            E.g., {"FR:co2_emissions": <series>, "DE:co2_emissions": <series>, ...}

        Returns
        -------
        dict
            Dictionary containing aggregated global outputs.
            E.g., {"overall:co2_emissions": <series>, ...}
        """
        output_data = {}

        # Sum aggregation
        for var in self.sum_variables:
            total = self._aggregate_sum(input_data, var)
            output_key = f"{self.global_namespace}:{var}"
            output_data[output_key] = total

        # Weighted average aggregation
        for config in self.weighted_avg_configs:
            var = config["variable"]
            weight = config["weight_by"]
            weighted_avg = self._aggregate_weighted_average(input_data, var, weight)
            output_key = f"{self.global_namespace}:{var}"
            output_data[output_key] = weighted_avg

        # Store outputs for AeroMAPS compatibility
        self._store_outputs(output_data)

        return output_data

    def _aggregate_sum(self, input_data: dict, variable: str) -> pd.Series:
        """
        Aggregate a variable across regions by summation.

        Parameters
        ----------
        input_data
            The input data dictionary.
        variable
            The variable name to aggregate.

        Returns
        -------
        pd.Series
            The summed values across all regions.
        """
        total = None

        for region in self.regions:
            key = f"{region}:{variable}"
            if key in input_data:
                value = input_data[key]
                if total is None:
                    total = value.copy() if hasattr(value, "copy") else value
                else:
                    total = total + value

        return total if total is not None else pd.Series(dtype=float)

    def _aggregate_weighted_average(
        self, input_data: dict, variable: str, weight_variable: str
    ) -> pd.Series:
        """
        Aggregate a variable across regions by weighted average.

        Parameters
        ----------
        input_data
            The input data dictionary.
        variable
            The variable name to aggregate.
        weight_variable
            The variable to use as weights.

        Returns
        -------
        pd.Series
            The weighted average across all regions.
        """
        weighted_sum = None
        total_weight = None

        for region in self.regions:
            var_key = f"{region}:{variable}"
            weight_key = f"{region}:{weight_variable}"

            if var_key in input_data and weight_key in input_data:
                value = input_data[var_key]
                weight = input_data[weight_key]

                weighted_value = value * weight

                if weighted_sum is None:
                    weighted_sum = weighted_value.copy() if hasattr(weighted_value, "copy") else weighted_value
                    total_weight = weight.copy() if hasattr(weight, "copy") else weight
                else:
                    weighted_sum = weighted_sum + weighted_value
                    total_weight = total_weight + weight

        if weighted_sum is not None and total_weight is not None:
            # Avoid division by zero
            result = weighted_sum / total_weight.replace(0, np.nan)
            return result
        else:
            return pd.Series(dtype=float)

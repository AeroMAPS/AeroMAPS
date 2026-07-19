"""
offsettings_use_choice

=====================
Central module with a model to handle offsetting mechanisms interaction.
"""

import warnings

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class OffsettingsUseChoice(AeroMAPSModel):
    """
    Central model to define the quantity of carbon offset by each offsetting mechanism considered
    depending on the usage specified (share or quantity) and priorities.
    The default mechanism fulfills the carbon offsetting demand not covered by the other mechanisms.

    Parameters
    ----------
    name : str
        Name of the model instance ('offsettings_use_choice' by default).
    configuration_data : dict
        Configuration data for the offsettings use choice model.
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
        # (Caution: use only non coupling attributes as mechanisms metadata is not a coupling variable)
        # Coupling variables should go in inputs_names
        self.offsettings_manager = offsettings_manager

        # Actual model variables goes in inputs_names
        self.input_names = {}

        for mechanism in self.offsettings_manager.get_all():
            name = mechanism.name
            if mechanism.default:
                # default mechanism does not use any usage definition even if defined
                pass
            elif mechanism.usage_type == "quantity":
                self.input_names.update(
                    {
                        f"{name}_usage_quantity": pd.Series([0.0]),
                    }
                )
            elif mechanism.usage_type == "share":
                self.input_names.update(
                    {
                        f"{name}_usage_share": pd.Series([0.0]),
                    }
                )

        # Fill and initialize inputs not defined in the yaml file (either user inputs or other models outputs)
        self.input_names.update(
            {
                "carbon_offset": pd.Series([0.0]),
            }
        )

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names = {}
        for mechanism in self.offsettings_manager.get_all():
            self.output_names[f"{mechanism.name}_carbon_offset"] = pd.Series([0.0])
            self.output_names[f"{mechanism.name}_share_carbon_offset"] = pd.Series([0.0])
            self.output_names[f"{mechanism.name}_cumulative_carbon_offset"] = pd.Series([0.0])

        # Fill in expected outputs for the different offsetting categories (e.g. carbon dioxide removal)
        for category in self.offsettings_manager.get_all_types("category"):
            self.output_names[f"{category}_carbon_offset"] = pd.Series([0.0])
            self.output_names[f"{category}_share_carbon_offset"] = pd.Series([0.0])
            self.output_names[f"{category}_cumulative_carbon_offset"] = pd.Series([0.0])
            for mechanism in self.offsettings_manager.get(category=category):
                self.output_names[f"{mechanism.name}_share_{category}"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        Compute the carbon offset of each offsetting mechanism based on the defined usages and priority rules.

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

        # Total carbon offsetting demand, computed upstream (e.g. level and residual carbon offset models)
        carbon_offset = input_data["carbon_offset"].reindex(full_index).fillna(0)
        remaining_carbon_offset = carbon_offset.copy()

        # No need to define mechanisms if there is no carbon offsetting demand
        if carbon_offset.notna().any() and carbon_offset.sum() != 0:
            # Default mechanism should be defined
            default_mechanism = self.offsettings_manager.get(default=True)
            if not default_mechanism:
                raise ValueError(
                    "It is mandatory to define a default offsetting mechanism in the offsettings_data.yaml"
                )
            elif len(default_mechanism) > 1:
                raise ValueError(
                    "There should be only one default offsetting mechanism defined in the offsettings_data.yaml"
                )
            else:
                # First case: quantity-defined mechanisms
                quantity_mechanisms = self.offsettings_manager.get(
                    usage_type="quantity", default=False
                )
                if quantity_mechanisms:
                    total_quantity = (
                        sum(
                            input_data[f"{mechanism.name}_usage_quantity"]
                            for mechanism in quantity_mechanisms
                        )
                        .reindex(full_index)
                        .fillna(0)
                    )
                    if (total_quantity <= carbon_offset).all():
                        # If the sum of quantities is less than or equal to the total, keep the quantities as output
                        for mechanism in quantity_mechanisms:
                            mechanism_offset = input_data[f"{mechanism.name}_usage_quantity"]
                            output_data[f"{mechanism.name}_carbon_offset"] = mechanism_offset
                            remaining_carbon_offset -= mechanism_offset.reindex(full_index).fillna(
                                0
                            )
                    else:
                        # If the sum exceeds the total, decrease them homogeneously
                        scaling_factor = pd.Series(
                            np.where(
                                total_quantity > remaining_carbon_offset,
                                remaining_carbon_offset / total_quantity,
                                1,
                            ),
                            index=total_quantity.index,
                        )
                        for mechanism in quantity_mechanisms:
                            original = input_data[f"{mechanism.name}_usage_quantity"].fillna(0)
                            mechanism_offset = (
                                original * scaling_factor.loc[original.index]
                            ).fillna(0)
                            output_data[f"{mechanism.name}_carbon_offset"] = mechanism_offset
                            remaining_carbon_offset -= mechanism_offset.reindex(full_index).fillna(
                                0
                            )

                            modified_years = mechanism_offset.loc[original.index][
                                mechanism_offset.loc[original.index] != original.loc[original.index]
                            ]

                            if not modified_years.empty:
                                msg = (
                                    "\nThe sum of the quantity-defined offsetting mechanisms exceeds the total carbon offsetting demand.\n"
                                    f"→ Mechanism '{mechanism.name}' carbon offset was adjusted in the following years:\n"
                                )
                                for year in modified_years.index:
                                    msg += f"   - {year}: {mechanism_offset[year]:.2e} MtCO2 instead of {original[year]:.2e} MtCO2\n"

                                warnings.warn(msg)

                # Second case: share-defined mechanisms
                share_mechanisms = self.offsettings_manager.get(usage_type="share", default=False)
                if share_mechanisms:
                    total_share_quantity = (
                        sum(
                            input_data[f"{mechanism.name}_usage_share"] / 100 * carbon_offset
                            for mechanism in share_mechanisms
                        )
                        .reindex(full_index)
                        .fillna(0)
                    )
                    if (total_share_quantity <= remaining_carbon_offset).all():
                        # If the sum of quantities is less than or equal to the total, keep the quantities as output
                        for mechanism in share_mechanisms:
                            mechanism_offset = (
                                input_data[f"{mechanism.name}_usage_share"] / 100 * carbon_offset
                            )
                            output_data[f"{mechanism.name}_carbon_offset"] = mechanism_offset
                            remaining_carbon_offset -= mechanism_offset.reindex(full_index).fillna(
                                0
                            )
                    else:
                        # If the sum exceeds the total, decrease them homogeneously
                        scaling_factor = pd.Series(
                            np.where(
                                total_share_quantity > remaining_carbon_offset,
                                remaining_carbon_offset / total_share_quantity,
                                1,
                            ),
                            index=total_share_quantity.index,
                        )
                        for mechanism in share_mechanisms:
                            original_share = input_data[f"{mechanism.name}_usage_share"].fillna(0)
                            mechanism_offset = (
                                original_share / 100 * carbon_offset * scaling_factor
                            ).fillna(0)
                            output_data[f"{mechanism.name}_carbon_offset"] = mechanism_offset
                            remaining_carbon_offset -= mechanism_offset.reindex(full_index).fillna(
                                0
                            )

                            modified_years = mechanism_offset.loc[original_share.index][
                                mechanism_offset.loc[original_share.index]
                                != (original_share / 100 * carbon_offset.loc[original_share.index])
                            ]

                            if not modified_years.empty:
                                msg = (
                                    "\nThe sum of the share-defined offsetting mechanisms exceeds the total carbon offsetting demand (minus quantity-based mechanisms).\n"
                                    f"→ Mechanism '{mechanism.name}' share was adjusted in the following years:\n"
                                )
                                for year in modified_years.index:
                                    msg += f"   - {year}: {(mechanism_offset[year] * 100 / carbon_offset[year]):.1f} % instead of {(original_share[year]):.1f} %\n"

                                warnings.warn(msg)

                # Third case: default mechanism completes to fill the remaining carbon offsetting demand
                mechanism = default_mechanism[0]
                output_data[f"{mechanism.name}_carbon_offset"] = remaining_carbon_offset.copy()
                remaining_carbon_offset -= remaining_carbon_offset

        else:
            # If there is no carbon offsetting demand, set all carbon offsets to 0
            for mechanism in self.offsettings_manager.get_all():
                output_data[f"{mechanism.name}_carbon_offset"] = pd.Series(0.0, index=full_index)

        # Compute metrics derived from each mechanism carbon offset
        # Share of each mechanism in the total carbon offset
        for mechanism in self.offsettings_manager.get_all():
            mechanism_offset = (
                output_data[f"{mechanism.name}_carbon_offset"].reindex(full_index).fillna(0)
            )
            output_data[f"{mechanism.name}_carbon_offset"] = mechanism_offset
            output_data[f"{mechanism.name}_share_carbon_offset"] = (
                mechanism_offset / carbon_offset.replace(0, np.nan) * 100
            )
            # Cumulative carbon offset of each mechanism [GtCO2]
            cumulative = mechanism_offset.copy()
            cumulative.loc[: self.prospection_start_year - 1] = 0.0
            output_data[f"{mechanism.name}_cumulative_carbon_offset"] = cumulative.cumsum() / 1000

        # Aggregates for each offsetting category (e.g. carbon dioxide removal vs emissions avoidance)
        for category in self.offsettings_manager.get_all_types("category"):
            category_carbon_offset = sum(
                output_data[f"{mechanism.name}_carbon_offset"]
                for mechanism in self.offsettings_manager.get(category=category)
            )
            output_data[f"{category}_carbon_offset"] = category_carbon_offset
            output_data[f"{category}_share_carbon_offset"] = (
                category_carbon_offset / carbon_offset.replace(0, np.nan) * 100
            )
            category_cumulative = category_carbon_offset.copy()
            category_cumulative.loc[: self.prospection_start_year - 1] = 0.0
            output_data[f"{category}_cumulative_carbon_offset"] = (
                category_cumulative.cumsum() / 1000
            )
            for mechanism in self.offsettings_manager.get(category=category):
                output_data[f"{mechanism.name}_share_{category}"] = (
                    output_data[f"{mechanism.name}_carbon_offset"]
                    / category_carbon_offset.replace(0, np.nan)
                    * 100
                )

        # Add all output data in self.df and self.float_outputs
        self._store_outputs(output_data)

        return output_data

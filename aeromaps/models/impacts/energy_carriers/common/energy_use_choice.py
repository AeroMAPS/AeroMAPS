import warnings
from dataclasses import dataclass

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


@dataclass
class LocalEnergyCarrier:
    name: str
    aircraft_type: str
    default: bool = False
    mandate_type: str = None


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

        # Store model metadata in an dataclass
        # (Caution: use only non coupling attributes as pathways metadata is not a coupling variable)
        # Coupling variables should go in inputs_names

        self.pathways_metadata = {
            key: LocalEnergyCarrier(
                name=key,
                aircraft_type=val.get("aircraft_type"),
                default=val.get("default"),
                mandate_type=val.get("mandate", {}).get(f"{key}_mandate_type"),
            )
            for key, val in configuration_data.items()
        }

        # Get the inputs from the configuration file
        self.input_names = {}

        for key, val in self.pathways_metadata.items():
            if val.mandate_type == "volume":
                self.input_names.update(
                    {
                        f"{key}_mandate_volume": configuration_data[key]["mandate"].get(
                            f"{key}_mandate_volume"
                        )
                    }
                )
            elif val.mandate_type == "share":
                self.input_names.update(
                    {
                        f"{key}_mandate_volume": configuration_data[key]["mandate"].get(
                            f"{key}_mandate_share"
                        )
                    }
                )
            else:
                pass  # default patwhay has no mandate

        # Fill and initialize inputs not defined in the yaml file (either user inputs or other models outputs)
        self.input_names.update(
            {
                "energy_consumption_dropin_fuel": pd.Series([0.0]),
                "energy_consumption_hydrogen": pd.Series([0.0]),
                "energy_consumption_electric": pd.Series([0.0]),
                # TODO discuss relevance of keeping that outside of the yaml: pros: simpler yaml reading. cons: logic?
                # TODO rename to something like "target share"
                # "biofuel_share": pd.Series([0.0]),
                # "electrofuel_share": pd.Series([0.0]),
            }
        )

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names = {
            key + "_energy_consumption": pd.Series([0.0]) for key in self.pathways_metadata.keys()
        }

        self.output_names.update(
            {
                "biofuel_share": pd.Series([0.0]),
                # "electrofuel_share": pd.Series([0.0]),
            }
        )
        print(self.input_names)

    def compute(self, input_data) -> dict:
        # Get inputs from the configuration file
        output_data = {}
        ###### DROP-IN FUELS ######
        # Separate pathways into three categories
        dropin_default_pathway = None
        dropin_quantity_pathways = []
        dropin_blending_mandate_pathways = []

        ###### HYDROGEN ######
        # Separate pathways into three categories
        hydrogen_default_pathway = None
        hydrogen_quantity_pathways = []
        hydrogen_blending_mandate_pathways = []

        ###### ELECTRIC ######
        # Separate pathways into three categories
        electric_default_pathway = None
        electric_quantity_pathways = []
        electric_blending_mandate_pathways = []

        # populate the various aircraft energy types
        for pathway, metadata in self.pathways_metadata.items():
            if metadata["aircraft_type"] == "dropin":
                # First case: get the default dropin pathway
                if metadata.get("default", True):
                    dropin_default_pathway = pathway
                elif f"{pathway}_energy_quantity" in metadata.get("usage", {}):
                    dropin_quantity_pathways.append(pathway)
                elif f"{pathway}_energy_blending_mandate" in metadata.get("usage", {}):
                    dropin_blending_mandate_pathways.append(pathway)
            elif metadata["aircraft_type"] == "hydrogen":
                # First case: get the default hydrogen pathway
                if metadata.get("default", False):
                    hydrogen_default_pathway = pathway
                elif f"{pathway}_energy_quantity" in metadata.get("usage", {}):
                    hydrogen_quantity_pathways.append(pathway)
                elif f"{pathway}_energy_blending_mandate" in metadata.get("usage", {}):
                    hydrogen_blending_mandate_pathways.append(pathway)
            elif metadata["aircraft_type"] == "electric":
                # First case: get the default electric pathway
                if metadata.get("default", False):
                    electric_default_pathway = pathway
                elif f"{pathway}_energy_quantity" in metadata.get("usage", {}):
                    electric_quantity_pathways.append(pathway)
                elif f"{pathway}_energy_blending_mandate" in metadata.get("usage", {}):
                    electric_blending_mandate_pathways.append(pathway)

        # Now for each energy type, compute an energy quantity to be produced based on priority order.
        # DROP-IN FUELS

        # Get the consumption of drop-in fuel
        energy_consumption_dropin_fuel = input_data["energy_consumption_dropin_fuel"]
        remaining_energy_consumption_dropin_fuel = energy_consumption_dropin_fuel.copy()

        if (
            energy_consumption_dropin_fuel.notna().any()
            and energy_consumption_dropin_fuel.sum() != 0
        ):
            # Default pathway should be defined
            if dropin_default_pathway is None:
                raise ValueError(
                    "It is mandatory to define a default drop-in fuel pathway defined in the energy_carriers_data.yaml"
                )
            else:
                # First case: quantity-defined pathways
                total_quantity = sum(
                    input_data[f"{pathway}_energy_quantity"] for pathway in dropin_quantity_pathways
                )
                if (total_quantity.fillna(0) <= energy_consumption_dropin_fuel.fillna(0)).all():
                    # If the sum of quantities is less than or equal to the total, keep the quantities as output
                    for pathway in dropin_quantity_pathways:
                        pathway_consumption = input_data[f"{pathway}_energy_quantity"]
                        output_data[f"{pathway}_energy_consumption"] = pathway_consumption
                        remaining_energy_consumption_dropin_fuel -= pathway_consumption
                else:
                    # If the sum exceeds the total, decrease them homogeneously
                    scaling_factor = energy_consumption_dropin_fuel / total_quantity
                    # print(scaling_factor)
                    warnings.warn(
                        "The sum of the quantity-defined drop-in fuel "
                        "pathways exceeds the total drop-in energy consumption."
                    )
                    for pathway in dropin_quantity_pathways:
                        pathway_consumption = (
                            input_data[f"{pathway}_energy_quantity"] * scaling_factor
                        )
                        output_data[f"{pathway}_energy_consumption"] = pathway_consumption
                        remaining_energy_consumption_dropin_fuel -= pathway_consumption
                        warnings.warn(
                            f"Pathway{pathway} energy consumption is set to {pathway_consumption} "
                            f"instead of {input_data[f'{pathway}_energy_quantity']}"
                        )

                # Second case : blending mandate pathways
                total_share_quantity = sum(
                    input_data[f"{pathway}_energy_blending_mandate"]
                    / 100
                    * energy_consumption_dropin_fuel
                    for pathway in dropin_blending_mandate_pathways
                )
                if (
                    total_share_quantity.fillna(0)
                    <= remaining_energy_consumption_dropin_fuel.fillna(0)
                ).all():
                    # If the sum of quantities is less than or equal to the total, keep the quantities as output
                    for pathway in dropin_blending_mandate_pathways:
                        pathway_consumption = (
                            input_data[f"{pathway}_energy_blending_mandate"]
                            / 100
                            * energy_consumption_dropin_fuel
                        )
                        output_data[f"{pathway}_energy_consumption"] = pathway_consumption
                        remaining_energy_consumption_dropin_fuel -= pathway_consumption
                else:
                    # If the sum exceeds the total, decrease them homogeneously
                    scaling_factor = remaining_energy_consumption_dropin_fuel / total_share_quantity
                    warnings.warn(
                        "The sum of the share-defined drop-in fuel pathways exceeds "
                        "the total drop-in energy consumption (minus quantity based pathways)."
                    )
                    for pathway in dropin_blending_mandate_pathways:
                        pathway_consumption = (
                            input_data[f"{pathway}_energy_blending_mandate"]
                            / 100
                            * energy_consumption_dropin_fuel
                            * scaling_factor
                        )
                        output_data[f"{pathway}_energy_consumption"] = pathway_consumption
                        remaining_energy_consumption_dropin_fuel -= pathway_consumption
                        warnings.warn(
                            f"Pathway{pathway} energy consumption is set to {pathway_consumption/scaling_factor/100} "
                            f"instead of {input_data[f'{pathway}_energy_quantity']}"
                        )

                # Third case: default pathway completes to fill the remaining energy consumption
                if dropin_default_pathway is not None:
                    output_data[f"{dropin_default_pathway}_energy_consumption"] = (
                        remaining_energy_consumption_dropin_fuel.copy()
                    )
                    remaining_energy_consumption_dropin_fuel -= (
                        remaining_energy_consumption_dropin_fuel
                    )

                # TODO HYDROGEN AND ELECTRICITY
                # TODO COMPUTE REFUELEU SHARES

                biofuel_share = ()

        print(output_data)

        return output_data

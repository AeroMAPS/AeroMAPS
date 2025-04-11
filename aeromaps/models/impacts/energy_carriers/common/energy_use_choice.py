import warnings
from dataclasses import dataclass
from typing import List

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


@dataclass
class LocalEnergyCarrier:
    name: str = None
    aircraft_type: str = None
    default: bool = False
    mandate_type: str = None
    energy_origin: str = None


class LocalEnergyCarrierManager:
    def __init__(self, carriers: List[LocalEnergyCarrier] = None):
        self.carriers = carriers if carriers is not None else []

    def add(self, carrier: LocalEnergyCarrier):
        self.carriers.append(carrier)

    def get(self, **criteria) -> List[LocalEnergyCarrier]:
        return [
            c
            for c in self.carriers
            if all(getattr(c, attr, None) == val for attr, val in criteria.items())
        ]

    def get_all(self):
        return self.carriers


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

        self.pathways_manager = LocalEnergyCarrierManager(
            [
                LocalEnergyCarrier(
                    name=key,
                    aircraft_type=val.get("aircraft_type"),
                    default=val.get("default"),
                    mandate_type=val.get("mandate", {}).get(f"{key}_mandate_type"),
                    energy_origin=val.get("energy_origin"),
                )
                for key, val in configuration_data.items()
            ]
        )

        # Actual model variables goes in inputs_names
        self.input_names = {}

        for pathway in self.pathways_manager.get_all():
            name = pathway.name
            if pathway.default:
                # default pathway does not use any mandate even if defined
                pass
            if pathway.mandate_type == "quantity":
                self.input_names.update(
                    {
                        f"{name}_mandate_quantity": configuration_data[name]["mandate"].get(
                            f"{name}_mandate_quantity"
                        )
                    }
                )
            elif pathway.mandate_type == "share":
                self.input_names.update(
                    {
                        f"{name}_mandate_share": configuration_data[name]["mandate"].get(
                            f"{name}_mandate_share"
                        )
                    }
                )

        # Fill and initialize inputs not defined in the yaml file (either user inputs or other models outputs)
        self.input_names.update(
            {
                "energy_consumption_dropin_fuel": pd.Series([0.0]),
                "energy_consumption_hydrogen": pd.Series([0.0]),
                "energy_consumption_electric": pd.Series([0.0]),
                # TODO discuss idea of having a target share to force refuel-eu like mandate
                # "biofuel_share": pd.Series([0.0]),
                # "electrofuel_share": pd.Series([0.0]),
            }
        )

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names = {
            pathway.name + "_energy_consumption": pd.Series([0.0])
            for pathway in self.pathways_manager.get_all()
        }

        self.output_names.update(
            {
                "biofuel_share": pd.Series([0.0]),
                "electrofuel_share": pd.Series([0.0]),
                "kerosene_share": pd.Series([0.0]),
            }
        )

    def compute(self, input_data) -> dict:
        # Get inputs from the configuration file
        output_data = {}
        # For each energy type, compute an energy quantity to be produced based on priority order.

        ###### DROP-IN FUELS ######

        # Get the consumption of drop-in fuel
        energy_consumption_dropin_fuel = input_data["energy_consumption_dropin_fuel"]
        remaining_energy_consumption_dropin_fuel = energy_consumption_dropin_fuel.copy()

        # No need to define pathways if there is no drop-in fuel consumption
        if (
            energy_consumption_dropin_fuel.notna().any()
            and energy_consumption_dropin_fuel.sum() != 0
        ):
            # Default pathway should be defined
            dropin_default_pathway = self.pathways_manager.get(aircraft_type="dropin", default=True)
            if not dropin_default_pathway:
                raise ValueError(
                    "It is mandatory to define a default drop-in fuel pathway defined in the energy_carriers_data.yaml"
                )
            elif len(dropin_default_pathway) > 1:
                raise ValueError(
                    "There should be only one default drop-in fuel pathway defined in the energy_carriers_data.yaml"
                )
            else:
                # First case: quantity-defined pathways
                dropin_quantity_pathways = self.pathways_manager.get(
                    aircraft_type="dropin", mandate_type="quantity"
                )
                total_quantity = sum(
                    input_data[f"{pathway.name}_mandate_quantity"]
                    for pathway in dropin_quantity_pathways
                )
                if (total_quantity.fillna(0) <= energy_consumption_dropin_fuel.fillna(0)).all():
                    # If the sum of quantities is less than or equal to the total, keep the quantities as output
                    for pathway in dropin_quantity_pathways:
                        pathway_consumption = input_data[f"{pathway.name}_mandate_quantity"]
                        output_data[f"{pathway.name}_energy_consumption"] = pathway_consumption
                        remaining_energy_consumption_dropin_fuel -= pathway_consumption.fillna(0)
                else:
                    # If the sum exceeds the total, decrease them homogeneously
                    scaling_factor = energy_consumption_dropin_fuel / total_quantity
                    warnings.warn(
                        "The sum of the quantity-defined drop-in fuel "
                        "pathways exceeds the total drop-in energy consumption."
                    )
                    for pathway in dropin_quantity_pathways:
                        pathway_consumption = (
                            input_data[f"{pathway.name}_mandate_quantity"] * scaling_factor
                        )
                        output_data[f"{pathway.name}_energy_consumption"] = pathway_consumption
                        remaining_energy_consumption_dropin_fuel -= pathway_consumption.fillna(0)
                        warnings.warn(
                            f"Pathway{pathway.name} energy consumption is set to {pathway_consumption} "
                            f"instead of {input_data[f'{pathway.name}_mandate_quantity']}"
                        )

                # Second case : blending mandate pathways
                dropin_share_pathways = self.pathways_manager.get(
                    aircraft_type="dropin", mandate_type="share"
                )
                total_share_quantity = sum(
                    input_data[f"{pathway.name}_mandate_share"]
                    / 100
                    * energy_consumption_dropin_fuel
                    for pathway in dropin_share_pathways
                )
                if (
                    total_share_quantity.fillna(0)
                    <= remaining_energy_consumption_dropin_fuel.fillna(0)
                ).all():
                    # If the sum of quantities is less than or equal to the total, keep the quantities as output
                    for pathway in dropin_share_pathways:
                        pathway_consumption = (
                            input_data[f"{pathway.name}_mandate_share"]
                            / 100
                            * energy_consumption_dropin_fuel
                        )
                        output_data[f"{pathway.name}_energy_consumption"] = pathway_consumption
                        remaining_energy_consumption_dropin_fuel -= pathway_consumption.fillna(0)
                else:
                    # If the sum exceeds the total, decrease them homogeneously
                    scaling_factor = remaining_energy_consumption_dropin_fuel / total_share_quantity
                    warnings.warn(
                        "The sum of the share-defined drop-in fuel pathways exceeds "
                        "the total drop-in energy consumption (minus quantity based pathways)."
                    )
                    for pathway in dropin_share_pathways:
                        pathway_consumption = (
                            input_data[f"{pathway.name}_mandate_share"]
                            / 100
                            * energy_consumption_dropin_fuel
                            * scaling_factor
                        )
                        output_data[f"{pathway.name}_energy_consumption"] = pathway_consumption
                        remaining_energy_consumption_dropin_fuel -= pathway_consumption.fillna(0)
                        warnings.warn(
                            f"Pathway{pathway.name} energy consumption is set to {pathway_consumption/scaling_factor/100} "
                            f"instead of {input_data[f'{pathway.name}_mandate_share']}"
                        )

                # Third case: default pathway completes to fill the remaining energy consumption
                pathway = dropin_default_pathway[0]
                output_data[f"{pathway.name}_energy_consumption"] = (
                    remaining_energy_consumption_dropin_fuel.copy()
                )
                remaining_energy_consumption_dropin_fuel -= remaining_energy_consumption_dropin_fuel

                # TODO Rename biofuel_share to dropin_biofuel_share for more clarity?
                dropin_biofuel_consumption = sum(
                    output_data[f"{pathway.name}_energy_consumption"]
                    for pathway in self.pathways_manager.get(
                        aircraft_type="dropin", energy_origin="biomass"
                    )
                )
                biofuel_share = dropin_biofuel_consumption / energy_consumption_dropin_fuel * 100
                output_data["biofuel_share"] = biofuel_share.fillna(0)

                dropin_electrofuel_consumption = sum(
                    output_data[f"{pathway.name}_energy_consumption"]
                    for pathway in self.pathways_manager.get(
                        aircraft_type="dropin", energy_origin="electrofuel"
                    )
                )
                electrofuel_share = (
                    dropin_electrofuel_consumption / energy_consumption_dropin_fuel * 100
                )
                output_data["electrofuel_share"] = electrofuel_share.fillna(0)

                dropin_kerosene_consumption = sum(
                    output_data[f"{pathway.name}_energy_consumption"]
                    for pathway in self.pathways_manager.get(
                        aircraft_type="dropin", energy_origin="fossil"
                    )
                )
                kerosene_share = dropin_kerosene_consumption / energy_consumption_dropin_fuel * 100
                output_data["kerosene_share"] = kerosene_share.fillna(0)

            # TODO HYDROGEN AND ELECTRICITY

        return output_data

import warnings

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class EnergyUseChoice(AeroMAPSModel):
    """
    Central model to define volume consumed of each energy carrier considered depending on the mandate specified and priorities.
    """

    def __init__(
        self,
        name,
        configuration_data,
        pathways_manager,
        *args,
        **kwargs,
    ):
        super().__init__(
            name=name,
            model_type="custom",
            *args,
            **kwargs,
        )

        # get pathways manager to easily access pathways metadata (=NO VARIABLES)
        # (Caution: use only non coupling attributes as pathways metadata is not a coupling variable)
        # Coupling variables should go in inputs_names
        self.pathways_manager = pathways_manager

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
                # not handling other energy carriers for now
            }
        )

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names = {}
        for pathway in self.pathways_manager.get_all():
            self.output_names[f"{pathway.name}_energy_consumption"] = pd.Series([0.0])
            self.output_names[f"{pathway.name}_share_total_energy"] = pd.Series([0.0])

        # Fill in expected outputs for different aircraft types
        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                self.output_names[f"{pathway.name}_share_{aircraft_type}"] = pd.Series([0.0])

        for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
            self.output_names[f"{energy_origin}_share_total_energy"] = pd.Series([0.0])

        self.output_names.update(
            {
                "biofuel_share": pd.Series([0.0]),
                "electrofuel_share": pd.Series([0.0]),
                "kerosene_share": pd.Series([0.0]),
            }
        )

    def compute(self, input_data) -> dict:
        """
        Compute the energy consumption of each energy carrier based on the defined pathways and mandates.
        """
        # Get inputs from the configuration file
        output_data = {}
        # For each energy type, compute an energy quantity to be produced based on priority order.

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            # Get the energy consumption for the given aircraft type
            try:
                energy_consumption = input_data[f"energy_consumption_{aircraft_type}"]
            except KeyError:
                raise KeyError(
                    f"Aircraft type <{aircraft_type}> specified in energy_carriers_data.yaml not supported by AeroMAPS aircraft models."
                )
            remaining_energy_consumption = energy_consumption.copy()

            # No need to define pathways if there is no fuel consumption
            if energy_consumption.notna().any() and energy_consumption.sum() != 0:
                # Default pathway should be defined
                type_default_pathway = self.pathways_manager.get(
                    aircraft_type=aircraft_type, default=True
                )
                if not type_default_pathway:
                    raise ValueError(
                        f"It is mandatory to define a default {aircraft_type} fuel pathway defined in the energy_carriers_data.yaml"
                    )
                elif len(type_default_pathway) > 1:
                    raise ValueError(
                        f"There should be only one default {aircraft_type} fuel pathway defined in the energy_carriers_data.yaml"
                    )
                else:
                    # First case: quantity-defined pathways
                    type_quantity_pathways = self.pathways_manager.get(
                        aircraft_type=aircraft_type, mandate_type="quantity"
                    )
                    total_quantity = sum(
                        input_data[f"{pathway.name}_mandate_quantity"]
                        for pathway in type_quantity_pathways
                    )
                    if (total_quantity.fillna(0) <= energy_consumption.fillna(0)).all():
                        # If the sum of quantities is less than or equal to the total, keep the quantities as output
                        for pathway in type_quantity_pathways:
                            pathway_consumption = input_data[f"{pathway.name}_mandate_quantity"]
                            output_data[f"{pathway.name}_energy_consumption"] = pathway_consumption
                            remaining_energy_consumption -= pathway_consumption.fillna(0)
                    else:
                        # If the sum exceeds the total, decrease them homogeneously
                        scaling_factor = pd.Series(
                            np.where(
                                total_quantity > remaining_energy_consumption,
                                remaining_energy_consumption / total_quantity,
                                1,
                            ),
                            index=total_quantity.index,
                        )
                        for pathway in type_quantity_pathways:
                            original = input_data[f"{pathway.name}_mandate_quantity"].fillna(0)
                            pathway_consumption = (original * scaling_factor).fillna(0)
                            output_data[f"{pathway.name}_energy_consumption"] = pathway_consumption
                            remaining_energy_consumption -= pathway_consumption

                            modified_years = pathway_consumption[pathway_consumption != original]

                            if not modified_years.empty:
                                msg = (
                                    f"\nThe sum of the quantity-defined {aircraft_type} fuel pathways exceeds the total {aircraft_type} energy consumption.\n"
                                    f"→ Pathway '{pathway.name}' energy consumption was adjusted in the following years:\n"
                                )
                                for year in modified_years.index:
                                    msg += f"   - {year}: {pathway_consumption[year]:.2e} MJ instead of {original[year]:.2e} MJ\n"

                                warnings.warn(msg)

                    # Second case : blending mandate pathways
                    type_share_pathways = self.pathways_manager.get(
                        aircraft_type=aircraft_type, mandate_type="share"
                    )
                    total_share_quantity = sum(
                        input_data[f"{pathway.name}_mandate_share"] / 100 * energy_consumption
                        for pathway in type_share_pathways
                    )
                    if (
                        total_share_quantity.fillna(0) <= remaining_energy_consumption.fillna(0)
                    ).all():
                        # If the sum of quantities is less than or equal to the total, keep the quantities as output
                        for pathway in type_share_pathways:
                            pathway_consumption = (
                                input_data[f"{pathway.name}_mandate_share"]
                                / 100
                                * energy_consumption
                            )
                            output_data[f"{pathway.name}_energy_consumption"] = pathway_consumption
                            remaining_energy_consumption -= pathway_consumption.fillna(0)
                    else:
                        # If the sum exceeds the total, decrease them homogeneously
                        scaling_factor = pd.Series(
                            np.where(
                                total_share_quantity > remaining_energy_consumption,
                                remaining_energy_consumption / total_share_quantity,
                                1,
                            ),
                            index=total_share_quantity.index,
                        )
                        for pathway in type_share_pathways:
                            original_share = input_data[f"{pathway.name}_mandate_share"].fillna(0)
                            pathway_consumption = (
                                original_share / 100 * energy_consumption * scaling_factor
                            ).fillna(0)
                            output_data[f"{pathway.name}_energy_consumption"] = pathway_consumption
                            remaining_energy_consumption -= pathway_consumption

                            modified_years = pathway_consumption[
                                pathway_consumption != original_share / 100 * energy_consumption
                            ]

                            if not modified_years.empty:
                                msg = (
                                    f"\nThe sum of the share-defined {aircraft_type} fuel pathways exceeds the total {aircraft_type} energy consumption (minus quantity-based pathways).\n"
                                    f"→ Pathway '{pathway.name}' share was adjusted in the following years:\n"
                                )
                                for year in modified_years.index:
                                    msg += f"   - {year}: {(pathway_consumption[year] * 100 / energy_consumption[year]):.1f} % instead of {(original_share[year]):.1f} %\n"

                                warnings.warn(msg)

                    # Third case: default pathway completes to fill the remaining energy consumption
                    pathway = type_default_pathway[0]
                    output_data[f"{pathway.name}_energy_consumption"] = (
                        remaining_energy_consumption.copy()
                    )
                    remaining_energy_consumption -= remaining_energy_consumption

                    # TODO modify the rest of aeromaps to work without these?
                    dropin_biofuel_consumption = sum(
                        output_data[f"{pathway.name}_energy_consumption"]
                        for pathway in self.pathways_manager.get(
                            aircraft_type=aircraft_type, energy_origin="biomass"
                        )
                    )
                    biofuel_share = dropin_biofuel_consumption / energy_consumption * 100
                    output_data["biofuel_share"] = biofuel_share.fillna(0)

                    dropin_electrofuel_consumption = sum(
                        output_data[f"{pathway.name}_energy_consumption"]
                        for pathway in self.pathways_manager.get(
                            aircraft_type=aircraft_type, energy_origin="electrofuel"
                        )
                    )
                    electrofuel_share = dropin_electrofuel_consumption / energy_consumption * 100
                    output_data["electrofuel_share"] = electrofuel_share.fillna(0)

                    dropin_kerosene_consumption = sum(
                        output_data[f"{pathway.name}_energy_consumption"]
                        for pathway in self.pathways_manager.get(
                            aircraft_type=aircraft_type, energy_origin="fossil"
                        )
                    )
                    kerosene_share = dropin_kerosene_consumption / energy_consumption * 100
                    output_data["kerosene_share"] = kerosene_share.fillna(0)

        # compute metrics derived from each patwhay consumption

        # TODO could be replaced by energy consumption once calculated differently
        total_energy_consumption = (
            input_data["energy_consumption_dropin_fuel"]
            + input_data["energy_consumption_hydrogen"]
            + input_data["energy_consumption_electric"]
        )

        # TODO  Get those inside main loop ? It would be messy in my opinion
        #       --> at least it can be optimized.
        # Compute share of each pathway in the total energy consumption
        for pathway in self.pathways_manager.get_all():
            output_data[f"{pathway.name}_share_total_energy"] = (
                output_data[f"{pathway.name}_energy_consumption"] / total_energy_consumption * 100
            )

        # Compute share of each pathway in a given aircraft type energy consumption
        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            type_energy_consumption = input_data[f"energy_consumption_{aircraft_type}"]
            for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                output_data[f"{pathway.name}_share_{aircraft_type}"] = (
                    output_data[f"{pathway.name}_energy_consumption"]
                    / type_energy_consumption
                    * 100
                )

        for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
            # Get the total energy consumption for each energy origin
            origin_energy_consumption = sum(
                output_data[f"{pathway.name}_energy_consumption"]
                for pathway in self.pathways_manager.get(energy_origin=energy_origin)
            )
            output_data[f"{energy_origin}_share_total_energy"] = (
                origin_energy_consumption / total_energy_consumption * 100
            )

        # TODO put all outputs in the df
        return output_data

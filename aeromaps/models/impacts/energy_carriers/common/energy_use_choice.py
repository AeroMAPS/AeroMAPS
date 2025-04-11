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
                # TODO discuss idea of having a target share to force refuel-eu like mandate
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
        """
        Compute the energy consumption of each energy carrier based on the defined pathways and mandates.
        """
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
                    scaling_factor = pd.Series(
                        np.where(
                            total_quantity > remaining_energy_consumption_dropin_fuel,
                            remaining_energy_consumption_dropin_fuel / total_quantity,
                            1,
                        ),
                        index=total_quantity.index,
                    )
                    for pathway in dropin_quantity_pathways:
                        original = input_data[f"{pathway.name}_mandate_quantity"].fillna(0)
                        pathway_consumption = (original * scaling_factor).fillna(0)
                        output_data[f"{pathway.name}_energy_consumption"] = pathway_consumption
                        remaining_energy_consumption_dropin_fuel -= pathway_consumption

                        modified_years = pathway_consumption[pathway_consumption != original]

                        if not modified_years.empty:
                            msg = (
                                f"\nThe sum of the quantity-defined drop-in fuel pathways exceeds the total drop-in energy consumption.\n"
                                f"→ Pathway '{pathway.name}' energy consumption was adjusted in the following years:\n"
                            )
                            for year in modified_years.index:
                                msg += f"   - {year}: {pathway_consumption[year]:.2e} MJ instead of {original[year]:.2e} MJ\n"

                            warnings.warn(msg)

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
                    scaling_factor = pd.Series(
                        np.where(
                            total_share_quantity > remaining_energy_consumption_dropin_fuel,
                            remaining_energy_consumption_dropin_fuel / total_share_quantity,
                            1,
                        ),
                        index=total_share_quantity.index,
                    )
                    for pathway in dropin_share_pathways:
                        original_share = input_data[f"{pathway.name}_mandate_share"].fillna(0)
                        pathway_consumption = (
                            original_share / 100 * energy_consumption_dropin_fuel * scaling_factor
                        ).fillna(0)
                        output_data[f"{pathway.name}_energy_consumption"] = pathway_consumption
                        remaining_energy_consumption_dropin_fuel -= pathway_consumption

                        modified_years = pathway_consumption[
                            pathway_consumption
                            != original_share / 100 * energy_consumption_dropin_fuel
                        ]

                        if not modified_years.empty:
                            msg = (
                                f"\nThe sum of the share-defined drop-in fuel pathways exceeds the total drop-in energy consumption (minus quantity-based pathways).\n"
                                f"→ Pathway '{pathway.name}' share was adjusted in the following years:\n"
                            )
                            for year in modified_years.index:
                                msg += f"   - {year}: {(pathway_consumption[year] * 100 / energy_consumption_dropin_fuel[year]):.1f} % instead of {(original_share[year]):.1f} %\n"

                            warnings.warn(msg)

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

            # TODO HYDROGEN AND ELECTRICITY ONCE DROP-IN ALL SET

        return output_data

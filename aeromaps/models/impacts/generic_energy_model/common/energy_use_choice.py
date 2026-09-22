"""
energy_use_choice

=====================
Central module with a model to handle pathways interaction.
"""

import warnings

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


def derive_share_families(
    volumes,
    total_energy_consumption,
    type_energy_consumption,
    pathways_manager,
    fallback_index,
):
    """Every share family that follows from the per-pathway volumes.

    Eight of the nine output families this module emits are the ninth divided by a
    total: share of all energy, share of an aircraft type, share of an energy origin,
    and the per-origin/per-type cross-tabulations. None of them is an independent
    decision -- given ``{pathway: volume}`` they are fixed.

    Pulled out of :meth:`EnergyUseChoice.compute` so the fuel market can emit the same
    families from volumes it solved for rather than volumes it was handed, without a
    second copy of this arithmetic. Two copies would drift, and the failure mode is
    silent: ``EnergyCarriersMeans`` multiplies by a share sum it never checks, so a
    share family that disagrees with its volumes rescales CO2 with no error raised.

    Parameters
    ----------
    volumes
        ``{pathway_name: Series}`` in MJ -- the ``{p}_energy_consumption`` family.
    total_energy_consumption
        Series in MJ, the denominator of the ``share_total_energy`` families.
    type_energy_consumption
        ``{aircraft_type: Series}`` in MJ, one hard budget per aircraft type.
    pathways_manager
        Metadata only; no coupling variables are read from it.
    fallback_index
        Year index for the three mandatory zero outputs, used only when no pathway of
        that origin exists.

    Returns
    -------
    dict
        The derived families. Does NOT include ``{p}_energy_consumption`` itself.
    """
    derived = {}

    for pathway in pathways_manager.get_all():
        derived[f"{pathway.name}_share_total_energy"] = (
            volumes[pathway.name] / total_energy_consumption * 100
        )

    for aircraft_type in pathways_manager.get_all_types("aircraft_type"):
        # Note the fillna(0) here and its ABSENCE in the energy-origin block below.
        # Preserved from the original rather than harmonised: the two differ in what
        # they emit where a budget is NaN, and that is downstream-visible behaviour.
        type_energy = type_energy_consumption[aircraft_type].fillna(0)
        for pathway in pathways_manager.get(aircraft_type=aircraft_type):
            derived[f"{pathway.name}_share_{aircraft_type}"] = (
                volumes[pathway.name] / type_energy.replace(0, np.nan) * 100
            )

    for energy_origin in pathways_manager.get_all_types("energy_origin"):
        origin_energy_consumption = sum(
            volumes[pathway.name].fillna(0)
            for pathway in pathways_manager.get(energy_origin=energy_origin)
        )
        for pathway in pathways_manager.get(energy_origin=energy_origin):
            derived[f"{pathway.name}_share_{energy_origin}"] = (
                volumes[pathway.name] / origin_energy_consumption.replace(0, np.nan) * 100
            )
        derived[f"{energy_origin}_share_total_energy"] = (
            origin_energy_consumption / total_energy_consumption * 100
        )

        for aircraft_type in pathways_manager.get_all_types("aircraft_type"):
            if pathways_manager.get(aircraft_type=aircraft_type, energy_origin=energy_origin):
                type_energy = type_energy_consumption[aircraft_type]

                origin_type_energy_consumption = sum(
                    volumes[pathway.name].fillna(0)
                    for pathway in pathways_manager.get(
                        energy_origin=energy_origin, aircraft_type=aircraft_type
                    )
                )

                derived[f"{aircraft_type}_{energy_origin}_energy_consumption"] = (
                    origin_type_energy_consumption
                )
                derived[f"{energy_origin}_share_{aircraft_type}"] = (
                    origin_type_energy_consumption / type_energy.replace(0, np.nan) * 100
                )
                derived[f"{aircraft_type}_share_{energy_origin}"] = (
                    origin_type_energy_consumption
                    / origin_energy_consumption.replace(0, np.nan)
                    * 100
                )
                for pathway in pathways_manager.get(
                    energy_origin=energy_origin, aircraft_type=aircraft_type
                ):
                    derived[f"{pathway.name}_share_{aircraft_type}_{energy_origin}"] = (
                        volumes[pathway.name]
                        / origin_type_energy_consumption.replace(0, np.nan)
                        * 100
                    )

    # Mandatory for non_co2 to work even when no pathway of that origin is declared.
    for output in (
        "biomass_share_dropin_fuel",
        "electricity_share_dropin_fuel",
        "fossil_share_dropin_fuel",
    ):
        if output not in derived:
            derived[output] = pd.Series(0.0, index=fallback_index)

    return derived


class EnergyUseChoice(AeroMAPSModel):
    """
    Central model to define volume consumed of each energy carrier considered depending on the mandate specified and priorities.

    Parameters
    ----------
    name : str
        Name of the model instance ('energy_use_choice' by default).
    configuration_data : dict
        Configuration data for the energy use choice model.
    pathways_manager : EnergyCarrierManager
        Manager containing all energy pathways metadata.

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
                        f"{name}_mandate_quantity": pd.Series([0.0]),
                    }
                )
            elif pathway.mandate_type == "share":
                self.input_names.update(
                    {
                        f"{name}_mandate_share": pd.Series([0.0]),
                    }
                )

        # Fill and initialize inputs not defined in the yaml file (either user inputs or other models outputs)
        self.input_names.update(
            {
                "energy_consumption_dropin_fuel": pd.Series([0.0]),
                "energy_consumption_hydrogen": pd.Series([0.0]),
                "energy_consumption_electric": pd.Series([0.0]),
                "energy_consumption": pd.Series([0.0]),
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
            for pathway in self.pathways_manager.get(energy_origin=energy_origin):
                self.output_names[f"{pathway.name}_share_{energy_origin}"] = pd.Series([0.0])
            for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
                if self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    self.output_names[f"{energy_origin}_share_{aircraft_type}"] = pd.Series([0.0])
                    self.output_names[f"{aircraft_type}_share_{energy_origin}"] = pd.Series([0.0])
                    self.output_names[f"{aircraft_type}_{energy_origin}_energy_consumption"] = (
                        pd.Series([0.0])
                    )
                    for pathway in self.pathways_manager.get(
                        energy_origin=energy_origin, aircraft_type=aircraft_type
                    ):
                        self.output_names[
                            f"{pathway.name}_share_{aircraft_type}_{energy_origin}"
                        ] = pd.Series([0.0])

        # mandatory outputs for aeromaps models to work even if no pathway is defined for a given type
        self.output_names.update(
            {
                "biomass_share_dropin_fuel": pd.Series([0.0]),
                "electricity_share_dropin_fuel": pd.Series([0.0]),
                "fossil_share_dropin_fuel": pd.Series([0.0]),
            }
        )

    def compute(self, input_data) -> dict:
        """
        Compute the energy consumption of each energy carrier based on the defined pathways and mandates and priority rules.

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
                    if type_quantity_pathways:
                        total_quantity = (
                            sum(
                                input_data[f"{pathway.name}_mandate_quantity"]
                                for pathway in type_quantity_pathways
                            )
                            .reindex(energy_consumption.index)
                            .fillna(0)
                        )
                        if (total_quantity <= energy_consumption.fillna(0)).all():
                            # If the sum of quantities is less than or equal to the total, keep the quantities as output
                            for pathway in type_quantity_pathways:
                                pathway_consumption = input_data[f"{pathway.name}_mandate_quantity"]
                                output_data[f"{pathway.name}_energy_consumption"] = (
                                    pathway_consumption
                                )
                                remaining_energy_consumption -= pathway_consumption.reindex(
                                    energy_consumption.index
                                ).fillna(0)
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
                                output_data[f"{pathway.name}_energy_consumption"] = (
                                    pathway_consumption
                                )
                                remaining_energy_consumption -= pathway_consumption.reindex(
                                    energy_consumption.index
                                ).fillna(0)

                                modified_years = pathway_consumption.loc[original.index][
                                    pathway_consumption.loc[original.index]
                                    != original.loc[original.index]
                                ]

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
                    if type_share_pathways:
                        total_share_quantity = (
                            sum(
                                input_data[f"{pathway.name}_mandate_share"]
                                / 100
                                * energy_consumption
                                for pathway in type_share_pathways
                            )
                            .reindex(energy_consumption.index)
                            .fillna(0)
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
                                output_data[f"{pathway.name}_energy_consumption"] = (
                                    pathway_consumption
                                )
                                remaining_energy_consumption -= pathway_consumption.reindex(
                                    energy_consumption.index
                                ).fillna(0)
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
                                original_share = input_data[f"{pathway.name}_mandate_share"].fillna(
                                    0
                                )
                                pathway_consumption = (
                                    original_share / 100 * energy_consumption * scaling_factor
                                ).fillna(0)
                                output_data[f"{pathway.name}_energy_consumption"] = (
                                    pathway_consumption
                                )
                                remaining_energy_consumption -= pathway_consumption.reindex(
                                    energy_consumption.index
                                ).fillna(0)

                                modified_years = pathway_consumption.loc[original_share.index][
                                    pathway_consumption.loc[original_share.index]
                                    != (
                                        original_share
                                        / 100
                                        * energy_consumption.loc[original_share.index]
                                    )
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

            else:
                # If there is no energy consumption, set all energy consumption to 0
                for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                    output_data[f"{pathway.name}_energy_consumption"] = pd.Series(
                        [0.0] * (self.end_year - self.historic_start_year + 1),
                        index=pd.RangeIndex(start=self.historic_start_year, stop=self.end_year + 1),
                    )

        # Every remaining family follows from the volumes just decided. Shared with the
        # fuel market, which solves for those volumes instead of allocating them.
        output_data.update(
            derive_share_families(
                volumes={
                    pathway.name: output_data[f"{pathway.name}_energy_consumption"]
                    for pathway in self.pathways_manager.get_all()
                },
                total_energy_consumption=input_data["energy_consumption"],
                type_energy_consumption={
                    aircraft_type: input_data[f"energy_consumption_{aircraft_type}"]
                    for aircraft_type in self.pathways_manager.get_all_types("aircraft_type")
                },
                pathways_manager=self.pathways_manager,
                fallback_index=range(self.historic_start_year, self.end_year + 1),
            )
        )

        # Add all output data in self.df and self.float_outputs
        self._store_outputs(output_data)

        return output_data

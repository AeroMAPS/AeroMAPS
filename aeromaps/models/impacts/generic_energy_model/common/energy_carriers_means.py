"""
energy_carriers_means

=======================
This module contains models to compute mean emissions and costs
"""

import warnings

import jax.numpy as jnp
import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.utils.defaults import get_default_series


class EnergyCarriersMeans(AeroMAPSModel):
    """
    This model loops through the pathways and computes mean emissions

    Parameters
    ----------
    name : str
        Name of the model instance ('energy_carriers_means' by default).
    configuration_data : dict
        Dictionary containing generic pathways configuration data.
    pathways_manager : PathwaysManager
        Instance of the PathwaysManager containing all defined energy pathways.

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

        self.pathways_manager = pathways_manager

        self.input_names = {}
        self.output_names = {}

        aircraft_types = ["dropin_fuel", "hydrogen", "electric"]

        for aircraft_type in aircraft_types:
            self.output_names.update(
                {
                    f"{aircraft_type}_mean_co2_emission_factor": pd.Series([0.0]),
                    f"{aircraft_type}_mean_mfsp": pd.Series([0.0]),
                    f"{aircraft_type}_mean_net_mfsp": pd.Series([0.0]),
                    f"{aircraft_type}_mean_net_mfsp_without_carbon_tax": pd.Series([0.0]),
                    f"{aircraft_type}_mean_carbon_tax_supplement": pd.Series([0.0]),
                    f"{aircraft_type}_marginal_net_mfsp": pd.Series([0.0]),
                    f"{aircraft_type}_mean_unit_subsidy": pd.Series([0.0]),
                    f"{aircraft_type}_mean_unit_tax": pd.Series([0.0]),
                    f"{aircraft_type}_mean_unit_carbon_tax": pd.Series([0.0]),
                }
            )
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                # check if the energy origin is used for this pathway type
                if self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    self.output_names.update(
                        {
                            f"{aircraft_type}_{energy_origin}_mean_co2_emission_factor": pd.Series(
                                [0.0]
                            ),
                            f"{aircraft_type}_{energy_origin}_mean_mfsp": pd.Series([0.0]),
                            f"{aircraft_type}_{energy_origin}_mean_net_mfsp": pd.Series([0.0]),
                            f"{aircraft_type}_{energy_origin}_mean_net_mfsp_without_carbon_tax": pd.Series(
                                [0.0]
                            ),
                            f"{aircraft_type}_{energy_origin}_mean_carbon_tax_supplement": pd.Series(
                                [0.0]
                            ),
                            f"{aircraft_type}_{energy_origin}_marginal_net_mfsp": pd.Series([0.0]),
                            f"{aircraft_type}_{energy_origin}_mean_unit_subsidy": pd.Series([0.0]),
                            f"{aircraft_type}_{energy_origin}_mean_unit_tax": pd.Series([0.0]),
                            f"{aircraft_type}_{energy_origin}_mean_unit_carbon_tax": pd.Series(
                                [0.0]
                            ),
                        }
                    )

            for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                self.input_names.update(
                    {
                        f"{pathway.name}_share_{aircraft_type}": pd.Series([0.0]),
                        f"{pathway.name}_mean_co2_emission_factor": pd.Series([0.0]),
                        f"{pathway.name}_net_mfsp": pd.Series([0.0]),
                        f"{pathway.name}_net_mfsp_without_carbon_tax": pd.Series([0.0]),
                        f"{pathway.name}_mean_mfsp": pd.Series([0.0]),
                        f"{pathway.name}_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                        f"{pathway.name}_mean_unit_subsidy": pd.Series([0.0]),
                        f"{pathway.name}_mean_unit_tax": pd.Series([0.0]),
                        f"{pathway.name}_mean_unit_carbon_tax": pd.Series([0.0]),
                    }
                )

    def compute(self, input_data) -> dict:
        """
        This function loops through different energy types and computes the mean emissions and costs
        TODO: SPLIT COST AND EMISSIONS

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

        aircraft_types = ["dropin_fuel", "hydrogen", "electric"]

        for aircraft_type in aircraft_types:
            # intialize the mean values for the aircraft type

            mean_emission_factor = get_default_series(self.historic_start_year, self.end_year)
            mean_mfsp = get_default_series(self.historic_start_year, self.end_year)
            mean_net_mfsp = get_default_series(self.historic_start_year, self.end_year)
            mean_net_mfsp_without_carbon_tax = get_default_series(
                self.historic_start_year, self.end_year
            )
            mean_carbon_tax_supplement = get_default_series(self.historic_start_year, self.end_year)
            marginal_net_mfsp = get_default_series(self.historic_start_year, self.end_year)
            cumulative_share = get_default_series(self.historic_start_year, self.end_year)
            mean_unit_subsidy = get_default_series(self.historic_start_year, self.end_year)
            mean_unit_tax = get_default_series(self.historic_start_year, self.end_year)
            mean_unit_carbon_tax = get_default_series(self.historic_start_year, self.end_year)

            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                # Get the pathways for this aircraft type and energy origin
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
                    origin_mean_emission_factor = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_mean_mfsp = get_default_series(self.historic_start_year, self.end_year)
                    origin_mean_net_mfsp = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_mean_net_mfsp_without_carbon_tax = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_mean_carbon_tax_supplement = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_marginal_net_mfsp = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_cumulative_share = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_mean_unit_subsidy = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_mean_unit_tax = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_mean_unit_carbon_tax = get_default_series(
                        self.historic_start_year, self.end_year
                    )

                    for pathway in pathways:
                        share = input_data[f"{pathway.name}_share_{aircraft_type}"]
                        origin_share = input_data[
                            f"{pathway.name}_share_{aircraft_type}_{energy_origin}"
                        ]
                        cumulative_share = cumulative_share + share.fillna(0) / 100
                        origin_cumulative_share = (
                            origin_cumulative_share + origin_share.fillna(0) / 100
                        )

                        # Emission factors

                        pathway_emission_factor = input_data[
                            f"{pathway.name}_mean_co2_emission_factor"
                        ]
                        mean_emission_factor += (pathway_emission_factor * share).fillna(0) / 100
                        origin_mean_emission_factor += (
                            pathway_emission_factor * origin_share
                        ).fillna(0) / 100

                        # MFSP and costs
                        pathway_mfsp = input_data[f"{pathway.name}_mean_mfsp"]
                        mean_mfsp += (pathway_mfsp * share).fillna(0) / 100
                        origin_mean_mfsp += (pathway_mfsp * origin_share).fillna(0) / 100

                        pathway_net_mfsp = input_data[f"{pathway.name}_net_mfsp"]
                        mean_net_mfsp += (pathway_net_mfsp * share).fillna(0) / 100
                        origin_mean_net_mfsp += (pathway_net_mfsp * origin_share).fillna(0) / 100

                        pathway_net_mfsp_without_carbon_tax = input_data[
                            f"{pathway.name}_net_mfsp_without_carbon_tax"
                        ]
                        mean_net_mfsp_without_carbon_tax += (
                            pathway_net_mfsp_without_carbon_tax * share
                        ).fillna(0) / 100
                        origin_mean_net_mfsp_without_carbon_tax += (
                            pathway_net_mfsp_without_carbon_tax * origin_share
                        ).fillna(0) / 100

                        mean_carbon_tax_supplement += (
                            (pathway_net_mfsp - pathway_net_mfsp_without_carbon_tax) * share
                        ).fillna(0) / 100
                        origin_mean_carbon_tax_supplement += (
                            (pathway_net_mfsp - pathway_net_mfsp_without_carbon_tax) * origin_share
                        ).fillna(0) / 100

                        pathway_unit_subsidy = input_data[f"{pathway.name}_mean_unit_subsidy"]
                        mean_unit_subsidy += (pathway_unit_subsidy * share).fillna(0) / 100
                        origin_mean_unit_subsidy += (pathway_unit_subsidy * origin_share).fillna(
                            0
                        ) / 100

                        pathway_unit_tax = input_data[f"{pathway.name}_mean_unit_tax"]
                        mean_unit_tax += (pathway_unit_tax * share).fillna(0) / 100
                        origin_mean_unit_tax += (pathway_unit_tax * origin_share).fillna(0) / 100

                        pathway_unit_carbon_tax = input_data[f"{pathway.name}_mean_unit_carbon_tax"]
                        mean_unit_carbon_tax += (pathway_unit_carbon_tax * share).fillna(0) / 100
                        origin_mean_unit_carbon_tax += (
                            pathway_unit_carbon_tax * origin_share
                        ).fillna(0) / 100

                        # compute the marginal net MFSP for each aircraft type: the most expensive pathways each year
                        marginal_net_mfsp = marginal_net_mfsp.where(
                            marginal_net_mfsp
                            > pathway_net_mfsp.reindex(marginal_net_mfsp.index).fillna(0),
                            pathway_net_mfsp.reindex(marginal_net_mfsp.index).fillna(0),
                        )
                        origin_marginal_net_mfsp = origin_marginal_net_mfsp.where(
                            origin_marginal_net_mfsp
                            > pathway_net_mfsp.reindex(origin_marginal_net_mfsp.index).fillna(0),
                            pathway_net_mfsp.reindex(origin_marginal_net_mfsp.index).fillna(0),
                        )

                    origin_valid_years = origin_cumulative_share.replace(0, np.nan)

                    output_data[f"{aircraft_type}_{energy_origin}_mean_co2_emission_factor"] = (
                        origin_mean_emission_factor * origin_valid_years
                    )
                    output_data[f"{aircraft_type}_{energy_origin}_mean_mfsp"] = (
                        origin_mean_mfsp * origin_valid_years
                    )
                    output_data[f"{aircraft_type}_{energy_origin}_mean_net_mfsp"] = (
                        origin_mean_net_mfsp * origin_valid_years
                    )
                    output_data[
                        f"{aircraft_type}_{energy_origin}_mean_net_mfsp_without_carbon_tax"
                    ] = origin_mean_net_mfsp_without_carbon_tax * origin_valid_years
                    output_data[f"{aircraft_type}_{energy_origin}_mean_carbon_tax_supplement"] = (
                        origin_mean_carbon_tax_supplement * origin_valid_years
                    )
                    output_data[f"{aircraft_type}_{energy_origin}_marginal_net_mfsp"] = (
                        origin_marginal_net_mfsp * origin_valid_years
                    )
                    # Store mean unit subsidy, tax, carbon tax
                    output_data[f"{aircraft_type}_{energy_origin}_mean_unit_subsidy"] = (
                        origin_mean_unit_subsidy * origin_valid_years
                    )
                    output_data[f"{aircraft_type}_{energy_origin}_mean_unit_tax"] = (
                        origin_mean_unit_tax * origin_valid_years
                    )
                    output_data[f"{aircraft_type}_{energy_origin}_mean_unit_carbon_tax"] = (
                        origin_mean_unit_carbon_tax * origin_valid_years
                    )

            # if no energy consumption for any year, replace by nan. if all pathways not equal to 100%, triggers warning
            valid_years = cumulative_share.replace(0, np.nan)
            # check that there are only ones in the cumulative share

            faulty_years = valid_years[valid_years.notna() & (valid_years.round(3) != 1.000)].index
            if not faulty_years.empty:
                warnings.warn(
                    f"AeroMAPS internal error: sum of pathway shares for {aircraft_type} is not equal to 100% in the following years: {faulty_years.tolist()}"
                )

            # store means in the inputs data, and multiply by cumulative share to set nans when there s no energy consumption
            output_data[f"{aircraft_type}_mean_co2_emission_factor"] = (
                mean_emission_factor * valid_years
            )
            output_data[f"{aircraft_type}_mean_mfsp"] = mean_mfsp * valid_years
            output_data[f"{aircraft_type}_mean_net_mfsp"] = mean_net_mfsp * valid_years
            output_data[f"{aircraft_type}_mean_net_mfsp_without_carbon_tax"] = (
                mean_net_mfsp_without_carbon_tax * valid_years
            )
            output_data[f"{aircraft_type}_mean_carbon_tax_supplement"] = (
                mean_carbon_tax_supplement * valid_years
            )
            output_data[f"{aircraft_type}_marginal_net_mfsp"] = marginal_net_mfsp * valid_years
            # Store mean unit subsidy, tax, carbon tax
            output_data[f"{aircraft_type}_mean_unit_subsidy"] = mean_unit_subsidy * valid_years
            output_data[f"{aircraft_type}_mean_unit_tax"] = mean_unit_tax * valid_years
            output_data[f"{aircraft_type}_mean_unit_carbon_tax"] = (
                mean_unit_carbon_tax * valid_years
            )

        # get output data in the means
        self._store_outputs(output_data)

        return output_data

    def jax_compute(self, input_data) -> dict:
        """JAX version of :meth:`compute` (same contract, pure jax.numpy)."""
        output_data = {}
        n = self.end_year - self.historic_start_year + 1
        aircraft_types = ["dropin_fuel", "hydrogen", "electric"]

        fields = (
            ("mean_co2_emission_factor", "mean_co2_emission_factor"),
            ("mean_mfsp", "mean_mfsp"),
            ("net_mfsp", "mean_net_mfsp"),
            ("net_mfsp_without_carbon_tax", "mean_net_mfsp_without_carbon_tax"),
            ("mean_unit_subsidy", "mean_unit_subsidy"),
            ("mean_unit_tax", "mean_unit_tax"),
            ("mean_unit_carbon_tax", "mean_unit_carbon_tax"),
        )

        for aircraft_type in aircraft_types:
            means = {out: jnp.zeros(n) for _, out in fields}
            mean_carbon_tax_supplement = jnp.zeros(n)
            marginal_net_mfsp = jnp.zeros(n)
            cumulative_share = jnp.zeros(n)

            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if not pathways:
                    continue
                origin_means = {out: jnp.zeros(n) for _, out in fields}
                origin_mean_carbon_tax_supplement = jnp.zeros(n)
                origin_marginal_net_mfsp = jnp.zeros(n)
                origin_cumulative_share = jnp.zeros(n)

                for pathway in pathways:
                    share = jnp.asarray(input_data[f"{pathway.name}_share_{aircraft_type}"])
                    origin_share = jnp.asarray(
                        input_data[f"{pathway.name}_share_{aircraft_type}_{energy_origin}"]
                    )
                    cumulative_share = cumulative_share + jnp.nan_to_num(share) / 100.0
                    origin_cumulative_share = (
                        origin_cumulative_share + jnp.nan_to_num(origin_share) / 100.0
                    )

                    for in_key, out_key in fields:
                        value = jnp.asarray(input_data[f"{pathway.name}_{in_key}"])
                        means[out_key] = means[out_key] + jnp.nan_to_num(value * share) / 100.0
                        origin_means[out_key] = (
                            origin_means[out_key] + jnp.nan_to_num(value * origin_share) / 100.0
                        )

                    net_mfsp = jnp.asarray(input_data[f"{pathway.name}_net_mfsp"])
                    net_mfsp_wo_ct = jnp.asarray(
                        input_data[f"{pathway.name}_net_mfsp_without_carbon_tax"]
                    )
                    supplement = net_mfsp - net_mfsp_wo_ct
                    mean_carbon_tax_supplement = (
                        mean_carbon_tax_supplement + jnp.nan_to_num(supplement * share) / 100.0
                    )
                    origin_mean_carbon_tax_supplement = (
                        origin_mean_carbon_tax_supplement
                        + jnp.nan_to_num(supplement * origin_share) / 100.0
                    )

                    marginal_net_mfsp = jnp.maximum(marginal_net_mfsp, jnp.nan_to_num(net_mfsp))
                    origin_marginal_net_mfsp = jnp.maximum(
                        origin_marginal_net_mfsp, jnp.nan_to_num(net_mfsp)
                    )

                origin_valid = jnp.where(
                    origin_cumulative_share == 0.0, jnp.nan, origin_cumulative_share
                )
                prefix = f"{aircraft_type}_{energy_origin}"
                for _, out_key in fields:
                    output_data[f"{prefix}_{out_key}"] = origin_means[out_key] * origin_valid
                output_data[f"{prefix}_mean_carbon_tax_supplement"] = (
                    origin_mean_carbon_tax_supplement * origin_valid
                )
                output_data[f"{prefix}_marginal_net_mfsp"] = origin_marginal_net_mfsp * origin_valid

            valid = jnp.where(cumulative_share == 0.0, jnp.nan, cumulative_share)
            for _, out_key in fields:
                output_data[f"{aircraft_type}_{out_key}"] = means[out_key] * valid
            output_data[f"{aircraft_type}_mean_carbon_tax_supplement"] = (
                mean_carbon_tax_supplement * valid
            )
            output_data[f"{aircraft_type}_marginal_net_mfsp"] = marginal_net_mfsp * valid

        return output_data


class EnergyCarriersMassicShares(AeroMAPSModel):
    """
    This model computes the massic shares of each pathway using its lhv and its energy consumption

    Parameters
    ----------
    name : str
        Name of the model instance ('energy_carriers_massic_shares' by default).

    Attributes
    ----------
    pathways_manager : EnergyCarrierManager
        Instance of the EnergyCarrierManager containing all defined energy pathways.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.
    """

    def __init__(self, name="energy_carriers_massic_shares", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
        """
        Sets up input and output names for the model based on the pathways in the pathways_manager.

        Returns
        -------
        None

        """
        self.input_names = {}
        self.output_names = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                self.input_names.update(
                    {
                        f"{pathway.name}_energy_consumption": pd.Series([0.0]),
                        f"{pathway.name}_lhv": 0.0,
                    }
                )
                self.output_names.update(
                    {
                        f"{pathway.name}_mass_consumption": pd.Series([0.0]),
                        f"{pathway.name}_massic_share_{aircraft_type}": pd.Series([0.0]),
                        f"{pathway.name}_massic_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(self, input_data) -> dict:
        """
        This function computes the massic shares of each pathway using its lhv and its energy consumption
        Shares are given per aircraft type and aircraft type + energy origin

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

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            mass_consumption = sum(
                input_data[f"{pathway.name}_energy_consumption"].fillna(0)
                / input_data[f"{pathway.name}_lhv"]
                for pathway in self.pathways_manager.get(aircraft_type=aircraft_type)
            )
            # initialise the mean values for the aircraft type
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                # Get the pathways for this aircraft type and energy origin
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
                    origin_mass_consumption = sum(
                        input_data[f"{pathway.name}_energy_consumption"].fillna(0)
                        / input_data[f"{pathway.name}_lhv"]
                        for pathway in pathways
                    )

                    for pathway in pathways:
                        pathway_energy_consumption = input_data[
                            f"{pathway.name}_energy_consumption"
                        ]
                        pathway_lhv = input_data[f"{pathway.name}_lhv"]
                        pathway_mass_consumption = (
                            pathway_energy_consumption / pathway_lhv
                        ).fillna(0)

                        # compute the massic share for each pathway
                        origin_massic_share = (
                            pathway_mass_consumption / origin_mass_consumption
                        ).fillna(0) * 100
                        massic_share = (pathway_mass_consumption / mass_consumption).fillna(0) * 100

                        output_data[f"{pathway.name}_mass_consumption"] = pathway_mass_consumption
                        output_data[
                            f"{pathway.name}_massic_share_{aircraft_type}_{energy_origin}"
                        ] = origin_massic_share
                        output_data[f"{pathway.name}_massic_share_{aircraft_type}"] = massic_share

        self._store_outputs(output_data)
        return output_data

    def jax_compute(self, input_data) -> dict:
        """JAX version of :meth:`compute` (same contract, pure jax.numpy)."""
        output_data = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            mass_consumption = sum(
                jnp.nan_to_num(jnp.asarray(input_data[f"{pathway.name}_energy_consumption"]))
                / input_data[f"{pathway.name}_lhv"]
                for pathway in self.pathways_manager.get(aircraft_type=aircraft_type)
            )
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if not pathways:
                    continue
                origin_mass_consumption = sum(
                    jnp.nan_to_num(jnp.asarray(input_data[f"{pathway.name}_energy_consumption"]))
                    / input_data[f"{pathway.name}_lhv"]
                    for pathway in pathways
                )
                for pathway in pathways:
                    pathway_mass_consumption = jnp.nan_to_num(
                        jnp.asarray(input_data[f"{pathway.name}_energy_consumption"])
                        / input_data[f"{pathway.name}_lhv"]
                    )
                    origin_massic_share = (
                        jnp.nan_to_num(pathway_mass_consumption / origin_mass_consumption) * 100.0
                    )
                    massic_share = (
                        jnp.nan_to_num(pathway_mass_consumption / mass_consumption) * 100.0
                    )

                    output_data[f"{pathway.name}_mass_consumption"] = pathway_mass_consumption
                    output_data[f"{pathway.name}_massic_share_{aircraft_type}_{energy_origin}"] = (
                        origin_massic_share
                    )
                    output_data[f"{pathway.name}_massic_share_{aircraft_type}"] = massic_share

        return output_data


class EnergyCarriersMeanLHV(AeroMAPSModel):
    """
    This model computes the mean energy LHV for each aircraft type and energy origin

    Parameters
    ----------
    name : str
        Name of the model instance ('energy_carriers_mean_lhv' by default).

    Attributes
    ----------
    pathways_manager : EnergyCarrierManager
        Instance of the EnergyCarrierManager containing all defined energy pathways.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.
    """

    def __init__(self, name="energy_carriers_mean_lhv", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
        """
        Sets up input and output names for the model based on the pathways in the pathways_manager.

        Returns
        -------
        None
        """
        self.input_names = {}
        self.output_names = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            self.output_names.update(
                {
                    f"{aircraft_type}_mean_lhv": pd.Series([0.0]),
                }
            )
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                if self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    self.output_names.update(
                        {
                            f"{aircraft_type}_{energy_origin}_mean_lhv": pd.Series([0.0]),
                        }
                    )

            for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                self.input_names.update(
                    {
                        f"{pathway.name}_lhv": 0.0,
                        f"{pathway.name}_massic_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                        f"{pathway.name}_massic_share_{aircraft_type}": pd.Series([0.0]),
                    }
                )

    def compute(self, input_data) -> dict:
        """
        Average H20 emission index calculation.
        This function computes the mean LHV for each aircraft type and energy origin using the massic shares of each pathway.

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

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            mean_lhv = get_default_series(self.historic_start_year, self.end_year)
            cumulative_share = get_default_series(self.historic_start_year, self.end_year)
            # initialise the mean values for the aircraft type
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                # Get the pathways for this aircraft type and energy origin
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
                    origin_mean_lhv = get_default_series(self.historic_start_year, self.end_year)
                    origin_cumulative_share = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_massic_share_{aircraft_type}_{energy_origin}"
                        ]
                        share = input_data[f"{pathway.name}_massic_share_{aircraft_type}"]
                        origin_cumulative_share = (
                            origin_cumulative_share + origin_share.fillna(0) / 100
                        )

                        cumulative_share = cumulative_share + share.fillna(0) / 100

                        pathway_lhv = input_data[f"{pathway.name}_lhv"]

                        origin_mean_lhv += (pathway_lhv * origin_share).fillna(0) / 100
                        mean_lhv += (pathway_lhv * share).fillna(0) / 100

                    origin_valid_years = origin_cumulative_share.replace(0, np.nan)
                    valid_years = cumulative_share.replace(0, np.nan)

                    output_data[f"{aircraft_type}_{energy_origin}_mean_lhv"] = (
                        origin_mean_lhv * origin_valid_years
                    )
                    output_data[f"{aircraft_type}_mean_lhv"] = mean_lhv * valid_years

        self._store_outputs(output_data)

        return output_data

    def jax_compute(self, input_data) -> dict:
        """JAX version of :meth:`compute` (same contract, pure jax.numpy)."""
        output_data = {}
        n = self.end_year - self.historic_start_year + 1

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            mean_lhv = jnp.zeros(n)
            cumulative_share = jnp.zeros(n)
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if not pathways:
                    continue
                origin_mean_lhv = jnp.zeros(n)
                origin_cumulative_share = jnp.zeros(n)
                for pathway in pathways:
                    origin_share = jnp.asarray(
                        input_data[f"{pathway.name}_massic_share_{aircraft_type}_{energy_origin}"]
                    )
                    share = jnp.asarray(input_data[f"{pathway.name}_massic_share_{aircraft_type}"])
                    origin_cumulative_share = (
                        origin_cumulative_share + jnp.nan_to_num(origin_share) / 100.0
                    )
                    cumulative_share = cumulative_share + jnp.nan_to_num(share) / 100.0

                    pathway_lhv = input_data[f"{pathway.name}_lhv"]
                    origin_mean_lhv = (
                        origin_mean_lhv + jnp.nan_to_num(pathway_lhv * origin_share) / 100.0
                    )
                    mean_lhv = mean_lhv + jnp.nan_to_num(pathway_lhv * share) / 100.0

                origin_valid = jnp.where(
                    origin_cumulative_share == 0.0, jnp.nan, origin_cumulative_share
                )
                valid = jnp.where(cumulative_share == 0.0, jnp.nan, cumulative_share)

                output_data[f"{aircraft_type}_{energy_origin}_mean_lhv"] = (
                    origin_mean_lhv * origin_valid
                )
                output_data[f"{aircraft_type}_mean_lhv"] = mean_lhv * valid

        return output_data

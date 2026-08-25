"""
cost

======
Module to compute pathway mfsp and investments using the bottom-up techno-economic model.
"""

import warnings

import jax.numpy as jnp
import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.models.jax_helpers import jax_nan_add, year_pos, years_index
from aeromaps.utils.functions import _get_value_for_year, _custom_series_addition


class BottomUpCost(AeroMAPSModel):
    """
    Bottom-up techno-economic cost model for a given pathway, based on annual plant additions.

    Parameters
    ----------
    name : str
        Name of the model instance ('f"{pathway_name}_bottom_up_unit_cost"' by default).
    configuration_data : dict
        Configuration data for the pathway from the yaml file.
    resources_data : dict
        Configuration data for the resources from the yaml file.
    processes_data : dict
        Configuration data for the processes from the yaml file.

    Attributes
    ----------
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.
    resource_keys : list
        List of resource keys used in the pathway.
    process_keys : list
        List of process keys used in the pathway.
    compute_all_years : bool
        Flag indicating whether to compute costs for all years or only for years with commissioned capacity.
    compute_abatement_cost : bool
        Flag indicating whether to compute abatement costs.
    """

    MODEL_APPROACH = "bottom_up"

    def __init__(self, name, configuration_data, resources_data, processes_data, *args, **kwargs):
        super().__init__(
            name=name,
            model_type="custom",
            *args,
            **kwargs,
        )
        # Get the name of the pathway
        self.pathway_name = configuration_data["name"]

        # Get the inputs from the configuration file: two options
        # 1. All inputs of a certain category in the yaml file
        for key, val in configuration_data.get("inputs").get("economics", {}).items():
            # TODO initialize with zeros instead of actual val?
            self.input_names[key] = val
        for key, val in configuration_data.get("inputs").get("technical", {}).items():
            # TODO initialize with zeros instead of actual val? How to better get rid of unnecessary variables
            if (
                key == f"{self.pathway_name}_resource_names"
                or key == f"{self.pathway_name}_processes_names"
            ):
                pass  # avoid having strings as variable in gemseo, not needed as variables
            else:
                self.input_names[key] = val

        # 2. Set individual inputs, coming either from other models or from the yaml as well
        self.input_names.update(
            {
                f"{self.pathway_name}_energy_production_commissioned": pd.Series([0.0]),
                f"{self.pathway_name}_energy_consumption": pd.Series([0.0]),
                f"{self.pathway_name}_energy_unused": pd.Series([0.0]),
                f"{self.pathway_name}_mean_co2_emission_factor": pd.Series([0.0]),
                "private_discount_rate": 0.0,
                "carbon_tax": pd.Series([0.0]),
            }
        )
        if configuration_data.get("environmental_model") == "bottom_up":
            self.input_names.update(
                {
                    f"{self.pathway_name}_vintage_eis_co2_emission_factor": pd.Series([0.0]),
                }
            )

        self.output_names = {
            f"{self.pathway_name}_mean_mfsp_without_resource": pd.Series([0.0]),
            f"{self.pathway_name}_mean_unit_capex": pd.Series([0.0]),
            f"{self.pathway_name}_mean_unit_fixed_opex": pd.Series([0.0]),
            f"{self.pathway_name}_mean_unit_variable_opex": pd.Series([0.0]),
            f"{self.pathway_name}_capex_cost": pd.Series([0.0]),
            # Ajout des sorties vintage pour les coûts principaux
            f"{self.pathway_name}_vintage_unit_capex": pd.Series([0.0]),
            f"{self.pathway_name}_vintage_unit_fixed_opex": pd.Series([0.0]),
            f"{self.pathway_name}_vintage_unit_variable_opex": pd.Series([0.0]),
        }

        # 3. Getting resources is a bit more complex as we need to get necessary resources for the pathway
        self.resource_keys = (
            configuration_data.get("inputs")
            .get("technical", {})
            .get(f"{self.pathway_name}_resource_names", [])
        ).copy()

        for key in self.resource_keys:
            # Outputs.
            self.output_names[f"{self.pathway_name}_excluding_processes_{key}_mean_unit_cost"] = (
                pd.Series([0.0])
            )
            # Ajout sortie vintage pour chaque ressource
            self.output_names[
                f"{self.pathway_name}_excluding_processes_{key}_vintage_unit_cost"
            ] = pd.Series([0.0])

        self.process_keys = (
            configuration_data.get("inputs")
            .get("technical", {})
            .get(f"{self.pathway_name}_processes_names", [])
        ).copy()

        for process_key in self.process_keys:
            for key, val in processes_data[process_key].get("inputs").get("technical", {}).items():
                if key == f"{process_key}_resource_names":
                    resources = (
                        processes_data[process_key]
                        .get("inputs")
                        .get("technical", {})
                        .get(f"{process_key}_resource_names", [])
                    ).copy()
                    self.resource_keys.extend(resources)
                    for resource in resources:
                        self.output_names[
                            f"{self.pathway_name}_{process_key}_{resource}_mean_unit_cost"
                        ] = pd.Series([0.0])
                        # Ajout sortie vintage pour chaque ressource de process
                        self.output_names[
                            f"{self.pathway_name}_{process_key}_{resource}_vintage_unit_cost"
                        ] = pd.Series([0.0])
                else:
                    # TODO initialize with zeros instead of actual val?
                    self.input_names[key] = val

            for key, val in processes_data[process_key].get("inputs").get("economics", {}).items():
                # TODO initialize with zeros instead of actual val?
                self.input_names[key] = val
            self.output_names[
                f"{self.pathway_name}_{process_key}_mean_unit_cost_without_resources"
            ] = pd.Series([0.0])
            self.output_names[f"{self.pathway_name}_{process_key}_mean_unit_capex"] = pd.Series(
                [0.0]
            )
            self.output_names[f"{self.pathway_name}_{process_key}_capex_cost"] = pd.Series([0.0])
            self.output_names[f"{self.pathway_name}_{process_key}_mean_unit_fixed_opex"] = (
                pd.Series([0.0])
            )
            self.output_names[f"{self.pathway_name}_{process_key}_mean_unit_variable_opex"] = (
                pd.Series([0.0])
            )
            self.output_names[f"{self.pathway_name}_{process_key}_vintage_unit_capex"] = pd.Series(
                [0.0]
            )
            self.output_names[f"{self.pathway_name}_{process_key}_vintage_unit_fixed_opex"] = (
                pd.Series([0.0])
            )
            self.output_names[f"{self.pathway_name}_{process_key}_vintage_unit_variable_opex"] = (
                pd.Series([0.0])
            )

        # Getting unique resources
        self.resource_keys = list(set(self.resource_keys))

        # Adding resources-linked inputs and outputs
        # TODO specify eco/cost as for process
        for key in self.resource_keys:
            if f"{key}_cost" in resources_data[key]["specifications"]:
                self.input_names[f"{key}_cost"] = pd.Series([0.0])
            if f"{key}_load_factor" in resources_data[key]["specifications"]:
                self.input_names[f"{key}_load_factor"] = pd.Series([0.0])
            # Outputs.

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names.update(
            {
                f"{self.pathway_name}_net_mfsp_without_carbon_tax": pd.Series([0.0]),
                f"{self.pathway_name}_net_mfsp": pd.Series([0.0]),
                f"{self.pathway_name}_mean_mfsp": pd.Series([0.0]),
                f"{self.pathway_name}_marginal_mfsp": pd.Series([0.0]),
                f"{self.pathway_name}_mean_unit_tax": pd.Series([0.0]),
                f"{self.pathway_name}_mean_unit_carbon_tax": pd.Series([0.0]),
                f"{self.pathway_name}_mean_unit_subsidy": pd.Series([0.0]),
            }
        )

        if configuration_data.get("environmental_model") == "bottom_up":
            self.output_names.update(
                {
                    f"{self.pathway_name}_vintage_eis_carbon_tax": pd.Series([0.0]),
                }
            )

        if configuration_data.get("compute_all_years"):
            self.compute_all_years = True
        else:
            self.compute_all_years = False

        if configuration_data.get("abatement_cost"):
            self.compute_abatement_cost = True
            self.output_names[f"{self.pathway_name}_lifespan_unitary_discounted_costs"] = pd.Series(
                [0.0]
            )
            self.input_names["social_discount_rate"] = 0.0
        else:
            self.compute_abatement_cost = False

    def compute(self, input_data) -> dict:
        """
        Execute the bottom-up techno-economic cost computation for the pathway.
        Each plant (vintage) is commissioned with the characteristics of its commissioning year,
        and its emissions are distributed over its lifespan, weighted by its share in annual production.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.
        """
        optional_nan_series = pd.Series(
            np.nan, index=range(self.historic_start_year, self.end_year + 1)
        )

        energy_production_commissioned = input_data[
            f"{self.pathway_name}_energy_production_commissioned"
        ]
        energy_consumption = input_data[f"{self.pathway_name}_energy_consumption"]
        energy_unused = input_data[f"{self.pathway_name}_energy_unused"]

        # first lets initialize the output data with mean mfsp components by parsing resources and processes
        # Prepare outputs
        output_data = {k: optional_nan_series.copy() for k in self.output_names}

        # First lets compute the core mfsp
        for year, needed_capacity in energy_production_commissioned.items():
            # Get the technical inputs
            private_discount_rate = _get_value_for_year(
                input_data.get("private_discount_rate"), year, 0.0
            )
            lifespan = _get_value_for_year(
                input_data.get(f"{self.pathway_name}_eis_plant_lifespan"), year, 25
            )
            construction_time = _get_value_for_year(
                input_data.get(f"{self.pathway_name}_eis_construction_time"), year, 3
            )
            plant_load_factor = _get_value_for_year(
                input_data.get(f"{self.pathway_name}_eis_plant_load_factor"), year, 1
            )

            # plant production is potentially evaluated beyond scenario end year
            vintage_indexes = range(year, year + lifespan)
            vintage_mfsp = pd.Series(np.nan, index=vintage_indexes)
            if (
                energy_consumption[year] > 0
                and needed_capacity <= 0
                and self.compute_abatement_cost
                and not self.compute_all_years
            ):
                warnings.warn(
                    f"\n⚠️ For {self.pathway_name}, no plants commissioned in {year}. Unable to compute "
                    f"CAC: compute_all_years = False. Set it true to avoid NaN values in the MACC for this year."
                )
            if needed_capacity > 0 or self.compute_all_years:
                if needed_capacity < 0:
                    warnings.warn(
                        f"Negative needed capacity for {self.pathway_name} in year {year}. "
                        "This is not expected despite the compute_all_years option being set to True."
                    )
                # relative contibution of the vintage
                relative_share = needed_capacity / (energy_consumption + energy_unused)

                relative_share = relative_share.loc[year : year + lifespan - 1]

                # I -- First lets compute the core MFSP (no resources, no processes)
                # Get the inputs for the year
                capex = _get_value_for_year(
                    input_data.get(f"{self.pathway_name}_eis_capex"), year, 0.0
                )

                # get the plant load factor for the year: minimum of plant load factor and resource load factors
                # TODO what shall we do with processes LF? Uncoupling core and processes make sense in many cases.
                main_process_load_factor = plant_load_factor
                for key in input_data.get(f"{self.pathway_name}_resource_names", []):
                    if f"{key}_load_factor" in input_data:
                        resource_load_factor = _get_value_for_year(
                            input_data.get(f"{key}_load_factor"), year, 1.0
                        )
                        if resource_load_factor is not None:
                            main_process_load_factor = min(
                                main_process_load_factor, resource_load_factor
                            )

                # Compute the capital cost per unit of energy produced. Capex in €/(MJ/Year), mfsp capex in €/MJ
                mfsp_capex = (
                    self._spread_capital(capex, private_discount_rate, lifespan, construction_time)
                    / main_process_load_factor
                )

                capex_year = capex * needed_capacity
                output_data[f"{self.pathway_name}_capex_cost"].loc[
                    year - construction_time : year
                ] = _custom_series_addition(
                    output_data[f"{self.pathway_name}_capex_cost"].loc[
                        year - construction_time : year
                    ],
                    capex_year / construction_time / main_process_load_factor,
                )

                output_data[f"{self.pathway_name}_mean_unit_capex"].loc[
                    year : year + lifespan - 1
                ] = _custom_series_addition(
                    output_data[f"{self.pathway_name}_mean_unit_capex"].loc[
                        year : year + lifespan - 1
                    ],
                    mfsp_capex * relative_share,
                )

                # compyte the EIS unitary capex
                output_data[f"{self.pathway_name}_vintage_unit_capex"].loc[year] = mfsp_capex

                # As var opex is in € per MJ we can directly get it
                variable_opex = _get_value_for_year(
                    input_data.get(f"{self.pathway_name}_eis_variable_opex"), year, 0.0
                )
                output_data[f"{self.pathway_name}_mean_unit_variable_opex"].loc[
                    year : year + lifespan - 1
                ] = _custom_series_addition(
                    output_data[f"{self.pathway_name}_mean_unit_variable_opex"].loc[
                        year : year + lifespan - 1
                    ],
                    variable_opex * relative_share,
                )

                # compyte the EIS variable opex --> No need, directly from input eis_variable_opex
                output_data[f"{self.pathway_name}_vintage_unit_variable_opex"].loc[year] = (
                    variable_opex
                )

                # As fixed opex is in €/year for a plant of 1 MJ/year, we can directly get it in €/MJ
                fixed_opex = (
                    _get_value_for_year(
                        input_data.get(f"{self.pathway_name}_eis_fixed_opex"), year, 0.0
                    )
                    / main_process_load_factor
                )
                output_data[f"{self.pathway_name}_mean_unit_fixed_opex"].loc[
                    year : year + lifespan - 1
                ] = _custom_series_addition(
                    output_data[f"{self.pathway_name}_mean_unit_fixed_opex"].loc[
                        year : year + lifespan - 1
                    ],
                    fixed_opex * relative_share,
                )

                # compyte the EIS fixed opex
                output_data[f"{self.pathway_name}_vintage_unit_fixed_opex"].loc[year] = fixed_opex

                vintage_mfsp = _custom_series_addition(
                    vintage_mfsp, mfsp_capex + fixed_opex + variable_opex
                )

                output_data[f"{self.pathway_name}_mean_mfsp_without_resource"].loc[
                    year : year + lifespan - 1
                ] = _custom_series_addition(
                    output_data[f"{self.pathway_name}_mean_mfsp_without_resource"].loc[
                        year : year + lifespan - 1
                    ],
                    vintage_mfsp * relative_share,
                )

                # II -- Now lets get the resources as in TopDownCost model
                for key in self.resource_keys:
                    # get the specific consumption of the resource
                    specific_consumption = _get_value_for_year(
                        input_data.get(
                            f"{self.pathway_name}_eis_resource_specific_consumption_{key}"
                        ),
                        year,
                        None,
                    )

                    if specific_consumption is not None:
                        resource_price = input_data.get(f"{key}_cost", optional_nan_series.copy())

                        # cast mfsp_resource to a series with the same index as
                        # vintage_mfsp by keeping correct values (<end year) extending last year value to the end of the vintage_mfsp
                        mfsp_resource = pd.Series(
                            [
                                resource_price[year] * specific_consumption
                                if year <= self.end_year and year in resource_price.index
                                else resource_price.iloc[-1] * specific_consumption
                                for year in vintage_mfsp.index
                            ],
                            index=vintage_mfsp.index,
                        )

                        vintage_mfsp = _custom_series_addition(vintage_mfsp, mfsp_resource)

                        # Store the resource cost in the output data
                        output_data[
                            f"{self.pathway_name}_excluding_processes_{key}_mean_unit_cost"
                        ].loc[year : year + lifespan - 1] = _custom_series_addition(
                            output_data[
                                f"{self.pathway_name}_excluding_processes_{key}_mean_unit_cost"
                            ].loc[year : year + lifespan - 1],
                            mfsp_resource * relative_share,
                        )

                        # compyte the EIS resource cost (at first year energy cost)
                        output_data[
                            f"{self.pathway_name}_excluding_processes_{key}_vintage_unit_cost"
                        ].loc[year] = mfsp_resource[year]

                    # get processes that use this resource
                    for process_key in self.process_keys:
                        specific_consumption = _get_value_for_year(
                            input_data.get(
                                f"{process_key}_eis_resource_specific_consumption_{key}"
                            ),
                            year,
                            None,
                        )

                        if specific_consumption is not None:
                            process_ressource_price = input_data.get(
                                f"{key}_cost", optional_nan_series.copy()
                            )
                            # cast mfsp_resource to a series with the same index as
                            # vintage_mfsp by keeping correct values (<end year) extending last year value to the end of the vintage_mfsp
                            mfsp_process_ressource = pd.Series(
                                [
                                    process_ressource_price[year] * specific_consumption
                                    if year <= self.end_year
                                    and year in process_ressource_price.index
                                    else process_ressource_price.iloc[-1] * specific_consumption
                                    for year in vintage_mfsp.index
                                ],
                                index=vintage_mfsp.index,
                            )

                            vintage_mfsp = _custom_series_addition(
                                vintage_mfsp, mfsp_process_ressource
                            )

                            # Store the resource cost in the output data
                            output_data[
                                f"{self.pathway_name}_{process_key}_{key}_mean_unit_cost"
                            ].loc[year : year + lifespan - 1] = _custom_series_addition(
                                output_data[
                                    f"{self.pathway_name}_{process_key}_{key}_mean_unit_cost"
                                ].loc[year : year + lifespan - 1],
                                mfsp_process_ressource * relative_share,
                            )

                            # compyte the EIS resource cost (at first year energy cost)
                            output_data[
                                f"{self.pathway_name}_{process_key}_{key}_vintage_unit_cost"
                            ].loc[year] = mfsp_process_ressource[year]

                # III -- Now lets get the processes
                for process_key in self.process_keys:
                    process_capex = _get_value_for_year(
                        input_data.get(f"{process_key}_eis_capex"), year, 0.0
                    )
                    process_lifespan = _get_value_for_year(
                        input_data.get(f"{process_key}_eis_plant_lifespan"), year, 25
                    )
                    process_construction_time = _get_value_for_year(
                        input_data.get(f"{process_key}_eis_construction_time"), year, 3.0
                    )
                    process_load_factor = _get_value_for_year(
                        input_data.get(f"{process_key}_eis_plant_load_factor"), year, 1.0
                    )
                    # get the process load factor for the year: minimum of process load factor and resource load factors
                    for key in input_data.get(f"{process_key}_resource_names", []):
                        if f"{key}_load_factor" in input_data:
                            resource_load_factor = _get_value_for_year(
                                input_data.get(f"{key}_load_factor"), year, 1.0
                            )
                            if resource_load_factor is not None:
                                process_load_factor = min(process_load_factor, resource_load_factor)
                    # Compute the capital cost per unit of energy produced for the process
                    mfsp_capex_process = (
                        self._spread_capital(
                            process_capex,
                            private_discount_rate,
                            process_lifespan,
                            process_construction_time,
                        )
                        / process_load_factor
                    )

                    output_data[f"{self.pathway_name}_{process_key}_capex_cost"].loc[
                        year - process_construction_time : year
                    ] = _custom_series_addition(
                        output_data[f"{self.pathway_name}_{process_key}_capex_cost"].loc[
                            year - process_construction_time : year
                        ],
                        process_capex * needed_capacity / construction_time / process_load_factor,
                    )

                    # Get the variable and fixed opex for the process
                    variable_opex_process = _get_value_for_year(
                        input_data.get(f"{process_key}_eis_variable_opex"),
                        year,
                        0.0,
                    )
                    fixed_opex_process = (
                        _get_value_for_year(
                            input_data.get(f"{process_key}_eis_fixed_opex"),
                            year,
                            0.0,
                        )
                        / process_load_factor
                    )
                    # Compute the MFSP for the process
                    mfsp_process = mfsp_capex_process + variable_opex_process + fixed_opex_process
                    # Add the MFSP for the process to the pathway MFSP
                    vintage_mfsp = _custom_series_addition(vintage_mfsp, mfsp_process)
                    # Store the process cost in the output data
                    output_data[
                        f"{self.pathway_name}_{process_key}_mean_unit_cost_without_resources"
                    ].loc[year : year + process_lifespan] = _custom_series_addition(
                        output_data[
                            f"{self.pathway_name}_{process_key}_mean_unit_cost_without_resources"
                        ].loc[year : year + process_lifespan],
                        mfsp_process * relative_share,
                    )
                    output_data[f"{self.pathway_name}_{process_key}_mean_unit_capex"].loc[
                        year : year + lifespan - 1
                    ] = _custom_series_addition(
                        output_data[f"{self.pathway_name}_{process_key}_mean_unit_capex"].loc[
                            year : year + lifespan - 1
                        ],
                        mfsp_capex_process * relative_share,
                    )
                    # compyte the EIS unitary capex
                    output_data[f"{self.pathway_name}_{process_key}_vintage_unit_capex"].loc[
                        year
                    ] = mfsp_capex_process

                    output_data[f"{self.pathway_name}_{process_key}_mean_unit_fixed_opex"].loc[
                        year : year + lifespan - 1
                    ] = _custom_series_addition(
                        output_data[f"{self.pathway_name}_{process_key}_mean_unit_fixed_opex"].loc[
                            year : year + lifespan - 1
                        ],
                        fixed_opex_process * relative_share,
                    )
                    # compyte the EIS fixed opex
                    output_data[f"{self.pathway_name}_{process_key}_vintage_unit_fixed_opex"].loc[
                        year
                    ] = fixed_opex_process

                    output_data[f"{self.pathway_name}_{process_key}_mean_unit_variable_opex"].loc[
                        year : year + lifespan - 1
                    ] = _custom_series_addition(
                        output_data[
                            f"{self.pathway_name}_{process_key}_mean_unit_variable_opex"
                        ].loc[year : year + lifespan - 1],
                        variable_opex_process * relative_share,
                    )

                    # compyte the EIS variable opex
                    output_data[
                        f"{self.pathway_name}_{process_key}_vintage_unit_variable_opex"
                    ].loc[year] = variable_opex_process

                output_data[f"{self.pathway_name}_mean_mfsp"].loc[year : year + lifespan - 1] = (
                    _custom_series_addition(
                        output_data[f"{self.pathway_name}_mean_mfsp"].loc[
                            year : year + lifespan - 1
                        ],
                        vintage_mfsp * relative_share,
                    )
                )

                # marginal mfsp: is the new vintage the marginal one at some point of the scenario?
                # Slice the relevant part
                target = output_data[f"{self.pathway_name}_marginal_mfsp"].loc[
                    year : year + lifespan - 1
                ]
                # Find common indices
                common_index = target.index.intersection(vintage_mfsp.index)
                # Align both Series
                target_common = target.loc[common_index]
                vintage_common = vintage_mfsp.loc[common_index]
                # Build mask:
                # (1) vintage > target
                # (2) or target is NaN and vintage is not NaN
                mask = (vintage_common > target_common) | (
                    target_common.isna() & vintage_common.notna()
                )
                # Apply the update
                output_data[f"{self.pathway_name}_marginal_mfsp"].loc[common_index] = (
                    target_common.where(~mask, vintage_common)
                )

                # compute discounted costs if necessary
                if self.compute_abatement_cost:
                    if vintage_mfsp.notna().any():
                        discounted_mfsp = self._unitary_cumulative_discounted_costs_vintage(
                            mfsp_series=vintage_mfsp,
                            year=year,
                            plant_lifespan=lifespan,
                            discount_rate=input_data["social_discount_rate"],
                        )
                    else:
                        discounted_mfsp = np.NaN
                    output_data[f"{self.pathway_name}_lifespan_unitary_discounted_costs"][year] = (
                        discounted_mfsp
                    )

        ### STEP 2: add taxes and subsidies like in TopDownCost model
        # Only pathway subsidies and taxes are considered here, not resources or processes taxes

        pathway_unit_subsidy_without_resource = input_data.get(
            f"{self.pathway_name}_mean_unit_subsidy_without_resource", optional_nan_series.copy()
        )

        pathway_unit_tax_without_resource = input_data.get(
            f"{self.pathway_name}_mean_unit_tax_without_resource", optional_nan_series.copy()
        )

        # Avoiding adding nans if subsidies and taxes defined for a shorter period of time than the mfsp
        pathway_net_mfsp_without_carbon_tax = _custom_series_addition(
            _custom_series_addition(
                output_data[f"{self.pathway_name}_mean_mfsp"], pathway_unit_tax_without_resource
            ),
            -pathway_unit_subsidy_without_resource,
        )

        # Handle possible differential carbon_tax
        if f"{self.pathway_name}_carbon_tax" in input_data:
            carbon_tax = (
                input_data[f"{self.pathway_name}_carbon_tax"] / 1000
            )  # converted to €/kgCO2
        else:
            carbon_tax = input_data["carbon_tax"] / 1000  # converted to €/kgCO2

        emission_factor = (
            input_data[f"{self.pathway_name}_mean_co2_emission_factor"] / 1000
        )  # converted to kgCO2/MJ
        pathway_unit_carbon_tax = carbon_tax * emission_factor

        if f"{self.pathway_name}_vintage_eis_co2_emission_factor" in input_data:
            vintage_eis_carbon_tax = (
                input_data[f"{self.pathway_name}_vintage_eis_co2_emission_factor"]
                / 1000
                * carbon_tax
            )
            output_data[f"{self.pathway_name}_vintage_eis_carbon_tax"] = vintage_eis_carbon_tax

        pathway_net_mfsp = _custom_series_addition(
            pathway_net_mfsp_without_carbon_tax, pathway_unit_carbon_tax
        )

        output_data.update(
            {
                f"{self.pathway_name}_net_mfsp_without_carbon_tax": pathway_net_mfsp_without_carbon_tax,
                f"{self.pathway_name}_net_mfsp": pathway_net_mfsp,
                f"{self.pathway_name}_mean_unit_tax": pathway_unit_tax_without_resource,
                f"{self.pathway_name}_mean_unit_carbon_tax": pathway_unit_carbon_tax,
                f"{self.pathway_name}_mean_unit_subsidy": pathway_unit_subsidy_without_resource,
            }
        )

        # Store the results in the df and retun

        self._store_outputs(output_data)

        return output_data

    def _jax_vintage_values(self, value, vintage_positions, default):
        """Per-vintage value of a technical input, mirroring :func:`_get_value_for_year`."""
        n_vintages = vintage_positions.shape[0]
        if value is None:
            return None if default is None else jnp.full(n_vintages, float(default))
        value = jnp.asarray(value)
        if value.ndim == 0:
            return jnp.full(n_vintages, value)
        picked = value[vintage_positions]
        if default is None:
            return picked
        return jnp.where(jnp.isnan(picked), default, picked)

    @staticmethod
    def _jax_spread_capital(capex, private_discount_rate, lifespan, construction_time):
        """JAX form of :meth:`_spread_capital`, with the zero-rate case selected by value.

        The discount rate is a discipline input, so the ``!= 0`` test cannot be a
        Python branch; the geometric-series branch is evaluated on a guarded rate
        so a zero rate does not produce a NaN derivative.
        """
        rate = jnp.asarray(private_discount_rate, dtype=jnp.float64)
        non_zero = rate != 0.0
        safe_rate = jnp.where(non_zero, rate, 1.0)
        term = 1.0 / (1.0 + safe_rate)

        capital_cost_npv = capex / construction_time * (1.0 - term**construction_time) / (
            1.0 - term
        )
        total_actualised_production = (
            term**construction_time * (1.0 - term**lifespan) / (1.0 - term)
        )
        return jnp.where(
            non_zero, capital_cost_npv / total_actualised_production, capex / lifespan
        )

    def jax_compute(self, input_data) -> dict:
        """JAX version of :meth:`compute` (same contract, pure jax.numpy).

        Like the environmental bottom-up model, the per-vintage pandas loop
        becomes a (vintage, age) grid scattered back onto the model years, with
        ``_custom_series_addition`` expressed as a NaN-aware accumulation so the
        NaN pattern of every output is preserved.
        """
        pathway = self.pathway_name
        n_years = len(years_index(self))
        nan_series = jnp.full(n_years, jnp.nan)
        output_data = {name: nan_series for name in self.output_names}

        energy_production_commissioned = jnp.asarray(
            input_data[f"{pathway}_energy_production_commissioned"]
        )
        energy_consumption = jnp.asarray(input_data[f"{pathway}_energy_consumption"])
        energy_unused = jnp.asarray(input_data[f"{pathway}_energy_unused"])

        first_vintage = year_pos(self, self.prospection_start_year)
        vintage_positions = jnp.arange(first_vintage, n_years)
        n_vintages = n_years - first_vintage
        needed_capacity = energy_production_commissioned[first_vintage:]

        def vintage_values(name, default):
            return self._jax_vintage_values(input_data.get(name), vintage_positions, default)

        def static_year_value(name, default):
            """Plant design parameter frozen over the horizon (window lengths)."""
            return _get_value_for_year(
                input_data.get(name), self.prospection_start_year, default
            )

        lifespan = int(static_year_value(f"{pathway}_eis_plant_lifespan", 25))
        construction_time = static_year_value(f"{pathway}_eis_construction_time", 3)

        private_discount_rate = vintage_values("private_discount_rate", 0.0)
        plant_load_factor = vintage_values(f"{pathway}_eis_plant_load_factor", 1.0)

        # Operating window of each vintage.
        ages = jnp.arange(lifespan)
        target = vintage_positions[:, None] + ages[None, :]
        inside = target < n_years
        target_clamped = jnp.minimum(target, n_years - 1)

        if self.compute_all_years:
            active = jnp.ones(n_vintages, dtype=bool)
        else:
            active = needed_capacity > 0

        def masked(grid):
            return jnp.where(active[:, None], grid, jnp.nan)

        def scatter(grid, positions, valid):
            """NaN-aware accumulation of a (vintage, age) grid onto the model years."""
            contributing = valid & ~jnp.isnan(grid)
            flat = positions.ravel()
            total = jnp.zeros(n_years).at[flat].add(
                jnp.where(contributing, jnp.nan_to_num(grid), 0.0).ravel()
            )
            count = jnp.zeros(n_years).at[flat].add(
                contributing.ravel().astype(jnp.float64)
            )
            return jnp.where(count > 0, total, jnp.nan)

        def scatter_operating(grid):
            return scatter(masked(grid), target_clamped, inside)

        def on_commissioning_year(values):
            """Place one value per vintage on its own commissioning year."""
            return jnp.concatenate(
                [jnp.full(first_vintage, jnp.nan), jnp.where(active, values, jnp.nan)]
            )

        def held_over_window(series):
            """A model-year series read over each vintage window, held past end_year."""
            return jnp.asarray(series)[target_clamped]

        # Share of the annual production carried by each vintage.
        relative_share = jnp.where(
            inside,
            needed_capacity[:, None] / (energy_consumption + energy_unused)[target_clamped],
            jnp.nan,
        )

        # --- I: core MFSP (no resources, no processes) ------------------------
        capex = vintage_values(f"{pathway}_eis_capex", 0.0)

        main_process_load_factor = plant_load_factor
        for key in input_data.get(f"{pathway}_resource_names", []):
            if f"{key}_load_factor" in input_data:
                main_process_load_factor = jnp.minimum(
                    main_process_load_factor, vintage_values(f"{key}_load_factor", 1.0)
                )

        mfsp_capex = (
            self._jax_spread_capital(
                capex, private_discount_rate, lifespan, construction_time
            )
            / main_process_load_factor
        )

        # Capex is spread backwards over the construction period.
        construction_ages = jnp.arange(int(construction_time) + 1)
        construction_target = vintage_positions[:, None] - construction_ages[None, :]
        construction_valid = construction_target >= 0
        construction_target = jnp.maximum(construction_target, 0)
        capex_year = capex * needed_capacity
        output_data[f"{pathway}_capex_cost"] = scatter(
            jnp.where(
                active[:, None],
                jnp.broadcast_to(
                    (capex_year / construction_time / main_process_load_factor)[:, None],
                    construction_target.shape,
                ),
                jnp.nan,
            ),
            construction_target,
            construction_valid,
        )

        output_data[f"{pathway}_mean_unit_capex"] = scatter_operating(
            mfsp_capex[:, None] * relative_share
        )
        output_data[f"{pathway}_vintage_unit_capex"] = on_commissioning_year(mfsp_capex)

        variable_opex = vintage_values(f"{pathway}_eis_variable_opex", 0.0)
        output_data[f"{pathway}_mean_unit_variable_opex"] = scatter_operating(
            variable_opex[:, None] * relative_share
        )
        output_data[f"{pathway}_vintage_unit_variable_opex"] = on_commissioning_year(
            variable_opex
        )

        fixed_opex = vintage_values(f"{pathway}_eis_fixed_opex", 0.0) / main_process_load_factor
        output_data[f"{pathway}_mean_unit_fixed_opex"] = scatter_operating(
            fixed_opex[:, None] * relative_share
        )
        output_data[f"{pathway}_vintage_unit_fixed_opex"] = on_commissioning_year(fixed_opex)

        vintage_mfsp = jnp.broadcast_to(
            (mfsp_capex + fixed_opex + variable_opex)[:, None], target.shape
        ).astype(jnp.float64)
        output_data[f"{pathway}_mean_mfsp_without_resource"] = scatter_operating(
            vintage_mfsp * relative_share
        )

        # --- II: resources ----------------------------------------------------
        for key in self.resource_keys:
            resource_price = input_data.get(f"{key}_cost")
            price_over_window = (
                jnp.full(target.shape, jnp.nan)
                if resource_price is None
                else held_over_window(resource_price)
            )

            specific_consumption = vintage_values(
                f"{pathway}_eis_resource_specific_consumption_{key}", None
            )
            if specific_consumption is not None:
                mfsp_resource = specific_consumption[:, None] * price_over_window
                vintage_mfsp = jax_nan_add(vintage_mfsp, mfsp_resource)
                output_data[f"{pathway}_excluding_processes_{key}_mean_unit_cost"] = (
                    scatter_operating(mfsp_resource * relative_share)
                )
                output_data[f"{pathway}_excluding_processes_{key}_vintage_unit_cost"] = (
                    on_commissioning_year(mfsp_resource[:, 0])
                )

            for process_key in self.process_keys:
                process_specific_consumption = vintage_values(
                    f"{process_key}_eis_resource_specific_consumption_{key}", None
                )
                if process_specific_consumption is None:
                    continue
                mfsp_process_resource = process_specific_consumption[:, None] * price_over_window
                vintage_mfsp = jax_nan_add(vintage_mfsp, mfsp_process_resource)
                output_data[f"{pathway}_{process_key}_{key}_mean_unit_cost"] = scatter_operating(
                    mfsp_process_resource * relative_share
                )
                output_data[f"{pathway}_{process_key}_{key}_vintage_unit_cost"] = (
                    on_commissioning_year(mfsp_process_resource[:, 0])
                )

        # --- III: processes ---------------------------------------------------
        for process_key in self.process_keys:
            process_capex = vintage_values(f"{process_key}_eis_capex", 0.0)
            process_lifespan = int(static_year_value(f"{process_key}_eis_plant_lifespan", 25))
            process_construction_time = static_year_value(
                f"{process_key}_eis_construction_time", 3.0
            )
            process_load_factor = vintage_values(f"{process_key}_eis_plant_load_factor", 1.0)
            for key in input_data.get(f"{process_key}_resource_names", []):
                if f"{key}_load_factor" in input_data:
                    process_load_factor = jnp.minimum(
                        process_load_factor, vintage_values(f"{key}_load_factor", 1.0)
                    )

            mfsp_capex_process = (
                self._jax_spread_capital(
                    process_capex,
                    private_discount_rate,
                    process_lifespan,
                    process_construction_time,
                )
                / process_load_factor
            )

            process_construction_ages = jnp.arange(int(process_construction_time) + 1)
            process_construction_target = (
                vintage_positions[:, None] - process_construction_ages[None, :]
            )
            process_construction_valid = process_construction_target >= 0
            process_construction_target = jnp.maximum(process_construction_target, 0)
            # Note: the pandas version divides the process capex by the pathway's
            # construction_time, not the process one; kept as is.
            output_data[f"{pathway}_{process_key}_capex_cost"] = scatter(
                jnp.where(
                    active[:, None],
                    jnp.broadcast_to(
                        (
                            process_capex
                            * needed_capacity
                            / construction_time
                            / process_load_factor
                        )[:, None],
                        process_construction_target.shape,
                    ),
                    jnp.nan,
                ),
                process_construction_target,
                process_construction_valid,
            )

            variable_opex_process = vintage_values(f"{process_key}_eis_variable_opex", 0.0)
            fixed_opex_process = (
                vintage_values(f"{process_key}_eis_fixed_opex", 0.0) / process_load_factor
            )
            mfsp_process = mfsp_capex_process + variable_opex_process + fixed_opex_process
            vintage_mfsp = jax_nan_add(vintage_mfsp, mfsp_process[:, None])

            # This one spans process_lifespan + 1 years, unlike the other windows.
            process_ages = jnp.arange(process_lifespan + 1)
            process_target = vintage_positions[:, None] + process_ages[None, :]
            process_inside = process_target < n_years
            process_target_clamped = jnp.minimum(process_target, n_years - 1)
            process_relative_share = jnp.where(
                process_inside,
                needed_capacity[:, None]
                / (energy_consumption + energy_unused)[process_target_clamped],
                jnp.nan,
            )
            output_data[f"{pathway}_{process_key}_mean_unit_cost_without_resources"] = scatter(
                jnp.where(
                    active[:, None], mfsp_process[:, None] * process_relative_share, jnp.nan
                ),
                process_target_clamped,
                process_inside,
            )

            output_data[f"{pathway}_{process_key}_mean_unit_capex"] = scatter_operating(
                mfsp_capex_process[:, None] * relative_share
            )
            output_data[f"{pathway}_{process_key}_vintage_unit_capex"] = on_commissioning_year(
                mfsp_capex_process
            )
            output_data[f"{pathway}_{process_key}_mean_unit_fixed_opex"] = scatter_operating(
                fixed_opex_process[:, None] * relative_share
            )
            output_data[f"{pathway}_{process_key}_vintage_unit_fixed_opex"] = (
                on_commissioning_year(fixed_opex_process)
            )
            output_data[f"{pathway}_{process_key}_mean_unit_variable_opex"] = scatter_operating(
                variable_opex_process[:, None] * relative_share
            )
            output_data[f"{pathway}_{process_key}_vintage_unit_variable_opex"] = (
                on_commissioning_year(variable_opex_process)
            )

        output_data[f"{pathway}_mean_mfsp"] = scatter_operating(vintage_mfsp * relative_share)

        # The marginal MFSP keeps, for each year, the most expensive vintage still
        # operating; the pandas `where` update is a NaN-aware running maximum.
        marginal_grid = masked(jnp.where(inside, vintage_mfsp, jnp.nan))
        marginal_contributing = ~jnp.isnan(marginal_grid)
        marginal_flat = target_clamped.ravel()
        marginal_max = jnp.full(n_years, -jnp.inf).at[marginal_flat].max(
            jnp.where(marginal_contributing, marginal_grid, -jnp.inf).ravel()
        )
        output_data[f"{pathway}_marginal_mfsp"] = jnp.where(
            jnp.isfinite(marginal_max), marginal_max, jnp.nan
        )

        if self.compute_abatement_cost:
            discount_rate = input_data["social_discount_rate"]
            # Past end_year the vintage keeps the cost of the last year of its
            # own window (the pandas `.iloc[-1]`), not the cost at end_year.
            held_cost = jnp.where(inside, vintage_mfsp, vintage_mfsp[:, -1][:, None])
            discount = (1.0 + discount_rate) ** (-ages)
            has_value = jnp.any(~jnp.isnan(vintage_mfsp), axis=1) & active
            discounted = jnp.where(
                has_value, jnp.sum(held_cost * discount[None, :], axis=1), jnp.nan
            )
            output_data[f"{pathway}_lifespan_unitary_discounted_costs"] = jnp.concatenate(
                [jnp.full(first_vintage, jnp.nan), discounted]
            )

        # --- STEP 2: taxes and subsidies --------------------------------------
        pathway_unit_subsidy_without_resource = jnp.asarray(
            input_data.get(f"{pathway}_mean_unit_subsidy_without_resource", nan_series)
        )
        pathway_unit_tax_without_resource = jnp.asarray(
            input_data.get(f"{pathway}_mean_unit_tax_without_resource", nan_series)
        )

        pathway_net_mfsp_without_carbon_tax = jax_nan_add(
            jax_nan_add(output_data[f"{pathway}_mean_mfsp"], pathway_unit_tax_without_resource),
            -pathway_unit_subsidy_without_resource,
        )

        if f"{pathway}_carbon_tax" in input_data:
            carbon_tax = jnp.asarray(input_data[f"{pathway}_carbon_tax"]) / 1000.0
        else:
            carbon_tax = jnp.asarray(input_data["carbon_tax"]) / 1000.0

        emission_factor = (
            jnp.asarray(input_data[f"{pathway}_mean_co2_emission_factor"]) / 1000.0
        )
        pathway_unit_carbon_tax = carbon_tax * emission_factor

        if f"{pathway}_vintage_eis_co2_emission_factor" in input_data:
            output_data[f"{pathway}_vintage_eis_carbon_tax"] = (
                jnp.asarray(input_data[f"{pathway}_vintage_eis_co2_emission_factor"])
                / 1000.0
                * carbon_tax
            )

        output_data.update(
            {
                f"{pathway}_net_mfsp_without_carbon_tax": pathway_net_mfsp_without_carbon_tax,
                f"{pathway}_net_mfsp": jax_nan_add(
                    pathway_net_mfsp_without_carbon_tax, pathway_unit_carbon_tax
                ),
                f"{pathway}_mean_unit_tax": pathway_unit_tax_without_resource,
                f"{pathway}_mean_unit_carbon_tax": pathway_unit_carbon_tax,
                f"{pathway}_mean_unit_subsidy": pathway_unit_subsidy_without_resource,
            }
        )
        return output_data

    def _spread_capital(
        self,
        capex,
        private_discount_rate,
        lifespan,
        construction_time,
    ):
        """
        This function computes the capex share of the MFSP for a given plant, based on the inputs provided.
        """
        if private_discount_rate != 0:
            term = 1 / (1 + private_discount_rate)

            # Construction of the facility
            # The construction is supposed to span over x years, with a uniform cost repartition
            # NPV of the capital cost is now calculated as a geometric series instead of a loop
            # (possible as uniform cost repartition)
            capital_cost_npv = (
                capex / construction_time * (1 - term**construction_time) / (1 - term)
            )

            # Npv of the unitary production for the whole lifespan obtained by sum of geometric series
            # (possible as constant production)
            total_actualised_production = (
                term**construction_time * (1 - term**lifespan) / (1 - term)
            )

            capital_cost_lc = capital_cost_npv / total_actualised_production

        else:
            # unit production
            capital_cost_lc = capex / lifespan

        return capital_cost_lc

    def _unitary_cumulative_discounted_costs_vintage(
        self,
        mfsp_series,
        year,
        plant_lifespan,
        discount_rate,
    ):
        """
        Compute the discounted MFSP for a given vintage over its lifespan.
        """
        discounted_cumul_cost = 0.0
        for i in range(year, year + int(plant_lifespan)):
            if i <= self.end_year:
                cost = mfsp_series[i] if i in mfsp_series.index else mfsp_series.iloc[-1]
            else:
                cost = mfsp_series.iloc[-1]
            discounted_cumul_cost += cost / ((1 + discount_rate) ** (i - year))
        return discounted_cumul_cost

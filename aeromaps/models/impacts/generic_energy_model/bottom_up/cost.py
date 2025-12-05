"""
cost

======
Module to compute pathway mfsp and investments using the bottom-up techno-economic model.
"""

import warnings

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
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

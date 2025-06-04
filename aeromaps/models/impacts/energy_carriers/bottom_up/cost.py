import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.utils.functions import get_value_for_year


class BottomUpCost(AeroMAPSModel):
    """
    Bottom-up techno-economic cost model for a given pathway, based on annual plant additions.
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
            # TODO initialize with zeros instead of actual val?
            self.input_names[key] = val

        # 2. Set individual inputs, coming either from other models or from the yaml as well
        self.input_names.update(
            {
                f"{self.pathway_name}_energy_production_commissioned": pd.Series([0.0]),
                f"{self.pathway_name}_energy_consumption": pd.Series([0.0]),
                "private_discount_rate": 0.0,
            }
        )

        self.output_names = {
            f"{self.pathway_name}_mfsp_without_resource": pd.Series([0.0]),
            f"{self.pathway_name}_unit_capex": pd.Series([0.0]),
            f"{self.pathway_name}_unit_fixed_opex": pd.Series([0.0]),
            f"{self.pathway_name}_unit_variable_opex": pd.Series([0.0]),
            f"{self.pathway_name}_capex_cost": pd.Series([0.0]),
        }

        # 3. Getting resources is a bit more complex as we need to get necessary resources for the pathway
        self.resource_keys = (
            configuration_data.get("inputs")
            .get("technical", {})
            .get(f"{self.pathway_name}_resource_names", [])
        ).copy()

        for key in self.resource_keys:
            # Outputs.
            self.output_names[f"{self.pathway_name}_excluding_processes_{key}_unit_cost"] = (
                pd.Series([0.0])
            )
            # self.output_names[self.pathway_name + "_excluding_processes_" + key + "_unit_tax"] = (
            #     pd.Series([0.0])
            # )
            # self.output_names[
            #     self.pathway_name + "_excluding_processes_" + key + "_unit_subsidy"
            # ] = pd.Series([0.0])

        self.process_keys = (
            configuration_data.get("inputs")
            .get("technical", {})
            .get(f"{self.pathway_name}_processes_names", [])
        ).copy()

        for process_key in self.process_keys:
            for key, val in processes_data[process_key].get("inputs").get("technical", {}).items():
                if key == f"{process_key}_resource_names":
                    self.input_names[key] = val
                    resources = (
                        processes_data[process_key]
                        .get("inputs")
                        .get("technical", {})
                        .get(f"{process_key}_resource_names", [])
                    ).copy()
                    self.resource_keys.extend(resources)
                    for resource in resources:
                        self.output_names[
                            f"{self.pathway_name}_{process_key}_{resource}_unit_cost"
                        ] = pd.Series([0.0])
                        # self.output_names[
                        #     self.pathway_name + "_" + process_key + "_" + resource + "_unit_tax"
                        # ] = pd.Series([0.0])
                        # self.output_names[
                        #     self.pathway_name + "_" + process_key + "_" + resource + "_unit_subsidy"
                        # ] = pd.Series([0.0])
                else:
                    # TODO initialize with zeros instead of actual val?
                    self.input_names[key] = val

            for key, val in processes_data[process_key].get("inputs").get("economics", {}).items():
                # TODO initialize with zeros instead of actual val?
                self.input_names[key] = val
            self.output_names[f"{self.pathway_name}_{process_key}_without_resources_unit_cost"] = (
                pd.Series([0.0])
            )
            self.output_names[f"{self.pathway_name}_{process_key}_unit_capex"] = pd.Series([0.0])
            self.output_names[f"{self.pathway_name}_{process_key}_capex_cost"] = pd.Series([0.0])
            self.output_names[f"{self.pathway_name}_{process_key}_unit_fixed_opex"] = pd.Series(
                [0.0]
            )
            self.output_names[f"{self.pathway_name}_{process_key}_unit_variable_opex"] = pd.Series(
                [0.0]
            )

            # self.output_names[
            #     self.pathway_name + "_" + process_key + "_without_resources_unit_tax"
            # ] = pd.Series([0.0])
            # self.output_names[
            #     self.pathway_name + "_" + process_key + "_without_resources_unit_subsidy"
            # ] = pd.Series([0.0])

        # Getting unique resources
        self.resource_keys = list(set(self.resource_keys))

        # Adding resources-linked inputs and outputs
        # TODO specify eco/cost as for process
        for key in self.resource_keys:
            if f"{key}_cost" in resources_data[key]["specifications"]:
                self.input_names[f"{key}_cost"] = pd.Series([0.0])
            if f"{key}_load_factor" in resources_data[key]["specifications"]:
                self.input_names[f"{key}_load_factor"] = pd.Series([0.0])
            # if f"{key}_subsidy" in resources_data[key]["specifications"]:
            #     self.input_names[key + "_subsidy"] = pd.Series([0.0])
            # if f"{key}_tax" in resources_data[key]["specifications"]:
            #     self.input_names[key + "_tax"] = pd.Series([0.0])
            # Outputs.

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names.update(
            {
                f"{self.pathway_name}_net_mfsp_without_carbon_tax": pd.Series([0.0]),
                f"{self.pathway_name}_net_mfsp": pd.Series([0.0]),
                f"{self.pathway_name}_mfsp": pd.Series([0.0]),
                f"{self.pathway_name}_unit_tax": pd.Series([0.0]),
                f"{self.pathway_name}_unit_carbon_tax": pd.Series([0.0]),
                f"{self.pathway_name}_unit_subsidy": pd.Series([0.0]),
            }
        )

        # Ajoute la sortie pour le MFSP actualisé (discounted) uniquement si abatement cost activé
        if configuration_data.get("abatement_cost"):
            self.compute_abatement_cost = True
            self.output_names[f"{self.pathway_name}_lifespan_unitary_discounted_costs"] = pd.Series(
                [0.0]
            )
            self.input_names["social_discount_rate"] = 0.0
        else:
            self.compute_abatement_cost = False

    def compute(self, input_data) -> dict:
        optional_null_series = pd.Series(
            0.0, index=range(self.prospection_start_year, self.end_year + 1)
        )

        energy_production_commissioned = input_data[
            f"{self.pathway_name}_energy_production_commissioned"
        ]
        energy_consumption = input_data[f"{self.pathway_name}_energy_consumption"]

        indexes = range(self.prospection_start_year, self.end_year + 1)

        # plant_building_cost = pd.Series(np.zeros(len(indexes)), indexes)
        # pathway_total_cost = pd.Series(np.zeros(len(indexes)), indexes)

        # first lets initialize the output data with mean mfsp components by parsing resources and processes
        # Prepare outputs
        output_data = {k: pd.Series(0.0, index=indexes) for k in self.output_names}

        # First lets compute the core mfsp
        for year, needed_capacity in energy_production_commissioned.items():
            # Get the technical inputs
            private_discount_rate = get_value_for_year(
                input_data.get("private_discount_rate"), year, 0.0
            )
            lifespan = get_value_for_year(
                input_data.get(f"{self.pathway_name}_eis_plant_lifespan"), year, 25
            )
            construction_time = get_value_for_year(
                input_data.get(f"{self.pathway_name}_eis_construction_time"), year, 3
            )
            plant_load_factor = get_value_for_year(
                input_data.get(f"{self.pathway_name}_eis_plant_load_factor"), year, 1
            )

            # plant production is potentially evaluated beyond scenario end year
            vintage_indexes = range(year, year + lifespan + 1)
            vintage_mfsp = pd.Series(np.zeros(len(vintage_indexes)), vintage_indexes)
            if needed_capacity > 0:
                # relative contibution of the vintage
                relative_share = needed_capacity / energy_consumption
                relative_share = relative_share.loc[year : year + lifespan]

                # I -- First lets compute the core MFSP (no resources, no processes)
                # Get the inputs for the year
                capex = get_value_for_year(
                    input_data.get(f"{self.pathway_name}_eis_capex"), year, 0.0
                )

                # get the plant load factor for the year: minimum of plant load factor and resource load factors
                # TODO what shall we do with processes LF? Uncoupling core and processes make sense in many cases.
                main_process_load_factor = plant_load_factor
                for key in input_data.get(f"{self.pathway_name}_resource_names", []):
                    if f"{key}_load_factor" in input_data:
                        resource_load_factor = get_value_for_year(
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
                ] = capex_year / construction_time
                output_data[f"{self.pathway_name}_unit_capex"].loc[year : year + lifespan] += (
                    mfsp_capex * relative_share
                )

                # As var opex is in € per MJ we can directly get it
                variable_opex = get_value_for_year(
                    input_data.get(f"{self.pathway_name}_eis_variable_opex"), year, 0.0
                )
                output_data[f"{self.pathway_name}_unit_variable_opex"].loc[
                    year : year + lifespan
                ] += variable_opex * relative_share

                # As fixed opex is in €/year for a plant of 1 MJ/year, we can directly get it in €/MJ
                fixed_opex = (
                    get_value_for_year(
                        input_data.get(f"{self.pathway_name}_eis_fixed_opex"), year, 0.0
                    )
                    / main_process_load_factor
                )
                output_data[f"{self.pathway_name}_unit_fixed_opex"].loc[year : year + lifespan] += (
                    fixed_opex * relative_share
                )

                vintage_mfsp += mfsp_capex + fixed_opex + variable_opex

                output_data[f"{self.pathway_name}_mfsp_without_resource"].loc[
                    year : year + lifespan
                ] += vintage_mfsp * relative_share

                # II -- Now lets get the resources as in TopDownCost model
                for key in self.resource_keys:
                    # get the specific consumption of the resource
                    specific_consumption = get_value_for_year(
                        input_data.get(
                            f"{self.pathway_name}_eis_resource_specific_consumption_{key}"
                        ),
                        year,
                        None,
                    )

                    if specific_consumption is not None:
                        resource_price = input_data.get(f"{key}_cost", optional_null_series.copy())

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

                        vintage_mfsp = vintage_mfsp + mfsp_resource

                        # Store the resource cost in the output data
                        output_data[f"{self.pathway_name}_excluding_processes_{key}_unit_cost"].loc[
                            year : year + lifespan
                        ] += mfsp_resource * relative_share

                    # get processes that use this resource
                    for process_key in self.process_keys:
                        specific_consumption = get_value_for_year(
                            input_data.get(
                                f"{process_key}_eis_resource_specific_consumption_{key}"
                            ),
                            year,
                            None,
                        )

                        if specific_consumption is not None:
                            process_ressource_price = input_data.get(
                                f"{key}_cost", optional_null_series.copy()
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

                            vintage_mfsp = vintage_mfsp + mfsp_process_ressource

                            # Store the resource cost in the output data
                            output_data[f"{self.pathway_name}_{process_key}_{key}_unit_cost"].loc[
                                year : year + lifespan
                            ] += mfsp_process_ressource * relative_share

                # III -- Now lets get the processes
                for process_key in self.process_keys:
                    process_capex = get_value_for_year(
                        input_data.get(f"{process_key}_eis_capex"), year, 0.0
                    )
                    process_lifespan = get_value_for_year(
                        input_data.get(f"{process_key}_eis_plant_lifespan"), year, 25
                    )
                    process_construction_time = get_value_for_year(
                        input_data.get(f"{process_key}_eis_construction_time"), year, 3.0
                    )
                    process_load_factor = get_value_for_year(
                        input_data.get(f"{process_key}_eis_plant_load_factor"), year, 1.0
                    )
                    # get the process load factor for the year: minimum of process load factor and resource load factors
                    for key in input_data.get(f"{process_key}_resource_names", []):
                        if f"{key}_load_factor" in input_data:
                            resource_load_factor = get_value_for_year(
                                input_data.get(f"{key}_load_factor"), year, 1.0
                            )
                            if resource_load_factor is not None:
                                process_load_factor = min(process_load_factor, resource_load_factor)
                    # Compute the capital cost per unit of energy produced for the process
                    if process_capex is not None:
                        capex_process = (
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
                        ] = process_capex * needed_capacity / construction_time
                    else:
                        capex_process = 0.0
                    # Get the variable and fixed opex for the process
                    variable_opex_process = get_value_for_year(
                        input_data.get(f"{self.pathway_name}_{process_key}_eis_variable_opex"),
                        year,
                        0.0,
                    )
                    fixed_opex_process = (
                        get_value_for_year(
                            input_data.get(f"{self.pathway_name}_{process_key}_eis_fixed_opex"),
                            year,
                            0.0,
                        )
                        / process_load_factor
                    )
                    # Compute the MFSP for the process
                    mfsp_process = capex_process + variable_opex_process + fixed_opex_process
                    # Add the MFSP for the process to the pathway MFSP
                    vintage_mfsp = vintage_mfsp + mfsp_process
                    # Store the process cost in the output data
                    output_data[
                        f"{self.pathway_name}_{process_key}_without_resources_unit_cost"
                    ].loc[year : year + process_lifespan] += mfsp_process * relative_share
                    output_data[f"{self.pathway_name}_{process_key}_unit_capex"].loc[
                        year : year + lifespan
                    ] += capex_process * relative_share
                    output_data[f"{self.pathway_name}_{process_key}_unit_fixed_opex"].loc[
                        year : year + lifespan
                    ] += fixed_opex_process * relative_share
                    output_data[f"{self.pathway_name}_{process_key}_unit_variable_opex"].loc[
                        year : year + lifespan
                    ] += variable_opex_process * relative_share

                output_data[f"{self.pathway_name}_mfsp"].loc[year : year + lifespan] += (
                    vintage_mfsp * relative_share
                )

            # compute discounted costs if necessary
            if self.compute_abatement_cost:
                discounted_mfsp = self._cumulative_discounted_costs(
                    mfsp_series=vintage_mfsp,
                    year=year,
                    plant_lifespan=lifespan,
                    discount_rate=input_data["social_discount_rate"],
                )
                output_data[f"{self.pathway_name}_lifespan_unitary_discounted_costs"][year] += (
                    discounted_mfsp
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

    def _cumulative_discounted_costs(
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

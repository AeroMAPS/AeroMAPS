import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.utils.functions import get_value_for_year


class BottomUpEnvironmental(AeroMAPSModel):
    """
    Generic model for aviation energy carriers, relying on user's description of the carriers in the configuration file.
    """

    def __init__(
        self,
        name,
        configuration_data,
        resources_data,
        processes_data,
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
        # Get the name of the pathway
        self.pathway_name = configuration_data["name"]

        # Get the inputs from the configuration file: two options
        # 1. All inputs of a certain category in the yaml file
        for key, val in configuration_data.get("inputs").get("environmental", {}).items():
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
            }
        )

        # TODO find a better way to get the resource inputs ? Now better with the list(str) argument of each pathway .yaml
        # 3. Getting resources is a bit more complex as we need to get necessary resources for the pathway
        self.resource_keys = (
            configuration_data.get("inputs")
            .get("technical", {})
            .get(f"{self.pathway_name}_resource_names", [])
        )

        self.process_keys = (
            configuration_data.get("inputs")
            .get("technical", {})
            .get(f"{self.pathway_name}_processes_names", [])
        )

        # Adding resources-linked inputs and outputs
        for key in self.resource_keys:
            self.output_names[
                self.pathway_name + "_excluding_processes_" + key + "_co2_emission_factor"
            ] = pd.Series([0.0])
            self.output_names[
                self.pathway_name + "_excluding_processes_" + key + "_total_consumption"
            ] = pd.Series([0.0])
            self.output_names[
                self.pathway_name
                + "_excluding_processes_"
                + key
                + "_total_mobilised_with_selectivity"
            ] = pd.Series([0.0])

            self.output_names[self.pathway_name + "_" + key + "_total_consumption"] = pd.Series(
                [0.0]
            )
            self.output_names[
                self.pathway_name + "_" + key + "_total_mobilised_with_selectivity"
            ] = pd.Series([0.0])

        for process_key in self.process_keys:
            for key, val in processes_data[process_key].get("inputs").get("technical", {}).items():
                if key == f"{process_key}_resource_names":
                    self.input_names[key] = val
                    resources = (
                        processes_data[process_key]
                        .get("inputs")
                        .get("technical", {})
                        .get(f"{process_key}_resource_names", [])
                    )
                    self.resource_keys.extend(resources)
                    for resource in resources:
                        self.output_names[
                            self.pathway_name
                            + "_"
                            + process_key
                            + "_"
                            + resource
                            + "_co2_emission_factor"
                        ] = pd.Series([0.0])
                        self.output_names[
                            self.pathway_name
                            + "_"
                            + process_key
                            + "_"
                            + resource
                            + "_total_consumption"
                        ] = pd.Series([0.0])
                        self.output_names[
                            self.pathway_name
                            + "_"
                            + process_key
                            + "_"
                            + resource
                            + "_total_mobilised_with_selectivity"
                        ] = pd.Series([0.0])
                else:
                    # TODO initialize with zeros instead of actual val?
                    self.input_names[key] = val

            for key, val in processes_data[process_key].get("inputs").get("economics", {}).items():
                # TODO initialize with zeros instead of actual val?
                self.input_names[key] = val
            self.output_names[
                self.pathway_name + "_" + process_key + "_without_resources_co2_emission_factor"
            ] = pd.Series([0.0])

        # Getting unique resources
        self.resource_keys = list(set(self.resource_keys))

        for key in self.resource_keys:
            if f"{key}_co2_emission_factor" in resources_data[key]["specifications"]:
                self.input_names[key + "_co2_emission_factor"] = pd.Series([0.0])

            self.output_names[self.pathway_name + "_" + key + "_total_consumption"] = pd.Series(
                [0.0]
            )
            self.output_names[
                self.pathway_name + "_" + key + "_total_mobilised_with_selectivity"
            ] = pd.Series([0.0])

        # Fill in the other expected outputs with names from the compute method
        self.output_names.update(
            {
                self.pathway_name + "_co2_emission_factor": pd.Series([0.0]),
                self.pathway_name + "_total_co2_emissions": pd.Series([0.0]),
                # Base EF, added by hand
                self.pathway_name + "_co2_emission_factor_without_resource": pd.Series([0.0]),
            }
        )
        print(self.output_names)

    def compute(self, input_data) -> dict:
        """
        Compute the environmental impact of the energy carrier pathway.
        Each plant (vintage) is commissioned with the characteristics of its commissioning year,
        and its emissions are distributed over its lifespan, weighted by its share in annual production.
        """

        optional_null_series = pd.Series(
            0.0, index=range(self.prospection_start_year, self.end_year + 1)
        )
        # Get time index and basic parameters
        years = range(self.prospection_start_year, self.end_year + 1)

        energy_production_commissioned = input_data[
            f"{self.pathway_name}_energy_production_commissioned"
        ]
        energy_consumption = input_data[f"{self.pathway_name}_energy_consumption"]

        # Prepare outputs
        output_data = {k: pd.Series(0.0, index=years) for k in self.output_names}

        co2_emission_factor = optional_null_series.copy()

        # For each vintage, compute its emission factor and contribution
        for year, needed_capacity in energy_production_commissioned.items():
            lifespan = get_value_for_year(
                input_data.get(f"{self.pathway_name}_eis_lifespan"), year, 1
            )
            # The plant will operate from year to year+lifespan (or until end_year)
            vintage_indexes = range(year, year + lifespan)
            vintage_emission_factor = pd.Series(np.zeros(len(vintage_indexes)), vintage_indexes)
            if needed_capacity > 0:
                # relative contibution of the vintage
                relative_share = needed_capacity / energy_consumption
                relative_share = relative_share.loc[year : year + lifespan]

                # I -- First lets compute the core MFSP (no resources, no processes)
                # Get the inputs for the year
                core_emission_factor = get_value_for_year(
                    input_data.get(f"{self.pathway_name}_eis_co2_emission_factor_without_resource"),
                    year,
                    0.0,
                )
                kerosene_selectivity = get_value_for_year(
                    input_data.get(f"{self.pathway_name}_eis_kerosene_selectivity"), year, 1.0
                )

                vintage_emission_factor += core_emission_factor
                output_data[f"{self.pathway_name}_co2_emission_factor_without_resource"].loc[
                    vintage_indexes
                ] += core_emission_factor * relative_share

                # II) Now let's compute the emissions from resources that are linked to the pathway itself
                for key in self.resource_keys:
                    specific_consumption = get_value_for_year(
                        input_data.get(
                            self.pathway_name + "_eis_resource_specific_consumption_" + key
                        ),
                        year,
                        None,
                    )

                    total_ressource_consumption = optional_null_series.copy()
                    total_ressource_mobilised_with_selectivity = optional_null_series.copy()

                    if specific_consumption is not None:
                        resources_consumption = (
                            energy_production_commissioned[year] * specific_consumption
                        )
                        resources_consumption_with_selectivity = (
                            resources_consumption * kerosene_selectivity
                        )

                        total_ressource_consumption.loc[vintage_indexes] = resources_consumption
                        total_ressource_mobilised_with_selectivity.loc[vintage_indexes] = (
                            resources_consumption_with_selectivity
                        )

                        output_data[
                            self.pathway_name + "_excluding_processes_" + key + "_total_consumption"
                        ].loc[vintage_indexes] += resources_consumption
                        output_data[
                            self.pathway_name
                            + "_excluding_processes_"
                            + key
                            + "_total_mobilised_with_selectivity"
                        ].loc[vintage_indexes] += resources_consumption_with_selectivity

                        # Get the CO2 emission factor for the resource
                        unit_emissions = input_data.get(
                            key + "_co2_emission_factor", optional_null_series
                        )
                        # get resource emission per unit of energy
                        co2_emission_factor_ressource = specific_consumption * unit_emissions
                        vintage_emission_factor += co2_emission_factor_ressource
                        output_data[
                            self.pathway_name
                            + "_excluding_processes_"
                            + key
                            + "_co2_emission_factor"
                        ].loc[vintage_indexes] += co2_emission_factor_ressource * relative_share
                    # III) Now let's compute the emissions from processes that gets a ressource
                    for process_key in self.process_keys:
                        specific_consumption = get_value_for_year(
                            input_data.get(
                                process_key + "_eis_resource_specific_consumption_" + key
                            ),
                            year,
                            None,
                        )
                        if specific_consumption is not None:
                            resources_consumption = (
                                energy_production_commissioned[year] * specific_consumption
                            )
                            resources_consumption_with_selectivity = (
                                resources_consumption * kerosene_selectivity
                            )

                            total_ressource_consumption.loc[vintage_indexes] = resources_consumption
                            total_ressource_mobilised_with_selectivity.loc[vintage_indexes] = (
                                resources_consumption_with_selectivity
                            )

                            output_data[
                                self.pathway_name
                                + "_"
                                + process_key
                                + "_"
                                + key
                                + "_total_consumption"
                            ].loc[vintage_indexes] += resources_consumption
                            output_data[
                                self.pathway_name
                                + "_"
                                + process_key
                                + "_"
                                + key
                                + "_total_mobilised_with_selectivity"
                            ].loc[vintage_indexes] += resources_consumption_with_selectivity

                            # Get the CO2 emission factor for the resource
                            unit_emissions = input_data.get(
                                key + "_co2_emission_factor", optional_null_series
                            )
                            # get resource emission per unit of energy
                            co2_emission_factor_ressource = specific_consumption * unit_emissions
                            vintage_emission_factor += co2_emission_factor_ressource
                            output_data[
                                self.pathway_name
                                + "_"
                                + process_key
                                + "_"
                                + key
                                + "_co2_emission_factor"
                            ].loc[vintage_indexes] += co2_emission_factor_ressource * relative_share
                    # store the total consumption of the resource
                    output_data[self.pathway_name + "_" + key + "_total_consumption"].loc[
                        vintage_indexes
                    ] += total_ressource_consumption
                    output_data[
                        self.pathway_name + "_" + key + "_total_mobilised_with_selectivity"
                    ].loc[vintage_indexes] += total_ressource_mobilised_with_selectivity

                # IV) Now let's compute the emissions from processes themselves
                for process_key in self.process_keys:
                    # Get the inputs for the year
                    process_emission_factor = get_value_for_year(
                        input_data.get(process_key + "_eis_co2_emission_factor_without_resources"),
                        year,
                        0.0,
                    )
                    vintage_emission_factor += process_emission_factor
                    output_data[
                        self.pathway_name
                        + "_"
                        + process_key
                        + "_without_resources_co2_emission_factor"
                    ].loc[vintage_indexes] += process_emission_factor * relative_share

                # Compute the average emission factor from the vintage
                co2_emission_factor.loc[vintage_indexes] += vintage_emission_factor * relative_share

            # Store the emission factor
            output_data[f"{self.pathway_name}_co2_emission_factor"] = co2_emission_factor
            # Compute the total emissions from the vintage
            total_co2_emissions = energy_consumption * co2_emission_factor
            output_data[self.pathway_name + "_total_co2_emissions"] = total_co2_emissions

        self._store_outputs(output_data)
        return output_data

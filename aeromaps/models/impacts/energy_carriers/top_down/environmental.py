import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class TopDownEnvironmental(AeroMAPSModel):
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
        # Individual inputs defined in the yaml file
        # -- None
        # Individual inputs defined by EnergyUseChoice
        self.input_names[f"{self.pathway_name}_energy_consumption"] = pd.Series([0.0])

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
                f"{self.pathway_name}_excluding_processes_{key}_co2_emission_factor"
            ] = pd.Series([0.0])
            self.output_names[
                f"{self.pathway_name}_excluding_processes_{key}_total_consumption"
            ] = pd.Series([0.0])
            self.output_names[
                f"{self.pathway_name}_excluding_processes_{key}_total_mobilised_with_selectivity"
            ] = pd.Series([0.0])

            self.output_names[f"{self.pathway_name}_{key}_total_consumption"] = pd.Series([0.0])
            self.output_names[f"{self.pathway_name}_{key}_total_mobilised_with_selectivity"] = (
                pd.Series([0.0])
            )

        for process_key in self.process_keys:
            for key, val in processes_data[process_key].get("inputs").get("technical", {}).items():
                if key == f"{process_key}_resource_names":
                    resources = (
                        processes_data[process_key]
                        .get("inputs")
                        .get("technical", {})
                        .get(f"{process_key}_resource_names", [])
                    )
                    self.resource_keys.extend(resources)
                    for resource in resources:
                        self.output_names[
                            f"{self.pathway_name}_{process_key}_{resource}_co2_emission_factor"
                        ] = pd.Series([0.0])
                        self.output_names[
                            f"{self.pathway_name}_{process_key}_{resource}_total_consumption"
                        ] = pd.Series([0.0])
                        self.output_names[
                            f"{self.pathway_name}_{process_key}_{resource}_total_mobilised_with_selectivity"
                        ] = pd.Series([0.0])
                else:
                    # TODO initialize with zeros instead of actual val?
                    self.input_names[key] = val

            for key, val in processes_data[process_key].get("inputs").get("economics", {}).items():
                # TODO initialize with zeros instead of actual val?
                self.input_names[key] = val
            self.output_names[
                f"{self.pathway_name}_{process_key}_without_resources_co2_emission_factor"
            ] = pd.Series([0.0])

        # Getting unique resources
        self.resource_keys = list(set(self.resource_keys))

        for key in self.resource_keys:
            if f"{key}_co2_emission_factor" in resources_data[key]["specifications"]:
                self.input_names[f"{key}_co2_emission_factor"] = pd.Series([0.0])

            self.output_names[f"{self.pathway_name}_{key}_total_consumption"] = pd.Series([0.0])
            self.output_names[f"{self.pathway_name}_{key}_total_mobilised_with_selectivity"] = (
                pd.Series([0.0])
            )

        # Fill in the other expected outputs with names from the compute method
        self.output_names.update(
            {
                f"{self.pathway_name}_co2_emission_factor": pd.Series([0.0]),
                f"{self.pathway_name}_total_co2_emissions": pd.Series([0.0]),
            }
        )

    def compute(self, input_data) -> dict:
        output_data = {}
        optional_null_series = pd.Series(
            0.0, index=range(self.prospection_start_year, self.end_year + 1)
        )

        co2_emission_factor = input_data.get(
            f"{self.pathway_name}_co2_emission_factor_without_resource", optional_null_series
        )

        # Get the total energy consumption of the pathway
        energy_consumption = input_data[f"{self.pathway_name}_energy_consumption"]

        # Pathway selectivity
        pathway_kerosene_selectivity = input_data.get(
            f"{self.pathway_name}_kerosene_selectivity", 1.0
        )

        for key in self.resource_keys:
            # 1 ) --> pathway gets directly a resource
            specific_consumption = input_data.get(
                f"{self.pathway_name}_resource_specific_consumption_{key}", None
            )
            total_ressource_consumption = optional_null_series.copy()
            total_ressource_mobilised_with_selectivity = optional_null_series.copy()

            if specific_consumption is not None:
                ressource_consumption = energy_consumption * specific_consumption
                ressource_required_with_selectivity = (
                    ressource_consumption / pathway_kerosene_selectivity
                )
                total_ressource_consumption = total_ressource_consumption.add(
                    ressource_consumption, fill_value=0
                )
                total_ressource_mobilised_with_selectivity = (
                    total_ressource_mobilised_with_selectivity.add(
                        ressource_required_with_selectivity, fill_value=0
                    )
                )

                output_data[f"{self.pathway_name}_excluding_processes_{key}_total_consumption"] = (
                    ressource_consumption
                )
                output_data[
                    f"{self.pathway_name}_excluding_processes_{key}_total_mobilised_with_selectivity"
                ] = ressource_required_with_selectivity

                unit_emissions = input_data.get(f"{key}_co2_emission_factor", optional_null_series)
                # get resource emission per unit of energy
                co2_emission_factor_ressource = specific_consumption * unit_emissions

                output_data[
                    f"{self.pathway_name}_excluding_processes_{key}_co2_emission_factor"
                ] = co2_emission_factor_ressource
                co2_emission_factor = co2_emission_factor.add(
                    co2_emission_factor_ressource, fill_value=0
                )
            # 2 ) --> pathway gets a process that uses a resource
            for process_key in self.process_keys:
                specific_consumption = input_data.get(
                    f"{process_key}_resource_specific_consumption_{key}"
                )
                if specific_consumption is not None:
                    ressource_consumption = energy_consumption * specific_consumption
                    ressource_required_with_selectivity = (
                        ressource_consumption / pathway_kerosene_selectivity
                    )

                    total_ressource_consumption = total_ressource_consumption.add(
                        ressource_consumption, fill_value=0
                    )
                    total_ressource_mobilised_with_selectivity = (
                        total_ressource_mobilised_with_selectivity.add(
                            ressource_required_with_selectivity, fill_value=0
                        )
                    )

                    output_data[f"{self.pathway_name}_{process_key}_{key}_total_consumption"] = (
                        ressource_consumption
                    )
                    output_data[
                        f"{self.pathway_name}_{process_key}_{key}_total_mobilised_with_selectivity"
                    ] = ressource_required_with_selectivity

                    unit_emissions = input_data.get(
                        f"{key}_co2_emission_factor", optional_null_series
                    )
                    # get resource emission per unit of energy
                    co2_emission_factor_ressource = specific_consumption * unit_emissions

                    output_data[f"{self.pathway_name}_{process_key}_{key}_co2_emission_factor"] = (
                        co2_emission_factor_ressource
                    )
                    co2_emission_factor = co2_emission_factor.add(
                        co2_emission_factor_ressource, fill_value=0
                    )
            # Store the total resource consumption
            output_data[f"{self.pathway_name}_{key}_total_consumption"] = (
                total_ressource_consumption
            )

            output_data[f"{self.pathway_name}_{key}_total_mobilised_with_selectivity"] = (
                total_ressource_mobilised_with_selectivity
            )

        # 3 ) --> pathway gets a process that makes own emissions (besides resources)
        for process_key in self.process_keys:
            co2_emission_factor_process = input_data.get(
                f"{process_key}_co2_emission_factor_without_resource", optional_null_series
            )
            output_data[
                f"{self.pathway_name}_{process_key}_without_resources_co2_emission_factor"
            ] = co2_emission_factor_process

            co2_emission_factor = co2_emission_factor.add(co2_emission_factor_process)

        # Store the total CO2 emission factor in the dataframe
        output_data[f"{self.pathway_name}_co2_emission_factor"] = co2_emission_factor
        # Calculate the total CO2 emissions
        total_co2_emissions = energy_consumption * co2_emission_factor
        output_data[f"{self.pathway_name}_total_co2_emissions"] = total_co2_emissions

        self._store_outputs(output_data)

        return output_data

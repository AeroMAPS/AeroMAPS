import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class TopDownCost(AeroMAPSModel):
    """
    Top down unit cost model for energy carriers.
    It subtracts subsidies from user provided mfsp and adds taxes to it.
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
        for key, val in configuration_data.get("inputs").get("economics", {}).items():
            # TODO initialize with zeros instead of actual val?
            self.input_names[key] = val
        for key, val in configuration_data.get("inputs").get("technical", {}).items():
            # TODO initialize with zeros instead of actual val?
            self.input_names[key] = val

        # 2. Set individual inputs, coming either from other models or from the yaml as well
        self.input_names.update(
            {
                "carbon_tax": pd.Series([0.0]),
                f"{self.pathway_name}_mean_co2_emission_factor": pd.Series([0.0]),
            }
        )

        # 3. Getting resources is a bit more complex as we need to get necessary resources for the pathway
        self.resource_keys = (
            configuration_data.get("inputs")
            .get("technical", {})
            .get(f"{self.pathway_name}_resource_names", [])
        )

        for key in self.resource_keys:
            # Outputs.
            self.output_names[f"{self.pathway_name}_excluding_processes_{key}_mean_unit_cost"] = (
                pd.Series([0.0])
            )
            self.output_names[f"{self.pathway_name}_excluding_processes_{key}_mean_unit_tax"] = (
                pd.Series([0.0])
            )
            self.output_names[
                f"{self.pathway_name}_excluding_processes_{key}_mean_unit_subsidy"
            ] = pd.Series([0.0])

        self.process_keys = (
            configuration_data.get("inputs")
            .get("technical", {})
            .get(f"{self.pathway_name}_processes_names", [])
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
                            f"{self.pathway_name}_{process_key}_{resource}_mean_unit_cost"
                        ] = pd.Series([0.0])
                        self.output_names[
                            f"{self.pathway_name}_{process_key}_{resource}_mean_unit_tax"
                        ] = pd.Series([0.0])
                        self.output_names[
                            f"{self.pathway_name}_{process_key}_{resource}_mean_unit_subsidy"
                        ] = pd.Series([0.0])
                else:
                    # TODO initialize with zeros instead of actual val?
                    self.input_names[key] = val

            for key, val in processes_data[process_key].get("inputs").get("economics", {}).items():
                # TODO initialize with zeros instead of actual val?
                self.input_names[key] = val
            self.output_names[
                f"{self.pathway_name}_{process_key}_without_resources_mean_unit_cost"
            ] = pd.Series([0.0])
            self.output_names[
                f"{self.pathway_name}_{process_key}_without_resources_mean_unit_tax"
            ] = pd.Series([0.0])
            self.output_names[
                f"{self.pathway_name}_{process_key}_without_resources_mean_unit_subsidy"
            ] = pd.Series([0.0])

        # Getting unique resources
        self.resource_keys = list(set(self.resource_keys))

        # Adding resources-linked inputs and outputs
        # TODO specify eco/cost as for process
        for key in self.resource_keys:
            if f"{key}_cost" in resources_data[key]["specifications"]:
                self.input_names[f"{key}_cost"] = pd.Series([0.0])
            if f"{key}_subsidy" in resources_data[key]["specifications"]:
                self.input_names[f"{key}_subsidy"] = pd.Series([0.0])
            if f"{key}_tax" in resources_data[key]["specifications"]:
                self.input_names[f"{key}_tax"] = pd.Series([0.0])
            # Outputs.

        # Fill in the expected outputs with names from the compute method, initialized with NaN
        self.output_names.update(
            {
                f"{self.pathway_name}_net_mfsp_without_carbon_tax": pd.Series([0.0]),
                f"{self.pathway_name}_net_mfsp": pd.Series([0.0]),
                f"{self.pathway_name}_mean_mfsp": pd.Series([0.0]),
                f"{self.pathway_name}_mean_unit_tax": pd.Series([0.0]),
                f"{self.pathway_name}_mean_unit_carbon_tax": pd.Series([0.0]),
                f"{self.pathway_name}_mean_unit_subsidy": pd.Series([0.0]),
            }
        )

    def compute(self, input_data) -> dict:
        # Get inputs from the configuration file
        # Mandatory inputs
        output_data = {}

        optional_null_series = pd.Series(
            0.0, index=range(self.historic_start_year, self.end_year + 1)
        )

        # Usage of get/ brackets -> get usefull to set null values to optional inputs
        pathway_mfsp_without_resource = input_data.get(
            f"{self.pathway_name}_mean_mfsp_without_resource", optional_null_series.copy()
        )
        pathway_mfsp = pathway_mfsp_without_resource.copy()

        pathway_unit_subsidy_without_resource = input_data.get(
            f"{self.pathway_name}_mean_unit_subsidy_without_resource", optional_null_series.copy()
        )
        pathway_unit_subsidy = pathway_unit_subsidy_without_resource.copy()

        pathway_unit_tax_without_resource = input_data.get(
            f"{self.pathway_name}_mean_unit_tax_without_resource", optional_null_series.copy()
        )
        pathway_unit_tax = pathway_unit_tax_without_resource.copy()

        for key in self.resource_keys:
            # 1 ) --> pathway gets directly a resource
            specific_consumption = input_data.get(
                f"{self.pathway_name}_resource_specific_consumption_{key}", None
            )
            if specific_consumption is not None:
                mfsp_ressource = (
                    input_data.get(f"{key}_cost", optional_null_series.copy())
                    * specific_consumption
                )
                # usage of add to avoid getting a nan if one of the series is not defined intentionally
                pathway_mfsp = pathway_mfsp.add(mfsp_ressource, fill_value=0)

                output_data[f"{self.pathway_name}_excluding_processes_{key}_mean_unit_cost"] = (
                    mfsp_ressource
                )

                subsidy_ressource = (
                    input_data.get(f"{key}_subsidy", optional_null_series.copy())
                    * specific_consumption
                )
                pathway_unit_subsidy = pathway_unit_subsidy.add(subsidy_ressource, fill_value=0)
                output_data[f"{self.pathway_name}_excluding_processes_{key}_mean_unit_subsidy"] = (
                    subsidy_ressource
                )

                tax_ressource = (
                    input_data.get(f"{key}_tax", optional_null_series.copy()) * specific_consumption
                )
                pathway_unit_tax = pathway_unit_tax.add(tax_ressource, fill_value=0)
                output_data[f"{self.pathway_name}_excluding_processes_{key}_mean_unit_tax"] = (
                    tax_ressource
                )

            # 2 ) --> pathway gets a process that uses a resource
            for process_key in self.process_keys:
                specific_consumption = input_data.get(
                    f"{process_key}_resource_specific_consumption_{key}"
                )
                if specific_consumption is not None:
                    mfsp_ressource = (
                        input_data.get(f"{key}_cost", optional_null_series.copy())
                        * specific_consumption
                    )
                    # usage of add to avoid getting a nan if one of the series is not defined intentionally
                    pathway_mfsp = pathway_mfsp.add(mfsp_ressource, fill_value=0)

                    output_data[f"{self.pathway_name}_{process_key}_{key}_mean_unit_cost"] = (
                        mfsp_ressource
                    )

                    subsidy_ressource = (
                        input_data.get(f"{key}_subsidy", optional_null_series.copy())
                        * specific_consumption
                    )
                    pathway_unit_subsidy = pathway_unit_subsidy.add(subsidy_ressource, fill_value=0)
                    output_data[f"{self.pathway_name}_{process_key}_{key}_mean_unit_subsidy"] = (
                        subsidy_ressource
                    )

                    tax_ressource = (
                        input_data.get(f"{key}_tax", optional_null_series.copy())
                        * specific_consumption
                    )
                    pathway_unit_tax = pathway_unit_tax.add(tax_ressource, fill_value=0)
                    output_data[f"{self.pathway_name}_{process_key}_{key}_mean_unit_tax"] = (
                        tax_ressource
                    )

        # 3 ) --> pathway needs process cost without resources
        for process_key in self.process_keys:
            mfsp_process = input_data.get(
                f"{process_key}_mean_mfsp_without_resource", optional_null_series.copy()
            )
            pathway_mfsp = pathway_mfsp.add(mfsp_process, fill_value=0)
            output_data[f"{self.pathway_name}_{process_key}_without_resources_mean_unit_cost"] = (
                mfsp_process
            )

            subsidy_process = input_data.get(
                f"{process_key}_without_resources_mean_unit_subsidy", optional_null_series.copy()
            )
            pathway_unit_subsidy = pathway_unit_subsidy.add(subsidy_process, fill_value=0)
            output_data[
                f"{self.pathway_name}_{process_key}_without_resources_mean_unit_subsidy"
            ] = subsidy_process

            tax_process = input_data.get(
                f"{process_key}_without_resources_mean_unit_tax", optional_null_series.copy()
            )
            pathway_unit_tax = pathway_unit_tax.add(tax_process, fill_value=0)
            output_data[f"{self.pathway_name}_{process_key}_without_resources_mean_unit_tax"] = (
                tax_process
            )

        # Avoiding adding nans if subsidies and taxes defined for a shorter period of time than the mfsp
        pathway_net_mfsp_without_carbon_tax = pathway_mfsp.add(
            -pathway_unit_subsidy, fill_value=0
        ).add(pathway_unit_tax, fill_value=0)

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

        pathway_net_mfsp = pathway_net_mfsp_without_carbon_tax.add(
            pathway_unit_carbon_tax, fill_value=0
        )

        output_data.update(
            {
                f"{self.pathway_name}_net_mfsp_without_carbon_tax": pathway_net_mfsp_without_carbon_tax,
                f"{self.pathway_name}_net_mfsp": pathway_net_mfsp,
                f"{self.pathway_name}_mean_mfsp": pathway_mfsp,
                f"{self.pathway_name}_mean_unit_tax": pathway_unit_tax,
                f"{self.pathway_name}_mean_unit_carbon_tax": pathway_unit_carbon_tax,
                f"{self.pathway_name}_mean_unit_subsidy": pathway_unit_subsidy,
            }
        )

        # Store the results in the df
        self._store_outputs(output_data)

        return output_data

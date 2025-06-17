import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.models.impacts.energy_carriers.common.energy_carriers_manager import (
    EnergyCarrierManager,
)
from aeromaps.utils.functions import custom_series_addition


class EnergyResourceConsumption(AeroMAPSModel):
    """
    Aggregates all pathways consumption for a given resource. And compare to available share.
    """

    def __init__(
        self,
        name,
        configuration_data,
        pathways_manager: EnergyCarrierManager,
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
        self.pathways_manager = pathways_manager
        # Get the name of the resource
        self.resource_name = configuration_data["name"]

        self.input_names = {}
        self.output_names = {}

        if f"{self.resource_name}_availability_global" in configuration_data["specifications"]:
            self.input_names[f"{self.resource_name}_availability_global"] = configuration_data[
                "specifications"
            ][f"{self.resource_name}_availability_global"]
            self.output_names.update(
                {
                    f"{self.resource_name}_consumed_global_share": pd.Series([0.0]),
                    f"{self.resource_name}_necessary_global_share_with_selectivity": pd.Series(
                        [0.0]
                    ),
                }
            )
        if (
            f"{self.resource_name}_availability_aviation_allocated_share"
            in configuration_data["specifications"]
        ):
            self.input_names[f"{self.resource_name}_availability_aviation_allocated_share"] = (
                configuration_data[
                    "specifications"
                ][f"{self.resource_name}_availability_aviation_allocated_share"]
            )
            self.output_names.update(
                {
                    f"{self.resource_name}_consumed_aviation_allocated_share": pd.Series([0.0]),
                }
            )

        for pathway in self.pathways_manager.get(
            resources_used=self.resource_name
        ) + self.pathways_manager.get(resources_used_processes=self.resource_name):
            self.input_names.update(
                {
                    f"{pathway.name}_{self.resource_name}_total_consumption": pd.Series([0.0]),
                    f"{pathway.name}_{self.resource_name}_total_mobilised_with_selectivity": pd.Series(
                        [0.0]
                    ),
                }
            )

        self.output_names.update(
            {
                f"{self.resource_name}_total_consumption": pd.Series([0.0]),
                f"{self.resource_name}_total_necessary_with_selectivity": pd.Series([0.0]),
            }
        )

    def compute(self, input_data) -> dict:
        output_data = {}

        total_resource_consumption = pd.Series(
            0.0, index=range(self.prospection_start_year, self.end_year + 1)
        )
        total_resource_mobilised_with_selectivity = pd.Series(
            0.0, index=range(self.prospection_start_year, self.end_year + 1)
        )

        for pathway in self.pathways_manager.get(
            resources_used=self.resource_name
        ) + self.pathways_manager.get(resources_used_processes=self.resource_name):
            total_resource_consumption = custom_series_addition(
                total_resource_consumption,
                input_data[f"{pathway.name}_{self.resource_name}_total_consumption"],
            )
            total_resource_mobilised_with_selectivity = custom_series_addition(
                total_resource_mobilised_with_selectivity,
                input_data[f"{pathway.name}_{self.resource_name}_total_mobilised_with_selectivity"],
            )

        output_data[f"{self.resource_name}_total_consumption"] = total_resource_consumption
        output_data[f"{self.resource_name}_total_necessary_with_selectivity"] = (
            total_resource_mobilised_with_selectivity
        )

        if f"{self.resource_name}_availability_global" in input_data:
            output_data[f"{self.resource_name}_consumed_global_share"] = (
                total_resource_consumption
                / input_data[f"{self.resource_name}_availability_global"]
                * 100
            )
            output_data[f"{self.resource_name}_necessary_global_share_with_selectivity"] = (
                total_resource_mobilised_with_selectivity
                / input_data[f"{self.resource_name}_availability_global"]
                * 100
            )

        if f"{self.resource_name}_availability_aviation_allocated_share" in input_data:
            output_data[f"{self.resource_name}_consumed_aviation_allocated_share"] = (
                total_resource_consumption
                / (
                    input_data[f"{self.resource_name}_availability_global"]
                    * input_data[f"{self.resource_name}_availability_aviation_allocated_share"]
                    / 100
                )
                * 100
            )

        self._store_outputs(output_data)

        return output_data


class OverallResourcesConsumption(AeroMAPSModel):
    """
    Aggregates total consumption and shares for all resources using outputs from EnergyResourceConsumption.
    """

    def __init__(
        self,
        name,
        resources_data,
        *args,
        **kwargs,
    ):
        super().__init__(
            name=name,
            model_type="custom",
            *args,
            **kwargs,
        )

        # keep only resources whose availability is defined
        self.resources_names_origins = {
            resource: resources_data[resource].get("origin", "unknown")
            for resource in resources_data.keys()
            if f"{resource}_availability_global" in resources_data[resource]["specifications"]
        }

        # getting the unique origins of the resources
        self.resources_origins = set(self.resources_names_origins.values())

        self.resources_names = list(self.resources_names_origins.keys())

        # Dynamically build input/output names for all resources
        self.input_names = {}
        self.output_names = {}
        for resource in self.resources_names:
            self.input_names[f"{resource}_total_consumption"] = pd.Series([0.0])
            self.input_names[f"{resource}_total_necessary_with_selectivity"] = pd.Series([0.0])
            self.input_names[f"{resource}_availability_global"] = 0.0
            self.input_names[f"{resource}_availability_aviation_allocated_share"] = 0.0

        for origin in self.resources_origins:
            self.output_names[f"{origin}_total_consumption"] = pd.Series([0.0])
            self.output_names[f"{origin}_total_necessary_with_selectivity"] = pd.Series([0.0])
            self.output_names[f"{origin}_availability_global"] = 0.0
            self.output_names[f"{origin}_availability_aviation_allocated"] = 0.0
            self.output_names[f"{origin}_consumed_global_share"] = pd.Series([0.0])
            self.output_names[f"{origin}_consumed_aviation_allocated_share"] = pd.Series([0.0])
            self.output_names[f"{origin}_necessary_global_share_with_selectivity"] = pd.Series(
                [0.0]
            )
            self.output_names[f"{origin}_overall_aviation_allocated_share"] = 0.0

    def compute(self, input_data) -> dict:
        output_data = {}

        index = range(self.prospection_start_year, self.end_year + 1)

        # Prepare aggregation by origin
        origin_consumption = {
            origin: pd.Series(0.0, index=index) for origin in self.resources_origins
        }
        origin_necessary = {
            origin: pd.Series(0.0, index=index) for origin in self.resources_origins
        }
        origin_availability = {origin: 0.0 for origin in self.resources_origins}
        origin_availability_aviation_allocated = {origin: 0.0 for origin in self.resources_origins}

        # Aggregate by origin
        for resource in self.resources_names:
            origin = self.resources_names_origins.get(resource, None)
            if origin is None:
                print(
                    f"Warning: No origin found for resource:{resource}, aggregate shares not computed."
                )
                continue
            else:
                origin = origin

            total_consumption = input_data[f"{resource}_total_consumption"]
            total_necessary = input_data[f"{resource}_total_necessary_with_selectivity"]
            availability = input_data[f"{resource}_availability_global"]
            availability_aviation_allocated = (
                input_data[f"{resource}_availability_aviation_allocated_share"] / 100 * availability
            )

            origin_consumption[origin] = custom_series_addition(
                origin_consumption[origin], total_consumption
            )
            origin_necessary[origin] = custom_series_addition(
                origin_necessary[origin], total_necessary
            )
            origin_availability[origin] += availability
            origin_availability_aviation_allocated[origin] += availability_aviation_allocated

        # Compute shares for each origin
        for origin in self.resources_origins:
            total_consumption = origin_consumption[origin]
            total_necessary = origin_necessary[origin]
            total_availability = origin_availability[origin]
            total_availability_aviation_allocated = origin_availability_aviation_allocated[origin]

            consumed_global_share = total_consumption / total_availability * 100
            necessary_global_share_with_selectivity = total_necessary / total_availability * 100
            # Aviation allocated share in percent
            consumed_aviation_allocated_share = (
                total_consumption / total_availability_aviation_allocated * 100
            )
            overall_aviation_allocated_share = (
                total_availability_aviation_allocated / total_availability * 100
            )

            output_data[f"{origin}_total_consumption"] = total_consumption
            output_data[f"{origin}_total_necessary_with_selectivity"] = total_necessary
            output_data[f"{origin}_consumed_global_share"] = consumed_global_share
            output_data[f"{origin}_necessary_global_share_with_selectivity"] = (
                necessary_global_share_with_selectivity
            )
            output_data[f"{origin}_overall_aviation_allocated_share"] = (
                overall_aviation_allocated_share
            )
            output_data[f"{origin}_consumed_aviation_allocated_share"] = (
                consumed_aviation_allocated_share
            )
            output_data[f"{origin}_availability_global"] = total_availability
            output_data[f"{origin}_availability_aviation_allocated"] = (
                total_availability_aviation_allocated
            )

        self._store_outputs(output_data)
        return output_data

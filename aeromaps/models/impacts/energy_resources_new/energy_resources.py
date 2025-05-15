import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.models.impacts.energy_carriers.common.energy_carriers_manager import (
    EnergyCarrierManager,
)


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

        self.input_names = {
            f"{self.resource_name}_availability_global": configuration_data["specifications"][
                f"{self.resource_name}_availability_global"
            ],
            f"{self.resource_name}_availability_aviation_allocated_share": configuration_data[
                "specifications"
            ][f"{self.resource_name}_availability_aviation_allocated_share"],
        }

        for pathway in self.pathways_manager.get(resources_used=self.resource_name):
            self.input_names.update(
                {
                    f"{pathway.name}_{self.resource_name}_total_consumption": pd.Series([0.0]),
                    f"{pathway.name}_{self.resource_name}_total_mobilised_with_selectivity": pd.Series(
                        [0.0]
                    ),
                }
            )

        self.output_names = {
            f"{self.resource_name}_total_consumption": pd.Series([0.0]),
            f"{self.resource_name}_total_necessary_with_selectivity": pd.Series([0.0]),
            f"{self.resource_name}_consumed_global_share": pd.Series([0.0]),
            f"{self.resource_name}_necessary_global_share_with_selectivity": pd.Series([0.0]),
            f"{self.resource_name}_consumed_aviation_allocated_share": pd.Series([0.0]),
        }

    def compute(self, input_data) -> dict:
        output_data = {}

        total_resource_consumption = pd.Series(
            0.0, index=range(self.prospection_start_year, self.end_year + 1)
        )
        total_resource_mobilised_with_selectivity = pd.Series(
            0.0, index=range(self.prospection_start_year, self.end_year + 1)
        )

        for pathway in self.pathways_manager.get(resources_used=self.resource_name):
            total_resource_consumption += input_data[
                f"{pathway.name}_{self.resource_name}_total_consumption"
            ]
            total_resource_mobilised_with_selectivity += input_data[
                f"{pathway.name}_{self.resource_name}_total_mobilised_with_selectivity"
            ]

        output_data[f"{self.resource_name}_total_consumption"] = total_resource_consumption
        output_data[f"{self.resource_name}_total_necessary_with_selectivity"] = (
            total_resource_mobilised_with_selectivity
        )

        output_data[f"{self.resource_name}_consumed_global_share"] = (
            total_resource_consumption / input_data[f"{self.resource_name}_availability_global"]
        )
        output_data[f"{self.resource_name}_necessary_global_share_with_selectivity"] = (
            total_resource_mobilised_with_selectivity
            / input_data[f"{self.resource_name}_availability_global"]
        )

        output_data[f"{self.resource_name}_consumed_aviation_allocated_share"] = (
            total_resource_consumption
            / (
                input_data[f"{self.resource_name}_availability_global"]
                * input_data[f"{self.resource_name}_availability_aviation_allocated_share"]
                / 100
            )
        )

        self._store_outputs(output_data)

        return output_data

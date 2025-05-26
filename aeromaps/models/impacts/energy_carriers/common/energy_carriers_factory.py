# import all the concrete implementations of the energy carriers
from aeromaps.models.impacts.energy_carriers.common.energy_carriers_means import (
    EnergyCarriersMeans,
    EnergyCarriersMeanLHV,
)
from aeromaps.models.impacts.energy_carriers.common.energy_use_choice import EnergyUseChoice
from aeromaps.models.impacts.energy_carriers.top_down.cost import (
    TopDownCost,
)
from aeromaps.models.impacts.energy_carriers.top_down.environmental import (
    TopDownEnvironmental,
)
from aeromaps.models.impacts.energy_carriers.bottom_up.cost import (
    BottomUpCost,
)
from aeromaps.models.impacts.energy_carriers.bottom_up.environmental import (
    BottomUpEnvironmental,
)
from aeromaps.models.impacts.energy_carriers.bottom_up.production_capacity import (
    BottomUpCapacity,
)
from aeromaps.models.impacts.energy_resources_new.energy_resources import EnergyResourceConsumption


class AviationEnergyCarriersFactory:
    @staticmethod
    def create_carrier(pathway_name, pathway_data, resources_data, processs_data):
        environmental_model_type = pathway_data["environmental_model"]
        cost_model_type = pathway_data["cost_model"]
        # case distinction between energy model types
        # TODO split the config file into two separate files here instead in the inits ?

        if environmental_model_type == "top-down" and cost_model_type == "top-down":
            return {
                f"{pathway_name}_top_down_unit_cost": TopDownCost(
                    f"{pathway_name}_top_down_unit_cost",
                    pathway_data,
                    resources_data,
                    processs_data,
                ),
                f"{pathway_name}_top_down_unit_environmental": TopDownEnvironmental(
                    f"{pathway_name}_top_down_unit_environmental",
                    pathway_data,
                    resources_data,
                    processs_data,
                ),
            }
        elif environmental_model_type == "top-down" and cost_model_type == "bottom-up":
            return {
                f"{pathway_name}_top_down_total_environmental": TopDownEnvironmental(
                    f"{pathway_name}_top_down_total_environmental",
                    pathway_data,
                    resources_data,
                    processs_data,
                ),
                f"{pathway_name}_bottom_up_cost": BottomUpCost(
                    f"{pathway_name}_bottom_up_cost", pathway_data, resources_data, processs_data
                ),
                f"{pathway_name}_bottom_up_capacity": BottomUpCapacity(
                    f"{pathway_name}_bottom_up_capacity", pathway_data
                ),
            }
        elif environmental_model_type == "bottom-up" and cost_model_type == "top-down":
            return {
                f"{pathway_name}_bottom_up_environmental": BottomUpEnvironmental(
                    f"{pathway_name}_bottom_up_environmental",
                    pathway_data,
                    resources_data,
                    processs_data,
                ),
                f"{pathway_name}_bottom_up_capacity": BottomUpCapacity(
                    f"{pathway_name}_bottom_up_capacity",
                    pathway_data,
                ),
                f"{pathway_name}_top_down_unit_cost": TopDownCost(
                    f"{pathway_name}_top_down_unit_cost",
                    pathway_data,
                    resources_data,
                    processs_data,
                ),
            }
        elif environmental_model_type == "bottom-up" and cost_model_type == "bottom-up":
            return {
                f"{pathway_name}_bottom_up_environmental": TopDownEnvironmental(
                    f"{pathway_name}_bottom_up_environmental",
                    pathway_data,
                    resources_data,
                    processs_data,
                ),
                f"{pathway_name}_bottom_up_capacity": BottomUpCapacity(
                    f"{pathway_name}_bottom_up_capacity",
                    pathway_data,
                ),
                f"{pathway_name}_bottom_up_cost": TopDownCost(
                    f"{pathway_name}_bottom_up_cost", pathway_data, resources_data, processs_data
                ),
            }
        else:
            # return error message depending on which model type is unknown
            if environmental_model_type not in ["top-down", "bottom-up"]:
                raise ValueError(f"Unsupported model type: {environmental_model_type}")
            if cost_model_type not in ["top-down", "bottom-up"]:
                raise ValueError(f"Unsupported model type: {cost_model_type}")

    @staticmethod
    def instantiate_energy_carriers_models(energy_carriers_data, pathways_manager):
        """Instantiates energy carriers models."""
        return {
            "energy_use_choice": EnergyUseChoice(
                "energy_use_choice", energy_carriers_data, pathways_manager
            ),
            "energy_carriers_means": EnergyCarriersMeans(
                "energy_carriers_means", energy_carriers_data, pathways_manager
            ),
            "energy_carriers_mean_lhv": EnergyCarriersMeanLHV("energy_carriers_mean_lhv"),
        }

    @staticmethod
    def instantiate_resource_consumption_models(resources_data, pathways_manager):
        """Instantiates energy carriers models."""
        models = {}
        for resource in resources_data.keys():
            models.update(
                {
                    f"{resource}_consumption": EnergyResourceConsumption(
                        f"{resource}_consumption", resources_data[resource], pathways_manager
                    )
                }
            )
        return models

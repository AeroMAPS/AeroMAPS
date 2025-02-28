# import all the concrete implementations of the energy carriers
from aeromaps.models.impacts.energy_carriers.top_down.total_cost import (
    TopDownTotalCost,
)
from aeromaps.models.impacts.energy_carriers.top_down.total_environmental import (
    TopDownTotalEnvironmental,
)
from aeromaps.models.impacts.energy_carriers.top_down.unit_cost import (
    TopDownUnitCost,
)
from aeromaps.models.impacts.energy_carriers.top_down.unit_environmental import (
    TopDownUnitEnvironmental,
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


class AviationEnergyCarriersFactory:
    @staticmethod
    def create_carrier(pathway_name, configuration_file):
        environmental_model_type = configuration_file["environmental_model"]
        cost_model_type = configuration_file["cost_model"]
        # case distinction between energy model types
        # TODO split the config file into two separate files here instead in the inits ?

        if environmental_model_type == "top-down" and cost_model_type == "top-down":
            return {
                f"{pathway_name}_top_down_total_cost": TopDownTotalCost(
                    f"{pathway_name}_top_down_total_cost", configuration_file
                ),
                f"{pathway_name}_top_down_total_environmental": TopDownTotalEnvironmental(
                    f"{pathway_name}_top_down_total_environmental", configuration_file
                ),
                f"{pathway_name}_top_down_unit_cost": TopDownUnitCost(
                    f"{pathway_name}_top_down_unit_cost", configuration_file
                ),
                f"{pathway_name}_top_down_unit_environmental": TopDownUnitEnvironmental(
                    f"{pathway_name}_top_down_unit_environmental", configuration_file
                ),
            }
        elif environmental_model_type == "top-down" and cost_model_type == "bottom-up":
            return {
                f"{pathway_name}_top_down_total_environmental": TopDownTotalEnvironmental(
                    f"{pathway_name}_top_down_total_environmental", configuration_file
                ),
                f"{pathway_name}_top_down_unit_environmental": TopDownUnitEnvironmental(
                    f"{pathway_name}_top_down_unit_environmental", configuration_file
                ),
                f"{pathway_name}_bottom_up_cost": BottomUpCost(
                    f"{pathway_name}_bottom_up_cost", configuration_file
                ),
                f"{pathway_name}_bottom_up_capacity": BottomUpCapacity(
                    f"{pathway_name}_bottom_up_capacity", configuration_file
                ),
            }
        elif environmental_model_type == "bottom-up" and cost_model_type == "top-down":
            return {
                f"{pathway_name}_bottom_up_environmental": BottomUpEnvironmental(
                    f"{pathway_name}_bottom_up_environmental", configuration_file
                ),
                f"{pathway_name}_bottom_up_capacity": BottomUpCapacity(
                    f"{pathway_name}_bottom_up_capacity", configuration_file
                ),
                f"{pathway_name}_top_down_total_cost": TopDownTotalCost(
                    f"{pathway_name}_top_down_total_cost", configuration_file
                ),
                f"{pathway_name}_top_down_unit_cost": TopDownUnitCost(
                    f"{pathway_name}_top_down_unit_cost", configuration_file
                ),
            }
        elif environmental_model_type == "bottom-up" and cost_model_type == "bottom-up":
            return {
                f"{pathway_name}_bottom_up_environmental": BottomUpEnvironmental(
                    f"{pathway_name}_bottom_up_environmental", configuration_file
                ),
                f"{pathway_name}_bottom_up_capacity": BottomUpCapacity(
                    f"{pathway_name}_bottom_up_capacity", configuration_file
                ),
                f"{pathway_name}_bottom_up_cost": BottomUpCost(
                    f"{pathway_name}_bottom_up_cost", configuration_file
                ),
            }
        else:
            # return error message depending on which model type is unknown
            if environmental_model_type not in ["top-down", "bottom-up"]:
                raise ValueError(f"Unsupported model type: {environmental_model_type}")
            if cost_model_type not in ["top-down", "bottom-up"]:
                raise ValueError(f"Unsupported model type: {cost_model_type}")

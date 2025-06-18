# import all the concrete implementations of the energy carriers
from aeromaps.models.impacts.energy_carriers.bottom_up.abatement_cost import (
    EnergyAbatementCost,
    ReferenceAbatementCost,
)
from aeromaps.models.impacts.energy_carriers.bottom_up.abatement_effective import (
    EnergyAbatementEffective,
)
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
from aeromaps.models.impacts.energy_resources_new.energy_resources import (
    EnergyResourceConsumption,
    OverallResourcesConsumption,
)


class AviationEnergyCarriersFactory:
    @staticmethod
    def create_carrier(pathway_name, energy_carriers_data, resources_data, processs_data):
        pathway_data = energy_carriers_data[pathway_name]
        environmental_model_type = pathway_data["environmental_model"]
        cost_model_type = pathway_data["cost_model"]
        # case distinction between energy model types
        # TODO split the config file into two separate files here instead in the inits ?
        models = {}
        if environmental_model_type == "top-down":
            models.update(
                {
                    f"{pathway_name}_top_down_unit_environmental": TopDownEnvironmental(
                        f"{pathway_name}_top_down_unit_environmental",
                        pathway_data,
                        resources_data,
                        processs_data,
                    )
                }
            )
        elif environmental_model_type == "bottom-up":
            models.update(
                {
                    f"{pathway_name}_bottom_up_unit_environmental": BottomUpEnvironmental(
                        f"{pathway_name}_bottom_up_unit_environmental",
                        pathway_data,
                        resources_data,
                        processs_data,
                    )
                }
            )
        else:
            raise ValueError(f"Unsupported environmental model type: {environmental_model_type}")
        if cost_model_type == "top-down":
            models.update(
                {
                    f"{pathway_name}_top_down_unit_cost": TopDownCost(
                        f"{pathway_name}_top_down_unit_cost",
                        pathway_data,
                        resources_data,
                        processs_data,
                    )
                }
            )
        elif cost_model_type == "bottom-up":
            models.update(
                {
                    f"{pathway_name}_bottom_up_unit_cost": BottomUpCost(
                        f"{pathway_name}_bottom_up_unit_cost",
                        pathway_data,
                        resources_data,
                        processs_data,
                    )
                }
            )
        else:
            raise ValueError(f"Unsupported cost model type: {cost_model_type}")
        # add capacity model
        if environmental_model_type == "bottom-up" or cost_model_type == "bottom-up":
            models.update(
                {
                    f"{pathway_name}_bottom_up_capacity": BottomUpCapacity(
                        f"{pathway_name}_bottom_up_capacity", pathway_data, processs_data
                    )
                }
            )
        if pathway_data.get("abatement_cost"):
            if environmental_model_type != "bottom-up" or cost_model_type != "bottom-up":
                raise ValueError(
                    "Abatement cost model can only be used with bottom-up environmental or cost models."
                )
            # add abatement cost and effective models
            models.update(
                {
                    f"{pathway_name}_bottom_up_abatement_cost": EnergyAbatementCost(
                        f"{pathway_name}_bottom_up_abatement_cost",
                        pathway_name,
                    ),
                    f"{pathway_name}_abatement_effective": EnergyAbatementEffective(
                        f"{pathway_name}_abatement_effective",
                        pathway_name,
                    ),
                }
            )
        if pathway_data.get("abatement_cost_reference"):
            models.update(
                {
                    f"{pathway_name}_abatement_cost_reference": ReferenceAbatementCost(
                        f"{pathway_name}_abatement_cost_reference",
                        pathway_name,
                        pathway_data,
                    )
                }
            )
        return models

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
        models.update(
            {
                "overall_resources_consumption": OverallResourcesConsumption(
                    "overall_resources_consumption",
                    resources_data,
                ),
            }
        )
        return models

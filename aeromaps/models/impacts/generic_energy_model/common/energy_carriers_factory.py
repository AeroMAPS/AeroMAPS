"""
Factory to create energy carriers models based on yaml configuration files.
"""

# import all the concrete implementations of the energy carriers
from aeromaps.models.impacts.generic_energy_model.bottom_up.abatement_cost import (
    EnergyAbatementCost,
    ReferenceAbatementCost,
)
from aeromaps.models.impacts.generic_energy_model.bottom_up.abatement_effective import (
    EnergyAbatementEffective,
)
from aeromaps.models.impacts.generic_energy_model.common.energy_carriers_means import (
    EnergyCarriersMeans,
    EnergyCarriersMeanLHV,
)
from aeromaps.models.impacts.generic_energy_model.common.energy_use_choice import EnergyUseChoice
from aeromaps.models.impacts.generic_energy_model.top_down.cost import (
    TopDownCost,
)
from aeromaps.models.impacts.generic_energy_model.top_down.environmental import (
    TopDownEnvironmental,
)
from aeromaps.models.impacts.generic_energy_model.bottom_up.cost import (
    BottomUpCost,
)
from aeromaps.models.impacts.generic_energy_model.bottom_up.environmental import (
    BottomUpEnvironmental,
)
from aeromaps.models.impacts.generic_energy_model.bottom_up.production_capacity import (
    BottomUpCapacity,
)
from aeromaps.models.impacts.energy_resources.energy_resources import (
    EnergyResourceConsumption,
    OverallResourcesConsumption,
)

import warnings


class AviationEnergyCarriersFactory:
    """
    Factory to create energy carriers models based on yaml configuration files.
    """

    @staticmethod
    def create_carrier(pathway_name, energy_carriers_data, resources_data, process_data):
        """
        Create energy carrier models based on the configuration data.

        Parameters
        ----------
        pathway_name : str
            Name of the energy pathway to create models for.
        energy_carriers_data : dict
            Configuration data for energy carriers.
        resources_data : dict
            Configuration data for energy resources.
        process_data : dict
            Configuration data for processes.

        Returns
        -------
        dict
            Dictionary of instantiated energy carrier models.
        """
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
                        process_data,
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
                        process_data,
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
                        process_data,
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
                        process_data,
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
                        f"{pathway_name}_bottom_up_capacity", pathway_data, process_data
                    )
                }
            )
        if pathway_data.get("abatement_cost"):
            if cost_model_type != "bottom-up":
                raise ValueError(
                    "Abatement cost model can only be used with bottom-up cost models."
                )
            if environmental_model_type != "bottom-up":
                warnings.warn(
                    "\n⚠️ Using Top-Down environmental model for abatement cost. Not recommended."
                )
            # add abatement cost and effective models
            models.update(
                {
                    f"{pathway_name}_bottom_up_abatement_cost": EnergyAbatementCost(
                        f"{pathway_name}_bottom_up_abatement_cost",
                        pathway_name,
                        pathway_data,
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
        """
        Instantiates energy carriers related models. Energy use choice, means, mean LHV, ...

        Parameters
        ----------
        energy_carriers_data : dict
            Configuration data for energy carriers.
        pathways_manager : PathwaysManager
            Manager for handling energy pathways.

        Returns
        -------
        dict
            Dictionary of instantiated energy carriers models.
        """
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
        """
        Instantiates energy resource consumption models.

        Parameters
        ----------
        resources_data : dict
            Configuration data for energy resources.
        pathways_manager : PathwaysManager
            Manager for handling energy pathways.

        Returns
        -------
        dict
            Dictionary of instantiated energy resource consumption models.
        """
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

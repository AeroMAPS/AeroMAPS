"""
Factory to create offsetting mechanisms models based on yaml configuration files.
"""

# import all the concrete implementations of the offsetting mechanisms
from aeromaps.models.impacts.generic_offsettings_model.common.offsettings_means import (
    OffsettingsMeans,
)
from aeromaps.models.impacts.generic_offsettings_model.common.offsettings_use_choice import (
    OffsettingsUseChoice,
)
from aeromaps.models.impacts.generic_offsettings_model.top_down.cost import (
    OffsettingTopDownCost,
)


class CarbonOffsettingsFactory:
    """
    Factory to create offsetting mechanisms models based on yaml configuration files.
    """

    @staticmethod
    def create_mechanism(mechanism_name, offsettings_data):
        """
        Create offsetting mechanism models based on the configuration data.

        Parameters
        ----------
        mechanism_name : str
            Name of the offsetting mechanism to create models for.
        offsettings_data : dict
            Configuration data for offsetting mechanisms.

        Returns
        -------
        dict
            Dictionary of instantiated offsetting mechanism models.
        """
        mechanism_data = offsettings_data[mechanism_name]
        cost_model_type = mechanism_data["cost_model"]
        models = {}
        if cost_model_type == "top-down":
            models.update(
                {
                    f"{mechanism_name}_top_down_unit_cost": OffsettingTopDownCost(
                        f"{mechanism_name}_top_down_unit_cost",
                        mechanism_data,
                    )
                }
            )
        else:
            # Placeholder for future bottom-up offsetting cost models (e.g. DACCS plants deployment)
            raise ValueError(f"Unsupported cost model type: {cost_model_type}")
        return models

    @staticmethod
    def instantiate_offsettings_models(offsettings_data, offsettings_manager):
        """
        Instantiates offsettings related models. Offsettings use choice, means, ...

        Parameters
        ----------
        offsettings_data : dict
            Configuration data for offsetting mechanisms.
        offsettings_manager : OffsettingMechanismManager
            Manager for handling offsetting mechanisms.

        Returns
        -------
        dict
            Dictionary of instantiated offsettings models.
        """
        return {
            "offsettings_use_choice": OffsettingsUseChoice(
                "offsettings_use_choice", offsettings_data, offsettings_manager
            ),
            "offsettings_means": OffsettingsMeans(
                "offsettings_means", offsettings_data, offsettings_manager
            ),
        }

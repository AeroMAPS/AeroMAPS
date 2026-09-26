"""
Factory to create operational concept models based on yaml configuration files.
"""

from aeromaps.models.impacts.emissions.co2_emissions import (
    DetailedCo2EmissionsPerOperationalConcept,
)
from aeromaps.models.impacts.generic_operations_model.common.operations_use_choice import (
    OperationsUseChoice,
)


class OperationsFactory:
    """
    Factory to create the generic operations models based on yaml configuration files.
    """

    @staticmethod
    def instantiate_operations_models(operations_data, operations_manager):
        """
        Instantiate the generic operations models.

        Parameters
        ----------
        operations_data : dict
            Configuration data for the operational concepts.
        operations_manager : OperationalConceptManager
            Manager handling the operational concepts.

        Returns
        -------
        dict
            Dictionary of instantiated operations models.
        """
        return {
            "operations_use_choice": OperationsUseChoice(
                "operations_use_choice", operations_data, operations_manager
            ),
            "detailed_co2_emissions_per_operational_concept": (
                DetailedCo2EmissionsPerOperationalConcept(
                    "detailed_co2_emissions_per_operational_concept",
                    operations_manager=operations_manager,
                )
            ),
        }

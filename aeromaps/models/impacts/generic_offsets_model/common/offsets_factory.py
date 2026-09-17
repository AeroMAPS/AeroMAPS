"""
Factory to create the generic offsets model based on yaml configuration files.
"""

from aeromaps.models.impacts.generic_offsets_model.common.offsets_use_choice import (
    OffsetsUseChoice,
)


class OffsetsFactory:
    """
    Factory to create the generic offsets models based on yaml configuration files.
    """

    @staticmethod
    def instantiate_offsets_models(offsets_data, offsets_manager):
        """
        Instantiate the generic offsets models.

        Parameters
        ----------
        offsets_data : dict
            Configuration data for the offsetting schemes.
        offsets_manager : OffsetSchemeManager
            Manager handling the offsetting schemes.

        Returns
        -------
        dict
            Dictionary of instantiated offsets models.
        """
        return {
            "offsets_use_choice": OffsetsUseChoice(
                "offsets_use_choice", offsets_data, offsets_manager
            ),
        }

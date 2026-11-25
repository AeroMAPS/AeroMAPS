"""Base climate model settings."""

from typing import Any, ClassVar

from aeromaps.models.impacts.climate.climate_models_settings.species_settings import SpeciesSettings
from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration


class ClimateModelSettings(BaseProcessConfiguration):
    """Base class for climate models settings."""

    climate_model: str
    """Climate model name."""

    species_settings: SpeciesSettings
    """The settings for the different atmospheric species."""

    model_settings: dict[str, Any] | None = None
    """Optional extra settings for the model."""

    _default_settings: ClassVar[dict | None] = None

    def __init__(self, /, **data: Any):
        default_settings = self._default_settings
        if default_settings and not data:
            data = default_settings
        super().__init__(**data)

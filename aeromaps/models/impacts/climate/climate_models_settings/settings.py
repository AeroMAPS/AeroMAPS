"""Base climate model settings."""

from typing import Any

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

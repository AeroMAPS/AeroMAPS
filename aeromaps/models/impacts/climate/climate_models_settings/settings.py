"""Base climate model settings."""

from __future__ import annotations
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

    _instances: ClassVar[dict[str, ClimateModelSettings]] = {}

    def __init__(self, /, **data: Any):
        default_settings = self._default_settings
        user_data = data
        if default_settings:
            data = default_settings
        if user_data:
            data.update(user_data)
        super().__init__(**data)
        if self.climate_model in ClimateModelSettings._instances:
            raise ValueError(
                f"Climate Model settings {self.climate_model} exists already in the registry."
            )
        ClimateModelSettings._instances.update({self.climate_model: self})

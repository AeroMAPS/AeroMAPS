"""IPCC climate model."""

from pathlib import Path
from typing import ClassVar

from aeromaps.models.impacts.climate.climate_models_settings.settings import ClimateModelSettings
from aeromaps.utils.yaml import read_yaml_file


DATA_DIR = (
    Path(__file__).parents[4]
    / "resources"
    / "data"
    / "default_climate_models"
    / "climate_model_ipcc.yaml"
)

data = read_yaml_file(str(DATA_DIR))


class IPCCModelSettings(ClimateModelSettings):
    """IPCC climate model settings."""

    climate_model: str = "IPCC"

    _default_settings: ClassVar[dict] = data

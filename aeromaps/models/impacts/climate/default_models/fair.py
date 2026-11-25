"""FaIR climate model."""

from pathlib import Path
from typing import ClassVar

from aeromaps.models.impacts.climate.climate_models_settings.settings import ClimateModelSettings
from aeromaps.utils.yaml import read_yaml_file


DATA_DIR = (
    Path(__file__).parents[4]
    / "resources"
    / "data"
    / "default_climate_models"
    / "climate_model_fair.yaml"
)

data = read_yaml_file(str(DATA_DIR))


class FaIRModelSettings(ClimateModelSettings):
    """FaIR climate model settings."""

    climate_model: str = "FaIR"

    _default_settings: ClassVar[dict] = data

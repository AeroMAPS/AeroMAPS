"""Loader for AeroMAPS climate models settings."""

from pathlib import Path

from aeromaps.models.impacts.climate.climate_models_settings.settings import ClimateModelSettings
from aeromaps.utils.yaml import read_yaml_file


MODELS_DATA_DIR = Path(__file__).parents[4] / "resources" / "data" / "default_climate_models"

DEFAULT_CLIMATE_MODELS = {
    "FaIR": MODELS_DATA_DIR / "climate_model_fair.yaml",
    "GWP*": MODELS_DATA_DIR / "climate_model_gwpstar.yaml",
    "IPCC": MODELS_DATA_DIR / "climate_model_ipcc.yaml",
    "LWE": MODELS_DATA_DIR / "climate_model_lwe.yaml",
}


def load_default_climate_model_settings(model_name: str) -> ClimateModelSettings:
    """Load the settings for a given default climate model.
    Args:
        model_name: The name of the default climate model.

    Returns: The settings of the model.

    Raises:
        ValueError if the name of the model is unknown.
    """
    if model_name not in DEFAULT_CLIMATE_MODELS:
        raise ValueError(
            f"Unknown climate model: {model_name}, available models are:{list(DEFAULT_CLIMATE_MODELS.keys())}"
        )
    data = read_yaml_file(str(DEFAULT_CLIMATE_MODELS[model_name]))

    return ClimateModelSettings(**data)

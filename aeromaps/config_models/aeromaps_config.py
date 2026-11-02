"""AeroMAPS process configuration."""

from aeromaps.config_models.base_config import BaseConfig
from aeromaps.config_models.data_config import DataConfig
from aeromaps.config_models.models_config import ModelsConfig


class AeroMapsConfig(BaseConfig):
    data: DataConfig
    models: ModelsConfig

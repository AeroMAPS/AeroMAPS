"""AeroMAPS process configuration."""

from aeromaps.process_configuration.base_config import BaseConfig
from aeromaps.process_configuration.data_config import DataConfig
from aeromaps.process_configuration.models_config import ModelsConfig


class AeroMapsConfig(BaseConfig):
    data: DataConfig
    models: ModelsConfig

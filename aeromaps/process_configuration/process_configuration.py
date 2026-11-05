"""AeroMAPS process configuration."""

from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration
from aeromaps.process_configuration.data_configuration import DataConfig
from aeromaps.process_configuration.process_models_configuration import ModelsConfig


class AeroMAPSProcessConfiguration(BaseProcessConfiguration):
    data: DataConfig
    models: ModelsConfig

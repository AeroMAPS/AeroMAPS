"""AeroMAPS process configuration."""

from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration
from aeromaps.process_configuration.data_configuration import ProcessDataConfiguration
from aeromaps.process_configuration.process_models_configuration import ProcessModelsConfiguration


class AeroMAPSProcessConfiguration(BaseProcessConfiguration):
    data: ProcessDataConfiguration = ProcessDataConfiguration()
    models: ProcessModelsConfiguration = ProcessModelsConfiguration()

"""AeroMAPS process configuration."""

from pathlib import Path

from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration
from aeromaps.process_configuration.data_configuration import ProcessDataConfiguration
from aeromaps.process_configuration.process_models_configuration import ProcessModelsConfiguration


class AeroMAPSProcessConfiguration(BaseProcessConfiguration):
    """Configuration class for an AeroMAPSProcess.

    This class can be used directly to configure an `AeroMAPSProcess`.

    Relative paths are resolved against either the directory of the configuration file
    if one is given or against the field `data_directory` if the class is used to
    configure the process.

    The literal value **default** for the different path fields, resolves a model data
    file from the installed package instead if relative to the given directory.
    However this practice is not recommended. To use default values for any field,
    either don't set it on the model or don't set the key in the configuration file.

    .. Warning::

    If using directly to configure the process, the field `data_directory` must be a valid
    directory, and it is the directly to which all relative paths resolve to.
    """

    data: ProcessDataConfiguration = ProcessDataConfiguration()
    """The data (inputs and outputs) configuration of the process."""

    models: ProcessModelsConfiguration = ProcessModelsConfiguration()
    """The models configuration of the process.

    A model is initialized **ONLY** if it is  set in the configuration data model. 
    Set to `None` to switch that model off.
    """

    data_directory: Path | str | None = None
    """Directory to resolve relative paths to if no configuration file is used."""

"""
Initialization module for the AeroMAPS package, which provides the function to create an AeroMAPSProcess.
"""

from aeromaps.core.process import AeroMAPSProcess


def create_process(
    configuration_file=None,
    custom_models=None,
    optimisation=False,
    multi_regional=False,
) -> AeroMAPSProcess:
    """
    Create an AeroMAPS process.

    Parameters
    ----------
    configuration_file : str, optional
        Path to the configuration file (default is None).
    custom_models : dict, optional
        Dictionary of additional models to be used. These are merged with
        the standard models loaded from the configuration file's
        `models.standards` list (default is None).
    optimisation : bool, optional
        Whether to enable optimisation (default is False).
    multi_regional : bool, optional
        Whether to enable multi-regional mode (default is False).
        When True, the process reads a regionalisation configuration file
        to set up multiple regional processes with namespaced disciplines.
        This can also be enabled by specifying a 'regionalisation' section
        in the configuration file.

    Returns
    -------
    AeroMAPSProcess
        An instance of the AeroMAPSProcess class.
    """

    return AeroMAPSProcess(
        configuration_file=configuration_file,
        custom_models=custom_models,
        optimisation=optimisation,
        multi_regional=multi_regional,
    )

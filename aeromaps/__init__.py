"""
Initialization module for the AeroMAPS package, which provides the function to create an AeroMAPSProcess.
"""

from aeromaps.core.process import AeroMAPSProcess
from aeromaps.core.multi_process import MultiProcess


def create_process(
    configuration_file=None,
    custom_models=None,
    optimisation=False,
) -> AeroMAPSProcess:
    """
    Create an AeroMAPS process.

    Parameters
    ----------
    configuration_file : str, optional
        Path to the configuration file (default is None).
    models : dict, optional
        Dictionary of additional models to be used. These are merged with
        the standard models loaded from the configuration file's
        `models.standards` list (default is None).
    optimisation : bool, optional
        Whether to enable optimisation (default is False).

    Returns
    -------
    AeroMAPSProcess
        An instance of the AeroMAPSProcess class.
    """

    return AeroMAPSProcess(
        configuration_file=configuration_file,
        custom_models=custom_models,
        optimisation=optimisation,
    )


def create_multi_process(processes) -> MultiProcess:
    """
    Create a MultiProcess manager for scenario comparison.
    
    Parameters
    ----------
    processes : dict or list
        Dictionary mapping scenario names to AeroMAPSProcess objects,
        or a list of AeroMAPSProcess objects.
    
    Returns
    -------
    MultiProcess
        An instance of the MultiProcess class for managing multiple scenarios.
    
    Examples
    --------
    >>> process1 = create_process(configuration_file="config1.yaml")
    >>> process2 = create_process(configuration_file="config2.yaml")
    >>> process1.compute()
    >>> process2.compute()
    >>> multi = create_multi_process({"scenario_1": process1, "scenario_2": process2})
    >>> multi.list_available_plots()
    >>> multi.plot("co2_emissions_comparison")
    """
    return MultiProcess(processes)


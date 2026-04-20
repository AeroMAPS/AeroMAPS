"""
Initialization module for the AeroMAPS package.

This module provides factory functions to create AeroMAPS processes:
- create_process: Auto-detects single vs multi-regional mode from config
- create_multi_regional_process: Explicit multi-regional process creation
"""

from typing import Optional, Union

from aeromaps.core.process import AeroMAPSProcess
from aeromaps.core.multi_regional_process import MultiRegionalProcess
from aeromaps.core.processes_assembly import AeroMAPSProcessesAssembly


def create_process(
    configuration_file: Optional[str] = None,
    custom_models: Optional[dict] = None,
    optimisation: bool = False,
    multi_regional: bool = False,
    disable_execution_statistics: Optional[bool] = None,
) -> Union[AeroMAPSProcess, MultiRegionalProcess]:
    """
    Create an AeroMAPS process, auto-detecting single vs multi-regional mode.

    This factory function automatically creates the appropriate process type
    based on the configuration file contents or the multi_regional parameter.
    If the configuration file contains a 'regionalisation' section, a
    MultiRegionalProcess is created; otherwise, a standard AeroMAPSProcess
    is created.

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
        Note: Only supported for single-region mode currently.
    multi_regional : bool, optional
        Whether to force multi-regional mode (default is False).
        This can also be auto-detected from the configuration file's
        'regionalisation' section.
    disable_execution_statistics : bool, optional
        Whether to disable GEMSEO's execution statistics shared memory.
        If None (default), automatically enabled for multi-regional mode to
        avoid semaphore exhaustion with many disciplines.

    Returns
    -------
    AeroMAPSProcess or MultiRegionalProcess
        The appropriate process instance based on the configuration.

    Examples
    --------
    >>> # Single-region process
    >>> process = create_process(configuration_file="config.yaml")
    >>> process.compute()
    >>>
    >>> # Multi-regional process (auto-detected from config)
    >>> process = create_process(configuration_file="config_with_regionalisation.yaml")
    >>> process.compute()
    >>> process.regional_processes["FR"].plot("co2_emissions")
    """
    # Check if multi-regional mode should be used
    use_multi_regional = multi_regional

    if not use_multi_regional and configuration_file is not None:
        # Auto-detect from configuration file
        try:
            from aeromaps.utils.yaml import read_yaml_file

            config = read_yaml_file(configuration_file)
            use_multi_regional = "regionalisation" in config
        except Exception:
            pass

    if use_multi_regional:
        if optimisation:
            import warnings

            warnings.warn(
                "Optimisation mode is not yet supported for multi-regional processes. "
                "Using standard MDA mode instead.",
                UserWarning,
            )

        return MultiRegionalProcess(
            configuration_file=configuration_file,
            custom_models=custom_models,
            disable_execution_statistics=disable_execution_statistics,
        )
    else:
        return AeroMAPSProcess(
            configuration_file=configuration_file,
            custom_models=custom_models,
            optimisation=optimisation,
            disable_execution_statistics=disable_execution_statistics,
        )


def create_multi_regional_process(
    configuration_file: str,
    custom_models: Optional[dict] = None,
    disable_execution_statistics: Optional[bool] = None,
) -> MultiRegionalProcess:
    """
    Create a multi-regional AeroMAPS process explicitly.

    Use this function when you specifically want a MultiRegionalProcess
    with access to its multi-regional API (regional_processes, etc.).

    Parameters
    ----------
    configuration_file : str
        Path to the configuration file with 'regionalisation' section.
    custom_models : dict, optional
        Dictionary of additional models to be used.
    disable_execution_statistics : bool, optional
        Whether to disable GEMSEO's execution statistics.

    Returns
    -------
    MultiRegionalProcess
        A configured multi-regional process instance.

    Examples
    --------
    >>> process = create_multi_regional_process("config.yaml")
    >>> process.compute(parallel=True, max_workers=4)
    >>>
    >>> # Access regional data
    >>> for region_id in process.list_regions():
    ...     regional_proc = process.regional_processes[region_id]
    ...     print(f"{region_id}: {regional_proc.data['vector_outputs']['co2_emissions'].iloc[-1]}")
    >>>
    >>> # Get aggregated global results
    >>> global_outputs = process.get_global_outputs()
    """
    return MultiRegionalProcess(
        configuration_file=configuration_file,
        custom_models=custom_models,
        disable_execution_statistics=disable_execution_statistics,
    )


def assemble_processes(processes) -> AeroMAPSProcessesAssembly:
    """
    Create a MultiProcess manager for scenario comparison.

    Parameters
    ----------
    processes : dict or list
        Dictionary mapping scenario names to AeroMAPSProcess objects,
        or a list of AeroMAPSProcess objects.

    Returns
    -------
    AeroMAPSProcessesAssembly
        An instance of the MultiProcess class for managing multiple scenarios.

    Examples
    --------
    >>> process1 = create_process(configuration_file="config1.yaml")
    >>> process2 = create_process(configuration_file="config2.yaml")
    >>> process1.compute()
    >>> process2.compute()
    >>> multi = assemble_processes({"scenario_1": process1, "scenario_2": process2})
    >>> multi.list_available_plots()
    >>> multi.plot("co2_emissions_comparison")
    """
    return AeroMAPSProcessesAssembly(processes)

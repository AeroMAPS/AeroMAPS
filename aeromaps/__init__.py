"""
Initialization module for the AeroMAPS package, which provides the function to create an AeroMAPSProcess.
"""

from aeromaps.core.models import default_models_top_down
from aeromaps.core.process import AeroMAPSProcess


def create_process(
    configuration_file=None,
    models=default_models_top_down,
    use_fleet_model=False,
    add_examples_aircraft_and_subcategory=True,
    optimisation=False,
) -> AeroMAPSProcess:
    """
    Create an AeroMAPS process.

    Parameters
    ----------
    configuration_file : str, optional
        Path to the configuration file (default is None).
    models : dict, optional
        Dictionary of models to be used (default is default_models_top_down).
    use_fleet_model : bool, optional
        Whether to use the fleet model (default is False).
    add_examples_aircraft_and_subcategory : bool, optional
        Whether to add example aircraft and subcategories (default is True).
    optimisation : bool, optional
        Whether to enable optimisation (default is False).

    Returns
    -------
    AeroMAPSProcess
        An instance of the AeroMAPSProcess class.
    """

    return AeroMAPSProcess(
        configuration_file=configuration_file,
        models=models,
        use_fleet_model=use_fleet_model,
        add_examples_aircraft_and_subcategory=add_examples_aircraft_and_subcategory,
        optimisation=optimisation,
    )

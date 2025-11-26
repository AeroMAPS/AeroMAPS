# Contains the principal high-level functions of AeroMAPS
from aeromaps.core.models import default_models_top_down
from aeromaps.core.process import AeroMAPSProcess


def create_process(
    configuration_file=None,
    models=default_models_top_down,
    optimisation=False,
) -> AeroMAPSProcess:
    """
    Create an AeroMAPS process.
    """

    return AeroMAPSProcess(
        configuration_file=configuration_file,
        models=models,
        optimisation=optimisation,
    )

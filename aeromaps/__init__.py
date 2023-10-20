# Contains the principal high-level functions of AeroMAPS

from aeromaps.core.process import AeromapsProcess
from aeromaps.core.models import models_simple, models_complex

def create_process(model_type: str = "simple") -> AeromapsProcess:
    """
    Create an AeroMAPS process.

    :param model_type: the type of model to use. Must be either 'simple' or 'complex'.
    :return: an AeroMAPS process
    """

    if model_type == "simple":
        model = models_simple
    elif model_type == "complex":
        model = models_complex
    else:
        raise ValueError("Model type must be 'simple' or 'complex'")

    return AeromapsProcess(models=model, read_json=True)

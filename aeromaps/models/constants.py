from aenum import Enum


# Definition of model type
class ModelType(Enum):
    """
    Enumeration of model type.
    """

    LINEAR = "linear"
    QUADRATIC = "quadratic"
    CUBIC = "cubic"

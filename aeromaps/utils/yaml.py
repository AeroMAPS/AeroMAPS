import yaml
import warnings
from aeromaps.models.base import AeroMapsCustomDataType


def aeromaps_custom_data_type_constructor(loader, node):
    """
    Custom constructor to handle specific interpolation input types in yaml files.

    Parameters
    ----------
    loader : yaml.Loader
        The YAML loader instance.
    node : yaml.Node
        The YAML node to be constructed.
    """
    value = loader.construct_mapping(node, deep=True)
    return AeroMapsCustomDataType(value)


yaml.add_constructor("!AeroMapsCustomDataType", aeromaps_custom_data_type_constructor)


def read_yaml_file(file_name="parameters.yaml"):
    """
    Example function to read a YAML file and returns its contents as a dictionary.

    Parameters
    ----------
    file_name : str
        The path to the YAML file to be read (default is "parameters.yaml").

    Returns
    -------
    dict
        The contents of the YAML file as a dictionary.
    """
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            data = yaml.load(file, Loader=yaml.Loader)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        warnings.warn(f"Error reading YAML file: {e}")
        return {}

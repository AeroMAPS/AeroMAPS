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
    Read a YAML file and return its contents as a dictionary.

    Parameters
    ----------
    file_name : str or None
        The path to the YAML file to be read. If None, returns an empty dict.

    Returns
    -------
    dict
        The contents of the YAML file as a dictionary.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    yaml.YAMLError
        If the file contains invalid YAML.
    ValueError
        If the file does not contain a YAML mapping (dict).
    """
    if file_name is None:
        return {}
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            data = yaml.load(file, Loader=yaml.Loader)
    except FileNotFoundError:
        raise FileNotFoundError(f"YAML file not found: '{file_name}'")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in '{file_name}': {e}") from e
    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a YAML mapping in '{file_name}', got {type(data).__name__}"
        )
    return data

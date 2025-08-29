import yaml

from aeromaps.models.base import AeroMapsCustomDataType


def aeromaps_custom_data_type_constructor(loader, node):
    """
    Custom constructor to handle specific interpolation input types in yaml files.
    """
    value = loader.construct_mapping(node, deep=True)
    return AeroMapsCustomDataType(value)


yaml.add_constructor("!AeroMapsCustomDataType", aeromaps_custom_data_type_constructor)


def read_yaml_file(file_name="parameters.yaml"):
    """Example function to read a YAML file and returns its contents as a dictionary."""
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            data = yaml.load(file, Loader=yaml.Loader)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        return {}

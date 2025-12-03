"""
Utilities for loading, storing, and converting AeroMAPSProcess self.parameters.
"""

from json import dump

from aeromaps.utils.functions import _dict_from_json, _dict_from_parameters_dict


class Parameters:
    """
    Container for AeroMAPSProcess input parameters
    TODO: is that the most appropriate description?


    """

    def to_dict(self):
        """
        Return a dictionary representation of the parameters.

        Returns
        -------
        data
            Dictionary mapping attribute names to their values.
        """
        return self.__dict__

    def from_dict(self, data):
        """
        Update attributes from a dictionary.

        Parameters
        ----------
        data
            Dictionary of parameter names and values to set on the instance.
        """
        for key, value in data.items():
            setattr(self, key, value)

    def write_json(self, file_name="parameters.json"):
        """
        Write parameters to a JSON file.

        Parameters
        ----------
        file_name
            Path to the output JSON file.
        """
        with open(file_name, "w", encoding="utf-8") as f:
            dump(self.to_dict(), f, ignore_nan=True, ensure_ascii=False, indent=4)

    def read_json(self, file_name="parameters.json"):
        """
        Read parameters from a JSON file and update the instance.

        Parameters
        ----------
        file_name
            Path to the input JSON file.
        """
        data = _dict_from_json(file_name=file_name)

        # Old reference data is kept
        self.from_dict(data)

    def read_json_direct(self, parameters_dict):
        """
        Load parameters from a dictionary-like object and update the instance.

        Parameters
        ----------
        parameters_dict
            Dictionary or object containing parameter keys and values.
        """
        data = _dict_from_parameters_dict(parameters_dict)

        # Old reference data is kept
        self.from_dict(data)

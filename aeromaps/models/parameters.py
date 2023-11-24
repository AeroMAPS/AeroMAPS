from dataclasses import asdict
from json import dump
import pandas as pd

from aeromaps.utils.functions import _dict_from_json


class Parameters:
    def to_dict(self):
        data = self.__dict__

        for key, value in data.items():
            if isinstance(value, pd.Series):
                data[key] = list(value)

        return data

    def from_dict(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def write_json(self, file_name="parameters.json"):
        with open(file_name, "w", encoding="utf-8") as f:
            dump(self.to_dict(), f, ignore_nan=True, ensure_ascii=False, indent=4)

    def read_json(self, file_name="parameters.json"):

        data = _dict_from_json(file_name=file_name)

        # Old reference data is kept
        self.from_dict(data)

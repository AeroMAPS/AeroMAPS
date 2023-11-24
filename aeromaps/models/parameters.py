from dataclasses import asdict
from json import dump
import pandas as pd

from aeromaps.utils.functions import _dict_from_json

class Parameters:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attributes = ', '.join(f'{key}={getattr(self, key)}' for key in vars(self))
        return f"Parameters({attributes})"

    def dict(self):
        parameters_dict = self.__dict__

        for key, value in parameters_dict.items():
            if isinstance(value, pd.Series):
                parameters_dict[key] = list(value)

        return parameters_dict

    def write_json(self, file_name="parameters.json"):
        with open(file_name, "w", encoding="utf-8") as f:
            dump(self.dict(), f, ignore_nan=True, ensure_ascii=False, indent=4)

    @classmethod
    def read_json(cls, file_name="parameters.json"):

        data = _dict_from_json(file_name=file_name)

        return cls(**data)

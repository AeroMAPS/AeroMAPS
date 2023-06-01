from dataclasses import dataclass, asdict, field
from json import dump, load
import pandas as pd

from dacite import from_dict

from aeromaps.utils.functions import _dict_from_json

from aeromaps.models.sustainability_assessment.parameters import SustainabilityAssessmentParameters
from aeromaps.models.impacts.parameters import ImpactsParameters
from aeromaps.models.air_transport.parameters import AirTransportParameters


@dataclass
class YearParameters:
    historic_start_year: int = 2000
    prospection_start_year: int = 2020
    end_year: int = 2050


@dataclass
class AllParameters(
    YearParameters, SustainabilityAssessmentParameters, ImpactsParameters, AirTransportParameters
):
    @property
    def __dict__(self):
        parameters_dict = asdict(self)

        for key, value in parameters_dict.items():
            if isinstance(value, pd.Series):
                parameters_dict[key] = list(value)

        return parameters_dict

    def write_json(self, file_name="parameters.json"):
        with open(file_name, "w", encoding="utf-8") as f:
            dump(self.__dict__, f, ignore_nan=True, ensure_ascii=False, indent=4)

    @staticmethod
    def read_json(file_name="parameters.json"):

        parameters_dict = _dict_from_json(file_name=file_name)

        return from_dict(data_class=AllParameters, data=parameters_dict)


all_parameters = AllParameters()

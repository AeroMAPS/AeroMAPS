import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

from aeromaps.models.constants import ModelType


class AeromapsModel(object):
    def __init__(
        self,
        name,
        parameters=None,
    ):
        self.name = name
        self.parameters = parameters
        self.float_outputs = {}
        if self.parameters is not None:
            self._initialize_df()

    def _initialize_df(self):
        self.historic_start_year = self.parameters.historic_start_year
        self.prospection_start_year = self.parameters.prospection_start_year
        self.end_year = self.parameters.end_year
        self.df: pd.DataFrame = pd.DataFrame(
            index=range(self.historic_start_year, self.end_year + 1)
        )
        self.years = np.linspace(self.historic_start_year, self.end_year, len(self.df.index))


def InterpolationAeromapsFunction(self, reference_years, reference_years_values, method='linear'):

    # Init
    for k in range(self.prospection_start_year, self.end_year + 1):
        self.df.loc[k, "interpolation_function_values"] = 0.0

    # Main
    if len(reference_years) == 0:
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "interpolation_function_values"] = reference_years_values
    else:
        interpolation_function = interp1d(
            reference_years,
            reference_years_values,
            kind=method,
        )
        if reference_years[-1] >= self.end_year:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
        else:
            for k in range(self.prospection_start_year, reference_years[-1] + 1):
                self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
            for k in range(reference_years[-1] + 1, self.end_year + 1):
                self.df.loc[k, "interpolation_function_values"] = self.df.loc[
                    k - 1, "interpolation_function_values"
                ]

    interpolation_function_values = self.df.loc[:, "interpolation_function_values"]

    return interpolation_function_values

import pandas as pd
import numpy as np
from scipy.interpolate import interp1d


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


def InterpolationAeromapsFunction(self, reference_years, reference_years_values, method="linear"):

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

    # Delete intermediate df column
    self.df.pop("interpolation_function_values")

    return interpolation_function_values


def LevelingAeromapsFunction(self, reference_periods, reference_periods_values):

    # Main
    if len(reference_periods) == 0:
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "leveling_function_values"] = reference_periods_values
    else:
        if reference_periods[-1] >= self.end_year:
            for i in range(0, len(reference_periods) - 1):
                for k in range(reference_periods[i], reference_periods[i + 1] + 1):
                    self.df.loc[k, "leveling_function_values"] = reference_periods_values[i]
        else:
            for i in range(0, len(reference_periods) - 1):
                for k in range(reference_periods[i], reference_periods[i + 1] + 1):
                    self.df.loc[k, "leveling_function_values"] = reference_periods_values[i]
            for k in range(reference_periods[-1] + 1, self.end_year + 1):
                self.df.loc[k, "leveling_function_values"] = self.df.loc[
                    k - 1, "leveling_function_values"
                ]

    leveling_function_values = self.df.loc[:, "leveling_function_values"]

    # Delete intermediate df column
    self.df.pop("leveling_function_values")

    return leveling_function_values

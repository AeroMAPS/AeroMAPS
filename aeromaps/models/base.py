import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import warnings


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


def AeromapsInterpolationFunction(
    self,
    reference_years,
    reference_years_values,
    method="linear",
    positive_constraint=False,
    model_name="Not provided",
):

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
        if reference_years[-1] == self.end_year:
            for k in range(self.prospection_start_year, reference_years[-1] + 1):
                if positive_constraint and interpolation_function(k) <= 0.0:
                    self.df.loc[k, "interpolation_function_values"] = 0.0
                else:
                    self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
        elif reference_years[-1] > self.end_year:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on AeromapsInterpolationFunction:"
                + " The last reference year for the interpolation is higher than end_year, the interpolation function is therefore not used in its entirety.",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                if positive_constraint and interpolation_function(k) <= 0.0:
                    self.df.loc[k, "interpolation_function_values"] = 0.0
                else:
                    self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
        else:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on AeromapsInterpolationFunction:"
                + " The last reference year for the interpolation is lower than end_year, the value associated to the last reference year is therefore used as a constant for the upper years.",
            )
            for k in range(self.prospection_start_year, reference_years[-1] + 1):
                if positive_constraint and interpolation_function(k) <= 0.0:
                    self.df.loc[k, "interpolation_function_values"] = 0.0
                else:
                    self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
            for k in range(reference_years[-1] + 1, self.end_year + 1):
                self.df.loc[k, "interpolation_function_values"] = self.df.loc[
                    k - 1, "interpolation_function_values"
                ]

    interpolation_function_values = self.df.loc[:, "interpolation_function_values"]

    # Delete intermediate df column
    self.df.pop("interpolation_function_values")

    return interpolation_function_values


def AeromapsLevelingFunction(
    self, reference_periods, reference_periods_values, model_name="Not provided"
):

    # Main
    if len(reference_periods) == 0:
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "leveling_function_values"] = reference_periods_values
    else:
        if reference_periods[-1] == self.end_year:
            for i in range(0, len(reference_periods) - 1):
                for k in range(reference_periods[i], reference_periods[i + 1] + 1):
                    self.df.loc[k, "leveling_function_values"] = reference_periods_values[i]
        elif reference_periods[-1] > self.end_year:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on AeromapsLevelingFunction:"
                + " The last reference year for the leveling is higher than end_year, the leveling function is therefore not used in its entirety.",
            )
            for i in range(0, len(reference_periods) - 1):
                for k in range(reference_periods[i], reference_periods[i + 1] + 1):
                    if k <= self.end_year:
                        self.df.loc[k, "leveling_function_values"] = reference_periods_values[i]
                    else:
                        pass
        else:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on AeromapsLevelingFunction:"
                + " The last reference year for the leveling is lower than end_year, the value associated to the last reference period is therefore used as a constant for the upper period.",
            )
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

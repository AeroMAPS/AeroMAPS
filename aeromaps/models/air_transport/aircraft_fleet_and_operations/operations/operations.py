import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class OperationsLogistic(AeroMAPSModel):
    def __init__(self, name="operations_logistic", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        operations_final_gain: float,
        operations_start_year: int,
        operations_duration: float,
    ) -> pd.Series:
        """Operations gain for efficiency calculation."""

        transition_year = operations_start_year + operations_duration / 2
        operations_limit = 0.02 * operations_final_gain
        operations_parameter = np.log(100 / 2 - 1) / (operations_duration / 2)
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "operations_gain"] = 0
        for k in range(self.prospection_start_year - 1, self.end_year + 1):
            if (
                operations_final_gain / (1 + np.exp(-operations_parameter * (k - transition_year)))
                < operations_limit
            ):
                self.df.loc[k, "operations_gain"] = 0
            else:
                self.df.loc[k, "operations_gain"] = operations_final_gain / (
                    1 + np.exp(-operations_parameter * (k - transition_year))
                )

        operations_gain = self.df["operations_gain"]

        return operations_gain


class OperationsInterpolation(AeroMAPSModel):
    def __init__(self, name="operations_interpolation", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        operations_gain_reference_years: list,
        operations_gain_reference_years_values: list,
    ) -> pd.Series:
        """Operations gain for efficiency calculation."""

        operations_gain_prospective = AeromapsInterpolationFunction(
            self,
            operations_gain_reference_years,
            operations_gain_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "operations_gain"] = operations_gain_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "operations_gain"] = 0
        operations_gain = self.df["operations_gain"]

        return operations_gain

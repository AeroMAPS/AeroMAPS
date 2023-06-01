from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel


class LoadFactor(AeromapsModel):
    def __init__(self, name="load_factor", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        load_factor_end_year: float = 0.0,
        covid_load_factor_2020: float = 0.0,
        rpk: pd.Series = pd.Series(dtype="float64"),
        ask_init: pd.Series = pd.Series(dtype="float64"),
    ) -> pd.Series:
        """Load factor calculation."""

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "load_factor"] = rpk.loc[k] / ask_init.loc[k] * 100

        # Initialization for load factor
        load_factor_2019 = self.df.loc[2019, "load_factor"]

        # Parameters for the model
        a, b = self.parameters_load_factor_model(load_factor_2019, load_factor_end_year)

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "load_factor"] = a * (k - 2019) ** 2 + b * (k - 2019) + load_factor_2019

        # Covid-19 : à refaire proprement
        self.df.loc[2020, "load_factor"] = covid_load_factor_2020

        load_factor = self.df["load_factor"]

        return load_factor

    @staticmethod
    def parameters_load_factor_model(load_factor_2019, load_factor_end_year):
        load_factor_2019 = load_factor_2019
        load_factor_2050 = load_factor_end_year
        # Calculate via derivative : 2ax+b
        derivative = 2 * (-5.62003082e-05) * 31 + 3.59670410e-03
        a = -(load_factor_2050 - load_factor_2019 - derivative * (2050 - 2019)) / (2050 - 2019) ** 2
        b = derivative - 2 * a * (2050 - 2019)
        return [a, b]

from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel


class OperationsContrailsSimple(AeromapsModel):
    def __init__(self, name="operations_contrails_simple", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        operations_contrails_final_gain: float,
        operations_contrails_final_overconsumption: float,
        operations_contrails_start_year: float,
        operations_contrails_duration: float,
    ) -> Tuple[pd.Series, pd.Series]:
        """Operations contrails gain for ERF calculation."""

        transition_year = operations_contrails_start_year + operations_contrails_duration / 2
        operations_contrails_limit = 0.02 * operations_contrails_final_gain
        operations_parameter = np.log(100 / 2 - 1) / (operations_contrails_duration / 2)
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "operations_contrails_gain"] = 0
            self.df.loc[k, "operations_contrails_overconsumption"] = 0
        for k in range(self.prospection_start_year, self.end_year + 1):
            if (
                operations_contrails_final_gain
                / (1 + np.exp(-operations_parameter * (k - transition_year)))
                < operations_contrails_limit
            ):
                self.df.loc[k, "operations_contrails_gain"] = 0
                self.df.loc[k, "operations_contrails_overconsumption"] = 0
            else:
                self.df.loc[k, "operations_contrails_gain"] = operations_contrails_final_gain / (
                    1 + np.exp(-operations_parameter * (k - transition_year))
                )
                self.df.loc[
                    k, "operations_contrails_overconsumption"
                ] = operations_contrails_final_overconsumption / (
                    1 + np.exp(-operations_parameter * (k - transition_year))
                )

        operations_contrails_gain = self.df["operations_contrails_gain"]
        operations_contrails_overconsumption = self.df["operations_contrails_overconsumption"]

        return operations_contrails_gain, operations_contrails_overconsumption

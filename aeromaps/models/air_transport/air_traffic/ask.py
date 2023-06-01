from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel


class ASK(AeromapsModel):
    def __init__(self, name="ask", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        load_factor: pd.Series = pd.Series(dtype="float64"),
        rpk: pd.Series = pd.Series(dtype="float64"),
        rpk_short_range: pd.Series = pd.Series(dtype="float64"),
        rpk_medium_range: pd.Series = pd.Series(dtype="float64"),
        rpk_long_range: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """ASK calculation."""

        # ASK calculation
        ask = rpk / (load_factor / 100)
        self.df.loc[:, "ask"] = ask

        # Short range
        for k in range(self.historic_start_year, self.end_year + 1):
            self.df.loc[k, "ask_short_range"] = rpk_short_range.loc[k] / (load_factor.loc[k] / 100)

        # Medium range
        for k in range(self.historic_start_year, self.end_year + 1):
            self.df.loc[k, "ask_medium_range"] = rpk_medium_range.loc[k] / (
                load_factor.loc[k] / 100
            )

        # Long range
        for k in range(self.historic_start_year, self.end_year + 1):
            self.df.loc[k, "ask_long_range"] = rpk_long_range.loc[k] / (load_factor.loc[k] / 100)

        ask_short_range = self.df["ask_short_range"]
        ask_medium_range = self.df["ask_medium_range"]
        ask_long_range = self.df["ask_long_range"]

        return ask, ask_short_range, ask_medium_range, ask_long_range

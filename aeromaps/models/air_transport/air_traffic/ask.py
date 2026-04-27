"""
ask
===============

Module for computing Available Seat Kilometers (ASK).

``ASK``       — legacy single-model for the hard-coded 3-range structure.
``ASKMarkets`` — per-market version using ``AeroMAPSCustomModelWrapper``.

.. note::
    PHASE-5-CLEANUP: ``ASK`` is a legacy class superseded by ``ASKMarkets``.
    Delete it (and its import in ``models.py``) once the per-market path is
    validated end-to-end.
"""

from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class ASK(AeroMAPSModel):
    """
    Class to compute Available Seat Kilometers (ASK) and its breakdown by range for passenger aircraft, based on load factor and revenue passenger kilometers [RPK].

    Parameters
    ----------
    name : str
        Name of the model instance ('ask' by default).
    """

    def __init__(self, name="ask", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        load_factor: pd.Series,
        rpk: pd.Series,
        rpk_short_range: pd.Series,
        rpk_medium_range: pd.Series,
        rpk_long_range: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Execute the computation of Available Seat Kilometers (ASK) and its breakdown by range.

        Parameters
        ----------
        load_factor
            Annual passenger load factor [%].
        rpk
            Annual RPKs [RPK].
        rpk_short_range
            Annual RPKs for short-range flights [RPK].
        rpk_medium_range
            Annual RPKs for medium-range flights [RPK].
        rpk_long_range
            Annual RPKs for long-range flights [RPK].

        Returns
        -------
        ask
            Annual ASKs [ASK].
        ask_short_range
            ASKs for short-range flights [ASK].
        ask_medium_range
            ASKs for medium-range flights [ASK].
        ask_long_range
            ASKs for long-range flights [ASK].
        """

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


class ASKMarkets(AeroMAPSModel):
    """Per-market ASK for use when a MarketManager is loaded.

    For each passenger market: ``<mid>_ask = <mid>_rpk / (load_factor / 100)``.
    Also outputs the total ``ask`` consumed by downstream models.

    Parameters
    ----------
    name : str
        Discipline name.
    passenger_market_ids : list of str
        Ordered list of passenger market ids.
    """

    def __init__(self, name: str, passenger_market_ids: list, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.passenger_market_ids = list(passenger_market_ids)
        self.input_names = {"load_factor": pd.Series([0.0])}
        for mid in self.passenger_market_ids:
            self.input_names[f"{mid}_rpk"] = pd.Series([0.0])
        self.output_names = {"ask": pd.Series([0.0])}
        for mid in self.passenger_market_ids:
            self.output_names[f"{mid}_ask"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        load_factor = input_data["load_factor"]
        output_data = {}
        total_ask = None

        for mid in self.passenger_market_ids:
            rpk = input_data[f"{mid}_rpk"]
            ask = rpk / (load_factor / 100)
            self.df.loc[:, f"{mid}_ask"] = ask
            output_data[f"{mid}_ask"] = ask
            total_ask = ask if total_ask is None else total_ask + ask

        self.df.loc[:, "ask"] = total_ask
        output_data["ask"] = total_ask

        self._store_outputs(output_data)
        return output_data

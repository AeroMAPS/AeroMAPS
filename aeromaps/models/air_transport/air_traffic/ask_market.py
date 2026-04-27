"""
ask_market
==========

Per-market ASK models for use when a MarketManager is loaded.

Two classes:

* ``ASKMarket``      — ASK for one passenger market.
* ``ASKAggregator``  — sums per-market ASKs into the total ``ask`` consumed
                       by downstream models.

All use ``model_type="custom"`` (``AeroMAPSCustomModelWrapper``).  Input/output
names are built from the market id at construction time.
"""

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class ASKMarket(AeroMAPSModel):
    """ASK for one passenger market: ``<mid>_ask = <mid>_rpk / (load_factor / 100)``.

    Parameters
    ----------
    name : str
        Discipline name.
    market_id : str
        Market identifier (e.g. ``'short_range'``, ``'domestic'``).
    """

    def __init__(self, name: str, market_id: str, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        mid = market_id
        self.market_id = mid
        self.input_names = {
            "load_factor": pd.Series([0.0]),
            f"{mid}_rpk": pd.Series([0.0]),
        }
        self.output_names = {
            f"{mid}_ask": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        mid = self.market_id
        load_factor = input_data["load_factor"]
        rpk = input_data[f"{mid}_rpk"]

        ask = rpk / (load_factor / 100)
        self.df.loc[:, f"{mid}_ask"] = ask

        output_data = {f"{mid}_ask": ask}
        self._store_outputs(output_data)
        return output_data


class ASKAggregator(AeroMAPSModel):
    """Sum per-market ASKs into the total ``ask`` consumed by downstream models.

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
        self.input_names = {}
        for mid in self.passenger_market_ids:
            self.input_names[f"{mid}_ask"] = pd.Series([0.0])
        self.output_names = {
            "ask": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        total_ask = None
        for mid in self.passenger_market_ids:
            series = input_data[f"{mid}_ask"]
            total_ask = series if total_ask is None else total_ask + series

        self.df.loc[:, "ask"] = total_ask

        output_data = {"ask": total_ask}
        self._store_outputs(output_data)
        return output_data

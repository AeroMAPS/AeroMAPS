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
    """ASK for one passenger market: ``<mid>_ask = <mid>_rpk / (<mid>_load_factor / 100)``.

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
            f"load_factor_{mid}": pd.Series([0.0]),
            f"rpk_{mid}": pd.Series([0.0]),
        }
        self.output_names = {
            f"ask_{mid}": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        """Compute ASK for one passenger market from RPK and load factor.

        Parameters
        ----------
        input_data : dict
            Inputs containing market RPK and load factor series.

        Returns
        -------
        dict
            Output dictionary with the market ASK series.
        """
        mid = self.market_id
        load_factor = input_data[f"load_factor_{mid}"]
        rpk = input_data[f"rpk_{mid}"]

        ask = rpk / (load_factor / 100)
        self.df.loc[:, f"ask_{mid}"] = ask

        output_data = {f"ask_{mid}": ask}
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
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
        self.output_names = {
            "ask": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        """Aggregate per-market ASK into the total ASK series.

        Parameters
        ----------
        input_data : dict
            Inputs containing per-market ASK series.

        Returns
        -------
        dict
            Output dictionary with the total ASK series.
        """
        total_ask = None
        for mid in self.passenger_market_ids:
            series = input_data[f"ask_{mid}"]
            total_ask = series if total_ask is None else total_ask + series

        self.df.loc[:, "ask"] = total_ask

        output_data = {"ask": total_ask}
        self._store_outputs(output_data)
        return output_data

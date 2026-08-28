"""
ask_market
==========

Per-market ASK models for use when a MarketManager is loaded.

Two classes:

* ``ASKMarket``      — ASK for one passenger market.
* ``ASKAggregator``  — sums per-market ASKs into the total ``ask`` consumed
                       by downstream models, and publishes each market's share
                       of that total (``ask_<mid>_share``).

All use ``model_type="custom"`` (``AeroMAPSCustomModelWrapper``).  Input/output
names are built from the market id at construction time.
"""

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


def _ask_shares(ask_per_market, total_ask, declared_shares):
    """Each market's share of total ASK [%], defined in every year.

    Downstream models average per-ASK *intensities* -- costs per ASK -- across markets,
    and the weight for that average is a share. Rebuilding the share at the point of
    use, as ``ask_m / sum(ask)``, divides by a total that is zero in any year where no
    market flies: ``0/0``, one NaN that then spreads through every downstream cost and,
    in a cost-feedback MDA, back around the coupling loop.

    So the share is published here instead, once, where the volumes and their total are
    both already at hand.

    In a year where the total *is* zero the volumes carry no information about the
    split, and no manipulation of them will produce one. The weighting then falls back
    to ``<mid>_rpk_share_last_historical_year``, the split the scenario itself declares
    -- the same figure the traffic models use to allocate RPK, and the base of the
    per-market computation to begin with. It is defined by construction rather than
    reconstructed, which is exactly what is wanted in the year where reconstruction is
    impossible.

    A NaN total (the historical years, before any model has written a value) is left as
    NaN: an undefined split is being resolved here, missing data is not being invented.
    """
    shares = {}
    no_traffic = total_ask == 0
    for mid, ask in ask_per_market.items():
        share = ask / total_ask.where(~no_traffic) * 100
        shares[mid] = share.mask(no_traffic, declared_shares[mid])
    return shares


class ASKMarket(AeroMAPSModel):
    """ASK for one passenger market: ``<mid>_ask = <mid>_rpk / (<mid>_load_factor / 100)``.

    Parameters
    ----------
    name : str
        Discipline name.
    market_id : str
        Market identifier (e.g. ``'short_range'``, ``'domestic'``).
    """

    MARKET_SCOPE = "per_market"

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

    Also publishes each market's share of that total, ``ask_<mid>_share``, which is
    what downstream models should weight per-ASK intensities with. Reconstructing the
    weighting from the volumes at the point of use divides by a total that can be zero;
    a share is a share whatever the volumes are. See :func:`_ask_shares` for the year
    where even the shares have to come from somewhere else.

    Parameters
    ----------
    name : str
        Discipline name.
    passenger_market_ids : list of str
        Ordered list of passenger market ids.
    """

    MARKET_SCOPE = "aggregator"

    def __init__(self, name: str, passenger_market_ids: list, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.passenger_market_ids = list(passenger_market_ids)
        self.input_names = {}
        for mid in self.passenger_market_ids:
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            # Fallback weighting for a year with no traffic at all; see _ask_shares.
            self.input_names[f"{mid}_rpk_share_last_historical_year"] = 0.0
        self.output_names = {
            "ask": pd.Series([0.0]),
        }
        for mid in self.passenger_market_ids:
            self.output_names[f"ask_{mid}_share"] = pd.Series([0.0])

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
        ask_per_market = {mid: input_data[f"ask_{mid}"] for mid in self.passenger_market_ids}

        total_ask = None
        for mid in self.passenger_market_ids:
            series = ask_per_market[mid]
            total_ask = series if total_ask is None else total_ask + series

        self.df.loc[:, "ask"] = total_ask

        output_data = {"ask": total_ask}

        declared_shares = {
            mid: float(input_data[f"{mid}_rpk_share_last_historical_year"])
            for mid in self.passenger_market_ids
        }
        for mid, share in _ask_shares(ask_per_market, total_ask, declared_shares).items():
            self.df.loc[:, f"ask_{mid}_share"] = share
            output_data[f"ask_{mid}_share"] = share

        self._store_outputs(output_data)
        return output_data

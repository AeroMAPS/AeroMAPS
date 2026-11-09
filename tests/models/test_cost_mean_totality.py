"""The global cost means must stay defined in a year with no traffic.

The global mean of a per-ASK cost is an average of *intensities*, so its weight is a
share. Rebuilding that share from the volumes at the point of use -- ``ask_m / sum(ask)``
-- divides by a total that is zero in any year where no market flies. The resulting NaN
does not stay put in a cost-feedback MDA: it spreads through every downstream cost and
back around the coupling loop, where the residual then reports it as convergence,
because AeroMAPS' NaN sentinel differences against itself to exactly zero.

So the share is published once by ``ASKAggregator``, where the split is known even in
that year, and the cost models weight by it. Two things need pinning, and they live in
two different places:

* ``_ask_shares`` -- the split is defined in every year, and sums to 100.
* ``_ask_share_weighted_mean`` -- the mean is the share-weighted sum, and is the same
  number the old volume-weighted form produced wherever there was traffic.
"""

import numpy as np
import pandas as pd
import pytest

from aeromaps.models.air_transport.air_traffic.ask_market import _ask_shares
from aeromaps.models.impacts.costs.airlines.direct_operating_costs import (
    _ask_share_weighted_mean,
)


def _series(values):
    return pd.Series(values, index=pd.RangeIndex(len(values)), dtype=float)


def _frames(means, shares):
    index = pd.RangeIndex(len(next(iter(means.values()))))
    return (
        {mid: pd.Series(v, index=index, dtype=float) for mid, v in means.items()},
        {mid: pd.Series(v, index=index, dtype=float) for mid, v in shares.items()},
        index,
    )


def _shares_from(asks, declared):
    ask_per_market = {mid: _series(v) for mid, v in asks.items()}
    total = sum(ask_per_market.values())
    return _ask_shares(ask_per_market, total, declared)


# --------------------------------------------------------------------------------
# The shares themselves
# --------------------------------------------------------------------------------


def test_shares_are_the_volume_split_where_there_is_traffic():
    shares = _shares_from(
        {"short": [100.0, 300.0], "long": [300.0, 100.0]},
        {"short": 27.2, "long": 72.8},
    )
    assert shares["short"].to_numpy() == pytest.approx([25.0, 75.0])
    assert shares["long"].to_numpy() == pytest.approx([75.0, 25.0])


def test_shares_sum_to_one_hundred_in_every_year():
    shares = _shares_from(
        {"short": [100.0, 0.0, 7.0], "long": [300.0, 0.0, 3.0]},
        {"short": 27.2, "long": 72.8},
    )
    total = sum(shares.values())
    assert total.to_numpy() == pytest.approx([100.0, 100.0, 100.0])


def test_a_year_with_no_traffic_falls_back_to_the_declared_split():
    """The volumes carry no information about the split; the scenario's does."""
    shares = _shares_from(
        {"short": [100.0, 0.0], "long": [300.0, 0.0]},
        {"short": 27.2, "long": 72.8},
    )
    assert shares["short"].to_numpy() == pytest.approx([25.0, 27.2])
    assert shares["long"].to_numpy() == pytest.approx([75.0, 72.8])
    assert np.isfinite(np.concatenate([s.to_numpy() for s in shares.values()])).all()


def test_a_single_empty_market_simply_carries_no_weight():
    """The partial case needs no special handling, and must not get any."""
    shares = _shares_from(
        {"short": [100.0], "long": [0.0]},
        {"short": 27.2, "long": 72.8},
    )
    assert shares["short"].to_numpy() == pytest.approx([100.0])
    assert shares["long"].to_numpy() == pytest.approx([0.0])


def test_a_nan_total_stays_nan():
    """The historical years, before any model has written a value.

    An undefined split is being resolved here; missing data is not being invented.
    """
    shares = _shares_from(
        {"short": [np.nan, 100.0], "long": [np.nan, 300.0]},
        {"short": 27.2, "long": 72.8},
    )
    assert np.isnan(shares["short"].iloc[0])
    assert shares["short"].iloc[1] == pytest.approx(25.0)


# --------------------------------------------------------------------------------
# The defect itself, reproduced
# --------------------------------------------------------------------------------


def _volume_weighted_mean(means, asks):
    """The pre-#157 global mean, verbatim: ``sum(ask_m * mean_m) / sum(ask_m)``.

    Kept here so the failure it produced can be exhibited next to the fix rather than
    only described. Nothing in the package calls this any more.
    """
    ask_total = sum(asks.values())
    return sum(means[mid] * asks[mid] for mid in means) / ask_total


def test_the_old_volume_weighting_returned_nan_in_a_year_with_no_traffic():
    """The defect: ``0/0``. This is what used to reach every downstream cost."""
    asks = {"short": _series([100.0, 0.0]), "long": _series([300.0, 0.0])}
    means = {"short": _series([2.0, 3.0]), "long": _series([6.0, 9.0])}

    old = _volume_weighted_mean(means, asks)

    assert not np.isnan(old.iloc[0]), "the ordinary year was never the problem"
    assert np.isnan(old.iloc[1]), "expected 0/0; this test no longer reproduces anything"


def test_the_share_weighted_form_gives_a_number_in_the_same_year():
    """The fix, on the identical inputs."""
    asks = {"short": [100.0, 0.0], "long": [300.0, 0.0]}
    means, _, index = _frames({"short": [2.0, 3.0], "long": [6.0, 9.0]}, asks)
    shares = _shares_from(asks, {"short": 25.0, "long": 75.0})

    new = _ask_share_weighted_mean(means, shares, index)

    assert np.isfinite(new.to_numpy()).all()
    assert new.iloc[1] == pytest.approx(7.5)  # 3*0.25 + 9*0.75, the declared split


def test_the_nan_used_to_spread_through_everything_downstream():
    """Why one undefined year mattered: nothing downstream stops it.

    The global mean feeds the total cost, the total cost feeds the fare, the fare feeds
    demand -- ordinary arithmetic all the way, so the NaN reaches the end of the chain
    in that year. In a cost-feedback MDA the fare is a coupling variable, so it is handed
    back in as an input on the next iteration and the NaN outlives the year that made it.
    """
    asks = {"only": _series([100.0, 0.0])}
    means = {"only": _series([2.0, 3.0])}

    doc_mean = _volume_weighted_mean(means, asks)
    total_cost = doc_mean + 0.01  # + NOC, IOC, offsets...
    airfare = total_cost * 1.05  # + operational profit

    assert np.isfinite(airfare.iloc[0])
    assert np.isnan(airfare.iloc[1]), "one undefined weighting, and the fare is gone"


# --------------------------------------------------------------------------------
# The mean that consumes them
# --------------------------------------------------------------------------------


def test_ordinary_years_take_the_share_weighted_mean():
    means, shares, index = _frames(
        {"short": [2.0, 4.0], "long": [6.0, 8.0]},
        {"short": [25.0, 75.0], "long": [75.0, 25.0]},
    )
    result = _ask_share_weighted_mean(means, shares, index)
    # 2*0.25 + 6*0.75 = 5.0 ; 4*0.75 + 8*0.25 = 5.0
    assert result.to_numpy() == pytest.approx([5.0, 5.0])


def test_share_weighting_matches_volume_weighting_where_there_is_traffic():
    """The reformulation must be the identity wherever the old form was defined."""
    asks = {"short": [100.0, 300.0, 42.0], "long": [300.0, 100.0, 58.0]}
    means, _, index = _frames({"short": [2.0, 4.0, 11.0], "long": [6.0, 8.0, 13.0]}, asks)
    shares = _shares_from(asks, {"short": 27.2, "long": 72.8})

    ask_per_market = {mid: _series(v) for mid, v in asks.items()}
    volume_weighted = sum(means[mid] * ask_per_market[mid] for mid in means) / sum(
        ask_per_market.values()
    )

    result = _ask_share_weighted_mean(means, shares, index)
    assert result.to_numpy() == pytest.approx(volume_weighted.to_numpy())


def test_a_year_with_no_traffic_at_all_is_still_a_real_cost():
    """Not NaN, and emphatically not zero: the intensities are still defined."""
    asks = {"short": [100.0, 0.0], "long": [300.0, 0.0]}
    means, _, index = _frames({"short": [2.0, 3.0], "long": [6.0, 9.0]}, asks)
    shares = _shares_from(asks, {"short": 25.0, "long": 75.0})

    result = _ask_share_weighted_mean(means, shares, index)

    assert result.to_numpy() == pytest.approx([5.0, 7.5])  # 3*0.25 + 9*0.75
    assert np.isfinite(result.to_numpy()).all()
    assert result.iloc[1] != 0.0


def test_the_no_traffic_fallback_is_not_zero_even_when_costs_are_high():
    """Guards against a regression to a fabricated 0.0."""
    asks = {"only": [0.0]}
    means, _, index = _frames({"only": [1234.5]}, asks)
    shares = _shares_from(asks, {"only": 100.0})
    result = _ask_share_weighted_mean(means, shares, index)
    assert result.to_numpy() == pytest.approx([1234.5])


def test_a_pre_existing_nan_is_left_alone():
    """The fallback resolves an undefined weighting; it does not fill missing data."""
    means, shares, index = _frames(
        {"short": [np.nan, 2.0]},
        {"short": [100.0, 100.0]},
    )
    result = _ask_share_weighted_mean(means, shares, index)
    assert np.isnan(result.iloc[0])
    assert result.iloc[1] == pytest.approx(2.0)


def test_no_passenger_markets_defaults_to_zero():
    index = pd.RangeIndex(3)
    result = _ask_share_weighted_mean({}, {}, index)
    assert result.to_numpy() == pytest.approx([0.0, 0.0, 0.0])

"""The global ASK-weighted cost means must stay defined in a year with no traffic.

When every passenger market has zero ASK, the weighted mean is ``0/0`` and pandas
returns NaN. In a cost-feedback MDA that NaN does not stay put: it spreads through
every downstream cost and back around the coupling loop, where the residual then
reports it as convergence, because AeroMAPS' NaN sentinel differences against itself
to exactly zero.

Substituting zero would be no better -- there is no *zero* cost per ASK where there is
no traffic, and reporting one invents a number that was never computed. What is
undefined in such a year is only the *weighting*: the quantity being averaged is an
intensity, so each market's cost per ASK is still well defined. Those years take the
unweighted mean instead.

These tests pin all three cases: the ordinary weighted path, the partial case where
only some markets are empty, and the degenerate case where none has traffic.
"""

import numpy as np
import pandas as pd
import pytest

from aeromaps.models.impacts.costs.airlines.direct_operating_costs import _ask_weighted_mean


def _frames(means, asks):
    index = pd.RangeIndex(len(next(iter(means.values()))))
    return (
        {mid: pd.Series(v, index=index, dtype=float) for mid, v in means.items()},
        {mid: pd.Series(v, index=index, dtype=float) for mid, v in asks.items()},
        index,
    )


def test_ordinary_years_take_the_ask_weighted_mean():
    means, asks, index = _frames(
        {"short": [2.0, 4.0], "long": [6.0, 8.0]},
        {"short": [100.0, 300.0], "long": [300.0, 100.0]},
    )
    result = _ask_weighted_mean(means, asks, index)
    # (2*100 + 6*300)/400 = 5.0 ; (4*300 + 8*100)/400 = 5.0
    assert result.to_numpy() == pytest.approx([5.0, 5.0])


def test_a_single_empty_market_simply_carries_no_weight():
    """The partial case needs no special handling, and must not get any."""
    means, asks, index = _frames(
        {"short": [2.0], "long": [6.0]},
        {"short": [100.0], "long": [0.0]},
    )
    result = _ask_weighted_mean(means, asks, index)
    assert result.to_numpy() == pytest.approx([2.0])


def test_a_year_with_no_traffic_at_all_takes_the_unweighted_mean():
    """Not NaN, and emphatically not zero: the intensities are still defined."""
    means, asks, index = _frames(
        {"short": [2.0, 3.0], "long": [6.0, 9.0]},
        {"short": [100.0, 0.0], "long": [300.0, 0.0]},
    )
    result = _ask_weighted_mean(means, asks, index)

    assert result.to_numpy() == pytest.approx([5.0, 6.0])  # (3+9)/2 = 6
    assert np.isfinite(result.to_numpy()).all()
    assert result.iloc[1] != 0.0


def test_the_no_traffic_fallback_is_not_zero_even_when_costs_are_high():
    """Guards against a regression to a fabricated 0.0."""
    means, asks, index = _frames({"only": [1234.5]}, {"only": [0.0]})
    result = _ask_weighted_mean(means, asks, index)
    assert result.to_numpy() == pytest.approx([1234.5])


def test_a_pre_existing_nan_is_left_alone():
    """The fallback resolves an undefined weighting; it does not fill missing data."""
    means, asks, index = _frames(
        {"short": [np.nan, 2.0]},
        {"short": [100.0, 200.0]},
    )
    result = _ask_weighted_mean(means, asks, index)
    assert np.isnan(result.iloc[0])
    assert result.iloc[1] == pytest.approx(2.0)


def test_no_passenger_markets_defaults_to_zero():
    index = pd.RangeIndex(3)
    result = _ask_weighted_mean({}, {}, index)
    assert result.to_numpy() == pytest.approx([0.0, 0.0, 0.0])

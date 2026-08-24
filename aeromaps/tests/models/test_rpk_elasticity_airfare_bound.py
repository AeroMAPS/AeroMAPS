"""``RPKElasticity`` must stay defined on the airfares an MDA iterate can carry.

A converging fixed-point solver does not only evaluate models at plausible points.
GEMSEO's acceleration methods extrapolate the coupling vector by unconstrained least
squares, with no notion of variable bounds, so this discipline can be handed an
airfare no discipline ever produced -- a negative one, for instance.

That matters because the multiplier raises the airfare ratio to ``price_elasticity``,
which is fractional. ``numpy`` returns ``nan`` for a negative float64 base under a
fractional exponent, silently, where plain Python would return a complex number. In
the unified-MDA spike this single operation turned a solver excursion into a
chain-wide NaN that the residual then reported as *convergence*, because the NaN
sentinel differences against itself to exactly zero.

These tests pin three things: the hole is closed, the bound is *inactive* on ordinary
airfares so it cannot move a converged answer, and it says so out loud when it fires.
"""

import warnings

import numpy as np
import pandas as pd
import pytest

from aeromaps.models.air_transport.air_traffic.rpk_market import RPKElasticity

HISTORIC_START, PROSPECTION_START, END = 2000, 2020, 2050
INITIAL_AIRFARE = 0.09236379319842411  # EUR/RPK, the 2019 reference
LOW_FACTOR, HIGH_FACTOR = RPKElasticity.AIRFARE_BOUNDS_RELATIVE


class _Parameters:
    """Minimal stand-in for the process parameters object a model needs to build ``df``."""

    climate_historic_start_year = 1940
    historic_start_year = HISTORIC_START
    prospection_start_year = PROSPECTION_START
    end_year = END


def _series(value):
    return pd.Series(float(value), index=range(HISTORIC_START, END + 1))


def _build():
    return RPKElasticity(
        name="rpk_elasticity",
        passenger_market_ids=["short_range"],
        parameters=_Parameters(),
    )


def _inputs(airfare, initial_airfare=INITIAL_AIRFARE):
    return {
        "rpk_no_elasticity": _series(1.0e12),
        "airfare_per_rpk": airfare,
        "price_elasticity": -0.9,
        "initial_airfare_per_rpk": initial_airfare,
        "rpk_short_range_no_elasticity": _series(1.0e12),
        "short_range_covid_end_year": float(PROSPECTION_START - 1),
    }


def _compute(airfare, initial_airfare=INITIAL_AIRFARE):
    """Run ``compute`` ignoring the bound warning, which its own tests cover."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return _build().compute(_inputs(airfare, initial_airfare))


# ------------------------------------------------------------------ the hole itself


def test_negative_airfare_gives_finite_outputs():
    """The exact failure found in the spike: a negative airfare used to give NaN.

    Values taken from the first manufacture measured there -- the airfare falling to
    -2.11 EUR/RPK against the 0.0924 reference, i.e. a ratio of -22.9.
    """
    airfare = _series(0.09)
    airfare.loc[2041:END] = np.linspace(-0.0227, -2.11219, END - 2041 + 1)

    output = _compute(airfare)

    assert np.isfinite(output["elasticity_factor"].to_numpy()).all()
    assert np.isfinite(output["rpk"].to_numpy()).all()
    assert np.isfinite(output["rpk_short_range"].to_numpy()).all()
    assert np.isfinite(float(output["cagr_rpk"]))

    # Saturation, not an arbitrary value: a negative airfare is treated as the
    # cheapest the band allows, so demand sits at the band's upper response.
    assert output["elasticity_factor"].loc[END] == pytest.approx(LOW_FACTOR**-0.9)


def test_zero_airfare_gives_finite_outputs():
    """Zero is the other end of the hole: it gives +inf under a negative elasticity."""
    output = _compute(_series(0.0))
    assert np.isfinite(output["elasticity_factor"].to_numpy()).all()
    assert np.isfinite(output["rpk"].to_numpy()).all()


def test_infinite_airfare_gives_finite_outputs():
    output = _compute(_series(np.inf))
    assert np.isfinite(output["elasticity_factor"].to_numpy()).all()
    assert output["elasticity_factor"].loc[END] == pytest.approx(HIGH_FACTOR**-0.9)


# --------------------------------------------------- the bound must not move answers


def test_ordinary_airfare_is_untouched():
    """The bound must be inactive in band, or it would move converged scenarios."""
    output = _compute(_series(INITIAL_AIRFARE * 1.4))
    projected = output["elasticity_factor"].loc[PROSPECTION_START:END]
    assert projected.to_numpy() == pytest.approx(1.4**-0.9)


def test_bound_engages_only_outside_the_band():
    """Pin where the bound engages, so widening or narrowing it is a visible change."""
    just_inside = _compute(_series(INITIAL_AIRFARE * HIGH_FACTOR * 0.99))
    just_outside = _compute(_series(INITIAL_AIRFARE * HIGH_FACTOR * 1.01))

    assert just_inside["elasticity_factor"].loc[END] == pytest.approx((HIGH_FACTOR * 0.99) ** -0.9)
    assert just_outside["elasticity_factor"].loc[END] == pytest.approx(HIGH_FACTOR**-0.9)


# ------------------------------------------------------------------- the warning


def _bound_warnings(record):
    """Only this model's bound warning -- pandas emits unrelated FutureWarnings."""
    return [w for w in record if "airfare_per_rpk left the" in str(w.message)]


def test_bounding_warns_with_the_old_and_the_new_airfare():
    airfare = _series(0.09)
    airfare.loc[2041:END] = np.linspace(-0.0227, -2.11219, END - 2041 + 1)

    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        _build().compute(_inputs(airfare))

    bound = _bound_warnings(record)
    assert len(bound) == 1, "one warning per compute(), not one per year"
    message = str(bound[0].message)

    assert "airfare_per_rpk" in message
    assert "2041-2050" in message
    assert "10 year(s)" in message
    # The old airfare and the value it was replaced by, as asked for.
    assert "-2.11219" in message
    assert f"{INITIAL_AIRFARE * LOW_FACTOR:.6g}" in message


def test_ordinary_airfare_does_not_warn():
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        _build().compute(_inputs(_series(INITIAL_AIRFARE * 1.4)))

    assert _bound_warnings(record) == []


def test_nan_airfare_does_not_warn_and_stays_nan():
    """A missing value is not a bounded value: it is not the bound's business."""
    airfare = _series(INITIAL_AIRFARE)
    airfare.loc[2041:END] = np.nan

    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        output = _build().compute(_inputs(airfare))

    assert _bound_warnings(record) == []
    assert output["elasticity_factor"].loc[2041:END].isna().all()

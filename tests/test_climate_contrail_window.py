"""
test_climate_contrail_window
============================

Guards the year window over which the contrail fuel-effect correction is
applied in :class:`~aeromaps.models.impacts.climate.climate.ClimateModel`.

Background
----------
``ClimateModel.compute`` first seeds ``contrails_distance_corrected`` with the
raw aircraft distance over the full climate window, then overwrites a second
slice with ``distance * (1 - gain/100) * fuel_effect_correction_contrails``.

``fuel_effect_correction_contrails`` is built from pathway massic shares, which
only exist from ``prospection_start_year`` onwards -- it is exactly 0.0 over the
historic period. When that second slice started at ``historic_start_year`` the
multiplication silently zeroed every historic year, destroying all historic
contrail forcing: total aviation ERF in 2018 read 49.5 mW/m2 against the
~100.9 mW/m2 of Lee et al. (2021), the gap being almost exactly Lee's
contrail-cirrus term. With the window corrected the same scenario reads
100.4 mW/m2.

What is tested
--------------
1. The corrected distance is strictly positive across the whole climate window,
   at several ``prospection_start_year`` settings (the boundary is a
   configurable parameter, so the guard must hold at each).
2. Over the historic period the corrected distance equals the raw distance,
   i.e. no correction leaks in where it is undefined.
3. Over the prospective period the correction *is* applied.
4. Historic contrail ERF is non-zero -- the observable the bug destroyed.

The real ``compute`` is exercised end to end (AeroCM included) against
synthetic inputs, so a regression in the slice bounds fails the test.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from aeromaps.models.impacts.climate.climate import ClimateModel


CLIMATE_HISTORIC_START = 1940
HISTORIC_START = 2000
END_YEAR = 2050
CORRECTION = 0.9  # non-trivial prospective correction, distinguishable from 1.0


def _make_model(prospection_start_year):
    """A ClimateModel with the year attributes and dataframe the process injects."""
    model = ClimateModel.__new__(ClimateModel)
    model.climate_model = "LWE"
    model.species_settings = None
    model.model_settings = None
    model.name = "climate"
    model.climate_historic_start_year = CLIMATE_HISTORIC_START
    model.historic_start_year = HISTORIC_START
    model.prospection_start_year = prospection_start_year
    model.end_year = END_YEAR
    model.mapping = {
        "Total": "total",
        "CO2": "co2",
        "Non-CO2": "non_co2",
        "Contrails": "contrails",
        "NOx - ST O3 increase": "nox_short_term_o3_increase",
        "NOX - CH4 induced O3": "nox_long_term_o3_decrease",
        "NOX - CH4 decrease": "nox_ch4_decrease",
        "NOX - CH4 induced H2O": "nox_stratospheric_water_vapor_decrease",
        "H2O": "h2o",
        "Sulfur": "sulfur",
        "Soot": "soot",
        "Aerosols": "aerosol",
    }
    model.df_climate = pd.DataFrame(
        index=pd.Index(range(CLIMATE_HISTORIC_START, END_YEAR + 1), name="year")
    )
    return model


def _make_inputs(prospection_start_year):
    """Synthetic inputs mirroring the real shape of each series.

    ``fuel_effect_correction_contrails`` is zero before ``prospection_start_year``
    and non-zero after it, exactly as the pathway-share model produces it.
    """
    climate_years = list(range(CLIMATE_HISTORIC_START, END_YEAR + 1))
    model_years = list(range(HISTORIC_START, END_YEAR + 1))
    n = len(climate_years)

    distance = pd.Series(np.linspace(1.0e9, 1.4e11, n), index=climate_years)
    co2 = pd.Series(np.linspace(30.0, 1100.0, n), index=climate_years)

    correction = pd.Series(0.0, index=model_years)
    correction.loc[prospection_start_year:] = CORRECTION

    return {
        "total_aircraft_distance": distance,
        "co2_emissions": co2,
        "nox_emissions": co2 * 4.0e-3,
        "h2o_emissions": co2 * 0.4,
        "soot_emissions": co2 * 2.0e-6,
        "sulfur_emissions": co2 * 4.0e-5,
        "fuel_effect_correction_contrails": correction,
        "operations_contrails_gain": pd.Series(0.0, index=model_years),
    }


@pytest.fixture(scope="module")
def computed():
    """Run the real compute once per prospection_start_year under test."""
    out = {}
    for year in (2020, 2024, 2025):
        model = _make_model(year)
        inputs = _make_inputs(year)
        model.compute(inputs)
        out[year] = (model, inputs)
    return out


@pytest.mark.parametrize("prospection_start_year", [2020, 2024, 2025])
def test_contrail_distance_never_zeroed(computed, prospection_start_year):
    """No year of the climate window may lose its contrail distance."""
    model, _ = computed[prospection_start_year]
    corrected = model.df_climate["contrails_distance_corrected"]

    assert corrected.notna().all(), "corrected contrail distance has NaN years"
    assert (corrected > 0).all(), (
        "corrected contrail distance is zero for years "
        f"{corrected.index[corrected <= 0].tolist()}"
    )


@pytest.mark.parametrize("prospection_start_year", [2020, 2024, 2025])
def test_historic_years_keep_raw_distance(computed, prospection_start_year):
    """The correction must not be applied where it is undefined."""
    model, inputs = computed[prospection_start_year]
    historic = slice(CLIMATE_HISTORIC_START, prospection_start_year - 1)

    pd.testing.assert_series_equal(
        model.df_climate.loc[historic, "contrails_distance_corrected"],
        inputs["total_aircraft_distance"].loc[historic],
        check_names=False,
        check_index_type=False,
    )


@pytest.mark.parametrize("prospection_start_year", [2020, 2024, 2025])
def test_prospective_years_are_corrected(computed, prospection_start_year):
    """The correction is still applied over the prospective period."""
    model, inputs = computed[prospection_start_year]
    prospective = slice(prospection_start_year, END_YEAR)

    pd.testing.assert_series_equal(
        model.df_climate.loc[prospective, "contrails_distance_corrected"],
        inputs["total_aircraft_distance"].loc[prospective] * CORRECTION,
        check_names=False,
        check_index_type=False,
    )


@pytest.mark.parametrize("prospection_start_year", [2020, 2024, 2025])
def test_historic_contrail_forcing_is_non_zero(computed, prospection_start_year):
    """The observable the bug destroyed: historic contrail ERF must exist."""
    model, _ = computed[prospection_start_year]
    historic_erf = model.df_climate.loc[
        HISTORIC_START : prospection_start_year - 1, "contrails_erf"
    ]

    assert (historic_erf > 0).all(), (
        "historic contrail ERF is zero for years "
        f"{historic_erf.index[historic_erf <= 0].tolist()}"
    )

"""
Regression tests for the sub-lever decomposition of CO2 emissions.

The three decomposition models are "exact by construction": the sum of the
sub-lever contributions (including their residual / cross-mix terms) must equal
the corresponding global lever of action computed by DetailedCo2Emissions.

* DetailedCo2EmissionsPerAircraft : aircraft efficiency lever, per aircraft.
* DetailedCo2EmissionsPerPathway  : aircraft energy lever, per energy pathway.
* DetailedCo2EmissionsPerMarket   : every lever, per market (+ cross-mix).

These tests lock that invariant against the bottom-up, multi-market
``config_advanced`` scenario so any future change that breaks the additivity is
caught in CI.
"""

import os

import pytest
from aeromaps import create_process
from aeromaps.models.impacts.emissions.co2_emissions import (
    market_lever_dataframe,
    market_lever_names,
)

CONFIG = os.path.join(os.path.dirname(__file__), "..", "tested_configs", "config_advanced.yaml")

# The decomposition residuals are exact up to floating-point accumulation over
# the ~15 sub-levers; MtCO2 magnitudes are O(1e3), so 1e-6 is a safe tolerance.
TOL = 1e-6


@pytest.fixture(scope="module")
def process():
    proc = create_process(configuration_file=CONFIG)
    proc.compute()
    return proc


@pytest.fixture(scope="module")
def outputs(process):
    df = process.data["vector_outputs"]
    years = list(
        range(int(process.parameters.prospection_start_year), process.parameters.end_year + 1)
    )
    return df, years


def _max_abs(series, years):
    return float(series.loc[years].abs().max())


def test_efficiency_lever_decomposed_per_aircraft(process, outputs):
    df, years = outputs
    global_lever = (
        df["co2_emissions_last_historical_year_technology"]
        - df["co2_emissions_including_aircraft_efficiency"]
    )
    # The per-market efficiency columns share the "..._lever_efficiency_" prefix
    # but belong to a different decomposition, so exclude them explicitly.
    market_columns = set(market_lever_names(process.markets).values())
    sub_levers = [
        c
        for c in df.columns
        if c.startswith("co2_emissions_lever_efficiency_") and c not in market_columns
    ]
    assert sub_levers, "per-aircraft efficiency sub-levers missing"
    residual = global_lever - df[sub_levers].sum(axis=1)
    assert _max_abs(residual, years) < TOL


def test_energy_lever_decomposed_per_pathway(process, outputs):
    df, years = outputs
    global_lever = df["co2_emissions_including_load_factor"] - df["co2_emissions_including_energy"]
    market_columns = set(market_lever_names(process.markets).values())
    sub_levers = [
        c
        for c in df.columns
        if c.startswith("co2_emissions_lever_energy_") and c not in market_columns
    ]
    assert sub_levers, "per-pathway energy sub-levers missing"
    residual = global_lever - df[sub_levers].sum(axis=1)
    assert _max_abs(residual, years) < TOL


@pytest.mark.parametrize(
    "lever, upper, lower",
    [
        (
            "efficiency",
            "co2_emissions_last_historical_year_technology",
            "co2_emissions_including_aircraft_efficiency",
        ),
        (
            "operations",
            "co2_emissions_including_aircraft_efficiency",
            "co2_emissions_including_operations",
        ),
        (
            "loadfactor",
            "co2_emissions_including_operations",
            "co2_emissions_including_load_factor",
        ),
        (
            "energy",
            "co2_emissions_including_load_factor",
            "co2_emissions_including_energy",
        ),
    ],
)
def test_lever_decomposed_per_market(process, outputs, lever, upper, lower):
    df, years = outputs
    global_lever = df[upper] - df[lower]
    # Use the tidy (lever, market) accessor rather than ad-hoc prefix matching.
    per_market = market_lever_dataframe(df, process.markets)
    lever_view = per_market.xs(lever, level="lever", axis=1)
    assert not lever_view.empty, f"per-market {lever} sub-levers missing"
    # Sum over markets *and* the cross-market-mix residual must equal the global lever.
    residual = global_lever - lever_view.sum(axis=1)
    assert _max_abs(residual, years) < TOL


def test_market_lever_dataframe_is_tidy(process, outputs):
    df, _ = outputs
    per_market = market_lever_dataframe(df, process.markets)
    assert list(per_market.columns.names) == ["lever", "market"]
    # Filtering by a single market returns all of its available levers.
    short_range = per_market.xs("short_range", level="market", axis=1)
    assert set(short_range.columns) == {"efficiency", "operations", "loadfactor", "energy"}
    # Freight has no load-factor lever.
    freight = per_market.xs("freight", level="market", axis=1)
    assert "loadfactor" not in freight.columns

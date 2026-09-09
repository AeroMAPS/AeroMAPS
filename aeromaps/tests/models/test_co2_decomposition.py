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
import shutil

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


# --- Continuous improvement of the recent reference aircraft ---------------------
#
# The fleet model measures every aircraft contribution against the recent
# reference *including its own* continuous improvement factor, so the drift of
# that baseline must be reported as its own sub-lever, not left in the residual.

CIF_BLOCK = """      continuous_improvement_factor_energy: !AeroMapsCustomDataType
        years: [2020, 2050]
        values: [1.0, 0.8]
        method: linear
"""


@pytest.fixture(scope="module")
def process_with_continuous_improvement(tmp_path_factory):
    """config_advanced with a 20 % continuous improvement on every recent reference."""
    root = tmp_path_factory.mktemp("cif")
    source = os.path.dirname(CONFIG)
    shutil.copy(CONFIG, root / "config_advanced.yaml")
    shutil.copytree(os.path.join(source, "data"), root / "data")

    inventory = root / "data" / "aircraft_inventory.yaml"
    lines = inventory.read_text().splitlines(keepends=True)
    patched, in_recent_reference = [], False
    for line in lines:
        if line.startswith("  - id:"):
            in_recent_reference = line.rstrip().endswith("_recent")
        patched.append(line)
        if in_recent_reference and line.startswith("      energy_per_ask:"):
            patched.append(CIF_BLOCK)
    inventory.write_text("".join(patched))

    proc = create_process(configuration_file=str(root / "config_advanced.yaml"))
    proc.compute()
    return proc


def test_continuous_improvement_is_its_own_sub_lever(process, process_with_continuous_improvement):
    df_reference = process.data["vector_outputs"]
    df = process_with_continuous_improvement.data["vector_outputs"]
    years = list(
        range(
            int(process.parameters.prospection_start_year),
            process.parameters.end_year + 1,
        )
    )
    end_year = years[-1]

    # Without a factor the sub-lever is identically zero; with one it carries the gain.
    assert (
        _max_abs(df_reference["co2_emissions_lever_efficiency_continuous_improvement"], years) == 0
    )
    assert df.loc[end_year, "co2_emissions_lever_efficiency_continuous_improvement"] > 1.0

    # The residual is a pure traffic-mix term: it only depends on reference-year
    # intensities and on the traffic split, so it must not move with the factor.
    residual_shift = (
        df["co2_emissions_lever_efficiency_other"]
        - df_reference["co2_emissions_lever_efficiency_other"]
    )
    assert _max_abs(residual_shift, years) < TOL

    # And the decomposition still closes exactly on the global lever.
    global_lever = (
        df["co2_emissions_last_historical_year_technology"]
        - df["co2_emissions_including_aircraft_efficiency"]
    )
    market_columns = set(market_lever_names(process_with_continuous_improvement.markets).values())
    sub_levers = [
        c
        for c in df.columns
        if c.startswith("co2_emissions_lever_efficiency_") and c not in market_columns
    ]
    assert _max_abs(global_lever - df[sub_levers].sum(axis=1), years) < TOL

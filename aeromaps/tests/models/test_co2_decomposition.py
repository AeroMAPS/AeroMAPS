"""
Regression tests for the sub-lever decomposition of CO2 emissions.

The decomposition models are "exact by construction": the sum of the sub-lever
contributions (including their residual / cross-mix terms) must equal the
corresponding global lever of action computed by DetailedCo2Emissions.

* DetailedCo2EmissionsPerAircraft : aircraft efficiency lever, per aircraft.
* DetailedCo2EmissionsPerPathway  : aircraft energy lever, per energy pathway.
* DetailedCo2EmissionsPerMarket   : every lever, per market (+ cross-mix).

These tests lock that invariant against the bottom-up, multi-market
``config_advanced`` scenario and, for the market and pathway decompositions
that do not need the fleet model, against the top-down ``config_basic`` one.
"""

import os
import shutil

import pytest
from aeromaps import create_process
from aeromaps.models.impacts.emissions.co2_emissions import (
    MARKET_LEVERS_FREIGHT,
    MARKET_LEVERS_PASSENGER,
    aircraft_efficiency_sub_lever_columns,
    efficiency_sub_lever_column,
    market_lever_dataframe,
    pathway_energy_sub_lever_columns,
)

CONFIGS = os.path.join(os.path.dirname(__file__), "..", "tested_configs")
CONFIG = os.path.join(CONFIGS, "config_advanced.yaml")
CONFIG_TOP_DOWN = os.path.join(CONFIGS, "config_basic.yaml")

# The decomposition residuals are exact up to floating-point accumulation over
# the ~15 sub-levers; MtCO2 magnitudes are O(1e3), so 1e-6 is a safe tolerance.
TOL = 1e-6

# (lever, upper level, lower level) of the global cascade.
CASCADE = [
    (
        "demand",
        "co2_emissions_last_historical_year_technology_baseline3",
        "co2_emissions_last_historical_year_technology",
    ),
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
    ("loadfactor", "co2_emissions_including_operations", "co2_emissions_including_load_factor"),
    ("energy", "co2_emissions_including_load_factor", "co2_emissions_including_energy"),
]


def _run(config):
    proc = create_process(configuration_file=config)
    proc.compute()
    return proc


@pytest.fixture(scope="module")
def process():
    return _run(CONFIG)


@pytest.fixture(scope="module")
def process_top_down():
    return _run(CONFIG_TOP_DOWN)


def _years(process):
    return list(
        range(int(process.parameters.prospection_start_year), process.parameters.end_year + 1)
    )


def _max_abs(series, years):
    return float(series.loc[years].abs().max())


def _global_lever(df, lever):
    upper, lower = next((up, low) for name, up, low in CASCADE if name == lever)
    return df[upper] - df[lower]


def test_efficiency_lever_decomposed_per_aircraft(process):
    df = process.data["vector_outputs"]
    columns = aircraft_efficiency_sub_lever_columns(process.fleet_model.fleet)
    assert all(column in df.columns for column in columns)
    residual = _global_lever(df, "efficiency") - df[columns].sum(axis=1)
    assert _max_abs(residual, _years(process)) < TOL


@pytest.mark.parametrize("fixture", ["process", "process_top_down"])
def test_energy_lever_decomposed_per_pathway(request, fixture):
    proc = request.getfixturevalue(fixture)
    df = proc.data["vector_outputs"]
    columns = pathway_energy_sub_lever_columns(proc.pathways_manager)
    assert all(column in df.columns for column in columns)
    residual = _global_lever(df, "energy") - df[columns].sum(axis=1)
    assert _max_abs(residual, _years(proc)) < TOL


@pytest.mark.parametrize("fixture", ["process", "process_top_down"])
@pytest.mark.parametrize("lever", [name for name, _, _ in CASCADE])
def test_lever_decomposed_per_market(request, fixture, lever):
    proc = request.getfixturevalue(fixture)
    df = proc.data["vector_outputs"]
    # Use the tidy (lever, market) accessor rather than ad-hoc prefix matching.
    lever_view = market_lever_dataframe(df, proc.markets).xs(lever, level="lever", axis=1)
    assert not lever_view.empty, f"per-market {lever} sub-levers missing"
    # Sum over markets *and* the cross-market-mix residual must equal the global lever.
    residual = _global_lever(df, lever) - lever_view.sum(axis=1)
    assert _max_abs(residual, _years(proc)) < TOL


def test_market_lever_dataframe_is_tidy(process):
    df = process.data["vector_outputs"]
    per_market = market_lever_dataframe(df, process.markets)
    assert list(per_market.columns.names) == ["lever", "market"]
    # Filtering by a single market returns all of its available levers.
    short_range = per_market.xs("short_range", level="market", axis=1)
    assert set(short_range.columns) == set(MARKET_LEVERS_PASSENGER)
    # Freight has no load-factor lever.
    freight = per_market.xs("freight", level="market", axis=1)
    assert set(freight.columns) == set(MARKET_LEVERS_FREIGHT)


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
    shutil.copy(CONFIG, root / "config_advanced.yaml")
    shutil.copytree(os.path.join(CONFIGS, "data"), root / "data")

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

    return _run(str(root / "config_advanced.yaml"))


def test_continuous_improvement_is_its_own_sub_lever(process, process_with_continuous_improvement):
    df_reference = process.data["vector_outputs"]
    df = process_with_continuous_improvement.data["vector_outputs"]
    years = _years(process)
    end_year = years[-1]
    continuous_improvement = efficiency_sub_lever_column("continuous_improvement")
    other = efficiency_sub_lever_column("other")

    # Without a factor the sub-lever is identically zero; with one it carries the gain.
    assert _max_abs(df_reference[continuous_improvement], years) == 0
    assert df.loc[end_year, continuous_improvement] > 1.0

    # The residual is a pure traffic-mix term: it only depends on reference-year
    # intensities and on the traffic split, so it must not move with the factor.
    assert _max_abs(df[other] - df_reference[other], years) < TOL

    # And the decomposition still closes exactly on the global lever.
    columns = aircraft_efficiency_sub_lever_columns(
        process_with_continuous_improvement.fleet_model.fleet
    )
    residual = _global_lever(df, "efficiency") - df[columns].sum(axis=1)
    assert _max_abs(residual, years) < TOL

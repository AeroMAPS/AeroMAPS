"""
Tests for the generic offsets model.

Each offsetting scheme declared in the YAML carries its own quantity rule (level,
share of residual, prescribed quantity) and its own price. The scheme quantities sum
exactly to ``carbon_offset``, the scheme expenses to ``carbon_offset * carbon_offset_price``,
and the generic model replaces the simple offset models and the single-price offset
cost model.
"""

import os

import pytest
from aeromaps import create_process
from aeromaps.models.impacts.emissions.co2_emissions import (
    offset_category_column,
    offset_scheme_column,
)

CONFIG = os.path.join(os.path.dirname(__file__), "..", "tested_configs", "config_offsets.yaml")
OFFSETS_DATA = os.path.join(os.path.dirname(CONFIG), "data", "offsets_data.yaml")

TOL = 1e-9


@pytest.fixture(scope="module")
def process():
    proc = create_process(configuration_file=CONFIG)
    proc.compute()
    return proc


def _has_model(models, name):
    for key, value in models.items():
        if key == name:
            return True
        if isinstance(value, dict) and _has_model(value, name):
            return True
    return False


def _years(process):
    return list(
        range(int(process.parameters.prospection_start_year), process.parameters.end_year + 1)
    )


def test_generic_offsets_replaces_simple_models(process):
    assert process.offsets_manager is not None
    assert len(process.offsets_manager.get_all()) == 3
    for name in (
        "level_carbon_offset",
        "residual_carbon_offset",
        "manual_carbon_offset",
        "carbon_offset",
        "passenger_aircraft_noc_carbon_offset",
    ):
        assert not _has_model(process.models, name)
    assert _has_model(process.models, "offsets_use_choice")
    # The cumulative offset still runs on the aggregate.
    assert _has_model(process.models, "cumulative_carbon_offset")


def test_scheme_quantities_sum_to_carbon_offset(process):
    df = process.data["vector_outputs"]
    years = _years(process)
    columns = [offset_scheme_column(s.name) for s in process.offsets_manager.get_all()]
    residual = (df["carbon_offset"] - df[columns].sum(axis=1)).loc[years].abs().max()
    assert residual == pytest.approx(0.0, abs=TOL)
    assert df["carbon_offset"].loc[years[-1]] > 0


def test_expense_is_sum_of_priced_schemes(process):
    df = process.data["vector_outputs"]
    years = _years(process)
    expense = sum(
        df[offset_scheme_column(s.name)] * df[f"{s.name}_carbon_offset_price"]
        for s in process.offsets_manager.get_all()
    )
    assert (df["carbon_offset_expense"] - expense).loc[years].abs().max() == pytest.approx(
        0.0, abs=TOL
    )
    # The single-price cost chain is reproduced exactly by the weighted mean price.
    weighted = df["carbon_offset"] * df["carbon_offset_price"]
    assert (df["carbon_offset_expense"] - weighted).loc[years].abs().max() == pytest.approx(
        0.0, abs=1e-6
    )
    per_ask = df["carbon_offset_expense"] * 1e6 / df["ask"]
    assert (df["noc_carbon_offset_per_ask"] - per_ask).loc[years].abs().max() == pytest.approx(
        0.0, abs=TOL
    )


def test_level_rule_matches_the_simple_model(process):
    """CORSIA-style scheme: emissions above 85 % of 2019, times the coverage."""
    df = process.data["vector_outputs"]
    years = _years(process)
    co2 = process.data["climate_outputs"]["co2_emissions"].reindex(df.index)
    coverage = df["corsia_quantity_coverage"].reindex(df.index).fillna(0)
    expected = (co2 - 0.85 * co2.loc[2019]).clip(lower=0.0) * coverage / 100
    assert (df[offset_scheme_column("corsia")] - expected).loc[years].abs().max() == pytest.approx(
        0.0, abs=TOL
    )


def test_share_rule_applies_to_the_residual_of_level_schemes(process):
    df = process.data["vector_outputs"]
    end = _years(process)[-1]
    # 100 % of the residual in the end year: removals cover everything CORSIA does not.
    co2 = process.data["climate_outputs"]["co2_emissions"]
    residual = co2.loc[end] - df[offset_scheme_column("corsia")].loc[end]
    assert df[offset_scheme_column("removals")].loc[end] == pytest.approx(residual, abs=TOL)


def test_quantity_rule_and_price_hold(process):
    df = process.data["vector_outputs"]
    years = _years(process)
    assert (df[offset_scheme_column("ets")].loc[years] - 5.0).abs().max() == pytest.approx(
        0.0, abs=TOL
    )
    assert df["ets_carbon_offset_price"].loc[years[0]] == pytest.approx(80.0, abs=1e-6)
    assert df["ets_carbon_offset_price"].loc[2050] == pytest.approx(120.0, abs=1e-6)
    # Historic years carry no offset.
    assert (df["carbon_offset"].loc[: years[0] - 1].fillna(0) == 0).all()


def test_category_aggregates_sum_to_total(process):
    df = process.data["vector_outputs"]
    years = _years(process)
    categories = process.offsets_manager.get_all_types("category")
    by_category = sum(df[offset_category_column(c)] for c in categories)
    assert (df["carbon_offset"] - by_category).loc[years].abs().max() == pytest.approx(0.0, abs=TOL)
    by_category_expense = sum(df[f"{c}_carbon_offset_expense"] for c in categories)
    assert (df["carbon_offset_expense"] - by_category_expense).loc[
        years
    ].abs().max() == pytest.approx(0.0, abs=TOL)


@pytest.mark.parametrize(
    "plot",
    ["carbon_offset_by_scheme", "carbon_offset_by_category", "carbon_offset_expense_by_scheme"],
)
def test_offsets_plots(process, plot):
    process.plot(plot, save=False)


@pytest.mark.parametrize(
    "granularity, expected",
    [
        ("scheme", {"Corsia", "Ets", "Removals"}),
        ("category", {"Offsets", "Allowances", "Removals"}),
    ],
)
def test_detailed_plot_splits_the_offset(process, granularity, expected):
    plot = process.plot(
        "air_transport_co2_emissions_detailed", save=False, offset_granularity=granularity
    )
    labels = {collection.get_label() for collection in plot.ax.collections}
    assert expected <= labels
    assert "Carbon offset" not in labels


def _offsets_process(tmp_path, offsets_yaml):
    """Compute the tested config with another offsets data file."""
    (tmp_path / "offsets_data.yaml").write_text(offsets_yaml)
    config = open(CONFIG).read().replace("./data/offsets_data.yaml", "./offsets_data.yaml")
    (tmp_path / "config.yaml").write_text(config)
    proc = create_process(configuration_file=str(tmp_path / "config.yaml"))
    proc.compute()
    return proc


def test_over_offsetting_is_reported(tmp_path, caplog):
    # The tested schemes offset 100 % of the residual in 2050 plus a prescribed quantity.
    with caplog.at_level("WARNING"):
        _offsets_process(tmp_path, open(OFFSETS_DATA).read())
    assert "exceeds the CO2 emissions" in caplog.text


def test_residual_shares_above_100_percent_are_reported(tmp_path, caplog):
    offsets_yaml = open(OFFSETS_DATA).read().replace("values: [0.0, 100.0]", "values: [0.0, 150.0]")
    with caplog.at_level("WARNING"):
        _offsets_process(tmp_path, offsets_yaml)
    assert "exceed 100 %" in caplog.text

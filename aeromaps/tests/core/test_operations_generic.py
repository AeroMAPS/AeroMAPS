"""
Tests for the generic operations model.

Each operational concept declared in the YAML contributes fuel-efficiency and/or
contrail gains that compose *multiplicatively* into the aggregate operational
effects (``operations_gain``, ``operations_contrails_gain``,
``operations_contrails_overconsumption``). The generic model replaces the simple
operations / contrails models, and the per-concept contributions sum exactly to
each aggregate.
"""

import os

import numpy as np
import pytest
from aeromaps import create_process

CONFIG = os.path.join(os.path.dirname(__file__), "..", "tested_configs", "config_operations.yaml")

TOL = 1e-9
YEAR = 2050


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


def test_generic_operations_replaces_simple_models(process):
    assert process.operations_manager is not None
    assert len(process.operations_manager.get_all()) == 4
    # The generic model is the single producer of the aggregate effects.
    assert not _has_model(process.models, "operations_logistic")
    assert not _has_model(process.models, "operations_interpolation")
    assert not _has_model(process.models, "operations_contrails_simple")
    assert _has_model(process.models, "operations_use_choice")


def test_fuel_efficiency_gain_is_multiplicative(process):
    df = process.data["vector_outputs"]
    concepts = [c.name for c in process.operations_manager.get_all() if c.has_fuel_efficiency]
    gains = [df[f"{c}_fuel_efficiency_gain"].loc[YEAR] / 100 for c in concepts]
    expected = (1 - np.prod([1 - g for g in gains])) * 100
    assert df["operations_gain"].loc[YEAR] == pytest.approx(expected, abs=TOL)
    # Multiplicative result is strictly below the naive additive sum when >1 concept.
    assert df["operations_gain"].loc[YEAR] < sum(g * 100 for g in gains)


def test_per_concept_contributions_sum_to_aggregate(process):
    df = process.data["vector_outputs"]
    years = list(
        range(int(process.parameters.prospection_start_year), process.parameters.end_year + 1)
    )
    for aggregate, channel in [
        ("operations_gain", "operations_gain_contribution"),
        ("operations_contrails_gain", "operations_contrails_gain_contribution"),
        (
            "operations_contrails_overconsumption",
            "operations_contrails_overconsumption_contribution",
        ),
    ]:
        contribution_cols = [
            f"{c.name}_{channel}"
            for c in process.operations_manager.get_all()
            if f"{c.name}_{channel}" in df.columns
        ]
        assert contribution_cols, f"no contributions for {channel}"
        residual = (df[aggregate] - df[contribution_cols].sum(axis=1)).loc[years].abs().max()
        assert residual == pytest.approx(0.0, abs=1e-9)


def test_category_aggregates_sum_to_total(process):
    df = process.data["vector_outputs"]
    categories = process.operations_manager.get_all_types("category")
    category_total = sum(df[f"{cat}_operations_gain_contribution"] for cat in categories)
    residual = (df["operations_gain"] - category_total).abs().max()
    assert residual == pytest.approx(0.0, abs=1e-9)


def test_contrail_channels_present(process):
    df = process.data["vector_outputs"]
    # contrail_avoidance drives the non-CO2 contrail gain and its fuel penalty.
    assert df["operations_contrails_gain"].loc[YEAR] > 0
    assert df["operations_contrails_overconsumption"].loc[YEAR] > 0


def test_attribution_is_order_independent(process):
    """Logarithmic shares: contribution_i / ln(1 - g_i) is the same for every concept."""
    df = process.data["vector_outputs"]
    concepts = [c.name for c in process.operations_manager.get_all() if c.has_fuel_efficiency]
    ratios = []
    for concept in concepts:
        gain = df[f"{concept}_fuel_efficiency_gain"].loc[YEAR] / 100
        contribution = df[f"{concept}_operations_gain_contribution"].loc[YEAR]
        ratios.append(contribution / np.log1p(-gain))
    assert max(ratios) - min(ratios) == pytest.approx(0.0, abs=TOL)


def test_operations_lever_decomposed_per_concept(process):
    """The CO2 sub-wedges per concept (and per category) sum to the operations lever."""
    from aeromaps.models.impacts.emissions.co2_emissions import (
        OPERATIONS_OTHER,
        operations_category_column,
        operations_concept_column,
    )

    df = process.data["vector_outputs"]
    years = list(
        range(int(process.parameters.prospection_start_year), process.parameters.end_year + 1)
    )
    lever = (
        df["co2_emissions_including_aircraft_efficiency"] - df["co2_emissions_including_operations"]
    )
    concepts = [c for c in process.operations_manager.get_all() if c.has_fuel_efficiency]
    per_concept = sum(df[operations_concept_column(c.name)] for c in concepts)
    residual = df[operations_concept_column(OPERATIONS_OTHER)]
    assert (lever - per_concept - residual).loc[years].abs().max() < 1e-6
    # The lever is proportional to operations_gain, so the residual is zero.
    assert residual.loc[years].abs().max() < 1e-6
    assert df[operations_concept_column("airspace_and_atm")].loc[YEAR] > 0

    categories = list(dict.fromkeys(c.category for c in concepts))
    per_category = sum(df[operations_category_column(cat)] for cat in categories)
    assert (per_concept - per_category).loc[years].abs().max() < 1e-6

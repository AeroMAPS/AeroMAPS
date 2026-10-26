"""
Regression tests for categories named like one of their members.

The default operations and offsets data give each concept or scheme the same name as
its category. Per-member and per-category outputs used to share one naming pattern,
so as soon as a second member joined such a category, the category total overwrote
the member's own column: a wrong expense for offsets, and for operations a concept
credited with its whole category, which the CO2 decomposition then offset with a
negative residual.
"""

import os

import pytest
from aeromaps import create_process
from aeromaps.models.impacts.emissions.co2_emissions import (
    OPERATIONS_OTHER,
    operations_category_column,
    operations_concept_column,
)
from aeromaps.models.impacts.generic_offsets_model.common.offsets_use_choice import (
    category_expense_column,
)
from aeromaps.models.impacts.generic_operations_model.common.operations_use_choice import (
    category_contribution_column,
)

CONFIGS = os.path.join(os.path.dirname(__file__), "..", "tested_configs")

YEAR = 2050
TOL = 1e-9


@pytest.fixture(scope="module")
def operations():
    proc = create_process(
        configuration_file=os.path.join(CONFIGS, "config_operations_shared_category.yaml")
    )
    proc.compute()
    return proc.data["vector_outputs"]


@pytest.fixture(scope="module")
def offsets():
    proc = create_process(
        configuration_file=os.path.join(CONFIGS, "config_offsets_shared_category.yaml")
    )
    proc.compute()
    return proc.data["vector_outputs"]


def test_concept_keeps_its_own_contribution(operations):
    df = operations.loc[YEAR]
    own = df["airline_operations_operations_gain_contribution"]
    other = df["single_engine_taxi_operations_gain_contribution"]
    category = df[
        category_contribution_column("airline_operations", "operations_gain_contribution")
    ]
    assert own + other == pytest.approx(df["operations_gain"], abs=TOL)
    assert category == pytest.approx(own + other, abs=TOL)
    assert own < category


def test_operations_decomposition_has_no_spurious_residual(operations):
    df = operations.loc[YEAR]
    lever = (
        df["co2_emissions_including_aircraft_efficiency"] - df["co2_emissions_including_operations"]
    )
    concepts = (
        df[operations_concept_column("airline_operations")]
        + df[operations_concept_column("single_engine_taxi")]
    )
    assert df[operations_concept_column(OPERATIONS_OTHER)] == pytest.approx(0.0, abs=1e-6)
    assert concepts == pytest.approx(lever, abs=1e-6)
    assert df[operations_category_column("airline_operations")] == pytest.approx(lever, abs=1e-6)


def test_scheme_keeps_its_own_expense(offsets):
    df = offsets.loc[YEAR]
    assert df["removals_carbon_offset_expense"] == pytest.approx(10.0 * 100.0, abs=TOL)
    assert df["direct_air_capture_carbon_offset_expense"] == pytest.approx(5.0 * 400.0, abs=TOL)
    assert df[category_expense_column("removals")] == pytest.approx(
        df["carbon_offset_expense"], abs=TOL
    )


def test_colliding_output_names_fail_at_setup():
    from aeromaps.models.impacts.generic_offsets_model.common.offsets_manager import (
        OffsetSchemeManager,
        OffsetSchemeMetadata,
    )
    from aeromaps.models.impacts.generic_offsets_model.common.offsets_use_choice import (
        OffsetsUseChoice,
    )

    manager = OffsetSchemeManager()
    # A scheme whose expense column is spelt like the category's.
    manager.add(OffsetSchemeMetadata("category_removals", "removals", "quantity"))
    with pytest.raises(ValueError, match="declared twice"):
        OffsetsUseChoice("offsets_use_choice", {}, manager)

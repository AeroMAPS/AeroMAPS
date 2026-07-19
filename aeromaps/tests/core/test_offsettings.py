"""
Unit tests for the generic offsettings model (use choice priority rules and cost model).
"""

import warnings

import pandas as pd
import pytest

from aeromaps.models.impacts.generic_offsettings_model.common.offsettings_manager import (
    OffsettingMechanismManager,
    OffsettingMechanismMetadata,
)
from aeromaps.models.impacts.generic_offsettings_model.common.offsettings_use_choice import (
    OffsettingsUseChoice,
)
from aeromaps.models.impacts.generic_offsettings_model.top_down.cost import (
    OffsettingTopDownCost,
)

HISTORIC_START_YEAR = 2000
PROSPECTION_START_YEAR = 2020
END_YEAR = 2050

FULL_INDEX = pd.RangeIndex(HISTORIC_START_YEAR, END_YEAR + 1)
PROSPECTIVE_INDEX = pd.RangeIndex(PROSPECTION_START_YEAR, END_YEAR + 1)


def _setup_years(model):
    """Set the year attributes normally provided by the parameters object."""
    model.historic_start_year = HISTORIC_START_YEAR
    model.prospection_start_year = PROSPECTION_START_YEAR
    model.end_year = END_YEAR
    model.df = pd.DataFrame(index=FULL_INDEX)
    model.float_outputs = {}
    return model


def _default_manager():
    manager = OffsettingMechanismManager()
    manager.add(
        OffsettingMechanismMetadata(
            name="cdr_quant", category="carbon_dioxide_removal", usage_type="quantity"
        )
    )
    manager.add(
        OffsettingMechanismMetadata(
            name="cdr_share", category="carbon_dioxide_removal", usage_type="share"
        )
    )
    manager.add(
        OffsettingMechanismMetadata(name="avoidance", category="emissions_avoidance", default=True)
    )
    return manager


def _use_choice(manager):
    return _setup_years(OffsettingsUseChoice("offsettings_use_choice", {}, manager))


def _carbon_offset_demand(value=100.0):
    """Constant prospective carbon offsetting demand, zero over the historic period."""
    demand = pd.Series(0.0, index=FULL_INDEX)
    demand.loc[PROSPECTION_START_YEAR:] = value
    return demand


def test_use_choice_quantity_share_and_default_split():
    model = _use_choice(_default_manager())
    output_data = model.compute(
        {
            "carbon_offset": _carbon_offset_demand(),
            "cdr_quant_usage_quantity": pd.Series(30.0, index=PROSPECTIVE_INDEX),
            "cdr_share_usage_share": pd.Series(20.0, index=PROSPECTIVE_INDEX),
        }
    )

    assert output_data["cdr_quant_carbon_offset"].loc[2030] == pytest.approx(30.0)
    assert output_data["cdr_share_carbon_offset"].loc[2030] == pytest.approx(20.0)
    # Default mechanism absorbs the remainder
    assert output_data["avoidance_carbon_offset"].loc[2030] == pytest.approx(50.0)
    # Category aggregates
    assert output_data["carbon_dioxide_removal_carbon_offset"].loc[2030] == pytest.approx(50.0)
    assert output_data["carbon_dioxide_removal_share_carbon_offset"].loc[2030] == pytest.approx(
        50.0
    )
    assert output_data["cdr_quant_share_carbon_dioxide_removal"].loc[2030] == pytest.approx(60.0)
    # Cumulative carbon offset [GtCO2]: 30 MtCO2/year over 2020-2030 included
    assert output_data["cdr_quant_cumulative_carbon_offset"].loc[2030] == pytest.approx(0.33)


def test_use_choice_quantity_capped_to_demand():
    model = _use_choice(_default_manager())
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        output_data = model.compute(
            {
                "carbon_offset": _carbon_offset_demand(),
                "cdr_quant_usage_quantity": pd.Series(150.0, index=PROSPECTIVE_INDEX),
                "cdr_share_usage_share": pd.Series(20.0, index=PROSPECTIVE_INDEX),
            }
        )
    assert any(
        "exceeds the total carbon offsetting demand" in str(warning.message)
        for warning in caught_warnings
    )
    # Quantity mechanism capped at the demand, nothing left for the others
    assert output_data["cdr_quant_carbon_offset"].loc[2030] == pytest.approx(100.0)
    assert output_data["cdr_share_carbon_offset"].loc[2030] == pytest.approx(0.0)
    assert output_data["avoidance_carbon_offset"].loc[2030] == pytest.approx(0.0)


def test_use_choice_missing_default_mechanism_raises():
    manager = OffsettingMechanismManager()
    manager.add(
        OffsettingMechanismMetadata(
            name="cdr_share", category="carbon_dioxide_removal", usage_type="share"
        )
    )
    model = _use_choice(manager)
    with pytest.raises(ValueError, match="default offsetting mechanism"):
        model.compute(
            {
                "carbon_offset": _carbon_offset_demand(),
                "cdr_share_usage_share": pd.Series(20.0, index=PROSPECTIVE_INDEX),
            }
        )


def test_use_choice_zero_demand_outputs_zeros():
    model = _use_choice(_default_manager())
    output_data = model.compute(
        {
            "carbon_offset": pd.Series(0.0, index=FULL_INDEX),
            "cdr_quant_usage_quantity": pd.Series(30.0, index=PROSPECTIVE_INDEX),
            "cdr_share_usage_share": pd.Series(20.0, index=PROSPECTIVE_INDEX),
        }
    )
    assert (output_data["cdr_quant_carbon_offset"] == 0).all()
    assert (output_data["avoidance_carbon_offset"] == 0).all()


def test_top_down_cost_with_subsidy_and_tax():
    configuration_data = {
        "name": "cdr_share",
        "inputs": {
            "economics": {
                "cdr_share_mean_unit_cost": pd.Series([0.0]),
                "cdr_share_mean_unit_subsidy": pd.Series([0.0]),
                "cdr_share_mean_unit_tax": pd.Series([0.0]),
            }
        },
    }
    model = _setup_years(OffsettingTopDownCost("cdr_share_top_down_unit_cost", configuration_data))
    output_data = model.compute(
        {
            "cdr_share_mean_unit_cost": pd.Series(200.0, index=PROSPECTIVE_INDEX),
            "cdr_share_mean_unit_subsidy": pd.Series(50.0, index=PROSPECTIVE_INDEX),
            "cdr_share_mean_unit_tax": pd.Series(10.0, index=PROSPECTIVE_INDEX),
            "cdr_share_carbon_offset": _carbon_offset_demand(20.0),
        }
    )
    # Net unit cost = 200 - 50 + 10 = 160 €/tCO2
    assert output_data["cdr_share_net_unit_cost"].loc[2030] == pytest.approx(160.0)
    # Total cost = 20 MtCO2 * 160 €/tCO2 = 3200 M€
    assert output_data["cdr_share_carbon_offset_cost"].loc[2030] == pytest.approx(3200.0)
    assert output_data["cdr_share_carbon_offset_subsidy"].loc[2030] == pytest.approx(1000.0)
    assert output_data["cdr_share_carbon_offset_tax"].loc[2030] == pytest.approx(200.0)
    # No cost over the historic period (no carbon offset)
    assert output_data["cdr_share_carbon_offset_cost"].loc[2010] == pytest.approx(0.0)

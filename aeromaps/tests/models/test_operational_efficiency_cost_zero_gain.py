"""The operational efficiency cost must stay defined when no operational gain is targeted.

``OperationalEfficiencyCost`` spreads the final implementation cost along the gain
trajectory, ``cost_final_value * operations_gain / operations_final_gain``. With
``operations_final_gain = 0`` -- the "current operations" setting -- the logistic gain
is zero in every year and the ratio is ``0/0``. The NaN reaches the total cost and the
fare; with price-elastic demand the fare is a coupling variable, so the run fails.

No measure is targeted, so nothing is paid for: the cost is zero. This is a computed
value, not a NaN replaced by zero, and it is not the limit of the ratio (the shape of
the logistic), which would bill measures that have no effect.
"""

import importlib.resources

import numpy as np
import pandas as pd
import pytest
import yaml

from aeromaps import create_process
from aeromaps.models.air_transport.aircraft_fleet_and_operations.operations.operations import (
    OperationsLogistic,
)
from aeromaps.models.impacts.costs.operations.operations_cost import (
    OperationalEfficiencyCost,
)

HISTORIC_START, PROSPECTION_START, END = 2000, 2020, 2050
COST_FINAL_VALUE = 0.0012  # €/ASK


class _Parameters:
    """Minimal stand-in for the process parameters object a model needs to build ``df``."""

    climate_historic_start_year = 1940
    historic_start_year = HISTORIC_START
    prospection_start_year = PROSPECTION_START
    end_year = END


def _operations_gain(final_gain):
    model = OperationsLogistic("operations_logistic", parameters=_Parameters())
    return model.compute(
        operations_final_gain=final_gain,
        operations_start_year=2025,
        operations_duration=25.0,
    )


def _cost(final_gain, operations_gain):
    model = OperationalEfficiencyCost("operational_efficiency_cost", parameters=_Parameters())
    return model.compute(
        operational_efficiency_cost_non_energy_per_ask_final_value=COST_FINAL_VALUE,
        operations_final_gain=final_gain,
        operations_gain=operations_gain,
    )


# --------------------------------------------------------------------------------
# The defect itself, reproduced
# --------------------------------------------------------------------------------


def test_the_old_ratio_returned_nan_with_a_zero_final_gain():
    """The pre-fix formula, verbatim, on the gain the logistic produces for zero."""
    gain = _operations_gain(0.0)
    assert (gain == 0.0).all(), "a zero final gain should give a zero trajectory"

    with np.errstate(invalid="ignore"):
        old = COST_FINAL_VALUE * gain / 0.0

    assert old.isna().all(), "expected 0/0; this test no longer reproduces anything"


# --------------------------------------------------------------------------------
# The fix
# --------------------------------------------------------------------------------


def test_a_zero_final_gain_costs_nothing():
    cost = _cost(0.0, _operations_gain(0.0))

    assert np.isfinite(cost.to_numpy()).all()
    assert (cost == 0.0).all()


def test_a_zero_final_gain_does_not_mutate_its_inputs():
    gain = _operations_gain(0.0)
    before = gain.copy()

    _cost(0.0, gain)

    pd.testing.assert_series_equal(gain, before)


def test_a_zero_final_gain_keeps_the_nan_pattern_of_the_gain():
    """An undefined year stays undefined; only the 0/0 is resolved."""
    gain = _operations_gain(0.0).copy()
    gain.iloc[0] = np.nan

    cost = _cost(0.0, gain)

    assert np.isnan(cost.iloc[0])
    assert (cost.iloc[1:] == 0.0).all()


def test_a_non_zero_final_gain_is_unchanged():
    gain = _operations_gain(8.0)

    cost = _cost(8.0, gain)

    pd.testing.assert_series_equal(
        cost, COST_FINAL_VALUE * gain / 8.0, check_names=False, rtol=0, atol=0
    )
    assert cost[END] == pytest.approx(COST_FINAL_VALUE, rel=0.03)


# --------------------------------------------------------------------------------
# The case that exposed it: price-elastic demand with current operations
# --------------------------------------------------------------------------------

STANDARDS = [
    "models_traffic",
    "models_efficiency_top_down",
    "models_energy_with_fuel_effect",
    "models_offset",
    "models_emissions",
    "models_sustainability",
    "models_energy_cost",
    "models_operation_cost_top_down",
]


def _elastic_config(directory):
    source = importlib.resources.files("aeromaps").joinpath(
        "resources/data/default_markets/markets.yaml"
    )
    markets = yaml.safe_load(source.read_text())
    markets["global"]["demand"] = {"model": "cagr_elasticity"}
    (directory / "markets.yaml").write_text(yaml.dump(markets))

    configuration = {
        "models": {
            "markets": {"markets_data_file": str(directory / "markets.yaml")},
            "climate": {"climate_model_data_file": "default"},
            "energy": {
                "energy_carriers_model_data_file": "default",
                "resources_model_data_file": "default",
                "processes_model_data_file": "default",
            },
            "standards": STANDARDS,
        }
    }
    (directory / "config.yaml").write_text(yaml.dump(configuration))
    return str(directory / "config.yaml")


def test_elastic_demand_computes_without_operational_gain(tmp_path):
    """Raised on #157 before the fix: the NaN fare reached the emissions."""
    process = create_process(configuration_file=_elastic_config(tmp_path))
    process.parameters.operations_final_gain = 0.0

    process.compute()

    df = process.data["vector_outputs"]
    prospective = df.loc[process.parameters.prospection_start_year : process.parameters.end_year]
    assert np.isfinite(prospective["airfare_per_rpk"].to_numpy()).all()
    assert np.isfinite(prospective["rpk"].to_numpy()).all()
    assert (prospective["operational_efficiency_cost_non_energy_per_ask"] == 0.0).all()

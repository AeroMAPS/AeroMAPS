"""Direct pandas/JAX comparison of the plant-commissioning model.

The tested configurations only exercise pathways with no pre-scenario history
and never over-shoot demand, so the reconstructed virtual history and the
excess-production branches are covered here instead.
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from aeromaps.models.impacts.generic_energy_model.bottom_up.production_capacity import (
    BottomUpCapacity,
)

PARAMETERS = SimpleNamespace(
    climate_historic_start_year=1940,
    historic_start_year=2000,
    prospection_start_year=2020,
    end_year=2050,
)
YEARS = range(2000, 2051)


def _build_model(technical, processes_data=None):
    configuration_data = {"name": "px", "inputs": {"technical": dict(technical)}}
    return BottomUpCapacity(
        name="px_capacity",
        configuration_data=configuration_data,
        processes_data=processes_data or {},
        parameters=PARAMETERS,
    )


def _assert_paths_agree(model, input_data):
    pandas_input = {
        key: (value.copy() if isinstance(value, pd.Series) else value)
        for key, value in input_data.items()
    }
    pandas_output = model.compute(pandas_input)

    jax_input = {
        key: (value.to_numpy(dtype=float) if isinstance(value, pd.Series) else value)
        for key, value in input_data.items()
    }
    jax_output = model.jax_compute(jax_input)

    assert set(jax_output) == set(pandas_output)
    for name, expected in pandas_output.items():
        actual = np.asarray(jax_output[name], dtype=float)
        expected = np.asarray(expected, dtype=float)
        assert actual.shape == expected.shape, name
        np.testing.assert_allclose(actual, expected, rtol=1e-10, atol=1e-8, err_msg=name)
    return pandas_output


def _demand(prospective_values, historic_values=None):
    demand = pd.Series(np.nan, index=YEARS)
    if historic_values is not None:
        demand.loc[2000:2019] = historic_values
    demand.loc[2020:] = prospective_values
    return demand


def test_growing_demand_without_history():
    demand = _demand(np.linspace(1e9, 5e10, 31))
    model = _build_model({"px_eis_plant_lifespan": 20, "px_eis_plant_load_factor": 0.9})
    output = _assert_paths_agree(
        model,
        {
            "px_energy_consumption": demand,
            "px_eis_plant_lifespan": 20,
            "px_eis_plant_load_factor": 0.9,
        },
    )
    # Nothing is built before the prospective window opens.
    assert output["px_energy_production_commissioned"].loc[2020] == pytest.approx(1e9)


def test_virtual_history_is_reconstructed():
    demand = _demand(np.linspace(4e10, 9e10, 31), np.linspace(2e10, 4e10, 20))
    model = _build_model({"px_eis_plant_lifespan": 25, "px_eis_plant_load_factor": 0.95})
    output = _assert_paths_agree(
        model,
        {
            "px_energy_consumption": demand,
            "px_eis_plant_lifespan": 25,
            "px_eis_plant_load_factor": 0.95,
            "px_technology_introduction_year": 1985,
            "px_technology_introduction_volume": 1e9,
        },
    )
    # Plants commissioned before the scenario are still running in 2020.
    assert output["px_plant_operating_capacity"].loc[2020] > 0.0


def test_declining_demand_leaves_capacity_unused():
    demand = _demand(np.concatenate([np.linspace(1e10, 6e10, 16), np.linspace(6e10, 2e10, 15)]))
    model = _build_model({"px_eis_plant_lifespan": 30, "px_eis_plant_load_factor": 1.0})
    output = _assert_paths_agree(
        model,
        {
            "px_energy_consumption": demand,
            "px_eis_plant_lifespan": 30,
            "px_eis_plant_load_factor": 1.0,
        },
    )
    assert output["px_energy_unused"].loc[2050] > 0.0


def test_process_building_scenario():
    demand = _demand(np.linspace(1e9, 5e10, 31))
    processes_data = {
        "pr": {"inputs": {"technical": {"pr_resource_names": ["r"], "pr_load_factor": 0.8}}}
    }
    model = _build_model(
        {
            "px_eis_plant_lifespan": 20,
            "px_eis_plant_load_factor": 0.9,
            "px_processes_names": ["pr"],
        },
        processes_data,
    )
    _assert_paths_agree(
        model,
        {
            "px_energy_consumption": demand,
            "px_eis_plant_lifespan": 20,
            "px_eis_plant_load_factor": 0.9,
            "pr_load_factor": 0.8,
        },
    )

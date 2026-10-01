"""
An ``end_year`` changed after ``create_process`` must give the results of a process created
with it, whether or not the process has already been computed. Coupling seeds
(``_coupling_defaults``) must follow it without overriding a value set as a parameter.
"""

import importlib.resources
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import yaml

from aeromaps import create_process
from aeromaps.core.gemseo import AeroMAPSAutoModelWrapper, AeroMAPSCustomModelWrapper
from aeromaps.models.base import AeroMAPSModel


def _seed(model):
    return pd.Series(1.0, index=range(model.historic_start_year, model.end_year + 1))


class SeededAutoModel(AeroMAPSModel):
    def __init__(self, parameters):
        super().__init__(name="seeded_auto", parameters=parameters)

    def _initialize_df(self):
        super()._initialize_df()
        self._coupling_defaults = {"seed": _seed(self)}

    def compute(self, seed: pd.Series) -> pd.Series:
        doubled_seed = 2.0 * seed
        return doubled_seed


class SeededCustomModel(AeroMAPSModel):
    def __init__(self, parameters):
        super().__init__(name="seeded_custom", parameters=parameters, model_type="custom")
        self.input_names = {"seed": pd.Series([0.0])}
        self.output_names = {"doubled_seed": pd.Series([0.0])}

    def _initialize_df(self):
        super()._initialize_df()
        self._coupling_defaults = {"seed": _seed(self)}

    def compute(self, input_data):
        return {"doubled_seed": 2.0 * input_data["seed"]}


WRAPPERS = [
    (SeededAutoModel, AeroMAPSAutoModelWrapper),
    (SeededCustomModel, AeroMAPSCustomModelWrapper),
]


def _parameters(end_year=2050):
    return SimpleNamespace(
        climate_historic_start_year=1940,
        historic_start_year=2000,
        prospection_start_year=2025,
        end_year=end_year,
    )


def _extend_end_year(wrapper, end_year):
    # What AeroMAPSProcess._pre_compute does for each discipline.
    wrapper.model.parameters.end_year = end_year
    wrapper.model._initialize_df()
    wrapper.refresh_coupling_seeds()


def _doubled_seed(wrapper):
    return np.asarray(wrapper.execute()["doubled_seed"])


@pytest.mark.parametrize("model_class, wrapper_class", WRAPPERS)
def test_seed_follows_end_year(model_class, wrapper_class):
    wrapper = wrapper_class(model_class(_parameters()))
    _extend_end_year(wrapper, 2070)

    assert wrapper.default_input_data["seed"].index[-1] == 2070
    np.testing.assert_array_equal(_doubled_seed(wrapper), np.full(71, 2.0))


@pytest.mark.parametrize("model_class, wrapper_class", WRAPPERS)
def test_parameter_set_before_wrapping_wins_over_seed(model_class, wrapper_class):
    parameters = _parameters()
    parameters.seed = pd.Series(5.0, index=range(2000, 2071))
    wrapper = wrapper_class(model_class(parameters))
    _extend_end_year(wrapper, 2070)

    np.testing.assert_array_equal(_doubled_seed(wrapper), np.full(71, 10.0))


@pytest.mark.parametrize("model_class, wrapper_class", WRAPPERS)
def test_parameter_set_after_wrapping_wins_over_seed(model_class, wrapper_class):
    wrapper = wrapper_class(model_class(_parameters()))
    wrapper.model.parameters.seed = pd.Series(5.0, index=range(2000, 2071))
    _extend_end_year(wrapper, 2070)

    np.testing.assert_array_equal(_doubled_seed(wrapper), np.full(71, 10.0))


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


def _elastic_process(directory, end_year_at_creation=None):
    markets_file = importlib.resources.files("aeromaps").joinpath(
        "resources/data/default_markets/markets.yaml"
    )
    markets = yaml.safe_load(markets_file.read_text())
    markets["global"]["demand"] = {"model": "cagr_elasticity"}
    (directory / "markets.yaml").write_text(yaml.dump(markets))

    config = {
        "models": {
            "markets": {"markets_data_file": str(directory / "markets.yaml")},
            "climate": {"climate_model_data_file": "default"},
            "energy": {
                key: "default"
                for key in (
                    "energy_carriers_model_data_file",
                    "resources_model_data_file",
                    "processes_model_data_file",
                )
            },
            "standards": STANDARDS,
        }
    }
    if end_year_at_creation is not None:
        (directory / "inputs.json").write_text(json.dumps({"end_year": end_year_at_creation}))
        config["data"] = {"inputs": {"json_inputs_file": str(directory / "inputs.json")}}
    (directory / "config.yaml").write_text(yaml.dump(config))
    return create_process(configuration_file=str(directory / "config.yaml"))


def test_end_year_set_after_create_process_matches_end_year_at_creation(tmp_path):
    (tmp_path / "at_creation").mkdir()
    (tmp_path / "after").mkdir()

    reference = _elastic_process(tmp_path / "at_creation", end_year_at_creation=2070)
    reference.compute()

    process = _elastic_process(tmp_path / "after")
    process.parameters.end_year = 2070
    process.compute()

    years = range(2051, 2071)
    for name in ("rpk", "airfare_per_rpk"):
        np.testing.assert_allclose(
            process.data["vector_outputs"].loc[years, name],
            reference.data["vector_outputs"].loc[years, name],
            rtol=1e-9,
            err_msg=name,
        )


def _assert_same_outputs(process, reference):
    assert process.data["years"] == reference.data["years"]
    for frame, name in (
        ("vector_outputs", "rpk"),
        ("vector_outputs", "airfare_per_rpk"),
        ("vector_outputs", "cumulative_co2_emissions"),
        ("climate_outputs", "temperature_increase_from_aviation"),
    ):
        np.testing.assert_allclose(
            process.data[frame][name], reference.data[frame][name], rtol=1e-9, err_msg=name
        )


def test_end_year_changed_between_computes_matches_fresh_processes(tmp_path):
    for name in ("2050", "2070", "changed"):
        (tmp_path / name).mkdir()
    reference_2050 = _elastic_process(tmp_path / "2050")
    reference_2050.compute()
    reference_2070 = _elastic_process(tmp_path / "2070", end_year_at_creation=2070)
    reference_2070.compute()

    process = _elastic_process(tmp_path / "changed")
    process.compute()
    process.parameters.end_year = 2070
    process.compute()
    _assert_same_outputs(process, reference_2070)

    process.parameters.end_year = 2050
    process.compute()
    _assert_same_outputs(process, reference_2050)


def _fleet_process(directory, end_year_at_creation=None):
    # The bottom-up fleet model keeps its own dataframe, outside the disciplines.
    shutil.copytree(Path(__file__).parent.parent / "tested_configs", directory)
    if end_year_at_creation is not None:
        inputs_file = directory / "data" / "inputs_advanced.json"
        inputs = json.loads(inputs_file.read_text())
        inputs["end_year"] = end_year_at_creation
        inputs_file.write_text(json.dumps(inputs))
    return create_process(configuration_file=str(directory / "config_advanced.yaml"))


def test_end_year_changed_between_computes_with_fleet_matches_fresh_process(tmp_path):
    reference = _fleet_process(tmp_path / "2070", end_year_at_creation=2070)
    reference.compute()

    process = _fleet_process(tmp_path / "changed")
    process.compute()
    process.parameters.end_year = 2070
    process.compute()
    _assert_same_outputs(process, reference)

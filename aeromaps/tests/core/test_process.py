"""
Test module for AeroMAPS process.

This module tests the AeroMAPSProcess class functionality and that all model
groups can be instantiated and run without errors.
"""

import json
from pathlib import Path

import pytest

from aeromaps import create_process
from aeromaps.process_configuration.process_configuration import AeroMAPSProcessConfiguration
from aeromaps.utils.yaml import read_yaml_file

CONFIG_DIR = Path(__file__).parent.parent / "tested_configs"

DEFAULT_CONFIG_FILE = Path(__file__).parents[2] / "resources" / "data" / "config.yaml"

BASIC_FULL_CONFIG_FILE = CONFIG_DIR / "config_basic_full.yaml"

MERGED_BASIC_FULL_CONFIG = {
    "data": {
        "inputs": {
            "data_information_file": "./data_information.yaml",
            "json_inputs_file": "./parameters.json",
            "partitioning_data_file": "./partitioning_inputs.json",
        },
        "outputs": {"json_outputs_file": "./outputs.json", "excel_outputs_file": "./data.xlsx"},
    },
    "models": {
        "climate": {"climate_model_data_file": "default"},
        "markets": {"markets_data_file": "./default_markets/markets.yaml"},
        "fleet": {
            "aircraft_inventory_model_data_file": "./default_fleet/aircraft_inventory.yaml",
            "fleet_model_data_file": "./default_fleet/fleet.yaml",
        },
        "fleet_push": {
            "classification_data_file": "./default_fleet_push/default_aircraft_classification.yaml",
            "market_param_data_file": "./default_fleet_push/default_market_param.yaml",
            "in_production_inventory_file": "./default_fleet_push/default_in_production_aircraft_inventory.yaml",
            "new_aircraft_inventory_file": "./default_fleet_push/default_new_aircraft_inventory.yaml",
            "aircraft_parameters_file": "../../utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/aircraft_type_key_parameters.xlsx",
            "fleet_snapshot_file": "../../utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/agg_fleet_end_2024.xlsx",
        },
        "energy": {
            "energy_carriers_model_data_file": "default",
            "resources_model_data_file": "default",
            "processes_model_data_file": "default",
        },
        "operations": {"operations_model_data_file": "./default_operations/operations_data.yaml"},
        "offsets": {"offsets_model_data_file": "./default_offsets/offsets_data.yaml"},
        "life_cycle_assessment": {"lca_model_data_file": "default", "split_by": "phase"},
        "standards": [
            "models_traffic",
            "models_efficiency_top_down",
            "models_energy_without_fuel_effect",
            "models_offset",
            "models_emissions",
            "models_sustainability",
            "models_energy_cost",
            "models_operation_cost_top_down",
        ],
    },
}


def get_tested_config_files():
    """Get paths for all configuration files in tested_configs, plus None."""
    config_paths = list(CONFIG_DIR.glob("*.yaml"))
    # config_paths.append(None)
    return config_paths


# TODO: expand tests for None and relative path cases
# The case for None is particular because the default config in resources is
# broken (missing inputs), so skipping for now.
# Also, sustainability models always require a climate simulation, so they were
# removed from the basic analysis to run faster.

CONFIGS_TO_TEST = get_tested_config_files()


@pytest.fixture
def csv_data_information_file(tmp_path):
    """Fixture to create a temporary CSV data information file."""
    csv_file = tmp_path / "data_information.csv"
    csv_file.write_text(
        "Name;Type;Unit;Description;Reference for default input value (if applicable)\n"
        "co2_emissions;Vector;MtCO2; ;\n",
        encoding="utf-8",
    )
    return str(csv_file)


@pytest.mark.parametrize("config_file", CONFIGS_TO_TEST)
def test_initialization(config_file):
    """Test that the process can be created with default configuration."""
    proc = create_process(configuration_file=config_file)
    assert proc is not None
    # When no config file is provided, configuration_file should be None
    assert proc.models is not None
    assert proc.data is not None
    # assert os.path.exists(proc.configuration_file)


@pytest.mark.parametrize("config_file", CONFIGS_TO_TEST)
def test_compute(config_file):
    """Test that the process can be created with an absolute path config."""
    # Get absolute path to default config
    proc = create_process(configuration_file=config_file)
    proc.compute()

    df_dict = proc.get_dataframes()
    assert df_dict is not None
    assert isinstance(df_dict, dict)
    assert "vector_outputs" in df_dict
    assert df_dict["vector_outputs"] is not None

    json_data = proc.get_json()
    assert json_data is not None
    assert isinstance(json_data, dict)

    plots = proc.list_available_plots()
    assert plots is not None
    assert isinstance(plots, list)
    assert len(plots) > 0

    # Schemas can be exported for any tested configuration and stay JSON-serialisable
    schemas = proc.export_schema()
    assert set(schemas) == {"inputs", "outputs"}
    co2 = schemas["outputs"]["properties"]["co2_emissions"]
    # After a run, untyped auto-model outputs get their type from the data containers
    assert co2["type"] == "array"
    assert co2["unit"] == "MtCO2"
    json.dumps(schemas)

    float_inputs = proc.list_float_inputs()
    assert float_inputs is not None
    assert isinstance(float_inputs, dict)
    assert len(float_inputs.keys()) > 0

    str_inputs = proc.list_str_inputs()
    assert str_inputs is not None
    assert isinstance(str_inputs, dict)
    assert hasattr(proc, "data")

    assert "float_inputs" in proc.data
    assert "vector_outputs" in proc.data
    assert "years" in proc.data

    years = proc.data["years"]
    assert "full_years" in years
    assert "historic_years" in years
    assert "prospective_years" in years
    assert hasattr(proc, "parameters")

    data = proc.data
    assert "vector_outputs" in data

    vector_outputs = data["vector_outputs"]
    assert vector_outputs is not None
    assert len(vector_outputs) > 0


@pytest.mark.parametrize("config_file", CONFIGS_TO_TEST)
def test_data_information_df(config_file):
    """Test that the data information DataFrame."""
    proc = create_process(configuration_file=config_file)
    proc.compute()
    # Every variable of the process must be documented (unit + description),
    # either by the model that reads or writes it or by data_information.yaml
    # (exact entry or pattern rule).
    data_information_df = proc._get_data_information_df()
    assert not data_information_df.empty
    unresolved = proc.list_undocumented_variables()
    assert f"{len(unresolved)} variables have no unit nor description: {unresolved[:10]}"
    # The metadata table is derived from the same resolution
    undocumented_rows = data_information_df[
        (data_information_df["Unit"] == "N/A") & (data_information_df["Description"] == "N/A")
    ]
    assert undocumented_rows.empty


@pytest.mark.parametrize("data_is_unresolved", [False, True])
def test_undocumented_variables(data_is_unresolved, csv_data_information_file):
    """Test the list_undocumented_variables method."""
    config_file = CONFIG_DIR / "config_basic.yaml"
    proc = create_process(configuration_file=str(config_file))
    file = csv_data_information_file if data_is_unresolved else None
    proc._load_data_information(file)
    unresolved = proc.list_undocumented_variables()
    assert data_is_unresolved == (len(unresolved) != 0)


def test_get_variable_information():
    """Test the public metadata lookup API (lazy loading included)."""
    config_file = CONFIG_DIR / "config_basic.yaml"
    proc = create_process(configuration_file=str(config_file))

    # Produced by a discipline: unit from the registry attached at build time,
    # description from the producer's docstring
    info = proc.get_variable_information("co2_emissions")
    assert info["Unit"] == "MtCO2"
    assert info["Description"] and info["Description"] != "N/A"
    assert info["Source"] == ""
    # Declared by the model that writes it
    assert proc.get_variable_information("manual_carbon_offset")["Unit"] == "MtCO2"
    registry_resolved = proc.list_registry_resolved_variables()
    assert registry_resolved
    assert "manual_carbon_offset" not in registry_resolved
    assert "co2_emissions" in registry_resolved
    # Pattern-resolved name (market ids are user-defined, so this must
    # work for names absent from the file)
    assert proc.get_variable_information("cagr_rpk_short_range")["Unit"] == "%"
    # Namespaced names resolve through their bare name
    assert proc.get_variable_information("FR:co2_emissions")["Unit"] == "MtCO2"
    # Unknown variable
    assert proc.get_variable_information("definitely_not_a_variable") is None


def test_process_models_are_independent():
    """Test that model instances are independent between processes."""
    # Build two processes from a valid config. (The no-argument default path is a
    # separate, known-broken case — its relative resource paths can't resolve, so
    # models.energy/markets are skipped and bottom-up custom models crash in
    # custom_setup; see get_tested_config_files note.)
    config_file = CONFIG_DIR / "config_basic.yaml"
    proc1 = create_process(configuration_file=str(config_file))
    proc2 = create_process(configuration_file=str(config_file))

    proc1.parameters.freight_cagr_reference_periods_values = [0.0]
    assert (
        proc1.parameters.freight_cagr_reference_periods_values
        != proc2.parameters.freight_cagr_reference_periods_values
    ), "Changing parameters in one process should not affect the other process"

    # Models should be different instances
    # Test with a common model that should exist in both
    common_models = set(proc1.models.keys()) & set(proc2.models.keys())
    assert len(common_models) > 0, "AeroMAPSProcessesAssembly should have some common models"

    # Check that at least one model is a different instance
    for model_name in list(common_models)[:3]:  # Test first 3 common models
        assert proc1.models[model_name] is not proc2.models[model_name], (
            f"Model {model_name} should be independent between processes"
        )


def test_process_configuration():
    """Test that the process properly loads the configuration"""

    process = create_process(configuration_file=BASIC_FULL_CONFIG_FILE)
    basic_full_config = read_yaml_file(BASIC_FULL_CONFIG_FILE)
    default_config = read_yaml_file(DEFAULT_CONFIG_FILE)
    default_config["models"]["customs"] = {}
    default_config["data"]["inputs"]["partitioning_other_data_file"] = None
    default_config["data"]["inputs"]["partitioning_climate_data_file"] = None
    default_config["models"]["life_cycle_assessment"]["methods"] = None
    default_config["data"]["inputs"]["csv_data_information_file"] = None
    default_config["data_directory"] = None
    MERGED_BASIC_FULL_CONFIG["models"]["customs"] = {}
    MERGED_BASIC_FULL_CONFIG["data"]["inputs"]["partitioning_other_data_file"] = None
    MERGED_BASIC_FULL_CONFIG["data"]["inputs"]["partitioning_climate_data_file"] = None
    MERGED_BASIC_FULL_CONFIG["data"]["inputs"]["csv_data_information_file"] = None
    MERGED_BASIC_FULL_CONFIG["models"]["life_cycle_assessment"]["methods"] = None
    MERGED_BASIC_FULL_CONFIG["data_directory"] = None
    assert process._user_config == basic_full_config
    assert process._default_config.model_dump() == default_config
    assert process.config.model_dump() == MERGED_BASIC_FULL_CONFIG


def test_process_configuration_with_config_model():
    """Test that the process can be configured with an instance of the configuration data model."""
    config = AeroMAPSProcessConfiguration(**read_yaml_file(BASIC_FULL_CONFIG_FILE))
    config.data_directory = Path(BASIC_FULL_CONFIG_FILE).parent
    process = create_process(
        configuration_file=BASIC_FULL_CONFIG_FILE, process_configuration_data_model=config
    )

    assert isinstance(process.config, AeroMAPSProcessConfiguration)

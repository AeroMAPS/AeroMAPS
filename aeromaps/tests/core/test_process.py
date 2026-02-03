"""
Test module for AeroMAPS process.

This module tests the AeroMAPSProcess class functionality.
"""

import pytest
import os
from aeromaps import create_process


def get_tested_config_files():
    """Get paths for configuration files to initialize process."""
    return [
        # None,
        # "./tested_configs/config_basic.yaml",
        # TODO: expand tests for None and relative path cases
        # The case for None is particular because the default config in resources is
        # broken (missing inputs), so skipping for now.
        # Also, sustainability models always require a climate simulation, so they were
        # removed from default_models_top_down
        "AeroMAPS/aeromaps/tests/core/tested_configs/config_basic.yaml",
    ]

CONFIGS_TO_TEST = get_tested_config_files()

@pytest.mark.parametrize("config_file", CONFIGS_TO_TEST)
def test_initialization(config_file):
    """Test that the process can be created with default configuration."""
    proc = create_process(configuration_file=config_file)
    assert proc is not None
    # When no config file is provided, configuration_file should be None
    assert proc.models is not None
    assert proc.data is not None
    assert os.path.exists(proc.configuration_file)

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

    float_inputs = proc.list_float_inputs()
    assert float_inputs is not None
    assert isinstance(float_inputs, dict)
    assert len(float_inputs.keys()) > 0

    str_inputs = proc.list_str_inputs()
    assert str_inputs is not None
    assert isinstance(str_inputs, dict)
    assert hasattr(proc, 'data')

    assert 'float_inputs' in proc.data
    assert 'vector_outputs' in proc.data
    assert 'years' in proc.data

    years = proc.data['years']
    assert 'full_years' in years
    assert 'historic_years' in years
    assert 'prospective_years' in years
    assert hasattr(proc, 'parameters')

    params = proc.parameters.to_dict()
    assert hasattr(params, 'float_parameters')

    data = proc.data
    assert 'vector_outputs' in data

    vector_outputs = data['vector_outputs']
    assert vector_outputs is not None
    assert len(vector_outputs) > 0

def test_process_models_are_independent():
    """Test that model instances are independent between processes."""
    # Create two processes with default config
    proc1 = create_process()
    proc2 = create_process()

    # Models should be different instances
    # Test with a common model that should exist in both
    common_models = set(proc1.models.keys()) & set(proc2.models.keys())
    assert len(common_models) > 0, "Processes should have some common models"

    # Check that at least one model is a different instance
    for model_name in list(common_models)[:3]:  # Test first 3 common models
        assert proc1.models[model_name] is not proc2.models[model_name], \
            f"Model {model_name} should be independent between processes"

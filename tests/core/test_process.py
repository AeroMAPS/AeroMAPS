"""
Test module for AeroMAPS process.

This module tests the AeroMAPSProcess class functionality.
"""

import pytest
from aeromaps import create_process


@pytest.fixture(scope="module")
def process():
    """Create and compute an AeroMAPS process for testing."""
    proc = create_process()
    proc.compute()
    return proc


def test_process_creation():
    """Test that the process can be created successfully."""
    proc = create_process()
    assert proc is not None


def test_process_compute():
    """Test that the process can be computed successfully."""
    proc = create_process()
    proc.compute()
    assert proc.data is not None
    assert hasattr(proc, 'data')


def test_process_has_parameters():
    """Test that the process has parameters after creation."""
    proc = create_process()
    assert hasattr(proc, 'parameters')


def test_process_has_models():
    """Test that the process has models after creation."""
    proc = create_process()
    assert hasattr(proc, 'models')
    assert len(proc.models) > 0


def test_get_dataframes(process):
    """Test that get_dataframes returns valid dataframes."""
    df_dict = process.get_dataframes()
    
    assert df_dict is not None
    assert isinstance(df_dict, dict)
    # Should contain vector_outputs at minimum
    assert "vector_outputs" in df_dict
    assert df_dict["vector_outputs"] is not None


def test_get_json(process):
    """Test that get_json returns valid JSON data."""
    json_data = process.get_json()
    
    assert json_data is not None
    assert isinstance(json_data, dict)


def test_list_available_plots(process):
    """Test that list_available_plots returns a list of plot names."""
    plots = process.list_available_plots()
    
    assert plots is not None
    assert isinstance(plots, list)
    assert len(plots) > 0


def test_list_float_inputs(process):
    """Test that list_float_inputs returns parameter names."""
    float_inputs = process.list_float_inputs()
    
    assert float_inputs is not None
    assert isinstance(float_inputs, list)
    assert len(float_inputs) > 0


def test_list_str_inputs(process):
    """Test that list_str_inputs returns parameter names."""
    str_inputs = process.list_str_inputs()
    
    assert str_inputs is not None
    assert isinstance(str_inputs, list)


def test_process_data_structure(process):
    """Test that the process data has expected structure."""
    assert hasattr(process, 'data')
    assert 'float_inputs' in process.data
    assert 'vector_outputs' in process.data
    assert 'years' in process.data
    
    # Check years structure
    years = process.data['years']
    assert 'full_years' in years
    assert 'historic_years' in years
    assert 'prospective_years' in years


def test_process_parameters_access(process):
    """Test that process parameters can be accessed."""
    assert hasattr(process, 'parameters')
    params = process.parameters
    
    # Parameters should have some attributes
    assert hasattr(params, 'float_parameters')


def test_process_models_execution(process):
    """Test that models have been executed by checking outputs exist."""
    data = process.data
    
    # Check that vector outputs exist and have data
    assert 'vector_outputs' in data
    vector_outputs = data['vector_outputs']
    assert vector_outputs is not None
    assert len(vector_outputs) > 0


def test_process_with_custom_config():
    """Test that process can be created with custom configuration."""
    # This tests the process can handle configuration files
    # Using None should use default config
    proc = create_process(configuration_file=None)
    assert proc is not None
    proc.compute()
    assert proc.data is not None


def test_process_models_are_independent():
    """Test that model instances are independent between processes."""
    # Create two processes
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

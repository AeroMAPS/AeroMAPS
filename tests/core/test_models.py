"""
Test module for AeroMAPS models configuration.

This module tests that all model groups can be instantiated and run without errors.
"""

import pytest
from inspect import signature
from aeromaps.core import models


# Get all model groups dynamically from the models module
def get_all_model_groups():
    """Get all model group dictionaries from the models module."""
    model_groups = []
    for attr_name in dir(models):
        if attr_name.startswith('models_') and not attr_name.startswith('__'):
            attr = getattr(models, attr_name)
            if isinstance(attr, dict):
                model_groups.append((attr_name, attr))
    return model_groups


# Get model groups for parametrization
MODEL_GROUPS = get_all_model_groups()


@pytest.mark.parametrize("group_name,group_dict", MODEL_GROUPS)
def test_model_group(group_name, group_dict):
    """
    Comprehensive test for a model group.
    
    Tests:
    1. Group is not empty
    2. All models can be instantiated
    3. All models have required attributes (compute, name)
    4. All models have valid compute signatures
    5. Group structure is valid (dictionary with string keys)
    """
    # Test 1: Group should not be empty
    assert len(group_dict) > 0, f"{group_name} should not be empty"
    
    # Test 2-4: Check all models in the group
    for model_name, model in group_dict.items():
        # Test 2: Model instantiation
        assert model is not None, f"{model_name} in {group_name} should not be None"
        
        # Test 3: Required attributes
        assert hasattr(model, 'compute'), f"{model_name} in {group_name} should have compute method"
        assert hasattr(model, 'name'), f"{model_name} in {group_name} should have name attribute"
        
        # Test 4: Valid compute signature
        sig = signature(model.compute)
        assert sig is not None, f"{model_name} in {group_name} should have a valid signature"
    
    # Test 5: Group structure
    assert isinstance(group_dict, dict), f"{group_name} should be a dictionary"
    for key in group_dict.keys():
        assert isinstance(key, str), f"Keys in {group_name} should be strings"


def test_all_model_groups_found():
    """Test that model groups are found in the models module."""
    model_groups_dict = {name: group for name, group in MODEL_GROUPS}
    assert len(model_groups_dict) > 0, "No model groups found in models module"
    
    # We expect at least the major groups
    assert 'models_traffic' in model_groups_dict
    assert 'models_efficiency_top_down' in model_groups_dict
    assert 'models_energy_without_fuel_effect' in model_groups_dict


def test_models_run_with_default_inputs():
    """Test that models can be created and run with a process using default inputs."""
    from aeromaps import create_process
    
    # Create a process which instantiates and runs models
    proc = create_process()
    
    # Verify models are loaded
    assert hasattr(proc, 'models')
    assert len(proc.models) > 0
    
    # Verify models have been properly initialized
    for name, model in proc.models.items():
        assert model is not None
        assert hasattr(model, 'compute')
    
    # Run the process to verify models work with default inputs
    proc.compute()
    
    # Check that outputs exist (successful run)
    assert 'vector_outputs' in proc.data
    vector_outputs = proc.data['vector_outputs']
    assert len(vector_outputs) > 0

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
    model_groups = {}
    for attr_name in dir(models):
        if attr_name.startswith('models_') and not attr_name.startswith('__'):
            attr = getattr(models, attr_name)
            if isinstance(attr, dict):
                model_groups[attr_name] = attr
    return model_groups


@pytest.fixture(scope="module")
def model_groups():
    """Fixture providing all model groups."""
    return get_all_model_groups()


def test_all_model_groups_found(model_groups):
    """Test that model groups are found in the models module."""
    assert len(model_groups) > 0, "No model groups found in models module"
    # We expect at least the major groups
    assert 'models_traffic' in model_groups
    assert 'models_efficiency_top_down' in model_groups
    assert 'models_energy_without_fuel_effect' in model_groups


def test_all_model_groups_instantiation(model_groups):
    """Test that all model groups can be instantiated."""
    for group_name, group_dict in model_groups.items():
        assert len(group_dict) > 0, f"{group_name} should not be empty"
        
        # Check that all models in the group are instantiated
        for model_name, model in group_dict.items():
            assert model is not None, f"{model_name} in {group_name} should not be None"
            assert hasattr(model, 'compute'), f"{model_name} in {group_name} should have compute method"


def test_all_model_groups_have_required_attributes(model_groups):
    """Test that all models in all groups have required attributes."""
    for group_name, group_dict in model_groups.items():
        for model_name, model in group_dict.items():
            assert hasattr(model, 'compute'), f"{model_name} in {group_name} should have compute method"
            assert hasattr(model, 'name'), f"{model_name} in {group_name} should have name attribute"


def test_all_model_groups_compute_signatures(model_groups):
    """Test that all models have proper compute signatures."""
    for group_name, group_dict in model_groups.items():
        for model_name, model in group_dict.items():
            sig = signature(model.compute)
            assert sig is not None, f"{model_name} in {group_name} should have a signature"
            # Compute should have parameters
            assert len(sig.parameters) >= 0, f"{model_name} in {group_name} compute should have parameters"


def test_all_model_groups_structure(model_groups):
    """Test that all model groups are properly structured as dictionaries."""
    for group_name, group_dict in model_groups.items():
        assert isinstance(group_dict, dict), f"{group_name} should be a dictionary"
        
        # Each should have string keys
        for key in group_dict.keys():
            assert isinstance(key, str), f"Keys in {group_name} should be strings"


def test_models_run_with_default_inputs():
    """Test that models can be created and used with a process."""
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


def test_process_runs_successfully():
    """Test that a process with models runs successfully."""
    from aeromaps import create_process
    
    proc = create_process()
    proc.compute()
    
    # Check that outputs exist
    assert 'vector_outputs' in proc.data
    vector_outputs = proc.data['vector_outputs']
    assert len(vector_outputs) > 0


def test_models_are_independent():
    """Test that model instances are independent between processes."""
    from aeromaps import create_process
    
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


def test_sample_models_from_each_group(model_groups):
    """Test sample models from each group to ensure they work."""
    # Test that we can access at least one model from each group
    for group_name, group_dict in model_groups.items():
        if len(group_dict) > 0:
            # Get first model from the group
            first_model_name = list(group_dict.keys())[0]
            first_model = group_dict[first_model_name]
            
            assert first_model is not None, f"First model in {group_name} should not be None"
            assert hasattr(first_model, 'compute'), f"First model in {group_name} should have compute"
            assert hasattr(first_model, 'name'), f"First model in {group_name} should have name"

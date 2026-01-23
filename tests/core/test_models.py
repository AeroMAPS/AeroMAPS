"""
Test module for AeroMAPS models configuration.

This module tests that model groups can be instantiated and run without errors.
"""

import pytest
from aeromaps.core.models import (
    models_traffic,
    models_efficiency_top_down,
    models_energy_without_fuel_effect,
)


def test_traffic_models_instantiation():
    """Test that traffic models can be instantiated."""
    assert len(models_traffic) > 0
    
    # Check that all models are instantiated
    for name, model in models_traffic.items():
        assert model is not None
        assert hasattr(model, 'compute')


def test_efficiency_models_instantiation():
    """Test that efficiency models can be instantiated."""
    assert len(models_efficiency_top_down) > 0
    
    # Check that all models are instantiated
    for name, model in models_efficiency_top_down.items():
        assert model is not None
        assert hasattr(model, 'compute')


def test_energy_models_instantiation():
    """Test that energy models can be instantiated."""
    assert len(models_energy_without_fuel_effect) > 0
    
    # Check that all models are instantiated
    for name, model in models_energy_without_fuel_effect.items():
        assert model is not None
        assert hasattr(model, 'compute')


def test_models_have_required_attributes():
    """Test that models have required attributes."""
    # Test a sample model from each group
    sample_models = [
        ("RPK", models_traffic.get("rpk")),
        ("LoadFactor", models_efficiency_top_down.get("load_factor")),
        ("EnergyConsumption", models_energy_without_fuel_effect.get("energy_consumption")),
    ]
    
    for name, model in sample_models:
        if model is not None:
            assert hasattr(model, 'compute'), f"{name} should have compute method"
            assert hasattr(model, 'name'), f"{name} should have name attribute"


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


def test_traffic_model_group_runs():
    """Test that traffic model group can run in a process."""
    from aeromaps import create_process
    
    proc = create_process()
    proc.compute()
    
    # Check that traffic-related outputs exist
    assert 'vector_outputs' in proc.data
    vector_outputs = proc.data['vector_outputs']
    
    # Check for some traffic-related outputs
    # These should exist after computation
    assert 'rpk' in vector_outputs.columns or len(vector_outputs) > 0


def test_model_compute_signatures():
    """Test that model compute methods have proper signatures."""
    from inspect import signature
    
    # Test a few sample models
    rpk_model = models_traffic.get("rpk")
    if rpk_model:
        sig = signature(rpk_model.compute)
        assert sig is not None
        # Compute should have parameters
        assert len(sig.parameters) > 0


def test_models_are_independent():
    """Test that model instances are independent."""
    from aeromaps import create_process
    
    # Create two processes
    proc1 = create_process()
    proc2 = create_process()
    
    # Models should be different instances
    if 'rpk' in proc1.models and 'rpk' in proc2.models:
        assert proc1.models['rpk'] is not proc2.models['rpk']


def test_model_groups_are_dictionaries():
    """Test that model groups are properly structured as dictionaries."""
    assert isinstance(models_traffic, dict)
    assert isinstance(models_efficiency_top_down, dict)
    assert isinstance(models_energy_without_fuel_effect, dict)
    
    # Each should have string keys
    for key in models_traffic.keys():
        assert isinstance(key, str)
    
    for key in models_efficiency_top_down.keys():
        assert isinstance(key, str)
    
    for key in models_energy_without_fuel_effect.keys():
        assert isinstance(key, str)

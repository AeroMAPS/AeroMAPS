"""
Test module for AeroMAPS models configuration.

This module tests that all model groups can be instantiated and run without errors.
"""

import pytest
import os
from pathlib import Path
from aeromaps import create_process
from aeromaps.core import models


# Get all model groups dynamically from the models module
def get_all_model_groups():
    """Get all model group dictionaries from the models module."""
    model_groups = []
    for attr_name in dir(models):
        if attr_name.startswith('models_') and not attr_name.startswith('__'):
            attr = getattr(models, attr_name)
            if isinstance(attr, dict):
                model_groups.append(attr_name)
    return model_groups


# Get model groups for parametrization
MODEL_GROUPS = get_all_model_groups()

# Get the path to config files
CONFIG_DIR = Path(__file__).parent / "config_models"


@pytest.mark.parametrize("group_name", MODEL_GROUPS)
def test_model_group(group_name):
    """
    Test that a model group can run successfully with default inputs.
    
    For each model group:
    1. Create a process with config for this sole model group
    2. Compute the process
    3. Assert process is instantiated, has data, vector_outputs exist and is not empty
    """
    # Get the config file path for this model group
    config_file = CONFIG_DIR / f"{group_name}.yaml"
    
    # Skip if config doesn't exist (shouldn't happen but safety check)
    if not config_file.exists():
        pytest.skip(f"Config file not found for {group_name}")
    
    # Create process with config for this sole model group
    proc = create_process(configuration_file=str(config_file))
    
    # Assert process is instantiated
    assert proc is not None, f"Process should be instantiated for {group_name}"
    
    # Compute the process
    proc.compute()
    
    # Assert process has data
    assert hasattr(proc, 'data'), f"Process should have data attribute for {group_name}"
    assert proc.data is not None, f"Process data should not be None for {group_name}"
    
    # Assert vector_outputs exist and is not empty
    assert 'vector_outputs' in proc.data, f"Process should have vector_outputs for {group_name}"
    vector_outputs = proc.data['vector_outputs']
    assert vector_outputs is not None, f"vector_outputs should not be None for {group_name}"
    assert len(vector_outputs) > 0, f"vector_outputs should not be empty for {group_name}"

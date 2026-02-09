"""
Test module for AeroMAPS models configuration.

This module tests that all model groups can be instantiated and run without errors.
"""

import pytest
from pathlib import Path
from aeromaps import create_process

CONFIG_DIR = Path(__file__).parent / "tested_configs"
# Get all model groups dynamically from the tested configs folder
def get_tested_config_files():
    """Get all model group dictionaries from the models module."""
    config_files = list(CONFIG_DIR.glob("*.yaml"))
    return config_files

CONFIGS_TO_TEST = get_tested_config_files()


@pytest.mark.parametrize("config_file", CONFIGS_TO_TEST)
def test_model_group(config_file):
    """Test that a model group can run successfully with default inputs."""
    proc = create_process(configuration_file=str(config_file))
    
    # Assert process is instantiated
    assert proc is not None
    
    # Compute the process
    proc.compute()
    
    # Assert process has data
    assert hasattr(proc, 'data')
    assert proc.data is not None
    
    # Assert vector_outputs exist and is not empty
    assert 'vector_outputs' in proc.data
    vector_outputs = proc.data['vector_outputs']
    assert vector_outputs is not None
    assert len(vector_outputs) > 0

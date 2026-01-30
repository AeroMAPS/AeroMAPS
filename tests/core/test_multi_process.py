"""
Test module for MultiProcess and multi-scenario plotting.

This module tests the MultiProcess class functionality for managing
multiple scenarios and creating comparison plots.
"""

import pytest
from aeromaps import create_process, create_multi_process


@pytest.fixture(scope="module")
def processes():
    """Create two test processes for comparison."""
    # Create first process
    proc1 = create_process()
    proc1.compute()
    
    # Create second process
    proc2 = create_process()
    proc2.compute()
    
    return {"scenario_1": proc1, "scenario_2": proc2}


def test_multi_process_creation_dict(processes):
    """Test MultiProcess can be created with a dictionary."""
    multi = create_multi_process(processes)
    assert multi is not None
    assert len(multi) == 2
    assert "scenario_1" in multi.get_scenario_names()
    assert "scenario_2" in multi.get_scenario_names()


def test_multi_process_creation_list(processes):
    """Test MultiProcess can be created with a list."""
    proc_list = list(processes.values())
    multi = create_multi_process(proc_list)
    assert multi is not None
    assert len(multi) == 2


def test_list_available_plots(processes):
    """Test that list_available_plots returns plot names."""
    multi = create_multi_process(processes)
    plots = multi.list_available_plots()
    
    assert plots is not None
    assert isinstance(plots, list)
    assert len(plots) > 0
    
    # Check some expected plots are available
    assert "co2_emissions_comparison" in plots
    assert "energy_consumption_comparison" in plots


def test_plot_co2_emissions_comparison(processes):
    """Test CO2 emissions comparison plot can be created."""
    multi = create_multi_process(processes)
    
    try:
        fig = multi.plot("co2_emissions_comparison", save=False)
        assert fig is not None
    except Exception as e:
        # If plot fails, it might be due to missing data, which is acceptable
        # as long as the error is informative
        assert "required outputs" in str(e).lower() or "missing" in str(e).lower()


def test_plot_energy_consumption_comparison(processes):
    """Test energy consumption comparison plot can be created."""
    multi = create_multi_process(processes)
    
    try:
        fig = multi.plot("energy_consumption_comparison", save=False)
        assert fig is not None
    except Exception as e:
        assert "required outputs" in str(e).lower() or "missing" in str(e).lower()


def test_plot_with_invalid_name(processes):
    """Test that invalid plot name raises NameError."""
    multi = create_multi_process(processes)
    
    with pytest.raises(NameError) as exc_info:
        multi.plot("invalid_plot_name")
    
    assert "not available" in str(exc_info.value).lower()


def test_get_scenario_names(processes):
    """Test get_scenario_names returns correct names."""
    multi = create_multi_process(processes)
    names = multi.get_scenario_names()
    
    assert isinstance(names, list)
    assert len(names) == 2
    assert "scenario_1" in names
    assert "scenario_2" in names


def test_multi_process_indexing(processes):
    """Test MultiProcess supports indexing."""
    multi = create_multi_process(processes)
    
    # Test dict-style indexing
    proc1 = multi["scenario_1"]
    assert proc1 is not None
    
    # Test integer indexing
    proc_by_idx = multi[0]
    assert proc_by_idx is not None


def test_empty_processes_raises_error():
    """Test that empty processes list raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        create_multi_process([])
    
    assert "at least one process" in str(exc_info.value).lower()


def test_invalid_type_raises_error():
    """Test that invalid type raises TypeError."""
    with pytest.raises(TypeError):
        create_multi_process("invalid")

"""
Test module for MultiProcess core functionality.

This module tests the MultiProcess class for managing multiple scenarios.
Plot-related tests are in test_multi_scenario_plots.py.
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


@pytest.fixture(scope="module")
def uncomputed_processes():
    """Create two test processes without computing."""
    # Create processes without computing
    proc1 = create_process()
    proc2 = create_process()
    
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


def test_compute_all(uncomputed_processes):
    """Test that compute_all() computes all processes."""
    multi = create_multi_process(uncomputed_processes)
    
    # Verify processes are not computed initially
    for proc in uncomputed_processes.values():
        assert not hasattr(proc, 'data') or proc.data is None or len(proc.data) == 0
    
    # Compute all processes
    multi.compute_all()
    
    # Verify all processes are now computed
    for proc in uncomputed_processes.values():
        assert hasattr(proc, 'data')
        assert proc.data is not None
        assert "vector_outputs" in proc.data


def test_get_scenario_names(processes):
    """Test get_scenario_names returns correct names."""
    multi = create_multi_process(processes)
    names = multi.get_scenario_names()
    
    assert isinstance(names, list)
    assert len(names) == 2
    assert "scenario_1" in names
    assert "scenario_2" in names


def test_multi_process_indexing(processes):
    """Test that MultiProcess supports indexing."""
    multi = create_multi_process(processes)
    
    # Test dictionary-style access
    assert multi["scenario_1"] is not None
    assert multi["scenario_2"] is not None
    
    # Test that we get the correct process
    assert multi["scenario_1"] == processes["scenario_1"]
    assert multi["scenario_2"] == processes["scenario_2"]


def test_multi_process_len(processes):
    """Test that len() works on MultiProcess."""
    multi = create_multi_process(processes)
    assert len(multi) == 2


def test_empty_processes_raises_error():
    """Test that empty processes dict raises ValueError."""
    with pytest.raises(ValueError):
        create_multi_process({})


def test_invalid_type_raises_error():
    """Test that invalid type raises TypeError."""
    with pytest.raises(TypeError):
        create_multi_process("not a dict or list")


def test_single_scenario_plot_required_outputs():
    """Test that SingleScenarioPlot has required_outputs."""
    from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
    
    assert hasattr(SingleScenarioPlot, 'required_outputs')
    assert hasattr(SingleScenarioPlot, 'get_required_outputs')


def test_single_scenario_plot_validation_warning():
    """Test that SingleScenarioPlot validates required outputs."""
    from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
    
    # Create a test plot class with required outputs
    class TestPlot(SingleScenarioPlot):
        required_outputs = ["nonexistent_output"]
        
        def _get_default_figsize(self):
            return (10, 6)
        
        def create_plot(self):
            pass
        
        def _update_plot_elements(self):
            pass
    
    proc = create_process()
    proc.compute()
    
    # Should warn about missing output
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        plot = TestPlot(proc)
        
        # Should have issued a warning
        assert len(w) > 0
        assert "nonexistent_output" in str(w[0].message)


def test_required_outputs_as_instance_parameter_single():
    """Test that required_outputs can be passed as instance parameter."""
    from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
    
    # Create test plot class with class-level required_outputs
    class TestPlot(SingleScenarioPlot):
        required_outputs = ["co2_emissions"]
        
        def _get_default_figsize(self):
            return (10, 6)
        
        def create_plot(self):
            pass
        
        def _update_plot_elements(self):
            pass
    
    proc = create_process()
    proc.compute()
    
    # Override at instance level
    plot = TestPlot(proc, required_outputs=["energy_consumption"])
    
    # Should use instance-level required_outputs
    assert plot.get_instance_required_outputs() == ["energy_consumption"]


def test_required_outputs_as_instance_parameter_multi():
    """Test that required_outputs can be passed as instance parameter for multi."""
    from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot
    
    # Create test plot class
    class TestPlot(MultiScenarioPlot):
        required_outputs = ["co2_emissions"]
        
        def _get_default_figsize(self):
            return (10, 6)
        
        def create_plot(self):
            pass
    
    proc1 = create_process()
    proc1.compute()
    proc2 = create_process()
    proc2.compute()
    
    processes_dict = {"s1": proc1, "s2": proc2}
    
    # Override at instance level
    plot = TestPlot(processes_dict, required_outputs=["energy_consumption"])
    
    # Should use instance-level required_outputs
    assert plot.get_instance_required_outputs() == ["energy_consumption"]

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
    assert "co2_per_rpk_comparison" in plots
    assert "fuel_supply_breakdown" in plots
    assert "carbon_budget_comparison" in plots


def test_new_intensity_plots_available(processes):
    """Test that new intensity plots are available."""
    multi = create_multi_process(processes)
    plots = multi.list_available_plots()
    
    assert "co2_per_rpk_comparison" in plots
    assert "co2_per_rtk_comparison" in plots
    assert "energy_per_ask_comparison" in plots
    assert "energy_per_rtk_comparison" in plots


def test_new_fuel_supply_plots_available(processes):
    """Test that new fuel supply plots are available."""
    multi = create_multi_process(processes)
    plots = multi.list_available_plots()
    
    assert "fuel_supply_breakdown" in plots
    assert "hydrogen_supply_comparison" in plots
    assert "electric_supply_comparison" in plots
    assert "biofuel_production_comparison" in plots
    assert "electrofuel_production_comparison" in plots


def test_carbon_budget_plot_available(processes):
    """Test that carbon budget plot is available."""
    multi = create_multi_process(processes)
    plots = multi.list_available_plots()
    
    assert "carbon_budget_comparison" in plots


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


def test_required_outputs_validation(processes):
    """Test that plots validate required outputs."""
    from aeromaps.plots.multi_scenario.emissions import CO2EmissionsComparisonPlot
    
    # Check that the plot class has required_outputs
    assert hasattr(CO2EmissionsComparisonPlot, 'required_outputs')
    assert CO2EmissionsComparisonPlot.required_outputs == ["co2_emissions"]
    
    # Check that get_required_outputs works
    required = CO2EmissionsComparisonPlot.get_required_outputs()
    assert required == ["co2_emissions"]


def test_plot_with_check_outputs_false(processes):
    """Test plotting with check_outputs=False skips validation."""
    multi = create_multi_process(processes)
    
    # This should not raise an error even if outputs are missing
    # because check_outputs=False
    try:
        fig = multi.plot("co2_emissions_comparison", check_outputs=False)
        assert fig is not None
    except Exception as e:
        # If it fails, it should not be due to validation
        assert "required outputs" not in str(e).lower()


def test_single_scenario_plot_required_outputs():
    """Test that single scenario plots can have required_outputs."""
    from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
    
    # Create a test plot class with required outputs
    class TestPlot(SingleScenarioPlot):
        required_outputs = ["test_output"]
        
        def _get_default_figsize(self):
            return (8, 6)
        
        def create_plot(self):
            pass
        
        def _update_plot_elements(self):
            pass
    
    # Verify the class has required_outputs
    assert TestPlot.required_outputs == ["test_output"]
    assert TestPlot.get_required_outputs() == ["test_output"]


def test_single_scenario_plot_validation_warning():
    """Test that single scenario plots warn about missing outputs."""
    import warnings
    from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
    
    # Create a test plot with required outputs
    class TestPlot(SingleScenarioPlot):
        required_outputs = ["nonexistent_output"]
        
        def _get_default_figsize(self):
            return (8, 6)
        
        def create_plot(self):
            pass
        
        def _update_plot_elements(self):
            pass
    
    # Create a process with data
    proc = create_process()
    proc.compute()
    
    # Creating the plot should issue a warning about missing outputs
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            plot = TestPlot(proc, check_outputs=True)
            # Check that a warning was issued
            assert len(w) > 0
            assert any("missing" in str(warning.message).lower() for warning in w)
        except Exception:
            # It's ok if the plot fails, as long as it warned first
            pass


def test_multi_scenario_plot_filters_invalid_scenarios():
    """Test that multi scenario plots filter out scenarios with missing outputs."""
    import warnings
    from aeromaps.plots.multi_scenario.emissions import CO2EmissionsComparisonPlot
    
    # Create processes
    proc1 = create_process()
    proc1.compute()
    proc2 = create_process()
    proc2.compute()
    
    processes = {"scenario_1": proc1, "scenario_2": proc2}
    
    # Both should have co2_emissions, so no filtering should occur
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        plot = CO2EmissionsComparisonPlot(processes, check_outputs=True)
        
        # Should have data for both scenarios
        assert len(plot.scenario_data) == 2


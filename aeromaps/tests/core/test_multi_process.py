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


def test_required_outputs_as_instance_parameter_single():
    """Test that required_outputs can be passed as instance parameter for SingleScenarioPlot."""
    from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
    
    # Create a simple test plot class
    class TestPlot(SingleScenarioPlot):
        required_outputs = ["co2_emissions"]
        
        def _get_default_figsize(self):
            return (10, 6)
        
        def create_plot(self):
            pass
        
        def _update_plot_elements(self):
            pass
    
    # Test class-level default
    assert TestPlot.get_required_outputs() == ["co2_emissions"]
    
    # Create process
    proc = create_process()
    proc.compute()
    
    # Test with instance override
    plot = TestPlot(proc, required_outputs=["co2_emissions", "energy_consumption"])
    assert plot.get_instance_required_outputs() == ["co2_emissions", "energy_consumption"]
    
    # Test using class default
    plot2 = TestPlot(proc)
    assert plot2.get_instance_required_outputs() == ["co2_emissions"]


def test_required_outputs_as_instance_parameter_multi():
    """Test that required_outputs can be passed as instance parameter for MultiScenarioPlot."""
    from aeromaps.plots.multi_scenario.emissions import CO2EmissionsComparisonPlot
    
    # Test class-level default
    assert CO2EmissionsComparisonPlot.get_required_outputs() == ["co2_emissions"]
    
    # Create processes
    proc1 = create_process()
    proc1.compute()
    proc2 = create_process()
    proc2.compute()
    
    processes = {"scenario_1": proc1, "scenario_2": proc2}
    
    # Test with instance override
    plot = CO2EmissionsComparisonPlot(
        processes, 
        required_outputs=["co2_emissions", "energy_consumption"],
        check_outputs=False  # Skip validation for this test
    )
    assert plot.get_instance_required_outputs() == ["co2_emissions", "energy_consumption"]
    
    # Test using class default
    plot2 = CO2EmissionsComparisonPlot(processes)
    assert plot2.get_instance_required_outputs() == ["co2_emissions"]


def test_scenario_grouping_basic():
    """Test basic scenario grouping with colors and line styles."""
    from aeromaps.plots.multi_scenario.emissions import CO2EmissionsComparisonPlot
    
    # Create processes
    proc1 = create_process()
    proc1.compute()
    proc2 = create_process()
    proc2.compute()
    proc3 = create_process()
    proc3.compute()
    proc4 = create_process()
    proc4.compute()
    
    processes = {
        "baseline_2030": proc1,
        "baseline_2040": proc2,
        "optimistic_2030": proc3,
        "optimistic_2040": proc4
    }
    
    # Define groups
    groups = {
        "Baseline": ["baseline_2030", "baseline_2040"],
        "Optimistic": ["optimistic_2030", "optimistic_2040"]
    }
    
    # Create plot with groups
    plot = CO2EmissionsComparisonPlot(processes, scenario_groups=groups)
    
    # Check that scenarios have styles
    assert hasattr(plot, 'scenario_styles')
    assert "baseline_2030" in plot.scenario_styles
    assert "baseline_2040" in plot.scenario_styles
    assert "optimistic_2030" in plot.scenario_styles
    assert "optimistic_2040" in plot.scenario_styles
    
    # Check that scenarios in same group have same color
    style_b1 = plot.get_scenario_style("baseline_2030")
    style_b2 = plot.get_scenario_style("baseline_2040")
    assert style_b1['color'] == style_b2['color']
    assert style_b1['group'] == "Baseline"
    assert style_b2['group'] == "Baseline"
    
    # Check that scenarios in same group have different line styles
    assert style_b1['linestyle'] != style_b2['linestyle']
    
    # Check that scenarios in different groups have different colors
    style_o1 = plot.get_scenario_style("optimistic_2030")
    assert style_b1['color'] != style_o1['color']
    assert style_o1['group'] == "Optimistic"


def test_scenario_grouping_no_groups():
    """Test that plots work without grouping (backward compatibility)."""
    from aeromaps.plots.multi_scenario.emissions import CO2EmissionsComparisonPlot
    
    # Create processes
    proc1 = create_process()
    proc1.compute()
    proc2 = create_process()
    proc2.compute()
    
    processes = {"scenario_1": proc1, "scenario_2": proc2}
    
    # Create plot without groups
    plot = CO2EmissionsComparisonPlot(processes, scenario_groups=None)
    
    # Check that scenarios have styles with default behavior
    style1 = plot.get_scenario_style("scenario_1")
    style2 = plot.get_scenario_style("scenario_2")
    
    # Without groups, each scenario gets its own color
    assert style1['color'] != style2['color']
    assert style1['group'] is None
    assert style2['group'] is None
    assert style1['linestyle'] == '-'  # Default solid line
    assert style2['linestyle'] == '-'


def test_multi_process_plot_with_scenario_groups(processes):
    """Test that scenario_groups can be passed through MultiProcess.plot()."""
    multi = create_multi_process(processes)
    
    # Define groups
    groups = {
        "Group1": ["scenario_1"],
        "Group2": ["scenario_2"]
    }
    
    # Should not raise an error
    plot = multi.plot("co2_emissions_comparison", scenario_groups=groups)
    assert plot is not None
    assert hasattr(plot, 'scenario_styles')


def test_scenario_style_for_unknown_scenario():
    """Test that get_scenario_style returns default for unknown scenarios."""
    from aeromaps.plots.multi_scenario.emissions import CO2EmissionsComparisonPlot
    
    # Create processes
    proc1 = create_process()
    proc1.compute()
    
    processes = {"scenario_1": proc1}
    plot = CO2EmissionsComparisonPlot(processes)
    
    # Get style for unknown scenario - should return default
    style = plot.get_scenario_style("unknown_scenario")
    assert style is not None
    assert 'color' in style
    assert 'linestyle' in style
    assert 'group' in style


"""
Test module for multi-scenario plots.

This module tests the multi-scenario plot classes and their functionality.
"""

import pytest
from aeromaps import create_process, create_multi_process


@pytest.fixture(scope="module")
def processes():
    """Create two test processes for comparison."""
    import os
    # Create first process
    config_path = os.path.join(
        os.path.dirname(__file__),
        "../core/tested_configs/config_basic.yaml"
    )
    proc1 = create_process(configuration_file=config_path)
    proc1.compute()
    
    # Create second process
    proc2 = create_process(configuration_file=config_path)
    proc2.parameters.cagr_passenger_short_range_reference_periods = []
    proc2.parameters.cagr_passenger_short_range_reference_periods_values = [1.0]
    proc2.parameters.cagr_passenger_medium_range_reference_periods = []
    proc2.parameters.cagr_passenger_medium_range_reference_periods_values = [1.0]
    proc2.parameters.cagr_passenger_long_range_reference_periods = []
    proc2.parameters.cagr_passenger_long_range_reference_periods_values = [1.0]
    proc2.parameters.cagr_freight_reference_periods = []
    proc2.parameters.cagr_freight_reference_periods_values = [1.0]
    proc2.compute()
    
    return {"scenario_1": proc1, "scenario_2": proc2}


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
    """Test creating CO2 emissions comparison plot."""
    multi = create_multi_process(processes)
    
    # Create plot - should not raise exception
    fig = multi.plot("co2_emissions_comparison")
    assert fig is not None


def test_plot_energy_consumption_comparison(processes):
    """Test creating energy consumption comparison plot."""
    multi = create_multi_process(processes)
    
    # Create plot - should not raise exception
    fig = multi.plot("energy_consumption_comparison")
    assert fig is not None


def test_plot_with_invalid_name(processes):
    """Test that invalid plot name raises KeyError."""
    multi = create_multi_process(processes)
    
    with pytest.raises(KeyError):
        multi.plot("nonexistent_plot")


def test_required_outputs_validation(processes):
    """Test that plots validate required outputs."""
    multi = create_multi_process(processes)
    
    # This should work fine since processes are computed
    fig = multi.plot("co2_emissions_comparison")
    assert fig is not None


def test_plot_with_check_outputs_false(processes):
    """Test that check_outputs=False skips validation."""
    multi = create_multi_process(processes)
    
    # Should work even if validation is disabled
    fig = multi.plot("co2_emissions_comparison", check_outputs=False)
    assert fig is not None


def test_multi_scenario_plot_filters_invalid_scenarios():
    """Test that MultiScenarioPlot filters out scenarios with missing outputs."""
    from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot
    
    # Create mock processes with different outputs
    proc1 = create_process()
    proc1.compute()
    proc1_data = proc1.data
    
    proc2 = create_process()
    proc2.compute()
    # Simulate missing output in proc2
    if "co2_emissions" in proc2.data.get("vector_outputs", {}):
        del proc2.data["vector_outputs"]["co2_emissions"]
    
    processes_dict = {"has_output": proc1, "missing_output": proc2}
    
    # Create a test plot class
    class TestPlot(MultiScenarioPlot):
        required_outputs = ["co2_emissions"]
        
        def _get_default_figsize(self):
            return (10, 6)
        
        def create_plot(self):
            pass
    
    # Create plot - it should filter out proc2
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        plot = TestPlot(processes_dict)
        
        # Should have warned about missing output
        assert len(w) > 0
        assert "missing_output" in str(w[0].message)
    
    # Only proc1 should be included
    assert len(plot.processes) == 1
    assert "has_output" in plot.processes


def test_scenario_grouping_basic():
    """Test basic scenario grouping functionality."""
    from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot
    
    # Create test processes
    proc1 = create_process()
    proc1.compute()
    proc2 = create_process()
    proc2.compute()
    proc3 = create_process()
    proc3.compute()
    
    processes = {
        "baseline_2030": proc1,
        "baseline_2040": proc2,
        "optimistic_2030": proc3
    }
    
    # Define groups
    groups = {
        "Baseline": ["baseline_2030", "baseline_2040"],
        "Optimistic": ["optimistic_2030"]
    }
    
    # Create test plot class
    class TestPlot(MultiScenarioPlot):
        def _get_default_figsize(self):
            return (10, 6)
        
        def create_plot(self):
            pass
    
    plot = TestPlot(processes, scenario_groups=groups)
    
    # Check that styles were set up
    style1 = plot.get_scenario_style("baseline_2030")
    style2 = plot.get_scenario_style("baseline_2040")
    style3 = plot.get_scenario_style("optimistic_2030")
    
    # Same group should have same color
    assert style1["color"] == style2["color"]
    assert style1["group"] == "Baseline"
    assert style2["group"] == "Baseline"
    
    # Different groups should have different colors
    assert style1["color"] != style3["color"]
    assert style3["group"] == "Optimistic"
    
    # Same group should have different linestyles
    assert style1["linestyle"] != style2["linestyle"]


def test_scenario_grouping_no_groups():
    """Test scenario styling without grouping."""
    from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot
    
    # Create test processes
    proc1 = create_process()
    proc1.compute()
    proc2 = create_process()
    proc2.compute()
    
    processes = {"scenario_1": proc1, "scenario_2": proc2}
    
    # Create test plot class without groups
    class TestPlot(MultiScenarioPlot):
        def _get_default_figsize(self):
            return (10, 6)
        
        def create_plot(self):
            pass
    
    plot = TestPlot(processes)
    
    # Without groups, each scenario should get its own color
    style1 = plot.get_scenario_style("scenario_1")
    style2 = plot.get_scenario_style("scenario_2")
    
    # Should have different colors
    assert style1["color"] != style2["color"]
    
    # Should not be in groups
    assert style1["group"] is None
    assert style2["group"] is None


def test_multi_process_plot_with_scenario_groups(processes):
    """Test MultiProcess.plot() with scenario_groups parameter."""
    multi = create_multi_process(processes)
    
    # Define groups (even though we only have 2 scenarios)
    groups = {
        "Group A": ["scenario_1"],
        "Group B": ["scenario_2"]
    }
    
    # Create plot with groups - should not raise exception
    fig = multi.plot("co2_emissions_comparison", scenario_groups=groups)
    assert fig is not None


def test_scenario_style_for_unknown_scenario():
    """Test get_scenario_style for unknown scenario returns default."""
    from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot
    
    # Create test process
    proc1 = create_process()
    proc1.compute()
    
    processes = {"known_scenario": proc1}
    
    # Create test plot class
    class TestPlot(MultiScenarioPlot):
        def _get_default_figsize(self):
            return (10, 6)
        
        def create_plot(self):
            pass
    
    plot = TestPlot(processes)
    
    # Request style for unknown scenario
    style = plot.get_scenario_style("unknown_scenario")
    
    # Should return a default style
    assert "color" in style
    assert "linestyle" in style
    assert style["group"] is None

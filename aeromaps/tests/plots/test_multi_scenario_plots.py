"""
Test module for multi-scenario plots.

This module tests the multi-scenario plot classes and their functionality.
"""

import pytest
from aeromaps import create_process, assemble_processes


@pytest.fixture(scope="module")
def processes():
    """Create two test processes for comparison."""
    import os

    # Create first process
    config_basic = os.path.join(os.path.dirname(__file__), "../tested_configs/config_basic.yaml")
    proc1 = create_process(configuration_file=config_basic)
    proc1.compute()

    proc2 = create_process(configuration_file=config_basic)
    proc2.parameters.short_range_cagr_reference_periods = []
    proc2.parameters.short_range_cagr_reference_periods_values = [1.0]
    proc2.parameters.medium_range_cagr_reference_periods = []
    proc2.parameters.medium_range_cagr_reference_periods_values = [1.0]
    proc2.parameters.long_range_cagr_reference_periods = []
    proc2.parameters.long_range_cagr_reference_periods_values = [1.0]
    proc2.parameters.freight_cagr_reference_periods = []
    proc2.parameters.freight_cagr_reference_periods_values = [1.0]
    proc2.compute()

    config_full = os.path.join(
        os.path.dirname(__file__), "../tested_configs/config_basic_full.yaml"
    )
    proc3 = create_process(configuration_file=config_full)
    proc3.compute()

    return {"scenario_1": proc1, "scenario_2": proc2, "scenario_3": proc3}


EXPECTED_PLOTS = [
    # Emissions
    "co2_emissions_comparison",
    "cumulative_co2_emissions_comparison",
    # Energy
    "energy_consumption_comparison",
    # Intensity
    "co2_per_rpk_comparison",
    "co2_per_rtk_comparison",
    "energy_per_ask_comparison",
    "energy_per_rtk_comparison",
    # Fuel supply
    "drop_in_supply_breakdown",
    "hydrogen_supply_comparison",
    "electric_supply_comparison",
    "biofuel_production_comparison",
    "electrofuel_production_comparison",
]


def test_expected_plots_available(processes):
    """Test that list_available_plots returns all expected plot names."""
    multi = assemble_processes(processes)
    plots = multi.list_available_plots()

    assert plots is not None
    assert isinstance(plots, list)
    assert len(plots) > 0

    for plot_name in EXPECTED_PLOTS:
        assert plot_name in plots, f"Expected plot '{plot_name}' not found in available plots"


def test_plot_co2_emissions_comparison(processes):
    """Test creating CO2 emissions comparison plot."""
    multi = assemble_processes(processes)

    # Create plot - should not raise exception
    fig = multi.plot("co2_emissions_comparison")
    assert fig is not None


def test_plot_energy_consumption_comparison(processes):
    """Test creating energy consumption comparison plot."""
    multi = assemble_processes(processes)

    # Create plot - should not raise exception
    fig = multi.plot("energy_consumption_comparison")
    assert fig is not None


def test_plot_with_invalid_name(processes):
    """Test that invalid plot name raises KeyError."""
    multi = assemble_processes(processes)

    with pytest.raises(KeyError):
        multi.plot("nonexistent_plot")


def test_required_outputs_validation(processes):
    """Test that plots validate required outputs."""
    multi = assemble_processes(processes)

    # This should work fine since processes are computed
    fig = multi.plot("co2_emissions_comparison")
    assert fig is not None


def test_plot_with_check_outputs_false(processes):
    """Test that check_outputs=False skips validation."""
    multi = assemble_processes(processes)

    # Should work even if validation is disabled
    fig = multi.plot("co2_emissions_comparison", check_outputs=False)
    assert fig is not None


def test_multi_scenario_plot_filters_invalid_scenarios(processes):
    """Test that MultiScenarioPlot filters out scenarios with missing outputs."""
    from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot

    # Create a test plot class
    class TestPlot(MultiScenarioPlot):
        def __init__(self, processes):
            super().__init__(processes, check_outputs=True, required_outputs=["total_erf"])

        def _get_default_figsize(self):
            return (10, 6)

        def _update_plot_elements(self):
            pass

        def create_plot(self):
            pass

    # Plot should filter out proc1 and proc2 as they don't have climate outputs
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        plot = TestPlot(processes)

        # Should have warned about missing output
        assert len(w) > 0
        assert "missing required outputs" in str(w[0].message)

    # Only proc3 should be included -> climate model
    assert len(plot.processes) == 1
    assert "scenario_3" in plot.processes.keys()


def test_scenario_groups(processes):
    """Test basic scenario grouping functionality."""
    from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot

    # Define groups
    groups = {"Baseline": ["scenario_1", "scenario_3"], "Low-growth": ["scenario_2"]}

    # Create test plot class
    class TestPlot(MultiScenarioPlot):
        def _get_default_figsize(self):
            return (10, 6)

        def _update_plot_elements(self):
            pass

        def create_plot(self):
            pass

    plot = TestPlot(processes, scenario_groups=groups)

    # Check that styles were set up
    style1 = plot.get_scenario_style("scenario_1")
    style2 = plot.get_scenario_style("scenario_2")
    style3 = plot.get_scenario_style("scenario_3")

    # Same group should have same color
    assert style1["color"] == style3["color"]
    assert style1["group"] == "Baseline"
    assert style3["group"] == "Baseline"

    # Different groups should have different colors
    assert style1["color"] != style2["color"]
    assert style2["group"] == "Low-growth"

    # Same group should have different linestyles
    assert style1["linestyle"] != style3["linestyle"]


def test_scenario_no_groups(processes):
    """Test scenario styling without grouping."""
    from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot

    # Create test plot class without groups
    class TestPlot(MultiScenarioPlot):
        def _get_default_figsize(self):
            return (10, 6)

        def _update_plot_elements(self):
            pass

        def create_plot(self):
            pass

    plot = TestPlot(processes)

    # Without groups, each scenario should get its own color
    style1 = plot.get_scenario_style("scenario_1")
    style2 = plot.get_scenario_style("scenario_2")
    style3 = plot.get_scenario_style("scenario_3")

    # Should have different colors
    assert style1["color"] != style2["color"]
    assert style1["color"] != style3["color"]
    assert style3["color"] != style2["color"]

    # Should not be in groups
    assert style1["group"] is None
    assert style2["group"] is None
    assert style3["group"] is None

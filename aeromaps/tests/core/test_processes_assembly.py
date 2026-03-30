"""
Test module for AeroMAPSProcessesAssembly core functionality.

This module tests the AeroMAPSProcessesAssembly class for managing multiple scenarios.
Plot-related tests are in test_multi_scenario_plots.py.
"""
from pathlib import Path

import pytest
import warnings
from aeromaps import create_process, assemble_processes


def get_tested_config_files():
    """Get paths for configuration files to initialize process."""
    config_path = Path(__file__).parent.parent / "tested_configs" / "config_basic.yaml"
    return [str(config_path)]


CONFIGS_TO_TEST = get_tested_config_files()


@pytest.mark.parametrize("config_file", CONFIGS_TO_TEST)
def test_multi_process_creation_and_operations(config_file):
    """Test AeroMAPSProcessesAssembly creation, indexing, and basic operations."""
    proc1 = create_process(configuration_file=config_file)
    proc1.compute()
    proc2 = create_process(configuration_file=config_file)
    proc2.compute()

    processes_dict = {"scenario_1": proc1, "scenario_2": proc2}
    processes_list = list(processes_dict.values())

    # Test creation with dict
    multi_dict = assemble_processes(processes_dict)
    assert multi_dict is not None
    assert len(multi_dict) == 2

    # Test creation with list
    multi_list = assemble_processes(processes_list)
    assert multi_list is not None
    assert len(multi_list) == 2

    # Test get_scenario_names
    names = multi_dict.get_scenario_names()
    assert isinstance(names, list)
    assert "scenario_1" in names
    assert "scenario_2" in names

    # Test dictionary-style and integer indexing
    assert multi_dict["scenario_1"] == proc1
    assert multi_dict["scenario_2"] == proc2
    assert multi_dict[0] is not None
    assert multi_dict[1] is not None

    # Test list_available_plots
    plots = multi_dict.list_available_plots()
    assert isinstance(plots, list)


@pytest.mark.parametrize("config_file", CONFIGS_TO_TEST)
def test_compute_all(config_file):
    """Test that compute_all() computes all processes."""
    proc1 = create_process(configuration_file=config_file)
    proc2 = create_process(configuration_file=config_file)
    uncomputed = {"scenario_1": proc1, "scenario_2": proc2}

    multi = assemble_processes(uncomputed)
    multi.compute_all()

    for proc in uncomputed.values():
        assert proc.data is not None
        assert "vector_outputs" in proc.data


def test_error_handling():
    """Test error handling for invalid inputs."""
    with pytest.raises(ValueError):
        assemble_processes({})

    with pytest.raises(TypeError):
        assemble_processes("not a dict or list")


@pytest.mark.parametrize("config_file", CONFIGS_TO_TEST)
def test_invalid_plot_name_raises_error(config_file):
    """Test that invalid plot name raises KeyError."""
    proc = create_process(configuration_file=config_file)
    proc.compute()
    multi = assemble_processes({"s1": proc})

    with pytest.raises(KeyError):
        multi.plot("nonexistent_plot_name")


@pytest.mark.parametrize("config_file", CONFIGS_TO_TEST)
def test_plot_classes_required_outputs(config_file):
    """Test required_outputs functionality for SingleScenarioPlot and MultiScenarioPlot."""
    from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
    from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot

    # Verify class attributes exist
    assert hasattr(SingleScenarioPlot, 'required_outputs')
    assert hasattr(SingleScenarioPlot, 'get_required_outputs')
    assert hasattr(MultiScenarioPlot, 'required_outputs')
    assert hasattr(MultiScenarioPlot, 'get_required_outputs')

    # Create test plot subclasses
    class TestSinglePlot(SingleScenarioPlot):
        required_outputs = ["nonexistent_output"]

        def _get_default_figsize(self):
            return (10, 6)

        def create_plot(self):
            pass

        def _update_plot_elements(self):
            pass

    class TestMultiPlot(MultiScenarioPlot):
        required_outputs = ["co2_emissions"]

        def _get_default_figsize(self):
            return (10, 6)

        def create_plot(self):
            pass

        def _update_plot_elements(self):
            pass

    proc1 = create_process(configuration_file=config_file)
    proc1.compute()
    proc2 = create_process(configuration_file=config_file)
    proc2.compute()

    # Test validation warning for missing outputs
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        TestSinglePlot(proc1)
        assert len(w) > 0
        assert "nonexistent_output" in str(w[0].message)

    # Test instance parameter override for single scenario
    single_plot = TestSinglePlot(proc1, required_outputs=["energy_consumption"])
    assert single_plot.get_instance_required_outputs() == ["energy_consumption"]

    # Test instance parameter override for multi scenario
    multi_plot = TestMultiPlot(
        {"s1": proc1, "s2": proc2},
        required_outputs=["energy_consumption"]
    )
    assert multi_plot.get_instance_required_outputs() == ["energy_consumption"]
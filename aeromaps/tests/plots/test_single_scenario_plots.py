"""
Test module for single scenario plots.

This module tests that all single scenario plots can be created without errors
when running a scenario with default configuration.
"""

import warnings

import pytest
from aeromaps import create_process
from aeromaps.plots.single_scenario import available_plots, available_plots_fleet
from aeromaps.plots.single_scenario_plot import SingleScenarioPlot


def _is_simple_fleet(name: str) -> bool:
    return name.endswith("_simple_fleet")


_STANDARD_PLOTS = sorted(
    [n for n in available_plots if not _is_simple_fleet(n)] + list(available_plots_fleet.keys())
)
_SIMPLE_FLEET_PLOTS = sorted(n for n in available_plots if _is_simple_fleet(n))


class TestPlot(SingleScenarioPlot):
    """Minimal concrete subclass used to test SingleScenarioPlot behaviour."""

    def __init__(self, process, check_outputs=True, required_outputs=None):
        super().__init__(
            process,
            check_outputs=check_outputs,
            required_outputs=required_outputs,
        )

    def _get_default_figsize(self):
        return (10, 6)

    def _update_plot_elements(self):
        pass

    def create_plot(self):
        pass


@pytest.fixture(scope="module")
def process():
    """
    Create and run an AeroMAPS process with test configuration.

    This fixture is module-scoped to avoid running the computation multiple times.
    Uses the full test configuration which includes all necessary models.
    """
    # Create process with full test configuration
    import os

    config_path = os.path.join(os.path.dirname(__file__), "../tested_configs/config_advanced.yaml")
    proc = create_process(configuration_file=config_path)

    # Run the scenario
    proc.compute()

    return proc


@pytest.fixture(scope="module")
def process_simple():
    """
    Create and run an AeroMAPS process with test configuration.

    This fixture is module-scoped to avoid running the computation multiple times.
    Uses the full test configuration which includes all necessary models.
    """
    # Create process with full test configuration
    import os

    config_path = os.path.join(
        os.path.dirname(__file__), "../tested_configs/config_advanced_simplified.yaml"
    )
    proc = create_process(configuration_file=config_path)

    # Run the scenario
    proc.compute()

    return proc


def test_no_duplicate_plot_names():
    """Plot names must not be registered in both available_plots and available_plots_fleet."""
    overlap = set(available_plots).intersection(available_plots_fleet)
    assert not overlap, f"Plot name registered in both dicts: {overlap}"


@pytest.mark.parametrize("plot_name", _STANDARD_PLOTS)
def test_standard_plot(process, plot_name):
    """Every plot reachable through the full-config process must build."""
    assert process.plot(plot_name, save=False) is not None


@pytest.mark.parametrize("plot_name", _SIMPLE_FLEET_PLOTS)
def test_simple_fleet_plot(process_simple, plot_name):
    """Simple-fleet variants must build under the simplified config."""
    assert process_simple.plot(plot_name, save=False) is not None


# ---------------------------------------------------------------------------
# TestPlot-based tests for check_outputs / required_outputs behaviour
# ---------------------------------------------------------------------------


def test_required_outputs_warns_on_missing(process):
    """Test that a warning is issued when required outputs are missing."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        plot = TestPlot(
            process,
            check_outputs=True,
            required_outputs=["nonexistent_output"],
        )

        assert len(w) > 0
        assert "missing" in str(w[0].message).lower()

    # The plot should still be created despite the warning
    assert plot is not None


def test_required_outputs_no_warning_when_present(process):
    """Test that no warning is issued when required outputs are present."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        plot = TestPlot(
            process,
            check_outputs=True,
            required_outputs=["rpk"],
        )

        output_warnings = [x for x in w if "missing" in str(x.message).lower()]
        assert len(output_warnings) == 0

    assert plot is not None


def test_check_outputs_false_skips_validation(process):
    """Test that check_outputs=False skips output validation entirely."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        plot = TestPlot(
            process,
            check_outputs=False,
            required_outputs=["nonexistent_output"],
        )

        output_warnings = [x for x in w if "missing" in str(x.message).lower()]
        assert len(output_warnings) == 0

    assert plot is not None


def test_no_required_outputs_no_warning(process):
    """Test that no warning is issued when required_outputs is empty."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        plot = TestPlot(
            process,
            check_outputs=True,
            required_outputs=[],
        )

        output_warnings = [x for x in w if "missing" in str(x.message).lower()]
        assert len(output_warnings) == 0

    assert plot is not None

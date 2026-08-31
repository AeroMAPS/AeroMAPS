"""Rendering tests for the mitigation-wedge plots.

The registry-wide test in ``test_single_scenario_plots`` already builds
``mitigation_wedges`` with no anchors against a default scenario. What is left to
cover is the anchored path, which is the one the ATAG figure uses, and the
multi-scenario comparison, which is not in the registry and so is not reached by
any generic test.
"""

from pathlib import Path

import pytest

from aeromaps.plots.multi_scenario import MitigationWedgeComparison
from aeromaps.utils.results_view import load_results

# parents[2] is the aeromaps package directory: .../aeromaps/tests/plots/<this>
ATAG = Path(__file__).resolve().parents[2] / "notebooks" / "scenarios" / "02_atag_waypoint2050"
FULL = ATAG / "3rd_edition_full" / "data_outputs"

pytestmark = pytest.mark.skipif(
    not (FULL / "t0.json").exists(),
    reason="ATAG third-edition outputs are not present in this checkout",
)


@pytest.fixture(scope="module")
def anchors():
    return load_results(FULL / "t0.json"), load_results(FULL / "t1.json")


def test_anchored_single_scenario_renders(anchors):
    plot = load_results(FULL / "s1.json").plot("mitigation_wedges", anchors=anchors)
    # Five pillars: fleet renewal, next generation in two pieces, operations,
    # fuel, market-based.
    assert len(plot.ax.collections) == 6
    assert plot.ax.get_ylabel().startswith("Annual CO")


def test_frozen_baseline_line_only_drawn_with_anchors(anchors):
    view = load_results(FULL / "s1.json")
    labelled = [
        line.get_label() for line in view.plot("mitigation_wedges", anchors=anchors).ax.lines
    ]
    assert "Frozen-technology baseline" in labelled

    bare = [line.get_label() for line in view.plot("mitigation_wedges").ax.lines]
    assert "Frozen-technology baseline" not in bare


def test_comparison_draws_one_panel_per_scenario(anchors):
    scenarios = {
        "S1": load_results(FULL / "s1.json"),
        "S2": load_results(FULL / "s2.json"),
    }
    comparison = MitigationWedgeComparison(scenarios, anchors=anchors)
    assert [ax.get_title() for ax in comparison.axes] == ["S1", "S2"]
    # Panels share the vertical axis, which is what makes them comparable.
    assert comparison.axes[0].get_ylim() == comparison.axes[1].get_ylim()
    assert comparison.axes[0].get_ylabel().startswith("Annual CO")
    assert comparison.axes[1].get_ylabel() == ""

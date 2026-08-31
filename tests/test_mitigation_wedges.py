"""The mitigation-wedge decomposition, against the committed ATAG outputs.

These pin the arithmetic that Table 2 and the decomposition figure are built on.
The numbers are the third edition's, read from the committed scenario outputs, so
a change in the model that moves them will fail here rather than silently
reappearing in the manuscript.
"""

from pathlib import Path

import numpy as np
import pytest

from aeromaps.utils.decomposition import mitigation_wedges, pillar_totals
from aeromaps.utils.results_view import load_results

ATAG = (
    Path(__file__).resolve().parents[1]
    / "aeromaps"
    / "notebooks"
    / "scenarios"
    / "02_atag_waypoint2050"
)
FULL = ATAG / "3rd_edition_full" / "data_outputs"

# The frozen-fleet baseline every row of Table 2 closes on, in MtCO2 at 2050.
FROZEN_BASELINE_2050 = 2835.0

pytestmark = pytest.mark.skipif(
    not (FULL / "t0.json").exists(),
    reason="ATAG third-edition outputs are not present in this checkout",
)


@pytest.fixture(scope="module")
def anchors():
    return load_results(FULL / "t0.json"), load_results(FULL / "t1.json")


def _pillars_at(view, anchors, year=2050):
    """The wedges at ``year``, plus the gross residual, mirroring make_tables."""
    years, boundaries = mitigation_wedges(view, anchors=anchors)
    index = int(np.where(years == year)[0][0])
    wedges = [boundaries[k][index] - boundaries[k + 1][index] for k in range(len(boundaries) - 2)]
    return wedges, boundaries[-2][index]


@pytest.mark.parametrize(
    "name, expected",
    [
        # fleet renewal, efficiency, alternative aircraft, operations, fuel
        ("s1", (473.8, 282.1, 0.0, 242.6, 1412.9)),
        ("s2", (473.8, 282.1, 218.1, 242.6, 1257.1)),
        ("t4", (473.8, 282.1, 247.0, 0.0, 0.0)),
    ],
)
def test_wedges_match_committed_scenarios(anchors, name, expected):
    wedges, _ = _pillars_at(load_results(FULL / f"{name}.json"), anchors)
    assert np.allclose(wedges, expected, atol=0.05)


@pytest.mark.parametrize("name", ["s1", "s2", "t0", "t1", "t2", "t3", "t4", "o3", "f2"])
def test_decomposition_is_a_partition(anchors, name):
    """Every wedge plus the gross residual closes on the frozen-fleet baseline.

    This is what makes the table a partition rather than an attribution, and it
    holds for the lever runs as well as the published scenarios.
    """
    wedges, gross = _pillars_at(load_results(FULL / f"{name}.json"), anchors)
    assert sum(wedges) + gross == pytest.approx(FROZEN_BASELINE_2050, abs=0.05)


def test_frozen_scenario_reports_no_technology(anchors):
    """T0 is the baseline, so it must claim nothing and close on the baseline.

    Without the clamp in ``mitigation_wedges`` the renewal anchor sits below both
    neighbours here and the split comes out as +473.8 renewal against -473.8 next
    generation: a correct total over a meaningless split.
    """
    wedges, gross = _pillars_at(load_results(FULL / "t0.json"), anchors)
    assert all(wedge >= 0.0 for wedge in wedges)
    assert np.allclose(wedges, 0.0, atol=1e-6)
    assert gross == pytest.approx(FROZEN_BASELINE_2050, abs=0.05)


@pytest.mark.parametrize(
    "name, expected",
    [
        # fleet renewal, next generation (efficiency + alternative aircraft),
        # operations, fuel
        ("s1", (473.8, 282.1, 242.6, 1412.9)),
        ("s2", (473.8, 500.2, 242.6, 1257.1)),
        ("t4", (473.8, 529.1, 0.0, 0.0)),
    ],
)
def test_pillar_totals_merge_the_technology_pieces(anchors, name, expected):
    """Table 2's rows: the figure draws next generation in two bands, the table
    reports one pillar, so the efficiency and alternative-aircraft pieces add."""
    pillars, _ = pillar_totals(load_results(FULL / f"{name}.json"), anchors=anchors)
    assert np.allclose(pillars, expected, atol=0.05)


def test_pillar_totals_close_on_the_baseline(anchors):
    pillars, gross = pillar_totals(load_results(FULL / "s1.json"), anchors=anchors)
    assert sum(pillars) + gross == pytest.approx(FROZEN_BASELINE_2050, abs=0.05)


def test_anchor_count_sets_the_number_of_wedges(anchors):
    """Dropping anchors collapses the technology pillar instead of failing."""
    view = load_results(FULL / "s1.json")
    counts = [len(mitigation_wedges(view, anchors=a)[1]) for a in ((), anchors[:1], anchors)]
    assert counts == [5, 6, 7]


def test_reduced_anchors_leave_the_lower_pillars_untouched(anchors):
    """Operations and fuel do not depend on how technology is split above them."""
    view = load_results(FULL / "s2.json")
    _, full = mitigation_wedges(view, anchors=anchors)
    _, none = mitigation_wedges(view, anchors=())
    # The last four boundaries are shared: scenario technology downwards.
    for a, b in zip(full[-4:], none[-4:]):
        assert np.allclose(np.asarray(a), np.asarray(b), equal_nan=True)

"""The offset glide, the grid runner and the traffic-variant solver."""

import numpy as np
import pandas as pd
import pytest

from aeromaps.utils.offsets import residual_share_for_net_target
from aeromaps.utils.sweep import grid, run_grid, summarise, tidy_to_wide
from aeromaps.utils.traffic_variants import scale_growth_after, solve_scale_for_target


# --------------------------------------------------------------------------- offsets

FIRST = 2000
FLAT_GROSS = [1000.0] * 51


def test_glide_reaches_exactly_zero_net_at_the_target():
    years, shares, net = residual_share_for_net_target(
        FLAT_GROSS, [0.0] * 51, handover_year=2035, net_zero_year=2050
    )
    assert years[0] == 2036 and years[-1] == 2050
    assert net == pytest.approx(1000.0)
    assert shares[-1] == pytest.approx(100.0)


def test_glide_is_continuous_at_the_handover_and_monotone():
    """The first year after the handover must barely move, not jump."""
    years, shares, net = residual_share_for_net_target(
        FLAT_GROSS, [0.0] * 51, handover_year=2035, net_zero_year=2050
    )
    span = 2050 - 2035
    # One year in, net has fallen by exactly one fifteenth of its handover value.
    assert shares[0] == pytest.approx(100.0 / span, abs=1e-3)
    assert all(b >= a for a, b in zip(shares, shares[1:]))


def test_existing_offsets_set_the_handover_level():
    """Net at the handover is gross minus what is already offset there."""
    offset = [0.0] * 51
    offset[2035 - FIRST] = 400.0
    _, _, net = residual_share_for_net_target(
        FLAT_GROSS, offset, handover_year=2035, net_zero_year=2050
    )
    assert net == pytest.approx(600.0)


def test_missing_offsets_read_as_zero():
    offset = [float("nan")] * 51
    _, _, net = residual_share_for_net_target(
        FLAT_GROSS, offset, handover_year=2035, net_zero_year=2050
    )
    assert net == pytest.approx(1000.0)


def test_the_schedule_is_scenario_specific():
    """Two scenarios reaching the same target need different shares.

    Copying one schedule onto another is the mistake this function exists to
    prevent: the share is a fraction of that scenario's own gross trajectory.
    """
    rising = [1000.0 + 20.0 * (year - FIRST) for year in range(FIRST, 2051)]
    _, flat_shares, _ = residual_share_for_net_target(
        FLAT_GROSS, [0.0] * 51, handover_year=2035, net_zero_year=2050
    )
    _, rising_shares, _ = residual_share_for_net_target(
        rising, [0.0] * 51, handover_year=2035, net_zero_year=2050
    )
    assert flat_shares[0] != pytest.approx(rising_shares[0])
    # Both still land on full offsetting at the target year.
    assert flat_shares[-1] == pytest.approx(100.0)
    assert rising_shares[-1] == pytest.approx(100.0)


def test_target_year_must_follow_the_handover():
    with pytest.raises(ValueError, match="must follow"):
        residual_share_for_net_target(FLAT_GROSS, [0.0] * 51, 2050, 2035)


# --------------------------------------------------------------------------- sweep


def test_grid_is_the_product_in_declaration_order():
    cells = grid({"a": ("x", "y"), "b": (1, 2, 3)})
    assert len(cells) == 6
    assert cells[0] == ("x", 1) and cells[-1] == ("y", 3)


def test_run_grid_reduces_each_cell_and_concatenates():
    seen = []

    class FakeProcess:
        def compute(self):
            pass

    def build(cell):
        seen.append(cell)
        return FakeProcess()

    def extract(process, cell):
        return pd.DataFrame({"a": [cell[0]], "year": [2050], "variable": ["v"], "value": [1.0]})

    cells = grid({"a": ("x", "y")})
    tidy = run_grid(cells, build, extract, progress=False)
    assert seen == cells
    assert len(tidy) == 2


def test_tidy_to_wide_pivots_and_derives():
    tidy = pd.DataFrame(
        {
            "a": ["x", "x"],
            "year": [2050, 2050],
            "variable": ["num", "den"],
            "value": [10.0, 2.0],
        }
    )
    wide = tidy_to_wide(tidy, ["a"], {"ratio": lambda f: f["num"] / f["den"]})
    assert wide.loc[0, "ratio"] == pytest.approx(5.0)


def test_summarise_takes_one_year():
    tidy = pd.DataFrame(
        {
            "a": ["x", "x"],
            "year": [2040, 2050],
            "variable": ["v", "v"],
            "value": [1.0, 2.0],
        }
    )
    assert summarise(tidy, ["a"], 2050).loc[0, "v"] == pytest.approx(2.0)


# --------------------------------------------------------------------------- variants


def _markets():
    return {
        "short_range": {
            "inputs": {
                "growth": {
                    "cagr_reference_periods": [2023, 2024, 2030],
                    "cagr_reference_periods_values": [10.0, 4.0, 2.0],
                }
            }
        },
        "defaults": {
            "passenger": {
                "inputs": {
                    "reference": {
                        "reference_cagr_reference_periods": [2023, 2030],
                        "reference_cagr_reference_periods_values": [10.0, 2.0],
                    }
                }
            }
        },
    }


def test_only_growth_after_the_pivot_is_scaled():
    """The observed period is data, not a projection, and must not be rescaled."""
    scaled = scale_growth_after(_markets(), 0.5, 2024, markets=("short_range",))
    values = scaled["short_range"]["inputs"]["growth"]["cagr_reference_periods_values"]
    assert values == [10.0, 4.0, 1.0]


def test_the_reference_curve_is_scaled_too():
    """Leaving it alone would describe a different scenario from the one run."""
    scaled = scale_growth_after(_markets(), 0.5, 2024, markets=("short_range",))
    reference = scaled["defaults"]["passenger"]["inputs"]["reference"]
    assert reference["reference_cagr_reference_periods_values"] == [10.0, 1.0]


def test_scaling_does_not_mutate_the_source():
    document = _markets()
    scale_growth_after(document, 0.5, 2024, markets=("short_range",))
    assert document["short_range"]["inputs"]["growth"]["cagr_reference_periods_values"][-1] == 2.0


def test_solver_finds_a_known_root():
    # A monotone response with the root at alpha = 3.
    assert solve_scale_for_target(lambda a: 2.0 * a, 6.0, (1.0, 5.0)) == pytest.approx(3.0)


def test_solver_stops_on_a_flat_response():
    """A flat secant cannot propose a next point; it must stop, not divide by zero."""
    calls = []

    def evaluate(alpha):
        calls.append(alpha)
        return 1.0

    solve_scale_for_target(evaluate, 999.0, (1.0, 2.0), max_iter=5)
    assert len(calls) == 2


def test_solver_handles_a_zero_target():
    """A zero target has no relative scale, so the tolerance must read as absolute.

    Dividing by the target instead raises, the same failure the flat-response case
    above guards against. The root of ``a - 3`` at a target of zero is a = 3.
    """
    assert solve_scale_for_target(lambda a: a - 3.0, 0.0, (1.0, 5.0)) == pytest.approx(3.0)


def test_solver_respects_the_iteration_cap():
    calls = []

    def evaluate(alpha):
        calls.append(alpha)
        return float(np.sin(alpha)) * 1e-9  # never reaches a target of 1

    solve_scale_for_target(evaluate, 1.0, (0.1, 0.2), max_iter=4)
    assert len(calls) <= 2 + 4

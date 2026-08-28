"""Missing values belong beside the coupling vector, not inside it.

AeroMAPS series are legitimately undefined over the historical years, and a coupling
belonging to a pathway a scenario does not use is undefined throughout. GEMSEO has no
notion of a missing value, so those NaNs used to travel *inside* the vector as
``-999999``. That works, but it puts a flag in the numeric channel: the solver is
entitled to blend, scale, project and normalise that vector, and every one of those
operations can destroy the flag with nothing noticing.

The projection performed by ``set_bounds`` is the worst case, and the first test below
is the whole argument in one place: the same bound, on the same scenario, breaks a
converging solve while the sentinel is in charge and is harmless once the mask is.

Everything else here pins the properties the mask has to have to be safe:

* it changes representation, not arithmetic -- results bit-identical to the sentinel;
* it is established after the solver's first complete sweep, which is the earliest
  moment every coupling has been written by its real producer;
* it is scoped to one solve, so a second ``compute()`` re-derives it and nothing leaks
  between the regional solves that ``separate_processes`` runs in parallel;
* a NaN at a position it says carries a value is reported, not absorbed.
"""

import threading

import numpy as np
import pandas as pd
import pytest
from gemseo.mda.mda_chain import MDAChain

from aeromaps.core import process as process_module
from aeromaps.core.gemseo import (
    AeroMAPSCustomModelWrapper,
    CustomDataConverter,
    _ACTIVE_MASKS,
    check_mda_convergence,
    freeze_nan_masks_after_first_sweep,
    nan_intrusions,
    nan_mask,
    record_nan_intrusion,
)
from aeromaps.models.base import AeroMAPSModel

YEARS = range(2000, 2051)
HISTORICAL = 20  # index of the first projected year, 2020


class _Parameters:
    climate_historic_start_year = 1940
    historic_start_year = 2000
    prospection_start_year = 2020
    end_year = 2050


def _series(value):
    return pd.Series(float(value), index=YEARS)


def _partly_defined(value=1.0):
    """A series shaped like a real AeroMAPS coupling: NaN before the projection."""
    series = _series(value)
    series.iloc[:HISTORICAL] = np.nan
    return series


class _Source(AeroMAPSModel):
    """Writes ``x`` from ``y``; both are undefined over the historical years."""

    def __init__(self, name="source", **kwargs):
        super().__init__(name=name, model_type="custom", **kwargs)
        self.input_names = {"y": pd.Series([0.0])}
        self.output_names = {"x": pd.Series([0.0])}

    def compute(self, input_data):
        return {"x": _partly_defined(1.0) + 0.4 * input_data["y"].fillna(0.0)}


class _Sink(AeroMAPSModel):
    def __init__(self, name="sink", **kwargs):
        super().__init__(name=name, model_type="custom", **kwargs)
        self.input_names = {"x": pd.Series([0.0])}
        self.output_names = {"y": pd.Series([0.0])}

    def compute(self, input_data):
        return {"y": _partly_defined(1.0) + 0.4 * input_data["x"].fillna(0.0)}


def _chain(masked=True):
    disciplines = [
        AeroMAPSCustomModelWrapper(_Source(parameters=_Parameters())),
        AeroMAPSCustomModelWrapper(_Sink(parameters=_Parameters())),
    ]
    for discipline in disciplines:
        for name in ("x", "y"):
            if name in discipline.io.input_grammar.names:
                discipline.default_input_data.setdefault(name, _partly_defined(1.0))
    chain = MDAChain(
        disciplines=disciplines,
        inner_mda_name="MDAGaussSeidel",
        tolerance=1e-12,
        max_mda_iter=60,
    )
    if masked:
        freeze_nan_masks_after_first_sweep(chain)
    return chain


def _solve(masked=True, bounds=None):
    chain = _chain(masked=masked)
    if bounds is not None:
        low, high = bounds
        chain.set_bounds({"x": (np.array([low]), np.array([high]))})
    chain.execute()
    mda = chain.inner_mdas[0]
    return chain, mda, list(mda.residual_history)


# --------------------------------------------------------------------------------
# The defect: a bound plus the sentinel
# --------------------------------------------------------------------------------


def test_bounds_and_the_sentinel_break_a_solve_that_converged_without_them():
    """The defect, reproduced.

    Bounds are enforced by projecting the *whole* iterate. The projection cannot tell a
    sentinel from a value, so ``-999999`` is clipped up to the lower bound, stops
    matching ``== -999999``, and is handed back to the disciplines as a real number.
    A correctness measure destroys correctness, silently.
    """
    _chain_, _mda, unbounded = _solve(masked=False)
    assert unbounded[-1] <= 1e-12, "the unbounded sentinel solve should converge"

    _chain_, _mda, bounded = _solve(masked=False, bounds=(0.0, 1e6))

    assert bounded[-1] > 1e-12, (
        "expected the bound to break the sentinel solve; this no longer reproduces"
    )


def test_the_mask_makes_the_same_bound_harmless():
    """The fix, with only the mask changed."""
    _chain_, _mda, unbounded = _solve(masked=True)
    _chain_, _mda, bounded = _solve(masked=True, bounds=(0.0, 1e6))

    assert unbounded[-1] <= 1e-12
    assert bounded[-1] <= 1e-12
    assert len(bounded) == len(unbounded)


# --------------------------------------------------------------------------------
# Representation, not arithmetic
# --------------------------------------------------------------------------------


def test_masked_and_sentinel_solves_agree_bit_for_bit():
    _chain_, sentinel_mda, sentinel = _solve(masked=False)
    _chain_, masked_mda, masked = _solve(masked=True)

    assert sentinel == masked
    for name in ("x", "y"):
        left = sentinel_mda.io.data[name].to_numpy(dtype=float)
        right = masked_mda.io.data[name].to_numpy(dtype=float)
        assert np.array_equal(left, right, equal_nan=True)


def _peak_magnitude_during_solve(masked):
    """The largest component the solver ever holds in its iterate.

    Sampled *inside* the solve, via GEMSEO's iteration callback: outside it no mask is
    in force by design, so the conversion falls back to the sentinel and the question
    cannot be asked from there.
    """
    chain = _chain(masked=masked)
    peak = []

    def observe(mda):
        peak.append(float(np.abs(mda.get_current_resolved_variables_vector()).max()))

    chain.inner_mdas[0].add_iteration_callback(observe)
    chain.execute()
    return max(peak)


def test_the_masked_vector_carries_no_sentinel_magnitude_value():
    """The point of the exercise: nothing of order 1e6 in a vector the solver blends."""
    assert _peak_magnitude_during_solve(masked=False) >= 999999.0
    assert _peak_magnitude_during_solve(masked=True) < 1e3


def test_the_undefined_positions_still_come_back_as_nan():
    """A mask that lost the NaNs would be worse than the sentinel, not better."""
    _chain_, masked_mda, _history = _solve(masked=True)
    for name in ("x", "y"):
        value = masked_mda.io.data[name]
        assert int(value.isna().sum()) == HISTORICAL
        assert value.iloc[:HISTORICAL].isna().all()
        assert value.iloc[HISTORICAL:].notna().all()


# --------------------------------------------------------------------------------
# Scope: one solve, one mask
# --------------------------------------------------------------------------------


def test_no_mask_is_in_force_outside_a_solve():
    """Otherwise a stale mask would rewrite values nobody is solving for."""
    _solve(masked=True)
    assert _ACTIVE_MASKS.get() is None
    assert nan_mask("x", (len(YEARS),)) is None


def test_a_second_execute_re_derives_the_mask():
    """Frozen within a solve, not across solves: the next one may be a different scenario."""
    chain = _chain(masked=True)
    chain.execute()
    first = list(chain.inner_mdas[0].residual_history)

    chain.execute()
    second = list(chain.inner_mdas[0].residual_history)

    assert second, "the second execute produced no residual history"
    assert nan_intrusions(chain.inner_mdas[0]) == {}
    assert first  # both solves ran


def test_installing_the_hooks_twice_is_a_no_op():
    chain = _chain(masked=True)
    freeze_nan_masks_after_first_sweep(chain)
    chain.execute()
    assert chain.inner_mdas[0].residual_history[-1] <= 1e-12


def test_masks_do_not_leak_between_threads():
    """``separate_processes(parallel=True)`` solves regions in a ThreadPoolExecutor.

    A module-global mask store would let one region's mask rewrite another's couplings.
    A ContextVar cannot: each thread starts with its own empty context.
    """
    seen = {}

    def worker(key):
        seen[key] = _ACTIVE_MASKS.get()

    _ACTIVE_MASKS.set({"x": np.ones(3, dtype=bool)})
    thread = threading.Thread(target=worker, args=("child",))
    thread.start()
    thread.join()

    assert seen["child"] is None, "the child thread inherited a mask"
    assert _ACTIVE_MASKS.get() is not None


# --------------------------------------------------------------------------------
# A NaN where the mask says there is a value
# --------------------------------------------------------------------------------


def test_an_intrusion_is_recorded_and_reported_as_converging_on_nan():
    """The exact form of the "converged on NaN" condition, now without inference.

    The old check had to guess from the shape of the NaNs -- "a NaN sitting after a real
    value". The mask knows which positions held a value after the first sweep, so a NaN
    anywhere else is a coupling that died during the solve, full stop.
    """
    chain, mda, _history = _solve(masked=True)

    # Simulate what a discipline going NaN mid-solve would have recorded.
    mda._aeromaps_nan_intrusions = {"x": 7, "y": 2}

    failures = check_mda_convergence(chain, on_failure="ignore")
    assert len(failures) == 1
    assert "converged on NaN" in failures[0]
    assert "x (7)" in failures[0]

    with pytest.raises(Exception, match="converged on NaN"):
        check_mda_convergence(chain)


def test_a_clean_solve_records_no_intrusion():
    chain, mda, _history = _solve(masked=True)
    assert nan_intrusions(mda) == {}
    assert check_mda_convergence(chain) == []


def test_record_nan_intrusion_outside_a_solve_is_harmless():
    """It must never raise from inside a data converter."""
    record_nan_intrusion("x", 3)  # no active solve; simply dropped


# --------------------------------------------------------------------------------
# The converter itself
# --------------------------------------------------------------------------------


def test_the_converter_falls_back_to_the_sentinel_without_a_mask():
    converter = CustomDataConverter(None)
    values = converter.convert_value_to_array("solo", _partly_defined(2.0))
    assert values[0] == CustomDataConverter.NAN_SENTINEL
    assert values[-1] == pytest.approx(2.0)

    back = converter.convert_array_to_value("solo", values)
    assert int(back.isna().sum()) == HISTORICAL


def test_a_length_change_falls_back_rather_than_re_masking():
    """A coupling whose length changed is a different bug and must not be papered over."""
    mask = np.ones(len(YEARS), dtype=bool)
    token = _ACTIVE_MASKS.set({"solo": mask})
    try:
        assert nan_mask("solo", (len(YEARS),)) is mask
        assert nan_mask("solo", (len(YEARS) + 3,)) is None
        assert nan_mask("unknown", (len(YEARS),)) is None
    finally:
        _ACTIVE_MASKS.reset(token)


def test_the_process_installs_the_hook():
    """The wiring, so the whole thing cannot be silently disconnected."""
    assert hasattr(process_module, "freeze_nan_masks_after_first_sweep")

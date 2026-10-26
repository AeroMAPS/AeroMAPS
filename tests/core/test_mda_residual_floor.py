"""A discipline that mutates its MDA input pins the residual, and nothing says so.

``aeromaps/tests/core/test_mda_input_mutation.py`` asserts the *invariant* -- that no
discipline in a real chain modifies a value it was handed. It cannot show what the
violation costs, because by then there is no violation left to observe.

This module shows it, on a two-discipline chain small enough to reason about. Each test
runs the same chain twice: once with the defect (``fillna(0, inplace=True)`` on a coupling
input, exactly what ``CO2Emissions`` used to do) and once without. The mechanism:

* GEMSEO snapshots the previous iterate with ``self.io.data.copy()`` -- a **shallow** copy,
  so the ``pd.Series`` it holds are the very objects passed to ``compute()``.
* AeroMAPS converts NaN to the ``-999999`` sentinel on the way into the coupling vector.
* So for an all-NaN coupling the *output* side of the residual is ``-999999`` while the
  *input* side has already been rewritten to ``0``: a constant difference of 999999 per
  element, at every iteration, for ever.

The failure is silent in both directions -- a discipline mutating an input *towards* its
output would drive a residual artificially to zero -- which is why the invariant, and not
just the symptom, is what the other module pins.
"""

import numpy as np
import pandas as pd
import pytest
from gemseo.mda.mda_chain import MDAChain

from aeromaps.core.gemseo import AeroMAPSCustomModelWrapper, check_mda_convergence
from aeromaps.models.base import AeroMAPSModel

YEARS = range(2000, 2051)
TOLERANCE = 1e-10
MAX_ITER = 60


class _Parameters:
    """Minimal stand-in for the process parameters object a model needs to build ``df``."""

    climate_historic_start_year = 1940
    historic_start_year = 2000
    prospection_start_year = 2020
    end_year = 2050


def _series(value):
    return pd.Series(float(value), index=YEARS)


class _Source(AeroMAPSModel):
    """Writes ``x`` from ``y``, and an all-NaN ``factor`` -- an unused pathway.

    The NaN series is the point. It is a legitimate output: AeroMAPS emits one for every
    pathway a scenario does not use, and the sentinel exists so that it costs nothing.

    ``factor_out`` is declared as an input and never read. It exists only to close the
    cycle: without it ``factor`` is feed-forward, GEMSEO leaves it out of the strongly
    coupled set, and it never reaches a residual at all -- which is not the situation
    ``CO2Emissions`` was in.
    """

    def __init__(self, name="source", **kwargs):
        super().__init__(name=name, model_type="custom", **kwargs)
        self.input_names = {"y": pd.Series([0.0]), "factor_out": pd.Series([0.0])}
        self.output_names = {"x": pd.Series([0.0]), "factor": pd.Series([0.0])}

    def compute(self, input_data):
        return {
            "x": 1.0 + 0.4 * input_data["y"],
            "factor": pd.Series(np.nan, index=YEARS),
        }


class _Sink(AeroMAPSModel):
    """Writes ``y`` from ``x``, and passes ``factor`` on as ``factor_out``.

    ``mutate=True`` reinstates the defect: the NaNs of the incoming ``factor`` are filled
    in place, which rewrites the solver's snapshot of the previous iterate.
    """

    def __init__(self, name="sink", mutate=False, **kwargs):
        super().__init__(name=name, model_type="custom", **kwargs)
        self.mutate = mutate
        self.input_names = {"x": pd.Series([0.0]), "factor": pd.Series([0.0])}
        self.output_names = {"y": pd.Series([0.0]), "factor_out": pd.Series([0.0])}

    def compute(self, input_data):
        factor = input_data["factor"]
        if self.mutate:
            # The pre-#157 body of CO2Emissions. The comment there said "locally fill";
            # in place is not local -- this is the same object the solver kept.
            factor.fillna(0, inplace=True)
        else:
            factor = factor.fillna(0)
        return {"y": 1.0 + 0.4 * input_data["x"], "factor_out": factor}


def _chain(mutate, sink_first=True):
    """The two disciplines, in a given Gauss-Seidel sweep order.

    The order matters, and that is why this defect could sit unnoticed. See
    ``test_the_floor_only_appears_when_the_mutator_runs_first``.
    """
    source = AeroMAPSCustomModelWrapper(_Source(parameters=_Parameters()))
    sink = AeroMAPSCustomModelWrapper(_Sink(mutate=mutate, parameters=_Parameters()))
    disciplines = [sink, source] if sink_first else [source, sink]
    seeds = {
        "x": _series(1.0),
        "y": _series(1.0),
        "factor": pd.Series(np.nan, index=YEARS),
        "factor_out": pd.Series(np.nan, index=YEARS),
    }
    for discipline in disciplines:
        for name, value in seeds.items():
            if name in discipline.io.input_grammar.names:
                discipline.default_input_data.setdefault(name, value)
    return MDAChain(
        disciplines=disciplines,
        inner_mda_name="MDAGaussSeidel",
        tolerance=TOLERANCE,
        max_mda_iter=MAX_ITER,
    )


def _solve(mutate, sink_first=True):
    chain = _chain(mutate, sink_first=sink_first)
    chain.execute()
    mda = chain.inner_mdas[0]
    return chain, mda, list(mda.residual_history)


def _residual(mda, name):
    return np.asarray(mda._BaseMDASolver__current_residuals[name], dtype=float)


def test_a_mutating_discipline_pins_the_residual():
    """The defect, reproduced: the residual stops falling and the solve never converges."""
    _chain_, mda, history = _solve(mutate=True)

    assert history[-1] > TOLERANCE, (
        "the mutating chain converged, so this test is no longer reproducing anything"
    )
    # And it is stuck, not merely slow: the last ten iterations go nowhere.
    tail = history[-10:]
    assert tail[-1] >= tail[0] * 0.99, f"residual still moving: {tail[0]:.3e} -> {tail[-1]:.3e}"


def test_the_same_chain_converges_when_nothing_is_mutated():
    """The fix, on the identical chain: only ``fillna``'s ``inplace`` differs."""
    _chain_, mda, history = _solve(mutate=False)

    assert history[-1] <= TOLERANCE, f"final residual {history[-1]:.3e}"
    assert len(history) < MAX_ITER


def test_the_floor_is_the_sentinel_differencing_against_a_filled_zero():
    """Not any residual: the pinned value is 999999 per element, and nothing else.

    This is what identifies the cause. The coupling has one element per year; the
    mutating side has rewritten every NaN to 0 while the producing side still emits NaN,
    which converts to ``-999999``.
    """
    _chain_, mda, _history = _solve(mutate=True)

    factor_residual = _residual(mda, "factor")

    assert factor_residual.shape == (len(YEARS),)
    assert np.allclose(np.abs(factor_residual), 999999.0), (
        f"expected the sentinel difference, got {factor_residual[:3]}"
    )
    # The couplings that are genuinely being solved are meanwhile fine, which is exactly
    # why this is hard to spot: the chain looks like it is converging on everything else.
    assert np.abs(_residual(mda, "x")).max() < 1e-3


def test_the_floor_only_appears_when_the_mutator_runs_first():
    """Why a defect this severe could sit unnoticed: it depends on the sweep order.

    The residual differences the *snapshot* against the *current* value. If the producing
    discipline runs first, it overwrites the coupling with a fresh NaN series and the
    mutator then rewrites both sides to 0 -- the two agree, the residual is 0, and
    nothing is visibly wrong. Only when the mutator runs first does the snapshot end up
    at 0 while the producer's fresh NaN goes to ``-999999`` on the other side.

    Same defect, same disciplines, opposite outcome. A reordering of the chain -- a model
    added, a coupling changed -- is enough to hide it again.
    """
    _chain_, mutator_first, _history = _solve(mutate=True, sink_first=True)
    _chain_, producer_first, _history = _solve(mutate=True, sink_first=False)

    assert np.allclose(np.abs(_residual(mutator_first, "factor")), 999999.0)
    assert np.allclose(_residual(producer_first, "factor"), 0.0)
    assert mutator_first.residual_history[-1] > TOLERANCE
    assert producer_first.residual_history[-1] <= TOLERANCE


def test_the_pinned_chain_is_reported_rather_than_returned():
    """The other half of the fix: this no longer looks like a solution.

    Before #157 the run above returned a full set of ordinary-looking outputs and the
    only signal was a GEMSEO WARNING among thousands of log lines.
    """
    chain, _mda, _history = _solve(mutate=True)

    failures = check_mda_convergence(chain, on_failure="ignore")
    assert len(failures) == 1
    assert "did not converge" in failures[0]
    # The message must name what is holding the residual up, or it is not actionable.
    assert "factor" in failures[0]

    with pytest.raises(Exception, match="did not converge"):
        check_mda_convergence(chain)


def test_the_converged_chain_stays_silent():
    chain, _mda, _history = _solve(mutate=False)
    assert check_mda_convergence(chain) == []


def test_the_mutation_is_visible_on_the_input_object_itself():
    """The direct evidence: the object handed in comes back changed.

    Independent of any solver behaviour -- this is the invariant
    ``test_mda_input_mutation.py`` asserts across every discipline of a real chain.
    """
    handed_in = pd.Series(np.nan, index=YEARS)
    sink = _Sink(mutate=True, parameters=_Parameters())
    sink.compute({"x": _series(1.0), "factor": handed_in})
    assert int(handed_in.isna().sum()) == 0, "expected the defect to rewrite the input"

    handed_in = pd.Series(np.nan, index=YEARS)
    sink = _Sink(mutate=False, parameters=_Parameters())
    sink.compute({"x": _series(1.0), "factor": handed_in})
    assert int(handed_in.isna().sum()) == len(YEARS), "the input must come back untouched"

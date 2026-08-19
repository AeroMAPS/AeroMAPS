"""Guard against disciplines mutating their MDA inputs in place.

GEMSEO snapshots the previous MDA iterate with ``self.io.data.copy()``, which is a
*shallow* copy: the pandas Series it holds are the very objects handed to each
discipline's ``compute()`` as ``input_data``. A discipline that mutates one of them in
place therefore rewrites the snapshot the solver is about to difference against, and
the residual of that coupling variable becomes meaningless.

The failure is silent and can go either way. Two real cases were found this way:

- ``CO2Emissions`` did ``co2_emission_factor.fillna(0, inplace=True)`` on a coupling
  input. For an all-NaN emission factor the output side of the residual converted to
  the ``-999999`` NaN sentinel while the input side had been rewritten to ``0``, so the
  residual held a constant ``999999`` per element and pinned the normalized residual at
  ~1.6e-6 -- above any usable tolerance, forever.
- ``BottomUpCapacity`` extended a coupling input with "virtual years" and re-sorted it
  in place, changing its *length*.

In the other direction, mutating an input to match the output would drive a residual
artificially to zero and report convergence that never happened.

This test asserts the invariant directly: after ``compute()``, every value a discipline
received must be unchanged in value, dtype, length and index.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from aeromaps import create_process
from aeromaps.core.gemseo import AeroMAPSAutoModelWrapper, AeroMAPSCustomModelWrapper

CONFIG_DIR = Path(__file__).parent.parent / "tested_configs"

# Configs whose chains contain coupling loops, so disciplines really are re-executed
# against a snapshotted iterate.
COUPLED_CONFIGS = [
    CONFIG_DIR / "config_basic.yaml",
    CONFIG_DIR / "config_elasticity_demand.yaml",
]


def _snapshot(input_data):
    """Copy every mutable value so later comparison is against a true 'before'."""
    snapshot = {}
    for name, value in input_data.items():
        if isinstance(value, pd.Series):
            snapshot[name] = (value.to_numpy(copy=True), value.index.to_numpy(copy=True))
        elif isinstance(value, np.ndarray):
            snapshot[name] = (value.copy(), None)
    return snapshot


def _find_mutations(discipline_name, snapshot, input_data):
    """Return a list of human-readable descriptions of any in-place change."""
    problems = []
    for name, (before_values, before_index) in snapshot.items():
        value = input_data[name]
        after_values = value.to_numpy() if isinstance(value, pd.Series) else np.asarray(value)

        if before_values.shape != after_values.shape:
            problems.append(
                f"{discipline_name}: input '{name}' changed length "
                f"{before_values.shape} -> {after_values.shape}"
            )
            continue

        if not np.array_equal(before_values, after_values, equal_nan=True):
            n = int((~_equal_elementwise(before_values, after_values)).sum())
            problems.append(
                f"{discipline_name}: input '{name}' had {n} element(s) rewritten in place"
            )

        if before_index is not None and isinstance(value, pd.Series):
            after_index = value.index.to_numpy()
            if before_index.shape == after_index.shape and not np.array_equal(
                before_index, after_index
            ):
                problems.append(f"{discipline_name}: index of input '{name}' was reordered")
    return problems


def _equal_elementwise(a, b):
    """Element-wise equality treating NaN as equal to NaN."""
    with np.errstate(invalid="ignore"):
        return (a == b) | (np.isnan(a) & np.isnan(b))


@pytest.fixture
def mutation_recorder(monkeypatch):
    """Patch both AeroMAPS discipline wrappers to record any input mutation."""
    problems = []

    for wrapper in (AeroMAPSCustomModelWrapper, AeroMAPSAutoModelWrapper):
        original_run = wrapper._run

        def make_run(original, wrapper_cls):
            def _run(self, input_data):
                snapshot = _snapshot(input_data)
                result = original(self, input_data)
                problems.extend(_find_mutations(self.name, snapshot, input_data))
                return result

            return _run

        monkeypatch.setattr(wrapper, "_run", make_run(original_run, wrapper))

    return problems


@pytest.mark.parametrize("config_file", COUPLED_CONFIGS, ids=lambda p: p.stem)
def test_disciplines_do_not_mutate_their_inputs(config_file, mutation_recorder):
    """No discipline may modify a value it was handed, in any AeroMAPS chain."""
    process = create_process(configuration_file=config_file)
    process.compute()

    assert not mutation_recorder, (
        "Disciplines mutated their MDA inputs in place, which corrupts the solver's "
        "previous-iterate snapshot and silently invalidates the residual:\n  "
        + "\n  ".join(sorted(set(mutation_recorder)))
    )

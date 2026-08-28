"""``MultiRegionalProcess`` had no automated coverage at all.

Nothing under ``aeromaps/tests/`` exercised it, which is how a solver setting could be
documented as changed while the code kept the old value (see
``test_the_unified_chain_is_held_to_the_same_settings_as_a_single_region``), and how
every output column could be duplicated on a second ``compute()`` without a single test
noticing.

Three things are pinned here, each with the defect reproduced next to the fix:

* the unified chain solves to the same tolerance and iteration budget as a single-region
  process, rather than to a looser standard because it was assembled per region;
* a repeated ``compute()`` refreshes the output columns instead of appending a second
  copy of every one of them;
* the two execution modes agree, which is the property the whole two-mode design rests on.

The scenario is the shipped two-region Europe tutorial, copied into a temporary directory
so the tests cannot write to the repository -- ``create_partitioning`` rewrites its input
JSON in place.
"""

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from aeromaps import create_multi_regional_process
from aeromaps.core.multi_regional_process import _concat_series

TUTORIAL = (
    Path(__file__).parents[1].parent / "notebooks" / "tutorials" / "11_multi_regional_two_regions"
)
CONFIGS = {
    "separate_processes": "regionalisation_europe_separate_processes.yaml",
    "unified_mda": "regionalisation_europe_unified_mda.yaml",
}

# What AeroMAPSProcess asks for, and the reason it does: at 1e-5 the Gauss-Seidel solver
# reports convergence while the doc_net_energy_per_rpk_mean <-> rpk loop is still ~25%
# off in SAF-type scenarios, and GEMSEO's default of 20 iterations stops well short.
SINGLE_REGION_TOLERANCE = 1e-10
SINGLE_REGION_MAX_ITER = 200


@pytest.fixture(scope="module")
def tutorial_dir(tmp_path_factory):
    """A writable copy of the two-region tutorial.

    ``create_partitioning`` rewrites ``partitioning_updated_inputs.json`` in place, so
    running this against the repository copy would leave the working tree dirty.
    """
    target = tmp_path_factory.mktemp("two_regions")
    shutil.copytree(TUTORIAL / "data", target / "data")
    for config in CONFIGS.values():
        shutil.copy(TUTORIAL / config, target / config)
    return target


def _process(tutorial_dir, mode):
    return create_multi_regional_process(
        configuration_file=str(tutorial_dir / CONFIGS[mode]),
        disable_execution_statistics=True,
    )


@pytest.fixture(scope="module")
def computed(tutorial_dir):
    """Both modes, each computed three times, with the column count after each."""
    results = {}
    for mode in CONFIGS:
        process = _process(tutorial_dir, mode)
        counts = []
        for _ in range(3):
            process.compute(parallel=False)
            counts.append(process.data["vector_outputs"].shape[1])
        results[mode] = (process, counts)
    return results


# --------------------------------------------------------------------------------
# The MDA settings
# --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mode", "attribute"),
    [("unified_mda", "mda_chain"), ("separate_processes", "_top_level_mda_chain")],
)
def test_every_chain_is_held_to_the_same_settings_as_a_single_region(tutorial_dir, mode, attribute):
    """Both chains a multi-regional run can build, not just one.

    This is the test that was missing. ``_top_level_mda_chain`` -- the aggregation chain
    of ``separate_processes`` -- was tightened, while ``mda_chain`` -- the chain that
    actually solves the coupled system in ``unified_mda`` -- was left at
    ``tolerance=1e-5`` with no ``max_mda_iter``, under a comment stating that the
    settings matched. The mode with *more* coupling was the one still held to a standard
    the single-region code says is not good enough.
    """
    process = _process(tutorial_dir, mode)
    chain = getattr(process, attribute)

    assert chain.settings.tolerance == SINGLE_REGION_TOLERANCE
    assert chain.settings.max_mda_iter == SINGLE_REGION_MAX_ITER


def test_the_single_region_process_is_where_those_numbers_come_from():
    """Pin the source of the two constants, so they cannot drift apart in silence."""
    import inspect

    from aeromaps.core.process import AeroMAPSProcess

    source = inspect.getsource(AeroMAPSProcess.setup_mda)
    assert "tolerance=1e-10" in source
    assert "max_mda_iter=200" in source


def test_the_gemseo_default_iteration_budget_is_the_one_being_guarded_against(
    tutorial_dir,
):
    """Omitting ``max_mda_iter`` is not a neutral choice: GEMSEO's default is 20.

    Pinned because the failure mode is invisible -- the setting is absent, not wrong,
    and 20 iterations produces a full set of ordinary-looking DataFrames.
    """
    from gemseo.mda.base_mda_settings import BaseMDASettings

    assert BaseMDASettings().max_mda_iter == 20
    assert SINGLE_REGION_MAX_ITER > 20


# --------------------------------------------------------------------------------
# Duplicated output columns on a repeated compute()
# --------------------------------------------------------------------------------


def _old_concat(frame, series):
    """The pre-#157 concatenation, verbatim: onto the existing frame, no drop."""
    if not series:
        return frame
    return pd.concat([frame] + [pd.DataFrame({k: v}) for k, v in series.items()], axis=1)


def test_the_old_concat_appended_a_second_copy_of_every_column():
    """The defect, in isolation: the second call doubles the frame."""
    index = pd.RangeIndex(3)
    series = {"a": pd.Series(1.0, index=index), "b": pd.Series(2.0, index=index)}

    frame = _old_concat(pd.DataFrame(index=index), series)
    assert frame.shape[1] == 2

    frame = _old_concat(frame, series)
    assert frame.shape[1] == 4, "expected the duplication; this no longer reproduces it"
    assert int(frame.columns.duplicated().sum()) == 2

    # And this is why it matters: a duplicated name stops being a Series.
    assert isinstance(frame["a"], pd.DataFrame)


def test_the_helper_refreshes_the_columns_instead():
    """The fix, on the same inputs -- and it must refresh, not merely deduplicate."""
    index = pd.RangeIndex(3)
    first = {"a": pd.Series(1.0, index=index), "b": pd.Series(2.0, index=index)}
    second = {"a": pd.Series(9.0, index=index), "b": pd.Series(2.0, index=index)}

    frame = _concat_series(pd.DataFrame(index=index), first)
    frame = _concat_series(frame, second)

    assert frame.shape[1] == 2
    assert int(frame.columns.duplicated().sum()) == 0
    assert isinstance(frame["a"], pd.Series)
    assert frame["a"].to_numpy() == pytest.approx(9.0), "the new value must win"


@pytest.mark.parametrize("mode", list(CONFIGS))
def test_repeated_compute_does_not_grow_the_output_frame(computed, mode):
    """The same property on the real process, in both execution modes."""
    process, counts = computed[mode]

    assert counts[0] == counts[1] == counts[2], f"column count per compute(): {counts}"
    for label in ("vector_outputs", "climate_outputs"):
        columns = process.data[label].columns
        assert int(columns.duplicated().sum()) == 0, f"{label} has duplicated columns"


@pytest.mark.parametrize("mode", list(CONFIGS))
def test_every_output_column_is_still_a_series(computed, mode):
    """The symptom that made the duplication hard to trace back to its cause."""
    process, _counts = computed[mode]
    outputs = process.data["vector_outputs"]
    for name in list(outputs.columns)[:50]:
        assert isinstance(outputs[name], pd.Series), f"{name} is not a Series"


# --------------------------------------------------------------------------------
# The two modes must agree
# --------------------------------------------------------------------------------


def test_the_two_execution_modes_produce_the_same_outputs(computed):
    """The property the whole two-mode design rests on, and previously untested."""
    separate = computed["separate_processes"][0].data["vector_outputs"]
    unified = computed["unified_mda"][0].data["vector_outputs"]

    assert set(separate.columns) == set(unified.columns)

    mismatches = []
    for name in separate.columns:
        left = separate[name].to_numpy(dtype=float)
        right = unified[name].to_numpy(dtype=float)
        if not np.allclose(left, right, rtol=1e-9, atol=1e-9, equal_nan=True):
            mismatches.append(name)
    assert not mismatches, f"{len(mismatches)} column(s) differ, e.g. {mismatches[:5]}"


def test_the_regional_and_aggregated_outputs_are_both_present(computed):
    """A namespaced regional series and the aggregate built from it."""
    outputs = computed["unified_mda"][0].data["vector_outputs"]
    regional = [c for c in outputs.columns if str(c).startswith("EU_DOM:")]
    overall = [c for c in outputs.columns if str(c).startswith("overall:")]
    assert regional, "no regional columns were harvested"
    assert overall, "no aggregated columns were harvested"

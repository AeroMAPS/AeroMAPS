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

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

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


# --------------------------------------------------------------------------------
# An end year changed after creation
# --------------------------------------------------------------------------------
#
# Before, neither mode followed it. ``separate_processes`` resized each region but not the
# top-level chain, and raised on the aggregated climate outputs. ``unified_mda`` raised
# nothing and returned results that stopped at the old end year: its namespaced
# disciplines are deep copies holding their own copy of the parameters, and nothing
# re-initialised them.

END_YEAR = 2070


@pytest.fixture(scope="module")
def tutorial_dir_at_end_year(tmp_path_factory):
    """The tutorial with ``END_YEAR`` set in every region's inputs at creation."""
    target = tmp_path_factory.mktemp("two_regions_end_year")
    shutil.copytree(TUTORIAL / "data", target / "data")
    for config in CONFIGS.values():
        shutil.copy(TUTORIAL / config, target / config)
    for inputs_file in (target / "data").glob("region_*/inputs.json"):
        inputs = json.loads(inputs_file.read_text())
        inputs["end_year"] = END_YEAR
        inputs_file.write_text(json.dumps(inputs, indent=2))
    return target


def _set_end_year(process, end_year, regions=None):
    for region_id in regions or process.list_regions():
        process.get_regional_process(region_id).parameters.end_year = end_year


@pytest.mark.parametrize("mode", list(CONFIGS))
def test_an_end_year_changed_after_creation_matches_one_set_at_creation(
    tutorial_dir, tutorial_dir_at_end_year, mode
):
    reference = _process(tutorial_dir_at_end_year, mode)
    reference.compute(parallel=False)

    process = _process(tutorial_dir, mode)
    process.compute(parallel=False)
    _set_end_year(process, END_YEAR)
    process.compute(parallel=False)

    assert process.data["years"] == reference.data["years"]
    for frame in ("vector_outputs", "climate_outputs"):
        left, right = process.data[frame], reference.data[frame]
        assert list(left.index) == list(right.index), frame
        assert set(left.columns) == set(right.columns), frame
        mismatches = [
            name
            for name in right.columns
            if not np.allclose(
                left[name].to_numpy(dtype=float),
                right[name].to_numpy(dtype=float),
                rtol=1e-9,
                atol=0.0,
                equal_nan=True,
            )
        ]
        assert not mismatches, f"{frame}: {len(mismatches)} differ, e.g. {mismatches[:5]}"
    assert process.data["float_outputs"] == pytest.approx(
        reference.data["float_outputs"], rel=1e-9, nan_ok=True
    )


def test_regions_with_different_year_bounds_are_refused(tutorial_dir):
    """The aggregate is indexed on one set of years, so the regions must share it."""
    process = _process(tutorial_dir, "unified_mda")
    _set_end_year(process, END_YEAR, regions=["EU_DOM"])

    with pytest.raises(ValueError, match="same year bounds"):
        process.compute(parallel=False)


def test_the_rebuilt_unified_chain_keeps_its_nan_masks_and_coupling_bounds(
    tutorial_dir, monkeypatch
):
    """As for a single region: what the chain's settings do not carry is installed again.

    Recorded at the call rather than read off the solvers, because the tutorial's chain has
    no strongly coupled block and so no inner MDA to carry them.
    """
    from aeromaps.core import multi_regional_process

    masked, bounded = [], []
    freeze = multi_regional_process.freeze_nan_masks_after_first_sweep
    apply_coupling_bounds = multi_regional_process.apply_coupling_bounds

    def recording_freeze(mda_chain):
        masked.append(id(mda_chain))
        return freeze(mda_chain)

    def recording_apply_coupling_bounds(mda_chain, disciplines, namespace=""):
        bounded.append((id(mda_chain), namespace))
        return apply_coupling_bounds(mda_chain, disciplines, namespace)

    monkeypatch.setattr(
        multi_regional_process, "freeze_nan_masks_after_first_sweep", recording_freeze
    )
    monkeypatch.setattr(
        multi_regional_process, "apply_coupling_bounds", recording_apply_coupling_bounds
    )

    process = _process(tutorial_dir, "unified_mda")
    created = id(process.mda_chain)
    process.compute(parallel=False)
    _set_end_year(process, END_YEAR)
    process.compute(parallel=False)

    rebuilt = id(process.mda_chain)
    assert rebuilt != created
    assert rebuilt in masked
    namespaces = {namespace for chain, namespace in bounded if chain == rebuilt}
    assert namespaces == {f"{region_id}:" for region_id in process.list_regions()}


# --------------------------------------------------------------------------------
# Top-level and global models are the process' own copies
# --------------------------------------------------------------------------------


def test_standard_models_are_copied_when_registered():
    """The standard registries hold module-level singletons, as for AeroMAPSProcess.

    Registered as they are, a second multi-regional process would rewrite the first one's
    model parameters and frames.
    """
    from aeromaps.core import models as aeromaps_models
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    singletons = {name: model for name, model in aeromaps_models.models_traffic.items()}
    process = MultiRegionalProcess.__new__(MultiRegionalProcess)
    process.models = {}
    names = []
    process._register_models_into({"models_traffic": aeromaps_models.models_traffic}, names)

    assert names
    for model in singletons.values():
        assert process.models[model.name] is not model
        assert type(process.models[model.name]) is type(model)


# --------------------------------------------------------------------------------
# A failed top-level chain stays inspectable
# --------------------------------------------------------------------------------


def test_a_failed_top_level_chain_still_harvests_its_outputs(tutorial_dir, monkeypatch):
    """The convergence check runs after harvesting, as in the unified and single paths."""
    from aeromaps.core import multi_regional_process
    from aeromaps.core.gemseo import MDAConvergenceError

    def failing_top_level_check(mda_chain, context="", on_failure="raise"):
        if context.startswith("top-level"):
            raise MDAConvergenceError("top-level chain did not converge")

    monkeypatch.setattr(multi_regional_process, "check_mda_convergence", failing_top_level_check)

    process = _process(tutorial_dir, "separate_processes")
    with pytest.raises(MDAConvergenceError):
        process.compute(parallel=False)

    outputs = process.data["vector_outputs"]
    assert "EU_DOM:rpk" in outputs
    assert "overall:rpk" in outputs


# --------------------------------------------------------------------------------
# A global model, actually instantiated
# --------------------------------------------------------------------------------

GLOBAL_MODEL = '''
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class WorldRpk(AeroMAPSModel):
    """Reads every region's ``{region}:rpk`` and writes one un-namespaced total."""

    def __init__(self, name="world_rpk", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.regions = []  # injected by MultiRegionalProcess before custom_setup()
        self.input_names = {}
        self.output_names = {"world_rpk": pd.Series([0.0])}

    def custom_setup(self):
        self.input_names = {f"{region}:rpk": pd.Series([0.0]) for region in self.regions}

    def compute(self, input_data):
        total = sum(input_data[f"{region}:rpk"] for region in self.regions)
        self.df.loc[:, "world_rpk"] = total
        return {"world_rpk": total}
'''


def _with_global_model(tutorial_dir, mode):
    (tutorial_dir / "world_rpk.py").write_text(GLOBAL_MODEL)
    config = yaml.safe_load((tutorial_dir / CONFIGS[mode]).read_text())
    config["regionalisation"]["global_models"] = {
        "customs": {"world_rpk": "world_rpk.py::WorldRpk"}
    }
    path = tutorial_dir / f"global_model_{mode}.yaml"
    path.write_text(yaml.dump(config))
    return create_multi_regional_process(
        configuration_file=str(path), disable_execution_statistics=True
    )


def test_a_global_model_reads_every_region_and_writes_an_unnamespaced_output(tutorial_dir):
    process = _with_global_model(tutorial_dir, "unified_mda")
    assert process.models["world_rpk"].regions == process.list_regions()

    process.compute(parallel=False)

    outputs = process.data["vector_outputs"]
    expected = sum(outputs[f"{region}:rpk"] for region in process.list_regions())
    np.testing.assert_allclose(outputs["world_rpk"], expected, rtol=1e-12)


def test_a_global_model_is_refused_in_separate_processes(tutorial_dir):
    """Separate processes solve each region alone, so no loop across regions can close."""
    with pytest.raises(NotImplementedError, match="global_models"):
        _with_global_model(tutorial_dir, "separate_processes")

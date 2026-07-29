"""
test_multi_regional_aggregation
===============================

Exercises the multi-regional aggregation pipeline for every output kind:
vector outputs, climate outputs (longer year index) and float outputs
(scalars), through the real ``RegionalAggregator`` + top-level MDAChain +
harvest path of ``MultiRegionalProcess._aggregate_regional_outputs``.

What is tested
--------------
1. ``sum`` aggregation of a vector, a climate and a float variable, each
   landing in the right data container (``vector_outputs``,
   ``climate_outputs``, ``float_outputs``).
2. ``weighted_average`` aggregation for vector/vector, climate/climate and
   float/float variable-weight pairs, with correct values.
3. Zero total weight yields NaN instead of a division error (scalar case).
4. A variable produced by no region fails with a ``ValueError`` naming it.
5. The float accessors (``get_global_float_outputs`` /
   ``get_regional_float_outputs``) strip the namespace prefix.

The MultiRegionalProcess is built synthetically (``__new__`` + hand-filled
regional data) so no regional AeroMAPS processes are instantiated; the
aggregator, MDA chain and harvest code under test are the real ones.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from aeromaps.core.multi_regional_process import MultiRegionalProcess
from aeromaps.models.multi_regional.regional_aggregator import RegionalAggregator

# ── Synthetic years and parameters ─────────────────────────────────────────────

HISTORIC_START = 2020
PROSPECTION_START = 2026
END_YEAR = 2035
CLIMATE_START = 2000

FULL_YEARS = list(range(HISTORIC_START, END_YEAR + 1))
CLIMATE_YEARS = list(range(CLIMATE_START, END_YEAR + 1))

PARAMS = SimpleNamespace(
    climate_historic_start_year=CLIMATE_START,
    historic_start_year=HISTORIC_START,
    prospection_start_year=PROSPECTION_START,
    end_year=END_YEAR,
)

REGION_SCALES = {"R1": 1.0, "R2": 2.0}


def _regional_data(scale: float) -> dict:
    n, nc = len(FULL_YEARS), len(CLIMATE_YEARS)
    return {
        "vector_outputs": pd.DataFrame(
            {
                "rpk": pd.Series(np.linspace(1.0, 2.0, n) * scale, index=FULL_YEARS),
                "ask": pd.Series(np.linspace(2.0, 3.0, n) * scale, index=FULL_YEARS),
                "load_factor": pd.Series(np.full(n, 80.0 + 5.0 * scale), index=FULL_YEARS),
            }
        ),
        "climate_outputs": pd.DataFrame(
            {
                "total_erf": pd.Series(np.linspace(0.5, 1.5, nc) * scale, index=CLIMATE_YEARS),
                "erf_weight": pd.Series(np.full(nc, scale), index=CLIMATE_YEARS),
            }
        ),
        "float_outputs": {
            "cumulative_metric": 10.0 * scale,
            "intensity_metric": 3.0 * scale,
            "weight_metric": 1.0 * scale,
            "zero_weight_metric": 0.0,
        },
    }


def _build_process(aggregation_config: dict) -> MultiRegionalProcess:
    proc = MultiRegionalProcess.__new__(MultiRegionalProcess)
    proc._region_ids = list(REGION_SCALES)
    proc._global_namespace = "overall"
    proc._top_level_model_names = []
    proc._regional_processes = {
        rid: SimpleNamespace(data=_regional_data(scale)) for rid, scale in REGION_SCALES.items()
    }
    proc.models = {
        "aggregator": RegionalAggregator(
            name="RegionalAggregator",
            regions=proc._region_ids,
            aggregation_config=aggregation_config,
            global_namespace="overall",
            parameters=PARAMS,
        )
    }
    proc._setup_separate_processes()
    proc.data = {
        "years": {"full_years": FULL_YEARS, "climate_full_years": CLIMATE_YEARS},
        "float_inputs": {},
        "vector_outputs": pd.DataFrame(index=FULL_YEARS),
        "climate_outputs": pd.DataFrame(index=CLIMATE_YEARS),
        "float_outputs": {},
    }
    return proc


# ── Sum aggregation across output kinds ────────────────────────────────────────


@pytest.fixture()
def summed_process() -> MultiRegionalProcess:
    proc = _build_process({"sum": ["rpk", "total_erf", "cumulative_metric"]})
    proc._aggregate_regional_outputs()
    return proc


def test_vector_sum_lands_in_vector_outputs(summed_process):
    result = summed_process.data["vector_outputs"]["overall:rpk"]
    expected = sum(
        summed_process._regional_processes[rid].data["vector_outputs"]["rpk"]
        for rid in REGION_SCALES
    )
    pd.testing.assert_series_equal(result, expected, check_names=False)


def test_climate_sum_lands_in_climate_outputs(summed_process):
    assert "overall:total_erf" not in summed_process.data["vector_outputs"].columns
    result = summed_process.data["climate_outputs"]["overall:total_erf"]
    expected = sum(
        summed_process._regional_processes[rid].data["climate_outputs"]["total_erf"]
        for rid in REGION_SCALES
    )
    assert list(result.index) == CLIMATE_YEARS
    pd.testing.assert_series_equal(result, expected, check_names=False)


def test_climate_sum_stored_in_aggregator_df_climate(summed_process):
    aggregator = summed_process.models["aggregator"]
    assert "overall:total_erf" in aggregator.df_climate.columns
    assert "overall:total_erf" not in aggregator.df.columns
    assert "overall:rpk" in aggregator.df.columns


def test_float_sum_lands_in_float_outputs(summed_process):
    assert summed_process.data["float_outputs"]["overall:cumulative_metric"] == pytest.approx(30.0)


# ── Weighted-average aggregation across output kinds ───────────────────────────


def test_weighted_average_vector_by_vector():
    proc = _build_process({"weighted_average": [{"variable": "load_factor", "weight_by": "ask"}]})
    proc._aggregate_regional_outputs()
    result = proc.data["vector_outputs"]["overall:load_factor"]
    r1, r2 = (proc._regional_processes[rid].data["vector_outputs"] for rid in REGION_SCALES)
    expected = (r1["load_factor"] * r1["ask"] + r2["load_factor"] * r2["ask"]) / (
        r1["ask"] + r2["ask"]
    )
    pd.testing.assert_series_equal(result, expected, check_names=False)


def test_weighted_average_climate_by_climate():
    proc = _build_process(
        {"weighted_average": [{"variable": "total_erf", "weight_by": "erf_weight"}]}
    )
    proc._aggregate_regional_outputs()
    result = proc.data["climate_outputs"]["overall:total_erf"]
    r1, r2 = (proc._regional_processes[rid].data["climate_outputs"] for rid in REGION_SCALES)
    expected = (r1["total_erf"] * r1["erf_weight"] + r2["total_erf"] * r2["erf_weight"]) / (
        r1["erf_weight"] + r2["erf_weight"]
    )
    pd.testing.assert_series_equal(result, expected, check_names=False)


def test_weighted_average_float_by_float():
    proc = _build_process(
        {"weighted_average": [{"variable": "intensity_metric", "weight_by": "weight_metric"}]}
    )
    proc._aggregate_regional_outputs()
    # (3*1 + 6*2) / (1 + 2) = 5
    assert proc.data["float_outputs"]["overall:intensity_metric"] == pytest.approx(5.0)


def test_weighted_average_float_zero_weight_is_nan():
    proc = _build_process(
        {"weighted_average": [{"variable": "intensity_metric", "weight_by": "zero_weight_metric"}]}
    )
    proc._aggregate_regional_outputs()
    assert np.isnan(proc.data["float_outputs"]["overall:intensity_metric"])


# ── Guard rails ────────────────────────────────────────────────────────────────


def test_variable_produced_by_no_region_raises():
    proc = _build_process({"sum": ["bogus_variable"]})
    with pytest.raises(ValueError, match="R1:bogus_variable.*aggregation"):
        proc._aggregate_regional_outputs()


def test_weight_produced_by_no_region_raises():
    proc = _build_process(
        {"weighted_average": [{"variable": "load_factor", "weight_by": "bogus_weight"}]}
    )
    with pytest.raises(ValueError, match="bogus_weight.*aggregation"):
        proc._aggregate_regional_outputs()


# ── Float accessors ────────────────────────────────────────────────────────────


def test_float_accessors_strip_namespace(summed_process):
    assert summed_process.get_global_float_outputs() == {"cumulative_metric": pytest.approx(30.0)}
    regional = summed_process.get_regional_float_outputs("R1")
    assert regional["cumulative_metric"] == pytest.approx(10.0)
    with pytest.raises(KeyError, match="R3"):
        summed_process.get_regional_float_outputs("R3")

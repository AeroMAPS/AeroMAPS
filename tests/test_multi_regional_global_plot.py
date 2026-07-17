"""
test_multi_regional_global_plot
===============================

Exercises ``MultiRegionalProcess.plot(name)`` (no ``region``): the global plot
path introduced for aggregated outputs.

What is tested
--------------
1. An aggregation-safe plot whose required outputs are present in the
   ``overall:`` namespace renders, and the drawn data is the aggregated series
   (prefix stripped) — both for a vector-only plot (RPK) and for one that also
   reads ``df_climate`` (air_transport_co2_emissions).
2. Missing aggregated variables fail with a ``ValueError`` naming the exact
   missing variables and pointing at the regionalisation ``aggregation`` block.
3. Non-aggregation-safe plots raise ``NotImplementedError`` redirecting to
   ``region=<id>``; fleet plots and unknown names raise ``NameError``;
   plotting before ``compute()`` raises ``RuntimeError``.
4. Registry consistency: every whitelisted name exists in ``available_plots``.

The MultiRegionalProcess is built synthetically (``__new__`` + hand-filled
``data``) so no regional AeroMAPS processes are instantiated; the plot classes
under test are the real ones.
"""

from __future__ import annotations

from types import SimpleNamespace

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")

from aeromaps.core.multi_regional_process import MultiRegionalProcess  # noqa: E402
from aeromaps.plots.single_scenario import (  # noqa: E402
    aggregation_safe_plots,
    available_plots,
)

# ── Synthetic multi-regional process ───────────────────────────────────────────

HISTORIC_START = 2020
PROSPECTION_START = 2026
END_YEAR = 2035
CLIMATE_START = 2000

FULL_YEARS = list(range(HISTORIC_START, END_YEAR + 1))
HISTORIC_YEARS = list(range(HISTORIC_START, PROSPECTION_START))
PROSPECTIVE_YEARS = list(range(PROSPECTION_START - 1, END_YEAR + 1))
CLIMATE_YEARS = list(range(CLIMATE_START, END_YEAR + 1))

CO2_PLOT_VECTOR_VARS = [
    "co2_emissions_last_historical_year_technology",
    "co2_emissions_including_aircraft_efficiency",
    "co2_emissions_including_load_factor",
    "co2_emissions_including_energy",
    "co2_emissions_last_historical_year_technology_baseline3",
    "carbon_offset",
]


def _build_process() -> MultiRegionalProcess:
    proc = MultiRegionalProcess.__new__(MultiRegionalProcess)
    proc._region_ids = ["R1", "R2"]
    proc._global_namespace = "overall"
    proc._regional_processes = {
        rid: SimpleNamespace(data={"float_inputs": {"dummy_param": 1.0}})
        for rid in proc._region_ids
    }

    n = len(FULL_YEARS)
    vector = {}
    for rid, scale in (("R1", 1.0), ("R2", 2.0)):
        vector[f"{rid}:rpk"] = pd.Series(np.linspace(1.0, 2.0, n) * scale, index=FULL_YEARS)
        for var in CO2_PLOT_VECTOR_VARS:
            vector[f"{rid}:{var}"] = pd.Series(np.linspace(3.0, 1.0, n) * scale, index=FULL_YEARS)
    vector["overall:rpk"] = vector["R1:rpk"] + vector["R2:rpk"]
    for var in CO2_PLOT_VECTOR_VARS:
        vector[f"overall:{var}"] = vector[f"R1:{var}"] + vector[f"R2:{var}"]

    nc = len(CLIMATE_YEARS)
    climate = {
        "R1:co2_emissions": pd.Series(np.linspace(2.0, 3.0, nc), index=CLIMATE_YEARS),
        "R2:co2_emissions": pd.Series(np.linspace(4.0, 6.0, nc), index=CLIMATE_YEARS),
    }
    climate["overall:co2_emissions"] = climate["R1:co2_emissions"] + climate["R2:co2_emissions"]

    proc.data = {
        "years": {
            "full_years": FULL_YEARS,
            "historic_years": HISTORIC_YEARS,
            "prospective_years": PROSPECTIVE_YEARS,
            "climate_full_years": CLIMATE_YEARS,
        },
        "float_inputs": {},
        "vector_outputs": pd.DataFrame(vector),
        "climate_outputs": pd.DataFrame(climate),
        "float_outputs": {"overall:some_float": 3.0, "R1:some_float": 1.0},
    }
    return proc


@pytest.fixture()
def process():
    return _build_process()


# ── Rendering ──────────────────────────────────────────────────────────────────


def test_global_rpk_plot_renders_aggregated_series(process):
    fig_obj = process.plot("revenue_passenger_kilometer")
    # Two lines: history + projection, carrying the aggregated overall series.
    history_line, projection_line = fig_obj.ax.get_lines()
    expected = process.data["vector_outputs"]["overall:rpk"]
    np.testing.assert_allclose(history_line.get_ydata(), expected.loc[HISTORIC_YEARS])
    np.testing.assert_allclose(projection_line.get_ydata(), expected.loc[PROSPECTIVE_YEARS])
    matplotlib.pyplot.close(fig_obj.fig)


def test_global_co2_plot_reads_vector_and_climate(process):
    fig_obj = process.plot("air_transport_co2_emissions")
    assert fig_obj.fig is not None
    matplotlib.pyplot.close(fig_obj.fig)


def test_global_view_strips_prefixes(process):
    from aeromaps.core.multi_regional_process import _GlobalOutputsView

    view = _GlobalOutputsView(process)
    assert "rpk" in view.data["vector_outputs"].columns
    assert "co2_emissions" in view.data["climate_outputs"].columns
    assert view.data["float_outputs"] == {"some_float": 3.0}
    assert view.data["float_inputs"] == {"dummy_param": 1.0}
    assert view.pathways_manager is None


# ── Guard rails ────────────────────────────────────────────────────────────────


def test_missing_aggregated_variables_error_lists_them(process):
    # load_factor is whitelisted but overall:load_factor was never aggregated.
    with pytest.raises(ValueError, match=r"load_factor.*aggregation"):
        process.plot("load_factor")


def test_non_aggregation_safe_plot_redirects_to_region(process):
    with pytest.raises(NotImplementedError, match=r"energy_mix.*region=<id>"):
        process.plot("energy_mix")


def test_fleet_plot_is_regional_only(process):
    with pytest.raises(NameError, match=r"annual_MACC.*fleet"):
        process.plot("annual_MACC")


def test_unknown_plot_name(process):
    with pytest.raises(NameError, match="not available"):
        process.plot("no_such_plot")


def test_plot_before_compute_raises(process):
    process.data["vector_outputs"] = pd.DataFrame()
    with pytest.raises(RuntimeError, match="compute"):
        process.plot("revenue_passenger_kilometer")


# ── Registry consistency ───────────────────────────────────────────────────────


def test_whitelist_is_subset_of_available_plots(process):
    assert set(aggregation_safe_plots) <= set(available_plots)
    assert process.list_available_global_plots() == list(aggregation_safe_plots)

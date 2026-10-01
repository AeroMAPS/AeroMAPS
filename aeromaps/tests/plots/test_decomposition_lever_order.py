"""
The ATAG lever order of the detailed CO2 decomposition plot.

Only the stacking changes with ``lever_order="atag"``: the sub-lever values are the
same, so the bands still close on the same curves, and the ATAG pillars of
``bottom_up_pillars`` sum to the same total as the cascade does.
"""

import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from aeromaps import create_process
from aeromaps.plots.single_scenario.main import AirTransportCO2EmissionsDetailedPlot
from aeromaps.utils.decomposition import bottom_up_pillars

CONFIG = os.path.join(
    os.path.dirname(__file__), "..", "tested_configs", "config_advanced.yaml"
)


@pytest.fixture(scope="module")
def process():
    proc = create_process(configuration_file=CONFIG)
    proc.compute()
    return proc


def _band_labels(plot):
    return [c.get_label() for c in plot.ax.collections if c.get_label() and not c.get_label().startswith("_")]


def test_lever_order_is_validated(process):
    with pytest.raises(ValueError):
        AirTransportCO2EmissionsDetailedPlot(process, lever_order="alphabetical")


def test_atag_order_keeps_the_same_bands(process):
    default = AirTransportCO2EmissionsDetailedPlot(process)
    atag = AirTransportCO2EmissionsDetailedPlot(process, lever_order="atag")
    # Same bands, stacked in another order. The ATAG stacking skips a band that is zero
    # throughout (here demand and the offsets), where the default one always draws it.
    missing = set(_band_labels(default)) - set(_band_labels(atag))
    assert missing <= {"Demand/supply side management", "Carbon offset"}
    assert set(_band_labels(atag)) <= set(_band_labels(default))
    plt.close("all")


def test_atag_order_puts_alternative_aircraft_before_operations(process):
    atag = AirTransportCO2EmissionsDetailedPlot(process, lever_order="atag")
    labels = _band_labels(atag)
    alternative = [i for i, label in enumerate(labels) if "hydrogen" in label.lower()]
    operations = [i for i, label in enumerate(labels) if label.startswith(("Load factor", "Fleet operations"))]
    if alternative and operations:
        assert max(alternative) < min(operations)
    plt.close("all")


def test_atag_pillars_close_on_the_gross_cascade(process):
    pillars = bottom_up_pillars(process)
    frame = process.data["vector_outputs"]
    years = range(process.parameters.prospection_start_year, process.parameters.end_year + 1)
    technology = frame["co2_emissions_last_historical_year_technology"]
    gross = pillars.attrs["gross"]
    # fleet renewal + next generation + operations + SAF (all physical levers) take the
    # frozen-technology trajectory down to the gross emissions.
    physical = pillars[["fleet_renewal", "next_generation", "operations", "saf"]].sum(axis=1)
    residual = (technology - gross - physical).loc[years]
    assert np.abs(residual).max() < 1e-6

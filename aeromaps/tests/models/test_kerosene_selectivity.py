"""Pin the meaning and the wiring of ``kerosene_selectivity``.

Selectivity is the share of a plant's output that is aviation fuel. It is therefore a
*divisor*: producing one unit of jet fuel at 15 % selectivity mobilises ``1 / 0.15``
units of feedstock, which is what the ``*_total_mobilised_with_selectivity`` outputs
report and what the resource-budget models divide by the global availability.

Two regressions are guarded here:

* the bottom-up model used to *multiply* by the selectivity, understating the resource
  footprint by ``s**2`` relative to the top-down model, which has always divided;
* it used to read ``{pathway}_eis_kerosene_selectivity``, a name no configuration file
  writes, so selectivity silently defaulted to 1.0 and hid the inversion.

Both models read the same ``kerosene_selectivity``, and both fall back to 1.0 when a
pathway does not declare one.
"""

from pathlib import Path

import pandas as pd
import pytest

from aeromaps import create_process
from aeromaps.models.impacts.generic_energy_model.bottom_up.environmental import (
    BottomUpEnvironmental,
)
from aeromaps.models.impacts.generic_energy_model.top_down.environmental import (
    TopDownEnvironmental,
)

CONFIG_DIR = Path(__file__).parent.parent / "tested_configs"

START_YEAR = 2020
END_YEAR = 2025
YEARS = range(START_YEAR, END_YEAR + 1)

SELECTIVITY = 0.2
SPECIFIC_CONSUMPTION = 1.5
LIFESPAN = 2
COMMISSIONING_YEAR = 2022
PRODUCTION = 10.0


def _with_year_range(model):
    """Give a standalone discipline the year range the process would have set."""
    model.historic_start_year = START_YEAR
    model.end_year = END_YEAR
    model.df = pd.DataFrame(index=pd.Index(YEARS, name="years"))
    return model


def _energy_series(values):
    return pd.Series(values, index=YEARS, dtype=float)


def _consumption_profile():
    """One vintage commissioned in 2022, producing over its two-year lifespan."""
    return _energy_series(
        [
            PRODUCTION if year in (COMMISSIONING_YEAR, COMMISSIONING_YEAR + 1) else 0.0
            for year in YEARS
        ]
    )


def _run_bottom_up(selectivity=SELECTIVITY):
    technical = {
        "pw_resource_names": ["feed"],
        "pw_eis_resource_specific_consumption_feed": SPECIFIC_CONSUMPTION,
        "pw_eis_plant_lifespan": LIFESPAN,
    }
    if selectivity is not None:
        technical["pw_kerosene_selectivity"] = selectivity

    model = _with_year_range(
        BottomUpEnvironmental(
            name="pw_bottom_up_unit_environmental",
            configuration_data={
                "name": "pw",
                "inputs": {"environmental": {}, "technical": technical},
            },
            resources_data={"feed": {"specifications": {}}},
            processes_data={},
        )
    )
    input_data = dict(model.input_names)
    input_data["pw_energy_production_commissioned"] = _energy_series(
        [PRODUCTION if year == COMMISSIONING_YEAR else 0.0 for year in YEARS]
    )
    input_data["pw_energy_consumption"] = _consumption_profile()
    input_data["pw_energy_unused"] = _energy_series([0.0] * len(YEARS))
    return model.compute(input_data)


def _run_top_down(selectivity=SELECTIVITY):
    technical = {
        "pw_resource_names": ["feed"],
        "pw_resource_specific_consumption_feed": SPECIFIC_CONSUMPTION,
    }
    if selectivity is not None:
        technical["pw_kerosene_selectivity"] = selectivity

    model = _with_year_range(
        TopDownEnvironmental(
            name="pw_top_down_unit_environmental",
            configuration_data={
                "name": "pw",
                "inputs": {"environmental": {}, "technical": technical},
            },
            resources_data={"feed": {"specifications": {}}},
            processes_data={},
        )
    )
    input_data = dict(model.input_names)
    input_data["pw_energy_consumption"] = _consumption_profile()
    return model.compute(input_data)


def test_bottom_up_mobilises_the_inverse_of_the_selectivity():
    """A pathway at selectivity ``s`` mobilises ``1 / s`` times what it consumes."""
    output = _run_bottom_up()

    consumption = output["pw_feed_total_consumption"]
    mobilised = output["pw_feed_total_mobilised_with_selectivity"]
    produced = consumption.dropna()

    assert not produced.empty
    assert produced.eq(PRODUCTION * SPECIFIC_CONSUMPTION).all()
    pd.testing.assert_series_equal(mobilised, consumption / SELECTIVITY, check_names=False)


def test_bottom_up_and_top_down_agree_on_the_same_selectivity():
    """The two modelling approaches must not disagree on the same physical input."""
    bottom_up = _run_bottom_up()["pw_feed_total_mobilised_with_selectivity"]
    top_down = _run_top_down()["pw_feed_total_mobilised_with_selectivity"]

    # The bottom-up model leaves years without a vintage at NaN where the top-down model
    # writes 0.0; compare only the years the vintage actually produces in.
    produced = bottom_up.dropna().index
    pd.testing.assert_series_equal(
        bottom_up.loc[produced], top_down.loc[produced], check_names=False
    )


@pytest.mark.parametrize("run", [_run_bottom_up, _run_top_down])
def test_unspecified_selectivity_means_the_whole_output_is_aviation_fuel(run):
    output = run(selectivity=None)

    pd.testing.assert_series_equal(
        output["pw_feed_total_mobilised_with_selectivity"],
        output["pw_feed_total_consumption"],
        check_names=False,
    )


@pytest.fixture(scope="module")
def advanced_process():
    process = create_process(configuration_file=CONFIG_DIR / "config_advanced.yaml")
    process.compute()
    return process


def test_selectivity_reaches_the_shipped_configurations(advanced_process):
    """End-to-end: the key a configuration writes is the key the model reads.

    The historical failure was a name mismatch, so this has to go through the real
    configuration plumbing rather than a hand-built ``input_data``.
    """
    suffix = "_total_mobilised_with_selectivity"
    outputs = advanced_process.data["vector_outputs"]

    selectivities = {
        name[: -len("_kerosene_selectivity")]: value
        for name, value in advanced_process.data["float_inputs"].items()
        if name.endswith("_kerosene_selectivity")
    }
    assert selectivities, "the tested configuration no longer declares any selectivity"
    assert any(value != 1.0 for value in selectivities.values()), (
        "the tested configuration only declares neutral selectivities, "
        "which cannot distinguish a multiplication from a division"
    )

    checked = 0
    for column in outputs.columns:
        if not column.endswith(suffix):
            continue
        # Pathway names may share a prefix ('ft_msw' / 'ft_others'), so take the longest.
        candidates = [p for p in selectivities if column.startswith(f"{p}_")]
        if not candidates:
            continue
        pathway = max(candidates, key=len)
        consumption = outputs[f"{column[: -len(suffix)]}_total_consumption"]
        if not (consumption.fillna(0.0) > 0).any():
            continue

        pd.testing.assert_series_equal(
            outputs[column],
            consumption / selectivities[pathway],
            check_names=False,
        )
        checked += 1

    assert checked, "no pathway consumed a resource; the assertion above never ran"

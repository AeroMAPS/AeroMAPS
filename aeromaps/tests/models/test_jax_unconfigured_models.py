"""Pandas/JAX comparison of the models no tested configuration instantiates.

`test_jax_parity` covers everything the six tested configurations wire up; the
models exercised here are reachable only through model sets that no tested
configuration selects (the welfare/surplus family, the simple freight
efficiency model and the legacy simple CO2 model), so they are compared
directly against their pandas `compute`.
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.aircraft_efficiency import (
    FreightAircraftEfficiencySimple,
)
from aeromaps.models.impacts.costs.scenario.scenario_cost import (
    AirlineSurplusLoss,
    ConsumerSurplusLoss,
    TaxRevenueLoss,
    TotalSurplusLoss,
    TotalWelfareLoss,
)
from aeromaps.models.impacts.emissions.co2_emissions import SimpleCO2Emissions

PARAMETERS = SimpleNamespace(
    climate_historic_start_year=1940,
    historic_start_year=2000,
    prospection_start_year=2020,
    end_year=2050,
)
YEARS = range(2000, 2051)
N_YEARS = len(YEARS)


def _series(values):
    return pd.Series(np.asarray(values, dtype=float), index=YEARS)


def _assert_paths_agree(model, kwargs):
    pandas_output = model.compute(
        **{k: (v.copy() if isinstance(v, pd.Series) else v) for k, v in kwargs.items()}
    )
    jax_output = model.jax_compute(
        **{
            k: (v.to_numpy(dtype=float) if isinstance(v, pd.Series) else v)
            for k, v in kwargs.items()
        }
    )
    if not isinstance(pandas_output, tuple):
        pandas_output, jax_output = (pandas_output,), (jax_output,)
    # jax_compute may return the model's `jax_extra_output_names` after the
    # declared outputs; those are checked against model.df by the caller.
    extras = len(getattr(model, "jax_extra_output_names", ()))
    assert len(jax_output) == len(pandas_output) + extras
    for position, (expected, actual) in enumerate(zip(pandas_output, jax_output)):
        expected = np.asarray(expected, dtype=float)
        actual = np.asarray(actual, dtype=float)
        assert expected.shape == actual.shape, position
        np.testing.assert_array_equal(np.isnan(expected), np.isnan(actual), err_msg=str(position))
        np.testing.assert_allclose(
            np.nan_to_num(actual),
            np.nan_to_num(expected),
            rtol=1e-9,
            atol=1e-10,
            err_msg=str(position),
        )
    for offset, name in enumerate(getattr(model, "jax_extra_output_names", ())):
        expected = model.df[name].to_numpy(dtype=float)
        actual = np.asarray(jax_output[len(pandas_output) + offset], dtype=float)
        np.testing.assert_allclose(actual, expected, rtol=1e-9, atol=1e-10, err_msg=name)
    return pandas_output


_RPK = _series(np.linspace(4e12, 1.2e13, N_YEARS))
_RPK_NO_ELASTICITY = _series(np.linspace(4e12, 1.4e13, N_YEARS))
_AIRFARE = _series(np.linspace(0.09, 0.13, N_YEARS))
_COST_PER_RPK = _series(np.linspace(0.08, 0.11, N_YEARS))


@pytest.mark.parametrize("price_elasticity", [-0.6, -1.0])
def test_total_surplus_loss(price_elasticity):
    model = TotalSurplusLoss("total_surplus_loss", parameters=PARAMETERS)
    _assert_paths_agree(
        model,
        {
            "rpk": _RPK,
            "rpk_no_elasticity": _RPK_NO_ELASTICITY,
            "cumulative_total_airline_cost_increase": _series(np.linspace(0.0, 5e5, N_YEARS)),
            "cumulative_total_airline_cost_increase_discounted": _series(
                np.linspace(0.0, 4e5, N_YEARS)
            ),
            "airfare_per_rpk": _AIRFARE,
            "price_elasticity": price_elasticity,
            "social_discount_rate": 0.03,
        },
    )


@pytest.mark.parametrize("price_elasticity", [-0.6, -1.0])
def test_consumer_surplus_loss(price_elasticity):
    model = ConsumerSurplusLoss("consumer_surplus_loss", parameters=PARAMETERS)
    _assert_paths_agree(
        model,
        {
            "rpk": _RPK,
            "rpk_no_elasticity": _RPK_NO_ELASTICITY,
            "airfare_per_rpk": _AIRFARE,
            "price_elasticity": price_elasticity,
            "social_discount_rate": 0.03,
        },
    )


def test_airline_surplus_loss():
    model = AirlineSurplusLoss("airline_surplus_loss", parameters=PARAMETERS)
    _assert_paths_agree(
        model,
        {
            "total_cost_per_rpk": _COST_PER_RPK,
            "rpk": _RPK,
            "rpk_no_elasticity": _RPK_NO_ELASTICITY,
            "social_discount_rate": 0.03,
            "airfare_per_rpk": _AIRFARE,
        },
    )


def test_tax_revenue_loss():
    model = TaxRevenueLoss("tax_revenue_loss", parameters=PARAMETERS)
    _assert_paths_agree(
        model,
        {
            "total_extra_tax_per_rpk": _series(np.linspace(0.0, 0.01, N_YEARS)),
            "rpk": _RPK,
            "rpk_no_elasticity": _RPK_NO_ELASTICITY,
            "social_discount_rate": 0.03,
        },
    )


def test_total_welfare_loss():
    model = TotalWelfareLoss("total_welfare_loss", parameters=PARAMETERS)
    _assert_paths_agree(
        model,
        {
            "delta_tax_revenue": _series(np.linspace(0.0, 1e4, N_YEARS)),
            "delta_consumer_surplus": _series(np.linspace(0.0, 3e4, N_YEARS)),
            "delta_airline_surplus": _series(np.linspace(0.0, 2e4, N_YEARS)),
            "social_discount_rate": 0.03,
        },
    )


def test_simple_co2_emissions():
    model = SimpleCO2Emissions("simple_co2_emissions", parameters=PARAMETERS)
    n_climate_history = PARAMETERS.historic_start_year - PARAMETERS.climate_historic_start_year
    model.climate_historical_data = np.column_stack(
        [
            np.arange(n_climate_history, dtype=float),
            np.linspace(0.1, 0.6, n_climate_history),
        ]
    )
    energy_init = _series(np.linspace(1e13, 1.5e13, N_YEARS))
    _assert_paths_agree(
        model,
        {
            "energy_consumption_init": energy_init,
            "dropin_fuel_mean_co2_emission_factor": _series(np.full(N_YEARS, 88.7)),
            "hydrogen_mean_co2_emission_factor": _series(np.linspace(90.0, 10.0, N_YEARS)),
            "electric_mean_co2_emission_factor": _series(np.linspace(60.0, 5.0, N_YEARS)),
            "energy_consumption_dropin_fuel": _series(np.linspace(1e13, 1.1e13, N_YEARS)),
            "energy_consumption_hydrogen": _series(np.linspace(0.0, 2e12, N_YEARS)),
            "energy_consumption_electricity": _series(np.linspace(0.0, 5e11, N_YEARS)),
        },
    )


class _Market:
    def __init__(self, market_id):
        self.id = market_id


class _Markets:
    def __init__(self, markets):
        self._markets = markets

    def get(self, traffic_type=None):
        return self._markets


def test_freight_aircraft_efficiency_simple():
    model = FreightAircraftEfficiencySimple("freight_aircraft_efficiency", parameters=PARAMETERS)
    model.markets = _Markets([_Market("belly"), _Market("full_freighter")])
    model.custom_setup()

    input_data = {
        "energy_consumption_init": _series(np.linspace(1e13, 1.5e13, N_YEARS)),
        "covid_energy_intensity_per_rtk_increase_2020": 12.0,
        "rtk": _series(np.linspace(2e11, 6e11, N_YEARS)),
    }
    for market_id, share in (("belly", 60.0), ("full_freighter", 40.0)):
        input_data[f"rtk_{market_id}"] = _series(np.linspace(1e11, 3e11, N_YEARS) * share / 100.0)
        input_data[f"{market_id}_energy_share_last_historical_year"] = share
        input_data[f"{market_id}_energy_per_rtk_dropin_fuel_gain_reference_years"] = [
            2020,
            2035,
            2050,
        ]
        input_data[f"{market_id}_energy_per_rtk_dropin_fuel_gain_reference_years_values"] = [
            0.0,
            1.5,
            1.0,
        ]

    pandas_output = model.compute(dict(input_data))
    jax_output = model.jax_compute(
        {
            k: (v.to_numpy(dtype=float) if isinstance(v, pd.Series) else v)
            for k, v in input_data.items()
        }
    )
    assert set(jax_output) == set(pandas_output)
    for name, expected in pandas_output.items():
        expected = np.asarray(expected, dtype=float)
        actual = np.asarray(jax_output[name], dtype=float)
        assert expected.shape == actual.shape, name
        np.testing.assert_array_equal(np.isnan(expected), np.isnan(actual), err_msg=name)
        np.testing.assert_allclose(
            np.nan_to_num(actual), np.nan_to_num(expected), rtol=1e-9, atol=1e-10, err_msg=name
        )

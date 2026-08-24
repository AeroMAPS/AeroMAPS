"""Fuel subsidies and fuel taxes must reach the fare, not only the reporting totals.

``PassengerAircraftDocEnergySubsidy`` and ``PassengerAircraftDocEnergyTax`` have
always turned per-MJ subsidies and excise taxes into a per-ASK DOC, and
``PassengerAircraftTotalDoc`` has always netted them into ``doc_total_per_ask_mean``.
But ``PassengerAircraftTotalCost`` -- the model that feeds the airfare, and through it
the price elasticity -- did not read either of them. A SAF subsidy therefore moved the
reported cost and left the fare, and hence demand, untouched: the policy instrument
most likely to be a market module's decision variable was invisible to the demand
response.

The two are not put in the same place. An energy tax joins the carbon tax and the
passenger tax in the extra-tax wedge; a subsidy gets its own category,
``total_subsidy_per_*``, and is subtracted. Both sit *outside*
``total_cost_per_*_without_extra_tax``, which is what
``PassengerAircraftMarginalCost`` anchors its supply-curve calibration on, so neither
can silently recalibrate ``a = 2(p0 - C0)/rpk_no_elasticity`` -- and both reach the
fare at full pass-through rather than being partly absorbed by the airline.

These tests pin: the wedge picks up the tax, the subsidy is its own subtracted
category, both survive the per-RPK conversion and the per-market split, the fare moves
by exactly the subsidy, the calibration series does not move, and a scenario with
neither is bit-for-bit what it was before.
"""

import pandas as pd
import pytest

from aeromaps.models.impacts.costs.airlines.total_airline_cost_and_airfare import (
    PassengerAircraftMarginalCost,
    PassengerAircraftTotalCost,
)

HISTORIC_START, PROSPECTION_START, END = 2000, 2020, 2050
LOAD_FACTOR = 80.0  # %, so per-RPK is per-ASK / 0.8


class _Parameters:
    """Minimal stand-in for the process parameters object a model needs to build ``df``."""

    climate_historic_start_year = 1940
    historic_start_year = HISTORIC_START
    prospection_start_year = PROSPECTION_START
    end_year = END


class _Market:
    def __init__(self, market_id):
        self.id = market_id


class _Markets:
    """Stand-in for the MarketManager injected before ``custom_setup``."""

    def __init__(self, ids):
        self._markets = [_Market(mid) for mid in ids]

    def get(self, traffic_type=None):
        return self._markets


MARKET_IDS = ["short_range", "long_range"]


def _series(value):
    return pd.Series(float(value), index=range(HISTORIC_START, END + 1))


def _total_cost(subsidy=0.0, energy_tax=0.0):
    model = PassengerAircraftTotalCost("passenger_aircraft_total_cost", parameters=_Parameters())
    model.markets = _Markets(MARKET_IDS)
    model.custom_setup()

    inputs = {
        "doc_non_energy_per_ask_mean": _series(0.030),
        "doc_energy_per_ask_mean": _series(0.020),
        "doc_carbon_tax_lowering_offset_per_ask_mean": _series(0.004),
        "doc_energy_tax_per_ask_mean": _series(energy_tax),
        "doc_energy_subsidy_per_ask_mean": _series(subsidy),
        "noc_carbon_offset_per_ask": _series(0.001),
        "non_operating_cost_per_ask": _series(0.005),
        "indirect_operating_cost_per_ask": _series(0.006),
        "passenger_tax_per_ask": _series(0.002),
        "operational_efficiency_cost_non_energy_per_ask": _series(0.0),
        "load_factor_cost_non_energy_per_ask": _series(0.0),
        "load_factor": _series(LOAD_FACTOR),
    }
    for mid in MARKET_IDS:
        inputs[f"doc_non_energy_per_ask_{mid}_mean"] = _series(0.030)
        inputs[f"doc_energy_per_ask_{mid}_mean"] = _series(0.020)
        inputs[f"doc_carbon_tax_lowering_offset_per_ask_{mid}_mean"] = _series(0.004)
        inputs[f"doc_energy_tax_per_ask_{mid}_mean"] = _series(energy_tax)
        inputs[f"doc_energy_subsidy_per_ask_{mid}_mean"] = _series(subsidy)
        inputs[f"load_factor_{mid}"] = _series(LOAD_FACTOR)

    return model.compute(inputs)


# --------------------------------------------------------------- the two categories


def test_an_energy_tax_joins_the_extra_tax_wedge():
    base = _total_cost()
    taxed = _total_cost(energy_tax=0.003)

    delta = taxed["total_extra_tax_per_ask"] - base["total_extra_tax_per_ask"]
    assert delta.to_numpy() == pytest.approx(0.003)
    assert taxed["total_subsidy_per_ask"].to_numpy() == pytest.approx(0.0)


def test_a_subsidy_is_its_own_category_and_is_subtracted():
    base = _total_cost()
    subsidised = _total_cost(subsidy=0.005)

    assert subsidised["total_subsidy_per_ask"].to_numpy() == pytest.approx(0.005)
    # It is NOT folded into the wedge: the wedge is unchanged.
    assert subsidised["total_extra_tax_per_ask"].to_numpy() == pytest.approx(
        base["total_extra_tax_per_ask"].to_numpy()
    )
    delta = subsidised["total_cost_per_ask"] - base["total_cost_per_ask"]
    assert delta.to_numpy() == pytest.approx(-0.005)


def test_neither_touches_the_supply_curve_calibration_series():
    """``*_without_extra_tax`` anchors ``a = 2(p0 - C0)/rpk_ne``. It must not move."""
    base = _total_cost()
    both = _total_cost(subsidy=0.005, energy_tax=0.003)

    for key in ("total_cost_per_ask_without_extra_tax", "total_cost_per_rpk_without_extra_tax"):
        assert both[key].to_numpy() == pytest.approx(base[key].to_numpy())


def test_both_survive_the_per_rpk_conversion():
    output = _total_cost(subsidy=0.005, energy_tax=0.003)

    assert output["total_subsidy_per_rpk"].to_numpy() == pytest.approx(0.005 / (LOAD_FACTOR / 100))
    expected_wedge = (0.004 + 0.002 + 0.003) / (LOAD_FACTOR / 100)
    assert output["total_extra_tax_per_rpk"].to_numpy() == pytest.approx(expected_wedge)


def test_the_per_market_split_gets_the_same_treatment():
    base = _total_cost()
    both = _total_cost(subsidy=0.005, energy_tax=0.003)

    for mid in MARKET_IDS:
        assert both[f"total_subsidy_per_ask_{mid}"].to_numpy() == pytest.approx(0.005)
        assert both[f"total_subsidy_per_rpk_{mid}"].to_numpy() == pytest.approx(
            0.005 / (LOAD_FACTOR / 100)
        )
        wedge = both[f"total_extra_tax_per_ask_{mid}"] - base[f"total_extra_tax_per_ask_{mid}"]
        assert wedge.to_numpy() == pytest.approx(0.003)
        cost = both[f"total_cost_per_ask_{mid}"] - base[f"total_cost_per_ask_{mid}"]
        assert cost.to_numpy() == pytest.approx(0.003 - 0.005)


def test_a_scenario_with_neither_is_unchanged():
    """The regression guard: no subsidy and no energy tax must reproduce the old totals."""
    output = _total_cost()

    per_ask = 0.030 + 0.020 + 0.005 + 0.006 + 0.001  # the without-extra-tax terms
    wedge = 0.004 + 0.002
    assert output["total_cost_per_ask_without_extra_tax"].to_numpy() == pytest.approx(per_ask)
    assert output["total_extra_tax_per_ask"].to_numpy() == pytest.approx(wedge)
    assert output["total_cost_per_ask"].to_numpy() == pytest.approx(per_ask + wedge)
    assert output["total_subsidy_per_ask"].to_numpy() == pytest.approx(0.0)


# ------------------------------------------------------------------------ the fare


def _airfare(subsidy_per_rpk):
    model = PassengerAircraftMarginalCost(
        "passenger_aircraft_marginal_cost", parameters=_Parameters()
    )
    _, _, airfare = model.compute(
        rpk=_series(1.0e12),
        rpk_no_elasticity=_series(1.0e12),
        total_cost_per_rpk_without_extra_tax=_series(0.0775),
        total_extra_tax_per_rpk=_series(0.0075),
        total_subsidy_per_rpk=_series(subsidy_per_rpk),
    )
    return airfare


def test_a_subsidy_moves_the_fare_by_exactly_the_subsidy():
    """The point of the whole fix: without this the elasticity never sees the policy."""
    base = _airfare(0.0)
    subsidised = _airfare(0.00625)

    projected = slice(PROSPECTION_START, END)
    delta = subsidised.loc[projected] - base.loc[projected]
    assert delta.to_numpy() == pytest.approx(-0.00625)


def test_the_fare_subsidy_is_full_pass_through_not_partly_absorbed():
    """The subsidy is applied on top of the supply function, so none of it is absorbed.

    A shift of the same size applied to the *cost* instead is damped by the ``a*rpk``
    term, so the two are measurably different -- which is why the placement matters.
    """
    base = _airfare(0.0)
    subsidised = _airfare(0.01)

    model = PassengerAircraftMarginalCost(
        "passenger_aircraft_marginal_cost", parameters=_Parameters()
    )
    _, _, cost_shifted = model.compute(
        rpk=_series(1.0e12),
        rpk_no_elasticity=_series(1.0e12),
        total_cost_per_rpk_without_extra_tax=_series(0.0775 - 0.01),
        total_extra_tax_per_rpk=_series(0.0075),
        total_subsidy_per_rpk=_series(0.0),
    )

    projected = slice(PROSPECTION_START, END)
    via_subsidy = (subsidised.loc[projected] - base.loc[projected]).abs().mean()
    via_cost = (cost_shifted.loc[projected] - base.loc[projected]).abs().mean()

    assert via_subsidy == pytest.approx(0.01)
    # The cost route also moves C0, which re-anchors the curve; it is not 1:1.
    assert via_cost != pytest.approx(0.01, abs=1e-6)

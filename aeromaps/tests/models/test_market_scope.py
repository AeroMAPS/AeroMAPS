"""Enforce the ``MARKET_SCOPE`` taxonomy (market-axis granularity of disciplines).

Every AeroMAPS discipline declares, at the class level, how it relates to the
market dimension via :attr:`AeroMAPSModel.MARKET_SCOPE` — the single source of
truth for the *per-market / cross-market / aggregator / market-agnostic*
distinction (the *region* axis is orthogonal, applied uniformly by namespacing).

These tests keep that declaration honest:

* the full market-family topology is pinned in one readable table (``EXPECTED_SCOPE``);
* every declared scope is a valid value;
* every ``per_market`` discipline actually carries its market id in its I/O names;
* a real process exposes all four scopes, so the annotations reach live disciplines.
"""

from pathlib import Path

import pytest

from aeromaps import create_process
from aeromaps.models.base import AeroMAPSModel, MARKET_SCOPES

from aeromaps.models.air_transport.air_traffic.ask_market import ASKAggregator, ASKMarket
from aeromaps.models.air_transport.air_traffic.rpk_market import (
    RPKAggregator,
    RPKElasticity,
    RPKMarket,
    RPKMeasuresMarket,
    RPKReferenceMarket,
)
from aeromaps.models.air_transport.air_traffic.rtk_market import (
    RTKAggregator,
    RTKMarket,
    RTKReferenceMarket,
)
from aeromaps.models.air_transport.air_traffic.price_and_income_elasticity import (
    RPKPriceIncomeElasticity,
)
from aeromaps.models.air_transport.air_traffic.price_elasticity_logistic_income import (
    RPKLogisticIncomePriceElasticity,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.load_factor.load_factor import (
    LoadFactorAggregator,
    LoadFactorMarket,
    LoadFactorMarketSimpleInterpolation,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.aircraft_efficiency import (
    FreightAircraftEfficiency,
    FreightAircraftEfficiencySimple,
    PassengerAircraftEfficiencyComplex,
    PassengerAircraftEfficiencySimpleASK,
    PassengerAircraftEfficiencySimpleShares,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model import (
    FleetModel,
)

CONFIG_DIR = Path(__file__).parent.parent / "tested_configs"

# The full market-axis topology, in one place. Editing a discipline's scope here
# and in the class is the deliberate two-step that flags a topology change in review.
EXPECTED_SCOPE = {
    ASKMarket: "per_market",
    ASKAggregator: "aggregator",
    RPKMarket: "per_market",
    RPKMeasuresMarket: "per_market",
    RPKReferenceMarket: "per_market",
    RPKAggregator: "aggregator",
    RPKElasticity: "cross_market",
    RPKPriceIncomeElasticity: "cross_market",
    RPKLogisticIncomePriceElasticity: "cross_market",
    RTKMarket: "per_market",
    RTKReferenceMarket: "per_market",
    RTKAggregator: "aggregator",
    LoadFactorMarket: "per_market",
    LoadFactorMarketSimpleInterpolation: "per_market",
    LoadFactorAggregator: "aggregator",
    PassengerAircraftEfficiencySimpleShares: "cross_market",
    PassengerAircraftEfficiencySimpleASK: "cross_market",
    PassengerAircraftEfficiencyComplex: "cross_market",
    FreightAircraftEfficiency: "cross_market",
    FreightAircraftEfficiencySimple: "cross_market",
    FleetModel: "cross_market",
}

# per_market classes constructed as ``Cls(name, market_id)``.
PER_MARKET_CTORS = [
    ASKMarket,
    RPKMarket,
    RPKMeasuresMarket,
    RPKReferenceMarket,
    RTKMarket,
    RTKReferenceMarket,
    LoadFactorMarket,
    LoadFactorMarketSimpleInterpolation,
]


def test_base_default_scope_is_market_agnostic():
    assert AeroMAPSModel.MARKET_SCOPE == "market_agnostic"
    assert AeroMAPSModel.MARKET_SCOPE in MARKET_SCOPES


@pytest.mark.parametrize(
    "cls,scope", list(EXPECTED_SCOPE.items()), ids=[c.__name__ for c in EXPECTED_SCOPE]
)
def test_declared_scope_matches_expected_and_is_valid(cls, scope):
    assert (
        cls.MARKET_SCOPE in MARKET_SCOPES
    ), f"{cls.__name__} declares an unknown MARKET_SCOPE {cls.MARKET_SCOPE!r}"
    assert cls.MARKET_SCOPE == scope, (
        f"{cls.__name__} MARKET_SCOPE changed to {cls.MARKET_SCOPE!r}; expected {scope!r}. "
        "If this is intentional, update EXPECTED_SCOPE (topology change — flag it in review)."
    )


@pytest.mark.parametrize("cls", PER_MARKET_CTORS, ids=[c.__name__ for c in PER_MARKET_CTORS])
def test_per_market_disciplines_carry_market_id_token(cls):
    """A per_market discipline must namespace every instance by its market id."""
    mid = "test_market"
    model = cls(name=f"{cls.__name__.lower()}_x", market_id=mid)
    assert model.MARKET_SCOPE == "per_market"
    names = list(model.input_names) + list(model.output_names)
    assert any(mid in n for n in names), (
        f"{cls.__name__} is declared per_market but no I/O name carries the market id "
        f"{mid!r}: {names}"
    )


def test_demand_process_exposes_all_market_scopes():
    """A real price-coupled demand process must contain live disciplines of every
    market-family scope, proving the class-level annotations reach the MDA."""
    proc = create_process(configuration_file=str(CONFIG_DIR / "config_elasticity_demand.yaml"))
    seen = {}
    for discipline in proc.disciplines:
        model = getattr(discipline, "model", None)
        if model is None:
            continue
        scope = getattr(model, "MARKET_SCOPE", None)
        assert (
            scope in MARKET_SCOPES
        ), f"{type(model).__name__} declares invalid MARKET_SCOPE {scope!r}"
        seen.setdefault(scope, type(model).__name__)
    for expected in ("per_market", "cross_market", "aggregator", "market_agnostic"):
        assert (
            expected in seen
        ), f"no {expected!r} discipline found in the demand process; saw {seen}"

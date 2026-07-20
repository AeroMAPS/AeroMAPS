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
from aeromaps.models.base import AeroMAPSModel, MARKET_SCOPES, MODEL_APPROACHES

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
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet_push.aircraft_efficiency_fleet_push import (
    PassengerAircraftEfficiencyFleetPush,
)
from aeromaps.models.impacts.costs.airlines.direct_operating_costs import (
    PassengerAircraftDocNonEnergyComplex,
    PassengerAircraftDocNonEnergySimple,
)
from aeromaps.models.impacts.emissions.non_co2_emissions import (
    NOxEmissionIndexComplex,
    SootEmissionIndexComplex,
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


# Modelling approach per discipline — only classes *exclusive* to one side of a
# top-down/bottom-up family declare it; approach-agnostic models stay None.
EXPECTED_APPROACH = {
    PassengerAircraftEfficiencySimpleShares: "top_down",
    PassengerAircraftDocNonEnergySimple: "top_down",
    PassengerAircraftEfficiencyComplex: "bottom_up",
    PassengerAircraftEfficiencyFleetPush: "bottom_up",
    PassengerAircraftDocNonEnergyComplex: "bottom_up",
    NOxEmissionIndexComplex: "bottom_up",
    SootEmissionIndexComplex: "bottom_up",
    FleetModel: "bottom_up",
}

# Approach-agnostic disciplines: shared across both wirings, or outside the split
# (demand, traffic, load factor). These must stay None.
APPROACH_AGNOSTIC = [
    FreightAircraftEfficiency,  # used in both top_down and bottom_up efficiency groups
    PassengerAircraftEfficiencySimpleASK,  # shared (top_down + push)
    RPKMarket,
    RPKPriceIncomeElasticity,
    LoadFactorMarket,
]


def test_base_default_scope_is_market_agnostic():
    assert AeroMAPSModel.MARKET_SCOPE == "market_agnostic"
    assert AeroMAPSModel.MARKET_SCOPE in MARKET_SCOPES


def test_base_default_approach_is_none():
    assert AeroMAPSModel.MODEL_APPROACH is None


@pytest.mark.parametrize(
    "cls,approach", list(EXPECTED_APPROACH.items()), ids=[c.__name__ for c in EXPECTED_APPROACH]
)
def test_declared_approach_matches_and_is_valid(cls, approach):
    assert (
        cls.MODEL_APPROACH in MODEL_APPROACHES
    ), f"{cls.__name__} declares an unknown MODEL_APPROACH {cls.MODEL_APPROACH!r}"
    assert (
        cls.MODEL_APPROACH == approach
    ), f"{cls.__name__} MODEL_APPROACH is {cls.MODEL_APPROACH!r}; expected {approach!r}"


@pytest.mark.parametrize("cls", APPROACH_AGNOSTIC, ids=[c.__name__ for c in APPROACH_AGNOSTIC])
def test_approach_agnostic_disciplines_declare_none(cls):
    assert cls.MODEL_APPROACH is None, (
        f"{cls.__name__} is shared/outside the top-down/bottom-up split and must stay "
        f"MODEL_APPROACH=None, got {cls.MODEL_APPROACH!r}"
    )


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


def test_describe_models_summary_and_filter():
    """describe_models renders the scope summary and honours the scope filter."""
    proc = create_process(configuration_file=str(CONFIG_DIR / "config_elasticity_demand.yaml"))

    out = proc.describe_models(display=False)
    assert "Market scope summary" in out
    for scope in ("per_market", "cross_market", "aggregator", "market_agnostic"):
        assert scope in out
    # market_agnostic disciplines are hidden from the table by default
    assert "hidden" in out
    # enriched columns: coupling role (derived) and modelling approach
    assert "COUPLING" in out and "APPROACH" in out
    assert "in MDA feedback loop" in out
    assert "loop" in out and "feed-fwd" in out
    assert "top_down" in out or "bottom_up" in out  # an approach-tagged discipline is listed

    cross = proc.describe_models(scope="cross_market", display=False)
    assert "RPKPriceIncomeElasticity" in cross  # a cross_market discipline is listed
    assert "ASKMarket" not in cross  # per_market disciplines are filtered out
    assert "ASKAggregator" not in cross  # aggregator disciplines are filtered out

    with pytest.raises(ValueError):
        proc.describe_models(scope="not_a_scope", display=False)

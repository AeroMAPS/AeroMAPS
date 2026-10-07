"""``SocioeconomicDrivers`` travels with the demand models that need it.

Both price-coupled demand models declare ``population`` and ``gdp_per_capita`` as
inputs, and nothing else in the package produces them, so the driver is built
alongside them by ``create_market_rpk_demand_model``.

It is deliberately *not* in ``models_traffic``: no defaults for the reference-year
inputs ship in ``parameters.json``, so a CAGR scenario that acquired this model
would start failing on inputs it has no reason to declare. The second test is the
guard on that.
"""

import pytest

from aeromaps.models.air_transport.air_traffic.socioeconomic_drivers import SocioeconomicDrivers
from aeromaps.models.air_transport.markets.markets_factory import (
    create_market_rpk_demand_model,
    create_market_rpk_models,
)


class _Market:
    def __init__(self, market_id):
        self.id = market_id
        self.traffic_type = "passenger"


class _Registry:
    def __init__(self, markets):
        self._markets = markets

    def get(self, **criteria):
        return [
            m for m in self._markets if all(getattr(m, k, None) == v for k, v in criteria.items())
        ]


@pytest.fixture
def markets():
    return _Registry([_Market("short_range")])


@pytest.mark.parametrize("demand_model", ["constant_elasticity", "logistic_income"])
def test_demand_models_bring_the_driver(markets, demand_model):
    models = create_market_rpk_demand_model(markets, {}, demand_model=demand_model)
    assert "socioeconomic_drivers" in models
    assert isinstance(models["socioeconomic_drivers"], SocioeconomicDrivers)


def test_the_cagr_chain_does_not(markets):
    """The default chain has no use for the drivers and must not acquire them."""
    models = create_market_rpk_models(markets, {})
    assert not any("socioeconomic" in name for name in models)


def test_unknown_demand_model_is_rejected(markets):
    with pytest.raises(ValueError, match="Unknown demand model"):
        create_market_rpk_demand_model(markets, {}, demand_model="nonsense")


def test_driver_declares_the_reference_year_inputs():
    """Its I/O is derived from ``compute``'s signature, which is the contract with
    the configuration: these are the four parameters a coupled scenario must set,
    and the reason the driver cannot be loaded for every scenario by default."""
    import inspect

    parameters = set(inspect.signature(SocioeconomicDrivers.compute).parameters)
    assert {
        "population_reference_years",
        "population_reference_years_values",
        "gdp_per_capita_reference_years",
        "gdp_per_capita_reference_years_values",
    } <= parameters

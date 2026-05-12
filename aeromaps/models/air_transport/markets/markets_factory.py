"""Factory helpers to instantiate market-driven traffic models."""

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
from aeromaps.models.air_transport.aircraft_fleet_and_operations.load_factor.load_factor import (
    LoadFactorAggregator,
    LoadFactorMarket,
)


def _has_measures_inputs(market_inputs: dict) -> bool:
    """True when the market YAML has a 'measures' sub-group (keys are already flattened)."""
    return isinstance(market_inputs, dict) and "measures" in market_inputs


def _has_reference_inputs(market_inputs: dict) -> bool:
    """True when the market YAML has a 'reference' sub-group for per-market reference CAGR."""
    return isinstance(market_inputs, dict) and "reference" in market_inputs


def create_market_rpk_models(
    markets, markets_data: dict = None, with_elasticity: bool = False
) -> dict:
    """Create per-market RPK models from the market registry and raw YAML data.

    Always creates one ``RPKMarket`` per passenger market.
    Creates ``RPKMeasuresMarket`` only when measures inputs are present.
    Creates ``RPKReferenceMarket`` only when reference inputs are present.

    When ``with_elasticity`` is True, ``RPKMarket`` outputs are suffixed with
    ``_no_elasticity`` so a downstream ``RPKElasticity`` can own the unsuffixed
    ``rpk_<mid>`` name.
    """
    models = {}
    if markets is None:
        return models

    markets_data = markets_data or {}
    suffix = "_no_elasticity" if with_elasticity else ""

    for market in markets.get(traffic_type="passenger"):
        mid = market.id
        market_inputs = markets_data.get(mid, {}).get("inputs", {})

        rpk_name = f"rpk_{mid}"
        models[rpk_name] = RPKMarket(name=rpk_name, market_id=mid, output_suffix=suffix)

        if _has_measures_inputs(market_inputs):
            measures_name = f"rpk_measures_{mid}"
            models[measures_name] = RPKMeasuresMarket(name=measures_name, market_id=mid)

        if _has_reference_inputs(market_inputs):
            reference_name = f"rpk_reference_{mid}"
            models[reference_name] = RPKReferenceMarket(name=reference_name, market_id=mid)

    return models


def create_market_rpk_aggregator(markets, with_elasticity: bool = False) -> dict:
    """Create an RPKAggregator that sums per-market rpk into the total ``rpk``.

    When ``with_elasticity`` is True, the aggregator consumes / emits names with
    a ``_no_elasticity`` suffix so a downstream ``RPKElasticity`` discipline can
    own the unsuffixed names.

    Returns an empty mapping when no markets registry is available.
    """
    if markets is None:
        return {}
    passenger_ids = [m.id for m in markets.get(traffic_type="passenger")]
    if not passenger_ids:
        return {}
    suffix = "_no_elasticity" if with_elasticity else ""
    model = RPKAggregator(
        name="rpk_aggregator",
        passenger_market_ids=passenger_ids,
        output_suffix=suffix,
    )
    return {"rpk_aggregator": model}


def create_market_rpk_elasticity(markets) -> dict:
    """Create the global ``RPKElasticity`` discipline for cost-feedback mode.

    Returns an empty mapping when no passenger markets are configured.
    """
    if markets is None:
        return {}
    passenger_ids = [m.id for m in markets.get(traffic_type="passenger")]
    if not passenger_ids:
        return {}
    return {
        "rpk_elasticity": RPKElasticity(name="rpk_elasticity", passenger_market_ids=passenger_ids)
    }


def create_market_ask_models(markets) -> dict:
    """Create per-market ASKMarket models and one ASKAggregator.

    Returns an empty mapping when no markets registry is available.
    """
    if markets is None:
        return {}
    passenger_ids = [m.id for m in markets.get(traffic_type="passenger")]
    if not passenger_ids:
        return {}
    models = {}
    for mid in passenger_ids:
        ask_name = f"ask_{mid}"
        models[ask_name] = ASKMarket(name=ask_name, market_id=mid)
    models["ask_aggregator"] = ASKAggregator(
        name="ask_aggregator", passenger_market_ids=passenger_ids
    )
    return models


def create_market_load_factor_models(markets) -> dict:
    """Create per-market LoadFactorMarket models and one LoadFactorAggregator.

    Always creates one ``LoadFactorMarket`` per passenger market (load_factor
    inputs are guaranteed by the ``defaults.passenger`` block in markets.yaml).
    The aggregator recombines per-market load factors into the global
    ``load_factor`` consumed by downstream disciplines.

    Returns an empty mapping when no passenger markets are configured.
    """
    if markets is None:
        return {}
    passenger_ids = [m.id for m in markets.get(traffic_type="passenger")]
    if not passenger_ids:
        return {}
    models = {}
    for mid in passenger_ids:
        lf_name = f"load_factor_{mid}"
        models[lf_name] = LoadFactorMarket(name=lf_name, market_id=mid)
    models["load_factor_aggregator"] = LoadFactorAggregator(name="load_factor_aggregator")
    return models


def create_market_rtk_models(markets, markets_data: dict = None) -> dict:
    """Create per-market RTK models for all freight markets.

    Always creates one ``RTKMarket`` per freight market.
    Creates ``RTKReferenceMarket`` only when a ``reference`` sub-group is
    present in the freight market's inputs.

    Returns an empty mapping when no freight market is configured.
    """
    models = {}
    if markets is None:
        return models

    freight_markets = markets.get(traffic_type="freight")
    if not freight_markets:
        return models

    markets_data = markets_data or {}

    for market in freight_markets:
        mid = market.id
        model_name = f"rtk_{mid}"
        models[model_name] = RTKMarket(name=model_name, market_id=mid)

        market_inputs = markets_data.get(mid, {}).get("inputs", {})
        if _has_reference_inputs(market_inputs):
            ref_name = f"rtk_reference_{mid}"
            models[ref_name] = RTKReferenceMarket(name=ref_name, market_id=mid)

    return models


def create_market_rtk_aggregator(markets) -> dict:
    """Create an RTKAggregator that sums per-market rtk into the total ``rtk``.

    Returns an empty mapping when no freight markets are configured.
    """
    if markets is None:
        return {}
    freight_ids = [m.id for m in markets.get(traffic_type="freight")]
    if not freight_ids:
        return {}
    model = RTKAggregator(name="rtk_aggregator", freight_market_ids=freight_ids)
    return {"rtk_aggregator": model}

"""Factory helpers to instantiate market-driven traffic models."""

from aeromaps.models.air_transport.air_traffic.rpk_market import (
    RPKMarket,
    RPKMeasuresMarket,
    RPKReferenceMarket,
)
from aeromaps.models.air_transport.air_traffic.rtk_market import RTKMarket


def _has_measures_inputs(market_inputs: dict) -> bool:
    measures = market_inputs.get("measures", {}) if isinstance(market_inputs, dict) else {}
    return all(
        key in measures
        for key in (
            "measures_final_impact",
            "measures_start_year",
            "measures_duration",
        )
    )


def _has_reference_inputs(market_inputs: dict) -> bool:
    reference = market_inputs.get("reference", {}) if isinstance(market_inputs, dict) else {}
    return all(
        key in reference
        for key in (
            "reference_cagr_reference_periods",
            "reference_cagr_reference_periods_values",
        )
    )


def create_market_rpk_models(markets, markets_data: dict = None) -> dict:
    """Create per-market RPK models from the market registry and raw YAML data.

    Always creates one ``RPKMarket`` per passenger market.
    Creates ``RPKMeasuresMarket`` only when measures inputs are present.
    Creates ``RPKReferenceMarket`` only when reference inputs are present.
    """
    models = {}
    if markets is None:
        return models

    markets_data = markets_data or {}

    for market in markets.get(traffic_type="passenger"):
        mid = market.id
        market_inputs = markets_data.get(mid, {}).get("inputs", {})

        rpk_name = f"rpk_{mid}"
        models[rpk_name] = RPKMarket(name=rpk_name, market_id=mid)

        if _has_measures_inputs(market_inputs):
            measures_name = f"rpk_measures_{mid}"
            models[measures_name] = RPKMeasuresMarket(name=measures_name, market_id=mid)

        if _has_reference_inputs(market_inputs):
            reference_name = f"rpk_reference_{mid}"
            models[reference_name] = RPKReferenceMarket(name=reference_name, market_id=mid)

    return models


def create_market_rtk_models(markets) -> dict:
    """Create market-driven RTK model for freight.

    Returns an empty mapping when no freight market is configured.
    Raises when multiple freight markets are configured, as the current
    RTKMarket implementation is intentionally single-market.
    """
    models = {}
    if markets is None:
        return models

    freight_markets = markets.get(traffic_type="freight")
    if len(freight_markets) == 0:
        return models
    if len(freight_markets) > 1:
        raise ValueError("Only one freight market is currently supported for RTK market mode.")

    market = freight_markets[0]
    model_name = f"rtk_{market.id}"
    models[model_name] = RTKMarket(name=model_name, market_id=market.id)
    return models

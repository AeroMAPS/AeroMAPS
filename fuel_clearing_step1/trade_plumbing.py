"""Does the plumbing carry fuel between regions? Explicit flows, checked end to end.

Usage::

    poetry run python -m fuel_clearing_step1.trade_plumbing

**The question.** Not what the flows should be -- the market will say that later -- but
whether the multi-regional process can carry them at all: a region producing what it does
not burn, the production reaching the models that belong to it, and every MJ accounted
for exactly once. The flows are set by hand, as an explicit sourcing matrix
(``scenario/regionalisation_trade.yaml``): all of region B's HEFA is made in A, and a
quarter of A's kerosene is made in B.

**Four runs**, full two-region MDA, five pathways: the standard mode (``EnergyUseChoice``
in each region) and the market mode (``FuelClearing``, nothing scarce), each without and
with trade. Trade changes where fuel is made and nothing else, so each pair must agree on
everything a consumer sees, and differ exactly as the matrix says on everything a producer
sees.
"""

from __future__ import annotations

import json
import logging
import time
import warnings
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
TRADE_CONFIG = HERE / "scenario" / "regionalisation_trade.yaml"
RESULTS = HERE / "trade_plumbing.json"

REGIONS = ("region_A", "region_B")
PROSPECTIVE = slice(2020, 2050)
HISTORICAL = slice(None, 2019)
PATHWAYS = ("fossil_kerosene", "hefa_fog", "ft_msw", "atj", "electrofuel")
# What a consumer sees. Trade must leave every one of these untouched.
CONSUMER_SIDE = (
    "energy_consumption_dropin_fuel",
    "co2_emissions_passenger",
    "co2_emissions_freight",
    "cumulative_co2_emissions",
    "airfare_per_rpk",
    "rpk",
    "dropin_fuel_mean_mfsp",
    *(f"{p}_energy_consumption" for p in PATHWAYS),
    *(f"{p}_total_co2_emissions" for p in PATHWAYS),
)
# hefa_fog's one feedstock and its specific consumption, energy_carriers_five.yaml.
FEEDSTOCK, SPECIFIC = "hefa_fog_biomass", 1.14


def _config(trade: bool, market: bool) -> dict:
    config = yaml.safe_load(TRADE_CONFIG.read_text())
    block = config["regionalisation"]
    block["fuel_trade"] = "matrix" if trade else None
    block["fuel_market"] = market
    standards, settings = [], {}
    if market:
        standards.append("models_fuel_market")
    if trade:
        standards.append("models_fuel_trade")
        settings["fuel_trade"] = block["global_models"]["settings"]["fuel_trade"]
    block["global_models"] = {"standards": standards, "settings": settings} if standards else {}
    if not trade:
        # Production exists only with trade; without it there is nothing to sum.
        block["aggregation"]["sum"] = [
            name for name in block["aggregation"]["sum"] if not name.endswith("_energy_production")
        ]
    return config


def _run(tag, trade, market):
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    target = TRADE_CONFIG.parent / f"_trade_{tag}.yaml"
    target.write_text(yaml.safe_dump(_config(trade, market)))
    try:
        started = time.perf_counter()
        process = MultiRegionalProcess(str(target))
        process.compute()
        elapsed = time.perf_counter() - started
    finally:
        target.unlink(missing_ok=True)
    return process, elapsed


def _worst_relative(a, b):
    """Largest |a - b| / max|b| over the columns given; 0 when both are all zero or NaN."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    both = np.isfinite(a) & np.isfinite(b)
    if np.any(np.isfinite(a) != np.isfinite(b)):
        return np.inf
    scale = np.max(np.abs(b[both])) if both.any() else 0.0
    if scale == 0.0:
        return float(np.max(np.abs(a[both]))) if both.any() else 0.0
    return float(np.max(np.abs(a[both] - b[both])) / scale)


def _checks(base, trade, sourcing):
    """Every identity the matrix implies, as ``{name: worst relative error}``."""
    b, t = base.data["vector_outputs"], trade.data["vector_outputs"]
    out = {}

    # 1. The consumer side does not move. Every region, every series a consumer sees --
    #    and a series that is not there is an error, not a skip: an earlier draft filtered
    #    missing names out and compared 28 of 30 without saying so.
    missing = [f"{r}:{n}" for r in REGIONS for n in CONSUMER_SIDE if f"{r}:{n}" not in b]
    if missing:
        raise KeyError(f"consumer-side series not in the outputs: {missing}")
    out["consumer side unchanged"] = max(
        _worst_relative(t[f"{r}:{name}"], b[f"{r}:{name}"])
        for r in REGIONS
        for name in CONSUMER_SIDE
    )

    # 2. Production is what the matrix says: each region makes its share of every
    #    region's consumption. Prospective years.
    worst = 0.0
    for pathway in PATHWAYS:
        rows = sourcing.get(pathway, {})
        for producer in REGIONS:
            expected = 0.0
            for consumer in REGIONS:
                row = rows.get(consumer, {consumer: 1.0})
                share = float(row.get(producer, 0.0))
                expected = expected + share * t[f"{consumer}:{pathway}_energy_consumption"].loc[
                    PROSPECTIVE
                ].fillna(0.0)
            got = t[f"{producer}:{pathway}_energy_production"].loc[PROSPECTIVE].fillna(0.0)
            worst = max(worst, _worst_relative(got, expected))
    out["production follows the matrix"] = worst

    # 3. Nothing created or lost: world production = world consumption, per pathway and
    #    year -- summed here, and through the aggregator.
    out["world production = world consumption"] = max(
        _worst_relative(
            sum(t[f"{r}:{p}_energy_production"].fillna(0.0) for r in REGIONS),
            sum(t[f"{r}:{p}_energy_consumption"].fillna(0.0) for r in REGIONS),
        )
        for p in PATHWAYS
    )
    out["... and through the aggregator"] = max(
        _worst_relative(
            t[f"overall:{p}_energy_production"].fillna(0.0),
            t[f"overall:{p}_energy_consumption"].fillna(0.0),
        )
        for p in ("hefa_fog", "fossil_kerosene")
    )

    # 4. The tracked flows add up to the net positions.
    worst = 0.0
    for pathway in sourcing:
        for r in REGIONS:
            other = next(o for o in REGIONS if o != r)
            out_flow = t[f"overall:{pathway}_energy_flow_{r}_to_{other}"]
            in_flow = t[f"overall:{pathway}_energy_flow_{other}_to_{r}"]
            worst = max(
                worst, _worst_relative(out_flow - in_flow, t[f"{r}:{pathway}_energy_net_export"])
            )
    out["flows add up to net exports"] = worst

    # 5. Feedstock follows production; the world total does not move.
    out["feedstock = specific use x production"] = max(
        _worst_relative(
            t[f"{r}:{FEEDSTOCK}_total_consumption"].loc[PROSPECTIVE],
            SPECIFIC * t[f"{r}:hefa_fog_energy_production"].loc[PROSPECTIVE].fillna(0.0),
        )
        for r in REGIONS
    )
    out["world feedstock unchanged"] = _worst_relative(
        t[f"overall:{FEEDSTOCK}_total_consumption"], b[f"overall:{FEEDSTOCK}_total_consumption"]
    )

    # 6. No trade in the historical years: there production is consumption.
    out["historical: production = consumption"] = max(
        _worst_relative(
            t[f"{r}:{p}_energy_production"].loc[HISTORICAL],
            t[f"{r}:{p}_energy_consumption"].loc[HISTORICAL],
        )
        for r in REGIONS
        for p in PATHWAYS
    )
    return out


def _snapshot(process):
    v = process.data["vector_outputs"]
    years = (2030, 2040, 2050)
    keep = {}
    for r in REGIONS:
        for name in (
            "hefa_fog_energy_consumption",
            "hefa_fog_energy_production",
            "hefa_fog_energy_net_export",
            "fossil_kerosene_energy_consumption",
            "fossil_kerosene_energy_production",
            f"{FEEDSTOCK}_total_consumption",
            f"{FEEDSTOCK}_consumed_global_share",
            "co2_emissions_passenger",
        ):
            key = f"{r}:{name}"
            if key in v:
                keep[key] = {y: float(v[key].loc[y]) for y in years}
    for key in v.columns:
        if key.startswith("overall:") and "_energy_flow_" in key:
            keep[key] = {y: float(v[key].loc[y]) for y in years}
    return keep


def run():
    warnings.resetwarnings()
    warnings.simplefilter("ignore")
    logging.disable(logging.INFO)
    sourcing = yaml.safe_load(TRADE_CONFIG.read_text())["regionalisation"]["global_models"][
        "settings"
    ]["fuel_trade"]["sourcing"]

    results = {}
    for mode, market in (("standard", False), ("market", True)):
        base, base_seconds = _run(f"{mode}_base", trade=False, market=market)
        trade, trade_seconds = _run(f"{mode}_trade", trade=True, market=market)
        checks = _checks(base, trade, sourcing)
        results[mode] = {
            "seconds": {"without trade": base_seconds, "with trade": trade_seconds},
            "iterations": {
                "without trade": len(base.mda_chain.inner_mdas[0].residual_history)
                if base.mda_chain.inner_mdas
                else 0,
                "with trade": len(trade.mda_chain.inner_mdas[0].residual_history)
                if trade.mda_chain.inner_mdas
                else 0,
            },
            "checks": checks,
            "with trade": _snapshot(trade),
            "without trade": _snapshot(base),
        }
        print(f"== {mode} mode  ({base_seconds:.1f} s without trade, {trade_seconds:.1f} s with)")
        for name, value in checks.items():
            print(f"   {name:40s} {value:.2e}")
    RESULTS.write_text(json.dumps(results, indent=1))
    return results


if __name__ == "__main__":
    run()

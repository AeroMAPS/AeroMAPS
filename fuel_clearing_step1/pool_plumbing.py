"""Does the plumbing carry a pooled fuel market? The market's stand-in, checked end to end.

Usage::

    poetry run python -m fuel_clearing_step1.pool_plumbing

**The question.** Not what a market would decide -- that comes later -- but whether the
multi-regional process can run one: every region burning fuel made anywhere, production
uncoupled from consumption, each side reaching the models it belongs to, and every MJ,
gram of CO2 and euro accounted for exactly once. The stand-in is the simplest rule that
exercises all of it (``regionalisation.fuel_trade: pool``): each region offers volumes, a
pathway's offers form one world pool, and each region burns a slice of every pool in
proportion to its share of world drop-in demand.

**Five runs**, full two-region MDA, five pathways, on the asymmetric bench of
``scenario/regionalisation_pool.yaml`` (A offers a lot on a clean grid and taxes carbon at
100 EUR/t; B offers little on a dirty grid at 5 EUR/t):

``autarky``
    No trade. Each region burns exactly what it offers, through the standard mode's
    ``EnergyUseChoice`` with quantity mandates equal to the offers -- the reference.
``pool``
    The same offers, pooled.
``oversupply``
    The pool with every offer x3.5, so that from the mid-2040s the world is offered more
    than it burns and part of every offer goes unused.
``eligibility``
    The pool with one eligibility rule, ``scenario/regionalisation_pool_eligibility.yaml``:
    region A may not burn waste-oil HEFA, of which it makes most.
``eligibility_oversupply``
    Both: offers x3.5 and A barred from HEFA, so that B, HEFA's only taker, fills up and
    the cap-and-return step of the rule is exercised.

Production is the same in ``autarky`` and ``pool`` -- the offers, all used -- so feedstock,
region by region, must not move; consumption is what moves. Writes ``pool_plumbing.json``
(checks and the series the artifact draws) and ``figures/pool_plumbing.png``.
"""

from __future__ import annotations

import json
import logging
import re
import time
import warnings
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
SCENARIO = HERE / "scenario"
POOL_CONFIG = SCENARIO / "regionalisation_pool.yaml"
ELIGIBILITY_CONFIG = SCENARIO / "regionalisation_pool_eligibility.yaml"
# The one rule of the eligibility runs: region A may not burn this pathway.
EXCLUDED = ("region_A", "hefa_fog")
RESULTS = HERE / "pool_plumbing.json"
FIGURE = HERE / "figures" / "pool_plumbing.png"

REGIONS = ("region_A", "region_B")
POOLED = ("hefa_fog", "ft_msw", "atj", "electrofuel")
PATHWAYS = (*POOLED, "fossil_kerosene")
RESIDUAL = "fossil_kerosene"
PROSPECTIVE = slice(2020, 2050)
HISTORICAL = slice(None, 2019)
YEARS = list(range(2020, 2051))
OVERSUPPLY = 3.5
# Each pathway's one feedstock and its specific consumption (MJ per MJ of fuel),
# region_*/energy_carriers_pool.yaml.
FEEDSTOCK = {
    "hefa_fog": ("hefa_fog_biomass", 1.14),
    "ft_msw": ("ft_msw_biomass", 2.17),
    "atj": ("atj_biomass", 2.08),
    "electrofuel": ("grid_electricity", 2.32),
}


# -- scenario variants -----------------------------------------------------------------


def _carriers_variant(text, variant):
    """A region's pool carriers file, as the autarky reference or with offers scaled."""
    if variant == "pool":
        return text
    if variant == "autarky":
        # The offer becomes the region's own quantity mandate: it burns what it makes.
        return text.replace(
            "    supply:\n      energy_offered:",
            '    mandate:\n      mandate_type: "quantity"\n      mandate_quantity:',
        )

    def scale(match):
        values = [float(v) * OVERSUPPLY for v in match.group(2).split(",")]
        # With a mantissa dot: YAML 1.1 reads a bare `7e+11` as a string.
        return match.group(1) + "[ " + ", ".join(f"{v:.6e}" for v in values) + " ]"

    return re.sub(
        r"(energy_offered: !AeroMapsCustomDataType\n\s+years: \[[^\]]*\]\n\s+values: )"
        r"\[([^\]]*)\]",
        scale,
        text,
    )


# variant -> (regionalisation file it starts from, what is done to the carriers files)
VARIANTS = {
    "autarky": (POOL_CONFIG, "autarky"),
    "pool": (POOL_CONFIG, "pool"),
    "oversupply": (POOL_CONFIG, "oversupply"),
    "eligibility": (ELIGIBILITY_CONFIG, "pool"),
    "eligibility_oversupply": (ELIGIBILITY_CONFIG, "oversupply"),
}


def _write_variant(variant):
    """Temporary region configs for one variant, next to the real ones; returns paths."""
    written = []
    base, carriers_variant = VARIANTS[variant]
    config = yaml.safe_load(base.read_text())
    block = config["regionalisation"]
    for region in REGIONS:
        folder = SCENARIO / region
        carriers = folder / f"_{variant}_carriers.yaml"
        carriers.write_text(
            _carriers_variant((folder / "energy_carriers_pool.yaml").read_text(), carriers_variant)
        )
        region_config = folder / f"_{variant}_config.yaml"
        region_config.write_text(
            (folder / "config_pool.yaml")
            .read_text()
            .replace("./energy_carriers_pool.yaml", f"./{carriers.name}")
        )
        written += [carriers, region_config]
        block["regions"][region]["config_file"] = f"{region}/{region_config.name}"
    if variant == "autarky":
        block["fuel_trade"] = None
        block["global_models"] = {}
        # Only consumption exists without trade.
        block["aggregation"]["sum"] = [
            name
            for name in block["aggregation"]["sum"]
            if not name.endswith(("_energy_production", "_energy_offered", "_energy_unused"))
        ]
    target = SCENARIO / f"_{variant}_regionalisation.yaml"
    target.write_text(yaml.safe_dump(config, sort_keys=False))
    written.append(target)
    return target, written


def _run(variant):
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    if VARIANTS[variant][1] == "pool":
        target, written = VARIANTS[variant][0], []
    else:
        target, written = _write_variant(variant)
    try:
        started = time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            process = MultiRegionalProcess(str(target))
            process.compute()
        elapsed = time.perf_counter() - started
    finally:
        for path in written:
            path.unlink(missing_ok=True)
    pool_warnings = sorted({str(w.message) for w in caught if "FuelTrade pool" in str(w.message)})
    return process, elapsed, pool_warnings


# -- checks ----------------------------------------------------------------------------


def _worst_relative(a, b):
    """Largest |a - b| / max|b| over the values given; 0 when both are all zero or NaN."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    both = np.isfinite(a) & np.isfinite(b)
    if np.any(np.isfinite(a) != np.isfinite(b)):
        return np.inf
    scale = np.max(np.abs(b[both])) if both.any() else 0.0
    if scale == 0.0:
        return float(np.max(np.abs(a[both]))) if both.any() else 0.0
    return float(np.max(np.abs(a[both] - b[both])) / scale)


def _p(v, region, name):
    return v[f"{region}:{name}"].loc[PROSPECTIVE].fillna(0.0)


def _eligible(region, pathway, excluding):
    return not (excluding and (region, pathway) == EXCLUDED)


def _checks(runs):
    """Every identity the pool implies, as ``{name: worst relative error}``."""
    a, t, o = (runs[name].data["vector_outputs"] for name in ("autarky", "pool", "oversupply"))
    e = runs["eligibility"].data["vector_outputs"]
    out = {}

    pooled_runs = (
        ("pool", t, False),
        ("oversupply", o, False),
        ("eligibility", e, True),
        ("eligibility + oversupply", runs["eligibility_oversupply"].data["vector_outputs"], True),
    )
    for label, v, excluding in pooled_runs:
        # 1. Each region burns exactly its demand, all pathways together.
        out[f"{label}: each region burns its demand"] = max(
            _worst_relative(
                sum(_p(v, r, f"{q}_energy_consumption") for q in PATHWAYS),
                _p(v, r, "energy_consumption_dropin_fuel"),
            )
            for r in REGIONS
        )
        # 2. ... and the world mix: the same share of every pathway in every region --
        #    every region ALLOWED to burn it, with an eligibility rule. Not where a region
        #    is capped at its demand, which is what oversupply does with the rule on.
        if label != "eligibility + oversupply":
            out[f"{label}: every eligible region burns the same share of each pool"] = max(
                _worst_relative(
                    _p(v, "region_A", f"{q}_energy_consumption")
                    / _p(v, "region_A", "energy_consumption_dropin_fuel"),
                    _p(v, "region_B", f"{q}_energy_consumption")
                    / _p(v, "region_B", "energy_consumption_dropin_fuel"),
                )
                for q in POOLED
                if _eligible("region_A", q, excluding) and _eligible("region_B", q, excluding)
            )
        if excluding:
            region, pathway = EXCLUDED
            out[f"{label}: the excluded region burns none of it"] = float(
                (
                    _p(v, region, f"{pathway}_energy_consumption")
                    / _p(v, region, "energy_consumption_dropin_fuel")
                )
                .abs()
                .max()
            )
        # 3. Offers are kept whole: made + unused = offered, made = offered x the
        #    pathway's use rate.
        out[f"{label}: made + unused = offered"] = max(
            _worst_relative(
                _p(v, r, f"{q}_energy_production") + _p(v, r, f"{q}_energy_unused"),
                _p(v, r, f"{q}_energy_offered"),
            )
            for r in REGIONS
            for q in POOLED
        )
        out[f"{label}: made = offered x the pathway's use rate"] = max(
            _worst_relative(
                _p(v, r, f"{q}_energy_production"),
                v[f"overall:{q}_pool_use_rate"].loc[PROSPECTIVE] * _p(v, r, f"{q}_energy_offered"),
            )
            for r in REGIONS
            for q in POOLED
        )
        # 3b. Nothing is left unused that an eligible region with room could have burnt:
        #     where a region still burns fossil kerosene, every pool it may draw on is
        #     fully used. Worst unused share of such a pool, 0 if the rule holds.
        worst = 0.0
        for r in REGIONS:
            room = _p(v, r, f"{RESIDUAL}_energy_consumption") > 1e-9 * _p(
                v, r, "energy_consumption_dropin_fuel"
            )
            for q in POOLED:
                if not _eligible(r, q, excluding) or not room.any():
                    continue
                unused = sum(_p(v, m, f"{q}_energy_unused") for m in REGIONS)
                offered = sum(_p(v, m, f"{q}_energy_offered") for m in REGIONS)
                share = (unused / offered.where(offered > 0)).fillna(0.0)
                worst = max(worst, float(share[room].max()))
        out[f"{label}: no pool left unused by an eligible region with room"] = worst
        # 4. Nothing created or lost, pathway by pathway -- summed here and through the
        #    aggregator.
        out[f"{label}: world made = world burnt"] = max(
            _worst_relative(
                sum(_p(v, r, f"{q}_energy_production") for r in REGIONS),
                sum(_p(v, r, f"{q}_energy_consumption") for r in REGIONS),
            )
            for q in PATHWAYS
        )
        out[f"{label}: ... and through the aggregator"] = max(
            _worst_relative(
                v[f"overall:{q}_energy_production"].loc[PROSPECTIVE],
                v[f"overall:{q}_energy_consumption"].loc[PROSPECTIVE],
            )
            for q in POOLED
        )
        # 5. The tracked flows are the net positions.
        out[f"{label}: flows = net exports"] = max(
            _worst_relative(
                v[f"overall:{q}_energy_flow_region_A_to_region_B"].loc[PROSPECTIVE]
                - v[f"overall:{q}_energy_flow_region_B_to_region_A"].loc[PROSPECTIVE],
                _p(v, "region_A", f"{q}_energy_net_export"),
            )
            for q in POOLED
        )
        # 6. Feedstock follows what is made, pathway by pathway.
        out[f"{label}: feedstock = specific use x made"] = max(
            _worst_relative(
                _p(v, r, f"{resource}_total_consumption"),
                specific * _p(v, r, f"{q}_energy_production"),
            )
            for r in REGIONS
            for q, (resource, specific) in FEEDSTOCK.items()
        )
        # 7. A region's drop-in CO2 is its consumption at the makers' emission factors --
        #    the means and the per-pathway totals agree.
        out[f"{label}: regional CO2, means = per-pathway totals"] = max(
            _worst_relative(
                _p(v, r, "dropin_fuel_mean_co2_emission_factor")
                * _p(v, r, "energy_consumption_dropin_fuel"),
                sum(_p(v, r, f"{q}_total_co2_emissions") for q in PATHWAYS),
            )
            for r in REGIONS
        )
        # 8. ... and the world's CO2 is the same counted where burnt or where made.
        out[f"{label}: world CO2, burnt = made"] = _worst_relative(
            sum(
                _p(v, r, f"{q}_energy_consumption")
                * _p(v, r, f"{q}_delivered_mean_co2_emission_factor")
                for r in REGIONS
                for q in PATHWAYS
            ),
            sum(
                _p(v, r, f"{q}_energy_production") * _p(v, r, f"{q}_mean_co2_emission_factor")
                for r in REGIONS
                for q in PATHWAYS
            ),
        )
        # 9. What buyers pay before carbon tax is what makers receive.
        out[f"{label}: world spending = makers' revenue"] = _worst_relative(
            sum(
                _p(v, r, f"{q}_energy_consumption")
                * _p(v, r, f"{q}_delivered_net_mfsp_without_carbon_tax")
                for r in REGIONS
                for q in PATHWAYS
            ),
            sum(
                _p(v, r, f"{q}_energy_production") * _p(v, r, f"{q}_net_mfsp_without_carbon_tax")
                for r in REGIONS
                for q in PATHWAYS
            ),
        )
        # 10. The carbon tax is the burner's, on the maker's emission factor.
        out[f"{label}: carbon tax = burner's rate x makers' CO2"] = max(
            _worst_relative(
                _p(v, r, f"{q}_delivered_mean_unit_carbon_tax"),
                _p(v, r, "carbon_tax")
                / 1000
                * _p(v, r, f"{q}_delivered_mean_co2_emission_factor")
                / 1000,
            )
            for r in REGIONS
            for q in PATHWAYS
        )

    # 11. Same offers, all used: what each region MAKES, and so its feedstock, is the same
    #     pooled or not. Only consumption moves.
    out["pool vs autarky: feedstock unchanged, region by region"] = max(
        _worst_relative(
            _p(t, r, f"{resource}_total_consumption"), _p(a, r, f"{resource}_total_consumption")
        )
        for r in REGIONS
        for resource, _ in FEEDSTOCK.values()
    )
    # 12. No trade in the historical years.
    out["pool vs autarky: historical years identical"] = max(
        _worst_relative(
            t[f"{r}:{q}_energy_consumption"].loc[HISTORICAL].fillna(0.0),
            a[f"{r}:{q}_energy_consumption"].loc[HISTORICAL].fillna(0.0),
        )
        for r in REGIONS
        for q in PATHWAYS
    )
    # 13. The rule moves only who burns what: nothing goes unused in the eligibility run,
    #     so what each region makes, and its feedstock, is the pool's.
    out["eligibility vs pool: feedstock unchanged, region by region"] = max(
        _worst_relative(
            _p(e, r, f"{resource}_total_consumption"), _p(t, r, f"{resource}_total_consumption")
        )
        for r in REGIONS
        for resource, _ in FEEDSTOCK.values()
    )
    return out


# -- series for the artifact -------------------------------------------------------------


def _series(v, key):
    return [float(x) for x in v[key].reindex(YEARS).to_numpy()]


def _snapshot(process, traded):
    v = process.data["vector_outputs"]
    keep = {}
    for r in REGIONS:
        names = [
            "energy_consumption_dropin_fuel",
            "dropin_fuel_mean_co2_emission_factor",
            "dropin_fuel_mean_mfsp",
            "dropin_fuel_mean_net_mfsp",
            "dropin_fuel_mean_unit_carbon_tax",
            "airfare_per_rpk",
            "rpk",
            "carbon_tax",
        ]
        for q in PATHWAYS:
            names += [f"{q}_energy_consumption", f"{q}_mean_co2_emission_factor", f"{q}_mean_mfsp"]
            if traded:
                names += [
                    f"{q}_energy_production",
                    f"{q}_energy_net_export",
                    f"{q}_delivered_mean_co2_emission_factor",
                    f"{q}_delivered_mean_mfsp",
                    f"{q}_delivered_net_mfsp",
                ]
        for q in POOLED:
            if traded:
                names += [f"{q}_energy_offered", f"{q}_energy_unused"]
        for resource, _ in FEEDSTOCK.values():
            names.append(f"{resource}_total_consumption")
        for name in names:
            key = f"{r}:{name}"
            if key in v:
                keep[key] = _series(v, key)
    for key in v.columns:
        if key.startswith("overall:") and (
            "_energy_flow_" in key or key.endswith("_pool_use_rate")
        ):
            keep[key] = _series(v, key)
    return keep


def _iterations(process):
    inner = process.mda_chain.inner_mdas
    return len(inner[0].residual_history) if inner else 0


# -- figure ----------------------------------------------------------------------------


def _figure(results):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colour = {"region_A": "#3B4BB8", "region_B": "#C4572F"}
    label = {"region_A": "A (offers a lot)", "region_B": "B (offers little)"}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))

    ax = axes[0]
    for r in REGIONS:
        for run, style in (("autarky", ":"), ("pool", "-")):
            s = results["series"][run]
            saf = np.sum([s[f"{r}:{q}_energy_consumption"] for q in POOLED], axis=0)
            share = 100 * saf / np.array(s[f"{r}:energy_consumption_dropin_fuel"])
            ax.plot(YEARS, share, style, color=colour[r], lw=2, label=f"{label[r]}, {run}")
    ax.set_title("Share of sustainable fuel in what each region burns")
    ax.set_ylabel("%")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    s = results["series"]["pool"]
    bottom = np.zeros(len(YEARS))
    for q, shade in zip(POOLED, ("#00897A", "#4DB6AC", "#80CBC4", "#B2DFDB")):
        net = np.array(s[f"overall:{q}_energy_flow_region_A_to_region_B"]) - np.array(
            s[f"overall:{q}_energy_flow_region_B_to_region_A"]
        )
        ax.fill_between(YEARS, bottom / 1e12, (bottom + net) / 1e12, color=shade, label=q)
        bottom = bottom + net
    ax.set_title("Net flow A -> B, pool (EJ/yr)")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[2]
    for r in REGIONS:
        for run, style in (("autarky", ":"), ("pool", "-")):
            ax.plot(
                YEARS,
                results["series"][run][f"{r}:dropin_fuel_mean_co2_emission_factor"],
                style,
                color=colour[r],
                lw=2,
                label=f"{label[r]}, {run}",
            )
    ax.set_title("CO2 per MJ of drop-in fuel burnt (gCO2/MJ)")
    ax.legend(frameon=False, fontsize=8)

    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    FIGURE.parent.mkdir(exist_ok=True)
    fig.savefig(FIGURE, dpi=130)


# -- main ------------------------------------------------------------------------------


def run():
    logging.disable(logging.INFO)
    results = {"seconds": {}, "iterations": {}, "pool_warnings": {}, "series": {}}
    runs = {}
    for variant in VARIANTS:
        process, seconds, pool_warnings = _run(variant)
        runs[variant] = process
        results["seconds"][variant] = seconds
        results["iterations"][variant] = _iterations(process)
        results["pool_warnings"][variant] = pool_warnings
        results["series"][variant] = _snapshot(process, traded=variant != "autarky")
        print(f"== {variant:10s} {seconds:5.1f} s, {results['iterations'][variant]} iterations")
    results["checks"] = _checks(runs)
    for name, value in results["checks"].items():
        print(f"   {name:55s} {value:.2e}")
    results["years"] = YEARS
    RESULTS.write_text(json.dumps(results, indent=1))
    _figure(results)
    return results


if __name__ == "__main__":
    run()

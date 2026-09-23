"""Five pathways: a supply curve that bends against one that jumps.

Usage::

    poetry run python -m fuel_clearing_step1.five_pathways          # run, then plot
    poetry run python -m fuel_clearing_step1.five_pathways --plot   # plot the saved run

**The question.** Step 1 limits a pathway in one of two ways. Either its cost *bends* --
``saturation_intensity`` (gamma) and ``saturation_stiffness`` (n) make the marginal cost
rise as output approaches ``capacity`` (K) -- or its output is *capped*, with
``capacity_limit``, and the cost stays flat right up to the wall. The first was chosen at
step 1 for a reason that no longer holds: a hard cap gives a step-function dual, and a
step-function price whipsawed the coupling loop. The demand anchor (REPORT section 8.6)
removed that failure at the source, so the cap is available again -- and it is the shape
an engineer can defend, because ``gamma`` and ``n`` are not measurable quantities.

**Why five pathways.** The two-pathway bench cannot answer this. With one sustainable
pathway the obligation names the only fuel that can meet it, so there is no allocation to
make and a staircase has no steps to step between. Five pathways in the real merit order
(``scenario/energy_carriers_five.yaml``) give four.

**What is held fixed.** Both configurations use the same K, the same loose ramp-up, the
same buy-out, the same demand anchor and the same MDA tolerance. The soft one lets a
pathway pass K at rising cost; the hard one does not. That is the only difference, which
is what makes the comparison a comparison.
"""

from __future__ import annotations

import json
import logging
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "scenario" / "regionalisation_five.yaml"
RESULTS = HERE / "five_pathways.json"
FIGURES = HERE / "figures"

PATHWAYS = ("fossil_kerosene", "hefa_fog", "ft_msw", "atj", "electrofuel")
ELIGIBLE = ("hefa_fog", "ft_msw", "atj", "electrofuel")
REGIONS = ("region_A", "region_B")

# Capacity in MJ/yr, the SAME number in both configurations -- soft as the scale the cost
# bends at, hard as the wall it stops at. Sized against region A's 2050 drop-in demand of
# 1.41e13 MJ: 14 %, 20 % and 20 % of it. They sum to 54 % of region A's demand and 37 % of
# region B's, against a 70 % obligation, so in both regions the obligation cannot be met
# from the capped pathways alone -- which is what puts a *choice* in front of the market.
#
# These are illustrative, not calibrated. The ordering (waste oils scarcest, PtL not
# feedstock-bound) is defensible; the levels are not yet, and REPORT section 9 says so.
CAPACITY = {"hefa_fog": 2.0e12, "ft_msw": 2.8e12, "atj": 2.8e12}
# The same three, plus a ceiling on the backstop. With `electrofuel` uncapped some pathway
# is always marginal at its own cost and the staircase never leaves a price undefined --
# so the one thing the demand anchor exists for is never exercised. Capping it puts total
# eligible capacity at 8.6 PJ/yr and lets the traffic loop drive demand down until the
# obligation exactly exhausts it. See `all_capped` in CASES.
CAPACITY_ALL = {**CAPACITY, "electrofuel": 1.0e12}
# electrofuel deliberately has none: PtL is bound by electricity and capital, not by a
# feedstock, so it is the backstop that closes the obligation at its own cost. A market
# where every pathway is capped is a market where the buy-out sets the price, and then
# nothing about supply shape is visible at all.

COMMON = dict(
    buyout_price=0.30,
    rampup_limit=1.0e3,
    rampup_seed_share=1.0,
    demand_elasticity=0.5,
)
MDA_TOLERANCE = 1.0e-7
# 200 is the default and is not enough for `all_capped`, which has to walk demand all the
# way onto a vertical segment. Raised for every case so the comparison is run under one
# stopping rule; the cases that converged in 11-97 sweeps are untouched by it.
MDA_MAX_ITER = 900

CASES = {
    "reference": dict(saturation_intensity=0.0),
    "smoothed_n4": dict(
        saturation_intensity=1.0,
        saturation_stiffness=4.0,
        pathways={p: {"capacity": k} for p, k in CAPACITY.items()},
    ),
    "smoothed_n16": dict(
        saturation_intensity=1.0,
        saturation_stiffness=16.0,
        pathways={p: {"capacity": k} for p, k in CAPACITY.items()},
    ),
    "hard": dict(
        saturation_intensity=0.0,
        pathways={p: {"capacity_limit": k} for p, k in CAPACITY.items()},
    ),
    # Every eligible route capped, so the obligation can only be met by exhausting all of
    # them: the supply curve is vertical at the clearing quantity and the price has to come
    # from somewhere else. This is the case the demand anchor was built for, and the only
    # one in the spike where it is load-bearing rather than merely a convergence aid.
    #
    # eta = 2, not 0.5. On a vertical segment the loop's true response is stiff, and
    # REPORT section 8.6's rule applies: over-stating beta is safe, under-stating it by
    # more than a factor of two is not. At 0.5 this case does not converge in 900 sweeps
    # (residual 0.15, still falling); at 2.0 it converges in 128.
    "all_capped": dict(
        saturation_intensity=0.0,
        demand_elasticity=2.0,
        pathways={p: {"capacity_limit": k} for p, k in CAPACITY_ALL.items()},
    ),
}
WEIGHTS = (0.0, 1.0)

LABELS = {
    "reference": "nothing scarce",
    "smoothed_n4": "bends, $n=4$",
    "smoothed_n16": "bends, $n=16$",
    "hard": "jumps (hard cap)",
    "all_capped": "jumps, no backstop",
}
PATHWAY_COLOURS = {
    "fossil_kerosene": "#4d4d4d",
    "hefa_fog": "#2f6b4f",
    "ft_msw": "#5ba37a",
    "atj": "#c9a227",
    "electrofuel": "#a93226",
}


def _run_one(settings, tag):
    """One full two-region MDA. A failure is a result, so it is recorded, not raised."""
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    config = yaml.safe_load(CONFIG.read_text())
    config["regionalisation"]["mda_tolerance"] = MDA_TOLERANCE
    config["regionalisation"]["mda_max_iter"] = MDA_MAX_ITER
    config["regionalisation"]["global_models"]["settings"] = {"fuel_clearing": settings}
    target = CONFIG.parent / f"_five_{tag}.yaml"
    target.write_text(yaml.safe_dump(config))

    record = {"settings": {k: v for k, v in settings.items() if k != "pathways"}}
    try:
        process = MultiRegionalProcess(str(target))
        market = process.models["fuel_clearing"]
        market.record_trace = True
        market.trace = []
        try:
            process.compute()
            record["ok"] = True
        except Exception as exc:
            record["ok"] = False
            record["error"] = f"{type(exc).__name__}: {exc}"[:300]
            return record
        outputs = process.data["vector_outputs"]
        record["iterations"] = len(market.trace)
        # The last solve of a converged loop: `a` is zero there, so its duals and volumes
        # are the ones the unregularised programme would have returned.
        record["last"] = market.trace[-1] if market.trace else None
        record["pathway_order"] = list(market.pathway_names)
        for region in REGIONS:
            record[region] = _harvest(outputs, region)
        return record
    finally:
        target.unlink(missing_ok=True)


def _harvest(outputs, region):
    """Everything the comparison needs, as year-indexed lists plus the 2050 slice."""

    def series(name):
        return [float(v) for v in outputs[f"{region}:{name}"].loc[2020:2050]]

    def at(name, year=2050):
        return float(outputs[f"{region}:{name}"].loc[year])

    return dict(
        years=list(range(2020, 2051)),
        shares={p: series(f"{p}_share_dropin_fuel") for p in PATHWAYS},
        volumes={p: series(f"{p}_energy_consumption") for p in PATHWAYS},
        net_mfsp={p: at(f"{p}_net_mfsp") for p in PATHWAYS},
        mean_mfsp={p: at(f"{p}_mean_mfsp") for p in PATHWAYS},
        delivered=series("dropin_fuel_mean_mfsp"),
        energy_price=series("fuel_market_energy_price"),
        compliance_price=series("fuel_market_compliance_price"),
        airfare=series("airfare_per_rpk"),
        rpk=series("rpk"),
        co2=series("co2_emissions_passenger"),
        dropin_demand=series("energy_consumption_dropin_fuel"),
        mandate=at("hefa_fog_mandate_share") / 100.0,
    )


def run():
    warnings.resetwarnings()
    warnings.simplefilter("ignore")
    logging.disable(logging.INFO)

    results = {}
    for weight in WEIGHTS:
        for case, settings in CASES.items():
            tag = f"{case}_w{weight:g}"
            results[tag] = _run_one({**COMMON, **settings, "pricing_weight": weight}, tag)
            cell = results[tag]
            if cell["ok"]:
                a = cell["region_A"]
                print(
                    f"{tag:18s} lamM {a['compliance_price'][-1]:.5f}  "
                    f"delivered {a['delivered'][-1]:.5f}  rpk {a['rpk'][-1]:.4g}  "
                    f"iters {cell['iterations']}",
                    flush=True,
                )
            else:
                print(f"{tag:18s} FAILED {cell['error'][:90]}", flush=True)
            RESULTS.write_text(json.dumps(results, indent=1))
    return results


# --- figures --------------------------------------------------------------------------


def plot_mix(results):
    """The 2050 mix, per case and region. What the shape of the limit does to allocation."""
    figure, axes = plt.subplots(1, 2, figsize=(11.0, 4.3), constrained_layout=True)
    cases = [c for c in CASES if c != "all_capped"]
    for axis, region in zip(axes, REGIONS):
        bottom = np.zeros(len(cases))
        for pathway in PATHWAYS:
            values = np.array(
                [
                    results[f"{c}_w1"][region]["shares"][pathway][-1]
                    if results[f"{c}_w1"]["ok"]
                    else np.nan
                    for c in cases
                ]
            )
            axis.bar(
                cases,
                values,
                bottom=bottom,
                color=PATHWAY_COLOURS[pathway],
                label=pathway,
                width=0.6,
            )
            bottom += np.nan_to_num(values)
        axis.set_xticks(range(len(cases)), [LABELS[c] for c in cases], fontsize=8)
        axis.set_ylabel("share of drop-in fuel, 2050, %")
        axis.set_title(region.replace("_", " "), fontsize=10)
        axis.spines[["top", "right"]].set_visible(False)
    axes[1].legend(frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(1.01, 0.5))
    figure.suptitle("Five pathways, $w=1$: the same capacity, enforced two ways", fontsize=11)
    _save(figure, "five_pathways_mix.png")


def plot_effects(results):
    """Price, airfare and traffic, against the no-scarcity run. Four panels, both regions."""
    cases = [c for c in CASES if c not in ("reference", "all_capped")]
    panels = (
        ("compliance_price", "compliance price $\\lambda^M$, EUR/MJ", False),
        ("delivered", "delivered fuel price, EUR/MJ", False),
        ("airfare", "airfare per RPK vs no scarcity, %", True),
        ("rpk", "RPK 2050 vs no scarcity, %", True),
    )
    figure, axes = plt.subplots(1, 4, figsize=(15.0, 3.8), constrained_layout=True)
    width = 0.36
    for axis, (key, ylabel, relative) in zip(axes, panels):
        for offset, region, colour in (
            (-width / 2, REGIONS[0], "#1f5f8b"),
            (width / 2, REGIONS[1], "#c9772e"),
        ):
            values = []
            for case in cases:
                cell = results[f"{case}_w1"]
                base = results["reference_w1"][region][key][-1]
                if not cell["ok"]:
                    values.append(np.nan)
                elif relative:
                    values.append(100.0 * (cell[region][key][-1] - base) / base)
                else:
                    values.append(cell[region][key][-1])
            axis.bar(
                np.arange(len(cases)) + offset,
                values,
                width=width,
                color=colour,
                label=region.replace("_", " "),
            )
        axis.set_xticks(np.arange(len(cases)), [LABELS[c] for c in cases], fontsize=8)
        axis.set_ylabel(ylabel, fontsize=9)
        axis.axhline(0.0, color="0.6", linewidth=1, linestyle=":")
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, fontsize=8)
    figure.suptitle(
        "What the shape of the limit costs: 2050, $w=1$, against the same run with nothing scarce",
        fontsize=11,
    )
    _save(figure, "five_pathways_effects.png")


def plot_plane(results):
    """The price/quantity plane for the obligation, region A, 2050.

    The x axis is eligible (mandate-counting) volume; the y axis is what an eligible unit
    is paid, ``lambda^E + lambda^M``. In this plane the two configurations are two supply
    curves over the same four pathways:

    * **hard cap** -- flat at each pathway's cost for the width of its capacity, then
      vertical. A staircase.
    * **soft saturation** -- the aggregate inverse of ``q_p(pi) = K_p((pi/c_p - 1)/gamma)^(1/n)``,
      which is the same staircase with its corners rounded off.

    And the obligation is drawn twice, which is the whole point of the figure:

    * as the **vertical** line ``m * D`` it is at a fixed total demand -- and where that
      line crosses a vertical stretch of supply there is no crossing *point* at all, only
      a crossing segment. That is the dual interval, drawn;
    * as the **sloped** line the elastic balance actually prices against. Demand for
      eligible fuel is ``m * (D + a)`` with ``a = beta * (p0 - lambda^E - m*(pi - lambda^E))``,
      so its slope is ``-m^2 beta``: steep, because a 1 EUR/MJ rise in the eligible price
      raises the delivered price by only ``m`` of that, and only ``m`` of the demand it
      withdraws was eligible. Steep, but not vertical -- and that is the difference
      between a price and an interval.
    """
    region = REGIONS[0]
    hard = results["hard_w1"]
    soft = results["smoothed_n4_w1"]
    if not (hard["ok"] and soft["ok"]):
        print("plane: need both the hard and the soft run")
        return
    reference = hard[region]

    cost = {p: reference["net_mfsp"][p] for p in ELIGIBLE}
    order = sorted(ELIGIBLE, key=lambda p: cost[p])
    demand = reference["dropin_demand"][-1]
    mandate = reference["mandate"]
    obligation = mandate * demand

    figure, axis = plt.subplots(figsize=(7.6, 5.2), constrained_layout=True)
    unit = 1.0e12

    # --- the staircase ---------------------------------------------------------------
    x, y = [0.0], [cost[order[0]]]
    for pathway in order:
        width = CAPACITY.get(pathway)
        y[-1] = cost[pathway]
        if width is None:  # the uncapped backstop: flat from here on
            x.append(1.35 * obligation)
            y.append(cost[pathway])
            break
        x.extend([x[-1] + width, x[-1] + width])
        y.extend([cost[pathway], cost[pathway]])
    axis.step(
        np.array(x) / unit,
        y,
        where="post",
        color="#a93226",
        linewidth=2.0,
        label="hard cap: marginal cost is a staircase",
    )

    # --- the bent curve --------------------------------------------------------------
    gamma = CASES["smoothed_n4"]["saturation_intensity"]
    sat_n = CASES["smoothed_n4"]["saturation_stiffness"]
    backstop = cost[order[-1]]
    prices = np.linspace(min(cost.values()) * 1.0001, backstop, 600)
    quantity = np.zeros_like(prices)
    for pathway in order:
        capacity = CAPACITY.get(pathway)
        if capacity is None:
            continue
        ratio = np.maximum(prices / cost[pathway] - 1.0, 0.0) / gamma
        quantity += capacity * ratio ** (1.0 / sat_n)
    axis.plot(
        quantity / unit,
        prices,
        color="#1f5f8b",
        linewidth=2.0,
        label=f"soft saturation: bent ($\\gamma={gamma:g}$, $n={sat_n:g}$)",
    )
    # Above the backstop's cost the aggregate curve is flat: an uncapped pathway supplies
    # whatever is asked at its own cost, so nothing is ever paid more than that.
    axis.plot(
        [quantity[-1] / unit, 1.35 * obligation / unit],
        [backstop, backstop],
        color="#1f5f8b",
        linewidth=2.0,
    )

    # --- the obligation, twice -------------------------------------------------------
    axis.axvline(
        obligation / unit,
        color="0.35",
        linestyle="--",
        linewidth=1.4,
        label="obligation $mD$ at fixed demand (vertical)",
    )
    energy_price = reference["energy_price"][-1]
    anchor = energy_price + reference["compliance_price"][-1]
    slope = mandate**2 * (0.5 * demand / (energy_price + mandate * (anchor - energy_price)))
    span = np.linspace(anchor - 0.055, anchor + 0.02, 50)
    axis.plot(
        (obligation - slope * (span - anchor)) / unit,
        span,
        color="#2f6b4f",
        linewidth=1.6,
        label="what the market prices against (slope $-m^2\\beta$)",
    )

    for case, colour, marker in (("hard_w1", "#a93226", "o"), ("smoothed_n4_w1", "#1f5f8b", "s")):
        cell = results[case][region]
        eligible = sum(cell["volumes"][p][-1] for p in ELIGIBLE)
        price = cell["energy_price"][-1] + cell["compliance_price"][-1]
        axis.plot(
            eligible / unit,
            price,
            marker,
            color=colour,
            markersize=9,
            zorder=5,
            markeredgecolor="white",
        )

    for pathway in order:
        axis.annotate(
            pathway,
            (1.30 * obligation / unit, cost[pathway]),
            fontsize=8,
            color="0.3",
            va="center",
            ha="right",
        )

    axis.set_xlabel("eligible (mandate-counting) volume, PJ/yr")
    axis.set_ylabel("price of an eligible unit, $\\lambda^E + \\lambda^M$, EUR/MJ")
    axis.set_xlim(0, 1.35 * obligation / unit)
    axis.set_ylim(0, backstop * 1.15)
    axis.legend(frameon=False, fontsize=8, loc="upper left")
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_title(
        "Region A, 2050: where the crossing is a point and where it is a segment", fontsize=10
    )
    _save(figure, "five_pathways_plane.png")


def _save(figure, name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / name
    figure.savefig(target, dpi=150)
    plt.close(figure)
    print(f"wrote {target}")


def report(results):
    """The table the report quotes, printed so the numbers in it are traceable."""
    print()
    header = f"{'case':16s} {'region':9s} {'lambda_E':>9s} {'lambda_M':>9s} {'delivered':>10s} "
    print(header + f"{'airfare%':>9s} {'RPK%':>8s} {'CO2%':>8s}")
    for weight in WEIGHTS:
        print(f"-- w = {weight:g}")
        for case in CASES:
            cell = results.get(f"{case}_w{weight:g}", {})
            if not cell.get("ok"):
                print(f"{case:16s} FAILED")
                continue
            for region in REGIONS:
                data, base = cell[region], results[f"reference_w{weight:g}"][region]
                print(
                    f"{case:16s} {region:9s} {data['energy_price'][-1]:9.5f} "
                    f"{data['compliance_price'][-1]:9.5f} {data['delivered'][-1]:10.5f} "
                    f"{100 * (data['airfare'][-1] / base['airfare'][-1] - 1):9.2f} "
                    f"{100 * (data['rpk'][-1] / base['rpk'][-1] - 1):8.2f} "
                    f"{100 * (data['co2'][-1] / base['co2'][-1] - 1):8.2f}"
                )


def vertical_segment(results):
    """Where the obligation exhausts every eligible route, check the price came from demand.

    On a vertical stretch of supply the programme fixes the quantity and says nothing
    about the price. Two identities then have to hold, and neither is a cost:

    * the quantity is pinned by capacity -- ``m * D`` equals the total ceiling, because the
      traffic loop walked demand down until it did;
    * the price is pinned by the demand curve -- the balance's stationarity in ``a`` gives
      ``lambda_E + m*lambda_M = p0``, and the split is still fixed from the supply side by
      the uncapped residual, so ``lambda_M = (p0 - c_kerosene) / m``.

    The second is *leveraged*: at ``m = 0.7`` an error of 0.01 in the delivered price is an
    error of 0.014 in the compliance price. That is a real property of a share mandate.
    """
    cell = results.get("all_capped_w1")
    if not cell or not cell["ok"]:
        print("\nall_capped: not available")
        return
    total_cap = sum(CAPACITY_ALL.values())
    print("\nvertical segment (all_capped, w=1, 2050)")
    for region in REGIONS:
        data = cell[region]
        demand = data["dropin_demand"][-1]
        eligible = sum(data["volumes"][p][-1] for p in ELIGIBLE)
        mandate = data["mandate"]
        energy, compliance = data["energy_price"][-1], data["compliance_price"][-1]
        delivered_marginal = energy + mandate * compliance
        # p0 is the anchor the LAST solve priced against -- the previous iterate's
        # delivered marginal price, recorded in the trace. Comparing lambda_M against
        # (p0 - lambda_E)/m is therefore a real check: p0 comes from the iteration before,
        # and the two agree only if the loop has actually reached its fixed point.
        # (Comparing against (lambda_E + m*lambda_M - lambda_E)/m would be an identity
        # and would verify nothing.)
        anchor = cell["last"]["marginal"][REGIONS.index(region)][-1] if cell["last"] else np.nan
        implied = (anchor - energy) / mandate
        binding = eligible > (1 - 1e-6) * total_cap
        print(
            f"  {region}: capacity {'EXHAUSTED' if binding else 'spare'}  "
            f"eligible {eligible:.4g} of {total_cap:.4g}   m*D {mandate * demand:.4g}"
        )
        print(
            f"      lambda_E {energy:.5f}  lambda_M {compliance:.5f}  "
            f"lambda_E + m*lambda_M {delivered_marginal:.5f}   "
            f"anchor p0 {anchor:.5f}  ->  (p0 - lambda_E)/m {implied:.5f}  "
            f"(residual {compliance - implied:+.2e})"
        )
        dearest = max(data["net_mfsp"][p] for p in ELIGIBLE)
        print(
            f"      dearest pathway cost {dearest:.5f}; eligible unit paid "
            f"{energy + compliance:.5f}  -> rent above every cost: "
            f"{energy + compliance - dearest:+.5f}"
        )


def plot(results=None):
    results = results or json.loads(RESULTS.read_text())
    plot_mix(results)
    plot_effects(results)
    plot_plane(results)
    report(results)
    vertical_segment(results)
    return results


if __name__ == "__main__":
    plot() if "--plot" in sys.argv else plot(run())

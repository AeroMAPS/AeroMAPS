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
# eligible capacity at 8.6 EJ/yr and lets the traffic loop drive demand down until the
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

# Extra runs whose only job is to put more points on each region's DEMAND curve. At a
# converged w = 1 run the pair (obligation volume m*D, eligible price lambda_E + lambda_M)
# is a point where AeroMAPS's own traffic chain meets the market -- and since every w = 1
# run shares that chain and differs only in supply, all of them lie on one demand curve
# per region. Moving the capacities moves the crossing along it. Used by `plot_plane`
# only; nothing in the tables depends on them.
_PROBE_BASE = {**CAPACITY_ALL}
DEMAND_PROBES = {
    "efuel_2": {**CAPACITY, "electrofuel": 2.0e12},
    "efuel_3": {**CAPACITY, "electrofuel": 3.0e12},
    "all_x0.8": {p: 0.8 * k for p, k in _PROBE_BASE.items()},
    "all_x0.65": {p: 0.65 * k for p, k in _PROBE_BASE.items()},
}

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


def run_probes():
    """The demand-curve probes, appended to the saved results under ``probes``."""
    warnings.resetwarnings()
    warnings.simplefilter("ignore")
    logging.disable(logging.INFO)
    results = json.loads(RESULTS.read_text())
    results.setdefault("probes", {})
    for tag, caps in DEMAND_PROBES.items():
        settings = {
            **COMMON,
            "saturation_intensity": 0.0,
            "demand_elasticity": 2.0,
            "pricing_weight": 1.0,
            "pathways": {p: {"capacity_limit": k} for p, k in caps.items()},
        }
        results["probes"][tag] = _run_one(settings, f"probe_{tag}")
        cell = results["probes"][tag]
        status = "ok" if cell["ok"] else f"FAILED {cell.get('error', '')[:80]}"
        print(f"probe {tag:10s} {status}", flush=True)
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


def _soft_supply(prices, cost, gamma, sat_n):
    """Eligible volume supplied at each price by the saturating pathways, summed.

    Inverting marginal cost ``c (1 + gamma (q/K)^n)``: ``q = K ((pi/c - 1)/gamma)^(1/n)``.
    Uncapped pathways are not included -- they supply anything at their own cost, which
    the caller draws as a flat line.
    """
    quantity = np.zeros_like(prices)
    for pathway, capacity in CAPACITY.items():
        ratio = np.maximum(prices / cost[pathway] - 1.0, 0.0) / gamma
        quantity += capacity * ratio ** (1.0 / sat_n)
    return quantity


def _demand_points(results, region):
    """(obligation volume m*D, eligible price) at every converged w = 1 run, sorted by price.

    Every w = 1 run shares AeroMAPS's traffic chain and differs only in supply, so each
    converged run is one point of the SAME demand curve for that region. Nothing here is
    fitted: the curve drawn through them is only an interpolation between measured points.
    """
    cells = [results[f"{case}_w1"] for case in CASES]
    cells += list(results.get("probes", {}).values())
    points = set()
    for cell in cells:
        if not cell.get("ok"):
            continue
        data = cell[region]
        volume = data["mandate"] * data["dropin_demand"][-1]
        price = data["energy_price"][-1] + data["compliance_price"][-1]
        points.add((round(volume / 1.0e12, 4), round(price, 5)))
    return np.array(sorted(points, key=lambda xy: xy[1]))


def plot_plane(results):
    """The price/quantity plane for the obligation, 2050, w = 1. Two panels.

    Left: the supply side alone -- the same capacities K made into a staircase (hard cap)
    or bent (soft saturation) at several (gamma, n). The bend starts BEFORE K, because a
    plant's cost is already rising as it approaches K and the next fuel becomes the
    cheaper one sooner; and it runs PAST K, because nothing stops a soft pathway there.

    Right: both regions' demand for eligible fuel crossing that supply. Each region has
    its OWN copy of the staircase -- capacities are per region at step 1 -- and the demand
    curves are made of measured equilibria, not assumed. Three crossings: region A on a
    flat step (spare capacity, price = cost), region B on a flat step with e-fuel
    uncapped, and region B on a vertical riser once e-fuel is capped too -- where supply
    fixes the quantity and demand the price.
    """
    reference = results["hard_w1"]["region_A"]
    cost = {p: reference["net_mfsp"][p] for p in ELIGIBLE}
    order = sorted(ELIGIBLE, key=lambda p: cost[p])
    backstop = cost["electrofuel"]
    energy_price = reference["energy_price"][-1]
    ceiling = energy_price + COMMON["buyout_price"]
    unit = 1.0e12

    def staircase(extra_cap=None, right=15.0):
        x, y = [0.0], [cost[order[0]]]
        for pathway in order:
            width = CAPACITY.get(pathway, extra_cap if pathway == "electrofuel" else None)
            y[-1] = cost[pathway]
            if width is None:
                x.append(right)
                y.append(cost[pathway])
                return np.array(x), np.array(y)
            x.extend([x[-1] + width / unit, x[-1] + width / unit])
            y.extend([cost[pathway], cost[pathway]])
        # every eligible route capped: vertical up to the penalty, flat beyond it
        x.extend([x[-1], right])
        y.extend([ceiling, ceiling])
        return np.array(x), np.array(y)

    figure, (left, right) = plt.subplots(
        1, 2, figsize=(14.0, 5.6), constrained_layout=True, gridspec_kw={"width_ratios": [1, 1.25]}
    )

    # --- left: the shapes ---------------------------------------------------------------
    x, y = staircase(right=11.0)
    left.plot(x, y, color="#a93226", linewidth=2.2, label="hard cap: stops at K")
    prices = np.linspace(min(cost.values()) * 1.0001, backstop, 800)
    shapes = (
        (1.0, 2.0, "#a1d99b", "-"),
        (1.0, 4.0, "#41ab5d", "-"),
        (1.0, 16.0, "#006d2c", "-"),
        (3.0, 4.0, "#41ab5d", "--"),
    )
    for gamma, sat_n, colour, style in shapes:
        q = _soft_supply(prices, cost, gamma, sat_n) / unit
        left.plot(
            np.append(q, 11.0),
            np.append(prices, backstop),
            style,
            color=colour,
            linewidth=1.8,
            label=f"bends: $\\gamma$={gamma:g}, n={sat_n:g}",
        )
    cumulative = np.cumsum([CAPACITY[p] for p in order if p in CAPACITY]) / unit
    for k, pathway in zip(cumulative, [p for p in order if p in CAPACITY]):
        left.axvline(k, color="0.75", linewidth=0.8, linestyle=":")
        left.text(k, 0.004, f" K ends\n {pathway}", fontsize=7.5, color="0.4", va="bottom")
    for pathway in order:
        left.text(10.9, cost[pathway], pathway, fontsize=8, color="0.35", ha="right", va="bottom")
    left.set_xlim(0, 11.0)
    left.set_ylim(0, backstop * 1.12)
    left.set_title(
        "Same capacities K, different shapes:\nthe bend starts before K and runs past it",
        fontsize=10,
    )
    left.legend(frameon=False, fontsize=8, loc="upper left")

    # --- right: the crossings -----------------------------------------------------------
    x, y = staircase(right=15.0)
    right.plot(x, y, color="#a93226", linewidth=2.2, label="supply, e-fuel uncapped")
    x, y = staircase(extra_cap=CAPACITY_ALL["electrofuel"], right=15.0)
    right.plot(x, y, "--", color="#a93226", linewidth=1.6, label="supply, e-fuel capped at 1 EJ")
    right.axhline(ceiling, color="0.55", linestyle=":", linewidth=1.0)
    right.text(
        14.9,
        ceiling,
        "penalty: nobody pays more",
        fontsize=7.5,
        color="0.4",
        ha="right",
        va="bottom",
    )
    q = _soft_supply(prices, cost, 1.0, 4.0) / unit
    right.plot(
        np.append(q, 15.0),
        np.append(prices, backstop),
        color="#41ab5d",
        linewidth=1.3,
        alpha=0.8,
        label="supply, bends ($\\gamma$=1, n=4)",
    )

    colours = {"region_A": "#1f5f8b", "region_B": "#c9772e"}
    for region in REGIONS:
        points = _demand_points(results, region)
        if len(points) >= 2:
            from scipy.interpolate import PchipInterpolator

            curve = PchipInterpolator(points[:, 1], points[:, 0])
            grid = np.linspace(points[0, 1], points[-1, 1], 300)
            right.plot(
                curve(grid),
                grid,
                color=colours[region],
                linewidth=2.0,
                label=f"demand, {region.replace('_', ' ')} (measured)",
            )
        right.plot(points[:, 0], points[:, 1], "o", color=colours[region], markersize=3.5)

    def mark(case, region, text, offset):
        cell = results.get(case, {})
        if not cell.get("ok"):
            return
        data = cell[region]
        xy = (
            data["mandate"] * data["dropin_demand"][-1] / unit,
            data["energy_price"][-1] + data["compliance_price"][-1],
        )
        right.plot(
            *xy,
            "o",
            markersize=11,
            markerfacecolor="none",
            markeredgecolor=colours[region],
            markeredgewidth=2.0,
        )
        right.annotate(
            text,
            xy,
            xytext=offset,
            textcoords="offset points",
            fontsize=8,
            color="0.15",
            arrowprops=dict(arrowstyle="-", color="0.5", linewidth=0.8),
        )

    mark("hard_w1", "region_A", "A: spare capacity,\nprice = e-fuel cost", (-150, 30))
    mark("hard_w1", "region_B", "B: price = e-fuel cost", (-30, 40))
    mark(
        "all_capped_w1",
        "region_B",
        "B, e-fuel capped: all fuels at\ntheir limit, price from demand",
        (-200, 12),
    )
    mark("smoothed_n4_w1", "region_A", "A with bends: cheaper,\nno e-fuel needed", (60, -75))

    right.set_xlim(0, 15.0)
    right.set_ylim(0, ceiling * 1.08)
    right.set_title(
        "Where each region's obligation meets supply (each region has its own staircase)",
        fontsize=10,
    )
    right.legend(frameon=False, fontsize=8, loc="upper right", bbox_to_anchor=(1.0, 0.93))

    for axis in (left, right):
        axis.set_xlabel("eligible (mandate-counting) volume, EJ/yr")
        axis.spines[["top", "right"]].set_visible(False)
    left.set_ylabel("price of an eligible MJ, $\\lambda_E + \\lambda_M$, EUR/MJ")
    figure.suptitle("2050, w = 1", fontsize=10, x=0.02, ha="left")
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
    if "--probes" in sys.argv:
        plot(run_probes())
    elif "--plot" in sys.argv:
        plot()
    else:
        plot(run())

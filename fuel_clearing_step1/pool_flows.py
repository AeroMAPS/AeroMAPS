"""One global pool: each region supplies it and draws on it, and the flows are tracked.

Usage::

    poetry run python -m fuel_clearing_step1.pool_flows          # run, then plot
    poetry run python -m fuel_clearing_step1.pool_flows --plot   # plot the saved run

**The question.** At step 1 the regions are solved together but share nothing: region B
cannot burn a litre region A makes. REPORT section 12.5 settled the shape of the fix --
every region supplies one global pool with what it produces and draws what it consumes,
no routes and no transport costs, net flows tracked -- and the kernel now builds it
(``ClearingInputs.pooled``). This measures what it does to *volumes*: who produces what,
who burns it, what flows, and when a shared resource runs out. How pooling moves each
region's *price* is deliberately not the question here (it is D5's), and nothing below
interprets the prices it records.

**At fixed demand, kernel only.** Each region's demand and the pathway costs are taken
from the converged ``hard_w1`` run of ``five_pathways.py`` -- the same five pathways,
the same caps, the same obligation -- and held fixed, so traffic does not respond to
pooling. That isolates the flows from the traffic loop, and it gives a check for free:
the ``separate`` case is that run's own programme at its own fixed point, so it must
return that run's volumes.

**Three cases.**

- ``separate`` -- today: each region consumes what it produces.
- ``pooled`` -- the same plants (each region owns HEFA 2.0, FT-MSW 2.8, ATJ 2.8 EJ/yr),
  all five pathways pooled. Only the demand differs between the regions: B's traffic
  grows faster.
- ``waste_oil_in_A`` -- all 4.0 EJ/yr of waste-oil (HEFA) capacity sits in region A,
  none in B, run both separate and pooled. The same total resource, located on one
  side: the case where "common exhaustion" has something to show.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "five_pathways.json"
RESULTS = HERE / "pool_flows.json"
FIGURES = HERE / "figures"

REGIONS = ("region_A", "region_B")
YEARS = np.arange(2020, 2051)
ELIGIBLE = ("hefa_fog", "ft_msw", "atj", "electrofuel")
RESIDUAL = "fossil_kerosene"

# The obligation of scenario/energy_carriers_five.yaml, a staircase held from each listed
# year to the next ("method: previous"). Recovered from the saved run as a check: its
# eligible share equals this, year by year, to 1e-10.
MANDATE_YEARS = (2020, 2025, 2030, 2035, 2040, 2045, 2050)
MANDATE_VALUES = (0.0, 0.02, 0.06, 0.20, 0.34, 0.42, 0.70)

# five_pathways.CAPACITY, per region. e-fuel and kerosene stay uncapped.
CAPACITY = {"hefa_fog": 2.0e12, "ft_msw": 2.8e12, "atj": 2.8e12}
BUYOUT = 0.30
DISCOUNT_RATE = 0.04

LABELS = {
    "hefa_fog": "HEFA",
    "ft_msw": "FT-MSW",
    "atj": "ATJ",
    "electrofuel": "e-fuel",
    "fossil_kerosene": "kerosene",
}
# Categorical slots 1-4 of the dataviz reference palette, validated (light surface):
# worst adjacent CVD dE 9.1, normal-vision 22.9. ATJ and e-fuel sit below 3:1 contrast,
# so every line carries a direct label.
COLOURS = {"hefa_fog": "#2a78d6", "ft_msw": "#eb6834", "atj": "#1baf7a", "electrofuel": "#eda100"}
# Slots 7 and 5, so a region is never drawn in a fuel's colour: CVD dE 24.9, normal 33.9.
REGION_COLOURS = {"region_A": "#4a3aa7", "region_B": "#e87ba4"}
INK, MUTED, RULE = "#0b0b0b", "#52514e", "#d9d8d4"


def _mandate():
    share = np.zeros(YEARS.size)
    for year, value in zip(MANDATE_YEARS, MANDATE_VALUES):
        share[YEARS >= year] = value
    return share


def _source():
    """Demand, costs and pathway order of the converged ``hard_w1`` run."""
    run = json.loads(SOURCE.read_text())["hard_w1"]
    last = run["last"]
    order = list(run["pathway_order"])
    demand = np.array(last["demand"])
    # With no soft saturation the average cost IS the input cost, net of nothing the
    # kernel does -- so this recovers exactly the cost array that run solved against.
    cost = np.array(last["average_cost"])
    return order, demand, cost, np.array(last["volume"])


def _inputs(order, demand, cost, capacity, pooled):
    from aeromaps.models.impacts.generic_energy_model.fuel_clearing.kernel import (
        ClearingInputs,
    )

    regions, years = demand.shape
    pathways = len(order)
    limit = np.full((regions, pathways, years), np.inf)
    for r, region in enumerate(REGIONS):
        for pathway, value in capacity[region].items():
            limit[r, order.index(pathway), :] = value
    residual = order.index(RESIDUAL)
    q_init = np.zeros((regions, pathways))
    q_init[:, residual] = demand[:, 0]
    return ClearingInputs(
        demand=demand,
        cost=cost,
        is_sustainable=np.array([p in ELIGIBLE for p in order]),
        mandate_share=np.broadcast_to(_mandate(), (regions, years)).copy(),
        buyout_price=np.full((regions, years), BUYOUT),
        capacity=np.full((regions, pathways, years), np.inf),
        capacity_limit=limit,
        sat_gamma=np.zeros((regions, pathways)),
        sat_n=4.0,
        # Loose, as in five_pathways.COMMON: the caps are the only scarcity.
        rampup_limit=np.full((regions, pathways), 1.0e3),
        rampup_seed=np.broadcast_to(demand[:, :1], (regions, pathways)).copy(),
        q_init=q_init,
        discount_rate=DISCOUNT_RATE,
        pricing_weight=1.0,
        residual_pathway=residual,
        pooled=None if not pooled else np.ones(pathways, dtype=bool),
    )


def _record(order, inputs, outputs):
    """Everything the tables and figures need, per region and pathway, as lists."""
    scale = outputs.diagnostics["energy_scale"] * outputs.diagnostics["cost_scale"]
    record = {
        "pathway_order": order,
        "years": YEARS.tolist(),
        "objective": outputs.diagnostics["objective_scaled"] * scale,
        "solve_seconds": outputs.diagnostics["solve_seconds"],
        "pool": outputs.diagnostics.get("pool"),
    }
    for r, region in enumerate(REGIONS):
        record[region] = {
            "demand": inputs.demand[r].tolist(),
            "capacity": {p: inputs.capacity_limit[r, order.index(p)].tolist() for p in ELIGIBLE},
            "consumed": {p: outputs.volume[r, i].tolist() for i, p in enumerate(order)},
            "produced": {p: outputs.supply[r, i].tolist() for i, p in enumerate(order)},
            "net_flow": {p: outputs.net_flow[r, i].tolist() for i, p in enumerate(order)},
            # Recorded, not interpreted: how pooling moves prices is D5's question.
            "eligible_price": (outputs.energy_price[r] + outputs.compliance_price[r]).tolist(),
            "energy_price": outputs.energy_price[r].tolist(),
        }
    record["pool_price"] = {p: outputs.pool_price[i].tolist() for i, p in enumerate(order)}
    return record


CASES = {
    "separate": dict(pooled=False, capacity={r: CAPACITY for r in REGIONS}),
    "pooled": dict(pooled=True, capacity={r: CAPACITY for r in REGIONS}),
    "waste_oil_in_A_separate": dict(
        pooled=False,
        capacity={
            "region_A": {**CAPACITY, "hefa_fog": 2 * CAPACITY["hefa_fog"]},
            "region_B": {**CAPACITY, "hefa_fog": 0.0},
        },
    ),
    "waste_oil_in_A_pooled": dict(
        pooled=True,
        capacity={
            "region_A": {**CAPACITY, "hefa_fog": 2 * CAPACITY["hefa_fog"]},
            "region_B": {**CAPACITY, "hefa_fog": 0.0},
        },
    ),
}


def flow_ranges(order, inputs, kernel_outputs):
    """How much of each pooled flow the market actually determines.

    The kernel's least-trade pass pins HOW MUCH is traded. It does not pin WHICH fuel: an
    exporter producing two fuels that sell at the same price -- typically two fuels both
    at their caps, both priced at the marginal fuel above them -- can ship either, at the
    same cost and the same traded volume. This finds, year by year, the smallest and the
    largest net flow of each fuel out of region A over every point that is optimal in
    cost AND in traded volume.

    Written out independently of the kernel, on purpose, as a second opinion: an LP per
    year, which is exact here because the growth limit is loose (the years do not
    interact). Its cost is checked against the kernel's, year by year.

    Two regions only: B's flow is minus A's.
    """
    import cvxpy as cp

    regions, pathways, years = inputs.shape
    cost, cap = inputs.cost, inputs.capacity_limit
    eligible = inputs.is_sustainable
    low = np.zeros((pathways, years))
    high = np.zeros((pathways, years))
    worst_cost_gap = 0.0
    tolerance = 1e-7

    for t in range(years):
        # Variables in units of the year's largest demand, costs in units of the mean
        # cost: order 1, as the kernel does it. In raw MJ (~1e13) Clarabel calls this
        # same LP infeasible.
        d = inputs.demand[:, t]
        scale_e, scale_c = float(d.max()), float(cost[:, :, t].mean())
        s = cp.Variable((regions, pathways), nonneg=True)
        u = cp.Variable((regions, pathways), nonneg=True)
        x = cp.Variable(regions, nonneg=True)
        base = [
            cp.sum(u, axis=1) == d / scale_e,
            cp.sum(cp.multiply(eligible, u), axis=1) + x
            >= inputs.mandate_share[:, t] * d / scale_e,
            cp.sum(s, axis=0) == cp.sum(u, axis=0),
        ]
        capped = np.isfinite(cap[:, :, t])
        base.append(s[capped] <= cap[:, :, t][capped] / scale_e)
        total_cost = cp.sum(cp.multiply(cost[:, :, t] / scale_c, s)) + cp.sum(
            cp.multiply(inputs.buyout_price[:, t] / scale_c, x)
        )
        first = cp.Problem(cp.Minimize(total_cost), base)
        first.solve(solver=cp.CLARABEL)
        if first.status != "optimal":
            raise RuntimeError(f"year index {t}: the cost LP returned {first.status}")
        optimum = first.value

        kernel_cost = float(
            np.sum(cost[:, :, t] * kernel_outputs.supply[:, :, t])
            + np.sum(inputs.buyout_price[:, t] * kernel_outputs.unmet[:, t])
        ) / (scale_c * scale_e)
        worst_cost_gap = max(worst_cost_gap, abs(kernel_cost - optimum) / abs(optimum))

        exports = cp.Variable((regions, pathways), nonneg=True)
        bound_cost = base + [exports >= s - u, total_cost <= optimum + tolerance * abs(optimum)]
        second = cp.Problem(cp.Minimize(cp.sum(exports)), bound_cost)
        second.solve(solver=cp.CLARABEL)
        if second.status != "optimal":
            raise RuntimeError(f"year index {t}: the least-trade LP returned {second.status}")
        least = second.value

        fixed = bound_cost + [cp.sum(exports) <= least + tolerance * max(least, 1.0)]
        for p in range(pathways):
            flow = s[0, p] - u[0, p]
            for sense, store in ((cp.Minimize, low), (cp.Maximize, high)):
                problem = cp.Problem(sense(flow), fixed)
                problem.solve(solver=cp.CLARABEL)
                if problem.status != "optimal":
                    raise RuntimeError(f"year index {t}: a range LP returned {problem.status}")
                store[p, t] = problem.value * scale_e
    return {
        "low": {p: low[i].tolist() for i, p in enumerate(order)},
        "high": {p: high[i].tolist() for i, p in enumerate(order)},
        "worst_relative_cost_gap_to_kernel": worst_cost_gap,
    }


def run():
    from aeromaps.models.impacts.generic_energy_model.fuel_clearing.kernel import clear_market

    order, demand, cost, saved_volume = _source()
    results = {}
    for case, spec in CASES.items():
        inputs = _inputs(order, demand, cost, spec["capacity"], spec["pooled"])
        outputs = clear_market(inputs)
        results[case] = _record(order, inputs.validate(), outputs)
        if case == "separate":
            # The run this was taken from, at its own fixed point: same programme, same
            # answer, to the MDA's tolerance rather than the solver's.
            gap = np.max(np.abs(outputs.volume - saved_volume)) / np.max(demand)
            results[case]["gap_to_saved_run"] = float(gap)
        if spec["pooled"]:
            results[case]["flow_range"] = flow_ranges(order, inputs.validate(), outputs)
        pool = results[case]["pool"] or {}
        print(
            f"{case:26s} cost {results[case]['objective']:.6e}  "
            f"traded {pool.get('traded', 0.0) / 1e12:8.3f} EJ  "
            f"(first pass {pool.get('traded_first_pass', 0.0) / 1e12:8.3f})  "
            f"{outputs.diagnostics['solve_seconds']:.2f}s",
            flush=True,
        )
    print(f"separate vs saved hard_w1 run: {results['separate']['gap_to_saved_run']:.2e} of demand")
    RESULTS.write_text(json.dumps(results, indent=1))
    return results


def _style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(RULE)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.grid(axis="y", color=RULE, linewidth=0.6)
    ax.set_axisbelow(True)


def plot_exhaustion(results):
    """Waste oil in A: who burns it, separately and pooled, against the one capacity."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0), sharey=True, dpi=200)
    capacity = np.array(results["waste_oil_in_A_pooled"]["region_A"]["capacity"]["hefa_fog"])
    for ax, case, title in (
        (axes[0], "waste_oil_in_A_separate", "Separate markets"),
        (axes[1], "waste_oil_in_A_pooled", "One global pool"),
    ):
        base = np.zeros(YEARS.size)
        for region in REGIONS:
            burnt = np.array(results[case][region]["consumed"]["hefa_fog"]) / 1e12
            ax.bar(
                YEARS,
                burnt,
                bottom=base,
                width=0.8,
                color=REGION_COLOURS[region],
                edgecolor="white",
                linewidth=1.0,
                label=f"burnt in {region.replace('region_', 'region ')}",
            )
            base = base + burnt
        ax.plot(YEARS, capacity / 1e12, color=INK, linewidth=1.2, linestyle=(0, (4, 3)))
        ax.text(
            2020.3,
            capacity[0] / 1e12 + 0.08,
            "waste-oil capacity, all in A",
            color=MUTED,
            fontsize=8.5,
            va="bottom",
        )
        full = np.flatnonzero(base >= capacity / 1e12 * (1 - 1e-6))
        if full.size:
            year = int(YEARS[full[0]])
            ax.annotate(
                f"used up from {year}",
                xy=(year, capacity[0] / 1e12),
                xytext=(year - 9.5, 4.55),
                fontsize=9,
                color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.8),
            )
        ax.set_title(title, loc="left", fontsize=11, color=INK)
        ax.set_ylim(0, 5.0)
        ax.set_xlim(2019.3, 2050.7)
        _style(ax)
    axes[0].set_ylabel("HEFA burnt, EJ/yr", color=MUTED, fontsize=9)
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", ncol=2, frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    FIGURES.mkdir(exist_ok=True)
    fig.savefig(FIGURES / "pool_exhaustion.png", facecolor="white")
    plt.close(fig)


def plot_flows(results):
    """What region A exports, per fuel, and how much of that the market decides."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0), dpi=200)
    for ax, case, title, top in (
        (axes[0], "waste_oil_in_A_pooled", "Waste oil all in A", 3.0),
        (axes[1], "pooled", "Same plants in both regions", 0.6),
    ):
        record = results[case]
        flows, ranges = record["region_A"]["net_flow"], record["flow_range"]
        total = sum(np.array(flows[p]) for p in ELIGIBLE) / 1e12
        # Years where some fuel's flow could be anything in a range at the same cost and
        # the same traded volume. There, only the total is the market's answer; the split
        # drawn is the solver's pick. One neutral band, not one per fuel: every fuel's
        # range is the whole export in those years, and per-fuel bands only overlap.
        width = (
            np.max(
                [np.array(ranges["high"][p]) - np.array(ranges["low"][p]) for p in ELIGIBLE], axis=0
            )
            / 1e12
        )
        open_split = width > 1e-3
        # Year-wide bars rather than a stepped fill: a stepped fill with gaps loses half a
        # year at each edge, which is exactly the edge the band is there to show.
        ax.bar(
            YEARS[open_split],
            total[open_split],
            width=1.0,
            color=MUTED,
            alpha=0.13,
            linewidth=0,
            label="split between fuels: not decided",
        )
        for pathway in ELIGIBLE:
            kernel = np.array(flows[pathway]) / 1e12
            if np.max(np.abs(kernel)) < 1e-3:
                continue
            ax.step(
                YEARS,
                kernel,
                where="mid",
                color=COLOURS[pathway],
                linewidth=1.8,
                label=LABELS[pathway],
            )
        ax.step(
            YEARS,
            total,
            where="mid",
            color=INK,
            linewidth=1.2,
            linestyle=(0, (4, 3)),
            label="all eligible fuel",
        )
        ax.set_title(title, loc="left", fontsize=11, color=INK)
        ax.set_ylim(-0.02 * top, top)
        ax.set_xlim(2019.3, 2050.7)
        _style(ax)
        ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    axes[0].set_ylabel("Net export of region A, EJ/yr", color=MUTED, fontsize=9)
    fig.tight_layout()
    FIGURES.mkdir(exist_ok=True)
    fig.savefig(FIGURES / "pool_flows.png", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    if "--plot" in sys.argv:
        results = json.loads(RESULTS.read_text())
    else:
        results = run()
    plot_exhaustion(results)
    plot_flows(results)

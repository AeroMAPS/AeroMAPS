"""Figures for the step-1 report. Regenerates everything under ``figures/``.

Usage::

    poetry run python -m fuel_clearing_step1.figures

Four figures:

``reproduction``
    Test 3.3.c made visible -- the kernel against the reference run, on the real
    two-region bench. This is the consistency check between the two modes.
``rampup_regimes``
    What the market does when a plausible ramp-up meets ReFuelEU's step obligation.
    The step years are where the two modes stop agreeing.
``pricing_vs_current``
    The market's delivered price against the current mode's ``{at}_mean_mfsp`` -- the
    price that reaches the airfare and so the demand loop. Volumes held fixed, so the
    difference is the pricing rule alone.
``price_continuity``
    The sweep of test 3.3.f. The test asserts continuity by refinement; this draws
    what that is protecting, which is the difference between a soft saturation and a
    hard capacity cap.
"""

from __future__ import annotations

import json
import warnings
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from aeromaps.models.impacts.generic_energy_model.fuel_clearing.kernel import (  # noqa: E402
    ClearingInputs,
    clear_market,
)

# Bench scripts elsewhere silence warnings at import (brief section 2.2).
warnings.resetwarnings()
warnings.simplefilter("default")

HERE = Path(__file__).resolve().parent
FIGURES = HERE / "figures"

YEARS = 12
DEMAND = 1.0e13
COST_SUSTAINABLE = 0.024
COST_KEROSENE = 0.012
CAPACITY = 5.0e12
GAMMA = 2.0
BUYOUT = 0.3

# The ramp-up is deliberately LOOSE here. With a tight one it binds before the mandate
# does, the volume stops responding, the buy-out covers the whole gap and the
# compliance price sits flat on the buy-out for the entire sweep -- measured, and it
# makes the figure say nothing about continuity. The regime worth drawing is the one
# where the mandate is what sets the volume.
RAMPUP_LIMIT = 2.0
RAMPUP_SEED = DEMAND * 0.1


def _case(mandate_share, sat_n):
    return ClearingInputs(
        demand=np.full((1, YEARS), DEMAND),
        cost=np.broadcast_to(
            np.array([[[COST_SUSTAINABLE], [COST_KEROSENE]]]), (1, 2, YEARS)
        ).copy(),
        is_sustainable=np.array([True, False]),
        mandate_share=mandate_share,
        buyout_price=np.full((1, YEARS), BUYOUT),
        capacity=np.broadcast_to(np.array([[[CAPACITY], [np.inf]]]), (1, 2, YEARS)).copy(),
        sat_gamma=np.array([[GAMMA, 0.0]]),
        sat_n=sat_n,
        rampup_limit=np.array([[RAMPUP_LIMIT, 0.0]]),
        rampup_seed=np.array([[RAMPUP_SEED, 0.0]]),
        q_init=np.array([[0.0, 0.0]]),
        discount_rate=0.04,
        pricing_weight=0.0,
    )


def price_continuity(points: int = 200, stiffnesses=(2.0, 4.0, 8.0, 16.0)):
    """Sweep a multiplier on the mandate and watch the compliance price.

    The brief's test 3.3.f asserts that neighbouring points do not jump. Drawing it
    across several values of ``n`` shows *why* decision 5 chose a soft saturation: the
    curve steepens with stiffness, and a hard cap is the limit where it becomes a step.
    """
    base = np.linspace(0.0, 0.5, YEARS)[None, :]
    factors = np.linspace(0.5, 2.0, points)
    step = float(factors[1] - factors[0])

    figure, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    summary = {}

    for sat_n in stiffnesses:
        prices, unmet = [], []
        for factor in factors:
            outputs = clear_market(_case(np.clip(base * factor, 0.0, 1.0), sat_n))
            # Report the last year, where the mandate is highest and saturation bites.
            prices.append(outputs.compliance_price[0, -1])
            unmet.append(outputs.unmet[0, -1] / DEMAND)
        prices, unmet = np.array(prices), np.array(unmet)
        jumps = np.abs(np.diff(prices))
        summary[sat_n] = (jumps.max(), jumps.max() / step)

        axes[0].plot(factors, prices, label=f"n = {sat_n:g}")
        axes[1].plot(factors, 100 * unmet, label=f"n = {sat_n:g}")

    axes[0].axhline(BUYOUT, linestyle="--", color="0.4", linewidth=1)
    axes[0].annotate(
        "buy-out price caps the dual",
        xy=(factors[0], BUYOUT),
        xytext=(4, 4),
        textcoords="offset points",
        fontsize=8,
        color="0.35",
    )
    axes[0].set_xlabel("multiplier on the mandate")
    axes[0].set_ylabel("compliance price, final year")
    axes[0].set_title("The dual rises smoothly, then saturates at the buy-out")
    axes[0].legend(frameon=False, fontsize=8)

    axes[1].set_xlabel("multiplier on the mandate")
    axes[1].set_ylabel("unmet obligation, % of demand")
    axes[1].set_title("Where the buy-out engages")
    axes[1].legend(frameon=False, fontsize=8)

    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)

    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / "price_continuity.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)

    print(f"wrote {target}")
    print(f"  sweep step {step:.5f}")
    for sat_n, (largest, ratio) in summary.items():
        print(
            f"  n={sat_n:>4g}: largest jump between neighbours {largest:.4g}  ({ratio:.2f} x step)"
        )
    return summary


# --- figures on the real bench ----------------------------------------------------

FIXTURE_DIR = HERE.parent / "aeromaps" / "tests" / "fixtures" / "fuel_clearing"
SUSTAINABLE, RESIDUAL = "hefa_fog", "fossil_kerosene"
MJ_TO_TWH = 1.0 / 3.6e9


def load_bench():
    """The committed reference run, as arrays the kernel takes.

    Prospective years only. The historical years carry NaN for the sustainable
    pathway in the current mode (REPORT.md section 4), and the market does not act on
    them anyway.
    """
    table = pd.read_parquet(FIXTURE_DIR / "reference.parquet")
    metadata = json.loads((FIXTURE_DIR / "metadata.json").read_text())
    regions = metadata["regions"]
    first, last = metadata["years"]["prospection_start"], metadata["years"]["end"]

    window = table[(table["year"] >= first) & (table["year"] <= last)]
    years = np.array(sorted(window["year"].unique()))

    def stack(column):
        return np.array(
            [
                window[window["region"] == region].sort_values("year")[column].to_numpy()
                for region in regions
            ]
        )

    return {
        "regions": regions,
        "years": years,
        "demand": stack("energy_demand"),
        "cost": np.stack([stack(f"{SUSTAINABLE}_mean_mfsp"), stack(f"{RESIDUAL}_mean_mfsp")], 1),
        "reference_share": stack(f"{SUSTAINABLE}_share_dropin_fuel") / 100.0,
        "reference_volume": stack(f"{SUSTAINABLE}_energy_consumption"),
        # The price that actually reaches the airline in the current mode, and so the
        # DOC, the airfare and the demand loop.
        "reference_delivered": stack("dropin_fuel_mean_mfsp"),
    }


def _delivered(outputs):
    """Volume-weighted mean market MFSP, per region and year.

    The same weighting `EnergyCarriersMeans` applies in the current mode
    (``Sigma_p share_p * mfsp_p``), so the two are directly comparable.
    """
    return (outputs.market_mfsp * outputs.volume).sum(axis=1) / outputs.volume.sum(axis=1)


def _bench_inputs(bench, *, rampup_limit, rampup_seed, buyout, capacity=np.inf, gamma=0.0):
    regions, years = bench["demand"].shape
    return ClearingInputs(
        demand=bench["demand"],
        cost=bench["cost"],
        is_sustainable=np.array([True, False]),
        mandate_share=bench["reference_share"],
        buyout_price=np.full((regions, years), buyout),
        capacity=np.full((regions, 2, years), capacity),
        sat_gamma=np.array([[gamma, 0.0]] * regions),
        sat_n=4.0,
        rampup_limit=np.array([[rampup_limit, 0.0]] * regions),
        rampup_seed=np.array([[rampup_seed, 0.0]] * regions),
        q_init=np.zeros((regions, 2)),
        discount_rate=0.04,
        pricing_weight=0.0,
    )


def reproduction():
    """Test 3.3.c drawn: the kernel reproducing the current mode on the real bench.

    Loose ramp-up, saturation off, buy-out far above any cost -- the settings under
    which the market has one degree of freedom left and should land exactly on the
    reference allocation.
    """
    bench = load_bench()
    outputs = clear_market(
        _bench_inputs(
            bench,
            rampup_limit=1.0e3,
            rampup_seed=float(bench["demand"].max()),
            buyout=1.0e3,
        )
    )

    figure, axes = plt.subplots(1, 3, figsize=(13.5, 4.0), constrained_layout=True)
    colours = ["#1f77b4", "#d62728"]

    for index, region in enumerate(bench["regions"]):
        axes[0].plot(
            bench["years"],
            bench["reference_volume"][index] * MJ_TO_TWH,
            color=colours[index],
            linewidth=2.4,
            alpha=0.45,
            label=f"{region}, current mode",
        )
        axes[0].plot(
            bench["years"],
            outputs.volume[index, 0] * MJ_TO_TWH,
            color=colours[index],
            linestyle="none",
            marker="o",
            markersize=3.2,
            markevery=2,
            label=f"{region}, market",
        )
        # Normalised by DEMAND, not by the reference volume. The obligation is zero
        # until 2025, so a reference-relative error divides by zero there and reports
        # solver noise as a 900 % discrepancy.
        reference = bench["reference_volume"][index]
        relative = np.abs(outputs.volume[index, 0] - reference) / bench["demand"][index]
        axes[1].semilogy(
            bench["years"], np.maximum(relative, 1e-18), color=colours[index], label=region
        )
        axes[2].plot(
            bench["years"],
            100 * bench["reference_share"][index],
            color=colours[index],
            label=region,
        )

    axes[0].set_ylabel("sustainable fuel, TWh")
    axes[0].set_title("Volumes: market lands on the reference")
    axes[0].legend(frameon=False, fontsize=7.5)

    axes[1].axhline(1e-7, linestyle="--", color="0.4", linewidth=1)
    axes[1].annotate(
        "solver noise floor, 1e-7 of demand",
        xy=(bench["years"][0], 1e-7),
        xytext=(4, 4),
        textcoords="offset points",
        fontsize=7.5,
        color="0.35",
    )
    axes[1].set_ylabel("|market - reference| / demand")
    axes[1].set_title("Residual, log scale")
    axes[1].legend(frameon=False, fontsize=7.5)

    axes[2].set_ylabel("mandate, % of drop-in energy")
    axes[2].set_title("ReFuelEU obligation, as a step")
    axes[2].legend(frameon=False, fontsize=7.5)

    for axis in axes:
        axis.set_xlabel("year")
        axis.spines[["top", "right"]].set_visible(False)

    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / "reproduction.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)

    worst = max(
        float(
            np.max(np.abs(outputs.volume[i, 0] - bench["reference_volume"][i]) / bench["demand"][i])
        )
        for i in range(len(bench["regions"]))
    )
    print(f"wrote {target}")
    print(f"  worst difference against the reference, as a fraction of demand: {worst:.3e}")
    return worst


def rampup_regimes(limits=(0.15, 0.30, 0.60, 1.20)):
    """A plausible ramp-up against ReFuelEU's steps: where the modes part company.

    The obligation demands +202 %, +233 %, +70 %, +24 % and +66 % growth at its step
    years. Anything near an industrial rate is violated there and slack between, so
    the buy-out carries the difference and the compliance price pins to it.
    """
    bench = load_bench()
    buyout = 0.05  # above the ~0.011 the mandate costs when it is reachable
    region = 0

    figure, axes = plt.subplots(1, 3, figsize=(13.5, 4.0), constrained_layout=True)

    axes[0].plot(
        bench["years"],
        100 * bench["reference_share"][region],
        color="0.2",
        linewidth=2.2,
        linestyle="--",
        label="obligation",
    )
    for limit in limits:
        outputs = clear_market(
            _bench_inputs(
                bench,
                rampup_limit=limit,
                rampup_seed=float(bench["demand"].max()) * 0.005,
                buyout=buyout,
            )
        )
        share = outputs.volume[region, 0] / bench["demand"][region]
        axes[0].plot(bench["years"], 100 * share, label=f"g = {limit:.0%}/yr")
        axes[1].plot(
            bench["years"],
            100 * outputs.unmet[region] / bench["demand"][region],
            label=f"g = {limit:.0%}/yr",
        )
        axes[2].plot(bench["years"], outputs.compliance_price[region], label=f"g = {limit:.0%}/yr")

    axes[0].set_ylabel("sustainable share, %")
    axes[0].set_title("Perfect foresight builds ahead of each step")
    axes[1].set_ylabel("unmet obligation, % of demand")
    axes[1].set_title("The buy-out is needed only at the 2035 step")
    axes[2].axhline(buyout, linestyle="--", color="0.4", linewidth=1)
    axes[2].annotate(
        "buy-out",
        xy=(bench["years"][-1], buyout),
        xytext=(-30, 4),
        textcoords="offset points",
        fontsize=7.5,
        color="0.35",
    )
    axes[2].set_ylabel("compliance price, EUR/MJ")
    axes[2].set_title("Price is zero wherever the market is ahead")

    for axis in axes:
        axis.set_xlabel("year")
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, fontsize=7.5, loc="upper left")
    axes[1].legend(frameon=False, fontsize=7.5, loc="upper left")
    axes[2].legend(frameon=False, fontsize=7.5, loc="upper left", ncol=2)

    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / "rampup_regimes.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)
    print(f"wrote {target}")


def _tracking_capacity(bench, headroom=1.25, floor_share=0.02):
    """Exogenous capacity that follows the build-out, instead of a flat number.

    A constant ``K`` against an obligation running 0 -> 70 % puts ``q/K`` almost
    entirely in the last few years, so the saturation markup is invisible until 2050
    and the figure says nothing about the decades in between. Capacity is an
    ``(R, P, T)`` input, so it can track the volume actually needed with a fixed
    headroom -- which is also the more plausible reading of "exogenous capacity".

    Floored at a small share of demand so the early years, where the obligation is
    zero, do not divide by zero.
    """
    sustainable = np.maximum(bench["reference_volume"] * headroom, bench["demand"] * floor_share)
    return np.stack([sustainable, np.full_like(sustainable, np.inf)], axis=1)


def pricing_vs_current(region=0, gamma=1.0):
    """The market's delivered price against the current mode's `{at}_mean_mfsp`.

    This is the quantity that reaches the DOC, the airfare and therefore the demand
    loop, so it is where the two modes either agree or do not.

    The allocation is held fixed across all four curves -- mandate set to the
    reference share, ramp-up loose -- so every difference shown is the **pricing rule**
    and not a different set of volumes.

    The structural point the figure makes: **`w` does nothing at all unless the
    saturation term is active.** With a flat marginal cost, average equals marginal for
    every pathway (lambda_E = c_k and lambda_M = c_s - c_k, so the sustainable
    pathway's marginal price is exactly c_s), and decision 10's blend has two identical
    endpoints. Measured: w = 0 and w = 1 agree to the last digit with gamma = 0.
    """
    bench = load_bench()
    loose = dict(rampup_limit=1.0e3, rampup_seed=float(bench["demand"].max()), buyout=1.0e3)
    regions = len(bench["regions"])

    flat = _delivered(clear_market(_bench_inputs(bench, **loose)))
    # w = 1 with saturation OFF *and the ramp-up slack*. Lies exactly on the w = 0
    # curve: with nothing scarce, average cost equals marginal price for every pathway
    # and decision 10's blend has two identical endpoints.
    flat_marginal = _delivered(
        clear_market(replace(_bench_inputs(bench, **loose), pricing_weight=1.0))
    )
    # The same thing with saturation still OFF but the ramp-up BINDING. Now w is very
    # much alive, because the ramp-up's own scarcity raises the compliance dual above
    # c_s - c_k and so pushes the marginal price above the average cost. w is inert
    # only when NOTHING is scarce -- not merely when gamma = 0.
    tight = dict(rampup_limit=0.10, rampup_seed=float(bench["demand"].max()) * 0.005, buyout=0.05)
    tight_marginal = _delivered(
        clear_market(replace(_bench_inputs(bench, **tight), pricing_weight=1.0))
    )
    saturated = replace(
        _bench_inputs(bench, **loose),
        capacity=_tracking_capacity(bench),
        sat_gamma=np.array([[gamma, 0.0]] * regions),
    )
    saturated_average = _delivered(clear_market(saturated))
    saturated_marginal = _delivered(clear_market(replace(saturated, pricing_weight=1.0)))

    current = bench["reference_delivered"]
    years = bench["years"]
    figure, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), constrained_layout=True)

    axes[0].plot(
        years,
        current[region],
        color="0.25",
        linewidth=2.8,
        alpha=0.5,
        label="current mode, {at}_mean_mfsp",
    )
    axes[0].plot(
        years,
        flat[region],
        color="#1f77b4",
        linestyle="none",
        marker="o",
        markersize=3.4,
        markevery=2,
        label="market, w=0, no saturation",
    )
    axes[0].plot(
        years,
        saturated_average[region],
        color="#2ca02c",
        linewidth=1.8,
        label=f"market, w=0, saturation (gamma={gamma:g}, n=4)",
    )
    axes[0].plot(
        years,
        saturated_marginal[region],
        color="#d62728",
        linewidth=1.8,
        label="market, w=1, saturation",
    )
    axes[0].set_ylabel("delivered price, EUR/MJ")
    axes[0].set_title("What price reaches the airline")
    axes[0].legend(frameon=False, fontsize=7)

    # Where the gap comes from, stacked on the current mode's price.
    markup = saturated_average[region] - current[region]
    rent = saturated_marginal[region] - saturated_average[region]
    axes[1].fill_between(
        years, 0, markup, color="#2ca02c", alpha=0.45, label="saturation markup (w=0)"
    )
    axes[1].fill_between(
        years,
        markup,
        markup + rent,
        color="#d62728",
        alpha=0.45,
        label="rent passed through (w: 0 -> 1)",
    )
    axes[1].set_ylabel("uplift over the current mode, EUR/MJ")
    axes[1].set_title("Where the difference comes from")
    axes[1].legend(frameon=False, fontsize=7.5, loc="upper left")

    for values, colour, style, label in (
        (flat, "#1f77b4", "-", "w=0, nothing scarce"),
        (flat_marginal, "#9467bd", (0, (2, 2)), "w=1, nothing scarce"),
        (saturated_marginal, "#d62728", "-", "w=1, saturation scarce"),
        (tight_marginal, "#ff7f0e", "-", "w=1, ramp-up scarce (gamma=0)"),
    ):
        axes[2].plot(
            years,
            100 * (values[region] - current[region]) / current[region],
            color=colour,
            linestyle=style,
            linewidth=2.2 if style != "-" else 1.6,
            label=label,
        )
    axes[2].axhline(0, color="0.5", linewidth=1)
    axes[2].set_ylabel("difference vs current mode, %")
    axes[2].set_title("w bites wherever there is scarcity rent")
    axes[2].legend(frameon=False, fontsize=7.5, loc="upper left")

    for axis in axes:
        axis.set_xlabel("year")
        axis.spines[["top", "right"]].set_visible(False)

    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / "pricing_vs_current.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)

    worst_flat = float(np.max(np.abs(flat - current) / current))
    inert = float(np.max(np.abs(flat_marginal - flat) / flat))
    print(f"wrote {target}")
    print(f"  w=0 no saturation vs current mode: max relative difference {worst_flat:.3e}")
    print(f"  w=1 vs w=0, nothing scarce:        max relative difference {inert:.3e} (w inert)")
    live = float(np.max(np.abs(tight_marginal - flat) / flat))
    print(f"  w=1 vs w=0, ramp-up scarce, gamma=0: max relative difference {live:.3e} (w live)")
    print(
        f"  2050, region {region}: current {current[region, -1]:.5f}, "
        f"w=0+sat {saturated_average[region, -1]:.5f} "
        f"(+{100 * markup[-1] / current[region, -1]:.1f} %), "
        f"w=1+sat {saturated_marginal[region, -1]:.5f} "
        f"(+{100 * (markup[-1] + rent[-1]) / current[region, -1]:.1f} %)"
    )


if __name__ == "__main__":
    reproduction()
    rampup_regimes()
    pricing_vs_current()
    price_continuity()

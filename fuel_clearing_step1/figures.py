"""Figures for the step-1 report. Regenerates everything under ``figures/``.

Usage::

    poetry run python -m fuel_clearing_step1.figures

Three figures:

``reproduction``
    Test 3.3.c made visible -- the kernel against the reference run, on the real
    two-region bench. This is the consistency check between the two modes.
``rampup_regimes``
    What the market does when a plausible ramp-up meets ReFuelEU's step obligation.
    The step years are where the two modes stop agreeing.
``price_continuity``
    The sweep of test 3.3.f. The test asserts continuity by refinement; this draws
    what that is protecting, which is the difference between a soft saturation and a
    hard capacity cap.
"""

from __future__ import annotations

import json
import warnings
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
    }


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


if __name__ == "__main__":
    reproduction()
    rampup_regimes()
    price_continuity()

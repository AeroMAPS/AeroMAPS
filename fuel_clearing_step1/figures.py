"""Figures for the step-1 report. Regenerates everything under ``figures/``.

Usage::

    poetry run python -m fuel_clearing_step1.figures

Currently: the price-continuity sweep of test 3.3.f. The test asserts the bound; this
draws what the bound is protecting, which is the difference between a soft saturation
and a hard capacity cap.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

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


if __name__ == "__main__":
    price_continuity()

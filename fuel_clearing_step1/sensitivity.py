"""Sensitivity of the cleared market to its major parameters, on the real bench.

Usage::

    poetry run python -m fuel_clearing_step1.sensitivity

One-at-a-time sweeps around a baseline, plus a two-dimensional map of the saturation
term. Everything runs on the committed two-region reference fixture, with the ReFuelEU
step obligation, so the numbers are comparable with the rest of the step-1 work.

Four outputs are tracked, chosen because they are what the rest of AeroMAPS feels:

``delivered price``
    Volume-weighted ``market_mfsp``. This is what reaches the DOC, the airfare and so
    the demand loop -- the only quantity the traffic loop actually sees.
``compliance price``
    The mandate's dual. The policy-relevant price, and the one capped by the buy-out.
``unmet``
    Cumulative buy-out volume as a share of cumulative demand.
``elasticity``
    ``d ln(delivered price) / d ln(demand)`` at the operating point. This is the local
    gain of the market seen from the traffic loop: the larger it is, the harder the
    coupled fixed point is to reach.
"""

from __future__ import annotations

import warnings
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from aeromaps.models.impacts.generic_energy_model.fuel_clearing.kernel import (  # noqa: E402
    ClearingError,
    clear_market,
)

from .figures import (  # noqa: E402
    FIGURES,
    _bench_inputs,
    _delivered,
    _tracking_capacity,
    load_bench,
)

warnings.resetwarnings()
warnings.simplefilter("default")

HERE = Path(__file__).resolve().parent

# Baseline: a mandate that binds, a ramp-up that bites at the steps, saturation active.
BASELINE = dict(sat_n=4.0, gamma=1.0, rampup=0.30, weight=0.0, buyout=0.05, discount=0.04)
REGION = 0

# Capacity headroom over the obligation's own volume. 1.25 -- enough for the figures,
# where the ramp-up is loose -- is NOT enough here: with a ramp-up that bites, perfect
# foresight pre-builds, so between steps the market holds close to twice what the
# obligation asks (measured q/K up to 1.97 at 1.25x headroom). The saturation term then
# sits far out on (q/K)**n and Clarabel starts refusing the problem. Capacity sized on
# the mandate is undersized the moment the market anticipates -- a modelling result in
# its own right, not just a numerical nuisance.
HEADROOM = 2.5


def _build(bench, *, sat_n, gamma, rampup, weight, buyout, discount):
    regions = len(bench["regions"])
    inputs = _bench_inputs(
        bench,
        rampup_limit=rampup,
        rampup_seed=float(bench["demand"].max()) * 0.005,
        buyout=buyout,
    )
    return replace(
        inputs,
        capacity=_tracking_capacity(bench, headroom=HEADROOM),
        sat_gamma=np.array([[gamma, 0.0]] * regions),
        sat_n=sat_n,
        pricing_weight=weight,
        discount_rate=discount,
        compute_elasticity=True,
    )


def _measure(bench, **settings):
    """Run one case and reduce it to the four headline numbers."""
    try:
        outputs = clear_market(_build(bench, **settings))
    except ClearingError:
        # Recorded as a gap in the curve rather than silently interpolated over:
        # a case that does not clear is a result.
        return dict(delivered=np.nan, compliance=np.nan, unmet=np.nan, elasticity=np.nan)

    delivered = _delivered(outputs)
    demand = bench["demand"]
    # The elasticity is a diagnostic whose own re-solve can fail where the primary
    # solve succeeded; the kernel then records `elasticity_error` instead. Absent is a
    # valid answer, and losing it must not lose the case.
    elasticity = outputs.diagnostics.get("elasticity_at_operating_point")
    return dict(
        delivered=float(delivered[REGION, -1]),
        compliance=float(outputs.compliance_price[REGION].max()),
        unmet=float(outputs.unmet[REGION].sum() / demand[REGION].sum()),
        elasticity=np.nan if elasticity is None else float(np.max(np.abs(elasticity[REGION]))),
    )


SWEEPS = {
    "sat_n": ("saturation stiffness n", [1.0, 2.0, 4.0, 8.0, 12.0, 16.0]),
    "gamma": ("saturation intensity gamma", [0.0, 0.25, 0.5, 1.0, 2.0, 4.0]),
    "rampup": ("ramp-up limit g, per year", [0.10, 0.15, 0.20, 0.30, 0.60, 1.20]),
    "weight": ("pricing weight w", [0.0, 0.25, 0.5, 0.75, 1.0]),
    "buyout": ("buy-out price, EUR/MJ", [0.02, 0.03, 0.05, 0.10, 0.30]),
    "discount": ("discount rate", [0.0, 0.02, 0.04, 0.06, 0.08]),
}


def one_at_a_time():
    """Sweep each parameter alone, holding the rest at the baseline."""
    bench = load_bench()
    baseline = _measure(bench, **BASELINE)

    figure, axes = plt.subplots(2, 3, figsize=(13.5, 7.2), constrained_layout=True)
    results = {}

    for axis, (name, (label, values)) in zip(axes.ravel(), SWEEPS.items()):
        rows = [_measure(bench, **{**BASELINE, name: value}) for value in values]
        results[name] = (values, rows)

        delivered = [row["delivered"] for row in rows]
        compliance = [row["compliance"] for row in rows]

        axis.plot(
            values,
            delivered,
            marker="o",
            markersize=4,
            color="#1f77b4",
            label="delivered price, 2050",
        )
        axis.set_xlabel(label)
        axis.set_ylabel("delivered price, EUR/MJ", color="#1f77b4")
        axis.tick_params(axis="y", labelcolor="#1f77b4")
        axis.axvline(BASELINE[name], color="0.7", linestyle=":", linewidth=1.2)

        twin = axis.twinx()
        twin.plot(
            values,
            compliance,
            marker="s",
            markersize=4,
            color="#d62728",
            label="max compliance price",
        )
        twin.set_ylabel("max compliance price, EUR/MJ", color="#d62728")
        twin.tick_params(axis="y", labelcolor="#d62728")
        twin.spines[["top"]].set_visible(False)

        axis.spines[["top"]].set_visible(False)
        axis.set_title(label, fontsize=10)

    figure.suptitle(
        "One-at-a-time sensitivity around the baseline (dotted line), region A, 2050",
        fontsize=11,
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / "sensitivity_oat.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)

    print(f"wrote {target}")
    print(
        f"  baseline: delivered {baseline['delivered']:.5f} EUR/MJ, "
        f"max compliance {baseline['compliance']:.5f}, "
        f"unmet {100 * baseline['unmet']:.2f} %, "
        f"elasticity {baseline['elasticity']:.4f}"
    )
    for name, (values, rows) in results.items():
        delivered = np.array([row["delivered"] for row in rows])
        spread = 100 * (np.nanmax(delivered) - np.nanmin(delivered)) / baseline["delivered"]
        print(f"  {name:9s} {SWEEPS[name][0]:30s} delivered-price spread {spread:6.1f} %")
    return baseline, results


def saturation_map(stiffnesses=(1, 2, 4, 8, 12, 16), intensities=(0.0, 0.25, 0.5, 1.0, 2.0, 4.0)):
    """The saturation term's two parameters, together, at w = 0 and w = 1.

    They do not act independently. ``gamma`` scales the markup and ``n`` shapes it, and
    because the bench runs mostly *below* capacity (``q/K`` around 0.8), raising ``n``
    pushes ``(q/K)**n`` down -- a stiffer saturation is a *smaller* markup until
    capacity is actually reached, and only then does it bite.
    """
    bench = load_bench()
    reference = bench["reference_delivered"][REGION, -1]

    figure, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), constrained_layout=True)
    grids = []

    for axis, weight in zip(axes, (0.0, 1.0)):
        grid = np.zeros((len(intensities), len(stiffnesses)))
        for row, gamma in enumerate(intensities):
            for column, sat_n in enumerate(stiffnesses):
                measured = _measure(
                    bench, **{**BASELINE, "gamma": gamma, "sat_n": float(sat_n), "weight": weight}
                )
                grid[row, column] = 100 * (measured["delivered"] - reference) / reference
        grids.append(grid)

        image = axis.imshow(np.ma.masked_invalid(grid), origin="lower", cmap="magma", aspect="auto")
        axis.set_xticks(range(len(stiffnesses)), [str(s) for s in stiffnesses])
        axis.set_yticks(range(len(intensities)), [f"{g:g}" for g in intensities])
        axis.set_xlabel("stiffness n")
        axis.set_ylabel("intensity gamma")
        axis.set_title(f"Uplift over the current mode, %   (w = {weight:g})")
        for row in range(len(intensities)):
            for column in range(len(stiffnesses)):
                value = grid[row, column]
                # A cell that did not clear is labelled, not left blank: refusing to
                # solve is a result about that corner of the parameter space.
                text = "x" if not np.isfinite(value) else f"{value:.0f}"
                axis.text(
                    column,
                    row,
                    text,
                    ha="center",
                    va="center",
                    fontsize=7.5,
                    color="0.6"
                    if not np.isfinite(value)
                    else ("white" if value < np.nanmax(grid) * 0.6 else "black"),
                )
        figure.colorbar(image, ax=axis, shrink=0.85)

    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / "saturation_map.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)

    print(f"wrote {target}")
    for weight, grid in zip((0.0, 1.0), grids):
        failed = int(np.sum(~np.isfinite(grid)))
        print(
            f"  w={weight:g}: range {np.nanmin(grid):6.1f} to {np.nanmax(grid):6.1f} %, "
            f"gamma=0 row {'flat at 0' if np.allclose(grid[0], 0, atol=1e-6) else 'NOT zero'}, "
            f"{failed} cell(s) did not clear"
        )
    return grids


if __name__ == "__main__":
    one_at_a_time()
    saturation_map()

"""Why ``w > 0`` did not converge, watched rather than inferred -- and the fix.

Usage::

    poetry run python -m fuel_clearing_step1.convergence          # run, then plot
    poetry run python -m fuel_clearing_step1.convergence --plot   # plot the saved run

REPORT.md section 8.3 concluded that the ``w = 1`` failure is a *discontinuous dual*:
the price is a function of which constraints are tight, that set changes as the traffic
loop moves demand, and a quantity that jumps cannot be the input to a fixed-point
iteration. That was an inference from the shape of the residual. It is not the only
story consistent with a residual that will not fall -- a gain above one, a badly scaled
coupling and an outright bug all look similar from outside -- so it is recorded here as
a measurement instead.

The kernel now reports ``active_signature``: a digest of which constraints are tight,
taken from the PRIMAL slacks, never from the multipliers. Reading the active set off the
duals would beg the question, since whether a multiplier is non-zero is exactly what
degenerates. Two iterations with the same signature solved the same linear system for
their prices; a signature that flips back and forth between two values is the
discontinuity, seen.

Three runs, same scenario, same scarcity:

``w=0``
    the price is a function of volumes. Expected to converge, and the control: if this
    one also showed a flipping signature, the signature would be measuring nothing.
``w=1``, rigid balance
    the price is a function of the duals. The failure as it stands.
``w=1``, demand-anchored
    the same, with a slope on the energy balance, so that where supply is vertical the
    price is read off the demand side instead of the cost side. The added term is inert
    once the loop settles, so this converges to a solution of the *unregularised*
    program or not at all.
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
CONFIG = HERE / "scenario" / "regionalisation_market.yaml"
RESULTS = HERE / "convergence.json"
FIGURES = HERE / "figures"

# The scarcity the coupled grid uses, so this diagnoses the same market that grid ran on.
SCARCE = dict(rampup_limit=0.20, rampup_seed_share=0.005, capacity=1.1e13, buyout_price=0.30)

# The loop is stopped at a tolerance the market can actually reach. Clarabel returns the
# conic duals to `solver_tolerance` (1e-9), and the chain amplifies that: the residual
# floor measured here is 2-3e-8, so roughly 100x the solver's own figure. It is NOT a
# constant to pick once -- it moved when the kerosene plumbing was fixed, because
# removing a strictly convex term costs the solver accuracy. See REPORT.md section 8.7,
# and the control there: a cell that converges at both tolerances returns a
# bit-identical answer, so this loosens the stopping rule and not the result.
MDA_TOLERANCE = 1.0e-7

CASES = {
    "w0": dict(pricing_weight=0.0),
    "w1_plain": dict(pricing_weight=1.0),
    "w1_anchored": dict(pricing_weight=1.0, demand_elasticity=0.5),
}

LABELS = {
    "w0": "w = 0  (price from volumes)",
    "w1_plain": "w = 1, rigid balance",
    "w1_anchored": "w = 1, demand-anchored",
}
COLOURS = {"w0": "#2f6b4f", "w1_plain": "#a93226", "w1_anchored": "#1f5f8b"}

# The left panel is cut here: past it the failing run repeats exactly and the
# converged ones are flat, so the extra 130 sweeps cost legibility and add nothing.
_LEFT_PANEL_SWEEPS = 70


def _run_one(settings, tag):
    """One MDA, with the market's per-iteration trace switched on."""
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    config = yaml.safe_load(CONFIG.read_text())
    config["regionalisation"]["mda_tolerance"] = MDA_TOLERANCE
    config["regionalisation"]["global_models"]["settings"] = {
        "fuel_clearing": {**SCARCE, **settings}
    }
    target = CONFIG.parent / f"_convergence_{tag}.yaml"
    target.write_text(yaml.safe_dump(config))

    record = {"settings": settings}
    try:
        process = MultiRegionalProcess(str(target))
        market = process.models["fuel_clearing"]
        market.record_trace = True
        market.trace = []
        try:
            process.compute()
            record["ok"] = True
        except Exception as exc:  # a run that does not converge still leaves a trace
            record["ok"] = False
            record["error"] = f"{type(exc).__name__}: {exc}"[:300]
        record["trace"] = market.trace
    finally:
        target.unlink(missing_ok=True)
    return record


def run():
    warnings.resetwarnings()
    warnings.simplefilter("ignore")
    logging.disable(logging.INFO)

    results = {}
    for tag, settings in CASES.items():
        results[tag] = _run_one(settings, tag)
        trace = results[tag]["trace"]
        signatures = [step["signature"] for step in trace]
        print(
            f"{tag:12s} ok={results[tag]['ok']}  iterations={len(trace)}  "
            f"distinct active sets={len(set(signatures))}",
            flush=True,
        )
        RESULTS.write_text(json.dumps(results, indent=1))
    return results


def _series(trace, key, region=0, year=-1):
    return [step[key][region][year] for step in trace]


def _worst_cell(trace, key="marginal"):
    """The (region, year) whose price moves most in the second half of a run.

    Picked from the FAILING run and then plotted for all three, because a cell that has
    settled looks identical under every treatment and would show nothing. Region A in
    2050 is such a cell: the trouble is elsewhere, and choosing the panel by eye rather
    than by measurement is how the first version of this figure came to look reassuring.
    """
    values = np.asarray([step[key] for step in trace])  # (iterations, R, T)
    tail = values[len(values) // 2 :]
    spread = tail.max(axis=0) - tail.min(axis=0)
    return np.unravel_index(int(np.argmax(spread)), spread.shape)


def plot(results=None):
    results = results or json.loads(RESULTS.read_text())

    figure, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), constrained_layout=True)

    # -- left: the price, at the cell the failing run cannot settle -------------
    failing = results.get("w1_plain", {}).get("trace") or next(
        r["trace"] for r in results.values() if r["trace"]
    )
    region, year = _worst_cell(failing)
    for tag, record in results.items():
        trace = record["trace"]
        if not trace:
            continue
        price = _series(trace, "marginal", region=region, year=year)
        # The failing run repeats identically after its first few dozen sweeps, so the
        # panel is cut where information stops arriving rather than where the run stops.
        # Drawn thin and without markers because at this density the markers merge into
        # a solid block and hide everything plotted underneath them.
        axes[0].plot(
            range(1, min(len(price), _LEFT_PANEL_SWEEPS) + 1),
            price[:_LEFT_PANEL_SWEEPS],
            "-" if tag == "w1_plain" else "-o",
            color=COLOURS[tag],
            markersize=3,
            linewidth=0.8 if tag == "w1_plain" else 1.5,
            alpha=0.85 if tag == "w1_plain" else 1.0,
            label=LABELS[tag],
        )
    # The two values the failing run alternates between ARE the ends of the interval the
    # multiplier is free in at this cell. Shading them is the clearest statement of the
    # whole diagnosis: the anchored run does not split the difference by damping, it
    # lands on the one point of that interval the demand curve selects.
    tail = np.asarray(_series(failing, "marginal", region=region, year=year))[len(failing) // 2 :]
    low, high = float(tail.min()), float(tail.max())
    axes[0].axhspan(low, high, color=COLOURS["w1_plain"], alpha=0.08, zorder=0)
    settled = results.get("w1_anchored", {}).get("trace")
    if settled:
        final = _series(settled, "marginal", region=region, year=year)[-1]
        axes[0].annotate(
            f"the interval $\\lambda$ is free in,\n{100 * (high - low) / low:.0f}% wide\n"
            f"\u2192 demand picks {final:.5f}",
            xy=(_LEFT_PANEL_SWEEPS * 0.80, final),
            xytext=(_LEFT_PANEL_SWEEPS * 0.30, low + 0.22 * (high - low)),
            fontsize=8,
            color="0.15",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="0.75", alpha=0.95),
            arrowprops=dict(arrowstyle="->", color="0.35", linewidth=1.0),
        )
    axes[0].set_xlabel("market solve (coupling iteration)")
    axes[0].set_ylabel(f"marginal price, region {'AB'[region]} {2020 + year}")
    axes[0].set_title(
        "What the loop is trying to converge\n"
        f"(the cell that moves most; first {_LEFT_PANEL_SWEEPS} sweeps, the rest repeat)",
        fontsize=10,
    )
    axes[0].legend(frameon=True, framealpha=0.95, edgecolor="0.8", fontsize=8, loc="lower right")

    # -- middle: the active set, as a category per iteration --------------------
    # Signatures are hashes, so they are mapped to integers in order of first
    # appearance: the VALUE means nothing, only whether it changes.
    for row, (tag, record) in enumerate(results.items()):
        trace = record["trace"]
        if not trace:
            continue
        order = {}
        for step in trace:
            order.setdefault(step["signature"], len(order))
        index = [order[step["signature"]] for step in trace]
        axes[1].plot(
            range(1, len(index) + 1),
            np.asarray(index) + 0.06 * row,
            "-o",
            color=COLOURS[tag],
            markersize=3,
            linewidth=1.4,
            label=LABELS[tag],
        )
    axes[1].set_xlabel("market solve (coupling iteration)")
    axes[1].set_ylabel("active set, numbered by first appearance")
    axes[1].set_title("Which constraints are tight", fontsize=10)
    axes[1].legend(frameon=True, framealpha=0.95, edgecolor="0.8", fontsize=8, loc="center right")

    # -- right: how far each solve sat from its anchor -------------------------
    anchored = results.get("w1_anchored", {}).get("trace", [])
    gaps = [
        step["demand_adjustment"] for step in anchored if step.get("demand_adjustment") is not None
    ]
    if gaps:
        axes[2].semilogy(
            range(2, len(gaps) + 2), gaps, "-o", color=COLOURS["w1_anchored"], markersize=3
        )
    axes[2].set_xlabel("market solve (coupling iteration)")
    axes[2].set_ylabel("max |a| / demand")
    axes[2].set_title(
        "How far the balance was bent\n(at zero the term is inert and the prices are exact)",
        fontsize=10,
    )

    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle(
        "The w > 0 failure is a changing active set, and an anchored solve removes it",
        fontsize=11.5,
    )

    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / "convergence.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)
    print(f"wrote {target}")
    return results


def summarise(results=None):
    """The numbers the report quotes, printed rather than eyeballed off the figure."""
    results = results or json.loads(RESULTS.read_text())
    for tag, record in results.items():
        trace = record["trace"]
        if not trace:
            print(f"{tag}: no trace")
            continue
        signatures = [step["signature"] for step in trace]
        price = np.asarray(_series(trace, "delivered"))
        tail = price[-8:]
        swing = (tail.max() - tail.min()) / tail.mean() if tail.mean() else float("nan")
        # How often the active set changed from one solve to the next, over the last
        # half of the run -- an early change is just the loop finding its feet.
        half = signatures[len(signatures) // 2 :]
        flips = sum(a != b for a, b in zip(half, half[1:]))
        print(
            f"{tag:12s} ok={str(record['ok']):5s} solves={len(trace):3d} "
            f"distinct active sets={len(set(signatures)):2d} "
            f"flips in 2nd half={flips:3d} "
            f"last-8 price swing={swing:.3%}"
        )
        if not record["ok"]:
            print(f"{'':12s} {record.get('error', '')}")


if __name__ == "__main__":
    if "--plot" in sys.argv:
        plot()
        summarise()
    else:
        outcome = run()
        plot(outcome)
        summarise(outcome)

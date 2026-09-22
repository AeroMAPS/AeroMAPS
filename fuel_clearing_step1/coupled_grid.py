"""Measurement 4.5.1, coupled: the saturation grid run through the full MDA.

Usage::

    poetry run python -m fuel_clearing_step1.coupled_grid          # run, then plot
    poetry run python -m fuel_clearing_step1.coupled_grid --plot   # plot the saved run

The kernel-level map in ``sensitivity.saturation_map`` holds the volumes fixed by
construction: it reads the market alone, at a demand the market does not influence. Here
the market sits inside the traffic loop, so a higher price cuts demand, which cuts the
volume, which relieves the scarcity that raised the price. The measurement is how much
of the kernel-level effect survives that feedback.

Each cell is a full two-region MDA, so the grid costs minutes rather than seconds and
its results are saved to ``coupled_grid.json`` rather than recomputed for the figure.

**No acceleration, and no need for it.** An earlier version of this grid applied Secant
to the inner MDAs because ``w = 1`` would not converge otherwise, and still lost most of
the ``w = 1`` row. The cause was not the solver: the price at ``w = 1`` is a multiplier,
and a multiplier jumps when the set of tight constraints changes, which no acceleration
scheme can smooth (``convergence.py`` measures the jump). Giving the balance a demand
slope removes it at the source, and plain Gauss-Seidel then converges -- so the
acceleration is gone from here, along with the claim that it was what helped.
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
RESULTS = HERE / "coupled_grid.json"
FIGURES = HERE / "figures"

# Scarcity held fixed while the saturation pair is swept, so the grid isolates it.
SCARCE = dict(rampup_limit=0.20, rampup_seed_share=0.005, capacity=1.1e13, buyout_price=0.30)
# The demand slope the market prices against where its own supply curve is vertical. It
# is inert at the fixed point, so it changes which cells converge and not what they
# converge to; 0.5 is the fastest value on this bench (fuel_clearing_step1/convergence.py).
ANCHOR = dict(demand_elasticity=0.5)
# The loop is stopped at a tolerance the market can actually reach. Clarabel returns the
# conic duals to `solver_tolerance` (1e-9), which is about 3e-9 of demand once scaled --
# and refuses the stiffest cones outright if asked for better. The default 1e-10 is a
# digit below that floor, so at n=16 the loop reported non-convergence having converged:
# zero active-set changes, the price stationary to 1e-11, residual pinned at 2.86e-9.
# Measured on a cell that converges either way (n=8), 1e-8 returns a bit-identical
# answer, so this loosens the stopping rule and not the result.
MDA_TOLERANCE = 1.0e-8
STIFFNESSES = (2.0, 4.0, 8.0, 16.0)
INTENSITIES = (0.5, 1.0, 2.0)
WEIGHTS = (0.0, 1.0)


def _run_one(settings, tag):
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    config = yaml.safe_load(CONFIG.read_text())
    config["regionalisation"]["mda_tolerance"] = MDA_TOLERANCE
    if settings:
        config["regionalisation"]["global_models"]["settings"] = {"fuel_clearing": settings}
    target = CONFIG.parent / f"_coupled_grid_{tag}.yaml"
    target.write_text(yaml.safe_dump(config))
    try:
        process = MultiRegionalProcess(str(target))
        process.compute()
        outputs = process.data["vector_outputs"]
        region = process.list_regions()[0]
        return dict(
            ok=True,
            delivered=float(outputs[f"{region}:dropin_fuel_mean_mfsp"].loc[2050]),
            compliance=float(outputs[f"{region}:fuel_market_compliance_price"].max()),
            rpk=float(outputs[f"{region}:rpk"].loc[2050]),
            co2=float(outputs[f"{region}:co2_emissions_passenger"].loc[2050]),
            share=float(outputs[f"{region}:hefa_fog_share_dropin_fuel"].loc[2050]),
        )
    except Exception as exc:  # a cell that does not converge is a result, not a crash
        return dict(ok=False, error=f"{type(exc).__name__}: {exc}"[:200])
    finally:
        target.unlink(missing_ok=True)


def run():
    warnings.resetwarnings()
    warnings.simplefilter("default")
    logging.disable(logging.INFO)

    results = {"reference": _run_one(dict(ANCHOR), "ref")}
    print("reference (no scarcity):", results["reference"], flush=True)
    for weight in WEIGHTS:
        for gamma in INTENSITIES:
            for stiffness in STIFFNESSES:
                key = f"w{weight:g}_g{gamma:g}_n{stiffness:g}"
                results[key] = _run_one(
                    {
                        **SCARCE,
                        **ANCHOR,
                        "saturation_intensity": gamma,
                        "saturation_stiffness": stiffness,
                        "pricing_weight": weight,
                    },
                    key,
                )
                print(f"  {key:16s} {results[key]}", flush=True)
                RESULTS.write_text(json.dumps(results, indent=1))
    return results


def plot(results=None):
    """Delivered price and the traffic response, against the kernel-level expectation."""
    results = results or json.loads(RESULTS.read_text())
    reference = results["reference"]

    figure, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), constrained_layout=True)
    colours = {0.5: "#1f77b4", 1.0: "#d62728", 2.0: "#2f6b4f"}

    for weight, style in zip(WEIGHTS, ("-o", "--s")):
        for gamma in INTENSITIES:
            price, traffic = [], []
            for stiffness in STIFFNESSES:
                cell = results.get(f"w{weight:g}_g{gamma:g}_n{stiffness:g}", {})
                ok = cell.get("ok")
                price.append(
                    100 * (cell["delivered"] - reference["delivered"]) / reference["delivered"]
                    if ok
                    else np.nan
                )
                traffic.append(
                    100 * (cell["rpk"] - reference["rpk"]) / reference["rpk"] if ok else np.nan
                )
            label = f"gamma={gamma:g}, w={weight:g}"
            axes[0].plot(STIFFNESSES, price, style, color=colours[gamma], label=label, markersize=4)
            axes[1].plot(
                STIFFNESSES, traffic, style, color=colours[gamma], label=label, markersize=4
            )

    axes[0].set_ylabel("delivered price vs no scarcity, %")
    axes[1].set_ylabel("RPK 2050 vs no scarcity, %")
    for axis in axes:
        axis.set_xlabel("saturation stiffness n")
        axis.set_xscale("log", base=2)
        axis.set_xticks(STIFFNESSES, [f"{s:g}" for s in STIFFNESSES])
        axis.axhline(0.0, color="0.6", linewidth=1, linestyle=":")
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, fontsize=8, ncol=2)
    axes[0].set_title("What the market charges", fontsize=10)
    axes[1].set_title("What the traffic loop does about it", fontsize=10)
    figure.suptitle(
        "Measurement 4.5.1, coupled: saturation swept through the full MDA, region A",
        fontsize=11,
    )

    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / "coupled_grid.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)
    print(f"wrote {target}")
    return results


if __name__ == "__main__":
    plot() if "--plot" in sys.argv else plot(run())

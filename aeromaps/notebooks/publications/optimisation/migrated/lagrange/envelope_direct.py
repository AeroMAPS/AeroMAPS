"""Measure d f*/d(carbon budget) directly, by re-optimising at a perturbed bound.

This is the ground truth the multiplier is supposed to equal. Every other check
in this folder infers the derivative from the sweep grid, whose spacing (0.2 in
the budget share) is far too coarse to resolve it near an active-set change.
Here the bound is moved by a hundredth of a share point and the problem is
re-solved from the stored optimum, so the two points are on the same branch and
the secant is a genuine derivative.

The perturbed solves use **tight** solver settings, not the published ones. The
objective changes by only ~0.5 scaled units across the ±0.01 perturbation, so a
solver that stops within ``ftol_abs=0.001`` of its optimum - the published
setting - can corrupt the secant by several percent, and the "ground truth"
would then inherit exactly the defect it is meant to measure. Measured on
``main`` at 2.8, the loose settings gave -8.9 % against the multiplier where the
tight ones are needed to tell whether that is real.

It writes nothing to ``results/``. ``budget_tag`` rounds to one decimal, so a
run at 2.59 would land on ``opt_<case>_2_6.hdf`` and overwrite the published
history; these runs are kept in memory and reported instead.
"""

from __future__ import annotations

import json
import sys
import time
import warnings

import numpy as np
import pandas as pd

from gemseo.algos.opt.scipy_local.settings.slsqp import SLSQP_Settings

from pathlib import Path

# optimisation_runs.py lives one level up, beside the notebooks.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import optimisation_runs as R
from aeromaps.core.gemseo import disable_gemseo_execution_statistics
from extract_multipliers import OUT, RESULTS, _restore

EU_ASK_SHARE = 15.49 / 100
GROSS_BUDGET_2050_GTCO2 = 799.189271182
DELTA = 0.01  # share points either side


FTOL = 1e-8
KKT_TOL_REL = 1e-6


def solve_at(case: str, budget: float, x0, max_iter: int = 200):
    """One optimisation at an arbitrary budget, started from ``x0``, not saved."""
    process = R.build_process(case, optimisation=True, carbon_budget=budget)
    R.setup_optimisation(process, x0=x0, max_iter=max_iter)
    # Tighter than the published sweep: see the module docstring.
    process.gemseo_settings["algorithm"] = SLSQP_Settings(
        max_iter=max_iter,
        enable_progress_bar=False,
        ftol_abs=FTOL,
        ftol_rel=FTOL,
        kkt_tol_rel=KKT_TOL_REL,
        normalize_design_space=False,
    )
    start = time.perf_counter()
    process.compute()
    result = process.scenario.get_result().optimization_result
    return {
        "budget": budget,
        "f_opt": float(result.f_opt),
        "feasible": bool(result.is_feasible),
        "seconds": round(time.perf_counter() - start, 1),
        "message": str(result.message),
        "n_iter": len(process.scenario.formulation.optimization_problem.database),
    }


def envelope_at(case: str, budget: float, delta: float = DELTA):
    """Central difference of the optimal objective about ``budget``."""
    tag = f"{budget:.1f}".replace(".", "_")
    stored = _restore(RESULTS / f"opt_{case}_{tag}.hdf")
    x = np.asarray(stored.solution.x_opt, float)
    x0 = {"electrofuel": list(x[:5]), "biofuel": list(x[5:])}

    low = solve_at(case, budget - delta, x0)
    high = solve_at(case, budget + delta, x0)

    payload = json.loads((RESULTS / f"opt_{case}_{tag}.json").read_text())
    cumulative = np.asarray(payload["vector_outputs"]["cumulative_co2_emissions"], float)
    budget_adjusted = (
        GROSS_BUDGET_2050_GTCO2 * payload["float_inputs"]["aviation_carbon_budget_objective"] / 100
        - cumulative[2025 - 2000]
    )
    d_budget_d_share = GROSS_BUDGET_2050_GTCO2 * EU_ASK_SHARE / 100
    slope = (high["f_opt"] - low["f_opt"]) / (2 * delta) / 1e-10
    price = -slope / (d_budget_d_share * 1e9)

    table = pd.read_csv(OUT / "lagrange_multipliers.csv")
    row = table[(table.run == f"opt_{case}_{tag}") & (table.constraint == "G1")]
    reported = float(row.shadow_price_eur_per_tco2_discounted2020.iloc[0]) if len(row) else np.nan
    return {
        "case": case,
        "budget": budget,
        "f_lo": low["f_opt"],
        "f_hi": high["f_opt"],
        "feasible_lo": low["feasible"],
        "feasible_hi": high["feasible"],
        "seconds": low["seconds"] + high["seconds"],
        "direct_price_eur_per_tco2": price,
        "reported_lambda_G1_eur_per_tco2": reported,
        "relative_error": (reported - price) / price if price else np.nan,
        "budget_adjusted_gtco2": budget_adjusted,
    }


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    # GEMSEO takes a shared-memory Value per discipline and macOS allows 32
    # segments system-wide, so several of these at once fail with ENOSPC unless
    # the statistics are disabled first.
    disable_gemseo_execution_statistics()
    targets = [("B15", 2.6), ("main", 2.6)]
    if len(sys.argv) > 1:
        targets = [(a.split(":")[0], float(a.split(":")[1])) for a in sys.argv[1:]]
    rows = []
    for case, budget in targets:
        row = envelope_at(case, budget)
        rows.append(row)
        print(
            f"{case} @ {budget}: direct = {row['direct_price_eur_per_tco2']:.1f}, "
            f"reported lambda = {row['reported_lambda_G1_eur_per_tco2']:.1f}, "
            f"rel err = {row['relative_error']:+.1%}  ({row['seconds']:.0f} s)",
            flush=True,
        )
    suffix = "_" + "_".join(f"{c}{b:g}" for c, b in targets) if len(sys.argv) > 1 else ""
    pd.DataFrame(rows).to_csv(OUT / f"envelope_direct{suffix}.csv", index=False)
    print("\ndone", flush=True)

"""Elasticity sweep: cost-optimal mandate at a fixed carbon budget, five elasticities.

Carbon budget fixed at 2.8 % of the world aviation budget throughout; every other
parameter at baseline. The eps -> 0 anchor is run with the ``cost`` objective,
because the isoelastic surplus integral divides by the elasticity and is undefined
at zero; that objective is the airline-cost term of the surplus objective, which is
exactly what the published problem reduces to when demand cannot respond.

Resumable: a run whose .hdf is already on disk is skipped.

Usage:  poetry run python run_sweep.py [eps ...]
"""

from __future__ import annotations

import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
sys.path.insert(0, str(PAPER))

import optimisation_runs as R  # noqa: E402
from aeromaps.core.gemseo import disable_gemseo_execution_statistics  # noqa: E402
from gemseo.algos.opt.scipy_local.settings.slsqp import SLSQP_Settings  # noqa: E402

os.chdir(PAPER)  # config yamls resolve against the working directory

RESULTS = HERE / "results"

# The paper's default is ftol_abs=1e-3, which on a scaled objective of order 5 is a
# relative tolerance of ~2e-4. That is loose enough to stop SLSQP after 19 evaluations
# with the design still moving; on the carbon-budget sweep the same setting shifted
# mandate shares by up to 11.8 percentage points. The mandate share is exactly what
# this sweep reports, so it is tightened here.
FTOL = 1e-8
KKT_TOL_REL = 1e-6

_ORIGINAL_SETUP = R.setup_optimisation


def _tighten(process, *args, **kwargs):
    """setup_optimisation, then replace only the solver settings."""
    result = _ORIGINAL_SETUP(process, *args, **kwargs)
    process.gemseo_settings["algorithm"] = SLSQP_Settings(
        max_iter=kwargs.get("max_iter", MAX_ITER),
        enable_progress_bar=True,
        ftol_abs=FTOL,
        ftol_rel=FTOL,
        kkt_tol_rel=KKT_TOL_REL,
        normalize_design_space=False,
    )
    return result


CARBON_BUDGET = 2.8
CASE = "main"
MAX_ITER = 100
ELASTICITIES = [0.0, -0.6, -0.8, -0.9, -1.0, -1.4]
CONSTRAINTS = {
    "aviation_carbon_budget_constraint": "G1",
    "blend_completeness_constraint": "G2",
    "biomass_trajectory_constraint": "G3",
    "electricity_trajectory_constraint": "G4",
    "biofuel_use_growth_constraint": "G5",
    "electrofuel_use_growth_constraint": "G6",
}
OPTIM_YEARS = [2030, 2035, 2040, 2045, 2050]


def _max_violation(problem) -> float:
    """Largest inequality violation at the optimum (0 if fully feasible)."""
    entry = problem.database[np.asarray(problem.solution.x_opt, float)]
    worst = 0.0
    for name in CONSTRAINTS:
        if name in entry:
            worst = max(worst, float(np.max(np.atleast_1d(np.asarray(entry[name], float)))))
    return max(worst, 0.0)


def stem_for(eps: float) -> Path:
    return RESULTS / f"eps_{eps:g}".replace(".", "_").replace("-", "m")


def run_one(eps: float, x0=None) -> dict:
    """One optimisation. Returns solver diagnostics."""
    stem = stem_for(eps)
    if stem.with_suffix(".hdf").exists():
        print(f"  eps={eps}: on disk, skipped", flush=True)
        return {"eps": eps, "skipped": True}

    # The eps -> 0 anchor is not the elasticity model evaluated at zero: it is the
    # formulation with no airfare <-> RPK coupling at all -- fixed demand, the
    # non-feedback cost chain, minimising airline cost. Anything else leaves an MDA
    # iterating a loop that is not there.
    no_feedback = eps == 0.0
    objective = "cost" if no_feedback else "surplus"
    config = "config_rte_nofeedback.yaml" if no_feedback else "config_rte.yaml"

    t0 = time.perf_counter()
    process = R.build_process(CASE, config=config, optimisation=True, carbon_budget=CARBON_BUDGET)
    if not no_feedback:
        process.parameters.price_elasticity = eps
    # setup_optimisation installs the shared-MDA cache itself, after it has created
    # the GEMSEO scenario; calling it here as well fails on a scenario that does
    # not exist yet.
    _tighten(process, x0=x0, max_iter=MAX_ITER, objective=objective)
    process.compute()

    result = process.scenario.get_result().optimization_result
    problem = process.scenario.formulation.optimization_problem
    RESULTS.mkdir(parents=True, exist_ok=True)
    R._save(process, stem)  # history first, then outputs -- same format as the paper's runs

    diag = {
        "eps": eps,
        "objective": objective,
        "f_opt": float(result.f_opt),
        "feasible": bool(result.is_feasible),
        "message": str(result.message),
        "n_evaluations": len(problem.database),
        "max_constraint_violation": _max_violation(problem),
        "ftol_abs": FTOL,
        "kkt_tol_rel": KKT_TOL_REL,
        "seconds": round(time.perf_counter() - t0, 1),
        "skipped": False,
    }
    print(
        f"  eps={eps}: f={diag['f_opt']:.6g} feasible={diag['feasible']} "
        f"({diag['seconds']:.0f} s, {diag['n_evaluations']} evals)",
        flush=True,
    )
    return diag


def active_set_table() -> pd.DataFrame:
    """Step 2 deliverable: run x constraint x year, active/inactive."""
    from gemseo.algos.optimization_problem import OptimizationProblem

    rows = []
    for eps in ELASTICITIES:
        path = stem_for(eps).with_suffix(".hdf")
        if not path.exists():
            continue
        problem = OptimizationProblem.from_hdf(str(path))
        x = np.asarray(problem.solution.x_opt, float)
        tol = float(problem.tolerances.inequality)
        entry = problem.database[x]
        for name, family in CONSTRAINTS.items():
            if name not in entry:
                continue
            arr = np.atleast_1d(np.asarray(entry[name], float))
            years = [None] if family == "G1" else OPTIM_YEARS
            for i, year in enumerate(years):
                if i >= len(arr):
                    continue
                rows.append(
                    {
                        "eps": eps,
                        "constraint": family,
                        "year": year,
                        "value": float(arr[i]),
                        "active": bool(abs(arr[i]) <= tol),
                    }
                )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    disable_gemseo_execution_statistics()
    targets = [float(a) for a in sys.argv[1:]] or ELASTICITIES

    print(f"=== elasticity sweep, carbon budget {CARBON_BUDGET} %, case {CASE} ===", flush=True)
    diagnostics, x0 = [], None
    for eps in targets:
        diagnostics.append(run_one(eps, x0=x0))

    pd.DataFrame(diagnostics).to_csv(HERE / "sweep_diagnostics.csv", index=False)
    table = active_set_table()
    if len(table):
        table.to_csv(HERE / "sweep_active_set.csv", index=False)
        print(f"\nactive-set table: {len(table)} rows -> sweep_active_set.csv", flush=True)
    print(f"diagnostics -> {HERE / 'sweep_diagnostics.csv'}", flush=True)

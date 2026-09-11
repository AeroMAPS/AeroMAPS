"""The section 1 optimisation: case main at the ReFuelEU-equivalent carbon budget.

The budget the paper's headline run is held to is the one ReFuelEU itself implies --
3.8656495 GtCO2 cumulative 2020-2050, 3.122636344 % of the world budget -- so that the
optimum and the regulation it is compared against consume the same carbon. That value
falls between the 3.2 and 3.0 rungs of the block E ladder, so it needs its own run.

Blocks A-D already contain an optimisation at exactly this budget, ``base``. This one is
not a copy of it: ``base`` is seeded from the previous sweep's optimum, and this is
warm-started from the ladder's 3.2 optimum. On a non-convex problem the start
point can decide which local optimum SLSQP lands on, so the two are worth comparing --
the script prints the comparison and says whether they agree.

The same budget is also run for the other cases -- the three biomass allocations and
the pessimistic roadmap -- so the sensitivity summary can compare every case at the one
budget blocks A-D are held to. Each is warm-started from its own 3.2 rung, the way
``main`` is, and saved as ``opt_<case>_refueleu``.

Usage:  poetry run python run_refueleu_budget.py [case ...]     # default: main
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
sys.path.insert(0, str(PAPER))
sys.path.insert(0, str(HERE))

import optimisation_runs as R  # noqa: E402
from run_batch import BIOMASS_SHARE, BUDGET_GTCO2, BUDGET_WORLD_SHARE, FTOL, KKT_TOL_REL  # noqa: E402
from run_block_e import BIOMASS_OVERRIDE, MAX_ITER, RESULTS_E  # noqa: E402

CASES = ("main", "B5", "B75", "B15", "pess")


def stem(case):
    return RESULTS_E / f"opt_{case}_refueleu"


def main(case="main"):
    from aeromaps.core.gemseo import disable_gemseo_execution_statistics
    from gemseo import configure_logger
    from gemseo.algos.opt.scipy_local.settings.slsqp import SLSQP_Settings

    configure_logger(level=logging.INFO)
    disable_gemseo_execution_statistics()
    os.chdir(PAPER)

    out = stem(case)
    warm_from = RESULTS_E / f"opt_{case}_3_2.hdf"
    # The ladder's convention: main and pess at a round 10 %, the biomass cases at the
    # allocation that defines them.
    biomass = BIOMASS_OVERRIDE.get(case, R.CASES[case]["biomass_share"])
    if out.with_suffix(".json").exists():
        print(f"{out.name}: on disk, skipped")
    else:
        warm = R.read_run(warm_from)
        if warm is None or not warm["feasible"]:
            raise SystemExit(f"need a feasible {warm_from.name} to warm-start from")

        process = R.build_process(
            case,
            config="config_rte.yaml",
            optimisation=True,
            carbon_budget=BUDGET_WORLD_SHARE,
        )
        process.parameters.generic_biomass_availability_aviation_allocated_share = (
            biomass * R.EU_ASK_SHARE
        )
        R.setup_optimisation(process, x0=warm["x"], max_iter=MAX_ITER, objective="surplus")
        process.gemseo_settings["algorithm"] = SLSQP_Settings(
            max_iter=MAX_ITER,
            enable_progress_bar=True,
            ftol_abs=FTOL,
            ftol_rel=FTOL,
            kkt_tol_rel=KKT_TOL_REL,
            normalize_design_space=False,
        )

        print(f"=== {case} at the ReFuelEU-equivalent budget ===", flush=True)
        print(f"    {BUDGET_WORLD_SHARE:.9f} % world share = {BUDGET_GTCO2:.10f} GtCO2", flush=True)
        print(f"    biomass {biomass} % (batch uses {BIOMASS_SHARE} %)", flush=True)
        print(f"    warm-started from {warm_from.name}", flush=True)

        started = time.perf_counter()
        process.compute()
        R._save(process, out)
        result = process.scenario.get_result().optimization_result
        print(
            f"--- f={float(result.f_opt):.6f} feasible={bool(result.is_feasible)} "
            f"({time.perf_counter() - started:.0f} s)",
            flush=True,
        )

    if case == "main":
        compare()


def compare():
    """Against ``base``, which reached the same budget from a different start."""
    ladder = R.read_run(stem("main").with_suffix(".hdf"))
    cold = R.read_run(HERE / "results" / "base.hdf")
    if ladder is None or cold is None:
        return

    def flat(run):
        return np.array(run["x"]["electrofuel"] + run["x"]["biofuel"])

    gap = np.abs(flat(ladder) - flat(cold))
    print("\n=== warm-started (this run) vs cold-started (blocks A-D `base`) ===")
    print(
        f"  objective   {ladder['objective']:.6f}  vs {cold['objective']:.6f}"
        f"   ({abs(ladder['objective'] - cold['objective']):.2e})"
    )
    print(f"  design      max |dx| = {gap.max():.3e} percentage points")
    print(
        "  -> same optimum"
        if gap.max() < 1e-3
        else "  -> DIFFERENT local optima; the start point decided the answer"
    )


if __name__ == "__main__":
    requested = sys.argv[1:] or ["main"]
    unknown = [case for case in requested if case not in CASES]
    if unknown:
        raise SystemExit(f"unknown case(s) {unknown}; choose from {CASES}")
    for case in requested:
        main(case)

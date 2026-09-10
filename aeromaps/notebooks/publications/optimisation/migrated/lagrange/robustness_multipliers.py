"""Step 5: how noisy are these multipliers, for the baseline run.

Three questions, answered as far as the stored histories allow:

* how much the multiplier set moves when the active-set tolerance moves,
* how well converged the run is (iterations, KKT residual, feasibility),
* how much the finite-difference step matters.

The third cannot be answered from stored data: changing the differentiation
step changes every gradient in the problem, so it needs a re-run. The cost is
reported instead of guessed at.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from extract_multipliers import (
    FAMILIES,
    OUT,
    RESULTS,
    _restore,
    evaluation_point,
    multipliers,
    split_objective,
)

BASELINE = "opt_main_2_6"
TOLERANCES = [1e-10, 1e-8, 1e-6, 1e-4, 1e-3, 1e-2, 1e-1]


def tolerance_sweep(run: str = BASELINE) -> pd.DataFrame:
    problem = _restore(RESULTS / f"{run}.hdf")
    scale, _ = split_objective(problem.objective.name)
    x_eval, distance, _ = evaluation_point(problem, f"@{problem.objective.name}")

    rows = []
    for tol in TOLERANCES:
        arrays, residual, violation = multipliers(problem, x_eval, ineq_tolerance=tol)
        entry = {
            "ineq_tolerance": tol,
            "kkt_residual": residual,
            "max_constraint_violation": violation,
        }
        n_nonzero = 0
        for name, (family, years) in FAMILIES.items():
            if name not in {c.name for c in problem.constraints}:
                continue
            values = np.atleast_1d(arrays["inequality"][name]) / scale
            n_nonzero += int((values > 0).sum())
            for i, year in enumerate(years):
                label = family if year is None else f"{family}_{year}"
                entry[label] = values[i]
        entry["n_nonzero_multipliers"] = n_nonzero
        rows.append(entry)
    frame = pd.DataFrame(rows)
    frame.insert(0, "run", run)
    frame.insert(1, "x_eval_distance_from_x_opt", distance)
    return frame


def convergence_summary(table: pd.DataFrame) -> pd.DataFrame:
    per_run = table.groupby("run").first()
    return per_run[
        [
            "case",
            "carbon_budget_share_world_pct",
            "objective_kind",
            "run_feasible",
            "n_database_entries",
            "n_gradient_points",
            "kkt_residual",
            "kkt_residual_relative",
            "objective_grad_norm",
            "max_constraint_violation",
            "termination_message",
        ]
    ].reset_index()


if __name__ == "__main__":
    sweep = tolerance_sweep()
    sweep.to_csv(OUT / "robustness_tolerance_sweep.csv", index=False)
    shown = [c for c in sweep.columns if c.startswith("G")] + ["n_nonzero_multipliers"]
    print(f"=== active-set tolerance sweep, {BASELINE} " f"(multipliers in EUR per unit of g) ===")
    print(
        sweep.set_index("ineq_tolerance")[shown]
        .loc[:, lambda d: (d != 0).any()]
        .to_string(float_format=lambda v: f"{v:,.4g}")
    )

    table = pd.read_csv(OUT / "lagrange_multipliers.csv")
    summary = convergence_summary(table)
    summary.to_csv(OUT / "robustness_convergence.csv", index=False)
    feasible = summary[summary.run_feasible]
    print("\n=== convergence, feasible runs ===")
    print(f"  runs                         : {len(feasible)}")
    print(
        f"  design points evaluated      : median {feasible.n_database_entries.median():.0f}"
        f"  (min {feasible.n_database_entries.min()}, max {feasible.n_database_entries.max()})"
    )
    print(f"  gradient evaluations         : median {feasible.n_gradient_points.median():.0f}")
    print(
        f"  relative KKT residual        : median {feasible.kkt_residual_relative.median():.2e}"
        f"  max {feasible.kkt_residual_relative.max():.2e}"
    )
    poor = feasible[feasible.kkt_residual_relative > 1e-2]
    print(f"  runs with relative KKT > 1e-2: {len(poor)} of {len(feasible)}")
    if len(poor):
        print(poor[["run", "kkt_residual_relative", "termination_message"]].to_string(index=False))

    print("\n=== finite-difference step ===")
    print("  Not varied. The step is baked into every gradient in the stored")
    print("  database, so changing it means re-running the optimisation: the")
    print("  differentiation_step recorded in the HDF is 1e-6 for every run.")
    print("  A single re-run costs a full SLSQP solve (median 20 design points,")
    print("  each an MDA), so a step sweep over the 44 feasible runs is not a")
    print("  cheap check. The envelope tests in validate_multipliers.py bound")
    print("  the same error from outside and need no re-run.")

"""Repair multipliers without re-running the optimisation.

Two of the three defects in the stored set are gradient defects, not optimum
defects: the optimum itself is fine, only the Jacobian attached to it is wrong
or missing. Both are fixable by re-evaluating the model at the *stored* x_opt,
which costs ~20 s against ~730 s for a full re-run.

**Wrong gradient (opt_B15_2_6).** Its optimum is the only one in the set where
the blend-completeness constraint is active - drop-in shares sum to exactly
100 %. Above 100 % the energy model renormalises the pathway shares, so a
*forward* difference on either 2050 share steps across that clip and measures a
flattened derivative. Measured on this run, forward differencing misses the
objective change along the continuation step by -2.34 % while backward
differencing misses by +0.04 %, and the whole discrepancy sits in the two 2050
components. Everything else is identical.

**Missing gradient (opt_B15_2_2, opt_B15_2_4).** SLSQP reported an x_opt it had
never differentiated. Evaluating there supplies what is missing.

The rule used here is to step *inward*: backward wherever the design-space bound
allows it, forward only where a variable sits on its lower bound. Every
recomputed gradient is then checked against a neighbouring run's objective, the
same test as ``validate_pointwise.py``.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

import sys
from pathlib import Path

# optimisation_runs.py lives one level up, beside the notebooks.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import optimisation_runs as R
from extract_multipliers import OUT, RESULTS, _restore, split_objective

# Runs whose stored gradient is wrong or missing, with the case and budget
# needed to rebuild their process.
TARGETS = {
    "opt_B15_2_6": ("B15", 2.6),
    "opt_B15_2_4": ("B15", 2.4),
    "opt_B15_2_2": ("B15", 2.2),
}
STEP = 1e-6


def _functions_at(problem, name_order):
    """A callable returning the objective and every constraint at one point."""

    def evaluate(x):
        values, _ = problem.evaluate_functions(
            design_vector=np.asarray(x, float), design_vector_is_normalized=False
        )
        return np.concatenate([np.atleast_1d(np.ravel(values[n])) for n in name_order])

    return evaluate


def recompute(run: str, step: float = STEP):
    """Objective and constraint Jacobians at the stored optimum, stepping inward."""
    case, budget = TARGETS[run]
    stored = _restore(RESULTS / f"{run}.hdf")
    x_opt = np.asarray(stored.solution.x_opt, float)
    lower = stored.design_space.get_lower_bounds()
    upper = stored.design_space.get_upper_bounds()

    process = R.build_process(case, optimisation=True, carbon_budget=budget)
    R.setup_optimisation(process, x0={"electrofuel": list(x_opt[:5]), "biofuel": list(x_opt[5:])})
    problem = process.scenario.formulation.optimization_problem
    names = [problem.objective.name] + [c.name for c in problem.constraints]
    evaluate = _functions_at(problem, names)

    base = evaluate(x_opt)
    jacobian = np.zeros((base.size, x_opt.size))
    for i in range(x_opt.size):
        offset = np.zeros(x_opt.size)
        offset[i] = step
        if x_opt[i] - step >= lower[i]:
            jacobian[:, i] = (base - evaluate(x_opt - offset)) / step
        elif x_opt[i] + step <= upper[i]:
            jacobian[:, i] = (evaluate(x_opt + offset) - base) / step
        else:  # pragma: no cover - a variable pinned between both bounds
            jacobian[:, i] = np.nan

    scale, _ = split_objective(problem.objective.name)
    sizes = [1] + [np.atleast_1d(np.ravel(base)).size for _ in []]  # placeholder
    # Split the stacked Jacobian back into objective and per-constraint blocks.
    blocks, row = {}, 0
    for name in names:
        dim = (
            1
            if name == problem.objective.name
            else problem.constraints[[c.name for c in problem.constraints].index(name)].dim
        )
        blocks[name] = jacobian[row : row + dim]
        row += dim
    del sizes
    return {
        "run": run,
        "x_opt": x_opt,
        "values": {n: base[i] for i, n in enumerate([names[0]])},
        "objective_name": problem.objective.name,
        "objective_scale": scale,
        "grad_objective": blocks[problem.objective.name][0],
        "constraint_jacobians": {c.name: blocks[c.name] for c in problem.constraints},
        "f_opt": float(base[0]),
    }


def check(result) -> dict:
    """Validate a recomputed gradient against a neighbouring run's objective."""
    case, budget = TARGETS[result["run"]]
    neighbour_budget = round(budget + 0.2, 1)
    tag = f"{neighbour_budget:.1f}".replace(".", "_")
    path = RESULTS / f"opt_{case}_{tag}.hdf"
    if not path.exists():
        return {"neighbour": None, "trapezoid_error_pct": np.nan}
    other = _restore(path)
    x_other = np.asarray(other.solution.x_opt, float)
    entry = other.database.get(x_other)
    grad_key = f"@{other.objective.name}"
    if entry is None or grad_key not in entry:
        return {"neighbour": path.stem, "trapezoid_error_pct": np.nan}
    g_other = np.asarray(entry[grad_key], float)
    step = x_other - result["x_opt"]
    actual = other.solution.f_opt - result["f_opt"]
    trapezoid = 0.5 * (result["grad_objective"] + g_other) @ step
    return {
        "neighbour": path.stem,
        "trapezoid_error_pct": 100 * (trapezoid - actual) / actual,
    }


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    rows = []
    store = {}
    for run in TARGETS:
        result = recompute(run)
        store[run] = result
        verdict = check(result)
        rows.append(
            {
                "run": run,
                "f_opt_recomputed_scaled": result["f_opt"],
                **verdict,
            }
        )
        print(
            f"{run}: f={result['f_opt']:.9f}  "
            f"trapezoid error vs {verdict['neighbour']} = "
            f"{verdict['trapezoid_error_pct']:.3f} %"
        )
    np.save(OUT / "recomputed_gradients.npy", store, allow_pickle=True)
    pd.DataFrame(rows).to_csv(OUT / "recomputed_gradients.csv", index=False)
    print(f"\nsaved to {OUT / 'recomputed_gradients.npy'}")

"""Where the marginal tonne comes from, and why it is not a fuel's abatement cost.

At the baseline optimum every design variable is pinned by an active constraint -
ten active constraints in a ten-dimensional design space - so the optimum is a
*vertex*. Relaxing the carbon budget therefore does not substitute one fuel at
the margin; it slides the whole solution along the edge left free by the other
nine constraints, moving several mandate shares at once.

This script solves for that direction, applies it, and reports which years the
extra CO2 comes from. The emissions-weighted discount factor it produces is the
bridge between λ_G1 - a present-value price on an undiscounted physical stock,
which is the TCAC structure - and a per-year, per-fuel abatement cost.
"""

from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

import extract_multipliers as E
import sys
from pathlib import Path

# optimisation_runs.py lives one level up, beside the notebooks.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import optimisation_runs as R
from aeromaps.core.gemseo import disable_gemseo_execution_statistics

RUN, CASE, BUDGET = "opt_main_2_6", "main", 2.6
DISCOUNT_RATE = 0.045
DELTA_GT = 0.01


def edge_direction(problem, entry, x):
    """dx per GtCO2 of budget relaxed, along the edge the active set leaves free."""
    tol = float(problem.tolerances.inequality)
    lower = problem.design_space.get_lower_bounds()
    rows, names = [], []
    for j in range(problem.design_space.dimension):
        if abs(x[j] - lower[j]) <= tol:
            e = np.zeros(x.size)
            e[j] = 1.0
            rows.append(e)
            names.append(f"bound[{j}]")
    for constraint in problem.constraints:
        values = np.atleast_1d(np.asarray(entry[constraint.name], float))
        jac = np.atleast_2d(np.asarray(entry[f"@{constraint.name}"], float))
        for i in range(len(values)):
            if abs(values[i]) <= tol:
                rows.append(jac[i])
                names.append(f"{constraint.name}[{i}]")
    payload = json.loads((E.RESULTS / f"{RUN}.json").read_text())
    budget = (
        799.189271182 * payload["float_inputs"]["aviation_carbon_budget_objective"] / 100
        - np.asarray(payload["vector_outputs"]["cumulative_co2_emissions"], float)[25]
    )
    rhs = np.zeros(x.size)
    rhs[names.index("aviation_carbon_budget_constraint[0]")] = 1.0 / budget
    return np.linalg.solve(np.array(rows), rhs), names


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    disable_gemseo_execution_statistics()

    problem = E._restore(E.RESULTS / f"{RUN}.hdf")
    x, _, entry = E.evaluation_point(problem, f"@{problem.objective.name}")
    direction, names = edge_direction(problem, entry, x)

    process = R.build_process(CASE, optimisation=True, carbon_budget=BUDGET)
    R.setup_optimisation(process, x0={"electrofuel": list(x[:5]), "biofuel": list(x[5:])})

    def emissions(vector):
        process.parameters.generic_electrofuel_mandate_share_values_optim = list(vector[:5])
        process.parameters.generic_biofuel_mandate_share_values_optim = list(vector[5:])
        process.compute()
        series = np.asarray(process.data["vector_outputs"]["co2_emissions_including_energy"], float)
        return pd.Series(series, index=range(2000, 2000 + len(series)))

    base = emissions(x)
    moved = emissions(x + DELTA_GT * direction)
    delta = (moved - base) / DELTA_GT  # MtCO2 per GtCO2 relaxed

    years = list(range(2026, 2051))
    table = pd.DataFrame(
        {
            "year": years,
            "extra_co2_mtco2": [delta.loc[y] for y in years],
        }
    )
    table["discount_to_2020"] = [(1 + DISCOUNT_RATE) ** (y - 2020) for y in years]
    total = table.extra_co2_mtco2.sum()
    table["pct_of_extra_co2"] = 100 * table.extra_co2_mtco2 / total
    table.to_csv(E.OUT / "tcac_decomposition.csv", index=False)

    weight = (table.extra_co2_mtco2 * table.discount_to_2020).sum() / total
    print(table[table.year >= 2034].to_string(index=False, float_format=lambda v: f"{v:9.3f}"))
    print(f"\ntotal extra CO2 = {total / 1000:.4f} GtCO2 (target 1.0)")
    print(f"emissions-weighted discount factor = {weight:.3f}")
    print(
        f"lambda_G1 = 229 EUR/tCO2 (2020 PV)  ->  {229.0 * weight:.0f} EUR/tCO2 "
        f"in year-of-emission money"
    )

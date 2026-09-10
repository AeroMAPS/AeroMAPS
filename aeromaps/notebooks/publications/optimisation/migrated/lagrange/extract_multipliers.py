"""Post-optimal Lagrange multipliers for the migrated ReFuelEU optimisation.

Everything here is read from the stored ``results/*.hdf`` histories. No
optimisation is re-run and no AeroMAPS model is evaluated: the HDF database
already holds, at the optimum, the objective gradient and all 26 constraint
Jacobians that the KKT least-squares needs.

Two wrinkles are worth knowing about.

``OptimizationProblem.from_hdf`` calls ``set_pt_from_database`` for the
objective but not for the constraints, so a restored problem cannot evaluate
its own constraints. Applying that same supported call to the constraints
(``_restore``) is what makes GEMSEO's own ``LagrangeMultipliers`` runnable
offline.

SLSQP reports as ``x_opt`` whichever iterate had the best objective, and that
is not always a point it differentiated: a run that stops on ``ftol_abs``
right after a line-search step leaves its last step ungradiented. So the
evaluation point is the *nearest gradient-bearing iterate*, and the distance
to ``x_opt`` is recorded on every row. Beyond ``X_MATCH_TOL`` that is a
different point, and the run is reported as not recoverable rather than
silently evaluated somewhere else.

Units. The surplus runs minimised ``1e-10 * cumulative_total_surplus_loss_
discounted_obj``. That output is euros despite a ``[M€]`` docstring: it is
``€/RPK x RPK``. So a raw multiplier is "scaled-objective units per unit of
constraint" and dividing by the scale puts it in euros, discounted to 2020 at
4.5 %/yr. The min-CO2 runs minimise ``10 * aviation_carbon_budget_constraint``
instead, whose multipliers are carbon, not money; they get their own column and
the euro columns stay empty.
"""

from __future__ import annotations

import json
import os
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from gemseo.algos.lagrange_multipliers import LagrangeMultipliers
from gemseo.algos.optimization_problem import OptimizationProblem

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent  # migrated/, which holds optimisation_runs.py and results/

# Which sweep to analyse. ``rerun_tight.py`` writes a parallel ladder under
# ``results_tight/`` (ftol_abs=1e-8, kkt_tol_rel=1e-6) beside the original
# ``results/``; set AEROMAPS_LAGRANGE_RESULTS to pick one. Every other script in
# this folder imports RESULTS and OUT from here, so the switch propagates and the
# two analyses can never overwrite each other's tables or figures.
# The paper's own sweep stays beside the notebooks that produce it; sweeps made
# only for this analysis live in here. Look locally first, then next door.
_REQUESTED = os.environ.get("AEROMAPS_LAGRANGE_RESULTS", "results")
RESULTS = HERE / _REQUESTED if (HERE / _REQUESTED).is_dir() else PAPER / _REQUESTED
_SUFFIX = _REQUESTED.removeprefix("results_")
OUT = HERE if RESULTS.name == "results" else HERE / f"analysis_{_SUFFIX}"
OUT.mkdir(exist_ok=True)

# --- constants mirroring optimisation_runs.py / constraints_rte.py ----------- #
EU_ASK_SHARE = 15.49 / 100
OPTIM_YEARS = [2030, 2035, 2040, 2045, 2050]
DISCOUNT_RATE = 0.045
DISCOUNT_BASE_YEAR = 2020  # prospection_start_year
SERIES_START_YEAR = 2000  # historic_start_year: index base of every series
EJ_PER_YEAR_TO_MJ = 1e12
RAMP_RATE = 0.2  # tau, both fuels
RAMP_VOLUME_EJ_PER_YR = 0.2 * EU_ASK_SHARE  # EU-downscaled volume cap

# How close a gradient-bearing iterate must sit to x_opt to count as being x_opt.
# Machine-precision hash misses land at ~1e-13; a genuinely different iterate is
# many orders of magnitude further away, so nothing sits near this threshold.
X_MATCH_TOL = 1e-6

CASES = {
    "main": {"biomass_share": 9.90, "efficiency_gain": 1.35, "label": "9.9 % biomass"},
    "B5": {"biomass_share": 5.00, "efficiency_gain": 1.35, "label": "5 % biomass"},
    "B75": {"biomass_share": 7.50, "efficiency_gain": 1.35, "label": "7.5 % biomass"},
    "B15": {"biomass_share": 15.00, "efficiency_gain": 1.35, "label": "15 % biomass"},
    "pess": {"biomass_share": 9.90, "efficiency_gain": 0.91, "label": "Low efficiency"},
}

# constraint name -> (paper label, the years its components refer to)
FAMILIES = {
    "aviation_carbon_budget_constraint": ("G1", [None]),
    "blend_completeness_constraint": ("G2", OPTIM_YEARS),
    "biomass_trajectory_constraint": ("G3", OPTIM_YEARS),
    "electricity_trajectory_constraint": ("G4", OPTIM_YEARS),
    "biofuel_use_growth_constraint": ("G5", OPTIM_YEARS),
    "electrofuel_use_growth_constraint": ("G6", OPTIM_YEARS),
}

RUN_RE = re.compile(r"^opt_(?P<case>[A-Za-z0-9]+)_(?P<budget>mincarb|\d+_\d+)$")
SCALE_RE = re.compile(r"^(?P<scale>[0-9.e+-]+)\*(?P<name>.+)$")


def parse_run_id(stem: str):
    """``opt_main_2_6`` -> ``("main", 2.6)``; ``opt_main_mincarb`` -> ``("main", None)``."""
    m = RUN_RE.match(stem)
    if not m:
        return None
    budget = m["budget"]
    return m["case"], (None if budget == "mincarb" else float(budget.replace("_", ".")))


def split_objective(name: str):
    """``1e-10*foo`` -> ``(1e-10, "foo")``. The scale is applied in ``setup_optimisation``."""
    m = SCALE_RE.match(name)
    if not m:
        return 1.0, name
    return float(m["scale"]), m["name"]


def series(payload: dict, name: str) -> pd.Series:
    """A model output series, re-indexed by calendar year."""
    values = np.asarray(payload["vector_outputs"][name], dtype=float)
    return pd.Series(values, index=range(SERIES_START_YEAR, SERIES_START_YEAR + len(values)))


def _restore(path: Path) -> OptimizationProblem:
    """Load a stored problem and make its constraints evaluable from the database."""
    problem = OptimizationProblem.from_hdf(str(path))
    for constraint in problem.constraints:
        constraint.set_pt_from_database(
            problem.database, problem.design_space, normalize=False, jac=True
        )
    return problem


def evaluation_point(problem: OptimizationProblem, grad_key: str):
    """The nearest iterate to ``x_opt`` that carries gradients, and how far away it is."""
    x_opt = np.asarray(problem.solution.x_opt, dtype=float)
    best = None
    for x, values in problem.database.items():
        if grad_key not in values:
            continue
        x_vect = np.asarray(x.unwrap(), dtype=float)
        distance = float(np.max(np.abs(x_vect - x_opt)))
        if best is None or distance < best[1]:
            best = (x_vect, distance, values)
    if best is None:
        raise ValueError("no iterate in the database carries gradients")
    return best


def multipliers(problem, x_eval, ineq_tolerance=None):
    """GEMSEO's own post-optimal KKT solve, at ``x_eval``."""
    if ineq_tolerance is None:
        ineq_tolerance = float(problem.tolerances.inequality)
    lm = LagrangeMultipliers(problem)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lm.compute(x_eval, ineq_tolerance=ineq_tolerance)
    return lm.get_multipliers_arrays(), lm.kkt_residual, lm.constraint_violation


# The active set is *identified from stationarity*, not assumed from a tolerance.
#
# The optimiser's own feasibility tolerance is 1e-4, but SLSQP routinely stops with
# a constraint sitting at a slack of 1e-4 to 8e-3 -- satisfied, yet binding in every
# way that matters (for the share constraints one unit is 100 percentage points, so
# 5e-4 is 0.05 pp from the bound). Excluding such a row leaves the objective gradient
# outside the cone of active constraint gradients, and GEMSEO's NNLS solve then
# returns a residual of 1e-2 to 1e-1 -- reported on 14 of the 46 feasible runs, all
# of which are genuinely converged.
#
# No single tolerance separates the two populations: opt_B5_3_4 needs 8.5e-3 to close,
# while opt_main_* carry a G2 row at 5.5e-3 in 2050 that is structurally slack. So
# instead of a fixed cut, walk the ladder and keep the *smallest* tolerance whose
# residual reaches machine precision. That is self-validating: a spuriously included
# constraint cannot lower a residual that is already zero, and NNLS gives it lambda=0.
# A run that never closes keeps its tightest result and is flagged by the residual.
ACTIVE_SET_TOL_LADDER = (3e-4, 1e-3, 3e-3, 1e-2)
KKT_CLOSED_REL = 1e-8


def resolve_active_set(problem, x_eval, grad_norm):
    """Multipliers at the smallest tolerance that explains the objective gradient."""
    base = float(problem.tolerances.inequality)
    best = None
    for tol in (base, *(t for t in ACTIVE_SET_TOL_LADDER if t > base)):
        arrays, residual, violation = multipliers(problem, x_eval, ineq_tolerance=tol)
        relative = residual / grad_norm
        if best is None or relative < best[3]:
            best = (arrays, residual, violation, relative, tol)
        if relative <= KKT_CLOSED_REL:
            break
    return best


def ramp_branch(consumption: pd.Series, year: int):
    """Which side of ``max(rate_cap, volume_cap)`` binds, and both caps.

    Mirrors ``constraints_rte._ramp_up_violation`` exactly, lookback rule included.
    """
    check_years = [OPTIM_YEARS[0] - 5] + list(OPTIM_YEARS)
    lookback = year - 5 if (year - 5) in check_years else year - 10
    dt = year - lookback
    previous = float(consumption.loc[lookback])
    rate_cap = previous * (1 + RAMP_RATE) ** dt
    volume_cap = RAMP_VOLUME_EJ_PER_YR * dt * EJ_PER_YEAR_TO_MJ
    return ("volume" if volume_cap >= rate_cap else "rate"), rate_cap, volume_cap, dt, previous


def undiscount(year) -> float:
    """Factor taking a 2020-discounted euro to a euro of ``year``."""
    return np.nan if year is None else (1 + DISCOUNT_RATE) ** (year - DISCOUNT_BASE_YEAR)


def rows_for_run(hdf: Path) -> list[dict]:
    case, budget_share = parse_run_id(hdf.stem)
    payload = json.loads((RESULTS / f"{hdf.stem}.json").read_text())

    problem = _restore(hdf)
    scale, objective_name = split_objective(problem.objective.name)
    is_min_co2 = objective_name == "aviation_carbon_budget_constraint"
    grad_key = f"@{problem.objective.name}"

    x_eval, distance, entry = evaluation_point(problem, grad_key)
    if distance > X_MATCH_TOL:
        raise ValueError(
            f"no gradient at x_opt; nearest gradient-bearing iterate is "
            f"{distance:.3e} away (inf-norm). Multipliers would be those of a "
            f"different point, so this run needs re-running."
        )
    # The KKT residual is the norm of an unsatisfied stationarity condition, so it
    # only means anything relative to the gradient it is trying to cancel.
    grad_norm = float(np.linalg.norm(np.asarray(entry[grad_key], dtype=float)))
    arrays, kkt_residual, violation, _, ineq_tol = resolve_active_set(problem, x_eval, grad_norm)

    fo, fi = payload["float_outputs"], payload["float_inputs"]
    cumulative_co2 = series(payload, "cumulative_co2_emissions")
    budget_adjusted = (  # GtCO2, the denominator the G1 constraint normalises by
        fo["gross_carbon_budget_2050"] * fi["aviation_carbon_budget_objective"] / 100
        - float(cumulative_co2.loc[2025])
    )
    allocated = {
        "G3": series(payload, "generic_biomass_availability_global")
        * fi["generic_biomass_availability_aviation_allocated_share"]
        / 100,
        "G4": series(payload, "generic_electricity_availability_global")
        * fi["generic_electricity_availability_aviation_allocated_share"]
        / 100,
    }
    consumption = {
        "G5": series(payload, "generic_biofuel_energy_consumption"),
        "G6": series(payload, "generic_electrofuel_energy_consumption"),
    }
    # Fossil kerosene is the *residual* of the drop-in blend, so when the
    # blend-completeness constraint is exactly active it is driven to zero and
    # the model's own share arithmetic becomes 0/0 - the pathology that
    # EPSILON_SHARE guards against for electrofuel, which has no counterpart
    # here because kerosene is not a design variable. A run whose residual
    # kerosene falls to floating-point noise is sitting outside the model's
    # valid domain, however well its KKT system is satisfied.
    kerosene_fraction = series(payload, "energy_consumption_kerosene") / series(
        payload, "energy_consumption_dropin_fuel"
    )
    residual_kerosene = float(min(kerosene_fraction.loc[y] for y in OPTIM_YEARS))
    # In a min-CO2 run the budget constraint is the objective, so it has no
    # multiplier; every other family keeps its own.
    present = {c.name for c in problem.constraints}

    rows = []
    for name, (family, years) in FAMILIES.items():
        if name not in present:
            continue
        mult = np.atleast_1d(arrays["inequality"][name])
        value = np.atleast_1d(np.asarray(entry[name], dtype=float))
        for i, year in enumerate(years):
            lam_raw = float(mult[i])
            g = float(value[i])
            # Objective units per unit of g. For a surplus run that is euros
            # discounted to 2020; for a min-CO2 run it is GtCO2.
            lam_native = lam_raw / scale
            row = {
                "run": hdf.stem,
                "case": case,
                "case_label": CASES[case]["label"],
                "biomass_share_world_pct": CASES[case]["biomass_share"],
                "efficiency_gain_pct_per_yr": CASES[case]["efficiency_gain"],
                "carbon_budget_share_world_pct": budget_share,
                "objective_kind": "min_co2" if is_min_co2 else "min_surplus_loss",
                "constraint": family,
                "constraint_name": name,
                "component": i,
                "year": year,
                "g_value": g,
                "g_bound": 0.0,
                "slack": abs(g),
                # Active at the tolerance the stationarity solve settled on, so the
                # flag and the multiplier vector always describe the same active set.
                "active": abs(g) <= ineq_tol,
                "ineq_tolerance": ineq_tol,
                "ineq_tolerance_is_default": ineq_tol == float(problem.tolerances.inequality),
                "lambda_raw": lam_raw,
                "objective_scale": scale,
                "f_opt_scaled": float(problem.solution.f_opt),
                "kkt_residual": kkt_residual,
                "kkt_residual_relative": kkt_residual / grad_norm,
                "objective_grad_norm": grad_norm,
                "max_constraint_violation": violation,
                # A run that stopped infeasible has no KKT point, so its
                # multipliers are not shadow prices. Carried on every row.
                "run_feasible": bool(problem.solution.is_feasible),
                "termination_message": str(problem.solution.message),
                "x_eval_distance_from_x_opt": distance,
                "n_database_entries": len(problem.database),
                "min_residual_kerosene_fraction": residual_kerosene,
                # 1e-9 is far below any economically meaningful blend share and
                # far above the ~1e-16 seen when the constraint saturates.
                "blend_degenerate": residual_kerosene < 1e-9,
                "n_gradient_points": sum(grad_key in v for v in problem.database.values()),
            }
            if is_min_co2:
                # objective = (cum - B)/B, so a unit of it is B GtCO2 of emissions.
                row["lambda_gtco2_per_unit_g"] = lam_native * budget_adjusted
                row["f_opt_eur_discounted2020"] = np.nan
            else:
                row["lambda_eur_discounted2020_per_unit_g"] = lam_native
                row["f_opt_eur_discounted2020"] = float(problem.solution.f_opt) / scale

            # --- physical units, per family ---------------------------------- #
            lam_eur = np.nan if is_min_co2 else lam_native
            if family == "G1":
                # g = (cum - B)/B, so df/dB = -lambda/B with B in GtCO2.
                row["budget_adjusted_gtco2"] = budget_adjusted
                row["shadow_price_eur_per_tco2_discounted2020"] = lam_eur / (budget_adjusted * 1e9)
            elif family in ("G3", "G4"):
                # g = consumption/allocated - 1, so df/d(allocated) = -lambda/allocated.
                alloc_mj = float(allocated[family].loc[year])
                row["allocated_resource_mj"] = alloc_mj
                row["allocated_resource_ej"] = alloc_mj / 1e12
                per_mj = lam_eur / alloc_mj
                row["shadow_price_eur_per_gj_discounted2020"] = per_mj * 1e3
                row["shadow_price_eur_per_ej_discounted2020"] = per_mj * 1e12
            elif family in ("G5", "G6"):
                branch, rate_cap, volume_cap, dt, previous = ramp_branch(consumption[family], year)
                # g = (E - cap)/volume_cap, so df/d(cap) = -lambda/volume_cap.
                per_mj = lam_eur / volume_cap
                row["ramp_branch_active"] = branch
                row["ramp_rate_cap_mj"] = rate_cap
                row["ramp_volume_cap_mj"] = volume_cap
                row["ramp_previous_consumption_mj"] = previous
                row["shadow_price_eur_per_gj_of_cap_discounted2020"] = per_mj * 1e3
                # Sensitivity to the *declared* bounds. Only the binding branch of
                # the max carries one; relaxing the other changes nothing.
                if branch == "volume":
                    row["d_obj_d_volume_bound_eur_per_ej_per_yr_discounted2020"] = (
                        lam_eur / RAMP_VOLUME_EJ_PER_YR
                    )
                    row["d_obj_d_rate_bound_eur_per_unit_tau_discounted2020"] = 0.0
                else:
                    row["d_obj_d_volume_bound_eur_per_ej_per_yr_discounted2020"] = 0.0
                    row["d_obj_d_rate_bound_eur_per_unit_tau_discounted2020"] = (
                        lam_eur * dt * previous * (1 + RAMP_RATE) ** (dt - 1) / volume_cap
                    )

            # Undiscounted equivalent, for comparison with published carbon values.
            factor = undiscount(year)
            row["undiscount_factor_to_year"] = factor
            for key in list(row):
                if key.startswith(("shadow_price", "d_obj_d")):
                    row[key.replace("_discounted2020", "_undiscounted_year")] = row[key] * factor
            rows.append(row)
    return rows


def build_table(verbose: bool = True):
    frames, skipped = [], {}
    for hdf in sorted(RESULTS.glob("opt_*.hdf")):
        if parse_run_id(hdf.stem) is None:
            continue
        try:
            frames.extend(rows_for_run(hdf))
        except Exception as exc:  # noqa: BLE001 - report, never fabricate
            skipped[hdf.stem] = f"{type(exc).__name__}: {exc}"
            if verbose:
                print(f"  SKIPPED {hdf.stem}: {exc}")
    return pd.DataFrame(frames), skipped


if __name__ == "__main__":
    table, skipped = build_table()
    table.to_csv(OUT / "lagrange_multipliers.csv", index=False)
    print(
        f"\n{len(table)} rows over {table['run'].nunique()} runs "
        f"({len(skipped)} skipped) -> lagrange_multipliers.csv"
    )

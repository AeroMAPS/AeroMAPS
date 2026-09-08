"""Scenario construction and run drivers for the migrated ReFuelEU optimisation.

The published work is five variants of one problem, differing only in how much
biomass aviation is allocated and how fast aircraft efficiency improves. They are
declared in ``CASES`` and everything else is shared, so a bug is fixed once.

Two entry points:

``run_sweep``     the carbon-budget continuation, largest budget first, each
                  optimisation started from the previous one's optimum.
``run_reference`` a plain MDA at a fixed mandate (fossil BAU, ReFuelEU).

Both write their results to ``results/`` as soon as a run finishes and skip what
is already on disk, so an interrupted sweep resumes where it stopped.
"""

from __future__ import annotations

import json
import time
from collections import OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd

from gemseo.algos.design_space import DesignSpace
from gemseo.algos.opt.scipy_local.settings.slsqp import SLSQP_Settings

from aeromaps import create_process
from aeromaps.core.gemseo import CustomDataConverter

# Share of world traffic departing the EU in 2019 (AeroSCOPE). Downscales the world
# carbon budget and the world biomass/electricity allocations to the EU perimeter.
EU_ASK_SHARE = 15.49 / 100

# ReFuelEU reference years carrying a design variable.
OPTIM_YEARS = [2030, 2035, 2040, 2045, 2050]

RESULTS_DIR = Path("results")

# Mandate shares over OPTIM_YEARS for the two non-optimised references.
REFUELEU_MANDATE = {
    "biofuel": [4.8, 15.0, 24.0, 27.0, 35.0],
    "electrofuel": [1.2, 5.0, 10.0, 15.0, 35.0],
}

# The five published variants. ``biomass_share`` is the share of *world* biomass
# allocated to aviation; ``efficiency_gain`` the annual drop-in energy-per-ASK gain
# in %/yr, which is the only thing the pessimistic technology roadmap changes.
CASES = {
    "main": {"biomass_share": 9.90, "efficiency_gain": 1.35, "label": "Reference"},
    "B5": {"biomass_share": 5.00, "efficiency_gain": 1.35, "label": "5 % biomass"},
    "B75": {"biomass_share": 7.50, "efficiency_gain": 1.35, "label": "7.5 % biomass"},
    "B15": {"biomass_share": 15.00, "efficiency_gain": 1.35, "label": "15 % biomass"},
    "pess": {"biomass_share": 9.90, "efficiency_gain": 0.91, "label": "Low efficiency"},
}

# Electricity allocation is the same in every published case (paper section 3.4).
ELECTRICITY_SHARE = 5.0

# Resource per unit of fuel energy, mirroring resource_specific_consumption in
# energy_rte.yaml. Turns a resource availability into the fuel it can produce.
RESOURCE_PER_FUEL = {"biomass": 2.104355, "electricity": 2.290426}

# Passenger markets per config, needed to push the efficiency gain. Freight has no
# drop-in gain curve unless the freight efficiency model is switched on.
PASSENGER_MARKETS = {
    "config_rte.yaml": ["short_range", "medium_range", "long_range"],
    "config_1m.yaml": ["passenger"],
}


# --------------------------------------------------------------------------- #
# Scenario
# --------------------------------------------------------------------------- #


def build_process(case="main", config="config_rte.yaml", optimisation=False, carbon_budget=2.6):
    """Create the process and set every scenario parameter.

    The constraint models of ``constraints_rte.py`` are part of the chain even for
    a plain MDA, so their inputs must always be defined - otherwise GEMSEO cannot
    order the disciplines.

    ``carbon_budget`` is the share of the *world* aviation carbon budget, before
    the EU downscaling; it is ignored by the min-CO2 problem, which has no budget
    constraint.
    """
    settings = CASES[case]
    process = create_process(configuration_file=config, optimisation=optimisation)

    # Entry point for the airfare <-> RPK loop, as in the published notebook.
    process.parameters.price_elasticity = -0.9
    process.parameters.airfare_per_rpk = pd.Series(
        0.09236379319842411,
        index=range(process.parameters.historic_start_year, process.parameters.end_year + 1),
    )

    # Constraint enforcement years (G2-G6).
    for name in [
        "blend_completeness_constraint",
        "biofuel_use_growth_constraint",
        "electrofuel_use_growth_constraint",
    ]:
        setattr(process.parameters, f"{name}_enforcement_years", OPTIM_YEARS)
    process.parameters.generic_biomass_availability_constraint_enforcement_years = OPTIM_YEARS
    process.parameters.generic_electricity_constraint_enforcement_years = OPTIM_YEARS

    # Ramp-up limits: 0.2 EJ/yr and 20 %/yr, downscaled to the EU perimeter (Eq. 12).
    process.parameters.volume_ramp_up_constraint_biofuel = 0.2 * EU_ASK_SHARE
    process.parameters.rate_ramp_up_constraint_biofuel = 0.2
    process.parameters.volume_ramp_up_constraint_electrofuel = 0.2 * EU_ASK_SHARE
    process.parameters.rate_ramp_up_constraint_electrofuel = 0.2

    # Carbon budget (G1), as a share of the world aviation budget.
    process.parameters.aviation_carbon_budget_objective = carbon_budget * EU_ASK_SHARE

    # Resource allocations (paper section 3.4). These override the values that
    # resources_rte.yaml pushed into the parameters at process creation, which is
    # what makes the biomass sensitivity study a parameter sweep rather than five
    # yaml files.
    process.parameters.generic_biomass_availability_aviation_allocated_share = (
        settings["biomass_share"] * EU_ASK_SHARE
    )
    process.parameters.generic_electricity_availability_aviation_allocated_share = (
        ELECTRICITY_SHARE * EU_ASK_SHARE
    )

    # Efficiency roadmap. Set per market because markets.yaml wins over the input
    # JSON, so writing this into inputs.json - as the published notebook did - is
    # silently ignored on main.
    for market in PASSENGER_MARKETS[config]:
        setattr(
            process.parameters,
            f"{market}_energy_per_ask_dropin_fuel_gain_reference_years_values",
            [settings["efficiency_gain"]],
        )

    # Fixed leading mandate entries (2020, 2025); later years are the design variables.
    process.parameters.generic_biofuel_mandate_share_values_fixed = [0.0, 2.0]
    process.parameters.generic_electrofuel_mandate_share_values_fixed = [0.0, 0.0]
    return process


def set_mandate(process, biofuel, electrofuel):
    """Impose a mandate over OPTIM_YEARS, bypassing the optimiser."""
    process.parameters.generic_biofuel_mandate_share_values_optim = list(biofuel)
    process.parameters.generic_electrofuel_mandate_share_values_optim = list(electrofuel)


# --------------------------------------------------------------------------- #
# Optimisation setup
# --------------------------------------------------------------------------- #


def share_mda_across_functions(process, size=16):
    """One MDA solve per design point instead of one per function.

    MDF hands the objective and each constraint its own ``MDOFunction`` and
    ``set_differentiation_method("finite_differences")`` differentiates each of them
    separately: seven sweeps over the same eleven design points, seven identical MDA
    solves each time. Measured on this problem, three SLSQP iterations cost 252 MDA
    solves where 33 are needed -- 607 s instead of 54 s.

    GEMSEO's own discipline cache does not absorb the repeats. Its key is a hash of
    all 241 chain inputs, and three identical calls produce three entries even when
    the stored inputs compare byte-identical. Keying on the design variables -- the
    only thing the converged fixed point depends on -- does absorb them, with iterates
    identical to the uncached run and the objective agreeing to nine significant
    digits.

    An LRU of 16 covers a full function sweep (eleven points); without a bound the
    memo would retain every design point of the run, each holding 241 arrays.
    """
    mda = process.scenario.formulation.mda
    solve, memo = mda.execute, OrderedDict()

    def cached(input_data=None, **kwargs):
        if input_data is None:
            return solve(**kwargs)
        key = tuple((name, tuple(np.ravel(value))) for name, value in sorted(input_data.items()))
        if key in memo:
            memo.move_to_end(key)
        else:
            outputs = solve(input_data, **kwargs)
            memo[key] = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in outputs.items()}
            while len(memo) > size:
                memo.popitem(last=False)
        return memo[key]

    mda.execute = cached
    return process


# Start point of the very first optimisation of a sweep, i.e. the largest carbon
# budget. Every later run starts from its predecessor's optimum instead.
COLD_START = {
    "biofuel": [8.35, 21.24, 41.05, 43.81, 43.95],
    "electrofuel": [0.5, 5.78, 15.03, 39.12, 55.41],
}

# The min-CO2 problem sits well beyond the budget-constrained optima, so it gets its
# own start point rather than continuing the ladder.
MIN_CARBON_START = {
    "biofuel": [9.54, 27.04, 50.68, 47.96, 49.99],
    "electrofuel": [9.54, 27.04, 49.32, 52.04, 50.01],
}

_CONSTRAINTS = [
    "blend_completeness_constraint",
    "electricity_trajectory_constraint",
    "biomass_trajectory_constraint",
    "electrofuel_use_growth_constraint",
    "biofuel_use_growth_constraint",
]


def setup_optimisation(process, x0=None, max_iter=50, objective="surplus", warm_start=False):
    """Configure the SLSQP problem of section 3.5 of the paper.

    Scenario parameters are already set by ``build_process``; this only adds the
    design space, the objective and the constraints.

    ``objective="surplus"`` minimises the discounted total surplus loss subject to
    G1-G6, which is the published problem. ``objective="carbon"`` minimises the
    carbon budget consumed subject to G2-G6 only, giving the left-hand end of every
    trade-off curve: the least CO2 the system can reach at any cost.

    ``warm_start`` trades reproducibility for speed and is off by default -- see the
    comment at the bottom of this function.
    """
    x0 = x0 or (MIN_CARBON_START if objective == "carbon" else COLD_START)

    process.gemseo_settings["scenario_type"] = "MDO"
    process.gemseo_settings["formulation"] = "MDF"

    design_space = DesignSpace()
    design_space.add_variable(
        "generic_electrofuel_mandate_share_values_optim",
        # Lower bound held off zero: a pathway share returning to zero after being
        # positive gives 0/0 in its own share variable and the MDA dies with
        # "converged on NaN". This is the same reason biofuel carries a lower bound
        # of 2 -- numerics, not policy. The bound sits below the 1.2 % ReFuelEU 2030
        # sub-mandate, so it does not bind on any scenario of interest.
        size=5,
        lower_bound=[1e-5] * 5,
        upper_bound=[100] * 5,
        value=np.clip(x0["electrofuel"], 1e-5, 100),
    )
    design_space.add_variable(
        "generic_biofuel_mandate_share_values_optim",
        size=5,
        lower_bound=[2] * 5,
        upper_bound=[100] * 5,
        value=np.clip(x0["biofuel"], 2, 100),
    )
    process.gemseo_settings["design_space"] = design_space

    if objective == "surplus":
        process.gemseo_settings["objective_name"] = "cumulative_total_surplus_loss_discounted_obj"
        constraints = ["aviation_carbon_budget_constraint"] + _CONSTRAINTS
        scale = 1e-10
    elif objective == "carbon":
        process.gemseo_settings["objective_name"] = "aviation_carbon_budget_constraint"
        constraints = _CONSTRAINTS
        scale = 10.0
    else:
        raise ValueError(f"objective must be 'surplus' or 'carbon', got {objective!r}")

    process.create_gemseo_scenario()

    # Bring the objective into a range SLSQP is comfortable with.
    problem = process.scenario.formulation.optimization_problem
    problem.objective = problem.objective * scale

    for constraint in constraints:
        process.scenario.add_constraint(constraint, constraint_type="ineq")

    process.scenario.set_differentiation_method("finite_differences")
    process.gemseo_settings["algorithm"] = SLSQP_Settings(
        max_iter=max_iter,
        enable_progress_bar=True,
        ftol_abs=0.001,
        normalize_design_space=False,
    )

    # Design variables arrive as ndarray but are consumed as lists downstream.
    CustomDataConverter._list_names.update(process.scenario.get_optim_variable_names())

    # One MDA solve per design point rather than one per function. Roughly 11x here;
    # see the docstring above for why GEMSEO's own cache does not do this.
    share_mda_across_functions(process)

    if warm_start:
        # Start each MDA from the previous solve's couplings. The finite-difference
        # points sit ~1e-6 apart, so Gauss-Seidel needs about half the sweeps:
        # measured 10.3 -> 5.1 per solve, and the objective gradient 17.8 s -> 12.6 s.
        #
        # It is off by default because it makes f(x) depend on evaluation *order*. The
        # MDA stops as soon as the residual crosses tolerance, so the converged point
        # sits somewhere in a ball around the true fixed point and its position depends
        # on where the sweep started. Measured against a cold run, the gradient moves
        # by 9.4e-06 relative at tolerance 1e-10 and the SLSQP iterates visibly
        # diverge. Tightening to 1e-12 shrinks that ball and brings the gradient back
        # to 6.5e-07 relative while keeping most of the gain.
        #
        # Use it for exploratory work -- scanning start points, checking whether a
        # budget is feasible at all. Published runs should stay reproducible.
        mda = process.scenario.formulation.mda
        mda.settings.warm_start = True
        for inner_mda in mda.inner_mdas:
            inner_mda.settings.warm_start = True
            inner_mda.settings.tolerance = 1e-12

    return process


# --------------------------------------------------------------------------- #
# Runs
# --------------------------------------------------------------------------- #


def budget_tag(budget):
    """2.6 -> '2_6', matching the published result file names."""
    return f"{budget:.1f}".replace(".", "_")


def _optimum(result):
    """Split GEMSEO's x_opt back into the two pathways, in design-space order."""
    x = np.asarray(result.x_opt)
    return {"electrofuel": list(x[:5]), "biofuel": list(x[5:])}


def _save(process, stem):
    """Write history then outputs. History first: extracting results is where a late
    failure would otherwise throw away the whole run."""
    stem.parent.mkdir(parents=True, exist_ok=True)
    process.scenario.save_optimization_history(str(stem.with_suffix(".hdf")))
    process.write_json(str(stem.with_suffix(".json")))


def run_optimisation(case, budget=None, config="config_rte.yaml", x0=None, max_iter=50, **kwargs):
    """One optimisation, saved to ``results/``. ``budget=None`` means min-CO2."""
    objective = "carbon" if budget is None else "surplus"
    stem = RESULTS_DIR / (
        f"opt_{case}_mincarb" if budget is None else f"opt_{case}_{budget_tag(budget)}"
    )

    process = build_process(
        case, config=config, optimisation=True, carbon_budget=2.6 if budget is None else budget
    )
    setup_optimisation(process, x0=x0, max_iter=max_iter, objective=objective, **kwargs)

    start = time.perf_counter()
    process.compute()
    elapsed = time.perf_counter() - start

    _save(process, stem)
    result = process.scenario.get_result().optimization_result
    return {
        "case": case,
        "budget": "min CO2" if budget is None else budget,
        "objective": float(result.f_opt),
        "feasible": bool(result.is_feasible),
        "evaluations": len(process.scenario.formulation.optimization_problem.database),
        "seconds": round(elapsed, 1),
        "message": str(result.message),
        "x": _optimum(result),
        "path": str(stem.with_suffix(".json")),
    }


def run_sweep(case, budgets=None, config="config_rte.yaml", max_iter=50, resume=True, **kwargs):
    """Carbon-budget continuation for one case, loosest budget first.

    Each optimisation starts from the previous one's optimum. Tightening the budget
    moves the optimum smoothly, so the previous solution is a far better start point
    than a fixed guess: SLSQP begins just outside the new feasible set instead of
    somewhere unrelated to it. The published notebooks instead pasted a hand-picked
    start into every run, which is why several of their low budgets were annotated
    "not possible" and commented out.

    An infeasible run is not propagated -- its ``x_opt`` is a best effort, not an
    optimum -- so the chain carries the last feasible design forward instead.

    With ``resume=True`` a budget whose JSON already exists is skipped and its
    optimum read back from the HDF, so an interrupted sweep continues cleanly.
    Delete the file to force a re-run.
    """
    budgets = budgets if budgets is not None else [3.8, 3.6, 3.4, 3.2, 3.0, 2.8, 2.6, 2.4, 2.2, 2.0]

    rows, x0 = [], None
    for budget in list(budgets) + [None]:
        stem = RESULTS_DIR / (
            f"opt_{case}_mincarb" if budget is None else f"opt_{case}_{budget_tag(budget)}"
        )
        if resume and stem.with_suffix(".json").exists():
            x0 = read_optimum(stem.with_suffix(".hdf")) or x0
            print(f"{case} {'min CO2' if budget is None else budget}: already on disk, skipped")
            continue

        row = run_optimisation(
            case, budget=budget, config=config, x0=x0, max_iter=max_iter, **kwargs
        )
        rows.append(row)
        print(
            f"{case} {row['budget']}: obj {row['objective']:+.4f}  "
            f"{'feasible' if row['feasible'] else 'INFEASIBLE'}  "
            f"{row['evaluations']} evals  {row['seconds']} s"
        )
        # min-CO2 is the last entry and starts from its own point, so it never feeds
        # the chain.
        if row["feasible"] and budget is not None:
            x0 = row["x"]

    return pd.DataFrame(rows)


def read_optimum(hdf_path):
    """Recover a saved run's optimum, so a resumed sweep keeps its continuation."""
    from gemseo.algos.optimization_problem import OptimizationProblem

    try:
        x = np.asarray(OptimizationProblem.from_hdf(str(hdf_path)).optimum.design)
    except Exception:
        return None
    return {"electrofuel": list(x[:5]), "biofuel": list(x[5:])} if x.size == 10 else None


def run_reference(case, kind="refueleu", config="config_rte.yaml", resume=True):
    """A plain MDA at a fixed mandate: the two comparison points of the paper.

    ``fossil`` is the BAU with no mandate at all. The 2025 leading entry is zeroed
    along with the design years: leaving biofuel at 2 % in 2025 and 0 % afterwards
    would take its pathway share from positive back to zero, which is the 0/0 that
    makes the MDA converge on NaN.
    """
    stem = RESULTS_DIR / f"{kind}_{case}"
    if resume and stem.with_suffix(".json").exists():
        print(f"{case} {kind}: already on disk, skipped")
        return str(stem.with_suffix(".json"))

    process = build_process(case, config=config, optimisation=False)
    if kind == "refueleu":
        set_mandate(process, **REFUELEU_MANDATE)
    elif kind == "fossil":
        process.parameters.generic_biofuel_mandate_share_values_fixed = [0.0, 0.0]
        process.parameters.generic_electrofuel_mandate_share_values_fixed = [0.0, 0.0]
        set_mandate(process, biofuel=[0.0] * 5, electrofuel=[0.0] * 5)
    else:
        raise ValueError(f"kind must be 'refueleu' or 'fossil', got {kind!r}")

    process.compute()
    stem.parent.mkdir(parents=True, exist_ok=True)
    process.write_json(str(stem.with_suffix(".json")))
    print(f"{case} {kind}: written to {stem.with_suffix('.json')}")
    return str(stem.with_suffix(".json"))


# --------------------------------------------------------------------------- #
# Reading results back
# --------------------------------------------------------------------------- #

YEARS = range(2000, 2051)


def load(path):
    """Read one saved run as ``(vector_outputs_frame, float_outputs_dict)``.

    Vector outputs come back as bare lists; giving them the year index is what lets
    the figures say ``.loc[2050]`` instead of counting from the end.
    """
    with open(path) as f:
        data = json.load(f)
    vectors = {
        k: pd.Series(v, index=YEARS)
        for k, v in data.get("vector_outputs", {}).items()
        if isinstance(v, list) and len(v) == len(YEARS)
    }
    return pd.DataFrame(vectors), data.get("float_outputs", {})

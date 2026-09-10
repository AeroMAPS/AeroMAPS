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
import sys
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
    "config_rte_nofeedback.yaml": ["short_range", "medium_range", "long_range"],
    "config_1m.yaml": ["passenger"],
}

# Configs whose markets.yaml wires in the RPKElasticity layer, and so have an
# airfare <-> RPK loop to seed. The no-feedback variant has neither parameter.
ELASTIC_CONFIGS = {"config_rte.yaml", "config_1m.yaml"}


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

    # Entry point for the airfare <-> RPK loop, as in the published notebook. The
    # no-feedback config has no such loop, and neither parameter exists there.
    if config in ELASTIC_CONFIGS:
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


# Smallest electrofuel share the optimiser may ask for. A pathway share returning to
# exactly zero after being positive gives 0/0 in its own share variable and the MDA dies
# with "converged on NaN", so the design space is held off zero rather than at it. This
# is numerics, not policy: 1e-6 % of the drop-in blend is seven orders of magnitude below
# the 1.2 % ReFuelEU 2030 sub-mandate, so it binds on nothing of interest and reads as
# zero in every figure.
EPSILON_SHARE = 1e-6

# Start point of the very first optimisation of a sweep, i.e. the largest carbon
# budget. Every later run starts from its predecessor's optimum instead. Electrofuel
# starts at the floor in 2030, as the published notebooks did (they used 2.7e-11).
COLD_START = {
    "biofuel": [8.35, 21.24, 41.05, 43.81, 43.95],
    "electrofuel": [EPSILON_SHARE, 5.78, 15.03, 39.12, 55.41],
}

# Fallback start for a min-CO2 run launched on its own. Inside a sweep it is not used:
# min-CO2 comes last and inherits the tightest feasible budget's optimum, which is the
# nearest point there is -- squeezing the budget drives the mandate towards the same
# resource and ramp-up limits that bind the min-CO2 solution.
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


def setup_optimisation(
    process,
    x0=None,
    max_iter=50,
    objective="surplus",
    warm_start=False,
    drop_constraints=(),
):
    """Configure the SLSQP problem of section 3.5 of the paper.

    Scenario parameters are already set by ``build_process``; this only adds the
    design space, the objective and the constraints.

    ``objective="surplus"`` minimises the discounted total surplus loss subject to
    G1-G6, which is the published problem. ``objective="carbon"`` is the paper's
    ``optim_setup_min_carb``: minimise the carbon budget consumed, subject to G2-G6
    only -- the budget constraint becomes the objective, so it is dropped from the
    constraint set. That gives the left-hand end of every trade-off curve, the least
    CO2 the system can reach at any cost, and it is what ``run_sweep`` runs last for
    each case as ``opt_<case>_mincarb``.

    The published notebooks solved the min-CO2 problem with NLOPT's MMA; nlopt is not
    installed here, so both objectives use SLSQP. Scaling differs to keep each in a
    range the solver is comfortable with (1e-10 on the surplus, 10 on the budget).

    ``warm_start`` trades reproducibility for speed and is off by default -- see the
    comment at the bottom of this function.

    ``drop_constraints`` names constraints to leave out of the problem. Dropping is
    not relaxing: the constraint is absent, not widened, so the run answers "what
    would the optimum be if this limit did not exist" rather than "how far must it
    move to admit this point".
    """
    x0 = x0 or (MIN_CARBON_START if objective == "carbon" else COLD_START)

    process.gemseo_settings["scenario_type"] = "MDO"
    process.gemseo_settings["formulation"] = "MDF"

    design_space = DesignSpace()
    design_space.add_variable(
        "generic_electrofuel_mandate_share_values_optim",
        # Floored at EPSILON_SHARE rather than at zero -- see its definition above.
        # Biofuel's lower bound of 2 comes from the policy instead: ReFuelEU mandates
        # 2 % from 2025 and the paper never relaxes it.
        size=5,
        lower_bound=[EPSILON_SHARE] * 5,
        upper_bound=[100] * 5,
        value=np.clip(x0["electrofuel"], EPSILON_SHARE, 100),
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
    elif objective == "cost":
        # The airline-cost term of the surplus objective, on its own. This is what
        # "surplus" reduces to when demand cannot respond to price, so it is the
        # price_elasticity -> 0 limit of the published problem -- needed because the
        # surplus integral itself divides by the elasticity and is undefined at zero.
        # Same constraint set and scaling as "surplus" so the two are comparable.
        process.gemseo_settings["objective_name"] = "cumulative_total_airline_cost_discounted_obj"
        constraints = ["aviation_carbon_budget_constraint"] + _CONSTRAINTS
        scale = 1e-10
    else:
        raise ValueError(f"objective must be 'surplus', 'carbon' or 'cost', got {objective!r}")

    process.create_gemseo_scenario()

    # Bring the objective into a range SLSQP is comfortable with.
    problem = process.scenario.formulation.optimization_problem
    problem.objective = problem.objective * scale

    for constraint in constraints:
        # ``drop_constraints`` removes a constraint from the problem entirely rather
        # than relaxing its bound. The only use so far is the dedicated-wind
        # electrofuel run, where the pathway is assumed to build its own generation
        # and so does not draw on the shared electricity allocation G4 rations.
        if constraint in drop_constraints:
            continue
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


def run_sweep(
    case,
    budgets=None,
    config="config_rte.yaml",
    max_iter=50,
    resume=True,
    stop_on_error=False,
    **kwargs,
):
    """Carbon-budget continuation for one case, loosest budget first.

    Each optimisation starts from the previous one's optimum. Tightening the budget
    moves the optimum smoothly, so the previous solution is a far better start point
    than a fixed guess: SLSQP begins just outside the new feasible set instead of
    somewhere unrelated to it. The published notebooks instead pasted a hand-picked
    start into every run, which is why several of their low budgets were annotated
    "not possible" and commented out.

    An infeasible run is not propagated -- its ``x_opt`` is a best effort, not an
    optimum -- so the chain carries the last feasible design forward instead.

    With ``resume=True`` a budget already on disk is skipped and its optimum read back
    from the HDF, so an interrupted sweep continues cleanly. **A run that ended
    infeasible is skipped too**, because on the same start point it would reproduce
    itself exactly; the summary marks it and you delete its files to retry, normally
    after raising ``max_iter`` or handing it a different ``x0`` via
    ``run_optimisation``.

    A run that raises is reported and the ladder continues from the last feasible
    design, so one blow-up does not cost the whole sweep. Pass ``stop_on_error=True``
    to get the traceback instead.

    The returned frame covers the whole ladder, skipped runs included, so it is the
    same table whether the sweep ran from scratch or resumed.
    """
    budgets = budgets if budgets is not None else [3.8, 3.6, 3.4, 3.2, 3.0, 2.8, 2.6, 2.4, 2.2, 2.0]

    rows, x0 = [], None
    for budget in list(budgets) + [None]:
        label = "min CO2" if budget is None else budget
        stem = RESULTS_DIR / (
            f"opt_{case}_mincarb" if budget is None else f"opt_{case}_{budget_tag(budget)}"
        )

        if resume and stem.with_suffix(".json").exists():
            saved = read_run(stem.with_suffix(".hdf"))
            feasible = bool(saved and saved["feasible"])
            rows.append(
                {
                    "case": case,
                    "budget": label,
                    "objective": saved["objective"] if saved else np.nan,
                    "feasible": feasible,
                    "status": "on disk" if feasible else "on disk, INFEASIBLE - delete to retry",
                    "path": str(stem.with_suffix(".json")),
                }
            )
            print(f"{case} {label}: {rows[-1]['status']}, skipped")
            if feasible and budget is not None:
                x0 = saved["x"]
            continue

        try:
            row = run_optimisation(
                case, budget=budget, config=config, x0=x0, max_iter=max_iter, **kwargs
            )
        except Exception as error:
            if stop_on_error:
                raise
            # Nothing was saved: _save runs only after a successful compute.
            rows.append(
                {
                    "case": case,
                    "budget": label,
                    "objective": np.nan,
                    "feasible": False,
                    "status": f"{type(error).__name__}: {error}",
                    "path": "",
                }
            )
            print(f"{case} {label}: FAILED - {type(error).__name__}: {str(error)[:120]}")
            continue

        row["status"] = "ran" if row["feasible"] else "ran, INFEASIBLE"
        rows.append(row)
        print(
            f"{case} {label}: obj {row['objective']:+.4f}  "
            f"{'feasible' if row['feasible'] else 'INFEASIBLE'}  "
            f"{row['evaluations']} evals  {row['seconds']} s"
        )
        # min-CO2 is the last entry, so it consumes the chain but never feeds it.
        if row["feasible"] and budget is not None:
            x0 = row["x"]

    return pd.DataFrame(rows)


def read_run(hdf_path):
    """Recover a saved run's optimum, objective and feasibility from its HDF.

    Feasibility is what lets a resumed sweep tell a finished run from a failed one --
    the JSON is written either way, so its existence alone says nothing.
    """
    from gemseo.algos.optimization_problem import OptimizationProblem

    try:
        optimum = OptimizationProblem.from_hdf(str(hdf_path)).optimum
        x = np.asarray(optimum.design)
    except Exception:
        return None
    if x.size != 10:
        return None
    return {
        "x": {"electrofuel": list(x[:5]), "biofuel": list(x[5:])},
        "objective": float(np.ravel(optimum.objective)[0]),
        "feasible": bool(optimum.is_feasible),
    }


# Display order and labels of the five vector constraints, all enforced on
# OPTIM_YEARS, so their five components read as one row per reference year.
CONSTRAINT_LABELS = OrderedDict(
    [
        ("blend_completeness_constraint", "Blend\ncompleteness"),
        ("biomass_trajectory_constraint", "Biomass\navailability"),
        ("electricity_trajectory_constraint", "Electricity\navailability"),
        ("biofuel_use_growth_constraint", "Biofuel\nramp-up"),
        ("electrofuel_use_growth_constraint", "Electrofuel\nramp-up"),
    ]
)

CARBON_CONSTRAINT = "aviation_carbon_budget_constraint"


def _constraint_frame(values):
    """One evaluation's constraint values as a frame indexed by enforcement year."""
    columns = {}
    for name in CONSTRAINT_LABELS:
        component = values.get(name)
        if component is None:
            continue
        component = np.ravel(np.asarray(component, dtype=float))
        if component.size == len(OPTIM_YEARS):
            columns[name] = component
    return pd.DataFrame(columns, index=OPTIM_YEARS)


def _mandate_frame(x):
    """The design vector as a year x pathway frame, in design-space order."""
    x = np.ravel(np.asarray(x, dtype=float))
    return pd.DataFrame(
        {"electrofuel": x[:5], "biofuel": x[5:]},
        index=OPTIM_YEARS,
    )


def _evaluation(values, x):
    """One point of a run: what it asked for, and what that violated."""
    carbon = values.get(CARBON_CONSTRAINT)
    return {
        "constraints": _constraint_frame(values),
        "carbon": float(np.ravel(carbon)[0]) if carbon is not None else np.nan,
        "mandate": _mandate_frame(x),
    }


def read_constraints(hdf_path):
    """A saved run's optimum, as ``constraints`` / ``carbon`` / ``mandate`` / ``feasible``.

    ``constraints`` is the five vector constraints as a year x constraint frame,
    ``carbon`` the scalar carbon-budget constraint (NaN for a min-CO2 run, where it
    is the objective) and ``mandate`` the design variables the optimiser settled on.
    Negative is slack, zero is active, positive is violated.
    """
    from gemseo.algos.optimization_problem import OptimizationProblem

    try:
        optimum = OptimizationProblem.from_hdf(str(hdf_path)).optimum
    except Exception:
        return None
    evaluation = _evaluation(optimum.constraints or {}, optimum.design)
    evaluation["feasible"] = bool(optimum.is_feasible)
    return evaluation


def read_constraint_history(hdf_path):
    """Every iterate of a saved run, in the same shape ``read_constraints`` returns.

    Line-search points carry the objective alone and are dropped; so are the points
    a hair away from their predecessor, which are finite-difference perturbations
    rather than steps. The last entry is the optimum.
    """
    from gemseo.algos.optimization_problem import OptimizationProblem

    problem = OptimizationProblem.from_hdf(str(hdf_path))
    history, previous = [], None
    for x in problem.database.get_x_vect_history():
        values = problem.database[x]
        if not all(name in values for name in CONSTRAINT_LABELS):
            continue
        x = np.asarray(x, dtype=float)
        if previous is not None and np.linalg.norm(x - previous) < 1e-5:
            continue
        previous = x
        history.append(_evaluation(values, x))
    return history


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


DEFAULT_BUDGETS = [3.8, 3.6, 3.4, 3.2, 3.0, 2.8, 2.6, 2.4, 2.2, 2.0]


def status(cases=None, budgets=None):
    """What is on disk, as a case-by-budget grid, with the age of each result.

    The terminal view of a sweep in progress. It reads ``results/`` rather than any
    log, so it reports a sweep running in a notebook kernel -- whose output goes to
    the cell, not to any terminal -- exactly as well as one started from a shell.

    Cells are ``ok`` / ``INFEAS`` plus how long ago the file was written, so the run
    in progress is the one whose case has a result a few minutes old.
    """
    cases = list(cases or CASES)
    budgets = DEFAULT_BUDGETS if budgets is None else list(budgets)
    now = time.time()

    def cell(stem):
        result = stem.with_suffix(".json")
        if not result.exists():
            return "-"
        age = (now - result.stat().st_mtime) / 60
        age_text = f"{age:.0f}m" if age < 90 else f"{age / 60:.1f}h"
        saved = read_run(stem.with_suffix(".hdf"))
        if saved is None:  # a reference MDA has no history
            return f"ok {age_text}"
        return f"{'ok' if saved['feasible'] else 'INFEAS'} {age_text}"

    rows = []
    for label, tag in [(f"{b:.1f}", budget_tag(b)) for b in budgets] + [("min CO2", "mincarb")]:
        rows.append(
            {
                "budget": label,
                **{case: cell(RESULTS_DIR / f"opt_{case}_{tag}") for case in cases},
            }
        )
    for kind in ("fossil", "refueleu"):
        rows.append(
            {
                "budget": kind,
                **{case: cell(RESULTS_DIR / f"{kind}_{case}") for case in cases},
            }
        )

    frame = pd.DataFrame(rows).set_index("budget")
    print(f"results in {RESULTS_DIR.resolve()}")
    print(frame.to_string())
    done = (frame != "-").sum().sum()
    print(f"\n{done} of {frame.size} runs on disk")
    return frame


# --------------------------------------------------------------------------- #
# Command line: one case per process
# --------------------------------------------------------------------------- #
#
# The five cases share nothing -- disjoint parameters, disjoint result files -- so
# they are the level at which this problem parallelises:
#
#     for case in main B5 B75 B15 pess; do
#         poetry run python optimisation_runs.py $case > log_$case.txt 2>&1 &
#     done
#
# Five processes, one core each, five sweeps in the time of the slowest. Nothing
# below that level is worth parallelising:
#
# * The budgets of one case are a continuation chain -- each starts from the
#   previous optimum -- so they are sequential by construction. Running them
#   independently means giving that up and cold-starting each one.
# * Parallel finite differences inside a run do not pay. GEMSEO refuses threads
#   ("all workers shall be different objects": the eleven perturbed points share one
#   MDA object). Processes work but measured 436 s against 112 s serial on three
#   SLSQP iterations -- roughly 4x slower, because each point ships the whole
#   106-discipline chain to a worker and, worse, the workers cannot see the memo
#   installed by share_mda_across_functions, whose ~7x saving is larger than
#   anything the parallelism could return.


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Run one case of the ReFuelEU sweep.")
    parser.add_argument(
        "case", nargs="?", choices=sorted(CASES), help="which published variant to run"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="print what is on disk for every case and exit; works while sweeps are running",
    )
    parser.add_argument("--max-iter", type=int, default=50)
    parser.add_argument("--config", default="config_rte.yaml")
    parser.add_argument("--no-resume", action="store_true", help="re-run budgets already on disk")
    args = parser.parse_args(argv)

    if args.status:
        return status()
    if args.case is None:
        parser.error("give a case to run, or --status")

    # Make the log worth tailing. Three separate problems, all of them silent:
    #   - stdout is block-buffered when redirected to a file, so the per-run lines sit
    #     in a 8 kB buffer for hours. Line buffering puts them in the log as they print.
    #   - GEMSEO logs at INFO, including the SLSQP iteration lines, but only once a
    #     handler exists; without configure_logger() the run is completely quiet.
    #   - the yaml interpolation UserWarnings otherwise bury everything else.
    import warnings

    import gemseo

    from aeromaps.utils.functions import custom_logger_config

    sys.stdout.reconfigure(line_buffering=True)
    warnings.filterwarnings("ignore")
    custom_logger_config(gemseo.configure_logger())

    for kind in ("fossil", "refueleu"):
        run_reference(args.case, kind=kind, config=args.config)

    summary = run_sweep(
        args.case,
        config=args.config,
        max_iter=args.max_iter,
        resume=not args.no_resume,
    )
    print()
    print(summary.drop(columns=["x"], errors="ignore").to_string(index=False))
    return summary


if __name__ == "__main__":
    main()

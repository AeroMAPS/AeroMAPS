"""Overnight sweep: one-parameter-at-a-time around the ReFuelEU-equivalent budget.

Every run in blocks A-D shares one carbon budget -- the cumulative 2020-2050 CO2 of
the ReFuelEU (linear) scenario at eps_P = -0.9, computed once and held fixed. It is
expressed as a share because that is what ``CarbonBudgetConstraint`` takes, but the
two are equivalent: when the constraint is active it pins

    cumulative_co2_emissions[2050] = gross_carbon_budget_2050 * share / 100

and both factors on the right are exogenous, so a fixed share *is* a fixed absolute
budget. Verified across the elasticity sweep: C2050 identical to six significant
figures while C2025 moved by 0.6 %.

Biomass allocated to aviation is 10 % here, not the paper's 9.90 %. The old value was
reverse-engineered so that production efficiency covered 2019 aviation energy use,
which makes a convention look derived.

Usage
-----
    poetry run python run_batch.py --jobs 3     # whole batch, resumable
    poetry run python run_batch.py --jobs 3 eps_m0_6 eps_m0_8
    poetry run python run_batch.py --only base  # in-process, no log capture
    poetry run python run_batch.py --list

Each run is a subprocess whose entire output -- GEMSEO's logger, the SLSQP progress
bar, any traceback -- goes to ``logs/<run_id>.log``, so a run in progress can be
watched with ``tail -f`` and a finished one still has its full record. ``status.py``
gives the overview; ``--jobs N`` runs N of them at once.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections import OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
sys.path.insert(0, str(PAPER))

RESULTS = HERE / "results"
LOGS = HERE / "logs"
SUMMARY = HERE / "summary.csv"
# One file per run. Parallel children cannot safely read-modify-write a shared CSV,
# so each writes only its own row and the driver merges them.
ROWS = HERE / "rows"

# --------------------------------------------------------------------------- #
# The fixed framing
# --------------------------------------------------------------------------- #

# ReFuelEU (linear) at eps_P = -0.9: cumulative 2020-2050 CO2 on the EU perimeter,
# against a world gross budget of 799.1892711816 GtCO2. ``build_process`` takes the share
# *before* the EU downscaling, hence the division by EU_ASK_SHARE.
#
# ``preflight.py`` recomputes this from the reference run and says so if it has moved.
#
# It moved when the mandate's first obligation became a step at 2025 rather than a
# linear phase-in from 2020, which stopped the reference abating 4.06 MtCO2 in four years
# the regulation obliges nothing -- abatement that lowered the ceiling for every run
# rather than buying any of them headroom. (The ramp-up correction cannot move it: this
# is the cumulative CO2 of an MDA, and constraints do not enter one.) Earlier values,
# for reference: 3.119357596335 % / 3.8615905850289276 GtCO2.
BUDGET_WORLD_SHARE = 3.122636344
BUDGET_GTCO2 = 3.8656495

BIOMASS_SHARE = 10.0  # % of world biomass allocated to aviation (was 9.90)

# The paper's default is ftol_abs=1e-3, a relative tolerance of ~2e-4 on an objective
# of order 5. On the carbon-budget sweep that stopped SLSQP with the design still
# moving and shifted mandate shares by up to 11.8 percentage points. Mandate share is
# the headline output of this batch, so it is tightened.
#
# The ftol stop is disabled outright rather than tightened. "The objective stopped
# moving" is not an optimality test, and every run here warm-starts from the baseline
# optimum, where a one-parameter change often leaves the objective nearly flat on the
# first trial step: the first pass at ftol_abs=1e-8 stopped r_3_2 after 4 evaluations
# without it having moved from its start point at all, while its sibling r_7 moved by
# 2.09 and stopped on KKT. The KKT residual is the criterion worth trusting, so it is
# left as the only one -- max_iter still bounds the run.
FTOL = 0.0
KKT_TOL_REL = 1e-6
MAX_ITER = 50

# --------------------------------------------------------------------------- #
# The matrix
# --------------------------------------------------------------------------- #

# One parameter at a time from a common centre. ``base`` is the centre and is also
# block A's eps = -0.9 entry, block B's 20 %/yr entry, block B's 0.2 EJ/yr entry, block
# C's grid-electricity entry and block D's 4.5 % entry -- which is why the batch is 13
# optimisations rather than the ~20 the brief estimated.
RUNS = OrderedDict(
    [
        (
            "base",
            {"block": "baseline", "label": "baseline (eps -0.9, 20 %/yr, 0.2 EJ/yr, r 4.5 %)"},
        ),
        # A. Elasticity.
        ("eps_m0_6", {"block": "A", "label": "eps_P = -0.6", "elasticity": -0.6}),
        ("eps_m0_8", {"block": "A", "label": "eps_P = -0.8", "elasticity": -0.8}),
        ("eps_m1_0", {"block": "A", "label": "eps_P = -1.0", "elasticity": -1.0}),
        ("eps_m1_4", {"block": "A", "label": "eps_P = -1.4", "elasticity": -1.4}),
        # A'. Fixed demand: no airfare -> RPK loop at all, and the airline-cost
        # objective the surplus objective reduces to when demand cannot respond.
        (
            "fixed_demand",
            {"block": "A'", "label": "fixed demand (no cost feedback)", "no_feedback": True},
        ),
        # B. Ramp-up rate cap.
        ("rate_11_8", {"block": "B", "label": "ramp rate 11.8 %/yr (IEA NZE)", "rate": 0.118}),
        ("rate_39", {"block": "B", "label": "ramp rate 39 %/yr (wind/PV emergence)", "rate": 0.39}),
        # B'. Ramp-up volume cap.
        ("vol_0_1", {"block": "B'", "label": "ramp volume 0.1 EJ/yr", "volume": 0.1}),
        ("vol_0_4", {"block": "B'", "label": "ramp volume 0.4 EJ/yr", "volume": 0.4}),
        # C. Dedicated-wind electrofuel. The pathway builds its own generation, so it
        # does not draw on the shared electricity allocation and G4 is dropped -- not
        # relaxed, dropped, so the run answers what the optimum is without that limit.
        (
            "efuel_wind",
            {
                "block": "C",
                "label": "dedicated-wind electrofuel, no electricity limit",
                "efuel_wind": True,
                "drop_constraints": ("electricity_trajectory_constraint",),
            },
        ),
        # D. Discount rate. Enters the objective's definition as well as the scenario,
        # so part of any movement is mechanical.
        ("r_3_2", {"block": "D", "label": "discount rate 3.2 %", "discount": 0.032}),
        ("r_7", {"block": "D", "label": "discount rate 7 %", "discount": 0.07}),
        # An extreme rate, well outside any social-discounting convention. It is here to
        # find where the vertex breaks: 3.2 % leaves the optimum exactly where 4.5 % put
        # it, and 7 % barely moves it, so the question is how hard the objective has to
        # be tilted before the active set itself changes.
        ("r_15", {"block": "D", "label": "discount rate 15 % (extreme)", "discount": 0.15}),
    ]
)

WIND_CSV = HERE / "efuel_dedicated_wind.csv"


# --------------------------------------------------------------------------- #
# One run
# --------------------------------------------------------------------------- #


def _apply(process, spec, R):
    """Everything this batch changes relative to ``build_process``'s defaults."""
    # Biomass allocation, every run.
    process.parameters.generic_biomass_availability_aviation_allocated_share = (
        BIOMASS_SHARE * R.EU_ASK_SHARE
    )

    if "elasticity" in spec:
        process.parameters.price_elasticity = spec["elasticity"]

    if "rate" in spec:
        process.parameters.rate_ramp_up_constraint_biofuel = spec["rate"]
        process.parameters.rate_ramp_up_constraint_electrofuel = spec["rate"]

    if "volume" in spec:
        process.parameters.volume_ramp_up_constraint_biofuel = spec["volume"] * R.EU_ASK_SHARE
        process.parameters.volume_ramp_up_constraint_electrofuel = spec["volume"] * R.EU_ASK_SHARE

    if "discount" in spec:
        process.parameters.social_discount_rate = spec["discount"]

    if spec.get("efuel_wind"):
        wind = pd.read_csv(WIND_CSV)
        # The baseline series carry a 2000 anchor holding the 2020 value, so the swap
        # keeps the same shape rather than extrapolating off the front of the table.
        years = [2000] + wind["year"].astype(int).tolist()
        mfsp = [float(wind["mfsp"].iloc[0])] + wind["mfsp"].astype(float).tolist()
        ef = [float(wind["emission_factor"].iloc[0])] + wind["emission_factor"].astype(
            float
        ).tolist()
        process.parameters.generic_electrofuel_mean_mfsp_without_resource_years = years
        process.parameters.generic_electrofuel_mean_mfsp_without_resource_values = mfsp
        process.parameters.generic_electrofuel_mean_co2_emission_factor_without_resource_years = (
            years
        )
        process.parameters.generic_electrofuel_mean_co2_emission_factor_without_resource_values = ef

    return process


def _x0(R):
    """Start every run from the baseline optimum; fall back to the cold start."""
    saved = R.read_run(RESULTS / "base.hdf")
    if saved and saved["feasible"]:
        return saved["x"]
    return None  # setup_optimisation falls back to COLD_START


def run_one(run_id):
    """Build, solve and save one run. Runs in the current process."""
    import logging

    import optimisation_runs as R
    from aeromaps.core.gemseo import disable_gemseo_execution_statistics
    from gemseo import configure_logger
    from gemseo.algos.opt.scipy_local.settings.slsqp import SLSQP_Settings

    # GEMSEO reports each SLSQP iteration at INFO. Without a handler at that level the
    # log holds only warnings, which is nothing to watch: a run that is progressing and
    # a run that is wedged look identical. Only the gemseo logger is raised -- the root
    # logger at INFO buries the run under matplotlib and font-manager chatter.
    # GEMSEO's own logger configuration, which is what produced the paper's run logs:
    # the problem statement, the design-space table, and one line per SLSQP iteration
    # carrying the objective. Without it the log holds only warnings, and a run that is
    # progressing looks exactly like one that is wedged.
    configure_logger(level=logging.INFO)

    disable_gemseo_execution_statistics()
    os.chdir(PAPER)  # config yamls resolve against the working directory

    spec = RUNS[run_id]
    no_feedback = bool(spec.get("no_feedback"))
    config = "config_rte_nofeedback.yaml" if no_feedback else "config_rte.yaml"
    objective = "cost" if no_feedback else "surplus"

    print(f"=== {run_id}: {spec['label']} (block {spec['block']}) ===", flush=True)
    print(
        f"    budget {BUDGET_WORLD_SHARE:.6f} % world share = {BUDGET_GTCO2:.6f} GtCO2", flush=True
    )
    print(f"    config {config}, objective {objective}, biomass {BIOMASS_SHARE} %", flush=True)

    process = R.build_process(
        "main", config=config, optimisation=True, carbon_budget=BUDGET_WORLD_SHARE
    )
    _apply(process, spec, R)

    x0 = None if run_id == "base" else _x0(R)
    R.setup_optimisation(
        process,
        x0=x0,
        max_iter=MAX_ITER,
        objective=objective,
        drop_constraints=spec.get("drop_constraints", ()),
    )
    # Replace only the solver settings; setup_optimisation has built everything else.
    process.gemseo_settings["algorithm"] = SLSQP_Settings(
        max_iter=MAX_ITER,
        enable_progress_bar=True,
        ftol_abs=FTOL,
        ftol_rel=FTOL,
        kkt_tol_rel=KKT_TOL_REL,
        normalize_design_space=False,
    )

    start = time.perf_counter()
    process.compute()
    elapsed = time.perf_counter() - start

    R._save(process, RESULTS / run_id)
    problem = process.scenario.formulation.optimization_problem
    result = process.scenario.get_result().optimization_result

    row = {
        "run": run_id,
        "block": spec["block"],
        "label": spec["label"],
        "objective_name": objective,
        "f_opt": float(result.f_opt),
        "feasible": bool(result.is_feasible),
        "message": str(result.message),
        "n_evaluations": len(problem.database),
        "max_constraint_violation": _max_violation(problem),
        "seconds": round(elapsed, 1),
        "budget_world_share": BUDGET_WORLD_SHARE,
        "biomass_share": BIOMASS_SHARE,
        "elasticity": spec.get("elasticity", "n/a" if no_feedback else -0.9),
        "rate_cap": spec.get("rate", 0.20),
        "volume_cap": spec.get("volume", 0.2),
        "discount_rate": spec.get("discount", 0.045),
        "efuel_pathway": "dedicated wind" if spec.get("efuel_wind") else "grid electricity",
        "dropped_constraints": ";".join(spec.get("drop_constraints", ())) or "none",
        "ftol_abs": FTOL,
        "kkt_tol_rel": KKT_TOL_REL,
    }
    _write_row(row)
    print(
        f"--- {run_id}: f={row['f_opt']:.6f} feasible={row['feasible']} "
        f"({row['seconds']:.0f} s, {row['n_evaluations']} evals, "
        f"max violation {row['max_constraint_violation']:.2e})",
        flush=True,
    )
    return row


def _max_violation(problem):
    """Largest constraint violation at the optimum, across scalar and vector ones."""
    optimum = problem.optimum
    worst = 0.0
    for value in (optimum.constraints or {}).values():
        worst = max(worst, float(np.max(np.ravel(np.asarray(value, dtype=float)))))
    return worst


def _write_row(row):
    """Record this run's diagnostics, and refresh the merged summary."""
    ROWS.mkdir(exist_ok=True)
    (ROWS / f"{row['run']}.json").write_text(json.dumps(row, indent=2, default=str))
    rebuild_summary()


def rebuild_summary():
    """Merge the per-run rows into summary.csv, in matrix order.

    Idempotent and safe to call from anywhere: it only ever reads the row files and
    overwrites the summary, so a parallel child finishing mid-rebuild costs at worst a
    summary that is one row stale until the next call.
    """
    rows = []
    for run_id in RUNS:
        path = ROWS / f"{run_id}.json"
        if path.exists():
            rows.append(json.loads(path.read_text()))
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    frame.to_csv(SUMMARY, index=False)
    return frame


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #


def _done(run_id):
    return (RESULTS / f"{run_id}.json").exists() and (RESULTS / f"{run_id}.hdf").exists()


def _spawn(run_id):
    """Start one run as a subprocess, its whole output going to logs/<run_id>.log."""
    log = LOGS / f"{run_id}.log"
    handle = open(log, "w")
    handle.write(f"# {run_id}: {RUNS[run_id]['label']}\n")
    handle.write(f"# started {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    handle.flush()
    process = subprocess.Popen(
        [sys.executable, "-u", str(Path(__file__).resolve()), "--only", run_id],
        stdout=handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process, handle, time.time()


def drive(run_ids, jobs=1):
    """Run the queue, at most ``jobs`` at a time.

    Every run warm-starts from the baseline optimum, so ``base`` is a barrier: it runs
    alone and the rest only start once it is on disk. Without that they would all fall
    back to the cold start and take longer than the serialisation saves.

    Each run's output goes to its own log rather than to the console, because parallel
    runs interleaved on one stream are unreadable. The console gets one line per start
    and per finish; ``status.py`` gives the overview.
    """
    RESULTS.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)

    queue = [r for r in run_ids if not _done(r)]
    for run_id in run_ids:
        if _done(run_id):
            print(f"{run_id}: on disk, skipped", flush=True)

    # The barrier: base first, alone.
    if "base" in queue:
        queue.remove("base")
        print("base: running alone (warm-start source) -> logs/base.log", flush=True)
        process, handle, started = _spawn("base")
        code = process.wait()
        handle.close()
        print(
            f"base: {'done' if code == 0 else f'FAILED (exit {code})'}"
            f" in {time.time() - started:.0f} s",
            flush=True,
        )
        if code != 0:
            print("base failed; the rest would start from the cold start. Stopping.", flush=True)
            return

    running = {}
    while queue or running:
        while queue and len(running) < jobs:
            run_id = queue.pop(0)
            print(
                f"{run_id}: started ({len(running) + 1}/{jobs} slots) -> logs/{run_id}.log",
                flush=True,
            )
            running[run_id] = _spawn(run_id)

        time.sleep(5)

        for run_id, (process, handle, started) in list(running.items()):
            code = process.poll()
            if code is None:
                continue
            handle.close()
            del running[run_id]
            elapsed = time.time() - started
            if code == 0:
                print(f"{run_id}: done in {elapsed:.0f} s", flush=True)
            else:
                # A failure is recorded and the batch continues: one blow-up should not
                # cost the night. The missing row in summary.csv is the record.
                print(
                    f"{run_id}: FAILED (exit {code}) after {elapsed:.0f} s,"
                    f" see logs/{run_id}.log",
                    flush=True,
                )

    rebuild_summary()
    print("\nbatch finished; summary.csv rebuilt", flush=True)


def main(argv):
    if "--list" in argv:
        for run_id, spec in RUNS.items():
            mark = "done" if _done(run_id) else "    "
            print(f"  [{mark}] {run_id:14s} {spec['block']:8s} {spec['label']}")
        return
    if "--only" in argv:
        run_one(argv[argv.index("--only") + 1])
        return
    jobs = 1
    if "--jobs" in argv:
        index = argv.index("--jobs")
        jobs = int(argv[index + 1])
        argv = argv[:index] + argv[index + 2 :]
    wanted = [a for a in argv if not a.startswith("-")]
    unknown = [a for a in wanted if a not in RUNS]
    if unknown:
        raise SystemExit(f"unknown run(s): {unknown}. --list to see them.")
    drive(wanted or list(RUNS), jobs=jobs)


if __name__ == "__main__":
    main(sys.argv[1:])

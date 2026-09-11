"""Block E: the carbon-budget x biomass-share surface behind Figure 9, regenerated.

Why it has to be re-run rather than reused. Two things moved under the published
surface: the surplus beta is now anchored on ``initial_airfare_per_rpk`` -- the same
2019 price that anchors supply and the traffic response -- where it used to be anchored
on the scenario's own airfare in 2025; and aviation's biomass allocation is 10 % rather
than the reverse-engineered 9.90 %. The first changes the objective non-uniformly,
because the surplus share of it ranges from 15 % to 98 % across the budget ladder, so
optima move rather than merely rescale.

Every surplus figure in the submitted paper depends on this surface: Table 3's
cumulative losses, the 614 bn EUR vs BAU and its 537 bn EUR / 27 % split, the ReFuelEU
annotations on Figure 9, and section 4.4's 39 % / 242 bn EUR / 95 bn EUR.

The budget axis is deliberately unchanged -- the point of the figure is to explore
ambitious scenarios, so it is not re-centred on the ReFuelEU-equivalent value. That
value, 3.119358 % of the world budget, is marked on the surface instead, alongside the
existing ReFuelEU linear and step markers.

``pess`` is swept here because it is the same ladder and costs nothing extra to run,
but it does not belong on Figure 9: its biomass share coincides with ``main``'s, so it
would land on top of it. It is a technology sensitivity, reported separately.

Each case is a continuation chain -- loosest budget first, each run started from the
previous optimum -- so a case must stay serial. Cases are independent, and run in
parallel.

Usage
-----
    poetry run python run_block_e.py --jobs 3
    poetry run python run_block_e.py --jobs 3 main B15
    poetry run python run_block_e.py --only main       # one case, in this process
    poetry run python run_block_e.py --status
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
sys.path.insert(0, str(PAPER))
sys.path.insert(0, str(HERE))

RESULTS_E = HERE / "results_e"
LOGS = HERE / "logs"

# The published ladder, unchanged. min-CO2 is appended by run_sweep itself.
BUDGETS = [3.8, 3.6, 3.4, 3.2, 3.0, 2.8, 2.6, 2.4, 2.2, 2.0]

# The four biomass shares Figure 9 interpolates over, plus the technology sensitivity.
# 9.90 becomes 10.0 for the two cases that carried it; B5/B75/B15 keep their own.
CASES = ["main", "B5", "B75", "B15", "pess"]
BIOMASS_OVERRIDE = {"main": 10.0, "pess": 10.0}

FTOL = 0.0
KKT_TOL_REL = 1e-6
MAX_ITER = 50


def run_case(case):
    """One case's full budget continuation, written to results_e/."""
    import logging

    import optimisation_runs as R
    from aeromaps.core.gemseo import disable_gemseo_execution_statistics
    from gemseo import configure_logger
    from gemseo.algos.opt.scipy_local.settings.slsqp import SLSQP_Settings

    # GEMSEO's own logger configuration, which is what produced the paper's run logs:
    # the problem statement, the design-space table, and one line per SLSQP iteration
    # carrying the objective. Without it the log holds only warnings, and a run that is
    # progressing looks exactly like one that is wedged.
    configure_logger(level=logging.INFO)

    disable_gemseo_execution_statistics()
    os.chdir(PAPER)

    if case in BIOMASS_OVERRIDE:
        R.CASES[case]["biomass_share"] = BIOMASS_OVERRIDE[case]
    RESULTS_E.mkdir(exist_ok=True)
    R.RESULTS_DIR = RESULTS_E

    # Same tightening as blocks A-D: the ftol stop is off, KKT is the only criterion.
    original = R.setup_optimisation

    def tightened(process, *args, **kwargs):
        result = original(process, *args, **kwargs)
        process.gemseo_settings["algorithm"] = SLSQP_Settings(
            max_iter=kwargs.get("max_iter", MAX_ITER),
            enable_progress_bar=True,
            ftol_abs=FTOL,
            ftol_rel=FTOL,
            kkt_tol_rel=KKT_TOL_REL,
            normalize_design_space=False,
        )
        return result

    R.setup_optimisation = tightened

    print(f"=== block E, case {case}, biomass {R.CASES[case]['biomass_share']} % ===", flush=True)
    frame = R.run_sweep(case, budgets=BUDGETS, max_iter=MAX_ITER)
    frame.to_csv(RESULTS_E / f"sweep_{case}.csv", index=False)

    # The two fixed-mandate comparison points, at this case's biomass share.
    for kind in ("fossil", "refueleu"):
        R.run_reference(case, kind=kind)
    print(f"=== block E, case {case}: finished ===", flush=True)


def run_rung(case, tag, seed_dir):
    """One budget of one case, started from the same budget's previous optimum.

    The chain in ``run_case`` exists because a neighbouring budget is a better start
    point than a fixed guess. An optimum at the *same* budget under a slightly different
    model is better still -- and, unlike the chain, it makes the rungs independent, so
    all 55 run at once instead of five chains of eleven.

    The seed is a start point, not an answer: SLSQP still has to satisfy the current
    constraints from it. A missing or infeasible seed falls back to the cold start rather
    than failing, so a partial seed directory is usable.
    """
    import logging

    import optimisation_runs as R
    from aeromaps.core.gemseo import disable_gemseo_execution_statistics
    from gemseo import configure_logger
    from gemseo.algos.opt.scipy_local.settings.slsqp import SLSQP_Settings

    configure_logger(level=logging.INFO)
    disable_gemseo_execution_statistics()
    os.chdir(PAPER)

    if case in BIOMASS_OVERRIDE:
        R.CASES[case]["biomass_share"] = BIOMASS_OVERRIDE[case]
    RESULTS_E.mkdir(exist_ok=True)
    R.RESULTS_DIR = RESULTS_E

    original = R.setup_optimisation

    def tightened(process, *args, **kwargs):
        result = original(process, *args, **kwargs)
        process.gemseo_settings["algorithm"] = SLSQP_Settings(
            max_iter=kwargs.get("max_iter", MAX_ITER),
            enable_progress_bar=True,
            ftol_abs=FTOL,
            ftol_rel=FTOL,
            kkt_tol_rel=KKT_TOL_REL,
            normalize_design_space=False,
        )
        return result

    R.setup_optimisation = tightened

    budget = None if tag == "mincarb" else float(tag.replace("_", "."))
    seed = R.read_run(Path(seed_dir) / f"opt_{case}_{tag}.hdf")
    x0 = seed["x"] if seed and seed["feasible"] else None

    print(f"=== block E, {case} {tag}, biomass {R.CASES[case]['biomass_share']} % ===", flush=True)
    print(
        f"    seed: {'opt_' + case + '_' + tag + ' from ' + str(seed_dir)}"
        if x0
        else "    seed: none available, cold start",
        flush=True,
    )

    row = R.run_optimisation(case, budget=budget, x0=x0, max_iter=MAX_ITER)
    print(
        f"--- {case} {tag}: obj {row['objective']:+.5f} "
        f"{'feasible' if row['feasible'] else 'INFEASIBLE'} "
        f"{row['evaluations']} evals {row['seconds']} s",
        flush=True,
    )


def _spawn_rung(case, tag, seed_dir):
    log = LOGS / f"blockE_{case}_{tag}.log"
    handle = open(log, "w")
    handle.write(f"# block E, {case} {tag}\n# started {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    handle.flush()
    process = subprocess.Popen(
        [
            sys.executable,
            "-u",
            str(Path(__file__).resolve()),
            "--only-rung",
            case,
            tag,
            str(seed_dir),
        ],
        stdout=handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process, handle, time.time()


def drive_seeded(cases, jobs, seed_dir):
    """Every (case, budget) as an independent job, seeded from ``seed_dir``."""
    RESULTS_E.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    tags = [f"{b:.1f}".replace(".", "_") for b in BUDGETS] + ["mincarb"]

    # Budget-major, so a round of the queue takes one rung from each case rather than
    # finishing one case before starting the next. Wall time is the same either way --
    # the rungs are independent now -- but every case advances from the start, so a case
    # that is going to misbehave says so in the first few minutes instead of an hour in.
    # Ordering costs nothing in seed quality: each rung is seeded from its own budget.
    queue = [
        (case, tag)
        for tag in tags
        for case in cases
        if not (RESULTS_E / f"opt_{case}_{tag}.json").exists()
    ]
    print(f"{len(queue)} rungs to run, {jobs} at a time, seeded from {seed_dir}\n", flush=True)

    running = {}
    while queue or running:
        while queue and len(running) < jobs:
            case, tag = queue.pop(0)
            print(f"{case} {tag}: started -> logs/blockE_{case}_{tag}.log", flush=True)
            running[(case, tag)] = _spawn_rung(case, tag, seed_dir)
        time.sleep(10)
        for key, (process, handle, started) in list(running.items()):
            if process.poll() is None:
                continue
            handle.close()
            code = process.returncode
            del running[key]
            print(
                f"{key[0]} {key[1]}: {'done' if code == 0 else f'FAILED (exit {code})'}"
                f" in {(time.time() - started) / 60:.0f} min",
                flush=True,
            )

    # The fixed-mandate comparison points, once per case.
    for case in cases:
        for kind in ("fossil", "refueleu"):
            subprocess.run(
                [sys.executable, "-u", str(Path(__file__).resolve()), "--reference", case, kind],
                check=False,
            )
    print("\nblock E finished", flush=True)


def run_case_reference(case, kind):
    import logging

    import optimisation_runs as R
    from aeromaps.core.gemseo import disable_gemseo_execution_statistics
    from gemseo import configure_logger

    configure_logger(level=logging.WARNING)
    disable_gemseo_execution_statistics()
    os.chdir(PAPER)
    if case in BIOMASS_OVERRIDE:
        R.CASES[case]["biomass_share"] = BIOMASS_OVERRIDE[case]
    RESULTS_E.mkdir(exist_ok=True)
    R.RESULTS_DIR = RESULTS_E
    R.run_reference(case, kind=kind)


def _spawn(case):
    log = LOGS / f"blockE_{case}.log"
    handle = open(log, "w")
    handle.write(f"# block E, case {case}\n# started {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    handle.flush()
    process = subprocess.Popen(
        [sys.executable, "-u", str(Path(__file__).resolve()), "--only", case],
        stdout=handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process, handle, time.time()


def drive(cases, jobs=3):
    RESULTS_E.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    queue, running = list(cases), {}
    while queue or running:
        while queue and len(running) < jobs:
            case = queue.pop(0)
            print(f"{case}: started -> logs/blockE_{case}.log", flush=True)
            running[case] = _spawn(case)
        time.sleep(10)
        for case, (process, handle, started) in list(running.items()):
            if process.poll() is None:
                continue
            handle.close()
            code = process.returncode
            del running[case]
            print(
                f"{case}: {'done' if code == 0 else f'FAILED (exit {code})'}"
                f" in {(time.time() - started) / 60:.0f} min",
                flush=True,
            )
    print("\nblock E finished", flush=True)


def _running_rungs():
    """(case, tag) pairs with a live subprocess."""
    try:
        out = subprocess.run(
            ["pgrep", "-fl", "run_block_e.py"], capture_output=True, text=True
        ).stdout
    except FileNotFoundError:
        return {}
    live = {}
    for line in out.splitlines():
        if "--only-rung" in line:
            parts = line.split("--only-rung", 1)[1].split()
            if len(parts) >= 2:
                live[(parts[0], parts[1])] = True
        elif "--only" in line:
            live[(line.split("--only", 1)[1].split()[0], "*")] = True
    return live


def status():
    """The whole ladder as a case x budget grid, plus what is running now."""
    tags = [f"{b:.1f}".replace(".", "_") for b in BUDGETS] + ["mincarb"]
    live, now = _running_rungs(), time.time()

    print(f"=== block E, carbon budget x biomass ladder  ({time.strftime('%H:%M:%S')}) ===\n")
    header = "        " + "".join(f"{t.replace('_', '.'):>8}" for t in tags)
    print(header)

    done = failed = 0
    durations = []
    for case in CASES:
        row = f"{case:>7} "
        for tag in tags:
            result = RESULTS_E / f"opt_{case}_{tag}.json"
            if result.exists():
                saved = R_read(RESULTS_E / f"opt_{case}_{tag}.hdf")
                ok = saved is None or saved["feasible"]
                done += 1
                failed += not ok
                row += f"{'  ok' if ok else '  XX':>8}"
                log = LOGS / f"blockE_{case}_{tag}.log"
                if log.exists():
                    durations.append(log.stat().st_mtime - _started(log))
            elif (case, tag) in live or (case, "*") in live:
                log = LOGS / f"blockE_{case}_{tag}.log"
                age = (now - _started(log)) / 60 if log.exists() else 0
                row += f"{f'{age:.0f}m':>8}"
            else:
                row += f"{'.':>8}"
        print(row)

    total = len(CASES) * len(tags)
    print(f"\n  {done}/{total} on disk" + (f", {failed} INFEASIBLE" if failed else ""))
    if live:
        print("  running now: " + ", ".join(f"{c} {t}" for c, t in sorted(live)))
    else:
        print("  *** nothing running ***")
    if durations and done < total:
        mean = sum(durations) / len(durations)
        remaining = total - done - len(live)
        slots = max(len(live), 1)
        eta = mean * remaining / slots
        print(
            f"  mean {mean / 60:.0f} min per rung  ->  about {eta / 3600:.1f} h left at {slots} at a time"
        )


def _started(log):
    """Wall-clock start recorded in the log header, or its creation time."""
    try:
        line = log.read_text().splitlines()[1]
        return time.mktime(
            time.strptime(line.replace("# started ", "").strip(), "%Y-%m-%d %H:%M:%S")
        )
    except Exception:
        return log.stat().st_ctime


def R_read(path):
    import optimisation_runs as R

    return R.read_run(path)


def main(argv):
    if "--status" in argv:
        return status()
    if "--only" in argv:
        return run_case(argv[argv.index("--only") + 1])
    if "--only-rung" in argv:
        index = argv.index("--only-rung")
        return run_rung(argv[index + 1], argv[index + 2], argv[index + 3])
    if "--reference" in argv:
        index = argv.index("--reference")
        return run_case_reference(argv[index + 1], argv[index + 2])

    jobs = 3
    if "--jobs" in argv:
        index = argv.index("--jobs")
        jobs = int(argv[index + 1])
        argv = argv[:index] + argv[index + 2 :]
    seed_dir = None
    if "--seed" in argv:
        index = argv.index("--seed")
        seed_dir = argv[index + 1]
        argv = argv[:index] + argv[index + 2 :]

    wanted = [a for a in argv if not a.startswith("-")] or CASES
    if seed_dir:
        # Resolve before spawning: the children chdir to PAPER, so a relative seed path
        # would be read against the wrong directory.
        drive_seeded(wanted, jobs=jobs, seed_dir=Path(seed_dir).resolve())
    else:
        drive(wanted, jobs=jobs)


if __name__ == "__main__":
    main(sys.argv[1:])

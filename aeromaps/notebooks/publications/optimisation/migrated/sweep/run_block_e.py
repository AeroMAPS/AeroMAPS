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

import pandas as pd

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


def status():
    rows = []
    for case in CASES:
        done = sum(
            (RESULTS_E / f"opt_{case}_{t}.json").exists()
            for t in [f"{b:.1f}".replace(".", "_") for b in BUDGETS]
        )
        mincarb = (RESULTS_E / f"opt_{case}_mincarb.json").exists()
        rows.append({"case": case, "budgets_done": f"{done}/{len(BUDGETS)}", "mincarb": mincarb})
    frame = pd.DataFrame(rows)
    print(frame.to_string(index=False))
    total = sum(int(r["budgets_done"].split("/")[0]) for r in rows) + sum(
        r["mincarb"] for r in rows
    )
    print(f"\n  {total}/{len(CASES) * (len(BUDGETS) + 1)} runs on disk")


def main(argv):
    if "--status" in argv:
        return status()
    if "--only" in argv:
        return run_case(argv[argv.index("--only") + 1])
    jobs = 3
    if "--jobs" in argv:
        index = argv.index("--jobs")
        jobs = int(argv[index + 1])
        argv = argv[:index] + argv[index + 2 :]
    wanted = [a for a in argv if not a.startswith("-")] or CASES
    drive(wanted, jobs=jobs)


if __name__ == "__main__":
    main(sys.argv[1:])

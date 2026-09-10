"""Where the overnight batch has got to, as one screen.

Reads ``results/`` and ``summary.csv`` rather than any log, so it reports a batch
started from any shell -- or from a notebook whose output went to a cell.

Usage:  poetry run python status.py        # once
        watch -n 30 poetry run python status.py
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from run_batch import LOGS, RESULTS, RUNS, SUMMARY  # noqa: E402


def _running():
    """Run ids with a live ``--only`` subprocess."""
    try:
        # -fl, not GNU's -af: BSD pgrep on macOS has no -a.
        out = subprocess.run(
            ["pgrep", "-fl", "run_batch.py"], capture_output=True, text=True
        ).stdout
    except FileNotFoundError:
        return set()
    live = set()
    for line in out.splitlines():
        if "--only" in line:
            live.add(line.rsplit("--only", 1)[1].strip())
    return live


def _age(seconds):
    if seconds < 90:
        return f"{seconds:.0f}s"
    if seconds < 5400:
        return f"{seconds / 60:.0f}m"
    return f"{seconds / 3600:.1f}h"


def main():
    summary = pd.read_csv(SUMMARY).set_index("run") if SUMMARY.exists() else pd.DataFrame()
    live, now = _running(), time.time()

    print(f"=== overnight sweep, blocks A-D  ({time.strftime('%H:%M:%S')}) ===\n")
    done = failed = 0
    elapsed_total = 0.0

    for run_id, spec in RUNS.items():
        log = LOGS / f"{run_id}.log"
        if run_id in summary.index:
            row = summary.loc[run_id]
            ok = bool(row.feasible)
            done += 1
            failed += not ok
            elapsed_total += float(row.seconds)
            state = "done  " if ok else "INFEAS"
            detail = (
                f"f={row.f_opt:9.5f}  {row.n_evaluations:>3} evals  "
                f"{_age(float(row.seconds)):>5}  viol {row.max_constraint_violation:.1e}"
            )
        elif run_id in live:
            state = "RUN   "
            started = log.stat().st_mtime if log.exists() else now
            # The log is appended to as the run talks, so its mtime is the last sign of
            # life rather than the start; the header line carries the start time.
            first = log.read_text().splitlines()[1] if log.exists() else ""
            begun = first.replace("# started ", "")
            detail = f"since {begun[-8:]}  last output {_age(now - started)} ago"
        elif (RESULTS / f"{run_id}.json").exists():
            state = "done  "
            done += 1
            detail = "on disk (no summary row -- rerun to refresh)"
        elif log.exists():
            state = "FAILED"
            failed += 1
            detail = f"see logs/{run_id}.log"
        else:
            state = "queued"
            detail = ""
        print(f"  [{state}] {run_id:14s} {spec['block']:8s} {detail}")

    total = len(RUNS)
    print(f"\n  {done}/{total} finished" + (f", {failed} not feasible" if failed else ""))
    if done:
        mean = elapsed_total / max(done - failed, 1)
        remaining = total - done - len(live)
        print(
            f"  mean {_age(mean)} per run  ->  about {_age(mean * remaining)} left after the current one"
        )
    if not live and done < total:
        print("\n  *** nothing running *** -- relaunch with: poetry run python run_batch.py")


if __name__ == "__main__":
    main()

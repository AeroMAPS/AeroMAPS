"""Re-run a sweep with convergence settings chosen for multiplier quality.

The published sweep sets ``ftol_abs=0.001``. GEMSEO's default is ``1e-9``, so
that is a million times looser, and it is why 19 of the 44 feasible runs stop on
``ftol_abs`` with a relative KKT residual between 1e-2 and 0.11: SLSQP halts
when the objective stops moving, which happens well before stationarity on the
flat, loose-budget end of the ladder. A multiplier is a solution of the
stationarity condition, so a run that never reached stationarity cannot have
good multipliers however well its objective converged.

Two changes, both to the solver only - the optimisation problem, the scenario
and every model input are untouched:

* ``ftol_abs`` / ``ftol_rel`` tightened, so objective stagnation stops being the
  binding criterion;
* ``kkt_tol_rel`` enabled. GEMSEO leaves it at ``inf``; setting it makes SLSQP
  stop on the *KKT residual*, which is precisely the quantity that governs
  multiplier quality, rather than on a proxy for it.

GEMSEO's execution statistics are disabled first. ``ExecutionStatistics`` takes a
shared-memory ``multiprocessing.Value`` per discipline, and macOS allows only
``kern.sysv.shmmni=32`` segments system-wide (``shmseg=8`` per process). One
sweep fits; five in parallel, at 106 disciplines each, exhaust the pool, and
POSIX reports that exhaustion as ``ENOSPC`` - "No space left on device", with
half a terabyte free. ``disable_gemseo_execution_statistics`` swaps the shared
memory for plain attributes, which is what makes the five cases run at once.

Results go to ``results_tight/`` so the published histories in ``results/`` are
never overwritten and the two can be compared.

Usage:  poetry run python rerun_tight.py <case>
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

from gemseo.algos.opt.scipy_local.settings.slsqp import SLSQP_Settings


# optimisation_runs.py lives one level up, beside the notebooks.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import optimisation_runs as R
from aeromaps.core.gemseo import disable_gemseo_execution_statistics

OUTPUT_DIR = Path(__file__).resolve().parent / "results_tight"

FTOL = 1e-8
KKT_TOL_REL = 1e-6
MAX_ITER = 200


def _tighten(process, *args, **kwargs):
    """Call the published setup, then replace only the solver settings."""
    result = _ORIGINAL_SETUP(process, *args, **kwargs)
    process.gemseo_settings["algorithm"] = SLSQP_Settings(
        max_iter=kwargs.get("max_iter", MAX_ITER),
        enable_progress_bar=True,
        ftol_abs=FTOL,
        ftol_rel=FTOL,
        kkt_tol_rel=KKT_TOL_REL,
        normalize_design_space=False,
    )
    return result


_ORIGINAL_SETUP = R.setup_optimisation


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    # Must run before any discipline is built: see the module docstring.
    disable_gemseo_execution_statistics()
    case = sys.argv[1] if len(sys.argv) > 1 else "main"

    R.setup_optimisation = _tighten
    R.RESULTS_DIR = OUTPUT_DIR
    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"case={case}  ftol={FTOL}  kkt_tol_rel={KKT_TOL_REL}  max_iter={MAX_ITER}", flush=True)
    summary = R.run_sweep(case, max_iter=MAX_ITER)
    print(summary.to_string(index=False), flush=True)

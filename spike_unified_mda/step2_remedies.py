"""Do the Step-1 remedies also rescue the REAL chain past its Gauss-Seidel limit?

Measured on the stock chain. An earlier version of this script monkey-patched the NaN
sentinel to make the residual meaningful; that was a diagnostic for the residual floor,
whose real cause -- a discipline mutating its own coupling input -- is now fixed in
AeroMAPS, so the workaround is gone and these numbers are the real chain's.
"""

import logging
import os
import sys
import warnings

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)

from gemseo.algos.sequence_transformer.acceleration import AccelerationMethod  # noqa: E402

from aeromaps.core.gemseo import (  # noqa: E402
    _couplings_with_spread_nans,
    check_mda_convergence,
)
from aeromaps.core.multi_regional_process import MultiRegionalProcess  # noqa: E402
from spike_unified_mda.mda_settings import rebuild  # noqa: E402

CONFIG = "spike_unified_mda/scenario/regionalisation_spike.yaml"

NONE = AccelerationMethod.NONE

VARIANTS = [
    ("GS baseline", {"acceleration_method": NONE}),
    ("GS relax=0.7", {"over_relaxation_factor": 0.7, "acceleration_method": NONE}),
    ("GS relax=0.4", {"over_relaxation_factor": 0.4, "acceleration_method": NONE}),
    ("GS + Alternate2Delta", {"acceleration_method": "Alternate2Delta"}),
    ("MDAJacobi (GEMSEO default)", {"inner_mda_name": "MDAJacobi", "acceleration_method": NONE}),
]

HARD_CASES = [(0.3, 8.0), (0.3, 16.0), (3.0, 8.0)]

if os.environ.get("SPIKE_EXTRA_CASES"):
    HARD_CASES += [(0.3, 32.0), (0.3, 64.0), (3.0, 16.0), (10.0, 8.0), (30.0, 4.0)]

if __name__ == "__main__":
    print(
        f"{'stiffness':>10} {'gamma':>6} {'variant':>28} {'status':>11} {'iters':>6} {'residual':>11}"
    )
    print("-" * 80)
    for s, g in HARD_CASES:
        print()
        for label, extra in VARIANTS:
            os.environ["SPIKE_STIFFNESS"] = str(s)
            os.environ["SPIKE_GAMMA"] = str(g)
            try:
                p = MultiRegionalProcess(CONFIG)
                p.on_mda_failure = "warn"
                rebuild(p, **extra)
                p.compute()
                m = p.mda_chain.inner_mdas[0]
                h = list(m.residual_history)
                # A residual under the tolerance is not proof of a solution: NaN
                # couplings difference against themselves to zero.
                if check_mda_convergence(p.mda_chain, on_failure="ignore"):
                    status = "NaN" if _couplings_with_spread_nans(m) else "NOT conv"
                else:
                    status = "converged"
                print(f"{s:>10} {g:>6} {label:>28} {status:>11} {len(h):>6} {h[-1]:>11.2e}")
            except Exception as exc:  # noqa: BLE001
                print(
                    f"{s:>10} {g:>6} {label:>28} {'ERROR':>11}  {type(exc).__name__}: {str(exc)[:60]}"
                )
            sys.stdout.flush()

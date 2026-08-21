"""Do the Step-1 remedies also rescue the REAL chain past its Gauss-Seidel limit?"""

import logging
import os
import sys
import warnings

import pandas as pd

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)

from aeromaps.core.gemseo import CustomDataConverter  # noqa: E402

_orig = CustomDataConverter.convert_value_to_array


def _patched(self, name, value):
    if isinstance(value, pd.Series):
        value = value.fillna(0.0)
    return _orig(self, name, value)


CustomDataConverter.convert_value_to_array = _patched

from aeromaps.core.multi_regional_process import MultiRegionalProcess  # noqa: E402
from spike_unified_mda.mda_settings import rebuild  # noqa: E402

CONFIG = "spike_unified_mda/scenario/regionalisation_spike.yaml"

VARIANTS = [
    ("GS baseline", {}),
    ("GS relax=0.7", {"over_relaxation_factor": 0.7}),
    ("GS relax=0.4", {"over_relaxation_factor": 0.4}),
    ("GS + Alternate2Delta", {"acceleration_method": "Alternate2Delta"}),
    ("MDAJacobi (GEMSEO default)", {"inner_mda_name": "MDAJacobi"}),
]

HARD_CASES = [(0.3, 8.0), (0.3, 16.0), (3.0, 8.0)]

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
                rebuild(p, **extra)
                p.compute()
                m = p.mda_chain.inner_mdas[0]
                h = list(m.residual_history)
                ok = h[-1] <= m.settings.tolerance
                print(
                    f"{s:>10} {g:>6} {label:>28} {('converged' if ok else 'NOT conv'):>11} "
                    f"{len(h):>6} {h[-1]:>11.2e}"
                )
            except Exception as exc:  # noqa: BLE001
                print(
                    f"{s:>10} {g:>6} {label:>28} {'ERROR':>11}  {type(exc).__name__}: {str(exc)[:60]}"
                )
            sys.stdout.flush()

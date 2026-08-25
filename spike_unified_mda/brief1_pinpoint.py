"""Brief 1, question 1: pin the exact operand that turns finite inputs into NaN.

Wraps ``RPKElasticity.compute`` and, the first time its output multiplier goes
non-finite while every input was finite, dumps the operands of the one power
operation in that method:

    multiplier = (airfare_per_rpk / initial_airfare_per_rpk) ** price_elasticity
"""

import logging
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)

CONFIG = "spike_unified_mda/scenario/regionalisation_spike.yaml"
PROJ = 2025

STIFFNESS = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3
GAMMA = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0

os.environ["SPIKE_STIFFNESS"] = str(STIFFNESS)
os.environ["SPIKE_GAMMA"] = str(GAMMA)

from aeromaps.models.air_transport.air_traffic.rpk_market import RPKElasticity  # noqa: E402
from aeromaps.core.multi_regional_process import MultiRegionalProcess  # noqa: E402
from spike_unified_mda.mda_settings import rebuild  # noqa: E402

_original = RPKElasticity.compute
STATE = {"run": 0, "dumped": False, "history": []}


def probed(self, input_data):
    STATE["run"] += 1
    airfare = input_data["airfare_per_rpk"]
    init = float(input_data["initial_airfare_per_rpk"])
    elasticity = float(input_data["price_elasticity"])

    proj = airfare.loc[airfare.index >= PROJ]
    arr = proj.to_numpy(dtype=float)
    STATE["history"].append(
        {
            "run": STATE["run"],
            "model": self.name,
            "airfare_min": float(np.nanmin(arr)),
            "airfare_max": float(np.nanmax(arr)),
            "n_negative": int((arr < 0).sum()),
            "n_zero": int((arr == 0).sum()),
            "n_nonfinite": int((~np.isfinite(arr)).sum()),
        }
    )

    out = _original(self, input_data)

    mult = out["elasticity_factor"]
    mproj = mult.loc[mult.index >= PROJ].to_numpy(dtype=float)
    inputs_finite = np.isfinite(arr).all() and np.isfinite(init) and np.isfinite(elasticity)

    if (not np.isfinite(mproj).all()) and inputs_finite and not STATE["dumped"]:
        STATE["dumped"] = True
        bad = ~np.isfinite(mproj)
        years = mult.loc[mult.index >= PROJ].index.to_numpy()
        ratio = arr / init
        print("\n" + "=" * 78)
        print(f"FIRST MANUFACTURE  -- {self.name}, compute() call #{STATE['run']}")
        print("=" * 78)
        print(f"  initial_airfare_per_rpk = {init!r}   (finite: {np.isfinite(init)})")
        print(f"  price_elasticity        = {elasticity!r}")
        print(f"  airfare_per_rpk  min={np.nanmin(arr):.6g}  max={np.nanmax(arr):.6g}")
        print(f"  airfare_per_rpk  all finite: {np.isfinite(arr).all()}")
        print(f"  airfare_per_rpk  negative in {int((arr < 0).sum())} projection years")
        print(f"  airfare_per_rpk  exactly zero in {int((arr == 0).sum())} projection years")
        print(f"\n  NaN multiplier in {int(bad.sum())} years, first {years[bad][0]}")
        print(f"\n  {'year':>6} {'airfare':>16} {'ratio':>16} {'ratio**elast':>16}")
        for y, a, r, m in zip(years[bad][:12], arr[bad][:12], ratio[bad][:12], mproj[bad][:12]):
            print(f"  {y:>6} {a:>16.6g} {r:>16.6g} {m:>16.6g}")
        print("\n  reproduction of the exact operation, in isolation:")
        r0 = float(ratio[bad][0])
        print(f"    ({r0!r}) ** ({elasticity!r}) = {r0 ** elasticity!r}")
        print(f"    numpy: np.float64({r0!r}) ** {elasticity!r} = {np.float64(r0) ** elasticity!r}")
        print("=" * 78 + "\n")
    return out


RPKElasticity.compute = probed

p = MultiRegionalProcess(CONFIG)
p.on_mda_failure = "warn"
rebuild(p)  # DEFAULTS -> Alternate2Delta acceleration
p.compute()

hist = pd.DataFrame(STATE["history"])
hist.to_csv("spike_unified_mda/brief1_out/airfare_history.csv", index=False)
sub = hist[hist["model"].str.startswith("region_A")].reset_index(drop=True)
print("region_A airfare_per_rpk seen by RPKElasticity, per MDA iteration:")
print(f"{'k':>4} {'min':>14} {'max':>14} {'<0':>4} {'==0':>4} {'nonfin':>7}")
for i, row in sub.iterrows():
    print(
        f"{i + 1:>4} {row['airfare_min']:>14.6g} {row['airfare_max']:>14.6g} "
        f"{int(row['n_negative']):>4} {int(row['n_zero']):>4} {int(row['n_nonfinite']):>7}"
    )

"""Brief 1: with the price bound in place, WHAT still manufactures a NaN?

The bounded 0.3/16 run still goes non-finite. This re-runs it with both the price
bound and the finite -> non-finite origin probe active, so the remaining source(s)
are named. That is the list of "totality fixes" the brief asks to cost.
"""

import logging
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)

STIFFNESS = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3
GAMMA = float(sys.argv[2]) if len(sys.argv) > 2 else 16.0
LOW, HIGH = 0.1, 20.0
PROJ = 2025
CONFIG = "spike_unified_mda/scenario/regionalisation_spike.yaml"

from spike_unified_mda.brief1_probe import install_origin_probe  # noqa: E402

probe = install_origin_probe()

os.environ["SPIKE_STIFFNESS"] = str(STIFFNESS)
os.environ["SPIKE_GAMMA"] = str(GAMMA)

from aeromaps.core.multi_regional_process import MultiRegionalProcess  # noqa: E402
from gemseo.algos.sequence_transformer.acceleration import AccelerationMethod  # noqa: E402
from spike_unified_mda.mda_settings import rebuild  # noqa: E402

p = MultiRegionalProcess(CONFIG)
p.on_mda_failure = "warn"
rebuild(p, acceleration_method=AccelerationMethod.ALTERNATE_2_DELTA)

# Clip the price where the carbon-tax discipline reads it.
for disc in p.disciplines:
    model = getattr(disc, "model", None)
    if model is not None and type(model).__name__ == "SpikeMarketCarbonTax":
        original = model.compute

        def tax_compute(input_data, _o=original):
            price = input_data["spike_fuel_price"]
            idx = price.index >= PROJ
            arr = price.loc[idx].to_numpy(dtype=float)
            low, high = LOW * 150.0, HIGH * 150.0
            clipped = np.clip(np.nan_to_num(arr, nan=high, posinf=high, neginf=low), low, high)
            price = price.copy()
            price.loc[idx] = clipped
            data = dict(input_data)
            data["spike_fuel_price"] = price
            return _o(data)

        model.compute = tax_compute

p.compute()

events = sorted(probe.events, key=lambda e: e["run_index"])
manufactured = [e for e in events if e["manufactured"]]

print(f"\n=== BOUNDED price, stiffness={STIFFNESS} gamma={GAMMA}, Alternate2Delta ===")
m = p.mda_chain.inner_mdas[0]
print(f"{len(m.residual_history)} iterations, residual {list(m.residual_history)[-1]:.3e}")
print(f"transitions: {len(events)}   manufactured: {len(manufactured)}\n")

print("--- MANUFACTURED, grouped by discipline ---")
if manufactured:
    df = pd.DataFrame(manufactured)
    grp = (
        df.groupby("discipline")
        .agg(
            n_vars=("variable", "nunique"), first_run=("run_index", "min"), kinds=("kind", "unique")
        )
        .sort_values("first_run")
    )
    print(grp.to_string())
    print("\n--- earliest 12 ---")
    for e in manufactured[:12]:
        print(
            f"  run {e['run_index']:>5}  {e['discipline']}.{e['variable']}  "
            f"[{e['kind']}]  from year {e['first_year']}"
        )
else:
    print("none -- the bounded run manufactured no NaN at all.")

if events:
    pd.DataFrame(events).to_csv(
        f"spike_unified_mda/brief1_out/bounded_origin_s{STIFFNESS}_g{GAMMA}.csv", index=False
    )

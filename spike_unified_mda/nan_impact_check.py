"""Does neutralising the NaN sentinel change the RESULTS, or only the residual?

nan_floor_probe.py showed the same four headline numbers either way. That is not
evidence of equivalence: replacing fillna(-999999) with fillna(0.0) also disables
the round-trip that restores NaN in convert_array_to_value, so every NaN coupling
value becomes a permanent 0. This compares ALL output columns.

Run twice, once per mode, and diff the two dumps:
    python -m spike_unified_mda.nan_impact_check stock
    python -m spike_unified_mda.nan_impact_check neutralised
    python -m spike_unified_mda.nan_impact_check compare
"""

import logging
import pickle
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)

MODE = sys.argv[1] if len(sys.argv) > 1 else "stock"
DUMP = "/private/tmp/claude-1489595312/-Users-a-salgas-PycharmProjects-AeroMAPS/86a1383b-c9c0-4b10-9c2d-264b5e5ddd65/scratchpad/nan_impact_{}.pkl"


def compare():
    a = pd.read_pickle(DUMP.format("stock"))
    b = pd.read_pickle(DUMP.format("neutralised"))
    print(f"stock       : {a.shape}")
    print(f"neutralised : {b.shape}")
    only_a = sorted(set(a.columns) - set(b.columns))
    only_b = sorted(set(b.columns) - set(a.columns))
    if only_a:
        print(f"columns only in stock      : {len(only_a)} e.g. {only_a[:5]}")
    if only_b:
        print(f"columns only in neutralised: {len(only_b)} e.g. {only_b[:5]}")

    common = [c for c in a.columns if c in set(b.columns)]
    identical, nan_only, differing = [], [], []
    for c in common:
        x = a[c].to_numpy(dtype=float)
        y = b[c].to_numpy(dtype=float)
        if np.array_equal(x, y, equal_nan=True):
            identical.append(c)
            continue
        # difference confined to positions where stock is NaN and neutralised is 0?
        mask = np.isnan(x) & (y == 0.0)
        rest_equal = np.array_equal(np.where(mask, 0.0, x), np.where(mask, 0.0, y), equal_nan=True)
        if rest_equal and mask.any():
            nan_only.append(c)
        else:
            with np.errstate(invalid="ignore", divide="ignore"):
                scale = np.maximum(np.abs(x), np.abs(y))
                rel = np.abs(x - y) / np.where(scale > 0, scale, np.nan)
                r = np.nanmax(rel) if np.isfinite(rel).any() else 0.0
            differing.append((float(r) if np.isfinite(r) else np.inf, c))

    differing.sort(reverse=True)
    print(f"\ncolumns compared            : {len(common)}")
    print(f"  bit-identical             : {len(identical)}")
    print(f"  differ only NaN -> 0      : {len(nan_only)}")
    print(f"  genuinely differing       : {len(differing)}")
    if differing:
        rels = [r for r, _ in differing]
        buckets = [
            ("rel > 1e-2  (material)", sum(1 for r in rels if r > 1e-2)),
            ("1e-4 < rel <= 1e-2", sum(1 for r in rels if 1e-4 < r <= 1e-2)),
            ("1e-6 < rel <= 1e-4", sum(1 for r in rels if 1e-6 < r <= 1e-4)),
            ("1e-9 < rel <= 1e-6", sum(1 for r in rels if 1e-9 < r <= 1e-6)),
            ("rel <= 1e-9 (noise)", sum(1 for r in rels if r <= 1e-9)),
        ]
        print("\n  distribution of MAX RELATIVE difference:")
        for label, n in buckets:
            print(f"      {label:<28} {n:>5}")
        print("\n  worst 15 by relative difference:")
        for r, c in differing[:15]:
            print(f"      {r:>12.4e}  {c}")
    if nan_only[:6]:
        print(f"\n  NaN->0 columns, sample    : {nan_only[:6]}")


if MODE == "compare":
    compare()
    sys.exit(0)

if MODE == "neutralised":
    from aeromaps.core.gemseo import CustomDataConverter

    _orig = CustomDataConverter.convert_value_to_array

    def _patched(self, name, value):
        if isinstance(value, pd.Series):
            value = value.fillna(0.0)
        return _orig(self, name, value)

    CustomDataConverter.convert_value_to_array = _patched

from aeromaps.core.multi_regional_process import MultiRegionalProcess  # noqa: E402
from spike_unified_mda.mda_settings import tune  # noqa: E402

p = MultiRegionalProcess("spike_unified_mda/scenario/regionalisation_spike.yaml")
tune(p)
p.compute()
vo = p.data["vector_outputs"]
with open(DUMP.format(MODE), "wb") as fh:
    pickle.dump(vo, fh)
m = p.mda_chain.inner_mdas[0]
h = list(m.residual_history)
print(f"{MODE}: {vo.shape}, {len(h)} iterations, residual {h[-1]:.3e}")

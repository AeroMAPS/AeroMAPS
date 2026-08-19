"""Criteria 1-4 on the REAL AeroMAPS chain (Step 2 scenario).

Run with:
  python -m spike_unified_mda.step2_criteria 1234        # criteria to run
  python -m spike_unified_mda.step2_criteria 4 --neutralise
The --neutralise flag applies the NaN-sentinel diagnostic from nan_floor_probe
so that residual-based convergence is actually meaningful on the real chain.
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

if "--neutralise" in sys.argv:
    from aeromaps.core.gemseo import CustomDataConverter

    _orig = CustomDataConverter.convert_value_to_array

    def _patched(self, name, value):
        if isinstance(value, pd.Series):
            value = value.fillna(0.0)
        return _orig(self, name, value)

    CustomDataConverter.convert_value_to_array = _patched

from aeromaps.core.multi_regional_process import MultiRegionalProcess  # noqa: E402


def make_process(stiffness=None, gamma=None, mda=None):
    if stiffness is not None:
        os.environ["SPIKE_STIFFNESS"] = str(stiffness)
    if gamma is not None:
        os.environ["SPIKE_GAMMA"] = str(gamma)
    p = MultiRegionalProcess(CONFIG)
    if mda:
        # Rebuild the chain with different solver settings.
        p._regionalisation_config["mda"] = {**p._regionalisation_config.get("mda", {}), **mda}
        p._setup_unified_mda()
    return p


def mda_stats(p):
    m = p.mda_chain.inner_mdas[0]
    h = list(m.residual_history)
    return {
        "n_coupled": len(m.disciplines),
        "iterations": len(h),
        "residual": float(h[-1]),
        "tolerance": float(m.settings.tolerance),
        "converged": float(h[-1]) <= float(m.settings.tolerance),
    }


def criterion_1():
    p = make_process()
    cs = p.mda_chain.coupling_structure
    scc = [d.name for d in cs.strongly_coupled_disciplines]
    strong = sorted(cs.strong_couplings)
    print(f"disciplines in chain           : {len(p.disciplines)}")
    print(f"strongly connected component   : {len(scc)} disciplines")
    print(f"SpikeFuelMarket in the SCC     : {'SpikeFuelMarket' in scc}")
    print(f"spike disciplines in the SCC   : {[n for n in scc if 'Spike' in n]}")
    print(f"RPKElasticity in the same SCC  : {[n for n in scc if 'Elasticity' in n]}")
    print(f"spike strong couplings         : {[c for c in strong if 'spike' in c]}")
    print(
        f"airfare/rpk strong couplings   : "
        f"{[c for c in strong if c.split(':')[-1] in ('rpk', 'airfare_per_rpk')]}"
    )
    return p


def criterion_2(p=None):
    p = p or make_process()
    p.compute()
    s = mda_stats(p)
    print("nominal case (stiffness=0.3, gamma=1, price_elasticity=-0.9):")
    print(
        f"  {s['n_coupled']} coupled disciplines, {s['iterations']} Gauss-Seidel iterations, "
        f"residual {s['residual']:.3e}, tolerance {s['tolerance']:.0e} -> "
        f"{'CONVERGED' if s['converged'] else 'NOT CONVERGED'}"
    )
    return p


def criterion_3():
    """Two compute() on identical inputs -> bit-identical outputs?"""
    p1 = make_process()
    p1.compute()
    a = p1.data["vector_outputs"].copy()

    # Same process object, second compute().
    p1.compute()
    b = p1.data["vector_outputs"].copy()

    print(f"first compute()  : vector_outputs shape {a.shape}")
    print(f"second compute() : vector_outputs shape {b.shape}")
    dup = b.columns[b.columns.duplicated()]
    print(f"duplicated columns after 2nd compute(): {len(dup)}")

    common = [c for c in a.columns if c in set(b.columns)]
    b_dedup = b.loc[:, ~b.columns.duplicated(keep="last")]
    diffs = {}
    for c in common:
        x, y = a[c].to_numpy(dtype=float), b_dedup[c].to_numpy(dtype=float)
        if not np.array_equal(x, y, equal_nan=True):
            diffs[c] = float(np.nanmax(np.abs(x - y)))
    print(f"columns compared : {len(common)}")
    print(
        f"bit-identical    : {len(diffs) == 0}"
        + (
            f"  (worst |delta| = {max(diffs.values()):.3e} on {len(diffs)} columns)"
            if diffs
            else ""
        )
    )

    # Fresh cold process.
    p2 = make_process()
    p2.compute()
    c = p2.data["vector_outputs"]
    common2 = [col for col in a.columns if col in set(c.columns)]
    diffs2 = {}
    for col in common2:
        x, y = a[col].to_numpy(dtype=float), c[col].to_numpy(dtype=float)
        if not np.array_equal(x, y, equal_nan=True):
            diffs2[col] = float(np.nanmax(np.abs(x - y)))
    print(
        f"fresh process vs first run: bit-identical = {len(diffs2) == 0}"
        + (f"  (worst |delta| = {max(diffs2.values()):.3e})" if diffs2 else "")
    )


def criterion_4(mda=None, label=""):
    print(f"\n--- sweep {label} ---")
    print(
        f"{'stiffness':>10} {'gamma':>7} {'status':>14} {'iters':>6} {'residual':>11} "
        f"{'price_2050':>11} {'overall_rpk_2050':>17}"
    )
    cases = [
        (0.3, 1.0),
        (1.0, 1.0),
        (3.0, 1.0),
        (10.0, 1.0),
        (30.0, 1.0),
        (0.3, 2.0),
        (0.3, 4.0),
        (0.3, 8.0),
        (0.3, 16.0),
        (3.0, 2.0),
        (3.0, 4.0),
        (3.0, 8.0),
    ]
    for s, g in cases:
        try:
            p = make_process(stiffness=s, gamma=g, mda=mda)
            p.compute()
            st = mda_stats(p)
            vo = p.data["vector_outputs"]
            price = vo["region_A:spike_fuel_price"].loc[2050]
            rpk = vo["overall:rpk"].loc[2050]
            print(
                f"{s:>10} {g:>7} {('converged' if st['converged'] else 'NOT conv'):>14} "
                f"{st['iterations']:>6} {st['residual']:>11.2e} {price:>11.4f} {rpk:>17.6e}"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"{s:>10} {g:>7} {'ERROR':>14}  {type(exc).__name__}: {str(exc)[:70]}")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].isdigit() else "1234"
    print(
        f"=== Step 2 criteria ({'NaN sentinel neutralised' if '--neutralise' in sys.argv else 'stock AeroMAPS'}) ===\n"
    )
    proc = None
    if "1" in which:
        print("### Criterion 1 - assembly and coupling graph")
        proc = criterion_1()
        print()
    if "2" in which:
        print("### Criterion 2 - convergence")
        criterion_2(proc)
        print()
    if "3" in which:
        print("### Criterion 3 - idempotence")
        criterion_3()
        print()
    if "4" in which:
        print("### Criterion 4 - robustness margin")
        criterion_4(label="plain MDAGaussSeidel")

"""Brief 1: does the elasticity boundary survive the domain-exit diagnosis?

Sweeps |price_elasticity| at the NOMINAL supply curve (stiffness=0.3, gamma=1) and
records, for each value: convergence, whether the trajectory stayed finite, and
whether the iterates settled or locked onto a limit cycle.

The elasticity is overridden on the RPKElasticity discipline's input, which is the
only place it enters the airfare -> RPK loop.
"""

import argparse
import logging
import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)

CONFIG = "spike_unified_mda/scenario/regionalisation_spike.yaml"
PROJ, YEAR = 2025, 2050


def detect_cycle(values, tol=1e-6, max_period=12):
    """Smallest period p such that the tail repeats to within tol, else None."""
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if len(v) < 30:
        return None
    tail = v[-24:]
    for p in range(1, max_period + 1):
        a, b = tail[-2 * p : -p], tail[-p:]
        if len(a) < p:
            continue
        denom = np.maximum(np.abs(b), 1e-12)
        if np.max(np.abs(a - b) / denom) < tol:
            return p
    return None


def run(elasticity, stiffness, gamma, accel, max_iter):
    os.environ["SPIKE_STIFFNESS"] = str(stiffness)
    os.environ["SPIKE_GAMMA"] = str(gamma)
    from aeromaps.core.multi_regional_process import MultiRegionalProcess
    from gemseo.algos.sequence_transformer.acceleration import AccelerationMethod
    from spike_unified_mda.mda_settings import rebuild

    p = MultiRegionalProcess(CONFIG)
    p.on_mda_failure = "warn"
    rebuild(
        p,
        max_mda_iter=max_iter,
        acceleration_method=AccelerationMethod.ALTERNATE_2_DELTA
        if accel
        else AccelerationMethod.NONE,
    )

    prices, nan_seen = [], {"n": 0}
    for disc in p.disciplines:
        model = getattr(disc, "model", None)
        if model is None:
            continue
        cls = type(model).__name__
        if cls == "RPKElasticity":
            original = model.compute

            def rpk_compute(input_data, _o=original):
                data = dict(input_data)
                data["price_elasticity"] = -abs(elasticity)
                out = _o(data)
                m = out["elasticity_factor"]
                arr = m.loc[m.index >= PROJ].to_numpy(dtype=float)
                if not np.isfinite(arr).all():
                    nan_seen["n"] += 1
                return out

            model.compute = rpk_compute
        elif cls == "SpikeFuelMarket":
            original = model.compute

            def market_compute(input_data, _o=original, _m=model):
                out = _o(input_data)
                prices.append(float(out[f"{_m.regions[0]}:spike_fuel_price"].loc[YEAR]))
                return out

            model.compute = market_compute

    p.compute()
    m = p.mda_chain.inner_mdas[0]
    hist = list(m.residual_history)
    vo = p.data["vector_outputs"]
    finite_prices = [x for x in prices if np.isfinite(x)]
    return {
        "elasticity": elasticity,
        "iterations": len(hist),
        "residual": float(hist[-1]),
        "converged": float(hist[-1]) <= 1e-10,
        "nan_multiplier_calls": nan_seen["n"],
        "price_2050": float(vo["region_A:spike_fuel_price"].loc[YEAR]),
        "rpk_2050": float(vo["overall:rpk"].loc[YEAR]),
        "p_min": min(finite_prices) if finite_prices else np.nan,
        "p_max": max(finite_prices) if finite_prices else np.nan,
        "n_nonfinite_p": sum(1 for x in prices if not np.isfinite(x)),
        "cycle_period": detect_cycle(prices),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--values", nargs="+", type=float, default=[0.9, 1.5, 1.85, 2.5, 4.0, 6.0])
    ap.add_argument("--stiffness", type=float, default=0.3)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--accel", action="store_true")
    ap.add_argument("--max-iter", type=int, default=200)
    args = ap.parse_args()

    print(
        f"\n=== elasticity sweep, stiffness={args.stiffness} gamma={args.gamma} "
        f"accel={'Alternate2Delta' if args.accel else 'none'} ==="
    )
    hdr = (
        f"{'|elast|':>8} {'status':>10} {'iters':>6} {'residual':>11} {'p_2050':>12} "
        f"{'p_min':>11} {'p_max':>12} {'nonfin p':>9} {'NaN mult':>9} {'cycle':>6}"
    )
    print(hdr)
    print("-" * len(hdr))
    rows = []
    for e in args.values:
        try:
            r = run(e, args.stiffness, args.gamma, args.accel, args.max_iter)
        except Exception as exc:  # noqa: BLE001
            print(f"{e:>8} {'ERROR':>10}  {type(exc).__name__}: {str(exc)[:60]}")
            continue
        rows.append(r)
        print(
            f"{r['elasticity']:>8} {('conv' if r['converged'] else 'NOT conv'):>10} "
            f"{r['iterations']:>6} {r['residual']:>11.2e} {r['price_2050']:>12.5g} "
            f"{r['p_min']:>11.5g} {r['p_max']:>12.5g} {r['n_nonfinite_p']:>9} "
            f"{r['nan_multiplier_calls']:>9} {str(r['cycle_period']):>6}"
        )
    os.makedirs("spike_unified_mda/brief1_out", exist_ok=True)
    pd.DataFrame(rows).to_csv(
        f"spike_unified_mda/brief1_out/elasticity_sweep" f"{'_accel' if args.accel else ''}.csv",
        index=False,
    )


if __name__ == "__main__":
    main()

"""Brief 1: cost the "totality" fix, without touching the cost models.

The brief forbids fixing the models in this session, so the candidate fix is applied
as a probe wrapper on the live discipline instances:

  totality fix T1 -- RPKElasticity: the multiplier becomes DEFINED AND SATURATING for
      any airfare, by clipping the airfare/initial_airfare ratio into [lo, hi] before
      the fractional power. Outside that band the demand response saturates instead of
      returning NaN (ratio < 0) or exploding (ratio -> 0).

  totality fix T2 -- SpikeFuelMarket price: same wide bound on the cleared price.

Reports, for each case and each combination of fixes: convergence, whether any NaN
was manufactured, and whether the clip was ACTIVE at the converged point (if it is
not, the answer is a fixed point of the unmodified problem).
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


def run(stiffness, gamma, t1, t2, lo, hi, max_iter, accel=True):
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

    state = {"nan_mult": 0, "t1_active": [], "t2_active": [], "k": 0, "prices": []}

    for disc in p.disciplines:
        model = getattr(disc, "model", None)
        if model is None:
            continue
        cls = type(model).__name__

        if cls == "RPKElasticity" and t1:
            original = model.compute

            def rpk_compute(input_data, _o=original):
                data = dict(input_data)
                a = data["airfare_per_rpk"]
                init = float(data["initial_airfare_per_rpk"])
                idx = a.index >= PROJ
                arr = a.loc[idx].to_numpy(dtype=float)
                ratio = arr / init
                active = (~np.isfinite(ratio)) | (ratio < lo) | (ratio > hi)
                state["t1_active"].append((state["k"], int(active.sum())))
                fixed = np.clip(np.nan_to_num(ratio, nan=hi, posinf=hi, neginf=lo), lo, hi)
                a = a.copy()
                a.loc[idx] = fixed * init
                data["airfare_per_rpk"] = a
                out = _o(data)
                m = out["elasticity_factor"]
                marr = m.loc[m.index >= PROJ].to_numpy(dtype=float)
                if not np.isfinite(marr).all():
                    state["nan_mult"] += 1
                return out

            model.compute = rpk_compute

        elif cls == "RPKElasticity" and not t1:
            original = model.compute

            def rpk_plain(input_data, _o=original):
                out = _o(input_data)
                m = out["elasticity_factor"]
                marr = m.loc[m.index >= PROJ].to_numpy(dtype=float)
                if not np.isfinite(marr).all():
                    state["nan_mult"] += 1
                return out

            model.compute = rpk_plain

        elif cls == "SpikeMarketCarbonTax" and t2:
            original = model.compute

            def tax_compute(input_data, _o=original):
                price = input_data["spike_fuel_price"]
                idx = price.index >= PROJ
                arr = price.loc[idx].to_numpy(dtype=float)
                low, high = lo * 150.0, hi * 150.0
                active = (~np.isfinite(arr)) | (arr < low) | (arr > high)
                state["t2_active"].append((state["k"], int(active.sum())))
                clipped = np.clip(np.nan_to_num(arr, nan=high, posinf=high, neginf=low), low, high)
                price = price.copy()
                price.loc[idx] = clipped
                data = dict(input_data)
                data["spike_fuel_price"] = price
                return _o(data)

            model.compute = tax_compute

        elif cls == "SpikeFuelMarket":
            original = model.compute

            def market_compute(input_data, _o=original, _m=model):
                state["k"] += 1
                out = _o(input_data)
                state["prices"].append(float(out[f"{_m.regions[0]}:spike_fuel_price"].loc[YEAR]))
                return out

            model.compute = market_compute

    p.compute()
    m = p.mda_chain.inner_mdas[0]
    hist = list(m.residual_history)
    vo = p.data["vector_outputs"]

    def last_active(events):
        act = [k for k, n in events if n > 0]
        return max(act) if act else None

    return {
        "stiffness": stiffness,
        "gamma": gamma,
        "T1": t1,
        "T2": t2,
        "iterations": len(hist),
        "residual": float(hist[-1]),
        "converged": float(hist[-1]) <= 1e-10,
        "nan_multiplier_calls": state["nan_mult"],
        "price_2050": float(vo["region_A:spike_fuel_price"].loc[YEAR]),
        "rpk_2050": float(vo["overall:rpk"].loc[YEAR]),
        "T1_last_active_k": last_active(state["t1_active"]),
        "T2_last_active_k": last_active(state["t2_active"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="+", default=["0.3,8", "0.3,16", "3,8"])
    ap.add_argument("--lo", type=float, default=0.1)
    ap.add_argument("--hi", type=float, default=20.0)
    ap.add_argument("--max-iter", type=int, default=300)
    ap.add_argument("--combos", nargs="+", default=["1,0", "1,1"])
    ap.add_argument("--plain", action="store_true", help="plain Gauss-Seidel, no acceleration")
    args = ap.parse_args()

    hdr = (
        f"{'case':>10} {'T1':>3} {'T2':>3} {'status':>10} {'iters':>6} {'residual':>11} "
        f"{'NaN mult':>9} {'price_2050':>12} {'rpk_2050':>12} {'T1 last':>8} {'T2 last':>8}"
    )
    print(
        f"\n=== totality probe, bound [{args.lo}x, {args.hi}x], "
        f"{'plain GS' if args.plain else 'Alternate2Delta'}, max_iter={args.max_iter} ==="
    )
    print(hdr)
    print("-" * len(hdr))
    rows = []
    for case in args.cases:
        s, g = (float(x) for x in case.split(","))
        for combo in args.combos:
            t1, t2 = (bool(int(x)) for x in combo.split(","))
            try:
                r = run(s, g, t1, t2, args.lo, args.hi, args.max_iter, accel=not args.plain)
            except Exception as exc:  # noqa: BLE001
                print(
                    f"{case:>10} {int(t1):>3} {int(t2):>3} {'ERROR':>10}  "
                    f"{type(exc).__name__}: {str(exc)[:50]}"
                )
                continue
            rows.append(r)
            print(
                f"{case:>10} {int(r['T1']):>3} {int(r['T2']):>3} "
                f"{('conv' if r['converged'] else 'NOT conv'):>10} {r['iterations']:>6} "
                f"{r['residual']:>11.2e} {r['nan_multiplier_calls']:>9} "
                f"{r['price_2050']:>12.6g} {r['rpk_2050']:>12.6g} "
                f"{str(r['T1_last_active_k']):>8} {str(r['T2_last_active_k']):>8}"
            )
    os.makedirs("spike_unified_mda/brief1_out", exist_ok=True)
    pd.DataFrame(rows).to_csv("spike_unified_mda/brief1_out/totality.csv", index=False)


if __name__ == "__main__":
    main()

"""Brief 1, question 2: is the divergence asymptotic or transient?

Instruments the coupling by patching the MODEL INSTANCES of an already-built
process (the spike models are loaded by file path, so patching the class in
`spike_unified_mda.scenario.spike_market_models` would patch a different module
object). For every MDA iteration k it records, per region:

  * ``p_emitted``   -- the price SpikeFuelMarket.compute() actually returned
  * ``p_received``  -- the price SpikeMarketCarbonTax.compute() was handed,
                       i.e. after GEMSEO's sequence transformer (acceleration /
                       relaxation) has had its say
  * saturation against a wide bound, 0.1x .. 20x the fossil reference base_price,
    with iteration index, region and first offending year.

With ``--bound`` the received price is clipped into that bound, so the question
"does the bound bind only at the start, or for ever?" can be answered.
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
PROJ = 2025
YEAR = 2050


def build(stiffness, gamma, accel):
    os.environ["SPIKE_STIFFNESS"] = str(stiffness)
    os.environ["SPIKE_GAMMA"] = str(gamma)
    from aeromaps.core.multi_regional_process import MultiRegionalProcess
    from gemseo.algos.sequence_transformer.acceleration import AccelerationMethod
    from spike_unified_mda.mda_settings import rebuild

    p = MultiRegionalProcess(CONFIG)
    p.on_mda_failure = "warn"
    rebuild(
        p,
        acceleration_method=AccelerationMethod.ALTERNATE_2_DELTA
        if accel
        else AccelerationMethod.NONE,
    )
    return p


def instrument(process, log, bound=None):
    """Patch the live model instances inside the built process."""
    base_price = [None]

    for disc in process.disciplines:
        model = getattr(disc, "model", None)
        if model is None:
            continue
        cls = type(model).__name__

        if cls == "SpikeFuelMarket":
            original = model.compute
            base_price[0] = None

            def market_compute(input_data, _o=original, _m=model):
                out = _o(input_data)
                log["k"] += 1
                base_price[0] = float(_m.config["base_price"])
                for region in _m.regions:
                    price = out[f"{region}:spike_fuel_price"]
                    arr = price.loc[price.index >= PROJ].to_numpy(dtype=float)
                    fin = arr[np.isfinite(arr)]
                    log["emitted"].append(
                        {
                            "k": log["k"],
                            "region": region,
                            "p_2050": float(price.loc[YEAR]),
                            "p_min": float(fin.min()) if fin.size else np.nan,
                            "p_max": float(fin.max()) if fin.size else np.nan,
                            "n_neg": int((arr < 0).sum()),
                            "n_nonfinite": int((~np.isfinite(arr)).sum()),
                        }
                    )
                return out

            model.compute = market_compute

        elif cls == "SpikeMarketCarbonTax":
            original = model.compute

            def tax_compute(input_data, _o=original, _m=model):
                price = input_data["spike_fuel_price"]
                proj_idx = price.index >= PROJ
                arr = price.loc[proj_idx].to_numpy(dtype=float)
                years = price.loc[proj_idx].index.to_numpy()
                fin = arr[np.isfinite(arr)]
                region = getattr(_m, "_probe_region", _m.name)
                log["received"].append(
                    {
                        "k": log["k"],
                        "region": region,
                        "p_2050": float(price.loc[YEAR]),
                        "p_min": float(fin.min()) if fin.size else np.nan,
                        "p_max": float(fin.max()) if fin.size else np.nan,
                        "n_neg": int((arr < 0).sum()),
                        "n_nonfinite": int((~np.isfinite(arr)).sum()),
                    }
                )
                if bound is not None:
                    base = base_price[0] if base_price[0] else 150.0
                    low, high = bound[0] * base, bound[1] * base
                    for side, mask in (
                        ("high", arr > high),
                        ("low", arr < low),
                        ("nonfinite", ~np.isfinite(arr)),
                    ):
                        if mask.any():
                            log["sat"].append(
                                {
                                    "k": log["k"],
                                    "region": region,
                                    "side": side,
                                    "n_years": int(mask.sum()),
                                    "first_year": int(years[mask][0]),
                                    "worst": float(np.nanmax(np.abs(arr[mask])))
                                    if side != "nonfinite"
                                    else np.nan,
                                }
                            )
                    clipped = np.clip(
                        np.nan_to_num(arr, nan=high, posinf=high, neginf=low), low, high
                    )
                    price = price.copy()
                    price.loc[proj_idx] = clipped
                    input_data = dict(input_data)
                    input_data["spike_fuel_price"] = price
                return _o(input_data)

            model.compute = tax_compute

        elif cls == "RPKElasticity":
            original = model.compute

            def rpk_compute(input_data, _o=original, _m=model):
                a = input_data["airfare_per_rpk"]
                arr = a.loc[a.index >= PROJ].to_numpy(dtype=float)
                fin = arr[np.isfinite(arr)]
                log["airfare"].append(
                    {
                        "k": log["k"],
                        "a_2050": float(a.loc[YEAR]),
                        "a_min": float(fin.min()) if fin.size else np.nan,
                        "n_neg": int((arr < 0).sum()),
                        "n_nonfinite": int((~np.isfinite(arr)).sum()),
                    }
                )
                return _o(input_data)

            model.compute = rpk_compute

    # Tag the two carbon-tax instances with their namespace, for readable output.
    seen = 0
    for disc in process.disciplines:
        model = getattr(disc, "model", None)
        if model is not None and type(model).__name__ == "SpikeMarketCarbonTax":
            model._probe_region = f"region_{'AB'[seen]}" if seen < 2 else f"#{seen}"
            seen += 1


def run_case(stiffness, gamma, accel, bound, show):
    log = {"k": 0, "emitted": [], "received": [], "sat": [], "airfare": []}
    p = build(stiffness, gamma, accel)
    instrument(p, log, bound=bound)
    p.compute()

    m = p.mda_chain.inner_mdas[0]
    hist = list(m.residual_history)
    vo = p.data["vector_outputs"]

    em = pd.DataFrame(log["emitted"])
    rc = pd.DataFrame(log["received"])
    sat = pd.DataFrame(log["sat"])
    af = pd.DataFrame(log["airfare"])

    tag = f"s{stiffness}_g{gamma}{'_accel' if accel else ''}{'_bounded' if bound else ''}"
    print("\n" + "=" * 100)
    print(
        f"CASE stiffness={stiffness} gamma={gamma} "
        f"accel={'Alternate2Delta' if accel else 'none'} "
        f"bound={'%gx-%gx' % bound if bound else 'none'}"
    )
    print("=" * 100)
    print(
        f"  {len(hist)} iterations, final residual {hist[-1]:.3e}, "
        f"price_2050={vo['region_A:spike_fuel_price'].loc[YEAR]:.6g}, "
        f"rpk_2050={vo['overall:rpk'].loc[YEAR]:.6g}"
    )

    emA = em[em.region == "region_A"].reset_index(drop=True)
    rcA = rc[rc.region == "region_A"].reset_index(drop=True)

    print(f"\n  p_k at {YEAR}, region_A -- emitted by the market vs received after the")
    print("  sequence transformer, and the airfare the elasticity model then sees:")
    print(
        f"  {'k':>4} {'p emitted':>15} {'p received':>15} {'recv<0':>7} {'recv nonfin':>12} "
        f"{'airfare 2050':>14} {'af<0':>5} {'residual':>11}"
    )
    n = min(show, len(emA))
    for i in range(n):
        pe = emA.p_2050.iloc[i] if i < len(emA) else np.nan
        pr = rcA.p_2050.iloc[i] if i < len(rcA) else np.nan
        nn = int(rcA.n_neg.iloc[i]) if i < len(rcA) else -1
        nf = int(rcA.n_nonfinite.iloc[i]) if i < len(rcA) else -1
        a = af[af.k == i + 1]
        av = float(a.a_2050.iloc[0]) if len(a) else np.nan
        an = int(a.n_neg.iloc[0]) if len(a) else -1
        res = hist[i] if i < len(hist) else np.nan
        print(
            f"  {i + 1:>4} {pe:>15.6g} {pr:>15.6g} {nn:>7} {nf:>12} "
            f"{av:>14.6g} {an:>5} {res:>11.3e}"
        )

    if bound is not None:
        print(f"\n  saturation events: {len(sat)}")
        if len(sat):
            ks = sorted(sat.k.unique())
            print(f"  iterations that saturate: {ks if len(ks) <= 40 else str(ks[:40]) + ' ...'}")
            print("  by side:")
            print(
                "   "
                + sat.groupby("side")
                .agg(
                    count=("k", "size"),
                    first_k=("k", "min"),
                    last_k=("k", "max"),
                    worst=("worst", "max"),
                )
                .to_string()
                .replace("\n", "\n   ")
            )
            last_k = int(sat.k.max())
            print(
                f"\n  VERDICT INPUT: last saturating iteration = {last_k} of {len(hist)} "
                f"-> {'RELEASES (transient)' if last_k < len(hist) - 2 else 'STILL BINDING at the end (asymptotic)'}"
            )

    out = "spike_unified_mda/brief1_out"
    os.makedirs(out, exist_ok=True)
    for name, frame in (("emitted", em), ("received", rc), ("sat", sat), ("airfare", af)):
        if len(frame):
            frame.to_csv(f"{out}/{name}_{tag}.csv", index=False)
    pd.DataFrame({"residual": hist}).to_csv(f"{out}/residual_{tag}.csv", index=False)
    return {
        "tag": tag,
        "iterations": len(hist),
        "residual": hist[-1],
        "last_sat_k": int(sat.k.max()) if len(sat) else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="+", default=["0.3,4", "0.3,8", "0.3,16"])
    ap.add_argument("--accel", action="store_true")
    ap.add_argument("--bound", action="store_true")
    ap.add_argument("--low", type=float, default=0.1)
    ap.add_argument("--high", type=float, default=20.0)
    ap.add_argument("--show", type=int, default=45)
    args = ap.parse_args()

    bound = (args.low, args.high) if args.bound else None
    summary = []
    for case in args.cases:
        s, g = (float(x) for x in case.split(","))
        summary.append(run_case(s, g, args.accel, bound, args.show))

    print("\n" + "=" * 100)
    print("SUMMARY")
    for row in summary:
        print(
            f"  {row['tag']:<28} {row['iterations']:>4} it  residual {row['residual']:.3e}"
            + (f"  last saturating k = {row['last_sat_k']}" if row["last_sat_k"] else "")
        )


if __name__ == "__main__":
    main()

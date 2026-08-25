"""Brief 1 -- where the domain exit comes from, and what shape the divergence has.

Two independent instruments, both read-only with respect to the AeroMAPS models.

``origin``
    Wraps every discipline's ``_run`` and records, per (discipline, variable), the
    first iteration at which a projection-year value stops being finite. A
    discipline whose INPUTS were all finite at that moment MANUFACTURED the
    non-finite value; anything else is downstream propagation. Answers question 1.

``traj``
    Re-runs the sweep with an optional wide price bound on ``SpikeFuelMarket``
    (0.1x to 20x the fossil reference ``base_price``), logs every saturation with
    its iteration index / region / year, and dumps ``p_k`` against ``k``.
    Answers question 2.

Usage:
    python -m spike_unified_mda.brief1_probe origin --stiffness 0.3 --gamma 8
    python -m spike_unified_mda.brief1_probe traj [--bound] [--out DIR]
"""

import argparse
import logging
import os
import sys
import warnings
from collections import defaultdict

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)

CONFIG = "spike_unified_mda/scenario/regionalisation_spike.yaml"

# Projection years only: AeroMAPS series are legitimately NaN on the historical block.
PROJ_START = 2025


# ---------------------------------------------------------------- helpers


def _bad_mask(value):
    """Projection-year non-finite mask for one variable value, or None if N/A."""
    if isinstance(value, pd.Series):
        try:
            sub = value.loc[value.index >= PROJ_START]
        except TypeError:
            return None
        arr = pd.to_numeric(sub, errors="coerce").to_numpy(dtype=float)
        return ~np.isfinite(arr), sub.index.to_numpy()
    if isinstance(value, (float, int, np.floating, np.integer)):
        return ~np.isfinite(np.array([float(value)])), np.array([-1])
    return None


def _classify(value, mask):
    """'nan' / 'inf' / 'nan+inf' for the flagged entries."""
    if isinstance(value, pd.Series):
        arr = pd.to_numeric(value.loc[value.index >= PROJ_START], errors="coerce").to_numpy(
            dtype=float
        )
    else:
        arr = np.array([float(value)])
    flagged = arr[mask]
    has_nan = bool(np.isnan(flagged).any())
    has_inf = bool(np.isinf(flagged).any())
    return "nan+inf" if (has_nan and has_inf) else ("inf" if has_inf else "nan")


# ---------------------------------------------------------------- origin probe


class OriginProbe:
    """Records the first finite -> non-finite transition of every output variable."""

    def __init__(self):
        self.tick = 0  # incremented once per SpikeFuelMarket execution ~ MDA iteration
        self.seen_clean = defaultdict(set)  # discipline -> {var} seen finite at least once
        self.events = []  # first transition per (discipline, var)
        self.recorded = set()
        self.run_index = 0

    def inspect(self, disc_name, input_data, output_data):
        self.run_index += 1
        if not isinstance(output_data, dict):
            return

        # Which inputs were already non-finite when this discipline ran?
        dirty_inputs = []
        for name, value in (input_data or {}).items():
            got = _bad_mask(value)
            if got is None:
                continue
            mask, _ = got
            if mask.any():
                dirty_inputs.append(name)

        for name, value in output_data.items():
            got = _bad_mask(value)
            if got is None:
                continue
            mask, years = got
            key = (disc_name, name)
            if not mask.any():
                self.seen_clean[disc_name].add(name)
                continue
            # Non-finite now. Only interesting if this variable was finite before.
            if name not in self.seen_clean[disc_name]:
                continue  # structurally NaN (unused pathway) -- not a transition
            if key in self.recorded:
                continue
            self.recorded.add(key)
            self.events.append(
                {
                    "tick": self.tick,
                    "run_index": self.run_index,
                    "discipline": disc_name,
                    "variable": name,
                    "kind": _classify(value, mask),
                    "first_year": int(years[mask][0]) if years[mask][0] != -1 else -1,
                    "n_years": int(mask.sum()),
                    "n_dirty_inputs": len(dirty_inputs),
                    "dirty_inputs": ",".join(sorted(dirty_inputs)[:4]),
                    "manufactured": len(dirty_inputs) == 0,
                }
            )


def install_origin_probe():
    from aeromaps.core import gemseo as gemseo_mod

    probe = OriginProbe()

    for cls_name in ("AeroMAPSCustomModelWrapper", "AeroMAPSAutoModelWrapper"):
        cls = getattr(gemseo_mod, cls_name)
        original = cls._run

        def make(original=original):
            def _run(self, input_data):
                out = original(self, input_data)
                try:
                    probe.inspect(self.name, input_data, out)
                except Exception as exc:  # noqa: BLE001
                    print(f"[probe error on {self.name}] {exc}", file=sys.stderr)
                return out

            return _run

        cls._run = make()

    # Tick the iteration counter on every market clearing.
    from spike_unified_mda.scenario import spike_market_models as smm

    market_compute = smm.SpikeFuelMarket.compute

    def ticking_compute(self, input_data):
        probe.tick += 1
        return market_compute(self, input_data)

    smm.SpikeFuelMarket.compute = ticking_compute
    return probe


# ---------------------------------------------------------------- price bound


class PriceLog:
    """Per-iteration record of the cleared price, plus saturation events."""

    def __init__(self, bound=None):
        self.bound = bound  # (low, high) or None
        self.rows = []
        self.saturations = []
        self.tick = 0


def install_price_instrument(log):
    from spike_unified_mda.scenario import spike_market_models as smm

    original = smm.SpikeFuelMarket.compute

    def instrumented(self, input_data):
        log.tick += 1
        out = original(self, input_data)

        base = float(self.config["base_price"])
        for region in self.regions:
            key = f"{region}:spike_fuel_price"
            price = out[key]
            proj = price.loc[price.index >= PROJ_START]
            arr = proj.to_numpy(dtype=float)

            log.rows.append(
                {
                    "tick": log.tick,
                    "region": region,
                    "p_2050": float(price.loc[2050]),
                    "p_max": float(np.nanmax(arr)) if np.isfinite(arr).any() else np.nan,
                    "p_min": float(np.nanmin(arr)) if np.isfinite(arr).any() else np.nan,
                    "n_nonfinite": int((~np.isfinite(arr)).sum()),
                    "demand_ratio_2050": float(
                        out["spike_total_fuel_demand"].loc[2050] / self.config["demand_ref"]
                    ),
                }
            )

            if log.bound is not None:
                low, high = log.bound[0] * base, log.bound[1] * base
                years = proj.index.to_numpy()
                hi_hit = arr > high
                lo_hit = arr < low
                nf_hit = ~np.isfinite(arr)
                for label, mask in (("high", hi_hit), ("low", lo_hit), ("nonfinite", nf_hit)):
                    if mask.any():
                        log.saturations.append(
                            {
                                "tick": log.tick,
                                "region": region,
                                "side": label,
                                "n_years": int(mask.sum()),
                                "first_year": int(years[mask][0]),
                                "worst": float(np.nanmax(np.abs(arr[mask])))
                                if label != "nonfinite"
                                else np.nan,
                            }
                        )
                clipped = np.clip(np.nan_to_num(arr, nan=high, posinf=high, neginf=low), low, high)
                new_price = price.copy()
                new_price.loc[new_price.index >= PROJ_START] = clipped
                out[key] = new_price
                self.df.loc[:, key] = new_price
        return out

    smm.SpikeFuelMarket.compute = instrumented


# ---------------------------------------------------------------- runner


def make_process(stiffness, gamma, plain_gauss_seidel=True):
    os.environ["SPIKE_STIFFNESS"] = str(stiffness)
    os.environ["SPIKE_GAMMA"] = str(gamma)
    from aeromaps.core.multi_regional_process import MultiRegionalProcess
    from gemseo.algos.sequence_transformer.acceleration import AccelerationMethod

    from spike_unified_mda.mda_settings import rebuild

    p = MultiRegionalProcess(CONFIG)
    p.on_mda_failure = "warn"
    settings = {"acceleration_method": AccelerationMethod.NONE} if plain_gauss_seidel else {}
    rebuild(p, **settings)
    return p


def mda_stats(p):
    m = p.mda_chain.inner_mdas[0]
    h = list(m.residual_history)
    return {
        "iterations": len(h),
        "residual": float(h[-1]) if h else float("nan"),
        "tolerance": float(m.settings.tolerance),
    }


def cmd_origin(args):
    probe = install_origin_probe()
    p = make_process(args.stiffness, args.gamma, plain_gauss_seidel=not args.accelerated)
    p.compute()
    st = mda_stats(p)

    print(f"\n=== ORIGIN PROBE  stiffness={args.stiffness} gamma={args.gamma} ===")
    print(
        f"{st['iterations']} iterations, final residual {st['residual']:.3e} "
        f"(tolerance {st['tolerance']:.0e}), {probe.run_index} discipline executions\n"
    )

    events = sorted(probe.events, key=lambda e: (e["run_index"],))
    manufactured = [e for e in events if e["manufactured"]]

    print(f"first finite -> non-finite transitions: {len(events)}")
    print(f"of which MANUFACTURED (all inputs finite): {len(manufactured)}\n")

    if not events:
        print("no transition recorded -- the run stayed finite.")
        return

    print("--- first 15 transitions, in execution order ---")
    header = f"{'it':>3} {'run':>5} {'M':>2} {'discipline':<34} {'variable':<40} {'kind':>7} {'yr':>5} {'dirty in':>9}"
    print(header)
    print("-" * len(header))
    for e in events[:15]:
        print(
            f"{e['tick']:>3} {e['run_index']:>5} {'*' if e['manufactured'] else ' ':>2} "
            f"{e['discipline'][:34]:<34} {e['variable'][:40]:<40} {e['kind']:>7} "
            f"{e['first_year']:>5} {e['n_dirty_inputs']:>9}"
        )

    print("\n--- MANUFACTURED (the actual sources) ---")
    if not manufactured:
        print("none: every non-finite value came in through an input.")
    for e in manufactured[:20]:
        print(
            f"  it {e['tick']:>3} run {e['run_index']:>5}  {e['discipline']}"
            f".{e['variable']}  [{e['kind']}]  from year {e['first_year']}"
            f"  ({e['n_years']} years)"
        )

    out = pd.DataFrame(events)
    path = os.path.join(args.out, f"origin_s{args.stiffness}_g{args.gamma}.csv")
    os.makedirs(args.out, exist_ok=True)
    out.to_csv(path, index=False)
    print(f"\nfull event log -> {path}")


def cmd_traj(args):
    os.makedirs(args.out, exist_ok=True)
    bound = (args.low, args.high) if args.bound else None
    cases = [tuple(float(x) for x in c.split(",")) for c in args.cases]

    all_rows = []
    print(f"\n=== TRAJECTORY PROBE  bound={'%.2gx-%.2gx base' % bound if bound else 'NONE'} ===")
    for stiffness, gamma in cases:
        log = PriceLog(bound=bound)
        install_price_instrument(log)
        p = make_process(stiffness, gamma, plain_gauss_seidel=not args.accelerated)
        p.compute()
        st = mda_stats(p)

        df = pd.DataFrame(log.rows)
        df["stiffness"] = stiffness
        df["gamma"] = gamma
        all_rows.append(df)

        sat = pd.DataFrame(log.saturations)
        n_sat_ticks = sorted(sat["tick"].unique()) if len(sat) else []
        vo = p.data["vector_outputs"]
        price_2050 = vo["region_A:spike_fuel_price"].loc[2050]
        rpk_2050 = vo["overall:rpk"].loc[2050]

        print(
            f"\n-- stiffness={stiffness} gamma={gamma}: {st['iterations']} it, "
            f"residual {st['residual']:.3e}, price_2050={price_2050:.4g}, rpk_2050={rpk_2050:.4g}"
        )
        if bound is not None:
            print(
                f"   saturating iterations: {n_sat_ticks if len(n_sat_ticks) < 25 else str(n_sat_ticks[:25]) + '...'}"
            )
            if len(sat):
                per_side = sat.groupby("side")["tick"].agg(["count", "min", "max"])
                print(per_side.to_string().replace("\n", "\n   "))
                sat["stiffness"] = stiffness
                sat["gamma"] = gamma
                sat.to_csv(
                    os.path.join(args.out, f"saturations_s{stiffness}_g{gamma}.csv"), index=False
                )

        region_a = df[df["region"] == "region_A"]
        print("   p_k at 2050 (region_A), by iteration:")
        vals = region_a["p_2050"].to_numpy()
        for start in range(0, min(len(vals), args.show), 10):
            chunk = vals[start : start + 10]
            print(f"     k={start + 1:>3}: " + " ".join(f"{v:>11.4g}" for v in chunk))

    out = pd.concat(all_rows, ignore_index=True)
    path = os.path.join(args.out, "trajectories.csv" if not bound else "trajectories_bounded.csv")
    out.to_csv(path, index=False)
    print(f"\ntrajectory log -> {path}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    o = sub.add_parser("origin")
    o.add_argument("--stiffness", type=float, default=0.3)
    o.add_argument("--gamma", type=float, default=8.0)
    o.add_argument("--accelerated", action="store_true")
    o.add_argument("--out", default="spike_unified_mda/brief1_out")
    o.set_defaults(func=cmd_origin)

    t = sub.add_parser("traj")
    t.add_argument("--bound", action="store_true")
    t.add_argument("--low", type=float, default=0.1)
    t.add_argument("--high", type=float, default=20.0)
    t.add_argument("--cases", nargs="+", default=["0.3,4", "0.3,8", "0.3,16"])
    t.add_argument("--accelerated", action="store_true")
    t.add_argument("--show", type=int, default=60)
    t.add_argument("--out", default="spike_unified_mda/brief1_out")
    t.set_defaults(func=cmd_traj)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

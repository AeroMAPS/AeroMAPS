"""Brief 2: finite-difference validation of the ``DemandSlope`` discipline.

Runs the spike scenario with ``DemandSlope`` wired in as a regional custom model,
then re-runs it with ``p_SAF`` shifted by ``delta`` EUR/MJ and compares the
discipline's ``{region}:fuel_demand_slope`` against ``(RPK(p+delta) - RPK(p))/delta``
measured on the converged MDA.
"""

import argparse
import logging
import os
import warnings

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)

CONFIG = "spike_unified_mda/scenario/regionalisation_spike_slope.yaml"
REGIONS = ("region_A", "region_B")
SAF_PATHWAYS = ("hefa_fog", "hefa_others", "ft_msw", "ft_others", "atj", "electrofuel")


def build(delta, stiffness, base_price):
    os.environ["SPIKE_STIFFNESS"] = str(stiffness)
    os.environ["SPIKE_BASE_PRICE"] = str(base_price)
    from aeromaps.core.multi_regional_process import MultiRegionalProcess
    from spike_unified_mda.mda_settings import rebuild

    process = MultiRegionalProcess(CONFIG)
    process.on_mda_failure = "warn"
    rebuild(process)
    if delta:
        for disc in process.disciplines:
            model = getattr(disc, "model", None)
            if getattr(model, "pathway_name", None) not in SAF_PATHWAYS:
                continue
            key = f"{model.pathway_name}_mean_mfsp_without_resource"
            original = model.compute

            def shifted(input_data, _o=original, _k=key):
                data = dict(input_data)  # never mutate the previous-iterate snapshot
                if _k in data:
                    data[_k] = data[_k] + delta
                return _o(data)

            model.compute = shifted
    process.compute()
    return process.data["vector_outputs"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delta", type=float, default=1e-5)
    ap.add_argument("--stiffness", type=float, default=0.0)
    ap.add_argument("--base-price", type=float, default=0.0)
    ap.add_argument("--central", action="store_true", help="central difference")
    ap.add_argument("--years", nargs="+", type=int, default=[2025, 2030, 2035, 2040, 2045, 2050])
    args = ap.parse_args()

    base = build(0.0, args.stiffness, args.base_price)
    up = build(args.delta, args.stiffness, args.base_price)
    down = build(-args.delta, args.stiffness, args.base_price) if args.central else None

    print(
        f"\nDemandSlope vs finite difference — stiffness={args.stiffness} "
        f"base_price={args.base_price} delta={args.delta:g} EUR/MJ "
        f"({'central' if args.central else 'forward'})"
    )

    worst = 0.0
    for region in REGIONS:
        rpk_b = base[f"{region}:rpk"]
        if args.central:
            fd = (up[f"{region}:rpk"] - down[f"{region}:rpk"]) / (2 * args.delta)
        else:
            fd = (up[f"{region}:rpk"] - rpk_b) / args.delta
        analytic = base[f"{region}:fuel_demand_slope"]
        open_loop = base[f"{region}:fuel_demand_slope_open_loop"]
        alpha = base[f"{region}:saf_blend_share"]

        print(f"\n=== {region} ===")
        print(
            f"  {'year':>6} {'alpha':>7} {'s analytic':>13} {'s numeric':>13} "
            f"{'rel.gap':>9} {'open loop gap':>14}"
        )
        for y in args.years:
            an, nu, op = float(analytic.loc[y]), float(fd.loc[y]), float(open_loop.loc[y])
            if abs(nu) < 1e-3 * abs(float(rpk_b.loc[y])) * 1e-9:
                print(
                    f"  {y:>6} {alpha.loc[y]:>7.3f} {an:>13.4e} {nu:>13.4e} "
                    f"{'(clamped)':>9} {'(clamped)':>14}"
                )
                continue
            gap = (an - nu) / nu
            worst = max(worst, abs(gap))
            print(
                f"  {y:>6} {alpha.loc[y]:>7.3f} {an:>13.4e} {nu:>13.4e} "
                f"{gap:>9.2%} {(op - nu) / nu:>14.2%}"
            )

    print(f"\nworst relative gap, analytic vs numeric: {worst:.3%}")
    print(
        "(last column: the four-stage open-loop product alone, i.e. without the "
        "airline supply-function feedback)"
    )


if __name__ == "__main__":
    main()

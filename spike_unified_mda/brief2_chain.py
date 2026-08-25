"""Brief 2: stage-by-stage decomposition of dD/dp_SAF, analytic vs finite difference.

Reference case: the Step-2 spike scenario, two regions, ``cagr_elasticity`` demand
(``RPKElasticity``) + ``models_operation_cost_top_down_feedback``
(``PassengerAircraftMarginalCost``).  The spike's own fuel market is neutralised by
default (``--base-price 0 --stiffness 0``) so the only closed loop is the one the
brief is about: airfare <-> RPK.  ``--stiffness``/``--base-price`` turn the extra
market loop back on to show what it adds.

p_SAF is defined as the euro/MJ selling price of SAF: the shock adds delta to
``{pathway}_mean_mfsp_without_resource`` of every non-fossil drop-in pathway, which
is a purely additive term of ``{pathway}_mean_mfsp``.  alpha is then the SAF share of
drop-in energy and ``d mfsp_mean/d p_SAF = alpha`` exactly.
"""

import argparse
import logging
import os
import warnings

import pandas as pd

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)

CONFIG = "spike_unified_mda/scenario/regionalisation_spike.yaml"
REGIONS = ("region_A", "region_B")
MARKETS = ("short_range", "medium_range", "long_range")

# Non-fossil drop-in pathways of default_energy_carriers/energy_carriers_data.yaml.
SAF_PATHWAYS = ("hefa_fog", "hefa_others", "ft_msw", "ft_others", "atj", "electrofuel")

P0 = 0.09236379319842411  # initial_price_per_rpk_corrected, hard-coded in the cost model
EPS = -0.9  # global.elasticity.price_elasticity of the spike markets.yaml


def build(delta, stiffness, base_price):
    """Build and run the scenario with ``delta`` EUR/MJ added to every SAF MFSP."""
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
            name = getattr(model, "pathway_name", None)
            if name not in SAF_PATHWAYS:
                continue
            key = f"{name}_mean_mfsp_without_resource"
            original = model.compute

            def shifted(input_data, _o=original, _k=key):
                # Copy: the discipline's input_data is GEMSEO's previous-iterate
                # snapshot and must never be mutated in place.
                data = dict(input_data)
                if _k in data:
                    data[_k] = data[_k] + delta
                return _o(data)

            model.compute = shifted

    process.compute()
    residual = float(process.mda_chain.inner_mdas[0].residual_history[-1])
    return process.data["vector_outputs"], residual


def stages(vo, region, years):
    """Per-year analytic ingredients of the four-stage chain, for one region."""
    g = lambda n: vo[f"{region}:{n}"]  # noqa: E731

    # --- stage 4: dilution.  alpha = SAF share of drop-in energy.
    alpha = 1.0 - g("fossil_kerosene_share_dropin_fuel") / 100.0

    # --- stage 3: energy intensity.  d doc_energy_per_ask_mean / d mfsp_dropin
    #     = sum_m (energy_per_ask_m_dropin * ask_share_m_dropin/100) * ask_m / sum_m ask_m
    ask_total = sum(g(f"ask_{m}") for m in MARKETS)
    e_ask = (
        sum(
            g(f"energy_per_ask_{m}_dropin_fuel")
            * g(f"ask_{m}_dropin_fuel_share")
            / 100.0
            * g(f"ask_{m}")
            for m in MARKETS
        )
        / ask_total
    )
    load_factor = g("load_factor")
    kappa = e_ask / (load_factor / 100.0)  # MJ/RPK: d total_cost_per_rpk / d mfsp

    # --- stage 2: the ad-hoc inverse supply function.
    c0 = float(g("total_cost_per_rpk_without_extra_tax").loc[2019])
    a = 2.0 * (P0 - c0) / g("rpk_no_elasticity")

    # --- stage 1: elasticity.
    rpk = g("rpk")
    airfare = g("airfare_per_rpk")
    eta = EPS * rpk / airfare  # dRPK / d airfare

    loop = a * eta  # dimensionless loop gain
    frame = pd.DataFrame(
        {
            "alpha": alpha,
            "e_ask_MJ_per_ASK": e_ask,
            "kappa_MJ_per_RPK": kappa,
            "a_EURperRPK2": a,
            "eta_RPK2_per_EUR": eta,
            "loop_gain_a_eta": loop,
            "passthrough": 1.0 / (1.0 - loop),
            "open_loop": eta * kappa * alpha,
            "closed_loop": eta * kappa * alpha / (1.0 - loop),
        }
    ).loc[years]
    frame.attrs["c0"] = c0
    return frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delta", type=float, default=1e-3, help="EUR/MJ shock on p_SAF")
    ap.add_argument("--stiffness", type=float, default=0.0)
    ap.add_argument("--base-price", type=float, default=0.0)
    ap.add_argument("--years", nargs="+", type=int, default=[2030, 2035, 2040, 2045, 2050])
    args = ap.parse_args()

    years = args.years
    base, res_b = build(0.0, args.stiffness, args.base_price)
    pert, res_p = build(args.delta, args.stiffness, args.base_price)
    print(
        f"\nreference case: stiffness={args.stiffness} base_price={args.base_price} "
        f"delta={args.delta:g} EUR/MJ"
    )
    print(f"MDA residuals: base={res_b:.2e}  perturbed={res_p:.2e}")

    for region in REGIONS:
        st = stages(base, region, years)
        g = lambda n: base[f"{region}:{n}"]  # noqa: E731
        gp = lambda n: pert[f"{region}:{n}"]  # noqa: E731

        # Numerical stage derivatives, read off the two converged runs.
        fd = pd.DataFrame(
            {
                "d_mfsp": (gp("dropin_fuel_mean_mfsp") - g("dropin_fuel_mean_mfsp")) / args.delta,
                "d_cost_rpk": (
                    gp("total_cost_per_rpk_without_extra_tax")
                    - g("total_cost_per_rpk_without_extra_tax")
                )
                / args.delta,
                "d_airfare": (gp("airfare_per_rpk") - g("airfare_per_rpk")) / args.delta,
                "d_rpk": (gp("rpk") - g("rpk")) / args.delta,
            }
        ).loc[years]

        print(
            f"\n=== {region} — C0 = {st.attrs['c0']:.6f} EUR/RPK, "
            f"markup (p0-C0)/p0 = {(P0 - st.attrs['c0']) / P0:.4f} ==="
        )

        print("\n  stage 4  d mfsp_mean/d p_SAF   (analytic = alpha)")
        print(f"  {'year':>6} {'alpha':>12} {'FD':>12} {'rel.gap':>10}")
        for y in years:
            an, nu = st.loc[y, "alpha"], fd.loc[y, "d_mfsp"]
            print(f"  {y:>6} {an:>12.6f} {nu:>12.6f} {(nu - an) / an:>10.2e}")

        print("\n  stage 3  d total_cost_per_rpk/d mfsp_mean   (analytic = kappa, MJ/RPK)")
        print(f"  {'year':>6} {'kappa':>12} {'FD':>12} {'rel.gap':>10}")
        for y in years:
            an = st.loc[y, "kappa_MJ_per_RPK"]
            nu = fd.loc[y, "d_cost_rpk"] / fd.loc[y, "d_mfsp"]
            print(f"  {y:>6} {an:>12.6f} {nu:>12.6f} {(nu - an) / an:>10.2e}")

        print(
            "\n  stage 2  d airfare/d total_cost_per_rpk   (partial = 1; equilibrium = 1/(1-a.eta))"
        )
        print(f"  {'year':>6} {'1/(1-a.eta)':>12} {'FD':>12} {'rel.gap':>10} {'absorbed':>10}")
        for y in years:
            an = st.loc[y, "passthrough"]
            nu = fd.loc[y, "d_airfare"] / fd.loc[y, "d_cost_rpk"]
            print(f"  {y:>6} {an:>12.6f} {nu:>12.6f} {(nu - an) / an:>10.2e} " f"{1 - an:>10.2%}")

        print("\n  stage 1  d RPK/d airfare   (analytic = eps.RPK/airfare)")
        print(f"  {'year':>6} {'eta':>14} {'FD':>14} {'rel.gap':>10}")
        for y in years:
            an = st.loc[y, "eta_RPK2_per_EUR"]
            nu = fd.loc[y, "d_rpk"] / fd.loc[y, "d_airfare"]
            print(f"  {y:>6} {an:>14.4e} {nu:>14.4e} {(nu - an) / an:>10.2e}")

        print("\n  end to end  dD/dp_SAF   [RPK per (EUR/MJ)]")
        print(
            f"  {'year':>6} {'open loop':>14} {'closed loop':>14} {'FD':>14} "
            f"{'gap open':>10} {'gap closed':>11}"
        )
        for y in years:
            op, cl, nu = (
                st.loc[y, "open_loop"],
                st.loc[y, "closed_loop"],
                fd.loc[y, "d_rpk"],
            )
            print(
                f"  {y:>6} {op:>14.4e} {cl:>14.4e} {nu:>14.4e} "
                f"{(nu - op) / op:>10.2%} {(nu - cl) / cl:>11.2%}"
            )

        print("\n  as an elasticity  (dD/D) / (dp_SAF/p_SAF) at p_SAF = mfsp of the SAF blend")
        print(f"  {'year':>6} {'loop gain':>12} {'passthru':>10} {'dD/D per +0.01 EUR/MJ':>24}")
        for y in years:
            print(
                f"  {y:>6} {st.loc[y, 'loop_gain_a_eta']:>12.5f} "
                f"{st.loc[y, 'passthrough']:>10.5f} "
                f"{fd.loc[y, 'd_rpk'] * 0.01 / g('rpk').loc[y]:>24.4%}"
            )


if __name__ == "__main__":
    main()

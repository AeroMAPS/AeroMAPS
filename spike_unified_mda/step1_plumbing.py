"""Step 1 of the spike: pure plumbing, no AeroMAPS chain.

Builds an MDAChain from one non-namespaced global SpikeClearing plus one
namespaced SpikeDemand per region, exactly as MultiRegionalProcess._setup_unified_mda
would assemble them, and exercises the five acceptance criteria on it.
"""

import argparse
import json
import logging
from types import SimpleNamespace

import numpy as np
from gemseo.mda.mda_chain import MDAChain

from aeromaps.core.gemseo import (
    AeroMAPSCustomModelWrapper,
    apply_namespace_to_disciplines,
    disable_gemseo_execution_statistics,
)
from spike_unified_mda.spike_models import SpikeClearing, SpikeDemand

disable_gemseo_execution_statistics()

# Minimal stand-in for AeroMAPS Parameters: only the year attributes that
# AeroMAPSModel._initialize_df reads.
SPIKE_PARAMETERS = SimpleNamespace(
    climate_historic_start_year=1940,
    historic_start_year=2000,
    prospection_start_year=2020,
    end_year=2050,
)

DEFAULT_REGIONS = {"EU": 1.0, "US": 0.8, "APAC": 1.4}


def build_chain(
    regions=None,
    stiffness=0.3,
    gamma=1.0,
    elasticity=0.5,
    p0=1.0,
    tolerance=1e-10,
    max_mda_iter=200,
    local_offset=None,
    log_convergence=False,
):
    """Assemble the unified MDAChain for the toy system."""
    regions = regions if regions is not None else DEFAULT_REGIONS
    region_ids = list(regions)
    demand_ref = float(sum(regions.values()))

    # --- Global, NOT namespaced discipline ---------------------------------
    clearing = SpikeClearing(name="SpikeClearing", parameters=SPIKE_PARAMETERS)
    clearing.configure(
        regions=region_ids,
        p0=p0,
        stiffness=stiffness,
        gamma=gamma,
        demand_ref=demand_ref,
        local_offset=local_offset,
    )
    clearing.custom_setup()
    clearing._initialize_df()  # re-run so _coupling_defaults sees the region list
    clearing_disc = AeroMAPSCustomModelWrapper(model=clearing)

    # --- Regional, namespaced disciplines ----------------------------------
    disciplines = []
    for rid, d0 in regions.items():
        demand = SpikeDemand(name="SpikeDemand", parameters=SPIKE_PARAMETERS)
        demand.configure(d0=d0, p0=p0, elasticity=elasticity)
        demand._initialize_df()
        disc = AeroMAPSCustomModelWrapper(model=demand)
        disciplines.extend(apply_namespace_to_disciplines([disc], rid))

    disciplines.append(clearing_disc)

    mda = MDAChain(
        disciplines=disciplines,
        tolerance=tolerance,
        max_mda_iter=max_mda_iter,
        initialize_defaults=True,
        inner_mda_name="MDAGaussSeidel",
        log_convergence=log_convergence,
    )
    return mda, disciplines, clearing, region_ids, demand_ref


def inner_mda_stats(mda):
    """Return (n_iterations, final_residual, converged) of the coupled inner MDA."""
    stats = []
    for inner in mda.inner_mdas:
        hist = list(getattr(inner, "residual_history", []) or [])
        if not hist:
            continue
        stats.append(
            {
                "mda": type(inner).__name__,
                "n_iterations": len(hist),
                "final_residual": float(hist[-1]),
                "normed_residual": float(getattr(inner, "normed_residual", np.nan)),
            }
        )
    return stats


def describe_coupling(mda, clearing_name="SpikeClearing"):
    """Report the coupling structure and whether the global discipline is in the SCC."""
    cs = mda.coupling_structure
    sccs = []
    for group in cs.strongly_coupled_disciplines:
        # GEMSEO returns a flat list of strongly coupled disciplines
        sccs.append(group.name if hasattr(group, "name") else str(group))
    couplings = sorted(cs.all_couplings)
    strong = sorted(cs.strong_couplings)
    return {
        "disciplines": [d.name for d in mda.disciplines],
        "strongly_coupled_disciplines": sccs,
        "all_couplings": couplings,
        "strong_couplings": strong,
        "clearing_in_scc": any(clearing_name in n for n in sccs),
    }


def analytic_fixed_point(stiffness, gamma, elasticity, tol=1e-15, max_iter=100000):
    """Reference scalar fixed point x = (1 + s x^g)^(-e) with x = D_tot/D_ref.

    Valid only when local_offset is zero for every region.
    """
    x = 1.0
    for _ in range(max_iter):
        nx = (1.0 + stiffness * x**gamma) ** (-elasticity)
        if abs(nx - x) < tol:
            return nx, True
        x = nx
    return x, False


def loop_gain(x, stiffness, gamma, elasticity):
    """|g'(x)| of the Gauss-Seidel map at x (theoretical contraction factor)."""
    if x <= 0:
        return np.inf
    denom = 1.0 + stiffness * x**gamma
    return abs(-elasticity * denom ** (-elasticity - 1.0) * stiffness * gamma * x ** (gamma - 1.0))


def run_case(
    stiffness,
    gamma,
    elasticity,
    tolerance=1e-10,
    max_mda_iter=200,
    regions=None,
    local_offset=None,
    verbose=False,
):
    """Build, execute, and report one parameter case."""
    mda, disciplines, clearing, region_ids, demand_ref = build_chain(
        regions=regions,
        stiffness=stiffness,
        gamma=gamma,
        elasticity=elasticity,
        tolerance=tolerance,
        max_mda_iter=max_mda_iter,
        local_offset=local_offset,
    )
    result = {
        "stiffness": stiffness,
        "gamma": gamma,
        "elasticity": elasticity,
        "tolerance": tolerance,
        "max_mda_iter": max_mda_iter,
    }
    try:
        out = mda.execute()
    except Exception as exc:  # noqa: BLE001 - spike wants the failure mode recorded
        result["status"] = "error"
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result, mda, None

    stats = inner_mda_stats(mda)
    result["inner_mda"] = stats
    total = out["spike_total_demand"]
    x_num = float(total.iloc[-1]) / demand_ref
    x_ref, ref_ok = analytic_fixed_point(stiffness, gamma, elasticity)
    result["x_numeric"] = x_num
    result["x_analytic"] = x_ref if ref_ok else None
    result["x_error"] = abs(x_num - x_ref) if ref_ok else None
    result["loop_gain_at_fp"] = loop_gain(x_ref, stiffness, gamma, elasticity) if ref_ok else None

    res = stats[0]["normed_residual"] if stats else np.nan
    n_it = stats[0]["n_iterations"] if stats else -1
    converged = bool(np.isfinite(res) and res <= tolerance)
    result["status"] = (
        "converged" if converged else ("stagnated" if n_it >= max_mda_iter else "stalled")
    )
    result["n_iterations"] = n_it
    result["final_residual"] = res
    if verbose:
        print(json.dumps(result, indent=2, default=str))
    return result, mda, out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stiffness", type=float, default=0.3)
    parser.add_argument("--gamma", type=float, default=1.0)
    parser.add_argument("--elasticity", type=float, default=0.5)
    parser.add_argument("--tolerance", type=float, default=1e-10)
    parser.add_argument("--max-iter", type=int, default=200)
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)
    res, mda, out = run_case(
        args.stiffness, args.gamma, args.elasticity, args.tolerance, args.max_iter
    )
    print("=== COUPLING ===")
    print(json.dumps(describe_coupling(mda), indent=2, default=str))
    print("=== RESULT ===")
    print(json.dumps(res, indent=2, default=str))

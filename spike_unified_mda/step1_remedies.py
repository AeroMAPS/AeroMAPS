"""Do damping / acceleration / Newton rescue the diverged cases?

IMPORTANT: MDAChain forwards to its inner MDAs only the settings that belong to
``BaseMDASettings`` (tolerance, max_mda_iter, warm_start, log_convergence, ...).
``over_relaxation_factor`` and ``acceleration_method`` are NOT in that set, so
passing them to ``MDAChain(...)`` silently configures the outer chain only.
They must go through ``inner_mda_settings``.
"""

import warnings

import numpy as np
from scipy.optimize import brentq
from gemseo.mda.mda_chain import MDAChain

from aeromaps.core.gemseo import (
    AeroMAPSCustomModelWrapper,
    apply_namespace_to_disciplines,
    disable_gemseo_execution_statistics,
)
from spike_unified_mda.spike_models import SpikeClearing, SpikeDemand
from spike_unified_mda.step1_plumbing import DEFAULT_REGIONS, SPIKE_PARAMETERS

disable_gemseo_execution_statistics()
warnings.filterwarnings("ignore")


def true_fixed_point(stiffness, gamma, elasticity):
    """Ground truth for x = D_tot/D_ref, by bracketing root find (not fixed-point iteration)."""

    def f(x):
        return x - (1.0 + stiffness * x**gamma) ** (-elasticity)

    lo, hi = 1e-12, 1.0
    if f(lo) * f(hi) > 0:
        return None
    return brentq(f, lo, hi, xtol=1e-15, rtol=1e-15, maxiter=500)


def build(stiffness, gamma, elasticity, regions=None, p0=1.0, linearize=False, **mda_settings):
    regions = regions or DEFAULT_REGIONS
    region_ids = list(regions)
    demand_ref = float(sum(regions.values()))
    clearing = SpikeClearing(name="SpikeClearing", parameters=SPIKE_PARAMETERS)
    clearing.configure(region_ids, p0, stiffness, gamma, demand_ref)
    clearing.custom_setup()
    clearing._initialize_df()
    discs = []
    for rid, d0 in regions.items():
        dm = SpikeDemand(name="SpikeDemand", parameters=SPIKE_PARAMETERS)
        dm.configure(d0=d0, p0=p0, elasticity=elasticity)
        dm._initialize_df()
        discs.extend(apply_namespace_to_disciplines([AeroMAPSCustomModelWrapper(model=dm)], rid))
    discs.append(AeroMAPSCustomModelWrapper(model=clearing))
    if linearize:
        for d in discs:
            d.linearization_mode = "finite_differences"
    return MDAChain(disciplines=discs, initialize_defaults=True, **mda_settings), demand_ref


def try_case(
    label,
    stiffness,
    gamma,
    elasticity=0.5,
    tolerance=1e-10,
    max_mda_iter=500,
    linearize=False,
    inner=None,
):
    inner = inner or {}
    try:
        mda, dref = build(
            stiffness,
            gamma,
            elasticity,
            linearize=linearize,
            tolerance=tolerance,
            max_mda_iter=max_mda_iter,
            inner_mda_settings=inner,
            inner_mda_name=inner.pop("_name", "MDAGaussSeidel"),
        )
        out = mda.execute()
    except Exception as exc:  # noqa: BLE001
        return {
            "case": label,
            "s": stiffness,
            "gamma": gamma,
            "status": "ERROR",
            "err": f"{type(exc).__name__}: {str(exc)[:110]}",
        }
    hist = list(mda.inner_mdas[0].residual_history)
    res = float(hist[-1]) if hist else np.nan
    x_num = float(out["spike_total_demand"].iloc[-1]) / dref
    x_ref = true_fixed_point(stiffness, gamma, elasticity)
    return {
        "case": label,
        "s": stiffness,
        "gamma": gamma,
        "status": "converged" if res <= tolerance else "NOT conv",
        "iters": len(hist),
        "residual": res,
        "x_num": x_num,
        "x_ref": x_ref,
        "x_err": abs(x_num - x_ref) if x_ref is not None else None,
    }


HARD_CASES = [(3.0, 4.0), (3.0, 5.0), (3.0, 6.0), (3.0, 10.0), (0.3, 20.0), (0.3, 30.0)]

VARIANTS = [
    ("GS baseline", {"_name": "MDAGaussSeidel"}, False),
    ("GS relax=0.7", {"_name": "MDAGaussSeidel", "over_relaxation_factor": 0.7}, False),
    ("GS relax=0.4", {"_name": "MDAGaussSeidel", "over_relaxation_factor": 0.4}, False),
    ("GS relax=0.2", {"_name": "MDAGaussSeidel", "over_relaxation_factor": 0.2}, False),
    ("GS relax=0.05", {"_name": "MDAGaussSeidel", "over_relaxation_factor": 0.05}, False),
    (
        "GS + Alternate2Delta",
        {"_name": "MDAGaussSeidel", "acceleration_method": "Alternate2Delta"},
        False,
    ),
    (
        "GS + SecantAcceleration",
        {"_name": "MDAGaussSeidel", "acceleration_method": "SecantAcceleration"},
        False,
    ),
    ("Jacobi (dflt accel)", {"_name": "MDAJacobi"}, False),
    ("Jacobi no accel", {"_name": "MDAJacobi", "acceleration_method": "NoTransformation"}, False),
    ("NewtonRaphson (FD)", {"_name": "MDANewtonRaphson"}, True),
]

if __name__ == "__main__":
    hdr = f"{'s':>5} {'gam':>5} {'variant':>24} {'status':>10} {'it':>4} {'residual':>10} {'x_num':>10} {'x_ref':>10} {'x_err':>9}"
    print(hdr)
    print("-" * len(hdr))
    for s, g in HARD_CASES:
        print()
        for label, inner, lin in VARIANTS:
            r = try_case(label, s, g, inner=dict(inner), linearize=lin)
            if r["status"] == "ERROR":
                print(f"{s:>5} {g:>5} {label:>24} {'ERROR':>10}  -> {r['err'][:80]}")
                continue
            xe = r["x_err"]
            print(
                f"{s:>5} {g:>5} {label:>24} {r['status']:>10} {r['iters']:>4} "
                f"{r['residual']:>10.2e} {r['x_num']:>10.6f} "
                f"{(f'{r[chr(120)+chr(95)+chr(114)+chr(101)+chr(102)]:.6f}' if r['x_ref'] is not None else '-'):>10} "
                f"{(f'{xe:.1e}' if xe is not None else '-'):>9}"
            )

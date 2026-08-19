"""Criteria 2/3/4 exercised on the Step-1 pure-plumbing chain."""

import json

import numpy as np

from spike_unified_mda.step1_plumbing import (
    build_chain,
    describe_coupling,
    inner_mda_stats,
    run_case,
)


def _snapshot(out, keys):
    return {k: np.asarray(out[k], dtype=float).copy() for k in keys}


def _bitwise_equal(a, b):
    return all(np.array_equal(a[k], b[k]) for k in a)


def _max_abs_diff(a, b):
    return max(float(np.max(np.abs(a[k] - b[k]))) for k in a)


def criterion_3_idempotence(tolerance=1e-10):
    """Two compute() on identical inputs -> bit-identical outputs?

    Three variants are distinguished:
      A. same MDAChain executed twice (GEMSEO cache active)
      B. same MDAChain executed twice with the cache cleared (warm-started
         from the converged point, disciplines' self.df already populated)
      C. a freshly built cold chain vs. variant B
    """
    mda, _, clearing, region_ids, demand_ref = build_chain(tolerance=tolerance)
    keys = [f"{r}:spike_price" for r in region_ids] + ["spike_total_demand"]

    out1 = mda.execute()
    snap1 = _snapshot(out1, keys)
    n1 = inner_mda_stats(mda)[0]["n_iterations"]

    out2 = mda.execute()
    snap2 = _snapshot(out2, keys)
    n2 = inner_mda_stats(mda)[0]["n_iterations"]

    mda.cache.clear()
    out3 = mda.execute()
    snap3 = _snapshot(out3, keys)
    n3 = inner_mda_stats(mda)[0]["n_iterations"]

    mda_cold, _, _, _, _ = build_chain(tolerance=tolerance)
    out4 = mda_cold.execute()
    snap4 = _snapshot(out4, keys)
    n4 = inner_mda_stats(mda_cold)[0]["n_iterations"]

    return {
        "A_same_chain_cached": {
            "bitwise_identical": _bitwise_equal(snap1, snap2),
            "max_abs_diff": _max_abs_diff(snap1, snap2),
            "iterations": [n1, n2],
        },
        "B_same_chain_cache_cleared": {
            "bitwise_identical": _bitwise_equal(snap1, snap3),
            "max_abs_diff": _max_abs_diff(snap1, snap3),
            "iterations": [n1, n3],
        },
        "C_cold_vs_warm": {
            "bitwise_identical": _bitwise_equal(snap3, snap4),
            "max_abs_diff": _max_abs_diff(snap3, snap4),
            "iterations": [n3, n4],
        },
    }


def criterion_4_sweep(tolerance=1e-10, max_mda_iter=200, elasticity=0.5):
    """Sweep stiffness and gamma upwards until divergence or stagnation."""
    rows = []

    # 1D sweep on stiffness at gamma = 1
    for s in [0.3, 1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 50, 100, 200, 500, 1000]:
        res, _, _ = run_case(s, 1.0, elasticity, tolerance, max_mda_iter)
        rows.append({"sweep": "stiffness@gamma=1", **_row(res)})

    # 1D sweep on gamma at stiffness = 0.3
    for g in [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 60, 100]:
        res, _, _ = run_case(0.3, float(g), elasticity, tolerance, max_mda_iter)
        rows.append({"sweep": "gamma@stiffness=0.3", **_row(res)})

    # 1D sweep on gamma at a realistic-ish steep stiffness = 3
    for g in [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20]:
        res, _, _ = run_case(3.0, float(g), elasticity, tolerance, max_mda_iter)
        rows.append({"sweep": "gamma@stiffness=3", **_row(res)})

    return rows


def _row(res):
    return {
        "stiffness": res["stiffness"],
        "gamma": res["gamma"],
        "status": res["status"],
        "n_iterations": res.get("n_iterations"),
        "final_residual": res.get("final_residual"),
        "loop_gain_at_fp": res.get("loop_gain_at_fp"),
        "x_error": res.get("x_error"),
        "error": res.get("error"),
    }


def criterion_2_nominal():
    res, mda, _ = run_case(0.3, 1.0, 0.5, 1e-10, 200)
    return {"coupling": describe_coupling(mda), "result": res}


if __name__ == "__main__":
    import sys

    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    payload = {}
    if what in ("all", "2"):
        payload["criterion_2_nominal"] = criterion_2_nominal()
    if what in ("all", "3"):
        payload["criterion_3_idempotence"] = criterion_3_idempotence()
    if what in ("all", "4"):
        payload["criterion_4_sweep"] = criterion_4_sweep()
    print(json.dumps(payload, indent=2, default=str))

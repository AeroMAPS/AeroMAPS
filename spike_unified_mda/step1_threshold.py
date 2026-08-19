"""Fine location of the plain-Gauss-Seidel breakdown threshold, vs the theory."""

import warnings
import numpy as np
from scipy.optimize import brentq

from spike_unified_mda.step1_remedies import build, true_fixed_point

warnings.filterwarnings("ignore")


def loop_gain(x, s, g, e):
    if x is None or x <= 0:
        return np.inf
    return abs(e * (1.0 + s * x**g) ** (-e - 1.0) * s * g * x ** (g - 1.0))


def theoretical_gamma_star(s, e, lo=1.0, hi=200.0):
    """gamma at which the Gauss-Seidel contraction factor |g'(x*)| reaches 1."""

    def f(g):
        return loop_gain(true_fixed_point(s, g, e), s, g, e) - 1.0

    if f(lo) > 0:
        return None
    return brentq(f, lo, hi, xtol=1e-6)


def converges(s, g, e=0.5, tol=1e-10, max_iter=2000, inner=None):
    inner = dict(inner or {})
    name = inner.pop("_name", "MDAGaussSeidel")
    mda, dref = build(
        s, g, e, tolerance=tol, max_mda_iter=max_iter, inner_mda_name=name, inner_mda_settings=inner
    )
    mda.execute()
    hist = list(mda.inner_mdas[0].residual_history)
    return (float(hist[-1]) <= tol), len(hist), float(hist[-1])


def bisect_threshold(s, e=0.5, lo=1.0, hi=200.0, tol=1e-10, max_iter=2000, inner=None, depth=18):
    """Largest gamma that still converges, by bisection."""
    ok_lo, _, _ = converges(s, lo, e, tol, max_iter, inner)
    if not ok_lo:
        return None
    for _ in range(depth):
        mid = 0.5 * (lo + hi)
        ok, _, _ = converges(s, mid, e, tol, max_iter, inner)
        if ok:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-3:
            break
    return lo


if __name__ == "__main__":
    e = 0.5
    print(f"elasticity = {e}, tolerance = 1e-10, max_mda_iter = 2000\n")
    print(
        f"{'stiffness':>10} {'gamma* (empirical)':>20} {'gamma* (theory |g|=1)':>23} "
        f"{'iters at 0.95*g*':>17} {'gain at g*':>11}"
    )
    print("-" * 88)
    for s in (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0):
        emp = bisect_threshold(s, e)
        th = theoretical_gamma_star(s, e)
        if emp is None:
            print(f"{s:>10} {'diverges at gamma=1':>20}")
            continue
        _, it, _ = converges(s, 0.95 * emp, e)
        gain = loop_gain(true_fixed_point(s, emp, e), s, emp, e)
        print(f"{s:>10} {emp:>20.3f} {(f'{th:.3f}' if th else 'n/a'):>23} {it:>17} {gain:>11.4f}")

    print("\nWith GaussSeidel over-relaxation 0.7 (damping):")
    for s in (0.3, 3.0, 10.0):
        emp = bisect_threshold(s, e, hi=400.0, inner={"over_relaxation_factor": 0.7})
        print(f"  stiffness={s:>6}: gamma* = {emp:.3f}" if emp else f"  stiffness={s}: none")

    print("\nWith GaussSeidel + Alternate2Delta acceleration:")
    for s in (0.3, 3.0, 10.0):
        emp = bisect_threshold(s, e, hi=400.0, inner={"acceleration_method": "Alternate2Delta"})
        print(f"  stiffness={s:>6}: gamma* = {emp:.3f}" if emp else f"  stiffness={s}: none")

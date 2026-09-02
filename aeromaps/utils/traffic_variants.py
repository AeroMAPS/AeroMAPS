"""Build low and high traffic variants by scaling a markets file's growth.

A study that wants a traffic range usually has published endpoints -- a 2050 RPK
for the low case and one for the high case -- and a central markets file. What it
does not have is the growth rates that land on them. This module closes that gap:
:func:`scale_growth_after` produces a candidate markets document, and
:func:`solve_scale_for_target` searches for the scale factor whose run hits the
endpoint.

Scaling only *after* a pivot year is deliberate. The observed period is not a
projection and must not be rescaled, so the pivot is normally the prospection
start. Rescaling through it would make the variants disagree with data.

The evaluation is passed in rather than performed here, because running a
scenario needs a configuration this module has no business owning. That also
keeps the solver testable without a model run.
"""

import copy


def scale_growth_after(
    document,
    alpha,
    pivot_year,
    markets=("short_range", "medium_range", "long_range"),
    traffic_types=("passenger", "freight"),
):
    """A copy of a markets document with post-pivot CAGR growth scaled by ``alpha``.

    Both the per-market growth curves and the ``defaults`` reference curves are
    scaled. Leaving the reference untouched would describe a different scenario
    from the one being run, and the reference is what the demand models measure
    their response against.

    Parameters
    ----------
    document : dict
        A loaded ``markets.yaml``. It is deep-copied, not mutated.
    alpha : float
        Multiplier on each growth rate after ``pivot_year``.
    pivot_year : int
        Periods starting at or before this year keep their central value.
    markets, traffic_types : iterable of str, optional
        Which market blocks and which ``defaults`` sub-blocks to scale.

    Returns
    -------
    dict
        The scaled document.
    """
    document = copy.deepcopy(document)

    for market in markets:
        growth = (document.get(market, {}).get("inputs") or {}).get("growth")
        if not growth:
            continue
        years = growth["cagr_reference_periods"]
        growth["cagr_reference_periods_values"] = [
            value * alpha if year > pivot_year else value
            for year, value in zip(years, growth["cagr_reference_periods_values"])
        ]

    for traffic_type in traffic_types:
        reference = (
            document.get("defaults", {}).get(traffic_type, {}).get("inputs", {}).get("reference")
        )
        if not reference:
            continue
        years = reference["reference_cagr_reference_periods"]
        reference["reference_cagr_reference_periods_values"] = [
            value * alpha if year > pivot_year else value
            for year, value in zip(years, reference["reference_cagr_reference_periods_values"])
        ]
    return document


def solve_scale_for_target(evaluate, target, bracket, tol=5e-4, max_iter=12):
    """Secant search for the scale factor whose evaluation lands on ``target``.

    Parameters
    ----------
    evaluate : callable
        ``evaluate(alpha)`` returning the metric to match. It is called once per
        iteration, so it is the expensive part; the caller normally writes the
        candidate file and runs a scenario inside it.
    target : float
        The value to hit.
    bracket : tuple of float
        Two starting factors. They need not bracket the root -- the secant method
        does not require it -- but a pair straddling it converges fastest.
    tol : float, optional
        Relative tolerance on ``target``, or absolute when ``target`` is zero,
        which has no relative scale to be measured against.
    max_iter : int, optional
        Cap on iterations. Secant can stall on a flat or noisy response, so this
        bounds the work rather than promising convergence.

    Returns
    -------
    float
        The best factor found. The caller is responsible for writing it out,
        since the last evaluation may not have been at the returned value.
    """
    a, b = bracket
    fa, fb = evaluate(a) - target, evaluate(b) - target
    # A zero target has no relative scale, so tol reads as absolute there. Dividing
    # by it instead would raise, which is the same failure the flat-secant guard
    # below already takes care to avoid. For any other target this is unchanged.
    scale = abs(target) or 1.0
    for _ in range(max_iter):
        if abs(fb) / scale < tol:
            break
        if fb == fa:
            # A flat secant cannot propose a next point; stop rather than divide
            # by zero and report the best factor reached.
            break
        a, b = b, b - fb * (b - a) / (fb - fa)
        fa, fb = fb, evaluate(b) - target
    return b

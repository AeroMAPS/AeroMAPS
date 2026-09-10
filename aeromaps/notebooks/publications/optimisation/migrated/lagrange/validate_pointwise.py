"""Per-run trust flags for lambda_G1.

The aggregate envelope test in ``validate_multipliers.py`` measures bias and
scatter over the whole grid. It cannot catch a single bad run, because one
outlier barely moves a median. These two checks are pointwise, and between them
they do catch it.

**Bracket test.** The optimal objective is convex and decreasing in the carbon
budget, so the point derivative at a grid node must lie between the secant
slopes either side of it. A multiplier outside that bracket contradicts the
objective values of its own neighbours. Neighbours that stopped infeasible are
not on the same optimal-value curve and are excluded.

**Gradient-consistency test.** The surplus objective is the *same* function in
every run - only the budget constraint differs - so a gradient stored at one
run's optimum can be tested against the objective value at a neighbouring run's
optimum. ``0.5 (g_i + g_{i+1}) . (x_{i+1} - x_i)`` estimates ``f_{i+1} - f_i``
to third order, which is a direct measure of stored-gradient quality and needs
no re-run.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from extract_multipliers import OUT, RESULTS, _restore, evaluation_point

GROSS_BUDGET_2050_GTCO2 = 799.189271182
EU_ASK_SHARE = 15.49 / 100
BUDGETS = ["2_0", "2_2", "2_4", "2_6", "2_8", "3_0", "3_2", "3_4", "3_6", "3_8"]

# A run whose stored gradient misses the objective change by more than this is
# not to be trusted: the typical run manages 0.05 %.
GRADIENT_TOLERANCE_PCT = 0.5
# Slack on the bracket, to absorb the curvature between grid nodes.
BRACKET_SLACK = 0.10


def load_points():
    """Every run's optimum, gradient, objective and feasibility, by case."""
    points = {}
    for case in ["B5", "B75", "main", "B15", "pess"]:
        entries = []
        for budget in BUDGETS:
            path = RESULTS / f"opt_{case}_{budget}.hdf"
            if not path.exists():
                continue
            problem = _restore(path)
            grad_key = f"@{problem.objective.name}"
            try:
                x_eval, distance, entry = evaluation_point(problem, grad_key)
            except ValueError:
                x_eval, distance, entry = None, np.nan, None
            entries.append(
                {
                    "case": case,
                    "run": path.stem,
                    "budget": float(budget.replace("_", ".")),
                    "f_opt": problem.solution.f_opt / 1e-10,
                    "feasible": bool(problem.solution.is_feasible),
                    "x": None if entry is None else x_eval,
                    "grad": None if entry is None else np.asarray(entry[grad_key], float),
                    "has_gradient": entry is not None and distance < 1e-6,
                }
            )
        points[case] = sorted(entries, key=lambda e: e["budget"])
    return points


def gradient_consistency(points) -> pd.DataFrame:
    rows = []
    for case, entries in points.items():
        usable = [e for e in entries if e["feasible"] and e["has_gradient"]]
        for lo, hi in zip(usable, usable[1:]):
            step = hi["x"] - lo["x"]
            actual = hi["f_opt"] - lo["f_opt"]
            trapezoid = 0.5 * (lo["grad"] + hi["grad"]) @ step / 1e-10
            rows.append(
                {
                    "case": case,
                    "interval": f"{lo['budget']}->{hi['budget']}",
                    "run_lo": lo["run"],
                    "run_hi": hi["run"],
                    "delta_f_actual_eur": actual,
                    "delta_f_from_gradients_eur": trapezoid,
                    "error_pct": 100 * (trapezoid - actual) / actual if actual else np.nan,
                }
            )
    return pd.DataFrame(rows)


def bracket_test(points, table: pd.DataFrame) -> pd.DataFrame:
    d_budget_d_share = GROSS_BUDGET_2050_GTCO2 * EU_ASK_SHARE / 100
    lookup = {
        r.run: r.shadow_price_eur_per_tco2_discounted2020
        for r in table[table.constraint == "G1"].drop_duplicates("run").itertuples()
    }
    rows = []
    for case, entries in points.items():
        by_budget = {e["budget"]: e for e in entries}
        for entry in entries:
            if not entry["feasible"] or entry["run"] not in lookup:
                continue
            secants = {}
            for side, other in (
                ("left", round(entry["budget"] - 0.2, 1)),
                ("right", round(entry["budget"] + 0.2, 1)),
            ):
                neighbour = by_budget.get(other)
                # An infeasible neighbour is not on the optimal-value curve.
                if neighbour is None or not neighbour["feasible"]:
                    continue
                lo, hi = (neighbour, entry) if side == "left" else (entry, neighbour)
                slope = (hi["f_opt"] - lo["f_opt"]) / (hi["budget"] - lo["budget"])
                secants[side] = -slope / (d_budget_d_share * 1e9)
            lam = lookup[entry["run"]]
            if len(secants) == 2:
                low, high = min(secants.values()), max(secants.values())
                passed = bool(low * (1 - BRACKET_SLACK) <= lam <= high * (1 + BRACKET_SLACK))
            else:
                passed = None
            rows.append(
                {
                    "run": entry["run"],
                    "case": case,
                    "budget": entry["budget"],
                    "secant_left_eur_per_tco2": secants.get("left", np.nan),
                    "lambda_G1_eur_per_tco2": lam,
                    "secant_right_eur_per_tco2": secants.get("right", np.nan),
                    "in_bracket": passed,
                }
            )
    return pd.DataFrame(rows)


def run_quality(table: pd.DataFrame) -> pd.DataFrame:
    points = load_points()
    gradients = gradient_consistency(points)
    brackets = bracket_test(points, table)
    gradients.to_csv(OUT / "validation_gradient_consistency.csv", index=False)

    # A failing interval implicates both its endpoints, so attribute the blame:
    # a run that also sits in a *passing* interval is exonerated, because its
    # gradient demonstrably works there. What is left is the common member of
    # the failing intervals, which is the run actually at fault.
    failed, passed = set(), set()
    for row in gradients.itertuples():
        target = failed if abs(row.error_pct) > GRADIENT_TOLERANCE_PCT else passed
        target.update({row.run_lo, row.run_hi})
    suspect = failed - passed

    per_run = table.groupby("run").first().reset_index()
    quality = brackets.merge(
        per_run[["run", "run_feasible", "kkt_residual_relative"]], on="run", how="left"
    )
    quality["gradient_suspect"] = quality.run.isin(suspect)
    quality["kkt_converged"] = quality.kkt_residual_relative < 1e-2
    quality["trustworthy"] = (
        quality.run_feasible
        & quality.kkt_converged
        & ~quality.gradient_suspect
        & (quality.in_bracket != False)  # noqa: E712 - None means "not testable"
    )
    return quality.sort_values(["case", "budget"])


if __name__ == "__main__":
    table = pd.read_csv(OUT / "lagrange_multipliers.csv")
    quality = run_quality(table)
    quality.to_csv(OUT / "validation_run_quality.csv", index=False)
    print("Per-run trust flags for lambda_G1\n")
    print(quality.to_string(index=False, float_format=lambda v: f"{v:9.4g}"))
    print(f"\ntrustworthy: {int(quality.trustworthy.sum())} / {len(quality)} feasible runs")
    bad = quality[~quality.trustworthy]
    print("\nrejected:")
    print(
        bad[
            ["run", "lambda_G1_eur_per_tco2", "in_bracket", "gradient_suspect", "kkt_converged"]
        ].to_string(index=False, float_format=lambda v: f"{v:9.4g}")
    )

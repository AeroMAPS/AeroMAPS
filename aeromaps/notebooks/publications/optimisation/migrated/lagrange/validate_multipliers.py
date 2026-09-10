"""Independent finite-difference validation of the extracted multipliers.

The envelope theorem says the multiplier on an active constraint equals the
derivative of the optimal objective with respect to that constraint's bound.
The sweep grid gives that derivative a second, completely independent estimate:
differentiate the optimal objective numerically along the grid and compare.

Nothing here reuses a multiplier to build the finite difference, so agreement
is real evidence and not an identity.

Only feasible runs take part. A run that stopped infeasible has no KKT point,
so its "multipliers" are not shadow prices - see the report.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from extract_multipliers import (
    EU_ASK_SHARE,
    OUT,
)

GROSS_BUDGET_2050_GTCO2 = 799.189271182  # constant across every run
BIOMASS_AXIS = ["B5", "B75", "main", "B15"]  # same efficiency roadmap, 1.35 %/yr


def central_difference(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Three-point derivative on a possibly non-uniform grid.

    ``numpy.gradient`` already does exactly this, including the one-sided
    endpoints; it is spelled out here only to keep the convention explicit.
    """
    return np.gradient(y, x, edge_order=2)


def budget_envelope(table: pd.DataFrame) -> pd.DataFrame:
    """Check lambda_G1 against d f*/d(carbon budget share), along each case."""
    rows = []
    surplus = table[
        (table.objective_kind == "min_surplus_loss")
        & table.run_feasible
        & table.carbon_budget_share_world_pct.notna()
    ]
    for case, block in surplus.groupby("case"):
        g1 = (
            block[block.constraint == "G1"]
            .sort_values("carbon_budget_share_world_pct")
            .drop_duplicates("run")
        )
        if len(g1) < 3:
            continue
        share = g1.carbon_budget_share_world_pct.to_numpy(float)
        f_opt = g1.f_opt_eur_discounted2020.to_numpy(float)
        lam = g1.lambda_eur_discounted2020_per_unit_g.to_numpy(float)
        budget = g1.budget_adjusted_gtco2.to_numpy(float)

        # d f*/d share, predicted. g = (cum - B)/B so d f*/dB = -lambda/B, and
        # B is linear in the share: dB/d share = gross * EU_ASK_SHARE / 100.
        d_budget_d_share = GROSS_BUDGET_2050_GTCO2 * EU_ASK_SHARE / 100
        predicted = -lam / budget * d_budget_d_share
        observed = central_difference(share, f_opt)

        rows.append(
            pd.DataFrame(
                {
                    "case": case,
                    "carbon_budget_share_world_pct": share,
                    "f_opt_eur": f_opt,
                    "lambda_G1_eur_per_unit_g": lam,
                    "budget_adjusted_gtco2": budget,
                    "d_f_d_share_predicted_eur": predicted,
                    "d_f_d_share_findiff_eur": observed,
                    "relative_error": np.where(
                        observed != 0, (predicted - observed) / observed, np.nan
                    ),
                    "shadow_price_eur_per_tco2": lam / (budget * 1e9),
                    # Same derivative expressed as a carbon price, straight from the
                    # finite difference: d f*/d(budget in tCO2).
                    "findiff_price_eur_per_tco2": -observed / (d_budget_d_share * 1e9),
                }
            )
        )
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def biomass_envelope(table: pd.DataFrame) -> pd.DataFrame:
    """Check sum_t lambda_G3 against d f*/d(biomass share), at constant budget."""
    rows = []
    surplus = table[
        (table.objective_kind == "min_surplus_loss")
        & table.run_feasible
        & table.carbon_budget_share_world_pct.notna()
        & table.case.isin(BIOMASS_AXIS)
    ]
    # Sum of the annual G3 multipliers, per run. They all differentiate the same
    # discounted objective, so summing the discounted values is the consistent
    # thing to do - mixing in undiscounted ones here would be an error.
    g3 = (
        surplus[surplus.constraint == "G3"]
        .groupby(["run", "case", "biomass_share_world_pct", "carbon_budget_share_world_pct"])
        .agg(
            lambda_G3_sum_eur_per_unit_g=("lambda_eur_discounted2020_per_unit_g", "sum"),
            n_active_G3=("active", "sum"),
            f_opt_eur=("f_opt_eur_discounted2020", "first"),
        )
        .reset_index()
    )
    for budget, block in g3.groupby("carbon_budget_share_world_pct"):
        block = block.sort_values("biomass_share_world_pct")
        if len(block) < 3:
            continue
        share = block.biomass_share_world_pct.to_numpy(float)
        f_opt = block.f_opt_eur.to_numpy(float)
        lam_sum = block.lambda_G3_sum_eur_per_unit_g.to_numpy(float)

        # E_allocated is proportional to the biomass share, so at an active
        # constraint d g_t/d share = -1/share and d f*/d share = -sum(lambda)/share.
        predicted = -lam_sum / share
        observed = central_difference(share, f_opt)

        rows.append(
            pd.DataFrame(
                {
                    "carbon_budget_share_world_pct": budget,
                    "case": block.case.to_numpy(),
                    "biomass_share_world_pct": share,
                    "f_opt_eur": f_opt,
                    "lambda_G3_sum_eur_per_unit_g": lam_sum,
                    "n_active_G3": block.n_active_G3.to_numpy(),
                    "d_f_d_biomass_share_predicted_eur": predicted,
                    "d_f_d_biomass_share_findiff_eur": observed,
                    "relative_error": np.where(
                        observed != 0, (predicted - observed) / observed, np.nan
                    ),
                }
            )
        )
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def trapezoid_check(x, y, dydx, labels=None) -> pd.DataFrame:
    """Integral form of the envelope check, over each consecutive grid interval.

    Comparing derivatives point-by-point on a coarse, unevenly spaced grid
    conflates two different errors: whether the multiplier is right, and how
    badly a three-point stencil truncates on a strongly curved objective. The
    integral form separates them. The envelope theorem gives

        f*(b2) - f*(b1) = integral of d f*/db over [b1, b2],

    and the trapezoid of the *predicted* derivatives at the two ends estimates
    that integral to O(h^3) instead of differentiating to O(h^2). Its error is
    second order in the curvature, so on this grid it is the fairer test.
    """
    x, y, dydx = np.asarray(x, float), np.asarray(y, float), np.asarray(dydx, float)
    rows = []
    for i in range(len(x) - 1):
        width = x[i + 1] - x[i]
        predicted = width * (dydx[i] + dydx[i + 1]) / 2
        observed = y[i + 1] - y[i]
        rows.append(
            {
                "interval": f"{x[i]:g} -> {x[i + 1]:g}",
                "x_lo": x[i],
                "x_hi": x[i + 1],
                "delta_f_predicted_eur": predicted,
                "delta_f_observed_eur": observed,
                "relative_error": (predicted - observed) / observed if observed else np.nan,
            }
        )
        if labels is not None:
            rows[-1].update(labels)
    return pd.DataFrame(rows)


def regress(predicted, observed, label: str) -> dict:
    """Fit ``observed = slope * predicted`` and split bias from scatter.

    A pointwise relative error mixes two very different failures. If the
    multipliers carried a units or normalisation bug the slope would sit away
    from 1 and every point would miss the same way; if the grid is simply too
    coarse to resolve a piecewise-smooth derivative, the slope stays at 1 and
    the misses scatter either side. Only the first would make the numbers
    unpublishable, so it is worth measuring separately.
    """
    predicted = np.asarray(predicted, float)
    observed = np.asarray(observed, float)
    keep = np.isfinite(predicted) & np.isfinite(observed) & (observed != 0)
    predicted, observed = predicted[keep], observed[keep]
    slope = float(predicted @ observed / (predicted @ predicted))
    residual = observed - slope * predicted
    centred = observed - observed.mean()
    return {
        "check": label,
        "n": len(observed),
        "slope": slope,
        "bias_pct": 100 * (slope - 1),
        "r_squared": float(1 - residual @ residual / (centred @ centred)),
        "residual_scatter_pct": 100 * float(np.std(residual / observed)),
    }


def slackness_report(table: pd.DataFrame) -> pd.DataFrame:
    """Sign and complementary-slackness audit, split by feasibility."""
    rows = []
    for feasible, block in table.groupby("run_feasible"):
        rows.append(
            {
                "run_feasible": feasible,
                "runs": block.run.nunique(),
                "rows": len(block),
                "negative_multipliers": int((block.lambda_raw < 0).sum()),
                "nonzero_lambda_on_inactive": int(((block.lambda_raw > 0) & (~block.active)).sum()),
                "active_with_zero_lambda": int(((block.active) & (block.lambda_raw <= 0)).sum()),
                "max_lambda_on_inactive": float(block.loc[~block.active, "lambda_raw"].max()),
                "max_constraint_violation": float(block.max_constraint_violation.max()),
                "median_relative_kkt_residual": float(
                    block.groupby("run").kkt_residual_relative.first().median()
                ),
                "max_relative_kkt_residual": float(
                    block.groupby("run").kkt_residual_relative.first().max()
                ),
            }
        )
    return pd.DataFrame(rows)


def summarise(label: str, frame: pd.DataFrame, column: str = "relative_error") -> None:
    err = frame[column].replace([np.inf, -np.inf], np.nan).dropna().abs()
    print(f"\n=== {label} ===")
    print(
        f"  n = {len(err)}   median |rel err| = {err.median():.3%}   "
        f"mean = {err.mean():.3%}   max = {err.max():.3%}"
    )
    print(
        f"  within 10% : {(err <= 0.10).sum()}/{len(err)}    "
        f"within 15% : {(err <= 0.15).sum()}/{len(err)}"
    )


if __name__ == "__main__":
    table = pd.read_csv(OUT / "lagrange_multipliers.csv")

    slack = slackness_report(table)
    slack.to_csv(OUT / "validation_slackness.csv", index=False)
    print("=== sign / complementary slackness ===")
    print(slack.to_string(index=False))

    budget = budget_envelope(table)
    budget.to_csv(OUT / "validation_budget_envelope.csv", index=False)
    summarise("envelope check 1: carbon budget (all grid points)", budget)
    interior = (
        budget.groupby("case")
        .apply(lambda b: b.iloc[1:-1], include_groups=False)
        .reset_index(drop=True)
    )
    summarise("envelope check 1: carbon budget (interior points only)", interior)

    biomass = biomass_envelope(table)
    biomass.to_csv(OUT / "validation_biomass_envelope.csv", index=False)
    summarise("envelope check 2: biomass (all grid points)", biomass)
    inner = (
        biomass.groupby("carbon_budget_share_world_pct")
        .apply(lambda b: b.iloc[1:-1], include_groups=False)
        .reset_index(drop=True)
    )
    summarise("envelope check 2: biomass (interior points only)", inner)

    # --- integral form, the fairer test on this grid ---------------------- #
    budget_trapz = pd.concat(
        [
            trapezoid_check(
                b.carbon_budget_share_world_pct,
                b.f_opt_eur,
                b.d_f_d_share_predicted_eur,
                labels={"case": case},
            )
            for case, b in budget.groupby("case")
        ],
        ignore_index=True,
    )
    budget_trapz.to_csv(OUT / "validation_budget_envelope_integral.csv", index=False)
    summarise("envelope check 1 (integral form): carbon budget", budget_trapz)

    biomass_trapz = pd.concat(
        [
            trapezoid_check(
                b.biomass_share_world_pct,
                b.f_opt_eur,
                b.d_f_d_biomass_share_predicted_eur,
                labels={"carbon_budget_share_world_pct": budget_share},
            )
            for budget_share, b in biomass.groupby("carbon_budget_share_world_pct")
        ],
        ignore_index=True,
    )
    biomass_trapz.to_csv(OUT / "validation_biomass_envelope_integral.csv", index=False)
    summarise("envelope check 2 (integral form): biomass, all intervals", biomass_trapz)

    # Where biomass has stopped binding the multiplier is correctly zero and the
    # finite difference is differencing a saturated objective, so restrict to
    # intervals where the constraint is actually doing something.
    binding = biomass[biomass.n_active_G3 >= 2]
    biomass_binding = pd.concat(
        [
            trapezoid_check(
                b.biomass_share_world_pct,
                b.f_opt_eur,
                b.d_f_d_biomass_share_predicted_eur,
                labels={"carbon_budget_share_world_pct": budget_share},
            )
            for budget_share, b in binding.groupby("carbon_budget_share_world_pct")
            if len(b) >= 2
        ],
        ignore_index=True,
    )
    biomass_binding.to_csv(OUT / "validation_biomass_envelope_binding.csv", index=False)
    summarise(
        "envelope check 2 (integral form): biomass, intervals where G3 binds",
        biomass_binding,
    )

    # --- bias vs scatter, the test that decides publishability ------------- #
    big = biomass_trapz[biomass_trapz.delta_f_observed_eur.abs() > 1e9]
    regression = pd.DataFrame(
        [
            regress(
                budget_trapz.delta_f_predicted_eur,
                budget_trapz.delta_f_observed_eur,
                "G1 / carbon budget, integral form",
            ),
            regress(
                big.delta_f_predicted_eur,
                big.delta_f_observed_eur,
                "G3 / biomass, integral form (|df| > 1e9 EUR)",
            ),
        ]
    )
    regression.to_csv(OUT / "validation_regression.csv", index=False)
    print("\n=== bias vs scatter (slope 1.0 => unbiased multipliers) ===")
    print(regression.to_string(index=False, float_format=lambda v: f"{v:.4g}"))

    print(f"\nwrote validation_*.csv to {OUT}")

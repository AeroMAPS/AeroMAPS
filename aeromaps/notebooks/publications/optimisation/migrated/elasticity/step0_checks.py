"""Step 0 of the elasticity brief: the two checks that gate the batch.

Check 1 - the calibration point must be elasticity-invariant.
    The demand curve is P(Q) = beta(t) Q^(1/eps) with beta(t) = P_0 / Q_0(t)^(1/eps),
    so at the calibration price P_0 every elasticity must reproduce the same traffic.
    Run a 2019-technology reference (no efficiency gain, no mandate) at each
    elasticity and compare the traffic trajectories. If they diverge, the beta
    recalibration is not doing what the paper says and the sweep is uninterpretable.

Check 2 - the eps = -1 code path.
    ``scenario_cost.py`` branches on ``price_elasticity == -1`` because the
    isoelastic surplus integral becomes logarithmic there. Confirm the branch is
    reached and that the surplus loss is continuous across it, by comparing
    -1.0 against -0.999 and -1.001.

Usage:  poetry run python step0_checks.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
sys.path.insert(0, str(PAPER))

import optimisation_runs as R  # noqa: E402
from aeromaps.core.gemseo import disable_gemseo_execution_statistics  # noqa: E402

# config_rte.yaml and the yamls it pulls in are resolved against the working
# directory, so run from the paper folder. Every path written here is absolute.
os.chdir(PAPER)

RESULTS = HERE / "results"
ELASTICITIES = [-0.6, -0.8, -0.9, -1.0, -1.4]
BRANCH_PROBE = [-0.999, -1.0, -1.001]
CASE = "main"
START_YEAR = 2000


def series(payload: dict, name: str) -> pd.Series:
    values = np.asarray(payload["vector_outputs"][name], dtype=float)
    return pd.Series(values, index=range(START_YEAR, START_YEAR + len(values)))


def run(elasticity: float, tech_2019: bool, mandate: str, stem: str) -> dict:
    """One plain MDA. ``tech_2019`` zeroes the efficiency roadmap."""
    path = RESULTS / f"{stem}.json"
    if path.exists():
        print(f"  {stem}: on disk, skipped", flush=True)
        return json.loads(path.read_text())

    t0 = time.perf_counter()
    process = R.build_process(CASE, optimisation=False)
    process.parameters.price_elasticity = elasticity

    if tech_2019:
        # 2019 technology: no drop-in efficiency improvement at all.
        for market in R.PASSENGER_MARKETS["config_rte.yaml"]:
            setattr(
                process.parameters,
                f"{market}_energy_per_ask_dropin_fuel_gain_reference_years_values",
                [0.0],
            )

    if mandate == "none":
        # No mandate anywhere, 2025 leading entry included: leaving biofuel at 2 %
        # in 2025 and 0 % after takes a pathway share from positive back to zero,
        # which is the 0/0 that makes the MDA converge on NaN.
        process.parameters.generic_biofuel_mandate_share_values_fixed = [0.0, 0.0]
        process.parameters.generic_electrofuel_mandate_share_values_fixed = [0.0, 0.0]
        R.set_mandate(process, biofuel=[0.0] * 5, electrofuel=[0.0] * 5)
    elif mandate == "refueleu":
        R.set_mandate(process, **R.REFUELEU_MANDATE)
    else:
        raise ValueError(mandate)

    process.compute()
    RESULTS.mkdir(parents=True, exist_ok=True)
    process.write_json(str(path))
    print(f"  {stem}: {time.perf_counter() - t0:.0f} s", flush=True)
    return json.loads(path.read_text())


def check_1() -> pd.DataFrame:
    print("\n=== Check 1: is the calibration point elasticity-invariant? ===", flush=True)
    print("2019 technology, no mandate, five elasticities\n", flush=True)
    rows, traffic = [], {}
    for eps in ELASTICITIES:
        p = run(eps, tech_2019=True, mandate="none", stem=f"ref2019_eps{eps}")
        rpk = series(p, "rpk")
        rpk0 = series(p, "rpk_no_elasticity")
        fare = series(p, "airfare_per_rpk")
        traffic[eps] = rpk
        rows.append(
            {
                "eps": eps,
                "rpk_2050_Tpkm": rpk.loc[2050] / 1e12,
                "rpk_no_elasticity_2050": rpk0.loc[2050] / 1e12,
                "fare_2025": fare.loc[2025],
                "fare_2050": fare.loc[2050],
                "max_|rpk/rpk0 - 1|": float((rpk / rpk0 - 1).abs().max()),
            }
        )
    df = pd.DataFrame(rows).set_index("eps")
    t = pd.DataFrame(traffic)
    spread = (t.max(axis=1) - t.min(axis=1)) / t.mean(axis=1)
    df.attrs["max_relative_spread"] = float(spread.max())
    df.attrs["spread_year"] = int(spread.idxmax())
    return df


def check_2() -> pd.DataFrame:
    print("\n=== Check 2: the eps = -1 branch ===", flush=True)
    print("ReFuelEU mandate at -0.999 / -1.0 / -1.001\n", flush=True)
    rows = []
    for eps in BRANCH_PROBE:
        p = run(eps, tech_2019=False, mandate="refueleu", stem=f"branch_eps{eps}")
        fo = p["float_outputs"]
        rows.append(
            {
                "eps": eps,
                "branch": "log" if eps == -1 else "power",
                "area_loss_2050_MEUR": series(p, "area_loss").loc[2050],
                "cum_surplus_loss_disc_MEUR": fo.get(
                    "cumulative_total_surplus_loss_discounted_obj", np.nan
                ),
                "rpk_2050_Tpkm": series(p, "rpk").loc[2050] / 1e12,
            }
        )
    return pd.DataFrame(rows).set_index("eps")


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    disable_gemseo_execution_statistics()
    pd.set_option("display.width", 200)

    c1 = check_1()
    print("\n", c1.to_string(float_format=lambda v: f"{v:,.6g}"))
    print(
        f"\n  traffic spread across elasticities: "
        f"max {c1.attrs['max_relative_spread']:.3e} (year {c1.attrs['spread_year']})"
    )
    print(f"  VERDICT: {'PASS' if c1.attrs['max_relative_spread'] < 1e-6 else 'FAIL'}")

    c2 = check_2()
    print("\n", c2.to_string(float_format=lambda v: f"{v:,.8g}"))
    a = c2.area_loss_2050_MEUR
    jump = abs(a.loc[-1.0] - 0.5 * (a.loc[-0.999] + a.loc[-1.001]))
    rel = jump / abs(a.loc[-1.0]) if a.loc[-1.0] else np.nan
    print(f"\n  |log branch - midpoint of the two power-branch neighbours| = {rel:.3e} relative")
    print(f"  VERDICT: {'PASS' if rel < 1e-3 else 'FAIL'}")

    c1.to_csv(HERE / "step0_check1_calibration.csv")
    c2.to_csv(HERE / "step0_check2_branch.csv")
    print(f"\nwrote step0_check*.csv to {HERE}")

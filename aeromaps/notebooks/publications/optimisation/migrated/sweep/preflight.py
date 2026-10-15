"""Preflight: fix the carbon budget every optimisation is held to, and check it.

1. The ReFuelEU-derived carbon budget, recomputed from a fresh reference MDA at 10 %
   biomass allocation, and its world-budget-share equivalent. The ReFuelEU-step
   variant and fossil BAU are run alongside for reference.
2. Whether the ReFuelEU-linear trajectory satisfies G2-G6 -- and if not, under which
   of block B's ramp-up caps it would.

Usage:  poetry run python preflight.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
sys.path.insert(0, str(PAPER))

import optimisation_runs as R  # noqa: E402

RESULTS = HERE / "results"
YEARS = list(range(2000, 2051))
OPTIM_YEARS = R.OPTIM_YEARS
BIOMASS_SHARE = 10.0

# ReFuelEU Aviation (Regulation (EU) 2023/2405, Annex I) as legislated: a share that
# holds flat between milestones and jumps at them, rather than the linear ramp the
# yaml interpolates. Total SAF share, and the synthetic sub-share within it.
#
# Written out year by year from the regulation, so it needs no interpolation at all.
REFUELEU_STEP = {
    # first_year: (total SAF %, synthetic sub-share %)
    2025: (2.0, 0.0),
    2030: (6.0, 1.2),
    2032: (6.0, 2.0),
    2035: (20.0, 5.0),
    2040: (34.0, 10.0),
    2045: (42.0, 15.0),
    2050: (70.0, 35.0),
}

EJ_PER_YEAR_TO_MJ = 1e12


# --------------------------------------------------------------------------- #
# Constraint recomputation
# --------------------------------------------------------------------------- #


def _ramp(consumption, rate, volume):
    """G5/G6 exactly as ``constraints_rte._ramp_up_violation`` computes them.

    Both branches are increments on the previous period: the volume term is a capacity
    *addition*, so it sits on top of ``E_{t-1}`` rather than replacing it.
    """
    out, check_years = {}, [OPTIM_YEARS[0] - 5] + list(OPTIM_YEARS)
    for year in OPTIM_YEARS:
        lookback = year - 5 if (year - 5) in check_years else year - 10
        dt = year - lookback
        previous = consumption.loc[lookback]
        allowance = volume * dt * EJ_PER_YEAR_TO_MJ
        cap = max(previous * (1 + rate) ** dt, previous + allowance)
        out[year] = (consumption.loc[year] - cap) / allowance
    return pd.Series(out)


def constraints_of(path, rate=0.20, volume=0.2 * R.EU_ASK_SHARE, biomass_share=BIOMASS_SHARE):
    """G2-G6 for a saved MDA, at a chosen set of ramp-up caps.

    Validated against the constraint values GEMSEO stores in an optimisation's HDF:
    applied to opt_main_3_0 this reproduces them to JSON print precision.
    """
    data = json.load(open(path))
    vectors, floats = data["vector_outputs"], data["float_inputs"]
    series = lambda key: pd.Series(vectors[key], index=YEARS)  # noqa: E731

    # The saved run's own biomass allocation, so the share can be restated at another.
    saved_share = floats["generic_biomass_availability_aviation_allocated_share"] / R.EU_ASK_SHARE
    biomass = (
        series("generic_biomass_consumed_aviation_allocated_share") * saved_share / biomass_share
    )

    return pd.DataFrame(
        {
            "blend_completeness": (
                (
                    series("generic_biofuel_mandate_share")
                    + series("generic_electrofuel_mandate_share")
                    - 99.999
                )
                / 100
            ).loc[OPTIM_YEARS],
            "biomass": ((biomass - 100) / 100).loc[OPTIM_YEARS],
            "electricity": (
                (series("generic_electricity_consumed_aviation_allocated_share") - 100) / 100
            ).loc[OPTIM_YEARS],
            "biofuel_ramp": _ramp(series("generic_biofuel_energy_consumption"), rate, volume),
            "electrofuel_ramp": _ramp(
                series("generic_electrofuel_energy_consumption"), rate, volume
            ),
        }
    )


# --------------------------------------------------------------------------- #
# Reference runs
# --------------------------------------------------------------------------- #


def _step_series():
    """The step mandate as a value per year, as net biofuel and electrofuel shares."""
    biofuel, electrofuel = {}, {}
    milestones = sorted(REFUELEU_STEP)
    for index, first in enumerate(milestones):
        last = milestones[index + 1] - 1 if index + 1 < len(milestones) else 2050
        total, synthetic = REFUELEU_STEP[first]
        for year in range(first, last + 1):
            # The model's "biofuel" pathway is the non-synthetic remainder of the
            # SAF mandate, matching REFUELEU_MANDATE in optimisation_runs.
            biofuel[year], electrofuel[year] = total - synthetic, synthetic
    years = list(range(2020, 2051))
    return (
        years,
        [biofuel.get(y, 0.0) for y in years],
        [electrofuel.get(y, 0.0) for y in years],
    )


def run_reference(kind):
    """A plain MDA at 10 % biomass: 'refueleu_linear', 'refueleu_step' or 'fossil'."""
    stem = RESULTS / kind
    if stem.with_suffix(".json").exists():
        print(f"  {kind}: on disk, skipped")
        return stem.with_suffix(".json")

    import os

    from aeromaps.core.gemseo import disable_gemseo_execution_statistics

    disable_gemseo_execution_statistics()
    os.chdir(PAPER)

    process = R.build_process("main", config="config_rte.yaml", optimisation=False)
    process.parameters.generic_biomass_availability_aviation_allocated_share = (
        BIOMASS_SHARE * R.EU_ASK_SHARE
    )

    if kind == "refueleu_linear":
        R.set_mandate(process, **R.REFUELEU_MANDATE)
    elif kind == "refueleu_step":
        years, biofuel, electrofuel = _step_series()
        # A value at every year, so the yaml's linear interpolation has nothing left to
        # interpolate and the steps survive intact.
        #
        # ``ReducedMandate`` is on the chain whatever the mandate is, and it builds the
        # value list as fixed + optim, so the series has to arrive through that split
        # rather than as one vector. The cut is at 2030, the first design year: 2020-2029
        # are "fixed", 2030-2050 take the place of the design variables.
        split = years.index(2030)
        process.parameters.generic_biofuel_mandate_share_years = years
        process.parameters.generic_electrofuel_mandate_share_years = years
        process.parameters.generic_biofuel_mandate_share_values_fixed = biofuel[:split]
        process.parameters.generic_electrofuel_mandate_share_values_fixed = electrofuel[:split]
        R.set_mandate(process, biofuel=biofuel[split:], electrofuel=electrofuel[split:])
    elif kind == "fossil":
        process.parameters.generic_biofuel_mandate_share_values_fixed = [0.0, 0.0, 0.0]
        process.parameters.generic_electrofuel_mandate_share_values_fixed = [0.0, 0.0]
        R.set_mandate(process, biofuel=[0.0] * 5, electrofuel=[0.0] * 5)
    else:
        raise ValueError(kind)

    process.compute()
    RESULTS.mkdir(exist_ok=True)
    process.write_json(str(stem.with_suffix(".json")))
    print(f"  {kind}: written")
    return stem.with_suffix(".json")


def budget_of(path):
    """Cumulative 2020-2050 CO2 and its world-budget-share equivalent."""
    data = json.load(open(path))
    cumulative = dict(zip(YEARS, data["vector_outputs"]["cumulative_co2_emissions"]))[2050]
    gross = data["float_outputs"]["gross_carbon_budget_2050"]
    return cumulative, 100 * cumulative / gross, 100 * cumulative / gross / R.EU_ASK_SHARE


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def main():
    print("=" * 78)
    print("PREFLIGHT 1 - the fixed carbon budget")
    print("=" * 78)
    paths = {kind: run_reference(kind) for kind in ("refueleu_linear", "refueleu_step", "fossil")}

    rows = []
    for kind in ("refueleu_linear", "refueleu_step", "fossil"):
        gt, eu_share, world_share = budget_of(paths[kind])
        rows.append(
            {
                "scenario": kind,
                "cumulative_GtCO2": gt,
                "EU_share_pct": eu_share,
                "world_share_pct": world_share,
            }
        )
    table = pd.DataFrame(rows)
    print()
    print(table.to_string(index=False, float_format=lambda v: f"{v:.6f}"))
    table.to_csv(HERE / "preflight_budget.csv", index=False)

    import run_batch

    linear = table.loc[table.scenario == "refueleu_linear"].iloc[0]
    drift = abs(linear.world_share_pct - run_batch.BUDGET_WORLD_SHARE)
    print(f"\n  run_batch.BUDGET_WORLD_SHARE = {run_batch.BUDGET_WORLD_SHARE:.9f} %")
    print(f"  recomputed here              = {linear.world_share_pct:.9f} %   drift {drift:.2e}")
    if drift > 1e-6:
        print("  *** MISMATCH - update BUDGET_WORLD_SHARE before launching ***")

    print()
    print("=" * 78)
    print("PREFLIGHT 2 - does ReFuelEU-linear satisfy G2-G6? (positive = violated)")
    print("=" * 78)
    print("\nAt baseline caps (20 %/yr, 0.2 EJ/yr):\n")
    baseline = constraints_of(paths["refueleu_linear"])
    print(baseline.to_string(float_format=lambda v: f"{v:9.6f}"))
    worst = baseline.max().max()
    print(f"\n  worst violation {worst:+.6f}" f"  -> {'VIOLATED' if worst > 0 else 'feasible'}")

    print("\nWorst violation across block B / B' cap variants:\n")
    grid = []
    for rate in (0.118, 0.20, 0.39):
        for volume in (0.1, 0.2, 0.4):
            frame = constraints_of(
                paths["refueleu_linear"], rate=rate, volume=volume * R.EU_ASK_SHARE
            )
            worst = frame.max().max()
            where = frame.stack().idxmax()
            grid.append(
                {
                    "rate_cap": rate,
                    "volume_cap_EJ_yr": volume,
                    "worst": worst,
                    "feasible": worst <= 0,
                    "binding": f"{where[1]} {where[0]}",
                }
            )
    grid = pd.DataFrame(grid)
    print(grid.to_string(index=False, float_format=lambda v: f"{v:.6f}"))
    grid.to_csv(HERE / "preflight_refueleu_feasibility.csv", index=False)


if __name__ == "__main__":
    main()

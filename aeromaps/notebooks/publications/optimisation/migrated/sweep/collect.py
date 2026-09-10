"""Turn the batch's saved runs into the three tables the brief asks for.

  sweep_by_year.csv        one row per (run, year)
  sweep_summary.csv        one row per run: parameters, objective, diagnostics,
                           and the policy cost against its matched fossil-BAU reference
  sweep_constraints.csv    one row per (run, constraint, reference year): value,
                           slack, and whether it is active

On the surplus columns: ``cumulative_total_surplus_loss_discounted`` is measured
against 2019 unit economics applied to the exogenous traffic trajectory, so it is
negative for every scenario here -- fossil BAU included. The column carried forward as
a policy cost is the difference against the matched reference, which is what the paper
means by a surplus loss. See run_references.py.

Usage:  poetry run python collect.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
sys.path.insert(0, str(PAPER))
sys.path.insert(0, str(HERE))

import optimisation_runs as R  # noqa: E402
from run_batch import RESULTS, RUNS, rebuild_summary  # noqa: E402
from run_references import reference_key  # noqa: E402

YEARS = list(range(2000, 2051))
OPTIM_YEARS = R.OPTIM_YEARS

# name in the tidy CSV -> name in the run's vector_outputs
SERIES = {
    "rpk": "rpk",
    "rpk_no_elasticity": "rpk_no_elasticity",
    "ask": "ask",
    "airfare_per_rpk": "airfare_per_rpk",
    "total_cost_per_rpk": "total_cost_per_rpk",
    "co2_emissions": "co2_emissions",
    "cumulative_co2_emissions": "cumulative_co2_emissions",
    "biofuel_mandate_share": "generic_biofuel_mandate_share",
    "electrofuel_mandate_share": "generic_electrofuel_mandate_share",
    "biofuel_energy": "generic_biofuel_energy_consumption",
    "electrofuel_energy": "generic_electrofuel_energy_consumption",
    "dropin_energy": "energy_consumption_dropin_fuel",
    "biomass_allocated_share": "generic_biomass_consumed_aviation_allocated_share",
    "electricity_allocated_share": "generic_electricity_consumed_aviation_allocated_share",
    "area_loss": "area_loss",
    "total_airline_cost": "total_airline_cost",
    "cumulative_total_airline_cost_discounted": "cumulative_total_airline_cost_discounted",
    "cumulative_total_surplus_loss_discounted": "cumulative_total_surplus_loss_discounted",
}

CONSTRAINTS = {
    "blend_completeness": None,
    "biomass": None,
    "electricity": None,
    "biofuel_ramp": None,
    "electrofuel_ramp": None,
}

# A constraint counts as active when its violation is within this of zero. The runs
# stop on a KKT residual, so a genuinely active constraint lands within ~1e-6; the
# looser bound here keeps a constraint that the solver left a hair slack from being
# reported as non-binding.
ACTIVE_TOL = 1e-4


def _load(name):
    path = RESULTS / f"{name}.json"
    if not path.exists():
        return None
    data = json.load(open(path))
    return data["vector_outputs"], data["float_outputs"], data["float_inputs"]


def by_year():
    frames = []
    for run_id, spec in RUNS.items():
        loaded = _load(run_id)
        if loaded is None:
            continue
        vectors, _, _ = loaded
        columns = {}
        for label, key in SERIES.items():
            columns[label] = pd.Series(vectors[key], index=YEARS) if key in vectors else np.nan
        frame = pd.DataFrame(columns, index=YEARS)
        frame.insert(0, "run", run_id)
        frame.insert(1, "block", spec["block"])
        frame.insert(2, "year", YEARS)
        frames.append(frame.loc[2019:2050])
    return pd.concat(frames, ignore_index=True)


def constraints_table():
    from preflight import constraints_of

    rows = []
    for run_id, spec in RUNS.items():
        if not (RESULTS / f"{run_id}.json").exists():
            continue
        _, _, floats = _load(run_id)
        frame = constraints_of(
            RESULTS / f"{run_id}.json",
            rate=floats["rate_ramp_up_constraint_biofuel"],
            volume=floats["volume_ramp_up_constraint_biofuel"],
            biomass_share=floats["generic_biomass_availability_aviation_allocated_share"]
            / R.EU_ASK_SHARE,
        )
        dropped = spec.get("drop_constraints", ())
        for year in OPTIM_YEARS:
            for name in frame.columns:
                # A dropped constraint is absent from the problem, not satisfied by it.
                # Its recomputed value is still informative -- it says what the run
                # would have violated had the limit been there -- so it is reported
                # with in_problem=False rather than left out.
                in_problem = not (
                    name == "electricity" and "electricity_trajectory_constraint" in dropped
                )
                value = float(frame.loc[year, name])
                rows.append(
                    {
                        "run": run_id,
                        "block": spec["block"],
                        "constraint": name,
                        "year": year,
                        "value": value,
                        "slack": -value,
                        "active": bool(abs(value) <= ACTIVE_TOL) and in_problem,
                        "violated": bool(value > ACTIVE_TOL) and in_problem,
                        "in_problem": in_problem,
                    }
                )
    return pd.DataFrame(rows)


def summary():
    frame = rebuild_summary()
    if frame.empty:
        return frame

    costs = []
    for run_id, spec in RUNS.items():
        run = _load(run_id)
        ref = _load(reference_key(spec))
        if run is None or ref is None:
            costs.append({"run": run_id, "reference": reference_key(spec)})
            continue
        key = (
            "cumulative_total_airline_cost_discounted"
            if spec.get("no_feedback")
            else "cumulative_total_surplus_loss_discounted"
        )
        run_value = pd.Series(run[0][key], index=YEARS).loc[2050]
        ref_value = pd.Series(ref[0][key], index=YEARS).loc[2050]
        cumulative = pd.Series(run[0]["cumulative_co2_emissions"], index=YEARS).loc[2050]
        rpk = pd.Series(run[0]["rpk"], index=YEARS)
        bio = pd.Series(run[0]["generic_biofuel_mandate_share"], index=YEARS)
        ele = pd.Series(run[0]["generic_electrofuel_mandate_share"], index=YEARS)
        costs.append(
            {
                "run": run_id,
                "reference": reference_key(spec),
                "measured_on": key,
                "scenario_bnEUR": run_value / 1e9,
                "reference_bnEUR": ref_value / 1e9,
                "policy_cost_bnEUR": (run_value - ref_value) / 1e9,
                "cumulative_co2_GtCO2": cumulative,
                "aaf_share_2030": bio.loc[2030] + ele.loc[2030],
                "aaf_share_2040": bio.loc[2040] + ele.loc[2040],
                "aaf_share_2050": bio.loc[2050] + ele.loc[2050],
                "biofuel_share_2050": bio.loc[2050],
                "electrofuel_share_2050": ele.loc[2050],
                "rpk_2050_Tpkm": rpk.loc[2050] / 1e12,
                "rpk_cagr_2019_2050_pct": 100 * ((rpk.loc[2050] / rpk.loc[2019]) ** (1 / 31) - 1),
            }
        )
    return frame.merge(pd.DataFrame(costs), on="run", how="outer")


def main():
    HERE.mkdir(exist_ok=True)

    years = by_year()
    years.to_csv(HERE / "sweep_by_year.csv", index=False)
    print(f"sweep_by_year.csv       {len(years)} rows, {years.run.nunique()} runs")

    table = constraints_table()
    table.to_csv(HERE / "sweep_constraints.csv", index=False)
    print(f"sweep_constraints.csv   {len(table)} rows")

    frame = summary()
    frame.to_csv(HERE / "sweep_summary.csv", index=False)
    print(f"sweep_summary.csv       {len(frame)} rows")

    missing = frame[frame.policy_cost_bnEUR.isna()] if "policy_cost_bnEUR" in frame else frame
    if len(missing):
        print(f"\n  no matched reference yet for: {list(missing.run)}")

    print("\n=== headline ===")
    show = [
        "run",
        "block",
        "feasible",
        "aaf_share_2050",
        "electrofuel_share_2050",
        "rpk_2050_Tpkm",
        "policy_cost_bnEUR",
        "n_evaluations",
        "message",
    ]
    view = frame[[c for c in show if c in frame]].copy()
    if "message" in view:
        view["stopped_on"] = (
            view.pop("message").str.contains("KKT").map({True: "KKT", False: "OTHER"})
        )
    print(view.to_string(index=False, float_format=lambda v: f"{v:.3f}"))


if __name__ == "__main__":
    main()

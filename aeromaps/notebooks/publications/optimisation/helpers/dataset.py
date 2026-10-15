"""The paper's results as a small dataset, and the readers that 02_results draws from.

Every figure of ``02_results.ipynb`` is drawn from the four files in ``dataset/``, not
from the raw runs: a reader who only wants to look at the scenarios needs nothing else,
and one who re-runs the optimisations rebuilds the dataset from them with

    poetry run python -m helpers.dataset      # from the paper folder

which reads, for each run the article uses (``SCENARIOS``), its raw outputs under
``runs/results_sensitivities`` or ``runs/results_carbon_biomass_grid`` -- one JSON of model outputs and, for an
optimisation, one HDF of its history -- and writes

    scenarios.csv    one row per run: what kind of run it is, its parameters, and
                     whether the optimum it reports is feasible
    timeseries.csv   IAMC layout -- model, scenario, region, variable, unit, then one
                     column per year 2000-2050 -- for the variables in VARIABLES
    optima.csv       per optimisation, the point GEMSEO reports as its optimum: the
                     design variables and every constraint value there
    variables.csv    the variables, with units and descriptions

Values are written in Python's shortest round-trip form and read back with pandas'
round-trip parser, so the dataset reproduces the raw runs bit for bit, and the figures
with it.

One subtlety the dataset inherits rather than resolves. ``timeseries.csv`` holds the
outputs of SLSQP's final iterate -- what the raw JSON holds -- while ``optima.csv`` and
``feasible`` describe GEMSEO's ``x_opt``, read from the HDF. In 14 of the 74
optimisations the two are different iterates; see ``setup_optimisation`` in
``helpers/optimisation_runs.py`` for why the final iterate is the one the paper reports.
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

PAPER = Path(__file__).resolve().parent.parent
DATA_DIR = PAPER / "dataset"
RAW = PAPER / "runs"

YEARS = range(2000, 2051)
OPTIM_YEARS = [2030, 2035, 2040, 2045, 2050]
EU_ASK_SHARE = 15.49 / 100

MODEL = "AeroMAPS"
REGION = "EU"  # every run is downscaled to the EU perimeter by EU_ASK_SHARE

# Everything 02_results and the sweep plots read, then a few totals a reader will want.
# Units checked against the model code; "drop-in blend" is drop-in fuel energy.
VARIABLES = {
    # Traffic and prices
    "rpk": ("pkm/yr", "Revenue passenger kilometres"),
    "rpk_no_elasticity": ("pkm/yr", "Revenue passenger kilometres before the price response"),
    "ask": ("ASK/yr", "Available seat kilometres"),
    "airfare_per_rpk": ("EUR/pkm", "Airfare per revenue passenger kilometre"),
    "total_cost_per_rpk": ("EUR/pkm", "Airline cost per revenue passenger kilometre"),
    "doc_energy_per_ask_mean": ("EUR/ASK", "Fleet-mean energy direct operating cost per ASK"),
    "doc_total_per_ask_mean": ("EUR/ASK", "Fleet-mean total direct operating cost per ASK"),
    "total_airline_cost": ("EUR/yr", "Total airline cost"),
    "total_airline_cost_increase": ("EUR/yr", "Airline cost increase against 2019 unit costs"),
    # Economic objective
    "area_loss": ("EUR/yr", "Passenger surplus loss: area under the demand curve"),
    "cumulative_total_surplus_loss_discounted": (
        "EUR",
        "Cumulative total surplus loss from 2020, discounted to 2020 (the objective)",
    ),
    # Emissions
    "co2_emissions_including_energy": ("MtCO2/yr", "CO2 emissions, all levers applied"),
    "co2_emissions_passenger": ("MtCO2/yr", "CO2 emissions of passenger traffic"),
    "co2_emissions_freight": ("MtCO2/yr", "CO2 emissions of freight traffic"),
    "co2_emissions_last_historical_year_technology_baseline3": (
        "MtCO2/yr",
        "CO2 emissions with 2019 technology flying the scenario's traffic",
    ),
    "cumulative_co2_emissions": ("GtCO2", "Cumulative CO2 emissions from 2020"),
    # Energy
    "energy_consumption": ("MJ/yr", "Total energy consumption"),
    "energy_consumption_dropin_fuel": ("MJ/yr", "Drop-in fuel energy consumption"),
    "generic_biofuel_energy_consumption": ("MJ/yr", "Biofuel energy consumption"),
    "generic_electrofuel_energy_consumption": ("MJ/yr", "Electrofuel energy consumption"),
    "fossil_kerosene_share_dropin_fuel": ("%", "Fossil kerosene share of the drop-in blend"),
    "generic_biofuel_share_dropin_fuel": ("%", "Biofuel share of the drop-in blend"),
    "generic_electrofuel_share_dropin_fuel": ("%", "Electrofuel share of the drop-in blend"),
    "generic_biofuel_mandate_share": ("%", "Biofuel mandate, share of the drop-in blend"),
    "generic_electrofuel_mandate_share": ("%", "Electrofuel mandate, share of the drop-in blend"),
    # Fuel costs and emission factors
    "fossil_kerosene_mean_mfsp": ("EUR/MJ", "Fossil kerosene minimum fuel selling price"),
    "generic_biofuel_mean_mfsp": ("EUR/MJ", "Biofuel minimum fuel selling price"),
    "generic_electrofuel_mean_mfsp": ("EUR/MJ", "Electrofuel minimum fuel selling price"),
    "fossil_kerosene_mean_mfsp_without_resource": (
        "EUR/MJ",
        "Fossil kerosene MFSP, excluding resource cost",
    ),
    "generic_biofuel_mean_mfsp_without_resource": (
        "EUR/MJ",
        "Biofuel MFSP, excluding resource cost",
    ),
    "generic_electrofuel_mean_mfsp_without_resource": (
        "EUR/MJ",
        "Electrofuel MFSP, excluding resource cost",
    ),
    "fossil_kerosene_mean_co2_emission_factor": ("gCO2/MJ", "Fossil kerosene emission factor"),
    "generic_biofuel_mean_co2_emission_factor": ("gCO2/MJ", "Biofuel emission factor"),
    "generic_electrofuel_mean_co2_emission_factor": ("gCO2/MJ", "Electrofuel emission factor"),
    "fossil_kerosene_mean_co2_emission_factor_without_resource": (
        "gCO2/MJ",
        "Fossil kerosene emission factor, excluding resource emissions",
    ),
    "generic_biofuel_mean_co2_emission_factor_without_resource": (
        "gCO2/MJ",
        "Biofuel emission factor, excluding resource emissions",
    ),
    "generic_electrofuel_mean_co2_emission_factor_without_resource": (
        "gCO2/MJ",
        "Electrofuel emission factor, excluding resource emissions",
    ),
    # Resources
    "biomass_availability_aviation_allocated": ("MJ/yr", "Biomass allocated to aviation"),
    "electricity_availability_aviation_allocated": ("MJ/yr", "Electricity allocated to aviation"),
    "generic_biomass_consumed_global_share": ("%", "Biomass consumed, share of world supply"),
}

# The vector constraints of the problem, in the order the figures show them.
CONSTRAINTS = [
    "blend_completeness_constraint",
    "biomass_trajectory_constraint",
    "electricity_trajectory_constraint",
    "biofuel_use_growth_constraint",
    "electrofuel_use_growth_constraint",
]
CARBON_CONSTRAINT = "aviation_carbon_budget_constraint"

FLOAT_OUTPUTS = ["carbon_budget_consumed_share", CARBON_CONSTRAINT]

CASE_LABELS = {
    "main": "Reference",
    "B5": "5 % biomass",
    "B75": "7.5 % biomass",
    "B15": "15 % biomass",
    "pess": "Pessimistic technology",
}
BUDGET_TAGS = ["3_8", "3_6", "3_4", "3_2", "3_0", "2_8", "2_6", "2_4", "2_2", "2_0"]
SENSITIVITIES = [
    "base",
    "eps_m0_6",
    "eps_m0_8",
    "eps_m1_0",
    "eps_m1_4",
    "fixed_demand",
    "rate_11_8",
    "rate_39",
    "vol_0_1",
    "vol_0_4",
    "efuel_wind",
    "r_3_2",
    "r_7",
    "r_15",
]

# Every run the article draws on, with the folder under runs/ that holds its raw output.
SCENARIOS = {
    # the carbon-budget ladder of each case, its minimum-CO2 end, and the case at the
    # ReFuelEU-equivalent budget
    **{
        f"opt_{case}_{tag}": "results_carbon_biomass_grid"
        for case in CASE_LABELS
        for tag in [*BUDGET_TAGS, "mincarb", "refueleu"]
    },
    # one-parameter sensitivities around base, at the ReFuelEU-equivalent budget
    **{run: "results_sensitivities" for run in SENSITIVITIES},
    # fixed-mandate references
    "fossil_main": "results_carbon_biomass_grid",
    "fossil_pess": "results_carbon_biomass_grid",
    "refueleu_main": "results_carbon_biomass_grid",
    "refueleu_step": "results_sensitivities",
}


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #


REFERENCE_LABELS = {
    "fossil_main": "Reference, fossil BAU (no optimisation)",
    "fossil_pess": "Pessimistic technology, fossil BAU (no optimisation)",
    "refueleu_main": "Reference, ReFuelEU mandate interpolated linearly (no optimisation)",
    "refueleu_step": "Reference, ReFuelEU mandate held in steps (no optimisation)",
}


def _describe(scenario):
    """Family, case, objective and label of one run."""
    if scenario in REFERENCE_LABELS:
        case = "pess" if scenario.endswith("pess") else "main"
        return "reference", case, "none", REFERENCE_LABELS[scenario]
    if scenario in SENSITIVITIES:
        sys.path.insert(0, str(RAW))
        from run_batch import RUNS

        spec = RUNS[scenario]
        objective = "cost" if spec.get("no_feedback") else "surplus"
        return f"sensitivity {spec['block']}", "main", objective, spec["label"]
    _, case, tag = scenario.split("_", 2)
    case_label = CASE_LABELS[case]
    if tag == "mincarb":
        return "budget ladder", case, "carbon", f"{case_label}, minimum CO2"
    if tag == "refueleu":
        return "central budget", case, "surplus", f"{case_label}, ReFuelEU-equivalent budget"
    budget = tag.replace("_", ".")
    return "budget ladder", case, "surplus", f"{case_label}, {budget} % of world budget"


def _optimum(hdf):
    """GEMSEO's optimum from a run's history: design, constraint values, feasibility."""
    from gemseo.algos.optimization_problem import OptimizationProblem

    try:
        optimum = OptimizationProblem.from_hdf(str(hdf)).optimum
    except Exception:
        return None
    return optimum


def export(out_dir=DATA_DIR):
    """Write the four dataset files from the raw runs. See the module docstring."""
    import logging
    import warnings

    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scenarios, series, optima = [], [], []

    for scenario, folder in SCENARIOS.items():
        path = RAW / folder / f"{scenario}.json"
        data = json.load(open(path))
        family, case, objective, label = _describe(scenario)
        inputs, floats = data["float_inputs"], data.get("float_outputs", {})
        row = {
            "scenario": scenario,
            "source": f"runs/{folder}",
            "family": family,
            "case": case,
            "objective": objective,
            "label": label,
            "carbon_budget_world_share_pct": inputs["aviation_carbon_budget_objective"]
            / EU_ASK_SHARE,
            "biomass_world_share_pct": inputs[
                "generic_biomass_availability_aviation_allocated_share"
            ]
            / EU_ASK_SHARE,
            "electricity_world_share_pct": inputs[
                "generic_electricity_availability_aviation_allocated_share"
            ]
            / EU_ASK_SHARE,
            "price_elasticity": inputs.get("price_elasticity", np.nan),
            "ramp_rate_cap": inputs["rate_ramp_up_constraint_biofuel"],
            "ramp_volume_cap_EJ_per_yr": inputs["volume_ramp_up_constraint_biofuel"] / EU_ASK_SHARE,
            "social_discount_rate": inputs["social_discount_rate"],
            "efuel_pathway": "dedicated wind" if scenario == "efuel_wind" else "grid",
            "feasible": np.nan,
            **{name: floats.get(name, np.nan) for name in FLOAT_OUTPUTS},
        }

        optimum = _optimum(path.with_suffix(".hdf")) if path.with_suffix(".hdf").exists() else None
        if optimum is not None:
            row["feasible"] = bool(optimum.is_feasible)
            values = optimum.constraints or {}
            for name in CONSTRAINTS:
                if name in values:
                    component = np.ravel(np.asarray(values[name], dtype=float))
                    if component.size == len(OPTIM_YEARS):
                        optima += [
                            (scenario, name, year, value)
                            for year, value in zip(OPTIM_YEARS, component)
                        ]
            if CARBON_CONSTRAINT in values:
                optima.append(
                    (
                        scenario,
                        CARBON_CONSTRAINT,
                        np.nan,
                        np.ravel(values[CARBON_CONSTRAINT])[0],
                    )
                )
            x = np.ravel(np.asarray(optimum.design, dtype=float))
            for pathway, part in (("electrofuel", x[:5]), ("biofuel", x[5:])):
                optima += [
                    (scenario, f"{pathway}_design", year, value)
                    for year, value in zip(OPTIM_YEARS, part)
                ]
        scenarios.append(row)

        vectors = data["vector_outputs"]
        for variable, (unit, _) in VARIABLES.items():
            values = vectors.get(variable)
            if isinstance(values, list) and len(values) == len(YEARS):
                series.append([MODEL, scenario, REGION, variable, unit, *values])

    pd.DataFrame(scenarios).to_csv(out_dir / "scenarios.csv", index=False)
    pd.DataFrame(
        series, columns=["model", "scenario", "region", "variable", "unit", *map(str, YEARS)]
    ).to_csv(out_dir / "timeseries.csv", index=False)
    pd.DataFrame(optima, columns=["scenario", "quantity", "year", "value"]).astype(
        {"year": "Int64"}
    ).to_csv(out_dir / "optima.csv", index=False)
    pd.DataFrame(
        [(name, unit, description) for name, (unit, description) in VARIABLES.items()],
        columns=["variable", "unit", "description"],
    ).to_csv(out_dir / "variables.csv", index=False)
    print(
        f"{len(scenarios)} scenarios, {len(series)} series, {len(optima)} optimum values -> {out_dir}"
    )


# --------------------------------------------------------------------------- #
# Readers
# --------------------------------------------------------------------------- #


def _read(name):
    return pd.read_csv(DATA_DIR / name, float_precision="round_trip")


@lru_cache(maxsize=None)
def scenarios():
    """One row per run, indexed by scenario name."""
    return _read("scenarios.csv").set_index("scenario")


@lru_cache(maxsize=None)
def _timeseries():
    frame = _read("timeseries.csv")
    return {
        scenario: group.set_index("variable")[list(map(str, YEARS))]
        for scenario, group in frame.groupby("scenario")
    }


@lru_cache(maxsize=None)
def _optima():
    return {scenario: group for scenario, group in _read("optima.csv").groupby("scenario")}


def exists(scenario):
    return scenario in scenarios().index


def outputs(scenario):
    """The run's variables as {name: list over 2000-2050}, as the raw JSON holds them."""
    frame = _timeseries()[scenario]
    return {variable: list(row.to_numpy(dtype=float)) for variable, row in frame.iterrows()}


def load(scenario):
    """``(vector_outputs_frame, float_outputs_dict)``, as ``optimisation_runs.load``."""
    frame = _timeseries()[scenario]
    vectors = {
        variable: pd.Series(row.to_numpy(dtype=float), index=YEARS)
        for variable, row in frame.iterrows()
    }
    row = scenarios().loc[scenario]
    return pd.DataFrame(vectors), {name: row[name] for name in FLOAT_OUTPUTS}


def discount_rate(scenario):
    return float(scenarios().loc[scenario, "social_discount_rate"])


def feasible(scenario):
    """Whether GEMSEO's optimum is feasible; None for a run that is not an optimisation."""
    value = scenarios().loc[scenario, "feasible"]
    return None if pd.isna(value) else bool(value)


def read_constraints(scenario):
    """A run's optimum as ``constraints`` / ``carbon`` / ``mandate`` / ``feasible``.

    The same structure as ``optimisation_runs.read_constraints``, or None for a run
    that is not an optimisation.
    """
    rows = _optima().get(scenario)
    if rows is None:
        return None
    by_quantity = {q: group.sort_values("year") for q, group in rows.groupby("quantity")}
    constraints = pd.DataFrame(
        {
            name: by_quantity[name]["value"].to_numpy(dtype=float)
            for name in CONSTRAINTS
            if name in by_quantity
        },
        index=OPTIM_YEARS,
    )
    carbon = by_quantity.get(CARBON_CONSTRAINT)
    return {
        "constraints": constraints,
        "carbon": float(carbon["value"].iloc[0]) if carbon is not None else np.nan,
        "mandate": pd.DataFrame(
            {
                pathway: by_quantity[f"{pathway}_design"]["value"].to_numpy(dtype=float)
                for pathway in ("electrofuel", "biofuel")
            },
            index=OPTIM_YEARS,
        ),
        "feasible": feasible(scenario),
    }


if __name__ == "__main__":
    export()

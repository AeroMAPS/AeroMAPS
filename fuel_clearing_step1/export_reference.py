"""Export the step-1 reference run: the current mode, as the market must reproduce it.

Runs the two-region bench (``scenario/regionalisation.yaml``) in ``unified_mda`` with
fuel shares fixed, not optimised, and every pathway on the top-down cost model. Writes
what the ``clear_market`` kernel needs as inputs and what test 3.3.c compares against.

Deliberately NOT a pytest fixture generator: it is a one-shot export whose output is
committed, so the kernel's tests do not depend on a 2-region MDA converging.

Usage::

    poetry run python -m fuel_clearing_step1.export_reference

Outputs (see ``metadata.json`` for units and provenance):

``reference.parquet``
    One row per (region, year) over the FULL year index, historical included --
    the market has to reproduce the historical years identically, so it needs to
    see them. Columns are the demand, per-pathway volumes, per-pathway MFSP, the
    aircraft-type mean MFSP, and the mandate shares that produced the volumes.

``metadata.json``
    Commit, config path, units, year boundaries, pathway roles, and the measured
    closure of the energy-balance invariant.
"""

from __future__ import annotations

import json
import logging
import subprocess
import warnings
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# The bench scripts under spike_unified_mda/ silence warnings at import; several of
# the invariants this export checks are guarded by `warnings.warn` and nothing else,
# so anything imported above must not be allowed to keep them off (brief section 2.2).
warnings.resetwarnings()
warnings.simplefilter("default")

logging.disable(logging.INFO)

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CONFIG = HERE / "scenario" / "regionalisation.yaml"
OUT_DIR = REPO / "aeromaps" / "tests" / "fixtures" / "fuel_clearing"

# Pathway roles for step 1. `default` is the residual that closes the energy balance
# in EnergyUseChoice; `sustainable` is what the mandate counts (is_sustainable in the
# kernel). Kept explicit rather than re-read from the yaml so the fixture states the
# role its tests assume.
SUSTAINABLE = ["hefa_fog"]
DEFAULT_PATHWAY = "fossil_kerosene"
PATHWAYS = SUSTAINABLE + [DEFAULT_PATHWAY]

AIRCRAFT_TYPE = "dropin_fuel"
DEMAND_VAR = f"energy_consumption_{AIRCRAFT_TYPE}"

UNITS = {
    "energy_demand": "MJ",
    "energy_consumption": "MJ",
    "mean_mfsp": "EUR/MJ",
    "mandate_share": "percent of aircraft-type energy",
}


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    except subprocess.CalledProcessError:  # pragma: no cover - not a git checkout
        return "unknown"


def _git_dirty() -> bool:
    try:
        return bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip()
        )
    except subprocess.CalledProcessError:  # pragma: no cover
        return True


def run_reference():
    """Build and solve the reference scenario. Returns the process."""
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    process = MultiRegionalProcess(str(CONFIG))
    process.compute()
    return process


def extract(process) -> tuple[pd.DataFrame, dict]:
    """Pull the market-relevant series out of the solved process, and check closure."""
    vector_outputs = process.data["vector_outputs"]
    regions = process.list_regions()

    frames = []
    closure = {}

    for region in regions:

        def series(name: str) -> pd.Series:
            return vector_outputs[f"{region}:{name}"]

        frame = pd.DataFrame(index=vector_outputs.index)
        frame.index.name = "year"
        frame["region"] = region
        frame["energy_demand"] = series(DEMAND_VAR)

        for pathway in PATHWAYS:
            frame[f"{pathway}_energy_consumption"] = series(f"{pathway}_energy_consumption")
            frame[f"{pathway}_mean_mfsp"] = series(f"{pathway}_mean_mfsp")
            frame[f"{pathway}_share_{AIRCRAFT_TYPE}"] = series(f"{pathway}_share_{AIRCRAFT_TYPE}")

        frame[f"{AIRCRAFT_TYPE}_mean_mfsp"] = series(f"{AIRCRAFT_TYPE}_mean_mfsp")

        # The invariant nothing downstream checks (INVENTORY.md section 3.1). Measured
        # here rather than asserted, so the fixture records how exactly the current
        # mode closes it -- that number is the tolerance test 3.3.c is entitled to.
        total = sum(frame[f"{p}_energy_consumption"].fillna(0) for p in PATHWAYS)
        demand = frame["energy_demand"].fillna(0)
        gap = (total - demand).abs()
        scale = demand.abs().replace(0, pd.NA)
        closure[region] = {
            "max_absolute_gap_MJ": float(gap.max()),
            "max_relative_gap": float((gap / scale).max(skipna=True)),
        }

        frames.append(frame.reset_index())

    table = pd.concat(frames, ignore_index=True)
    table = table[["region", "year"] + [c for c in table.columns if c not in ("region", "year")]]
    return table, closure


def main() -> None:
    process = run_reference()
    table, closure = extract(process)

    reference_process = process.regional_processes[process.list_regions()[0]]
    prospection_start = int(reference_process.parameters.prospection_start_year)
    # The ramp-up's initial condition q_init is the sustainable volume of the last year
    # the market does NOT act on -- i.e. the year before prospection starts.
    last_historical = prospection_start - 1
    end_year = int(reference_process.parameters.end_year)

    # The current mode emits NaN -- not zero -- for a non-default pathway over the
    # historical years, because the mandate share series is undefined there and
    # `share/100 * demand` propagates it (see the `historical_nan` block below).
    # Decision 9 forbids the kernel ever seeing a NaN, so q_init is coerced to 0.0 and
    # the coercion is recorded rather than hidden.
    q_init = {}
    q_init_was_nan = {}
    for region in process.list_regions():
        row = table[(table["region"] == region) & (table["year"] == last_historical)]
        raw = {p: float(row[f"{p}_energy_consumption"].iloc[0]) for p in PATHWAYS}
        q_init_was_nan[region] = [p for p, v in raw.items() if pd.isna(v)]
        q_init[region] = {p: (0.0 if pd.isna(v) else v) for p, v in raw.items()}

    # Where the reference is NaN, per column, so the kernel's tests know which
    # differences against it are expected rather than regressions.
    historical_nan = {}
    for region in process.list_regions():
        block = table[table["region"] == region].set_index("year").loc[:last_historical]
        nan_cols = {c: int(block[c].isna().sum()) for c in block.columns if block[c].isna().any()}
        historical_nan[region] = nan_cols

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_parquet(OUT_DIR / "reference.parquet", index=False)

    metadata = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_by": "fuel_clearing_step1/export_reference.py",
        "commit": _git_commit(),
        "working_tree_dirty": _git_dirty(),
        "config": str(CONFIG.relative_to(REPO)),
        "execution_mode": "unified_mda",
        "regions": list(process.list_regions()),
        "years": {
            "first": int(table["year"].min()),
            "last_historical": last_historical,
            "prospection_start": prospection_start,
            "end": end_year,
        },
        "aircraft_type": AIRCRAFT_TYPE,
        "pathways": {
            "all": PATHWAYS,
            "sustainable": SUSTAINABLE,
            "default_residual": DEFAULT_PATHWAY,
        },
        "cost_model": "top-down",
        "shares": "fixed (mandate shares from the carriers yaml), NOT optimised",
        "units": UNITS,
        # q_init for the ramp-up: sustainable production in the last historical year.
        "q_init_MJ": q_init,
        "q_init_coerced_from_nan": q_init_was_nan,
        # The current mode's NaN footprint over the historical years. The market emits
        # zeros there (decision 9), so these columns are exactly where the two modes
        # cannot be bit-identical -- section 4.2's guard-rail has to allow for it.
        "historical_nan_columns": historical_nan,
        # How exactly the current mode closes the energy balance. The market's own
        # closure step (brief section 3.2) must not need a larger correction than this.
        "energy_balance_closure": closure,
        "columns": list(table.columns),
    }
    # allow_nan=False: a bare NaN is not valid JSON, and a metadata file that no
    # strict parser can read would be found only by whoever needs it most.
    (OUT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")

    print(f"wrote {OUT_DIR / 'reference.parquet'}  ({len(table)} rows)")
    print(f"wrote {OUT_DIR / 'metadata.json'}")
    for region, stats in closure.items():
        print(
            f"  {region}: energy-balance gap "
            f"max {stats['max_absolute_gap_MJ']:.4g} MJ "
            f"({stats['max_relative_gap']:.3g} relative)"
        )


if __name__ == "__main__":
    main()

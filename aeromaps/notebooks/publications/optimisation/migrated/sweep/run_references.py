"""Fossil-BAU references matched to each run's parameters.

``cumulative_total_surplus_loss_discounted`` is measured against 2019 unit economics
applied to the exogenous traffic trajectory, not against a no-policy scenario. Unit
costs fall over the horizon, so that quantity is negative for every scenario in this
batch -- fossil BAU included, at -194 bn EUR. Only *differences* against a reference
are policy costs, and the reference has to share the run's parameters: the discount
rate rescales the whole series, and the elasticity moves the traffic it is summed over.

Without this, block D reads as a 1.6 bn EUR swing between r = 3.2 % and r = 7 % when
almost all of that is the mechanical effect of discounting on a quantity that is
negative to begin with.

Eight references cover the thirteen runs: five elasticities, the no-feedback
formulation, and the two off-baseline discount rates. Ramp-up caps, biomass share and
the electrofuel pathway need no reference of their own -- fossil BAU burns no
alternative fuel, so none of them changes it.

Usage:  poetry run python run_references.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
sys.path.insert(0, str(PAPER))
sys.path.insert(0, str(HERE))

import optimisation_runs as R  # noqa: E402
from run_batch import BIOMASS_SHARE, RUNS  # noqa: E402

RESULTS = HERE / "results"
YEARS = list(range(2000, 2051))


def reference_key(spec):
    """The reference a run must be compared against."""
    if spec.get("no_feedback"):
        return "ref_fossil_nofeedback"
    elasticity = spec.get("elasticity", -0.9)
    discount = spec.get("discount", 0.045)
    if discount != 0.045:
        return f"ref_fossil_r{discount:g}".replace(".", "_")
    return f"ref_fossil_eps{elasticity:g}".replace(".", "_").replace("-", "m")


def spec_of(key):
    """Invert reference_key: the parameters that reference must be run with."""
    for spec in RUNS.values():
        if reference_key(spec) == key:
            return spec
    raise KeyError(key)


def run_reference(key):
    stem = RESULTS / key
    if stem.with_suffix(".json").exists():
        print(f"  {key}: on disk, skipped")
        return

    from aeromaps.core.gemseo import disable_gemseo_execution_statistics

    disable_gemseo_execution_statistics()
    os.chdir(PAPER)

    spec = spec_of(key)
    no_feedback = bool(spec.get("no_feedback"))
    config = "config_rte_nofeedback.yaml" if no_feedback else "config_rte.yaml"

    process = R.build_process(
        "main", config=config, optimisation=False, carbon_budget=3.119357596335
    )
    process.parameters.generic_biomass_availability_aviation_allocated_share = (
        BIOMASS_SHARE * R.EU_ASK_SHARE
    )
    if "elasticity" in spec and not no_feedback:
        process.parameters.price_elasticity = spec["elasticity"]
    if "discount" in spec:
        process.parameters.social_discount_rate = spec["discount"]

    # Fossil BAU: no mandate at all. The 2025 leading entry is zeroed along with the
    # design years -- leaving biofuel at 2 % in 2025 and 0 % after would take its
    # pathway share from positive back to zero, the 0/0 that kills the MDA on NaN.
    process.parameters.generic_biofuel_mandate_share_values_fixed = [0.0, 0.0]
    process.parameters.generic_electrofuel_mandate_share_values_fixed = [0.0, 0.0]
    R.set_mandate(process, biofuel=[0.0] * 5, electrofuel=[0.0] * 5)

    started = time.perf_counter()
    process.compute()
    RESULTS.mkdir(exist_ok=True)
    process.write_json(str(stem.with_suffix(".json")))
    print(f"  {key}: written ({time.perf_counter() - started:.0f} s)")


def main():
    keys = []
    for spec in RUNS.values():
        key = reference_key(spec)
        if key not in keys:
            keys.append(key)
    print(f"=== {len(keys)} matched fossil-BAU references for {len(RUNS)} runs ===")
    for key in keys:
        run_reference(key)

    print("\n=== mapping ===")
    table = pd.DataFrame(
        [{"run": run_id, "reference": reference_key(spec)} for run_id, spec in RUNS.items()]
    )
    print(table.to_string(index=False))
    table.to_csv(HERE / "run_reference_map.csv", index=False)


if __name__ == "__main__":
    main()

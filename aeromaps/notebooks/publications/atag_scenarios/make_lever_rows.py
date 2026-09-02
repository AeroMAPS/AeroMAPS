"""
make_lever_rows
================
Build and run the standalone single-lever scenarios that Table 2 needs beyond
the technology runs T0-T4: the operations levels O2 and O3, and the fuel levels
F1, F2 and F3.

Why these did not already exist: the operations and SAF columns of Table 2 used
to be read from the sweep grid (``3rd_edition_variants``), whose cells inherit
S1's full configuration, load factor included. Load factor rises from 82.6 to
88.4 % under S1, so the sweep's "T1" carried 5.8 points of load-factor gain that
the standalone T1 run does not, and its operations column read the drift rather
than the operations lever. Reading every row of Table 2 from a standalone run
fixes that, at the cost of five runs that did not exist: O1 and F0 already
coincide with T1 (zero operations gain, no drop-in SAF), so only five new cells
are needed.

Each run starts from T1 -- technology-only, zero operations gain, no drop-in
SAF -- and changes exactly one thing:

O2, O3
    Operations gain and load factor together, since the reports bundle both
    into the operations pillar. O3 is pinned to S1's own published endpoint,
    88.389 %; O2 is the arithmetic midpoint between the reports' two published
    endpoints, 82.4 and 88.389 %, since no intermediate value exists to read.

    Note that O1 is *not* the reports' 82.4 %. The technology runs hold the load
    factor flat at its last observed value instead, so that a row with no
    operations lever reports no operations wedge; see the note beside
    O1_LOAD_FACTOR below.
F1, F2, F3
    The energy carrier file alone, reusing the same files the sweep already
    validates against S0's and S1's and S2's own fuel deployment: F1 the light
    edition's single generic carrier, F2 and F3 the full edition's per-pathway
    files. Nothing else changes, so any difference between these rows and T1
    is attributable to the fuel lever alone.

Run from this directory, once the T1 technology run exists::

    python make_lever_rows.py
"""

import json
from pathlib import Path

import yaml

from aeromaps import create_process
from aeromaps.utils.scenarios import find_scenario

HERE = Path(__file__).parent
FULL = HERE / "3rd_edition_full"  # results live here
FULL_SCENARIO = find_scenario("atag_3rd_edition_full")  # its definition is packaged

# F0's energy file is T1's own, read once rather than hand-copied, so a change
# to T1 cannot leave this script quietly stale.
_T1_INPUTS = json.loads(
    (FULL_SCENARIO.path / "data_inputs" / "t1_inputs.json").read_text(encoding="utf-8")
)

# The two load factors the reports publish for their operations pillar. O2 is
# interpolated between them, since no intermediate value is given.
#
# O1_LOAD_FACTOR is deliberately *not* read from t1_inputs.json, though the two
# used to coincide. The technology runs now hold the load factor flat at its
# last observed value (82.116 %) so that a scenario with no operations lever
# reports no operations wedge; the reports' own no-improvement level is the
# pre-COVID 82.4 %, which by 2050 is a small recovery rather than a flat line.
# The operations axis stays anchored on the published pair, so reading O1 from
# the pinned technology inputs would drag the O2 midpoint to 85.25 and quietly
# redefine a lever level that the reports do specify.
O1_LOAD_FACTOR = 82.4  # published no-improvement endpoint
S1_LOAD_FACTOR = 88.389  # published operations endpoint, matches s1_inputs.json

OPERATIONS_RUNS = {
    "o2": {
        "operations_gain_reference_years": [2020, 2050],
        "operations_gain_reference_years_values": [0, 3],
        "load_factor": round((O1_LOAD_FACTOR + S1_LOAD_FACTOR) / 2, 4),
    },
    "o3": {
        "operations_gain_reference_years": [2020, 2050],
        "operations_gain_reference_years_values": [0, 6],
        "load_factor": S1_LOAD_FACTOR,
    },
}

# name -> (energy carriers file, resources file, processes file), matching the
# sweep's own SAF_LEVELS exactly so a fuel-axis row here and a sweep cell at
# the same level are the same run in every respect but technology and operations.
FUEL_RUNS = {
    "f1": (
        "../../3rd_edition_light/data_inputs/s0_energy.yaml",
        "default",
        "default",
    ),
    "f2": (
        "../data_inputs/s1_energy.yaml",
        "../data_inputs/resources.yaml",
        "../data_inputs/processes.yaml",
    ),
    "f3": (
        "../data_inputs/s2_energy.yaml",
        "../data_inputs/resources.yaml",
        "../data_inputs/processes.yaml",
    ),
}


def _base_config():
    return yaml.safe_load((FULL / "config_files" / "config_t1.yaml").read_text(encoding="utf-8"))


def write_operations_run(name, overrides):
    inputs = dict(_T1_INPUTS)
    inputs["operations_gain_reference_years"] = overrides["operations_gain_reference_years"]
    inputs["operations_gain_reference_years_values"] = overrides[
        "operations_gain_reference_years_values"
    ]
    for market in ("short_range", "medium_range", "long_range"):
        inputs[f"{market}_load_factor_end_year"] = overrides["load_factor"]
    inputs_path = FULL / "data_inputs" / f"{name}_inputs.json"
    inputs_path.write_text(json.dumps(inputs, indent=4) + "\n", encoding="utf-8")

    config = _base_config()
    config["data"]["inputs"]["json_inputs_file"] = f"../data_inputs/{name}_inputs.json"
    config["data"]["outputs"]["json_outputs_file"] = f"../data_outputs/{name}.json"
    config_path = FULL / "config_files" / f"config_{name}.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return config_path


def write_fuel_run(name, carriers_file, resources_file, processes_file):
    # No inputs.json changes: the SAF mandate lives entirely inside the energy
    # carrier YAML, so swapping the file is the whole lever.
    inputs_path = FULL / "data_inputs" / f"{name}_inputs.json"
    inputs_path.write_text(json.dumps(_T1_INPUTS, indent=4) + "\n", encoding="utf-8")

    config = _base_config()
    config["data"]["inputs"]["json_inputs_file"] = f"../data_inputs/{name}_inputs.json"
    config["data"]["outputs"]["json_outputs_file"] = f"../data_outputs/{name}.json"
    config["models"]["energy"]["energy_carriers_model_data_file"] = carriers_file
    config["models"]["energy"]["resources_model_data_file"] = resources_file
    config["models"]["energy"]["processes_model_data_file"] = processes_file
    config_path = FULL / "config_files" / f"config_{name}.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return config_path


def run(config_path):
    process = create_process(configuration_file=str(config_path))
    process.compute()
    process.write_json()
    return process


def main():
    print("O1 load factor %.4f, S1 (O3) load factor %.4f" % (O1_LOAD_FACTOR, S1_LOAD_FACTOR))
    for name, overrides in OPERATIONS_RUNS.items():
        print(
            "%s: gain -> %s, load factor -> %.4f"
            % (
                name.upper(),
                overrides["operations_gain_reference_years_values"],
                overrides["load_factor"],
            )
        )
        config_path = write_operations_run(name, overrides)
        run(config_path)

    for name, (carriers, resources, processes) in FUEL_RUNS.items():
        print("%s: energy -> %s" % (name.upper(), carriers))
        config_path = write_fuel_run(name, carriers, resources, processes)
        run(config_path)

    print("done")


if __name__ == "__main__":
    main()

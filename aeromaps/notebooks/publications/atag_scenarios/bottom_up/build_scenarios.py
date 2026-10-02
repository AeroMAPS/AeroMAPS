"""
build_scenarios
===============
Write the bottom-up variants of the ATAG scenarios S0, S1 and S2.

The published runs are top-down: the efficiency, operations and offsets of every
scenario are curves read from its ``*_inputs.json``. The bottom-up variants carry the
same assumptions through the detailed modules instead, so that the CO2 decomposition
of AeroMAPS (per aircraft, per operational concept, per energy pathway, per offsetting
scheme) is available on them:

``operations``
    One generic operational concept, whose gain is the scenario's own
    ``operations_gain`` curve.
``offsets``
    Three generic schemes reproducing the three top-down rules with the scenario's own
    inputs: the level rule (CORSIA), the share of the residual and the prescribed
    quantity.
``fleet``
    The bottom-up fleet written by ``calibrate_fleet.py``, which fits it to the
    top-down energy per ASK.
``energy``
    The scenario's own energy carriers file, unchanged.

Run from this directory::

    python build_scenarios.py
"""

import json
from pathlib import Path

import yaml

import aeromaps.utils.yaml  # noqa: F401  registers the custom data type representer
from aeromaps.models.base import AeroMapsCustomDataType
from aeromaps.utils.scenarios import find_scenario, scenarios_root

HERE = Path(__file__).parent
ROOT = HERE.parent
TARGET = scenarios_root() / "atag_3rd_edition_bottom_up"

# scenario -> (top-down scenario key, inputs stem, energy file stem)
SCENARIOS = {
    "s0": ("atag_3rd_edition_light", "s0"),
    "s1": ("atag_3rd_edition_full", "s1"),
    "s2": ("atag_3rd_edition_full", "s2"),
}


def custom(years, values, method="linear"):
    """A year-indexed curve, the way the generic modules read their inputs."""
    return AeroMapsCustomDataType(
        {"years": [int(y) for y in years], "values": [float(v) for v in values], "method": method}
    )


def operations_yaml(inputs):
    years = inputs["operations_gain_reference_years"]
    values = inputs["operations_gain_reference_years_values"]
    return {
        "operations": {
            "name": "operations",
            "category": "operations",
            "inputs": {"fuel_efficiency": {"gain": custom(years, values)}},
        }
    }


def offsets_yaml(inputs):
    """The three top-down offset rules, as generic schemes, from the scenario's inputs."""
    level_years = inputs["carbon_offset_baseline_level_vs_corsia_reference_year_reference_periods"]
    level_values = inputs["carbon_offset_baseline_level_vs_corsia_reference_year_reference_periods_values"]
    if len(level_values) == 1:
        level_values = level_values * len(level_years)
    return {
        "corsia": {
            "name": "corsia",
            "category": "offsets",
            "inputs": {
                "quantity": {
                    "mode": "level",
                    "reference_year": 2019,
                    "baseline_level_vs_reference_year": custom(level_years, level_values),
                    "coverage": custom([2020, 2050], [100.0, 100.0]),
                },
                "economics": {"price": custom([2020, 2050], [0.0, 0.0])},
            },
        },
        "residual_offsets": {
            "name": "residual_offsets",
            "category": "offsets",
            "inputs": {
                "quantity": {
                    "mode": "share_of_residual",
                    "share": custom(
                        inputs["residual_carbon_offset_share_reference_years"],
                        inputs["residual_carbon_offset_share_reference_years_values"],
                    ),
                },
                "economics": {"price": custom([2020, 2050], [0.0, 0.0])},
            },
        },
        "prescribed_offsets": {
            "name": "prescribed_offsets",
            "category": "offsets",
            "inputs": {
                "quantity": {
                    "mode": "quantity",
                    "amount": custom(
                        inputs["manual_carbon_offset_reference_years"],
                        inputs["manual_carbon_offset_reference_years_values"],
                    ),
                },
                "economics": {"price": custom([2020, 2050], [0.0, 0.0])},
            },
        },
    }


def config_yaml(name, edition):
    return {
        "data": {
            "inputs": {"json_inputs_file": f"../data_inputs/{name}_inputs.json"},
            "outputs": {"json_outputs_file": f"../data_outputs/{name}.json"},
        },
        "models": {
            "climate": {
                "climate_model_data_file": "../../climate_models/climate_model_fair_contrail_efficacy.yaml"
            },
            "markets": {"markets_data_file": "../../markets/markets_central.yaml"},
            "fleet": {
                "fleet_model_data_file": f"../data_inputs/{name}_fleet.yaml",
                "aircraft_inventory_model_data_file": f"../data_inputs/{name}_aircraft_inventory.yaml",
            },
            "operations": {"operations_model_data_file": f"../data_inputs/{name}_operations.yaml"},
            "offsets": {"offsets_model_data_file": f"../data_inputs/{name}_offsets.yaml"},
            "energy": {
                "energy_carriers_model_data_file": f"../../{edition}/data_inputs/{name}_energy.yaml",
                # The light edition reads the packaged default resources and processes.
                "resources_model_data_file": "default"
                if edition.endswith("light")
                else f"../../{edition}/data_inputs/resources.yaml",
                "processes_model_data_file": "default"
                if edition.endswith("light")
                else f"../../{edition}/data_inputs/processes.yaml",
            },
            "standards": [
                "models_traffic",
                "models_efficiency_bottom_up",
                "models_energy_with_fuel_effect",
                "models_energy_cost",
                "models_emissions",
                "models_offset",
                "models_sustainability",
                "models_operation_cost_top_down",
            ],
        },
    }


def dump(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(content, Dumper=yaml.SafeDumper, sort_keys=False, width=100), encoding="utf-8")


def main():
    (TARGET / "scenario.yaml").parent.mkdir(parents=True, exist_ok=True)
    (TARGET / "scenario.yaml").write_text(
        'name: "ATAG Waypoint 2050, third edition (bottom-up)"\n'
        "category: institutional\n"
        'tags: ["atag reference", "exogenous demand", "bottom-up"]\n'
        "description: >-\n"
        "  S0, S1 and S2 of the third edition rebuilt with the bottom-up fleet and the generic\n"
        "  operations and offsets modules, fitted to the top-down runs, so that the detailed\n"
        "  CO2 decomposition applies to them.\n",
        encoding="utf-8",
    )
    for name, (edition, stem) in SCENARIOS.items():
        source = Path(find_scenario(edition).path) / "data_inputs"
        inputs = json.loads((source / f"{stem}_inputs.json").read_text(encoding="utf-8"))
        # The inputs of the bottom-up variants are the top-down ones, whose efficiency and
        # operations curves the detailed modules ignore.
        (TARGET / "data_inputs").mkdir(parents=True, exist_ok=True)
        (TARGET / "data_inputs" / f"{name}_inputs.json").write_text(
            json.dumps(inputs, indent=2), encoding="utf-8"
        )
        dump(TARGET / "data_inputs" / f"{name}_operations.yaml", operations_yaml(inputs))
        dump(TARGET / "data_inputs" / f"{name}_offsets.yaml", offsets_yaml(inputs))
        dump(TARGET / "config_files" / f"config_{name}.yaml", config_yaml(name, edition))
        print("wrote", name)


if __name__ == "__main__":
    main()

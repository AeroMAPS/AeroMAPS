"""
Test module for the JSON Schema export of the process variables
(aeromaps/utils/schema.py).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from aeromaps import create_process
from aeromaps.utils.schema import (
    INPUTS_SCHEMA_FILE,
    OUTPUTS_SCHEMA_FILE,
    SCHEMA_DIALECT,
    _json_type,
    _json_value,
    build_variable_schemas,
)

CONFIG_DIR = Path(__file__).parent.parent / "tested_configs"


def test_json_type_mapping():
    assert _json_type(float) == {"type": "number"}
    assert _json_type(int) == {"type": "integer"}
    assert _json_type(bool) == {"type": "boolean"}
    assert _json_type(str) == {"type": "string"}
    for array_type in (pd.Series, np.ndarray, list):
        assert _json_type(array_type) == {"type": "array", "items": {"type": "number"}}
    assert _json_type(None) == {}


def test_json_value_conversion():
    assert _json_value(pd.Series([1.0, np.nan], index=[2020, 2021])) == [1.0, None]
    assert _json_value(np.array([1, 2])) == [1, 2]
    assert _json_value(np.float64(2.5)) == 2.5
    assert _json_value(float("nan")) is None
    assert _json_value("text") == "text"
    assert _json_value(object()) is None


def test_export_on_basic_configuration(tmp_path):
    process = create_process(configuration_file=str(CONFIG_DIR / "config_basic.yaml"))
    schemas = build_variable_schemas(process)

    for key in ("inputs", "outputs"):
        assert schemas[key]["$schema"] == SCHEMA_DIALECT
        assert schemas[key]["type"] == "object"
        assert schemas[key]["properties"]

    outputs = schemas["outputs"]["properties"]
    inputs = schemas["inputs"]["properties"]
    # Outputs are never inputs, and every output names its producer
    assert not set(outputs) & set(inputs)
    assert all("x-producer" in prop for prop in outputs.values())
    assert all(prop["x-consumers"] for prop in inputs.values())

    co2 = outputs["co2_emissions"]
    assert co2["unit"] == "MtCO2"
    assert co2["description"]
    # Auto-model outputs are untyped before the process has run (see test_process)
    assert "type" not in co2

    # Units declared at the model level flow into the schema, types come from the grammar
    assert outputs["manual_carbon_offset"]["unit"] == "MtCO2"
    values = inputs["manual_carbon_offset_reference_years_values"]
    assert values["unit"] == "MtCO2"
    assert values["type"] == "array"

    # Inputs carry their default value when it is representable
    assert inputs["end_year"]["default"] == process.parameters.end_year

    # Files are written and are valid JSON
    paths = process.export_schema(tmp_path)
    assert [path.name for path in paths] == [INPUTS_SCHEMA_FILE, OUTPUTS_SCHEMA_FILE]
    for path in paths:
        with open(path, encoding="utf-8") as file:
            assert json.load(file)["properties"]

    # Defaults can be omitted
    without_defaults = process.export_schema(include_defaults=False)
    assert all("default" not in prop for prop in without_defaults["inputs"]["properties"].values())

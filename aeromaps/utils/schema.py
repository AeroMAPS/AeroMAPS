"""
JSON Schema export of the variables exchanged by an AeroMAPS process.

The schemas are derived from the GEMSEO grammars of the disciplines, so they
describe what the models actually read and write: a variable read by a model
and produced by none is an input, a variable produced by a model is an output.
Each property carries the JSON type inferred from the grammar, the ``unit``,
``description`` and ``source`` metadata (extra keywords, ignored by validators)
and, for inputs, the default value the process would use.

Draft-07 is used so the files can be consumed as-is by JSON Schema form
libraries such as RJSF.
"""

import json
import math
from numbers import Number
from pathlib import Path

import numpy as np
import pandas as pd

SCHEMA_DIALECT = "http://json-schema.org/draft-07/schema#"

INPUTS_SCHEMA_FILE = "inputs_schema.json"
OUTPUTS_SCHEMA_FILE = "outputs_schema.json"

# Parameters read by the process itself (time index bounds) rather than through a
# discipline grammar; they are inputs all the same.
PROCESS_LEVEL_INPUTS = (
    "climate_historic_start_year",
    "historic_start_year",
    "prospection_start_year",
    "end_year",
)
PROCESS_CONSUMER = "AeroMAPSProcess"


def _json_type(python_type) -> dict:
    """Map a grammar element type to a JSON Schema type fragment."""
    if not isinstance(python_type, type):
        return {}
    if issubclass(python_type, bool):
        return {"type": "boolean"}
    if issubclass(python_type, str):
        return {"type": "string"}
    if issubclass(python_type, (int, np.integer)):
        return {"type": "integer"}
    if issubclass(python_type, (Number, np.floating)):
        return {"type": "number"}
    if issubclass(python_type, (pd.Series, np.ndarray, list, tuple)):
        return {"type": "array", "items": {"type": "number"}}
    return {}


def _json_value(value):
    """Convert a default value to JSON; None when it cannot be represented."""
    if isinstance(value, pd.Series):
        return _json_value(value.to_numpy())
    if isinstance(value, np.ndarray):
        return [_json_value(item) for item in value.tolist()]
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, np.generic):
        return _json_value(value.item())
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, int):
        return value
    return None


def _type_from_process_data(process, name: str) -> dict:
    """Infer the JSON type of a variable from where it landed in the process data.

    Auto models do not annotate their outputs one by one, so the grammar carries
    no type for them; once the process has run, the data containers tell.
    """
    data = getattr(process, "data", None) or {}
    for container, fragment in (
        ("float_inputs", {"type": "number"}),
        ("float_outputs", {"type": "number"}),
        ("str_inputs", {"type": "string"}),
        ("vector_inputs", {"type": "array", "items": {"type": "number"}}),
        ("vector_outputs", {"type": "array", "items": {"type": "number"}}),
        ("climate_outputs", {"type": "array", "items": {"type": "number"}}),
    ):
        variables = data.get(container)
        if variables is not None and name in variables:
            return dict(fragment)
    return {}


def _variable_property(process, grammar, name: str) -> dict:
    """Build the schema of one variable from its grammar type and metadata."""
    prop = _json_type(grammar[name]) or _type_from_process_data(process, name)
    info = process.get_variable_information(name) or {}
    unit = info.get("Unit")
    if unit and unit != "N/A":
        prop["unit"] = unit
    description = info.get("Description")
    if description and description != "N/A":
        prop["description"] = description
    source = info.get("Source")
    if source:
        prop["source"] = source
    return prop


def build_variable_schemas(process, include_defaults: bool = True) -> dict:
    """Build the JSON Schemas of the inputs and outputs of a process.

    Parameters
    ----------
    process
        An AeroMAPSProcess whose disciplines have been initialised.
    include_defaults
        Whether to attach the default value of each input. Time series are
        exported as plain lists; their year index is the process time index.

    Returns
    -------
    schemas
        Dictionary with keys ``inputs`` and ``outputs``, each a JSON Schema.
    """
    disciplines = process.disciplines
    produced_by = {}
    for discipline in disciplines:
        for name in discipline.output_grammar.names:
            produced_by.setdefault(name, discipline.name)

    inputs = {}
    outputs = {}
    for name in PROCESS_LEVEL_INPUTS:
        value = getattr(process.parameters, name, None)
        if value is None:
            continue
        prop = _json_type(type(value))
        info = process.get_variable_information(name) or {}
        if info.get("Unit") and info["Unit"] != "N/A":
            prop["unit"] = info["Unit"]
        if info.get("Description") and info["Description"] != "N/A":
            prop["description"] = info["Description"]
        prop["x-consumers"] = [PROCESS_CONSUMER]
        if include_defaults:
            prop["default"] = _json_value(value)
        inputs[name] = prop
    for discipline in disciplines:
        for name in discipline.input_grammar.names:
            if name in produced_by:
                continue
            prop = inputs.get(name)
            if prop is None:
                prop = _variable_property(process, discipline.input_grammar, name)
                prop["x-consumers"] = []
                inputs[name] = prop
            prop["x-consumers"].append(discipline.name)
            if include_defaults and "default" not in prop:
                default = discipline.default_input_data.get(name)
                if default is not None:
                    json_default = _json_value(default)
                    if json_default is not None:
                        prop["default"] = json_default
        for name in discipline.output_grammar.names:
            if name in outputs:
                continue
            prop = _variable_property(process, discipline.output_grammar, name)
            prop["x-producer"] = produced_by[name]
            outputs[name] = prop

    def _schema(title, properties):
        return {
            "$schema": SCHEMA_DIALECT,
            "title": title,
            "type": "object",
            "properties": dict(sorted(properties.items())),
            "additionalProperties": False,
        }

    return {
        "inputs": _schema("AeroMAPS inputs", inputs),
        "outputs": _schema("AeroMAPS outputs", outputs),
    }


def export_variable_schemas(process, directory, include_defaults: bool = True) -> list:
    """Write the input and output schemas of a process as JSON files.

    Parameters
    ----------
    process
        An AeroMAPSProcess whose disciplines have been initialised.
    directory
        Target directory, created if needed.
    include_defaults
        See build_variable_schemas.

    Returns
    -------
    paths
        The two written file paths, inputs first.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    schemas = build_variable_schemas(process, include_defaults=include_defaults)
    paths = []
    for key, file_name in (("inputs", INPUTS_SCHEMA_FILE), ("outputs", OUTPUTS_SCHEMA_FILE)):
        path = directory / file_name
        with open(path, "w", encoding="utf-8") as file:
            json.dump(schemas[key], file, ensure_ascii=False, indent=2)
            file.write("\n")
        paths.append(path)
    return paths

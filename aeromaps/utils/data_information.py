"""
Registry of variable metadata (unit, description, source) for AeroMAPS.

Metadata is stored in a YAML file (default: ``resources/data/data_information.yaml``)
with two sections:

- ``variables``: exact variable names mapped to their unit/description/source,
- ``patterns``: ordered glob rules (``*`` wildcard) covering variables whose names
  are generated dynamically (e.g. per energy pathway). Exact entries always take
  precedence over patterns; among patterns, the first match wins.

All units are validated against the vocabulary of ``aeromaps.utils.units`` when
the file is loaded. The legacy semicolon-separated CSV format is still readable
for backward compatibility.
"""

import re
import warnings
from pathlib import Path

import pandas as pd
import xarray as xr
import yaml

from aeromaps.utils.units import UnitError, parse_unit


def _glob_to_regex(pattern: str) -> re.Pattern:
    """Translate a glob pattern with ``*`` wildcards into a capturing regex."""
    parts = pattern.split("*")
    regex = "(.*)".join(re.escape(part) for part in parts)
    return re.compile(f"^{regex}$")


class DataInformation:
    """
    Lookup table for variable metadata, with exact entries and glob patterns.

    Parameters
    ----------
    variables
        Mapping of variable name to a dict with keys 'unit', 'description'
        and optionally 'source'.
    patterns
        Ordered list of dicts with keys 'match' (glob pattern), 'unit',
        'description' and optionally 'source'.
    source_file
        Path of the file the metadata was loaded from, used in error messages.

    Attributes
    ----------
    variables
        Exact variable entries.
    patterns
        Pattern rules, each with its compiled regex.
    """

    _UNKNOWN = {"Unit": "N/A", "Description": "N/A", "Source": "N/A"}

    # Explicit sentinel for entries whose unit is not expressible statically
    # (e.g. LCA impacts, whose unit depends on the LCIA method)
    NOT_APPLICABLE = "N/A"

    def __init__(self, variables: dict, patterns: list = None, source_file=None):
        self.variables = variables or {}
        self.patterns = []
        self.source_file = source_file
        self._validate_units()
        for rule in patterns or []:
            if "match" not in rule:
                raise ValueError(f"Pattern rule without 'match' key in '{source_file}': {rule}")
            unit = rule.get("unit")
            if unit is not None and str(unit) != self.NOT_APPLICABLE:
                try:
                    parse_unit(str(unit))
                except UnitError as e:
                    raise UnitError(
                        f"Invalid unit in pattern '{rule['match']}' of '{source_file}': {e}"
                    ) from e
            self.patterns.append({**rule, "_regex": _glob_to_regex(rule["match"])})

    def _validate_units(self):
        errors = []
        for name, entry in self.variables.items():
            unit = entry.get("unit")
            if unit is None:
                errors.append(f"  - variable '{name}': missing unit")
                continue
            if str(unit) == self.NOT_APPLICABLE:
                continue
            try:
                parse_unit(str(unit))
            except UnitError as e:
                errors.append(f"  - variable '{name}': {e}")
        if errors:
            raise UnitError(
                f"Invalid units in data information file '{self.source_file}':\n"
                + "\n".join(errors)
            )

    @classmethod
    def from_file(cls, file_name) -> "DataInformation":
        """
        Load metadata from a YAML file (or a legacy CSV file).

        Parameters
        ----------
        file_name
            Path to the metadata file; format is chosen from the extension.

        Returns
        -------
        data_information
            Loaded and validated DataInformation instance.
        """
        path = Path(file_name)
        if path.suffix.lower() == ".csv":
            warnings.warn(
                f"Reading data information from CSV ('{path}') is deprecated. "
                "Convert the file to the YAML format (see data_information.yaml in "
                "aeromaps/resources/data).",
                DeprecationWarning,
            )
            return cls.from_csv(path)
        return cls.from_yaml(path)

    @classmethod
    def from_yaml(cls, file_name) -> "DataInformation":
        """Load metadata from the YAML format (sections 'variables' and 'patterns')."""
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                content = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Data information file not found: '{file_name}'")
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse data information file '{file_name}': {e}") from e
        if not isinstance(content, dict):
            raise ValueError(
                f"Expected a YAML mapping with 'variables'/'patterns' in '{file_name}'."
            )
        return cls(
            variables=content.get("variables", {}),
            patterns=content.get("patterns", []),
            source_file=file_name,
        )

    @classmethod
    def from_csv(cls, file_name) -> "DataInformation":
        """Load metadata from the legacy semicolon-separated CSV format."""
        try:
            df = pd.read_csv(file_name, encoding="utf-8-sig", sep=";")
        except FileNotFoundError:
            raise FileNotFoundError(f"Data information file not found: '{file_name}'")
        except Exception as e:
            raise ValueError(f"Failed to parse data information file '{file_name}': {e}") from e
        source_column = next(
            (c for c in df.columns if c.lower().startswith("reference") or c == "Source"),
            None,
        )
        variables = {}
        for _, row in df.iterrows():
            entry = {
                "unit": row.get("Unit"),
                "description": row.get("Description"),
            }
            if source_column is not None and pd.notna(row.get(source_column)):
                entry["source"] = row[source_column]
            variables[row["Name"]] = entry
        return cls(variables=variables, patterns=[], source_file=file_name)

    def lookup(self, name: str):
        """
        Resolve metadata for a variable name.

        Parameters
        ----------
        name
            Variable name to resolve.

        Returns
        -------
        info
            Dict with keys 'Unit', 'Description' and 'Source', or None if the
            name matches neither an exact entry nor a pattern.
        """
        entry = self.variables.get(name)
        if entry is not None:
            return {
                "Unit": entry.get("unit", "N/A"),
                "Description": entry.get("description", "N/A"),
                "Source": entry.get("source", ""),
            }
        for rule in self.patterns:
            match = rule["_regex"].match(name)
            if match:
                description = rule.get("description", "N/A")
                prefix = match.group(1) if match.groups() else ""
                description = str(description).format(name=name, prefix=prefix)
                return {
                    "Unit": rule.get("unit", "N/A"),
                    "Description": description,
                    "Source": rule.get("source", ""),
                }
        return None

    def build_dataframe(self, data: dict) -> pd.DataFrame:
        """
        Build the consolidated data information table for process data.

        Parameters
        ----------
        data
            Process data dictionary mapping a data type (e.g. 'float_inputs',
            'vector_outputs') to a container of variable names.

        Returns
        -------
        data_information_df
            DataFrame with columns Name, Type, Unit, Description and Source;
            variables without metadata get 'N/A' entries.
        """
        rows = []
        for data_type, variables in data.items():
            # FIXME: xarray not supported yet for data information
            if isinstance(variables, xr.DataArray):
                continue
            for variable in variables:
                info = self.lookup(variable) or self._UNKNOWN
                rows.append({"Name": variable, "Type": data_type, **info})
        return pd.DataFrame(rows, columns=["Name", "Type", "Unit", "Description", "Source"])

    def unresolved_names(self, data: dict) -> list:
        """
        List variables from process data that have no metadata entry.

        Parameters
        ----------
        data
            Process data dictionary, as in build_dataframe.

        Returns
        -------
        names
            Sorted list of variable names with no exact or pattern match.
        """
        names = set()
        for variables in data.values():
            if isinstance(variables, xr.DataArray):
                continue
            for variable in variables:
                if self.lookup(variable) is None:
                    names.add(variable)
        return sorted(names)

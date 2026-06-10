import logging
import os.path as pth
import json
from json import load

import numpy as np
import pandas as pd

from pandas import read_csv
from deepdiff import DeepDiff

from aeromaps.resources import data
from aeromaps.resources import climate_data


def _dict_from_json(file_name="parameters.json") -> dict:
    """
    Convert a JSON parameters file into a dictionary

    Parameters
    ----------
    file_name
        Name of the JSON file to read.

    Returns
    -------
    dict
        Dictionary containing the parameters from the JSON file.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    json.JSONDecodeError
        If the file contains invalid JSON.
    """
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            parameters_dict = load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Parameters file not found: '{file_name}'")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in '{file_name}': {e.msg}", e.doc, e.pos) from e
    dict = _dict_from_parameters_dict(parameters_dict)
    return dict


def _flatten_dict(val, prefix=""):
    """
    Recursively flatten a nested dictionary by concatenating keys with an underscore.

    Parameters
    ----------
    val
        The dictionary to flatten.
    prefix
        The prefix to prepend to each key.

    Returns
    -------
    flattened
        A flattened dictionary where nested keys are concatenated using underscores.
    """
    flattened = {}
    if val:
        for param_name, param_value in val.items():
            full_param_name = f"{prefix}_{param_name}" if prefix else param_name
            if isinstance(param_value, dict):
                flattened.update(_flatten_dict(param_value, full_param_name))
            else:
                flattened[full_param_name] = param_value
    return flattened


def _dict_from_parameters_dict(parameters_dict) -> dict:
    """
    Convert specific lists in the parameters dictionary to pandas Series with appropriate indices.

    Parameters
    ----------
    parameters_dict
        Dictionary containing parameters to be converted.

    Returns
    -------
    dict
        Updated dictionary with specified lists converted to pandas Series.
    """
    for key, value in parameters_dict.items():
        # TODO: generic handling of timetables
        if isinstance(value, list) and key in [
            "rpk_init",
            "ask_init",
            "rtk_init",
            "pax_init",
            "freight_init",
            "energy_consumption_init",
            "total_aircraft_distance_init",
            "gdp_per_capita_init",
            "population_init",
        ]:
            new_index = range(
                parameters_dict["historic_start_year"], parameters_dict["prospection_start_year"]
            )
            parameters_dict[key] = pd.Series(value, index=new_index)

    return parameters_dict


def _dict_to_df(data, orient="index") -> pd.DataFrame:
    """
    Convert a dictionary to a pandas DataFrame, ensuring all values have the same length by padding with NaN if necessary.
    Parameters
    ----------
    data
        Dictionary to convert to DataFrame.
    orient
        Orientation of the DataFrame ('index' as default).

    Returns
    -------
    df
        DataFrame created from the dictionary.

    """
    # Check if values from data have the same length or else populate with NaN
    max_len = max([len(v) for v in data.values()])
    for key, value in data.items():
        if len(value) < max_len:
            data[key] = np.append(value, np.full(max_len - len(value), np.nan))

    df = pd.DataFrame.from_dict(data, orient=orient)
    return df


def compute_partitioning(
    world_data: dict,
    per_market_passenger_data: dict,
    total_seats_last_historical_year: float,
    freight_energy_share_last_historical_year: float,
    path: str = "",
) -> None:
    """
    Generate a partitioned AeroMAPS inputs JSON for a geographic scope.

    Parameters
    ----------
    world_data
        World parameters dict loaded from parameters.json.
    per_market_passenger_data
        Mapping of market_id to {"ask_last_historical_year": float, "energy_last_historical_year": float}
        for every passenger market in the scope. Energy values must already
        be expressed in the AeroMAPS scope (i.e. passeger only, belly freight excluded).
    total_seats_last_historical_year
        Total seats in 2019 for the partitioned scope, used to scale pax_init.
    freight_energy_share_last_historical_year
        Freight energy share in 2019 for the scope [%]. Must cover all freight
        (belly + dedicated). Total energy is derived from the market energies
        and this share: total = passenger_energy / (1 - freight_share / 100).
    path
        Directory where partitioning_updated_inputs.json will be written.
    """

    n_historic_years = world_data["prospection_start_year"] - world_data["historic_start_year"]
    world_ask_last_historical_year = world_data["ask_init"][n_historic_years - 1]
    world_seats_last_historical_year = (
        world_data["pax_init"][n_historic_years - 1]
        * world_data["ask_init"][n_historic_years - 1]
        / world_data["rpk_init"][n_historic_years - 1]
        * 100
    )

    total_ask_last_historical_year = sum(
        d["ask_last_historical_year"] for d in per_market_passenger_data.values()
    )
    passenger_energy_last_historical_year = sum(
        d["energy_ask_last_historical_year"] * d["ask_last_historical_year"]
        for d in per_market_passenger_data.values()
    )
    total_energy_last_historical_year = passenger_energy_last_historical_year / (
        1 - freight_energy_share_last_historical_year / 100
    )

    # Per-market shares
    market_energy_shares = {
        mid: d["energy_ask_last_historical_year"]
        * d["ask_last_historical_year"]
        / total_energy_last_historical_year
        * 100
        for mid, d in per_market_passenger_data.items()
    }
    market_rpk_shares = {
        mid: d["ask_last_historical_year"] / total_ask_last_historical_year * 100
        for mid, d in per_market_passenger_data.items()
    }

    # Scaling ratios for historical vectors
    share_ask = total_ask_last_historical_year / world_ask_last_historical_year * 100
    share_seats = total_seats_last_historical_year / world_seats_last_historical_year
    share_energy = (
        total_energy_last_historical_year
        / world_data["energy_consumption_init"][n_historic_years - 1]
        * 100
    )

    historical_years = range(n_historic_years)
    scaled_vectors = {
        "rpk_init": [world_data["rpk_init"][k] * share_ask / 100 for k in historical_years],
        "ask_init": [world_data["ask_init"][k] * share_ask / 100 for k in historical_years],
        "rtk_init": [world_data["rtk_init"][k] * share_ask / 100 for k in historical_years],
        "freight_init": [world_data["freight_init"][k] * share_ask / 100 for k in historical_years],
        "total_aircraft_distance_init": [
            world_data["total_aircraft_distance_init"][k] * share_ask / 100
            for k in historical_years
        ],
        "pax_init": [world_data["pax_init"][k] * share_seats / 100 for k in historical_years],
        "energy_consumption_init": [
            world_data["energy_consumption_init"][k] * share_energy / 100 for k in historical_years
        ],
    }

    # Climate data
    climate_world_data_path = pth.join(
        climate_data.__path__[0], "temperature_historical_dataset.csv"
    )
    climate_world_data = pd.read_csv(climate_world_data_path, delimiter=";", header=None).values
    climate_data_dict = {
        "years": climate_world_data[:, 0].tolist(),
        "co2_emissions": (climate_world_data[:, 1] * share_energy / 100).tolist(),
        "nox_emissions": (climate_world_data[:, 2] * share_energy / 100).tolist(),
        "h2o_emissions": (climate_world_data[:, 3] * share_energy / 100).tolist(),
        "soot_emissions": (climate_world_data[:, 4] * share_energy / 100).tolist(),
        "sulfur_emissions": (climate_world_data[:, 5] * share_energy / 100).tolist(),
        "distance": (climate_world_data[:, 6] * share_ask / 100).tolist(),
    }

    # Build output — market float data uses <market_id>_<leaf> naming
    other_float_data = {}
    for mid, share in market_energy_shares.items():
        other_float_data[f"{mid}_energy_share_last_historical_year"] = share
    for mid, share in market_rpk_shares.items():
        other_float_data[f"{mid}_rpk_share_last_historical_year"] = share
    other_float_data["freight_energy_share_last_historical_year"] = (
        freight_energy_share_last_historical_year
    )
    other_float_data["commercial_aviation_coefficient"] = 1

    other_years = list(
        range(world_data["historic_start_year"], world_data["prospection_start_year"])
    )
    output = {
        "other_float_data": other_float_data,
        "other_vector_data": {"years": other_years, **scaled_vectors},
        "climate_data": climate_data_dict,
    }

    partitioning_updated_inputs_path = pth.join(path, "partitioning_updated_inputs.json")
    with open(partitioning_updated_inputs_path, "w") as outfile:
        json.dump(output, outfile, indent=4)


def create_partitioning(file, path="", freight_energy_share_last_historical_year=15.0):
    """
    Generate a partitioned AeroMAPS inputs JSON from an AeroSCOPE CSV file.

    Parameters
    ----------
    file
        Path to the CSV file containing AeroSCOPE data for the partitioned scope.
    path
        Directory path where the generated files will be saved.
    freight_energy_share_last_historical_year
        Freight energy share in 2019 for the partitioned scope [%]. Defaults to
        the world value declared in ``default_markets/markets.yaml`` (15.0).
        Override when partitioning to a region whose freight share differs.

    Returns
    -------
    None

    """

    # World input data recovery
    world_data_path = pth.join(data.__path__[0], "parameters.json")
    with open(world_data_path, "r") as parameters_file:
        world_data_dict = json.load(parameters_file)

    freight_energy_share_last_historical_year_partitioned = (
        freight_energy_share_last_historical_year
    )

    # AeroSCOPE CSV layout (fixed format):
    #   row 0: ASK        — col 1=total, col 2=SR, col 3=MR, col 4=LR
    #   row 2: seats      — col 1=total
    #   row 4: energy/ASK — col 1=total, col 2=SR, col 3=MR, col 4=LR
    partitioned_data = read_csv(file, delimiter=",").values
    total_seats_last_historical_year = partitioned_data[2, 1]

    # AeroSCOPE scope → AeroMAPS scope corrections:
    # 1. Belly freight: AeroSCOPE energy-per-ASK includes belly freight carried on
    #    passenger aircraft; AeroMAPS accounts for it separately, so we remove it
    #    from per-market passenger energy using the world belly-freight fraction.
    # 2. Dedicated freight: AeroSCOPE covers passenger aircraft only; we scale total
    #    energy up to include dedicated freighters (half of total freight energy share).
    _belly_frac = freight_energy_share_last_historical_year_partitioned / 2 / 100
    _ded_frac = freight_energy_share_last_historical_year_partitioned / 2 / 100
    belly_correction = 1 - _belly_frac / (1 - _ded_frac)

    _raw_markets = {
        "short_range": (partitioned_data[0, 2], partitioned_data[4, 2]),
        "medium_range": (partitioned_data[0, 3], partitioned_data[4, 3]),
        "long_range": (partitioned_data[0, 4], partitioned_data[4, 4]),
    }
    per_market_passenger_data = {}
    for mid, (ask, epask) in _raw_markets.items():
        if pd.isna(ask) or ask == 0.0:
            # Void market: keep it in the scope but with zero traffic and energy.
            logging.warning(f"No traffic is assumed for {mid}.")
            per_market_passenger_data[mid] = {
                "ask_last_historical_year": 0.0,
                "energy_ask_last_historical_year": 0.0,
            }
            continue
        if pd.isna(epask):
            raise ValueError(f"{mid} ASK is non-zero but energy per ASK is null.")
        per_market_passenger_data[mid] = {
            "ask_last_historical_year": ask,
            "energy_ask_last_historical_year": epask * belly_correction,
        }

    compute_partitioning(
        world_data=world_data_dict,
        per_market_passenger_data=per_market_passenger_data,
        total_seats_last_historical_year=total_seats_last_historical_year,
        freight_energy_share_last_historical_year=freight_energy_share_last_historical_year_partitioned,
        path=path,
    )


def merge_json_files(file1, file2, output_file):
    """
    Merge two JSON files into a single JSON file.

    Parameters
    ----------
    file1
        Path to the first JSON file.
    file2
        Path to the second JSON file.
    output_file
        Path to the output JSON file where the merged content will be saved.

    Returns
    -------
    None

    """
    with open(file1, "r") as f1, open(file2, "r") as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    merged_data = {**data1, **data2}

    with open(output_file, "w") as outfile:
        json.dump(merged_data, outfile, indent=4)


def compare_json_files(
    file1_path: str,
    file2_path: str,
    ignore_order: bool = False,
    verbose: bool = True,
    rtol: float = 0.0001,
    atol: float = 0.1,
) -> bool:
    """
    Compare two JSON files using deepdiff and return whether differences exist.

    Parameters
    ----------
    file1_path
        Path to the first JSON file.
    file2_path
        Path to the second JSON file.
    ignore_order
        Whether to ignore the order in lists.
    verbose
        Whether to print differences.
    rtol
        Relative tolerance for numeric comparisons.
    atol
        Absolute tolerance for numeric comparisons.

    Returns
    -------
    differences_exist
        True if differences exist between the two JSON files, False otherwise.
    """
    with open(file1_path, "r") as f1, open(file2_path, "r") as f2:
        json1 = json.load(f1)
        json2 = json.load(f2)

    diff = DeepDiff(
        json1,
        json2,
        ignore_order=ignore_order,
        exclude_paths=False or [],
    )

    # Remove value changes that are within tolerance
    if "values_changed" in diff:
        keys_to_remove = []
        for key, value in diff["values_changed"].items():
            if isinstance(value, dict) and "new_value" in value and "old_value" in value:
                new_value = value["new_value"]
                old_value = value["old_value"]
                if (
                    isinstance(new_value, (float, int))
                    and isinstance(old_value, (float, int))
                    and np.isclose(new_value, old_value, rtol=rtol, atol=atol, equal_nan=True)
                ):
                    keys_to_remove.append(key)
                elif isinstance(new_value, dict) and isinstance(old_value, dict):
                    # Check if all numeric values in the dict are close enough
                    if all(
                        np.isclose(new_value[k], old_value[k], rtol=rtol, atol=atol, equal_nan=True)
                        for k in new_value
                        if isinstance(new_value[k], (float, int))
                        and k in old_value
                        and isinstance(old_value[k], (float, int))
                    ):
                        keys_to_remove.append(key)
        for key in keys_to_remove:
            del diff["values_changed"][key]
        if not diff["values_changed"]:
            del diff["values_changed"]

    # Clean up iterable diffs by removing items that are close enough to something in the other JSON
    iterable_messages = []

    def cleanup_iterable_diff(tag, other_json):
        if tag in diff:
            keys_to_remove = []
            for key, value in diff[tag].items():
                # The path looks like "root['some_list'][2]"
                prefix, idx_str = key.rsplit("[", 1)
                idx = idx_str[:-1]  # Remove the trailing ']'
                other_parent = eval(prefix.replace("root", "other_json"))
                if isinstance(other_parent, list):
                    if np.isclose(
                        value, other_parent[int(idx)], rtol=rtol, atol=atol, equal_nan=True
                    ):
                        keys_to_remove.append(key)
                    else:
                        iterable_messages.append(
                            f"For: {prefix}, index {idx} beyond tolerance: {value} against {other_parent[int(idx)]}"
                        )
            for k in keys_to_remove:
                del diff[tag][k]
            if not diff[tag]:
                del diff[tag]

    cleanup_iterable_diff("iterable_item_added", json1)
    cleanup_iterable_diff("iterable_item_removed", json2)

    if verbose:
        if diff or iterable_messages:
            print("Differences found:")
            if diff:
                print(json.dumps(diff, indent=2, default=convert_non_serializable))
            if iterable_messages:
                for message in iterable_messages:
                    print(message)
        else:
            print("No differences found.")
    return bool(diff)


def convert_non_serializable(obj):
    """
    Convert non-serializable objects to a serializable format for JSON output.

    Parameters
    ----------
    obj
        The object to convert.

    Returns
    -------
    serializable
        A JSON-serializable representation of the object.

    """
    # Native containers -> convert to list
    if isinstance(obj, (set, list, tuple)):
        return list(obj)

    # If it's an iterable (but not a string/bytes/mapping), try to convert to list.
    # This handles deepdiff.SetOrdered and similar container-like types that don't
    # expose useful __dict__ contents.
    if not isinstance(obj, (str, bytes, dict)) and hasattr(obj, "__iter__"):
        try:
            lst = list(obj)
            return lst
        except Exception:
            # If it cannot be converted to a list, fall through to other handlers
            pass

    # If object has a non-empty __dict__, prefer that (useful for plain objects)
    if hasattr(obj, "__dict__") and obj.__dict__:
        # Optional debug left intentionally minimal
        # print('Converting using __dict__', obj)
        return obj.__dict__

    # Last resort: convert to string
    return str(obj)


def _get_value_for_year(value, year, default_return=None):
    """
    Utility function for generic bottom up model.
    Retrieve a value for a specific year from a given value, which can be an integer, float, or pandas Series.

    Parameters
    ----------
    value
        The value to retrieve from (can be int, float, or pd.Series).
    year
        The year for which to retrieve the value.
    default_return
        The default value to return if the year is not found in the Series.

    Returns
    -------
    result
        The retrieved value for the specified year, or the default return value.
    """
    if isinstance(value, (int, float)):
        return value
    elif isinstance(value, pd.Series):
        return value.loc[year] if year in value.index else default_return
    return default_return


def _custom_series_addition(s1, s2) -> pd.Series:
    """
    Adds two pandas Series, handling missing indices (NaN) gracefully.

    For each index in the result (union of both Series indices):
      - If both values are NaN, the result is NaN.
      - If only one value is NaN, the other value is used.
      - Otherwise, the two values are summed.

    Parameters
    ----------
    s1
        First Series (or scalar) to add.
    s2
        Second Series (or scalar) to add.

    Returns
    -------
    pd.Series
        Resulting Series from the addition, aligned on the union of indices.
    """

    if np.isscalar(s1):
        return pd.Series(np.where(pd.isna(s2), s1, s1 + s2), index=s2.index)
    if np.isscalar(s2):
        return pd.Series(np.where(pd.isna(s1), s2, s1 + s2), index=s1.index)

    # Extend the indices of both Series to create a full index
    full_index = s1.index.union(s2.index)
    s1_aligned = s1.reindex(full_index)
    s2_aligned = s2.reindex(full_index)

    na1 = s1_aligned.isna()
    na2 = s2_aligned.isna()

    # Vectorized addition with handling for NaN values
    return pd.Series(
        np.where(
            na1 & na2,
            np.nan,  # If both are NaN, result is NaN
            np.where(
                na1,
                s2_aligned,  # If s1 is NaN, use s2
                np.where(na2, s1_aligned, s1_aligned + s2_aligned),
            ),  # If s2 is NaN, use s1, otherwise sum both
        ),
        index=full_index,
    )


def custom_logger_config(logger):
    """
    Configure logging and docstring parsing for GEMSEO disciplines.

    Applies a filter to enrich GEMSEO's missing Args-section warning with the
    offending callable, and patches GEMSEO's docstring parser to support NumPy
    "Parameters" sections in addition to Google-style "Args".


    Parameters
    ----------
    logger
        The logger to configure.

    Returns
    -------
    logger
        The configured logger with the custom filter applied.

    """

    # Patch GEMSEO docstring parsing to support NumPy-style Parameters sections.
    try:
        import inspect
        import re
        import gemseo.utils.source_parsing as source_parsing

        if not getattr(source_parsing, "_aeromaps_numpy_docstring_patch", False):

            def _parse_numpy_parameters(docstring: str) -> dict:
                lines = inspect.cleandoc(docstring).splitlines()
                params = {}

                # Locate "Parameters" section header
                start_idx = None
                for i, line in enumerate(lines):
                    if line.strip() == "Parameters":
                        if i + 1 < len(lines) and set(lines[i + 1].strip()) == {"-"}:
                            start_idx = i + 2
                            break
                if start_idx is None:
                    return {}

                current_name = None
                current_desc = []

                def flush_param():
                    if current_name:
                        params[current_name] = " ".join(current_desc).strip()

                i = start_idx
                while i < len(lines):
                    line = lines[i]
                    # Stop at next section header
                    if line and not line.startswith(" "):
                        if i + 1 < len(lines) and set(lines[i + 1].strip()) == {"-"}:
                            break

                    if line and not line.startswith(" "):
                        flush_param()
                        header = line.strip()
                        if not header:
                            current_name = None
                            current_desc = []
                        else:
                            # Accept both "name : type" and bare "name" entries.
                            name = header.split(" :", 1)[0].strip()
                            current_name = name if name else None
                            current_desc = []
                    else:
                        if current_name is not None:
                            current_desc.append(line.strip())
                    i += 1

                flush_param()
                return params

            def _parse_google_or_numpy(docstring: str, n_arguments: int = 0) -> dict:
                args_sections = source_parsing.RE_PATTERN_ARGS_SECTION.findall(docstring)
                if len(args_sections) == 1:
                    args_section = inspect.cleandoc(args_sections[0])
                    parsed_doc = {}
                    for name, desc in source_parsing.RE_PATTERN_ARGS.findall(args_section):
                        parsed_doc[name] = re.sub(
                            r"\n ", "\n", re.sub(r"[\r\t\f\v ]+", " ", desc).strip()
                        )
                    return parsed_doc

                numpy_doc = _parse_numpy_parameters(docstring)
                if numpy_doc:
                    return numpy_doc

                if n_arguments:
                    source_parsing.LOGGER.warning("The Args section is missing.")
                return {}

            source_parsing.parse_google = _parse_google_or_numpy
            source_parsing._aeromaps_numpy_docstring_patch = True
    except Exception:
        # If GEMSEO is unavailable, keep logger config functional.
        pass

    # Enrich the warning with the originating callable when available.
    class SuppressArgsSectionWarning(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            message = record.getMessage()
            if message != "The Args section is missing.":
                return True

            model_name = None
            frame = None
            try:
                import inspect

                frame = inspect.currentframe()
                while frame:
                    if (
                        frame.f_code.co_name == "get_options_doc"
                        and frame.f_globals.get("__name__") == "gemseo.utils.source_parsing"
                    ):
                        func = frame.f_locals.get("function")
                        qualname = getattr(func, "__qualname__", None) if func else None
                        module = getattr(func, "__module__", None) if func else None
                        if qualname and module:
                            model_name = f"{module}.{qualname}"
                        elif qualname:
                            model_name = qualname
                        break
                    frame = frame.f_back
            finally:
                del frame

            if model_name:
                record.msg = f"{message} (function: {model_name})"
                record.args = ()
            return True

    args_warning_filter = getattr(logger, "_aeromaps_args_warning_filter", None)
    if args_warning_filter is None:
        args_warning_filter = SuppressArgsSectionWarning()
        logger._aeromaps_args_warning_filter = args_warning_filter

    if args_warning_filter not in logger.filters:
        logger.addFilter(args_warning_filter)
    for handler in logger.handlers:
        if args_warning_filter not in handler.filters:
            handler.addFilter(args_warning_filter)

    return logger


def clean_notebooks_on_tests(namespace=None, force_cleanup=False):
    """
    Clean up the notebook namespace by deleting variables when running tests or when forced to save semaphore memory.

    Parameters
    ----------
    namespace
        The namespace (dictionary) to clean. If None, uses globals().
    force_cleanup
        If True, forces cleanup regardless of test detection.

    Returns
    -------
    None

    """
    import os
    import gc

    logger = logging.getLogger("aeromaps.utils.functions")
    logger.info("🧹 clean_notebooks_on_tests called")

    if namespace is None:
        namespace = globals()
    RUNNING_TEST = os.environ.get("PYTEST_CURRENT_TEST") is not None

    if RUNNING_TEST or force_cleanup:
        logger.info("🧪 Detected test run or force cleanup")
        to_delete = [
            var
            for var in list(namespace.keys())
            if not var.startswith("_")
            and var not in ("os", "gc", "RUNNING_TEST", "clean_notebooks_on_tests", "namespace")
        ]
        for var in to_delete:
            del namespace[var]
        gc.collect()
        logger.info(f"✅ Cleaned up {len(to_delete)} variables")
    else:
        logger.info("⏭ Skipping cleanup during notebook run")

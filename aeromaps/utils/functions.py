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
    """
    with open(file_name, "r", encoding="utf-8") as f:
        parameters_dict = load(f)
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


def create_partitioning(file, path=""):
    """
    Generation of a JSON input file (air transport data) and a CSV file (climate data) for running an AeroMAPS process for a partitioned scope.

    Parameters
    ----------
    file
        Path to the CSV file containing AeroSCOPE data for the partitioned scope.
    path
        Directory path where the generated files will be saved.

    Returns
    -------
    None

    """

    # World input data recovery
    world_data_path = pth.join(data.__path__[0], "parameters.json")
    with open(world_data_path, "r") as parameters_file:
        world_data_dict = json.load(parameters_file)

    # Assumption on freight
    freight_energy_share_2019_partitioned = world_data_dict["freight_energy_share_2019"]

    # AeroSCOPE data recovery
    partitioned_data_df = read_csv(file, delimiter=",")
    partitioned_data = partitioned_data_df.values
    total_ask_2019 = partitioned_data[0, 1]
    short_range_ask_2019 = partitioned_data[0, 2]
    medium_range_ask_2019 = partitioned_data[0, 3]
    long_range_ask_2019 = partitioned_data[0, 4]
    total_seats_2019 = partitioned_data[2, 1]
    total_energy_consumption_per_ask_2019 = partitioned_data[4, 1]
    short_range_energy_consumption_per_ask_2019 = partitioned_data[4, 2]
    medium_range_energy_consumption_per_ask_2019 = partitioned_data[4, 3]
    long_range_energy_consumption_per_ask_2019 = partitioned_data[4, 4]
    total_energy_consumption_2019 = (
        total_energy_consumption_per_ask_2019
        * total_ask_2019
        / (1 - freight_energy_share_2019_partitioned / 2 / 100)
    )  # Dedicated freight (half of total freight) not included in AeroSCOPE
    short_range_energy_consumption_2019 = (
        short_range_energy_consumption_per_ask_2019 * short_range_ask_2019
    ) * (1 - 0.075 / (1 - 0.075))
    medium_range_energy_consumption_2019 = (
        medium_range_energy_consumption_per_ask_2019 * medium_range_ask_2019
    ) * (1 - 0.075 / (1 - 0.075))
    long_range_energy_consumption_2019 = (
        long_range_energy_consumption_per_ask_2019 * long_range_ask_2019
    ) * (1 - 0.075 / (1 - 0.075))

    # Calculation of the partitioned input values

    ## Float inputs
    short_range_energy_share_2019_partitioned = (
        short_range_energy_consumption_2019 / total_energy_consumption_2019 * 100
    )
    medium_range_energy_share_2019_partitioned = (
        medium_range_energy_consumption_2019 / total_energy_consumption_2019 * 100
    )
    long_range_energy_share_2019_partitioned = (
        long_range_energy_consumption_2019 / total_energy_consumption_2019 * 100
    )
    short_range_rpk_share_2019_partitioned = short_range_ask_2019 / total_ask_2019 * 100
    medium_range_rpk_share_2019_partitioned = medium_range_ask_2019 / total_ask_2019 * 100
    long_range_rpk_share_2019_partitioned = long_range_ask_2019 / total_ask_2019 * 100
    commercial_aviation_coefficient_partitioned = 1

    ## Vector inputs
    share_ask_partitioned_vs_world_2019 = total_ask_2019 / world_data_dict["ask_init"][19] * 100
    share_seats_partitioned_vs_world_2019 = total_seats_2019 / (
        world_data_dict["pax_init"][19]
        * world_data_dict["ask_init"][19]
        / world_data_dict["rpk_init"][19]
        * 100
    )
    share_energy_consumption_partitioned_vs_world_2019 = (
        total_energy_consumption_2019 / world_data_dict["energy_consumption_init"][19] * 100
    )
    rpk_init_partitioned = []
    ask_init_partitioned = []
    rtk_init_partitioned = []
    total_aircraft_distance_init_partitioned = []
    freight_init_partitioned = []
    pax_init_partitioned = []
    energy_consumption_init_partitioned = []
    for k in range(0, 20):
        rpk_init_partitioned.append(
            world_data_dict["rpk_init"][k] * share_ask_partitioned_vs_world_2019 / 100
        )
        ask_init_partitioned.append(
            world_data_dict["ask_init"][k] * share_ask_partitioned_vs_world_2019 / 100
        )
        rtk_init_partitioned.append(
            world_data_dict["rtk_init"][k] * share_ask_partitioned_vs_world_2019 / 100
        )
        freight_init_partitioned.append(
            world_data_dict["freight_init"][k] * share_ask_partitioned_vs_world_2019 / 100
        )
        total_aircraft_distance_init_partitioned.append(
            world_data_dict["total_aircraft_distance_init"][k]
            * share_ask_partitioned_vs_world_2019
            / 100
        )
        pax_init_partitioned.append(
            world_data_dict["pax_init"][k] * share_seats_partitioned_vs_world_2019 / 100
        )
        energy_consumption_init_partitioned.append(
            world_data_dict["energy_consumption_init"][k]
            * share_energy_consumption_partitioned_vs_world_2019
            / 100
        )

    historic_start_year_partitioned = world_data_dict["historic_start_year"]
    prospection_start_year_partitioned = world_data_dict["prospection_start_year"]

    # Climate data computation
    climate_world_data_path = pth.join(
        climate_data.__path__[0], "temperature_historical_dataset.csv"
    )
    climate_world_data_df = pd.read_csv(climate_world_data_path, delimiter=";", header=None)
    climate_world_data = climate_world_data_df.values
    climate_world_data_years = climate_world_data[:, 0]
    climate_world_data_co2_emissions = climate_world_data[:, 1]
    climate_world_data_nox_emissions = climate_world_data[:, 2]
    climate_world_data_h2o_emissions = climate_world_data[:, 3]
    climate_world_data_soot_emissions = climate_world_data[:, 4]
    climate_world_data_sulfur_emissions = climate_world_data[:, 5]
    climate_world_data_distance = climate_world_data[:, 6]
    
    climate_partitioned_data_years = climate_world_data_years.tolist()
    climate_partitioned_data_co2_emissions = (
        climate_world_data_co2_emissions * share_energy_consumption_partitioned_vs_world_2019 / 100
    ).tolist()
    climate_partitioned_data_nox_emissions = (
        climate_world_data_nox_emissions * share_energy_consumption_partitioned_vs_world_2019 / 100
    ).tolist()
    climate_partitioned_data_h2o_emissions = (
        climate_world_data_h2o_emissions * share_energy_consumption_partitioned_vs_world_2019 / 100
    ).tolist()
    climate_partitioned_data_soot_emissions = (
        climate_world_data_soot_emissions * share_energy_consumption_partitioned_vs_world_2019 / 100
    ).tolist()
    climate_partitioned_data_sulfur_emissions = (
        climate_world_data_sulfur_emissions
        * share_energy_consumption_partitioned_vs_world_2019
        / 100
    ).tolist()
    climate_partitioned_data_distance = (
        climate_world_data_distance * share_ask_partitioned_vs_world_2019 / 100
    ).tolist()

    # Build years list for other_data (historic_start_year to prospection_start_year - 1)
    other_data_years = list(range(historic_start_year_partitioned, prospection_start_year_partitioned))

    # Generation of a single JSON file with all partitioned inputs
    partitioning_updated_inputs_dict = {
        # Float inputs
        "other_float_data": {
            "short_range_energy_share_2019": short_range_energy_share_2019_partitioned,
            "medium_range_energy_share_2019": medium_range_energy_share_2019_partitioned,
            "long_range_energy_share_2019": long_range_energy_share_2019_partitioned,
            "freight_energy_share_2019": freight_energy_share_2019_partitioned,
            "short_range_rpk_share_2019": short_range_rpk_share_2019_partitioned,
            "medium_range_rpk_share_2019": medium_range_rpk_share_2019_partitioned,
            "long_range_rpk_share_2019": long_range_rpk_share_2019_partitioned,
            "commercial_aviation_coefficient": commercial_aviation_coefficient_partitioned
        },
        # Other data (lists indexed by historic_start_year to prospection_start_year - 1)
        "other_vector_data": {
            "years": other_data_years,
            "rpk_init": rpk_init_partitioned,
            "ask_init": ask_init_partitioned,
            "rtk_init": rtk_init_partitioned,
            "pax_init": pax_init_partitioned,
            "freight_init": freight_init_partitioned,
            "energy_consumption_init": energy_consumption_init_partitioned,
            "total_aircraft_distance_init": total_aircraft_distance_init_partitioned,
        },
        # Climate data (lists indexed by climate_historic_start_year to prospection_start_year - 1)
        "climate_data": {
            "years": climate_partitioned_data_years,
            "co2_emissions": climate_partitioned_data_co2_emissions,
            "nox_emissions": climate_partitioned_data_nox_emissions,
            "h2o_emissions": climate_partitioned_data_h2o_emissions,
            "soot_emissions": climate_partitioned_data_soot_emissions,
            "sulfur_emissions": climate_partitioned_data_sulfur_emissions,
            "distance": climate_partitioned_data_distance,
        },
    }
    partitioning_updated_inputs_path = pth.join(path, "partitioning_updated_inputs.json")
    with open(partitioning_updated_inputs_path, "w") as outfile:
        json.dump(partitioning_updated_inputs_dict, outfile, indent=4)

    return


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
    Specific filter to remove a warning triggered in the absence of a docstring in each discipline.
    Hopefully temporary!!!


    Parameters
    ----------
    logger
        The logger to configure.

    Returns
    -------
    logger
        The configured logger with the custom filter applied.

    """

    # Specific filter to remove a warning triggered in the absence of a docstring in each discipline.
    class SuppressArgsSectionWarning(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.getMessage() != "The Args section is missing."

    for handler in logger.handlers:
        handler.addFilter(SuppressArgsSectionWarning())

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

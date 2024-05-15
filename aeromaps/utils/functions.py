import json
from json import load
import pandas as pd
from pandas import read_csv
import os.path as pth

from aeromaps.resources import data


def _dict_from_json(file_name="parameters.json") -> dict:
    with open(file_name, "r", encoding="utf-8") as f:
        parameters_dict = load(f)

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
            parameters_dict[key] = pd.Series(value)

    return parameters_dict


def _dict_to_df(data, orient="index") -> pd.DataFrame:
    df = pd.DataFrame.from_dict(data, orient=orient)
    return df


def create_partitioning(file, path=''):
    """Generation of a JSON input file for running an AeroMAPS process for a partitioned scope."""

    # AeroSCOPE data recovery
    partitioned_data_df = read_csv(file, delimiter=",")
    partitioned_data = partitioned_data_df.values
    share_ask_partitioned_vs_world_2019 = partitioned_data[5, 1]
    share_seats_partitioned_vs_world_2019 = partitioned_data[6, 1]
    share_energy_consumption_partitioned_vs_world_2019 = partitioned_data[7, 1]
    total_ask_2019 = partitioned_data[0, 1]
    short_range_ask_2019 = partitioned_data[0, 2]
    medium_range_ask_2019 = partitioned_data[0, 3]
    long_range_ask_2019 = partitioned_data[0, 4]
    total_energy_consumption_per_ask_2019 = partitioned_data[4, 1]
    short_range_energy_consumption_per_ask_2019 = partitioned_data[4, 2]
    medium_range_energy_consumption_per_ask_2019 = partitioned_data[4, 3]
    long_range_energy_consumption_per_ask_2019 = partitioned_data[4, 4]
    total_energy_consumption_2019 = total_energy_consumption_per_ask_2019 * total_ask_2019
    short_range_energy_consumption_2019 = (
        short_range_energy_consumption_per_ask_2019 * short_range_ask_2019
    )
    medium_range_energy_consumption_2019 = (
        medium_range_energy_consumption_per_ask_2019 * medium_range_ask_2019
    )
    long_range_energy_consumption_2019 = (
        long_range_energy_consumption_per_ask_2019 * long_range_ask_2019
    )

    # World input data recovery
    world_data_path = pth.join(data.__path__[0], "parameters.json")
    with open(world_data_path, "r") as parameters_file:
        world_data_dict = json.load(parameters_file)

    # Calculation of the partitioned input values

    ## Float inputs
    freight_energy_share_2019_partitioned = world_data_dict["freight_energy_share_2019"]
    passenger_energy_share_2019_partitioned = 100 - freight_energy_share_2019_partitioned
    short_range_energy_share_2019_partitioned = (
        (short_range_energy_consumption_2019 / total_energy_consumption_2019 * 100)
        * passenger_energy_share_2019_partitioned
        / 100
    )
    medium_range_energy_share_2019_partitioned = (
        (medium_range_energy_consumption_2019 / total_energy_consumption_2019 * 100)
        * passenger_energy_share_2019_partitioned
        / 100
    )
    long_range_energy_share_2019_partitioned = (
        (long_range_energy_consumption_2019 / total_energy_consumption_2019 * 100)
        * passenger_energy_share_2019_partitioned
        / 100
    )
    short_range_rpk_share_2019_partitioned = short_range_ask_2019 / total_ask_2019 * 100
    medium_range_rpk_share_2019_partitioned = medium_range_ask_2019 / total_ask_2019 * 100
    long_range_rpk_share_2019_partitioned = long_range_ask_2019 / total_ask_2019 * 100
    commercial_aviation_coefficient_partitioned = 1

    ## Vector inputs
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
            / (
                1 - freight_energy_share_2019_partitioned / 2 / 100
            )  # Dedicated freight (half of total freight) not included in AeroSCOPE
        )

    # Generation of the JSON file
    partitioned_inputs_dict = {
        "rpk_init": rpk_init_partitioned,
        "ask_init": ask_init_partitioned,
        "rtk_init": rtk_init_partitioned,
        "pax_init": pax_init_partitioned,
        "freight_init": freight_init_partitioned,
        "energy_consumption_init": energy_consumption_init_partitioned,
        "total_aircraft_distance_init": total_aircraft_distance_init_partitioned,
        "short_range_energy_share_2019": short_range_energy_share_2019_partitioned,
        "medium_range_energy_share_2019": medium_range_energy_share_2019_partitioned,
        "long_range_energy_share_2019": long_range_energy_share_2019_partitioned,
        "freight_energy_share_2019": freight_energy_share_2019_partitioned,
        "short_range_rpk_share_2019": short_range_rpk_share_2019_partitioned,
        "medium_range_rpk_share_2019": medium_range_rpk_share_2019_partitioned,
        "long_range_rpk_share_2019": long_range_rpk_share_2019_partitioned,
        "commercial_aviation_coefficient": commercial_aviation_coefficient_partitioned,
    }
    partitioned_inputs_path = pth.join(path, "partitioned_inputs.json")
    with open(partitioned_inputs_path, "w") as outfile:
        json.dump(partitioned_inputs_dict, outfile)

    return

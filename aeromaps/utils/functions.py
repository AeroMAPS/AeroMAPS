import json
from json import load
import numpy as np
import pandas as pd
from pandas import read_csv
import os.path as pth

from aeromaps.resources import data
from aeromaps.resources import climate_data


def _dict_from_json(file_name="parameters.json") -> dict:
    with open(file_name, "r", encoding="utf-8") as f:
        parameters_dict = load(f)
    dict = _dict_from_parameters_dict(parameters_dict)
    return dict


def _dict_from_parameters_dict(parameters_dict) -> dict:
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
    # Check if values from data have the same length or else populate with NaN
    max_len = max([len(v) for v in data.values()])
    for key, value in data.items():
        if len(value) < max_len:
            data[key] = np.append(value, np.full(max_len - len(value), np.nan))

    df = pd.DataFrame.from_dict(data, orient=orient)
    return df


def create_partitioning(file, path=""):
    """Generation of a JSON input file (air transport data) and a CSV file (climate data) for running an AeroMAPS process for a partitioned scope."""

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

    # TODO move historic and prospection start year out of custom input file

    historic_start_year_partitioned = world_data_dict["historic_start_year"]
    prospection_start_year_partitioned = world_data_dict["prospection_start_year"]

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
        "historic_start_year": historic_start_year_partitioned,
        "prospection_start_year": prospection_start_year_partitioned,
    }
    partitioned_inputs_path = pth.join(path, "partitioned_inputs.json")
    with open(partitioned_inputs_path, "w") as outfile:
        json.dump(partitioned_inputs_dict, outfile)

    # Generation of a CSV file for using climate models
    climate_world_data_path = pth.join(
        climate_data.__path__[0], "temperature_historical_dataset.csv"
    )
    climate_world_data_df = pd.read_csv(climate_world_data_path, delimiter=";")
    climate_world_data = climate_world_data_df.values
    climate_world_data_years = climate_world_data[:, 0]
    climate_world_data_co2_emissions = climate_world_data[:, 1]
    climate_world_data_nox_emissions = climate_world_data[:, 2]
    climate_world_data_h2o_emissions = climate_world_data[:, 3]
    climate_world_data_soot_emissions = climate_world_data[:, 4]
    climate_world_data_sulfur_emissions = climate_world_data[:, 5]
    climate_world_data_distance = climate_world_data[:, 6]
    climate_partitioned_data_years = climate_world_data_years
    climate_partitioned_data_co2_emissions = (
        climate_world_data_co2_emissions * share_energy_consumption_partitioned_vs_world_2019 / 100
    )
    climate_partitioned_data_nox_emissions = (
        climate_world_data_nox_emissions * share_energy_consumption_partitioned_vs_world_2019 / 100
    )
    climate_partitioned_data_h2o_emissions = (
        climate_world_data_h2o_emissions * share_energy_consumption_partitioned_vs_world_2019 / 100
    )
    climate_partitioned_data_soot_emissions = (
        climate_world_data_soot_emissions * share_energy_consumption_partitioned_vs_world_2019 / 100
    )
    climate_partitioned_data_sulfur_emissions = (
        climate_world_data_sulfur_emissions
        * share_energy_consumption_partitioned_vs_world_2019
        / 100
    )
    climate_partitioned_data_distance = (
        climate_world_data_distance * share_ask_partitioned_vs_world_2019 / 100
    )
    climate_partitioned_data_years_number = len(climate_partitioned_data_years)
    partitioned_historical_climate_dataset = np.zeros((climate_partitioned_data_years_number, 7))
    for k in range(0, climate_partitioned_data_years_number):
        partitioned_historical_climate_dataset[k, 0] = climate_partitioned_data_years[k]
        partitioned_historical_climate_dataset[k, 1] = climate_partitioned_data_co2_emissions[k]
        partitioned_historical_climate_dataset[k, 2] = climate_partitioned_data_nox_emissions[k]
        partitioned_historical_climate_dataset[k, 3] = climate_partitioned_data_h2o_emissions[k]
        partitioned_historical_climate_dataset[k, 4] = climate_partitioned_data_soot_emissions[k]
        partitioned_historical_climate_dataset[k, 5] = climate_partitioned_data_sulfur_emissions[k]
        partitioned_historical_climate_dataset[k, 6] = climate_partitioned_data_distance[k]
    climate_partitioned_data_path = pth.join(path, "partitioned_temperature_historical_dataset.csv")
    np.savetxt(climate_partitioned_data_path, partitioned_historical_climate_dataset, delimiter=";")

    return

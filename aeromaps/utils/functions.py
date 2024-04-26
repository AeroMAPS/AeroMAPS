from json import load
import pandas as pd


def _dict_from_json(file_name="parameters.json") -> dict:
    with open(file_name, "r", encoding="utf-8") as f:
        parameters_dict = load(f)

    for key, value in parameters_dict.items():
        # TODO: generic handling of timetables
        if isinstance(value, list) and key in [
            'rpk_init',
            'ask_init',
            'rtk_init',
            'pax_init',
            'freight_init',
            'energy_consumption_init',
            'total_aircraft_distance_init'
        ]:
            parameters_dict[key] = pd.Series(value)

    return parameters_dict


def _dict_to_df(data, orient="index") -> pd.DataFrame:
    df = pd.DataFrame.from_dict(data, orient=orient)
    return df

"""
fleet_model push
===========

Module for modeling aircraft fleet composition and renewal over time.

This module provides data structures and models for representing aircraft fleets,
including individual aircraft, subcategories (e.g., narrow-body recent, narrow-body old), and
categories (e.g., narrow-body, wide-body). It supports fleet
evolution modeling using yearly aircraft delivery volumes, and computes energy consumption, emissions (NOx, soot), and
operating costs based on fleet composition.

The module uses 1 dictionary to define market segments relatively to the current fleet. It can use a second dictionnary to define aircraft type aggregation on each segment.
These dictionnaries are aggregated in a YAML file, including the parameters that were calibrated on past data. These parameters can also be modified by hand by conifgurating the YAML file.

Then, a YAML configuration files to define in production and future aircraft models, allowing a flexible customization of fleet scenarios.
Finally, a YAML file allows to configurate growth rates per year per market, and possibly adjust on these market retirement and utilisation age sensibilities.
"""

import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import time as tm

from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model_push_visualisations import (
    visualise_10y_seats_deliveries_by_submarket, visu_deliveries_array, visu_retirements_array,visu_fleet_array,
    visu_retirement_age, visu_energy_intensity)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model_push_calculations import i_d, solve_deliv, fleet_content


def _project_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _resolve_project_path(path_like: str | Path) -> Path:
    path = Path(path_like)
    if path.is_absolute():
        return path
    return (_project_root() / path).resolve()


def _load_yaml(path_like: str | Path) -> dict:
    with _resolve_project_path(path_like).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _build_aircraft_to_submarket_mapping(classification_data: dict) -> dict[str, str]:
    return {
        str(aircraft_type).strip(): str(submarket).strip()
        for item in classification_data.get("aircraft_types", [])
        if isinstance(item, dict)
        for aircraft_type, submarket in item.items()
    }


def _build_submarket_to_types_mapping(aircraft_to_submarket: dict[str, str]) -> dict[str, list[str]]:
    submarket_to_types = {}
    for aircraft_type, submarket in aircraft_to_submarket.items():
        submarket_to_types.setdefault(submarket, []).append(aircraft_type)
    return submarket_to_types


def calculate_stats_by_submarket(
    classification_yaml_path: str,
    aircraft_parameters_excel_path: str,
    excel_sheet_name=0,
) -> pd.DataFrame:
    """
    Compute aggregated statistics by submarket from:
    - a YAML file mapping aircraft types to submarkets
    - an Excel file containing aircraft parameters by type

    Returns
    -------
    pd.DataFrame
        DataFrame containing aggregated totals by submarket.
    """
    classification_data = _load_yaml(classification_yaml_path)
    mapping = _build_aircraft_to_submarket_mapping(classification_data)

    df = pd.read_excel(_resolve_project_path(aircraft_parameters_excel_path), sheet_name=excel_sheet_name)
    df = df.copy()
    df["submarket"] = df["Aircraft Type"].astype(str).str.strip().map(mapping)
    df["total_ask_produced_2024"] = pd.to_numeric(df["total_ask_produced_2024"], errors="coerce")
    df["adj_distance_aircraft_year(km)"] = pd.to_numeric(
        df["adj_distance_aircraft_year(km)"], errors="coerce"
    )
    df["MJ_fuel_ask"] = pd.to_numeric(df["MJ_fuel_ask"], errors="coerce")

    df = df[
        df["submarket"].notna()
        & df["total_ask_produced_2024"].notna()
        & df["adj_distance_aircraft_year(km)"].notna()
        & (df["adj_distance_aircraft_year(km)"] != 0)
        & df["MJ_fuel_ask"].notna()
    ].copy()

    if df.empty:
        raise ValueError("No valid rows remain after filtering missing or invalid values.")

    df["ask_over_distance"] = df["total_ask_produced_2024"] / df["adj_distance_aircraft_year(km)"]
    df["MJ_fuel_ask_weighted"] = df["MJ_fuel_ask"] * df["total_ask_produced_2024"]

    grouped = df.groupby("submarket", as_index=False).agg(
        total_adjusted_asks=("total_ask_produced_2024", "sum"),
        ask_over_distance_sum=("ask_over_distance", "sum"),
        MJ_fuel_ask_weighted_sum=("MJ_fuel_ask_weighted", "sum"),
    )

    grouped["distance_aircraft_year_segment"] = (
        grouped["total_adjusted_asks"] / grouped["ask_over_distance_sum"]
    )
    grouped["MJ_fuel_ask_segment"] = (
        grouped["MJ_fuel_ask_weighted_sum"] / grouped["total_adjusted_asks"]
    )
    return grouped[
        [
            "submarket",
            "total_adjusted_asks",
            "distance_aircraft_year_segment",
            "MJ_fuel_ask_segment",
        ]
    ]


def fleet_process(classification_yaml_path: str,
    market_param_yaml_path: str,
    in_production_yaml_path: str,
    new_aircraft_yaml_path: str,
    aircraft_parameters_excel_path: str,
    fleet_excel_path: str,
    aircraft_parameters_sheet_name=0,
    fleet_sheet_name=0,
                  ):
    a = tm.time()

    classification_data = _load_yaml(classification_yaml_path)
    market_data_config = _load_yaml(market_param_yaml_path)
    in_production_fleet_data = _load_yaml(in_production_yaml_path)
    new_fleet_data = _load_yaml(new_aircraft_yaml_path)

    classification_yaml_path = _resolve_project_path(classification_yaml_path)
    market_param_yaml_path = _resolve_project_path(market_param_yaml_path)
    in_production_yaml_path = _resolve_project_path(in_production_yaml_path)
    new_aircraft_yaml_path = _resolve_project_path(new_aircraft_yaml_path)
    aircraft_parameters_excel_path = _resolve_project_path(aircraft_parameters_excel_path)
    fleet_excel_path = _resolve_project_path(fleet_excel_path)

    markets = calculate_stats_by_submarket(
        classification_yaml_path=classification_yaml_path,
        aircraft_parameters_excel_path=aircraft_parameters_excel_path,
    )
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    print(markets)
    pd.reset_option("display.max_rows")
    pd.reset_option("display.max_columns")
    pd.reset_option("display.width")

    mapping_types = _build_aircraft_to_submarket_mapping(classification_data)
    submarket_to_types = _build_submarket_to_types_mapping(mapping_types)

    fleet_df = pd.read_excel(fleet_excel_path, sheet_name=fleet_sheet_name).copy()
    params_df = pd.read_excel(aircraft_parameters_excel_path, sheet_name=aircraft_parameters_sheet_name).copy()

    fleet_df["Aircraft Type"] = fleet_df["Aircraft Type"].astype(str).str.strip()
    params_df["Aircraft Type"] = params_df["Aircraft Type"].astype(str).str.strip()
    fleet_df["submarket"] = fleet_df["Aircraft Type"].map(mapping_types)
    params_df["submarket"] = params_df["Aircraft Type"].map(mapping_types)

    rows = []
    for market, content in new_fleet_data["markets"].items():
        for aircraft in content.get("new_aircraft_types", []):
            row = aircraft.copy()
            row["market"] = market
            rows.append(row)
    new_ac_carac = pd.DataFrame(rows)
    if not new_ac_carac.empty:
        new_ac_carac["market"] = new_ac_carac["market"].astype(str).str.strip()

    rows = []
    for market, content in in_production_fleet_data["markets"].items():
        for aircraft in content.get("current_aircraft_types", []):
            ref_points = aircraft.get("reference_production_points", [])
            years = [p["year"] for p in ref_points]
            values = [p["value"] for p in ref_points]
            rows.append(
                {
                    "name": aircraft["name"],
                    "market": market,
                    "energy_efficiency": aircraft["energy_efficiency"],
                    "seats": aircraft["seats"],
                    "ret_year_delay": aircraft["ret_year_delay"],
                    "production_profile": [years, values],
                }
            )
    in_prod_ac_carac = pd.DataFrame(rows)
    if not in_prod_ac_carac.empty:
        in_prod_ac_carac["market"] = in_prod_ac_carac["market"].astype(str).str.strip()

    rows = []
    for market, content in market_data_config["markets"].items():
        ref_points = content.get("reference_growth", [])
        years = [p["year"] for p in ref_points]
        rate = [p["rate"] for p in ref_points]
        rows.append(
            {
                "market": market,
                "age_utilisation_sensib": content["age_utilisation_sensib"],
                "age_retirement_sensib": content["age_retirement_sensib"],
                "production_profile": [years, rate],
            }
        )
    markets_data = pd.DataFrame(rows)
    if not in_prod_ac_carac.empty:
        markets_data["market"] = markets_data["market"].astype(str).str.strip()
    markets_data.index = markets_data["market"]

    print(f"Time to load the settings: {tm.time() - a:.2f}s")
    for i in range(markets.shape[0]):
        market_name = markets.iloc[i, 0]
        total_asks = markets.iloc[i, 1]
        distance_per_aircraft = markets.iloc[i, 2]
        print(f"Submarket: {market_name}")
        keys_market = submarket_to_types.get(market_name, [])

        selec_fleet = fleet_df[fleet_df["Aircraft Type"].isin(keys_market)]
        old_ac_carac = params_df[params_df["Aircraft Type"].isin(keys_market)]
        selec_new_ac = new_ac_carac[new_ac_carac["market"] == market_name]
        selec_in_prod_ac = in_prod_ac_carac[in_prod_ac_carac["market"] == market_name]
        market_data = markets_data.loc[market_name]
        ac_names = list(old_ac_carac["Aircraft Type"]) + list(selec_in_prod_ac["name"]) + list(selec_new_ac["name"])
        years, deliveries, ask_content, fleet_content, energy_content = market_process(total_asks, market_data, distance_per_aircraft, selec_fleet, old_ac_carac,
                                              selec_in_prod_ac, selec_new_ac)
        visu_fleet_array(ask_content[1:].sum(axis=1), ac_names,'ASK')
        # visu_fleet_array(fleet_content[1:].sum(axis=1), ac_names, 'Aircraft seats')
        visu_fleet_array(deliveries, ac_names, '# Aircraft produced')
        visu_retirements_array(fleet_content, ac_names)  # to see the aircraft seats outflow
        # visu_retirements_array(ask_content, ac_names) # to see the ask outflow
        visu_retirement_age(fleet_content, ac_names)
        visu_fleet_array(energy_content[1:].sum(axis=1), ac_names, 'energy consumption (MJ)')
        visu_energy_intensity(energy_content, ask_content, years, market_name)

    return None


def market_process(total_asks, market_data, distance_per_aircraft, fleet_market, old_ac_carac, in_prod_ac_carac, future_ac_carac):
    market_growth = market_data["production_profile"]
    age_utilisation_sensibility = market_data['age_utilisation_sensib']
    age_retirement_sensibility = market_data['age_retirement_sensib']
    #traffic evolution
    growth_rates = (market_growth[0][0]-2024)*[market_growth[1][0]]
    for i in range(len(market_growth[0])-1):
        growth_rates+=(market_growth[0][i+1]-market_growth[0][i])*[market_growth[1][i+1]]
    growth_rates = np.log(1+np.array(growth_rates))
    growth_rates_cum = np.concatenate([np.array([0]),np.cumsum(growth_rates)])

    yearly_traffic = total_asks*np.exp(growth_rates_cum)
    years = np.arange(2025,market_growth[0][-1]+1)
    modeled_periods = years.shape[0]
    n_old_ac = old_ac_carac.shape[0]
    n_prod_ac = in_prod_ac_carac.shape[0]
    n_new_ac = future_ac_carac.shape[0]
    #fleet array
    fleet_ini = (fleet_market.values[:,1:-1].T).astype(float)
    fleet_ini = np.hstack((fleet_ini, np.zeros((fleet_ini.shape[0],n_prod_ac+n_new_ac))))
    fleet_ini = np.vstack((fleet_ini, np.zeros((modeled_periods,fleet_ini.shape[1]))))
    # fuel intensity array
    energy_intensity = np.concatenate([old_ac_carac["MJ_fuel_ask"].values, in_prod_ac_carac["energy_efficiency"].values, future_ac_carac["energy_efficiency"].values])
    #seats array
    seats_array = np.concatenate([old_ac_carac["average_seats"].values, in_prod_ac_carac["seats"].values, future_ac_carac["seats"].values])
    #productivity array
    kms_array = np.concatenate([old_ac_carac["adj_distance_aircraft_year(km)"].values, np.array((in_prod_ac_carac.shape[0]+future_ac_carac.shape[0])*[distance_per_aircraft])])
    prod_array = kms_array * seats_array
    period_utilisation_array = np.exp(age_utilisation_sensibility * np.arange(modeled_periods+1))
    age_utilisation_array = np.exp(-age_utilisation_sensibility * (np.arange(fleet_ini.shape[0])-fleet_ini.shape[0]+modeled_periods+1))
    #deliveries array
    deliveries_ini = np.zeros(fleet_ini.shape[1])
    deliveries = np.array([deliveries_ini] *(modeled_periods) )
    production_profiles = in_prod_ac_carac["production_profile"].values
    # in production aircraft volumes
    for ac in range(n_prod_ac):
        production_profile = production_profiles[ac]
        production_volumes = np.array([])
        tot_production_y = production_profile[0][-1]-production_profile[0][0]
        for i in range(len(production_profile[0]) - 1):
            n_y = production_profile[0][i+1] - production_profile[0][i]
            prod_ref = production_profile[1][i]
            prod_ev = production_profile[1][i+1]-prod_ref
            production_volumes = np.concatenate([production_volumes,np.arange(n_y)/(n_y-1) * prod_ev + prod_ref])
        deliveries[-modeled_periods:-modeled_periods+tot_production_y,n_old_ac+ac] = production_volumes
    # future aircraft volumes
    delivery_params = future_ac_carac[['intro_year', 'production_duration','renewal_rate', 'time_to_market','seats']].values
    for ac in range(n_new_ac):
        eis = (delivery_params[ac, 0]-2025).astype(int)
        duration = delivery_params[ac, 1].astype(int)
        time_to_market = delivery_params[ac, 3]
        prod_volume = yearly_traffic[eis] * delivery_params[ac, 2]/distance_per_aircraft/delivery_params[ac, 4]
        mu, gamma = solve_deliv(time_to_market, duration)
        for t in range(duration):
            if eis + t + 1 < modeled_periods:
                deliveries_ac_t = prod_volume * mu * i_d(gamma, duration, t,(t + 1))
                deliveries[-modeled_periods+eis +t,n_old_ac + n_prod_ac + ac] = deliveries_ac_t  # +1->empty_delivery first
    # fleet activity check
    fleet_delivered = fleet_ini.copy()
    fleet_delivered[-modeled_periods:,:] = deliveries
    fleet_delivered_activity_type_y = (fleet_delivered*age_utilisation_array[:,None]*prod_array[None,:])
    fleet_delivered_activity_y = fleet_delivered_activity_type_y.sum(axis = 1)
    fleet_delivered_activity = np.cumsum(fleet_delivered_activity_y, axis=0)[-1-modeled_periods:]*period_utilisation_array
    # plt.plot(np.concatenate([np.array([2024]),years]),fleet_delivered_activity)
    # plt.plot(np.concatenate([np.array([2024]),years]),yearly_traffic)
    # plt.show()
    if np.any(fleet_delivered_activity < 0.999999*yearly_traffic):
        raise ValueError("not enough aircraft in the fleet to meet the demand in market segment")

    #retirement propensity array
    ret_year_delay_type = np.concatenate([old_ac_carac["retirement_propensions"].values, in_prod_ac_carac["ret_year_delay"].values*age_retirement_sensibility, future_ac_carac["ret_year_delay"].values*age_retirement_sensibility])
    ret_year_delay_type_y = ret_year_delay_type[None,:]+(age_retirement_sensibility*np.arange(fleet_ini.shape[0]))[:, None]
    ret_year_delay_type_y+= (0.1338-age_retirement_sensibility)*(fleet_ini.shape[0]-modeled_periods)
    # fleet composition convergence
    aircraft_seats_volumes = []
    ask_volumes = []
    x_eq = 1
    print('Computing fleet composition...')
    for t in range(modeled_periods):
        fleet_delivered_activity_type_y_t = fleet_delivered_activity_type_y.copy()
        fleet_delivered_activity_type_y_t[-modeled_periods+t:,:] = 0
        fleet_delivered_activity_type_y_t = fleet_delivered_activity_type_y_t*period_utilisation_array[t]
        ask_volumes_type_y_t, x_eq = fleet_content(
            0, x_eq, fleet_delivered_activity_type_y_t, ret_year_delay_type_y,
            yearly_traffic[t], epsilon=1e-6, first=True
        )
        if x_eq < 1e-30:
            x_eq = x_eq ** (1 / 8)
            ret_year_delay_type_y = ret_year_delay_type_y - 3 * np.log(2)

        aircraft_seats_volumes_t = ask_volumes_type_y_t/period_utilisation_array[t]/age_utilisation_array[:,None]/kms_array[None,:]
        aircraft_seats_volumes.append(aircraft_seats_volumes_t)
        ask_volumes.append(ask_volumes_type_y_t)
    ask_volumes = np.array(ask_volumes)
    aircraft_seats_volumes = np.array(aircraft_seats_volumes)
    energy_consumption = energy_intensity[None, None, :] * ask_volumes
    return years, deliveries[:-1], ask_volumes, aircraft_seats_volumes, energy_consumption









# production_volumes = visualise_10y_seats_deliveries_by_submarket(
# classification_yaml_path="aeromaps/resources/data/default_fleet_push/default_aircraft_classification.yaml",
# aircraft_parameters_excel_path="aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/aircraft_type_key_parameters.xlsx",
# fleet_excel_path = "aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/agg_fleet_2024.xlsx",
# )

# fleet_process(
#     classification_yaml_path="aeromaps/resources/data/default_fleet_push/default_aircraft_classification.yaml",
#     market_param_yaml_path="aeromaps/resources/data/default_fleet_push/default_market_param.yaml",
#     in_production_yaml_path="aeromaps/resources/data/default_fleet_push/default_in_production_aircraft_inventory.yaml",
#     new_aircraft_yaml_path="aeromaps/resources/data/default_fleet_push/default_new_aircraft_inventory.yaml",
#     aircraft_parameters_excel_path="aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/aircraft_type_key_parameters.xlsx",
#     fleet_excel_path="aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/agg_fleet_end_2024.xlsx",
# )

fleet_process(
    classification_yaml_path="aeromaps/resources/data/default_fleet_push/default_aircraft_classification.yaml",
    market_param_yaml_path="aeromaps/resources/data/default_fleet_push/default_market_param.yaml",
    in_production_yaml_path="aeromaps/resources/data/default_fleet_push/default_in_production_aircraft_inventory.yaml",
    new_aircraft_yaml_path="aeromaps/resources/data/default_fleet_push/default_new_aircraft_inventory.yaml",
    aircraft_parameters_excel_path="aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/aircraft_type_key_parameters.xlsx",
    fleet_excel_path="aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/agg_fleet_end_2024.xlsx",
)



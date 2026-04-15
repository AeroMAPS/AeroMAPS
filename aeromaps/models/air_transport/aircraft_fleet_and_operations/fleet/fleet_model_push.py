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
from scipy import integrate, optimize



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
    module_dir = Path(__file__).resolve().parent
    project_root = module_dir.parents[4]

    classification_yaml_path = Path(classification_yaml_path)
    if not classification_yaml_path.is_absolute():
        classification_yaml_path = (project_root / classification_yaml_path).resolve()

    aircraft_parameters_excel_path = Path(aircraft_parameters_excel_path)
    if not aircraft_parameters_excel_path.is_absolute():
        aircraft_parameters_excel_path = (project_root / aircraft_parameters_excel_path).resolve()

    with classification_yaml_path.open("r", encoding="utf-8") as f:
        classification_data = yaml.safe_load(f) or {}

    mapping = {
        str(aircraft_type).strip(): str(submarket).strip()
        for item in classification_data.get("aircraft_types", [])
        if isinstance(item, dict)
        for aircraft_type, submarket in item.items()
    }

    df = pd.read_excel(aircraft_parameters_excel_path, sheet_name=excel_sheet_name)
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


def visualise_5y_seats_deliveries_by_submarket(
    classification_yaml_path: str,
    aircraft_parameters_excel_path: str,
    fleet_excel_path: str,
    aircraft_parameters_sheet_name=0,
    fleet_sheet_name=0,
) -> pd.DataFrame:
    """
    Compute and visualise weighted aircraft production volumes by submarket over 2020-2024.

    The weighted volume for each aircraft type is:
        production_volume * average_seats

    Then values are aggregated by submarket for each year.

    Parameters
    ----------
    classification_yaml_path : str
        Path to the YAML file mapping aircraft types to submarkets.
    aircraft_parameters_excel_path : str
        Path to the Excel file containing at least:
        - 'Aircraft Type'
        - 'average_seats'
    fleet_excel_path : str
        Path to the Excel file containing aircraft production volumes:
        - aircraft types in index or first column
        - years as columns
    aircraft_parameters_sheet_name : int or str, default=0
        Sheet name/index for the aircraft parameters Excel file.
    production_sheet_name : int or str, default=0
        Sheet name/index for the production Excel file.

    Returns
    -------
    pd.DataFrame
        Aggregated weighted production volumes by submarket and year.
    """
    module_dir = Path(__file__).resolve().parent
    project_root = module_dir.parents[4]

    classification_yaml_path = Path(classification_yaml_path)
    if not classification_yaml_path.is_absolute():
        classification_yaml_path = (project_root / classification_yaml_path).resolve()

    aircraft_parameters_excel_path = Path(aircraft_parameters_excel_path)
    if not aircraft_parameters_excel_path.is_absolute():
        aircraft_parameters_excel_path = (project_root / aircraft_parameters_excel_path).resolve()

    fleet_excel_path = Path(fleet_excel_path)
    if not fleet_excel_path.is_absolute():
        fleet_excel_path = (project_root / fleet_excel_path).resolve()


    with classification_yaml_path.open("r", encoding="utf-8") as f:
        classification_data = yaml.safe_load(f) or {}

    mapping = {
        str(aircraft_type).strip(): str(submarket).strip()
        for item in classification_data.get("aircraft_types", [])
        if isinstance(item, dict)
        for aircraft_type, submarket in item.items()
    }

    params_df = pd.read_excel(aircraft_parameters_excel_path, sheet_name=aircraft_parameters_sheet_name)
    params_df = params_df.copy()
    params_df["Aircraft Type"] = params_df["Aircraft Type"].astype(str).str.strip()
    params_df["submarket"] = params_df["Aircraft Type"].map(mapping)
    params_df["average_seats"] = pd.to_numeric(params_df["average_seats"], errors="coerce")

    params_df = params_df[params_df["submarket"].notna() & params_df["average_seats"].notna()].copy()

    production_df = pd.read_excel(
        fleet_excel_path,
        sheet_name=fleet_sheet_name,
        index_col=0,
    )

    production_df = production_df.copy()
    production_df.index = production_df.index.astype(str).str.strip()
    production_df.columns = [str(col).strip() for col in production_df.columns]

    years = [2020, 2021, 2022, 2023, 2024]
    result_rows = []

    for year in years:
        year_col = str(year)

        merged = params_df[["Aircraft Type", "submarket", "average_seats"]].merge(
            production_df[[year_col]],
            left_on="Aircraft Type",
            right_index=True,
            how="inner",
        )

        merged[year_col] = pd.to_numeric(merged[year_col], errors="coerce")
        merged = merged[merged[year_col].notna()].copy()

        merged["weighted_seats_deliveries"] = merged[year_col] * merged["average_seats"]

        grouped = (
            merged.groupby("submarket", as_index=False)["weighted_seats_deliveries"]
            .sum()
            .assign(year=year)
        )

        result_rows.append(grouped)

    result_df = pd.concat(result_rows, ignore_index=True)

    pivot_df = result_df.pivot(index="submarket", columns="year", values="weighted_seats_deliveries").fillna(0.0)
    pivot_df = pivot_df[years]

    ax = pivot_df.T.plot(
        kind="bar",
        figsize=(12, 6),
        width=0.85,
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Seats production volumes")
    ax.legend(title="Submarket", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    plt.yscale('log')
    plt.tight_layout()
    plt.show()

    return result_df



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

    module_dir = Path(__file__).resolve().parent
    project_root = module_dir.parents[4]

    classification_yaml_path = Path(classification_yaml_path)
    if not classification_yaml_path.is_absolute():
        classification_yaml_path = (project_root / classification_yaml_path).resolve()

    market_param_yaml_path = Path(market_param_yaml_path)
    if not market_param_yaml_path.is_absolute():
        market_param_yaml_path = (project_root / market_param_yaml_path).resolve()

    in_production_yaml_path = Path(in_production_yaml_path)
    if not in_production_yaml_path.is_absolute():
        in_production_yaml_path = (project_root / in_production_yaml_path).resolve()

    new_aircraft_yaml_path = Path(new_aircraft_yaml_path)
    if not new_aircraft_yaml_path.is_absolute():
        new_aircraft_yaml_path = (project_root / new_aircraft_yaml_path).resolve()

    aircraft_parameters_excel_path = Path(aircraft_parameters_excel_path)
    if not aircraft_parameters_excel_path.is_absolute():
        aircraft_parameters_excel_path = (project_root / aircraft_parameters_excel_path).resolve()

    fleet_excel_path = Path(fleet_excel_path)
    if not fleet_excel_path.is_absolute():
        fleet_excel_path = (project_root / fleet_excel_path).resolve()

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

    with classification_yaml_path.open("r", encoding="utf-8") as f:
        classification_data = yaml.safe_load(f) or {}
    mapping_types = {
        str(aircraft_type).strip(): str(submarket).strip()
        for item in classification_data.get("aircraft_types", [])
        if isinstance(item, dict)
        for aircraft_type, submarket in item.items()
    }

    # Inverse mapping: submarket -> aircraft types
    submarket_to_types = {}
    for aircraft_type, submarket in mapping_types.items():
        submarket_to_types.setdefault(submarket, []).append(aircraft_type)

    fleet_df = pd.read_excel(fleet_excel_path, sheet_name=fleet_sheet_name).copy()
    params_df = pd.read_excel(aircraft_parameters_excel_path, sheet_name=aircraft_parameters_sheet_name).copy()

    # Precompute submarket once
    fleet_df["Aircraft Type"] = fleet_df["Aircraft Type"].astype(str).str.strip()
    params_df["Aircraft Type"] = params_df["Aircraft Type"].astype(str).str.strip()
    fleet_df["submarket"] = fleet_df["Aircraft Type"].map(mapping_types)
    params_df["submarket"] = params_df["Aircraft Type"].map(mapping_types)

    with new_aircraft_yaml_path.open("r", encoding="utf-8") as f:
        new_fleet_data = yaml.safe_load(f) or {}
    rows = []
    for market, content in new_fleet_data["markets"].items():
        for aircraft in content.get("new_aircraft_types", []):
            row = aircraft.copy()
            row["market"] = market
            rows.append(row)
    new_ac_carac = pd.DataFrame(rows)
    if not new_ac_carac.empty:
        new_ac_carac["market"] = new_ac_carac["market"].astype(str).str.strip()

    with in_production_yaml_path.open("r", encoding="utf-8") as f:
        in_production_fleet_data = yaml.safe_load(f) or {}
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
                    "ret_prop": aircraft["ret_prop"],
                    "production_profile": [years, values],
                }
            )
    in_prod_ac_carac = pd.DataFrame(rows)
    if not in_prod_ac_carac.empty:
        in_prod_ac_carac["market"] = in_prod_ac_carac["market"].astype(str).str.strip()

    with market_param_yaml_path.open("r", encoding="utf-8") as f:
        growth_data = yaml.safe_load(f) or {}
    growth_rates = {
        str(market).strip(): ([v["year"] for v in values], [v["rate"] for v in values])
        for market, values in growth_data.get("markets_growths", {}).items()
    }
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
        market_growth = growth_rates.get(market_name)

        fleet_content_market = market_process(total_asks, market_growth, distance_per_aircraft, selec_fleet, old_ac_carac, selec_in_prod_ac, selec_new_ac)
            # suite du traitement...
    return None


def market_process(total_asks, market_growth, distance_per_aircraft, fleet_market, old_ac_carac, in_prod_ac_carac, future_ac_carac):
    #traffic evolution
    growth_rates = (market_growth[0][0]-2025)*[market_growth[1][0]]
    for i in range(len(market_growth[0])-1):
        growth_rates+=(market_growth[0][i+1]-market_growth[0][i])*[market_growth[1][i+1]]
    growth_rates = np.log(1+np.array(growth_rates))
    growth_rates_cum = np.cumsum(growth_rates)
    yearly_traffic = total_asks*np.exp(growth_rates_cum)
    years = np.arange(2025,market_growth[0][-1])
    modeled_periods = years.shape[0]
    n_old_ac = old_ac_carac.shape[0]
    n_prod_ac = in_prod_ac_carac.shape[0]
    n_new_ac = future_ac_carac.shape[0]

    #fleet array
    ac_names = list(old_ac_carac["Aircraft Type"]) + list(in_prod_ac_carac["name"]) + list(future_ac_carac["name"])
    fleet_ini = fleet_market.values[:,1:]
    fleet_ini = np.hstack((fleet_ini, np.zeros((n_old_ac, n_prod_ac+n_new_ac))))
    fleet_ini = np.vstack((fleet_ini, np.zeros((modeled_periods, fleet_ini.shape[1]))))
    #seats array
    seats_array = np.concatenate([old_ac_carac["avg_seats"].values, in_prod_ac_carac["seats"].values, future_ac_carac["seats"].values])
    #productivity array
    kms_array = np.concatenate([old_ac_carac["adj_distance_aircraft_year(km)"].values, np.array((in_prod_ac_carac.shape[0]+future_ac_carac.shape[0])*[distance_per_aircraft])])
    prod_array = kms_array * seats_array
    #deliveries array
    deliveries_ini = np.zeros(fleet_ini.shape[1])
    deliveries = np.array([deliveries_ini] * modeled_periods)

    production_profiles = in_prod_ac_carac["production_profile"].values
    for ac in range(n_prod_ac):
        production_profile = production_profiles[ac]
        production_volumes = np.array([])
        for i in range(len(production_profile[0]) - 1):
            n_y = production_profile[0][i+1] - production_profile[0][i]
            prod_ref = production_profile[1][i]
            prod_ev = production_profile[1][i+1]-prod_ref
            production_volumes = np.concatenate([production_volumes,np.arange(n_y)/(n_y-1) * prod_ev + prod_ref])
        deliveries[n_old_ac+ac,-modeled_periods:] = production_volumes

    delivery_params = future_ac_carac[['intro_year', 'production_duration','renewal_rate', 'time_to_market','seats']].values
    for ac in range(n_new_ac):
        eis = delivery_params[ac, 0]-2025
        duration = delivery_params[ac, 1]
        time_to_market = delivery_params[ac, 2]
        prod_volume = yearly_traffic[eis] * delivery_params[ac, 3]/distance_per_aircraft/delivery_params[ac, 4]
        mu, gamma = solve_deliv(time_to_market, duration)
        for t in range(duration):
            if eis + t + 1 < modeled_periods:
                deliveries_ac_t = prod_volume * mu * I_d(gamma, duration, t,(t + 1))
                deliveries[n_old_ac + n_new_ac + ac, -modeled_periods+eis +t] = deliveries_ac_t  # +1->empty_delivery first


    if cum_fleet.sum(axis =(1,2))<yearly_traffic:
        print("Not enough aircraft in the fleet to meet the demand")
    #retirement array

    return None




def I1(gamma, m):
    """∫₀ᵐ t(m-t) exp(γt) dt"""
    val, _ = integrate.quad(lambda t: t * (m - t) * np.exp(gamma * t), 0, m)
    return val

def I_d(gamma, m, a, b):
    """∫₀ᵐ t(m-t) exp(γt) dt"""
    val, _ = integrate.quad(lambda t: t * (m - t) * np.exp(gamma * t), a, b)
    return val

def I2(gamma, m):
    """∫₀ᵐ t²(m-t) exp(γt) dt"""
    val, _ = integrate.quad(lambda t: t**2 * (m - t) * np.exp(gamma * t), 0, m)
    return val

def solve_deliv(B, m, gamma_bounds=(-10, 10)):

    if not (0 < B / 1 < m):
        raise ValueError(
            f"B/A = {B:.4f} doit être strictement dans (0, {m}) "
            "(la moyenne de t sous f doit rester dans l'intervalle)."
        )

    ratio = B
    def g(gamma):
        i1 = I1(gamma, m)
        if abs(i1) < 1e-14:
            return np.inf
        return I2(gamma, m) / i1 - ratio
    # Vérification que g change de signe sur l'intervalle
    ga, gb = gamma_bounds
    fa, fb = g(ga), g(gb)
    if fa * fb > 0:
        raise ValueError(
            f"Impossible de trouver gamma dans [{ga}, {gb}] : "
            f"g({ga})={fa:.3f}, g({gb})={fb:.3f}. "
            "Essayez d'élargir gamma_bounds."
        )

    gamma_sol = optimize.brentq(g, ga, gb, xtol=1e-12, rtol=1e-12)
    mu_sol    = 1 / I1(gamma_sol, m)

    return mu_sol, gamma_sol




fleet_process(
    classification_yaml_path="aeromaps/resources/data/default_fleet_push/default_aircraft_classification.yaml",
    market_param_yaml_path="aeromaps/resources/data/default_fleet_push/default_market_param.yaml",
    in_production_yaml_path="aeromaps/resources/data/default_fleet_push/default_in_production_aircraft_inventory.yaml",
    new_aircraft_yaml_path="aeromaps/resources/data/default_fleet_push/default_new_aircraft_inventory.yaml",
    aircraft_parameters_excel_path="aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/aircraft_type_key_parameters.xlsx",
    fleet_excel_path="aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/agg_fleet_2024.xlsx",
)

# markets = calculate_stats_by_submarket(
#     classification_yaml_path="aeromaps/resources/data/default_fleet_push/default_aircraft_classification.yaml",
#     aircraft_parameters_excel_path="aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/aircraft_type_key_parameters.xlsx",
# )



# production_volumes = visualise_5y_seats_deliveries_by_submarket(
# classification_yaml_path="aeromaps/resources/data/default_fleet_push/default_aircraft_classification.yaml",
# aircraft_parameters_excel_path="aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/aircraft_type_key_parameters.xlsx",
# fleet_excel_path = "aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/agg_fleet_2024.xlsx",
# )

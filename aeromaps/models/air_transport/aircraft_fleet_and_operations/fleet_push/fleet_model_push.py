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

import logging

import yaml
import pandas as pd
import numpy as np
from pathlib import Path

from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet_push.fleet_model_push_calculations import (
    i_d,
    solve_deliv,
    fleet_content,
)

logger = logging.getLogger(__name__)


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


def _build_aircraft_to_market_mapping(classification_data: dict) -> dict[str, str]:
    return {
        str(aircraft_type).strip(): str(market).strip()
        for item in classification_data.get("aircraft_types", [])
        if isinstance(item, dict)
        for aircraft_type, market in item.items()
    }


def _build_market_to_types_mapping(aircraft_to_market: dict[str, str]) -> dict[str, list[str]]:
    market_to_types = {}
    for aircraft_type, market in aircraft_to_market.items():
        market_to_types.setdefault(market, []).append(aircraft_type)
    return market_to_types


def calculate_stats_by_market(
    classification_yaml_path: str,
    aircraft_parameters_excel_path: str,
    excel_sheet_name=0,
) -> pd.DataFrame:
    """
    Compute aggregated statistics by market from:
    - a YAML file mapping aircraft types to markets
    - an Excel file containing aircraft parameters by type

    Returns
    -------
    pd.DataFrame
        DataFrame containing aggregated totals by market.
    """
    classification_data = _load_yaml(classification_yaml_path)
    mapping = _build_aircraft_to_market_mapping(classification_data)

    df = pd.read_excel(
        _resolve_project_path(aircraft_parameters_excel_path), sheet_name=excel_sheet_name
    )
    df = df.copy()
    df["market"] = df["Aircraft Type"].astype(str).str.strip().map(mapping)
    df["total_ask_produced_2024"] = pd.to_numeric(df["total_ask_produced_2024"], errors="coerce")
    df["adj_distance_aircraft_year(km)"] = pd.to_numeric(
        df["adj_distance_aircraft_year(km)"], errors="coerce"
    )
    df["MJ_fuel_ask"] = pd.to_numeric(df["MJ_fuel_ask"], errors="coerce")

    df = df[
        df["market"].notna()
        & df["total_ask_produced_2024"].notna()
        & df["adj_distance_aircraft_year(km)"].notna()
        & (df["adj_distance_aircraft_year(km)"] != 0)
        & df["MJ_fuel_ask"].notna()
    ].copy()

    if df.empty:
        raise ValueError("No valid rows remain after filtering missing or invalid values.")

    df["ask_over_distance"] = df["total_ask_produced_2024"] / df["adj_distance_aircraft_year(km)"]
    df["MJ_fuel_ask_weighted"] = df["MJ_fuel_ask"] * df["total_ask_produced_2024"]

    grouped = df.groupby("market", as_index=False).agg(
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
            "market",
            "total_adjusted_asks",
            "distance_aircraft_year_segment",
            "MJ_fuel_ask_segment",
        ]
    ]


def market_process(
    market_data,
    distance_per_aircraft,
    fleet_market,
    old_ac_carac,
    in_prod_ac_carac,
    future_ac_carac,
    ask_series,
    last_historical_year,
):
    """Pure, side-effect-free fleet-renewal engine for a single market segment.

    The AeroMAPS ASK series is always injected; the engine has no internal
    traffic-growth profile.

    Parameters
    ----------
    ask_series : array-like
        Per-year ASK volumes used DIRECTLY as the traffic target
        (``yearly_traffic``), aligned to the engine's projection horizon: the
        ``last_historical_year`` (pivot/base year) followed by every projection year
        up to ``market_growth[0][-1]`` (length ``modeled_periods + 1``).
    last_historical_year : int
        Pivot / calibration base year. ``first_projection_year`` is derived as
        ``last_historical_year + 1``.

    Returns
    -------
    tuple
        ``(years, deliveries[:-1], ask_volumes, aircraft_seats_volumes,
        energy_consumption)``.

    Raises
    ------
    ValueError
        When the delivered fleet activity cannot meet the demand for at least one
        year. A failed simulation in that case is acceptable (legacy behaviour).
    """
    first_projection_year = last_historical_year + 1
    market_growth = market_data["production_profile"]
    age_utilisation_sensibility = market_data["age_utilisation_sensib"]
    age_retirement_sensibility = market_data["age_retirement_sensib"]
    years = np.arange(first_projection_year, market_growth[0][-1] + 1)
    modeled_periods = years.shape[0]
    # ASK injection: use the supplied per-year traffic directly. It is aligned to
    # [last_historical_year, ..., market_growth[0][-1]] -> length modeled_periods + 1.
    yearly_traffic = np.asarray(ask_series, dtype=float).ravel()
    n_old_ac = old_ac_carac.shape[0]
    n_prod_ac = in_prod_ac_carac.shape[0]
    n_new_ac = future_ac_carac.shape[0]
    # fleet array
    fleet_ini = (fleet_market.values[:, 1:-1].T).astype(float)
    fleet_ini = np.hstack((fleet_ini, np.zeros((fleet_ini.shape[0], n_prod_ac + n_new_ac))))
    fleet_ini = np.vstack((fleet_ini, np.zeros((modeled_periods, fleet_ini.shape[1]))))
    # fuel intensity array
    energy_intensity = np.concatenate(
        [
            old_ac_carac["MJ_fuel_ask"].values,
            in_prod_ac_carac["energy_efficiency"].values,
            future_ac_carac["energy_efficiency"].values,
        ]
    )
    # seats array
    seats_array = np.concatenate(
        [
            old_ac_carac["average_seats"].values,
            in_prod_ac_carac["seats"].values,
            future_ac_carac["seats"].values,
        ]
    )
    # productivity array
    kms_array = np.concatenate(
        [
            old_ac_carac["adj_distance_aircraft_year(km)"].values,
            np.array(
                (in_prod_ac_carac.shape[0] + future_ac_carac.shape[0]) * [distance_per_aircraft]
            ),
        ]
    )
    prod_array = kms_array * seats_array
    period_utilisation_array = np.exp(age_utilisation_sensibility * np.arange(modeled_periods + 1))
    age_utilisation_array = np.exp(
        -age_utilisation_sensibility
        * (np.arange(fleet_ini.shape[0]) - fleet_ini.shape[0] + modeled_periods + 1)
    )
    # deliveries array
    deliveries_ini = np.zeros(fleet_ini.shape[1])
    deliveries = np.array([deliveries_ini] * (modeled_periods))
    production_profiles = in_prod_ac_carac["production_profile"].values
    # in production aircraft volumes
    for ac in range(n_prod_ac):
        production_profile = production_profiles[ac]
        production_volumes = np.array([])
        tot_production_y = production_profile[0][-1] - production_profile[0][0]
        for i in range(len(production_profile[0]) - 1):
            n_y = production_profile[0][i + 1] - production_profile[0][i]
            prod_ref = production_profile[1][i]
            prod_ev = production_profile[1][i + 1] - prod_ref
            production_volumes = np.concatenate(
                [production_volumes, np.arange(n_y) / (n_y - 1) * prod_ev + prod_ref]
            )
        deliveries[-modeled_periods : -modeled_periods + tot_production_y, n_old_ac + ac] = (
            production_volumes
        )
    # future aircraft volumes
    delivery_params = future_ac_carac[
        ["intro_year", "production_duration", "renewal_rate", "time_to_market", "seats"]
    ].values
    n_mod = yearly_traffic.shape[
        0
    ]  # parameter to fix the limit of the reference traffic year when applying a renewal rate.
    for ac in range(n_new_ac):
        eis = (delivery_params[ac, 0] - first_projection_year).astype(int)
        duration = delivery_params[ac, 1].astype(int)
        time_to_market = delivery_params[ac, 3]

        prod_volume = (
            yearly_traffic[min(eis + duration, n_mod - 1)]
            * delivery_params[ac, 2]
            / distance_per_aircraft
            / delivery_params[ac, 4]
        )
        mu, gamma = solve_deliv(time_to_market, duration)
        for t in range(duration):
            if eis + t + 1 < modeled_periods:
                deliveries_ac_t = prod_volume * mu * i_d(gamma, duration, t, (t + 1))
                deliveries[-modeled_periods + eis + t, n_old_ac + n_prod_ac + ac] = (
                    deliveries_ac_t  # +1->empty_delivery first
                )
    # fleet activity check
    fleet_delivered = fleet_ini.copy()
    fleet_delivered[-modeled_periods:, :] = deliveries
    fleet_delivered_activity_type_y = (
        fleet_delivered * age_utilisation_array[:, None] * prod_array[None, :]
    )
    fleet_delivered_activity_y = fleet_delivered_activity_type_y.sum(axis=1)
    fleet_delivered_activity = (
        np.cumsum(fleet_delivered_activity_y, axis=0)[-1 - modeled_periods :]
        * period_utilisation_array
    )
    # Capacity check (legacy behaviour): raise when the delivered fleet activity
    # cannot meet the demand. A failed simulation in that case is acceptable.
    if np.any(fleet_delivered_activity < 0.999999 * yearly_traffic):
        raise ValueError("not enough aircraft in the fleet to meet the demand in market segment")

    # retirement propensity array
    ret_year_delay_type = np.concatenate(
        [
            old_ac_carac["retirement_propensions"].values,
            in_prod_ac_carac["ret_year_delay"].values * age_retirement_sensibility,
            future_ac_carac["ret_year_delay"].values * age_retirement_sensibility,
        ]
    )
    ret_year_delay_type_y = (
        ret_year_delay_type[None, :]
        + (age_retirement_sensibility * np.arange(fleet_ini.shape[0]))[:, None]
    )
    ret_year_delay_type_y += (0.1338 - age_retirement_sensibility) * (
        fleet_ini.shape[0] - modeled_periods
    )
    # fleet composition convergence
    aircraft_seats_volumes = []
    ask_volumes = []
    x_eq = 1
    logger.debug("Computing fleet composition...")
    for t in range(modeled_periods):
        fleet_delivered_activity_type_y_t = fleet_delivered_activity_type_y.copy()
        fleet_delivered_activity_type_y_t[-modeled_periods + t :, :] = 0
        fleet_delivered_activity_type_y_t = (
            fleet_delivered_activity_type_y_t * period_utilisation_array[t]
        )
        ask_volumes_type_y_t, x_eq = fleet_content(
            0,
            x_eq,
            fleet_delivered_activity_type_y_t,
            ret_year_delay_type_y,
            yearly_traffic[t],
            epsilon=1e-6,
            first=True,
        )
        if x_eq < 1e-30:
            x_eq = x_eq ** (1 / 8)
            ret_year_delay_type_y = ret_year_delay_type_y - 3 * np.log(2)

        aircraft_seats_volumes_t = (
            ask_volumes_type_y_t
            / period_utilisation_array[t]
            / age_utilisation_array[:, None]
            / kms_array[None, :]
        )
        aircraft_seats_volumes.append(aircraft_seats_volumes_t)
        ask_volumes.append(ask_volumes_type_y_t)
    ask_volumes = np.array(ask_volumes)
    aircraft_seats_volumes = np.array(aircraft_seats_volumes)
    energy_consumption = energy_intensity[None, None, :] * ask_volumes
    return years, deliveries[:-1], ask_volumes, aircraft_seats_volumes, energy_consumption

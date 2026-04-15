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
from pathlib import Path


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

    if not classification_yaml_path.exists():
        raise FileNotFoundError(f"Classification YAML file not found: '{classification_yaml_path}'")
    if not aircraft_parameters_excel_path.exists():
        raise FileNotFoundError(
            f"Aircraft parameters Excel file not found: '{aircraft_parameters_excel_path}'"
        )

    with classification_yaml_path.open("r", encoding="utf-8") as f:
        classification_data = yaml.safe_load(f) or {}

    mapping = {
        str(aircraft_type).strip(): str(submarket).strip()
        for item in classification_data.get("aircraft_types", [])
        if isinstance(item, dict)
        for aircraft_type, submarket in item.items()
    }

    if not mapping:
        raise ValueError("No aircraft type mapping was found in the classification YAML file.")

    df = pd.read_excel(aircraft_parameters_excel_path, sheet_name=excel_sheet_name)

    required_columns = {
        "Aircraft Type",
        "total_ask_produced_2024",
        "adj_distance_aircraft_year(km)",
        "MJ_fuel_ask",
    }
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required column(s) in the Excel file: {sorted(missing_columns)}")

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





markets = calculate_stats_by_submarket(
    classification_yaml_path="aeromaps/resources/data/default_fleet_push/default_aircraft_classification.yaml",
    aircraft_parameters_excel_path="aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/aircraft_type_key_parameters.xlsx",
)
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
print(markets)
pd.reset_option("display.max_rows")
pd.reset_option("display.max_columns")
pd.reset_option("display.width")

"""
fleet_model
===========

Module for modeling aircraft fleet composition and renewal over time.

This module provides data structures and models for representing aircraft fleets,
including individual aircraft, subcategories (e.g., narrow-body, wide-body), and
categories (e.g., short-range, medium-range, long-range). It supports fleet
evolution modeling using S-shaped logistic functions for aircraft market share
transitions, and computes energy consumption, emissions (NOx, soot), and
operating costs based on fleet composition.

The module uses YAML configuration files to define aircraft inventories and
fleet structures, allowing flexible customization of fleet scenarios.
"""

from __future__ import annotations

import warnings
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.utils.yaml import read_yaml_file

AIRCRAFT_COLUMNS = [
    "Name",
    "EIS Year",
    "Consumption evolution [%]",
    "NOx evolution [%]",
    "Soot evolution [%]",
    "Non-Energy DOC evolution [%]",
    "Cruise altitude [m]",
    "Energy type",
    "Hybridization factor",
    "Average ASK per year",
    "Manufacturing Cost [M€]",
    "Non Recurring Costs [M€]",
    "Operational Empty Weight [t]",
]
SUBCATEGORY_COLUMNS = ["Name", "Share [%]"]

PACKAGE_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_FLEET_DATA_DIR = PACKAGE_ROOT / "resources" / "data" / "default_fleet"
DEFAULT_AIRCRAFT_INVENTORY_CONFIG_FILE = DEFAULT_FLEET_DATA_DIR / "aircraft_inventory.yaml"
DEFAULT_FLEET_CONFIG_FILE = DEFAULT_FLEET_DATA_DIR / "fleet.yaml"


@dataclass
class AircraftParameters:
    """Parameters defining an aircraft's characteristics and performance.

    Attributes
    ----------
    entry_into_service_year
        Year when the aircraft enters service [yr].
    consumption_evolution
        Relative change in energy consumption compared to reference aircraft [%].
    nox_evolution
        Relative change in NOx emissions compared to reference aircraft [%].
    soot_evolution
        Relative change in soot emissions compared to reference aircraft [%].
    doc_non_energy_evolution
        Relative change in non-energy direct operating costs compared to reference aircraft [%].
    cruise_altitude
        Typical cruise altitude of the aircraft [m].
    hybridization_factor
        Degree of hybridization for hybrid-electric aircraft, from 0 (conventional) to 1 (fully electric) [-].
    ask_year
        Average number of Available Seat Kilometers produced per aircraft per year [ASK/yr].
    nrc_cost
        Non-recurring costs (development costs) [€].
    rc_cost
        Recurring costs (manufacturing cost per unit) [€].
    oew
        Operational Empty Weight of the aircraft [t].
    full_name
        Full qualified name including category and subcategory path.
    """

    entry_into_service_year: Optional[float] = None
    consumption_evolution: Optional[float] = None
    nox_evolution: Optional[float] = None
    soot_evolution: Optional[float] = None
    doc_non_energy_evolution: Optional[float] = None
    cruise_altitude: Optional[float] = None
    hybridization_factor: float = 0.0
    ask_year: Optional[float] = None
    nrc_cost: Optional[float] = None
    rc_cost: Optional[float] = None
    oew: Optional[float] = None
    full_name: Optional[str] = None


@dataclass
class ReferenceAircraftParameters:
    """Parameters defining a reference aircraft used as baseline for comparisons.

    Reference aircraft serve as the baseline against which new aircraft performance
    improvements are measured. Each subcategory has an "old" and a "recent" reference.

    Attributes
    ----------
    energy_per_ask
        Energy consumption per Available Seat Kilometer [MJ/ASK].
    emission_index_nox
        NOx emission index per ASK [kg/ASK].
    emission_index_soot
        Soot emission index per ASK [kg/ASK].
    doc_non_energy_base
        Base non-energy direct operating cost per ASK [€/ASK].
    entry_into_service_year
        Year when the reference aircraft entered service [yr].
    cruise_altitude
        Typical cruise altitude of the aircraft [m].
    hybridization_factor
        Degree of hybridization, from 0 (conventional) to 1 (fully electric) [-].
    ask_year
        Average number of Available Seat Kilometers produced per aircraft per year [ASK/yr].
    nrc_cost
        Non-recurring costs (development costs) [€].
    rc_cost
        Recurring costs (manufacturing cost per unit) [€].
    oew
        Operational Empty Weight of the aircraft [t].
    full_name
        Full qualified name including category and subcategory path.
    """

    energy_per_ask: Optional[float] = None
    emission_index_nox: Optional[float] = None
    emission_index_soot: Optional[float] = None
    doc_non_energy_base: Optional[float] = None
    entry_into_service_year: Optional[float] = None
    cruise_altitude: Optional[float] = None
    hybridization_factor: float = 0.0
    ask_year: Optional[float] = None
    nrc_cost: Optional[float] = None
    rc_cost: Optional[float] = None
    oew: Optional[float] = None
    full_name: Optional[str] = None


@dataclass
class SubcategoryParameters:
    """Parameters for an aircraft subcategory.

    Attributes
    ----------
    share
        Market share of this subcategory within its parent category [%].
    """

    share: Optional[float] = None


@dataclass
class CategoryParameters:
    """Parameters for an aircraft category.

    Attributes
    ----------
    life
        Average operational lifetime of aircraft in this category [yr].
    limit
        Lower threshold for market share below which aircraft share is set to zero [%] (needed for S-curve parametrization).
    """

    life: float
    limit: float = 2


class Aircraft(object):
    """Represents an individual aircraft type in the fleet.

    An aircraft belongs to a subcategory and has parameters that define its
    performance relative to a reference aircraft.

    Parameters
    ----------
    name
        Name identifier for the aircraft type.
    parameters
        Aircraft performance and cost parameters.
    energy_type
        Type of energy used: 'DROP_IN_FUEL', 'HYDROGEN', 'ELECTRIC', or 'HYBRID_ELECTRIC'.

    Attributes
    ----------
    name : str
        Name identifier for the aircraft type.
    parameters : AircraftParameters
        Aircraft performance and cost parameters.
    energy_type : str
        Type of energy used by the aircraft.
    """

    def __init__(
        self,
        name: str = None,
        parameters: AircraftParameters = None,
        energy_type="DROP_IN_FUEL",
    ):
        self.name = name
        if parameters is None:
            parameters = AircraftParameters()
        self.parameters = parameters
        self.energy_type = energy_type

    def from_dataframe_row(self, row):
        """Populate aircraft attributes from a DataFrame row.

        Parameters
        ----------
        row
            DataFrame row containing aircraft data with columns matching AIRCRAFT_COLUMNS.

        Returns
        -------
        Aircraft
            Self, with attributes populated from the row data.
        """
        self.name = row[AIRCRAFT_COLUMNS[0]]
        self.parameters.entry_into_service_year = row[AIRCRAFT_COLUMNS[1]]
        self.parameters.consumption_evolution = row[AIRCRAFT_COLUMNS[2]]
        self.parameters.nox_evolution = row[AIRCRAFT_COLUMNS[3]]
        self.parameters.soot_evolution = row[AIRCRAFT_COLUMNS[4]]
        self.parameters.doc_non_energy_evolution = row[AIRCRAFT_COLUMNS[5]]
        self.parameters.cruise_altitude = row[AIRCRAFT_COLUMNS[6]]
        self.energy_type = row[AIRCRAFT_COLUMNS[7]]
        self.parameters.hybridization_factor = row[AIRCRAFT_COLUMNS[8]]
        self.parameters.ask_year = row[AIRCRAFT_COLUMNS[9]]
        self.parameters.rc_cost = row[AIRCRAFT_COLUMNS[10]]
        self.parameters.nrc_cost = row[AIRCRAFT_COLUMNS[11]]
        self.parameters.oew = row[AIRCRAFT_COLUMNS[12]]

        return self


class SubCategory(object):
    """Represents a subcategory of aircraft within a category.

    Subcategories group similar aircraft types (e.g., conventional narrow-body,
    hydrogen narrow-body) within a category. Each subcategory has reference
    aircraft (old and recent) that serve as baselines for performance comparisons.

    Parameters
    ----------
    name
        Name identifier for the subcategory.
    parameters
        Subcategory parameters including market share.

    Attributes
    ----------
    name : str
        Name identifier for the subcategory.
    parameters : SubcategoryParameters
        Subcategory parameters including market share.
    aircraft : Dict[int, Aircraft]
        Dictionary of aircraft belonging to this subcategory.
    old_reference_aircraft : ReferenceAircraftParameters
        Parameters for the older reference aircraft baseline.
    recent_reference_aircraft : ReferenceAircraftParameters
        Parameters for the more recent reference aircraft baseline.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        parameters: Optional[SubcategoryParameters] = None,
    ):
        self.name = name
        self.parameters = parameters or SubcategoryParameters()
        self.aircraft: Dict[int, Aircraft] = {}
        self.old_reference_aircraft = ReferenceAircraftParameters()
        self.recent_reference_aircraft = ReferenceAircraftParameters()

    def add_aircraft(self, aircraft: Aircraft) -> None:
        """Add an aircraft to this subcategory.

        Parameters
        ----------
        aircraft
            Aircraft instance to add to the subcategory.
        """
        self.aircraft[len(self.aircraft)] = aircraft

    def remove_aircraft(self, aircraft_name: str) -> None:
        """Remove an aircraft from this subcategory by name.

        Parameters
        ----------
        aircraft_name
            Name of the aircraft to remove.
        """
        self.aircraft = {
            i: aircraft
            for i, aircraft in enumerate(
                [a for a in self.aircraft.values() if a.name != aircraft_name]
            )
        }

    def compute(self) -> None:
        """Execute compute method on all aircraft in the subcategory."""
        for aircraft in self.aircraft.values():
            compute_method = getattr(aircraft, "compute", None)
            if callable(compute_method):
                compute_method()


class Category(object):
    """Represents a category of aircraft in the fleet (e.g., Short Range, Medium Range).

    Categories group subcategories of aircraft that operate in similar market segments.
    Each category has parameters defining aircraft lifetime and market share thresholds.

    Parameters
    ----------
    name
        Name identifier for the category (e.g., 'Short Range', 'Medium Range', 'Long Range').
    parameters
        Category parameters including aircraft lifetime.

    Attributes
    ----------
    name : str
        Name identifier for the category.
    parameters : CategoryParameters
        Category parameters including aircraft lifetime.
    subcategories : Dict[int, SubCategory]
        Dictionary of subcategories within this category.
    total_shares : float
        Sum of all subcategory market shares (should equal 100%).
    """

    def __init__(self, name: str, parameters: CategoryParameters):
        self.name = name
        self.parameters = parameters
        self.subcategories: Dict[int, SubCategory] = {}
        self.total_shares = 0.0

    def _compute(self) -> None:
        """Validate shares and compute all subcategories."""
        self._check_shares()
        for subcategory in self.subcategories.values():
            subcategory.compute()

    def add_subcategory(self, subcategory: SubCategory) -> None:
        """Add a subcategory to this category.

        Parameters
        ----------
        subcategory
            SubCategory instance to add.
        """
        self.subcategories[len(self.subcategories)] = subcategory

    def remove_subcategory(self, subcategory_name: str) -> None:
        """Remove a subcategory from this category by name.

        Parameters
        ----------
        subcategory_name
            Name of the subcategory to remove.
        """
        self.subcategories = {
            i: subcat
            for i, subcat in enumerate(
                [sub for sub in self.subcategories.values() if sub.name != subcategory_name]
            )
        }
        self._check_shares()

    def _check_shares(self) -> None:
        """Validate that subcategory shares sum to 100%."""
        if not self.subcategories:
            self.total_shares = 0.0
            return
        self.total_shares = sum(
            float(sub.parameters.share or 0.0) for sub in self.subcategories.values()
        )
        if not np.isclose(self.total_shares, 100.0, atol=0.1):
            raise UserWarning(
                "Total shares for category %s are %f instead of 100%",
                (self.name, self.total_shares),
            )


class Fleet(object):
    """Represents the complete aircraft fleet structure.

    The Fleet class manages the hierarchical structure of aircraft categories,
    subcategories, and individual aircraft types. It loads configuration from
    YAML files and provides methods for fleet manipulation and display.

    Parameters
    ----------
    parameters
        External parameters used for reference aircraft calibration (e.g., energy shares).
    aircraft_inventory_path
        Path to the YAML file containing the aircraft inventory definitions.
        Defaults to the package's default aircraft inventory.
    fleet_config_path
        Path to the YAML file containing the fleet structure configuration.
        Defaults to the package's default fleet configuration.

    Attributes
    ----------
    categories : Dict[str, Category]
        Dictionary of aircraft categories indexed by category name.
    parameters
        External parameters for reference aircraft calibration.
    aircraft_inventory_path : Path
        Path to the aircraft inventory YAML file.
    fleet_config_path : Path
        Path to the fleet configuration YAML file.
    all_aircraft_elements : dict
        Flattened dictionary of all aircraft elements per category.
    """

    def __init__(
        self,
        parameters=None,
        aircraft_inventory_path: Optional[Path] = None,
        fleet_config_path: Optional[Path] = None,
    ):
        self._categories: Dict[str, Category] = {}
        self.parameters = parameters
        self.aircraft_inventory_path = (
            Path(aircraft_inventory_path)
            if aircraft_inventory_path is not None
            else DEFAULT_AIRCRAFT_INVENTORY_CONFIG_FILE
        )
        self.fleet_config_path = (
            Path(fleet_config_path) if fleet_config_path is not None else DEFAULT_FLEET_CONFIG_FILE
        )

        self._build_default_fleet()
        self.all_aircraft_elements = self.get_all_aircraft_elements()

    def compute(self):
        """Execute compute on all categories in the fleet."""
        for cat in self.categories.values():
            cat._compute()

    @property
    def categories(self):
        """Dict[str, Category]: Dictionary of aircraft categories."""
        return self._categories

    @categories.setter
    def categories(self, value):
        self._categories = value
        self.all_aircraft_elements = self.get_all_aircraft_elements()

    def get_all_aircraft_elements(self):
        """Retrieve all aircraft elements organized by category.

        Creates a flattened view of all aircraft in the fleet, including reference
        aircraft, with their full qualified names set.

        Returns
        -------
        dict
            Dictionary mapping category names to lists of aircraft elements
            (reference aircraft parameters and Aircraft instances).
        """
        all_aircraft_elements = {}

        for category in self.categories.values():
            if not category.subcategories:
                continue

            aircraft_per_category = []
            subcategory = category.subcategories[0]

            ref_old_aircraft_name = f"{category.name}:{subcategory.name}:old_reference"
            subcategory.old_reference_aircraft.full_name = ref_old_aircraft_name
            aircraft_per_category.append(subcategory.old_reference_aircraft)

            ref_recent_aircraft_name = f"{category.name}:{subcategory.name}:recent_reference"
            subcategory.recent_reference_aircraft.full_name = ref_recent_aircraft_name
            aircraft_per_category.append(subcategory.recent_reference_aircraft)

            for subcategory in category.subcategories.values():
                for aircraft in subcategory.aircraft.values():
                    aircraft_name = f"{category.name}:{subcategory.name}:{aircraft.name}"
                    aircraft.parameters.full_name = aircraft_name
                    aircraft_per_category.append(aircraft)

            all_aircraft_elements[category.name] = aircraft_per_category

        return all_aircraft_elements

    def pretty_print(
        self,
        include_aircraft=True,
        indent=2,
        display=True,
        absolute=False,
        reference="recent",
    ):
        """Return (and optionally print) a summary of the fleet.

        Parameters
        ----------
        include_aircraft : bool
            Whether to list individual aircraft under each subcategory.
        indent : int
            Number of spaces used for indentation when printing nested entries.
        display : bool
            If True, print the generated summary; otherwise only return the string.
        absolute : bool
            When True, convert aircraft deltas (consumption, DOC, NOx, soot) into
            absolute values using the selected reference aircraft as the baseline.
        reference : str
            Which reference aircraft to use for absolute conversions; accepts
            "recent" (default) or "old". If the requested reference is missing,
            the method falls back to the other available reference.
        """

        reference_mode = reference.lower()
        if reference_mode not in {"recent", "old"}:
            raise ValueError("reference must be 'recent' or 'old'")

        def _format_value(label, value, suffix=""):
            if value is None:
                return None
            if isinstance(value, float) and value.is_integer():
                value = int(value)
            return f"{label}={value}{suffix}"

        def _format_absolute(label, base_value, delta_percent, unit=""):
            if base_value is None or delta_percent is None:
                return None
            absolute_value = base_value * (1 + delta_percent / 100.0)
            return f"{label}={absolute_value:.4g}{unit}"

        def _format_reference_line(label, reference_obj):
            if reference_obj is None:
                return None
            bits = list(
                filter(
                    None,
                    [
                        _format_value("EIS", reference_obj.entry_into_service_year, " y"),
                        _format_value("energy/ASK", reference_obj.energy_per_ask, " MJ/ASK"),
                        _format_value("DOC", reference_obj.doc_non_energy_base, " €/ASK"),
                        _format_value("NOx", reference_obj.emission_index_nox, " kg/ASK"),
                        _format_value("soot", reference_obj.emission_index_soot, " kg/ASK"),
                    ],
                )
            )
            descriptor = ", ".join(bits) if bits else "no data"
            return f"{level_two}- {label} reference ({descriptor})"

        def _select_base_reference(subcategory):
            preferred = (
                subcategory.recent_reference_aircraft
                if reference_mode == "recent"
                else subcategory.old_reference_aircraft
            )
            fallback = (
                subcategory.old_reference_aircraft
                if reference_mode == "recent"
                else subcategory.recent_reference_aircraft
            )
            return preferred or fallback

        def _format_aircraft_line(aircraft, base_reference=None):
            params = aircraft.parameters or AircraftParameters()
            if absolute and base_reference is not None:
                bits = list(
                    filter(
                        None,
                        [
                            aircraft.energy_type or "UNKNOWN",
                            _format_value("EIS", params.entry_into_service_year, "y"),
                            _format_absolute(
                                "energy/ASK",
                                base_reference.energy_per_ask,
                                params.consumption_evolution,
                                " MJ/ASK",
                            ),
                            _format_absolute(
                                "DOC",
                                base_reference.doc_non_energy_base,
                                params.doc_non_energy_evolution,
                                " €/ASK",
                            ),
                            _format_absolute(
                                "NOx",
                                base_reference.emission_index_nox,
                                params.nox_evolution,
                                " kg/ASK",
                            ),
                            _format_absolute(
                                "soot",
                                base_reference.emission_index_soot,
                                params.soot_evolution,
                                " kg/ASK",
                            ),
                        ],
                    )
                )
            else:
                bits = list(
                    filter(
                        None,
                        [
                            aircraft.energy_type or "UNKNOWN",
                            _format_value("EIS", params.entry_into_service_year, "y"),
                            _format_value("cons", params.consumption_evolution, "%"),
                            _format_value("NOx", params.nox_evolution, "%"),
                            _format_value("soot", params.soot_evolution, "%"),
                            _format_value("DOC", params.doc_non_energy_evolution, "%"),
                        ],
                    )
                )
            descriptor = ", ".join(bits) if bits else "no data"
            return f"{level_two}- {aircraft.name} ({descriptor})"

        lines = []
        indent = max(indent, 0)
        level_one = " " * indent
        level_two = " " * (indent * 2)

        if not self.categories:
            lines.append("Fleet has no categories configured.")
        for category in self.categories.values():
            subcategories = list(category.subcategories.values())
            share_sum = sum(float(sub.parameters.share or 0.0) for sub in subcategories)
            meta_bits = []
            if category.parameters is not None:
                if category.parameters.life is not None:
                    meta_bits.append(f"life={category.parameters.life:g}y")
                if category.parameters.limit is not None:
                    meta_bits.append(f"limit={category.parameters.limit:g}")
            meta_bits.append(f"subcategories={len(subcategories)}")
            if subcategories:
                meta_bits.append(f"share_sum={share_sum:.1f}%")
            category_header = f"{category.name} ({', '.join(meta_bits)})"
            lines.append(category_header)

            for subcategory in subcategories:
                share_value = subcategory.parameters.share if subcategory.parameters else None
                share_str = f"{share_value:.1f}%" if share_value is not None else "n/a"
                aircraft_count = len(subcategory.aircraft)
                sub_line = (
                    f"{level_one}- {subcategory.name} "
                    f"(share={share_str}, aircraft={aircraft_count})"
                )
                lines.append(sub_line)

                # Reference aircraft details
                ref_old_line = _format_reference_line("old", subcategory.old_reference_aircraft)
                if ref_old_line:
                    lines.append(ref_old_line)
                ref_recent_line = _format_reference_line(
                    "recent", subcategory.recent_reference_aircraft
                )
                if ref_recent_line:
                    lines.append(ref_recent_line)

                if include_aircraft and aircraft_count:
                    base_reference = _select_base_reference(subcategory) if absolute else None
                    for aircraft in subcategory.aircraft.values():
                        lines.append(_format_aircraft_line(aircraft, base_reference=base_reference))

        output = "\n".join(lines)
        if display:
            print(output)
        return output

    def _build_default_fleet(self):
        if self.aircraft_inventory_path.exists() and self.fleet_config_path.exists():
            self._build_fleet_from_yaml()
        else:
            warnings.warn(
                "Fleet configuration YAML files were not found.",
                UserWarning,
            )

    def _load_aircraft_inventory(self):
        data = read_yaml_file(str(self.aircraft_inventory_path))
        aircraft_inventory: Dict[str, Aircraft] = {}
        reference_inventory: Dict[str, ReferenceAircraftParameters] = {}

        for reference_entry in data.get("reference_aircraft", []):
            reference_id = reference_entry.get("id")
            if reference_id is None:
                continue
            params = ReferenceAircraftParameters(**reference_entry.get("parameters", {}))
            reference_inventory[reference_id] = params

        for entry in data.get("aircraft", []):
            aircraft_id = entry.get("id")
            if aircraft_id is None:
                continue
            params = AircraftParameters(**entry.get("parameters", {}))
            aircraft_inventory[aircraft_id] = Aircraft(
                name=entry.get("name"),
                parameters=params,
                energy_type=entry.get("energy_type", "DROP_IN_FUEL"),
            )

        return aircraft_inventory, reference_inventory

    @staticmethod
    def _populate_reference_aircraft(reference, data):
        if not data:
            return
        for attr, value in data.items():
            setattr(reference, attr, value)

    def _build_fleet_from_yaml(self):
        inventory, reference_inventory = self._load_aircraft_inventory()
        fleet_config = read_yaml_file(str(self.fleet_config_path))
        categories: Dict[str, Category] = {}
        subcategory_inventory = self._build_subcategory_inventory(
            fleet_config.get("subcategories", [])
        )

        for category_cfg in fleet_config.get("categories", []):
            cat_name = category_cfg.get("name")
            if cat_name is None:
                continue
            cat_params = CategoryParameters(**category_cfg.get("parameters", {}))
            category = Category(cat_name, parameters=cat_params)

            for sub_cfg_entry in category_cfg.get("subcategories", []):
                sub_cfg = self._normalize_subcategory_entry(sub_cfg_entry)
                resolved_sub_cfg = self._resolve_subcategory_config(sub_cfg, subcategory_inventory)

                share_value = resolved_sub_cfg.get("share", 0.0)

                subcategory = SubCategory(
                    resolved_sub_cfg.get("name"),
                    parameters=SubcategoryParameters(share=share_value),
                )

                reference_cfg = resolved_sub_cfg.get("reference_aircraft", {})
                subcategory.old_reference_aircraft = self._select_reference_aircraft(
                    reference_cfg,
                    "old",
                    reference_inventory,
                    subcategory.old_reference_aircraft,
                )
                subcategory.recent_reference_aircraft = self._select_reference_aircraft(
                    reference_cfg,
                    "recent",
                    reference_inventory,
                    subcategory.recent_reference_aircraft,
                )

                for aircraft_entry in resolved_sub_cfg.get("aircraft", []):
                    aircraft_id = self._extract_aircraft_id(aircraft_entry)
                    if aircraft_id not in inventory:
                        raise KeyError(
                            f"Aircraft '{aircraft_id}' is missing from inventory {self.aircraft_inventory_path}"
                        )
                    subcategory.add_aircraft(aircraft=deepcopy(inventory[aircraft_id]))

                category.add_subcategory(subcategory=subcategory)

            categories[category.name] = category
            category._check_shares()

        self.categories = categories
        self._calibrate_reference_aircraft()

    @staticmethod
    def _build_subcategory_inventory(entries):
        inventory: Dict[str, Dict[str, Any]] = {}
        for entry in entries:
            sub_id = entry.get("id")
            if sub_id is None:
                continue
            inventory[sub_id] = entry
        return inventory

    def _resolve_subcategory_config(self, sub_cfg, subcategory_inventory):
        sub_id = sub_cfg.get("id")
        base_cfg: Dict[str, Any] = {}
        if sub_id is not None:
            if sub_id not in subcategory_inventory:
                raise KeyError(
                    f"Subcategory '{sub_id}' referenced in {self.fleet_config_path} is undefined"
                )
            base_cfg = deepcopy(subcategory_inventory[sub_id])

        resolved_cfg = deepcopy(base_cfg)
        for key, value in sub_cfg.items():
            if key == "id":
                continue
            if isinstance(value, dict):
                existing = resolved_cfg.get(key)
                merged = deepcopy(existing) if isinstance(existing, dict) else {}
                merged.update(value)
                resolved_cfg[key] = merged
            else:
                resolved_cfg[key] = deepcopy(value)

        if not resolved_cfg.get("name"):
            raise KeyError("Each subcategory definition must include a name")

        return resolved_cfg

    @staticmethod
    def _normalize_subcategory_entry(entry: Any) -> Dict[str, Any]:
        if isinstance(entry, str):
            return {"id": entry}
        if isinstance(entry, dict):
            return entry
        raise TypeError("Subcategory entries must be either string IDs or dictionaries")

    @staticmethod
    def _extract_aircraft_id(entry: Any) -> str:
        if isinstance(entry, str):
            return entry
        if isinstance(entry, dict):
            aircraft_id = entry.get("ref") or entry.get("id")
            if aircraft_id:
                return aircraft_id
        raise KeyError("Aircraft entries must provide an ID either as a string or under 'ref'/'id'")

    def _select_reference_aircraft(
        self,
        reference_cfg: Dict[str, Any],
        key: str,
        reference_inventory: Dict[str, ReferenceAircraftParameters],
        default_reference: ReferenceAircraftParameters,
    ) -> ReferenceAircraftParameters:
        ref_id = reference_cfg.get(f"{key}_ref")
        if ref_id is not None:
            if ref_id not in reference_inventory:
                raise KeyError(
                    f"Reference aircraft '{ref_id}' is missing from inventory {self.aircraft_inventory_path}"
                )
            return deepcopy(reference_inventory[ref_id])

        inline_data = reference_cfg.get(key, {})
        self._populate_reference_aircraft(default_reference, inline_data)
        return default_reference

    def _get_subcategory(self, category_name: str, subcategory_name: str):
        category = self.categories.get(category_name)
        if category is None:
            return None
        for subcategory in category.subcategories.values():
            if subcategory.name == subcategory_name:
                return subcategory
        return None

    def _calibrate_reference_aircraft(self):
        if self.parameters is None:
            return

        sr_cat = self.categories.get("Short Range")
        sr_nb_cat = self._get_subcategory("Short Range", "SR conventional narrow-body")
        if sr_cat is not None and sr_nb_cat is not None:
            old_sr_energy = sr_nb_cat.old_reference_aircraft.energy_per_ask
            recent_sr_energy = sr_nb_cat.recent_reference_aircraft.energy_per_ask
            if old_sr_energy is None or recent_sr_energy is None:
                raise ValueError("Short Range reference aircraft energy_per_ask must be defined")

            mean_energy_init_ask_short_range = (
                self.parameters.energy_consumption_init[2019]
                * self.parameters.short_range_energy_share_2019
            ) / (self.parameters.ask_init[2019] * self.parameters.short_range_rpk_share_2019)

            share_recent_short_range = (mean_energy_init_ask_short_range - old_sr_energy) / (
                recent_sr_energy - old_sr_energy
            )

            # We fix the life of short-range aircraft to 25 years for calibration
            # This way the share between old and recent reference aircraft in 2019 remains the same
            sr_life = 25
            # sr_life = sr_cat.parameters.life
            lambda_short_range = np.log(100 / 2 - 1) / (sr_life / 2)

            if 1 > share_recent_short_range > 0:
                t0_sr = np.log(
                    (1 - share_recent_short_range) / share_recent_short_range
                ) / lambda_short_range + (self.parameters.prospection_start_year - 1)
                t_eis_short_range = t0_sr - sr_life / 2
            elif share_recent_short_range > 1:
                warnings.warn(
                    "Warning Message - Fleet Model: Short Range Aircraft: "
                    "Average initial short-range fleet energy per ASK is lower than default energy per ASK "
                    "for the recent reference aircraft - AeroMAPS is using initial short-range fleet energy per ASK "
                    "as old and recent reference aircraft energy performances!"
                )
                t_eis_short_range = self.parameters.prospection_start_year - 1 - sr_life
                sr_nb_cat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask_short_range
                sr_nb_cat.recent_reference_aircraft.energy_per_ask = (
                    mean_energy_init_ask_short_range
                )
            else:
                warnings.warn(
                    "Warning Message - Fleet Model: Short Range Aircraft: "
                    "Average initial short-range fleet energy per ASK is higher than default energy per ASK for the old reference aircraft - "
                    "AeroMAPS is using initial short-range fleet energy per ASK as old aircraft energy performances. "
                    "Recent reference aircraft is introduced on first prospective year"
                )
                t_eis_short_range = self.parameters.prospection_start_year
                sr_nb_cat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask_short_range

            sr_nb_cat.recent_reference_aircraft.entry_into_service_year = t_eis_short_range

        mr_cat = self.categories.get("Medium Range")
        mr_subcat = self._get_subcategory("Medium Range", "MR conventional narrow-body")
        if mr_cat is not None and mr_subcat is not None:
            old_mr_energy = mr_subcat.old_reference_aircraft.energy_per_ask
            recent_mr_energy = mr_subcat.recent_reference_aircraft.energy_per_ask
            if old_mr_energy is None or recent_mr_energy is None:
                raise ValueError("Medium Range reference aircraft energy_per_ask must be defined")

            mean_energy_init_ask_medium_range = (
                self.parameters.energy_consumption_init[2019]
                * self.parameters.medium_range_energy_share_2019
            ) / (self.parameters.ask_init[2019] * self.parameters.medium_range_rpk_share_2019)

            share_recent_medium_range = (mean_energy_init_ask_medium_range - old_mr_energy) / (
                recent_mr_energy - old_mr_energy
            )

            # We fix the life of short-range aircraft to 25 years for calibration
            # This way the share between old and recent reference aircraft in 2019 remains the same
            mr_life = 25
            # mr_life = mr_cat.parameters.life
            lambda_medium_range = np.log(100 / 2 - 1) / (mr_life / 2)

            if 1 > share_recent_medium_range > 0:
                t0_mr = np.log(
                    (1 - share_recent_medium_range) / share_recent_medium_range
                ) / lambda_medium_range + (self.parameters.prospection_start_year - 1)
                t_eis_medium_range = t0_mr - mr_life / 2
            elif share_recent_medium_range > 1:
                warnings.warn(
                    "Warning Message - Fleet Model: medium Range Aircraft: "
                    "Average initial medium-range fleet energy per ASK is lower than default energy per ASK for the recent reference aircraft - "
                    "AeroMAPS is using initial medium-range fleet energy per ASK as old and recent reference aircraft energy performances!"
                )
                t_eis_medium_range = self.parameters.prospection_start_year - 1 - mr_life
                mr_subcat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask_medium_range
                mr_subcat.recent_reference_aircraft.energy_per_ask = (
                    mean_energy_init_ask_medium_range
                )
            else:
                warnings.warn(
                    "Warning Message - Fleet Model: medium Range Aircraft: "
                    "Average initial medium-range fleet energy per ASK is higher than default energy per ASK for the old reference aircraft - "
                    "AeroMAPS is using initial medium-range fleet energy per ASK as old aircraft energy performances. "
                    "Recent reference aircraft is introduced on first prospective year"
                )
                t_eis_medium_range = self.parameters.prospection_start_year
                mr_subcat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask_medium_range

            mr_subcat.recent_reference_aircraft.entry_into_service_year = t_eis_medium_range

        lr_cat = self.categories.get("Long Range")
        lr_subcat = self._get_subcategory("Long Range", "LR conventional wide-body")
        if lr_cat is not None and lr_subcat is not None:
            old_lr_energy = lr_subcat.old_reference_aircraft.energy_per_ask
            recent_lr_energy = lr_subcat.recent_reference_aircraft.energy_per_ask
            if old_lr_energy is None or recent_lr_energy is None:
                raise ValueError("Long Range reference aircraft energy_per_ask must be defined")

            mean_energy_init_ask_long_range = (
                self.parameters.energy_consumption_init[2019]
                * self.parameters.long_range_energy_share_2019
            ) / (self.parameters.ask_init[2019] * self.parameters.long_range_rpk_share_2019)

            share_recent_long_range = (mean_energy_init_ask_long_range - old_lr_energy) / (
                recent_lr_energy - old_lr_energy
            )

            # We fix the life of short-range aircraft to 25 years for calibration
            # This way the share between old and recent reference aircraft in 2019 remains the same
            lr_life = 25
            # lr_life = lr_cat.parameters.life
            lambda_long_range = np.log(100 / 2 - 1) / (lr_life / 2)

            if 1 > share_recent_long_range > 0:
                t0_lr = np.log(
                    (1 - share_recent_long_range) / share_recent_long_range
                ) / lambda_long_range + (self.parameters.prospection_start_year - 1)
                t_eis_long_range = t0_lr - lr_life / 2
            elif share_recent_long_range > 1:
                warnings.warn(
                    "Warning Message - Fleet Model: long Range Aircraft: "
                    "Average initial long-range fleet energy per ASK is lower than default energy per ASK for the recent reference aircraft - "
                    "AeroMAPS is using initial long-range fleet energy per ASK as old and recent reference aircraft energy performances!"
                )
                t_eis_long_range = self.parameters.prospection_start_year - 1 - lr_life
                lr_subcat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask_long_range
                lr_subcat.recent_reference_aircraft.energy_per_ask = mean_energy_init_ask_long_range
            else:
                warnings.warn(
                    "Warning Message - Fleet Model: long Range Aircraft: "
                    "Average initial long-range fleet energy per ASK is higher than default energy per ASK for the old reference aircraft - "
                    "AeroMAPS is using initial long-range fleet energy per ASK as old aircraft energy performances. "
                    "Recent reference aircraft is introduced on first prospective year"
                )
                t_eis_long_range = self.parameters.prospection_start_year
                lr_subcat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask_long_range

            lr_subcat.recent_reference_aircraft.entry_into_service_year = t_eis_long_range


class FleetModel(AeroMAPSModel):
    """AeroMAPS model for computing fleet evolution and characteristics over time.

    This model computes the temporal evolution of the aircraft fleet composition,
    including market shares for each aircraft type, energy consumption, emissions
    (NOx, soot), and non-energy direct operating costs. It uses S-shaped logistic
    functions to model the gradual introduction and retirement of aircraft types.

    Parameters
    ----------
    name
        Name of the model instance ('fleet_model' by default).
    fleet
        Fleet instance containing the fleet structure and aircraft definitions.
    *args
        Additional positional arguments passed to parent class.
    **kwargs
        Additional keyword arguments passed to parent class.

    Attributes
    ----------
    fleet : Fleet
        The Fleet instance used for computations.

    Notes
    -----
    The model computes several categories of outputs stored in self.df:

    - **Single aircraft shares**: Individual aircraft cumulative market penetration
    - **Aircraft shares**: Actual market share for each aircraft type
    - **Energy consumption**: Energy per ASK by subcategory and energy type
    - **DOC non-energy**: Non-energy direct operating costs by subcategory
    - **Non-CO2 emissions**: NOx and soot emission indices by subcategory
    - **Category means**: Weighted averages across subcategories for each category
    """

    def __init__(self, name="fleet_model", fleet=None, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.fleet = fleet

    def compute(
        self,
    ):
        """Compute fleet evolution and all derived metrics.

        Executes the complete fleet model computation pipeline:

        1. Single aircraft share computation (cumulative S-curve penetration)
        2. Aircraft share computation (differential market shares)
        3. Energy consumption and share by energy type
        4. Non-energy direct operating costs (DOC)
        5. Non-CO2 emission indices (NOx, soot)
        6. Category-level mean energy consumption
        7. Category-level mean DOC
        8. Category-level mean emission indices

        Returns
        -------
        np.ndarray
            Dummy output array (actual results stored in self.df).
        """
        # Start from empty dataframe (necessary for multiple runs of the model)
        self.df = pd.DataFrame(index=self.df.index)

        # Compute single aircraft shares
        self._compute_single_aircraft_share()

        # Compute aircraft shares
        self._compute_aircraft_share()

        # Compute energy consumption and share per subcategory with respect to energy type
        self._compute_energy_consumption_and_share_wrt_energy_type()

        # Compute non energy direct operating costs (DOC) and share per subcategory with respect to energy type
        self._compute_doc_non_energy()

        # Compute non-CO2 (NOx and soot) emission index and share per subcategory with respect to energy type
        self._compute_non_co2_emission_index()

        # Compute mean energy consumption per category with respect to energy type
        self._compute_mean_energy_consumption_per_category_wrt_energy_type()

        # Compute mean non energy direct operating cost (DOC) per category with respect to energy type
        self._compute_mean_doc_non_energy()

        # Compute mean non-CO2 emission index per category with respect to energy type
        self._compute_mean_non_co2_emission_index()

    def _compute_single_aircraft_share(self):
        """Compute cumulative single aircraft market penetration shares.

        Uses S-shaped logistic functions to model the gradual introduction of
        aircraft into the fleet based on their entry-into-service year and
        the category's fleet renewal lifetime.

        Handles two configuration modes:

        - Single subcategory: All aircraft compete for the full 100% market share,
          with reference aircraft (old and recent) taking the remaining share.
        - Multiple subcategories: Each subcategory has a target share parameter,
          and aircraft within subcategories compete for that share. The last
          subcategory fills the remainder.

        The computation adjusts reference aircraft curves to match historical
        fleet composition by scaling between a baseline 25-year lifetime and
        the actual category lifetime.

        Results are stored in the DataFrame with keys like:
        ``{category}:{subcategory}:{aircraft}:single_aircraft_share``
        ``{category}:{subcategory}:old_reference:single_aircraft_share``
        ``{category}:{subcategory}:recent_reference:single_aircraft_share``
        """
        temp_dict = {}

        for category in self.fleet.categories.values():
            limit = 2
            life_base = 25
            parameter_base = np.log(100 / limit - 1) / (life_base / 2)
            parameter_renewal = np.log(100 / limit - 1) / (category.parameters.life / 2)

            if len(category.subcategories) == 1:
                subcategory = list(category.subcategories.values())[0]
                year_ref_recent_begin = (
                    subcategory.recent_reference_aircraft.entry_into_service_year
                )
                year_ref_recent_base = year_ref_recent_begin + life_base / 2
                year_ref_recent = (
                    self.prospection_start_year
                    - parameter_base
                    / parameter_renewal
                    * (self.prospection_start_year - year_ref_recent_base)
                )
                ref_recent_single_aircraft_share = self._compute(
                    float(category.parameters.life),
                    float(year_ref_recent),
                    float(subcategory.parameters.share),
                    recent=True,
                )
                temp_dict[
                    f"{category.name}:{subcategory.name}:recent_reference:single_aircraft_share"
                ] = ref_recent_single_aircraft_share

                ref_old_single_aircraft_share = 100
                temp_dict[
                    f"{category.name}:{subcategory.name}:old_reference:single_aircraft_share"
                ] = ref_old_single_aircraft_share

                for aircraft in subcategory.aircraft.values():
                    single_aircraft_share = self._compute(
                        float(category.parameters.life),
                        float(aircraft.parameters.entry_into_service_year),
                        float(subcategory.parameters.share),
                    )
                    temp_dict[
                        f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                    ] = single_aircraft_share

            elif len(category.subcategories) == 2:
                subcategory = list(category.subcategories.values())[-1]
                for i, aircraft in subcategory.aircraft.items():
                    single_aircraft_share = self._compute(
                        float(category.parameters.life),
                        float(aircraft.parameters.entry_into_service_year),
                        float(subcategory.parameters.share),
                    )
                    temp_dict[
                        f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                    ] = single_aircraft_share
                    if i == 0:
                        oldest_single_aircraft_share = single_aircraft_share

                subcategory = list(category.subcategories.values())[0]
                year_ref_recent_begin = (
                    subcategory.recent_reference_aircraft.entry_into_service_year
                )
                year_ref_recent_base = year_ref_recent_begin + life_base / 2
                year_ref_recent = (
                    self.prospection_start_year
                    - parameter_base
                    / parameter_renewal
                    * (self.prospection_start_year - year_ref_recent_base)
                )
                ref_recent_single_aircraft_share = oldest_single_aircraft_share + self._compute(
                    float(category.parameters.life),
                    float(year_ref_recent),
                    100 - oldest_single_aircraft_share,
                    recent=True,
                )
                temp_dict[
                    f"{category.name}:{subcategory.name}:recent_reference:single_aircraft_share"
                ] = ref_recent_single_aircraft_share

                ref_old_single_aircraft_share = 100
                temp_dict[
                    f"{category.name}:{subcategory.name}:old_reference:single_aircraft_share"
                ] = ref_old_single_aircraft_share

                for aircraft in subcategory.aircraft.values():
                    single_aircraft_share = oldest_single_aircraft_share + self._compute(
                        float(category.parameters.life),
                        float(aircraft.parameters.entry_into_service_year),
                        100 - oldest_single_aircraft_share,
                    )
                    temp_dict[
                        f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                    ] = single_aircraft_share

            else:
                for key, subcategory in reversed(category.subcategories.items()):
                    if key == list(category.subcategories.keys())[-1]:
                        for i, aircraft in subcategory.aircraft.items():
                            single_aircraft_share = self._compute(
                                float(category.parameters.life),
                                float(aircraft.parameters.entry_into_service_year),
                                float(subcategory.parameters.share),
                            )
                            temp_dict[
                                f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                            ] = single_aircraft_share
                            if i == 0:
                                oldest_single_aircraft_share = single_aircraft_share

                    elif key == list(category.subcategories.keys())[0]:
                        year_ref_recent_begin = (
                            subcategory.recent_reference_aircraft.entry_into_service_year
                        )
                        year_ref_recent_base = year_ref_recent_begin + life_base / 2
                        year_ref_recent = (
                            self.prospection_start_year
                            - parameter_base
                            / parameter_renewal
                            * (self.prospection_start_year - year_ref_recent_base)
                        )
                        ref_recent_single_aircraft_share = (
                            oldest_single_aircraft_share
                            + self._compute(
                                float(category.parameters.life),
                                float(year_ref_recent),
                                100 - oldest_single_aircraft_share,
                                recent=True,
                            )
                        )
                        temp_dict[
                            f"{category.name}:{subcategory.name}:recent_reference:single_aircraft_share"
                        ] = ref_recent_single_aircraft_share

                        ref_old_single_aircraft_share = 100
                        temp_dict[
                            f"{category.name}:{subcategory.name}:old_reference:single_aircraft_share"
                        ] = ref_old_single_aircraft_share

                        for aircraft in subcategory.aircraft.values():
                            single_aircraft_share = oldest_single_aircraft_share + self._compute(
                                float(category.parameters.life),
                                float(aircraft.parameters.entry_into_service_year),
                                100 - oldest_single_aircraft_share,
                            )
                            temp_dict[
                                f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                            ] = single_aircraft_share

                    else:
                        for i, aircraft in subcategory.aircraft.items():
                            single_aircraft_share = oldest_single_aircraft_share + self._compute(
                                float(category.parameters.life),
                                float(aircraft.parameters.entry_into_service_year),
                                float(subcategory.parameters.share),
                            )
                            temp_dict[
                                f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                            ] = single_aircraft_share
                            if i == 0:
                                new_oldest_single_aircraft_share = single_aircraft_share
                        oldest_single_aircraft_share = new_oldest_single_aircraft_share

        final_dict = {
            key: np.array(values) if isinstance(values, list) else values
            for key, values in temp_dict.items()
        }

        final_df = pd.DataFrame(final_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

    def _compute_aircraft_share(self):
        """Compute individual aircraft share in the fleet.

        Calculates each aircraft's share (not cumulative) by differencing
        single_aircraft_share values. The share represents the actual portion
        of the fleet using that specific aircraft type, computed by subtracting
        the single_aircraft_share of the next aircraft in sequence.

        For the last aircraft in a subcategory/category, the share equals its
        single_aircraft_share. For others, the share is the difference between
        consecutive single_aircraft_share values.

        Also computes reference aircraft shares:
        - recent_reference: first subcategory reference minus first new aircraft
        - old_reference: 100% minus recent_reference single_aircraft_share

        Results are stored in the DataFrame with keys like:
        ``{category}:{subcategory}:{aircraft}:aircraft_share``
        """
        temp_dict = {}

        for category in self.fleet.categories.values():
            for key, subcategory in reversed(category.subcategories.items()):
                for i, aircraft in reversed(subcategory.aircraft.items()):
                    subcategory_key = f"{category.name}:{subcategory.name}:{aircraft.name}"

                    if (i == list(subcategory.aircraft.keys())[-1]) and (
                        key == list(category.subcategories.keys())[-1]
                    ):
                        aircraft_share = self.df[f"{subcategory_key}:single_aircraft_share"].values
                    elif (i == list(subcategory.aircraft.keys())[-1]) and (
                        key != list(category.subcategories.keys())[-1]
                    ):
                        single_aircraft_share = self.df[
                            f"{subcategory_key}:single_aircraft_share"
                        ].values
                        single_aircraft_share_n1 = self.df[
                            f"{category.name}:{category.subcategories[key + 1].name}:{category.subcategories[key + 1].aircraft[0].name}:single_aircraft_share"
                        ].values
                        aircraft_share = single_aircraft_share - single_aircraft_share_n1
                    else:
                        single_aircraft_share = self.df[
                            f"{subcategory_key}:single_aircraft_share"
                        ].values
                        single_aircraft_share_n1 = self.df[
                            f"{category.name}:{subcategory.name}:{subcategory.aircraft[i + 1].name}:single_aircraft_share"
                        ].values
                        aircraft_share = single_aircraft_share - single_aircraft_share_n1

                    temp_dict[f"{subcategory_key}:aircraft_share"] = aircraft_share

            ref_recent_single_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:recent_reference:single_aircraft_share"
            ].values

            if subcategory.aircraft:
                next_aircraft_single_share = self.df[
                    f"{category.name}:{category.subcategories[0].name}:{subcategory.aircraft[0].name}:single_aircraft_share"
                ].values
            else:
                next_aircraft_single_share = np.zeros_like(ref_recent_single_aircraft_share)

            ref_recent_aircraft_share = (
                ref_recent_single_aircraft_share - next_aircraft_single_share
            )
            temp_dict[
                f"{category.name}:{category.subcategories[0].name}:recent_reference:aircraft_share"
            ] = ref_recent_aircraft_share

            ref_old_aircraft_share = 100 - ref_recent_single_aircraft_share
            temp_dict[
                f"{category.name}:{category.subcategories[0].name}:old_reference:aircraft_share"
            ] = ref_old_aircraft_share

        final_dict = {
            key: np.array(values) if isinstance(values, list) else values
            for key, values in temp_dict.items()
        }

        final_df = pd.DataFrame(final_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

    def _compute_energy_consumption_and_share_wrt_energy_type(self):
        """Compute energy consumption and fleet share by energy type.

        For each category and subcategory, calculates:

        - Total energy consumption weighted by aircraft share
        - Energy consumption broken down by energy type (drop-in fuel, hydrogen,
          electric, hybrid electric)
        - Fleet share by energy type

        Reference aircraft (old and recent) are assumed to use drop-in fuel.
        New aircraft contribute based on their defined energy type. Hybrid
        electric aircraft split their consumption and share between drop-in
        fuel and electric based on their hybridization factor.

        Results are stored in the DataFrame with keys like:
        ``{category}:{subcategory}:energy_consumption:{energy_type}``
        ``{category}:{subcategory}:share:{energy_type}``
        ``{category}:share:{energy_type}``
        """
        temp_dict = {}

        for category in self.fleet.categories.values():
            ref_old_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:old_reference:aircraft_share"
            ].values
            ref_recent_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:recent_reference:aircraft_share"
            ].values

            recent_reference_aircraft_energy_consumption = category.subcategories[
                0
            ].recent_reference_aircraft.energy_per_ask

            for i, subcategory in category.subcategories.items():
                subcategory_key = f"{category.name}:{subcategory.name}"

                if i == 0:
                    initial_energy_consumption = (
                        subcategory.old_reference_aircraft.energy_per_ask
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.energy_per_ask
                        * ref_recent_aircraft_share
                        / 100
                    )
                    initial_share = ref_old_aircraft_share + ref_recent_aircraft_share
                else:
                    initial_energy_consumption = np.zeros_like(ref_old_aircraft_share)
                    initial_share = np.zeros_like(ref_old_aircraft_share)

                temp_dict[f"{subcategory_key}:energy_consumption"] = (
                    initial_energy_consumption.copy()
                )
                temp_dict[f"{subcategory_key}:energy_consumption:dropin_fuel"] = (
                    initial_energy_consumption.copy()
                )
                temp_dict[f"{subcategory_key}:energy_consumption:hydrogen"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:energy_consumption:electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:energy_consumption:hybrid_electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:share:total"] = initial_share.copy()
                temp_dict[f"{subcategory_key}:share:dropin_fuel"] = initial_share.copy()
                temp_dict[f"{subcategory_key}:share:hydrogen"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:share:electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:share:hybrid_electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )

                for aircraft in subcategory.aircraft.values():
                    aircraft_share = self.df[
                        f"{subcategory_key}:{aircraft.name}:aircraft_share"
                    ].values

                    energy_consumption = (
                        recent_reference_aircraft_energy_consumption
                        * (1 + float(aircraft.parameters.consumption_evolution) / 100)
                        * aircraft_share
                        / 100
                    )

                    temp_dict[f"{subcategory_key}:share:total"] += aircraft_share
                    temp_dict[f"{subcategory_key}:energy_consumption"] += energy_consumption

                    if aircraft.energy_type == "DROP_IN_FUEL":
                        temp_dict[f"{subcategory_key}:share:dropin_fuel"] += aircraft_share
                        temp_dict[f"{subcategory_key}:energy_consumption:dropin_fuel"] += (
                            energy_consumption
                        )

                    if aircraft.energy_type == "HYDROGEN":
                        temp_dict[f"{subcategory_key}:share:hydrogen"] += aircraft_share
                        temp_dict[f"{subcategory_key}:energy_consumption:hydrogen"] += (
                            energy_consumption
                        )

                    if aircraft.energy_type == "ELECTRIC":
                        temp_dict[f"{subcategory_key}:share:electric"] += aircraft_share
                        temp_dict[f"{subcategory_key}:energy_consumption:electric"] += (
                            energy_consumption
                        )

                    if aircraft.energy_type == "HYBRID_ELECTRIC":
                        hybridization_factor = float(aircraft.parameters.hybridization_factor)
                        temp_dict[f"{subcategory_key}:share:dropin_fuel"] += (
                            1 - hybridization_factor
                        ) * aircraft_share
                        temp_dict[f"{subcategory_key}:share:electric"] += (
                            hybridization_factor * aircraft_share
                        )
                        temp_dict[f"{subcategory_key}:energy_consumption:hybrid_electric"] += (
                            energy_consumption
                        )
                        temp_dict[f"{subcategory_key}:energy_consumption:dropin_fuel"] += (
                            1 - hybridization_factor
                        ) * energy_consumption
                        temp_dict[f"{subcategory_key}:energy_consumption:electric"] += (
                            hybridization_factor * energy_consumption
                        )

                for energy_type in ["dropin_fuel", "hydrogen", "electric", "hybrid_electric"]:
                    category_share_key = f"{category.name}:share:{energy_type}"
                    subcategory_share_key = f"{subcategory_key}:share:{energy_type}"
                    if category_share_key in temp_dict:
                        temp_dict[category_share_key] += temp_dict[subcategory_share_key]
                    else:
                        temp_dict[category_share_key] = temp_dict[subcategory_share_key].copy()

        final_dict = {
            key: np.array(values) if isinstance(values, list) else values
            for key, values in temp_dict.items()
        }

        final_df = pd.DataFrame(final_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

    def _compute_doc_non_energy(self):
        """Compute direct operating costs excluding energy costs.

        Calculates the non-energy portion of direct operating costs (DOC)
        for each category and subcategory, weighted by aircraft share.
        This includes costs like maintenance, crew, insurance, etc.

        Reference aircraft use their base DOC values. New aircraft apply
        their doc_non_energy_evolution percentage to the recent reference
        aircraft's base value.

        Results are broken down by energy type for allocation purposes:

        - dropin_fuel: Drop-in fuel aircraft DOC
        - hydrogen: Hydrogen aircraft DOC
        - electric: Electric aircraft DOC
        - hybrid_electric: Hybrid electric aircraft DOC

        Results are stored in the DataFrame with keys like:
        ``{category}:{subcategory}:doc_non_energy:{energy_type}``
        ``{category}:doc_non_energy:{energy_type}``
        """
        temp_dict = {}

        for category in self.fleet.categories.values():
            ref_old_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:old_reference:aircraft_share"
            ].values
            ref_recent_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:recent_reference:aircraft_share"
            ].values

            recent_reference_aircraft_doc_non_energy = category.subcategories[
                0
            ].recent_reference_aircraft.doc_non_energy_base

            for i, subcategory in category.subcategories.items():
                subcategory_key = f"{category.name}:{subcategory.name}"

                if i == 0:
                    initial_doc_non_energy = (
                        subcategory.old_reference_aircraft.doc_non_energy_base
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.doc_non_energy_base
                        * ref_recent_aircraft_share
                        / 100
                    )
                else:
                    initial_doc_non_energy = np.zeros_like(ref_old_aircraft_share)

                temp_dict[f"{subcategory_key}:doc_non_energy"] = initial_doc_non_energy.copy()
                temp_dict[f"{subcategory_key}:doc_non_energy:dropin_fuel"] = (
                    initial_doc_non_energy.copy()
                )
                temp_dict[f"{subcategory_key}:doc_non_energy:hydrogen"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:doc_non_energy:electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                temp_dict[f"{subcategory_key}:doc_non_energy:hybrid_electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )

                for aircraft in subcategory.aircraft.values():
                    aircraft_share = self.df[
                        f"{subcategory_key}:{aircraft.name}:aircraft_share"
                    ].values

                    doc_non_energy = (
                        recent_reference_aircraft_doc_non_energy
                        * (1 + float(aircraft.parameters.doc_non_energy_evolution) / 100)
                        * aircraft_share
                        / 100
                    )

                    temp_dict[f"{subcategory_key}:doc_non_energy"] += doc_non_energy

                    if aircraft.energy_type == "DROP_IN_FUEL":
                        temp_dict[f"{subcategory_key}:doc_non_energy:dropin_fuel"] += doc_non_energy

                    if aircraft.energy_type == "HYDROGEN":
                        temp_dict[f"{subcategory_key}:doc_non_energy:hydrogen"] += doc_non_energy

                    if aircraft.energy_type == "ELECTRIC":
                        temp_dict[f"{subcategory_key}:doc_non_energy:electric"] += doc_non_energy

                    if aircraft.energy_type == "HYBRID_ELECTRIC":
                        temp_dict[f"{subcategory_key}:doc_non_energy:hybrid_electric"] += (
                            doc_non_energy
                        )

            # Summing up doc_non_energy for categories
            for energy_type in ["dropin_fuel", "hydrogen", "electric", "hybrid_electric"]:
                category_doc_key = f"{category.name}:doc_non_energy:{energy_type}"
                subcategory_doc_key = f"{subcategory_key}:doc_non_energy:{energy_type}"
                if category_doc_key in temp_dict:
                    temp_dict[category_doc_key] += temp_dict[subcategory_doc_key]
                else:
                    temp_dict[category_doc_key] = temp_dict[subcategory_doc_key].copy()

        final_dict = {
            key: np.array(values) if isinstance(values, list) else values
            for key, values in temp_dict.items()
        }

        final_df = pd.DataFrame(final_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

    def _compute_non_co2_emission_index(self):
        """Compute NOx and soot emission indices for the fleet.

        Calculates emission indices for non-CO2 pollutants (NOx and soot)
        for each category and subcategory. Reference aircraft use their
        base emission index values. New aircraft apply evolution factors
        (nox_evolution, soot_evolution) to the recent reference values.

        Emission indices are computed per energy type:

        - dropin_fuel: Conventional and SAF-powered aircraft emissions
        - hydrogen: Hydrogen aircraft emissions (NOx only, no soot)
        - electric: Electric aircraft emissions (none)
        - hybrid_electric: Hybrid electric aircraft emissions

        Category-level emission indices are computed as share-weighted
        averages across all subcategories and energy types.

        Results are stored directly in the DataFrame with keys like:
        ``{category}:{subcategory}:emission_index_nox:{energy_type}``
        ``{category}:{subcategory}:emission_index_soot:{energy_type}``
        ``{category}:emission_index_nox``
        ``{category}:emission_index_soot``
        """
        # Non-CO2 (NOx and soot) emission index calculations for drop-in fuel and hydrogen
        for category in self.fleet.categories.values():
            # Reference aircraft information
            ref_old_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:old_reference:aircraft_share"
            ]
            ref_recent_aircraft_share = self.df[
                f"{category.name}:{category.subcategories[0].name}:recent_reference:aircraft_share"
            ]

            # Use the first subcategory's recent reference aircraft emission indices
            recent_reference_aircraft_emission_index_nox = category.subcategories[
                0
            ].recent_reference_aircraft.emission_index_nox
            recent_reference_aircraft_emission_index_soot = category.subcategories[
                0
            ].recent_reference_aircraft.emission_index_soot

            for i, subcategory in category.subcategories.items():
                subcategory_key = f"{category.name}:{subcategory.name}"
                if i == 0:
                    initial_nox = (
                        subcategory.old_reference_aircraft.emission_index_nox
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.emission_index_nox
                        * ref_recent_aircraft_share
                        / 100
                    )
                    initial_soot = (
                        subcategory.old_reference_aircraft.emission_index_soot
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.emission_index_soot
                        * ref_recent_aircraft_share
                        / 100
                    )
                else:
                    initial_nox = np.zeros_like(ref_old_aircraft_share)
                    initial_soot = np.zeros_like(ref_old_aircraft_share)

                # Initialize emission index columns
                self.df[f"{subcategory_key}:emission_index_nox"] = initial_nox
                self.df[f"{subcategory_key}:emission_index_soot"] = initial_soot
                self.df[f"{subcategory_key}:emission_index_nox:dropin_fuel"] = initial_nox.copy()
                self.df[f"{subcategory_key}:emission_index_nox:hydrogen"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                self.df[f"{subcategory_key}:emission_index_nox:electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                self.df[f"{subcategory_key}:emission_index_nox:hybrid_electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                self.df[f"{subcategory_key}:emission_index_soot:dropin_fuel"] = initial_soot.copy()
                self.df[f"{subcategory_key}:emission_index_soot:hydrogen"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                self.df[f"{subcategory_key}:emission_index_soot:electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )
                self.df[f"{subcategory_key}:emission_index_soot:hybrid_electric"] = np.zeros_like(
                    ref_old_aircraft_share
                )

                for aircraft in subcategory.aircraft.values():
                    aircraft_share_key = f"{subcategory_key}:{aircraft.name}:aircraft_share"
                    if aircraft_share_key in self.df.columns:
                        for idx in self.df.index:
                            aircraft_share = self.df.at[idx, aircraft_share_key]
                            if aircraft_share != 0.0:
                                evolution_nox = 1 + float(aircraft.parameters.nox_evolution) / 100
                                evolution_soot = 1 + float(aircraft.parameters.soot_evolution) / 100

                                self.df.at[idx, f"{subcategory_key}:emission_index_nox"] += (
                                    recent_reference_aircraft_emission_index_nox
                                    * evolution_nox
                                    * aircraft_share
                                    / 100
                                )
                                self.df.at[idx, f"{subcategory_key}:emission_index_soot"] += (
                                    recent_reference_aircraft_emission_index_soot
                                    * evolution_soot
                                    * aircraft_share
                                    / 100
                                )

                                if aircraft.energy_type == "DROP_IN_FUEL":
                                    self.df.at[
                                        idx, f"{subcategory_key}:emission_index_nox:dropin_fuel"
                                    ] += (
                                        recent_reference_aircraft_emission_index_nox
                                        * evolution_nox
                                        * aircraft_share
                                        / 100
                                    )
                                    self.df.at[
                                        idx, f"{subcategory_key}:emission_index_soot:dropin_fuel"
                                    ] += (
                                        recent_reference_aircraft_emission_index_soot
                                        * evolution_soot
                                        * aircraft_share
                                        / 100
                                    )
                                elif aircraft.energy_type == "HYDROGEN":
                                    self.df.at[
                                        idx, f"{subcategory_key}:emission_index_nox:hydrogen"
                                    ] += (
                                        recent_reference_aircraft_emission_index_nox
                                        * evolution_nox
                                        * aircraft_share
                                        / 100
                                    )
                                elif aircraft.energy_type == "ELECTRIC":
                                    self.df.at[
                                        idx, f"{subcategory_key}:emission_index_nox:electric"
                                    ] += (
                                        recent_reference_aircraft_emission_index_nox
                                        * evolution_nox
                                        * aircraft_share
                                        / 100
                                    )
                                elif aircraft.energy_type == "HYBRID_ELECTRIC":
                                    self.df.at[
                                        idx, f"{subcategory_key}:emission_index_nox:hybrid_electric"
                                    ] += (
                                        recent_reference_aircraft_emission_index_nox
                                        * evolution_nox
                                        * aircraft_share
                                        / 100
                                    )
                                    self.df.at[
                                        idx,
                                        f"{subcategory_key}:emission_index_soot:hybrid_electric",
                                    ] += (
                                        recent_reference_aircraft_emission_index_soot
                                        * evolution_soot
                                        * aircraft_share
                                        / 100
                                    )

            # Aggregating results for each category
            temp_dict = {
                key: np.zeros_like(self.df.index, dtype=float)
                for key in [
                    f"{category.name}:emission_index_nox",
                    f"{category.name}:emission_index_soot",
                    f"{category.name}:emission_index_nox:dropin_fuel",
                    f"{category.name}:emission_index_nox:hydrogen",
                    f"{category.name}:emission_index_nox:electric",
                    f"{category.name}:emission_index_nox:hybrid_electric",
                    f"{category.name}:emission_index_soot:dropin_fuel",
                    f"{category.name}:emission_index_soot:hydrogen",
                    f"{category.name}:emission_index_soot:electric",
                    f"{category.name}:emission_index_soot:hybrid_electric",
                ]
            }

            for subcategory in category.subcategories.values():
                subcategory_key = f"{category.name}:{subcategory.name}"
                for idx in self.df.index:
                    for emission_type in ["nox", "soot"]:
                        for energy_type in [
                            "dropin_fuel",
                            "hydrogen",
                            "electric",
                            "hybrid_electric",
                        ]:
                            key = f"{subcategory_key}:emission_index_{emission_type}:{energy_type}"
                            if key in self.df.columns:
                                temp_dict[
                                    f"{category.name}:emission_index_{emission_type}:{energy_type}"
                                ][self.df.index.get_loc(idx)] += self.df.at[idx, key]

            # Final aggregation
            for idx in self.df.index:
                dropin_fuel_share = self.df.at[idx, f"{category.name}:share:dropin_fuel"]
                hydrogen_share = self.df.at[idx, f"{category.name}:share:hydrogen"]
                electric_share = self.df.at[idx, f"{category.name}:share:electric"]
                hybrid_electric_share = self.df.at[idx, f"{category.name}:share:hybrid_electric"]

                total_share = (
                    dropin_fuel_share + hydrogen_share + electric_share + hybrid_electric_share
                )
                if total_share > 0:
                    self.df.at[idx, f"{category.name}:emission_index_nox"] = (
                        temp_dict[f"{category.name}:emission_index_nox:dropin_fuel"][
                            self.df.index.get_loc(idx)
                        ]
                        * (dropin_fuel_share / 100)
                        + temp_dict[f"{category.name}:emission_index_nox:hydrogen"][
                            self.df.index.get_loc(idx)
                        ]
                        * (hydrogen_share / 100)
                        + temp_dict[f"{category.name}:emission_index_nox:electric"][
                            self.df.index.get_loc(idx)
                        ]
                        * (electric_share / 100)
                        + temp_dict[f"{category.name}:emission_index_nox:hybrid_electric"][
                            self.df.index.get_loc(idx)
                        ]
                        * (hybrid_electric_share / 100)
                    )
                    self.df.at[idx, f"{category.name}:emission_index_soot"] = (
                        temp_dict[f"{category.name}:emission_index_soot:dropin_fuel"][
                            self.df.index.get_loc(idx)
                        ]
                        * (dropin_fuel_share / 100)
                        + temp_dict[f"{category.name}:emission_index_soot:hydrogen"][
                            self.df.index.get_loc(idx)
                        ]
                        * (hydrogen_share / 100)
                        + temp_dict[f"{category.name}:emission_index_soot:electric"][
                            self.df.index.get_loc(idx)
                        ]
                        * (electric_share / 100)
                        + temp_dict[f"{category.name}:emission_index_soot:hybrid_electric"][
                            self.df.index.get_loc(idx)
                        ]
                        * (hybrid_electric_share / 100)
                    )

    def _compute_mean_energy_consumption_per_category_wrt_energy_type(self):
        """Compute mean energy consumption per category by energy type.

        Aggregates subcategory-level energy consumption values to the category
        level. For each energy type (drop-in fuel, hydrogen, electric, hybrid
        electric), calculates the share-weighted mean energy consumption.

        The mean consumption for each energy type is computed by dividing
        the total energy consumption by the corresponding share. The overall
        category mean consumption is then computed as a weighted average
        across all energy types.

        Results are stored in the DataFrame with keys like:
        ``{category}:energy_consumption:{energy_type}``
        ``{category}:energy_consumption``
        """
        for category in self.fleet.categories.values():
            # Mean energy consumption per category
            # Initialization
            self.df[category.name + ":energy_consumption:dropin_fuel"] = 0.0
            self.df[category.name + ":energy_consumption:hydrogen"] = 0.0
            self.df[category.name + ":energy_consumption:electric"] = 0.0
            self.df[category.name + ":energy_consumption:hybrid_electric"] = 0.0
            # Calculation
            for subcategory in category.subcategories.values():
                # TODO: verify aircraft order
                for k in self.df.index:
                    if self.df.loc[k, category.name + ":share:dropin_fuel"] != 0.0:
                        self.df.loc[k, category.name + ":energy_consumption:dropin_fuel"] += (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":energy_consumption:dropin_fuel",
                            ]
                            / (self.df.loc[k, category.name + ":share:dropin_fuel"] / 100)
                        )
                    else:
                        self.df.loc[k, category.name + ":energy_consumption:dropin_fuel"] = 0.0

                    if self.df.loc[k, category.name + ":share:hydrogen"] != 0.0:
                        self.df.loc[k, category.name + ":energy_consumption:hydrogen"] += (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":energy_consumption:hydrogen",
                            ]
                            / (self.df.loc[k, category.name + ":share:hydrogen"] / 100)
                        )
                    else:
                        self.df.loc[k, category.name + ":energy_consumption:hydrogen"] = 0.0

                    if self.df.loc[k, category.name + ":share:electric"] != 0.0:
                        self.df.loc[k, category.name + ":energy_consumption:electric"] += (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":energy_consumption:electric",
                            ]
                            / (self.df.loc[k, category.name + ":share:electric"] / 100)
                        )
                    else:
                        self.df.loc[k, category.name + ":energy_consumption:electric"] = 0.0

                    if self.df.loc[k, category.name + ":share:hybrid_electric"] != 0.0:
                        self.df.loc[k, category.name + ":energy_consumption:hybrid_electric"] += (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":energy_consumption:hybrid_electric",
                            ]
                            / (self.df.loc[k, category.name + ":share:hybrid_electric"] / 100)
                        )
                    else:
                        self.df.loc[k, category.name + ":energy_consumption:hybrid_electric"] = 0.0

            # Mean consumption
            for k in self.df.index:
                self.df.loc[k, category.name + ":energy_consumption"] = (
                    self.df.loc[k, category.name + ":energy_consumption:dropin_fuel"]
                    * (self.df.loc[k, category.name + ":share:dropin_fuel"] / 100)
                    + self.df.loc[k, category.name + ":energy_consumption:hydrogen"]
                    * (self.df.loc[k, category.name + ":share:hydrogen"] / 100)
                    + self.df.loc[k, category.name + ":energy_consumption:electric"]
                    * (self.df.loc[k, category.name + ":share:electric"] / 100)
                    + self.df.loc[k, category.name + ":energy_consumption:hybrid_electric"]
                    * (self.df.loc[k, category.name + ":share:hybrid_electric"] / 100)
                )

    def _compute_mean_doc_non_energy(self):
        """Compute mean non-energy DOC per category by energy type.

        Aggregates subcategory-level DOC (non-energy) values to the category
        level. For each energy type (drop-in fuel, hydrogen, electric, hybrid
        electric), calculates the share-weighted mean DOC.

        The mean DOC for each energy type is computed by dividing the total
        DOC by the corresponding share. The overall category mean DOC is
        then computed as a weighted average across all energy types.

        Results are stored in the DataFrame with keys like:
        ``{category}:doc_non_energy:{energy_type}``
        ``{category}:doc_non_energy``
        """
        for category in self.fleet.categories.values():
            # Mean non energy DOC per category
            # Initialization
            self.df[category.name + ":doc_non_energy:dropin_fuel"] = 0.0
            self.df[category.name + ":doc_non_energy:hydrogen"] = 0.0
            self.df[category.name + ":doc_non_energy:electric"] = 0.0
            self.df[category.name + ":doc_non_energy:hybrid_electric"] = 0.0
            # Calculation
            for subcategory in category.subcategories.values():
                # TODO: verify aircraft order
                for k in self.df.index:
                    if self.df.loc[k, category.name + ":share:dropin_fuel"] != 0.0:
                        self.df.loc[k, category.name + ":doc_non_energy:dropin_fuel"] += (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":doc_non_energy:dropin_fuel",
                            ]
                            / (self.df.loc[k, category.name + ":share:dropin_fuel"] / 100)
                        )
                    else:
                        self.df.loc[k, category.name + ":doc_non_energy:dropin_fuel"] = 0.0

                    if self.df.loc[k, category.name + ":share:hydrogen"] != 0.0:
                        self.df.loc[k, category.name + ":doc_non_energy:hydrogen"] += self.df.loc[
                            k,
                            category.name + ":" + subcategory.name + ":doc_non_energy:hydrogen",
                        ] / (self.df.loc[k, category.name + ":share:hydrogen"] / 100)
                    else:
                        self.df.loc[k, category.name + ":doc_non_energy:hydrogen"] = 0.0

                    if self.df.loc[k, category.name + ":share:electric"] != 0.0:
                        self.df.loc[k, category.name + ":doc_non_energy:electric"] += self.df.loc[
                            k,
                            category.name + ":" + subcategory.name + ":doc_non_energy:electric",
                        ] / (self.df.loc[k, category.name + ":share:electric"] / 100)
                    else:
                        self.df.loc[k, category.name + ":doc_non_energy:electric"] = 0.0

                    if self.df.loc[k, category.name + ":share:hybrid_electric"] != 0.0:
                        self.df.loc[k, category.name + ":doc_non_energy:hybrid_electric"] += (
                            self.df.loc[
                                k,
                                category.name
                                + ":"
                                + subcategory.name
                                + ":doc_non_energy:hybrid_electric",
                            ]
                            / (self.df.loc[k, category.name + ":share:hybrid_electric"] / 100)
                        )
                    else:
                        self.df.loc[k, category.name + ":doc_non_energy:hybrid_electric"] = 0.0

            # Mean non energy DOC
            for k in self.df.index:
                self.df.loc[k, category.name + ":doc_non_energy"] = (
                    self.df.loc[k, category.name + ":doc_non_energy:dropin_fuel"]
                    * (self.df.loc[k, category.name + ":share:dropin_fuel"] / 100)
                    + self.df.loc[k, category.name + ":doc_non_energy:hydrogen"]
                    * (self.df.loc[k, category.name + ":share:hydrogen"] / 100)
                    + self.df.loc[k, category.name + ":doc_non_energy:electric"]
                    * (self.df.loc[k, category.name + ":share:electric"] / 100)
                    + self.df.loc[k, category.name + ":doc_non_energy:hybrid_electric"]
                    * (self.df.loc[k, category.name + ":share:hybrid_electric"] / 100)
                )

    def _compute_mean_non_co2_emission_index(self):
        """Compute mean NOx and soot emission indices per category.

        Aggregates subcategory-level emission indices to the category level.
        For each energy type (drop-in fuel, hydrogen, electric, hybrid electric),
        calculates the share-weighted mean emission index.

        The mean emission index for each energy type is computed by dividing
        the total emission index by the corresponding share. The overall
        category mean is then computed as a weighted average across all
        energy types.

        Results are stored in the DataFrame with keys like:
        ``{category}:emission_index_nox:{energy_type}``
        ``{category}:emission_index_soot:{energy_type}``
        ``{category}:emission_index_nox``
        ``{category}:emission_index_soot``
        """
        temp_dict = {}

        for category in self.fleet.categories.values():
            category_name = category.name
            # Initialize temporary storage for each energy type
            for energy_type in ["dropin_fuel", "hydrogen", "electric", "hybrid_electric"]:
                temp_dict[f"{category_name}:emission_index_nox:{energy_type}"] = np.zeros(
                    len(self.df)
                )
                temp_dict[f"{category_name}:emission_index_soot:{energy_type}"] = np.zeros(
                    len(self.df)
                )

            for subcategory in category.subcategories.values():
                subcategory_key = f"{category_name}:{subcategory.name}"
                for k in self.df.index:
                    dropin_fuel_share = self.df.at[k, f"{category_name}:share:dropin_fuel"]
                    hydrogen_share = self.df.at[k, f"{category_name}:share:hydrogen"]
                    electric_share = self.df.at[k, f"{category_name}:share:electric"]
                    hybrid_electric_share = self.df.at[k, f"{category_name}:share:hybrid_electric"]

                    if dropin_fuel_share != 0.0:
                        temp_dict[f"{category_name}:emission_index_nox:dropin_fuel"][
                            k - self.df.index[0]
                        ] += self.df.at[k, f"{subcategory_key}:emission_index_nox:dropin_fuel"] / (
                            dropin_fuel_share / 100
                        )
                        temp_dict[f"{category_name}:emission_index_soot:dropin_fuel"][
                            k - self.df.index[0]
                        ] += self.df.at[k, f"{subcategory_key}:emission_index_soot:dropin_fuel"] / (
                            dropin_fuel_share / 100
                        )

                    if hydrogen_share != 0.0:
                        temp_dict[f"{category_name}:emission_index_nox:hydrogen"][
                            k - self.df.index[0]
                        ] += self.df.at[k, f"{subcategory_key}:emission_index_nox:hydrogen"] / (
                            hydrogen_share / 100
                        )
                        temp_dict[f"{category_name}:emission_index_soot:hydrogen"][
                            k - self.df.index[0]
                        ] += self.df.at[k, f"{subcategory_key}:emission_index_soot:hydrogen"] / (
                            hydrogen_share / 100
                        )

                    if electric_share != 0.0:
                        temp_dict[f"{category_name}:emission_index_nox:electric"][
                            k - self.df.index[0]
                        ] += self.df.at[k, f"{subcategory_key}:emission_index_nox:electric"] / (
                            electric_share / 100
                        )
                        temp_dict[f"{category_name}:emission_index_soot:electric"][
                            k - self.df.index[0]
                        ] += self.df.at[k, f"{subcategory_key}:emission_index_soot:electric"] / (
                            electric_share / 100
                        )

                    if hybrid_electric_share != 0.0:
                        temp_dict[f"{category_name}:emission_index_nox:hybrid_electric"][
                            k - self.df.index[0]
                        ] += self.df.at[
                            k, f"{subcategory_key}:emission_index_nox:hybrid_electric"
                        ] / (hybrid_electric_share / 100)
                        temp_dict[f"{category_name}:emission_index_soot:hybrid_electric"][
                            k - self.df.index[0]
                        ] += self.df.at[
                            k, f"{subcategory_key}:emission_index_soot:hybrid_electric"
                        ] / (hybrid_electric_share / 100)

            # Calculate mean emission index
            for k in self.df.index:
                self.df.at[k, f"{category_name}:emission_index_nox"] = (
                    temp_dict[f"{category_name}:emission_index_nox:dropin_fuel"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:dropin_fuel"] / 100)
                    + temp_dict[f"{category_name}:emission_index_nox:hydrogen"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:hydrogen"] / 100)
                    + temp_dict[f"{category_name}:emission_index_nox:electric"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:electric"] / 100)
                    + temp_dict[f"{category_name}:emission_index_nox:hybrid_electric"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:hybrid_electric"] / 100)
                )
                self.df.at[k, f"{category_name}:emission_index_soot"] = (
                    temp_dict[f"{category_name}:emission_index_soot:dropin_fuel"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:dropin_fuel"] / 100)
                    + temp_dict[f"{category_name}:emission_index_soot:hydrogen"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:hydrogen"] / 100)
                    + temp_dict[f"{category_name}:emission_index_soot:electric"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:electric"] / 100)
                    + temp_dict[f"{category_name}:emission_index_soot:hybrid_electric"][
                        k - self.df.index[0]
                    ]
                    * (self.df.at[k, f"{category_name}:share:hybrid_electric"] / 100)
                )

        final_dict = {
            key: np.array(values) if isinstance(values, list) else values
            for key, values in temp_dict.items()
        }

        final_df = pd.DataFrame(final_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

    def plot(self):
        """Generate fleet renewal visualization plots.

        Creates a 2-row matplotlib figure with one column per category.
        The top row shows stacked area plots of aircraft shares over time,
        including old reference, recent reference, and new aircraft types.
        The bottom row shows the evolution of mean fleet energy consumption.

        The plot displays data from prospection_start_year to end_year.
        Aircraft shares are shown as cumulative (stacked) areas, while
        energy consumption is shown as a line plot.
        """
        x = np.linspace(
            self.prospection_start_year,
            self.end_year,
            self.end_year - self.prospection_start_year + 1,
        )

        categories = list(self.fleet.categories.values())

        f, axs = plt.subplots(2, len(categories), figsize=(20, 10))

        for i, category in enumerate(categories):
            # Top plot
            ax = axs[0, i]

            # Initial subcategory
            subcategory = category.subcategories[0]
            # Old reference aircraft
            var_name = (
                category.name + ":" + subcategory.name + ":" + "old_reference:single_aircraft_share"
            )
            ax.fill_between(
                x,
                self.df.loc[self.prospection_start_year : self.end_year, var_name],
                label=subcategory.name + " - Old reference aircraft",
            )

            # Recent reference aircraft
            var_name = (
                category.name
                + ":"
                + subcategory.name
                + ":"
                + "recent_reference:single_aircraft_share"
            )
            ax.fill_between(
                x,
                self.df.loc[self.prospection_start_year : self.end_year, var_name],
                label=subcategory.name + " - Recent reference aircraft",
            )

            for j, subcategory in category.subcategories.items():
                # New aircraft
                for aircraft in subcategory.aircraft.values():
                    var_name = (
                        category.name
                        + ":"
                        + subcategory.name
                        + ":"
                        + aircraft.name
                        + ":single_aircraft_share"
                    )
                    ax.fill_between(
                        x,
                        self.df.loc[self.prospection_start_year : self.end_year, var_name],
                        label=subcategory.name + " - " + aircraft.name,
                    )

            ax.set_xlim(self.prospection_start_year, self.end_year)
            ax.set_ylim(0, 100)
            ax.legend(loc="upper left", prop={"size": 8})
            ax.set_xlabel("Year")
            ax.set_ylabel("Share in fleet [%]")
            ax.set_title(categories[i].name)

            # Bottom plot
            ax = axs[1, i]
            ax.plot(
                x,
                self.df.loc[
                    self.prospection_start_year : self.end_year,
                    category.name + ":energy_consumption",
                ],
            )

            ax.set_xlim(self.prospection_start_year, self.end_year)
            ax.set_xlabel("Year")
            ax.set_ylabel("Fleet mean energy consumption [MJ/ASK]")
            # ax.set_title(categories[i].name)

        plt.plot()
        # plt.savefig("fleet_renewal.pdf")

    def _compute(self, life, entry_into_service_year, share, recent=False):
        """Compute S-shaped aircraft market penetration curve.

        Calculates the share of an aircraft type in the fleet over time
        using a logistic (S-shaped) function. The curve models the typical
        technology adoption pattern where market share grows slowly at first,
        then accelerates, and finally levels off.

        Parameters
        ----------
        life : float
            Aircraft operational lifetime in years. Determines the slope
            of the S-curve (shorter life = steeper curve).
        entry_into_service_year : int
            Year when the aircraft enters commercial service.
        share : float
            Target maximum market share for this aircraft type [%].
        recent : bool, optional
            If True, the midpoint is at entry_into_service_year (for recent
            reference aircraft). If False, the midpoint is at entry + life/2
            (for new aircraft). Default is False.

        Returns
        -------
        numpy.ndarray
            Array of share values [%] for each year from historic_start_year
            to end_year. Values below a 2% threshold are set to zero.
        """
        x = np.linspace(
            self.historic_start_year,
            self.end_year,
            self.end_year - self.historic_start_year + 1,
        )

        # Intermediate variable for S-shaped function
        limit = 2
        growth_rate = np.log(100 / limit - 1) / (life / 2)

        if not recent:
            midpoint_year = entry_into_service_year + life / 2
        else:
            midpoint_year = entry_into_service_year

        y_share = share / (1 + np.exp(-growth_rate * (x - midpoint_year)))
        y_share_max = 100 / (1 + np.exp(-growth_rate * (x - midpoint_year)))

        y = np.where(y_share_max < limit, 0.0, y_share)
        return y

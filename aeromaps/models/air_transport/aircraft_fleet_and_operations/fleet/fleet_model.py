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
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_assignment import (
    FleetAssignmentMixin,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_performance import (
    FleetPerformanceMixin,
)
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

# Pairs of (absolute_field, relative_field) on AircraftParameters that describe
# the same performance metric. Exactly one of the two must be set on each new
# aircraft card. See _validate_perf_mode.
_PERF_PAIRS = [
    ("energy_per_ask", "consumption_evolution"),
    ("emission_index_nox", "nox_evolution"),
    ("emission_index_soot", "soot_evolution"),
    ("doc_non_energy_base", "doc_non_energy_evolution"),
]


def _validate_perf_mode(aircraft_id: str, params: "AircraftParameters") -> None:
    """Enforce that each performance metric is declared either absolute or relative, not both/neither."""
    for absolute_name, relative_name in _PERF_PAIRS:
        has_abs = getattr(params, absolute_name) is not None
        has_rel = getattr(params, relative_name) is not None
        if has_abs and has_rel:
            raise ValueError(
                f"Aircraft '{aircraft_id}': both '{absolute_name}' (absolute) and "
                f"'{relative_name}' (relative) are set. Pick exactly one."
            )
        if not has_abs and not has_rel:
            raise ValueError(
                f"Aircraft '{aircraft_id}': neither '{absolute_name}' nor "
                f"'{relative_name}' is set. Pick exactly one."
            )


@dataclass
class AircraftParameters:
    """Parameters defining an aircraft's characteristics and performance.

    Performance metrics (energy per ASK, NOx, soot, non-energy DOC) can be
    declared in one of two modes per metric, independently:

    - **Relative**: ``*_evolution`` field, expressed as a percentage delta vs
      the subcategory's recent reference aircraft.
    - **Absolute**: same field name as on the reference-aircraft card
      (``energy_per_ask``, ``emission_index_nox``, ``emission_index_soot``,
      ``doc_non_energy_base``), expressed in absolute units.

    For each of the four metrics, **exactly one** of the relative or absolute
    field must be set. Both-set or neither-set raises ``ValueError`` at YAML
    load time (see :func:`Fleet._load_aircraft_inventory`).

    Attributes
    ----------
    entry_into_service_year
        Year when the aircraft enters service [yr].
    consumption_evolution
        Relative change in energy consumption compared to reference aircraft [%].
    energy_per_ask
        Absolute energy consumption per ASK [MJ/ASK]. Alternative to ``consumption_evolution``.
    nox_evolution
        Relative change in NOx emissions compared to reference aircraft [%].
    emission_index_nox
        Absolute NOx emission index per ASK [kg/ASK]. Alternative to ``nox_evolution``.
    soot_evolution
        Relative change in soot emissions compared to reference aircraft [%].
    emission_index_soot
        Absolute soot emission index per ASK [kg/ASK]. Alternative to ``soot_evolution``.
    doc_non_energy_evolution
        Relative change in non-energy direct operating costs compared to reference aircraft [%].
    doc_non_energy_base
        Absolute non-energy DOC per ASK [€/ASK]. Alternative to ``doc_non_energy_evolution``.
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
    energy_per_ask: Optional[float] = None
    nox_evolution: Optional[float] = None
    emission_index_nox: Optional[float] = None
    soot_evolution: Optional[float] = None
    emission_index_soot: Optional[float] = None
    doc_non_energy_evolution: Optional[float] = None
    doc_non_energy_base: Optional[float] = None
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

    # Per-metric resolvers: return the absolute value of a performance metric,
    # either taken directly from the aircraft card (absolute mode) or computed
    # from the recent reference aircraft and the relative evolution (relative
    # mode). Exactly one branch fires per metric, guaranteed by
    # _validate_perf_mode at YAML load time.
    #
    # For an aircraft that serves multiple markets, the relative-mode result
    # depends on which market's recent reference is passed in; the absolute-mode
    # result is the user-provided value as-is in both markets.

    def resolved_energy_per_ask(self, recent_ref: "ReferenceAircraftParameters") -> float:
        if self.parameters.energy_per_ask is not None:
            return float(self.parameters.energy_per_ask)
        return recent_ref.energy_per_ask * (1 + float(self.parameters.consumption_evolution) / 100)

    def resolved_emission_index_nox(self, recent_ref: "ReferenceAircraftParameters") -> float:
        if self.parameters.emission_index_nox is not None:
            return float(self.parameters.emission_index_nox)
        return recent_ref.emission_index_nox * (1 + float(self.parameters.nox_evolution) / 100)

    def resolved_emission_index_soot(self, recent_ref: "ReferenceAircraftParameters") -> float:
        if self.parameters.emission_index_soot is not None:
            return float(self.parameters.emission_index_soot)
        return recent_ref.emission_index_soot * (1 + float(self.parameters.soot_evolution) / 100)

    def resolved_doc_non_energy_base(self, recent_ref: "ReferenceAircraftParameters") -> float:
        if self.parameters.doc_non_energy_base is not None:
            return float(self.parameters.doc_non_energy_base)
        return recent_ref.doc_non_energy_base * (
            1 + float(self.parameters.doc_non_energy_evolution) / 100
        )


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
        Human-readable display name for the category (e.g., 'Short Range', 'Medium Range',
        'Long Range'), populated from
        :class:`~aeromaps.models.air_transport.markets.market.Market`.name when a
        :class:`MarketManager` is available, otherwise from the ``market_id``.
    parameters
        Category parameters including aircraft lifetime.
    market_id
        Market identifier that references this category's entry in ``markets.yaml``
        (e.g., ``short_range``).

    Attributes
    ----------
    name : str
        Human-readable display name for the category.
    market_id : str
        Market identifier string (e.g., ``"short_range"``).
    parameters : CategoryParameters
        Category parameters including aircraft lifetime.
    subcategories : Dict[int, SubCategory]
        Dictionary of subcategories within this category.
    total_shares : float
        Sum of all subcategory market shares (should equal 100%).
    calibration_subcategory_id : str or None
        ID of the subcategory used for reference aircraft calibration.
    """

    def __init__(self, name: str, parameters: CategoryParameters, market_id: str):
        self.name = name
        self.market_id = market_id
        self.parameters = parameters
        self.subcategories: Dict[int, SubCategory] = {}
        self.total_shares = 0.0
        self.calibration_subcategory_id: Optional[str] = None

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
    markets
        :class:`~aeromaps.models.air_transport.markets.market_manager.MarketManager`
        instance used to look up market display names and validate the
        ``market_served:`` field of each category entry in ``fleet.yaml``.
        When ``None``, validation is skipped and the
        ``market_id`` is used as the display name (used by lightweight unit tests
        that bypass the process-level wiring).

    Attributes
    ----------
    categories : Dict[str, Category]
        Dictionary of aircraft categories indexed by category name.
    parameters
        External parameters for reference aircraft calibration.
    markets
        The :class:`~aeromaps.models.air_transport.markets.market_manager.MarketManager`
        passed at construction time (or ``None``).
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
        markets=None,
    ):
        self._categories: Dict[str, Category] = {}
        self.parameters = parameters
        self.markets = markets
        # Populated during _build_fleet_from_yaml: subcategory id → display name.
        self._subcategory_name_by_id: Dict[str, str] = {}
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
            _validate_perf_mode(aircraft_id, params)
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
        # Build id → display name lookup used by _calibrate_reference_aircraft (3.B).
        self._subcategory_name_by_id = {
            sub_id: entry.get("name", sub_id) for sub_id, entry in subcategory_inventory.items()
        }

        # Schema: ``categories:`` is a list of entries; each entry must declare the
        # ``market_served:`` it serves (a market_id from markets.yaml).
        category_entries = fleet_config.get("categories", [])

        # Build a lookup from market_id → Market when MarketManager is available.
        market_lookup: Dict[str, Any] = {}
        if self.markets is not None:
            market_lookup = {m.id: m for m in self.markets.get_all()}

            # Validate: every category entry must reference a known market_id.
            unknown_ids = [
                entry.get("market_served")
                for entry in category_entries
                if entry.get("market_served") not in market_lookup
            ]
            if unknown_ids:
                raise KeyError(
                    f"fleet.yaml references unknown market IDs: {unknown_ids}. "
                    f"Known market IDs: {list(market_lookup)}"
                )

            # Validate: every passenger market must be served by a category entry.
            served_ids = {entry.get("market_served") for entry in category_entries}
            passenger_market_ids = {m.id for m in self.markets.get(traffic_type="passenger")}
            missing_ids = passenger_market_ids - served_ids
            if missing_ids:
                raise KeyError(
                    f"fleet.yaml is missing categories for passenger markets: {sorted(missing_ids)}"
                )

        for market_cfg in category_entries:
            market_id = market_cfg.get("market_served")
            if market_id is None:
                continue

            # Resolve display name: prefer MarketManager, fall back to market_id.
            cat_name = market_lookup[market_id].name if market_id in market_lookup else market_id

            cat_params = CategoryParameters(**market_cfg.get("parameters", {}))
            category = Category(cat_name, parameters=cat_params, market_id=market_id)
            category.calibration_subcategory_id = market_cfg.get("calibration_subcategory")

            for sub_cfg_entry in market_cfg.get("subcategories", []):
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
                            f"Aircraft '{aircraft_id}' is missing from inventory "
                            f"{self.aircraft_inventory_path}"
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

    def _calibration_subcategory_for(self, market_id: str) -> Optional[str]:
        """Return the calibration subcategory id for the given market id.

        Looks up the :class:`Category` whose ``market_id`` matches *market_id*
        and returns its ``calibration_subcategory_id`` (set during
        ``_build_fleet_from_yaml`` from the ``calibration_subcategory:`` YAML
        field).  Returns ``None`` if no matching category is found.
        """
        for cat in self.categories.values():
            if cat.market_id == market_id:
                return cat.calibration_subcategory_id
        return None

    def _subcategory_display_name(self, sub_id: str) -> Optional[str]:
        """Return the display name for a subcategory id.

        Uses the ``_subcategory_name_by_id`` lookup populated during
        ``_build_fleet_from_yaml``.  Returns ``None`` when *sub_id* is not found.
        """
        return self._subcategory_name_by_id.get(sub_id)

    def _calibrate_reference_aircraft(self):
        if self.parameters is None or self.markets is None:
            return

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            cat_name = market.name

            # Calibration subcategory is declared in fleet.yaml via
            # ``calibration_subcategory: <id>``.
            sub_id = self._calibration_subcategory_for(mid)
            if sub_id is None:
                continue
            sub_name = self._subcategory_display_name(sub_id)
            if sub_name is None:
                continue

            subcat = self._get_subcategory(cat_name, sub_name)
            if subcat is None:
                continue

            energy_share_param = f"{mid}_energy_share_2019"
            rpk_share_param = f"{mid}_rpk_share_2019"
            self._run_calibration_for_subcat(subcat, cat_name, energy_share_param, rpk_share_param)

    def _run_calibration_for_subcat(
        self,
        subcat,
        category_name: str,
        energy_share_param: str,
        rpk_share_param: str,
    ) -> None:
        """Calibrate a single reference-aircraft pair.

        Parameters
        ----------
        subcat
            The :class:`SubCategory` whose reference aircraft will be calibrated.
        category_name
            Human-readable market / category name (used in warning messages).
        energy_share_param
            Attribute name on ``self.parameters`` for the 2019 energy share
            (e.g. ``"short_range_energy_share_2019"``).
        rpk_share_param
            Attribute name on ``self.parameters`` for the 2019 RPK share
            (e.g. ``"short_range_rpk_share_2019"``).
        """
        old_energy = subcat.old_reference_aircraft.energy_per_ask
        recent_energy = subcat.recent_reference_aircraft.energy_per_ask
        if old_energy is None or recent_energy is None:
            raise ValueError(f"{category_name} reference aircraft energy_per_ask must be defined")

        mean_energy_init_ask = (
            self.parameters.energy_consumption_init[2019]
            * getattr(self.parameters, energy_share_param)
        ) / (self.parameters.ask_init[2019] * getattr(self.parameters, rpk_share_param))

        share_recent = (mean_energy_init_ask - old_energy) / (recent_energy - old_energy)

        # We fix the life to 25 years for calibration
        # This way the share between old and recent reference aircraft in 2019 remains the same
        life = 25
        lam = np.log(100 / 2 - 1) / (life / 2)

        if 1 > share_recent > 0:
            t0 = np.log((1 - share_recent) / share_recent) / lam + (
                self.parameters.prospection_start_year - 1
            )
            t_eis = t0 - life / 2
        elif share_recent > 1:
            warnings.warn(
                f"Warning Message - Fleet Model: {category_name} Aircraft: "
                f"Average initial {category_name} fleet energy per ASK is lower than default energy per ASK "
                f"for the recent reference aircraft - AeroMAPS is using initial {category_name} fleet energy per ASK "
                f"as old and recent reference aircraft energy performances!"
            )
            t_eis = self.parameters.prospection_start_year - 1 - life
            subcat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask
            subcat.recent_reference_aircraft.energy_per_ask = mean_energy_init_ask
        else:
            warnings.warn(
                f"Warning Message - Fleet Model: {category_name} Aircraft: "
                f"Average initial {category_name} fleet energy per ASK is higher than default energy per ASK for the old reference aircraft - "
                f"AeroMAPS is using initial {category_name} fleet energy per ASK as old aircraft energy performances. "
                f"Recent reference aircraft is introduced on first prospective year"
            )
            t_eis = self.parameters.prospection_start_year
            subcat.old_reference_aircraft.energy_per_ask = mean_energy_init_ask

        subcat.recent_reference_aircraft.entry_into_service_year = t_eis


class FleetModel(FleetAssignmentMixin, FleetPerformanceMixin, AeroMAPSModel):
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

    def __init__(self, name="fleet_model", fleet=None, markets=None, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.fleet = fleet
        self.markets = markets

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

        # Compute individual aircraft contributions to all performance metrics
        self._compute_aircraft_performance_contributions()

        # Compute fleet-renewal-only counterfactual performance (no new aircraft)
        self._compute_fleet_renewal_performance()

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

    def plot_performance_contributions(self, metric="energy"):
        """Plot individual aircraft contributions to a fleet performance metric.

        For each category shows:

        - Dashed grey line: recent reference value (neutral baseline).
        - Dashed orange line: fleet-renewal-only counterfactual (old aircraft
          phased out, replaced by recent reference — no new technology).
        - Red area above the baseline: penalty from old aircraft still in service.
        - Stacked coloured areas below the baseline: gain from each new aircraft
          type (stacked oldest-EIS first).
        - Black line: actual fleet mean.

        Parameters
        ----------
        metric : str
            One of ``"energy"``, ``"doc"``, ``"nox"``, ``"soot"``.

        Returns
        -------
        matplotlib.figure.Figure
        """
        _cfg = {
            "energy": {
                "fleet_col": lambda cat: f"{cat}:energy_consumption",
                "renewal_col": lambda cat: f"{cat}:energy_renewal_only",
                "contrib_col": lambda cat,
                sub,
                ac: f"{cat}:{sub}:{ac}:energy_efficiency_contribution",
                "old_col": lambda cat,
                sub: f"{cat}:{sub}:old_reference:energy_efficiency_contribution",
                "ref_val": lambda ref: float(ref.energy_per_ask),
                "ylabel": "Energy per ASK [MJ/ASK]",
            },
            "doc": {
                "fleet_col": lambda cat: f"{cat}:doc_non_energy",
                "renewal_col": lambda cat: f"{cat}:doc_renewal_only",
                "contrib_col": lambda cat, sub, ac: f"{cat}:{sub}:{ac}:doc_contribution",
                "old_col": lambda cat, sub: f"{cat}:{sub}:old_reference:doc_contribution",
                "ref_val": lambda ref: float(ref.doc_non_energy_base),
                "ylabel": "Non-energy DOC [€/ASK]",
            },
            "nox": {
                "fleet_col": lambda cat: f"{cat}:emission_index_nox",
                "renewal_col": lambda cat: f"{cat}:nox_renewal_only",
                "contrib_col": lambda cat, sub, ac: f"{cat}:{sub}:{ac}:nox_contribution",
                "old_col": lambda cat, sub: f"{cat}:{sub}:old_reference:nox_contribution",
                "ref_val": lambda ref: float(ref.emission_index_nox),
                "ylabel": "NOx emission index [kg/ASK]",
            },
            "soot": {
                "fleet_col": lambda cat: f"{cat}:emission_index_soot",
                "renewal_col": lambda cat: f"{cat}:soot_renewal_only",
                "contrib_col": lambda cat, sub, ac: f"{cat}:{sub}:{ac}:soot_contribution",
                "old_col": lambda cat, sub: f"{cat}:{sub}:old_reference:soot_contribution",
                "ref_val": lambda ref: float(ref.emission_index_soot),
                "ylabel": "Soot emission index [kg/ASK]",
            },
        }
        if metric not in _cfg:
            raise ValueError(f"metric must be one of {list(_cfg)}; got {metric!r}")
        cfg = _cfg[metric]

        years = self.df.loc[self.prospection_start_year : self.end_year].index
        categories = list(self.fleet.categories.values())
        fig, axs = plt.subplots(1, len(categories), figsize=(8 * len(categories), 5), squeeze=False)
        cmap = plt.get_cmap("tab10")

        for col_idx, category in enumerate(categories):
            ax = axs[0, col_idx]
            first_subcategory = category.subcategories[0]
            ref_recent_val = cfg["ref_val"](first_subcategory.recent_reference_aircraft)
            # prefix = f"{category.name}:{first_subcategory.name}"

            # Old-reference penalty (above baseline)
            old_penalty = -self.df.loc[
                years, cfg["old_col"](category.name, first_subcategory.name)
            ].values
            ax.fill_between(
                years,
                ref_recent_val,
                ref_recent_val + old_penalty,
                color="tomato",
                alpha=0.75,
                label="Old reference aircraft (penalty)",
            )

            # New aircraft gains (below baseline, stacked oldest → newest EIS)
            y_top = np.full(len(years), ref_recent_val)
            color_idx = 0
            for subcategory in category.subcategories.values():
                for aircraft in self._sorted_aircraft(subcategory):
                    gain = self.df.loc[
                        years,
                        cfg["contrib_col"](category.name, subcategory.name, aircraft.name),
                    ].values
                    ax.fill_between(
                        years,
                        y_top - gain,
                        y_top,
                        color=cmap(color_idx),
                        alpha=0.75,
                        label=f"{aircraft.name} (gain)",
                    )
                    y_top = y_top - gain
                    color_idx += 1

            # Recent reference baseline
            ax.axhline(
                ref_recent_val,
                color="grey",
                linestyle="--",
                linewidth=1,
                label="Recent reference baseline",
            )

            # Fleet-renewal-only counterfactual
            renewal = self.df.loc[years, cfg["renewal_col"](category.name)].values
            ax.plot(
                years,
                renewal,
                color="orange",
                linestyle="--",
                linewidth=1.5,
                label="Fleet renewal only (no new aircraft)",
            )

            # Actual fleet mean
            fleet_mean = self.df.loc[years, cfg["fleet_col"](category.name)].values
            ax.plot(years, fleet_mean, color="black", linewidth=2, label="Fleet mean")

            ax.set_xlim(self.prospection_start_year, self.end_year)
            ax.set_xlabel("Year")
            ax.set_ylabel(cfg["ylabel"])
            ax.set_title(category.name)
            ax.legend(loc="upper right", prop={"size": 8})

        fig.tight_layout()
        return fig

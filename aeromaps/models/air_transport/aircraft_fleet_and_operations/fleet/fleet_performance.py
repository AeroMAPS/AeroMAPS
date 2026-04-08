"""
fleet_performance
=================

Fleet performance metrics: energy consumption, DOC, and non-CO2 emissions.

This module provides ``FleetPerformanceMixin``, a mixin class intended to be
composed into ``FleetModel``.  It encapsulates all performance computations
that operate on the per-aircraft shares produced by ``FleetAssignmentMixin``:

* ``_compute_energy_consumption_and_share_wrt_energy_type`` — energy per ASK
  and fleet share broken down by energy type, at subcategory level.
* ``_compute_doc_non_energy`` — non-energy direct operating costs at
  subcategory level.
* ``_compute_non_co2_emission_index`` — NOx and soot emission indices at
  subcategory level, with preliminary category aggregation.
* ``_compute_mean_energy_consumption_per_category_wrt_energy_type`` — category-
  level weighted-mean energy consumption by energy type.
* ``_compute_mean_doc_non_energy`` — category-level weighted-mean DOC.
* ``_compute_mean_non_co2_emission_index`` — category-level weighted-mean NOx
  and soot indices.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class FleetPerformanceMixin:
    """Mixin providing fleet performance metric computation for FleetModel.

    All methods access fleet data and the model DataFrame through ``self``,
    which is expected to be a ``FleetModel`` instance whose assignment step
    has already been executed (i.e., ``aircraft_share`` columns are present
    in ``self.df``).
    """

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

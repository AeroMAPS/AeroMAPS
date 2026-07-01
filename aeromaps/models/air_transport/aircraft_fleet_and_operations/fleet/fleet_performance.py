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

from aeromaps.models.base import aeromaps_interpolation_function


# Despite the generic energy module, we do not plan yet to reach that levl of genericity
# for the available aircraft energy types in the fleet model.
# The current set of energy types is fixed, but the code is structured to allow easy addition of new energy types (amonia, hybrid-hydrogen, ...) in the future if needed.
# Canonical ordered list of energy types used throughout the fleet model.
# FLEET REFACTORING FLAG: In Phase 4 , downstream models will iterate over this same list when building
# dynamic I/O names templated as energy_per_ask_<market>_<carrier>.
ENERGY_TYPES = ["dropin_fuel", "hydrogen", "electric", "hybrid_electric"]

# Maps aircraft.energy_type enum values to the snake_case keys used in DataFrame columns.
# FLEET REFACTORING FLAG - TODO: we may avoid this mapping using only one case?
ENERGY_TYPE_KEY_MAP = {
    "DROP_IN_FUEL": "dropin_fuel",
    "HYDROGEN": "hydrogen",
    "ELECTRIC": "electric",
    "HYBRID_ELECTRIC": "hybrid_electric",
}

# Energy types that are considered to produce soot emissions.

SOOT_ENERGY_TYPES = {"DROP_IN_FUEL", "HYBRID_ELECTRIC"}


class FleetPerformanceMixin:
    """Mixin providing fleet performance metric computation for FleetModel.

    All methods access fleet data and the model DataFrame through ``self``,
    which is expected to be a ``FleetModel`` instance whose assignment step
    has already been executed (i.e., ``aircraft_share`` columns are present
    in ``self.df``).
    """

    def _continuous_improvement_factor(self, params):
        """Per-year multiplicative energy factor for an aircraft (default 1.0).

        ``params.continuous_improvement_factor_energy`` is an optional
        ``AeroMapsCustomDataType`` (years/values). When present, it is interpolated
        with the shared ``aeromaps_interpolation_function`` (honouring its declared
        ``method`` and ``positive_constraint``, with the last value held constant
        beyond the final reference year), exactly like every other custom data type
        in AeroMAPS. The resulting series spans ``prospection_start_year..end_year``;
        any historical years in ``self.df.index`` are filled with 1.0 (no
        improvement). When the field is absent, returns an all-ones array so the
        base ``energy_per_ask`` is used unchanged. Applied on top of the resolved
        (absolute or relative) base energy intensity.
        """
        cdt = getattr(params, "continuous_improvement_factor_energy", None)
        if cdt is None:
            return np.ones(len(self.df.index))
        series = aeromaps_interpolation_function(
            self,
            reference_years=cdt.years,
            reference_years_values=cdt.values,
            method=cdt.method,
            positive_constraint=cdt.positive_constraint,
            model_name="continuous_improvement_factor_energy",
        )
        # The shared interpolator only assigns prospection_start_year..end_year,
        # leaving historical years as NaN on the model index; fill them with 1.0
        # (no improvement) so the factor is neutral over the historical period.
        return series.reindex(self.df.index).fillna(1.0).values

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

            recent_reference_aircraft = category.subcategories[0].recent_reference_aircraft

            for i, subcategory in category.subcategories.items():
                subcategory_key = f"{category.name}:{subcategory.name}"

                if i == 0:
                    # Reference aircraft may also carry a per-year improvement factor
                    # (absent → all-ones), so old/recent references can improve over
                    # time exactly like new aircraft.
                    initial_energy_consumption = (
                        subcategory.old_reference_aircraft.energy_per_ask
                        * self._continuous_improvement_factor(subcategory.old_reference_aircraft)
                        * ref_old_aircraft_share
                        / 100
                        + subcategory.recent_reference_aircraft.energy_per_ask
                        * self._continuous_improvement_factor(subcategory.recent_reference_aircraft)
                        * ref_recent_aircraft_share
                        / 100
                    )
                    initial_share = ref_old_aircraft_share + ref_recent_aircraft_share
                else:
                    initial_energy_consumption = np.zeros_like(ref_old_aircraft_share)
                    initial_share = np.zeros_like(ref_old_aircraft_share)

                temp_dict[f"{subcategory_key}:energy_consumption:weighted_contribution"] = (
                    initial_energy_consumption.copy()
                )
                temp_dict[f"{subcategory_key}:share:total"] = initial_share.copy()
                for energy_type in ENERGY_TYPES:
                    is_dropin = energy_type == "dropin_fuel"
                    temp_dict[
                        f"{subcategory_key}:energy_consumption:weighted_contribution:{energy_type}"
                    ] = (
                        initial_energy_consumption.copy()
                        if is_dropin
                        else np.zeros_like(ref_old_aircraft_share)
                    )
                    temp_dict[f"{subcategory_key}:share:{energy_type}"] = (
                        initial_share.copy() if is_dropin else np.zeros_like(ref_old_aircraft_share)
                    )

                for aircraft in subcategory.aircraft.values():
                    aircraft_share = self.df[
                        f"{subcategory_key}:{aircraft.name}:aircraft_share"
                    ].values

                    energy_consumption = (
                        aircraft.resolved("energy_per_ask", recent_reference_aircraft)
                        * self._continuous_improvement_factor(aircraft.parameters)
                        * aircraft_share
                        / 100
                    )

                    temp_dict[f"{subcategory_key}:share:total"] += aircraft_share
                    temp_dict[f"{subcategory_key}:energy_consumption:weighted_contribution"] += (
                        energy_consumption
                    )

                    energy_type_key = ENERGY_TYPE_KEY_MAP[aircraft.energy_type]
                    if aircraft.energy_type == "HYBRID_ELECTRIC":
                        # Hybrid splits share and energy between drop-in fuel and electric.
                        # The hybrid_electric bucket tracks total hybrid energy for DOC/emissions.
                        hybridization_factor = float(aircraft.parameters.hybridization_factor)
                        temp_dict[f"{subcategory_key}:share:dropin_fuel"] += (
                            1 - hybridization_factor
                        ) * aircraft_share
                        temp_dict[f"{subcategory_key}:share:electric"] += (
                            hybridization_factor * aircraft_share
                        )
                        temp_dict[
                            f"{subcategory_key}:energy_consumption:weighted_contribution:hybrid_electric"
                        ] += energy_consumption
                        temp_dict[
                            f"{subcategory_key}:energy_consumption:weighted_contribution:dropin_fuel"
                        ] += (1 - hybridization_factor) * energy_consumption
                        temp_dict[
                            f"{subcategory_key}:energy_consumption:weighted_contribution:electric"
                        ] += hybridization_factor * energy_consumption
                    else:
                        temp_dict[f"{subcategory_key}:share:{energy_type_key}"] += aircraft_share
                        temp_dict[
                            f"{subcategory_key}:energy_consumption:weighted_contribution:{energy_type_key}"
                        ] += energy_consumption

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
        IT IS A 'WEIGHTED CONTRIBUTION' TO CATEGORY AVERAGE DOC, NOT A PER-AIRCRAFT VALUE.
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

            recent_reference_aircraft = category.subcategories[0].recent_reference_aircraft

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

                temp_dict[f"{subcategory_key}:doc_non_energy:weighted_contribution"] = (
                    initial_doc_non_energy.copy()
                )
                for energy_type in ENERGY_TYPES:
                    temp_dict[
                        f"{subcategory_key}:doc_non_energy:weighted_contribution:{energy_type}"
                    ] = (
                        initial_doc_non_energy.copy()
                        if energy_type == "dropin_fuel"
                        else np.zeros_like(ref_old_aircraft_share)
                    )

                for aircraft in subcategory.aircraft.values():
                    aircraft_share = self.df[
                        f"{subcategory_key}:{aircraft.name}:aircraft_share"
                    ].values

                    doc_non_energy = (
                        aircraft.resolved("doc_non_energy_base", recent_reference_aircraft)
                        * aircraft_share
                        / 100
                    )

                    temp_dict[f"{subcategory_key}:doc_non_energy:weighted_contribution"] += (
                        doc_non_energy
                    )

                    # We consider hybrid-electric as being a category on its own category (no fuel/electric split).
                    # TODO: is that propagated well in the downstream DOC energy chain?
                    energy_type_key = ENERGY_TYPE_KEY_MAP[aircraft.energy_type]
                    temp_dict[
                        f"{subcategory_key}:doc_non_energy:weighted_contribution:{energy_type_key}"
                    ] += doc_non_energy

            # Summing up doc_non_energy for categories
            for energy_type in ["dropin_fuel", "hydrogen", "electric", "hybrid_electric"]:
                # as a reminder, it is a weighted contribution to category's doc. Average per type of energy are computed in
                # _compute_mean_doc_non_energy.
                category_doc_key = (
                    f"{category.name}:doc_non_energy:weighted_contribution:{energy_type}"
                )
                subcategory_doc_key = (
                    f"{subcategory_key}:doc_non_energy:weighted_contribution:{energy_type}"
                )
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
        ``{category}:{subcategory}:emission_index_nox:weighted_contribution:{energy_type}``
        ``{category}:{subcategory}:emission_index_soot:weighted_contribution:{energy_type}``
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

            # Use the first subcategory's recent reference aircraft as baseline
            # for any aircraft declared in relative-evolution mode.
            recent_reference_aircraft = category.subcategories[0].recent_reference_aircraft

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
                self.df[f"{subcategory_key}:emission_index_nox:weighted_contribution"] = initial_nox
                self.df[f"{subcategory_key}:emission_index_soot:weighted_contribution"] = (
                    initial_soot
                )
                for energy_type in ENERGY_TYPES:
                    is_dropin = energy_type == "dropin_fuel"
                    self.df[
                        f"{subcategory_key}:emission_index_nox:weighted_contribution:{energy_type}"
                    ] = initial_nox.copy() if is_dropin else np.zeros_like(ref_old_aircraft_share)
                    self.df[
                        f"{subcategory_key}:emission_index_soot:weighted_contribution:{energy_type}"
                    ] = initial_soot.copy() if is_dropin else np.zeros_like(ref_old_aircraft_share)

                for aircraft in subcategory.aircraft.values():
                    aircraft_share_key = f"{subcategory_key}:{aircraft.name}:aircraft_share"
                    if aircraft_share_key in self.df.columns:
                        aircraft_share = self.df[aircraft_share_key].values

                        nox_wc = (
                            aircraft.resolved("emission_index_nox", recent_reference_aircraft)
                            * aircraft_share
                            / 100
                        )
                        soot_wc = (
                            aircraft.resolved("emission_index_soot", recent_reference_aircraft)
                            * aircraft_share
                            / 100
                        )

                        energy_type_key = ENERGY_TYPE_KEY_MAP[aircraft.energy_type]
                        self.df[f"{subcategory_key}:emission_index_nox:weighted_contribution"] += (
                            nox_wc
                        )
                        self.df[f"{subcategory_key}:emission_index_soot:weighted_contribution"] += (
                            soot_wc
                        )
                        self.df[
                            f"{subcategory_key}:emission_index_nox:weighted_contribution:{energy_type_key}"
                        ] += nox_wc
                        if aircraft.energy_type in SOOT_ENERGY_TYPES:
                            self.df[
                                f"{subcategory_key}:emission_index_soot:weighted_contribution:{energy_type_key}"
                            ] += soot_wc

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
            cat = category.name
            # Initialization
            for energy_type in ENERGY_TYPES:
                self.df[f"{cat}:energy_consumption:{energy_type}"] = 0.0
            # Calculation
            for subcategory in category.subcategories.values():
                # TODO: verify aircraft order
                for energy_type in ENERGY_TYPES:
                    share = self.df[f"{cat}:share:{energy_type}"].values
                    col = f"{cat}:energy_consumption:{energy_type}"
                    wc_col = f"{cat}:{subcategory.name}:energy_consumption:weighted_contribution:{energy_type}"
                    safe_share = np.where(share != 0.0, share / 100, 1.0)
                    self.df[col] = np.where(
                        share != 0.0,
                        self.df[col].values + self.df[wc_col].values / safe_share,
                        0.0,
                    )

            # Mean consumption
            self.df[f"{cat}:energy_consumption"] = sum(
                self.df[f"{cat}:energy_consumption:{energy_type}"].values
                * (self.df[f"{cat}:share:{energy_type}"].values / 100)
                for energy_type in ENERGY_TYPES
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
            cat = category.name
            # Initialization
            for energy_type in ENERGY_TYPES:
                self.df[f"{cat}:doc_non_energy:{energy_type}"] = 0.0
            # Calculation
            for subcategory in category.subcategories.values():
                # TODO: verify aircraft order
                for energy_type in ENERGY_TYPES:
                    share = self.df[f"{cat}:share:{energy_type}"].values
                    col = f"{cat}:doc_non_energy:{energy_type}"
                    wc_col = f"{cat}:{subcategory.name}:doc_non_energy:weighted_contribution:{energy_type}"
                    safe_share = np.where(share != 0.0, share / 100, 1.0)
                    self.df[col] = np.where(
                        share != 0.0,
                        self.df[col].values + self.df[wc_col].values / safe_share,
                        0.0,
                    )

            # Mean non energy DOC
            self.df[f"{cat}:doc_non_energy"] = sum(
                self.df[f"{cat}:doc_non_energy:{energy_type}"].values
                * (self.df[f"{cat}:share:{energy_type}"].values / 100)
                for energy_type in ENERGY_TYPES
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
            for energy_type in ENERGY_TYPES:
                temp_dict[f"{category_name}:emission_index_nox:{energy_type}"] = np.zeros(
                    len(self.df)
                )
                temp_dict[f"{category_name}:emission_index_soot:{energy_type}"] = np.zeros(
                    len(self.df)
                )

            for subcategory in category.subcategories.values():
                subcategory_key = f"{category_name}:{subcategory.name}"
                for energy_type in ENERGY_TYPES:
                    share = self.df[f"{category_name}:share:{energy_type}"].values
                    safe_share = np.where(share != 0.0, share / 100, 1.0)
                    for metric in ["nox", "soot"]:
                        wc = self.df[
                            f"{subcategory_key}:emission_index_{metric}:weighted_contribution:{energy_type}"
                        ].values
                        temp_dict[f"{category_name}:emission_index_{metric}:{energy_type}"] += (
                            np.where(share != 0.0, wc / safe_share, 0.0)
                        )

            # Calculate mean emission index (stored in temp_dict for final concat)
            for metric in ["nox", "soot"]:
                temp_dict[f"{category_name}:emission_index_{metric}"] = sum(
                    temp_dict[f"{category_name}:emission_index_{metric}:{energy_type}"]
                    * (self.df[f"{category_name}:share:{energy_type}"].values / 100)
                    for energy_type in ENERGY_TYPES
                )

        final_dict = {
            key: np.array(values) if isinstance(values, list) else values
            for key, values in temp_dict.items()
        }

        final_df = pd.DataFrame(final_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

    def _compute_aircraft_performance_contributions(self):
        """Compute each aircraft's individual contribution to all fleet performance metrics.

        For each new aircraft and the old reference aircraft, computes how much its
        presence shifts the fleet mean metric relative to the recent reference baseline:

            contribution(t) = aircraft_share(t) / 100 * (metric_recent_ref - metric_aircraft)

        Positive contribution = aircraft is better than recent reference (pulls metric down
        for energy/emissions/DOC).  Negative = worse (old reference aircraft).

        The identity holds for every metric m:
            fleet_mean_m(t) = m_recent_ref - sum_i(contribution_i(t))

        Stored columns (prefix = ``{category}:{subcategory}:{aircraft}``):

        * ``...:energy_efficiency_contribution``  [MJ/ASK]
        * ``...:doc_contribution``                [€/ASK]
        * ``...:nox_contribution``                [kg/ASK]
        * ``...:soot_contribution``               [kg/ASK]
        """
        temp_dict = {}

        # Per metric: (column suffix, attribute on ReferenceAircraftParameters
        # — same name used as the ``metric`` argument to Aircraft.resolved).
        metric_specs = [
            ("energy_efficiency_contribution", "energy_per_ask"),
            ("doc_contribution", "doc_non_energy_base"),
            ("nox_contribution", "emission_index_nox"),
            ("soot_contribution", "emission_index_soot"),
        ]

        for category in self.fleet.categories.values():
            first_subcategory = category.subcategories[0]
            ref_recent = first_subcategory.recent_reference_aircraft
            ref_old = first_subcategory.old_reference_aircraft

            prefix = f"{category.name}:{first_subcategory.name}"
            old_ref_share = self.df[f"{prefix}:old_reference:aircraft_share"].values

            for col_suffix, ref_attr in metric_specs:
                val_recent = float(getattr(ref_recent, ref_attr))
                val_old = float(getattr(ref_old, ref_attr))
                # Old reference: negative contribution (less efficient than recent ref)
                temp_dict[f"{prefix}:old_reference:{col_suffix}"] = (
                    old_ref_share / 100 * (val_recent - val_old)
                )
                # Recent reference: zero by definition
                temp_dict[f"{prefix}:recent_reference:{col_suffix}"] = np.zeros_like(old_ref_share)

            for subcategory in category.subcategories.values():
                subcat_key = f"{category.name}:{subcategory.name}"
                for aircraft in self._sorted_aircraft(subcategory):
                    aircraft_share = self.df[f"{subcat_key}:{aircraft.name}:aircraft_share"].values
                    for col_suffix, ref_attr in metric_specs:
                        val_recent = float(getattr(ref_recent, ref_attr))
                        aircraft_val = aircraft.resolved(ref_attr, ref_recent)
                        temp_dict[f"{subcat_key}:{aircraft.name}:{col_suffix}"] = (
                            aircraft_share / 100 * (val_recent - aircraft_val)
                        )

        final_df = pd.DataFrame(temp_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

    def _compute_fleet_renewal_performance(self):
        """Compute counterfactual fleet performance with fleet renewal only (no new aircraft).

        For each category and performance metric, computes what the fleet mean would be
        if no new aircraft ever entered service — only the gradual replacement of old
        reference aircraft by the recent reference aircraft (fleet renewal):

            metric_renewal(t) = metric_old * old_share(t)/100
                               + metric_recent * (1 - old_share(t)/100)

        This provides a baseline to isolate the additional gain from new technology
        beyond pure fleet renewal.

        Stored columns (one per category):

        * ``{category}:energy_renewal_only``   [MJ/ASK]
        * ``{category}:doc_renewal_only``      [€/ASK]
        * ``{category}:nox_renewal_only``      [kg/ASK]
        * ``{category}:soot_renewal_only``     [kg/ASK]
        """
        temp_dict = {}

        for category in self.fleet.categories.values():
            first_subcategory = category.subcategories[0]
            ref_recent = first_subcategory.recent_reference_aircraft
            ref_old = first_subcategory.old_reference_aircraft

            prefix = f"{category.name}:{first_subcategory.name}"
            old_share = self.df[f"{prefix}:old_reference:aircraft_share"].values  # 0–100

            metrics = {
                "energy_renewal_only": (
                    float(ref_old.energy_per_ask),
                    float(ref_recent.energy_per_ask),
                ),
                "doc_renewal_only": (
                    float(ref_old.doc_non_energy_base),
                    float(ref_recent.doc_non_energy_base),
                ),
                "nox_renewal_only": (
                    float(ref_old.emission_index_nox),
                    float(ref_recent.emission_index_nox),
                ),
                "soot_renewal_only": (
                    float(ref_old.emission_index_soot),
                    float(ref_recent.emission_index_soot),
                ),
            }

            for col_suffix, (val_old, val_recent) in metrics.items():
                temp_dict[f"{category.name}:{col_suffix}"] = (
                    val_old * old_share / 100 + val_recent * (1 - old_share / 100)
                )

        final_df = pd.DataFrame(temp_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

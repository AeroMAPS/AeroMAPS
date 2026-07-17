"""
fleet_assignment
================

Aircraft market share assignment via S-shaped (logistic) penetration curves.

This module provides ``FleetAssignmentMixin``, a mixin class intended to be
composed into ``FleetModel``.  It encapsulates the two-step share computation:

1. **Single-aircraft share** (``_compute_single_aircraft_share``) — cumulative
   S-curve penetration for each aircraft.  The curve represents *"share of the
   fleet using this aircraft type or any newer one"*.
2. **Individual aircraft share** (``_compute_aircraft_share``) — actual market
   share per aircraft, derived by differencing consecutive cumulative curves.

Supporting helpers:

* ``_compute`` — logistic S-curve primitive.
* ``_sorted_aircraft`` — sorts subcategory aircraft by EIS year so results are
  independent of YAML listing order.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aeromaps.models.base import aeromaps_interpolation_function


class FleetAssignmentMixin:
    """Mixin providing aircraft market share computation for FleetModel.

    All methods access fleet data and the model DataFrame through ``self``,
    which is expected to be a ``FleetModel`` instance.
    """

    @staticmethod
    def _sorted_aircraft(subcategory):
        """Return aircraft in a subcategory sorted by entry_into_service_year (oldest first).

        This ensures share computations are order-independent with respect to
        how aircraft are listed in the YAML configuration.
        """
        return sorted(
            subcategory.aircraft.values(),
            key=lambda a: float(a.parameters.entry_into_service_year),
        )

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
            # category.market_id links this category to its entry in markets.yaml
            # (e.g. "short_range").  Column names still use category.name (display
            # string) — the id→name rename is Phase 4 scope.
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

                for aircraft in self._sorted_aircraft(subcategory):
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
                for i, aircraft in enumerate(self._sorted_aircraft(subcategory)):
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

                for aircraft in self._sorted_aircraft(subcategory):
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
                        for i, aircraft in enumerate(self._sorted_aircraft(subcategory)):
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

                        for aircraft in self._sorted_aircraft(subcategory):
                            single_aircraft_share = oldest_single_aircraft_share + self._compute(
                                float(category.parameters.life),
                                float(aircraft.parameters.entry_into_service_year),
                                100 - oldest_single_aircraft_share,
                            )
                            temp_dict[
                                f"{category.name}:{subcategory.name}:{aircraft.name}:single_aircraft_share"
                            ] = single_aircraft_share

                    else:
                        for i, aircraft in enumerate(self._sorted_aircraft(subcategory)):
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

    def _share_series(self, params, *, required_for):
        """Interpolate a user-provided ``share`` series onto the model year index [%].

        ``params.share`` is an ``AeroMapsCustomDataType`` (years/values). It is
        interpolated with the shared ``aeromaps_interpolation_function`` (honouring
        its declared ``method`` and ``positive_constraint``, with the last value
        held constant beyond the final reference year), exactly like every other
        custom data type in AeroMAPS. The series spans
        ``prospection_start_year..end_year``; historical years (and any gap before
        the first reference year) are back-filled with the first prospective value
        — the left-clamp the previous ``np.interp`` produced — which preserves the
        per-category sum-to-100%% invariant. Raises if absent — in share-decoupling
        mode every aircraft must carry its own share.
        """
        cdt = getattr(params, "share", None)
        if cdt is None:
            raise ValueError(f"Share-decoupling mode: missing `share` series for {required_for}.")
        series = aeromaps_interpolation_function(
            self,
            reference_years=cdt.years,
            reference_years_values=cdt.values,
            method=cdt.method,
            positive_constraint=cdt.positive_constraint,
            model_name=f"share[{required_for}]",
        )
        return series.reindex(self.df.index).bfill().values

    def _compute_decoupled_aircraft_share(self):
        """Populate ``aircraft_share`` columns directly from user share series.

        Share-decoupling mode: bypasses the S-curve. Each aircraft/reference card
        carries a per-year ``share`` series; this writes the same
        ``{category}:{subcategory}:{aircraft|old_reference|recent_reference}:aircraft_share``
        columns that ``_compute_aircraft_share`` would, so every downstream
        performance step is unchanged. Reference aircraft are read from the first
        subcategory (matching ``_compute_*`` consumers). Shares are expected to
        sum to ~100% per category per year (enforced by the data generator).
        """
        temp_dict = {}
        for category in self.fleet.categories.values():
            first_subcategory = category.subcategories[0]
            ref_prefix = f"{category.name}:{first_subcategory.name}"
            temp_dict[f"{ref_prefix}:old_reference:aircraft_share"] = self._share_series(
                first_subcategory.old_reference_aircraft,
                required_for=f"{ref_prefix}:old_reference",
            )
            temp_dict[f"{ref_prefix}:recent_reference:aircraft_share"] = self._share_series(
                first_subcategory.recent_reference_aircraft,
                required_for=f"{ref_prefix}:recent_reference",
            )
            for subcategory in category.subcategories.values():
                subcat_key = f"{category.name}:{subcategory.name}"
                for aircraft in subcategory.aircraft.values():
                    temp_dict[f"{subcat_key}:{aircraft.name}:aircraft_share"] = self._share_series(
                        aircraft.parameters,
                        required_for=f"{subcat_key}:{aircraft.name}",
                    )

        final_df = pd.DataFrame(temp_dict, index=self.df.index)
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
            # category.market_id links this category to its entry in markets.yaml
            # (e.g. "short_range").  Column names still use category.name (display
            # string) — the id→name rename is Phase 4 scope.
            for key, subcategory in reversed(category.subcategories.items()):
                sorted_ac = self._sorted_aircraft(subcategory)
                n = len(sorted_ac)
                for j, aircraft in enumerate(reversed(sorted_ac)):
                    i = n - 1 - j  # 0 = oldest, n-1 = newest in sorted order
                    subcategory_key = f"{category.name}:{subcategory.name}:{aircraft.name}"

                    if (i == n - 1) and (key == list(category.subcategories.keys())[-1]):
                        aircraft_share = self.df[f"{subcategory_key}:single_aircraft_share"].values
                    elif (i == n - 1) and (key != list(category.subcategories.keys())[-1]):
                        next_subcategory = category.subcategories[key + 1]
                        next_oldest = self._sorted_aircraft(next_subcategory)[0]
                        single_aircraft_share = self.df[
                            f"{subcategory_key}:single_aircraft_share"
                        ].values
                        single_aircraft_share_n1 = self.df[
                            f"{category.name}:{next_subcategory.name}:{next_oldest.name}:single_aircraft_share"
                        ].values
                        aircraft_share = single_aircraft_share - single_aircraft_share_n1
                    else:
                        single_aircraft_share = self.df[
                            f"{subcategory_key}:single_aircraft_share"
                        ].values
                        single_aircraft_share_n1 = self.df[
                            f"{category.name}:{subcategory.name}:{sorted_ac[i + 1].name}:single_aircraft_share"
                        ].values
                        aircraft_share = single_aircraft_share - single_aircraft_share_n1

                    temp_dict[f"{subcategory_key}:aircraft_share"] = aircraft_share

            first_subcategory = category.subcategories[0]
            ref_recent_single_aircraft_share = self.df[
                f"{category.name}:{first_subcategory.name}:recent_reference:single_aircraft_share"
            ].values

            if first_subcategory.aircraft:
                first_subcat_oldest = self._sorted_aircraft(first_subcategory)[0]
                next_aircraft_single_share = self.df[
                    f"{category.name}:{first_subcategory.name}:{first_subcat_oldest.name}:single_aircraft_share"
                ].values
            else:
                next_aircraft_single_share = np.zeros_like(ref_recent_single_aircraft_share)

            ref_recent_aircraft_share = (
                ref_recent_single_aircraft_share - next_aircraft_single_share
            )
            temp_dict[
                f"{category.name}:{first_subcategory.name}:recent_reference:aircraft_share"
            ] = ref_recent_aircraft_share

            ref_old_aircraft_share = 100 - ref_recent_single_aircraft_share
            temp_dict[f"{category.name}:{first_subcategory.name}:old_reference:aircraft_share"] = (
                ref_old_aircraft_share
            )

        final_dict = {
            key: np.array(values) if isinstance(values, list) else values
            for key, values in temp_dict.items()
        }

        final_df = pd.DataFrame(final_dict, index=self.df.index)
        self.df = pd.concat([self.df, final_df], axis=1)

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

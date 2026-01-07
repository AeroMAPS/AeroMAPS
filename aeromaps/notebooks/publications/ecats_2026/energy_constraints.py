from typing import Tuple
import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class BlendCompletenessConstraint(AeroMAPSModel):
    def __init__(self, name="blend_completeness_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        generic_biofuel_mandate_share: pd.Series,
        electrofuel_mandate_share: pd.Series,
        blend_completeness_constraint_enforcement_years: list,
    ) -> list:
        """
        Compute constraint ensuring saf share is not above 100%.
        Normalised around zero: positive when above  100.
        """

        # Reference for normalisation: max absolute positive value
        total_share = generic_biofuel_mandate_share + electrofuel_mandate_share

        violation_normalised = (total_share - 100) / 100

        # Compute constraint: positive when consumption < 0
        blend_completeness_constraint = [
            violation_normalised.loc[year]
            for year in blend_completeness_constraint_enforcement_years
            if year in total_share.index
        ]

        return blend_completeness_constraint


class BiomassAvailabilityConstraintTrajectory(AeroMAPSModel):
    def __init__(self, name="biomass_availability_constraint_trajectory", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        generic_biomass_availability_constraint_enforcement_years: list,
        generic_biomass_consumed_aviation_allocated_share: pd.Series,
    ) -> Tuple[list, pd.Series]:
        """
        Compute biomass availability constraint violations.

        Parameters
        ----------
        generic_biomass_availability_constraint_enforcement_years : list
            Years in which the constraint should be enforced.
        generic_biomass_consumed_aviation_allocated_share : pd.Series
            Share (%) of available biomass consumed by aviation.

        Returns
        -------
        biomass_trajectory_constraint : list
            Normalised constraint violations (positive if >100%).
        violation_viz : pd.Series
            Time series (in %) for visualisation.
        """

        # Normalised violation: positive when allocation > 100%
        violation_normalised = (generic_biomass_consumed_aviation_allocated_share - 100) / 100

        # Values of the constraint at enforcement years
        biomass_trajectory_constraint = [
            violation_normalised.loc[year]
            for year in generic_biomass_availability_constraint_enforcement_years
            if year in violation_normalised.index
        ]

        # For visualisation: keep the raw share (%)
        biomass_violation_viz = generic_biomass_consumed_aviation_allocated_share.copy()
        self.df.loc[:, "biomass_availability_violation_viz"] = biomass_violation_viz

        return biomass_trajectory_constraint, biomass_violation_viz


class ElectricityAvailabilityConstraintTrajectory(AeroMAPSModel):
    def __init__(self, name="electricity_availability_constraint_trajectory", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        generic_electricity_constraint_enforcement_years: list,
        generic_electricity_consumed_aviation_allocated_share: pd.Series,
    ) -> Tuple[list, pd.Series]:
        """
        Compute generic electricity availability constraint violations.

        Parameters
        ----------
        generic_electricity_constraint_enforcement_years : list
            Years in which the constraint should be enforced.
        generic_electricity_consumed_aviation_allocated_share : pd.Series
            Share (%) of available generic electricity consumed by aviation.

        Returns
        -------
        generic_electricity_trajectory_constraint : list
            Normalised constraint violations (positive if >100%).
        violation_viz : pd.Series
            Time series (in %) for visualisation.
        """

        # Normalised violation: positive when allocation > 100%
        violation_normalised = (generic_electricity_consumed_aviation_allocated_share - 100) / 100

        # Values of the constraint at enforcement years
        generic_electricity_trajectory_constraint = [
            violation_normalised.loc[year]
            for year in generic_electricity_constraint_enforcement_years
            if year in violation_normalised.index
        ]

        # For visualisation: keep the raw share (%)
        electricity_violation_viz = generic_electricity_consumed_aviation_allocated_share.copy()
        self.df.loc[:, "generic_electricity_availability_violation_viz"] = electricity_violation_viz

        return generic_electricity_trajectory_constraint, electricity_violation_viz


class BiofuelUseGrowthConstraint(AeroMAPSModel):
    def __init__(self, name="biofuel_use_growth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        rate_ramp_up_constraint_biofuel: float,
        generic_biofuel_energy_consumption: pd.Series,
        volume_ramp_up_constraint_biofuel: float,
        biofuel_use_growth_constraint_enforcement_years: list,
    ) -> list:
        eps = 1e6  # Small value to avoid division by zero
        biofuel_use_growth_constraint = [
            (
                generic_biofuel_energy_consumption.loc[i]
                - max(
                    volume_ramp_up_constraint_biofuel * 5 * 1e12,
                    generic_biofuel_energy_consumption.loc[i - 5]
                    * (1 + rate_ramp_up_constraint_biofuel) ** 5,
                )
            )
            / (generic_biofuel_energy_consumption.loc[i] + eps)
            for i in biofuel_use_growth_constraint_enforcement_years
        ]

        return biofuel_use_growth_constraint

    # def compute(
    #     self,
    #     energy_consumption_biofuel: pd.Series,
    #     volume_ramp_up_constraint_biofuel: float,
    #     rate_ramp_up_constraint_biofuel: float,
    # ) -> Tuple[float, float, pd.Series, pd.Series]:
    #    # Complex version of the constraint, not used anymore but kept for reference
    #
    #     annual_biofuel_growth = energy_consumption_biofuel.diff().loc[2027 : self.end_year]
    #     annual_biofuel_growth_constraint = annual_biofuel_growth.copy()
    #
    #     ### Max ramp up constraint for visualisation. Do no maistake with actual rampup constraint !!!
    #     # All constraints with "VIZ" are for visualisation only !!!
    #     annual_biofuel_growth_constraint_viz = annual_biofuel_growth.copy()
    #
    #     biofuel_growth_constraint_theoretical_max_viz = pd.Series(
    #         index=range(self.prospection_start_year, self.end_year + 1), dtype=float
    #     )
    #     biofuel_growth_constraint_theoretical_max_viz.loc[2025] = energy_consumption_biofuel.loc[
    #         2025
    #     ]
    #
    #
    #
    #     for t in range(2026 + 1, self.end_year + 1):
    #         biofuel_growth_constraint_theoretical_max_viz.loc[t] = (
    #             biofuel_growth_constraint_theoretical_max_viz.loc[t - 1]
    #             + max(
    #                 volume_ramp_up_constraint_biofuel * 1e12,
    #                 rate_ramp_up_constraint_biofuel
    #                 * biofuel_growth_constraint_theoretical_max_viz.loc[t - 1],
    #             )
    #         )
    #
    #         # Real constraint definition
    #         year_rate_constraint = (
    #             rate_ramp_up_constraint_biofuel * energy_consumption_biofuel.loc[t - 1]
    #         )
    #         year_constraint = max(volume_ramp_up_constraint_biofuel * 1e12, year_rate_constraint)
    #
    #         annual_biofuel_growth_constraint_viz.loc[t] = (
    #             energy_consumption_biofuel.loc[t - 1] + year_constraint
    #         )
    #         annual_biofuel_growth_constraint.loc[t] = (
    #             annual_biofuel_growth_constraint.loc[t] - year_constraint
    #         ) / abs(np.mean((annual_biofuel_growth)))
    #
    #     biofuel_use_growth_constraint = max(annual_biofuel_growth_constraint)
    #     biofuel_use_no_degrowth_constraint = -min(annual_biofuel_growth) / abs(
    #         np.mean(annual_biofuel_growth)
    #     )
    #
    #     self.df.loc[:, "annual_biofuel_growth_constraint_viz"] = (
    #         annual_biofuel_growth_constraint_viz
    #     )
    #     self.df.loc[:, "biofuel_growth_constraint_theoretical_max_viz"] = (
    #         biofuel_growth_constraint_theoretical_max_viz
    #     )
    #     self.float_outputs["biofuel_use_growth_constraint"] = biofuel_use_growth_constraint
    #     self.float_outputs["biofuel_use_no_degrowth_constraint"] = (
    #         biofuel_use_no_degrowth_constraint
    #     )
    #     return (
    #         biofuel_use_growth_constraint,
    #         biofuel_use_no_degrowth_constraint,
    #         annual_biofuel_growth_constraint,
    #         annual_biofuel_growth,
    #     )


class ElectrofuelUseGrowthConstraint(AeroMAPSModel):
    def __init__(self, name="electrofuel_use_growth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        rate_ramp_up_constraint_electrofuel: float,
        electrofuel_energy_consumption: pd.Series,
        volume_ramp_up_constraint_electrofuel: float,
        electrofuel_use_growth_constraint_enforcement_years: list,
    ) -> list:
        eps = 1e6  # Small value to avoid division by zero
        electrofuel_use_growth_constraint = [
            (
                electrofuel_energy_consumption.loc[i]
                - max(
                    volume_ramp_up_constraint_electrofuel * 5 * 1e12,
                    electrofuel_energy_consumption.loc[i - 5]
                    * (1 + rate_ramp_up_constraint_electrofuel) ** 5,
                )
            )
            / (electrofuel_energy_consumption.loc[i] + eps)
            for i in electrofuel_use_growth_constraint_enforcement_years
        ]

        return electrofuel_use_growth_constraint

    # def compute(
    #     self,
    #     energy_consumption_electrofuel: pd.Series,
    #     volume_ramp_up_constraint_electrofuel: float,
    #     rate_ramp_up_constraint_electrofuel: float,
    # ) -> Tuple[float, float, pd.Series, pd.Series]:
    #    # Complex version of the constraint, not used anymore but kept for reference
    #     annual_electrofuel_growth = energy_consumption_electrofuel.diff().loc[2031 : self.end_year]
    #
    #     annual_electrofuel_growth_constraint = annual_electrofuel_growth.copy()
    #     ### Max ramp up constraint for visualisation. Do no maistake with actual rampup constraint !!!
    #     # All constraints with "VIZ" are for visualisation only !!!
    #     annual_electrofuel_growth_constraint_viz = annual_electrofuel_growth.copy()
    #
    #     electrofuel_growth_constraint_theoretical_max_viz = pd.Series(
    #         index=range(self.prospection_start_year, self.end_year + 1), dtype=float
    #     )
    #     electrofuel_growth_constraint_theoretical_max_viz.loc[2025] = (
    #         energy_consumption_electrofuel.loc[2025]
    #     )
    #
    #     for t in range(2030 + 1, self.end_year + 1):
    #         electrofuel_growth_constraint_theoretical_max_viz.loc[t] = (
    #             electrofuel_growth_constraint_theoretical_max_viz.loc[t - 1]
    #             + max(
    #                 volume_ramp_up_constraint_electrofuel * 1e12,
    #                 rate_ramp_up_constraint_electrofuel
    #                 * electrofuel_growth_constraint_theoretical_max_viz.loc[t - 1],
    #             )
    #         )
    #
    #         # Real constraint definition
    #         year_rate_constraint = (
    #             rate_ramp_up_constraint_electrofuel * energy_consumption_electrofuel.loc[t - 1]
    #         )
    #         year_constraint = max(
    #             volume_ramp_up_constraint_electrofuel * 1e12, year_rate_constraint
    #         )
    #
    #         annual_electrofuel_growth_constraint_viz.loc[t] = (
    #             energy_consumption_electrofuel.loc[t - 1] + year_constraint
    #         )
    #         annual_electrofuel_growth_constraint.loc[t] = (
    #             annual_electrofuel_growth_constraint.loc[t] - year_constraint
    #         ) / abs(np.mean((annual_electrofuel_growth)))
    #
    #     electrofuel_use_growth_constraint = max(annual_electrofuel_growth_constraint)
    #     electrofuel_use_no_degrowth_constraint = -min(annual_electrofuel_growth) / abs(
    #         np.mean(annual_electrofuel_growth)
    #     )
    #
    #     self.df.loc[:, "annual_electrofuel_growth_constraint_viz"] = (
    #         annual_electrofuel_growth_constraint_viz
    #     )
    #     self.df.loc[:, "electrofuel_growth_constraint_theoretical_max_viz"] = (
    #         electrofuel_growth_constraint_theoretical_max_viz
    #     )
    #     self.float_outputs["electrofuel_use_growth_constraint"] = electrofuel_use_growth_constraint
    #     self.float_outputs["electrofuel_use_no_degrowth_constraint"] = (
    #         electrofuel_use_no_degrowth_constraint
    #     )
    #     return (
    #         electrofuel_use_growth_constraint,
    #         electrofuel_use_no_degrowth_constraint,
    #         annual_electrofuel_growth_constraint,
    #         annual_electrofuel_growth,
    #     )

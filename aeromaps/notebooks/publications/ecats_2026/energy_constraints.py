from typing import Tuple
import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class BlendCompletenessConstraint(AeroMAPSModel):
    def __init__(self, name="blend_completeness_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        saf_ftg_mandate_share: pd.Series,
        saf_co2_mandate_share: pd.Series,
        blend_completeness_constraint_enforcement_years: list,
    ) -> list:
        """
        Compute constraint ensuring saf share is not above 100%.
        Normalised around zero: positive when above  100.
        """

        # Reference for normalisation: max absolute positive value
        total_share = saf_ftg_mandate_share + saf_co2_mandate_share

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
    def __init__(self, name="saf_ftg_use_growth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        rate_ramp_up_constraint_saf_ftg: float,
        saf_ftg_energy_consumption: pd.Series,
        volume_ramp_up_constraint_saf_ftg: float,
        saf_ftg_use_growth_constraint_enforcement_years: list,
    ) -> list:
        eps = 1e6  # Small value to avoid division by zero
        saf_ftg_use_growth_constraint = [
            (
                saf_ftg_energy_consumption.loc[i]
                - max(
                    volume_ramp_up_constraint_saf_ftg * 5 * 1e12,
                    saf_ftg_energy_consumption.loc[i - 5]
                    * (1 + rate_ramp_up_constraint_saf_ftg) ** 5,
                )
            )
            / (saf_ftg_energy_consumption.loc[i] + eps)
            for i in saf_ftg_use_growth_constraint_enforcement_years
        ]

        return saf_ftg_use_growth_constraint


class ElectrofuelUseGrowthConstraint(AeroMAPSModel):
    def __init__(self, name="saf_co2_use_growth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        rate_ramp_up_constraint_saf_co2: float,
        saf_co2_energy_consumption: pd.Series,
        volume_ramp_up_constraint_saf_co2: float,
        saf_co2_use_growth_constraint_enforcement_years: list,
    ) -> list:
        eps = 1e6  # Small value to avoid division by zero
        saf_co2_use_growth_constraint = [
            (
                saf_co2_energy_consumption.loc[i]
                - max(
                    volume_ramp_up_constraint_saf_co2 * 5 * 1e12,
                    saf_co2_energy_consumption.loc[i - 5]
                    * (1 + rate_ramp_up_constraint_saf_co2) ** 5,
                )
            )
            / (saf_co2_energy_consumption.loc[i] + eps)
            for i in saf_co2_use_growth_constraint_enforcement_years
        ]

        return saf_co2_use_growth_constraint

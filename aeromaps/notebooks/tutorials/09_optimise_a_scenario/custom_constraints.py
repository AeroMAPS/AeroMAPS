from aeromaps.models.base import AeroMAPSModel
import pandas as pd
from typing import Tuple


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


class GridElectricityAvailabilityConstraintTrajectory(AeroMAPSModel):
    def __init__(self, name="grid_electricity_availability_constraint_trajectory", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        grid_electricity_constraint_enforcement_years: list,
        grid_electricity_consumed_aviation_allocated_share: pd.Series,
    ) -> Tuple[list, pd.Series]:
        """
        Compute grid electricity availability constraint violations.

        Parameters
        ----------
        grid_electricity_constraint_enforcement_years : list
            Years in which the constraint should be enforced.
        grid_electricity_consumed_aviation_allocated_share : pd.Series
            Share (%) of available grid electricity consumed by aviation.

        Returns
        -------
        grid_electricity_trajectory_constraint : list
            Normalised constraint violations (positive if >100%).
        violation_viz : pd.Series
            Time series (in %) for visualisation.
        """

        # Normalised violation: positive when allocation > 100%
        violation_normalised = (grid_electricity_consumed_aviation_allocated_share - 100) / 100

        # Values of the constraint at enforcement years
        grid_electricity_trajectory_constraint = [
            violation_normalised.loc[year]
            for year in grid_electricity_constraint_enforcement_years
            if year in violation_normalised.index
        ]

        # For visualisation: keep the raw share (%)
        electricity_violation_viz = grid_electricity_consumed_aviation_allocated_share.copy()
        self.df.loc[:, "grid_electricity_availability_violation_viz"] = electricity_violation_viz

        return grid_electricity_trajectory_constraint, electricity_violation_viz

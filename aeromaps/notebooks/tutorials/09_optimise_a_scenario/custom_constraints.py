from aeromaps.models.base import AeroMAPSModel
from aeromaps.models.jax_helpers import year_pos
import jax.numpy as jnp
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

    jax_static_input_names = {"blend_completeness_constraint_enforcement_years"}

    def jax_compute(
        self,
        generic_biofuel_mandate_share,
        electrofuel_mandate_share,
        blend_completeness_constraint_enforcement_years,
    ):
        """JAX version of :meth:`compute` (same signature, pure jax.numpy)."""
        total_share = jnp.asarray(generic_biofuel_mandate_share) + jnp.asarray(
            electrofuel_mandate_share
        )
        violation_normalised = (total_share - 100.0) / 100.0
        positions = [
            year_pos(self, year)
            for year in blend_completeness_constraint_enforcement_years
            if self.historic_start_year <= year <= self.end_year
        ]
        blend_completeness_constraint = violation_normalised[jnp.array(positions, dtype=int)]
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

    jax_static_input_names = {"generic_biomass_availability_constraint_enforcement_years"}
    # ``compute`` files the viz series under another column name.
    jax_df_output_names = {"biomass_violation_viz": "biomass_availability_violation_viz"}

    def jax_compute(
        self,
        generic_biomass_availability_constraint_enforcement_years,
        generic_biomass_consumed_aviation_allocated_share,
    ):
        """JAX version of :meth:`compute` (same signature, pure jax.numpy)."""
        share = jnp.asarray(generic_biomass_consumed_aviation_allocated_share)
        violation_normalised = (share - 100.0) / 100.0
        positions = [
            year_pos(self, year)
            for year in generic_biomass_availability_constraint_enforcement_years
            if self.historic_start_year <= year <= self.end_year
        ]
        biomass_trajectory_constraint = violation_normalised[jnp.array(positions, dtype=int)]
        biomass_violation_viz = share
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

    jax_static_input_names = {"grid_electricity_constraint_enforcement_years"}
    # ``compute`` files the viz series under another column name.
    jax_df_output_names = {
        "electricity_violation_viz": "grid_electricity_availability_violation_viz"
    }

    def jax_compute(
        self,
        grid_electricity_constraint_enforcement_years,
        grid_electricity_consumed_aviation_allocated_share,
    ):
        """JAX version of :meth:`compute` (same signature, pure jax.numpy)."""
        share = jnp.asarray(grid_electricity_consumed_aviation_allocated_share)
        violation_normalised = (share - 100.0) / 100.0
        positions = [
            year_pos(self, year)
            for year in grid_electricity_constraint_enforcement_years
            if self.historic_start_year <= year <= self.end_year
        ]
        grid_electricity_trajectory_constraint = violation_normalised[
            jnp.array(positions, dtype=int)
        ]
        electricity_violation_viz = share
        return grid_electricity_trajectory_constraint, electricity_violation_viz

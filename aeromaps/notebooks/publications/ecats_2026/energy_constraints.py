from typing import Tuple
import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class ReducedMandate(AeroMAPSModel):
    """
    Model that expands short optimization vectors to full mandate share vectors.

    The optimization controls only the last 5 values of the mandate share vectors.
    This model prepends the 2 fixed leading values to create the full 7-element vectors
    expected by downstream AeroMAPS models.
    """

    def __init__(self, name="reduced_mandate", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        saf_ftg_mandate_share_values_optim: list,
        saf_co2_mandate_share_values_optim: list,
        saf_ftg_mandate_share_values_fixed: list,
        saf_co2_mandate_share_values_fixed: list,
    ) -> Tuple[list, list]:
        """
        Expand short optimization vectors with fixed leading values.

        Parameters
        ----------
        saf_ftg_mandate_share_values_optim : list
            Last 5 biofuel mandate share values (optimization variables).
        saf_co2_mandate_share_values_optim : list
            Last 5 electrofuel mandate share values (optimization variables).
        saf_ftg_mandate_share_values_fixed : list
            First 2 fixed biofuel mandate share values (not optimized).
        saf_co2_mandate_share_values_fixed : list
            First 2 fixed electrofuel mandate share values (not optimized).

        Returns
        -------
        saf_ftg_mandate_share_values : list
            Full 7-element biofuel mandate share vector.
        saf_co2_mandate_share_values : list
            Full 7-element electrofuel mandate share vector.
        """

        # Combine fixed and optimized values
        saf_ftg_mandate_share_values = (
            saf_ftg_mandate_share_values_fixed + saf_ftg_mandate_share_values_optim
        )
        saf_co2_mandate_share_values = (
            saf_co2_mandate_share_values_fixed + saf_co2_mandate_share_values_optim
        )

        return saf_ftg_mandate_share_values, saf_co2_mandate_share_values


class OptimizationObjectives(AeroMAPSModel):
    """
    This class computes optimization objectives: cumulative CO2 at end year
    and temperature impacts.

    Parameters
    ----------
    name : str
        Name of the model instance ('optimization_objectives' by default).
    """

    def __init__(self, name="optimization_objectives", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        cumulative_co2_emissions: pd.Series,
        temperature_increase_from_aviation: pd.Series,
    ) -> Tuple[float, float, float]:
        """
        Extract cumulative CO2 at end year and temperature impacts.

        Parameters
        ----------
        cumulative_co2_emissions : pd.Series
            Cumulative CO2 emissions from aviation over time [GtCO2].
        temperature_increase_from_aviation : pd.Series
            Temperature increase from aviation over time [°C].

        Returns
        -------
        cumulative_co2_end_year : float
            Cumulative CO2 emissions at end year [GtCO2].
        temperature_increase_end_year : float
            Temperature increase from aviation at end year [°C].
        mean_temperature_increase_from_aviation_2025_end_year : float
            Mean temperature increase from aviation over 2025_end_year [°C].
        """

        # Cumulative CO2 at end year
        cumulative_co2_end_year = cumulative_co2_emissions.loc[self.end_year]

        # Temperature increase at end year
        temperature_increase_end_year = temperature_increase_from_aviation.loc[self.end_year]

        # Mean temperature increase over 2025-2050
        mean_temperature_increase_from_aviation_2025_end = temperature_increase_from_aviation.loc[
            2025 : self.end_year
        ].mean()

        return (
            cumulative_co2_end_year,
            temperature_increase_end_year,
            mean_temperature_increase_from_aviation_2025_end,
        )


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

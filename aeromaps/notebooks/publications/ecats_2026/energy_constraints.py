from typing import Tuple
import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class ReducedMandate(AeroMAPSModel):
    """
    Model that expands short optimization vectors to full mandate share vectors.

    The optimization controls the tail of each mandate vector; fixed leading values
    are prepended to reconstruct the full vectors consumed by downstream models.
    """

    def __init__(self, name="reduced_mandate", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        saf_ftg_mandate_share_values_optim: list,
        saf_co2_fraction_optim: list,
        lcaf_fraction_optim: list,
        saf_ftg_mandate_share_values_fixed: list,
        saf_co2_mandate_share_values_fixed: list,
        lcaf_mandate_share_values_fixed: list,
    ) -> Tuple[list, list, list]:
        """
        Expand short optimization vectors with fixed leading values using cascading fractions.

        This implements a cascade parameterization where the second and third fuels are defined
        as fractions of the remaining blend capacity, ensuring the total always equals 100%.

        Parameters
        ----------
        saf_ftg_mandate_share_values_optim : list
            Biofuel mandate share values (absolute, 0-100) for optimization years.
        saf_co2_fraction_optim : list
            Electrofuel fraction of remaining blend (0-1) for optimization years.
        lcaf_fraction_optim : list
            LCAF fraction of remaining blend after electrofuel (0-1) for optimization years.
        saf_ftg_mandate_share_values_fixed : list
            First fixed biofuel mandate share values (not optimized).
        saf_co2_mandate_share_values_fixed : list
            First fixed electrofuel mandate share values (not optimized).
        lcaf_mandate_share_values_fixed : list
            First fixed LCAF mandate share values (not optimized).

        Returns
        -------
        saf_ftg_mandate_share_values : list
            Full biofuel mandate share vector.
        saf_co2_mandate_share_values : list
            Full electrofuel mandate share vector.
        lcaf_mandate_share_values : list
            Full LCAF mandate share vector.
        """

        # Initialize with fixed values
        saf_ftg_mandate_share_values = list(saf_ftg_mandate_share_values_fixed)
        saf_co2_mandate_share_values = list(saf_co2_mandate_share_values_fixed)
        lcaf_mandate_share_values = list(lcaf_mandate_share_values_fixed)

        # Apply cascade parameterization for optimization years
        # saf_ftg_share = X1 (absolute)
        # saf_co2_share = Y1 * (100 - X1) (fraction of remaining)
        # lcaf_share = Y2 * (100 - X1 - saf_co2_share) (fraction of remaining after CO2)
        # kerosene_share = 100 - X1 - saf_co2_share - lcaf_share (implicit)

        for i, x1 in enumerate(saf_ftg_mandate_share_values_optim):
            y1 = saf_co2_fraction_optim[i]
            y2 = lcaf_fraction_optim[i]

            saf_ftg_mandate_share_values.append(x1)

            remaining_after_ftg = 100 - x1
            saf_co2_share = y1 * remaining_after_ftg
            saf_co2_mandate_share_values.append(saf_co2_share)

            remaining_after_co2 = remaining_after_ftg - saf_co2_share
            lcaf_share = y2 * remaining_after_co2
            lcaf_mandate_share_values.append(lcaf_share)

        # logging.info(
        #    "SAF FTG: %s, SAF CO2 fractions: %s, LCAF fractions: %s",
        #    saf_ftg_mandate_share_values,
        #    saf_co2_mandate_share_values,
        #    lcaf_mandate_share_values,
        # )

        return saf_ftg_mandate_share_values, saf_co2_mandate_share_values, lcaf_mandate_share_values


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

        cumulative_co2_end_year = cumulative_co2_emissions.loc[self.end_year]
        temperature_increase_end_year = temperature_increase_from_aviation.loc[self.end_year]
        mean_temperature_increase_from_aviation_2025_end = temperature_increase_from_aviation.loc[
            2025 : self.end_year
        ].mean()

        return (
            cumulative_co2_end_year,
            temperature_increase_end_year,
            mean_temperature_increase_from_aviation_2025_end,
        )


class LCAFUseGrowthConstraint(AeroMAPSModel):
    def __init__(self, name="lcaf_use_growth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        rate_ramp_up_constraint_lcaf: float,
        lcaf_energy_consumption: pd.Series,
        lcaf_use_growth_constraint_enforcement_years: list,
    ) -> list:
        eps = 1e-6  # Small value to avoid division by zero
        lcaf_use_growth_constraint = []

        check_years = [2030] + lcaf_use_growth_constraint_enforcement_years

        for i in lcaf_use_growth_constraint_enforcement_years:
            # Prefer a 5-year lookback when available; otherwise fall back to 10-year (e.g., 2060, 2070)
            lookback_year = i - 5 if (i - 5) in check_years else i - 10
            delta_years = i - lookback_year
            reference = lcaf_energy_consumption.loc[lookback_year]
            current = lcaf_energy_consumption.loc[i]
            growth_violation = (
                current - reference * (1 + rate_ramp_up_constraint_lcaf) ** delta_years
            ) / (current + eps)
            lcaf_use_growth_constraint.append(growth_violation)

        return lcaf_use_growth_constraint


class BlendCompletenessConstraint(AeroMAPSModel):
    def __init__(self, name="blend_completeness_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        saf_ftg_mandate_share: pd.Series,
        saf_co2_mandate_share: pd.Series,
        lcaf_mandate_share: pd.Series,
        blend_completeness_constraint_enforcement_years: list,
    ) -> list:
        """
        Compute constraint ensuring saf share is not above 100%.
        Normalised around zero: positive when above  100.
        """

        # Reference for normalisation: max absolute positive value
        total_share = saf_ftg_mandate_share + saf_co2_mandate_share + lcaf_mandate_share

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
        saf_ftg_use_growth_constraint_enforcement_years: list,
    ) -> list:
        eps = 1e-6  # Small value to avoid division by zero
        saf_ftg_use_growth_constraint = []

        check_years = [2030] + saf_ftg_use_growth_constraint_enforcement_years

        for i in saf_ftg_use_growth_constraint_enforcement_years:
            # Prefer a 5-year lookback when available; otherwise fall back to 10-year (e.g., 2060, 2070)
            lookback_year = i - 5 if (i - 5) in check_years else i - 10
            delta_years = i - lookback_year
            reference = saf_ftg_energy_consumption.loc[lookback_year]
            current = saf_ftg_energy_consumption.loc[i]
            growth_violation = (
                current - reference * (1 + rate_ramp_up_constraint_saf_ftg) ** delta_years
            ) / (current + eps)
            saf_ftg_use_growth_constraint.append(growth_violation)

        return saf_ftg_use_growth_constraint


class ElectrofuelUseGrowthConstraint(AeroMAPSModel):
    def __init__(self, name="saf_co2_use_growth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        rate_ramp_up_constraint_saf_co2: float,
        saf_co2_energy_consumption: pd.Series,
        saf_co2_use_growth_constraint_enforcement_years: list,
    ) -> list:
        eps = 1e-6  # Small value to avoid division by zero
        saf_co2_use_growth_constraint = []

        check_years = [2030] + saf_co2_use_growth_constraint_enforcement_years

        for i in saf_co2_use_growth_constraint_enforcement_years:
            # Prefer a 5-year lookback when available; otherwise fall back to 10-year (e.g., 2060, 2070)
            lookback_year = i - 5 if (i - 5) in check_years else i - 10
            delta_years = i - lookback_year
            reference = saf_co2_energy_consumption.loc[lookback_year]
            current = saf_co2_energy_consumption.loc[i]
            growth_violation = (
                current - reference * (1 + rate_ramp_up_constraint_saf_co2) ** delta_years
            ) / (current + eps)
            saf_co2_use_growth_constraint.append(growth_violation)

        return saf_co2_use_growth_constraint

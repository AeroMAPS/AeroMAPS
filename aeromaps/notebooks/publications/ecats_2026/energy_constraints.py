from typing import Tuple
import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class ReducedMandate(AeroMAPSModel):
    """
    Model that expands short optimization vectors to full mandate share vectors.

    Conventional approach: the optimization directly controls the absolute share
    (0-100) of each pathway (SAF FTG, SAF CO2, LCAF) for the targeted years.
    Fixed leading values are prepended to reconstruct the full vectors consumed
    by downstream models. The kerosene share remains implicit as 100 minus the
    sum of the pathway shares; completeness is enforced via a dedicated constraint.
    """

    def __init__(self, name="reduced_mandate", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        saf_ftg_mandate_share_values_optim: list,
        saf_co2_mandate_share_values_optim: list,
        lcaf_mandate_share_values_optim: list,
        saf_ftg_mandate_share_values_fixed: list,
        saf_co2_mandate_share_values_fixed: list,
        lcaf_mandate_share_values_fixed: list,
    ) -> Tuple[list, list, list]:
        """
        Expand short optimization vectors with fixed leading values using direct shares.

        Parameters
        ----------
        saf_ftg_mandate_share_values_optim : list
            Biofuel (FTG) mandate share values (absolute, 0-100) for optimization years.
        saf_co2_mandate_share_values_optim : list
            Electrofuel (CO2-based) mandate share values (absolute, 0-100) for optimization years.
        lcaf_mandate_share_values_optim : list
            LCAF mandate share values (absolute, 0-100) for optimization years.
        saf_ftg_mandate_share_values_fixed : list
            Fixed leading biofuel mandate share values (not optimized).
        saf_co2_mandate_share_values_fixed : list
            Fixed leading electrofuel mandate share values (not optimized).
        lcaf_mandate_share_values_fixed : list
            Fixed leading LCAF mandate share values (not optimized).

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

        # Append the directly optimized absolute shares
        saf_ftg_mandate_share_values.extend(saf_ftg_mandate_share_values_optim)
        saf_co2_mandate_share_values.extend(saf_co2_mandate_share_values_optim)
        lcaf_mandate_share_values.extend(lcaf_mandate_share_values_optim)

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
    ) -> Tuple[float, float, float, float, float, float, float, float]:
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
        temperature_increase_end_year = temperature_increase_from_aviation.loc[2070]
        temperature_increase_2050 = temperature_increase_from_aviation.loc[2050]
        temperature_increase_2060 = temperature_increase_from_aviation.loc[2060]

        mean_temperature_increase_from_aviation_2025_end = temperature_increase_from_aviation.loc[
            2025 : self.end_year
        ].mean()
        cumulative_co2_2050 = cumulative_co2_emissions.loc[2050]
        cumulative_co2_2055 = cumulative_co2_emissions.loc[2055]
        cumulative_co2_2060 = cumulative_co2_emissions.loc[2060]

        return (
            cumulative_co2_end_year,
            cumulative_co2_2050,
            cumulative_co2_2055,
            cumulative_co2_2060,
            temperature_increase_end_year,
            temperature_increase_2050,
            temperature_increase_2060,
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
        Enforce blend completeness: the sum of FTG, CO2 and LCAF shares
        must not exceed 100% at enforcement years.

        Constraint value is normalized around zero: (sum - 100) / 100.
        It is satisfied when <= 0 and violated when > 0.
        """

        # Compute total drop-in fuel share
        total_share = saf_ftg_mandate_share + saf_co2_mandate_share + lcaf_mandate_share

        violation_normalised = (total_share - 100) / 100

        # Constraint values at enforcement years (skip if year not available)
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


def _no_degrowth_violation(energy: pd.Series, enforcement_years: list) -> list:
    """Compute normalized violations when energy decreases between control points."""

    eps = 1e-9

    years = [2030] + enforcement_years
    violations = []

    for prev, curr in zip(years[:-1], years[1:]):
        prev_val = energy.loc[prev]
        curr_val = energy.loc[curr]
        # Positive when current < previous (for inequality constraint >= 0)
        violation = (prev_val - curr_val) / (prev_val + eps)
        violations.append(violation)

    return violations


class SAFFTGNoDegrowthConstraint(AeroMAPSModel):
    """
    Prevent SAF FTG energy consumption from decreasing between enforcement years.

    Constraint is satisfied when <= 0; positive values indicate a decrease.
    """

    def __init__(self, name="saf_ftg_no_degrowth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        saf_ftg_energy_consumption: pd.Series,
        saf_ftg_no_degrowth_constraint_enforcement_years: list,
    ) -> list:
        saf_ftg_no_degrowth_constraint = _no_degrowth_violation(
            saf_ftg_energy_consumption, saf_ftg_no_degrowth_constraint_enforcement_years
        )
        return saf_ftg_no_degrowth_constraint


class SAFCO2NoDegrowthConstraint(AeroMAPSModel):
    """
    Prevent SAF CO2 energy consumption from decreasing between enforcement years.

    Constraint is satisfied when <= 0; positive values indicate a decrease.
    """

    def __init__(self, name="saf_co2_no_degrowth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        saf_co2_energy_consumption: pd.Series,
        saf_co2_no_degrowth_constraint_enforcement_years: list,
    ) -> list:
        saf_co2_no_degrowth_constraint = _no_degrowth_violation(
            saf_co2_energy_consumption, saf_co2_no_degrowth_constraint_enforcement_years
        )
        return saf_co2_no_degrowth_constraint


class LCAFNoDegrowthConstraint(AeroMAPSModel):
    """
    Prevent LCAF energy consumption from decreasing between enforcement years.

    Constraint is satisfied when <= 0; positive values indicate a decrease.
    """

    def __init__(self, name="lcaf_no_degrowth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        lcaf_energy_consumption: pd.Series,
        lcaf_no_degrowth_constraint_enforcement_years: list,
    ) -> list:
        lcaf_no_degrowth_constraint = _no_degrowth_violation(
            lcaf_energy_consumption, lcaf_no_degrowth_constraint_enforcement_years
        )
        return lcaf_no_degrowth_constraint

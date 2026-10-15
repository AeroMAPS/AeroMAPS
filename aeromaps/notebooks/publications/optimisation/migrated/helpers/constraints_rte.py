"""Constraints G2-G6 of the RTE optimisation paper, on the generic energy model.

Adapted from publications/ecats_2026/energy_constraints.py. The difference that
matters: the paper's ramp-up (Eq. 12) is the *least constraining* of a rate and a
volume limit, max{E_{t-1}(1+tau)^dt, E_{t-1} + dE*dt}; ecats implements the rate branch
only.

G1 (carbon budget) comes from the core CarbonBudgetConstraint via models_optim_complex.
"""

from typing import Tuple
import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class ReducedMandate(AeroMAPSModel):
    """Expand the optimiser's 5 reference-year shares into the full yaml vectors."""

    def __init__(self, name="reduced_mandate", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        generic_biofuel_mandate_share_values_optim: list,
        generic_electrofuel_mandate_share_values_optim: list,
        generic_biofuel_mandate_share_values_fixed: list,
        generic_electrofuel_mandate_share_values_fixed: list,
    ) -> Tuple[list, list]:
        generic_biofuel_mandate_share_values = list(
            generic_biofuel_mandate_share_values_fixed
        ) + list(generic_biofuel_mandate_share_values_optim)
        generic_electrofuel_mandate_share_values = list(
            generic_electrofuel_mandate_share_values_fixed
        ) + list(generic_electrofuel_mandate_share_values_optim)
        return generic_biofuel_mandate_share_values, generic_electrofuel_mandate_share_values


# Ceiling on the drop-in blend, just below 100 %.
#
# At exactly 100 % the residual fossil kerosene share is 100 - 100 = 0, and the
# energy model's own share arithmetic divides by it: measured on opt_B15_2_6, the
# 2050 kerosene energy came out at 7.3e-4 MJ against a ~1e12 MJ blend, a relative
# 4e-16, and re-evaluating that point kills the MDA with
# "converged on NaN: fossil_kerosene_share_dropin_fuel_fossil". It is the same
# 0/0 that EPSILON_SHARE guards against on the electrofuel pathway, which has no
# counterpart here because kerosene is the residual rather than a design variable.
#
# 99.999 % leaves 1e-5 of the blend as kerosene - eleven orders of magnitude above
# the degenerate value, and far below anything of policy interest, since the
# nearest non-saturated run sits at 0.55 %. Only the highest-biomass case ever
# reaches this ceiling; every other case runs out of biomass or electricity first.
MAX_BLEND_SHARE = 99.999


class BlendCompletenessConstraint(AeroMAPSModel):
    """G2: biofuel + electrofuel share must not exceed ``MAX_BLEND_SHARE``."""

    def __init__(self, name="blend_completeness_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        generic_biofuel_mandate_share: pd.Series,
        generic_electrofuel_mandate_share: pd.Series,
        blend_completeness_constraint_enforcement_years: list,
    ) -> list:
        total = generic_biofuel_mandate_share + generic_electrofuel_mandate_share
        violation = (total - MAX_BLEND_SHARE) / 100
        blend_completeness_constraint = [
            violation.loc[y]
            for y in blend_completeness_constraint_enforcement_years
            if y in total.index
        ]
        return blend_completeness_constraint


class BiomassAvailabilityConstraintTrajectory(AeroMAPSModel):
    """G3: aviation biomass use must stay within its allocated share."""

    def __init__(self, name="biomass_availability_constraint_trajectory", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        generic_biomass_availability_constraint_enforcement_years: list,
        generic_biomass_consumed_aviation_allocated_share: pd.Series,
    ) -> Tuple[list, pd.Series]:
        violation = (generic_biomass_consumed_aviation_allocated_share - 100) / 100
        biomass_trajectory_constraint = [
            violation.loc[y]
            for y in generic_biomass_availability_constraint_enforcement_years
            if y in violation.index
        ]
        biomass_violation_viz = generic_biomass_consumed_aviation_allocated_share.copy()
        self.df.loc[:, "biomass_availability_violation_viz"] = biomass_violation_viz
        return biomass_trajectory_constraint, biomass_violation_viz


class ElectricityAvailabilityConstraintTrajectory(AeroMAPSModel):
    """G4: aviation electricity use must stay within its allocated share."""

    def __init__(self, name="electricity_availability_constraint_trajectory", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        generic_electricity_constraint_enforcement_years: list,
        generic_electricity_consumed_aviation_allocated_share: pd.Series,
    ) -> Tuple[list, pd.Series]:
        violation = (generic_electricity_consumed_aviation_allocated_share - 100) / 100
        electricity_trajectory_constraint = [
            violation.loc[y]
            for y in generic_electricity_constraint_enforcement_years
            if y in violation.index
        ]
        electricity_violation_viz = generic_electricity_consumed_aviation_allocated_share.copy()
        self.df.loc[:, "electricity_availability_violation_viz"] = electricity_violation_viz
        return electricity_trajectory_constraint, electricity_violation_viz


# Energy consumptions are in MJ (~1e10-1e11 here) while the volume ramp-up limit is
# given in EJ/year, so the volume branch carries a 1e12 factor -- exactly as the
# published model does (`volume_ramp_up_constraint_biofuel * 5 * 1e12`). Without it the
# volume cap is ~1e-1 against a ~1e11 consumption, `max` can only ever pick the rate
# branch, and a pathway starting from zero has cap 0, pinning the violation at exactly
# 1.0 and making the ramp impossible to satisfy.
EJ_PER_YEAR_TO_MJ = 1e12


def _ramp_up_violation(consumption, enforcement_years, rate, volume):
    """Paper Eq. (12): the least constraining of the rate and volume limits.

        E_t <= max{ E_{t-1} (1 + tau)^dt ,  E_{t-1} + dE dt }

    Both branches are *increments* on the previous period's consumption. The rate branch
    compounds it; the volume branch adds a fixed industrial capacity addition. The max
    takes whichever is more permissive, which is what "the least constraining of the two"
    means.

    ``dE`` is a change in E, so the volume branch has to sit on top of ``E_{t-1}``. An
    earlier version of this function read the term as an absolute ceiling, ``dE dt``
    alone. That is wrong twice over: it under-constrains a pathway starting from zero
    (which may jump straight to dE dt in one period) and over-constrains every mature
    one, because once E_{t-1} exceeds dE dt the volume branch can never be the max again
    and the limit silently degenerates into a pure rate constraint. Measured on the
    ReFuelEU-budget optimum, the two readings disagree only in 2030 -- the one year the
    volume branch binds -- where the absolute form pinned biofuel at 0.1549 EJ against a
    true cap of 0.1910 EJ.

    The violation is normalised by ``volume * dt``, the industrial capacity-addition the
    scenario grants per period. That is a *constant* with respect to the design
    variables, so a violation of 1.0 reads as "one period of capacity additions beyond
    what is allowed" in every year and every run.

    Normalising by ``current`` instead would leave the feasible set untouched -- the
    denominator is strictly positive, so the sign never changes -- but costs twice over:
    it turns a nearly-linear constraint into a nonlinear one, and its derivative grows
    without bound as consumption approaches zero. Measured on the ReFuelEU point, that
    put the 2030 electrofuel row at roughly 600x the norm of every other constraint row,
    purely because electrofuel starts near zero there.
    """
    out = []
    check_years = [enforcement_years[0] - 5] + list(enforcement_years)
    for year in enforcement_years:
        lookback = year - 5 if (year - 5) in check_years else year - 10
        dt = year - lookback
        previous = consumption.loc[lookback]
        current = consumption.loc[year]
        allowance = volume * dt * EJ_PER_YEAR_TO_MJ
        cap = max(previous * (1 + rate) ** dt, previous + allowance)
        # Constant w.r.t. the design variables; varies by year only through dt.
        out.append((current - cap) / allowance)
    return out


class BiofuelUseGrowthConstraint(AeroMAPSModel):
    """G5: biofuel ramp-up, max(rate, volume)."""

    def __init__(self, name="biofuel_use_growth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        rate_ramp_up_constraint_biofuel: float,
        volume_ramp_up_constraint_biofuel: float,
        generic_biofuel_energy_consumption: pd.Series,
        biofuel_use_growth_constraint_enforcement_years: list,
    ) -> list:
        biofuel_use_growth_constraint = _ramp_up_violation(
            generic_biofuel_energy_consumption,
            biofuel_use_growth_constraint_enforcement_years,
            rate_ramp_up_constraint_biofuel,
            volume_ramp_up_constraint_biofuel,
        )
        return biofuel_use_growth_constraint


class ElectrofuelUseGrowthConstraint(AeroMAPSModel):
    """G6: electrofuel ramp-up, max(rate, volume)."""

    def __init__(self, name="electrofuel_use_growth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        rate_ramp_up_constraint_electrofuel: float,
        volume_ramp_up_constraint_electrofuel: float,
        generic_electrofuel_energy_consumption: pd.Series,
        electrofuel_use_growth_constraint_enforcement_years: list,
    ) -> list:
        electrofuel_use_growth_constraint = _ramp_up_violation(
            generic_electrofuel_energy_consumption,
            electrofuel_use_growth_constraint_enforcement_years,
            rate_ramp_up_constraint_electrofuel,
            volume_ramp_up_constraint_electrofuel,
        )
        return electrofuel_use_growth_constraint

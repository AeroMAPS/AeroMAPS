# @Time : 03/10/2024 13:43
# @Author : a.salgas
# @File : energy_availability_trajectory.py
# @Software: PyCharm


from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function


class BiomassAvailabilityConstraintTrajectory(AeroMAPSModel):
    def __init__(self, name="biomass_availability_constraint_trajectory", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        biomass_availability_constraint_trajectory_reference_years: list,
        biomass_availability_constraint_trajectory_reference_years_values: list,
        biomass_consumption: pd.Series,
        aviation_biomass_allocated_share: float,
    ) -> float:


        # Biomass
        biomass_availability_constraint_trajectory = aeromaps_interpolation_function(
            self,
            biomass_availability_constraint_trajectory_reference_years,
            biomass_availability_constraint_trajectory_reference_years_values,
            method="linear",
            positive_constraint=True,
            model_name=self.name,
        )

        aviation_available_biomass = (
                aviation_biomass_allocated_share / 100 * biomass_availability_constraint_trajectory
        )

        annual_constraint = (biomass_consumption - aviation_available_biomass)/aviation_available_biomass

        biomass_trajectory_constraint = np.max(annual_constraint.loc[self.prospection_start_year: self.end_year])

        self.float_outputs["biomass_trajectory_constraint"] = biomass_trajectory_constraint

        return biomass_trajectory_constraint
    


class ElectricityAvailabilityConstraintTrajectory(AeroMAPSModel):
    def __init__(self, name="electricity_availability_constraint_trajectory", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electricity_availability_constraint_trajectory_reference_years: list,
        electricity_availability_constraint_trajectory_reference_years_values: list,
        electricity_consumption: pd.Series,
        aviation_electricity_allocated_share: float,
    ) -> float:


        # Electricity
        electricity_availability_constraint_trajectory = aeromaps_interpolation_function(
            self,
            electricity_availability_constraint_trajectory_reference_years,
            electricity_availability_constraint_trajectory_reference_years_values,
            method="linear",
            positive_constraint=True,
            model_name=self.name,
        )

        aviation_available_electricity = (
                aviation_electricity_allocated_share / 100 * electricity_availability_constraint_trajectory
        )

        annual_constraint = (electricity_consumption - aviation_available_electricity) /aviation_available_electricity

        electricity_trajectory_constraint = np.max(annual_constraint.loc[self.prospection_start_year:self.end_year])

        self.float_outputs["electricity_trajectory_constraint"] = electricity_trajectory_constraint

        return electricity_trajectory_constraint


class BlendCompletenessConstraint(AeroMAPSModel):
    def __init__(self, name="blend_completeness_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            kerosene_share: pd.Series,
    )-> float:
        blend_completeness_constraint = - min(kerosene_share)/100

        self.float_outputs["blend_completeness_constraint"] = blend_completeness_constraint
        return blend_completeness_constraint


class BiofuelUseGrowthConstraint(AeroMAPSModel):
    def __init__(self, name="biofuel_use_growth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            energy_consumption_biofuel: pd.Series,
            volume_ramp_up_constraint_biofuel: float,
            rate_ramp_up_constraint_biofuel: float
    )-> Tuple[float, float]:

        annual_biofuel_growth = energy_consumption_biofuel.diff().loc[self.prospection_start_year+1:self.end_year]

        annual_constraint = annual_biofuel_growth.copy()

        for t in range(self.prospection_start_year+1, self.end_year+1):
            year_rate_constraint = rate_ramp_up_constraint_biofuel*energy_consumption_biofuel.loc[t-1]
            year_constraint = max(volume_ramp_up_constraint_biofuel * 1e12, year_rate_constraint)
            annual_constraint.loc[t] = (annual_constraint.loc[t] - year_constraint)/abs(np.mean((annual_biofuel_growth)))

        biofuel_use_growth_constraint = max(annual_constraint)

        # print(biofuel_use_growth_constraint)

        biofuel_use_no_degrowth_constraint = - min(annual_biofuel_growth)/abs(np.mean((annual_biofuel_growth)))

        # print(biofuel_use_no_degrowth_constraint)

        self.float_outputs["biofuel_use_growth_constraint"] = biofuel_use_growth_constraint
        self.float_outputs["biofuel_use_no_degrowth_constraint"] = biofuel_use_no_degrowth_constraint
        return biofuel_use_growth_constraint, biofuel_use_no_degrowth_constraint


class ElectrofuelUseGrowthConstraint(AeroMAPSModel):
    def __init__(self, name="electrofuel_use_growth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            energy_consumption_electrofuel: pd.Series,
            volume_ramp_up_constraint_electrofuel: float,
            rate_ramp_up_constraint_electrofuel: float
    ) -> Tuple[float, float]:

        annual_electrofuel_growth = energy_consumption_electrofuel.diff().loc[self.prospection_start_year + 1:self.end_year]

        annual_constraint = annual_electrofuel_growth.copy()*1e-12

        for t in range(self.prospection_start_year + 1, self.end_year + 1):
            year_rate_constraint = rate_ramp_up_constraint_electrofuel * energy_consumption_electrofuel.loc[t - 1]*1e-12
            year_constraint = max(volume_ramp_up_constraint_electrofuel, year_rate_constraint)
            annual_constraint.loc[t] = (annual_constraint.loc[t] - year_constraint)/abs(np.mean(annual_electrofuel_growth))

        electrofuel_use_growth_constraint = max(annual_constraint)

        electrofuel_use_no_degrowth_constraint = - min(annual_electrofuel_growth)/abs(np.mean(annual_electrofuel_growth))

        self.float_outputs["electrofuel_use_growth_constraint"] = electrofuel_use_growth_constraint
        self.float_outputs["electrofuel_use_no_degrowth_constraint"] = electrofuel_use_no_degrowth_constraint
        return electrofuel_use_growth_constraint, electrofuel_use_no_degrowth_constraint
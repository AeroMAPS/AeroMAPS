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

        annual_constraint=biomass_consumption - aviation_available_biomass

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

        annual_constraint = electricity_consumption - aviation_available_electricity

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
        blend_completeness_constraint = - min(kerosene_share)

        self.float_outputs["blend_completeness_constraint"] = blend_completeness_constraint
        return blend_completeness_constraint


class BiofuelUseGrowthConstraint(AeroMAPSModel):
    def __init__(self, name="biofuel_use_growth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            energy_consumption_biofuel: pd.Series,
    )-> float:
        annual_biofuel_growth = energy_consumption_biofuel.diff().loc[self.prospection_start_year+1:self.end_year]

        biofuel_use_growth_constraint = - min(annual_biofuel_growth)

        self.float_outputs["biofuel_use_growth_constraint"] = biofuel_use_growth_constraint
        return biofuel_use_growth_constraint


class ElectrofuelUseGrowthConstraint(AeroMAPSModel):
    def __init__(self, name="electrofuel_use_growth_constraint", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            energy_consumption_electrofuel: pd.Series,
    ) -> float:

        annual_electrofuel_growth=energy_consumption_electrofuel.diff().loc[self.prospection_start_year+1:self.end_year]

        electrofuel_use_growth_constraint = - min(annual_electrofuel_growth)

        self.float_outputs["electrofuel_use_growth_constraint"] = electrofuel_use_growth_constraint
        return electrofuel_use_growth_constraint
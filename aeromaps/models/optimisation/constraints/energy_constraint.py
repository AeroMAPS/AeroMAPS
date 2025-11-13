# # @Time : 03/10/2024 13:43
# # @Author : a.salgas
# # @File : energy_availability_trajectory.py
# # @Software: PyCharm
# from typing import Tuple
#
# import pandas as pd
#
# from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function
# # TODO DELETE THIS FILE.
#
#
# class BiomassAvailabilityConstraintTrajectory(AeroMAPSModel):
#     def __init__(self, name="biomass_availability_constraint_trajectory", *args, **kwargs):
#         super().__init__(name, *args, **kwargs)
#
#     def compute(
#         self,
#         biomass_availability_constraint_trajectory_reference_years: list,
#         biomass_availability_constraint_enforcement_years: list,
#         biomass_availability_constraint_trajectory_reference_years_values: list,
#         biomass_consumption: pd.Series,
#         energy_consumption_biofuel: pd.Series,
#         aviation_biomass_allocated_share: float,
#     ) -> Tuple[list, pd.Series]:
#         # Electricity
#         biomass_availability_constraint_trajectory = aeromaps_interpolation_function(
#             self,
#             biomass_availability_constraint_trajectory_reference_years,
#             biomass_availability_constraint_trajectory_reference_years_values,
#             method="linear",
#             positive_constraint=True,
#             model_name=self.name,
#         )
#
#         aviation_available_biomass = (
#             aviation_biomass_allocated_share / 100 * biomass_availability_constraint_trajectory
#         )
#
#         # biofuel_max_availability_viz was made are made to visualise
#         # the max potential biofuel produced in post-processing. Not used as a constraint until now.
#         # if no biofuel is used, no efficiency can be calculated, so viz value will be nan.
#         # Not problematic for use case.
#         avg_eff = energy_consumption_biofuel / biomass_consumption
#         start_biofuel = energy_consumption_biofuel.first_valid_index()
#         for k in range(self.prospection_start_year, start_biofuel):
#             avg_eff.loc[k] = avg_eff.loc[start_biofuel]
#
#         biofuel_max_availability_viz = avg_eff * aviation_available_biomass
#
#         eps = 1e6  # Small value to avoid division by zero
#         annual_constraint = (biomass_consumption - aviation_available_biomass) / (
#             aviation_available_biomass + eps
#         )
#
#         # biomass_trajectory_constraint = np.max(
#         #     annual_constraint.loc[self.prospection_start_year : self.end_year]
#         # ) # --> old version based on constraint aggregation.
#         biomass_trajectory_constraint = [
#             annual_constraint.loc[year]
#             for year in biomass_availability_constraint_enforcement_years
#         ]
#
#         self.df.loc[:, "biofuel_max_availability_viz"] = biofuel_max_availability_viz
#
#         # TODO if we want to track constraints, we migh introduce something like self.constraints.
#         #   I'm not sure if it's necessary as gemseo provide good post-processing features.
#         #   So only returning constraints as variables for now. Concerns all constraints.
#
#         return biomass_trajectory_constraint, biofuel_max_availability_viz
#
#
# class ElectricityAvailabilityConstraintTrajectory(AeroMAPSModel):
#     def __init__(self, name="electricity_availability_constraint_trajectory", *args, **kwargs):
#         super().__init__(name, *args, **kwargs)
#
#     def compute(
#         self,
#         electricity_availability_constraint_trajectory_reference_years: list,
#         electricity_availability_constraint_trajectory_reference_years_values: list,
#         electricity_availability_constraint_enforcement_years: list,
#         electricity_consumption: pd.Series,
#         energy_consumption_electrofuel: pd.Series,
#         aviation_electricity_allocated_share: float,
#     ) -> Tuple[list, pd.Series]:
#         # Electricity
#         electricity_availability_constraint_trajectory = aeromaps_interpolation_function(
#             self,
#             electricity_availability_constraint_trajectory_reference_years,
#             electricity_availability_constraint_trajectory_reference_years_values,
#             method="linear",
#             positive_constraint=True,
#             model_name=self.name,
#         )
#
#         aviation_available_electricity = (
#             aviation_electricity_allocated_share
#             / 100
#             * electricity_availability_constraint_trajectory
#         )
#
#         # electrofuel_max_availability_viz was made are made to visualise
#         # the max potential electrofuel produced in post-processing. Not used as a constraint until now.
#         # if no efuel is used, no efficiency can be calculated, so viz value will be nan.
#         # Not problematic for use case.
#         avg_eff = energy_consumption_electrofuel / electricity_consumption
#         start_efuel = energy_consumption_electrofuel.first_valid_index()
#         for k in range(self.prospection_start_year, start_efuel):
#             avg_eff.loc[k] = avg_eff.loc[start_efuel]
#
#         electrofuel_max_availability_viz = avg_eff * aviation_available_electricity
#
#         eps = 1e6  # Small value to avoid division by zero
#         annual_constraint = (electricity_consumption - aviation_available_electricity) / (
#             aviation_available_electricity + eps
#         )
#
#         # electricity_trajectory_constraint = np.max(
#         #     annual_constraint.loc[self.prospection_start_year : self.end_year]
#         # ) --> old version based on constraint aggregation.
#
#         electricity_trajectory_constraint = [
#             annual_constraint.loc[year]
#             for year in electricity_availability_constraint_enforcement_years
#         ]
#
#         self.df.loc[:, "electrofuel_max_availability_viz"] = electrofuel_max_availability_viz
#
#         return electricity_trajectory_constraint, electrofuel_max_availability_viz
#
#
# class BlendCompletenessConstraint(AeroMAPSModel):
#     def __init__(self, name="blend_completeness_constraint", *args, **kwargs):
#         super().__init__(name, *args, **kwargs)
#
#     def compute(
#         self,
#         kerosene_share: pd.Series,
#         blend_completeness_constraint_enforcement_years: list,
#     ) -> list:
#         # blend_completeness_constraint = -min(kerosene_share) / 100
#
#         blend_completeness_constraint = [
#             -kerosene_share.loc[year] / 100
#             for year in blend_completeness_constraint_enforcement_years
#         ]
#
#         return blend_completeness_constraint
#
#
# class BiofuelUseGrowthConstraint(AeroMAPSModel):
#     def __init__(self, name="biofuel_use_growth_constraint", *args, **kwargs):
#         super().__init__(name, *args, **kwargs)
#
#     def compute(
#         self,
#         rate_ramp_up_constraint_biofuel: float,
#         energy_consumption_biofuel: pd.Series,
#         volume_ramp_up_constraint_biofuel: float,
#         biofuel_use_growth_constraint_enforcement_years: list,
#     ) -> list:
#         eps = 1e6  # Small value to avoid division by zero
#         biofuel_use_growth_constraint = [
#             (
#                 energy_consumption_biofuel.loc[i]
#                 - max(
#                     volume_ramp_up_constraint_biofuel * 5 * 1e12,
#                     energy_consumption_biofuel.loc[i - 5]
#                     * (1 + rate_ramp_up_constraint_biofuel) ** 5,
#                 )
#             )
#             / (energy_consumption_biofuel.loc[i] + eps)
#             for i in biofuel_use_growth_constraint_enforcement_years
#         ]
#
#         return biofuel_use_growth_constraint
#
#     # def compute(
#     #     self,
#     #     energy_consumption_biofuel: pd.Series,
#     #     volume_ramp_up_constraint_biofuel: float,
#     #     rate_ramp_up_constraint_biofuel: float,
#     # ) -> Tuple[float, float, pd.Series, pd.Series]:
#     #    # Complex version of the constraint, not used anymore but kept for reference
#     #
#     #     annual_biofuel_growth = energy_consumption_biofuel.diff().loc[2027 : self.end_year]
#     #     annual_biofuel_growth_constraint = annual_biofuel_growth.copy()
#     #
#     #     ### Max ramp up constraint for visualisation. Do no maistake with actual rampup constraint !!!
#     #     # All constraints with "VIZ" are for visualisation only !!!
#     #     annual_biofuel_growth_constraint_viz = annual_biofuel_growth.copy()
#     #
#     #     biofuel_growth_constraint_theoretical_max_viz = pd.Series(
#     #         index=range(self.prospection_start_year, self.end_year + 1), dtype=float
#     #     )
#     #     biofuel_growth_constraint_theoretical_max_viz.loc[2025] = energy_consumption_biofuel.loc[
#     #         2025
#     #     ]
#     #
#     #
#     #
#     #     for t in range(2026 + 1, self.end_year + 1):
#     #         biofuel_growth_constraint_theoretical_max_viz.loc[t] = (
#     #             biofuel_growth_constraint_theoretical_max_viz.loc[t - 1]
#     #             + max(
#     #                 volume_ramp_up_constraint_biofuel * 1e12,
#     #                 rate_ramp_up_constraint_biofuel
#     #                 * biofuel_growth_constraint_theoretical_max_viz.loc[t - 1],
#     #             )
#     #         )
#     #
#     #         # Real constraint definition
#     #         year_rate_constraint = (
#     #             rate_ramp_up_constraint_biofuel * energy_consumption_biofuel.loc[t - 1]
#     #         )
#     #         year_constraint = max(volume_ramp_up_constraint_biofuel * 1e12, year_rate_constraint)
#     #
#     #         annual_biofuel_growth_constraint_viz.loc[t] = (
#     #             energy_consumption_biofuel.loc[t - 1] + year_constraint
#     #         )
#     #         annual_biofuel_growth_constraint.loc[t] = (
#     #             annual_biofuel_growth_constraint.loc[t] - year_constraint
#     #         ) / abs(np.mean((annual_biofuel_growth)))
#     #
#     #     biofuel_use_growth_constraint = max(annual_biofuel_growth_constraint)
#     #     biofuel_use_no_degrowth_constraint = -min(annual_biofuel_growth) / abs(
#     #         np.mean(annual_biofuel_growth)
#     #     )
#     #
#     #     self.df.loc[:, "annual_biofuel_growth_constraint_viz"] = (
#     #         annual_biofuel_growth_constraint_viz
#     #     )
#     #     self.df.loc[:, "biofuel_growth_constraint_theoretical_max_viz"] = (
#     #         biofuel_growth_constraint_theoretical_max_viz
#     #     )
#     #     self.float_outputs["biofuel_use_growth_constraint"] = biofuel_use_growth_constraint
#     #     self.float_outputs["biofuel_use_no_degrowth_constraint"] = (
#     #         biofuel_use_no_degrowth_constraint
#     #     )
#     #     return (
#     #         biofuel_use_growth_constraint,
#     #         biofuel_use_no_degrowth_constraint,
#     #         annual_biofuel_growth_constraint,
#     #         annual_biofuel_growth,
#     #     )
#
#
# class ElectrofuelUseGrowthConstraint(AeroMAPSModel):
#     def __init__(self, name="electrofuel_use_growth_constraint", *args, **kwargs):
#         super().__init__(name, *args, **kwargs)
#
#     def compute(
#         self,
#         rate_ramp_up_constraint_electrofuel: float,
#         energy_consumption_electrofuel: pd.Series,
#         volume_ramp_up_constraint_electrofuel: float,
#         electrofuel_use_growth_constraint_enforcement_years: list,
#     ) -> list:
#         eps = 1e6  # Small value to avoid division by zero
#         electrofuel_use_growth_constraint = [
#             (
#                 energy_consumption_electrofuel.loc[i]
#                 - max(
#                     volume_ramp_up_constraint_electrofuel * 5 * 1e12,
#                     energy_consumption_electrofuel.loc[i - 5]
#                     * (1 + rate_ramp_up_constraint_electrofuel) ** 5,
#                 )
#             )
#             / (energy_consumption_electrofuel.loc[i] + eps)
#             for i in electrofuel_use_growth_constraint_enforcement_years
#         ]
#
#         return electrofuel_use_growth_constraint
#
#     # def compute(
#     #     self,
#     #     energy_consumption_electrofuel: pd.Series,
#     #     volume_ramp_up_constraint_electrofuel: float,
#     #     rate_ramp_up_constraint_electrofuel: float,
#     # ) -> Tuple[float, float, pd.Series, pd.Series]:
#     #    # Complex version of the constraint, not used anymore but kept for reference
#     #     annual_electrofuel_growth = energy_consumption_electrofuel.diff().loc[2031 : self.end_year]
#     #
#     #     annual_electrofuel_growth_constraint = annual_electrofuel_growth.copy()
#     #     ### Max ramp up constraint for visualisation. Do no maistake with actual rampup constraint !!!
#     #     # All constraints with "VIZ" are for visualisation only !!!
#     #     annual_electrofuel_growth_constraint_viz = annual_electrofuel_growth.copy()
#     #
#     #     electrofuel_growth_constraint_theoretical_max_viz = pd.Series(
#     #         index=range(self.prospection_start_year, self.end_year + 1), dtype=float
#     #     )
#     #     electrofuel_growth_constraint_theoretical_max_viz.loc[2025] = (
#     #         energy_consumption_electrofuel.loc[2025]
#     #     )
#     #
#     #     for t in range(2030 + 1, self.end_year + 1):
#     #         electrofuel_growth_constraint_theoretical_max_viz.loc[t] = (
#     #             electrofuel_growth_constraint_theoretical_max_viz.loc[t - 1]
#     #             + max(
#     #                 volume_ramp_up_constraint_electrofuel * 1e12,
#     #                 rate_ramp_up_constraint_electrofuel
#     #                 * electrofuel_growth_constraint_theoretical_max_viz.loc[t - 1],
#     #             )
#     #         )
#     #
#     #         # Real constraint definition
#     #         year_rate_constraint = (
#     #             rate_ramp_up_constraint_electrofuel * energy_consumption_electrofuel.loc[t - 1]
#     #         )
#     #         year_constraint = max(
#     #             volume_ramp_up_constraint_electrofuel * 1e12, year_rate_constraint
#     #         )
#     #
#     #         annual_electrofuel_growth_constraint_viz.loc[t] = (
#     #             energy_consumption_electrofuel.loc[t - 1] + year_constraint
#     #         )
#     #         annual_electrofuel_growth_constraint.loc[t] = (
#     #             annual_electrofuel_growth_constraint.loc[t] - year_constraint
#     #         ) / abs(np.mean((annual_electrofuel_growth)))
#     #
#     #     electrofuel_use_growth_constraint = max(annual_electrofuel_growth_constraint)
#     #     electrofuel_use_no_degrowth_constraint = -min(annual_electrofuel_growth) / abs(
#     #         np.mean(annual_electrofuel_growth)
#     #     )
#     #
#     #     self.df.loc[:, "annual_electrofuel_growth_constraint_viz"] = (
#     #         annual_electrofuel_growth_constraint_viz
#     #     )
#     #     self.df.loc[:, "electrofuel_growth_constraint_theoretical_max_viz"] = (
#     #         electrofuel_growth_constraint_theoretical_max_viz
#     #     )
#     #     self.float_outputs["electrofuel_use_growth_constraint"] = electrofuel_use_growth_constraint
#     #     self.float_outputs["electrofuel_use_no_degrowth_constraint"] = (
#     #         electrofuel_use_no_degrowth_constraint
#     #     )
#     #     return (
#     #         electrofuel_use_growth_constraint,
#     #         electrofuel_use_no_degrowth_constraint,
#     #         annual_electrofuel_growth_constraint,
#     #         annual_electrofuel_growth,
#     #     )

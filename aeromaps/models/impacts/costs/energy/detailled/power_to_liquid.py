# @Time : 24/02/2023 17:44
# @Author : a.salgas
# @File : power_to_liquid.py
# @Software: PyCharm

from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class ElectrofuelCost(AeroMAPSModel):
    def __init__(self, name="electrofuel_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_electrofuel: pd.Series,
        electrofuel_eis_capex: pd.Series,
        electrofuel_eis_fixed_opex: pd.Series,
        electrofuel_eis_var_opex: pd.Series,
        electrolysis_efficiency: pd.Series,
        electrofuel_hydrogen_efficiency: pd.Series,
        kerosene_market_price: pd.Series,
        kerosene_emission_factor: pd.Series,
        electrofuel_emission_factor: pd.Series,
        electricity_market_price: pd.Series,
        co2_market_price: pd.Series,
        electrofuel_eis_specific_co2: pd.Series,
        electricity_load_factor: pd.Series,
        carbon_tax: pd.Series,
        exogenous_carbon_price_trajectory: pd.Series,
        plant_lifespan: float,
        private_discount_rate: float,
        social_discount_rate: float,
        lhv_electrofuel: float,
        density_electrofuel: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        ######## HYDROGEN PRODUCTION ########

        #### ELECTROLYSIS ####

        (
            electrofuel_plant_building_scenario,
            electrofuel_plant_building_cost,
            electrofuel_total_cost,
            electrofuel_mean_capex_share,
            electrofuel_mean_opex_share,
            electrofuel_mean_elec_share,
            electrofuel_mean_co2_share,
            electrofuel_mean_mfsp_litre,
            electrofuel_cost_premium,
            electrofuel_carbon_tax,
            electrofuel_mfsp_carbon_tax_supplement,
            carbon_abatement_cost_electrofuel,
            specific_carbon_abatement_cost_electrofuel,
            generic_specific_carbon_abatement_cost_electrofuel,
        ) = self._electrofuel_computation(
            electrofuel_eis_capex,
            electrofuel_eis_fixed_opex,
            electrofuel_eis_var_opex,
            electrolysis_efficiency,
            electrofuel_hydrogen_efficiency,
            electricity_market_price,
            energy_consumption_electrofuel,
            electricity_load_factor,
            co2_market_price,
            electrofuel_eis_specific_co2,
            kerosene_emission_factor,
            electrofuel_emission_factor,
            kerosene_market_price,
            carbon_tax,
            exogenous_carbon_price_trajectory,
            plant_lifespan,
            private_discount_rate,
            social_discount_rate,
            lhv_electrofuel,
            density_electrofuel,
        )

        self.df.loc[:, "electrofuel_plant_building_scenario"] = electrofuel_plant_building_scenario
        self.df.loc[:, "electrofuel_plant_building_cost"] = electrofuel_plant_building_cost
        self.df.loc[:, "electrofuel_total_cost"] = electrofuel_total_cost
        self.df.loc[:, "electrofuel_mean_capex_share"] = electrofuel_mean_capex_share
        self.df.loc[:, "electrofuel_mean_opex_share"] = electrofuel_mean_opex_share
        self.df.loc[:, "electrofuel_mean_elec_share"] = electrofuel_mean_elec_share
        self.df.loc[:, "electrofuel_mean_co2_share"] = electrofuel_mean_co2_share
        self.df.loc[:, "electrofuel_cost_premium"] = electrofuel_cost_premium
        self.df.loc[:, "electrofuel_mean_mfsp_litre"] = electrofuel_mean_mfsp_litre
        self.df.loc[:, "carbon_abatement_cost_electrofuel"] = carbon_abatement_cost_electrofuel
        self.df.loc[:, "specific_carbon_abatement_cost_electrofuel"] = (
            specific_carbon_abatement_cost_electrofuel
        )
        self.df.loc[:, "generic_specific_carbon_abatement_cost_electrofuel"] = (
            generic_specific_carbon_abatement_cost_electrofuel
        )
        self.df.loc[:, "electrofuel_carbon_tax"] = electrofuel_carbon_tax
        self.df.loc[:, "electrofuel_mfsp_carbon_tax_supplement"] = (
            electrofuel_mfsp_carbon_tax_supplement
        )

        return (
            electrofuel_plant_building_scenario,
            electrofuel_plant_building_cost,
            electrofuel_total_cost,
            electrofuel_mean_capex_share,
            electrofuel_mean_opex_share,
            electrofuel_mean_elec_share,
            electrofuel_mean_co2_share,
            electrofuel_cost_premium,
            electrofuel_mean_mfsp_litre,
            carbon_abatement_cost_electrofuel,
            electrofuel_carbon_tax,
            electrofuel_mfsp_carbon_tax_supplement,
            specific_carbon_abatement_cost_electrofuel,
            generic_specific_carbon_abatement_cost_electrofuel,
        )

    def _electrofuel_computation(
        self,
        electrofuel_eis_capex: pd.Series,
        electrofuel_eis_fixed_opex: pd.Series,
        electrofuel_eis_var_opex: pd.Series,
        # electrofuel_eis_specific_energy: pd.Series,
        electrolysis_efficiency: pd.Series,
        electrofuel_hydrogen_efficiency: pd.Series,
        electricity_market_price: pd.Series,
        energy_consumption_electrofuel: pd.Series,
        electricity_load_factor: pd.Series,
        co2_market_price: pd.Series,
        electrofuel_eis_specific_co2: pd.Series,
        kerosene_emission_factor: pd.Series,
        electrofuel_emission_factor: pd.Series,
        kerosene_market_price: pd.Series,
        carbon_tax: pd.Series,
        exogenous_carbon_price_trajectory: pd.Series,
        plant_lifespan: float,
        private_discount_rate: float,
        social_discount_rate: float,
        lhv_electrofuel: float,
        density_electrofuel: float,
    ):
        """
        Computes the yearly costs to respect a given hydrogen electrolysis production scenario.
        Capex in €/ton/day
        Fixed opex in  €/ton/day
        Variable opex in € per kg
        Specific electricity in kWh/kg --> Deprecated to harmonize with efficiency compytation, but might be reactivated later?
        Electricity market price in €/kWh
        Energy_consumption_hydrogen in MJ.
        Values returned are in M€ or t/day
        """

        # Constants:
        construction_time = 3
        plant_load_fact = 0.95

        # Avoided emission factor in gCO2/MJ
        avoided_emission_factor = kerosene_emission_factor - electrofuel_emission_factor

        # Demand scenario for the pathway in MJ
        demand_scenario = energy_consumption_electrofuel

        # Catching the indexes from the demand scenario
        indexes = demand_scenario.index

        # Additional plant capacity building needed (in ton/day output size) for a given year
        plant_building_scenario = pd.Series(np.zeros(len(indexes)), indexes)
        # Relative CAPEX cost to build the new facilities in M€2020
        plant_building_cost = pd.Series(np.zeros(len(indexes)), indexes)

        # Annual production in MJ
        electrofuel_production = pd.Series(np.zeros(len(indexes)), indexes)

        # carbon abatement cost in €/ton
        # carbon_abatement_cost = pd.Series(np.zeros(len(indexes)), indexes)

        specific_carbon_abatement_cost = pd.Series(np.nan, indexes)
        generic_specific_carbon_abatement_cost = pd.Series(np.nan, indexes)

        # Annual cost and cost components of hydrogen production in M€
        electrofuel_total_cost = pd.Series(np.zeros(len(indexes)), indexes)
        electrofuel_capex_cost = pd.Series(np.zeros(len(indexes)), indexes)
        electrofuel_opex_cost = pd.Series(np.zeros(len(indexes)), indexes)
        electrofuel_elec_cost = pd.Series(np.zeros(len(indexes)), indexes)
        electrofuel_co2_cost = pd.Series(np.zeros(len(indexes)), indexes)

        # Total extra cost linked to carbon tax in M€2020
        # electrofuel_carbon_tax_cost = pd.Series(np.zeros(len(indexes)), indexes)
        # Total annual cost premium in M€2020
        # electrofuel_cost_premium = pd.Series(np.zeros(len(indexes)), indexes)

        # Extra cost on mfsp linked to carbon tax in €/L
        # mfsp_supplement_carbon_tax = pd.Series(np.zeros(len(indexes)), indexes)

        # For each year o²f the demand scenario the demand is matched by the production
        for year in list(demand_scenario.index):
            # Production missing in year n+1 must be supplied by plant build in year n
            if (year + 1) <= self.end_year and electrofuel_production[year + 1] < demand_scenario[
                year + 1
            ]:
                # Getting the production not matched by plants already commissioned by creating an electrolyzer with year data technical data

                electrofuel_cost = self._compute_electrofuel_year_lcop(
                    int(construction_time),
                    int(plant_lifespan),
                    year - construction_time,
                    electricity_market_price,
                    co2_market_price,
                    electricity_load_factor,
                    electrofuel_eis_capex,
                    electrofuel_eis_fixed_opex,
                    electrofuel_eis_var_opex,
                    electrolysis_efficiency,
                    electrofuel_hydrogen_efficiency,
                    electrofuel_eis_specific_co2,
                    private_discount_rate,
                    plant_load_fact,
                    lhv_electrofuel,
                    density_electrofuel,
                )

                # Getting the production not matched by plants already commissioned
                missing_production = demand_scenario[year + 1] - electrofuel_production[year + 1]

                # Converting the missing production to a capacity (in t/day)
                missing_production_kg = missing_production / lhv_electrofuel
                missing_production_litres = missing_production_kg / density_electrofuel
                electrofuel_capacity_to_build = (
                    missing_production_kg
                    / 365.25
                    / min(electricity_load_factor[year], plant_load_fact)
                )  # capacity to build in kg/day production, taking into account load_factor

                electrolyser_capex_year = (
                    electrofuel_capacity_to_build * electrofuel_eis_capex[year] / 1000000
                )  # electrolyzer capex is in €/kg/day => M€
                plant_building_scenario[year] = electrofuel_capacity_to_build  # in ton/day capacity

                for construction_year in range(year - construction_time, year):
                    if self.historic_start_year < construction_year < self.end_year:
                        plant_building_cost[construction_year] += (
                            electrolyser_capex_year / construction_time
                        )

                # When production ends: either at the end of plant life or the end of the scenario;
                end_bound = int(min(list(demand_scenario.index)[-1], year + plant_lifespan))

                discounted_cumul_cost = 0
                cumul_em = 0
                generic_discounted_cumul_em = 0

                # Adding new plant production to future years
                for i in range(year + 1, end_bound + 1):
                    electrofuel_total_cost[i] = (
                        electrofuel_total_cost[i]
                        + (missing_production_litres * electrofuel_cost[i]["TOTAL"]) / 1000000
                    )  # €/L and production in litres => /1000000 for M€
                    electrofuel_capex_cost[i] = (
                        electrofuel_capex_cost[i]
                        + (missing_production_litres * electrofuel_cost[i]["CAPEX"]) / 1000000
                    )  # M€
                    electrofuel_opex_cost[i] = (
                        electrofuel_opex_cost[i]
                        + (missing_production_litres * electrofuel_cost[i]["FIX_OPEX"]) / 1000000
                        + (missing_production_litres * electrofuel_cost[i]["VAR_OPEX"]) / 1000000
                    )  # M€
                    electrofuel_elec_cost[i] = (
                        electrofuel_elec_cost[i]
                        + (missing_production_litres * electrofuel_cost[i]["ELECTRICITY"]) / 1000000
                    )  # M€
                    electrofuel_co2_cost[i] = (
                        electrofuel_co2_cost[i]
                        + (missing_production_litres * electrofuel_cost[i]["CO2"]) / 1000000
                    )  # M€
                    electrofuel_production[i] = electrofuel_production[i] + missing_production

                for i in range(year, year + int(plant_lifespan)):
                    if i < (self.end_year + 1):
                        discounted_cumul_cost += (
                            electrofuel_cost[i]["TOTAL"] - kerosene_market_price[i]
                        ) / (1 + social_discount_rate) ** (i - year)
                        cumul_em += (
                            avoided_emission_factor[i]
                            * (lhv_electrofuel * density_electrofuel)
                            / 1000000
                        )

                        # discounting emissions for non-hotelling scc
                        generic_discounted_cumul_em += (
                            avoided_emission_factor[i]
                            * (lhv_electrofuel * density_electrofuel)
                            / 1000000
                            * exogenous_carbon_price_trajectory[i]
                            / exogenous_carbon_price_trajectory[year]
                            / (1 + social_discount_rate) ** (i - year)
                        )
                    else:
                        discounted_cumul_cost += (
                            electrofuel_cost[self.end_year]["TOTAL"]
                            - kerosene_market_price[self.end_year]
                        ) / (1 + social_discount_rate) ** (i - year)
                        cumul_em += (
                            avoided_emission_factor[self.end_year]
                            * (lhv_electrofuel * density_electrofuel)
                            / 1000000
                        )

                        # discounting emissions for non-hotelling scc, keep last year scc growth rate as future scc growth rate
                        future_scc_growth = (
                            exogenous_carbon_price_trajectory[self.end_year]
                            / exogenous_carbon_price_trajectory[self.end_year - 1]
                        )

                        generic_discounted_cumul_em += (
                            avoided_emission_factor[self.end_year]
                            * (lhv_electrofuel * density_electrofuel)
                            / 1000000
                            * (
                                exogenous_carbon_price_trajectory[self.end_year]
                                / exogenous_carbon_price_trajectory[year]
                                * (future_scc_growth) ** (i - self.end_year)
                            )
                            / (1 + social_discount_rate) ** (i - year)
                        )

                # Using unitary values for cost and emission possible as long as the plant operates at constant capacity during its life
                # (Volume gets out of cac sums)
                specific_carbon_abatement_cost[year] = discounted_cumul_cost / cumul_em
                generic_specific_carbon_abatement_cost[year] = (
                    discounted_cumul_cost / generic_discounted_cumul_em
                )

            elif (year == self.end_year) or (
                electrofuel_production[year + 1] >= demand_scenario[year + 1] > 0
            ):
                specific_carbon_abatement_cost[year] = specific_carbon_abatement_cost[year - 1]
                generic_specific_carbon_abatement_cost[year] = (
                    generic_specific_carbon_abatement_cost[year - 1]
                )

        # MOD -> Scaling down production for diminishing production scenarios.
        # Very weak model, assuming that production not anymore needed by aviation is used elsewhere in the industry.
        # Stranded asset literature could be valuable to model this better.
        # Proportional production scaling

        scaling_factor = demand_scenario / electrofuel_production

        if not all(scaling_factor.isna()):
            electrofuel_total_cost = electrofuel_total_cost * scaling_factor
            electrofuel_capex_cost = electrofuel_capex_cost * scaling_factor
            electrofuel_opex_cost = electrofuel_opex_cost * scaling_factor
            electrofuel_elec_cost = electrofuel_elec_cost * scaling_factor
            electrofuel_co2_cost = electrofuel_co2_cost * scaling_factor

        electrofuel_mean_mfsp_litre = (
            electrofuel_total_cost
            / (demand_scenario / (lhv_electrofuel * density_electrofuel))
            * 1000000
        )

        electrofuel_mean_capex_share = electrofuel_capex_cost / electrofuel_total_cost * 100
        electrofuel_mean_opex_share = electrofuel_opex_cost / electrofuel_total_cost * 100
        electrofuel_mean_elec_share = electrofuel_elec_cost / electrofuel_total_cost * 100
        electrofuel_mean_co2_share = electrofuel_co2_cost / electrofuel_total_cost * 100

        electrofuel_cost_premium = (
            (electrofuel_mean_mfsp_litre - kerosene_market_price)
            * (demand_scenario / (lhv_electrofuel * density_electrofuel))
            / 1000000
        )

        # Compute the carbon tax (M€)
        electrofuel_carbon_tax = (
            carbon_tax * electrofuel_emission_factor * demand_scenario / 1000000 / 1000000
        )

        electrofuel_mfsp_carbon_tax_supplement = (
            carbon_tax
            * electrofuel_emission_factor
            / 1000000
            * (lhv_electrofuel * density_electrofuel)
        )
        # Abatement cost in €/tCO2e (= overcost for a ton of biofuel/avoided emissions)
        carbon_abatement_cost_electrofuel = (
            (electrofuel_mean_mfsp_litre - kerosene_market_price)
            / (avoided_emission_factor * (lhv_electrofuel * density_electrofuel))
            * 1000000
        )

        return (
            plant_building_scenario,
            plant_building_cost,
            electrofuel_total_cost,
            electrofuel_mean_capex_share,
            electrofuel_mean_opex_share,
            electrofuel_mean_elec_share,
            electrofuel_mean_co2_share,
            electrofuel_mean_mfsp_litre,
            electrofuel_cost_premium,
            electrofuel_carbon_tax,
            electrofuel_mfsp_carbon_tax_supplement,
            carbon_abatement_cost_electrofuel,
            specific_carbon_abatement_cost,
            generic_specific_carbon_abatement_cost,
        )

    def _compute_electrofuel_year_lcop(
        self,
        construction_time,
        plant_lifespan,
        base_year,
        electricity_market_price,
        co2_market_price,
        electricity_load_factor,
        electrofuel_capex,
        electrofuel_fixed_opex,
        electrofuel_var_opex,
        # electrofuel_specific_electricity,
        electrolysis_efficiency,
        electrofuel_hydrogen_efficiency,
        electrofuel_specific_co2,
        private_discount_rate,
        plant_load_fact,
        lhv_electrofuel,
        density_electrofuel,
    ):
        """
        This function computes the MFSP for electrofuel production for an plant commissioned at the base year.
        Costs are discounted to find a constant MFSP, excepted electricity, whose price is directly evolving
        from a year to another. Hydrogen production and fuel synthesis are considered a one-step process here.
        Capex in €/ (kg/day capacity)
        Fixed opex in €/ (kg/day capacity), on an annual basis
        Variable opex in € per L
        Specific electricity in kWh/L
        Specific CO2 in kg/L
        Electricity market price in €/kWh
        Electrofuel price returned in €/L
        """
        hydrogen_prices = {}

        technology_year = max(base_year, self.prospection_start_year)

        load_fact = min(plant_load_fact, electricity_load_factor[technology_year])

        real_year_days = 365.25 * load_fact
        real_var_opex = electrofuel_var_opex[technology_year] * real_year_days

        dropin_specific_energy = lhv_electrofuel * density_electrofuel / 3.6  # kWh/L

        # Electrolysis efficiency correction to remove DAC input from efficiency (Fig.2 of https://www.nature.com/articles/s41558-021-01032-7)

        electrofuel_efficiency = (
            electrolysis_efficiency
            * electrofuel_hydrogen_efficiency
            * (0.81 + 0.03 + 0.06)
            / (0.81 + 0.03)
        )

        electrofuel_specific_electricity = dropin_specific_energy / (electrofuel_efficiency)

        cap_cost_npv = 0
        fix_op_cost_npv = 0
        var_op_cost_npv = 0
        hydrogen_npv = 0

        # Construction
        for i in range(0, construction_time):
            # The construction is supposed to span over x years, with a uniform cost repartition
            cap_cost_npv += (
                electrofuel_capex[technology_year] * density_electrofuel / construction_time
            ) / (1 + private_discount_rate) ** (i)

        # commissioning
        for i in range(construction_time, plant_lifespan + construction_time):
            fix_op_cost_npv += (
                electrofuel_fixed_opex[technology_year]
                * density_electrofuel
                / (1 + private_discount_rate) ** (i)
            )
            var_op_cost_npv += real_var_opex / (1 + private_discount_rate) ** (i)
            hydrogen_npv += real_year_days / (1 + private_discount_rate) ** (i)

        cap_cost_lc = cap_cost_npv / hydrogen_npv
        fix_op_cost_lc = fix_op_cost_npv / hydrogen_npv
        var_op_cost_lc = var_op_cost_npv / hydrogen_npv

        end_bound = min(
            max(electricity_market_price.index), plant_lifespan + construction_time + base_year
        )

        for year in range(base_year + construction_time, int(end_bound) + 1):
            elec_price = electricity_market_price[year]
            elec_cost = elec_price * electrofuel_specific_electricity[technology_year]
            CO2_cost = electrofuel_specific_co2[technology_year] * co2_market_price[year]
            hydrogen_prices[year] = {
                "TOTAL": cap_cost_lc + var_op_cost_lc + fix_op_cost_lc + elec_cost + CO2_cost,
                "CAPEX": cap_cost_lc,
                "FIX_OPEX": fix_op_cost_lc,
                "VAR_OPEX": var_op_cost_lc,
                "ELECTRICITY": elec_cost,
                "CO2": CO2_cost,
            }

        return hydrogen_prices


class ElectrofuelCapex(AeroMAPSModel):
    def __init__(self, name="electrofuel_capex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrofuel_capex_reference_years: list,
        electrofuel_capex_reference_years_values: list,
    ) -> pd.Series:
        """Electrofuel capital expenditures at eis using interpolation functions"""

        electrofuel_eis_capex = AeromapsInterpolationFunction(
            self,
            electrofuel_capex_reference_years,
            electrofuel_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electrofuel_eis_capex"] = electrofuel_eis_capex

        return electrofuel_eis_capex


class ElectrofuelFixedOpex(AeroMAPSModel):
    def __init__(self, name="electrofuel_fixed_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrofuel_fixed_opex_reference_years: list,
        electrofuel_fixed_opex_reference_years_values: list,
    ) -> pd.Series:
        """Electrofuel fixed operational expenditures at entry into service using interpolation functions"""

        electrofuel_eis_fixed_opex = AeromapsInterpolationFunction(
            self,
            electrofuel_fixed_opex_reference_years,
            electrofuel_fixed_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electrofuel_eis_fixed_opex"] = electrofuel_eis_fixed_opex

        return electrofuel_eis_fixed_opex


class ElectrofuelVarOpex(AeroMAPSModel):
    def __init__(self, name="electrofuel_var_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrofuel_var_opex_reference_years: list,
        electrofuel_var_opex_reference_years_values: list,
    ) -> pd.Series:
        """Electrofuel variable operational expenditures at entry into service using interpolation functions"""

        electrofuel_eis_var_opex = AeromapsInterpolationFunction(
            self,
            electrofuel_var_opex_reference_years,
            electrofuel_var_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electrofuel_eis_var_opex"] = electrofuel_eis_var_opex

        return electrofuel_eis_var_opex


########## Deprecated for the time being, might be reactivated. ####################
#
# class ElectrofuelSpecificElectricity(AeroMAPSModel):
#
#     # changement d'usage par rapport à CAST==> on utilise pas l'efficacité moyenne pour la cons d'élec, mais
#     # l'efficacité de chaque année de mise en service de l'eclectolyseur. Permet de faire des choses plus détaillées
#     #
#     def __init__(self, name="electrofuel_specific_electricity", *args, **kwargs):
#         super().__init__(name, *args, **kwargs)
#
#     def compute(
#             self,
#             electrofuel_specific_electricity_2020: float,
#             electrofuel_specific_electricity_2030: float,
#             electrofuel_specific_electricity_2040: float,
#             electrofuel_specific_electricity_2050: float,
#     ) -> pd.Series:
#         """electrofuel efficiency at eis using interpolation functions"""
#         # FT MSW
#         reference_values_specific_electricity = [
#             electrofuel_specific_electricity_2020,
#             electrofuel_specific_electricity_2030,
#             electrofuel_specific_electricity_2040,
#             electrofuel_specific_electricity_2050
#         ]
#
#         reference_years = [2020, 2030, 2040, self.end_year]
#
#         specific_electricity_function = interp1d(
#             reference_years, reference_values_specific_electricity, kind="linear"
#         )
#         for k in range(self.prospection_start_year, self.end_year + 1):
#             self.df.loc[
#                 k, "electrofuel_eis_specific_electricity"
#             ] = specific_electricity_function(k)
#
#         electrofuel_eis_specific_electricity = self.df.loc[:, "electrofuel_eis_specific_electricity"]
#
#         return (
#             electrofuel_eis_specific_electricity
#         )
####################################################################################


class ElectrofuelSpecificCo2(AeroMAPSModel):
    # changement d'usage par rapport à CAST==> on utilise pas l'efficacité moyenne pour la cons d'élec, mais
    # l'efficacité de chaque année de mise en service de l'eclectolyseur. Permet de faire des choses plus détaillées.
    def __init__(self, name="electrofuel_specific_co2", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrofuel_specific_co2_reference_years: list,
        electrofuel_specific_co2_reference_years_values: list,
    ) -> pd.Series:
        """Electrofuel efficiency at eis using interpolation functions"""

        electrofuel_eis_specific_co2 = AeromapsInterpolationFunction(
            self,
            electrofuel_specific_co2_reference_years,
            electrofuel_specific_co2_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electrofuel_eis_specific_co2"] = electrofuel_eis_specific_co2

        return electrofuel_eis_specific_co2

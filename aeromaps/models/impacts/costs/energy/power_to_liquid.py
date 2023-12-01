# @Time : 24/02/2023 17:44
# @Author : a.salgas
# @File : power_to_liquid.py
# @Software: PyCharm

from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel, AeromapsInterpolationFunction


class ElectrofuelCost(AeromapsModel):
    def __init__(self, name="electrofuel_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_electrofuel: pd.Series = pd.Series(dtype="float64"),
        electrofuel_eis_capex: pd.Series = pd.Series(dtype="float64"),
        electrofuel_eis_fixed_opex: pd.Series = pd.Series(dtype="float64"),
        electrofuel_eis_var_opex: pd.Series = pd.Series(dtype="float64"),
        electrolysis_efficiency: pd.Series = pd.Series(dtype="float64"),
        electrofuel_hydrogen_efficiency: pd.Series = pd.Series(dtype="float64"),
        kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
        kerosene_emission_factor: pd.Series = pd.Series(dtype="float64"),
        electrofuel_emission_factor: pd.Series = pd.Series(dtype="float64"),
        electricity_market_price: pd.Series = pd.Series(dtype="float64"),
        co2_market_price: pd.Series = pd.Series(dtype="float64"),
        electrofuel_eis_specific_co2: pd.Series = pd.Series(dtype="float64"),
        electricity_load_factor: float = 0.0,
        carbon_tax: pd.Series = pd.Series(dtype="float64"),
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
    ]:

        ######## HYDROGEN PRODUCTION ########

        #### ELECTROLYSIS ####

        (
            electrofuel_plant_building_scenario,
            electrofuel_plant_building_cost,
            electrofuel_total_cost,
            electrofuel_capex_cost,
            electrofuel_opex_cost,
            electrofuel_elec_cost,
            electrofuel_co2_cost,
        ) = self.electrofuel_computation(
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
        )

        self.df.loc[:, "electrofuel_plant_building_scenario"] = electrofuel_plant_building_scenario
        self.df.loc[:, "electrofuel_plant_building_cost"] = electrofuel_plant_building_cost
        self.df.loc[:, "electrofuel_total_cost"] = electrofuel_total_cost
        self.df.loc[:, "electrofuel_capex_cost"] = electrofuel_capex_cost
        self.df.loc[:, "electrofuel_opex_cost"] = electrofuel_opex_cost
        self.df.loc[:, "electrofuel_elec_cost"] = electrofuel_elec_cost
        self.df.loc[:, "electrofuel_co2_cost"] = electrofuel_co2_cost

        ######## SYNTHESIS ########

        fuel_lhv = 35.3  # MJ/L

        # Compute the total cost premium (M€)
        electrofuel_cost_premium = (
            electrofuel_total_cost
            - (energy_consumption_electrofuel / fuel_lhv * kerosene_market_price) / 1000000
        )
        self.df.loc[:, "electrofuel_cost_premium"] = electrofuel_cost_premium

        # Average cost per L
        electrofuel_avg_cost_per_l = (
            electrofuel_total_cost / energy_consumption_electrofuel * fuel_lhv * 1000000
        )
        self.df.loc[:, "electrofuel_avg_cost_per_l"] = electrofuel_avg_cost_per_l

        # Abatement cost in €/tCO2e (= overcost for a ton of biofuel/avoided emissions)
        carbon_abatement_cost_electrofuel = (
            electrofuel_cost_premium
            * 1000000
            / energy_consumption_electrofuel
            / (kerosene_emission_factor - electrofuel_emission_factor)
            * 1000000
        )
        self.df.loc[:, "carbon_abatement_cost_electrofuel"] = carbon_abatement_cost_electrofuel

        electrofuel_carbon_tax = (
            energy_consumption_electrofuel
            * electrofuel_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        # M€
        self.df.loc[:, "electrofuel_carbon_tax"] = electrofuel_carbon_tax

        electrofuel_mfsp_carbon_tax_supplement = (
            carbon_tax * electrofuel_emission_factor / 1000000 * fuel_lhv
        )
        # €/L
        self.df.loc[
            :, "electrofuel_mfsp_carbon_tax_supplement"
        ] = electrofuel_mfsp_carbon_tax_supplement

        return (
            electrofuel_plant_building_scenario,
            electrofuel_plant_building_cost,
            electrofuel_total_cost,
            electrofuel_capex_cost,
            electrofuel_opex_cost,
            electrofuel_elec_cost,
            electrofuel_co2_cost,
            electrofuel_cost_premium,
            electrofuel_avg_cost_per_l,
            carbon_abatement_cost_electrofuel,
            electrofuel_carbon_tax,
            electrofuel_mfsp_carbon_tax_supplement,
        )

    @staticmethod
    def electrofuel_computation(
        electrofuel_eis_capex: pd.Series = pd.Series(dtype="float64"),
        electrofuel_eis_fixed_opex: pd.Series = pd.Series(dtype="float64"),
        electrofuel_eis_var_opex: pd.Series = pd.Series(dtype="float64"),
        # electrofuel_eis_specific_energy: pd.Series = pd.Series(dtype="float64"),
        electrolysis_efficiency: pd.Series = pd.Series(dtype="float64"),
        electrofuel_hydrogen_efficiency: pd.Series = pd.Series(dtype="float64"),
        electricity_market_price: pd.Series = pd.Series(dtype="float64"),
        energy_consumption_electrofuel: pd.Series = pd.Series(dtype="float64"),
        electricity_load_factor: float = 0.0,
        co2_market_price: pd.Series = pd.Series(dtype="float64"),
        electrofuel_eis_specific_co2: pd.Series = pd.Series(dtype="float64"),
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
        # Convert hydrogen demand from MJ to tons.

        kerosene_specific_energy = 43
        demand_scenario = energy_consumption_electrofuel / kerosene_specific_energy / 1000
        plant_life = 30

        # Catching the indexes from the demand scenario
        indexes = demand_scenario.index

        # Additional plant capacity building needed (in ton/day output size) for a given year
        plant_building_scenario = pd.Series(np.zeros(len(indexes)), indexes)
        # Relative CAPEX cost to build the new facilities in M€2020
        plant_building_cost = pd.Series(np.zeros(len(indexes)), indexes)
        # Annual production in tons
        electrofuel_production = pd.Series(np.zeros(len(indexes)), indexes)

        # Annual cost and cost components of hydrogen production in M€
        electrofuel_total_cost = pd.Series(np.zeros(len(indexes)), indexes)
        electrofuel_capex_cost = pd.Series(np.zeros(len(indexes)), indexes)
        electrofuel_opex_cost = pd.Series(np.zeros(len(indexes)), indexes)
        electrofuel_elec_cost = pd.Series(np.zeros(len(indexes)), indexes)
        electrofuel_co2_cost = pd.Series(np.zeros(len(indexes)), indexes)

        # For each year o²f the demand scenario the demand is matched by the production
        for year in list(demand_scenario.index)[:-1]:
            # Production missing in year n+1 must be supplied by plant build in year n
            if electrofuel_production[year + 1] < demand_scenario[year + 1]:
                # Getting the production not matched by plants already commissioned by creating an electrolyzer with year data technical data

                electrofuel_cost = ElectrofuelCost.compute_electrofuel_year_lcop(
                    year,
                    electricity_market_price,
                    co2_market_price,
                    electricity_load_factor,
                    electrofuel_eis_capex,
                    electrofuel_eis_fixed_opex,
                    electrofuel_eis_var_opex,
                    electrolysis_efficiency,
                    electrofuel_hydrogen_efficiency,
                    electrofuel_eis_specific_co2,
                )

                # Getting the production not matched by plants already commissioned
                missing_production = demand_scenario[year + 1] - electrofuel_production[year + 1]

                # Converting the missing production to a capacity (in t/day)
                electrofuel_capacity_to_build = (
                    missing_production / 365.25 / electricity_load_factor
                )  # capacity to build in t/day production, taking into account load_factor

                electrolyser_capex_year = (
                    electrofuel_capacity_to_build * electrofuel_eis_capex[year] / 1000
                )  # electrolyzer capex is in €/kg/day or m€/ton/day ==> M€/ton/day
                plant_building_cost[year] = electrolyser_capex_year
                plant_building_scenario[year] = electrofuel_capacity_to_build  # in ton/day capacity

                # When production ends: either at the end of plant life or the end of the scenario;
                end_bound = min(list(demand_scenario.index)[-1], year + plant_life)

                # Adding new plant production to future years
                for i in range(year + 1, end_bound + 1):
                    electrofuel_total_cost[i] = (
                        electrofuel_total_cost[i]
                        + (missing_production * electrofuel_cost[i]["TOTAL"]) / 1000
                    )  # €/kg and production in tons => /1000 for M€
                    electrofuel_capex_cost[i] = (
                        electrofuel_capex_cost[i]
                        + (missing_production * electrofuel_cost[i]["CAPEX"]) / 1000
                    )  # M€
                    electrofuel_opex_cost[i] = (
                        electrofuel_opex_cost[i]
                        + (missing_production * electrofuel_cost[i]["FIX_OPEX"]) / 1000
                        + (missing_production * electrofuel_cost[i]["VAR_OPEX"]) / 1000
                    )  # M€
                    electrofuel_elec_cost[i] = (
                        electrofuel_elec_cost[i]
                        + (missing_production * electrofuel_cost[i]["ELECTRICITY"]) / 1000
                    )  # M€
                    electrofuel_co2_cost[i] = (
                        electrofuel_co2_cost[i]
                        + (missing_production * electrofuel_cost[i]["CO2"]) / 1000
                    )  # M€
                    electrofuel_production[i] = electrofuel_production[i] + missing_production

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

        return (
            plant_building_scenario,
            plant_building_cost,
            electrofuel_total_cost,
            electrofuel_capex_cost,
            electrofuel_opex_cost,
            electrofuel_elec_cost,
            electrofuel_co2_cost,
        )

    @staticmethod
    def compute_electrofuel_year_lcop(
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
    ):
        """
        This function computes the MFSP for electrofuel production for an plant commissioned at the base year.
        Costs are discounted to find a constant MFSP, excepted electricity, whose price is directly evolving
        from a year to another. Hydrogen production and fuel synthesis are considered a one-step process here.
        Capex in €/ (kg/day capacity)
        Fixed opex in €/ (kg/day capacity), on an annual basis
        Variable opex in € per kg
        Specific electricity in kWh/kg
        Specific CO2 in kg/kg
        Electricity market price in €/kWh
        Electrofuel price returned in €/kg
        """
        operational_time = 30
        hydrogen_prices = {}
        construction_time = 3

        discount = 0.10
        load_fact = min(0.95, electricity_load_factor)
        real_year_days = 365.25 * load_fact
        real_var_opex = electrofuel_var_opex[base_year] * real_year_days

        fuel_lhv = 35.3
        # https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
        # fuel density at 15 degrees
        fuel_density = 0.804

        dropin_specific_energy = fuel_lhv / fuel_density / 3.6  # kWh/kg

        electrofuel_specific_electricity = dropin_specific_energy / (
            electrolysis_efficiency * electrofuel_hydrogen_efficiency
        )

        cap_cost_npv = 0
        fix_op_cost_npv = 0
        var_op_cost_npv = 0
        hydrogen_npv = 0

        # Construction
        for i in range(0, construction_time):
            # The construction is supposed to span over x years, with a uniform cost repartition
            cap_cost_npv += (electrofuel_capex[base_year] / construction_time) / (1 + discount) ** (
                i
            )

        # commissioning
        for i in range(construction_time, operational_time + construction_time):
            fix_op_cost_npv += electrofuel_fixed_opex[base_year] / (1 + discount) ** (i)
            var_op_cost_npv += real_var_opex / (1 + discount) ** (i)
            hydrogen_npv += real_year_days / (1 + discount) ** (i)

        cap_cost_lc = cap_cost_npv / hydrogen_npv
        fix_op_cost_lc = fix_op_cost_npv / hydrogen_npv
        var_op_cost_lc = var_op_cost_npv / hydrogen_npv

        end_bound = min(max(electricity_market_price.index), operational_time + base_year)

        for year in range(base_year, end_bound + 1):
            elec_price = electricity_market_price[year]
            elec_cost = elec_price * electrofuel_specific_electricity[base_year]
            CO2_cost = electrofuel_specific_co2[base_year] * co2_market_price[year]
            hydrogen_prices[year] = {
                "TOTAL": cap_cost_lc + var_op_cost_lc + fix_op_cost_lc + elec_cost + CO2_cost,
                "CAPEX": cap_cost_lc,
                "FIX_OPEX": fix_op_cost_lc,
                "VAR_OPEX": var_op_cost_lc,
                "ELECTRICITY": elec_cost,
                "CO2": CO2_cost,
            }

        return hydrogen_prices


class ElectrofuelCapex(AeromapsModel):
    def __init__(self, name="electrofuel_capex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrofuel_capex_reference_years: list = [],
        electrofuel_capex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:
        """Electrofuel capital expenditures at eis using interpolation functions"""

        electrofuel_eis_capex = AeromapsInterpolationFunction(
            self,
            electrofuel_capex_reference_years,
            electrofuel_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electrofuel_eis_capex"] = electrofuel_eis_capex

        return electrofuel_eis_capex


class ElectrofuelFixedOpex(AeromapsModel):
    def __init__(self, name="electrofuel_fixed_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrofuel_fixed_opex_reference_years: list = [],
        electrofuel_fixed_opex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:
        """Electrofuel fixed operational expenditures at entry into service using interpolation functions"""

        electrofuel_eis_fixed_opex = AeromapsInterpolationFunction(
            self,
            electrofuel_fixed_opex_reference_years,
            electrofuel_fixed_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electrofuel_eis_fixed_opex"] = electrofuel_eis_fixed_opex

        return electrofuel_eis_fixed_opex


class ElectrofuelVarOpex(AeromapsModel):
    def __init__(self, name="electrofuel_var_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrofuel_var_opex_reference_years: list = [],
        electrofuel_var_opex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:
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
# class ElectrofuelSpecificElectricity(AeromapsModel):
#
#     # changement d'usage par rapport à CAST==> on utilise pas l'efficacité moyenne pour la cons d'élec, mais
#     # l'efficacité de chaque année de mise en service de l'eclectolyseur. Permet de faire des choses plus détaillées
#     #
#     def __init__(self, name="electrofuel_specific_electricity", *args, **kwargs):
#         super().__init__(name, *args, **kwargs)
#
#     def compute(
#             self,
#             electrofuel_specific_electricity_2020: float = 0.0,
#             electrofuel_specific_electricity_2030: float = 0.0,
#             electrofuel_specific_electricity_2040: float = 0.0,
#             electrofuel_specific_electricity_2050: float = 0.0,
#     ) -> Tuple[pd.Series]:
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


class ElectrofuelSpecificCo2(AeromapsModel):

    # changement d'usage par rapport à CAST==> on utilise pas l'efficacité moyenne pour la cons d'élec, mais
    # l'efficacité de chaque année de mise en service de l'eclectolyseur. Permet de faire des choses plus détaillées.
    def __init__(self, name="electrofuel_specific_co2", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrofuel_specific_co2_reference_years: list = [],
        electrofuel_specific_co2_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:
        """Electrofuel efficiency at eis using interpolation functions"""

        electrofuel_eis_specific_co2 = AeromapsInterpolationFunction(
            self,
            electrofuel_specific_co2_reference_years,
            electrofuel_specific_co2_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electrofuel_eis_specific_co2"] = electrofuel_eis_specific_co2

        return electrofuel_eis_specific_co2

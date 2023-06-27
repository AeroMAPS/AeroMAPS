# @Time : 24/02/2023 17:42
# @Author : a.salgas
# @File : liquid_hydrogen.py
# @Software: PyCharm

# TODO :réfléchir à la facon implementer l'H2 avec toute la flexibilité dispo => ?
# TODO 2: quid de l'hydrogène bleu pour les couts -> a priori modélisation simpliste comme biofuel, utiliser les données de Parkinson et al?
# (pas prioritaire pour EASA, mais tdo avant bourget)

from typing import Tuple, Union, Any

import numpy as np
import pandas as pd
from pandas import Series

from aeromaps.models.base import AeromapsModel

from scipy.interpolate import interp1d


class LiquidHydrogenCost(AeromapsModel):
    def __init__(self, name="liquid_hydrogen_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            energy_consumption_hydrogen: pd.Series = pd.Series(dtype="float64"),
            hydrogen_electrolysis_share: pd.Series = pd.Series(dtype="float64"),
            hydrogen_gas_ccs_share: pd.Series = pd.Series(dtype="float64"),
            hydrogen_coal_ccs_share: pd.Series = pd.Series(dtype="float64"),
            hydrogen_gas_share: pd.Series = pd.Series(dtype="float64"),
            hydrogen_coal_share: pd.Series = pd.Series(dtype="float64"),
            electrolyser_eis_capex: pd.Series = pd.Series(dtype="float64"),
            electrolyser_eis_fixed_opex: pd.Series = pd.Series(dtype="float64"),
            electrolyser_eis_var_opex: pd.Series = pd.Series(dtype="float64"),
            electrolyser_eis_specific_electricity: pd.Series = pd.Series(dtype="float64"),
            liquefier_eis_capex: pd.Series = pd.Series(dtype="float64"),
            liquefier_eis_specific_electricity: pd.Series = pd.Series(dtype="float64"),
            kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
            kerosene_emission_factor: pd.Series = pd.Series(dtype="float64"),
            hydrogen_electrolysis_emission_factor: pd.Series = pd.Series(dtype="float64"),
            electricity_market_price: pd.Series = pd.Series(dtype="float64"),
            electricity_load_factor: float = 0.0,
            transport_cost_ratio: float = 0.0,
            energy_replacement_ratio: float = 1.0,
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
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series
    ]:
        ######## HYDROGEN PRODUCTION ########

        #### ELECTROLYSIS ####

        electrolysis_plant_building_scenario, \
            electrolysis_plant_building_cost, \
            electrolysis_h2_total_cost, \
            electrolysis_h2_capex_cost, \
            electrolysis_h2_opex_cost, \
            electrolysis_h2_elec_cost = self.electrolysis_computation(electrolyser_eis_capex,
                                                                      electrolyser_eis_fixed_opex,
                                                                      electrolyser_eis_var_opex,
                                                                      electrolyser_eis_specific_electricity,
                                                                      electricity_market_price,
                                                                      energy_consumption_hydrogen,
                                                                      hydrogen_electrolysis_share,
                                                                      electricity_load_factor)

        self.df.loc[:, 'electrolysis_plant_building_scenario'] = electrolysis_plant_building_scenario
        self.df.loc[:, 'electrolysis_plant_building_cost'] = electrolysis_plant_building_cost
        self.df.loc[:, 'electrolysis_h2_total_cost'] = electrolysis_h2_total_cost
        self.df.loc[:, 'electrolysis_h2_capex_cost'] = electrolysis_h2_capex_cost
        self.df.loc[:, 'electrolysis_h2_opex_cost'] = electrolysis_h2_opex_cost
        self.df.loc[:, 'electrolysis_h2_elec_cost'] = electrolysis_h2_elec_cost

        #### SMR CCS ####
        #### SMR ####
        #### COAL CCS ####
        #### COAL ####

        ######## HYDROGEN LIQUEFACTION ########
        liquefaction_plant_building_scenario, \
            liquefaction_plant_building_cost, \
            liquefaction_h2_total_cost, \
            liquefaction_h2_capex_cost, \
            liquefaction_h2_opex_cost, \
            liquefaction_h2_elec_cost = self.liquefaction_computation(liquefier_eis_capex,
                                                                      liquefier_eis_specific_electricity,
                                                                      electricity_market_price,
                                                                      energy_consumption_hydrogen)

        self.df.loc[:, 'liquefaction_plant_building_scenario'] = liquefaction_plant_building_scenario
        self.df.loc[:, 'liquefaction_plant_building_cost'] = liquefaction_plant_building_cost
        self.df.loc[:, 'liquefaction_h2_total_cost'] = liquefaction_h2_total_cost
        self.df.loc[:, 'liquefaction_h2_capex_cost'] = liquefaction_h2_capex_cost
        self.df.loc[:, 'liquefaction_h2_opex_cost'] = liquefaction_h2_opex_cost
        self.df.loc[:, 'liquefaction_h2_elec_cost'] = liquefaction_h2_elec_cost

        ######## HYDROGEN TRANSPORT ########

        transport_h2_total_cost = transport_cost_ratio * (electrolysis_h2_total_cost + liquefaction_h2_total_cost)

        self.df.loc[:, 'transport_h2_total_cost'] = transport_h2_total_cost

        ######## SYNTHESIS ########
        hydrogen_specific_energy = 119.93  # MJ/kg
        kerosene_lhv = 35.3  # MJ/L
        # energy_replacement_ratio = 1  # average energy required when hydrogen powered compared to kerosene

        h2_avg_cost_per_kg_electrolysis = (electrolysis_h2_total_cost / (
                energy_consumption_hydrogen / hydrogen_specific_energy * (hydrogen_electrolysis_share / 100))
                                           + (liquefaction_h2_total_cost + transport_h2_total_cost) / (
                                                   energy_consumption_hydrogen / hydrogen_specific_energy)) \
                                          * 1000000

        self.df.loc[:, "h2_avg_cost_per_kg_electrolysis"] = h2_avg_cost_per_kg_electrolysis
        # €/kg

        # WARNING/ to complete with other pathways once implemented !!

        total_hydrogen_supply_cost = electrolysis_h2_total_cost + liquefaction_h2_total_cost + transport_h2_total_cost
        self.df.loc[:, "total_hydrogen_supply_cost"] = total_hydrogen_supply_cost
        # M€

        total_h2_capex = electrolysis_plant_building_cost + liquefaction_plant_building_cost
        self.df.loc[:, "total_h2_capex"] = total_h2_capex
        # M€

        h2_cost_premium_electrolysis = electrolysis_h2_total_cost - \
                                       energy_consumption_hydrogen * hydrogen_electrolysis_share / 100 / energy_replacement_ratio / kerosene_lhv * kerosene_market_price / 1000000

        self.df.loc[:, "h2_cost_premium_electrolysis"] = h2_cost_premium_electrolysis
        # M€

        h2_avoided_emissions_factor = (
                    kerosene_emission_factor / energy_replacement_ratio - hydrogen_electrolysis_emission_factor)
        total_avoided_emissions = energy_consumption_hydrogen * hydrogen_electrolysis_share / 100 * h2_avoided_emissions_factor / 1000000
        # tCO2

        carbon_abatement_cost_h2_electrolysis = h2_cost_premium_electrolysis * 1000000 / total_avoided_emissions
        self.df.loc[:, 'carbon_abatement_cost_h2_electrolysis'] = carbon_abatement_cost_h2_electrolysis
        # €/t

        return (
            electrolysis_plant_building_scenario,
            electrolysis_plant_building_cost,
            electrolysis_h2_total_cost,
            electrolysis_h2_capex_cost,
            electrolysis_h2_opex_cost,
            electrolysis_h2_elec_cost,
            liquefaction_plant_building_scenario,
            liquefaction_plant_building_cost,
            liquefaction_h2_total_cost,
            liquefaction_h2_capex_cost,
            liquefaction_h2_opex_cost,
            liquefaction_h2_elec_cost,
            transport_h2_total_cost,
            h2_avg_cost_per_kg_electrolysis,
            total_hydrogen_supply_cost,
            total_h2_capex,
            h2_cost_premium_electrolysis,
            carbon_abatement_cost_h2_electrolysis
        )

    @staticmethod
    def electrolysis_computation(
            electrolyser_eis_capex: pd.Series = pd.Series(dtype="float64"),
            electrolyser_eis_fixed_opex: pd.Series = pd.Series(dtype="float64"),
            electrolyser_eis_var_opex: pd.Series = pd.Series(dtype="float64"),
            electrolyser_eis_specific_energy: pd.Series = pd.Series(dtype="float64"),
            electricity_market_price: pd.Series = pd.Series(dtype="float64"),
            energy_consumption_hydrogen: pd.Series = pd.Series(dtype="float64"),
            pathway_share: pd.Series = pd.Series(dtype="float64"),
            electricity_load_factor: float = 0.0,
    ):
        """
        Computes the yearly costs to respect a given hydrogen electrolysis production scenario.
        Capex in €/ton/day
        Fixed opex in  €/ton/day
        Variable opex in € per kg
        Specific electricity in kWh/kg
        Electricity market price in €/kWh
        Energy_consumption_hydrogen in MJ.
        Values returned are in M€ or t/day
        """
        # Convert hydrogen demand from MJ to tons.
        demand_scenario = energy_consumption_hydrogen / 119.93 / 1000 * pathway_share / 100
        plant_life = 30

        # Catching the indexes from the demand scenario
        indexes = demand_scenario.index

        # Additional plant capacity building needed (in ton/day output size) for a given year
        plant_building_scenario = pd.Series(np.zeros(len(indexes)), indexes)
        # Relative CAPEX cost to build the new facilities in M€2020
        plant_building_cost = pd.Series(np.zeros(len(indexes)), indexes)
        # Annual production in tons
        hydrogen_production = pd.Series(np.zeros(len(indexes)), indexes)

        # Annual cost and cost components of hydrogen production in M€
        h2_total_cost = pd.Series(np.zeros(len(indexes)), indexes)
        h2_capex_cost = pd.Series(np.zeros(len(indexes)), indexes)
        h2_opex_cost = pd.Series(np.zeros(len(indexes)), indexes)
        h2_elec_cost = pd.Series(np.zeros(len(indexes)), indexes)

        # For each year of the demand scenario the demand is matched by the production
        for year in list(demand_scenario.index)[:-1]:
            # Production missing in year n+1 must be supplied by plant build in year n
            if hydrogen_production[year + 1] < demand_scenario[year + 1]:
                # Getting the production not matched by plants already commissioned by creating an electrolyzer with year data technical data
                hydrogen_cost = LiquidHydrogenCost.compute_electrolyser_year_lcoh(year,
                                                                                  electricity_market_price,
                                                                                  electricity_load_factor,
                                                                                  electrolyser_eis_capex,
                                                                                  electrolyser_eis_fixed_opex,
                                                                                  electrolyser_eis_var_opex,
                                                                                  electrolyser_eis_specific_energy
                                                                                  )

                # Getting the production not matched by plants already commissioned
                missing_production = demand_scenario[year + 1] - hydrogen_production[year + 1]

                # Converting the missing production to a capacity (in t/day)
                electrolyser_capacity_to_build = missing_production / 365.25 / electricity_load_factor  # capacity to build in t/day production, taking into account load_factor

                electrolyser_capex_year = electrolyser_capacity_to_build * electrolyser_eis_capex[
                    year] / 1000  # electrolyzer capex is in €/kg/day or m€/ton/day ==> M€/ton/day
                plant_building_cost[year] = electrolyser_capex_year
                plant_building_scenario[year] = electrolyser_capacity_to_build  # in ton/day capacity

                # When production ends: either at the end of plant life or the end of the scenario;
                end_bound = min(list(demand_scenario.index)[-1], year + plant_life)

                # Adding new plant production to future years
                for i in range(year + 1, end_bound + 1):
                    h2_total_cost[i] = h2_total_cost[i] + (
                            missing_production * hydrogen_cost[i][
                        'TOTAL']) / 1000  # €/kg and production in tons => /1000 for M€
                    h2_capex_cost[i] = h2_capex_cost[i] + (
                            missing_production * hydrogen_cost[i]['CAPEX']) / 1000  # M€
                    h2_opex_cost[i] = h2_opex_cost[i] + (
                            missing_production * hydrogen_cost[i]['FIX_OPEX']) / 1000 + (
                                              missing_production * hydrogen_cost[i]['VAR_OPEX']) / 1000  # M€
                    h2_elec_cost[i] = h2_elec_cost[i] + (
                            missing_production * hydrogen_cost[i]['ELECTRICITY']) / 1000  # M€
                    hydrogen_production[i] = hydrogen_production[i] + missing_production



        return (
            plant_building_scenario,
            plant_building_cost,
            h2_total_cost,
            h2_capex_cost,
            h2_opex_cost,
            h2_elec_cost
        )

    @staticmethod
    def compute_electrolyser_year_lcoh(base_year,
                                       electricity_market_price,
                                       electricity_load_factor,
                                       electrolyser_capex,
                                       electrolyser_fixed_opex,
                                       electrolyser_var_opex,
                                       electrolyser_specific_electricity
                                       ):
        """
        This function computes the MFSP for hydrogen production for an electrolyser commissioned at the base year.
        Costs are discounted to find a constant MFSP, excepted electricity, whose price is directly evolving
        from a year to another.
        Capex in €/ (kg/day capacity)
        Fixed opex in €/ (kg/day capacity), on an annual basis
        Variable opex in € per kg
        Specific electricity in kWh/kg
        Electricity market price in €/kWh

        Hydrogen price returned in €/kg
        """

        operational_time = 30
        hydrogen_prices = {}
        construction_time = 3

        discount = 0.10
        load_fact = min(0.95, electricity_load_factor)
        real_year_days = 365.25 * load_fact
        real_var_opex = electrolyser_var_opex[base_year] * real_year_days

        cap_cost_npv = 0
        fix_op_cost_npv = 0
        var_op_cost_npv = 0
        hydrogen_npv = 0

        # Construction
        for i in range(0, construction_time):
            # The construction is supposed to span over x years, with a uniform cost repartition
            cap_cost_npv += (electrolyser_capex[base_year] / construction_time) / (1 + discount) ** (i)

        # commissioning
        for i in range(construction_time, operational_time + construction_time):
            fix_op_cost_npv += electrolyser_fixed_opex[base_year] / (1 + discount) ** (i)
            var_op_cost_npv += real_var_opex / (1 + discount) ** (i)
            hydrogen_npv += real_year_days / (1 + discount) ** (i)

        cap_cost_lc = cap_cost_npv / hydrogen_npv
        fix_op_cost_lc = fix_op_cost_npv / hydrogen_npv
        var_op_cost_lc = var_op_cost_npv / hydrogen_npv

        end_bound=min(max(electricity_market_price.index),base_year+operational_time)

        for year in range(base_year, end_bound+1):
            elec_price = electricity_market_price[year]
            elec_cost = elec_price * electrolyser_specific_electricity[base_year]
            hydrogen_prices[year] = {"TOTAL": cap_cost_lc + var_op_cost_lc + fix_op_cost_lc + elec_cost,
                                     "CAPEX": cap_cost_lc,
                                     "FIX_OPEX": fix_op_cost_lc, "VAR_OPEX": var_op_cost_lc, "ELECTRICITY": elec_cost,
                                     }
        return hydrogen_prices

    @staticmethod
    def liquefaction_computation(
            liquefier_eis_capex: pd.Series = pd.Series(dtype="float64"),
            liquefier_eis_specific_energy: pd.Series = pd.Series(dtype="float64"),
            electricity_market_price: pd.Series = pd.Series(dtype="float64"),
            energy_consumption_hydrogen: pd.Series = pd.Series(dtype="float64"),
    ):
        # Convert hydrogen demand from MJ to tons.
        demand_scenario = energy_consumption_hydrogen / 119.93 / 1000
        plant_life = 30
        plant_load_factor = 0.95

        # Catching the indexes from the demand scenario
        indexes = demand_scenario.index

        # Additional plant capacity building needed (in ton/day output size) for a given year
        plant_building_scenario = pd.Series(np.zeros(len(indexes)), indexes)
        # Relative CAPEX cost to build the new facilities in M€2020
        plant_building_cost = pd.Series(np.zeros(len(indexes)), indexes)
        # Annual production in tons
        hydrogen_production = pd.Series(np.zeros(len(indexes)), indexes)

        # Annual cost and cost components of hydrogen production in M€
        h2_total_cost = pd.Series(np.zeros(len(indexes)), indexes)
        h2_capex_cost = pd.Series(np.zeros(len(indexes)), indexes)
        h2_opex_cost = pd.Series(np.zeros(len(indexes)), indexes)
        h2_elec_cost = pd.Series(np.zeros(len(indexes)), indexes)

        # For each year of the demand scenario the demand is matched by the production
        for year in list(demand_scenario.index)[:-1]:
            # Production missing in year n+1 must be supplied by plant build in year n
            if hydrogen_production[year + 1] < demand_scenario[year + 1]:
                # Getting the production not matched by plants already commissioned by creating an electrolyzer with year data technical data

                liquefaction_cost = LiquidHydrogenCost.compute_liquefier_year_lcoh(year,
                                                                                   electricity_market_price,
                                                                                   liquefier_eis_capex,
                                                                                   liquefier_eis_specific_energy
                                                                                   )

                # Getting the production not matched by plants already commissioned
                missing_production = demand_scenario[year + 1] - hydrogen_production[year + 1]

                # Converting the missing production to a capacity (in t/day)
                liquefier_capacity_to_build = missing_production / 365.25 / plant_load_factor
                # capacity to build in t/day production, taking into account plant load_factor
                # However, considering electricity load factor is not relevant if we assume a GH2 buffer.

                liquefier_capex_year = liquefier_capacity_to_build * liquefier_eis_capex[
                    year] / 1000  # liquefier capex is in €/kg/day or m€/ton/day ==> M€/ton/day
                plant_building_cost[year] = liquefier_capex_year
                plant_building_scenario[year] = liquefier_capacity_to_build  # in ton/day capacity

                # When production ends: either at the end of plant life or the end of the scenario;
                end_bound = min(list(demand_scenario.index)[-1], year + plant_life)

                # Adding new plant production to future years
                for i in range(year + 1, end_bound + 1):
                    h2_total_cost[i] = h2_total_cost[i] + (
                            missing_production * liquefaction_cost[i]['TOTAL']) / 1000  # M€
                    h2_capex_cost[i] = h2_capex_cost[i] + (
                            missing_production * liquefaction_cost[i]['CAPEX']) / 1000  # M€
                    h2_opex_cost[i] = h2_opex_cost[i] + (
                            missing_production * liquefaction_cost[i]['FIX_OPEX']) / 1000 + (
                                              missing_production * liquefaction_cost[i]['VAR_OPEX']) / 1000  # M€
                    h2_elec_cost[i] = h2_elec_cost[i] + (
                            missing_production * liquefaction_cost[i]['ELECTRICITY']) / 1000  # M€
                    hydrogen_production[i] = hydrogen_production[i] + missing_production

        return (
            plant_building_scenario,
            plant_building_cost,
            h2_total_cost,
            h2_capex_cost,
            h2_opex_cost,
            h2_elec_cost
        )

    @staticmethod
    def compute_liquefier_year_lcoh(base_year,
                                    electricity_market_price,
                                    liquefier_capex,
                                    liquefier_specific_electricity
                                    ):
        """ This function computes the MFSP for hydrogen liquefaction for an liquefier commissioned at the base year.
        Costs are discounted to find a constant MFSP, excepted electricity, whose price is directly evolving
        from a year to another.
        """
        operational_time = 30
        liquefaction_prices = {}
        construction_time = 3

        discount = 0.10
        load_fact = 0.95
        real_year_days = 365.25 * load_fact

        cap_cost_npv = 0
        fix_op_cost_npv = 0
        hydrogen_npv = 0

        fixed_opex = 0.04 * liquefier_capex[base_year]

        # Construction
        for i in range(0, construction_time):
            # The construction is supposed to span over x years, with a uniform cost repartition
            cap_cost_npv += (liquefier_capex[base_year] / construction_time) / (1 + discount) ** (i)

        # commissioning
        for i in range(construction_time, operational_time + construction_time):
            fix_op_cost_npv += fixed_opex / (1 + discount) ** (i)
            hydrogen_npv += real_year_days / (1 + discount) ** (i)

        cap_cost_lc = cap_cost_npv / hydrogen_npv
        fix_op_cost_lc = fix_op_cost_npv / hydrogen_npv

        end_bound = min(max(electricity_market_price.index), operational_time+base_year)

        for year in range(base_year, end_bound+1):
            elec_price = electricity_market_price[year]
            elec_cost = elec_price * liquefier_specific_electricity[base_year]
            opex_var_cost = 0.05 * elec_cost
            liquefaction_prices[year] = {"TOTAL": cap_cost_lc + opex_var_cost + fix_op_cost_lc + elec_cost,
                                         "CAPEX": cap_cost_lc,
                                         "FIX_OPEX": fix_op_cost_lc, "VAR_OPEX": opex_var_cost,
                                         "ELECTRICITY": elec_cost,
                                         }

        return liquefaction_prices


class ElectrolyserCapex(AeromapsModel):
    def __init__(self, name="electrolyser_capex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            electrolyser_capex_2020: float = 0.0,
            electrolyser_capex_2030: float = 0.0,
            electrolyser_capex_2040: float = 0.0,
            electrolyser_capex_2050: float = 0.0,
    ) -> Tuple[pd.Series]:
        """Electrolyser capital expenditures at eis using interpolation functions"""
        # FT MSW
        reference_values_capex = [
            electrolyser_capex_2020,
            electrolyser_capex_2030,
            electrolyser_capex_2040,
            electrolyser_capex_2050
        ]

        reference_years = [2020, 2030, 2040, 2050]

        capex_function = interp1d(
            reference_years, reference_values_capex, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[
                k, "electrolyser_eis_capex"
            ] = capex_function(k)

        electrolyser_eis_capex = self.df.loc[:, "electrolyser_eis_capex"]

        return (
            electrolyser_eis_capex
        )


class ElectrolyserFixedOpex(AeromapsModel):
    def __init__(self, name="electrolyser_fixed_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            electrolyser_fixed_opex_2020: float = 0.0,
            electrolyser_fixed_opex_2030: float = 0.0,
            electrolyser_fixed_opex_2040: float = 0.0,
            electrolyser_fixed_opex_2050: float = 0.0,
    ) -> Tuple[pd.Series]:
        """Electrolyser fixed operational expenditures at entry into service using interpolation functions"""
        # FT MSW
        reference_values_fixed_opex = [
            electrolyser_fixed_opex_2020,
            electrolyser_fixed_opex_2030,
            electrolyser_fixed_opex_2040,
            electrolyser_fixed_opex_2050
        ]

        reference_years = [2020, 2030, 2040, 2050]

        fixed_opex_function = interp1d(
            reference_years, reference_values_fixed_opex, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[
                k, "electrolyser_eis_fixed_opex"
            ] = fixed_opex_function(k)

        electrolyser_eis_fixed_opex = self.df.loc[:, "electrolyser_eis_fixed_opex"]

        return (
            electrolyser_eis_fixed_opex
        )


class ElectrolyserVarOpex(AeromapsModel):
    def __init__(self, name="electrolyser_var_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            electrolyser_var_opex_2020: float = 0.0,
            electrolyser_var_opex_2030: float = 0.0,
            electrolyser_var_opex_2040: float = 0.0,
            electrolyser_var_opex_2050: float = 0.0,
    ) -> Tuple[pd.Series]:
        """Electrolyser variable operational expenditures at entry into service using interpolation functions"""
        # FT MSW
        reference_values_var_opex = [
            electrolyser_var_opex_2020,
            electrolyser_var_opex_2030,
            electrolyser_var_opex_2040,
            electrolyser_var_opex_2050
        ]

        reference_years = [2020, 2030, 2040, 2050]

        var_opex_function = interp1d(
            reference_years, reference_values_var_opex, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[
                k, "electrolyser_eis_var_opex"
            ] = var_opex_function(k)

        electrolyser_eis_var_opex = self.df.loc[:, "electrolyser_eis_var_opex"]

        return (
            electrolyser_eis_var_opex
        )


class ElectrolyserSpecificElectricity(AeromapsModel):

    # changement d'usage par rapport à CAST==> on utilise pas l'efficacité moyenne pour la cons d'élec, mais
    # l'efficacité de chaque année de mise en service de l'eclectolyseur. Permet de faire des choses plus détaillées.
    def __init__(self, name="electrolyser_specific_electricity", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            electrolyser_specific_electricity_2020: float = 0.0,
            electrolyser_specific_electricity_2030: float = 0.0,
            electrolyser_specific_electricity_2040: float = 0.0,
            electrolyser_specific_electricity_2050: float = 0.0,
    ) -> Tuple[pd.Series]:
        """Electrolyser efficiency at eis using interpolation functions"""
        # FT MSW
        reference_values_specific_electricity = [
            electrolyser_specific_electricity_2020,
            electrolyser_specific_electricity_2030,
            electrolyser_specific_electricity_2040,
            electrolyser_specific_electricity_2050
        ]

        reference_years = [2020, 2030, 2040, 2050]

        specific_electricity_function = interp1d(
            reference_years, reference_values_specific_electricity, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[
                k, "electrolyser_eis_specific_electricity"
            ] = specific_electricity_function(k)

        electrolyser_eis_specific_electricity = self.df.loc[:, "electrolyser_eis_specific_electricity"]

        return (
            electrolyser_eis_specific_electricity
        )


class LiquefierCapex(AeromapsModel):
    def __init__(self, name="liquefier_capex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            liquefier_capex_2020: float = 0.0,
            liquefier_capex_2030: float = 0.0,
            liquefier_capex_2040: float = 0.0,
            liquefier_capex_2050: float = 0.0,
    ) -> Tuple[pd.Series]:
        """liquefier capital expenditures at eis using interpolation functions"""
        # FT MSW
        reference_values_capex = [
            liquefier_capex_2020,
            liquefier_capex_2030,
            liquefier_capex_2040,
            liquefier_capex_2050
        ]

        reference_years = [2020, 2030, 2040, 2050]

        capex_function = interp1d(
            reference_years, reference_values_capex, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[
                k, "liquefier_eis_capex"
            ] = capex_function(k)

        liquefier_eis_capex = self.df.loc[:, "liquefier_eis_capex"]

        return (
            liquefier_eis_capex
        )


class LiquefierSpecificElectricity(AeromapsModel):

    # changement d'usage par rapport à CAST==> on utilise pas l'efficacité moyenne pour la cons d'élec, mais
    # l'efficacité de chaque année de mise en service de l'eclectolyseur. Permet de faire des choses plus détaillées.
    def __init__(self, name="liquefier_specific_electricity", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            liquefier_specific_electricity_2020: float = 0.0,
            liquefier_specific_electricity_2030: float = 0.0,
            liquefier_specific_electricity_2040: float = 0.0,
            liquefier_specific_electricity_2050: float = 0.0,
    ) -> Tuple[pd.Series]:
        """liquefier efficiency at eis using interpolation functions"""
        # FT MSW
        reference_values_specific_electricity = [
            liquefier_specific_electricity_2020,
            liquefier_specific_electricity_2030,
            liquefier_specific_electricity_2040,
            liquefier_specific_electricity_2050
        ]

        reference_years = [2020, 2030, 2040, 2050]

        specific_electricity_function = interp1d(
            reference_years, reference_values_specific_electricity, kind="linear"
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[
                k, "liquefier_eis_specific_electricity"
            ] = specific_electricity_function(k)

        liquefier_eis_specific_electricity = self.df.loc[:, "liquefier_eis_specific_electricity"]

        return (
            liquefier_eis_specific_electricity
        )

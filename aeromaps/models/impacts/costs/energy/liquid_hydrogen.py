# @Time : 24/02/2023 17:42
# @Author : a.salgas
# @File : liquid_hydrogen.py
# @Software: PyCharm


from typing import Tuple, Union, Any

import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel, AeromapsInterpolationFunction


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
        electrolysis_h2_eis_capex: pd.Series = pd.Series(dtype="float64"),
        electrolysis_h2_eis_fixed_opex: pd.Series = pd.Series(dtype="float64"),
        electrolysis_h2_eis_var_opex: pd.Series = pd.Series(dtype="float64"),
        electrolysis_efficiency: pd.Series = pd.Series(dtype="float64"),
        gas_ccs_eis_capex: pd.Series = pd.Series(dtype="float64"),
        gas_ccs_eis_fixed_opex: pd.Series = pd.Series(dtype="float64"),
        gas_ccs_efficiency: pd.Series = pd.Series(dtype="float64"),
        gas_ccs_load_factor: float = 0.0,
        hydrogen_gas_ccs_emission_factor: float = 0.0,
        gas_ccs_ccs_efficiency: float = 0.0,
        gas_eis_capex: pd.Series = pd.Series(dtype="float64"),
        gas_eis_fixed_opex: pd.Series = pd.Series(dtype="float64"),
        gas_efficiency: pd.Series = pd.Series(dtype="float64"),
        gas_load_factor: float = 0.0,
        hydrogen_gas_emission_factor: float = 0.0,
        coal_ccs_eis_capex: pd.Series = pd.Series(dtype="float64"),
        coal_ccs_eis_fixed_opex: pd.Series = pd.Series(dtype="float64"),
        coal_ccs_efficiency: pd.Series = pd.Series(dtype="float64"),
        coal_ccs_load_factor: float = 0.0,
        hydrogen_coal_ccs_emission_factor: float = 0.0,
        coal_ccs_ccs_efficiency: float = 0.0,
        coal_eis_capex: pd.Series = pd.Series(dtype="float64"),
        coal_eis_fixed_opex: pd.Series = pd.Series(dtype="float64"),
        coal_efficiency: pd.Series = pd.Series(dtype="float64"),
        coal_load_factor: float = 0.0,
        hydrogen_coal_emission_factor: float = 0.0,
        liquefier_eis_capex: pd.Series = pd.Series(dtype="float64"),
        liquefaction_efficiency: pd.Series = pd.Series(dtype="float64"),
        kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
        kerosene_emission_factor: pd.Series = pd.Series(dtype="float64"),
        hydrogen_electrolysis_emission_factor: pd.Series = pd.Series(dtype="float64"),
        electricity_market_price: pd.Series = pd.Series(dtype="float64"),
        gas_market_price: pd.Series = pd.Series(dtype="float64"),
        coal_market_price: pd.Series = pd.Series(dtype="float64"),
        ccs_cost: pd.Series = pd.Series(dtype="float64"),
        electricity_load_factor: float = 0.0,
        transport_cost_ratio: float = 0.0,
        energy_replacement_ratio: float = 1.0,
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
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        ######## HYDROGEN PRODUCTION ########

        #### ELECTROLYSIS ####
        (
            electrolysis_plant_building_scenario,
            electrolysis_plant_building_cost,
            electrolysis_h2_total_cost,
            electrolysis_h2_capex_cost,
            electrolysis_h2_opex_cost,
            electrolysis_h2_elec_cost,
        ) = self.electrolysis_computation(
            electrolysis_h2_eis_capex,
            electrolysis_h2_eis_fixed_opex,
            electrolysis_h2_eis_var_opex,
            electrolysis_efficiency,
            electricity_market_price,
            energy_consumption_hydrogen,
            hydrogen_electrolysis_share,
            electricity_load_factor,
        )

        self.df.loc[
            :, "electrolysis_plant_building_scenario"
        ] = electrolysis_plant_building_scenario
        self.df.loc[:, "electrolysis_plant_building_cost"] = electrolysis_plant_building_cost
        self.df.loc[:, "electrolysis_h2_total_cost"] = electrolysis_h2_total_cost
        self.df.loc[:, "electrolysis_h2_capex_cost"] = electrolysis_h2_capex_cost
        self.df.loc[:, "electrolysis_h2_opex_cost"] = electrolysis_h2_opex_cost
        self.df.loc[:, "electrolysis_h2_elec_cost"] = electrolysis_h2_elec_cost

        #### GAS CCS ####

        (
            gas_ccs_plant_building_scenario,
            gas_ccs_plant_building_cost,
            gas_ccs_h2_total_cost,
            gas_ccs_h2_capex_cost,
            gas_ccs_h2_opex_cost,
            gas_ccs_h2_fuel_cost,
            gas_ccs_h2_ccs_cost,
        ) = self.fossil_computation(
            gas_ccs_eis_capex,
            gas_ccs_eis_fixed_opex,
            # gas_ccs_eis_var_opex,
            gas_ccs_efficiency,
            gas_market_price,
            ccs_cost,
            energy_consumption_hydrogen,
            hydrogen_gas_ccs_share,
            gas_ccs_load_factor,
            hydrogen_gas_ccs_emission_factor,
            gas_ccs_ccs_efficiency,
        )

        self.df.loc[:, "gas_ccs_plant_building_scenario"] = gas_ccs_plant_building_scenario
        self.df.loc[:, "gas_ccs_plant_building_cost"] = gas_ccs_plant_building_cost
        self.df.loc[:, "gas_ccs_h2_total_cost"] = gas_ccs_h2_total_cost
        self.df.loc[:, "gas_ccs_h2_capex_cost"] = gas_ccs_h2_capex_cost
        self.df.loc[:, "gas_ccs_h2_opex_cost"] = gas_ccs_h2_opex_cost
        self.df.loc[:, "gas_ccs_h2_fuel_cost"] = gas_ccs_h2_fuel_cost
        self.df.loc[:, "gas_ccs_h2_ccs_cost"] = gas_ccs_h2_ccs_cost

        #### GAS ####

        (
            gas_plant_building_scenario,
            gas_plant_building_cost,
            gas_h2_total_cost,
            gas_h2_capex_cost,
            gas_h2_opex_cost,
            gas_h2_fuel_cost,
            gas_h2_cost,
        ) = self.fossil_computation(
            gas_eis_capex,
            gas_eis_fixed_opex,
            # gas_eis_var_opex,
            gas_efficiency,
            gas_market_price,
            ccs_cost,
            energy_consumption_hydrogen,
            hydrogen_gas_share,
            gas_load_factor,
            hydrogen_gas_emission_factor,
            0,
        )

        self.df.loc[:, "gas_plant_building_scenario"] = gas_plant_building_scenario
        self.df.loc[:, "gas_plant_building_cost"] = gas_plant_building_cost
        self.df.loc[:, "gas_h2_total_cost"] = gas_h2_total_cost
        self.df.loc[:, "gas_h2_capex_cost"] = gas_h2_capex_cost
        self.df.loc[:, "gas_h2_opex_cost"] = gas_h2_opex_cost
        self.df.loc[:, "gas_h2_fuel_cost"] = gas_h2_fuel_cost

        #### COAL CCS ####

        (
            coal_ccs_plant_building_scenario,
            coal_ccs_plant_building_cost,
            coal_ccs_h2_total_cost,
            coal_ccs_h2_capex_cost,
            coal_ccs_h2_opex_cost,
            coal_ccs_h2_fuel_cost,
            coal_ccs_h2_ccs_cost,
        ) = self.fossil_computation(
            coal_ccs_eis_capex,
            coal_ccs_eis_fixed_opex,
            # coal_ccs_eis_var_opex,
            coal_ccs_efficiency,
            coal_market_price,
            ccs_cost,
            energy_consumption_hydrogen,
            hydrogen_coal_ccs_share,
            coal_ccs_load_factor,
            hydrogen_coal_ccs_emission_factor,
            coal_ccs_ccs_efficiency,
        )

        self.df.loc[:, "coal_ccs_plant_building_scenario"] = coal_ccs_plant_building_scenario
        self.df.loc[:, "coal_ccs_plant_building_cost"] = coal_ccs_plant_building_cost
        self.df.loc[:, "coal_ccs_h2_total_cost"] = coal_ccs_h2_total_cost
        self.df.loc[:, "coal_ccs_h2_capex_cost"] = coal_ccs_h2_capex_cost
        self.df.loc[:, "coal_ccs_h2_opex_cost"] = coal_ccs_h2_opex_cost
        self.df.loc[:, "coal_ccs_h2_fuel_cost"] = coal_ccs_h2_fuel_cost
        self.df.loc[:, "coal_ccs_h2_ccs_cost"] = coal_ccs_h2_ccs_cost

        #### COAL ####

        (
            coal_plant_building_scenario,
            coal_plant_building_cost,
            coal_h2_total_cost,
            coal_h2_capex_cost,
            coal_h2_opex_cost,
            coal_h2_fuel_cost,
            coal_h2_cost,
        ) = self.fossil_computation(
            coal_eis_capex,
            coal_eis_fixed_opex,
            # coal_eis_var_opex,
            coal_efficiency,
            coal_market_price,
            ccs_cost,
            energy_consumption_hydrogen,
            hydrogen_coal_share,
            coal_load_factor,
            hydrogen_coal_emission_factor,
            0,
        )

        self.df.loc[:, "coal_plant_building_scenario"] = coal_plant_building_scenario
        self.df.loc[:, "coal_plant_building_cost"] = coal_plant_building_cost
        self.df.loc[:, "coal_h2_total_cost"] = coal_h2_total_cost
        self.df.loc[:, "coal_h2_capex_cost"] = coal_h2_capex_cost
        self.df.loc[:, "coal_h2_opex_cost"] = coal_h2_opex_cost
        self.df.loc[:, "coal_h2_fuel_cost"] = coal_h2_fuel_cost

        ######## HYDROGEN LIQUEFACTION ########

        (
            liquefaction_plant_building_scenario,
            liquefaction_plant_building_cost,
            liquefaction_h2_total_cost,
            liquefaction_h2_capex_cost,
            liquefaction_h2_opex_cost,
            liquefaction_h2_elec_cost,
        ) = self.liquefaction_computation(
            liquefier_eis_capex,
            liquefaction_efficiency,
            electricity_market_price,
            energy_consumption_hydrogen,
        )

        self.df.loc[
            :, "liquefaction_plant_building_scenario"
        ] = liquefaction_plant_building_scenario
        self.df.loc[:, "liquefaction_plant_building_cost"] = liquefaction_plant_building_cost
        self.df.loc[:, "liquefaction_h2_total_cost"] = liquefaction_h2_total_cost
        self.df.loc[:, "liquefaction_h2_capex_cost"] = liquefaction_h2_capex_cost
        self.df.loc[:, "liquefaction_h2_opex_cost"] = liquefaction_h2_opex_cost
        self.df.loc[:, "liquefaction_h2_elec_cost"] = liquefaction_h2_elec_cost

        ######## HYDROGEN TRANSPORT ########

        transport_h2_total_cost = transport_cost_ratio * (
            electrolysis_h2_total_cost.fillna(0)
            + gas_ccs_h2_total_cost.fillna(0)
            + gas_h2_total_cost.fillna(0)
            + coal_ccs_h2_total_cost.fillna(0)
            + coal_h2_total_cost.fillna(0)
            + liquefaction_h2_total_cost.fillna(0)
        )

        self.df.loc[:, "transport_h2_total_cost"] = transport_h2_total_cost

        ######## SYNTHESIS ########
        hydrogen_specific_energy = 119.93  # MJ/kg
        kerosene_lhv = 35.3  # MJ/L
        # energy_replacement_ratio = 1  # average energy required when hydrogen powered compared to kerosene

        # compute average costs per kg for each pathway

        h2_avg_cost_per_kg_electrolysis = (
            electrolysis_h2_total_cost
            / (
                energy_consumption_hydrogen
                / hydrogen_specific_energy
                * (hydrogen_electrolysis_share / 100)
            )
            + (liquefaction_h2_total_cost + transport_h2_total_cost)
            / (energy_consumption_hydrogen / hydrogen_specific_energy)
        ) * 1000000

        self.df.loc[:, "h2_avg_cost_per_kg_electrolysis"] = h2_avg_cost_per_kg_electrolysis
        # €/kg

        h2_avg_cost_per_kg_gas_ccs = (
            gas_ccs_h2_total_cost
            / (
                energy_consumption_hydrogen
                / hydrogen_specific_energy
                * (hydrogen_gas_ccs_share / 100)
            )
            + (liquefaction_h2_total_cost + transport_h2_total_cost)
            / (energy_consumption_hydrogen / hydrogen_specific_energy)
        ) * 1000000

        self.df.loc[:, "h2_avg_cost_per_kg_gas_ccs"] = h2_avg_cost_per_kg_gas_ccs
        # €/kg

        h2_avg_cost_per_kg_gas = (
            gas_h2_total_cost
            / (energy_consumption_hydrogen / hydrogen_specific_energy * (hydrogen_gas_share / 100))
            + (liquefaction_h2_total_cost + transport_h2_total_cost)
            / (energy_consumption_hydrogen / hydrogen_specific_energy)
        ) * 1000000

        self.df.loc[:, "h2_avg_cost_per_kg_gas"] = h2_avg_cost_per_kg_gas
        # €/kg

        h2_avg_cost_per_kg_coal_ccs = (
            coal_ccs_h2_total_cost
            / (
                energy_consumption_hydrogen
                / hydrogen_specific_energy
                * (hydrogen_coal_ccs_share / 100)
            )
            + (liquefaction_h2_total_cost + transport_h2_total_cost)
            / (energy_consumption_hydrogen / hydrogen_specific_energy)
        ) * 1000000

        self.df.loc[:, "h2_avg_cost_per_kg_coal_ccs"] = h2_avg_cost_per_kg_coal_ccs
        # €/kg

        h2_avg_cost_per_kg_coal = (
            coal_h2_total_cost
            / (energy_consumption_hydrogen / hydrogen_specific_energy * (hydrogen_coal_share / 100))
            + (liquefaction_h2_total_cost + transport_h2_total_cost)
            / (energy_consumption_hydrogen / hydrogen_specific_energy)
        ) * 1000000

        self.df.loc[:, "h2_avg_cost_per_kg_coal"] = h2_avg_cost_per_kg_coal
        # €/kg

        total_hydrogen_supply_cost = (
            electrolysis_h2_total_cost.fillna(0)
            + gas_ccs_h2_total_cost.fillna(0)
            + gas_h2_total_cost.fillna(0)
            + coal_ccs_h2_total_cost.fillna(0)
            + coal_h2_total_cost.fillna(0)
            + liquefaction_h2_total_cost.fillna(0)
            + transport_h2_total_cost.fillna(0)
        )

        self.df.loc[:, "total_hydrogen_supply_cost"] = total_hydrogen_supply_cost
        # M€

        h2_avg_cost_per_kg = (
            total_hydrogen_supply_cost
            / (energy_consumption_hydrogen / hydrogen_specific_energy)
            * 1000000
        )
        self.df.loc[:, "h2_avg_cost_per_kg"] = h2_avg_cost_per_kg
        # €/kg

        total_h2_building_cost = (
            electrolysis_plant_building_cost.fillna(0)
            + gas_ccs_plant_building_cost.fillna(0)
            + gas_plant_building_cost.fillna(0)
            + coal_ccs_plant_building_cost.fillna(0)
            + coal_plant_building_cost.fillna(0)
            + liquefaction_plant_building_cost.fillna(0)
        )

        self.df.loc[:, "total_h2_building_cost"] = total_h2_building_cost
        # M€

        # Compute Cost premiums, abatements costs and carbon tax for each pathway

        #### ELECTROLYSIS ####
        h2_cost_premium_electrolysis = (
            electrolysis_h2_total_cost
            + (liquefaction_h2_total_cost + transport_h2_total_cost)
            * hydrogen_electrolysis_share
            / 100
            - energy_consumption_hydrogen
            * hydrogen_electrolysis_share
            / 100
            / energy_replacement_ratio
            / kerosene_lhv
            * kerosene_market_price
            / 1000000
        )

        self.df.loc[:, "h2_cost_premium_electrolysis"] = h2_cost_premium_electrolysis
        # M€

        h2_avoided_emissions_factor = (
            kerosene_emission_factor / energy_replacement_ratio
            - hydrogen_electrolysis_emission_factor
        )
        total_avoided_emissions = (
            energy_consumption_hydrogen
            * hydrogen_electrolysis_share
            / 100
            * h2_avoided_emissions_factor
            / 1000000
        )
        # tCO2

        carbon_abatement_cost_h2_electrolysis = (
            h2_cost_premium_electrolysis * 1000000 / total_avoided_emissions
        )
        self.df.loc[
            :, "carbon_abatement_cost_h2_electrolysis"
        ] = carbon_abatement_cost_h2_electrolysis
        # €/t

        electrolysis_h2_carbon_tax = (
            energy_consumption_hydrogen
            * hydrogen_electrolysis_share
            / 100
            * hydrogen_electrolysis_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        # M€
        self.df.loc[:, "electrolysis_h2_carbon_tax"] = electrolysis_h2_carbon_tax

        electrolysis_h2_mfsp_carbon_tax_supplement = (
            carbon_tax * hydrogen_electrolysis_emission_factor / 1000000 * hydrogen_specific_energy
        )
        # €/kg_H2
        self.df.loc[
            :, "electrolysis_h2_mfsp_carbon_tax_supplement"
        ] = electrolysis_h2_mfsp_carbon_tax_supplement

        #### GAS CCS ####
        h2_cost_premium_gas_ccs = (
            gas_ccs_h2_total_cost
            + (liquefaction_h2_total_cost + transport_h2_total_cost) * hydrogen_gas_ccs_share / 100
            - energy_consumption_hydrogen
            * hydrogen_gas_ccs_share
            / 100
            / energy_replacement_ratio
            / kerosene_lhv
            * kerosene_market_price
            / 1000000
        )

        self.df.loc[:, "h2_cost_premium_gas_ccs"] = h2_cost_premium_gas_ccs
        # M€

        h2_avoided_emissions_factor = (
            kerosene_emission_factor / energy_replacement_ratio - hydrogen_gas_ccs_emission_factor
        )
        total_avoided_emissions = (
            energy_consumption_hydrogen
            * hydrogen_gas_ccs_share
            / 100
            * h2_avoided_emissions_factor
            / 1000000
        )
        # tCO2

        carbon_abatement_cost_h2_gas_ccs = (
            h2_cost_premium_gas_ccs * 1000000 / total_avoided_emissions
        )
        self.df.loc[:, "carbon_abatement_cost_h2_gas_ccs"] = carbon_abatement_cost_h2_gas_ccs
        # €/t

        gas_ccs_h2_carbon_tax = (
            energy_consumption_hydrogen
            * hydrogen_gas_ccs_share
            / 100
            * hydrogen_gas_ccs_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        # M€
        self.df.loc[:, "gas_ccs_h2_carbon_tax"] = gas_ccs_h2_carbon_tax

        gas_ccs_h2_mfsp_carbon_tax_supplement = (
            carbon_tax * hydrogen_gas_ccs_emission_factor / 1000000 * hydrogen_specific_energy
        )
        # €/kg_H2
        self.df.loc[
            :, "gas_ccs_h2_mfsp_carbon_tax_supplement"
        ] = gas_ccs_h2_mfsp_carbon_tax_supplement

        #### GAS ####
        h2_cost_premium_gas = (
            gas_h2_total_cost
            + (liquefaction_h2_total_cost + transport_h2_total_cost) * hydrogen_gas_share / 100
            - energy_consumption_hydrogen
            * hydrogen_gas_share
            / 100
            / energy_replacement_ratio
            / kerosene_lhv
            * kerosene_market_price
            / 1000000
        )

        self.df.loc[:, "h2_cost_premium_gas"] = h2_cost_premium_gas
        # M€

        h2_avoided_emissions_factor = (
            kerosene_emission_factor / energy_replacement_ratio - hydrogen_gas_emission_factor
        )
        total_avoided_emissions = (
            energy_consumption_hydrogen
            * hydrogen_gas_share
            / 100
            * h2_avoided_emissions_factor
            / 1000000
        )
        # tCO2

        carbon_abatement_cost_h2_gas = h2_cost_premium_gas * 1000000 / total_avoided_emissions
        self.df.loc[:, "carbon_abatement_cost_h2_gas"] = carbon_abatement_cost_h2_gas
        # €/t

        gas_h2_carbon_tax = (
            energy_consumption_hydrogen
            * hydrogen_gas_share
            / 100
            * hydrogen_gas_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        # M€
        self.df.loc[:, "gas_h2_carbon_tax"] = gas_h2_carbon_tax

        gas_h2_mfsp_carbon_tax_supplement = (
            carbon_tax * hydrogen_gas_emission_factor / 1000000 * hydrogen_specific_energy
        )
        # €/kg_H2
        self.df.loc[:, "gas_h2_mfsp_carbon_tax_supplement"] = gas_h2_mfsp_carbon_tax_supplement

        #### COAL CCS ####
        h2_cost_premium_coal_ccs = (
            coal_ccs_h2_total_cost
            + (liquefaction_h2_total_cost + transport_h2_total_cost) * hydrogen_coal_ccs_share / 100
            - energy_consumption_hydrogen
            * hydrogen_coal_ccs_share
            / 100
            / energy_replacement_ratio
            / kerosene_lhv
            * kerosene_market_price
            / 1000000
        )

        self.df.loc[:, "h2_cost_premium_coal_ccs"] = h2_cost_premium_coal_ccs
        # M€

        h2_avoided_emissions_factor = (
            kerosene_emission_factor / energy_replacement_ratio - hydrogen_coal_ccs_emission_factor
        )
        total_avoided_emissions = (
            energy_consumption_hydrogen
            * hydrogen_coal_ccs_share
            / 100
            * h2_avoided_emissions_factor
            / 1000000
        )
        # tCO2

        carbon_abatement_cost_h2_coal_ccs = (
            h2_cost_premium_coal_ccs * 1000000 / total_avoided_emissions
        )
        self.df.loc[:, "carbon_abatement_cost_h2_coal_ccs"] = carbon_abatement_cost_h2_coal_ccs
        # €/t

        coal_ccs_h2_carbon_tax = (
            energy_consumption_hydrogen
            * hydrogen_coal_ccs_share
            / 100
            * hydrogen_coal_ccs_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        # M€
        self.df.loc[:, "coal_ccs_h2_carbon_tax"] = coal_ccs_h2_carbon_tax

        coal_ccs_h2_mfsp_carbon_tax_supplement = (
            carbon_tax * hydrogen_coal_ccs_emission_factor / 1000000 * hydrogen_specific_energy
        )
        # €/kg_H2
        self.df.loc[
            :, "coal_ccs_h2_mfsp_carbon_tax_supplement"
        ] = coal_ccs_h2_mfsp_carbon_tax_supplement

        #### COAL ####
        h2_cost_premium_coal = (
            coal_h2_total_cost
            + (liquefaction_h2_total_cost + transport_h2_total_cost) * hydrogen_coal_share / 100
            - energy_consumption_hydrogen
            * hydrogen_coal_share
            / 100
            / energy_replacement_ratio
            / kerosene_lhv
            * kerosene_market_price
            / 1000000
        )

        self.df.loc[:, "h2_cost_premium_coal"] = h2_cost_premium_coal
        # M€

        h2_avoided_emissions_factor = (
            kerosene_emission_factor / energy_replacement_ratio - hydrogen_coal_emission_factor
        )
        total_avoided_emissions = (
            energy_consumption_hydrogen
            * hydrogen_coal_share
            / 100
            * h2_avoided_emissions_factor
            / 1000000
        )
        # tCO2

        carbon_abatement_cost_h2_coal = h2_cost_premium_coal * 1000000 / total_avoided_emissions
        self.df.loc[:, "carbon_abatement_cost_h2_coal"] = carbon_abatement_cost_h2_coal
        # €/t

        coal_h2_carbon_tax = (
            energy_consumption_hydrogen
            * hydrogen_coal_share
            / 100
            * hydrogen_coal_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        # M€
        self.df.loc[:, "coal_h2_carbon_tax"] = coal_h2_carbon_tax

        coal_h2_mfsp_carbon_tax_supplement = (
            carbon_tax * hydrogen_coal_emission_factor / 1000000 * hydrogen_specific_energy
        )
        # €/kg_H2
        self.df.loc[:, "coal_h2_mfsp_carbon_tax_supplement"] = coal_h2_mfsp_carbon_tax_supplement

        h2_avg_carbon_tax_per_kg = (
            (
                electrolysis_h2_carbon_tax.fillna(0)
                + gas_h2_carbon_tax.fillna(0)
                + gas_ccs_h2_carbon_tax.fillna(0)
                + coal_h2_carbon_tax.fillna(0)
                + coal_ccs_h2_carbon_tax.fillna(0)
            )
            / (energy_consumption_hydrogen / hydrogen_specific_energy)
            * 1000000
        )
        self.df.loc[:, "h2_avg_carbon_tax_per_kg"] = h2_avg_carbon_tax_per_kg
        # €/kg

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
            h2_avg_cost_per_kg,
            total_h2_building_cost,
            h2_cost_premium_electrolysis,
            carbon_abatement_cost_h2_electrolysis,
            electrolysis_h2_carbon_tax,
            electrolysis_h2_mfsp_carbon_tax_supplement,
            gas_ccs_plant_building_scenario,
            gas_ccs_plant_building_cost,
            gas_ccs_h2_total_cost,
            gas_ccs_h2_capex_cost,
            gas_ccs_h2_opex_cost,
            gas_ccs_h2_fuel_cost,
            gas_ccs_h2_ccs_cost,
            gas_plant_building_scenario,
            gas_plant_building_cost,
            gas_h2_total_cost,
            gas_h2_capex_cost,
            gas_h2_opex_cost,
            gas_h2_fuel_cost,
            coal_ccs_plant_building_scenario,
            coal_ccs_plant_building_cost,
            coal_ccs_h2_total_cost,
            coal_ccs_h2_capex_cost,
            coal_ccs_h2_opex_cost,
            coal_ccs_h2_fuel_cost,
            coal_ccs_h2_ccs_cost,
            coal_plant_building_scenario,
            coal_plant_building_cost,
            coal_h2_total_cost,
            coal_h2_capex_cost,
            coal_h2_opex_cost,
            coal_h2_fuel_cost,
            h2_avg_cost_per_kg_gas_ccs,
            h2_avg_cost_per_kg_gas,
            h2_avg_cost_per_kg_coal_ccs,
            h2_avg_cost_per_kg_coal,
            h2_cost_premium_gas_ccs,
            carbon_abatement_cost_h2_gas_ccs,
            gas_ccs_h2_carbon_tax,
            gas_ccs_h2_mfsp_carbon_tax_supplement,
            h2_cost_premium_gas,
            carbon_abatement_cost_h2_gas,
            gas_h2_carbon_tax,
            gas_h2_mfsp_carbon_tax_supplement,
            h2_cost_premium_coal_ccs,
            carbon_abatement_cost_h2_coal_ccs,
            coal_ccs_h2_carbon_tax,
            coal_ccs_h2_mfsp_carbon_tax_supplement,
            h2_cost_premium_coal,
            carbon_abatement_cost_h2_coal,
            coal_h2_carbon_tax,
            coal_h2_mfsp_carbon_tax_supplement,
            h2_avg_carbon_tax_per_kg,
        )

    @staticmethod
    def electrolysis_computation(
        electrolysis_h2_eis_capex: pd.Series = pd.Series(dtype="float64"),
        electrolysis_h2_eis_fixed_opex: pd.Series = pd.Series(dtype="float64"),
        electrolysis_h2_eis_var_opex: pd.Series = pd.Series(dtype="float64"),
        electrolysis_efficiency: pd.Series = pd.Series(dtype="float64"),
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
                hydrogen_cost = LiquidHydrogenCost.compute_electrolyser_year_lcoh(
                    year,
                    electricity_market_price,
                    electricity_load_factor,
                    electrolysis_h2_eis_capex,
                    electrolysis_h2_eis_fixed_opex,
                    electrolysis_h2_eis_var_opex,
                    electrolysis_efficiency,
                )

                # Getting the production not matched by plants already commissioned
                missing_production = demand_scenario[year + 1] - hydrogen_production[year + 1]

                # Converting the missing production to a capacity (in t/day)
                electrolyser_capacity_to_build = (
                    missing_production / 365.25 / electricity_load_factor
                )  # capacity to build in t/day production, taking into account load_factor

                electrolyser_capex_year = (
                    electrolyser_capacity_to_build * electrolysis_h2_eis_capex[year] / 1000
                )  # electrolyzer capex is in €/kg/day or m€/ton/day ==> M€/ton/day
                plant_building_cost[year] = electrolyser_capex_year
                plant_building_scenario[
                    year
                ] = electrolyser_capacity_to_build  # in ton/day capacity

                # When production ends: either at the end of plant life or the end of the scenario;
                end_bound = min(list(demand_scenario.index)[-1], year + plant_life)

                # Adding new plant production to future years
                for i in range(year + 1, end_bound + 1):
                    h2_total_cost[i] = (
                        h2_total_cost[i] + (missing_production * hydrogen_cost[i]["TOTAL"]) / 1000
                    )  # €/kg and production in tons => /1000 for M€
                    h2_capex_cost[i] = (
                        h2_capex_cost[i] + (missing_production * hydrogen_cost[i]["CAPEX"]) / 1000
                    )  # M€
                    h2_opex_cost[i] = (
                        h2_opex_cost[i]
                        + (missing_production * hydrogen_cost[i]["FIX_OPEX"]) / 1000
                        + (missing_production * hydrogen_cost[i]["VAR_OPEX"]) / 1000
                    )  # M€
                    h2_elec_cost[i] = (
                        h2_elec_cost[i]
                        + (missing_production * hydrogen_cost[i]["ELECTRICITY"]) / 1000
                    )  # M€
                    hydrogen_production[i] = hydrogen_production[i] + missing_production

        # MOD -> Scaling down production for diminishing production scenarios.
        # Very weak model, assuming that production not anymore needed by aviation is used elsewhere in the industry.
        # Stranded asset literature could be valuable to model this better.
        # Proportional production scaling

        scaling_factor = demand_scenario / hydrogen_production

        if not all(scaling_factor.isna()):
            h2_total_cost = h2_total_cost * scaling_factor
            h2_capex_cost = h2_capex_cost * scaling_factor
            h2_opex_cost = h2_opex_cost * scaling_factor
            h2_elec_cost = h2_elec_cost * scaling_factor

        return (
            plant_building_scenario,
            plant_building_cost,
            h2_total_cost,
            h2_capex_cost,
            h2_opex_cost,
            h2_elec_cost,
        )

    @staticmethod
    def compute_electrolyser_year_lcoh(
        base_year,
        electricity_market_price,
        electricity_load_factor,
        electrolyser_capex,
        electrolyser_fixed_opex,
        electrolyser_var_opex,
        plant_efficiency,
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

        hydrogen_specific_energy = 119.93 / 3.6  # kWh/kg
        # compute plant specific energy #kWh energy/kg h2
        electrolyser_specific_electricity = hydrogen_specific_energy / plant_efficiency

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
            cap_cost_npv += (electrolyser_capex[base_year] / construction_time) / (
                1 + discount
            ) ** (i)

        # commissioning
        for i in range(construction_time, operational_time + construction_time):
            fix_op_cost_npv += electrolyser_fixed_opex[base_year] / (1 + discount) ** (i)
            var_op_cost_npv += real_var_opex / (1 + discount) ** (i)
            hydrogen_npv += real_year_days / (1 + discount) ** (i)

        cap_cost_lc = cap_cost_npv / hydrogen_npv
        fix_op_cost_lc = fix_op_cost_npv / hydrogen_npv
        var_op_cost_lc = var_op_cost_npv / hydrogen_npv

        end_bound = min(max(electricity_market_price.index), base_year + operational_time)

        for year in range(base_year, end_bound + 1):
            elec_price = electricity_market_price[year]
            elec_cost = elec_price * electrolyser_specific_electricity[base_year]
            hydrogen_prices[year] = {
                "TOTAL": cap_cost_lc + var_op_cost_lc + fix_op_cost_lc + elec_cost,
                "CAPEX": cap_cost_lc,
                "FIX_OPEX": fix_op_cost_lc,
                "VAR_OPEX": var_op_cost_lc,
                "ELECTRICITY": elec_cost,
            }
        return hydrogen_prices

    @staticmethod
    def fossil_computation(
        plant_eis_capex: pd.Series = pd.Series(dtype="float64"),
        plant_eis_fixed_opex: pd.Series = pd.Series(dtype="float64"),
        # plant_eis_var_opex: pd.Series = pd.Series(dtype="float64"),
        plant_efficiency: pd.Series = pd.Series(dtype="float64"),
        fuel_market_price: pd.Series = pd.Series(dtype="float64"),
        ccs_cost: pd.Series = pd.Series(dtype="float64"),
        energy_consumption_hydrogen: pd.Series = pd.Series(dtype="float64"),
        pathway_share: pd.Series = pd.Series(dtype="float64"),
        plant_load_factor: float = 0.0,
        emission_factor: float = 0.0,
        ccs_efficiency: float = 0.0,
    ):
        """
        Computes the yearly costs to respect a given hydrogen production scenario.
        Capex in €/ton/day
        Fixed opex in  €/ton/day
        Variable opex in € per kg
        Specific electricity in kWh/kg
        fuel market price in €/kWh
        efficiency dimensionless
        Fuel market price in €/kWh
        CCS price in €/kg CO2
        CCS efficiency (no dimension), share of CO2 captured (0 if no CCS)
        emission factor => gCO2e/MJ
        Energy_consumption_hydrogen in MJ.
        Values returned are in M€ or t/day
        """

        hydrogen_specific_energy = 119.93  # MJ/kg

        # Convert hydrogen demand from MJ to tons.
        demand_scenario = (
            energy_consumption_hydrogen / hydrogen_specific_energy / 1000 * pathway_share / 100
        )
        plant_life = 25

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
        h2_fuel_cost = pd.Series(np.zeros(len(indexes)), indexes)
        h2_ccs_cost = pd.Series(np.zeros(len(indexes)), indexes)

        # For each year of the demand scenario the demand is matched by the production
        for year in list(demand_scenario.index)[:-1]:
            # Production missing in year n+1 must be supplied by plant build in year n
            if hydrogen_production[year + 1] < demand_scenario[year + 1]:

                # Getting the production not matched by plants already commissioned by creating an plant with EIS year technical data
                hydrogen_cost = LiquidHydrogenCost.compute_fossil_year_lcoh(
                    year,
                    fuel_market_price,
                    ccs_cost,
                    ccs_efficiency,
                    emission_factor,
                    plant_load_factor,
                    plant_eis_capex,
                    plant_eis_fixed_opex,
                    # plant_eis_var_opex,
                    plant_efficiency,
                )

                # Getting the production not matched by plants already commissioned
                missing_production = demand_scenario[year + 1] - hydrogen_production[year + 1]

                # Converting the missing production to a capacity (in t/day)
                plant_capacity_to_build = (
                    missing_production / 365.25 / plant_load_factor
                )  # capacity to build in t/day production, taking into account load_factor

                plant_capex_year = plant_capacity_to_build * plant_eis_capex[year] / 1000
                # plant capex is in €/kg/day or m€/ton/day ==> M€/ton/day

                plant_building_cost[year] = plant_capex_year
                plant_building_scenario[year] = plant_capacity_to_build
                # in ton/day capacity

                # When production ends: either at the end of plant life or the end of the scenario;
                end_bound = min(list(demand_scenario.index)[-1], year + plant_life)

                # Adding new plant production to future years
                for i in range(year + 1, end_bound + 1):
                    h2_total_cost[i] = (
                        h2_total_cost[i] + (missing_production * hydrogen_cost[i]["TOTAL"]) / 1000
                    )  # €/kg and production in tons => /1000 for M€
                    h2_capex_cost[i] = (
                        h2_capex_cost[i] + (missing_production * hydrogen_cost[i]["CAPEX"]) / 1000
                    )  # M€
                    h2_opex_cost[i] = (
                        h2_opex_cost[i]
                        + (missing_production * hydrogen_cost[i]["FIX_OPEX"]) / 1000
                        + (missing_production * hydrogen_cost[i]["VAR_OPEX"]) / 1000
                    )  # M€
                    h2_fuel_cost[i] = (
                        h2_fuel_cost[i] + (missing_production * hydrogen_cost[i]["FUEL"]) / 1000
                    )  # M€
                    h2_ccs_cost[i] = (
                        h2_ccs_cost[i] + (missing_production * hydrogen_cost[i]["CCS"]) / 1000
                    )  # M€

                    hydrogen_production[i] = hydrogen_production[i] + missing_production

        # MOD -> Scaling down production for diminishing production scenarios.
        # Very weak model, assuming that production not anymore needed by aviation is used elsewhere in the industry.
        # Stranded asset literature could be valuable to model this better.
        # Proportional production scaling

        scaling_factor = demand_scenario / hydrogen_production

        if not all(scaling_factor.isna()):
            h2_total_cost = h2_total_cost * scaling_factor
            h2_capex_cost = h2_capex_cost * scaling_factor
            h2_opex_cost = h2_opex_cost * scaling_factor
            h2_fuel_cost = h2_fuel_cost * scaling_factor
            h2_ccs_cost = h2_ccs_cost * scaling_factor

        return (
            plant_building_scenario,
            plant_building_cost,
            h2_total_cost,
            h2_capex_cost,
            h2_opex_cost,
            h2_fuel_cost,
            h2_ccs_cost,
        )

    @staticmethod
    def compute_fossil_year_lcoh(
        base_year,
        fuel_market_price,
        ccs_cost,
        ccs_efficiency,
        emission_factor,
        plant_load_factor,
        plant_capex,
        plant_fixed_opex,
        # plant_var_opex,
        plant_efficiency,
    ):
        """
        This function computes the MFSP for hydrogen production for an plant commissioned at the base year.
        Costs are discounted to find a constant MFSP, excepted electricity, whose price is directly evolving
        from a year to another.
        Capex in €/ (kg/day capacity)
        Fixed opex in €/ (kg/day capacity), on an annual basis
        Variable opex in € per kg
        efficiency dimensionless
        Fuel market price in €/kWh
        CCS price in €/kg CO2
        CCS efficiency (no dimension), share of CO2 captured (0 if no CCS)
        emission factor => gCO2e/MJ

        Hydrogen price returned in €/kg
        """
        hydrogen_specific_energy = 119.93 / 3.6  # kWh/kg
        # compute plant specific energy #kWh energy/kg h2
        plant_specific_energy = hydrogen_specific_energy / plant_efficiency

        emission_factor_kg = emission_factor * hydrogen_specific_energy * 3.6

        # compute the carbon captured per kg h2
        carbon_captured_kg = emission_factor_kg / (1 - ccs_efficiency) / 1000

        operational_time = 25
        hydrogen_prices = {}
        construction_time = 3

        discount = 0.10
        load_fact = plant_load_factor
        real_year_days = 365.25 * load_fact
        real_var_opex = 0  # plant_var_opex[base_year] * real_year_days

        cap_cost_npv = 0
        fix_op_cost_npv = 0
        var_op_cost_npv = 0
        hydrogen_npv = 0

        # Construction
        for i in range(0, construction_time):
            # The construction is supposed to span over x years, with a uniform cost repartition
            cap_cost_npv += (plant_capex[base_year] / construction_time) / (1 + discount) ** (i)

        # commissioning
        for i in range(construction_time, operational_time + construction_time):
            fix_op_cost_npv += plant_fixed_opex[base_year] / (1 + discount) ** (i)
            var_op_cost_npv += real_var_opex / (1 + discount) ** (i)
            hydrogen_npv += real_year_days / (1 + discount) ** (i)

        cap_cost_lc = cap_cost_npv / hydrogen_npv
        fix_op_cost_lc = fix_op_cost_npv / hydrogen_npv
        var_op_cost_lc = var_op_cost_npv / hydrogen_npv

        end_bound = min(max(fuel_market_price.index), base_year + operational_time)

        for year in range(base_year, end_bound + 1):
            fuel_price = fuel_market_price[year]
            fuel_cost = fuel_price * plant_specific_energy[base_year]
            co2_ccs_cost = ccs_cost[year] * carbon_captured_kg
            hydrogen_prices[year] = {
                "TOTAL": cap_cost_lc + var_op_cost_lc + fix_op_cost_lc + fuel_cost,
                "CAPEX": cap_cost_lc,
                "FIX_OPEX": fix_op_cost_lc,
                "VAR_OPEX": var_op_cost_lc,
                "FUEL": fuel_cost,
                "CCS": co2_ccs_cost,
            }
        return hydrogen_prices

    @staticmethod
    def liquefaction_computation(
        liquefier_eis_capex: pd.Series = pd.Series(dtype="float64"),
        liquefaction_efficiency: pd.Series = pd.Series(dtype="float64"),
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

                liquefaction_cost = LiquidHydrogenCost.compute_liquefier_year_lcoh(
                    year, electricity_market_price, liquefier_eis_capex, liquefaction_efficiency
                )

                # Getting the production not matched by plants already commissioned
                missing_production = demand_scenario[year + 1] - hydrogen_production[year + 1]

                # Converting the missing production to a capacity (in t/day)
                liquefier_capacity_to_build = missing_production / 365.25 / plant_load_factor
                # capacity to build in t/day production, taking into account plant load_factor
                # However, considering electricity load factor is not relevant if we assume a GH2 buffer.

                liquefier_capex_year = (
                    liquefier_capacity_to_build * liquefier_eis_capex[year] / 1000
                )  # liquefier capex is in €/kg/day or m€/ton/day ==> M€/ton/day
                plant_building_cost[year] = liquefier_capex_year
                plant_building_scenario[year] = liquefier_capacity_to_build  # in ton/day capacity

                # When production ends: either at the end of plant life or the end of the scenario;
                end_bound = min(list(demand_scenario.index)[-1], year + plant_life)

                # Adding new plant production to future years
                for i in range(year + 1, end_bound + 1):
                    h2_total_cost[i] = (
                        h2_total_cost[i]
                        + (missing_production * liquefaction_cost[i]["TOTAL"]) / 1000
                    )  # M€
                    h2_capex_cost[i] = (
                        h2_capex_cost[i]
                        + (missing_production * liquefaction_cost[i]["CAPEX"]) / 1000
                    )  # M€
                    h2_opex_cost[i] = (
                        h2_opex_cost[i]
                        + (missing_production * liquefaction_cost[i]["FIX_OPEX"]) / 1000
                        + (missing_production * liquefaction_cost[i]["VAR_OPEX"]) / 1000
                    )  # M€
                    h2_elec_cost[i] = (
                        h2_elec_cost[i]
                        + (missing_production * liquefaction_cost[i]["ELECTRICITY"]) / 1000
                    )  # M€
                    hydrogen_production[i] = hydrogen_production[i] + missing_production

        # MOD -> Scaling down production for diminishing production scenarios.
        # Very weak model, assuming that production not anymore needed by aviation is used elsewhere in the industry.
        # Stranded asset literature could be valuable to model this better.
        # Proportional production scaling

        scaling_factor = demand_scenario / hydrogen_production

        if not all(scaling_factor.isna()):
            h2_total_cost = h2_total_cost * scaling_factor
            h2_capex_cost = h2_capex_cost * scaling_factor
            h2_opex_cost = h2_opex_cost * scaling_factor
            h2_elec_cost = h2_elec_cost * scaling_factor

        return (
            plant_building_scenario,
            plant_building_cost,
            h2_total_cost,
            h2_capex_cost,
            h2_opex_cost,
            h2_elec_cost,
        )

    @staticmethod
    def compute_liquefier_year_lcoh(
        base_year, electricity_market_price, liquefier_capex, liquefaction_efficiency
    ):
        """This function computes the MFSP for hydrogen liquefaction for an liquefier commissioned at the base year.
        Costs are discounted to find a constant MFSP, excepted electricity, whose price is directly evolving
        from a year to another.
        """
        operational_time = 30
        liquefaction_prices = {}
        construction_time = 3

        hydrogen_specific_energy = 119.93 / 3.6  # kWh/kg
        # compute plant specific energy #kWh energy/kg h2
        liquefier_specific_electricity = hydrogen_specific_energy / liquefaction_efficiency

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

        end_bound = min(max(electricity_market_price.index), operational_time + base_year)

        for year in range(base_year, end_bound + 1):
            elec_price = electricity_market_price[year]
            elec_cost = elec_price * liquefier_specific_electricity[base_year]
            opex_var_cost = 0.05 * elec_cost
            liquefaction_prices[year] = {
                "TOTAL": cap_cost_lc + opex_var_cost + fix_op_cost_lc + elec_cost,
                "CAPEX": cap_cost_lc,
                "FIX_OPEX": fix_op_cost_lc,
                "VAR_OPEX": opex_var_cost,
                "ELECTRICITY": elec_cost,
            }

        return liquefaction_prices


class ElectrolyserCapex(AeromapsModel):
    def __init__(self, name="electrolyser_capex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrolyser_capex_reference_years: list = [],
        electrolyser_capex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:
        """Electrolyser capital expenditures at eis using interpolation functions"""

        electrolysis_h2_eis_capex = AeromapsInterpolationFunction(
            self,
            electrolyser_capex_reference_years,
            electrolyser_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electrolysis_h2_eis_capex"] = electrolysis_h2_eis_capex

        return electrolysis_h2_eis_capex


class ElectrolyserFixedOpex(AeromapsModel):
    def __init__(self, name="electrolyser_fixed_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrolyser_fixed_opex_reference_years: list = [],
        electrolyser_fixed_opex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:
        """Electrolyser fixed operational expenditures at entry into service using interpolation functions"""

        electrolysis_h2_eis_fixed_opex = AeromapsInterpolationFunction(
            self,
            electrolyser_fixed_opex_reference_years,
            electrolyser_fixed_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electrolysis_h2_eis_fixed_opex"] = electrolysis_h2_eis_fixed_opex

        return electrolysis_h2_eis_fixed_opex


class ElectrolyserVarOpex(AeromapsModel):
    def __init__(self, name="electrolyser_var_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrolyser_var_opex_reference_years: list = [],
        electrolyser_var_opex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:
        """Electrolyser variable operational expenditures at entry into service using interpolation functions"""

        electrolysis_h2_eis_var_opex = AeromapsInterpolationFunction(
            self,
            electrolyser_var_opex_reference_years,
            electrolyser_var_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electrolysis_h2_eis_var_opex"] = electrolysis_h2_eis_var_opex

        return electrolysis_h2_eis_var_opex


########## Deprecated for the time being, might be reactivated. #####################

# class ElectrolyserSpecificElectricity(AeromapsModel):

#     def __init__(self, name="electrolyser_specific_electricity", *args, **kwargs):
#         super().__init__(name, *args, **kwargs)
#
#     def compute(
#             self,
#             electrolyser_specific_electricity_2020: float = 0.0,
#             electrolyser_specific_electricity_2030: float = 0.0,
#             electrolyser_specific_electricity_2040: float = 0.0,
#             electrolyser_specific_electricity_2050: float = 0.0,
#     ) -> Tuple[pd.Series]:
#         """Electrolyser efficiency at eis using interpolation functions"""
#         # FT MSW
#         reference_values_specific_electricity = [
#             electrolyser_specific_electricity_2020,
#             electrolyser_specific_electricity_2030,
#             electrolyser_specific_electricity_2040,
#             electrolyser_specific_electricity_2050
#         ]
#
#         reference_years = [2020, 2030, 2040, 2050]
#
#         specific_electricity_function = interp1d(
#             reference_years, reference_values_specific_electricity, kind="linear"
#         )
#         for k in range(self.prospection_start_year, self.end_year + 1):
#             self.df.loc[
#                 k, "electrolyser_eis_specific_electricity"
#             ] = specific_electricity_function(k)
#
#         electrolyser_eis_specific_electricity = self.df.loc[:, "electrolyser_eis_specific_electricity"]
#
#         return (
#             electrolyser_eis_specific_electricity
#         )
####################################################################################


class LiquefierCapex(AeromapsModel):
    def __init__(self, name="liquefier_capex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        liquefier_capex_reference_years: list = [],
        liquefier_capex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:
        """Liquefier capital expenditures at eis using interpolation functions"""

        liquefier_eis_capex = AeromapsInterpolationFunction(
            self,
            liquefier_capex_reference_years,
            liquefier_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "liquefier_eis_capex"] = liquefier_eis_capex

        return liquefier_eis_capex


########## Deprecated for the time being, might be reactivated. ####################

# class LiquefierSpecificElectricity(AeromapsModel):
#     def __init__(self, name="liquefier_specific_electricity", *args, **kwargs):
#         super().__init__(name, *args, **kwargs)
#
#     def compute(
#             self,
#             liquefier_specific_electricity_2020: float = 0.0,
#             liquefier_specific_electricity_2030: float = 0.0,
#             liquefier_specific_electricity_2040: float = 0.0,
#             liquefier_specific_electricity_2050: float = 0.0,
#     ) -> Tuple[pd.Series]:
#         """liquefier efficiency at eis using interpolation functions"""
#         # FT MSW
#         reference_values_specific_electricity = [
#             liquefier_specific_electricity_2020,
#             liquefier_specific_electricity_2030,
#             liquefier_specific_electricity_2040,
#             liquefier_specific_electricity_2050
#         ]
#
#         reference_years = [2020, 2030, 2040, 2050]
#
#         specific_electricity_function = interp1d(
#             reference_years, reference_values_specific_electricity, kind="linear"
#         )
#         for k in range(self.prospection_start_year, self.end_year + 1):
#             self.df.loc[
#                 k, "liquefier_eis_specific_electricity"
#             ] = specific_electricity_function(k)
#
#         liquefier_eis_specific_electricity = self.df.loc[:, "liquefier_eis_specific_electricity"]
#
#         return (
#             liquefier_eis_specific_electricity
#         )
####################################################################################


class GasCcsCapex(AeromapsModel):
    def __init__(self, name="gas_ccs_capex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        gas_ccs_eis_capex_reference_years: list = [],
        gas_ccs_eis_capex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        gas_ccs_eis_capex = AeromapsInterpolationFunction(
            self,
            gas_ccs_eis_capex_reference_years,
            gas_ccs_eis_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gas_ccs_eis_capex"] = gas_ccs_eis_capex

        return gas_ccs_eis_capex


class GasCcsFixedOpex(AeromapsModel):
    def __init__(self, name="gas_ccs_fixed_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        gas_ccs_eis_fixed_opex_reference_years: list = [],
        gas_ccs_eis_fixed_opex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        gas_ccs_eis_fixed_opex = AeromapsInterpolationFunction(
            self,
            gas_ccs_eis_fixed_opex_reference_years,
            gas_ccs_eis_fixed_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gas_ccs_eis_fixed_opex"] = gas_ccs_eis_fixed_opex

        return gas_ccs_eis_fixed_opex


class GasCcsEfficiency(AeromapsModel):
    def __init__(self, name="gas_ccs_efficiency", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        gas_ccs_efficiency_reference_years: list = [],
        gas_ccs_efficiency_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        gas_ccs_efficiency = AeromapsInterpolationFunction(
            self,
            gas_ccs_efficiency_reference_years,
            gas_ccs_efficiency_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gas_ccs_efficiency"] = gas_ccs_efficiency

        return gas_ccs_efficiency


class GasCapex(AeromapsModel):
    def __init__(self, name="gas_capex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        gas_eis_capex_reference_years: list = [],
        gas_eis_capex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        gas_eis_capex = AeromapsInterpolationFunction(
            self,
            gas_eis_capex_reference_years,
            gas_eis_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gas_eis_capex"] = gas_eis_capex

        return gas_eis_capex


class GasFixedOpex(AeromapsModel):
    def __init__(self, name="gas_fixed_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        gas_eis_fixed_opex_reference_years: list = [],
        gas_eis_fixed_opex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        gas_eis_fixed_opex = AeromapsInterpolationFunction(
            self,
            gas_eis_fixed_opex_reference_years,
            gas_eis_fixed_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gas_eis_fixed_opex"] = gas_eis_fixed_opex

        return gas_eis_fixed_opex


class GasEfficiency(AeromapsModel):
    def __init__(self, name="gas_fixed_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        gas_efficiency_reference_years: list = [],
        gas_efficiency_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        gas_efficiency = AeromapsInterpolationFunction(
            self,
            gas_efficiency_reference_years,
            gas_efficiency_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gas_efficiency"] = gas_efficiency

        return gas_efficiency


class CoalCcsCapex(AeromapsModel):
    def __init__(self, name="coal_ccs_capex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        coal_ccs_eis_capex_reference_years: list = [],
        coal_ccs_eis_capex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        coal_ccs_eis_capex = AeromapsInterpolationFunction(
            self,
            coal_ccs_eis_capex_reference_years,
            coal_ccs_eis_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "coal_ccs_eis_capex"] = coal_ccs_eis_capex

        return coal_ccs_eis_capex


class CoalCcsFixedOpex(AeromapsModel):
    def __init__(self, name="coal_ccs_fixed_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        coal_ccs_eis_fixed_opex_reference_years: list = [],
        coal_ccs_eis_fixed_opex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        coal_ccs_eis_fixed_opex = AeromapsInterpolationFunction(
            self,
            coal_ccs_eis_fixed_opex_reference_years,
            coal_ccs_eis_fixed_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "coal_ccs_eis_fixed_opex"] = coal_ccs_eis_fixed_opex

        return coal_ccs_eis_fixed_opex


class CoalCcsEfficiency(AeromapsModel):
    def __init__(self, name="coal_ccs_efficiency", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        coal_ccs_efficiency_reference_years: list = [],
        coal_ccs_efficiency_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        coal_ccs_efficiency = AeromapsInterpolationFunction(
            self,
            coal_ccs_efficiency_reference_years,
            coal_ccs_efficiency_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "coal_ccs_efficiency"] = coal_ccs_efficiency

        return coal_ccs_efficiency


class CoalCapex(AeromapsModel):
    def __init__(self, name="coal_capex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        coal_eis_capex_reference_years: list = [],
        coal_eis_capex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        coal_eis_capex = AeromapsInterpolationFunction(
            self,
            coal_eis_capex_reference_years,
            coal_eis_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "coal_eis_capex"] = coal_eis_capex

        return coal_eis_capex


class CoalFixedOpex(AeromapsModel):
    def __init__(self, name="coal_fixed_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        coal_eis_fixed_opex_reference_years: list = [],
        coal_eis_fixed_opex_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        coal_eis_fixed_opex = AeromapsInterpolationFunction(
            self,
            coal_eis_fixed_opex_reference_years,
            coal_eis_fixed_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "coal_eis_fixed_opex"] = coal_eis_fixed_opex

        return coal_eis_fixed_opex


class CoalEfficiency(AeromapsModel):
    def __init__(self, name="coal_fixed_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        coal_efficiency_reference_years: list = [],
        coal_efficiency_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        coal_efficiency = AeromapsInterpolationFunction(
            self,
            coal_efficiency_reference_years,
            coal_efficiency_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "coal_efficiency"] = coal_efficiency

        return coal_efficiency


class CcsCost(AeromapsModel):
    def __init__(self, name="ccs_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        ccs_cost_reference_years: list = [],
        ccs_cost_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:

        ccs_cost = AeromapsInterpolationFunction(
            self, ccs_cost_reference_years, ccs_cost_reference_years_values, model_name=self.name
        )
        self.df.loc[:, "ccs_cost"] = ccs_cost

        return ccs_cost

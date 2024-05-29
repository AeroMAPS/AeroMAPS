from typing import Tuple

import numpy as np
import pandas as pd
from pandas import Series

from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class HydrogenCostSimple(AeroMAPSModel):
    def __init__(self, name="hydrogen_cost_simple", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_hydrogen: pd.Series = pd.Series(dtype="float64"),
        liquid_hydrogen_electrolysis_emission_factor: pd.Series = pd.Series(dtype="float64"),
        liquid_hydrogen_gas_ccs_emission_factor: pd.Series = pd.Series(dtype="float64"),
        liquid_hydrogen_gas_emission_factor: pd.Series = pd.Series(dtype="float64"),
        liquid_hydrogen_coal_ccs_emission_factor: pd.Series = pd.Series(dtype="float64"),
        liquid_hydrogen_coal_emission_factor: pd.Series = pd.Series(dtype="float64"),
        hydrogen_electrolysis_share: pd.Series = pd.Series(dtype="float64"),
        hydrogen_gas_ccs_share: pd.Series = pd.Series(dtype="float64"),
        hydrogen_gas_share: pd.Series = pd.Series(dtype="float64"),
        hydrogen_coal_ccs_share: pd.Series = pd.Series(dtype="float64"),
        hydrogen_coal_share: pd.Series = pd.Series(dtype="float64"),
        gh2_electrolysis_mfsp_simple: pd.Series = pd.Series(dtype="float64"),
        gh2_gas_ccs_mfsp_simple: pd.Series = pd.Series(dtype="float64"),
        gh2_gas_mfsp_simple: pd.Series = pd.Series(dtype="float64"),
        gh2_coal_ccs_mfsp_simple: pd.Series = pd.Series(dtype="float64"),
        gh2_coal_mfsp_simple: pd.Series = pd.Series(dtype="float64"),
        liquefaction_mfsp_simple: pd.Series = pd.Series(dtype="float64"),
        carbon_tax: pd.Series = pd.Series(dtype="float64"),
        lhv_hydrogen: float = 0.0,
        transport_cost_ratio: float = 0.0,
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
    ]:

        ### Electrolysis ####

        electrolysis_h2_total_cost = (
                gh2_electrolysis_mfsp_simple
                / lhv_hydrogen
                * energy_consumption_hydrogen
                * hydrogen_electrolysis_share
                / 100
                / 1e6
        )
        electrolysis_h2_carbon_tax = (
            energy_consumption_hydrogen
            * hydrogen_electrolysis_share
            / 100
            * liquid_hydrogen_electrolysis_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        # M€
        self.df.loc[:, "electrolysis_h2_carbon_tax"] = electrolysis_h2_carbon_tax

        electrolysis_h2_mfsp_carbon_tax_supplement = (
            carbon_tax * liquid_hydrogen_electrolysis_emission_factor / 1000000 * lhv_hydrogen
        )
        # €/kg_H2
        self.df.loc[
            :, "electrolysis_h2_mfsp_carbon_tax_supplement"
        ] = electrolysis_h2_mfsp_carbon_tax_supplement

        self.df.loc[:, "electrolysis_h2_total_cost"] = electrolysis_h2_total_cost

        ### gas ####

        gas_h2_total_cost = (
                gh2_gas_mfsp_simple
                / lhv_hydrogen
                * energy_consumption_hydrogen
                * hydrogen_gas_share
                / 100
                / 1e6
        )
        gas_h2_carbon_tax = (
            energy_consumption_hydrogen
            * hydrogen_gas_share
            / 100
            * liquid_hydrogen_gas_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        # M€
        self.df.loc[:, "gas_h2_carbon_tax"] = gas_h2_carbon_tax

        gas_h2_mfsp_carbon_tax_supplement = (
            carbon_tax * liquid_hydrogen_gas_emission_factor / 1000000 * lhv_hydrogen
        )
        # €/kg_H2
        self.df.loc[:, "gas_h2_mfsp_carbon_tax_supplement"] = gas_h2_mfsp_carbon_tax_supplement

        self.df.loc[:, "gas_h2_total_cost"] = gas_h2_total_cost

        ### gas_ccs ####

        gas_ccs_h2_total_cost = (
                gh2_gas_ccs_mfsp_simple
                / lhv_hydrogen
                * energy_consumption_hydrogen
                * hydrogen_gas_ccs_share
                / 100
                / 1e6
        )
        gas_ccs_h2_carbon_tax = (
            energy_consumption_hydrogen
            * hydrogen_gas_ccs_share
            / 100
            * liquid_hydrogen_gas_ccs_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        # M€
        self.df.loc[:, "gas_ccs_h2_carbon_tax"] = gas_ccs_h2_carbon_tax

        gas_ccs_h2_mfsp_carbon_tax_supplement = (
            carbon_tax * liquid_hydrogen_gas_ccs_emission_factor / 1000000 * lhv_hydrogen
        )
        # €/kg_H2
        self.df.loc[
            :, "gas_ccs_h2_mfsp_carbon_tax_supplement"
        ] = gas_ccs_h2_mfsp_carbon_tax_supplement

        self.df.loc[:, "gas_ccs_h2_total_cost"] = gas_ccs_h2_total_cost

        ### coal ####

        coal_h2_total_cost = (
                gh2_coal_mfsp_simple
                / lhv_hydrogen
                * energy_consumption_hydrogen
                * hydrogen_coal_share
                / 100
                / 1e6
        )
        coal_h2_carbon_tax = (
            energy_consumption_hydrogen
            * hydrogen_coal_share
            / 100
            * liquid_hydrogen_coal_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        # M€
        self.df.loc[:, "coal_h2_carbon_tax"] = coal_h2_carbon_tax

        coal_h2_mfsp_carbon_tax_supplement = (
            carbon_tax * liquid_hydrogen_coal_emission_factor / 1000000 * lhv_hydrogen
        )
        # €/kg_H2
        self.df.loc[:, "coal_h2_mfsp_carbon_tax_supplement"] = coal_h2_mfsp_carbon_tax_supplement

        self.df.loc[:, "coal_h2_total_cost"] = coal_h2_total_cost

        ### coal_ccs ####

        coal_ccs_h2_total_cost = (
                gh2_coal_ccs_mfsp_simple
                / lhv_hydrogen
                * energy_consumption_hydrogen
                * hydrogen_coal_ccs_share
                / 100
                / 1e6
        )
        coal_ccs_h2_carbon_tax = (
            energy_consumption_hydrogen
            * hydrogen_coal_ccs_share
            / 100
            * liquid_hydrogen_coal_ccs_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        # M€
        self.df.loc[:, "coal_ccs_h2_carbon_tax"] = coal_ccs_h2_carbon_tax

        coal_ccs_h2_mfsp_carbon_tax_supplement = (
            carbon_tax * liquid_hydrogen_coal_ccs_emission_factor / 1000000 * lhv_hydrogen
        )
        # €/kg_H2
        self.df.loc[
            :, "coal_ccs_h2_mfsp_carbon_tax_supplement"
        ] = coal_ccs_h2_mfsp_carbon_tax_supplement

        self.df.loc[:, "coal_ccs_h2_total_cost"] = coal_ccs_h2_total_cost

        liquefaction_h2_total_cost = (
                liquefaction_mfsp_simple / lhv_hydrogen * energy_consumption_hydrogen / 1e6
        )

        self.df.loc[:, "liquefaction_h2_total_cost"] = liquefaction_h2_total_cost

        transport_h2_total_cost = transport_cost_ratio * (
            electrolysis_h2_total_cost.fillna(0)
            + gas_ccs_h2_total_cost.fillna(0)
            + gas_h2_total_cost.fillna(0)
            + coal_ccs_h2_total_cost.fillna(0)
            + coal_h2_total_cost.fillna(0)
            + liquefaction_h2_total_cost.fillna(0)
        )

        self.df.loc[:, "transport_h2_total_cost"] = transport_h2_total_cost

        transport_h2_cost_per_kg = (
            transport_h2_total_cost / (energy_consumption_hydrogen / lhv_hydrogen) * 1000000
        )

        liquefaction_h2_mean_mfsp_kg = (
            liquefaction_h2_total_cost / (energy_consumption_hydrogen / lhv_hydrogen) * 1000000
        )

        self.df.loc[:, "transport_h2_cost_per_kg"] = transport_h2_cost_per_kg
        self.df.loc[:, "liquefaction_h2_mean_mfsp_kg"] = liquefaction_h2_mean_mfsp_kg

        ######## SYNTHESIS ########
        # compute average costs per kg for each pathway

        electrolysis_h2_mean_mfsp_kg = (
            electrolysis_h2_total_cost
            / (energy_consumption_hydrogen / lhv_hydrogen * (hydrogen_electrolysis_share / 100))
        ) * 1000000

        self.df.loc[:, "electrolysis_h2_mean_mfsp_kg"] = electrolysis_h2_mean_mfsp_kg
        # €/kg

        gas_ccs_h2_mean_mfsp_kg = (
            gas_ccs_h2_total_cost
            / (energy_consumption_hydrogen / lhv_hydrogen * (hydrogen_gas_ccs_share / 100))
        ) * 1000000

        self.df.loc[:, "gas_ccs_h2_mean_mfsp_kg"] = gas_ccs_h2_mean_mfsp_kg
        # €/kg

        gas_h2_mean_mfsp_kg = (
            gas_h2_total_cost
            / (energy_consumption_hydrogen / lhv_hydrogen * (hydrogen_gas_share / 100))
        ) * 1000000

        self.df.loc[:, "gas_h2_mean_mfsp_kg"] = gas_h2_mean_mfsp_kg
        # €/kg

        coal_ccs_h2_mean_mfsp_kg = (
            coal_ccs_h2_total_cost
            / (energy_consumption_hydrogen / lhv_hydrogen * (hydrogen_coal_ccs_share / 100))
        ) * 1000000

        self.df.loc[:, "coal_ccs_h2_mean_mfsp_kg"] = coal_ccs_h2_mean_mfsp_kg
        # €/kg

        coal_h2_mean_mfsp_kg = (
            coal_h2_total_cost
            / (energy_consumption_hydrogen / lhv_hydrogen * (hydrogen_coal_share / 100))
        ) * 1000000

        self.df.loc[:, "coal_h2_mean_mfsp_kg"] = coal_h2_mean_mfsp_kg
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

        average_hydrogen_mean_mfsp_kg = (
            total_hydrogen_supply_cost / (energy_consumption_hydrogen / lhv_hydrogen) * 1000000
        )
        self.df.loc[:, "average_hydrogen_mean_mfsp_kg"] = average_hydrogen_mean_mfsp_kg
        # €/kg

        average_hydrogen_mean_carbon_tax_kg = (
            (
                electrolysis_h2_carbon_tax.fillna(0)
                + gas_h2_carbon_tax.fillna(0)
                + gas_ccs_h2_carbon_tax.fillna(0)
                + coal_h2_carbon_tax.fillna(0)
                + coal_ccs_h2_carbon_tax.fillna(0)
            )
            / (energy_consumption_hydrogen / lhv_hydrogen)
            * 1000000
        )
        self.df.loc[:, "average_hydrogen_mean_carbon_tax_kg"] = average_hydrogen_mean_carbon_tax_kg

        return (
            electrolysis_h2_total_cost,
            liquefaction_h2_total_cost,
            transport_h2_total_cost,
            electrolysis_h2_mean_mfsp_kg,
            total_hydrogen_supply_cost,
            average_hydrogen_mean_mfsp_kg,
            electrolysis_h2_carbon_tax,
            electrolysis_h2_mfsp_carbon_tax_supplement,
            gas_ccs_h2_total_cost,
            gas_h2_total_cost,
            coal_ccs_h2_total_cost,
            coal_h2_total_cost,
            gas_ccs_h2_mean_mfsp_kg,
            gas_h2_mean_mfsp_kg,
            coal_ccs_h2_mean_mfsp_kg,
            coal_h2_mean_mfsp_kg,
            gas_ccs_h2_carbon_tax,
            gas_ccs_h2_mfsp_carbon_tax_supplement,
            gas_h2_carbon_tax,
            gas_h2_mfsp_carbon_tax_supplement,
            coal_ccs_h2_carbon_tax,
            coal_ccs_h2_mfsp_carbon_tax_supplement,
            coal_h2_carbon_tax,
            coal_h2_mfsp_carbon_tax_supplement,
            average_hydrogen_mean_carbon_tax_kg,
            transport_h2_cost_per_kg,
            liquefaction_h2_mean_mfsp_kg,
        )


class HydrogenMfspSimple(AeroMAPSModel):
    def __init__(self, name="hydrogen_mfsp_simple", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        gh2_electrolysis_mfsp_simple_reference_years: list = [],
        gh2_electrolysis_mfsp_simple_reference_years_values: list = [],
        gh2_gas_ccs_mfsp_simple_reference_years: list = [],
        gh2_gas_ccs_mfsp_simple_reference_years_values: list = [],
        gh2_gas_mfsp_simple_reference_years: list = [],
        gh2_gas_mfsp_simple_reference_years_values: list = [],
        gh2_coal_ccs_mfsp_simple_reference_years: list = [],
        gh2_coal_ccs_mfsp_simple_reference_years_values: list = [],
        gh2_coal_mfsp_simple_reference_years: list = [],
        gh2_coal_mfsp_simple_reference_years_values: list = [],
        liquefaction_mfsp_simple_reference_years: list = [],
        liquefaction_mfsp_simple_reference_years_values: list = []
    ) -> Tuple[
        pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series,
    ]:
        """Hydrogen mfsp_simple (Minimal fuel selling price) estimates"""

        # Electrolysis
        gh2_electrolysis_mfsp_simple = AeromapsInterpolationFunction(
            self,
            gh2_electrolysis_mfsp_simple_reference_years,
            gh2_electrolysis_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gh2_electrolysis_mfsp_simple"] = gh2_electrolysis_mfsp_simple

        # Gas CCS
        gh2_gas_ccs_mfsp_simple = AeromapsInterpolationFunction(
            self,
            gh2_gas_ccs_mfsp_simple_reference_years,
            gh2_gas_ccs_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gh2_gas_ccs_mfsp_simple"] = gh2_gas_ccs_mfsp_simple

        # Gas
        gh2_gas_mfsp_simple = AeromapsInterpolationFunction(
            self,
            gh2_gas_mfsp_simple_reference_years,
            gh2_gas_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gh2_gas_mfsp_simple"] = gh2_gas_mfsp_simple

        # Coal CCS
        gh2_coal_ccs_mfsp_simple = AeromapsInterpolationFunction(
            self,
            gh2_coal_ccs_mfsp_simple_reference_years,
            gh2_coal_ccs_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gh2_coal_ccs_mfsp_simple"] = gh2_coal_ccs_mfsp_simple

        # Coal
        gh2_coal_mfsp_simple = AeromapsInterpolationFunction(
            self,
            gh2_coal_mfsp_simple_reference_years,
            gh2_coal_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gh2_coal_mfsp_simple"] = gh2_coal_mfsp_simple

        # Liquefaction
        liquefaction_mfsp_simple = AeromapsInterpolationFunction(
            self,
            liquefaction_mfsp_simple_reference_years,
            liquefaction_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "liquefaction_mfsp_simple"] = liquefaction_mfsp_simple


        return (
            gh2_electrolysis_mfsp_simple,
            gh2_gas_ccs_mfsp_simple,
            gh2_gas_mfsp_simple,
            gh2_coal_ccs_mfsp_simple,
            gh2_coal_mfsp_simple,
            liquefaction_mfsp_simple)

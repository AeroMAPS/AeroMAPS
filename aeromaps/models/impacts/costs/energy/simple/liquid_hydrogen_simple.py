from typing import Tuple

import pandas as pd
from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class HydrogenCostSimple(AeroMAPSModel):
    def __init__(self, name="hydrogen_cost_simple", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_hydrogen: pd.Series,
        liquid_hydrogen_electrolysis_emission_factor: pd.Series,
        liquid_hydrogen_gas_ccs_emission_factor: pd.Series,
        liquid_hydrogen_gas_emission_factor: pd.Series,
        liquid_hydrogen_coal_ccs_emission_factor: pd.Series,
        liquid_hydrogen_coal_emission_factor: pd.Series,
        hydrogen_electrolysis_share: pd.Series,
        hydrogen_gas_ccs_share: pd.Series,
        hydrogen_gas_share: pd.Series,
        hydrogen_coal_ccs_share: pd.Series,
        hydrogen_coal_share: pd.Series,
        electrolysis_h2_mean_mfsp_kg: pd.Series,
        gas_ccs_h2_mean_mfsp_kg: pd.Series,
        gas_h2_mean_mfsp_kg: pd.Series,
        coal_ccs_h2_mean_mfsp_kg: pd.Series,
        coal_h2_mean_mfsp_kg: pd.Series,
        liquefaction_h2_mean_mfsp_kg: pd.Series,
        carbon_tax: pd.Series,
        lhv_hydrogen: float,
        transport_cost_ratio: float,
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
    ]:
        ### Electrolysis ####

        electrolysis_h2_total_cost = (
            electrolysis_h2_mean_mfsp_kg
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
        self.df.loc[:, "electrolysis_h2_mfsp_carbon_tax_supplement"] = (
            electrolysis_h2_mfsp_carbon_tax_supplement
        )

        self.df.loc[:, "electrolysis_h2_total_cost"] = electrolysis_h2_total_cost

        ### gas ####

        gas_h2_total_cost = (
            gas_h2_mean_mfsp_kg
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
            gas_ccs_h2_mean_mfsp_kg
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
        self.df.loc[:, "gas_ccs_h2_mfsp_carbon_tax_supplement"] = (
            gas_ccs_h2_mfsp_carbon_tax_supplement
        )

        self.df.loc[:, "gas_ccs_h2_total_cost"] = gas_ccs_h2_total_cost

        ### coal ####

        coal_h2_total_cost = (
            coal_h2_mean_mfsp_kg
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
            coal_ccs_h2_mean_mfsp_kg
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
        self.df.loc[:, "coal_ccs_h2_mfsp_carbon_tax_supplement"] = (
            coal_ccs_h2_mfsp_carbon_tax_supplement
        )

        self.df.loc[:, "coal_ccs_h2_total_cost"] = coal_ccs_h2_total_cost

        liquefaction_h2_total_cost = (
            liquefaction_h2_mean_mfsp_kg / lhv_hydrogen * energy_consumption_hydrogen / 1e6
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

        self.df.loc[:, "transport_h2_cost_per_kg"] = transport_h2_cost_per_kg

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
            total_hydrogen_supply_cost,
            average_hydrogen_mean_mfsp_kg,
            electrolysis_h2_carbon_tax,
            electrolysis_h2_mfsp_carbon_tax_supplement,
            gas_ccs_h2_total_cost,
            gas_h2_total_cost,
            coal_ccs_h2_total_cost,
            coal_h2_total_cost,
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
        )


class HydrogenMfspSimple(AeroMAPSModel):
    def __init__(self, name="hydrogen_mfsp_simple", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        gh2_electrolysis_mfsp_simple_reference_years: list,
        gh2_electrolysis_mfsp_simple_reference_years_values: list,
        gh2_gas_ccs_mfsp_simple_reference_years: list,
        gh2_gas_ccs_mfsp_simple_reference_years_values: list,
        gh2_gas_mfsp_simple_reference_years: list,
        gh2_gas_mfsp_simple_reference_years_values: list,
        gh2_coal_ccs_mfsp_simple_reference_years: list,
        gh2_coal_ccs_mfsp_simple_reference_years_values: list,
        gh2_coal_mfsp_simple_reference_years: list,
        gh2_coal_mfsp_simple_reference_years_values: list,
        liquefaction_mfsp_simple_reference_years: list,
        liquefaction_mfsp_simple_reference_years_values: list,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        """Hydrogen mfsp_simple (Minimal fuel selling price) estimates"""

        # Electrolysis
        electrolysis_h2_mean_mfsp_kg = AeromapsInterpolationFunction(
            self,
            gh2_electrolysis_mfsp_simple_reference_years,
            gh2_electrolysis_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electrolysis_h2_mean_mfsp_kg"] = electrolysis_h2_mean_mfsp_kg

        # Gas CCS
        gas_ccs_h2_mean_mfsp_kg = AeromapsInterpolationFunction(
            self,
            gh2_gas_ccs_mfsp_simple_reference_years,
            gh2_gas_ccs_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gas_ccs_h2_mean_mfsp_kg"] = gas_ccs_h2_mean_mfsp_kg

        # Gas
        gas_h2_mean_mfsp_kg = AeromapsInterpolationFunction(
            self,
            gh2_gas_mfsp_simple_reference_years,
            gh2_gas_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gas_h2_mean_mfsp_kg"] = gas_h2_mean_mfsp_kg

        # Coal CCS
        coal_ccs_h2_mean_mfsp_kg = AeromapsInterpolationFunction(
            self,
            gh2_coal_ccs_mfsp_simple_reference_years,
            gh2_coal_ccs_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "coal_ccs_h2_mean_mfsp_kg"] = coal_ccs_h2_mean_mfsp_kg

        # Coal
        coal_h2_mean_mfsp_kg = AeromapsInterpolationFunction(
            self,
            gh2_coal_mfsp_simple_reference_years,
            gh2_coal_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "coal_h2_mean_mfsp_kg"] = coal_h2_mean_mfsp_kg

        # Liquefaction
        liquefaction_h2_mean_mfsp_kg = AeromapsInterpolationFunction(
            self,
            liquefaction_mfsp_simple_reference_years,
            liquefaction_mfsp_simple_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "liquefaction_h2_mean_mfsp_kg"] = liquefaction_h2_mean_mfsp_kg

        return (
            electrolysis_h2_mean_mfsp_kg,
            gas_ccs_h2_mean_mfsp_kg,
            gas_h2_mean_mfsp_kg,
            coal_ccs_h2_mean_mfsp_kg,
            coal_h2_mean_mfsp_kg,
            liquefaction_h2_mean_mfsp_kg,
        )

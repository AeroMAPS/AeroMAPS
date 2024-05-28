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
        h2_electrolysis_mfsp: pd.Series = pd.Series(dtype="float64"),
        h2_gas_ccs_mfsp: pd.Series = pd.Series(dtype="float64"),
        h2_gas_mfsp: pd.Series = pd.Series(dtype="float64"),
        h2_coal_ccs_mfsp: pd.Series = pd.Series(dtype="float64"),
        h2_coal_mfsp: pd.Series = pd.Series(dtype="float64"),
        h2_liquefaction_mfsp: pd.Series = pd.Series(dtype="float64"),
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
            h2_electrolysis_mfsp
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
            h2_gas_mfsp
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
        self.df.loc[
            :, "gas_h2_mfsp_carbon_tax_supplement"
        ] = gas_h2_mfsp_carbon_tax_supplement

        self.df.loc[:, "gas_h2_total_cost"] = gas_h2_total_cost
        
        
        ### gas_ccs ####

        gas_ccs_h2_total_cost = (
            h2_gas_ccs_mfsp
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
            h2_coal_mfsp
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
        self.df.loc[
            :, "coal_h2_mfsp_carbon_tax_supplement"
        ] = coal_h2_mfsp_carbon_tax_supplement

        self.df.loc[:, "coal_h2_total_cost"] = coal_h2_total_cost

        ### coal_ccs ####

        coal_ccs_h2_total_cost = (
                h2_coal_ccs_mfsp
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

        liquefaction_h2_total_cost = h2_liquefaction_mfsp / lhv_hydrogen * energy_consumption_hydrogen / 1e6

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
                                               / (energy_consumption_hydrogen / lhv_hydrogen * (
                                                   hydrogen_electrolysis_share / 100))
                                       ) * 1000000

        self.df.loc[:, "electrolysis_h2_mean_mfsp_kg"] = electrolysis_h2_mean_mfsp_kg
        # €/kg

        gas_ccs_h2_mean_mfsp_kg = (
                                          gas_ccs_h2_total_cost
                                          / (energy_consumption_hydrogen / lhv_hydrogen * (
                                              hydrogen_gas_ccs_share / 100))
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
                                           / (energy_consumption_hydrogen / lhv_hydrogen * (
                                               hydrogen_coal_ccs_share / 100))
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

        h2_avg_cost_per_kg = (
                total_hydrogen_supply_cost / (energy_consumption_hydrogen / lhv_hydrogen) * 1000000
        )
        self.df.loc[:, "h2_avg_cost_per_kg"] = h2_avg_cost_per_kg
        # €/kg

        h2_avg_carbon_tax_per_kg = (
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
        self.df.loc[:, "h2_avg_carbon_tax_per_kg"] = h2_avg_carbon_tax_per_kg

        return (
            electrolysis_h2_total_cost,
            liquefaction_h2_total_cost,
            transport_h2_total_cost,
            electrolysis_h2_mean_mfsp_kg,
            total_hydrogen_supply_cost,
            h2_avg_cost_per_kg,
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
            h2_avg_carbon_tax_per_kg,
            transport_h2_cost_per_kg,
            liquefaction_h2_mean_mfsp_kg,
        )


class HydrogenMfspSimple(AeroMAPSModel):
    def __init__(self, name="hydrogen_mfsp_simple", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        h2_electrolysis_mfsp_reference_years: list = [],
        h2_electrolysis_mfsp_reference_years_values: list = [],
        h2_gas_ccs_mfsp_reference_years: list = [],
        h2_gas_ccs_mfsp_reference_years_values: list = [],
        h2_gas_mfsp_reference_years: list = [],
        h2_gas_mfsp_reference_years_values: list = [],
        h2_coal_ccs_mfsp_reference_years: list = [],
        h2_coal_ccs_mfsp_reference_years_values: list = [],
        h2_coal_mfsp_reference_years: list = [],
        h2_coal_mfsp_reference_years_values: list = [],
        h2_liquefaction_mfsp_reference_years: list = [],
        h2_liquefaction_mfsp_reference_years_values: list = [],
        hydrogen_electrolysis_share: pd.Series = pd.Series(dtype="float64"),
        hydrogen_gas_ccs_share: pd.Series = pd.Series(dtype="float64"),
        hydrogen_gas_share: pd.Series = pd.Series(dtype="float64"),
        hydrogen_coal_ccs_share: pd.Series = pd.Series(dtype="float64"),
        hydrogen_coal_share: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[
        pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series
    ]:
        """Hydrogen MFSP (Minimal fuel selling price) estimates"""

        # Electrolysis
        h2_electrolysis_mfsp = AeromapsInterpolationFunction(
            self,
            h2_electrolysis_mfsp_reference_years,
            h2_electrolysis_mfsp_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "h2_electrolysis_mfsp"] = h2_electrolysis_mfsp

        # Gas CCS
        h2_gas_ccs_mfsp = AeromapsInterpolationFunction(
            self,
            h2_gas_ccs_mfsp_reference_years,
            h2_gas_ccs_mfsp_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "h2_gas_ccs_mfsp"] = h2_gas_ccs_mfsp

        # Gas
        h2_gas_mfsp = AeromapsInterpolationFunction(
            self,
            h2_gas_mfsp_reference_years,
            h2_gas_mfsp_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "h2_gas_mfsp"] = h2_gas_mfsp

        # Coal CCS
        h2_coal_ccs_mfsp = AeromapsInterpolationFunction(
            self,
            h2_coal_ccs_mfsp_reference_years,
            h2_coal_ccs_mfsp_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "h2_coal_ccs_mfsp"] = h2_coal_ccs_mfsp

        # Coal
        h2_coal_mfsp = AeromapsInterpolationFunction(
            self,
            h2_coal_mfsp_reference_years,
            h2_coal_mfsp_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "h2_coal_mfsp"] = h2_coal_mfsp

        # Liquefaction
        h2_liquefaction_mfsp = AeromapsInterpolationFunction(
            self,
            h2_liquefaction_mfsp_reference_years,
            h2_liquefaction_mfsp_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "h2_liquefaction_mfsp"] = h2_liquefaction_mfsp

        # MEAN
        h2_mean_mfsp = (
                h2_electrolysis_mfsp * hydrogen_electrolysis_share / 100
                + h2_gas_ccs_mfsp * hydrogen_gas_ccs_share / 100
                + h2_gas_mfsp * hydrogen_gas_share / 100
                + h2_coal_ccs_mfsp * hydrogen_coal_ccs_share / 100
                + h2_coal_mfsp * hydrogen_coal_share / 100
        )

        self.df.loc[:, "h2_mean_mfsp"] = h2_mean_mfsp

        # MARGINAL

        h2_marginal_mfsp = self.df.loc[
            :,
            [
                "h2_electrolysis_mfsp",
                "h2_gas_ccs_mfsp",
                "h2_gas_mfsp",
                "h2_coal_ccs_mfsp",
                "h2_coal_mfsp",
                "h2_liquefaction_mfsp",
            ],
        ].max(axis="columns")

        self.df.loc[:, "h2_marginal_mfsp"] = h2_marginal_mfsp

        return (
            h2_electrolysis_mfsp,
            h2_gas_ccs_mfsp,
            h2_gas_mfsp,
            h2_coal_ccs_mfsp,
            h2_coal_mfsp,
            h2_liquefaction_mfsp,
            h2_mean_mfsp,
            h2_marginal_mfsp,
        )

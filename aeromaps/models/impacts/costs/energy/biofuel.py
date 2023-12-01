# @Time : 22/02/2023 16:01
# @Author : a.salgas
# @File : biofuel.py
# @Software: PyCharm
from typing import Tuple

import numpy as np
import pandas as pd
from aeromaps.models.base import AeromapsModel, AeromapsInterpolationFunction


class BiofuelCost(AeromapsModel):
    def __init__(self, name="biofuel_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_biofuel: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fog_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fog_emission_factor: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_emission_factor: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_emission_factor: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_emission_factor: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_emission_factor: pd.Series = pd.Series(dtype="float64"),
        kerosene_emission_factor: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fog_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_mfsp: pd.Series = pd.Series(dtype="float64"),
        kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fog_capex: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_capex: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_capex: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_capex: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_capex: pd.Series = pd.Series(dtype="float64"),
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
    ]:
        ### HEFA FOG
        (
            plant_building_scenario_hefa_fog,
            plant_building_cost_hefa_fog,
            biofuel_production_hefa_fog,
            carbon_abatement_cost_hefa_fog,
            biofuel_cost_hefa_fog,
            biofuel_carbon_tax_hefa_fog,
            biofuel_cost_premium_hefa_fog,
            biofuel_mfsp_carbon_tax_supplement_hefa_fog,
        ) = self.pathway_computation(
            biofuel_hefa_fog_emission_factor,
            kerosene_emission_factor,
            biofuel_hefa_fog_mfsp,
            carbon_tax,
            kerosene_market_price,
            biofuel_hefa_fog_capex,
            energy_consumption_biofuel,
            biofuel_hefa_fog_share,
        )

        self.df.loc[:, "plant_building_scenario_hefa_fog"] = plant_building_scenario_hefa_fog
        self.df.loc[:, "plant_building_cost_hefa_fog"] = plant_building_cost_hefa_fog
        self.df.loc[:, "carbon_abatement_cost_hefa_fog"] = carbon_abatement_cost_hefa_fog
        self.df.loc[:, "biofuel_cost_hefa_fog"] = biofuel_cost_hefa_fog
        self.df.loc[:, "biofuel_carbon_tax_hefa_fog"] = biofuel_carbon_tax_hefa_fog
        self.df.loc[:, "biofuel_cost_premium_hefa_fog"] = biofuel_cost_premium_hefa_fog
        self.df.loc[
            :, "biofuel_mfsp_carbon_tax_supplement_hefa_fog"
        ] = biofuel_mfsp_carbon_tax_supplement_hefa_fog

        ### HEFA OTHERS
        (
            plant_building_scenario_hefa_others,
            plant_building_cost_hefa_others,
            biofuel_production_hefa_others,
            carbon_abatement_cost_hefa_others,
            biofuel_cost_hefa_others,
            biofuel_carbon_tax_hefa_others,
            biofuel_cost_premium_hefa_others,
            biofuel_mfsp_carbon_tax_supplement_hefa_others,
        ) = self.pathway_computation(
            biofuel_hefa_others_emission_factor,
            kerosene_emission_factor,
            biofuel_hefa_others_mfsp,
            carbon_tax,
            kerosene_market_price,
            biofuel_hefa_others_capex,
            energy_consumption_biofuel,
            biofuel_hefa_others_share,
        )

        self.df.loc[:, "plant_building_scenario_hefa_others"] = plant_building_scenario_hefa_others
        self.df.loc[:, "plant_building_cost_hefa_others"] = plant_building_cost_hefa_others
        self.df.loc[:, "carbon_abatement_cost_hefa_others"] = carbon_abatement_cost_hefa_others
        self.df.loc[:, "biofuel_cost_hefa_others"] = biofuel_cost_hefa_others
        self.df.loc[:, "biofuel_carbon_tax_hefa_others"] = biofuel_carbon_tax_hefa_others
        self.df.loc[:, "biofuel_cost_premium_hefa_others"] = biofuel_cost_premium_hefa_others
        self.df.loc[
            :, "biofuel_mfsp_carbon_tax_supplement_hefa_others"
        ] = biofuel_mfsp_carbon_tax_supplement_hefa_others

        ### FT OTHERS
        (
            plant_building_scenario_ft_others,
            plant_building_cost_ft_others,
            biofuel_production_ft_others,
            carbon_abatement_cost_ft_others,
            biofuel_cost_ft_others,
            biofuel_carbon_tax_ft_others,
            biofuel_cost_premium_ft_others,
            biofuel_mfsp_carbon_tax_supplement_ft_others,
        ) = self.pathway_computation(
            biofuel_ft_others_emission_factor,
            kerosene_emission_factor,
            biofuel_ft_others_mfsp,
            carbon_tax,
            kerosene_market_price,
            biofuel_ft_others_capex,
            energy_consumption_biofuel,
            biofuel_ft_others_share,
        )

        self.df.loc[:, "plant_building_scenario_ft_others"] = plant_building_scenario_ft_others
        self.df.loc[:, "plant_building_cost_ft_others"] = plant_building_cost_ft_others
        self.df.loc[:, "carbon_abatement_cost_ft_others"] = carbon_abatement_cost_ft_others
        self.df.loc[:, "biofuel_cost_ft_others"] = biofuel_cost_ft_others
        self.df.loc[:, "biofuel_carbon_tax_ft_others"] = biofuel_carbon_tax_ft_others
        self.df.loc[:, "biofuel_cost_premium_ft_others"] = biofuel_cost_premium_ft_others
        self.df.loc[
            :, "biofuel_mfsp_carbon_tax_supplement_ft_others"
        ] = biofuel_mfsp_carbon_tax_supplement_ft_others

        ### FT MSW
        (
            plant_building_scenario_ft_msw,
            plant_building_cost_ft_msw,
            biofuel_production_ft_msw,
            carbon_abatement_cost_ft_msw,
            biofuel_cost_ft_msw,
            biofuel_carbon_tax_ft_msw,
            biofuel_cost_premium_ft_msw,
            biofuel_mfsp_carbon_tax_supplement_ft_msw,
        ) = self.pathway_computation(
            biofuel_ft_msw_emission_factor,
            kerosene_emission_factor,
            biofuel_ft_msw_mfsp,
            carbon_tax,
            kerosene_market_price,
            biofuel_ft_msw_capex,
            energy_consumption_biofuel,
            biofuel_ft_msw_share,
        )

        self.df.loc[:, "plant_building_scenario_ft_msw"] = plant_building_scenario_ft_msw
        self.df.loc[:, "plant_building_cost_ft_msw"] = plant_building_cost_ft_msw
        self.df.loc[:, "carbon_abatement_cost_ft_msw"] = carbon_abatement_cost_ft_msw
        self.df.loc[:, "biofuel_cost_ft_msw"] = biofuel_cost_ft_msw
        self.df.loc[:, "biofuel_carbon_tax_ft_msw"] = biofuel_carbon_tax_ft_msw
        self.df.loc[:, "biofuel_cost_premium_ft_msw"] = biofuel_cost_premium_ft_msw
        self.df.loc[
            :, "biofuel_mfsp_carbon_tax_supplement_ft_msw"
        ] = biofuel_mfsp_carbon_tax_supplement_ft_msw

        ### ATJ
        (
            plant_building_scenario_atj,
            plant_building_cost_atj,
            biofuel_production_atj,
            carbon_abatement_cost_atj,
            biofuel_cost_atj,
            biofuel_carbon_tax_atj,
            biofuel_cost_premium_atj,
            biofuel_mfsp_carbon_tax_supplement_atj,
        ) = self.pathway_computation(
            biofuel_atj_emission_factor,
            kerosene_emission_factor,
            biofuel_atj_mfsp,
            carbon_tax,
            kerosene_market_price,
            biofuel_atj_capex,
            energy_consumption_biofuel,
            biofuel_atj_share,
        )

        self.df.loc[:, "plant_building_scenario_atj"] = plant_building_scenario_atj
        self.df.loc[:, "plant_building_cost_atj"] = plant_building_cost_atj
        self.df.loc[:, "carbon_abatement_cost_atj"] = carbon_abatement_cost_atj
        self.df.loc[:, "biofuel_cost_atj"] = biofuel_cost_atj
        self.df.loc[:, "biofuel_carbon_tax_atj"] = biofuel_carbon_tax_atj
        self.df.loc[:, "biofuel_cost_premium_atj"] = biofuel_cost_premium_atj
        self.df.loc[
            :, "biofuel_mfsp_carbon_tax_supplement_atj"
        ] = biofuel_mfsp_carbon_tax_supplement_atj

        # MEAN tax
        biofuel_mean_carbon_tax_per_l = (
            biofuel_mfsp_carbon_tax_supplement_hefa_fog * biofuel_hefa_fog_share / 100
            + biofuel_mfsp_carbon_tax_supplement_hefa_others * biofuel_hefa_others_share / 100
            + biofuel_mfsp_carbon_tax_supplement_ft_others * biofuel_ft_others_share / 100
            + biofuel_mfsp_carbon_tax_supplement_ft_msw * biofuel_ft_msw_share / 100
            + biofuel_mfsp_carbon_tax_supplement_atj * biofuel_atj_share / 100
        )

        self.df.loc[:, "biofuel_mean_carbon_tax_per_l"] = biofuel_mean_carbon_tax_per_l

        return (
            plant_building_scenario_hefa_fog,
            plant_building_cost_hefa_fog,
            carbon_abatement_cost_hefa_fog,
            biofuel_cost_hefa_fog,
            biofuel_cost_premium_hefa_fog,
            biofuel_carbon_tax_hefa_fog,
            biofuel_mfsp_carbon_tax_supplement_hefa_fog,
            plant_building_scenario_hefa_others,
            plant_building_cost_hefa_others,
            carbon_abatement_cost_hefa_others,
            biofuel_cost_hefa_others,
            biofuel_cost_premium_hefa_others,
            biofuel_carbon_tax_hefa_others,
            biofuel_mfsp_carbon_tax_supplement_hefa_others,
            plant_building_scenario_ft_others,
            plant_building_cost_ft_others,
            carbon_abatement_cost_ft_others,
            biofuel_cost_ft_others,
            biofuel_cost_premium_ft_others,
            biofuel_carbon_tax_ft_others,
            biofuel_mfsp_carbon_tax_supplement_ft_others,
            plant_building_scenario_ft_msw,
            plant_building_cost_ft_msw,
            carbon_abatement_cost_ft_msw,
            biofuel_cost_ft_msw,
            biofuel_cost_premium_ft_msw,
            biofuel_carbon_tax_ft_msw,
            biofuel_mfsp_carbon_tax_supplement_ft_msw,
            plant_building_scenario_atj,
            plant_building_cost_atj,
            carbon_abatement_cost_atj,
            biofuel_cost_atj,
            biofuel_cost_premium_atj,
            biofuel_carbon_tax_atj,
            biofuel_mfsp_carbon_tax_supplement_atj,
            biofuel_mean_carbon_tax_per_l,
        )

    @staticmethod
    def pathway_computation(
        emission_factor: pd.Series = pd.Series(dtype="float64"),
        kerosene_emission_factor: pd.Series = pd.Series(dtype="float64"),
        mfsp: pd.Series = pd.Series(dtype="float64"),
        carbon_tax: pd.Series = pd.Series(dtype="float64"),
        kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
        capex: pd.Series = pd.Series(dtype="float64"),
        energy_consumption_biofuel: pd.Series = pd.Series(dtype="float64"),
        share: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[
        pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series
    ]:
        # Constants :
        # fuel lower heating value in MJ/L at 15 degrees
        fuel_lhv = 35.3

        # https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
        # fuel density at 15 degrees
        fuel_density = 0.804
        plant_life = 30

        # convert emision factor fom gCO2e/MJ to tCo2e/t and mfsp in €/L to €/ton
        emission_factor_ton = emission_factor * fuel_lhv / fuel_density * 1000 / 1000000
        mfsp_ton = mfsp / fuel_density * 1000
        kerosene_price_ton = kerosene_market_price / fuel_density * 1000
        avoided_emission_factor = (
            kerosene_emission_factor * fuel_lhv / fuel_density * 1000 / 1000000
            - emission_factor_ton
        )

        # compute demand scenario in ton for the given pathway
        demand_scenario = (
            energy_consumption_biofuel / (fuel_lhv / fuel_density) / 1000 * share / 100
        )

        indexes = demand_scenario.index

        # Additional plant capacity building needed (in ton/day output size) for a given year
        plant_building_scenario = pd.Series(np.zeros(len(indexes)), indexes)
        # Relative CAPEX cost to build the new facilities in M€2020
        plant_building_cost = pd.Series(np.zeros(len(indexes)), indexes)
        # Annual production in tons
        biofuel_production = pd.Series(np.zeros(len(indexes)), indexes)
        # carbon abatement cost in €/ton
        carbon_abatement_cost = pd.Series(np.zeros(len(indexes)), indexes)
        # Total annual production cost in M€2020
        biofuel_cost = pd.Series(np.zeros(len(indexes)), indexes)
        # Total extra cost linked to carbon tax
        biofuel_carbon_tax_cost = pd.Series(np.zeros(len(indexes)), indexes)
        # Total annual cost premium in M€2020
        biofuel_cost_premium = pd.Series(np.zeros(len(indexes)), indexes)
        # Extra cost on mfsp linked to carbon tax
        mfsp_supplement_carbon_tax = pd.Series(np.zeros(len(indexes)), indexes)

        # For each year of the demand scenario the demand is matched by the production
        for year in list(demand_scenario.index)[:-1]:
            # Production missing in year n+1 must be supplied by plant built in year n
            if biofuel_production[year + 1] < demand_scenario[year + 1]:
                # Getting the production not matched by plants already commissioned
                missing_production = demand_scenario[year + 1] - biofuel_production[year + 1]
                # Converting the missing production to a capacity (in t/day)
                capacity_to_build = (
                    missing_production / 365.25 / 0.95
                )  # capacity to build in t/day production, taking into account a load_factor of 0.95
                capex_year = (
                    capacity_to_build * capex[year] * 1000 / 1000000
                )  # conversion in € per ton per day and in M€
                # Adding the new capacity and related cost into the annual buildup dict
                plant_building_cost[year] = capex_year
                plant_building_scenario[year] = capacity_to_build

                # When production ends: either at the end of plant life or the end of the scenario;
                end_bound = min(list(demand_scenario.index)[-1], year + plant_life)
                # Adding new plant production to future years and computing total cost associated
                for i in range(year + 1, end_bound + 1):
                    biofuel_production[i] = biofuel_production[i] + missing_production

            # Compute the total biofuel cost of the scenario (M€)
            biofuel_cost[year + 1] = mfsp_ton[year + 1] * demand_scenario[year + 1] / 1000000

            # Compute the total cost premium (M€)
            biofuel_cost_premium[year + 1] = (
                (mfsp_ton[year + 1] - kerosene_price_ton[year + 1])
                * demand_scenario[year + 1]
                / 1000000
            )

            # Compute the carbon tax (M€)

            biofuel_carbon_tax_cost[year + 1] = (
                carbon_tax[year + 1]
                * emission_factor_ton[year + 1]
                * demand_scenario[year + 1]
                / 1000000
            )

            mfsp_supplement_carbon_tax[year + 1] = (
                carbon_tax[year + 1] * emission_factor_ton[year + 1] / 1000 * fuel_density
            )

            # Abatement cost in €/tCO2e (= overcost for a ton of biofuel/avoided emissions)
            carbon_abatement_cost[year + 1] = (
                mfsp_ton[year + 1] - kerosene_price_ton[year + 1]
            ) / avoided_emission_factor[year + 1]

        return (
            plant_building_scenario,
            plant_building_cost,
            biofuel_production,
            carbon_abatement_cost,
            biofuel_cost,
            biofuel_carbon_tax_cost,
            biofuel_cost_premium,
            mfsp_supplement_carbon_tax,
        )


class BiofuelMfsp(AeromapsModel):
    def __init__(self, name="biofuel_mfsp", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        biofuel_hefa_fog_mfsp_reference_years: list = [],
        biofuel_hefa_fog_mfsp_reference_years_values: list = [],
        biofuel_hefa_others_mfsp_reference_years: list = [],
        biofuel_hefa_others_mfsp_reference_years_values: list = [],
        biofuel_ft_others_mfsp_reference_years: list = [],
        biofuel_ft_others_mfsp_reference_years_values: list = [],
        biofuel_ft_msw_mfsp_reference_years: list = [],
        biofuel_ft_msw_mfsp_reference_years_values: list = [],
        biofuel_atj_mfsp_reference_years: list = [],
        biofuel_atj_mfsp_reference_years_values: list = [],
        biofuel_hefa_fog_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_share: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Biofuel MFSP (Minimal fuel selling price) estimates"""

        # HEFA FOG
        biofuel_hefa_fog_mfsp = AeromapsInterpolationFunction(
            self,
            biofuel_hefa_fog_mfsp_reference_years,
            biofuel_hefa_fog_mfsp_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_hefa_fog_mfsp"] = biofuel_hefa_fog_mfsp

        # HEFA OTHERS
        biofuel_hefa_others_mfsp = AeromapsInterpolationFunction(
            self,
            biofuel_hefa_others_mfsp_reference_years,
            biofuel_hefa_others_mfsp_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_hefa_others_mfsp"] = biofuel_hefa_others_mfsp

        # FT OTHERS
        biofuel_ft_others_mfsp = AeromapsInterpolationFunction(
            self,
            biofuel_ft_others_mfsp_reference_years,
            biofuel_ft_others_mfsp_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_ft_others_mfsp"] = biofuel_ft_others_mfsp

        # FT MSW
        biofuel_ft_msw_mfsp = AeromapsInterpolationFunction(
            self,
            biofuel_ft_msw_mfsp_reference_years,
            biofuel_ft_msw_mfsp_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_ft_msw_mfsp"] = biofuel_ft_msw_mfsp

        # ATJ
        biofuel_atj_mfsp = AeromapsInterpolationFunction(
            self,
            biofuel_atj_mfsp_reference_years,
            biofuel_atj_mfsp_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_atj_mfsp"] = biofuel_atj_mfsp

        # MEAN
        biofuel_mean_mfsp = (
            biofuel_hefa_fog_mfsp * biofuel_hefa_fog_share / 100
            + biofuel_hefa_others_mfsp * biofuel_hefa_others_share / 100
            + biofuel_ft_others_mfsp * biofuel_ft_others_share / 100
            + biofuel_ft_msw_mfsp * biofuel_ft_msw_share / 100
            + biofuel_atj_mfsp * biofuel_atj_share / 100
        )

        self.df.loc[:, "biofuel_mean_mfsp"] = biofuel_mean_mfsp

        # MARGINAL

        biofuel_marginal_mfsp = self.df.loc[
            :,
            [
                "biofuel_hefa_fog_mfsp",
                "biofuel_hefa_others_mfsp",
                "biofuel_ft_others_mfsp",
                "biofuel_ft_msw_mfsp",
                "biofuel_atj_mfsp",
            ],
        ].max(axis="columns")

        self.df.loc[:, "biofuel_marginal_mfsp"] = biofuel_marginal_mfsp

        return (
            biofuel_hefa_fog_mfsp,
            biofuel_hefa_others_mfsp,
            biofuel_ft_others_mfsp,
            biofuel_ft_msw_mfsp,
            biofuel_atj_mfsp,
            biofuel_mean_mfsp,
            biofuel_marginal_mfsp,
        )


class BiofuelCapex(AeromapsModel):
    def __init__(self, name="biofuel_capex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        biofuel_hefa_fog_capex_reference_years: list = [],
        biofuel_hefa_fog_capex_reference_years_values: list = [],
        biofuel_hefa_others_capex_reference_years: list = [],
        biofuel_hefa_others_capex_reference_years_values: list = [],
        biofuel_ft_others_capex_reference_years: list = [],
        biofuel_ft_others_capex_reference_years_values: list = [],
        biofuel_ft_msw_capex_reference_years: list = [],
        biofuel_ft_msw_capex_reference_years_values: list = [],
        biofuel_atj_capex_reference_years: list = [],
        biofuel_atj_capex_reference_years_values: list = [],
        biofuel_hefa_fog_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_share: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Biofuel CAPEX (CApital EXPenditures) estimates"""

        # HEFA FOG
        biofuel_hefa_fog_capex = AeromapsInterpolationFunction(
            self,
            biofuel_hefa_fog_capex_reference_years,
            biofuel_hefa_fog_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_hefa_fog_capex"] = biofuel_hefa_fog_capex

        # HEFA OTHERS
        biofuel_hefa_others_capex = AeromapsInterpolationFunction(
            self,
            biofuel_hefa_others_capex_reference_years,
            biofuel_hefa_others_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_hefa_others_capex"] = biofuel_hefa_others_capex

        # FT OTHERS
        biofuel_ft_others_capex = AeromapsInterpolationFunction(
            self,
            biofuel_ft_others_capex_reference_years,
            biofuel_ft_others_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_ft_others_capex"] = biofuel_ft_others_capex

        # FT MSW
        biofuel_ft_msw_capex = AeromapsInterpolationFunction(
            self,
            biofuel_ft_msw_capex_reference_years,
            biofuel_ft_msw_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_ft_msw_capex"] = biofuel_ft_msw_capex

        # ATJ
        biofuel_atj_capex = AeromapsInterpolationFunction(
            self,
            biofuel_atj_capex_reference_years,
            biofuel_atj_capex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_atj_capex"] = biofuel_atj_capex

        # MEAN
        biofuel_mean_capex = (
            biofuel_hefa_fog_capex * biofuel_hefa_fog_share / 100
            + biofuel_hefa_others_capex * biofuel_hefa_others_share / 100
            + biofuel_ft_others_capex * biofuel_ft_others_share / 100
            + biofuel_ft_msw_capex * biofuel_ft_msw_share / 100
            + biofuel_atj_capex * biofuel_atj_share / 100
        )

        self.df.loc[:, "biofuel_mean_capex"] = biofuel_mean_capex

        return (
            biofuel_hefa_fog_capex,
            biofuel_hefa_others_capex,
            biofuel_ft_others_capex,
            biofuel_ft_msw_capex,
            biofuel_atj_capex,
            biofuel_mean_capex,
        )

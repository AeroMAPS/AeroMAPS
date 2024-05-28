# @Time : 22/02/2023 16:01
# @Author : a.salgas
# @File : biofuel.py
# @Software: PyCharm
from typing import Tuple

import numpy as np
import pandas as pd
from pandas import Series

from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class BiofuelCostSimple(AeroMAPSModel):
    def __init__(self, name="biofuel_cost_simple", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_biofuel: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fog_emission_factor: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_emission_factor: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_emission_factor: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_emission_factor: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_emission_factor: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fog_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fog_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_mfsp: pd.Series = pd.Series(dtype="float64"),
        carbon_tax: pd.Series = pd.Series(dtype="float64"),
        plant_lifespan: float = 0.0,
        lhv_biofuel: float = 0.0,
        density_biofuel: float = 0.0,
    ) -> tuple[
        Series, Series, Series, Series, Series, Series, Series, Series, Series, Series, Series, Series, Series, Series, Series, Series, Series, Series, Series, Series,
        Series]:
        ### HEFA FOG
        (
            plant_building_scenario_hefa_fog,
            biofuel_production_hefa_fog,
            biofuel_cost_hefa_fog,
            biofuel_carbon_tax_hefa_fog,
            biofuel_mfsp_carbon_tax_supplement_hefa_fog,
        ) = self._pathway_computation(
            biofuel_hefa_fog_emission_factor,
            biofuel_hefa_fog_mfsp,
            carbon_tax,
            energy_consumption_biofuel,
            biofuel_hefa_fog_share,
            plant_lifespan,
            lhv_biofuel,
            density_biofuel,
        )

        self.df.loc[:, "plant_building_scenario_hefa_fog"] = plant_building_scenario_hefa_fog
        self.df.loc[:, "biofuel_cost_hefa_fog"] = biofuel_cost_hefa_fog
        self.df.loc[:, "biofuel_carbon_tax_hefa_fog"] = biofuel_carbon_tax_hefa_fog
        self.df.loc[
            :, "biofuel_mfsp_carbon_tax_supplement_hefa_fog"
        ] = biofuel_mfsp_carbon_tax_supplement_hefa_fog

        ### HEFA OTHERS
        (
            plant_building_scenario_hefa_others,
            biofuel_production_hefa_others,
            biofuel_cost_hefa_others,
            biofuel_carbon_tax_hefa_others,
            biofuel_mfsp_carbon_tax_supplement_hefa_others,
        ) = self._pathway_computation(
            biofuel_hefa_others_emission_factor,
            biofuel_hefa_others_mfsp,
            carbon_tax,
            energy_consumption_biofuel,
            biofuel_hefa_others_share,
            plant_lifespan,
            lhv_biofuel,
            density_biofuel,
        )

        self.df.loc[:, "plant_building_scenario_hefa_others"] = plant_building_scenario_hefa_others
        self.df.loc[:, "biofuel_cost_hefa_others"] = biofuel_cost_hefa_others
        self.df.loc[:, "biofuel_carbon_tax_hefa_others"] = biofuel_carbon_tax_hefa_others
        self.df.loc[
        :, "biofuel_mfsp_carbon_tax_supplement_hefa_others"
        ] = biofuel_mfsp_carbon_tax_supplement_hefa_others

        ### FT OTHERS
        (
            plant_building_scenario_ft_others,
            biofuel_production_ft_others,
            biofuel_cost_ft_others,
            biofuel_carbon_tax_ft_others,
            biofuel_mfsp_carbon_tax_supplement_ft_others,
        ) = self._pathway_computation(
            biofuel_ft_others_emission_factor,
            biofuel_ft_others_mfsp,
            carbon_tax,
            energy_consumption_biofuel,
            biofuel_ft_others_share,
            plant_lifespan,
            lhv_biofuel,
            density_biofuel,
        )

        self.df.loc[:, "plant_building_scenario_ft_others"] = plant_building_scenario_ft_others
        self.df.loc[:, "biofuel_cost_ft_others"] = biofuel_cost_ft_others
        self.df.loc[:, "biofuel_carbon_tax_ft_others"] = biofuel_carbon_tax_ft_others
        self.df.loc[
        :, "biofuel_mfsp_carbon_tax_supplement_ft_others"
        ] = biofuel_mfsp_carbon_tax_supplement_ft_others

        ### FT MSW
        (
            plant_building_scenario_ft_msw,
            biofuel_production_ft_msw,
            biofuel_cost_ft_msw,
            biofuel_carbon_tax_ft_msw,
            biofuel_mfsp_carbon_tax_supplement_ft_msw,
        ) = self._pathway_computation(
            biofuel_ft_msw_emission_factor,
            biofuel_ft_msw_mfsp,
            carbon_tax,
            energy_consumption_biofuel,
            biofuel_ft_msw_share,
            plant_lifespan,
            lhv_biofuel,
            density_biofuel,
        )

        self.df.loc[:, "plant_building_scenario_ft_msw"] = plant_building_scenario_ft_msw
        self.df.loc[:, "biofuel_cost_ft_msw"] = biofuel_cost_ft_msw
        self.df.loc[:, "biofuel_carbon_tax_ft_msw"] = biofuel_carbon_tax_ft_msw
        self.df.loc[
        :, "biofuel_mfsp_carbon_tax_supplement_ft_msw"
        ] = biofuel_mfsp_carbon_tax_supplement_ft_msw

        ### ATJ
        (
            plant_building_scenario_atj,
            biofuel_production_atj,
            biofuel_cost_atj,
            biofuel_carbon_tax_atj,
            biofuel_mfsp_carbon_tax_supplement_atj,
        ) = self._pathway_computation(
            biofuel_atj_emission_factor,
            biofuel_atj_mfsp,
            carbon_tax,
            energy_consumption_biofuel,
            biofuel_atj_share,
            plant_lifespan,
            lhv_biofuel,
            density_biofuel,
        )

        self.df.loc[:, "plant_building_scenario_atj"] = plant_building_scenario_atj
        self.df.loc[:, "biofuel_cost_atj"] = biofuel_cost_atj
        self.df.loc[:, "biofuel_carbon_tax_atj"] = biofuel_carbon_tax_atj
        self.df.loc[
        :, "biofuel_mfsp_carbon_tax_supplement_atj"
        ] = biofuel_mfsp_carbon_tax_supplement_atj

        # MEAN tax
        biofuel_mean_carbon_tax_per_l = (
            biofuel_mfsp_carbon_tax_supplement_hefa_fog.fillna(0) * biofuel_hefa_fog_share.fillna(0) / 100
            + biofuel_mfsp_carbon_tax_supplement_hefa_others.fillna(0) * biofuel_hefa_others_share.fillna(0) / 100
            + biofuel_mfsp_carbon_tax_supplement_ft_others.fillna(0) * biofuel_ft_others_share.fillna(0) / 100
            + biofuel_mfsp_carbon_tax_supplement_ft_msw.fillna(0) * biofuel_ft_msw_share.fillna(0) / 100
            + biofuel_mfsp_carbon_tax_supplement_atj.fillna(0) * biofuel_atj_share.fillna(0) / 100
        )

        self.df.loc[:, "biofuel_mean_carbon_tax_per_l"] = biofuel_mean_carbon_tax_per_l

        return (
            plant_building_scenario_hefa_fog,
            biofuel_cost_hefa_fog,
            biofuel_carbon_tax_hefa_fog,
            biofuel_mfsp_carbon_tax_supplement_hefa_fog,
            plant_building_scenario_hefa_others,
            biofuel_cost_hefa_others,
            biofuel_carbon_tax_hefa_others,
            biofuel_mfsp_carbon_tax_supplement_hefa_others,
            plant_building_scenario_ft_others,
            biofuel_cost_ft_others,
            biofuel_carbon_tax_ft_others,
            biofuel_mfsp_carbon_tax_supplement_ft_others,
            plant_building_scenario_ft_msw,
            biofuel_cost_ft_msw,
            biofuel_carbon_tax_ft_msw,
            biofuel_mfsp_carbon_tax_supplement_ft_msw,
            plant_building_scenario_atj,
            biofuel_cost_atj,
            biofuel_carbon_tax_atj,
            biofuel_mfsp_carbon_tax_supplement_atj,
            biofuel_mean_carbon_tax_per_l,
        )


    def _pathway_computation(
        self,
        emission_factor: pd.Series = pd.Series(dtype="float64"),
        mfsp: pd.Series = pd.Series(dtype="float64"),
        carbon_tax: pd.Series = pd.Series(dtype="float64"),
        energy_consumption_biofuel: pd.Series = pd.Series(dtype="float64"),
        share: pd.Series = pd.Series(dtype="float64"),
        plant_lifespan: float = 0.0,
        lhv_biofuel: float = 0.0,
        density_biofuel: float = 0.0,
    ) -> Tuple[
        pd.Series, pd.Series, pd.Series, pd.Series, pd.Series,
    ]:
        load_factor=0.95
        # Demand scenario for the pathway in MJ
        demand_scenario = energy_consumption_biofuel * share / 100

        indexes = demand_scenario.index

        # Additional plant capacity building needed (in ton/day output size) for a given year
        plant_building_scenario = pd.Series(np.zeros(len(indexes)), indexes)
        # Annual production in tons
        biofuel_production = pd.Series(np.zeros(len(indexes)), indexes)
        # Total annual production cost in M€2020
        biofuel_cost = pd.Series(np.zeros(len(indexes)), indexes)
        # Total extra cost linked to carbon tax
        biofuel_carbon_tax_cost = pd.Series(np.zeros(len(indexes)), indexes)

        # Extra cost on mfsp linked to carbon tax
        mfsp_supplement_carbon_tax = pd.Series(np.zeros(len(indexes)), indexes)

        # For each year of the demand scenario the demand is matched by the production
        for year in list(demand_scenario.index)[:-1]:
            # Production missing in year n+1 must be supplied by plant built in year n
            if biofuel_production[year + 1] < demand_scenario[year + 1]:
                # Getting the production not matched by plants already commissioned [MJ]
                missing_production = demand_scenario[year + 1] - biofuel_production[year + 1]
                # Converting the missing production to a capacity [in kg/day capacity], including availability of plant
                missing_production_kg = missing_production / lhv_biofuel
                missing_production_litres = missing_production_kg / density_biofuel
                capacity_to_build_kg_day = missing_production_kg / load_factor / 365
                plant_building_scenario[year] = capacity_to_build_kg_day
                # When production ends: either at the end of plant life or the end of the scenario;
                end_bound = min(list(demand_scenario.index)[-1], year + int(plant_lifespan))
                # Adding new plant production to future years and computing total cost associated
                biofuel_production[range(year + 1, end_bound + 1)] +=  missing_production

            # Compute the total biofuel cost of the scenario (M€)
            biofuel_cost[year + 1] = mfsp[year + 1]/density_biofuel/lhv_biofuel * demand_scenario[year + 1] / 1000000


            # Compute the carbon tax (M€)

            biofuel_carbon_tax_cost[year + 1] = (
                carbon_tax[year + 1]
                * emission_factor[year + 1]
                * demand_scenario[year + 1]
                / 1000000
            )

            mfsp_supplement_carbon_tax[year + 1] = (
                carbon_tax[year + 1] * emission_factor[year + 1] / 1000 * density_biofuel
            )


        return (
            plant_building_scenario,
            biofuel_production,
            biofuel_cost,
            biofuel_carbon_tax_cost,
            mfsp_supplement_carbon_tax,
        )


class BiofuelMfsp(AeroMAPSModel):
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



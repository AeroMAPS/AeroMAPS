# @Time : 22/02/2023 16:01
# @Author : a.salgas
# @File : biofuel.py
# @Software: PyCharm
from typing import Tuple

import numpy as np
import pandas as pd
from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class BiofuelCost(AeroMAPSModel):
    def __init__(self, name="biofuel_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_biofuel: pd.Series,
        biofuel_hefa_fog_share: pd.Series,
        biofuel_hefa_others_share: pd.Series,
        biofuel_atj_share: pd.Series,
        biofuel_ft_msw_share: pd.Series,
        biofuel_ft_others_share: pd.Series,
        biofuel_hefa_fog_emission_factor: pd.Series,
        biofuel_hefa_others_emission_factor: pd.Series,
        biofuel_ft_others_emission_factor: pd.Series,
        biofuel_ft_msw_emission_factor: pd.Series,
        biofuel_atj_emission_factor: pd.Series,
        kerosene_emission_factor: pd.Series,
        kerosene_market_price: pd.Series,
        biofuel_hefa_fog_capex: pd.Series,
        biofuel_hefa_fog_var_opex: pd.Series,
        biofuel_hefa_fog_feedstock_cost: pd.Series,
        biofuel_hefa_others_capex: pd.Series,
        biofuel_hefa_others_var_opex: pd.Series,
        biofuel_hefa_others_feedstock_cost: pd.Series,
        biofuel_hefa_fuel_efficiency: pd.Series,
        biofuel_hefa_oil_efficiency: pd.Series,
        biofuel_ft_others_capex: pd.Series,
        biofuel_ft_others_var_opex: pd.Series,
        biofuel_ft_others_feedstock_cost: pd.Series,
        biofuel_ft_msw_capex: pd.Series,
        biofuel_ft_msw_feedstock_cost: pd.Series,
        biofuel_ft_msw_var_opex: pd.Series,
        biofuel_ft_efficiency: pd.Series,
        biofuel_atj_capex: pd.Series,
        biofuel_atj_var_opex: pd.Series,
        biofuel_atj_feedstock_cost: pd.Series,
        biofuel_atj_efficiency: pd.Series,
        carbon_tax: pd.Series,
        exogenous_carbon_price_trajectory: pd.Series,
        plant_lifespan: float,
        private_discount_rate: float,
        social_discount_rate: float,
        lhv_biofuel: float,
        density_biofuel: float,
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
        ### HEFA FOG
        # print('HEFOG')
        (
            plant_building_scenario_hefa_fog,
            plant_building_cost_hefa_fog,
            biofuel_production_hefa_fog,
            carbon_abatement_cost_hefa_fog,
            biofuel_cost_hefa_fog,
            biofuel_mean_capex_share_hefa_fog,
            biofuel_mean_var_opex_share_hefa_fog,
            biofuel_mean_feedstock_share_hefa_fog,
            biofuel_hefa_fog_mfsp,
            biofuel_carbon_tax_hefa_fog,
            biofuel_cost_premium_hefa_fog,
            biofuel_mfsp_carbon_tax_supplement_hefa_fog,
            specific_carbon_abatement_cost_hefa_fog,
            generic_specific_carbon_abatement_cost_hefa_fog,
        ) = self._pathway_computation(
            biofuel_hefa_fog_emission_factor,
            kerosene_emission_factor,
            carbon_tax,
            kerosene_market_price,
            energy_consumption_biofuel,
            biofuel_hefa_fog_share,
            biofuel_hefa_fog_feedstock_cost,
            biofuel_hefa_fog_var_opex,
            biofuel_hefa_fog_capex,
            biofuel_hefa_fuel_efficiency,
            exogenous_carbon_price_trajectory,
            plant_lifespan,
            private_discount_rate,
            social_discount_rate,
            lhv_biofuel,
            density_biofuel,
        )

        self.df.loc[:, "plant_building_scenario_hefa_fog"] = plant_building_scenario_hefa_fog
        self.df.loc[:, "plant_building_cost_hefa_fog"] = plant_building_cost_hefa_fog
        self.df.loc[:, "carbon_abatement_cost_hefa_fog"] = carbon_abatement_cost_hefa_fog
        self.df.loc[:, "specific_carbon_abatement_cost_hefa_fog"] = (
            specific_carbon_abatement_cost_hefa_fog
        )
        self.df.loc[:, "generic_specific_carbon_abatement_cost_hefa_fog"] = (
            generic_specific_carbon_abatement_cost_hefa_fog
        )
        self.df.loc[:, "biofuel_cost_hefa_fog"] = biofuel_cost_hefa_fog
        self.df.loc[:, "biofuel_mean_capex_share_hefa_fog"] = biofuel_mean_capex_share_hefa_fog
        self.df.loc[:, "biofuel_mean_var_opex_share_hefa_fog"] = (
            biofuel_mean_var_opex_share_hefa_fog
        )
        self.df.loc[:, "biofuel_mean_feedstock_share_hefa_fog"] = (
            biofuel_mean_feedstock_share_hefa_fog
        )
        self.df.loc[:, "biofuel_hefa_fog_mfsp"] = biofuel_hefa_fog_mfsp
        self.df.loc[:, "biofuel_carbon_tax_hefa_fog"] = biofuel_carbon_tax_hefa_fog
        self.df.loc[:, "biofuel_cost_premium_hefa_fog"] = biofuel_cost_premium_hefa_fog
        self.df.loc[:, "biofuel_mfsp_carbon_tax_supplement_hefa_fog"] = (
            biofuel_mfsp_carbon_tax_supplement_hefa_fog
        )

        ### HEFA OTHERS
        # print('HEFA OTHER')
        (
            plant_building_scenario_hefa_others,
            plant_building_cost_hefa_others,
            biofuel_production_hefa_others,
            carbon_abatement_cost_hefa_others,
            biofuel_cost_hefa_others,
            biofuel_mean_capex_share_hefa_others,
            biofuel_mean_var_opex_share_hefa_others,
            biofuel_mean_feedstock_share_hefa_others,
            biofuel_hefa_others_mfsp,
            biofuel_carbon_tax_hefa_others,
            biofuel_cost_premium_hefa_others,
            biofuel_mfsp_carbon_tax_supplement_hefa_others,
            specific_carbon_abatement_cost_hefa_others,
            generic_specific_carbon_abatement_cost_hefa_others,
        ) = self._pathway_computation(
            biofuel_hefa_others_emission_factor,
            kerosene_emission_factor,
            carbon_tax,
            kerosene_market_price,
            energy_consumption_biofuel,
            biofuel_hefa_others_share,
            biofuel_hefa_others_feedstock_cost,
            biofuel_hefa_others_var_opex,
            biofuel_hefa_others_capex,
            biofuel_hefa_oil_efficiency * biofuel_hefa_fuel_efficiency,
            exogenous_carbon_price_trajectory,
            plant_lifespan,
            private_discount_rate,
            social_discount_rate,
            lhv_biofuel,
            density_biofuel,
        )

        self.df.loc[:, "plant_building_scenario_hefa_others"] = plant_building_scenario_hefa_others
        self.df.loc[:, "plant_building_cost_hefa_others"] = plant_building_cost_hefa_others
        self.df.loc[:, "carbon_abatement_cost_hefa_others"] = carbon_abatement_cost_hefa_others
        self.df.loc[:, "specific_carbon_abatement_cost_hefa_others"] = (
            specific_carbon_abatement_cost_hefa_others
        )
        self.df.loc[:, "generic_specific_carbon_abatement_cost_hefa_others"] = (
            generic_specific_carbon_abatement_cost_hefa_others
        )
        self.df.loc[:, "biofuel_cost_hefa_others"] = biofuel_cost_hefa_others
        self.df.loc[:, "biofuel_mean_capex_share_hefa_others"] = (
            biofuel_mean_capex_share_hefa_others
        )
        self.df.loc[:, "biofuel_mean_var_opex_share_hefa_others"] = (
            biofuel_mean_var_opex_share_hefa_others
        )
        self.df.loc[:, "biofuel_mean_feedstock_share_hefa_others"] = (
            biofuel_mean_feedstock_share_hefa_others
        )
        self.df.loc[:, "biofuel_hefa_others_mfsp"] = biofuel_hefa_others_mfsp
        self.df.loc[:, "biofuel_carbon_tax_hefa_others"] = biofuel_carbon_tax_hefa_others
        self.df.loc[:, "biofuel_cost_premium_hefa_others"] = biofuel_cost_premium_hefa_others
        self.df.loc[:, "biofuel_mfsp_carbon_tax_supplement_hefa_others"] = (
            biofuel_mfsp_carbon_tax_supplement_hefa_others
        )

        ### FT OTHERS
        # print('FT OTHERS')
        (
            plant_building_scenario_ft_others,
            plant_building_cost_ft_others,
            biofuel_production_ft_others,
            carbon_abatement_cost_ft_others,
            biofuel_cost_ft_others,
            biofuel_mean_capex_share_ft_others,
            biofuel_mean_var_opex_share_ft_others,
            biofuel_mean_feedstock_share_ft_others,
            biofuel_ft_others_mfsp,
            biofuel_carbon_tax_ft_others,
            biofuel_cost_premium_ft_others,
            biofuel_mfsp_carbon_tax_supplement_ft_others,
            specific_carbon_abatement_cost_ft_others,
            generic_specific_carbon_abatement_cost_ft_others,
        ) = self._pathway_computation(
            biofuel_ft_others_emission_factor,
            kerosene_emission_factor,
            carbon_tax,
            kerosene_market_price,
            energy_consumption_biofuel,
            biofuel_ft_others_share,
            biofuel_ft_others_feedstock_cost,
            biofuel_ft_others_var_opex,
            biofuel_ft_others_capex,
            biofuel_ft_efficiency,
            exogenous_carbon_price_trajectory,
            plant_lifespan,
            private_discount_rate,
            social_discount_rate,
            lhv_biofuel,
            density_biofuel,
        )

        self.df.loc[:, "plant_building_scenario_ft_others"] = plant_building_scenario_ft_others
        self.df.loc[:, "plant_building_cost_ft_others"] = plant_building_cost_ft_others
        self.df.loc[:, "carbon_abatement_cost_ft_others"] = carbon_abatement_cost_ft_others
        self.df.loc[:, "specific_carbon_abatement_cost_ft_others"] = (
            specific_carbon_abatement_cost_ft_others
        )
        self.df.loc[:, "generic_specific_carbon_abatement_cost_ft_others"] = (
            generic_specific_carbon_abatement_cost_ft_others
        )
        self.df.loc[:, "biofuel_cost_ft_others"] = biofuel_cost_ft_others
        self.df.loc[:, "biofuel_mean_capex_share_ft_others"] = biofuel_mean_capex_share_ft_others
        self.df.loc[:, "biofuel_mean_var_opex_share_ft_others"] = (
            biofuel_mean_var_opex_share_ft_others
        )
        self.df.loc[:, "biofuel_mean_feedstock_share_ft_others"] = (
            biofuel_mean_feedstock_share_ft_others
        )
        self.df.loc[:, "biofuel_ft_others_mfsp"] = biofuel_ft_others_mfsp
        self.df.loc[:, "biofuel_carbon_tax_ft_others"] = biofuel_carbon_tax_ft_others
        self.df.loc[:, "biofuel_cost_premium_ft_others"] = biofuel_cost_premium_ft_others
        self.df.loc[:, "biofuel_mfsp_carbon_tax_supplement_ft_others"] = (
            biofuel_mfsp_carbon_tax_supplement_ft_others
        )

        ### FT MSW
        # print('FT MSW')
        (
            plant_building_scenario_ft_msw,
            plant_building_cost_ft_msw,
            biofuel_production_ft_msw,
            carbon_abatement_cost_ft_msw,
            biofuel_cost_ft_msw,
            biofuel_mean_capex_share_ft_msw,
            biofuel_mean_var_opex_share_ft_msw,
            biofuel_mean_feedstock_share_ft_msw,
            biofuel_ft_msw_mfsp,
            biofuel_carbon_tax_ft_msw,
            biofuel_cost_premium_ft_msw,
            biofuel_mfsp_carbon_tax_supplement_ft_msw,
            specific_carbon_abatement_cost_ft_msw,
            generic_specific_carbon_abatement_cost_ft_msw,
        ) = self._pathway_computation(
            biofuel_ft_msw_emission_factor,
            kerosene_emission_factor,
            carbon_tax,
            kerosene_market_price,
            energy_consumption_biofuel,
            biofuel_ft_msw_share,
            biofuel_ft_msw_feedstock_cost,
            biofuel_ft_msw_var_opex,
            biofuel_ft_msw_capex,
            biofuel_ft_efficiency,
            exogenous_carbon_price_trajectory,
            plant_lifespan,
            private_discount_rate,
            social_discount_rate,
            lhv_biofuel,
            density_biofuel,
        )

        self.df.loc[:, "plant_building_scenario_ft_msw"] = plant_building_scenario_ft_msw
        self.df.loc[:, "plant_building_cost_ft_msw"] = plant_building_cost_ft_msw
        self.df.loc[:, "carbon_abatement_cost_ft_msw"] = carbon_abatement_cost_ft_msw
        self.df.loc[:, "specific_carbon_abatement_cost_ft_msw"] = (
            specific_carbon_abatement_cost_ft_msw
        )
        self.df.loc[:, "generic_specific_carbon_abatement_cost_ft_msw"] = (
            generic_specific_carbon_abatement_cost_ft_msw
        )
        self.df.loc[:, "biofuel_cost_ft_msw"] = biofuel_cost_ft_msw
        self.df.loc[:, "biofuel_mean_capex_share_ft_msw"] = biofuel_mean_capex_share_ft_msw
        self.df.loc[:, "biofuel_mean_var_opex_share_ft_msw"] = biofuel_mean_var_opex_share_ft_msw
        self.df.loc[:, "biofuel_mean_feedstock_share_ft_msw"] = biofuel_mean_feedstock_share_ft_msw
        self.df.loc[:, "biofuel_ft_msw_mfsp"] = biofuel_ft_msw_mfsp
        self.df.loc[:, "biofuel_carbon_tax_ft_msw"] = biofuel_carbon_tax_ft_msw
        self.df.loc[:, "biofuel_cost_premium_ft_msw"] = biofuel_cost_premium_ft_msw
        self.df.loc[:, "biofuel_mfsp_carbon_tax_supplement_ft_msw"] = (
            biofuel_mfsp_carbon_tax_supplement_ft_msw
        )

        ### ATJ
        # print('ATJ')
        (
            plant_building_scenario_atj,
            plant_building_cost_atj,
            biofuel_production_atj,
            carbon_abatement_cost_atj,
            biofuel_cost_atj,
            biofuel_mean_capex_share_atj,
            biofuel_mean_var_opex_share_atj,
            biofuel_mean_feedstock_share_atj,
            biofuel_atj_mfsp,
            biofuel_carbon_tax_atj,
            biofuel_cost_premium_atj,
            biofuel_mfsp_carbon_tax_supplement_atj,
            specific_carbon_abatement_cost_atj,
            generic_specific_carbon_abatement_cost_atj,
        ) = self._pathway_computation(
            biofuel_atj_emission_factor,
            kerosene_emission_factor,
            carbon_tax,
            kerosene_market_price,
            energy_consumption_biofuel,
            biofuel_atj_share,
            biofuel_atj_feedstock_cost,
            biofuel_atj_var_opex,
            biofuel_atj_capex,
            biofuel_atj_efficiency,
            exogenous_carbon_price_trajectory,
            plant_lifespan,
            private_discount_rate,
            social_discount_rate,
            lhv_biofuel,
            density_biofuel,
        )

        self.df.loc[:, "plant_building_scenario_atj"] = plant_building_scenario_atj
        self.df.loc[:, "plant_building_cost_atj"] = plant_building_cost_atj
        self.df.loc[:, "carbon_abatement_cost_atj"] = carbon_abatement_cost_atj
        self.df.loc[:, "specific_carbon_abatement_cost_atj"] = specific_carbon_abatement_cost_atj
        self.df.loc[:, "generic_specific_carbon_abatement_cost_atj"] = (
            generic_specific_carbon_abatement_cost_atj
        )
        self.df.loc[:, "biofuel_cost_atj"] = biofuel_cost_atj
        self.df.loc[:, "biofuel_mean_capex_share_atj"] = biofuel_mean_capex_share_atj
        self.df.loc[:, "biofuel_mean_var_opex_share_atj"] = biofuel_mean_var_opex_share_atj
        self.df.loc[:, "biofuel_mean_feedstock_share_atj"] = biofuel_mean_feedstock_share_atj
        self.df.loc[:, "biofuel_atj_mfsp"] = biofuel_atj_mfsp
        self.df.loc[:, "biofuel_carbon_tax_atj"] = biofuel_carbon_tax_atj
        self.df.loc[:, "biofuel_cost_premium_atj"] = biofuel_cost_premium_atj
        self.df.loc[:, "biofuel_mfsp_carbon_tax_supplement_atj"] = (
            biofuel_mfsp_carbon_tax_supplement_atj
        )

        biofuel_mean_mfsp = (
            (biofuel_hefa_fog_mfsp * biofuel_hefa_fog_share / 100).fillna(0)
            + (biofuel_hefa_others_mfsp * biofuel_hefa_others_share / 100).fillna(0)
            + (biofuel_ft_others_mfsp * biofuel_ft_others_share / 100).fillna(0)
            + (biofuel_ft_msw_mfsp * biofuel_ft_msw_share / 100).fillna(0)
            + (biofuel_atj_mfsp * biofuel_atj_share / 100).fillna(0)
        )

        self.df.loc[:, "biofuel_mean_mfsp"] = biofuel_mean_mfsp

        for k in range(self.prospection_start_year, self.end_year + 1):
            # check for vals
            valid = []
            if biofuel_atj_share.loc[k] > 0:
                valid.append(biofuel_atj_mfsp.loc[k])
            if biofuel_hefa_fog_share.loc[k] > 0:
                valid.append(biofuel_hefa_fog_mfsp.loc[k])
            if biofuel_ft_others_share.loc[k] > 0:
                valid.append(biofuel_ft_others_mfsp.loc[k])
            if biofuel_ft_msw_mfsp.loc[k] > 0:
                valid.append(biofuel_ft_msw_mfsp.loc[k])
            if biofuel_hefa_others_mfsp.loc[k] > 0:
                valid.append(biofuel_hefa_others_mfsp.loc[k])

            self.df.loc[k, "biofuel_marginal_mfsp"] = np.max(valid)

        biofuel_marginal_mfsp = self.df.loc[:, "biofuel_marginal_mfsp"]
        # MEAN tax
        biofuel_mean_carbon_tax_per_l = (
            (biofuel_mfsp_carbon_tax_supplement_hefa_fog * biofuel_hefa_fog_share / 100).fillna(0)
            + (
                biofuel_mfsp_carbon_tax_supplement_hefa_others * biofuel_hefa_others_share / 100
            ).fillna(0)
            + (biofuel_mfsp_carbon_tax_supplement_ft_others * biofuel_ft_others_share / 100).fillna(
                0
            )
            + (biofuel_mfsp_carbon_tax_supplement_ft_msw * biofuel_ft_msw_share / 100).fillna(0)
            + (biofuel_mfsp_carbon_tax_supplement_atj * biofuel_atj_share / 100).fillna(0)
        )

        self.df.loc[:, "biofuel_mean_carbon_tax_per_l"] = biofuel_mean_carbon_tax_per_l
        return (
            plant_building_scenario_hefa_fog,
            plant_building_cost_hefa_fog,
            carbon_abatement_cost_hefa_fog,
            specific_carbon_abatement_cost_hefa_fog,
            generic_specific_carbon_abatement_cost_hefa_fog,
            biofuel_cost_hefa_fog,
            biofuel_mean_capex_share_hefa_fog,
            biofuel_mean_var_opex_share_hefa_fog,
            biofuel_mean_feedstock_share_hefa_fog,
            biofuel_hefa_fog_mfsp,
            biofuel_carbon_tax_hefa_fog,
            biofuel_cost_premium_hefa_fog,
            biofuel_mfsp_carbon_tax_supplement_hefa_fog,
            plant_building_scenario_hefa_others,
            plant_building_cost_hefa_others,
            carbon_abatement_cost_hefa_others,
            specific_carbon_abatement_cost_hefa_others,
            generic_specific_carbon_abatement_cost_hefa_others,
            biofuel_cost_hefa_others,
            biofuel_mean_capex_share_hefa_others,
            biofuel_mean_var_opex_share_hefa_others,
            biofuel_mean_feedstock_share_hefa_others,
            biofuel_hefa_others_mfsp,
            biofuel_cost_premium_hefa_others,
            biofuel_carbon_tax_hefa_others,
            biofuel_mfsp_carbon_tax_supplement_hefa_others,
            plant_building_scenario_ft_others,
            plant_building_cost_ft_others,
            carbon_abatement_cost_ft_others,
            specific_carbon_abatement_cost_ft_others,
            generic_specific_carbon_abatement_cost_ft_others,
            biofuel_cost_ft_others,
            biofuel_mean_capex_share_ft_others,
            biofuel_mean_var_opex_share_ft_others,
            biofuel_mean_feedstock_share_ft_others,
            biofuel_ft_others_mfsp,
            biofuel_cost_premium_ft_others,
            biofuel_carbon_tax_ft_others,
            biofuel_mfsp_carbon_tax_supplement_ft_others,
            plant_building_scenario_ft_msw,
            plant_building_cost_ft_msw,
            carbon_abatement_cost_ft_msw,
            specific_carbon_abatement_cost_ft_msw,
            generic_specific_carbon_abatement_cost_ft_msw,
            biofuel_cost_ft_msw,
            biofuel_mean_capex_share_ft_msw,
            biofuel_mean_var_opex_share_ft_msw,
            biofuel_mean_feedstock_share_ft_msw,
            biofuel_ft_msw_mfsp,
            biofuel_cost_premium_ft_msw,
            biofuel_carbon_tax_ft_msw,
            biofuel_mfsp_carbon_tax_supplement_ft_msw,
            plant_building_scenario_atj,
            plant_building_cost_atj,
            biofuel_mean_capex_share_atj,
            biofuel_mean_var_opex_share_atj,
            biofuel_mean_feedstock_share_atj,
            biofuel_atj_mfsp,
            carbon_abatement_cost_atj,
            specific_carbon_abatement_cost_atj,
            generic_specific_carbon_abatement_cost_atj,
            biofuel_cost_atj,
            biofuel_cost_premium_atj,
            biofuel_carbon_tax_atj,
            biofuel_mfsp_carbon_tax_supplement_atj,
            biofuel_mean_carbon_tax_per_l,
            biofuel_mean_mfsp,
            biofuel_marginal_mfsp,
        )

    def _pathway_computation(
        self,
        emission_factor: pd.Series,
        kerosene_emission_factor: pd.Series,
        carbon_tax: pd.Series,
        kerosene_market_price: pd.Series,
        energy_consumption_biofuel: pd.Series,
        share: pd.Series,
        biomass_feedstock_cost: pd.Series,
        biofuel_eis_var_opex: pd.Series,
        biofuel_eis_capex: pd.Series,
        plant_eis_efficiency: pd.Series,
        exogenous_carbon_price_trajectory: pd.Series,
        plant_lifespan: float,
        private_discount_rate: float,
        social_discount_rate: float,
        lhv_biofuel: float,
        density_biofuel: float,
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
        # Constants:
        construction_time = 3
        load_factor = 0.95

        # Avoided emission factor in gCO2/MJ
        avoided_emission_factor = kerosene_emission_factor - emission_factor

        # Demand scenario for the pathway in MJ
        demand_scenario = energy_consumption_biofuel * share / 100

        indexes = demand_scenario.index

        # Additional plant capacity building needed (in ton/day output capacity) for a given year
        plant_building_scenario = pd.Series(np.zeros(len(indexes)), indexes)
        # Relative CAPEX cost to build the new facilities in M€2020
        plant_building_cost = pd.Series(np.zeros(len(indexes)), indexes)

        # Annual production in MJ
        biofuel_production = pd.Series(np.zeros(len(indexes)), indexes)

        # carbon abatement cost in €/ton
        carbon_abatement_cost = pd.Series(np.zeros(len(indexes)), indexes)

        specific_carbon_abatement_cost = pd.Series(np.nan, indexes)
        generic_specific_carbon_abatement_cost = pd.Series(np.nan, indexes)

        # Total and detailled annual production cost in M€2020
        biofuel_total_cost = pd.Series(np.zeros(len(indexes)), indexes)
        biofuel_capex_cost = pd.Series(np.zeros(len(indexes)), indexes)
        biofuel_opex_cost = pd.Series(np.zeros(len(indexes)), indexes)
        biofuel_feedstock_cost = pd.Series(np.zeros(len(indexes)), indexes)

        # Total extra cost linked to carbon tax in M€2020
        biofuel_carbon_tax_cost = pd.Series(np.zeros(len(indexes)), indexes)
        # Total annual cost premium in M€2020
        biofuel_cost_premium = pd.Series(np.zeros(len(indexes)), indexes)

        # Extra cost on mfsp linked to carbon tax in €/L
        mfsp_supplement_carbon_tax = pd.Series(np.zeros(len(indexes)), indexes)

        # For each year of the demand scenario the demand is matched by the production
        for year in list(demand_scenario.index):
            # Production missing in year n+1 must be supplied by plant built in year n
            if (year + 1) <= self.end_year and biofuel_production[year + 1] < demand_scenario[
                year + 1
            ]:
                # Getting the production not matched by plants already commissioned
                # by creating plants with actual year data technical data
                biofuel_mfsp = self._compute_pathway_year_mfsp(
                    int(construction_time),
                    int(plant_lifespan),
                    year - construction_time,
                    biomass_feedstock_cost,
                    biofuel_eis_var_opex,
                    biofuel_eis_capex,
                    plant_eis_efficiency,
                    private_discount_rate,
                    load_factor,
                    lhv_biofuel,
                    density_biofuel,
                )

                # Getting the production not matched by plants already commissioned [MJ]
                missing_production = demand_scenario[year + 1] - biofuel_production[year + 1]

                # Converting the missing production to a capacity [in kg/day capacity], including availability of plant
                missing_production_kg = missing_production / lhv_biofuel
                missing_production_litres = missing_production_kg / density_biofuel
                capacity_to_build_kg_day = missing_production_kg / load_factor / 365

                capex_year = (
                    capacity_to_build_kg_day * biofuel_eis_capex[year] / 1000000
                )  # conversion in € per ton per day and in M€

                # Adding the new capacity and related costs into the annual cost and capacity series.
                # It is assumed that building costs are equally distributed among the construction years.
                plant_building_scenario[year] = capacity_to_build_kg_day

                for construction_year in range(year - construction_time, year):
                    if self.historic_start_year < construction_year < self.end_year:
                        plant_building_cost[construction_year] += capex_year / construction_time

                # When production ends: either at the end of plant life or the end of the scenario;
                end_bound = int(min(list(demand_scenario.index)[-1], year + plant_lifespan))
                # Adding new plant production to future years and computing total cost associated

                discounted_cumul_cost = 0
                cumul_em = 0
                generic_discounted_cumul_em = 0

                for i in range(year + 1, end_bound + 1):
                    biofuel_total_cost[i] = (
                        biofuel_total_cost[i]
                        + (missing_production_litres * biofuel_mfsp[i]["TOTAL"]) / 1e6
                    )  # €/L and production in litres => /1000000 for M€
                    biofuel_capex_cost[i] = (
                        biofuel_capex_cost[i]
                        + (missing_production_litres * biofuel_mfsp[i]["CAPEX"]) / 1e6
                    )  # M€
                    biofuel_opex_cost[i] = (
                        biofuel_opex_cost[i]
                        + (missing_production_litres * biofuel_mfsp[i]["VAR_OPEX"]) / 1e6
                    )  # M€
                    biofuel_feedstock_cost[i] = (
                        biofuel_feedstock_cost[i]
                        + (missing_production_litres * biofuel_mfsp[i]["FEEDSTOCK"]) / 1e6
                    )  # M€
                    biofuel_production[i] = biofuel_production[i] + missing_production

                for i in range(year, year + int(plant_lifespan)):
                    if i < (self.end_year + 1):
                        discounted_cumul_cost += (
                            biofuel_mfsp[i]["TOTAL"] - kerosene_market_price[i]
                        ) / (1 + social_discount_rate) ** (i - year)
                        cumul_em += (
                            avoided_emission_factor[i] * (lhv_biofuel * density_biofuel) / 1000000
                        )
                        # discounting emissions for non-hotelling scc
                        generic_discounted_cumul_em += (
                            avoided_emission_factor[i]
                            * (lhv_biofuel * density_biofuel)
                            / 1000000
                            * exogenous_carbon_price_trajectory[i]
                            / exogenous_carbon_price_trajectory[year]
                            / (1 + social_discount_rate) ** (i - year)
                        )

                    else:
                        discounted_cumul_cost += (
                            biofuel_mfsp[self.end_year]["TOTAL"]
                            - kerosene_market_price[self.end_year]
                        ) / (1 + social_discount_rate) ** (i - year)
                        cumul_em += (
                            avoided_emission_factor[self.end_year]
                            * (lhv_biofuel * density_biofuel)
                            / 1000000
                        )
                        # discounting emissions for non-hotelling scc, keep last year scc growth rate as future scc growth rate
                        future_scc_growth = (
                            exogenous_carbon_price_trajectory[self.end_year]
                            / exogenous_carbon_price_trajectory[self.end_year - 1]
                        )

                        generic_discounted_cumul_em += (
                            avoided_emission_factor[self.end_year]
                            * (lhv_biofuel * density_biofuel)
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
                biofuel_production[year + 1] >= demand_scenario[year + 1] > 0
            ):
                specific_carbon_abatement_cost[year] = specific_carbon_abatement_cost[year - 1]
                generic_specific_carbon_abatement_cost[year] = (
                    generic_specific_carbon_abatement_cost[year - 1]
                )

        # MOD -> Scaling down production for diminishing production scenarios.
        # Very weak model, assuming that production not anymore needed by aviation is used elsewhere in the industry.
        # Stranded asset literature could be valuable to model this better.
        # Proportional production scaling

        scaling_factor = demand_scenario / biofuel_production

        if not all(scaling_factor.isna()):
            biofuel_total_cost = biofuel_total_cost * scaling_factor
            biofuel_capex_cost = biofuel_capex_cost * scaling_factor
            biofuel_opex_cost = biofuel_opex_cost * scaling_factor
            biofuel_feedstock_cost = biofuel_feedstock_cost * scaling_factor

        biofuel_mean_mfsp_litre = (
            biofuel_total_cost / (demand_scenario / (lhv_biofuel * density_biofuel)) * 1000000
        )

        biofuel_mean_capex_share = biofuel_capex_cost / biofuel_total_cost * 100
        biofuel_mean_opex_share = biofuel_opex_cost / biofuel_total_cost * 100
        biofuel_mean_feedstock_share = biofuel_feedstock_cost / biofuel_total_cost * 100

        biofuel_cost_premium = (
            (biofuel_mean_mfsp_litre - kerosene_market_price)
            * (demand_scenario / (lhv_biofuel * density_biofuel))
            / 1000000
        )

        # Compute the carbon tax (M€)

        biofuel_carbon_tax_cost = carbon_tax * emission_factor * demand_scenario / 1000000 / 1000000

        mfsp_supplement_carbon_tax = (
            carbon_tax * emission_factor * (lhv_biofuel * density_biofuel) / 1000000
        )

        # Abatement cost in €/tCO2e (= overcost for a ton of biofuel/avoided emissions)
        carbon_abatement_cost = (
            (biofuel_mean_mfsp_litre - kerosene_market_price)
            / (avoided_emission_factor * (lhv_biofuel * density_biofuel))
            * 1000000
        )

        return (
            plant_building_scenario,
            plant_building_cost,
            biofuel_production,
            carbon_abatement_cost,
            biofuel_total_cost,
            biofuel_mean_capex_share,
            biofuel_mean_opex_share,
            biofuel_mean_feedstock_share,
            biofuel_mean_mfsp_litre,
            biofuel_carbon_tax_cost,
            biofuel_cost_premium,
            mfsp_supplement_carbon_tax,
            specific_carbon_abatement_cost,
            generic_specific_carbon_abatement_cost,
        )

    def _compute_pathway_year_mfsp(
        self,
        construction_time,
        plant_lifespan,
        base_year,
        biomass_feedstock_cost,
        biofuel_eis_var_opex,
        biofuel_eis_capex,
        plant_eis_efficiency,
        private_discount_rate,
        load_fact,
        lhv_biofuel,
        density_biofuel,
    ):
        """
        This function computes the MFSP for a given biofuel production pathway for a plant commissioned at the base year.
        Costs are discounted to find a constant MFSP, excepted feedstock, whose price is directly evolving and passed on biofuel MFSP.
        Capex in €/(kg/day capacity)
        Variable opex in € per L of fuel produced (Constant plant entry into service value)
        Feedstock cost in € per MJ of biomass
        Overall plant conversion efficiency
        Biofuel MFSP returned in €/L
        """
        biofuel_prices = {}

        # modification to base year not to use undefined technology costs => either base year or start of prospection year
        technology_year = max(base_year, self.prospection_start_year)

        real_year_days = 365.25 * load_fact
        real_var_opex = biofuel_eis_var_opex[technology_year] * real_year_days
        cap_cost_npv = 0
        var_op_cost_npv = 0
        biofuel_npv = 0

        # Construction of the facility
        for i in range(0, construction_time):
            # The construction is supposed to span over x years, with a uniform cost repartition
            cap_cost_npv += (
                biofuel_eis_capex[technology_year] * density_biofuel / construction_time
            ) / (1 + private_discount_rate) ** i

        # Commissioning of the facility
        for i in range(construction_time, plant_lifespan + construction_time):
            var_op_cost_npv += real_var_opex / (1 + private_discount_rate) ** i
            biofuel_npv += real_year_days / (1 + private_discount_rate) ** i

        cap_cost_lc = cap_cost_npv / biofuel_npv
        var_op_cost_lc = var_op_cost_npv / biofuel_npv

        end_bound = min(
            max(biomass_feedstock_cost.index), base_year + construction_time + plant_lifespan
        )

        for year in range(base_year + construction_time, int(end_bound) + 1):
            feedstock_price = biomass_feedstock_cost[year]
            feedstock_cost = (
                feedstock_price
                * lhv_biofuel
                * density_biofuel
                / plant_eis_efficiency[technology_year]
            )
            biofuel_prices[year] = {
                "TOTAL": cap_cost_lc + var_op_cost_lc + feedstock_cost,
                "CAPEX": cap_cost_lc,
                "VAR_OPEX": var_op_cost_lc,
                "FEEDSTOCK": feedstock_cost,
            }
        return biofuel_prices


class BiofuelCapex(AeroMAPSModel):
    def __init__(self, name="biofuel_capex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        biofuel_hefa_fog_capex_reference_years: list,
        biofuel_hefa_fog_capex_reference_years_values: list,
        biofuel_hefa_others_capex_reference_years: list,
        biofuel_hefa_others_capex_reference_years_values: list,
        biofuel_ft_others_capex_reference_years: list,
        biofuel_ft_others_capex_reference_years_values: list,
        biofuel_ft_msw_capex_reference_years: list,
        biofuel_ft_msw_capex_reference_years_values: list,
        biofuel_atj_capex_reference_years: list,
        biofuel_atj_capex_reference_years_values: list,
        biofuel_hefa_fog_share: pd.Series,
        biofuel_hefa_others_share: pd.Series,
        biofuel_ft_others_share: pd.Series,
        biofuel_ft_msw_share: pd.Series,
        biofuel_atj_share: pd.Series,
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


class BiofuelVarOpex(AeroMAPSModel):
    def __init__(self, name="biofuel_var_opex", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        biofuel_hefa_fog_var_opex_reference_years: list,
        biofuel_hefa_fog_var_opex_reference_years_values: list,
        biofuel_hefa_others_var_opex_reference_years: list,
        biofuel_hefa_others_var_opex_reference_years_values: list,
        biofuel_ft_others_var_opex_reference_years: list,
        biofuel_ft_others_var_opex_reference_years_values: list,
        biofuel_ft_msw_var_opex_reference_years: list,
        biofuel_ft_msw_var_opex_reference_years_values: list,
        biofuel_atj_var_opex_reference_years: list,
        biofuel_atj_var_opex_reference_years_values: list,
        biofuel_hefa_fog_share: pd.Series,
        biofuel_hefa_others_share: pd.Series,
        biofuel_ft_others_share: pd.Series,
        biofuel_ft_msw_share: pd.Series,
        biofuel_atj_share: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Biofuel OPEX (Operational EXPenditures) estimates, excepted feedstock energy
        Values should be specified as €/L of fuel produced.
        It is therefore what could be qualified as variable var_opex."""

        # HEFA FOG
        biofuel_hefa_fog_var_opex = AeromapsInterpolationFunction(
            self,
            biofuel_hefa_fog_var_opex_reference_years,
            biofuel_hefa_fog_var_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_hefa_fog_var_opex"] = biofuel_hefa_fog_var_opex

        # HEFA OTHERS
        biofuel_hefa_others_var_opex = AeromapsInterpolationFunction(
            self,
            biofuel_hefa_others_var_opex_reference_years,
            biofuel_hefa_others_var_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_hefa_others_var_opex"] = biofuel_hefa_others_var_opex

        # FT OTHERS
        biofuel_ft_others_var_opex = AeromapsInterpolationFunction(
            self,
            biofuel_ft_others_var_opex_reference_years,
            biofuel_ft_others_var_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_ft_others_var_opex"] = biofuel_ft_others_var_opex

        # FT MSW
        biofuel_ft_msw_var_opex = AeromapsInterpolationFunction(
            self,
            biofuel_ft_msw_var_opex_reference_years,
            biofuel_ft_msw_var_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_ft_msw_var_opex"] = biofuel_ft_msw_var_opex

        # ATJ
        biofuel_atj_var_opex = AeromapsInterpolationFunction(
            self,
            biofuel_atj_var_opex_reference_years,
            biofuel_atj_var_opex_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_atj_var_opex"] = biofuel_atj_var_opex

        # MEAN
        biofuel_mean_var_opex = (
            biofuel_hefa_fog_var_opex * biofuel_hefa_fog_share / 100
            + biofuel_hefa_others_var_opex * biofuel_hefa_others_share / 100
            + biofuel_ft_others_var_opex * biofuel_ft_others_share / 100
            + biofuel_ft_msw_var_opex * biofuel_ft_msw_share / 100
            + biofuel_atj_var_opex * biofuel_atj_share / 100
        )

        self.df.loc[:, "biofuel_mean_var_opex"] = biofuel_mean_var_opex

        return (
            biofuel_hefa_fog_var_opex,
            biofuel_hefa_others_var_opex,
            biofuel_ft_others_var_opex,
            biofuel_ft_msw_var_opex,
            biofuel_atj_var_opex,
            biofuel_mean_var_opex,
        )


class BiofuelFeedstock(AeroMAPSModel):
    def __init__(self, name="biofuel_feedstock_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        biofuel_hefa_fog_feedstock_cost_reference_years: list,
        biofuel_hefa_fog_feedstock_cost_reference_years_values: list,
        biofuel_hefa_others_feedstock_cost_reference_years: list,
        biofuel_hefa_others_feedstock_cost_reference_years_values: list,
        biofuel_ft_others_feedstock_cost_reference_years: list,
        biofuel_ft_others_feedstock_cost_reference_years_values: list,
        biofuel_ft_msw_feedstock_cost_reference_years: list,
        biofuel_ft_msw_feedstock_cost_reference_years_values: list,
        biofuel_atj_feedstock_cost_reference_years: list,
        biofuel_atj_feedstock_cost_reference_years_values: list,
        biofuel_hefa_fog_share: pd.Series,
        biofuel_hefa_others_share: pd.Series,
        biofuel_ft_others_share: pd.Series,
        biofuel_ft_msw_share: pd.Series,
        biofuel_atj_share: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Biofuel feedstock_cost estimates
        Values should be specified as €/MJ of input biomass"""

        # HEFA FOG
        biofuel_hefa_fog_feedstock_cost = AeromapsInterpolationFunction(
            self,
            biofuel_hefa_fog_feedstock_cost_reference_years,
            biofuel_hefa_fog_feedstock_cost_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_hefa_fog_feedstock_cost"] = biofuel_hefa_fog_feedstock_cost

        # HEFA OTHERS
        biofuel_hefa_others_feedstock_cost = AeromapsInterpolationFunction(
            self,
            biofuel_hefa_others_feedstock_cost_reference_years,
            biofuel_hefa_others_feedstock_cost_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_hefa_others_feedstock_cost"] = biofuel_hefa_others_feedstock_cost

        # FT OTHERS
        biofuel_ft_others_feedstock_cost = AeromapsInterpolationFunction(
            self,
            biofuel_ft_others_feedstock_cost_reference_years,
            biofuel_ft_others_feedstock_cost_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_ft_others_feedstock_cost"] = biofuel_ft_others_feedstock_cost

        # FT MSW
        biofuel_ft_msw_feedstock_cost = AeromapsInterpolationFunction(
            self,
            biofuel_ft_msw_feedstock_cost_reference_years,
            biofuel_ft_msw_feedstock_cost_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_ft_msw_feedstock_cost"] = biofuel_ft_msw_feedstock_cost

        # ATJ
        biofuel_atj_feedstock_cost = AeromapsInterpolationFunction(
            self,
            biofuel_atj_feedstock_cost_reference_years,
            biofuel_atj_feedstock_cost_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "biofuel_atj_feedstock_cost"] = biofuel_atj_feedstock_cost

        # MEAN
        biofuel_mean_feedstock_cost = (
            biofuel_hefa_fog_feedstock_cost * biofuel_hefa_fog_share / 100
            + biofuel_hefa_others_feedstock_cost * biofuel_hefa_others_share / 100
            + biofuel_ft_others_feedstock_cost * biofuel_ft_others_share / 100
            + biofuel_ft_msw_feedstock_cost * biofuel_ft_msw_share / 100
            + biofuel_atj_feedstock_cost * biofuel_atj_share / 100
        )

        self.df.loc[:, "biofuel_mean_feedstock_cost"] = biofuel_mean_feedstock_cost

        return (
            biofuel_hefa_fog_feedstock_cost,
            biofuel_hefa_others_feedstock_cost,
            biofuel_ft_others_feedstock_cost,
            biofuel_ft_msw_feedstock_cost,
            biofuel_atj_feedstock_cost,
            biofuel_mean_feedstock_cost,
        )

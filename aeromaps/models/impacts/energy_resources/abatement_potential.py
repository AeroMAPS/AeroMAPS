# @Time : 13/03/2023 15:14
# @Author : a.salgas
# @File : abatement_potential.py
# @Software: PyCharm

from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel


class BiofuelAbatementPotential(AeromapsModel):
    def __init__(self, name="biofuel_abatement_potential", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        biofuel_atj_efficiency: pd.Series = pd.Series(dtype="float64"),
        # biomass_atj_consumption: pd.Series = pd.Series(dtype="float64"),
        kerosene_emission_factor: pd.Series = pd.Series(dtype="float64"),
        biofuel_atj_emission_factor: pd.Series = pd.Series(dtype="float64"),
        # biomass_hefa_fog_consumption: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fuel_efficiency: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_fog_emission_factor: pd.Series = pd.Series(dtype="float64"),
        # biomass_hefa_others_consumption: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_oil_efficiency: pd.Series = pd.Series(dtype="float64"),
        biofuel_hefa_others_emission_factor: pd.Series = pd.Series(dtype="float64"),
        # biomass_ft_consumption: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_efficiency: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_msw_emission_factor: pd.Series = pd.Series(dtype="float64"),
        # biofuel_ft_msw_share: pd.Series = pd.Series(dtype="float64"),
        # biofuel_ft_others_share: pd.Series = pd.Series(dtype="float64"),
        biofuel_ft_others_emission_factor: pd.Series = pd.Series(dtype="float64"),
        # hydrogen_electrolysis_emission_factor: pd.Series = pd.Series(dtype="float64"),
        # hydrogen_replacement_ratio: float = 1.0,
        electricity_hydrogen_consumption: pd.Series = pd.Series(dtype="float64"),
        electrolysis_efficiency: pd.Series = pd.Series(dtype="float64"),
        # liquefaction_efficiency: pd.Series = pd.Series(dtype="float64"),
        electricity_electrofuel_consumption: pd.Series = pd.Series(dtype="float64"),
        electrofuel_hydrogen_efficiency: pd.Series = pd.Series(dtype="float64"),
        electrofuel_emission_factor: pd.Series = pd.Series(dtype="float64"),
        available_biomass_atj: float = 0.0,
        available_biomass_hefa_fog: float = 0.0,
        available_biomass_hefa_others: float = 0.0,
        available_biomass_ft_msw: float = 0.0,
        available_biomass_ft_others: float = 0.0,
        aviation_biomass_allocated_share: float = 0.0,
        aviation_available_electricity: float = 0.0,
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
        """Maximal and effective abatement potential through biofuel usage under the allocated biomass hypothesis."""

        ##### Maximal #####

        energy_avail_atj = (
            aviation_biomass_allocated_share
            / 100
            * available_biomass_atj
            * 10**12
            * biofuel_atj_efficiency
        )

        abatement_potential_atj = (
            energy_avail_atj * (kerosene_emission_factor - biofuel_atj_emission_factor) / 1000000
        )

        # Biomass consumption in in EJ, while emission factors are in gCO2e/MJ, abatement potential is in tCO2e

        energy_avail_hefa_fog = (
            aviation_biomass_allocated_share
            / 100
            * available_biomass_hefa_fog
            * 10**12
            * biofuel_hefa_fuel_efficiency
        )
        abatement_potential_hefa_fog = (
            energy_avail_hefa_fog
            * (kerosene_emission_factor - biofuel_hefa_fog_emission_factor)
            / 1000000
        )

        energy_avail_hefa_others = (
            aviation_biomass_allocated_share
            / 100
            * available_biomass_hefa_others
            * 10**12
            * biofuel_hefa_oil_efficiency
            * biofuel_hefa_fuel_efficiency
        )
        abatement_potential_hefa_others = (
            energy_avail_hefa_others
            * (kerosene_emission_factor - biofuel_hefa_others_emission_factor)
            / 1000000
        )

        energy_avail_ft_msw = (
            aviation_biomass_allocated_share
            / 100
            * available_biomass_ft_msw
            * 10**12
            * biofuel_ft_efficiency
        )
        abatement_potential_ft_msw = (
            energy_avail_ft_msw
            * (kerosene_emission_factor - biofuel_ft_msw_emission_factor)
            / 1000000
        )

        energy_avail_ft_others = (
            aviation_biomass_allocated_share
            / 100
            * available_biomass_ft_others
            * 10**12
            * biofuel_ft_efficiency
        )
        abatement_potential_ft_others = (
            energy_avail_ft_others
            * (kerosene_emission_factor - biofuel_ft_others_emission_factor)
            / 1000000
        )

        ## TODO reactivate for potential hydrogen MACC
        # h2_avoided_emissions_factor = (
        #     kerosene_emission_factor / hydrogen_replacement_ratio
        #     - hydrogen_electrolysis_emission_factor
        # )
        # energy_avail_hydrogen_electrolysis = (
        #     aviation_available_electricity
        #     * electricity_hydrogen_consumption
        #     / (electricity_electrofuel_consumption + electricity_hydrogen_consumption)
        #     * 10**12
        #     * electrolysis_efficiency
        #     * liquefaction_efficiency
        # )
        # abatement_potential_hydrogen_electrolysis = (
        #     energy_avail_hydrogen_electrolysis * h2_avoided_emissions_factor / 1000000
        # )

        ## The same electricity consumption share (hydrogen/electrofuel) is kept for maxiaml abatement potential computation

        energy_avail_electrofuel = (
            aviation_available_electricity
            * electricity_electrofuel_consumption
            / (electricity_electrofuel_consumption + electricity_hydrogen_consumption)
            * 10**12
            * electrolysis_efficiency
            * electrofuel_hydrogen_efficiency
        )
        abatement_potential_electrofuel = (
            energy_avail_electrofuel
            * (kerosene_emission_factor - electrofuel_emission_factor)
            / 1000000
        )

        self.df.loc[:, "abatement_potential_atj"] = abatement_potential_atj
        self.df.loc[:, "abatement_potential_hefa_fog"] = abatement_potential_hefa_fog
        self.df.loc[:, "abatement_potential_hefa_others"] = abatement_potential_hefa_others
        self.df.loc[:, "abatement_potential_ft_msw"] = abatement_potential_ft_msw
        self.df.loc[:, "abatement_potential_ft_others"] = abatement_potential_ft_others
        # self.df.loc[
        #     :, "abatement_potential_hydrogen_electrolysis"
        # ] = abatement_potential_hydrogen_electrolysis
        self.df.loc[:, "abatement_potential_electrofuel"] = abatement_potential_electrofuel
        self.df.loc[:, "energy_avail_atj"] = energy_avail_atj
        self.df.loc[:, "energy_avail_hefa_fog"] = energy_avail_hefa_fog
        self.df.loc[:, "energy_avail_hefa_others"] = energy_avail_hefa_others
        self.df.loc[:, "energy_avail_ft_msw"] = energy_avail_ft_msw
        self.df.loc[:, "energy_avail_ft_others"] = energy_avail_ft_others
        # self.df.loc[:, "energy_avail_hydrogen_electrolysis"] = energy_avail_hydrogen_electrolysis
        self.df.loc[:, "energy_avail_electrofuel"] = energy_avail_electrofuel

        ##### Effective #####
        # TODO delete this part?

        # abatement_effective_atj = (
        #     biomass_atj_consumption
        #     * 10**12
        #     * biofuel_atj_efficiency
        #     * (kerosene_emission_factor - biofuel_atj_emission_factor)
        #     / 1000000
        # )
        #
        # # Biomass consumption in in EJ, while emission factors are in gCO2e/MJ, abatement effective is in tCO2e
        #
        # abatement_effective_hefa_fog = (
        #     biomass_hefa_fog_consumption
        #     * 10**12
        #     * biofuel_hefa_fuel_efficiency
        #     * (kerosene_emission_factor - biofuel_hefa_fog_emission_factor)
        #     / 1000000
        # )
        #
        # abatement_effective_hefa_others = (
        #     biomass_hefa_others_consumption
        #     * 10**12
        #     * biofuel_hefa_oil_efficiency
        #     * biofuel_hefa_fuel_efficiency
        #     * (kerosene_emission_factor - biofuel_hefa_others_emission_factor)
        #     / 1000000
        # )
        #
        # abatement_effective_ft_msw = (
        #     biomass_ft_consumption
        #     * (biofuel_ft_msw_share / (biofuel_ft_others_share + biofuel_ft_msw_share))
        #     * 10**12
        #     * biofuel_ft_efficiency
        #     * (kerosene_emission_factor - biofuel_ft_msw_emission_factor)
        #     / 1000000
        # )
        #
        # abatement_effective_ft_others = (
        #     biomass_ft_consumption
        #     * (biofuel_ft_others_share / (biofuel_ft_others_share + biofuel_ft_msw_share))
        #     * 10**12
        #     * biofuel_ft_efficiency
        #     * (kerosene_emission_factor - biofuel_ft_others_emission_factor)
        #     / 1000000
        # )
        #
        # h2_avoided_emissions_factor = (
        #     kerosene_emission_factor / hydrogen_replacement_ratio
        #     - hydrogen_electrolysis_emission_factor
        # )
        #
        # abatement_effective_hydrogen_electrolysis = (
        #     electricity_hydrogen_consumption
        #     * 10**12
        #     * electrolysis_efficiency
        #     * liquefaction_efficiency
        #     * h2_avoided_emissions_factor
        #     / 1000000
        # )
        #
        # abatement_effective_electrofuel = (
        #     electricity_electrofuel_consumption
        #     * 10**12
        #     * electrolysis_efficiency
        #     * electrofuel_hydrogen_efficiency
        #     * (kerosene_emission_factor - electrofuel_emission_factor)
        #     / 1000000
        # )

        # TODO delete?
        # self.df.loc[:, "abatement_effective_atj"] = abatement_effective_atj
        # self.df.loc[:, "abatement_effective_hefa_fog"] = abatement_effective_hefa_fog
        # self.df.loc[:, "abatement_effective_hefa_others"] = abatement_effective_hefa_others
        # self.df.loc[:, "abatement_effective_ft_msw"] = abatement_effective_ft_msw
        # self.df.loc[:, "abatement_effective_ft_others"] = abatement_effective_ft_others
        # self.df.loc[
        #     :, "abatement_effective_hydrogen_electrolysis"
        # ] = abatement_effective_hydrogen_electrolysis
        # self.df.loc[:, "abatement_effective_electrofuel"] = abatement_effective_electrofuel

        return (
            abatement_potential_atj,
            abatement_potential_hefa_fog,
            abatement_potential_hefa_others,
            abatement_potential_ft_msw,
            abatement_potential_ft_others,
            # abatement_potential_hydrogen_electrolysis,
            abatement_potential_electrofuel,
            # abatement_effective_atj,
            # abatement_effective_hefa_fog,
            # abatement_effective_hefa_others,
            # abatement_effective_ft_msw,
            # abatement_effective_ft_others,
            # abatement_effective_hydrogen_electrolysis,
            # abatement_effective_electrofuel,
            energy_avail_atj,
            energy_avail_hefa_fog,
            energy_avail_hefa_others,
            energy_avail_ft_msw,
            energy_avail_ft_others,
            # energy_avail_hydrogen_electrolysis,
            energy_avail_electrofuel,
        )

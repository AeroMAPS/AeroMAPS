# @Time : 06/02/2024 15:12
# @Author : a.salgas
# @File : operations_abatement_cost.py
# @Software: PyCharm
from typing import Tuple

import numpy as np
import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class OperationsAbatementCost(AeroMAPSModel):
    def __init__(self, name="operations_abatement_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        operational_efficiency_cost_non_energy_per_ask: pd.Series,
        operations_gain: pd.Series,
        kerosene_market_price: pd.Series,
        kerosene_emission_factor: pd.Series,
        energy_per_ask_mean_without_operations: pd.Series,
        energy_per_ask_mean: pd.Series,
        energy_per_rtk_mean_without_operations: pd.Series,
        energy_per_rtk_mean: pd.Series,
        rpk: pd.Series,
        rtk: pd.Series,
        load_factor: pd.Series,
        load_factor_cost_non_energy_per_ask: pd.Series,
        exogenous_carbon_price_trajectory: pd.Series,
        social_discount_rate: float,
        operations_duration: float,
        operations_start_year: int,
        lhv_kerosene: float,
        density_kerosene: float,
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
        fuel_lhv = lhv_kerosene * density_kerosene

        ############### PASSENGER OPERATIONS #############

        emissions_reduction_operations = (
            energy_per_ask_mean_without_operations
            * operations_gain
            / 100
            * kerosene_emission_factor
            / 1000000
        )

        extra_cost_operations_non_fuel = operational_efficiency_cost_non_energy_per_ask

        extra_cost_operations_fuel = (
            -energy_per_ask_mean_without_operations
            * operations_gain
            / 100
            * kerosene_market_price
            / fuel_lhv
        )

        operations_abatement_cost = (
            extra_cost_operations_non_fuel + extra_cost_operations_fuel
        ) / emissions_reduction_operations

        self.df.loc[:, "operations_abatement_cost"] = operations_abatement_cost

        operations_abatement_effective = (
            emissions_reduction_operations
            * rpk
            / load_factor.loc[self.prospection_start_year - 1]
            * 100
        )
        self.df.loc[:, "operations_abatement_effective"] = operations_abatement_effective

        # Definition of a specific abatement cost, comparable to a hotelling growth carbon value.
        # Discount the costs/benefits over the horizon necessary to deploy the incremental gains of a year
        for k in range(int(operations_start_year), self.end_year + 1):
            (scac, scac_prime) = self._get_discounted_vals(
                k,
                social_discount_rate,
                operations_duration,
                extra_cost_operations_non_fuel,
                extra_cost_operations_fuel,
                kerosene_market_price,
                kerosene_emission_factor,
                emissions_reduction_operations,
                exogenous_carbon_price_trajectory,
            )

            self.df.loc[k, "operations_specific_abatement_cost"] = scac
            self.df.loc[k, "operations_generic_specific_abatement_cost"] = scac_prime

        operations_specific_abatement_cost = self.df["operations_specific_abatement_cost"]
        operations_generic_specific_abatement_cost = self.df[
            "operations_generic_specific_abatement_cost"
        ]

        ################ FREIGHT OPERATIONS ################

        emissions_reduction_operations_freight = (
            energy_per_rtk_mean_without_operations
            * operations_gain
            / 100
            * kerosene_emission_factor
            / 1000000
        )

        extra_cost_operations_non_fuel_freight = pd.Series(
            np.zeros(len(self.df.index)), index=self.df.index
        )

        extra_cost_operations_fuel_freight = (
            -energy_per_rtk_mean_without_operations
            * operations_gain
            / 100
            * kerosene_market_price
            / fuel_lhv
        )

        operations_abatement_cost_freight = (
            extra_cost_operations_non_fuel_freight + extra_cost_operations_fuel_freight
        ) / emissions_reduction_operations_freight

        self.df.loc[:, "operations_abatement_cost_freight"] = operations_abatement_cost_freight

        operations_abatement_effective_freight = emissions_reduction_operations_freight * rtk
        self.df.loc[:, "operations_abatement_effective_freight"] = (
            operations_abatement_effective_freight
        )

        # Definition of a specific abatement cost, comparable to a hotelling growth carbon value.
        # Discount the costs/benefits over the horizon necessary to deploy the incremental gains of a year
        for k in range(int(operations_start_year), self.end_year + 1):
            (scac, scac_prime) = self._get_discounted_vals(
                k,
                social_discount_rate,
                operations_duration,
                extra_cost_operations_non_fuel_freight,
                extra_cost_operations_fuel_freight,
                kerosene_market_price,
                kerosene_emission_factor,
                emissions_reduction_operations_freight,
                exogenous_carbon_price_trajectory,
            )

            self.df.loc[k, "operations_specific_abatement_cost_freight"] = scac
            self.df.loc[k, "operations_generic_specific_abatement_cost_freight"] = scac_prime

        operations_specific_abatement_cost_freight = self.df[
            "operations_specific_abatement_cost_freight"
        ]
        operations_generic_specific_abatement_cost_freight = self.df[
            "operations_generic_specific_abatement_cost_freight"
        ]

        ############### PASSENGER LOAD FACTOR ########################

        energy_per_rpk_base = (
            energy_per_ask_mean / load_factor.loc[self.prospection_start_year - 1] * 100
        )
        energy_per_rpk_real = energy_per_ask_mean / load_factor * 100

        emissions_reduction_load_factor = (
            (energy_per_rpk_base - energy_per_rpk_real) * kerosene_emission_factor / 1000000
        )
        extra_cost_load_factor_fuel = (
            -(energy_per_rpk_base - energy_per_rpk_real) * kerosene_market_price / fuel_lhv
        )
        extra_cost_load_factor_non_fuel = load_factor_cost_non_energy_per_ask

        load_factor_abatement_cost = (
            extra_cost_load_factor_fuel + extra_cost_load_factor_non_fuel
        ) / emissions_reduction_load_factor

        self.df.loc[:, "load_factor_abatement_cost"] = load_factor_abatement_cost

        load_factor_abatement_effective = emissions_reduction_load_factor * rpk
        self.df.loc[:, "load_factor_abatement_effective"] = load_factor_abatement_effective

        # Definition of a specific abatement cost, comparable to a hotelling growth carbon value.
        # Discount the costs/benefits over the scenario temporal span.
        # Caution: the longer the scenario, the lower the specific abatement cost
        for k in range(self.prospection_start_year, self.end_year + 1):
            scac, scac_prime = self._get_discounted_vals(
                k,
                social_discount_rate,
                self.end_year - self.prospection_start_year,
                extra_cost_load_factor_non_fuel,
                extra_cost_load_factor_fuel,
                kerosene_market_price,
                kerosene_emission_factor,
                emissions_reduction_load_factor,
                exogenous_carbon_price_trajectory,
            )

            self.df.loc[k, "load_factor_specific_abatement_cost"] = scac
            self.df.loc[k, "load_factor_generic_specific_abatement_cost"] = scac_prime

        load_factor_specific_abatement_cost = self.df["load_factor_specific_abatement_cost"]
        load_factor_generic_specific_abatement_cost = self.df[
            "load_factor_generic_specific_abatement_cost"
        ]

        return (
            operations_abatement_cost,
            operations_abatement_effective,
            operations_specific_abatement_cost,
            operations_generic_specific_abatement_cost,
            operations_abatement_cost_freight,
            operations_abatement_effective_freight,
            operations_specific_abatement_cost_freight,
            operations_generic_specific_abatement_cost_freight,
            load_factor_abatement_cost,
            load_factor_abatement_effective,
            load_factor_specific_abatement_cost,
            load_factor_generic_specific_abatement_cost,
        )

    def _get_discounted_vals(
        self,
        year,
        discount_rate,
        measure_duration,
        extra_cost_non_fuel,
        extra_cost_fuel,
        kerosene_market_price,
        kerosene_emission_factor,
        emissions_reduction,
        exogenous_carbon_price_trajectory,
    ):
        discounted_cumul_cost = 0
        cumul_em = 0
        generic_discounted_cumul_em = 0
        for i in range(year, year + int(measure_duration)):
            if i < (self.end_year + 1):
                discounted_cumul_cost += (
                    extra_cost_non_fuel[year]
                    + extra_cost_fuel[year] * kerosene_market_price[i] / kerosene_market_price[year]
                ) / (1 + discount_rate) ** (i - year)
                cumul_em += (
                    emissions_reduction[year]
                    * kerosene_emission_factor[i]
                    / kerosene_emission_factor[year]
                )

                generic_discounted_cumul_em += (
                    emissions_reduction[year]
                    * kerosene_emission_factor[i]
                    / kerosene_emission_factor[year]
                    * exogenous_carbon_price_trajectory[i]
                    / exogenous_carbon_price_trajectory[year]
                    / (1 + discount_rate) ** (i - year)
                )
            else:
                discounted_cumul_cost += (
                    extra_cost_non_fuel[year]
                    + extra_cost_fuel[year]
                    * kerosene_market_price[self.end_year]
                    / kerosene_market_price[year]
                ) / (1 + discount_rate) ** (i - year)
                cumul_em += (
                    emissions_reduction[year]
                    * kerosene_emission_factor[self.end_year]
                    / kerosene_emission_factor[year]
                )

                # discounting emissions for non-hotelling scc, keep last year scc growth rate as future scc growth rate
                future_scc_growth = (
                    exogenous_carbon_price_trajectory[self.end_year]
                    / exogenous_carbon_price_trajectory[self.end_year - 1]
                )

                generic_discounted_cumul_em += (
                    emissions_reduction[year]
                    * (kerosene_emission_factor[self.end_year] / kerosene_emission_factor[year])
                    * (
                        exogenous_carbon_price_trajectory[self.end_year]
                        / exogenous_carbon_price_trajectory[year]
                        * (future_scc_growth) ** (i - self.end_year)
                    )
                    / (1 + discount_rate) ** (i - year)
                )

        if cumul_em == 0:
            scac = np.NaN
        else:
            scac = discounted_cumul_cost / cumul_em

        if generic_discounted_cumul_em == 0:
            scac_prime = np.NaN
        else:
            scac_prime = discounted_cumul_cost / generic_discounted_cumul_em

        return (
            scac,
            scac_prime,
        )

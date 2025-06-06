from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class BottomUpAbatementCost(AeroMAPSModel):
    """
    Computes specific abatement cost and generic specific abatement cost for a pathway,
    based on discounted costs and avoided emissions over the lifespan of each vintage.
    """

    def __init__(self, name, pathway_name, configuration_data, *args, **kwargs):
        super().__init__(
            name=name,
            model_type="custom",
            *args,
            **kwargs,
        )
        self.pathway_name = pathway_name

        # Inputs needed: discounted costs, unitary emissions, discounted emissions
        self.input_names = {
            f"{self.pathway_name}_lifespan_unitary_discounted_costs": pd.Series([0.0]),
            f"{self.pathway_name}_lifespan_unitary_emissions": pd.Series([0.0]),
            f"{self.pathway_name}_lifespan_discounted_unitary_emissions": pd.Series([0.0]),
            f"{self.pathway_name}_mfsp": pd.Series([0.0]),
            f"{self.pathway_name}_co2_emission_factor": pd.Series([0.0]),
            f"{self.pathway_name}_eis_plant_lifespan": 0.0,
            "social_discount_rate": 0.0,
            "exogenous_carbon_price_trajectory": pd.Series([0.0]),
        }
        # get the fossil kerosene reference to compute the CACs.
        if "fossil_kerosene" not in configuration_data.keys():
            raise ValueError(
                "Configuration data must contain 'fossil_kerosene' reference pathway for CAC computation."
            )
        else:
            # 2 cases: either fossil kerosene is defined to-down, as before. Weak CAC definition, considering its average price and EF
            # 1:
            if (
                configuration_data["fossil_kerosene"]["cost_model"] == "bottom-up"
                and configuration_data["fossil_kerosene"]["cost_model"] == "bottom-up"
            ):
                self.input_names.update(
                    {
                        "fossil_kerosene_lifespan_unitary_discounted_costs": pd.Series([0.0]),
                        "fossil_kerosene_lifespan_unitary_emissions": pd.Series([0.0]),
                        "fossil_kerosene_lifespan_discounted_unitary_emissions": pd.Series([0.0]),
                        "fossil_kerosene_mfsp": pd.Series([0.0]),
                        "fossil_kerosene_co2_emission_factor": pd.Series([0.0]),
                    }
                )
                self.bottom_up_cac = True
            else:
                print(
                    "Warning: fossil kerosene reference is not defined as bottom-up, using top-down values for CAC computation."
                )
                self.input_names.update(
                    {
                        "fossil_kerosene_mfsp": pd.Series([0.0]),
                        "fossil_kerosene_co2_emission_factor": pd.Series([0.0]),
                    }
                )
                self.bottom_up_cac = False

        # Outputs: specific abatement cost and generic specific abatement cost

        self.output_names = {
            f"{self.pathway_name}_abatement_cost": pd.Series([0.0]),
            f"{self.pathway_name}_specific_abatement_cost": pd.Series([0.0]),
            f"{self.pathway_name}_generic_specific_abatement_cost": pd.Series([0.0]),
        }

    def compute(self, input_data) -> dict:
        """
        Compute the specific abatement cost and generic specific abatement cost for each vintage.
        """
        unitary_discounted_costs = input_data.get(
            f"{self.pathway_name}_lifespan_unitary_discounted_costs", pd.Series([0.0])
        )
        unitary_discounted_emissions = input_data.get(
            f"{self.pathway_name}_lifespan_discounted_unitary_emissions", pd.Series([0.0])
        )
        unitary_emissions = input_data.get(
            f"{self.pathway_name}_lifespan_unitary_emissions", pd.Series([0.0])
        )
        mfsp = input_data.get(f"{self.pathway_name}_mfsp", pd.Series([0.0]))
        co2_emission_factor = input_data.get(
            f"{self.pathway_name}_co2_emission_factor", pd.Series([0.0])
        )
        fossil_mfsp = input_data.get("fossil_kerosene_mfsp", pd.Series([0.0]))
        fossil_ef = input_data.get("fossil_kerosene_co2_emission_factor", pd.Series([0.0]))

        if self.bottom_up_cac:
            reference_unitary_discounted_costs = input_data.get(
                "fossil_lifespan_unitary_discounted_costs", pd.Series([0.0])
            )
            reference_unitary_discounted_emissions = input_data.get(
                "fossil_lifespan_discounted_unitary_emissions", pd.Series([0.0])
            )
            reference_unitary_emissions = input_data.get(
                "fossil_lifespan_unitary_emissions", pd.Series([0.0])
            )

        else:
            reference_lifespan = input_data.get(f"{self.pathway_name}_eis_plant_lifespan", 25.0)
            social_discount_rate = input_data.get(f"{self.pathway_name}_social_discount_rate", 0.0)
            exogenous_carbon_price_trajectory = input_data.get(
                f"{self.pathway_name}_exogenous_carbon_price_trajectory", pd.Series([0.0])
            )

            reference_unitary_discounted_costs = self._unit_kerozene_discounted_cumul_costs(
                fossil_mfsp, reference_lifespan, social_discount_rate
            )
            (reference_unitary_emissions, reference_unitary_discounted_emissions) = (
                self._unitary_cumul_emissions_vintage(
                    fossil_ef,
                    exogenous_carbon_price_trajectory,
                    exogenous_carbon_price_trajectory,
                    reference_lifespan,
                    social_discount_rate,
                )
            )

        generic_specific_abatement_cost = (
            unitary_discounted_costs - reference_unitary_discounted_costs
        ) / (reference_unitary_discounted_emissions - unitary_discounted_emissions)
        specific_abatement_cost = (
            unitary_discounted_costs - reference_unitary_discounted_costs
        ) / (reference_unitary_emissions - unitary_emissions)

        abatement_cost = (mfsp - fossil_mfsp) / (fossil_ef - co2_emission_factor)

        # Unit conversion = > from €/gCO2 to €/tCO2
        specific_abatement_cost *= 1000000
        generic_specific_abatement_cost *= 1000000
        abatement_cost *= 1000000

        output_data = {
            f"{self.pathway_name}_specific_abatement_cost": specific_abatement_cost,
            f"{self.pathway_name}_generic_specific_abatement_cost": generic_specific_abatement_cost,
            f"{self.pathway_name}_abatement_cost": abatement_cost,
        }

        self._store_outputs(output_data)
        return output_data

    def _unitary_cumul_emissions_vintage(
        self,
        fossil_emission_factor: pd.Series,
        exogenous_carbon_price_trajectory: pd.Series,
        plant_lifespan: float,
        lhv_hydrogen: float,
        social_discount_rate: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
    ]:
        # Constants:

        indexes = fossil_emission_factor.index

        specific_em = pd.Series(np.nan, indexes)
        generic_discounted_specific_em = pd.Series(np.nan, indexes)

        for year in list(fossil_emission_factor.index):
            cumul_em = 0
            generic_discounted_cumul_em = 0
            for i in range(year, year + int(plant_lifespan)):
                if i < (self.end_year + 1):
                    cumul_em += fossil_emission_factor[i] * (lhv_hydrogen) / 1000000

                    # discounting emissions for non-hotelling scc
                    generic_discounted_cumul_em += (
                        fossil_emission_factor[i]
                        * exogenous_carbon_price_trajectory[i]
                        / exogenous_carbon_price_trajectory[year]
                        / (1 + social_discount_rate) ** (i - year)
                    )

                else:
                    cumul_em += fossil_emission_factor[self.end_year] * (lhv_hydrogen) / 1000000
                    # discounting emissions for non-hotelling scc, keep last year scc growth rate as future scc growth rate
                    future_scc_growth = (
                        exogenous_carbon_price_trajectory[self.end_year]
                        / exogenous_carbon_price_trajectory[self.end_year - 1]
                    )

                    generic_discounted_cumul_em += (
                        fossil_emission_factor[self.end_year]
                        * (
                            exogenous_carbon_price_trajectory[self.end_year]
                            / exogenous_carbon_price_trajectory[year]
                            * (future_scc_growth) ** (i - self.end_year)
                        )
                        / (1 + social_discount_rate) ** (i - year)
                    )

            specific_em[year] = cumul_em
            generic_discounted_specific_em[year] = generic_discounted_cumul_em

        return (specific_em, generic_discounted_specific_em)

    def _unit_kerozene_discounted_cumul_costs(
        self,
        kerosene_market_price: pd.Series,
        plant_lifespan: float,
        social_discount_rate: float,
    ) -> pd.Series:
        # Constants:

        indexes = kerosene_market_price.index

        specific_cost = pd.Series(np.nan, indexes)

        for year in list(kerosene_market_price.index):
            discounted_cumul_cost = 0
            for i in range(year, year + int(plant_lifespan)):
                if i < (self.end_year + 1):
                    discounted_cumul_cost += (kerosene_market_price[i]) / (
                        1 + social_discount_rate
                    ) ** (i - year)

                else:
                    discounted_cumul_cost += (kerosene_market_price[self.end_year]) / (
                        1 + social_discount_rate
                    ) ** (i - year)
            specific_cost[year] = discounted_cumul_cost

        return specific_cost

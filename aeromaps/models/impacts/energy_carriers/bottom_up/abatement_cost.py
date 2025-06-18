from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class EnergyAbatementCost(AeroMAPSModel):
    """
    Computes specific abatement cost and generic specific abatement cost for a pathway,
    based on discounted costs and avoided emissions over the lifespan of each vintage.
    """

    def __init__(self, name, pathway_name, *args, **kwargs):
        super().__init__(
            name=name,
            model_type="custom",
            *args,
            **kwargs,
        )
        self.pathway_name = pathway_name

        # Inputs needed: discounted costs, unitary emissions, discounted emissions
        self.input_names = {
            f"{self.pathway_name}_energy_consumption": pd.Series([0.0]),
            f"{self.pathway_name}_lifespan_unitary_discounted_costs": pd.Series([0.0]),
            f"{self.pathway_name}_lifespan_unitary_emissions": pd.Series([0.0]),
            f"{self.pathway_name}_lifespan_discounted_unitary_emissions": pd.Series([0.0]),
            f"{self.pathway_name}_mean_mfsp": pd.Series([0.0]),
            f"{self.pathway_name}_mean_co2_emission_factor": pd.Series([0.0]),
            f"{self.pathway_name}_eis_plant_lifespan": 0.0,
            "cac_reference_unitary_discounted_costs": pd.Series([0.0]),
            "cac_reference_unitary_discounted_emissions": pd.Series([0.0]),
            "cac_reference_unitary_emissions": pd.Series([0.0]),
            "cac_reference_co2_emission_factor": pd.Series([0.0]),
            "cac_reference_mfsp": pd.Series([0.0]),
            "social_discount_rate": 0.0,
            "exogenous_carbon_price_trajectory": pd.Series([0.0]),
        }

        # Outputs: specific abatement cost and generic specific abatement cost

        self.output_names = {
            f"{self.pathway_name}_carbon_abatement_cost": pd.Series([0.0]),
            f"{self.pathway_name}_specific_carbon_abatement_cost": pd.Series([0.0]),
            f"{self.pathway_name}_generic_specific_carbon_abatement_cost": pd.Series([0.0]),
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
        mfsp = input_data.get(f"{self.pathway_name}_mean_mfsp", pd.Series([0.0]))
        co2_emission_factor = input_data.get(
            f"{self.pathway_name}_mean_co2_emission_factor", pd.Series([0.0])
        )
        fossil_mfsp = input_data.get("cac_reference_mfsp", pd.Series([0.0]))
        fossil_ef = input_data.get("cac_reference_co2_emission_factor", pd.Series([0.0]))

        reference_unitary_discounted_costs = input_data.get(
            "cac_reference_unitary_discounted_costs", pd.Series([0.0])
        )
        reference_unitary_discounted_emissions = input_data.get(
            "cac_reference_unitary_discounted_emissions", pd.Series([0.0])
        )
        reference_unitary_emissions = input_data.get(
            "cac_reference_unitary_emissions", pd.Series([0.0])
        )

        generic_specific_carbon_abatement_cost = (
            unitary_discounted_costs - reference_unitary_discounted_costs
        ) / (reference_unitary_discounted_emissions - unitary_discounted_emissions)
        specific_carbon_abatement_cost = (
            unitary_discounted_costs - reference_unitary_discounted_costs
        ) / (reference_unitary_emissions - unitary_emissions)

        carbon_abatement_cost = (mfsp - fossil_mfsp) / (fossil_ef - co2_emission_factor)

        # Unit conversion = > from €/gCO2 to €/tCO2
        specific_carbon_abatement_cost *= 1000000
        generic_specific_carbon_abatement_cost *= 1000000
        carbon_abatement_cost *= 1000000

        output_data = {
            f"{self.pathway_name}_specific_carbon_abatement_cost": specific_carbon_abatement_cost,
            f"{self.pathway_name}_generic_specific_carbon_abatement_cost": generic_specific_carbon_abatement_cost,
            f"{self.pathway_name}_carbon_abatement_cost": carbon_abatement_cost,
        }

        self._store_outputs(output_data)
        return output_data


class ReferenceAbatementCost(AeroMAPSModel):
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
            "social_discount_rate": 0.0,
            "exogenous_carbon_price_trajectory": pd.Series([0.0]),
        }

        # 2 cases: either ref pathway is defined to-down, as before. Weak CAC definition, considering its average price and EF
        # 1:
        if (
            configuration_data["cost_model"] == "bottom-up"
            and configuration_data["cost_model"] == "bottom-up"
        ):
            self.input_names.update(
                {
                    f"{self.pathway_name}_lifespan_unitary_discounted_costs": pd.Series([0.0]),
                    f"{self.pathway_name}_lifespan_unitary_emissions": pd.Series([0.0]),
                    f"{self.pathway_name}_lifespan_discounted_unitary_emissions": pd.Series([0.0]),
                    f"{self.pathway_name}_mean_mfsp": pd.Series([0.0]),
                    f"{self.pathway_name}_mean_co2_emission_factor": pd.Series([0.0]),
                }
            )
            self.bottom_up_cac = True
        else:
            print(
                f"⚠️ Warning: reference pathway for CAC ({self.pathway_name} is not defined as bottom-up, "
                f"using top-down values for CAC computation."
            )
            self.input_names.update(
                {
                    f"{self.pathway_name}_mean_mfsp": pd.Series([0.0]),
                    f"{self.pathway_name}_mean_co2_emission_factor": pd.Series([0.0]),
                }
            )
            self.bottom_up_cac = False

        # Outputs: specific abatement cost and generic specific abatement cost

        self.output_names = {
            "cac_reference_unitary_discounted_costs": pd.Series([0.0]),
            "cac_reference_unitary_discounted_emissions": pd.Series([0.0]),
            "cac_reference_unitary_emissions": pd.Series([0.0]),
            "cac_reference_co2_emission_factor": pd.Series([0.0]),
            "cac_reference_mfsp": pd.Series([0.0]),
        }

    def compute(self, input_data) -> dict:
        """
        Compute the specific abatement cost and generic specific abatement cost for each vintage.
        """

        ref_mfsp = input_data.get(f"{self.pathway_name}_mean_mfsp", pd.Series([0.0]))
        ref_ef = input_data.get(f"{self.pathway_name}_mean_co2_emission_factor", pd.Series([0.0]))

        if self.bottom_up_cac:
            reference_unitary_discounted_costs = input_data.get(
                f"{self.pathway_name}_lifespan_unitary_discounted_costs", pd.Series([0.0])
            )
            reference_unitary_discounted_emissions = input_data.get(
                f"{self.pathway_name}_lifespan_discounted_unitary_emissions", pd.Series([0.0])
            )
            reference_unitary_emissions = input_data.get(
                f"{self.pathway_name}_lifespan_unitary_emissions", pd.Series([0.0])
            )

        else:
            reference_lifespan = input_data.get(f"{self.pathway_name}_eis_plant_lifespan", 25.0)
            social_discount_rate = input_data.get("social_discount_rate")
            exogenous_carbon_price_trajectory = input_data.get(
                "exogenous_carbon_price_trajectory", pd.Series([0.0])
            )

            reference_unitary_discounted_costs = self._unit_discounted_cumul_costs(
                ref_mfsp, reference_lifespan, social_discount_rate
            )
            (reference_unitary_emissions, reference_unitary_discounted_emissions) = (
                self._unitary_cumul_emissions_vintage(
                    ref_ef,
                    exogenous_carbon_price_trajectory,
                    reference_lifespan,
                    social_discount_rate,
                )
            )

        output_data = {
            "cac_reference_unitary_discounted_costs": reference_unitary_discounted_costs,
            "cac_reference_unitary_discounted_emissions": reference_unitary_discounted_emissions,
            "cac_reference_unitary_emissions": reference_unitary_emissions,
            "cac_reference_co2_emission_factor": ref_ef,
            "cac_reference_mfsp": ref_mfsp,
        }

        self._store_outputs(output_data)
        return output_data

    def _unitary_cumul_emissions_vintage(
        self,
        fossil_emission_factor: pd.Series,
        exogenous_carbon_price_trajectory: pd.Series,
        plant_lifespan: float,
        social_discount_rate: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
    ]:
        # Print all arguments for debugging:
        indexes = fossil_emission_factor.index
        specific_em = pd.Series(np.nan, indexes)
        generic_discounted_specific_em = pd.Series(np.nan, indexes)

        for year in list(fossil_emission_factor.index):
            cumul_em = 0
            generic_discounted_cumul_em = 0
            for i in range(year, year + int(plant_lifespan)):
                if i < (self.end_year + 1):
                    cumul_em += fossil_emission_factor[i]

                    # discounting emissions for non-hotelling scc
                    generic_discounted_cumul_em += (
                        fossil_emission_factor[i]
                        * exogenous_carbon_price_trajectory[i]
                        / exogenous_carbon_price_trajectory[year]
                        / (1 + social_discount_rate) ** (i - year)
                    )

                else:
                    cumul_em += fossil_emission_factor[self.end_year]
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

    def _unit_discounted_cumul_costs(
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

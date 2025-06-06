# @Time : 13/03/2023 10:46
# @Author : a.salgas
# @File : scenario_cost.py
# @Software: PyCharm
import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class NonDiscountedScenarioCost(AeroMAPSModel):
    def __init__(self, name="non_discounted_scenario_cost", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
        """
        Dynamically add all pathway mfsps and associated energy consumption variables to input_names.
        """
        self.input_names = {}
        if self.pathways_manager is not None:
            for p in self.pathways_manager.get_all():
                self.input_names[f"{p.name}_net_mfsp"] = pd.Series([0.0])
                self.input_names[f"{p.name}_mfsp"] = pd.Series([0.0])
                self.input_names[f"{p.name}_energy_consumption"] = pd.Series([0.0])
                if p.name == "fossil_kerosene":
                    self.input_names["fossil_kerosene_co2_emission_factor"] = pd.Series([0.0])

        # Add BAU computation
        self.input_names["co2_emissions_2019technology"] = pd.Series([0.0])
        self.input_names["co2_emissions_including_load_factor"] = pd.Series([0.0])
        self.input_names["carbon_tax"] = pd.Series([0.0])

        self.output_names = {
            "non_discounted_energy_expenses": pd.Series([0.0]),
            "non_discounted_net_energy_expenses": pd.Series([0.0]),
            "non_discounted_bau_energy_expenses": pd.Series([0.0]),
            "non_discounted_full_kero_energy_expenses": pd.Series([0.0]),
        }

    def compute(self, input_data) -> dict:
        # Compute the total energy expenses of the scenario
        non_discounted_energy_expenses = None
        non_discounted_net_energy_expenses = None
        for p in self.pathways_manager.get_all():
            net_mfsp = input_data.get(f"{p.name}_net_mfsp", pd.Series([0.0])).fillna(0)
            mfsp = input_data.get(f"{p.name}_mfsp", pd.Series([0.0])).fillna(0)
            energy_consumption = input_data.get(
                f"{p.name}_energy_consumption", pd.Series([0.0])
            ).fillna(0)
            cost = mfsp * energy_consumption
            net_cost = net_mfsp * energy_consumption
            if non_discounted_energy_expenses is None:
                non_discounted_energy_expenses = cost
                non_discounted_net_energy_expenses = net_cost
            else:
                non_discounted_energy_expenses = non_discounted_energy_expenses.add(
                    cost, fill_value=0
                )
                non_discounted_net_energy_expenses = non_discounted_net_energy_expenses.add(
                    net_cost, fill_value=0
                )

        non_discounted_energy_expenses = (
            non_discounted_energy_expenses / 1000000
        )  # Convert to millions euros
        non_discounted_net_energy_expenses = (
            non_discounted_net_energy_expenses / 1000000
        )  # Convert to millions euros

        # Compute the business as usual energy expenses

        if "fossil_kerosene_co2_emission_factor" not in input_data:
            print(
                "Warning: fossil_kerosene pathway not found in input data. Illustrative kerosene costs computed using defauylt values."
            )
            kerosene_emission_factor = 88.7
            kerosene_market_price = 0.013921201
        else:
            kerosene_emission_factor = input_data["fossil_kerosene_co2_emission_factor"].loc[
                self.prospection_start_year - 1
            ]
            kerosene_market_price = input_data["fossil_kerosene_mfsp"]

        co2_emissions_including_load_factor = input_data["co2_emissions_including_load_factor"]
        carbon_tax = input_data["carbon_tax"]
        energy_consumption_full_kero = (
            co2_emissions_including_load_factor * 1e12 / kerosene_emission_factor
        )

        non_discounted_full_kero_energy_expenses = (
            energy_consumption_full_kero * kerosene_market_price / 1000000
        )  # in million euros

        carbon_tax_full_kero = (
            co2_emissions_including_load_factor * carbon_tax
        )  # * 1e6 / 1e6 : to t co2 and to million euros

        co2_emissions_2019technology = input_data["co2_emissions_2019technology"]

        energy_consumption_bau = co2_emissions_2019technology * 1e12 / kerosene_emission_factor

        non_discounted_bau_energy_expenses = (
            energy_consumption_bau * kerosene_market_price / 1000000
        )  # in million euros

        carbon_tax_bau = (
            co2_emissions_2019technology * carbon_tax
        )  # * 1e6 / 1e6 : to t co2 and to million euros

        output_data = {
            "non_discounted_energy_expenses": non_discounted_energy_expenses,
            "non_discounted_net_energy_expenses": non_discounted_net_energy_expenses,
            "non_discounted_bau_energy_expenses": non_discounted_bau_energy_expenses,
            "non_discounted_full_kero_energy_expenses": non_discounted_full_kero_energy_expenses,
            "carbon_tax_full_kero": carbon_tax_full_kero,
            "carbon_tax_bau": carbon_tax_bau,
        }

        self._store_outputs(output_data)

        return output_data


class DicountedScenarioCost(AeroMAPSModel):
    def __init__(self, name="discounted_scenario_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        non_discounted_energy_expenses: pd.Series,
        social_discount_rate: float,
    ) -> pd.Series:
        discounted_energy_expenses = non_discounted_energy_expenses.copy()
        for k in range(self.prospection_start_year, self.end_year + 1):
            # Compute the discounter at year k
            discount_k = (1 + social_discount_rate) ** (k - self.prospection_start_year)
            # Apply the discount to the non-discounted energy expenses
            discounted_energy_expenses.loc[k] = discounted_energy_expenses.loc[k] / discount_k

        self.df.loc[:, "discounted_energy_expenses"] = discounted_energy_expenses

        return discounted_energy_expenses

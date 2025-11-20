# @Time : 13/03/2023 10:46
# @Author : a.salgas
# @File : scenario_cost.py
# @Software: PyCharm
"""
scenario_cost
===============================
Module to compute overall scenario costs.
"""

from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class NonDiscountedScenarioCost(AeroMAPSModel):
    """
    Class to compute the non-discounted energy expenses of the scenario.

    Parameters
    --------------
    name : str
        Name of the model instance ('non_discounted_scenario_cost' by default).

    Attributes
    --------------
    pathways_manager : EnergyCarrierManager
        EnergyCarrierManager instance to manage generic energy pathways and their data.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.

    Warnings
    --------------
    - Detailed i/o documentation is not yet provided for models defined wityh generic .yaml files?
    """

    def __init__(self, name="non_discounted_scenario_cost", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None
        # TODO rename in EnergyCost. Same for discounted function below.
        #   Provide detailed i/o documentation.

    def custom_setup(self):
        """
        Dynamically add all pathway MFSPs and associated energy consumption variables to input_names and function outputs to output_names.
        Specific function for custom AeroMAPSModel instances.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.input_names = {}
        if self.pathways_manager is not None:
            for p in self.pathways_manager.get_all():
                self.input_names[f"{p.name}_net_mfsp"] = pd.Series([0.0])
                self.input_names[f"{p.name}_mean_mfsp"] = pd.Series([0.0])
                self.input_names[f"{p.name}_energy_consumption"] = pd.Series([0.0])
                if p.name == "fossil_kerosene":
                    self.input_names["fossil_kerosene_mean_co2_emission_factor"] = pd.Series([0.0])

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
        """
        Compute the total energy expenses of the scenario

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.

        """
        # Compute the total energy expenses of the scenario
        non_discounted_energy_expenses = None
        non_discounted_net_energy_expenses = None
        for p in self.pathways_manager.get_all():
            net_mfsp = input_data.get(f"{p.name}_net_mfsp", pd.Series([0.0])).fillna(0)
            mfsp = input_data.get(f"{p.name}_mean_mfsp", pd.Series([0.0])).fillna(0)
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

        if "fossil_kerosene_mean_co2_emission_factor" not in input_data:
            print(
                "Warning: fossil_kerosene pathway not found in input data. Illustrative kerosene costs computed using default values."
            )
            kerosene_emission_factor = 88.7
            kerosene_market_price = 0.013921201
        else:
            kerosene_emission_factor = input_data["fossil_kerosene_mean_co2_emission_factor"].loc[
                self.prospection_start_year - 1
            ]
            kerosene_market_price = input_data["fossil_kerosene_mean_mfsp"]

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
    """
    Class to compute the discounted energy expenses of the scenario.

    Parameters
    --------------
    name : str
        Name of the model instance ('discounted_scenario_cost' by default).
    """

    def __init__(self, name="discounted_scenario_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        non_discounted_energy_expenses: pd.Series,
        social_discount_rate: float,
    ) -> Tuple[pd.Series, float]:
        """
        Execute the computation of discounted energy expenses of the scenario.

        Parameters
        ----------
        non_discounted_energy_expenses
            Non-discounted energy expenses [M€].
        social_discount_rate
            Social discount rate [%].

        Returns
        -------
        discounted_energy_expenses
            Discounted energy expenses [M€].
        discounted_energy_expenses_obj
            Cumulative discounted energy expenses at the end of the prospection period [M€].

        """
        discounted_energy_expenses = non_discounted_energy_expenses.copy()
        for k in range(self.prospection_start_year, self.end_year + 1):
            # Compute the discounter at year k
            discount_k = (1 + social_discount_rate) ** (k - self.prospection_start_year)
            # Apply the discount to the non-discounted energy expenses
            discounted_energy_expenses.loc[k] = discounted_energy_expenses.loc[k] / discount_k

        self.df.loc[:, "discounted_energy_expenses"] = discounted_energy_expenses

        discounted_energy_expenses_obj = discounted_energy_expenses.cumsum()[self.end_year]

        return discounted_energy_expenses, discounted_energy_expenses_obj


class TotalAirlineCostNoElast(AeroMAPSModel):
    """
    Class to compute total airline costs without considering demand elasticity.
    To be used with a fixed demand configuration only.

    Parameters
    --------------
    name : str
        Name of the model instance ('total_airline_cost_no_elast' by default).
    """

    def __init__(self, name="total_airline_cost_no_elast", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        total_cost_per_rpk: pd.Series,
        rpk: pd.Series,
        social_discount_rate: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        float,
    ]:
        """
        Execute the computation of total airline costs (to be used with a fixed demand configuration only).

        Parameters
        ----------
        total_cost_per_rpk
            Total cost per RPK [€/RPK].
        rpk
            Revenue passenger kilometers [RPK].
        social_discount_rate
            Social discount rate [%].

        Returns
        -------
        total_airline_cost
            Total airline cost [M€].
        cumulative_total_airline_cost
            Cumulative total airline cost [M€].
        cumulative_total_airline_cost_discounted
            Cumulative total airline cost discounted [M€].
        cumulative_total_airline_cost_increase
            Cumulative total airline cost increase [M€].
        cumulative_total_airline_cost_increase_discounted
            Cumulative total airline cost increase discounted [M€].
        cumulative_total_airline_cost_discounted_obj
            Cumulative total airline cost increase discounted at the end of the prospection period [M€].

        """
        initial_airline_cost = total_cost_per_rpk[self.prospection_start_year - 1] * rpk
        total_airline_cost = total_cost_per_rpk * rpk
        total_airline_cost_increase = total_airline_cost - initial_airline_cost

        total_airline_cost_discounted = total_airline_cost / (1 + social_discount_rate) ** (
            self.df.index - self.prospection_start_year
        )

        total_airline_cost_increase_discounted = total_airline_cost_increase / (
            1 + social_discount_rate
        ) ** (self.df.index - self.prospection_start_year)

        cumulative_total_airline_cost = total_airline_cost.cumsum()
        cumulative_total_airline_cost_discounted = total_airline_cost_discounted.cumsum()

        cumulative_total_airline_cost_increase = total_airline_cost_increase.cumsum()
        cumulative_total_airline_cost_increase_discounted = (
            total_airline_cost_increase_discounted.cumsum()
        )

        self.df.loc[:, "total_airline_cost"] = total_airline_cost
        self.df.loc[:, "cumulative_total_airline_cost"] = cumulative_total_airline_cost
        self.df.loc[:, "cumulative_total_airline_cost_discounted"] = (
            cumulative_total_airline_cost_discounted
        )
        self.df.loc[:, "total_airline_cost_increase"] = total_airline_cost_increase
        self.df.loc[:, "cumulative_total_airline_cost_increase"] = (
            cumulative_total_airline_cost_increase
        )
        self.df.loc[:, "cumulative_total_airline_cost_increase_discounted"] = (
            cumulative_total_airline_cost_increase_discounted
        )

        cumulative_total_airline_cost_discounted_obj = (
            cumulative_total_airline_cost_increase_discounted[self.end_year]
            - cumulative_total_airline_cost_increase_discounted[2025]
        )

        return (
            total_airline_cost,
            cumulative_total_airline_cost,
            cumulative_total_airline_cost_discounted,
            cumulative_total_airline_cost_increase,
            cumulative_total_airline_cost_increase_discounted,
            cumulative_total_airline_cost_discounted_obj,
        )


class TotalAirlineCost(AeroMAPSModel):
    """
    Class to compute total airline costs (to be used when considering demand elasticity).

    Parameters
    --------------
    name : str
        Name of the model instance ('total_airline_cost' by default).
    """

    def __init__(self, name="total_airline_cost", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        total_cost_per_rpk: pd.Series,
        rpk: pd.Series,
        rpk_no_elasticity: pd.Series,
        social_discount_rate: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        float,
    ]:
        """
        Execute the computation of total airline costs.

        Parameters
        ----------
        total_cost_per_rpk
            Total cost per RPK [€/RPK].
        rpk
            Revenue passenger kilometers [RPK].
        rpk_no_elasticity
            Revenue passenger kilometers without demand elasticity (exogenous growth assumption) [RPK].
        social_discount_rate
            Social discount rate [%].

        Returns
        -------
        total_airline_cost
            Total airline cost [M€].
        cumulative_total_airline_cost
            Cumulative total airline cost [M€].
        cumulative_total_airline_cost_discounted
            Cumulative total airline cost discounted [M€].
        cumulative_total_airline_cost_increase
            Cumulative total airline cost increase [M€].
        cumulative_total_airline_cost_increase_discounted
            Cumulative total airline cost increase discounted [M€].
        cumulative_total_airline_cost_discounted_obj
            Cumulative total airline cost increase discounted at the end of the prospection period [M€].

        """
        initial_airline_cost = (
            total_cost_per_rpk[self.prospection_start_year - 1] * rpk_no_elasticity
        )
        total_airline_cost = total_cost_per_rpk * rpk
        total_airline_cost_increase = total_airline_cost - initial_airline_cost

        total_airline_cost_discounted = total_airline_cost / (1 + social_discount_rate) ** (
            self.df.index - self.prospection_start_year
        )

        total_airline_cost_increase_discounted = total_airline_cost_increase / (
            1 + social_discount_rate
        ) ** (self.df.index - self.prospection_start_year)

        cumulative_total_airline_cost = total_airline_cost.cumsum()
        cumulative_total_airline_cost_discounted = total_airline_cost_discounted.cumsum()

        cumulative_total_airline_cost_increase = total_airline_cost_increase.cumsum()
        cumulative_total_airline_cost_increase_discounted = (
            total_airline_cost_increase_discounted.cumsum()
        )

        self.df.loc[:, "total_airline_cost"] = total_airline_cost
        self.df.loc[:, "cumulative_total_airline_cost"] = cumulative_total_airline_cost
        self.df.loc[:, "cumulative_total_airline_cost_discounted"] = (
            cumulative_total_airline_cost_discounted
        )
        self.df.loc[:, "total_airline_cost_increase"] = total_airline_cost_increase
        self.df.loc[:, "cumulative_total_airline_cost_increase"] = (
            cumulative_total_airline_cost_increase
        )
        self.df.loc[:, "cumulative_total_airline_cost_increase_discounted"] = (
            cumulative_total_airline_cost_increase_discounted
        )

        cumulative_total_airline_cost_discounted_obj = (
            cumulative_total_airline_cost_increase_discounted[self.end_year]
            - cumulative_total_airline_cost_increase_discounted[2025]
        )

        return (
            total_airline_cost,
            cumulative_total_airline_cost,
            cumulative_total_airline_cost_discounted,
            cumulative_total_airline_cost_increase,
            cumulative_total_airline_cost_increase_discounted,
            cumulative_total_airline_cost_discounted_obj,
        )


class TotalSurplusLoss(AeroMAPSModel):
    """
    Class to compute directly the total surplus loss (area loss + airline cost increase)
    No distinction between consumer surplus and producer surplus / tax revenues

    Parameters
    --------------
    name : str
        Name of the model instance ('total_surplus_loss' by default).
    """

    def __init__(self, name="total_surplus_loss", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        rpk: pd.Series,
        rpk_no_elasticity: pd.Series,
        cumulative_total_airline_cost_increase: pd.Series,
        cumulative_total_airline_cost_increase_discounted: pd.Series,
        airfare_per_rpk: pd.Series,
        price_elasticity: float,
        social_discount_rate: float,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, float]:
        """
        Execute the computation of total surplus loss.

        Parameters
        ----------
        rpk
            Revenue passenger kilometers [RPK].
        rpk_no_elasticity
            Revenue passenger kilometers without demand elasticity (exogenous growth assumption) [RPK].
        cumulative_total_airline_cost_increase
            Cumulative total airline cost increase [M€].
        cumulative_total_airline_cost_increase_discounted
            Cumulative total airline cost increase discounted [M€].
        airfare_per_rpk
            Airfare per RPK [€/RPK].
        price_elasticity
            Price elasticity of demand [-].
        social_discount_rate
            Social discount rate [%].

        Returns
        -------
        area_loss
            Area loss under the demand curve [M€].
        cumulative_total_surplus_loss
            Cumulative relative total surplus loss [M€].
        cumulative_total_surplus_loss_discounted
            Cumulative relative total surplus loss discounted [M€].
        cumulative_total_surplus_loss_discounted_obj
            Cumulative relative total surplus loss discounted at the end of the prospection period [M€].
        """

        # computation of demand function parameters: asummption => constant elasticity => P= beta * Q**(1/elasticity)
        beta = airfare_per_rpk[2025] / (rpk_no_elasticity ** (1 / price_elasticity))

        # Gloabl Surplus before removing total costs

        if price_elasticity == -1:
            # surplus delta extresssed by CS= beta * np.log(Qref/Qi)
            area_loss = beta * np.log(rpk_no_elasticity / rpk)

        else:
            area_loss = (
                beta
                * (1 / (1 + 1 / price_elasticity))
                * (
                    rpk_no_elasticity ** (1 + 1 / price_elasticity)
                    - rpk ** (1 + 1 / price_elasticity)
                )
            )

        self.df.loc[:, "area_loss"] = area_loss

        area_loss_discounted = area_loss / (1 + social_discount_rate) ** (
            self.df.index - self.prospection_start_year
        )

        self.df.loc[:, "area_loss_discounted"] = area_loss_discounted

        cumulative_total_surplus_loss = area_loss.cumsum() + cumulative_total_airline_cost_increase
        cumulative_total_surplus_loss_discounted = (
            area_loss_discounted.cumsum()
            + cumulative_total_airline_cost_increase_discounted[self.end_year]
            - cumulative_total_airline_cost_increase_discounted[2025]
        )

        self.df.loc[:, "cumulative_total_surplus_loss"] = cumulative_total_surplus_loss
        self.df.loc[:, "cumulative_total_surplus_loss_discounted"] = (
            cumulative_total_surplus_loss_discounted
        )

        cumulative_total_surplus_loss_discounted_obj = cumulative_total_surplus_loss_discounted[
            self.end_year
        ]

        return (
            area_loss,
            cumulative_total_surplus_loss,
            cumulative_total_surplus_loss_discounted,
            cumulative_total_surplus_loss_discounted_obj,
        )


class ConsumerSurplusLoss(AeroMAPSModel):
    """
    Class to compute the consumer surplus loss.
    Should not be used alongside TotalSurplusLoss.

    Parameters
    --------------
    name : str
        Name of the model instance ('consumer_surplus_loss' by default).

    """

    def __init__(self, name="consumer_surplus_loss", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        rpk: pd.Series,
        rpk_no_elasticity: pd.Series,
        airfare_per_rpk: pd.Series,
        price_elasticity: float,
        social_discount_rate: float,
    ) -> Tuple[pd.Series, pd.Series, float]:
        """

        Parameters
        ----------
        rpk
            Revenue passenger kilometers [RPK].
        rpk_no_elasticity
            Revenue passenger kilometers without demand elasticity (exogenous growth assumption) [RPK].
        airfare_per_rpk
            Airfare per RPK [€/RPK].
        price_elasticity
            Price elasticity of demand [-].
        social_discount_rate
            Social discount rate [%].

        Returns
        -------
        delta_consumer_surplus
            Consumer relative surplus loss [M€].
        delta_consumer_surplus_discounted
            Consumer relative surplus loss discounted [M€].

        """
        # computation of demand function parameters: assumption => constant elasticity => P= beta * Q**(1/elasticity)
        beta = airfare_per_rpk[2025] / (rpk_no_elasticity ** (1 / price_elasticity))

        # Passenger Surplus = area under demand curve - price

        if price_elasticity == -1:
            # surplus delta expresssed by CS= beta * np.log(Qref/Qi)
            delta_consumer_surplus = beta * np.log(rpk_no_elasticity / rpk)
            # FIXME SHOULD NOT BE THE SAME AS IN TOTAL SURPLUS LOSS WITH E=1

        else:
            # surplus delta expressed by
            delta_consumer_surplus = (
                beta
                * (-1 / (1 + price_elasticity))
                * (
                    rpk_no_elasticity ** (1 + 1 / price_elasticity)
                    - rpk ** (1 + 1 / price_elasticity)
                )
            )

        self.df.loc[:, "delta_consumer_surplus"] = delta_consumer_surplus

        delta_consumer_surplus_discounted = delta_consumer_surplus / (1 + social_discount_rate) ** (
            self.df.index - self.prospection_start_year
        )

        self.df.loc[:, "delta_consumer_surplus_discounted"] = delta_consumer_surplus_discounted

        cumulative_delta_consumer_surplus_obj = (
            delta_consumer_surplus_discounted.cumsum()[self.end_year]
            - delta_consumer_surplus_discounted.cumsum()[2025]
        )

        return (
            delta_consumer_surplus,
            delta_consumer_surplus_discounted,
            cumulative_delta_consumer_surplus_obj,
        )


class AirlineSurplusLoss(AeroMAPSModel):
    """
    Class to compute the airline surplus loss.
    Should not be used alongside TotalSurplusLoss.

    Parameters
    --------------
    name : str
        Name of the model instance ('airline_surplus_loss' by default).
    """

    def __init__(self, name="airline_surplus_loss", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        total_cost_per_rpk: pd.Series,
        rpk: pd.Series,
        rpk_no_elasticity: pd.Series,
        social_discount_rate: float,
        airfare_per_rpk: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, float]:
        """
        Execute the computation of airline surplus loss.

        Parameters
        ----------
        total_cost_per_rpk
            Total cost per RPK [€/RPK].
        rpk
            Revenue passenger kilometers [RPK].
        rpk_no_elasticity
            Revenue passenger kilometers without demand elasticity (exogenous growth assumption) [RPK].
        social_discount_rate
            Social discount rate [%].
        airfare_per_rpk
            Airfare per RPK [€/RPK].

        Returns
        -------
        delta_airline_surplus
            Airline relative surplus loss [M€].
        delta_airline_surplus_discounted
            Airline relative surplus loss discounted [M€].
        total_airline_surplus
            Total airline surplus [M€].
        cumulative_delta_airline_surplus_obj
            Cumulative airline relative surplus loss discounted at the end of the prospection period [M€

        """
        total_airline_cost = total_cost_per_rpk * rpk
        total_airline_revenue = airfare_per_rpk * rpk
        total_airline_surplus = total_airline_revenue - total_airline_cost

        initial_airline_cost = (
            total_cost_per_rpk[self.prospection_start_year - 1] * rpk_no_elasticity
        )
        initial_airline_revenue = (
            airfare_per_rpk[self.prospection_start_year - 1] * rpk_no_elasticity
        )
        initial_airline_surplus = initial_airline_revenue - initial_airline_cost

        delta_airline_surplus = initial_airline_surplus - total_airline_surplus
        delta_airline_surplus_discounted = delta_airline_surplus / (1 + social_discount_rate) ** (
            self.df.index - self.prospection_start_year
        )

        cumulative_delta_airline_surplus_obj = (
            delta_airline_surplus_discounted.cumsum()[self.end_year]
            - delta_airline_surplus_discounted.cumsum()[2025]
        )

        self.df.loc[:, "delta_airline_surplus"] = delta_airline_surplus
        self.df.loc[:, "delta_airline_surplus_discounted"] = delta_airline_surplus_discounted
        self.df.loc[:, "total_airline_surplus"] = total_airline_surplus

        return (
            delta_airline_surplus,
            delta_airline_surplus_discounted,
            total_airline_surplus,
            cumulative_delta_airline_surplus_obj,
        )


class TaxRevenueLoss(AeroMAPSModel):
    """
    Class to compute the tax revenue loss.

    Parameters
    --------------
    name : str
        Name of the model instance ('tax_revenue_loss' by default).

    """

    def __init__(self, name="tax_revenue_loss", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        total_extra_tax_per_rpk: pd.Series,
        rpk: pd.Series,
        rpk_no_elasticity: pd.Series,
        social_discount_rate: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        float,
    ]:
        """
        Execute the computation of tax revenue loss.

        Parameters
        ----------
        total_extra_tax_per_rpk
            Total extra tax per RPK [€/RPK].
        rpk
            Revenue passenger kilometers [RPK].
        rpk_no_elasticity
            Revenue passenger kilometers without demand elasticity (exogenous growth assumption) [RPK].
        social_discount_rate
            Social discount rate [%].

        Returns
        -------
        total_tax_revenue
            Total tax revenue [M€].
        delta_tax_revenue
            Tax revenue loss [M€].
        delta_tax_revenue_discounted
            Tax revenue loss discounted [M€].
        cumulative_delta_tax_revenue_obj
            Cumulative tax revenue loss discounted at the end of the prospection period [M€].

        """
        total_tax_revenue = total_extra_tax_per_rpk * rpk
        initial_tax_revenue = (
            total_extra_tax_per_rpk[self.prospection_start_year - 1] * rpk_no_elasticity
        )
        delta_tax_revenue = initial_tax_revenue - total_tax_revenue

        delta_tax_revenue_discounted = delta_tax_revenue / (1 + social_discount_rate) ** (
            self.df.index - self.prospection_start_year
        )

        cumulative_delta_tax_revenue_obj = (
            delta_tax_revenue_discounted.cumsum()[self.end_year]
            - delta_tax_revenue_discounted.cumsum()[2025]
        )

        self.df.loc[:, "total_tax_revenue"] = total_tax_revenue
        self.df.loc[:, "delta_tax_revenue"] = delta_tax_revenue
        self.df.loc[:, "delta_tax_revenue_discounted"] = delta_tax_revenue_discounted

        return (
            total_tax_revenue,
            delta_tax_revenue,
            delta_tax_revenue_discounted,
            cumulative_delta_tax_revenue_obj,
        )


class TotalWelfareLoss(AeroMAPSModel):
    """
    Class to compute the total welfare loss.

    Parameters
    --------------
    name : str
        Name of the model instance ('total_welfare_loss' by default).
    """

    def __init__(self, name="total_welfare_loss", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        delta_tax_revenue: pd.Series,
        delta_consumer_surplus: pd.Series,
        delta_airline_surplus: pd.Series,
        social_discount_rate: float,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, float]:
        """
        Execute the computation of total welfare loss.

        Parameters
        ----------
        delta_tax_revenue
            Tax revenue loss [M€].
        delta_consumer_surplus
            Consumer relative surplus loss [M€].
        delta_airline_surplus
            Airline relative surplus loss [M€].
        social_discount_rate
            Social discount rate [%].

        Returns
        -------
        total_welfare_loss
            Total welfare loss [M€].
        total_welfare_loss_discounted
            Total welfare loss discounted [M€].
        cumulative_total_welfare_loss_discounted
            Cumulative total welfare loss discounted [M€].
        cumulative_total_welfare_loss_obj
            Cumulative total welfare loss discounted at the end of the prospection period [M€].
        """

        total_welfare_loss = delta_consumer_surplus + delta_airline_surplus + delta_tax_revenue
        total_welfare_loss_discounted = total_welfare_loss / (1 + social_discount_rate) ** (
            self.df.index - self.prospection_start_year
        )

        cumulative_total_welfare_loss_discounted = total_welfare_loss_discounted.cumsum()

        cumulative_total_welfare_loss_obj = (
            cumulative_total_welfare_loss_discounted[self.end_year]
            - cumulative_total_welfare_loss_discounted[2025]
        )

        self.df.loc[:, "total_welfare_loss"] = total_welfare_loss
        self.df.loc[:, "total_welfare_loss_discounted"] = total_welfare_loss_discounted
        self.df.loc[:, "cumulative_total_welfare_loss_discounted"] = (
            cumulative_total_welfare_loss_discounted
        )

        return (
            total_welfare_loss,
            total_welfare_loss_discounted,
            cumulative_total_welfare_loss_discounted,
            cumulative_total_welfare_loss_obj,
        )

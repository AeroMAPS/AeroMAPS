# @Time : 04/01/2024 15:41
# @Author : a.salgas
# @File : total_airline_cost_and_airfare.py
# @Software: PyCharm
"""
total_airline_cost_and_airfare

====================================================
Module grouping models to compute total airline costs and airfares for passenger aircraft.
"""

# import numpy as np
import pandas as pd
# from scipy.interpolate import interp1d

from aeromaps.models.base import AeroMAPSModel  # , aeromaps_interpolation_function


class PassengerAircraftSimpleAirfare(AeroMAPSModel):
    """
    Class to compute simple airfare for passenger aircraft based on total cost and (fixed) operational profit.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_simple_airfare' by default).
    """

    def __init__(self, name="passenger_aircraft_simple_airfare", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        self.input_names = {
            "total_cost_per_ask": pd.Series([0.0]),
            "load_factor": pd.Series([0.0]),
            "operational_profit_per_ask": pd.Series([0.0]),
        }
        self.output_names = {
            "airfare_per_ask": pd.Series([0.0]),
            "airfare_per_rpk": pd.Series([0.0]),
        }

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            self.input_names[f"total_cost_per_ask_{mid}"] = pd.Series([0.0])
            self.output_names[f"airfare_per_ask_{mid}"] = pd.Series([0.0])
            self.output_names[f"airfare_per_rpk_{mid}"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        Execute the computation of simple airfare computation.

        Parameters
        ----------
        total_cost_per_ask
            Total cost per available seat kilometer (ASK) [€/ASK].
        total_cost_per_ask_short_range
            Total cost per available seat kilometer (ASK) for short-range flights [€/ASK].
        total_cost_per_ask_medium_range
            Total cost per available seat kilometer (ASK) for medium-range flights [€/ASK].
        total_cost_per_ask_long_range
            Total cost per available seat kilometer (ASK) for long-range flights [€/ASK].
        load_factor
            Load factor [%].
        operational_profit_per_ask
            Operational profit per available seat kilometer (ASK) [€/ASK].

        Returns
        -------
        airfare_per_ask
            Airfare per available seat kilometer (ASK) [€/ASK].
        airfare_per_ask_short_range
            Airfare per available seat kilometer (ASK) for short-range flights [€/ASK].
        airfare_per_ask_medium_range
            Airfare per available seat kilometer (ASK) for medium-range flights [€/ASK].
        airfare_per_ask_long_range
            Airfare per available seat kilometer (ASK) for long-range flights [€/ASK].
        airfare_per_rpk
            Airfare per revenue passenger kilometer (RPK) [€/RPK].
        airfare_per_rpk_short_range
            Airfare per revenue passenger kilometer (RPK) for short-range flights [€/RPK].
        airfare_per_rpk_medium_range
            Airfare per revenue passenger kilometer (RPK) for medium-range flights [€/RPK].
        airfare_per_rpk_long_range
            Airfare per revenue passenger kilometer (RPK) for long-range flights [€/RPK].

        """
        output_data = {}
        load_factor = input_data["load_factor"]

        airfare_per_ask = (
            input_data["total_cost_per_ask"] + input_data["operational_profit_per_ask"]
        )
        airfare_per_rpk = airfare_per_ask / (load_factor / 100)

        output_data["airfare_per_ask"] = airfare_per_ask
        output_data["airfare_per_rpk"] = airfare_per_rpk

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            airfare_per_ask_m = (
                input_data[f"total_cost_per_ask_{mid}"] + input_data["operational_profit_per_ask"]
            )
            airfare_per_rpk_m = airfare_per_ask_m / (load_factor / 100)
            output_data[f"airfare_per_ask_{mid}"] = airfare_per_ask_m
            output_data[f"airfare_per_rpk_{mid}"] = airfare_per_rpk_m

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftTotalCost(AeroMAPSModel):
    """
    Class to compute total cost for passenger aircraft by aggregating DOC, TOC, IOC, NOC...

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_total_cost' by default).
    """

    def __init__(self, name="passenger_aircraft_total_cost", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        self.input_names = {
            "doc_non_energy_per_ask_mean": pd.Series([0.0]),
            "doc_energy_per_ask_mean": pd.Series([0.0]),
            "doc_carbon_tax_lowering_offset_per_ask_mean": pd.Series([0.0]),
            "noc_carbon_offset_per_ask": pd.Series([0.0]),
            "non_operating_cost_per_ask": pd.Series([0.0]),
            "indirect_operating_cost_per_ask": pd.Series([0.0]),
            "passenger_tax_per_ask": pd.Series([0.0]),
            "operational_efficiency_cost_non_energy_per_ask": pd.Series([0.0]),
            "load_factor_cost_non_energy_per_ask": pd.Series([0.0]),
            "load_factor": pd.Series([0.0]),
        }
        self.output_names = {
            "total_cost_per_ask_without_extra_tax": pd.Series([0.0]),
            "total_extra_tax_per_ask": pd.Series([0.0]),
            "total_extra_tax_per_rpk": pd.Series([0.0]),
            "total_cost_per_ask": pd.Series([0.0]),
            "total_cost_per_rpk_without_extra_tax": pd.Series([0.0]),
            "total_cost_per_rpk": pd.Series([0.0]),
        }

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            self.input_names[f"doc_non_energy_per_ask_{mid}_mean"] = pd.Series([0.0])
            self.input_names[f"doc_energy_per_ask_{mid}_mean"] = pd.Series([0.0])
            self.input_names[f"doc_carbon_tax_lowering_offset_per_ask_{mid}_mean"] = pd.Series(
                [0.0]
            )

            self.output_names[f"total_cost_per_ask_without_extra_tax_{mid}"] = pd.Series([0.0])
            self.output_names[f"total_extra_tax_per_ask_{mid}"] = pd.Series([0.0])
            self.output_names[f"total_extra_tax_per_rpk_{mid}"] = pd.Series([0.0])
            self.output_names[f"total_cost_per_ask_{mid}"] = pd.Series([0.0])
            self.output_names[f"total_cost_per_rpk_without_extra_tax_{mid}"] = pd.Series([0.0])
            self.output_names[f"total_cost_per_rpk_{mid}"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        output_data = {}

        load_factor = input_data["load_factor"]

        total_cost_per_ask_without_extra_tax = (
            input_data["doc_non_energy_per_ask_mean"]
            + input_data["doc_energy_per_ask_mean"]
            + input_data["non_operating_cost_per_ask"]
            + input_data["indirect_operating_cost_per_ask"]
            + input_data["noc_carbon_offset_per_ask"]
            + input_data["operational_efficiency_cost_non_energy_per_ask"]
            + input_data["load_factor_cost_non_energy_per_ask"]
        )
        total_extra_tax_per_ask = (
            input_data["doc_carbon_tax_lowering_offset_per_ask_mean"]
            + input_data["passenger_tax_per_ask"]
        )
        total_cost_per_ask = total_cost_per_ask_without_extra_tax + total_extra_tax_per_ask

        total_cost_per_rpk_without_extra_tax = total_cost_per_ask_without_extra_tax / (
            load_factor / 100
        )
        total_extra_tax_per_rpk = total_extra_tax_per_ask / (load_factor / 100)
        total_cost_per_rpk = total_cost_per_rpk_without_extra_tax + total_extra_tax_per_rpk

        output_data["total_cost_per_ask_without_extra_tax"] = total_cost_per_ask_without_extra_tax
        output_data["total_extra_tax_per_ask"] = total_extra_tax_per_ask
        output_data["total_extra_tax_per_rpk"] = total_extra_tax_per_rpk
        output_data["total_cost_per_ask"] = total_cost_per_ask
        output_data["total_cost_per_rpk_without_extra_tax"] = total_cost_per_rpk_without_extra_tax
        output_data["total_cost_per_rpk"] = total_cost_per_rpk

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            total_cost_per_ask_without_extra_tax_m = (
                input_data[f"doc_non_energy_per_ask_{mid}_mean"]
                + input_data[f"doc_energy_per_ask_{mid}_mean"]
                + input_data["non_operating_cost_per_ask"]
                + input_data["indirect_operating_cost_per_ask"]
                + input_data["noc_carbon_offset_per_ask"]
                + input_data["operational_efficiency_cost_non_energy_per_ask"]
                + input_data["load_factor_cost_non_energy_per_ask"]
            )
            total_extra_tax_per_ask_m = (
                input_data[f"doc_carbon_tax_lowering_offset_per_ask_{mid}_mean"]
                + input_data["passenger_tax_per_ask"]
            )
            total_cost_per_ask_m = (
                total_cost_per_ask_without_extra_tax_m + total_extra_tax_per_ask_m
            )

            total_cost_per_rpk_without_extra_tax_m = total_cost_per_ask_without_extra_tax_m / (
                load_factor / 100
            )
            total_extra_tax_per_rpk_m = total_extra_tax_per_ask_m / (load_factor / 100)
            total_cost_per_rpk_m = (
                total_cost_per_rpk_without_extra_tax_m + total_extra_tax_per_rpk_m
            )

            output_data[f"total_cost_per_ask_without_extra_tax_{mid}"] = (
                total_cost_per_ask_without_extra_tax_m
            )
            output_data[f"total_extra_tax_per_ask_{mid}"] = total_extra_tax_per_ask_m
            output_data[f"total_extra_tax_per_rpk_{mid}"] = total_extra_tax_per_rpk_m
            output_data[f"total_cost_per_ask_{mid}"] = total_cost_per_ask_m
            output_data[f"total_cost_per_rpk_without_extra_tax_{mid}"] = (
                total_cost_per_rpk_without_extra_tax_m
            )
            output_data[f"total_cost_per_rpk_{mid}"] = total_cost_per_rpk_m

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftMarginalCost(AeroMAPSModel):
    """
    Class to compute marginal cost for passenger aircraft based on a linear marginal cost component and total cost.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_marginal_cost' by default).
    """

    def __init__(self, name="passenger_aircraft_marginal_cost", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        self.input_names = {
            "rpk": pd.Series([0.0]),
            "rpk_no_elasticity": pd.Series([0.0]),
            "total_cost_per_rpk_without_extra_tax": pd.Series([0.0]),
            "total_extra_tax_per_rpk": pd.Series([0.0]),
        }
        self.output_names = {
            "marginal_cost_per_rpk": pd.Series([0.0]),
            "airfare_per_rpk_true": pd.Series([0.0]),
            "airfare_per_rpk": pd.Series([0.0]),
        }

    def compute(self, input_data) -> dict:
        """
        Execute the computation of marginal cost and airfare.

        Parameters
        -------------
        rpk
            Revenue passenger kilometers (RPK) [RPK].
        rpk_no_elasticity
            Revenue passenger kilometers (RPK) without elasticity [RPK].
        total_cost_per_rpk_without_extra_tax
            Total cost per revenue passenger kilometer (RPK) without extra tax [€/RPK].
        total_extra_tax_per_rpk
            Total extra tax per revenue passenger kilometer (RPK) [€/RPK].

        Returns
        ---------
        marginal_cost_per_rpk
            Marginal cost per revenue passenger kilometer (RPK) [€/RPK].
        airfare_per_rpk_true
            True airfare per revenue passenger kilometer (RPK) [€/RPK]. TODO clarify its necessity. Remains of IDF MDO?
        airfare_per_rpk
            Airfare per revenue passenger kilometer (RPK) [€/RPK].


        """
        output_data = {}

        rpk = input_data["rpk"]
        rpk_no_elasticity = input_data["rpk_no_elasticity"]
        total_cost_per_rpk_without_extra_tax = input_data["total_cost_per_rpk_without_extra_tax"]
        total_extra_tax_per_rpk = input_data["total_extra_tax_per_rpk"]

        intial_total_cost_per_rpk_without_extra_tax = total_cost_per_rpk_without_extra_tax[
            self.prospection_start_year - 1
        ]

        # initial price => Same markup as iata stats, but using aeromaps cost (~ +0.01 €/RPK)
        initial_price_per_rpk_corrected = 0.09236379319842411

        # Were defining the inverse market-level suppy function ( cost =f (rpk) ) as a linear function by hypothesis
        # Calibration of this function is done base on average cost and prices for the last 20 years of IATA data (2020,2021,2022 excluded)
        # ==> TODO store notebook somewhere

        b = 2 * intial_total_cost_per_rpk_without_extra_tax - initial_price_per_rpk_corrected
        a = (
            2
            * (initial_price_per_rpk_corrected - intial_total_cost_per_rpk_without_extra_tax)
            / rpk_no_elasticity
        )

        # For latter update replace total cost by the step component of the marginal cost.
        marginal_cost_per_rpk = (
            a * rpk.loc[self.prospection_start_year : self.end_year]
            + b
            + total_cost_per_rpk_without_extra_tax.loc[self.prospection_start_year : self.end_year]
            - intial_total_cost_per_rpk_without_extra_tax
        )

        airfare_per_rpk_true = marginal_cost_per_rpk + total_extra_tax_per_rpk
        airfare_per_rpk_true = airfare_per_rpk_true
        airfare_per_rpk = airfare_per_rpk_true

        # ADD 2019 value to the airfare_per_rpk series
        airfare_per_rpk.loc[self.prospection_start_year - 1] = initial_price_per_rpk_corrected

        output_data["marginal_cost_per_rpk"] = marginal_cost_per_rpk
        output_data["airfare_per_rpk_true"] = airfare_per_rpk_true
        output_data["airfare_per_rpk"] = airfare_per_rpk

        self._store_outputs(output_data)
        return output_data

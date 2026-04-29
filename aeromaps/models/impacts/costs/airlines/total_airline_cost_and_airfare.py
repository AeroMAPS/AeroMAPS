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
from typing import Tuple

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

    Documentation
    --------------
    Inputs
        - total_cost_per_ask: Total cost per available seat kilometer (ASK) [EUR/ASK].
        - total_cost_per_ask_<market>: Total cost per ASK for a passenger market [EUR/ASK].
        - load_factor: Load factor [%].
        - load_factor_<market>: Load factor for a passenger market [%].
        - operational_profit_per_ask: Operational profit per ASK [EUR/ASK].
    Outputs
        - airfare_per_ask: Airfare per available seat kilometer (ASK) [EUR/ASK].
        - airfare_per_ask_<market>: Airfare per ASK for a passenger market [EUR/ASK].
        - airfare_per_rpk: Airfare per revenue passenger kilometer (RPK) [EUR/RPK].
        - airfare_per_rpk_<market>: Airfare per RPK for a passenger market [EUR/RPK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
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
            self.input_names[f"load_factor_{mid}"] = pd.Series([0.0])
            self.output_names[f"airfare_per_ask_{mid}"] = pd.Series([0.0])
            self.output_names[f"airfare_per_rpk_{mid}"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
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
            load_factor_m = input_data[f"load_factor_{mid}"]
            airfare_per_ask_m = (
                input_data[f"total_cost_per_ask_{mid}"] + input_data["operational_profit_per_ask"]
            )
            airfare_per_rpk_m = airfare_per_ask_m / (load_factor_m / 100)
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

    Documentation
    --------------
    Inputs
        - doc_non_energy_per_ask_mean: Mean DOC (non-energy) per ASK [EUR/ASK].
        - doc_non_energy_per_ask_<market>_mean: Mean DOC (non-energy) per ASK for a market [EUR/ASK].
        - doc_energy_per_ask_mean: Mean DOC (energy) per ASK [EUR/ASK].
        - doc_energy_per_ask_<market>_mean: Mean DOC (energy) per ASK for a market [EUR/ASK].
        - doc_carbon_tax_lowering_offset_per_ask_mean: Mean carbon tax lowering offset per ASK [EUR/ASK].
        - doc_carbon_tax_lowering_offset_per_ask_<market>_mean: Mean carbon tax lowering offset per ASK for a market [EUR/ASK].
        - noc_carbon_offset_per_ask: Non-operating cost carbon offset per ASK [EUR/ASK].
        - non_operating_cost_per_ask: Non-operating cost per ASK [EUR/ASK].
        - indirect_operating_cost_per_ask: Indirect operating cost per ASK [EUR/ASK].
        - passenger_tax_per_ask: Passenger tax per ASK [EUR/ASK].
        - operational_efficiency_cost_non_energy_per_ask: Operational efficiency cost (non-energy) per ASK [EUR/ASK].
        - load_factor_cost_non_energy_per_ask: Load factor cost (non-energy) per ASK [EUR/ASK].
        - load_factor: Load factor [%].
        - load_factor_<market>: Load factor for a passenger market [%].
    Outputs
        - total_cost_per_ask_without_extra_tax: Total cost per ASK excluding extra taxes [EUR/ASK].
        - total_cost_per_ask_without_extra_tax_<market>: Total cost per ASK excluding extra taxes for a market [EUR/ASK].
        - total_extra_tax_per_ask: Total extra tax per ASK [EUR/ASK].
        - total_extra_tax_per_ask_<market>: Total extra tax per ASK for a market [EUR/ASK].
        - total_extra_tax_per_rpk: Total extra tax per RPK [EUR/RPK].
        - total_extra_tax_per_rpk_<market>: Total extra tax per RPK for a market [EUR/RPK].
        - total_cost_per_ask: Total cost per ASK [EUR/ASK].
        - total_cost_per_ask_<market>: Total cost per ASK for a market [EUR/ASK].
        - total_cost_per_rpk_without_extra_tax: Total cost per RPK excluding extra taxes [EUR/RPK].
        - total_cost_per_rpk_without_extra_tax_<market>: Total cost per RPK excluding extra taxes for a market [EUR/RPK].
        - total_cost_per_rpk: Total cost per RPK [EUR/RPK].
        - total_cost_per_rpk_<market>: Total cost per RPK for a market [EUR/RPK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
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
            self.input_names[f"load_factor_{mid}"] = pd.Series([0.0])

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

            load_factor_m = input_data[f"load_factor_{mid}"]

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
                load_factor_m / 100
            )
            total_extra_tax_per_rpk_m = total_extra_tax_per_ask_m / (load_factor_m / 100)
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
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk: pd.Series,
        rpk_no_elasticity: pd.Series,
        total_cost_per_rpk_without_extra_tax: pd.Series,
        total_extra_tax_per_rpk: pd.Series,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        # np.ndarray,
    ]:
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

        self.df.loc[:, "marginal_cost_per_rpk"] = marginal_cost_per_rpk
        self.df.loc[:, "airfare_per_rpk"] = airfare_per_rpk

        return (
            marginal_cost_per_rpk,
            airfare_per_rpk_true,
            airfare_per_rpk,
        )

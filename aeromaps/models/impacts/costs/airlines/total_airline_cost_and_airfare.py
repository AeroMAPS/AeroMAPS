# @Time : 04/01/2024 15:41
# @Author : a.salgas
# @File : total_airline_cost_and_airfare.py
# @Software: PyCharm
"""
total_airline_cost_and_airfare

====================================================
Module grouping models to compute total airline costs and airfares for passenger aircraft.
"""

from typing import Tuple

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
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        total_cost_per_ask: pd.Series,
        total_cost_per_ask_short_range: pd.Series,
        total_cost_per_ask_medium_range: pd.Series,
        total_cost_per_ask_long_range: pd.Series,
        load_factor: pd.Series,
        operational_profit_per_ask: pd.Series,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
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
        # Airfare per ask
        airfare_per_ask = total_cost_per_ask + operational_profit_per_ask
        airfare_per_ask_short_range = total_cost_per_ask_short_range + operational_profit_per_ask
        airfare_per_ask_medium_range = total_cost_per_ask_medium_range + operational_profit_per_ask
        airfare_per_ask_long_range = total_cost_per_ask_long_range + operational_profit_per_ask

        # Airfare per rpk
        airfare_per_rpk = airfare_per_ask / (load_factor / 100)
        airfare_per_rpk_short_range = airfare_per_ask_short_range / (load_factor / 100)
        airfare_per_rpk_medium_range = airfare_per_ask_medium_range / (load_factor / 100)
        airfare_per_rpk_long_range = airfare_per_ask_long_range / (load_factor / 100)

        self.df.loc[:, "airfare_per_ask"] = airfare_per_ask
        self.df.loc[:, "airfare_per_ask_short_range"] = airfare_per_ask_short_range
        self.df.loc[:, "airfare_per_ask_medium_range"] = airfare_per_ask_medium_range
        self.df.loc[:, "airfare_per_ask_long_range"] = airfare_per_ask_long_range

        self.df.loc[:, "airfare_per_rpk"] = airfare_per_rpk
        self.df.loc[:, "airfare_per_rpk_short_range"] = airfare_per_rpk_short_range
        self.df.loc[:, "airfare_per_rpk_medium_range"] = airfare_per_rpk_medium_range
        self.df.loc[:, "airfare_per_rpk_long_range"] = airfare_per_rpk_long_range

        return (
            airfare_per_ask,
            airfare_per_ask_short_range,
            airfare_per_ask_medium_range,
            airfare_per_ask_long_range,
            airfare_per_rpk,
            airfare_per_rpk_short_range,
            airfare_per_rpk_medium_range,
            airfare_per_rpk_long_range,
        )


class PassengerAircraftTotalCost(AeroMAPSModel):
    """
    Class to compute total cost for passenger aircraft by aggregating DOC, TOC, IOC, NOC...

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_total_cost' by default).
    """

    def __init__(self, name="passenger_aircraft_total_cost", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        doc_non_energy_per_ask_mean: pd.Series,
        doc_non_energy_per_ask_short_range_mean: pd.Series,
        doc_non_energy_per_ask_medium_range_mean: pd.Series,
        doc_non_energy_per_ask_long_range_mean: pd.Series,
        doc_energy_per_ask_mean: pd.Series,
        doc_energy_per_ask_short_range_mean: pd.Series,
        doc_energy_per_ask_medium_range_mean: pd.Series,
        doc_energy_per_ask_long_range_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_short_range_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_medium_range_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_long_range_mean: pd.Series,
        noc_carbon_offset_per_ask: pd.Series,
        non_operating_cost_per_ask: pd.Series,
        indirect_operating_cost_per_ask: pd.Series,
        passenger_tax_per_ask: pd.Series,
        operational_efficiency_cost_non_energy_per_ask: pd.Series,
        load_factor_cost_non_energy_per_ask: pd.Series,
        load_factor: pd.Series,
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
    ]:
        """
        Execute the computation of total cost aggregation.
        Parameters
        ----------
        doc_non_energy_per_ask_mean
            Direct operating non-energy cost per available seat kilometer (ASK) [€/ASK].
        doc_non_energy_per_ask_short_range_mean
            Direct operating non-energy cost per available seat kilometer (ASK) for short-range flights [€/ASK].
        doc_non_energy_per_ask_medium_range_mean
            Direct operating non-energy cost per available seat kilometer (ASK) for medium-range flights [€/ASK].
        doc_non_energy_per_ask_long_range_mean
            Direct operating non-energy cost per available seat kilometer (ASK) for long-range flights [€/ASK].
        doc_energy_per_ask_mean
            Direct operating energy cost per available seat kilometer (ASK) [€/ASK].
        doc_energy_per_ask_short_range_mean
            Direct operating energy cost per available seat kilometer (ASK) for short-range flights [€/ASK].
        doc_energy_per_ask_medium_range_mean
            Direct operating energy cost per available seat kilometer (ASK) for medium-range flights [€/ASK].
        doc_energy_per_ask_long_range_mean
            Direct operating energy cost per available seat kilometer (ASK) for long-range flights [€/ASK].
        doc_carbon_tax_lowering_offset_per_ask_mean
            Direct operating carbon tax lowering offset per available seat kilometer (ASK) [€/ASK].
        doc_carbon_tax_lowering_offset_per_ask_short_range_mean
            Direct operating carbon tax lowering offset per available seat kilometer (ASK) for short-range flights [€/ASK].
        doc_carbon_tax_lowering_offset_per_ask_medium_range_mean
            Direct operating carbon tax lowering offset per available seat kilometer (ASK) for medium-range flights [€/ASK].
        doc_carbon_tax_lowering_offset_per_ask_long_range_mean
            Direct operating carbon tax lowering offset per available seat kilometer (ASK) for long-range flights [€/ASK].
        noc_carbon_offset_per_ask
            Non-operating carbon offset cost per available seat kilometer (ASK) [€/ASK].
        non_operating_cost_per_ask
            Non-operating cost per available seat kilometer (ASK) [€/ASK].
        indirect_operating_cost_per_ask
            Indirect operating cost per available seat kilometer (ASK) [€/ASK].
        passenger_tax_per_ask
            Passenger tax per available seat kilometer (ASK) [€/ASK].
        operational_efficiency_cost_non_energy_per_ask
            Operational efficiency non-energy cost per available seat kilometer (ASK) [€/ASK].
        load_factor_cost_non_energy_per_ask
            Load factor non-energy cost per available seat kilometer (ASK) [€/ASK].
        load_factor
            Load factor [%].

        Returns
        -------
        total_cost_per_ask_without_extra_tax
            Total cost per available seat kilometer (ASK) without extra tax [€/ASK].
        total_cost_per_ask_without_extra_tax_short_range
            Total cost per available seat kilometer (ASK) without extra tax for short-range flights [€/ASK].
        total_cost_per_ask_without_extra_tax_medium_range
            Total cost per available seat kilometer (ASK) without extra tax for medium-range flights [€/ASK].
        total_cost_per_ask_without_extra_tax_long_range
            Total cost per available seat kilometer (ASK) without extra tax for long-range flights [€/ASK].
        total_extra_tax_per_ask
            Total extra tax per available seat kilometer (ASK) [€/ASK].
        total_extra_tax_per_ask_short_range
            Total extra tax per available seat kilometer (ASK) for short-range flights [€/ASK].
        total_extra_tax_per_ask_medium_range
            Total extra tax per available seat kilometer (ASK) for medium-range flights [€/ASK].
        total_extra_tax_per_ask_long_range
            Total extra tax per available seat kilometer (ASK) for long-range flights [€/ASK].
        total_extra_tax_per_rpk
            Total extra tax per revenue passenger kilometer (RPK) [€/RPK].
        total_extra_tax_per_rpk_short_range
            Total extra tax per revenue passenger kilometer (RPK) for short-range flights [€/RPK].
        total_extra_tax_per_rpk_medium_range
            Total extra tax per revenue passenger kilometer (RPK) for medium-range flights [€/RPK].
        total_extra_tax_per_rpk_long_range
            Total extra tax per revenue passenger kilometer (RPK) for long-range flights [€/RPK].
        total_cost_per_ask
            Total cost per available seat kilometer (ASK) [€/ASK].
        total_cost_per_ask_short_range
            Total cost per available seat kilometer (ASK) for short-range flights [€/ASK].
        total_cost_per_ask_medium_range
            Total cost per available seat kilometer (ASK) for medium-range flights [€/ASK].
        total_cost_per_ask_long_range
            Total cost per available seat kilometer (ASK) for long-range flights [€/ASK].
        total_cost_per_rpk_without_extra_tax
            Total cost per revenue passenger kilometer (RPK) without extra tax [€/RPK].
        total_cost_per_rpk_without_extra_tax_short_range
            Total cost per revenue passenger kilometer (RPK) without extra tax for short-range flights [€/RPK].
        total_cost_per_rpk_without_extra_tax_medium_range
            Total cost per revenue passenger kilometer (RPK) without extra tax for medium-range flights [€/RPK].
        total_cost_per_rpk_without_extra_tax_long_range
            Total cost per revenue passenger kilometer (RPK) without extra tax for long-range flights [€/RPK].
        total_cost_per_rpk
            Total cost per revenue passenger kilometer (RPK) [€/RPK].
        total_cost_per_rpk_short_range
            Total cost per revenue passenger kilometer (RPK) for short-range flights [€/RPK].
        total_cost_per_rpk_medium_range
            Total cost per revenue passenger kilometer (RPK) for medium-range flights [€/RPK].
        total_cost_per_rpk_long_range
            Total cost per revenue passenger kilometer (RPK) for long-range flights [€/RPK].
        """
        ######## Overall #########

        # Cost without any tax

        total_cost_per_ask_without_extra_tax = (
            doc_non_energy_per_ask_mean
            + doc_energy_per_ask_mean
            + non_operating_cost_per_ask
            + indirect_operating_cost_per_ask
            + noc_carbon_offset_per_ask
            + operational_efficiency_cost_non_energy_per_ask
            + load_factor_cost_non_energy_per_ask
        )

        total_cost_per_ask_without_extra_tax_short_range = (
            doc_non_energy_per_ask_short_range_mean
            + doc_energy_per_ask_short_range_mean
            + non_operating_cost_per_ask
            + indirect_operating_cost_per_ask
            + noc_carbon_offset_per_ask
            + operational_efficiency_cost_non_energy_per_ask
            + load_factor_cost_non_energy_per_ask
        )

        total_cost_per_ask_without_extra_tax_medium_range = (
            doc_non_energy_per_ask_medium_range_mean
            + doc_energy_per_ask_medium_range_mean
            + non_operating_cost_per_ask
            + indirect_operating_cost_per_ask
            + noc_carbon_offset_per_ask
            + operational_efficiency_cost_non_energy_per_ask
            + load_factor_cost_non_energy_per_ask
        )

        total_cost_per_ask_without_extra_tax_long_range = (
            doc_non_energy_per_ask_long_range_mean
            + doc_energy_per_ask_long_range_mean
            + non_operating_cost_per_ask
            + indirect_operating_cost_per_ask
            + noc_carbon_offset_per_ask
            + operational_efficiency_cost_non_energy_per_ask
            + load_factor_cost_non_energy_per_ask
        )

        # Tax revenue
        total_extra_tax_per_ask = (
            doc_carbon_tax_lowering_offset_per_ask_mean + passenger_tax_per_ask
        )
        total_extra_tax_per_ask_short_range = (
            doc_carbon_tax_lowering_offset_per_ask_short_range_mean + passenger_tax_per_ask
        )
        total_extra_tax_per_ask_medium_range = (
            doc_carbon_tax_lowering_offset_per_ask_medium_range_mean + passenger_tax_per_ask
        )
        total_extra_tax_per_ask_long_range = (
            doc_carbon_tax_lowering_offset_per_ask_long_range_mean + passenger_tax_per_ask
        )

        # Average Cost per ask
        total_cost_per_ask = total_cost_per_ask_without_extra_tax + total_extra_tax_per_ask
        total_cost_per_ask_short_range = (
            total_cost_per_ask_without_extra_tax_short_range + total_extra_tax_per_ask_short_range
        )
        total_cost_per_ask_medium_range = (
            total_cost_per_ask_without_extra_tax_medium_range + total_extra_tax_per_ask_medium_range
        )
        total_cost_per_ask_long_range = (
            total_cost_per_ask_without_extra_tax_long_range + total_extra_tax_per_ask_long_range
        )

        # Cost per rpk
        total_cost_per_rpk_without_extra_tax = total_cost_per_ask_without_extra_tax / (
            load_factor / 100
        )
        total_cost_per_rpk_without_extra_tax_short_range = (
            total_cost_per_ask_without_extra_tax_short_range / (load_factor / 100)
        )
        total_cost_per_rpk_without_extra_tax_medium_range = (
            total_cost_per_ask_without_extra_tax_medium_range / (load_factor / 100)
        )
        total_cost_per_rpk_without_extra_tax_long_range = (
            total_cost_per_ask_without_extra_tax_long_range / (load_factor / 100)
        )

        # Tax per rpk
        total_extra_tax_per_rpk = total_extra_tax_per_ask / (load_factor / 100)
        total_extra_tax_per_rpk_short_range = total_extra_tax_per_ask_short_range / (
            load_factor / 100
        )
        total_extra_tax_per_rpk_medium_range = total_extra_tax_per_ask_medium_range / (
            load_factor / 100
        )
        total_extra_tax_per_rpk_long_range = total_extra_tax_per_ask_long_range / (
            load_factor / 100
        )

        # Average Cost per rpk
        total_cost_per_rpk = total_cost_per_rpk_without_extra_tax + total_extra_tax_per_rpk
        total_cost_per_rpk_short_range = (
            total_cost_per_rpk_without_extra_tax_short_range + total_extra_tax_per_rpk_short_range
        )
        total_cost_per_rpk_medium_range = (
            total_cost_per_rpk_without_extra_tax_medium_range + total_extra_tax_per_rpk_medium_range
        )
        total_cost_per_rpk_long_range = (
            total_cost_per_rpk_without_extra_tax_long_range + total_extra_tax_per_rpk_long_range
        )

        self.df.loc[:, "total_cost_per_ask_without_extra_tax"] = (
            total_cost_per_ask_without_extra_tax
        )
        self.df.loc[:, "total_cost_per_ask_without_extra_tax_short_range"] = (
            total_cost_per_ask_without_extra_tax_short_range
        )
        self.df.loc[:, "total_cost_per_ask_without_extra_tax_medium_range"] = (
            total_cost_per_ask_without_extra_tax_medium_range
        )
        self.df.loc[:, "total_cost_per_ask_without_extra_tax_long_range"] = (
            total_cost_per_ask_without_extra_tax_long_range
        )

        self.df.loc[:, "total_extra_tax_per_ask"] = total_extra_tax_per_ask
        self.df.loc[:, "total_extra_tax_per_ask_short_range"] = total_extra_tax_per_ask_short_range
        self.df.loc[:, "total_extra_tax_per_ask_medium_range"] = (
            total_extra_tax_per_ask_medium_range
        )
        self.df.loc[:, "total_extra_tax_per_ask_long_range"] = total_extra_tax_per_ask_long_range

        self.df.loc[:, "total_extra_tax_per_rpk"] = total_extra_tax_per_rpk
        self.df.loc[:, "total_extra_tax_per_rpk_short_range"] = total_extra_tax_per_rpk_short_range
        self.df.loc[:, "total_extra_tax_per_rpk_medium_range"] = (
            total_extra_tax_per_rpk_medium_range
        )
        self.df.loc[:, "total_extra_tax_per_rpk_long_range"] = total_extra_tax_per_rpk_long_range

        self.df.loc[:, "total_cost_per_ask"] = total_cost_per_ask
        self.df.loc[:, "total_cost_per_ask_short_range"] = total_cost_per_ask_short_range
        self.df.loc[:, "total_cost_per_ask_medium_range"] = total_cost_per_ask_medium_range
        self.df.loc[:, "total_cost_per_ask_long_range"] = total_cost_per_ask_long_range

        self.df.loc[:, "total_cost_per_rpk_without_extra_tax"] = (
            total_cost_per_rpk_without_extra_tax
        )
        self.df.loc[:, "total_cost_per_rpk_without_extra_tax_short_range"] = (
            total_cost_per_rpk_without_extra_tax_short_range
        )
        self.df.loc[:, "total_cost_per_rpk_without_extra_tax_medium_range"] = (
            total_cost_per_rpk_without_extra_tax_medium_range
        )
        self.df.loc[:, "total_cost_per_rpk_without_extra_tax_long_range"] = (
            total_cost_per_rpk_without_extra_tax_long_range
        )

        self.df.loc[:, "total_cost_per_rpk"] = total_cost_per_rpk
        self.df.loc[:, "total_cost_per_rpk_short_range"] = total_cost_per_rpk_short_range
        self.df.loc[:, "total_cost_per_rpk_medium_range"] = total_cost_per_rpk_medium_range
        self.df.loc[:, "total_cost_per_rpk_long_range"] = total_cost_per_rpk_long_range

        return (
            total_cost_per_ask_without_extra_tax,
            total_cost_per_ask_without_extra_tax_short_range,
            total_cost_per_ask_without_extra_tax_medium_range,
            total_cost_per_ask_without_extra_tax_long_range,
            total_extra_tax_per_ask,
            total_extra_tax_per_ask_short_range,
            total_extra_tax_per_ask_medium_range,
            total_extra_tax_per_ask_long_range,
            total_extra_tax_per_rpk,
            total_extra_tax_per_rpk_short_range,
            total_extra_tax_per_rpk_medium_range,
            total_extra_tax_per_rpk_long_range,
            total_cost_per_ask,
            total_cost_per_ask_short_range,
            total_cost_per_ask_medium_range,
            total_cost_per_ask_long_range,
            total_cost_per_rpk_without_extra_tax,
            total_cost_per_rpk_without_extra_tax_short_range,
            total_cost_per_rpk_without_extra_tax_medium_range,
            total_cost_per_rpk_without_extra_tax_long_range,
            total_cost_per_rpk,
            total_cost_per_rpk_short_range,
            total_cost_per_rpk_medium_range,
            total_cost_per_rpk_long_range,
        )


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

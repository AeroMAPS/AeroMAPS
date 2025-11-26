"""
direct_operating_costs
=======================

Direct Operating Costs (DOC) models for passenger aircraft.
"""

from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class PassengerAircraftDocNonEnergyComplex(AeroMAPSModel):
    """
    Non energy DOC per ASK calculation using generic fleet model

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_non_energy_complex' by default).

    Attributes
    ----------
    fleet_model : FleetModel(AeroMAPSModel)
        FleetModel instance to be used for complex efficiency computations.
    """

    def __init__(self, name="passenger_aircraft_doc_non_energy_complex", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = None

    def compute(
        self,
        ask_long_range_hydrogen_share: pd.Series,
        ask_long_range_dropin_fuel_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_medium_range_dropin_fuel_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_short_range_dropin_fuel_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_long_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_short_range: pd.Series,
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
    ]:
        """
        Parameters
        ----------
        ask_long_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from hydrogen aircraft [%].
        ask_long_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from drop-in fuel aircraft [%].
        ask_long_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from electric aircraft [%].
        ask_medium_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from hydrogen aircraft [%].
        ask_medium_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from drop-in fuel aircraft [%].
        ask_medium_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from electric aircraft [%].
        ask_short_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from hydrogen aircraft [%].
        ask_short_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from drop-in fuel aircraft [%].
        ask_short_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from electric aircraft [%].
        ask_long_range
            Number of Available Seat Kilometer (ASK) for passenger long-range market [ASK].
        ask_medium_range
            Number of Available Seat Kilometer (ASK) for passenger medium-range market [ASK].
        ask_short_range
            Number of Available Seat Kilometer (ASK) for passenger short-range market [ASK].

        Returns
        -------
        doc_non_energy_per_ask_short_range_dropin_fuel
            Direct operating cost attributable to non-energy expenses, for short range drop-in fleet [€/ASK].
        doc_non_energy_per_ask_medium_range_dropin_fuel
            Direct operating cost attributable to non-energy expenses, for medium range drop-in fleet [€/ASK].
        doc_non_energy_per_ask_long_range_dropin_fuel
            Direct operating cost attributable to non-energy expenses, for long range drop-in fleet [€/ASK].
        doc_non_energy_per_ask_short_range_hydrogen
            Direct operating cost attributable to non-energy expenses, for short range hydrogen fleet [€/ASK].
        doc_non_energy_per_ask_medium_range_hydrogen
            Direct operating cost attributable to non-energy expenses, for medium range hydrogen fleet [€/ASK].
        doc_non_energy_per_ask_long_range_hydrogen
            Direct operating cost attributable to non-energy expenses, for long range hydrogen fleet [€/ASK].
        doc_non_energy_per_ask_short_range_electric
            Direct operating cost attributable to non-energy expenses, for short range electric fleet [€/ASK].
        doc_non_energy_per_ask_medium_range_electric
            Direct operating cost attributable to non-energy expenses, for medium range electric fleet [€/ASK].
        doc_non_energy_per_ask_long_range_electric
            Direct operating cost attributable to non-energy expenses, for long range electric fleet [€/ASK].
        doc_non_energy_per_ask_short_range_mean
            Direct operating cost attributable to non-energy expenses, for short range fleet [€/ASK].
        doc_non_energy_per_ask_medium_range_mean
            Direct operating cost attributable to non-energy expenses, for medium range fleet [€/ASK].
        doc_non_energy_per_ask_long_range_mean
            Direct operating cost attributable to non-energy expenses, for long range fleet [€/ASK].
        doc_non_energy_per_ask_mean
            Direct operating cost attributable to non-energy expenses, for overall fleet [€/ASK].
        """
        doc_non_energy_per_ask_short_range_dropin_fuel = self.fleet_model.df[
            "Short Range:doc_non_energy:dropin_fuel"
        ]
        doc_non_energy_per_ask_medium_range_dropin_fuel = self.fleet_model.df[
            "Medium Range:doc_non_energy:dropin_fuel"
        ]
        doc_non_energy_per_ask_long_range_dropin_fuel = self.fleet_model.df[
            "Long Range:doc_non_energy:dropin_fuel"
        ]
        doc_non_energy_per_ask_short_range_hydrogen = self.fleet_model.df[
            "Short Range:doc_non_energy:hydrogen"
        ]
        doc_non_energy_per_ask_medium_range_hydrogen = self.fleet_model.df[
            "Medium Range:doc_non_energy:hydrogen"
        ]
        doc_non_energy_per_ask_long_range_hydrogen = self.fleet_model.df[
            "Long Range:doc_non_energy:hydrogen"
        ]
        doc_non_energy_per_ask_short_range_electric = self.fleet_model.df[
            "Short Range:doc_non_energy:electric"
        ]
        doc_non_energy_per_ask_medium_range_electric = self.fleet_model.df[
            "Medium Range:doc_non_energy:electric"
        ]
        doc_non_energy_per_ask_long_range_electric = self.fleet_model.df[
            "Long Range:doc_non_energy:electric"
        ]

        # Drop-in - Projections

        self.df.loc[:, "doc_non_energy_per_ask_short_range_dropin_fuel"] = (
            doc_non_energy_per_ask_short_range_dropin_fuel
        )
        self.df.loc[:, "doc_non_energy_per_ask_medium_range_dropin_fuel"] = (
            doc_non_energy_per_ask_medium_range_dropin_fuel
        )
        self.df.loc[:, "doc_non_energy_per_ask_long_range_dropin_fuel"] = (
            doc_non_energy_per_ask_long_range_dropin_fuel
        )

        # Hydrogen
        self.df.loc[:, "doc_non_energy_per_ask_short_range_hydrogen"] = (
            doc_non_energy_per_ask_short_range_hydrogen
        )
        self.df.loc[:, "doc_non_energy_per_ask_medium_range_hydrogen"] = (
            doc_non_energy_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "doc_non_energy_per_ask_long_range_hydrogen"] = (
            doc_non_energy_per_ask_long_range_hydrogen
        )

        # Electric
        self.df.loc[:, "doc_non_energy_per_ask_short_range_electric"] = (
            doc_non_energy_per_ask_short_range_electric
        )
        self.df.loc[:, "doc_non_energy_per_ask_medium_range_electric"] = (
            doc_non_energy_per_ask_medium_range_electric
        )
        self.df.loc[:, "doc_non_energy_per_ask_long_range_electric"] = (
            doc_non_energy_per_ask_long_range_electric
        )

        doc_non_energy_per_ask_long_range_mean = (
            doc_non_energy_per_ask_long_range_hydrogen * ask_long_range_hydrogen_share / 100
            + doc_non_energy_per_ask_long_range_dropin_fuel * ask_long_range_dropin_fuel_share / 100
            + doc_non_energy_per_ask_long_range_electric * ask_long_range_electric_share / 100
        )

        doc_non_energy_per_ask_medium_range_mean = (
            doc_non_energy_per_ask_medium_range_hydrogen * ask_medium_range_hydrogen_share / 100
            + doc_non_energy_per_ask_medium_range_dropin_fuel
            * ask_medium_range_dropin_fuel_share
            / 100
            + doc_non_energy_per_ask_medium_range_electric * ask_medium_range_electric_share / 100
        )

        doc_non_energy_per_ask_short_range_mean = (
            doc_non_energy_per_ask_short_range_hydrogen * ask_short_range_hydrogen_share / 100
            + doc_non_energy_per_ask_short_range_dropin_fuel
            * ask_short_range_dropin_fuel_share
            / 100
            + doc_non_energy_per_ask_short_range_electric * ask_short_range_electric_share / 100
        )

        doc_non_energy_per_ask_mean = (
            doc_non_energy_per_ask_long_range_mean * ask_long_range
            + doc_non_energy_per_ask_medium_range_mean * ask_medium_range
            + doc_non_energy_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        self.df.loc[:, "doc_non_energy_per_ask_long_range_mean"] = (
            doc_non_energy_per_ask_long_range_mean
        )

        self.df.loc[:, "doc_non_energy_per_ask_medium_range_mean"] = (
            doc_non_energy_per_ask_medium_range_mean
        )

        self.df.loc[:, "doc_non_energy_per_ask_short_range_mean"] = (
            doc_non_energy_per_ask_short_range_mean
        )

        self.df.loc[:, "doc_non_energy_per_ask_mean"] = doc_non_energy_per_ask_mean

        return (
            doc_non_energy_per_ask_short_range_dropin_fuel,
            doc_non_energy_per_ask_medium_range_dropin_fuel,
            doc_non_energy_per_ask_long_range_dropin_fuel,
            doc_non_energy_per_ask_short_range_hydrogen,
            doc_non_energy_per_ask_medium_range_hydrogen,
            doc_non_energy_per_ask_long_range_hydrogen,
            doc_non_energy_per_ask_short_range_electric,
            doc_non_energy_per_ask_medium_range_electric,
            doc_non_energy_per_ask_long_range_electric,
            doc_non_energy_per_ask_short_range_mean,
            doc_non_energy_per_ask_medium_range_mean,
            doc_non_energy_per_ask_long_range_mean,
            doc_non_energy_per_ask_mean,
        )


class PassengerAircraftDocNonEnergySimple(AeroMAPSModel):
    """
    Non energy DOC per ASK calculation using simple efficiency models

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_non_energy_simple' by default).
    """

    def __init__(self, name="passenger_aircraft_doc_non_energy_simple", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        doc_non_energy_per_ask_short_range_dropin_fuel_init: float,
        doc_non_energy_per_ask_medium_range_dropin_fuel_init: float,
        doc_non_energy_per_ask_long_range_dropin_fuel_init: float,
        doc_non_energy_per_ask_short_range_dropin_fuel_gain: float,
        doc_non_energy_per_ask_medium_range_dropin_fuel_gain: float,
        doc_non_energy_per_ask_long_range_dropin_fuel_gain: float,
        relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_short_range: float,
        relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_medium_range: float,
        relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_long_range: float,
        relative_doc_non_energy_per_ask_electric_wrt_dropin_short_range: float,
        relative_doc_non_energy_per_ask_electric_wrt_dropin_medium_range: float,
        relative_doc_non_energy_per_ask_electric_wrt_dropin_long_range: float,
        ask_long_range_hydrogen_share: pd.Series,
        ask_long_range_dropin_fuel_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_medium_range_dropin_fuel_share: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_short_range_dropin_fuel_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_long_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_short_range: pd.Series,
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
    ]:
        """
        DOC (without energy DOC) per ASK calculation using simple models.

        Parameters
        ----------
        doc_non_energy_per_ask_short_range_dropin_fuel_init
            Initial value for short range non-energy related direct operating cost [€/ASK].
        doc_non_energy_per_ask_medium_range_dropin_fuel_init
            Initial value for medium range non-energy related direct operating cost [€/ASK].
        doc_non_energy_per_ask_long_range_dropin_fuel_init
            Initial value for long range non-energy related direct operating cost [€/ASK].
        doc_non_energy_per_ask_short_range_dropin_fuel_gain
            Annual gain value for short-range non-energy related direct operating cost [%].
        doc_non_energy_per_ask_medium_range_dropin_fuel_gain
            Annual gain value for medium-range non-energy related direct operating cost [%].
        doc_non_energy_per_ask_long_range_dropin_fuel_gain
            Annual gain value for long-range non-energy related direct operating cost [%].
        relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_short_range
            Relative non-energy related direct operating cost for hydrogen short-range aircraft with respect to drop-in fuel aircraft [%].
        relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_medium_range
            Relative non-energy related direct operating cost for hydrogen medium-range aircraft with respect to drop-in fuel aircraft [%].
        relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_long_range
            Relative non-energy related direct operating cost for hydrogen long-range aircraft with respect to drop-in fuel aircraft [%].
        relative_doc_non_energy_per_ask_electric_wrt_dropin_short_range
            Relative non-energy related direct operating cost for electric short-range aircraft with respect to drop-in fuel aircraft [%].
        relative_doc_non_energy_per_ask_electric_wrt_dropin_medium_range
            Relative non-energy related direct operating cost for electric medium-range aircraft with respect to drop-in fuel aircraft [%].
        relative_doc_non_energy_per_ask_electric_wrt_dropin_long_range
            Relative non-energy related direct operating cost for electric long-range aircraft with respect to drop-in fuel aircraft [%].
        ask_long_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from hydrogen aircraft [%].
        ask_long_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from drop-in fuel aircraft [%].
        ask_medium_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from hydrogen aircraft [%].
        ask_medium_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from drop-in fuel aircraft [%].
        ask_short_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from hydrogen aircraft [%].
        ask_short_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from drop-in fuel aircraft [%].
        ask_long_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from electric aircraft [%].
        ask_medium_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from electric aircraft [%].
        ask_short_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from electric aircraft [%].
        ask_long_range
            Number of Available Seat Kilometer (ASK) for passenger long-range market [ASK].
        ask_medium_range
            Number of Available Seat Kilometer (ASK) for passenger medium-range market [ASK].
        ask_short_range
            Number of Available Seat Kilometer (ASK) for passenger short-range market [ASK].

        Returns
        -------
        doc_non_energy_per_ask_short_range_dropin_fuel
            Direct operating cost attributable to non-energy expenses, for short range drop-in fleet [€/ASK].
        doc_non_energy_per_ask_medium_range_dropin_fuel
            Direct operating cost attributable to non-energy expenses, for medium range drop-in fleet [€/ASK].
        doc_non_energy_per_ask_long_range_dropin_fuel
            Direct operating cost attributable to non-energy expenses, for long range drop-in fleet [€/ASK].
        doc_non_energy_per_ask_short_range_hydrogen
            Direct operating cost attributable to non-energy expenses, for short range hydrogen fleet [€/ASK].
        doc_non_energy_per_ask_medium_range_hydrogen
            Direct operating cost attributable to non-energy expenses, for medium range hydrogen fleet [€/ASK].
        doc_non_energy_per_ask_long_range_hydrogen
            Direct operating cost attributable to non-energy expenses, for long range hydrogen fleet [€/ASK].
        doc_non_energy_per_ask_short_range_electric
            Direct operating cost attributable to non-energy expenses, for short range electric fleet [€/ASK].
        doc_non_energy_per_ask_medium_range_electric
            Direct operating cost attributable to non-energy expenses, for medium range electric fleet [€/ASK].
        doc_non_energy_per_ask_long_range_electric
            Direct operating cost attributable to non-energy expenses, for long range electric fleet [€/ASK].
        doc_non_energy_per_ask_short_range_mean
            Direct operating cost attributable to non-energy expenses, for short range fleet [€/ASK].
        doc_non_energy_per_ask_medium_range_mean
            Direct operating cost attributable to non-energy expenses, for medium range fleet [€/ASK].
        doc_non_energy_per_ask_long_range_mean
            Direct operating cost attributable to non-energy expenses, for long range fleet [€/ASK].
        doc_non_energy_per_ask_mean
            Direct operating cost attributable to non-energy expenses, for overall fleet [€/ASK].
        """

        # Initialization based on 2019 values

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "doc_non_energy_per_ask_short_range_dropin_fuel"] = (
                doc_non_energy_per_ask_short_range_dropin_fuel_init
            )
            self.df.loc[k, "doc_non_energy_per_ask_medium_range_dropin_fuel"] = (
                doc_non_energy_per_ask_medium_range_dropin_fuel_init
            )
            self.df.loc[k, "doc_non_energy_per_ask_long_range_dropin_fuel"] = (
                doc_non_energy_per_ask_long_range_dropin_fuel_init
            )

        # Projections

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "doc_non_energy_per_ask_short_range_dropin_fuel"] = self.df.loc[
                k - 1, "doc_non_energy_per_ask_short_range_dropin_fuel"
            ] * (1 - doc_non_energy_per_ask_short_range_dropin_fuel_gain / 100)
            self.df.loc[k, "doc_non_energy_per_ask_medium_range_dropin_fuel"] = self.df.loc[
                k - 1, "doc_non_energy_per_ask_medium_range_dropin_fuel"
            ] * (1 - doc_non_energy_per_ask_medium_range_dropin_fuel_gain / 100)
            self.df.loc[k, "doc_non_energy_per_ask_long_range_dropin_fuel"] = self.df.loc[
                k - 1, "doc_non_energy_per_ask_long_range_dropin_fuel"
            ] * (1 - doc_non_energy_per_ask_long_range_dropin_fuel_gain / 100)

        doc_non_energy_per_ask_short_range_dropin_fuel = self.df[
            "doc_non_energy_per_ask_short_range_dropin_fuel"
        ]
        doc_non_energy_per_ask_medium_range_dropin_fuel = self.df[
            "doc_non_energy_per_ask_medium_range_dropin_fuel"
        ]
        doc_non_energy_per_ask_long_range_dropin_fuel = self.df[
            "doc_non_energy_per_ask_long_range_dropin_fuel"
        ]

        # Hydrogen

        doc_non_energy_per_ask_short_range_hydrogen = (
            doc_non_energy_per_ask_short_range_dropin_fuel
            * relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_short_range
        )
        doc_non_energy_per_ask_medium_range_hydrogen = (
            doc_non_energy_per_ask_medium_range_dropin_fuel
            * relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_medium_range
        )
        doc_non_energy_per_ask_long_range_hydrogen = (
            doc_non_energy_per_ask_long_range_dropin_fuel
            * relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_long_range
        )

        self.df.loc[:, "doc_non_energy_per_ask_short_range_hydrogen"] = (
            doc_non_energy_per_ask_short_range_hydrogen
        )
        self.df.loc[:, "doc_non_energy_per_ask_medium_range_hydrogen"] = (
            doc_non_energy_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "doc_non_energy_per_ask_long_range_hydrogen"] = (
            doc_non_energy_per_ask_long_range_hydrogen
        )

        # Electric
        doc_non_energy_per_ask_short_range_electric = (
            doc_non_energy_per_ask_short_range_dropin_fuel
            * relative_doc_non_energy_per_ask_electric_wrt_dropin_short_range
        )
        doc_non_energy_per_ask_medium_range_electric = (
            doc_non_energy_per_ask_medium_range_dropin_fuel
            * relative_doc_non_energy_per_ask_electric_wrt_dropin_medium_range
        )
        doc_non_energy_per_ask_long_range_electric = (
            doc_non_energy_per_ask_long_range_dropin_fuel
            * relative_doc_non_energy_per_ask_electric_wrt_dropin_long_range
        )

        self.df.loc[:, "doc_non_energy_per_ask_short_range_electric"] = (
            doc_non_energy_per_ask_short_range_electric
        )
        self.df.loc[:, "doc_non_energy_per_ask_medium_range_electric"] = (
            doc_non_energy_per_ask_medium_range_electric
        )
        self.df.loc[:, "doc_non_energy_per_ask_long_range_electric"] = (
            doc_non_energy_per_ask_long_range_electric
        )

        doc_non_energy_per_ask_long_range_mean = (
            doc_non_energy_per_ask_long_range_hydrogen * ask_long_range_hydrogen_share / 100
            + doc_non_energy_per_ask_long_range_dropin_fuel * ask_long_range_dropin_fuel_share / 100
            + doc_non_energy_per_ask_long_range_electric * ask_long_range_electric_share / 100
        )

        doc_non_energy_per_ask_medium_range_mean = (
            doc_non_energy_per_ask_medium_range_hydrogen * ask_medium_range_hydrogen_share / 100
            + doc_non_energy_per_ask_medium_range_dropin_fuel
            * ask_medium_range_dropin_fuel_share
            / 100
            + doc_non_energy_per_ask_medium_range_electric * ask_medium_range_electric_share / 100
        )

        doc_non_energy_per_ask_short_range_mean = (
            doc_non_energy_per_ask_short_range_hydrogen * ask_short_range_hydrogen_share / 100
            + doc_non_energy_per_ask_short_range_dropin_fuel
            * ask_short_range_dropin_fuel_share
            / 100
            + doc_non_energy_per_ask_short_range_electric * ask_short_range_electric_share / 100
        )

        doc_non_energy_per_ask_mean = (
            doc_non_energy_per_ask_long_range_mean * ask_long_range
            + doc_non_energy_per_ask_medium_range_mean * ask_medium_range
            + doc_non_energy_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        self.df.loc[:, "doc_non_energy_per_ask_long_range_mean"] = (
            doc_non_energy_per_ask_long_range_mean
        )

        self.df.loc[:, "doc_non_energy_per_ask_medium_range_mean"] = (
            doc_non_energy_per_ask_medium_range_mean
        )

        self.df.loc[:, "doc_non_energy_per_ask_short_range_mean"] = (
            doc_non_energy_per_ask_short_range_mean
        )

        self.df.loc[:, "doc_non_energy_per_ask_mean"] = doc_non_energy_per_ask_mean

        return (
            doc_non_energy_per_ask_short_range_dropin_fuel,
            doc_non_energy_per_ask_medium_range_dropin_fuel,
            doc_non_energy_per_ask_long_range_dropin_fuel,
            doc_non_energy_per_ask_short_range_hydrogen,
            doc_non_energy_per_ask_medium_range_hydrogen,
            doc_non_energy_per_ask_long_range_hydrogen,
            doc_non_energy_per_ask_short_range_electric,
            doc_non_energy_per_ask_medium_range_electric,
            doc_non_energy_per_ask_long_range_electric,
            doc_non_energy_per_ask_short_range_mean,
            doc_non_energy_per_ask_medium_range_mean,
            doc_non_energy_per_ask_long_range_mean,
            doc_non_energy_per_ask_mean,
        )


class PassengerAircraftDocEnergy(AeroMAPSModel):
    """
    Energy DOC per ASK calculation

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_energy' by default).
    """

    def __init__(self, name="passenger_aircraft_doc_energy", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_per_ask_long_range_dropin_fuel: pd.Series,
        energy_per_ask_long_range_hydrogen: pd.Series,
        energy_per_ask_medium_range_dropin_fuel: pd.Series,
        energy_per_ask_medium_range_hydrogen: pd.Series,
        energy_per_ask_short_range_dropin_fuel: pd.Series,
        energy_per_ask_short_range_hydrogen: pd.Series,
        energy_per_ask_long_range_electric: pd.Series,
        energy_per_ask_medium_range_electric: pd.Series,
        energy_per_ask_short_range_electric: pd.Series,
        dropin_fuel_mean_mfsp: pd.Series,
        hydrogen_mean_mfsp: pd.Series,
        electric_mean_mfsp: pd.Series,
        ask_long_range_hydrogen_share: pd.Series,
        ask_long_range_dropin_fuel_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_medium_range_dropin_fuel_share: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_short_range_dropin_fuel_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_long_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_short_range: pd.Series,
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
    ]:
        """
        DOC energy per ASK calculation.
        Parameters
        ----------
        energy_per_ask_long_range_dropin_fuel
            Energy consumption per ASK for passenger long-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_long_range_hydrogen
            Energy consumption per ASK for passenger long-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_medium_range_dropin_fuel
            Energy consumption per ASK for passenger medium-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_medium_range_hydrogen
            Energy consumption per ASK for passenger medium-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_short_range_dropin_fuel
            Energy consumption per ASK for passenger short-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_short_range_hydrogen
            Energy consumption per ASK for passenger short-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_long_range_electric
            Energy consumption per ASK for passenger long-range market aircraft using electricity [MJ/ASK].
        energy_per_ask_medium_range_electric
            Energy consumption per ASK for passenger medium-range market aircraft using electricity [MJ/ASK].
        energy_per_ask_short_range_electric
            Energy consumption per ASK for passenger short-range market aircraft using electricity [MJ/ASK].
        dropin_fuel_mean_mfsp
            Mean fuel selling price for drop-in fuels [€/MJ].
        hydrogen_mean_mfsp
            Mean fuel selling price for hydrogen [€/MJ].
        electric_mean_mfsp
            Mean fuel selling price for electricity [€/MJ].
        ask_long_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from hydrogen aircraft [%].
        ask_long_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from drop-in fuel aircraft [%].
        ask_medium_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from hydrogen aircraft [%].
        ask_medium_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from drop-in fuel aircraft [%].
        ask_short_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from hydrogen aircraft [%].
        ask_short_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from drop-in fuel aircraft [%].
        ask_long_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from electric aircraft [%].
        ask_medium_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from electric aircraft [%].
        ask_short_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from electric aircraft [%].
        ask_long_range
            Number of Available Seat Kilometer (ASK) for passenger long-range market [ASK].
        ask_medium_range
            Number of Available Seat Kilometer (ASK) for passenger medium-range market [ASK].
        ask_short_range
            Number of Available Seat Kilometer (ASK) for passenger short-range market [ASK].

        Returns
        -------
        doc_energy_per_ask_short_range_dropin_fuel
            Direct operating cost attributable to energy expenses, for short range drop-in fleet [€/ASK].
        doc_energy_per_ask_medium_range_dropin_fuel
            Direct operating cost attributable to energy expenses, for medium range drop-in fleet [€/ASK].
        doc_energy_per_ask_long_range_dropin_fuel
            Direct operating cost attributable to energy expenses, for long range drop-in fleet [€/ASK].
        doc_energy_per_ask_short_range_hydrogen
            Direct operating cost attributable to energy expenses, for short range hydrogen fleet [€/ASK].
        doc_energy_per_ask_medium_range_hydrogen
            Direct operating cost attributable to energy expenses, for medium range hydrogen fleet [€/ASK].
        doc_energy_per_ask_long_range_hydrogen
            Direct operating cost attributable to energy expenses, for long range hydrogen fleet [€/ASK].
        doc_energy_per_ask_short_range_electric
            Direct operating cost attributable to energy expenses, for short range electric fleet [€/ASK].
        doc_energy_per_ask_medium_range_electric
            Direct operating cost attributable to energy expenses, for medium range electric fleet [€/ASK].
        doc_energy_per_ask_long_range_electric
            Direct operating cost attributable to energy expenses, for long range electric fleet [€/ASK].
        doc_energy_per_ask_short_range_mean
            Direct operating cost attributable to energy expenses, for short range fleet [€/ASK].
        doc_energy_per_ask_medium_range_mean
            Direct operating cost attributable to energy expenses, for medium range fleet [€/ASK].
        doc_energy_per_ask_long_range_mean
            Direct operating cost attributable to energy expenses, for long range fleet [€/ASK].
        doc_energy_per_ask_mean
            Direct operating cost attributable to energy expenses, for overall fleet [€/ASK].
        """
        # Drop-in
        doc_energy_per_ask_long_range_dropin_fuel = (
            energy_per_ask_long_range_dropin_fuel.replace(0, np.NaN) * dropin_fuel_mean_mfsp
        )
        doc_energy_per_ask_medium_range_dropin_fuel = (
            energy_per_ask_medium_range_dropin_fuel.replace(0, np.NaN) * dropin_fuel_mean_mfsp
        )
        doc_energy_per_ask_short_range_dropin_fuel = (
            energy_per_ask_short_range_dropin_fuel.replace(0, np.NaN) * dropin_fuel_mean_mfsp
        )
        # Hydrogen
        doc_energy_per_ask_long_range_hydrogen = (
            energy_per_ask_long_range_hydrogen.replace(0, np.NaN) * hydrogen_mean_mfsp
        )
        doc_energy_per_ask_medium_range_hydrogen = (
            energy_per_ask_medium_range_hydrogen.replace(0, np.NaN) * hydrogen_mean_mfsp
        )
        doc_energy_per_ask_short_range_hydrogen = (
            energy_per_ask_short_range_hydrogen.replace(0, np.NaN) * hydrogen_mean_mfsp
        )
        # Electric
        doc_energy_per_ask_long_range_electric = (
            energy_per_ask_long_range_electric.replace(0, np.NaN) * electric_mean_mfsp
        )
        doc_energy_per_ask_medium_range_electric = (
            energy_per_ask_medium_range_electric.replace(0, np.NaN) * electric_mean_mfsp
        )
        doc_energy_per_ask_short_range_electric = (
            energy_per_ask_short_range_electric.replace(0, np.NaN) * electric_mean_mfsp
        )

        # Means
        doc_energy_per_ask_long_range_mean = (
            doc_energy_per_ask_long_range_hydrogen.fillna(0) * ask_long_range_hydrogen_share / 100
            + doc_energy_per_ask_long_range_dropin_fuel.fillna(0)
            * ask_long_range_dropin_fuel_share
            / 100
            + doc_energy_per_ask_long_range_electric.fillna(0) * ask_long_range_electric_share / 100
        )
        doc_energy_per_ask_medium_range_mean = (
            doc_energy_per_ask_medium_range_hydrogen.fillna(0)
            * ask_medium_range_hydrogen_share
            / 100
            + doc_energy_per_ask_medium_range_dropin_fuel.fillna(0)
            * ask_medium_range_dropin_fuel_share
            / 100
            + doc_energy_per_ask_medium_range_electric.fillna(0)
            * ask_medium_range_electric_share
            / 100
        )
        doc_energy_per_ask_short_range_mean = (
            doc_energy_per_ask_short_range_hydrogen.fillna(0) * ask_short_range_hydrogen_share / 100
            + doc_energy_per_ask_short_range_dropin_fuel.fillna(0)
            * ask_short_range_dropin_fuel_share
            / 100
            + doc_energy_per_ask_short_range_electric.fillna(0)
            * ask_short_range_electric_share
            / 100
        )
        doc_energy_per_ask_mean = (
            doc_energy_per_ask_long_range_mean * ask_long_range
            + doc_energy_per_ask_medium_range_mean * ask_medium_range
            + doc_energy_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        self.df.loc[:, "doc_energy_per_ask_long_range_dropin_fuel"] = (
            doc_energy_per_ask_long_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_per_ask_medium_range_dropin_fuel"] = (
            doc_energy_per_ask_medium_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_per_ask_short_range_dropin_fuel"] = (
            doc_energy_per_ask_short_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_per_ask_long_range_hydrogen"] = (
            doc_energy_per_ask_long_range_hydrogen
        )
        self.df.loc[:, "doc_energy_per_ask_medium_range_hydrogen"] = (
            doc_energy_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "doc_energy_per_ask_short_range_hydrogen"] = (
            doc_energy_per_ask_short_range_hydrogen
        )
        self.df.loc[:, "doc_energy_per_ask_long_range_electric"] = (
            doc_energy_per_ask_long_range_electric
        )
        self.df.loc[:, "doc_energy_per_ask_medium_range_electric"] = (
            doc_energy_per_ask_medium_range_electric
        )
        self.df.loc[:, "doc_energy_per_ask_short_range_electric"] = (
            doc_energy_per_ask_short_range_electric
        )
        self.df.loc[:, "doc_energy_per_ask_long_range_mean"] = doc_energy_per_ask_long_range_mean
        self.df.loc[:, "doc_energy_per_ask_medium_range_mean"] = (
            doc_energy_per_ask_medium_range_mean
        )
        self.df.loc[:, "doc_energy_per_ask_short_range_mean"] = doc_energy_per_ask_short_range_mean
        self.df.loc[:, "doc_energy_per_ask_mean"] = doc_energy_per_ask_mean

        return (
            doc_energy_per_ask_long_range_dropin_fuel,
            doc_energy_per_ask_medium_range_dropin_fuel,
            doc_energy_per_ask_short_range_dropin_fuel,
            doc_energy_per_ask_long_range_hydrogen,
            doc_energy_per_ask_medium_range_hydrogen,
            doc_energy_per_ask_short_range_hydrogen,
            doc_energy_per_ask_long_range_electric,
            doc_energy_per_ask_medium_range_electric,
            doc_energy_per_ask_short_range_electric,
            doc_energy_per_ask_long_range_mean,
            doc_energy_per_ask_medium_range_mean,
            doc_energy_per_ask_short_range_mean,
            doc_energy_per_ask_mean,
        )


class PassengerAircraftDocEnergyCarbonTax(AeroMAPSModel):
    """
    Carbon tax DOC per ASK calculation

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_energy_carbon_tax' by default
    """

    def __init__(self, name="passenger_aircraft_doc_energy_carbon_tax", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_per_ask_long_range_dropin_fuel: pd.Series,
        energy_per_ask_long_range_hydrogen: pd.Series,
        energy_per_ask_medium_range_dropin_fuel: pd.Series,
        energy_per_ask_medium_range_hydrogen: pd.Series,
        energy_per_ask_short_range_dropin_fuel: pd.Series,
        energy_per_ask_short_range_hydrogen: pd.Series,
        energy_per_ask_long_range_electric: pd.Series,
        energy_per_ask_medium_range_electric: pd.Series,
        energy_per_ask_short_range_electric: pd.Series,
        dropin_fuel_mean_unit_carbon_tax: pd.Series,
        hydrogen_mean_unit_carbon_tax: pd.Series,
        electric_mean_unit_carbon_tax: pd.Series,
        ask_long_range_hydrogen_share: pd.Series,
        ask_long_range_dropin_fuel_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_medium_range_dropin_fuel_share: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_short_range_dropin_fuel_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_long_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_short_range: pd.Series,
        co2_emissions: pd.Series,
        carbon_offset: pd.Series,
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
    ]:
        """
        Execution of the carbon tax DOC per ASK calculation.

        Parameters
        ----------
        energy_per_ask_long_range_dropin_fuel
            Energy consumption per ASK for passenger long-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_long_range_hydrogen
            Energy consumption per ASK for passenger long-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_medium_range_dropin_fuel
            Energy consumption per ASK for passenger medium-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_medium_range_hydrogen
            Energy consumption per ASK for passenger medium-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_short_range_dropin_fuel
            Energy consumption per ASK for passenger short-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_short_range_hydrogen
            Energy consumption per ASK for passenger short-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_long_range_electric
            Energy consumption per ASK for passenger long-range market aircraft using electricity [MJ/ASK].
        energy_per_ask_medium_range_electric
            Energy consumption per ASK for passenger medium-range market aircraft using electricity [MJ/ASK].
        energy_per_ask_short_range_electric
            Energy consumption per ASK for passenger short-range market aircraft using electricity [MJ/ASK].
        dropin_fuel_mean_unit_carbon_tax
            Mean unit carbon tax for drop-in fuels [€/MJ].
        hydrogen_mean_unit_carbon_tax
            Mean unit carbon tax for hydrogen [€/MJ].
        electric_mean_unit_carbon_tax
            Mean unit carbon tax for electricity [€/MJ].
        ask_long_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from hydrogen aircraft [%].
        ask_long_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from drop-in fuel aircraft [%].
        ask_medium_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from hydrogen aircraft [%].
        ask_medium_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from drop-in fuel aircraft [%].
        ask_short_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from hydrogen aircraft [%].
        ask_short_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from drop-in fuel aircraft [%].
        ask_long_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from electric aircraft [%].
        ask_medium_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from electric aircraft [%].
        ask_short_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from electric aircraft [%].
        ask_long_range
            Number of Available Seat Kilometer (ASK) for passenger long-range market [ASK].
        ask_medium_range
            Number of Available Seat Kilometer (ASK) for passenger medium-range market [ASK].
        ask_short_range
            Number of Available Seat Kilometer (ASK) for passenger short-range market [ASK].
        co2_emissions
            CO2 emissions from the commercial passenger aircraft sector [tonnes CO2].
        carbon_offset
            Carbon offset from the commercial passenger aircraft sector [tonnes CO2].

        Returns
        -------
        doc_energy_carbon_tax_per_ask_short_range_dropin_fuel
            Direct operating cost attributable to energy carbon tax, for short range drop-in fleet [€/ASK].
        doc_energy_carbon_tax_per_ask_medium_range_dropin_fuel
            Direct operating cost attributable to energy carbon tax, for medium range drop-in fleet [€/ASK].
        doc_energy_carbon_tax_per_ask_long_range_dropin_fuel
            Direct operating cost attributable to energy carbon tax, for long range drop-in fleet [€/ASK].
        doc_energy_carbon_tax_per_ask_short_range_hydrogen
            Direct operating cost attributable to energy carbon tax, for short range hydrogen fleet [€/ASK].
        doc_energy_carbon_tax_per_ask_medium_range_hydrogen
            Direct operating cost attributable to energy carbon tax, for medium range hydrogen fleet [€/ASK].
        doc_energy_carbon_tax_per_ask_long_range_hydrogen
            Direct operating cost attributable to energy carbon tax, for long range hydrogen fleet [€/ASK].
        doc_energy_carbon_tax_per_ask_short_range_electric
            Direct operating cost attributable to energy carbon tax, for short range electric fleet [€/ASK].
        doc_energy_carbon_tax_per_ask_medium_range_electric
            Direct operating cost attributable to energy carbon tax, for medium range electric fleet [€/ASK].
        doc_energy_carbon_tax_per_ask_long_range_electric
            Direct operating cost attributable to energy carbon tax, for long range electric fleet [€/ASK].
        doc_energy_carbon_tax_per_ask_short_range_mean
            Direct operating cost attributable to energy carbon tax, for short range fleet [€/ASK].
        doc_energy_carbon_tax_per_ask_medium_range_mean
            Direct operating cost attributable to energy carbon tax, for medium range fleet [€/ASK].
        doc_energy_carbon_tax_per_ask_long_range_mean
            Direct operating cost attributable to energy carbon tax, for long range fleet [€/ASK].
        doc_energy_carbon_tax_per_ask_mean
            Direct operating cost attributable to energy carbon tax, for overall fleet [€/ASK].
        doc_carbon_tax_lowering_offset_per_ask_mean
            Direct operating cost reduction attributable to carbon offset, for overall fleet [€/ASK].
        doc_carbon_tax_lowering_offset_per_ask_short_range_mean
            Direct operating cost reduction attributable to carbon offset, for short range fleet [€/ASK].
        doc_carbon_tax_lowering_offset_per_ask_medium_range_mean
            Direct operating cost reduction attributable to carbon offset, for medium range fleet [€/ASK].
        doc_carbon_tax_lowering_offset_per_ask_long_range_mean
            Direct operating cost reduction attributable to carbon offset, for long range fleet [€/ASK].
        """
        # Drop-in
        doc_energy_carbon_tax_per_ask_long_range_dropin_fuel = (
            energy_per_ask_long_range_dropin_fuel.replace(0, np.NaN)
            * dropin_fuel_mean_unit_carbon_tax
        )
        doc_energy_carbon_tax_per_ask_medium_range_dropin_fuel = (
            energy_per_ask_medium_range_dropin_fuel.replace(0, np.NaN)
            * dropin_fuel_mean_unit_carbon_tax
        )
        doc_energy_carbon_tax_per_ask_short_range_dropin_fuel = (
            energy_per_ask_short_range_dropin_fuel.replace(0, np.NaN)
            * dropin_fuel_mean_unit_carbon_tax
        )
        # Hydrogen
        doc_energy_carbon_tax_per_ask_long_range_hydrogen = (
            energy_per_ask_long_range_hydrogen.replace(0, np.NaN) * hydrogen_mean_unit_carbon_tax
        )
        doc_energy_carbon_tax_per_ask_medium_range_hydrogen = (
            energy_per_ask_medium_range_hydrogen.replace(0, np.NaN) * hydrogen_mean_unit_carbon_tax
        )
        doc_energy_carbon_tax_per_ask_short_range_hydrogen = (
            energy_per_ask_short_range_hydrogen.replace(0, np.NaN) * hydrogen_mean_unit_carbon_tax
        )
        # Electric
        doc_energy_carbon_tax_per_ask_long_range_electric = (
            energy_per_ask_long_range_electric.replace(0, np.NaN) * electric_mean_unit_carbon_tax
        )
        doc_energy_carbon_tax_per_ask_medium_range_electric = (
            energy_per_ask_medium_range_electric.replace(0, np.NaN) * electric_mean_unit_carbon_tax
        )
        doc_energy_carbon_tax_per_ask_short_range_electric = (
            energy_per_ask_short_range_electric.replace(0, np.NaN) * electric_mean_unit_carbon_tax
        )

        # Means
        doc_energy_carbon_tax_per_ask_long_range_mean = (
            doc_energy_carbon_tax_per_ask_long_range_hydrogen.fillna(0)
            * ask_long_range_hydrogen_share
            / 100
            + doc_energy_carbon_tax_per_ask_long_range_dropin_fuel.fillna(0)
            * ask_long_range_dropin_fuel_share
            / 100
            + doc_energy_carbon_tax_per_ask_long_range_electric.fillna(0)
            * ask_long_range_electric_share
            / 100
        )
        doc_energy_carbon_tax_per_ask_medium_range_mean = (
            doc_energy_carbon_tax_per_ask_medium_range_hydrogen.fillna(0)
            * ask_medium_range_hydrogen_share
            / 100
            + doc_energy_carbon_tax_per_ask_medium_range_dropin_fuel.fillna(0)
            * ask_medium_range_dropin_fuel_share
            / 100
            + doc_energy_carbon_tax_per_ask_medium_range_electric.fillna(0)
            * ask_medium_range_electric_share
            / 100
        )
        doc_energy_carbon_tax_per_ask_short_range_mean = (
            doc_energy_carbon_tax_per_ask_short_range_hydrogen.fillna(0)
            * ask_short_range_hydrogen_share
            / 100
            + doc_energy_carbon_tax_per_ask_short_range_dropin_fuel.fillna(0)
            * ask_short_range_dropin_fuel_share
            / 100
            + doc_energy_carbon_tax_per_ask_short_range_electric.fillna(0)
            * ask_short_range_electric_share
            / 100
        )
        doc_energy_carbon_tax_per_ask_mean = (
            doc_energy_carbon_tax_per_ask_long_range_mean * ask_long_range
            + doc_energy_carbon_tax_per_ask_medium_range_mean * ask_medium_range
            + doc_energy_carbon_tax_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        carbon_remaining_ratio = (
            co2_emissions.loc[self.historic_start_year : self.end_year] - carbon_offset.fillna(0)
        ) / co2_emissions.loc[self.historic_start_year : self.end_year]

        doc_carbon_tax_lowering_offset_per_ask_mean = (
            doc_energy_carbon_tax_per_ask_mean * carbon_remaining_ratio
        )

        doc_carbon_tax_lowering_offset_per_ask_short_range_mean = (
            doc_energy_carbon_tax_per_ask_short_range_mean * carbon_remaining_ratio
        )

        doc_carbon_tax_lowering_offset_per_ask_medium_range_mean = (
            doc_energy_carbon_tax_per_ask_medium_range_mean * carbon_remaining_ratio
        )

        doc_carbon_tax_lowering_offset_per_ask_long_range_mean = (
            doc_energy_carbon_tax_per_ask_long_range_mean * carbon_remaining_ratio
        )

        # Stockage dans le DataFrame
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_long_range_dropin_fuel"] = (
            doc_energy_carbon_tax_per_ask_long_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_medium_range_dropin_fuel"] = (
            doc_energy_carbon_tax_per_ask_medium_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_short_range_dropin_fuel"] = (
            doc_energy_carbon_tax_per_ask_short_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_long_range_hydrogen"] = (
            doc_energy_carbon_tax_per_ask_long_range_hydrogen
        )
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_medium_range_hydrogen"] = (
            doc_energy_carbon_tax_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_short_range_hydrogen"] = (
            doc_energy_carbon_tax_per_ask_short_range_hydrogen
        )
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_long_range_electric"] = (
            doc_energy_carbon_tax_per_ask_long_range_electric
        )
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_medium_range_electric"] = (
            doc_energy_carbon_tax_per_ask_medium_range_electric
        )
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_short_range_electric"] = (
            doc_energy_carbon_tax_per_ask_short_range_electric
        )
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_long_range_mean"] = (
            doc_energy_carbon_tax_per_ask_long_range_mean
        )
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_medium_range_mean"] = (
            doc_energy_carbon_tax_per_ask_medium_range_mean
        )
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_short_range_mean"] = (
            doc_energy_carbon_tax_per_ask_short_range_mean
        )
        self.df.loc[:, "doc_energy_carbon_tax_per_ask_mean"] = doc_energy_carbon_tax_per_ask_mean
        self.df.loc[:, "doc_carbon_tax_lowering_offset_per_ask_mean"] = (
            doc_carbon_tax_lowering_offset_per_ask_mean
        )

        self.df.loc[:, "doc_carbon_tax_lowering_offset_per_ask_short_range_mean"] = (
            doc_carbon_tax_lowering_offset_per_ask_medium_range_mean
        )
        self.df.loc[:, "doc_carbon_tax_lowering_offset_per_ask_medium_range_mean"] = (
            doc_carbon_tax_lowering_offset_per_ask_medium_range_mean
        )
        self.df.loc[:, "doc_carbon_tax_lowering_offset_per_ask_long_range_mean"] = (
            doc_carbon_tax_lowering_offset_per_ask_long_range_mean
        )

        return (
            doc_energy_carbon_tax_per_ask_long_range_dropin_fuel,
            doc_energy_carbon_tax_per_ask_medium_range_dropin_fuel,
            doc_energy_carbon_tax_per_ask_short_range_dropin_fuel,
            doc_energy_carbon_tax_per_ask_long_range_hydrogen,
            doc_energy_carbon_tax_per_ask_medium_range_hydrogen,
            doc_energy_carbon_tax_per_ask_short_range_hydrogen,
            doc_energy_carbon_tax_per_ask_long_range_electric,
            doc_energy_carbon_tax_per_ask_medium_range_electric,
            doc_energy_carbon_tax_per_ask_short_range_electric,
            doc_energy_carbon_tax_per_ask_long_range_mean,
            doc_energy_carbon_tax_per_ask_medium_range_mean,
            doc_energy_carbon_tax_per_ask_short_range_mean,
            doc_energy_carbon_tax_per_ask_mean,
            doc_carbon_tax_lowering_offset_per_ask_mean,
            doc_carbon_tax_lowering_offset_per_ask_short_range_mean,
            doc_carbon_tax_lowering_offset_per_ask_medium_range_mean,
            doc_carbon_tax_lowering_offset_per_ask_long_range_mean,
        )


class PassengerAircraftDocEnergySubsidy(AeroMAPSModel):
    """
    Energy subsidy DOC per ASK calculation

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_energy_subsidy' by default
    """

    def __init__(self, name="passenger_aircraft_doc_energy_subsidy", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_per_ask_long_range_dropin_fuel: pd.Series,
        energy_per_ask_long_range_hydrogen: pd.Series,
        energy_per_ask_medium_range_dropin_fuel: pd.Series,
        energy_per_ask_medium_range_hydrogen: pd.Series,
        energy_per_ask_short_range_dropin_fuel: pd.Series,
        energy_per_ask_short_range_hydrogen: pd.Series,
        energy_per_ask_long_range_electric: pd.Series,
        energy_per_ask_medium_range_electric: pd.Series,
        energy_per_ask_short_range_electric: pd.Series,
        dropin_fuel_mean_unit_subsidy: pd.Series,
        hydrogen_mean_unit_subsidy: pd.Series,
        electric_mean_unit_subsidy: pd.Series,
        ask_long_range_hydrogen_share: pd.Series,
        ask_long_range_dropin_fuel_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_medium_range_dropin_fuel_share: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_short_range_dropin_fuel_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_long_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_short_range: pd.Series,
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
    ]:
        """
        Execution of the energy subsidy DOC per ASK calculation.
        Parameters
        ----------
        energy_per_ask_long_range_dropin_fuel
            Energy consumption per ASK for passenger long-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_long_range_hydrogen
            Energy consumption per ASK for passenger long-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_medium_range_dropin_fuel
            Energy consumption per ASK for passenger medium-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_medium_range_hydrogen
            Energy consumption per ASK for passenger medium-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_short_range_dropin_fuel
            Energy consumption per ASK for passenger short-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_short_range_hydrogen
            Energy consumption per ASK for passenger short-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_long_range_electric
            Energy consumption per ASK for passenger long-range market aircraft using electricity [MJ/ASK].
        energy_per_ask_medium_range_electric
            Energy consumption per ASK for passenger medium-range market aircraft using electricity [MJ/ASK].
        energy_per_ask_short_range_electric
            Energy consumption per ASK for passenger short-range market aircraft using electricity [MJ/ASK].
        dropin_fuel_mean_unit_subsidy
            Mean unit subsidy for drop-in fuels [€/MJ].
        hydrogen_mean_unit_subsidy
            Mean unit subsidy for hydrogen [€/MJ].
        electric_mean_unit_subsidy
            Mean unit subsidy for electricity [€/MJ].
        ask_long_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from hydrogen aircraft [%].
        ask_long_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from drop-in fuel aircraft [%].
        ask_medium_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from hydrogen aircraft [%].
        ask_medium_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from drop-in fuel aircraft [%].
        ask_short_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from hydrogen aircraft [%].
        ask_short_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from drop-in fuel aircraft [%].
        ask_long_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from electric aircraft [%].
        ask_medium_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from electric aircraft [%].
        ask_short_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from electric aircraft [%].
        ask_long_range
            Number of Available Seat Kilometer (ASK) for passenger long-range market [ASK].
        ask_medium_range
            Number of Available Seat Kilometer (ASK) for passenger medium-range market [ASK].
        ask_short_range
            Number of Available Seat Kilometer (ASK) for passenger short-range market [ASK].

        Returns
        -------
        doc_energy_subsidy_per_ask_short_range_dropin_fuel
            Direct operating cost savings attributable to energy subsidy, for short range drop-in fleet [€/ASK].
        doc_energy_subsidy_per_ask_medium_range_dropin_fuel
            Direct operating cost savings attributable to energy subsidy, for medium range drop-in fleet [€/ASK].
        doc_energy_subsidy_per_ask_long_range_dropin_fuel
            Direct operating cost savings attributable to energy subsidy, for long range drop-in fleet [€/ASK].
        doc_energy_subsidy_per_ask_short_range_hydrogen
            Direct operating cost savings attributable to energy subsidy, for short range hydrogen fleet [€/ASK].
        doc_energy_subsidy_per_ask_medium_range_hydrogen
            Direct operating cost savings attributable to energy subsidy, for medium range hydrogen fleet [€/ASK].
        doc_energy_subsidy_per_ask_long_range_hydrogen
            Direct operating cost savings attributable to energy subsidy, for long range hydrogen fleet [€/ASK].
        doc_energy_subsidy_per_ask_short_range_electric
            Direct operating cost savings attributable to energy subsidy, for short range electric fleet [€/ASK].
        doc_energy_subsidy_per_ask_medium_range_electric
            Direct operating cost savings attributable to energy subsidy, for medium range electric fleet [€/ASK].
        doc_energy_subsidy_per_ask_long_range_electric
            Direct operating cost savings attributable to energy subsidy, for long range electric fleet [€/ASK].
        doc_energy_subsidy_per_ask_short_range_mean
            Direct operating cost savings attributable to energy subsidy, for short range fleet [€/ASK].
        doc_energy_subsidy_per_ask_medium_range_mean
            Direct operating cost savings attributable to energy subsidy, for medium range fleet [€/ASK].
        doc_energy_subsidy_per_ask_long_range_mean
            Direct operating cost savings attributable to energy subsidy, for long range fleet [€/ASK].
        doc_energy_subsidy_per_ask_mean
            Direct operating cost savings attributable to energy subsidy, for overall fleet [€/ASK].

        """
        # Drop-in
        doc_energy_subsidy_per_ask_long_range_dropin_fuel = (
            energy_per_ask_long_range_dropin_fuel * dropin_fuel_mean_unit_subsidy
        )
        doc_energy_subsidy_per_ask_medium_range_dropin_fuel = (
            energy_per_ask_medium_range_dropin_fuel * dropin_fuel_mean_unit_subsidy
        )
        doc_energy_subsidy_per_ask_short_range_dropin_fuel = (
            energy_per_ask_short_range_dropin_fuel * dropin_fuel_mean_unit_subsidy
        )
        # Hydrogen
        doc_energy_subsidy_per_ask_long_range_hydrogen = (
            energy_per_ask_long_range_hydrogen * hydrogen_mean_unit_subsidy
        )
        doc_energy_subsidy_per_ask_medium_range_hydrogen = (
            energy_per_ask_medium_range_hydrogen * hydrogen_mean_unit_subsidy
        )
        doc_energy_subsidy_per_ask_short_range_hydrogen = (
            energy_per_ask_short_range_hydrogen * hydrogen_mean_unit_subsidy
        )
        # Electric
        doc_energy_subsidy_per_ask_long_range_electric = (
            energy_per_ask_long_range_electric * electric_mean_unit_subsidy
        )
        doc_energy_subsidy_per_ask_medium_range_electric = (
            energy_per_ask_medium_range_electric * electric_mean_unit_subsidy
        )
        doc_energy_subsidy_per_ask_short_range_electric = (
            energy_per_ask_short_range_electric * electric_mean_unit_subsidy
        )

        # Moyennes pondérées
        doc_energy_subsidy_per_ask_long_range_mean = (
            doc_energy_subsidy_per_ask_long_range_hydrogen.fillna(0)
            * ask_long_range_hydrogen_share
            / 100
            + doc_energy_subsidy_per_ask_long_range_dropin_fuel.fillna(0)
            * ask_long_range_dropin_fuel_share
            / 100
            + doc_energy_subsidy_per_ask_long_range_electric.fillna(0)
            * ask_long_range_electric_share
            / 100
        )
        doc_energy_subsidy_per_ask_medium_range_mean = (
            doc_energy_subsidy_per_ask_medium_range_hydrogen.fillna(0)
            * ask_medium_range_hydrogen_share
            / 100
            + doc_energy_subsidy_per_ask_medium_range_dropin_fuel.fillna(0)
            * ask_medium_range_dropin_fuel_share
            / 100
            + doc_energy_subsidy_per_ask_medium_range_electric.fillna(0)
            * ask_medium_range_electric_share
            / 100
        )
        doc_energy_subsidy_per_ask_short_range_mean = (
            doc_energy_subsidy_per_ask_short_range_hydrogen.fillna(0)
            * ask_short_range_hydrogen_share
            / 100
            + doc_energy_subsidy_per_ask_short_range_dropin_fuel.fillna(0)
            * ask_short_range_dropin_fuel_share
            / 100
            + doc_energy_subsidy_per_ask_short_range_electric.fillna(0)
            * ask_short_range_electric_share
            / 100
        )
        doc_energy_subsidy_per_ask_mean = (
            doc_energy_subsidy_per_ask_long_range_mean * ask_long_range
            + doc_energy_subsidy_per_ask_medium_range_mean * ask_medium_range
            + doc_energy_subsidy_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        # Stockage dans le DataFrame
        self.df.loc[:, "doc_energy_subsidy_per_ask_long_range_dropin_fuel"] = (
            doc_energy_subsidy_per_ask_long_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_subsidy_per_ask_medium_range_dropin_fuel"] = (
            doc_energy_subsidy_per_ask_medium_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_subsidy_per_ask_short_range_dropin_fuel"] = (
            doc_energy_subsidy_per_ask_short_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_subsidy_per_ask_long_range_hydrogen"] = (
            doc_energy_subsidy_per_ask_long_range_hydrogen
        )
        self.df.loc[:, "doc_energy_subsidy_per_ask_medium_range_hydrogen"] = (
            doc_energy_subsidy_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "doc_energy_subsidy_per_ask_short_range_hydrogen"] = (
            doc_energy_subsidy_per_ask_short_range_hydrogen
        )
        self.df.loc[:, "doc_energy_subsidy_per_ask_long_range_electric"] = (
            doc_energy_subsidy_per_ask_long_range_electric
        )
        self.df.loc[:, "doc_energy_subsidy_per_ask_medium_range_electric"] = (
            doc_energy_subsidy_per_ask_medium_range_electric
        )
        self.df.loc[:, "doc_energy_subsidy_per_ask_short_range_electric"] = (
            doc_energy_subsidy_per_ask_short_range_electric
        )
        self.df.loc[:, "doc_energy_subsidy_per_ask_long_range_mean"] = (
            doc_energy_subsidy_per_ask_long_range_mean
        )
        self.df.loc[:, "doc_energy_subsidy_per_ask_medium_range_mean"] = (
            doc_energy_subsidy_per_ask_medium_range_mean
        )
        self.df.loc[:, "doc_energy_subsidy_per_ask_short_range_mean"] = (
            doc_energy_subsidy_per_ask_short_range_mean
        )
        self.df.loc[:, "doc_energy_subsidy_per_ask_mean"] = doc_energy_subsidy_per_ask_mean

        return (
            doc_energy_subsidy_per_ask_long_range_dropin_fuel,
            doc_energy_subsidy_per_ask_medium_range_dropin_fuel,
            doc_energy_subsidy_per_ask_short_range_dropin_fuel,
            doc_energy_subsidy_per_ask_long_range_hydrogen,
            doc_energy_subsidy_per_ask_medium_range_hydrogen,
            doc_energy_subsidy_per_ask_short_range_hydrogen,
            doc_energy_subsidy_per_ask_long_range_electric,
            doc_energy_subsidy_per_ask_medium_range_electric,
            doc_energy_subsidy_per_ask_short_range_electric,
            doc_energy_subsidy_per_ask_long_range_mean,
            doc_energy_subsidy_per_ask_medium_range_mean,
            doc_energy_subsidy_per_ask_short_range_mean,
            doc_energy_subsidy_per_ask_mean,
        )


class PassengerAircraftDocEnergyTax(AeroMAPSModel):
    """
    Energy tax (non-carbon) DOC per ASK calculation

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_energy_tax' by default
    """

    def __init__(self, name="passenger_aircraft_doc_energy_tax", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_per_ask_long_range_dropin_fuel: pd.Series,
        energy_per_ask_long_range_hydrogen: pd.Series,
        energy_per_ask_medium_range_dropin_fuel: pd.Series,
        energy_per_ask_medium_range_hydrogen: pd.Series,
        energy_per_ask_short_range_dropin_fuel: pd.Series,
        energy_per_ask_short_range_hydrogen: pd.Series,
        energy_per_ask_long_range_electric: pd.Series,
        energy_per_ask_medium_range_electric: pd.Series,
        energy_per_ask_short_range_electric: pd.Series,
        dropin_fuel_mean_unit_tax: pd.Series,
        hydrogen_mean_unit_tax: pd.Series,
        electric_mean_unit_tax: pd.Series,
        ask_long_range_hydrogen_share: pd.Series,
        ask_long_range_dropin_fuel_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_medium_range_dropin_fuel_share: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_short_range_dropin_fuel_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_long_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_short_range: pd.Series,
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
    ]:
        """
        Execution of the energy tax (non carbon) DOC per ASK calculation.
        Parameters
        ----------
        energy_per_ask_long_range_dropin_fuel
            Energy consumption per ASK for passenger long-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_long_range_hydrogen
            Energy consumption per ASK for passenger long-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_medium_range_dropin_fuel
            Energy consumption per ASK for passenger medium-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_medium_range_hydrogen
            Energy consumption per ASK for passenger medium-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_short_range_dropin_fuel
            Energy consumption per ASK for passenger short-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_short_range_hydrogen
            Energy consumption per ASK for passenger short-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_long_range_electric
            Energy consumption per ASK for passenger long-range market aircraft using electricity [MJ/ASK].
        energy_per_ask_medium_range_electric
            Energy consumption per ASK for passenger medium-range market aircraft using electricity [MJ/ASK].
        energy_per_ask_short_range_electric
            Energy consumption per ASK for passenger short-range market aircraft using electricity [MJ/ASK].
        dropin_fuel_mean_unit_tax
            Mean unit energy tax for drop-in fuels [€/MJ].
        hydrogen_mean_unit_tax
            Mean unit energy tax for hydrogen [€/MJ].
        electric_mean_unit_tax
            Mean unit energy tax for electricity [€/MJ].
        ask_long_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from hydrogen aircraft [%].
        ask_long_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from drop-in fuel aircraft [%].
        ask_medium_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from hydrogen aircraft [%].
        ask_medium_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from drop-in fuel aircraft [%].
        ask_short_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from hydrogen aircraft [%].
        ask_short_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from drop-in fuel aircraft [%].
        ask_long_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from electric aircraft [%].
        ask_medium_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from electric aircraft [%].
        ask_short_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from electric aircraft [%].
        ask_long_range
            Number of Available Seat Kilometer (ASK) for passenger long-range market [ASK].
        ask_medium_range
            Number of Available Seat Kilometer (ASK) for passenger medium-range market [ASK].
        ask_short_range
            Number of Available Seat Kilometer (ASK) for passenger short-range market [ASK].

        Returns
        -------
        doc_energy_tax_per_ask_short_range_dropin_fuel
            Direct operating cost attributable to energy tax, for short range drop-in fleet [€/ASK].
        doc_energy_tax_per_ask_medium_range_dropin_fuel
            Direct operating cost attributable to energy tax, for medium range drop-in fleet [€/ASK].
        doc_energy_tax_per_ask_long_range_dropin_fuel
            Direct operating cost attributable to energy tax, for long range drop-in fleet [€/ASK].
        doc_energy_tax_per_ask_short_range_hydrogen
            Direct operating cost attributable to energy tax, for short range hydrogen fleet [€/ASK].
        doc_energy_tax_per_ask_medium_range_hydrogen
            Direct operating cost attributable to energy tax, for medium range hydrogen fleet [€/ASK].
        doc_energy_tax_per_ask_long_range_hydrogen
            Direct operating cost attributable to energy tax, for long range hydrogen fleet [€/ASK].
        doc_energy_tax_per_ask_short_range_electric
            Direct operating cost attributable to energy tax, for short range electric fleet [€/ASK].
        doc_energy_tax_per_ask_medium_range_electric
            Direct operating cost attributable to energy tax, for medium range electric fleet [€/ASK].
        doc_energy_tax_per_ask_long_range_electric
            Direct operating cost attributable to energy tax, for long range electric fleet [€/ASK].
        doc_energy_tax_per_ask_short_range_mean
            Direct operating cost attributable to energy tax, for short range fleet [€/ASK].
        doc_energy_tax_per_ask_medium_range_mean
            Direct operating cost attributable to energy tax, for medium range fleet [€/ASK].
        doc_energy_tax_per_ask_long_range_mean
            Direct operating cost attributable to energy tax, for long range fleet [€/ASK].
        doc_energy_tax_per_ask_mean
            Direct operating cost attributable to energy tax, for overall fleet [€/ASK].
        """
        # Drop-in
        doc_energy_tax_per_ask_long_range_dropin_fuel = (
            energy_per_ask_long_range_dropin_fuel * dropin_fuel_mean_unit_tax
        )
        doc_energy_tax_per_ask_medium_range_dropin_fuel = (
            energy_per_ask_medium_range_dropin_fuel * dropin_fuel_mean_unit_tax
        )
        doc_energy_tax_per_ask_short_range_dropin_fuel = (
            energy_per_ask_short_range_dropin_fuel * dropin_fuel_mean_unit_tax
        )
        # Hydrogen
        doc_energy_tax_per_ask_long_range_hydrogen = (
            energy_per_ask_long_range_hydrogen * hydrogen_mean_unit_tax
        )
        doc_energy_tax_per_ask_medium_range_hydrogen = (
            energy_per_ask_medium_range_hydrogen * hydrogen_mean_unit_tax
        )
        doc_energy_tax_per_ask_short_range_hydrogen = (
            energy_per_ask_short_range_hydrogen * hydrogen_mean_unit_tax
        )
        # Electric
        doc_energy_tax_per_ask_long_range_electric = (
            energy_per_ask_long_range_electric * electric_mean_unit_tax
        )
        doc_energy_tax_per_ask_medium_range_electric = (
            energy_per_ask_medium_range_electric * electric_mean_unit_tax
        )
        doc_energy_tax_per_ask_short_range_electric = (
            energy_per_ask_short_range_electric * electric_mean_unit_tax
        )

        # Moyennes pondérées
        doc_energy_tax_per_ask_long_range_mean = (
            doc_energy_tax_per_ask_long_range_hydrogen.fillna(0)
            * ask_long_range_hydrogen_share
            / 100
            + doc_energy_tax_per_ask_long_range_dropin_fuel.fillna(0)
            * ask_long_range_dropin_fuel_share
            / 100
            + doc_energy_tax_per_ask_long_range_electric.fillna(0)
            * ask_long_range_electric_share
            / 100
        )
        doc_energy_tax_per_ask_medium_range_mean = (
            doc_energy_tax_per_ask_medium_range_hydrogen.fillna(0)
            * ask_medium_range_hydrogen_share
            / 100
            + doc_energy_tax_per_ask_medium_range_dropin_fuel.fillna(0)
            * ask_medium_range_dropin_fuel_share
            / 100
            + doc_energy_tax_per_ask_medium_range_electric.fillna(0)
            * ask_medium_range_electric_share
            / 100
        )
        doc_energy_tax_per_ask_short_range_mean = (
            doc_energy_tax_per_ask_short_range_hydrogen.fillna(0)
            * ask_short_range_hydrogen_share
            / 100
            + doc_energy_tax_per_ask_short_range_dropin_fuel.fillna(0)
            * ask_short_range_dropin_fuel_share
            / 100
            + doc_energy_tax_per_ask_short_range_electric.fillna(0)
            * ask_short_range_electric_share
            / 100
        )
        doc_energy_tax_per_ask_mean = (
            doc_energy_tax_per_ask_long_range_mean * ask_long_range
            + doc_energy_tax_per_ask_medium_range_mean * ask_medium_range
            + doc_energy_tax_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        # Stockage dans le DataFrame
        self.df.loc[:, "doc_energy_tax_per_ask_long_range_dropin_fuel"] = (
            doc_energy_tax_per_ask_long_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_tax_per_ask_medium_range_dropin_fuel"] = (
            doc_energy_tax_per_ask_medium_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_tax_per_ask_short_range_dropin_fuel"] = (
            doc_energy_tax_per_ask_short_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_tax_per_ask_long_range_hydrogen"] = (
            doc_energy_tax_per_ask_long_range_hydrogen
        )
        self.df.loc[:, "doc_energy_tax_per_ask_medium_range_hydrogen"] = (
            doc_energy_tax_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "doc_energy_tax_per_ask_short_range_hydrogen"] = (
            doc_energy_tax_per_ask_short_range_hydrogen
        )
        self.df.loc[:, "doc_energy_tax_per_ask_long_range_electric"] = (
            doc_energy_tax_per_ask_long_range_electric
        )
        self.df.loc[:, "doc_energy_tax_per_ask_medium_range_electric"] = (
            doc_energy_tax_per_ask_medium_range_electric
        )
        self.df.loc[:, "doc_energy_tax_per_ask_short_range_electric"] = (
            doc_energy_tax_per_ask_short_range_electric
        )
        self.df.loc[:, "doc_energy_tax_per_ask_long_range_mean"] = (
            doc_energy_tax_per_ask_long_range_mean
        )
        self.df.loc[:, "doc_energy_tax_per_ask_medium_range_mean"] = (
            doc_energy_tax_per_ask_medium_range_mean
        )
        self.df.loc[:, "doc_energy_tax_per_ask_short_range_mean"] = (
            doc_energy_tax_per_ask_short_range_mean
        )
        self.df.loc[:, "doc_energy_tax_per_ask_mean"] = doc_energy_tax_per_ask_mean

        return (
            doc_energy_tax_per_ask_long_range_dropin_fuel,
            doc_energy_tax_per_ask_medium_range_dropin_fuel,
            doc_energy_tax_per_ask_short_range_dropin_fuel,
            doc_energy_tax_per_ask_long_range_hydrogen,
            doc_energy_tax_per_ask_medium_range_hydrogen,
            doc_energy_tax_per_ask_short_range_hydrogen,
            doc_energy_tax_per_ask_long_range_electric,
            doc_energy_tax_per_ask_medium_range_electric,
            doc_energy_tax_per_ask_short_range_electric,
            doc_energy_tax_per_ask_long_range_mean,
            doc_energy_tax_per_ask_medium_range_mean,
            doc_energy_tax_per_ask_short_range_mean,
            doc_energy_tax_per_ask_mean,
        )


# class PassengerAircraftDocCarbonTax(AeroMAPSModel):
#     def __init__(self, name="passenger_aircraft_doc_carbon_tax", *args, **kwargs):
#         super().__init__(name=name, *args, **kwargs)
#         self.fleet_model = None
#
#     def compute(
#         self,
#         energy_per_ask_long_range_dropin_fuel: pd.Series,
#         energy_per_ask_long_range_hydrogen: pd.Series,
#         energy_per_ask_long_range_electric: pd.Series,
#         energy_per_ask_medium_range_dropin_fuel: pd.Series,
#         energy_per_ask_medium_range_hydrogen: pd.Series,
#         energy_per_ask_medium_range_electric: pd.Series,
#         energy_per_ask_short_range_dropin_fuel: pd.Series,
#         energy_per_ask_short_range_hydrogen: pd.Series,
#         energy_per_ask_short_range_electric: pd.Series,
#         dropin_fuel_mean_carbon_tax_supplement: pd.Series,
#         hydrogen_mean_carbon_tax_supplement: pd.Series,
#         electric_mean_carbon_tax_supplement: pd.Series,
#         ask_long_range_hydrogen_share: pd.Series,
#         ask_long_range_dropin_fuel_share: pd.Series,
#         ask_long_range_electric_share: pd.Series,
#         ask_medium_range_hydrogen_share: pd.Series,
#         ask_medium_range_dropin_fuel_share: pd.Series,
#         ask_medium_range_electric_share: pd.Series,
#         ask_short_range_hydrogen_share: pd.Series,
#         ask_short_range_dropin_fuel_share: pd.Series,
#         ask_short_range_electric_share: pd.Series,
#         ask_long_range: pd.Series,
#         ask_medium_range: pd.Series,
#         ask_short_range: pd.Series,
#         co2_emissions: pd.Series,
#         carbon_offset: pd.Series,
#     ) -> Tuple[
#         pd.Series,
#         pd.Series,
#         pd.Series,
#         pd.Series,
#         pd.Series,
#         pd.Series,
#         pd.Series,
#         pd.Series,
#         pd.Series,
#         pd.Series,
#         pd.Series,
#         pd.Series,
#         pd.Series,
#         pd.Series,
#     ]:
#         # Drop-in fuels lower heating value (MJ/L)
#         fuel_lhv = 35.3
#         # LH2 specific energy (MJ/kg)
#         hydrogen_specific_energy = 119.93
#
#         doc_carbon_tax_per_ask_long_range_dropin_fuel = pd.Series(
#             np.nan, range(self.historic_start_year, self.end_year + 1)
#         )
#         doc_carbon_tax_per_ask_long_range_hydrogen = pd.Series(
#             np.nan, range(self.historic_start_year, self.end_year + 1)
#         )
#         doc_carbon_tax_per_ask_long_range_electric = pd.Series(
#             np.nan, range(self.historic_start_year, self.end_year + 1)
#         )
#         doc_carbon_tax_per_ask_medium_range_dropin_fuel = pd.Series(
#             np.nan, range(self.historic_start_year, self.end_year + 1)
#         )
#         doc_carbon_tax_per_ask_medium_range_hydrogen = pd.Series(
#             np.nan, range(self.historic_start_year, self.end_year + 1)
#         )
#         doc_carbon_tax_per_ask_medium_range_electric = pd.Series(
#             np.nan, range(self.historic_start_year, self.end_year + 1)
#         )
#         doc_carbon_tax_per_ask_short_range_dropin_fuel = pd.Series(
#             np.nan, range(self.historic_start_year, self.end_year + 1)
#         )
#         doc_carbon_tax_per_ask_short_range_hydrogen = pd.Series(
#             np.nan, range(self.historic_start_year, self.end_year + 1)
#         )
#         doc_carbon_tax_per_ask_short_range_electric = pd.Series(
#             np.nan, range(self.historic_start_year, self.end_year + 1)
#         )
#         for k in range(self.historic_start_year, self.end_year + 1):
#             if ask_long_range_dropin_fuel_share[k] > 0:
#                 doc_carbon_tax_per_ask_long_range_dropin_fuel[k] = (
#                     energy_per_ask_long_range_dropin_fuel[k]
#                     * dropin_fuel_mean_carbon_tax_supplement[k]
#                     / fuel_lhv
#                 )
#             if ask_long_range_hydrogen_share[k] > 0:
#                 doc_carbon_tax_per_ask_long_range_hydrogen[k] = (
#                     energy_per_ask_long_range_hydrogen[k]
#                     * hydrogen_mean_carbon_tax_supplement[k]
#                     / hydrogen_specific_energy
#                 )
#             if ask_long_range_electric_share[k] > 0:
#                 doc_carbon_tax_per_ask_long_range_electric[k] = (
#                     energy_per_ask_long_range_electric[k]
#                     * electric_mean_carbon_tax_supplement[k]
#                     / 3.6
#                 )
#             if ask_medium_range_dropin_fuel_share[k] > 0:
#                 doc_carbon_tax_per_ask_medium_range_dropin_fuel[k] = (
#                     energy_per_ask_medium_range_dropin_fuel[k]
#                     * dropin_fuel_mean_carbon_tax_supplement[k]
#                     / fuel_lhv
#                 )
#             if ask_medium_range_hydrogen_share[k] > 0:
#                 doc_carbon_tax_per_ask_medium_range_hydrogen[k] = (
#                     energy_per_ask_medium_range_hydrogen[k]
#                     * hydrogen_mean_carbon_tax_supplement[k]
#                     / hydrogen_specific_energy
#                 )
#             if ask_medium_range_electric_share[k] > 0:
#                 doc_carbon_tax_per_ask_medium_range_electric[k] = (
#                     energy_per_ask_medium_range_electric[k]
#                     * electric_mean_carbon_tax_supplement[k]
#                     / 3.6
#                 )
#             if ask_short_range_dropin_fuel_share[k] > 0:
#                 doc_carbon_tax_per_ask_short_range_dropin_fuel[k] = (
#                     energy_per_ask_short_range_dropin_fuel[k]
#                     * dropin_fuel_mean_carbon_tax_supplement[k]
#                     / fuel_lhv
#                 )
#             if ask_short_range_hydrogen_share[k] > 0:
#                 doc_carbon_tax_per_ask_short_range_hydrogen[k] = (
#                     energy_per_ask_short_range_hydrogen[k]
#                     * hydrogen_mean_carbon_tax_supplement[k]
#                     / hydrogen_specific_energy
#                 )
#             if ask_short_range_electric_share[k] > 0:
#                 doc_carbon_tax_per_ask_short_range_electric[k] = (
#                     energy_per_ask_short_range_electric[k]
#                     * electric_mean_carbon_tax_supplement[k]
#                     / 3.6
#                 )
#
#         doc_carbon_tax_per_ask_long_range_mean = (
#             doc_carbon_tax_per_ask_long_range_hydrogen.fillna(0)
#             * ask_long_range_hydrogen_share
#             / 100
#             + doc_carbon_tax_per_ask_long_range_dropin_fuel.fillna(0)
#             * ask_long_range_dropin_fuel_share
#             / 100
#             + doc_carbon_tax_per_ask_long_range_electric.fillna(0)
#             * ask_long_range_electric_share
#             / 100
#         )
#
#         doc_carbon_tax_per_ask_medium_range_mean = (
#             doc_carbon_tax_per_ask_medium_range_hydrogen.fillna(0)
#             * ask_medium_range_hydrogen_share
#             / 100
#             + doc_carbon_tax_per_ask_medium_range_dropin_fuel.fillna(0)
#             * ask_medium_range_dropin_fuel_share
#             / 100
#             + doc_carbon_tax_per_ask_medium_range_electric.fillna(0)
#             * ask_medium_range_electric_share
#             / 100
#         )
#
#         doc_carbon_tax_per_ask_short_range_mean = (
#             doc_carbon_tax_per_ask_short_range_hydrogen.fillna(0)
#             * ask_short_range_hydrogen_share
#             / 100
#             + doc_carbon_tax_per_ask_short_range_dropin_fuel.fillna(0)
#             * ask_short_range_dropin_fuel_share
#             / 100
#             + doc_carbon_tax_per_ask_short_range_electric.fillna(0)
#             * ask_short_range_electric_share
#             / 100
#         )
#
#         doc_carbon_tax_per_ask_mean = (
#             doc_carbon_tax_per_ask_long_range_mean * ask_long_range
#             + doc_carbon_tax_per_ask_medium_range_mean * ask_medium_range
#             + doc_carbon_tax_per_ask_short_range_mean * ask_short_range
#         ) / (ask_long_range + ask_medium_range + ask_short_range)
#
#         for k in range(self.historic_start_year, self.end_year + 1):
#             self.df.loc[k, "doc_carbon_tax_lowering_offset_per_ask_mean"] = (
#                 doc_carbon_tax_per_ask_mean.loc[k]
#                 * (co2_emissions.loc[k] - carbon_offset.loc[k])
#                 / co2_emissions.loc[k]
#             )
#
#         self.df.loc[:, "doc_carbon_tax_per_ask_long_range_dropin_fuel"] = (
#             doc_carbon_tax_per_ask_long_range_dropin_fuel
#         )
#         self.df.loc[:, "doc_carbon_tax_per_ask_long_range_hydrogen"] = (
#             doc_carbon_tax_per_ask_long_range_hydrogen
#         )
#         self.df.loc[:, "doc_carbon_tax_per_ask_long_range_mean"] = (
#             doc_carbon_tax_per_ask_long_range_mean
#         )
#         self.df.loc[:, "doc_carbon_tax_per_ask_medium_range_dropin_fuel"] = (
#             doc_carbon_tax_per_ask_medium_range_dropin_fuel
#         )
#         self.df.loc[:, "doc_carbon_tax_per_ask_medium_range_hydrogen"] = (
#             doc_carbon_tax_per_ask_medium_range_hydrogen
#         )
#         self.df.loc[:, "doc_carbon_tax_per_ask_medium_range_mean"] = (
#             doc_carbon_tax_per_ask_medium_range_mean
#         )
#         self.df.loc[:, "doc_carbon_tax_per_ask_short_range_dropin_fuel"] = (
#             doc_carbon_tax_per_ask_short_range_dropin_fuel
#         )
#         self.df.loc[:, "doc_carbon_tax_per_ask_short_range_hydrogen"] = (
#             doc_carbon_tax_per_ask_short_range_hydrogen
#         )
#         self.df.loc[:, "doc_carbon_tax_per_ask_short_range_mean"] = (
#             doc_carbon_tax_per_ask_short_range_mean
#         )
#         self.df.loc[:, "doc_carbon_tax_per_ask_long_range_electric"] = (
#             doc_carbon_tax_per_ask_long_range_electric
#         )
#         self.df.loc[:, "doc_carbon_tax_per_ask_medium_range_electric"] = (
#             doc_carbon_tax_per_ask_medium_range_electric
#         )
#         self.df.loc[:, "doc_carbon_tax_per_ask_short_range_electric"] = (
#             doc_carbon_tax_per_ask_short_range_electric
#         )
#         self.df.loc[:, "doc_carbon_tax_per_ask_mean"] = doc_carbon_tax_per_ask_mean
#
#         doc_carbon_tax_lowering_offset_per_ask_mean = self.df[
#             "doc_carbon_tax_lowering_offset_per_ask_mean"
#         ]
#
#         return (
#             doc_carbon_tax_per_ask_long_range_dropin_fuel,
#             doc_carbon_tax_per_ask_long_range_hydrogen,
#             doc_carbon_tax_per_ask_long_range_electric,
#             doc_carbon_tax_per_ask_long_range_mean,
#             doc_carbon_tax_per_ask_medium_range_dropin_fuel,
#             doc_carbon_tax_per_ask_medium_range_hydrogen,
#             doc_carbon_tax_per_ask_medium_range_electric,
#             doc_carbon_tax_per_ask_medium_range_mean,
#             doc_carbon_tax_per_ask_short_range_dropin_fuel,
#             doc_carbon_tax_per_ask_short_range_hydrogen,
#             doc_carbon_tax_per_ask_short_range_electric,
#             doc_carbon_tax_per_ask_short_range_mean,
#             doc_carbon_tax_per_ask_mean,
#             doc_carbon_tax_lowering_offset_per_ask_mean,
#         )


class PassengerAircraftTotalDoc(AeroMAPSModel):
    """
    Aggregation of all DOC categories for total DOC per ASK calculation
    """

    def __init__(self, name="passenger_aircraft_total_doc", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = None

    def compute(
        self,
        doc_non_energy_per_ask_short_range_dropin_fuel: pd.Series,
        doc_non_energy_per_ask_medium_range_dropin_fuel: pd.Series,
        doc_non_energy_per_ask_long_range_dropin_fuel: pd.Series,
        doc_non_energy_per_ask_short_range_hydrogen: pd.Series,
        doc_non_energy_per_ask_medium_range_hydrogen: pd.Series,
        doc_non_energy_per_ask_long_range_hydrogen: pd.Series,
        doc_non_energy_per_ask_short_range_mean: pd.Series,
        doc_non_energy_per_ask_medium_range_mean: pd.Series,
        doc_non_energy_per_ask_long_range_mean: pd.Series,
        doc_non_energy_per_ask_mean: pd.Series,
        doc_energy_per_ask_long_range_dropin_fuel: pd.Series,
        doc_energy_per_ask_long_range_hydrogen: pd.Series,
        doc_energy_per_ask_long_range_mean: pd.Series,
        doc_energy_per_ask_medium_range_dropin_fuel: pd.Series,
        doc_energy_per_ask_medium_range_hydrogen: pd.Series,
        doc_energy_per_ask_medium_range_mean: pd.Series,
        doc_energy_per_ask_short_range_dropin_fuel: pd.Series,
        doc_energy_per_ask_short_range_hydrogen: pd.Series,
        doc_energy_per_ask_short_range_mean: pd.Series,
        doc_energy_per_ask_mean: pd.Series,
        doc_energy_carbon_tax_per_ask_long_range_dropin_fuel: pd.Series,
        doc_energy_carbon_tax_per_ask_long_range_hydrogen: pd.Series,
        doc_energy_carbon_tax_per_ask_long_range_mean: pd.Series,
        doc_energy_carbon_tax_per_ask_medium_range_dropin_fuel: pd.Series,
        doc_energy_carbon_tax_per_ask_medium_range_hydrogen: pd.Series,
        doc_energy_carbon_tax_per_ask_medium_range_mean: pd.Series,
        doc_energy_carbon_tax_per_ask_short_range_dropin_fuel: pd.Series,
        doc_energy_carbon_tax_per_ask_short_range_hydrogen: pd.Series,
        doc_energy_carbon_tax_per_ask_short_range_mean: pd.Series,
        doc_non_energy_per_ask_short_range_electric: pd.Series,
        doc_non_energy_per_ask_medium_range_electric: pd.Series,
        doc_non_energy_per_ask_long_range_electric: pd.Series,
        doc_energy_per_ask_short_range_electric: pd.Series,
        doc_energy_per_ask_medium_range_electric: pd.Series,
        doc_energy_per_ask_long_range_electric: pd.Series,
        doc_energy_carbon_tax_per_ask_short_range_electric: pd.Series,
        doc_energy_carbon_tax_per_ask_medium_range_electric: pd.Series,
        doc_energy_carbon_tax_per_ask_long_range_electric: pd.Series,
        doc_energy_carbon_tax_per_ask_mean: pd.Series,
        doc_energy_subsidy_per_ask_long_range_dropin_fuel: pd.Series,
        doc_energy_subsidy_per_ask_medium_range_dropin_fuel: pd.Series,
        doc_energy_subsidy_per_ask_short_range_dropin_fuel: pd.Series,
        doc_energy_subsidy_per_ask_long_range_hydrogen: pd.Series,
        doc_energy_subsidy_per_ask_medium_range_hydrogen: pd.Series,
        doc_energy_subsidy_per_ask_short_range_hydrogen: pd.Series,
        doc_energy_subsidy_per_ask_long_range_electric: pd.Series,
        doc_energy_subsidy_per_ask_medium_range_electric: pd.Series,
        doc_energy_subsidy_per_ask_short_range_electric: pd.Series,
        doc_energy_subsidy_per_ask_long_range_mean: pd.Series,
        doc_energy_subsidy_per_ask_medium_range_mean: pd.Series,
        doc_energy_subsidy_per_ask_short_range_mean: pd.Series,
        doc_energy_subsidy_per_ask_mean: pd.Series,
        doc_energy_tax_per_ask_long_range_dropin_fuel: pd.Series,
        doc_energy_tax_per_ask_medium_range_dropin_fuel: pd.Series,
        doc_energy_tax_per_ask_short_range_dropin_fuel: pd.Series,
        doc_energy_tax_per_ask_long_range_hydrogen: pd.Series,
        doc_energy_tax_per_ask_medium_range_hydrogen: pd.Series,
        doc_energy_tax_per_ask_short_range_hydrogen: pd.Series,
        doc_energy_tax_per_ask_long_range_electric: pd.Series,
        doc_energy_tax_per_ask_medium_range_electric: pd.Series,
        doc_energy_tax_per_ask_short_range_electric: pd.Series,
        doc_energy_tax_per_ask_long_range_mean: pd.Series,
        doc_energy_tax_per_ask_medium_range_mean: pd.Series,
        doc_energy_tax_per_ask_short_range_mean: pd.Series,
        doc_energy_tax_per_ask_mean: pd.Series,
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
    ]:
        """
        Execution of the total DOC per ASK calculation.
        Parameters
        ----------
        doc_non_energy_per_ask_short_range_dropin_fuel
            Non-energy direct operating cost per ASK for passenger short-range market aircraft using drop-in fuel [€/ASK].
        doc_non_energy_per_ask_medium_range_dropin_fuel
            Non-energy direct operating cost per ASK for passenger medium-range market aircraft using drop-in fuel [€/ASK].
        doc_non_energy_per_ask_long_range_dropin_fuel
            Non-energy direct operating cost per ASK for passenger long-range market aircraft using drop-in fuel [€/ASK].
        doc_non_energy_per_ask_short_range_hydrogen
            Non-energy direct operating cost per ASK for passenger short-range market aircraft using hydrogen [€/ASK].
        doc_non_energy_per_ask_medium_range_hydrogen
            Non-energy direct operating cost per ASK for passenger medium-range market aircraft using hydrogen [€/ASK].
        doc_non_energy_per_ask_long_range_hydrogen
            Non-energy direct operating cost per ASK for passenger long-range market aircraft using hydrogen [€/ASK].
        doc_non_energy_per_ask_short_range_mean
            Non-energy direct operating cost per ASK for passenger short-range market aircraft average [€/ASK].
        doc_non_energy_per_ask_medium_range_mean
            Non-energy direct operating cost per ASK for passenger medium-range market aircraft average [€/ASK].
        doc_non_energy_per_ask_long_range_mean
            Non-energy direct operating cost per ASK for passenger long-range market aircraft average [€/ASK].
        doc_non_energy_per_ask_mean
            Non-energy direct operating cost per ASK for passenger overall market aircraft average [€/ASK].
        doc_energy_per_ask_long_range_dropin_fuel
            Energy direct operating cost per ASK for passenger long-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_per_ask_long_range_hydrogen
            Energy direct operating cost per ASK for passenger long-range market aircraft using hydrogen [€/ASK].
        doc_energy_per_ask_long_range_mean
            Energy direct operating cost per ASK for passenger long-range market aircraft average [€/ASK].
        doc_energy_per_ask_medium_range_dropin_fuel
            Energy direct operating cost per ASK for passenger medium-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_per_ask_medium_range_hydrogen
            Energy direct operating cost per ASK for passenger medium-range market aircraft using hydrogen [€/ASK].
        doc_energy_per_ask_medium_range_mean
            Energy direct operating cost per ASK for passenger medium-range market aircraft average [€/ASK].
        doc_energy_per_ask_short_range_dropin_fuel
            Energy direct operating cost per ASK for passenger short-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_per_ask_short_range_hydrogen
            Energy direct operating cost per ASK for passenger short-range market aircraft using hydrogen [€/ASK].
        doc_energy_per_ask_short_range_mean
            Energy direct operating cost per ASK for passenger short-range market aircraft average [€/ASK].
        doc_energy_per_ask_mean
            Energy direct operating cost per ASK for passenger overall market aircraft average [€/ASK].
        doc_energy_carbon_tax_per_ask_long_range_dropin_fuel
            Energy carbon tax direct operating cost per ASK for passenger long-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_carbon_tax_per_ask_long_range_hydrogen
            Energy carbon tax direct operating cost per ASK for passenger long-range market aircraft using hydrogen [€/ASK].
        doc_energy_carbon_tax_per_ask_long_range_mean
            Energy carbon tax direct operating cost per ASK for passenger long-range market aircraft average [€/ASK].
        doc_energy_carbon_tax_per_ask_medium_range_dropin_fuel
            Energy carbon tax direct operating cost per ASK for passenger medium-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_carbon_tax_per_ask_medium_range_hydrogen
            Energy carbon tax direct operating cost per ASK for passenger medium-range market aircraft using hydrogen [€/ASK].
        doc_energy_carbon_tax_per_ask_medium_range_mean
            Energy carbon tax direct operating cost per ASK for passenger medium-range market aircraft average [€/ASK].
        doc_energy_carbon_tax_per_ask_short_range_dropin_fuel
            Energy carbon tax direct operating cost per ASK for passenger short-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_carbon_tax_per_ask_short_range_hydrogen
            Energy carbon tax direct operating cost per ASK for passenger short-range market aircraft using hydrogen [€/ASK].
        doc_energy_carbon_tax_per_ask_short_range_mean
            Energy carbon tax direct operating cost per ASK for passenger short-range market aircraft average [€/ASK].
        doc_non_energy_per_ask_short_range_electric
            Non-energy direct operating cost per ASK for passenger short-range market aircraft using electric propulsion [€/ASK].
        doc_non_energy_per_ask_medium_range_electric
            Non-energy direct operating cost per ASK for passenger medium-range market aircraft using electric propulsion [€/ASK].
        doc_non_energy_per_ask_long_range_electric
            Non-energy direct operating cost per ASK for passenger long-range market aircraft using electric propulsion [€/ASK].
        doc_energy_per_ask_short_range_electric
            Energy direct operating cost per ASK for passenger short-range market aircraft using electric propulsion [€/ASK].
        doc_energy_per_ask_medium_range_electric
            Energy direct operating cost per ASK for passenger medium-range market aircraft using electric propulsion [€/ASK].
        doc_energy_per_ask_long_range_electric
            Energy direct operating cost per ASK for passenger long-range market aircraft using electric propulsion [€/ASK].
        doc_energy_carbon_tax_per_ask_short_range_electric
            Energy carbon tax direct operating cost per ASK for passenger short-range market aircraft using electric propulsion [€/ASK].
        doc_energy_carbon_tax_per_ask_medium_range_electric
            Energy carbon tax direct operating cost per ASK for passenger medium-range market aircraft using electric propulsion [€/ASK].
        doc_energy_carbon_tax_per_ask_long_range_electric
            Energy carbon tax direct operating cost per ASK for passenger long-range market aircraft using electric propulsion [€/ASK].
        doc_energy_carbon_tax_per_ask_mean
            Energy carbon tax direct operating cost per ASK for passenger overall market aircraft average [€/ASK].
        doc_energy_subsidy_per_ask_long_range_dropin_fuel
            Energy subsidy direct operating cost per ASK for passenger long-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_subsidy_per_ask_medium_range_dropin_fuel
            Energy subsidy direct operating cost per ASK for passenger medium-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_subsidy_per_ask_short_range_dropin_fuel
            Energy subsidy direct operating cost per ASK for passenger short-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_subsidy_per_ask_long_range_hydrogen
            Energy subsidy direct operating cost per ASK for passenger long-range market aircraft using hydrogen [€/ASK].
        doc_energy_subsidy_per_ask_medium_range_hydrogen
            Energy subsidy direct operating cost per ASK for passenger medium-range market aircraft using hydrogen [€/ASK].
        doc_energy_subsidy_per_ask_short_range_hydrogen
            Energy subsidy direct operating cost per ASK for passenger short-range market aircraft using hydrogen [€/ASK].
        doc_energy_subsidy_per_ask_long_range_electric
            Energy subsidy direct operating cost per ASK for passenger long-range market aircraft using electric propulsion [€/ASK].
        doc_energy_subsidy_per_ask_medium_range_electric
            Energy subsidy direct operating cost per ASK for passenger medium-range market aircraft using electric propulsion [€/ASK].
        doc_energy_subsidy_per_ask_short_range_electric
            Energy subsidy direct operating cost per ASK for passenger short-range market aircraft using electric propulsion [€/ASK].
        doc_energy_subsidy_per_ask_long_range_mean
            Energy subsidy direct operating cost per ASK for passenger long-range market aircraft average [€/ASK].
        doc_energy_subsidy_per_ask_medium_range_mean
            Energy subsidy direct operating cost per ASK for passenger medium-range market aircraft average [€/ASK].
        doc_energy_subsidy_per_ask_short_range_mean
            Energy subsidy direct operating cost per ASK for passenger short-range market aircraft average [€/ASK].
        doc_energy_subsidy_per_ask_mean
            Energy subsidy direct operating cost per ASK for passenger overall market aircraft average [€/ASK].
        doc_energy_tax_per_ask_long_range_dropin_fuel
            Energy tax direct operating cost per ASK for passenger long-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_tax_per_ask_medium_range_dropin_fuel
            Energy tax direct operating cost per ASK for passenger medium-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_tax_per_ask_short_range_dropin_fuel
            Energy tax direct operating cost per ASK for passenger short-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_tax_per_ask_long_range_hydrogen
            Energy tax direct operating cost per ASK for passenger long-range market aircraft using hydrogen [€/ASK].
        doc_energy_tax_per_ask_medium_range_hydrogen
            Energy tax direct operating cost per ASK for passenger medium-range market aircraft using hydrogen [€/ASK].
        doc_energy_tax_per_ask_short_range_hydrogen
            Energy tax direct operating cost per ASK for passenger short-range market aircraft using hydrogen [€/ASK].
        doc_energy_tax_per_ask_long_range_electric
            Energy tax direct operating cost per ASK for passenger long-range market aircraft using electric propulsion [€/ASK].
        doc_energy_tax_per_ask_medium_range_electric
            Energy tax direct operating cost per ASK for passenger medium-range market aircraft using electric propulsion [€/ASK].
        doc_energy_tax_per_ask_short_range_electric
            Energy tax direct operating cost per ASK for passenger short-range market aircraft using electric propulsion [€/ASK].
        doc_energy_tax_per_ask_long_range_mean
            Energy tax direct operating cost per ASK for passenger long-range market aircraft average [€/ASK].
        doc_energy_tax_per_ask_medium_range_mean
            Energy tax direct operating cost per ASK for passenger medium-range market aircraft average [€/ASK].
        doc_energy_tax_per_ask_short_range_mean
            Energy tax direct operating cost per ASK for passenger short-range market aircraft average [€/ASK].
        doc_energy_tax_per_ask_mean
            Energy tax direct operating cost per ASK for passenger overall market aircraft average [€/ASK].

        Returns
        -------
        doc_total_per_ask_short_range_dropin_fuel
            Total direct operating cost per ASK for passenger short-range market aircraft using drop-in fuel [€/ASK].
        doc_total_per_ask_medium_range_dropin_fuel
            Total direct operating cost per ASK for passenger medium-range market aircraft using drop-in fuel [€/ASK].
        doc_total_per_ask_long_range_dropin_fuel
            Total direct operating cost per ASK for passenger long-range market aircraft using drop-in fuel [€/ASK].
        doc_total_per_ask_short_range_hydrogen
            Total direct operating cost per ASK for passenger short-range market aircraft using hydrogen [€/ASK].
        doc_total_per_ask_medium_range_hydrogen
            Total direct operating cost per ASK for passenger medium-range market aircraft using hydrogen [€/ASK].
        doc_total_per_ask_long_range_hydrogen
            Total direct operating cost per ASK for passenger long-range market aircraft using hydrogen [€/ASK].
        doc_total_per_ask_short_range_electric
            Total direct operating cost per ASK for passenger short-range market aircraft using electric propulsion [€/ASK].
        doc_total_per_ask_medium_range_electric
            Total direct operating cost per ASK for passenger medium-range market aircraft using electric propulsion [€/ASK].
        doc_total_per_ask_long_range_electric
            Total direct operating cost per ASK for passenger long-range market aircraft using electric propulsion [€/ASK].
        doc_total_per_ask_short_range_mean
            Total direct operating cost per ASK for passenger short-range market aircraft average [€/ASK].
        doc_total_per_ask_medium_range_mean
            Total direct operating cost per ASK for passenger medium-range market aircraft average [€/ASK].
        doc_total_per_ask_long_range_mean
            Total direct operating cost per ASK for passenger long-range market aircraft average [€/ASK].
        doc_total_per_ask_mean
            Total direct operating cost per ASK for passenger overall market aircraft average [€/ASK].
        """
        # Drop-in
        doc_total_per_ask_short_range_dropin_fuel = (
            doc_non_energy_per_ask_short_range_dropin_fuel
            + doc_energy_per_ask_short_range_dropin_fuel
            + doc_energy_carbon_tax_per_ask_short_range_dropin_fuel
            - doc_energy_subsidy_per_ask_short_range_dropin_fuel
            + doc_energy_tax_per_ask_short_range_dropin_fuel
        )

        doc_total_per_ask_medium_range_dropin_fuel = (
            doc_non_energy_per_ask_medium_range_dropin_fuel
            + doc_energy_per_ask_medium_range_dropin_fuel
            + doc_energy_carbon_tax_per_ask_medium_range_dropin_fuel
            - doc_energy_subsidy_per_ask_medium_range_dropin_fuel
            + doc_energy_tax_per_ask_medium_range_dropin_fuel
        )

        doc_total_per_ask_long_range_dropin_fuel = (
            doc_non_energy_per_ask_long_range_dropin_fuel
            + doc_energy_per_ask_long_range_dropin_fuel
            + doc_energy_carbon_tax_per_ask_long_range_dropin_fuel
            - doc_energy_subsidy_per_ask_long_range_dropin_fuel
            + doc_energy_tax_per_ask_long_range_dropin_fuel
        )

        # Hydrogen
        doc_total_per_ask_short_range_hydrogen = (
            doc_non_energy_per_ask_short_range_hydrogen
            + doc_energy_per_ask_short_range_hydrogen
            + doc_energy_carbon_tax_per_ask_short_range_hydrogen
            - doc_energy_subsidy_per_ask_short_range_hydrogen
            + doc_energy_tax_per_ask_short_range_hydrogen
        )

        doc_total_per_ask_medium_range_hydrogen = (
            doc_non_energy_per_ask_medium_range_hydrogen
            + doc_energy_per_ask_medium_range_hydrogen
            + doc_energy_carbon_tax_per_ask_medium_range_hydrogen
            - doc_energy_subsidy_per_ask_medium_range_hydrogen
            + doc_energy_tax_per_ask_medium_range_hydrogen
        )

        doc_total_per_ask_long_range_hydrogen = (
            doc_non_energy_per_ask_long_range_hydrogen
            + doc_energy_per_ask_long_range_hydrogen
            + doc_energy_carbon_tax_per_ask_long_range_hydrogen
            - doc_energy_subsidy_per_ask_long_range_hydrogen
            + doc_energy_tax_per_ask_long_range_hydrogen
        )

        # Electric
        doc_total_per_ask_short_range_electric = (
            doc_non_energy_per_ask_short_range_electric
            + doc_energy_per_ask_short_range_electric
            + doc_energy_carbon_tax_per_ask_short_range_electric
            - doc_energy_subsidy_per_ask_short_range_electric
            + doc_energy_tax_per_ask_short_range_electric
        )

        doc_total_per_ask_medium_range_electric = (
            doc_non_energy_per_ask_medium_range_electric
            + doc_energy_per_ask_medium_range_electric
            + doc_energy_carbon_tax_per_ask_medium_range_electric
            - doc_energy_subsidy_per_ask_medium_range_electric
            + doc_energy_tax_per_ask_medium_range_electric
        )

        doc_total_per_ask_long_range_electric = (
            doc_non_energy_per_ask_long_range_electric
            + doc_energy_per_ask_long_range_electric
            + doc_energy_carbon_tax_per_ask_long_range_electric
            - doc_energy_subsidy_per_ask_long_range_electric
            + doc_energy_tax_per_ask_long_range_electric
        )

        # Average per category
        doc_total_per_ask_short_range_mean = (
            doc_non_energy_per_ask_short_range_mean
            + doc_energy_per_ask_short_range_mean
            + doc_energy_carbon_tax_per_ask_short_range_mean
            - doc_energy_subsidy_per_ask_short_range_mean
            + doc_energy_tax_per_ask_short_range_mean
        )

        doc_total_per_ask_medium_range_mean = (
            doc_non_energy_per_ask_medium_range_mean
            + doc_energy_per_ask_medium_range_mean
            + doc_energy_carbon_tax_per_ask_medium_range_mean
            - doc_energy_subsidy_per_ask_medium_range_mean
            + doc_energy_tax_per_ask_medium_range_mean
        )

        doc_total_per_ask_long_range_mean = (
            doc_non_energy_per_ask_long_range_mean
            + doc_energy_per_ask_long_range_mean
            + doc_energy_carbon_tax_per_ask_long_range_mean
            - doc_energy_subsidy_per_ask_long_range_mean
            + doc_energy_tax_per_ask_long_range_mean
        )

        # Total average
        doc_total_per_ask_mean = (
            doc_non_energy_per_ask_mean
            + doc_energy_per_ask_mean
            + doc_energy_carbon_tax_per_ask_mean
            - doc_energy_subsidy_per_ask_mean
            + doc_energy_tax_per_ask_mean
        )

        self.df.loc[:, "doc_total_per_ask_short_range_dropin_fuel"] = (
            doc_total_per_ask_short_range_dropin_fuel
        )
        self.df.loc[:, "doc_total_per_ask_medium_range_dropin_fuel"] = (
            doc_total_per_ask_medium_range_dropin_fuel
        )
        self.df.loc[:, "doc_total_per_ask_long_range_dropin_fuel"] = (
            doc_total_per_ask_long_range_dropin_fuel
        )
        self.df.loc[:, "doc_total_per_ask_short_range_hydrogen"] = (
            doc_total_per_ask_short_range_hydrogen
        )
        self.df.loc[:, "doc_total_per_ask_medium_range_hydrogen"] = (
            doc_total_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "doc_total_per_ask_long_range_hydrogen"] = (
            doc_total_per_ask_long_range_hydrogen
        )
        self.df.loc[:, "doc_total_per_ask_short_range_electric"] = (
            doc_total_per_ask_short_range_electric
        )
        self.df.loc[:, "doc_total_per_ask_medium_range_electric"] = (
            doc_total_per_ask_medium_range_electric
        )
        self.df.loc[:, "doc_total_per_ask_long_range_electric"] = (
            doc_total_per_ask_long_range_electric
        )
        self.df.loc[:, "doc_total_per_ask_short_range_mean"] = doc_total_per_ask_short_range_mean
        self.df.loc[:, "doc_total_per_ask_medium_range_mean"] = doc_total_per_ask_medium_range_mean
        self.df.loc[:, "doc_total_per_ask_long_range_mean"] = doc_total_per_ask_long_range_mean
        self.df.loc[:, "doc_total_per_ask_mean"] = doc_total_per_ask_mean

        return (
            doc_total_per_ask_short_range_dropin_fuel,
            doc_total_per_ask_medium_range_dropin_fuel,
            doc_total_per_ask_long_range_dropin_fuel,
            doc_total_per_ask_short_range_hydrogen,
            doc_total_per_ask_medium_range_hydrogen,
            doc_total_per_ask_long_range_hydrogen,
            doc_total_per_ask_short_range_electric,
            doc_total_per_ask_medium_range_electric,
            doc_total_per_ask_long_range_electric,
            doc_total_per_ask_short_range_mean,
            doc_total_per_ask_medium_range_mean,
            doc_total_per_ask_long_range_mean,
            doc_total_per_ask_mean,
        )

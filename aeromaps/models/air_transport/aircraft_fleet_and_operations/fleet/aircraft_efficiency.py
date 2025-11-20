"""
aicraft_efficiency
=====================

This module contains models to compute aircraft efficiency, either using simple models or outputs from generic fleet model.
"""

from typing import Tuple
from numbers import Number

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function


class PassengerAircraftEfficiencySimpleShares(AeroMAPSModel):
    """
    Class to compute energy consumption per ASK (without operations) using simple annual improvement rates.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_efficiency_simple_shares' by default).
    """

    def __init__(self, name="passenger_aircraft_efficiency_simple_shares", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_init: pd.Series,
        ask_init: pd.Series,
        short_range_energy_share_2019: float,
        medium_range_energy_share_2019: float,
        long_range_energy_share_2019: float,
        short_range_rpk_share_2019: float,
        medium_range_rpk_share_2019: float,
        long_range_rpk_share_2019: float,
        energy_per_ask_short_range_dropin_fuel_gain_reference_years: list,
        energy_per_ask_short_range_dropin_fuel_gain_reference_years_values: list,
        energy_per_ask_medium_range_dropin_fuel_gain_reference_years: list,
        energy_per_ask_medium_range_dropin_fuel_gain_reference_years_values: list,
        energy_per_ask_long_range_dropin_fuel_gain_reference_years: list,
        energy_per_ask_long_range_dropin_fuel_gain_reference_years_values: list,
        relative_energy_per_ask_hydrogen_wrt_dropin_short_range_reference_years: list,
        relative_energy_per_ask_hydrogen_wrt_dropin_short_range_reference_years_values: list,
        relative_energy_per_ask_hydrogen_wrt_dropin_medium_range_reference_years: list,
        relative_energy_per_ask_hydrogen_wrt_dropin_medium_range_reference_years_values: list,
        relative_energy_per_ask_hydrogen_wrt_dropin_long_range_reference_years: list,
        relative_energy_per_ask_hydrogen_wrt_dropin_long_range_reference_years_values: list,
        relative_energy_per_ask_electric_wrt_dropin_short_range_reference_years: list,
        relative_energy_per_ask_electric_wrt_dropin_short_range_reference_years_values: list,
        relative_energy_per_ask_electric_wrt_dropin_medium_range_reference_years: list,
        relative_energy_per_ask_electric_wrt_dropin_medium_range_reference_years_values: list,
        relative_energy_per_ask_electric_wrt_dropin_long_range_reference_years: list,
        relative_energy_per_ask_electric_wrt_dropin_long_range_reference_years_values: list,
        hydrogen_final_market_share_short_range: float,
        hydrogen_introduction_year_short_range: Number,
        hydrogen_final_market_share_medium_range: float,
        hydrogen_introduction_year_medium_range: Number,
        hydrogen_final_market_share_long_range: float,
        hydrogen_introduction_year_long_range: Number,
        electric_final_market_share_short_range: float,
        electric_introduction_year_short_range: Number,
        electric_final_market_share_medium_range: float,
        electric_introduction_year_medium_range: Number,
        electric_final_market_share_long_range: float,
        electric_introduction_year_long_range: Number,
        fleet_renewal_duration: float,
        covid_energy_intensity_per_ask_increase_2020: float,
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
    ]:
        """
        Compute energy consumption per ASK (without operations) using simple annual improvement rates.

        Parameters
        ----------
        energy_consumption_init
            Historical energy consumption of aviation over 2000-2019 [MJ].
        ask_init
            Historical number of Available Seat Kilometer (ASK) over 2000-2019 [ASK].
        short_range_energy_share_2019
            Share of aviation energy consumed by passenger short-range market in 2019 [%].
        medium_range_energy_share_2019
            Share of aviation energy consumed by passenger medium-range market in 2019 [%].
        long_range_energy_share_2019
            Share of aviation energy consumed by passenger long-range market in 2019 [%].
        short_range_rpk_share_2019
            Share of RPK from short-range market in 2019 [%].
        medium_range_rpk_share_2019
            Share of RPK from medium-range market in 2019 [%].
        long_range_rpk_share_2019
            Share of RPK from long-range market in 2019 [%].
        energy_per_ask_short_range_dropin_fuel_gain_reference_years
            Reference years for the mean annual efficiency gains in terms of energy consumption per ASK for short-range drop-in fuel aircraft [yr].
        energy_per_ask_short_range_dropin_fuel_gain_reference_years_values
            Mean annual efficiency gains in terms of energy consumption per ASK for short-range drop-in fuel aircraft for the reference years [%].
        energy_per_ask_medium_range_dropin_fuel_gain_reference_years
            Reference years for the mean annual efficiency gains in terms of energy consumption per ASK for medium-range drop-in fuel aircraft [yr].
        energy_per_ask_medium_range_dropin_fuel_gain_reference_years_values
            Mean annual efficiency gains in terms of energy consumption per ASK for medium-range drop-in fuel aircraft for the reference years [%].
        energy_per_ask_long_range_dropin_fuel_gain_reference_years
            Reference years for the mean annual efficiency gains in terms of energy consumption per ASK for long-range drop-in fuel aircraft [yr].
        energy_per_ask_long_range_dropin_fuel_gain_reference_years_values
            Mean annual efficiency gains in terms of energy consumption per ASK for long-range drop-in fuel aircraft for the reference years [%].
        relative_energy_per_ask_hydrogen_wrt_dropin_short_range_reference_years
            Reference years for the relative energy consumption per ASK of hydrogen aircraft with respect to drop-in aircraft for passenger short-range market [yr].
        relative_energy_per_ask_hydrogen_wrt_dropin_short_range_reference_years_values
            Relative energy consumption per ASK of hydrogen aircraft with respect to drop-in aircraft for passenger short-range market for the reference years [-].
        relative_energy_per_ask_hydrogen_wrt_dropin_medium_range_reference_years
            Reference years for the relative energy consumption per ASK of hydrogen aircraft with respect to drop-in aircraft for passenger medium-range market [yr].
        relative_energy_per_ask_hydrogen_wrt_dropin_medium_range_reference_years_values
            Relative energy consumption per ASK of hydrogen aircraft with respect to drop-in aircraft for passenger medium-range market for the reference years [-].
        relative_energy_per_ask_hydrogen_wrt_dropin_long_range_reference_years
            Reference years for the relative energy consumption per ASK of hydrogen aircraft with respect to drop-in aircraft for passenger long-range market [yr].
        relative_energy_per_ask_hydrogen_wrt_dropin_long_range_reference_years_values
            Relative energy consumption per ASK of hydrogen aircraft with respect to drop-in aircraft for passenger long-range market for the reference years [-].
        relative_energy_per_ask_electric_wrt_dropin_short_range_reference_years
            Reference years for the relative energy consumption per ASK of electric aircraft with respect to drop-in aircraft for passenger short-range market [yr].
        relative_energy_per_ask_electric_wrt_dropin_short_range_reference_years_values
            Relative energy consumption per ASK of electric aircraft with respect to drop-in aircraft for passenger short-range market for the reference years [-].
        relative_energy_per_ask_electric_wrt_dropin_medium_range_reference_years
            Reference years for the relative energy consumption per ASK of electric aircraft with respect to drop-in aircraft for passenger medium-range market [yr].
        relative_energy_per_ask_electric_wrt_dropin_medium_range_reference_years_values
            Relative energy consumption per ASK of electric aircraft with respect to drop-in aircraft for passenger medium-range market for the reference years [-].
        relative_energy_per_ask_electric_wrt_dropin_long_range_reference_years
            Reference years for the relative energy consumption per ASK of electric aircraft with respect to drop-in aircraft for passenger long-range market [yr].
        relative_energy_per_ask_electric_wrt_dropin_long_range_reference_years_values
            Relative energy consumption per ASK of electric aircraft with respect to drop-in aircraft for passenger long-range market for the reference years [-].
        hydrogen_final_market_share_short_range
            Share of hydrogen aircraft in the passenger short-range market [%].
        hydrogen_introduction_year_short_range
            Entry-Into-Service year of hydrogen aircraft for short-range market [yr].
        hydrogen_final_market_share_medium_range
            Share of hydrogen aircraft in the passenger medium-range market [%].
        hydrogen_introduction_year_medium_range
            Entry-Into-Service year of hydrogen aircraft for medium-range market [yr].
        hydrogen_final_market_share_long_range
            Share of hydrogen aircraft in the passenger long-range market [%].
        hydrogen_introduction_year_long_range
            Entry-Into-Service year of hydrogen aircraft for long-range market [yr].
        electric_final_market_share_short_range
            Share of electric aircraft in the passenger short-range market [%].
        electric_introduction_year_short_range
            Entry-Into-Service year of electric aircraft for short-range market [yr].
        electric_final_market_share_medium_range
            Share of electric aircraft in the passenger medium-range market [%].
        electric_introduction_year_medium_range
            Entry-Into-Service year of electric aircraft for medium-range market [yr].
        electric_final_market_share_long_range
            Share of electric aircraft in the passenger long-range market [%].
        electric_introduction_year_long_range
            Entry-Into-Service year of electric aircraft for long-range market [yr].
        fleet_renewal_duration
            Duration for renewing 98% of the aircraft fleet [yr].
        covid_energy_intensity_per_ask_increase_2020
            Increase in energy intensity per ASK due to Covid-19 for the start year [%].

        Returns
        -------
        energy_per_ask_without_operations_short_range_dropin_fuel
            Energy consumption per ASK for passenger short-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_dropin_fuel
            Energy consumption per ASK for passenger medium-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_dropin_fuel
            Energy consumption per ASK for passenger long-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_short_range_hydrogen
            Energy consumption per ASK for passenger short-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_hydrogen
            Energy consumption per ASK for passenger medium-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_hydrogen
            Energy consumption per ASK for passenger long-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_short_range_electric
            Energy consumption per ASK for passenger short-range market aircraft using electric propulsion without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_electric
            Energy consumption per ASK for passenger medium-range market aircraft using electric propulsion without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_electric
            Energy consumption per ASK for passenger long-range market aircraft using electric propulsion without considering operation improvements [MJ/ASK].
        ask_short_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from drop-in fuel aircraft [%].
        ask_medium_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from drop-in fuel aircraft [%].
        ask_long_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from drop-in fuel aircraft [%].
        ask_short_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from hydrogen aircraft [%].
        ask_medium_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from hydrogen aircraft [%].
        ask_long_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from hydrogen aircraft [%].
        ask_short_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from electric aircraft [%].
        ask_medium_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from electric aircraft [%].
        ask_long_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from electric aircraft [%].
        """

        # Initialization based on 2019 share
        energy_consumption_per_ask_init = energy_consumption_init / ask_init
        # Vectorised
        years_hist = np.arange(self.historic_start_year, self.prospection_start_year)
        idx_hist = pd.Index(years_hist)

        years_proj = np.arange(self.prospection_start_year, self.end_year + 1)
        idx_proj = pd.Index(years_proj)

        self.df.loc[idx_hist, "energy_per_ask_without_operations_short_range_dropin_fuel"] = (
            energy_consumption_per_ask_init.loc[idx_hist]
            * short_range_energy_share_2019
            / short_range_rpk_share_2019
        )
        self.df.loc[idx_hist, "energy_per_ask_without_operations_medium_range_dropin_fuel"] = (
            energy_consumption_per_ask_init.loc[idx_hist]
            * medium_range_energy_share_2019
            / medium_range_rpk_share_2019
        )
        self.df.loc[idx_hist, "energy_per_ask_without_operations_long_range_dropin_fuel"] = (
            energy_consumption_per_ask_init.loc[idx_hist]
            * long_range_energy_share_2019
            / long_range_rpk_share_2019
        )

        # Projections

        ## Drop-in

        energy_per_ask_short_range_dropin_fuel_gain = aeromaps_interpolation_function(
            self,
            energy_per_ask_short_range_dropin_fuel_gain_reference_years,
            energy_per_ask_short_range_dropin_fuel_gain_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "energy_per_ask_short_range_dropin_fuel_gain"] = (
            energy_per_ask_short_range_dropin_fuel_gain
        )
        energy_per_ask_medium_range_dropin_fuel_gain = aeromaps_interpolation_function(
            self,
            energy_per_ask_medium_range_dropin_fuel_gain_reference_years,
            energy_per_ask_medium_range_dropin_fuel_gain_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "energy_per_ask_medium_range_dropin_fuel_gain"] = (
            energy_per_ask_medium_range_dropin_fuel_gain
        )
        energy_per_ask_long_range_dropin_fuel_gain = aeromaps_interpolation_function(
            self,
            energy_per_ask_long_range_dropin_fuel_gain_reference_years,
            energy_per_ask_long_range_dropin_fuel_gain_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "energy_per_ask_long_range_dropin_fuel_gain"] = (
            energy_per_ask_long_range_dropin_fuel_gain
        )

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_dropin_fuel"] = (
                self.df.loc[k - 1, "energy_per_ask_without_operations_short_range_dropin_fuel"]
                * (1 - energy_per_ask_short_range_dropin_fuel_gain.loc[k] / 100)
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_dropin_fuel"] = (
                self.df.loc[k - 1, "energy_per_ask_without_operations_medium_range_dropin_fuel"]
                * (1 - energy_per_ask_medium_range_dropin_fuel_gain.loc[k] / 100)
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_dropin_fuel"] = (
                self.df.loc[k - 1, "energy_per_ask_without_operations_long_range_dropin_fuel"]
                * (1 - energy_per_ask_long_range_dropin_fuel_gain.loc[k] / 100)
            )

        self.df.loc[2020, "energy_per_ask_without_operations_short_range_dropin_fuel"] = (
            self.df.loc[2019, "energy_per_ask_without_operations_short_range_dropin_fuel"]
            * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)
        )
        self.df.loc[2020, "energy_per_ask_without_operations_medium_range_dropin_fuel"] = (
            self.df.loc[2019, "energy_per_ask_without_operations_medium_range_dropin_fuel"]
            * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)
        )
        self.df.loc[2020, "energy_per_ask_without_operations_long_range_dropin_fuel"] = self.df.loc[
            2019, "energy_per_ask_without_operations_long_range_dropin_fuel"
        ] * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)

        energy_per_ask_without_operations_short_range_dropin_fuel = self.df[
            "energy_per_ask_without_operations_short_range_dropin_fuel"
        ]
        energy_per_ask_without_operations_medium_range_dropin_fuel = self.df[
            "energy_per_ask_without_operations_medium_range_dropin_fuel"
        ]
        energy_per_ask_without_operations_long_range_dropin_fuel = self.df[
            "energy_per_ask_without_operations_long_range_dropin_fuel"
        ]

        ## Hydrogen

        relative_energy_per_ask_hydrogen_wrt_dropin_short_range = aeromaps_interpolation_function(
            self,
            relative_energy_per_ask_hydrogen_wrt_dropin_short_range_reference_years,
            relative_energy_per_ask_hydrogen_wrt_dropin_short_range_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "relative_energy_per_ask_hydrogen_wrt_dropin_short_range"] = (
            relative_energy_per_ask_hydrogen_wrt_dropin_short_range
        )
        relative_energy_per_ask_hydrogen_wrt_dropin_medium_range = aeromaps_interpolation_function(
            self,
            relative_energy_per_ask_hydrogen_wrt_dropin_medium_range_reference_years,
            relative_energy_per_ask_hydrogen_wrt_dropin_medium_range_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "relative_energy_per_ask_hydrogen_wrt_dropin_medium_range"] = (
            relative_energy_per_ask_hydrogen_wrt_dropin_medium_range
        )
        relative_energy_per_ask_hydrogen_wrt_dropin_long_range = aeromaps_interpolation_function(
            self,
            relative_energy_per_ask_hydrogen_wrt_dropin_long_range_reference_years,
            relative_energy_per_ask_hydrogen_wrt_dropin_long_range_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "relative_energy_per_ask_hydrogen_wrt_dropin_long_range"] = (
            relative_energy_per_ask_hydrogen_wrt_dropin_long_range
        )

        # Années historiques : copie directe
        self.df.loc[idx_hist, "energy_per_ask_without_operations_short_range_hydrogen"] = (
            energy_per_ask_without_operations_short_range_dropin_fuel.loc[idx_hist]
        )
        self.df.loc[idx_hist, "energy_per_ask_without_operations_medium_range_hydrogen"] = (
            energy_per_ask_without_operations_medium_range_dropin_fuel.loc[idx_hist]
        )
        self.df.loc[idx_hist, "energy_per_ask_without_operations_long_range_hydrogen"] = (
            energy_per_ask_without_operations_long_range_dropin_fuel.loc[idx_hist]
        )
        # Années projections : vectorisé
        self.df.loc[idx_proj, "energy_per_ask_without_operations_short_range_hydrogen"] = (
            energy_per_ask_without_operations_short_range_dropin_fuel.loc[idx_proj]
            * self.df.loc[idx_proj, "relative_energy_per_ask_hydrogen_wrt_dropin_short_range"]
        )
        self.df.loc[idx_proj, "energy_per_ask_without_operations_medium_range_hydrogen"] = (
            energy_per_ask_without_operations_medium_range_dropin_fuel.loc[idx_proj]
            * self.df.loc[idx_proj, "relative_energy_per_ask_hydrogen_wrt_dropin_medium_range"]
        )
        self.df.loc[idx_proj, "energy_per_ask_without_operations_long_range_hydrogen"] = (
            energy_per_ask_without_operations_long_range_dropin_fuel.loc[idx_proj]
            * self.df.loc[idx_proj, "relative_energy_per_ask_hydrogen_wrt_dropin_long_range"]
        )

        energy_per_ask_without_operations_short_range_hydrogen = self.df[
            "energy_per_ask_without_operations_short_range_hydrogen"
        ]
        energy_per_ask_without_operations_medium_range_hydrogen = self.df[
            "energy_per_ask_without_operations_medium_range_hydrogen"
        ]
        energy_per_ask_without_operations_long_range_hydrogen = self.df[
            "energy_per_ask_without_operations_long_range_hydrogen"
        ]

        ## Electric

        relative_energy_per_ask_electric_wrt_dropin_short_range = aeromaps_interpolation_function(
            self,
            relative_energy_per_ask_electric_wrt_dropin_short_range_reference_years,
            relative_energy_per_ask_electric_wrt_dropin_short_range_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "relative_energy_per_ask_electric_wrt_dropin_short_range"] = (
            relative_energy_per_ask_electric_wrt_dropin_short_range
        )
        relative_energy_per_ask_electric_wrt_dropin_medium_range = aeromaps_interpolation_function(
            self,
            relative_energy_per_ask_electric_wrt_dropin_medium_range_reference_years,
            relative_energy_per_ask_electric_wrt_dropin_medium_range_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "relative_energy_per_ask_electric_wrt_dropin_medium_range"] = (
            relative_energy_per_ask_electric_wrt_dropin_medium_range
        )
        relative_energy_per_ask_electric_wrt_dropin_long_range = aeromaps_interpolation_function(
            self,
            relative_energy_per_ask_electric_wrt_dropin_long_range_reference_years,
            relative_energy_per_ask_electric_wrt_dropin_long_range_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "relative_energy_per_ask_electric_wrt_dropin_long_range"] = (
            relative_energy_per_ask_electric_wrt_dropin_long_range
        )

        self.df.loc[idx_hist, "energy_per_ask_without_operations_short_range_electric"] = (
            energy_per_ask_without_operations_short_range_dropin_fuel.loc[idx_hist]
        )
        self.df.loc[idx_hist, "energy_per_ask_without_operations_medium_range_electric"] = (
            energy_per_ask_without_operations_medium_range_dropin_fuel.loc[idx_hist]
        )
        self.df.loc[idx_hist, "energy_per_ask_without_operations_long_range_electric"] = (
            energy_per_ask_without_operations_long_range_dropin_fuel.loc[idx_hist]
        )
        self.df.loc[idx_proj, "energy_per_ask_without_operations_short_range_electric"] = (
            energy_per_ask_without_operations_short_range_dropin_fuel.loc[idx_proj]
            * self.df.loc[idx_proj, "relative_energy_per_ask_electric_wrt_dropin_short_range"]
        )
        self.df.loc[idx_proj, "energy_per_ask_without_operations_medium_range_electric"] = (
            energy_per_ask_without_operations_medium_range_dropin_fuel.loc[idx_proj]
            * self.df.loc[idx_proj, "relative_energy_per_ask_electric_wrt_dropin_medium_range"]
        )
        self.df.loc[idx_proj, "energy_per_ask_without_operations_long_range_electric"] = (
            energy_per_ask_without_operations_long_range_dropin_fuel.loc[idx_proj]
            * self.df.loc[idx_proj, "relative_energy_per_ask_electric_wrt_dropin_long_range"]
        )

        energy_per_ask_without_operations_short_range_electric = self.df[
            "energy_per_ask_without_operations_short_range_electric"
        ]
        energy_per_ask_without_operations_medium_range_electric = self.df[
            "energy_per_ask_without_operations_medium_range_electric"
        ]
        energy_per_ask_without_operations_long_range_electric = self.df[
            "energy_per_ask_without_operations_long_range_electric"
        ]

        # ASK Hydrogen

        years_all = np.arange(self.historic_start_year, self.end_year + 1)
        idx_all = pd.Index(years_all)

        # Hydrogen shares vectorisés
        self.df.loc[idx_all, "ask_short_range_hydrogen_share"] = self._simple_sigmoid_share(
            years_all,
            hydrogen_final_market_share_short_range,
            hydrogen_introduction_year_short_range,
            fleet_renewal_duration,
        )
        self.df.loc[idx_all, "ask_medium_range_hydrogen_share"] = self._simple_sigmoid_share(
            years_all,
            hydrogen_final_market_share_medium_range,
            hydrogen_introduction_year_medium_range,
            fleet_renewal_duration,
        )
        self.df.loc[idx_all, "ask_long_range_hydrogen_share"] = self._simple_sigmoid_share(
            years_all,
            hydrogen_final_market_share_long_range,
            hydrogen_introduction_year_long_range,
            fleet_renewal_duration,
        )

        ask_short_range_hydrogen_share = self.df["ask_short_range_hydrogen_share"]
        ask_medium_range_hydrogen_share = self.df["ask_medium_range_hydrogen_share"]
        ask_long_range_hydrogen_share = self.df["ask_long_range_hydrogen_share"]

        # ASK Electric

        # Electric shares vectorisés
        self.df.loc[idx_all, "ask_short_range_electric_share"] = self._simple_sigmoid_share(
            years_all,
            electric_final_market_share_short_range,
            electric_introduction_year_short_range,
            fleet_renewal_duration,
        )
        self.df.loc[idx_all, "ask_medium_range_electric_share"] = self._simple_sigmoid_share(
            years_all,
            electric_final_market_share_medium_range,
            electric_introduction_year_medium_range,
            fleet_renewal_duration,
        )
        self.df.loc[idx_all, "ask_long_range_electric_share"] = self._simple_sigmoid_share(
            years_all,
            electric_final_market_share_long_range,
            electric_introduction_year_long_range,
            fleet_renewal_duration,
        )

        ask_short_range_electric_share = self.df["ask_short_range_electric_share"]
        ask_medium_range_electric_share = self.df["ask_medium_range_electric_share"]
        ask_long_range_electric_share = self.df["ask_long_range_electric_share"]

        # ASK Drop-in fuel

        ask_short_range_dropin_fuel_share = (
            100 - ask_short_range_hydrogen_share - ask_short_range_electric_share
        )
        ask_medium_range_dropin_fuel_share = (
            100 - ask_medium_range_hydrogen_share - ask_medium_range_electric_share
        )
        ask_long_range_dropin_fuel_share = (
            100 - ask_long_range_hydrogen_share - ask_long_range_electric_share
        )
        self.df.loc[:, "ask_short_range_dropin_fuel_share"] = ask_short_range_dropin_fuel_share
        self.df.loc[:, "ask_medium_range_dropin_fuel_share"] = ask_medium_range_dropin_fuel_share
        self.df.loc[:, "ask_long_range_dropin_fuel_share"] = ask_long_range_dropin_fuel_share

        return (
            energy_per_ask_without_operations_short_range_dropin_fuel,
            energy_per_ask_without_operations_medium_range_dropin_fuel,
            energy_per_ask_without_operations_long_range_dropin_fuel,
            energy_per_ask_without_operations_short_range_hydrogen,
            energy_per_ask_without_operations_medium_range_hydrogen,
            energy_per_ask_without_operations_long_range_hydrogen,
            energy_per_ask_without_operations_short_range_electric,
            energy_per_ask_without_operations_medium_range_electric,
            energy_per_ask_without_operations_long_range_electric,
            ask_short_range_dropin_fuel_share,
            ask_medium_range_dropin_fuel_share,
            ask_long_range_dropin_fuel_share,
            ask_short_range_hydrogen_share,
            ask_medium_range_hydrogen_share,
            ask_long_range_hydrogen_share,
            ask_short_range_electric_share,
            ask_medium_range_electric_share,
            ask_long_range_electric_share,
        )

    @staticmethod
    def _simple_sigmoid_share(years, final_share, intro_year, fleet_renewal_duration):
        transition_year = intro_year + fleet_renewal_duration / 2
        share_limit = 0.02 * final_share
        share_param = np.log(100 / 2 - 1) / (fleet_renewal_duration / 2)
        share = final_share / (1 + np.exp(-share_param * (years - transition_year)))
        share = np.where(share < share_limit, 0, share)
        return share


class PassengerAircraftEfficiencySimpleASK(AeroMAPSModel):
    """
    Class to compute ASK for each aircraft type when using simple efficiency models.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_efficiency_simple_ask' by default).
    """

    def __init__(self, name="passenger_aircraft_efficiency_simple_ask", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        ask_short_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_long_range: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_long_range_hydrogen_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
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
        """
        Compute ASK breakdown by aircraft type and range.

        Parameters
        ----------
        ask_short_range
            Number of Available Seat Kilometre (ASK) for passenger short-range market [ASK].
        ask_medium_range
            Number of Available Seat Kilometre (ASK) for passenger medium-range market [ASK].
        ask_long_range
            Number of Available Seat Kilometre (ASK) for passenger long-range market [ASK].
        ask_short_range_hydrogen_share
            Share of Available Seat Kilometre (ASK) for passenger short-range market from hydrogen aircraft [%].
        ask_medium_range_hydrogen_share
            Share of Available Seat Kilometre (ASK) for passenger medium-range market from hydrogen aircraft [%].
        ask_long_range_hydrogen_share
            Share of Available Seat Kilometre (ASK) for passenger long-range market from hydrogen aircraft [%].
        ask_short_range_electric_share
            Share of Available Seat Kilometre (ASK) for passenger short-range market from electric aircraft [%].
        ask_medium_range_electric_share
            Share of Available Seat Kilometre (ASK) for passenger medium-range market from electric aircraft [%].
        ask_long_range_electric_share
            Share of Available Seat Kilometre (ASK) for passenger long-range market from electric aircraft [%].

        Returns
        -------
        ask_short_range_dropin_fuel
            ASK for short-range market from drop-in fuel aircraft [ASK].
        ask_medium_range_dropin_fuel
            ASK for medium-range market from drop-in fuel aircraft [ASK].
        ask_long_range_dropin_fuel
            ASK for long-range market from drop-in fuel aircraft [ASK].
        ask_short_range_hydrogen
            ASK for short-range market from hydrogen aircraft [ASK].
        ask_medium_range_hydrogen
            ASK for medium-range market from hydrogen aircraft [ASK].
        ask_long_range_hydrogen
            ASK for long-range market from hydrogen aircraft [ASK].
        ask_short_range_electric
            ASK for short-range market from electric aircraft [ASK].
        ask_medium_range_electric
            ASK for medium-range market from electric aircraft [ASK].
        ask_long_range_electric
            ASK for long-range market from electric aircraft [ASK].
        ask_dropin_fuel
            Total ASK for drop-in fuel aircraft across ranges [ASK].
        ask_hydrogen
            Total ASK for hydrogen aircraft across ranges [ASK].
        ask_electric
            Total ASK for electric aircraft across ranges [ASK].
        """

        # ASK Hydrogen
        ask_short_range_hydrogen = ask_short_range * ask_short_range_hydrogen_share / 100
        ask_medium_range_hydrogen = ask_medium_range * ask_medium_range_hydrogen_share / 100
        ask_long_range_hydrogen = ask_long_range * ask_long_range_hydrogen_share / 100
        self.df.loc[:, "ask_short_range_hydrogen"] = ask_short_range_hydrogen
        self.df.loc[:, "ask_medium_range_hydrogen"] = ask_medium_range_hydrogen
        self.df.loc[:, "ask_long_range_hydrogen"] = ask_long_range_hydrogen

        # ASK Electric

        ask_short_range_electric = ask_short_range * ask_short_range_electric_share / 100
        ask_medium_range_electric = ask_medium_range * ask_medium_range_electric_share / 100
        ask_long_range_electric = ask_long_range * ask_long_range_electric_share / 100
        self.df.loc[:, "ask_short_range_electric"] = ask_short_range_electric
        self.df.loc[:, "ask_medium_range_electric"] = ask_medium_range_electric
        self.df.loc[:, "ask_long_range_electric"] = ask_long_range_electric

        # ASK Drop-in fuel

        ask_short_range_dropin_fuel = (
            ask_short_range - ask_short_range_hydrogen - ask_short_range_electric
        )
        ask_medium_range_dropin_fuel = (
            ask_medium_range - ask_medium_range_hydrogen - ask_medium_range_electric
        )
        ask_long_range_dropin_fuel = (
            ask_long_range - ask_long_range_hydrogen - ask_long_range_electric
        )
        self.df.loc[:, "ask_short_range_dropin_fuel"] = ask_short_range_dropin_fuel
        self.df.loc[:, "ask_medium_range_dropin_fuel"] = ask_medium_range_dropin_fuel
        self.df.loc[:, "ask_long_range_dropin_fuel"] = ask_long_range_dropin_fuel

        # Total ASK

        ask_dropin_fuel = (
            ask_short_range_dropin_fuel + ask_medium_range_dropin_fuel + ask_long_range_dropin_fuel
        )
        ask_hydrogen = (
            ask_short_range_hydrogen + ask_medium_range_hydrogen + ask_long_range_hydrogen
        )
        ask_electric = (
            ask_short_range_electric + ask_medium_range_electric + ask_long_range_electric
        )

        self.df.loc[:, "ask_dropin_fuel"] = ask_dropin_fuel
        self.df.loc[:, "ask_hydrogen"] = ask_hydrogen
        self.df.loc[:, "ask_electric"] = ask_electric

        return (
            ask_short_range_dropin_fuel,
            ask_medium_range_dropin_fuel,
            ask_long_range_dropin_fuel,
            ask_short_range_hydrogen,
            ask_medium_range_hydrogen,
            ask_long_range_hydrogen,
            ask_short_range_electric,
            ask_medium_range_electric,
            ask_long_range_electric,
            ask_dropin_fuel,
            ask_hydrogen,
            ask_electric,
        )


class PassengerAircraftEfficiencyComplex(AeroMAPSModel):
    """
    Class to compute energy consumption per ASK (without operations) using complex models.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_efficiency_complex' by default).

    Attributes
    ----------
    fleet_model : FleetModel(AeroMAPSModel)
        FleetModel instance to be used for complex efficiency computations.
    """

    def __init__(self, name="passenger_aircraft_efficiency_complex", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = None

    def compute(
        self,
        dummy_fleet_model_output: np.ndarray,
        energy_consumption_init: pd.Series,
        ask: pd.Series,
        short_range_energy_share_2019: float,
        medium_range_energy_share_2019: float,
        long_range_energy_share_2019: float,
        short_range_rpk_share_2019: float,
        medium_range_rpk_share_2019: float,
        long_range_rpk_share_2019: float,
        covid_energy_intensity_per_ask_increase_2020: float,
        ask_short_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_long_range: pd.Series,
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
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        """
        Compute energy consumption per ASK (without operations) using complex fleet-model outputs.

        Parameters
        ----------
        dummy_fleet_model_output
            Dummy fleet model output to ensure the prior execution of the generic fleet model [-].
        energy_consumption_init
            Historical energy consumption of aviation over 2000-2019 [MJ].
        ask
            Number of Available Seat Kilometre (ASK) for all commercial air transport [ASK].
        short_range_energy_share_2019
            Share of aviation energy consumed by passenger short-range market in 2019 [%].
        medium_range_energy_share_2019
            Share of aviation energy consumed by passenger medium-range market in 2019 [%].
        long_range_energy_share_2019
            Share of aviation energy consumed by passenger long-range market in 2019 [%].
        short_range_rpk_share_2019
            Share of RPK from short-range market in 2019 [%].
        medium_range_rpk_share_2019
            Share of RPK from medium-range market in 2019 [%].
        long_range_rpk_share_2019
            Share of RPK from long-range market in 2019 [%].
        covid_energy_intensity_per_ask_increase_2020
            Increase in energy intensity per ASK due to Covid-19 for the start year [%].
        ask_short_range
            Number of Available Seat Kilometre (ASK) for passenger short-range market [ASK].
        ask_medium_range
            Number of Available Seat Kilometre (ASK) for passenger medium-range market [ASK].
        ask_long_range
            Number of Available Seat Kilometre (ASK) for passenger long-range market [ASK].

        Returns
        -------
        energy_per_ask_without_operations_short_range_dropin_fuel
            Energy consumption per ASK for passenger short-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_dropin_fuel
            Energy consumption per ASK for passenger medium-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_dropin_fuel
            Energy consumption per ASK for passenger long-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_short_range_hydrogen
            Energy consumption per ASK for passenger short-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_hydrogen
            Energy consumption per ASK for passenger medium-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_hydrogen
            Energy consumption per ASK for passenger long-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_short_range_electric
            Energy consumption per ASK for passenger short-range market aircraft using electric propulsion without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_electric
            Energy consumption per ASK for passenger medium-range market aircraft using electric propulsion without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_electric
            Energy consumption per ASK for passenger long-range market aircraft using electric propulsion without considering operation improvements [MJ/ASK].
        ask_short_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from drop-in fuel aircraft [%].
        ask_medium_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from drop-in fuel aircraft [%].
        ask_long_range_dropin_fuel_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from drop-in fuel aircraft [%].
        ask_short_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from hydrogen aircraft [%].
        ask_medium_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from hydrogen aircraft [%].
        ask_long_range_hydrogen_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from hydrogen aircraft [%].
        ask_short_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger short-range market from electric aircraft [%].
        ask_medium_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger medium-range market from electric aircraft [%].
        ask_long_range_electric_share
            Share of Available Seat Kilometer (ASK) for passenger long-range market from electric aircraft [%].
        ask_short_range_dropin_fuel
            ASK for short-range market from drop-in fuel aircraft [ASK].
        ask_medium_range_dropin_fuel
            ASK for medium-range market from drop-in fuel aircraft [ASK].
        ask_long_range_dropin_fuel
            ASK for long-range market from drop-in fuel aircraft [ASK].
        ask_short_range_hydrogen
            ASK for short-range market from hydrogen aircraft [ASK].
        ask_medium_range_hydrogen
            ASK for medium-range market from hydrogen aircraft [ASK].
        ask_long_range_hydrogen
            ASK for long-range market from hydrogen aircraft [ASK].
        ask_short_range_electric
            ASK for short-range market from electric aircraft [ASK].
        ask_medium_range_electric
            ASK for medium-range market from electric aircraft [ASK].
        ask_long_range_electric
            ASK for long-range market from electric aircraft [ASK].
        """

        # Pull outputs produced by the external fleet model
        ask_short_range_dropin_fuel_share = self.fleet_model.df["Short Range:share:dropin_fuel"]
        ask_medium_range_dropin_fuel_share = self.fleet_model.df["Medium Range:share:dropin_fuel"]
        ask_long_range_dropin_fuel_share = self.fleet_model.df["Long Range:share:dropin_fuel"]
        ask_short_range_hydrogen_share = self.fleet_model.df["Short Range:share:hydrogen"]
        ask_medium_range_hydrogen_share = self.fleet_model.df["Medium Range:share:hydrogen"]
        ask_long_range_hydrogen_share = self.fleet_model.df["Long Range:share:hydrogen"]
        ask_short_range_electric_share = self.fleet_model.df["Short Range:share:electric"]
        ask_medium_range_electric_share = self.fleet_model.df["Medium Range:share:electric"]
        ask_long_range_electric_share = self.fleet_model.df["Long Range:share:electric"]

        energy_per_ask_without_operations_short_range_dropin_fuel = self.fleet_model.df[
            "Short Range:energy_consumption:dropin_fuel"
        ]
        energy_per_ask_without_operations_medium_range_dropin_fuel = self.fleet_model.df[
            "Medium Range:energy_consumption:dropin_fuel"
        ]
        energy_per_ask_without_operations_long_range_dropin_fuel = self.fleet_model.df[
            "Long Range:energy_consumption:dropin_fuel"
        ]
        energy_per_ask_without_operations_short_range_hydrogen = self.fleet_model.df[
            "Short Range:energy_consumption:hydrogen"
        ]
        energy_per_ask_without_operations_medium_range_hydrogen = self.fleet_model.df[
            "Medium Range:energy_consumption:hydrogen"
        ]
        energy_per_ask_without_operations_long_range_hydrogen = self.fleet_model.df[
            "Long Range:energy_consumption:hydrogen"
        ]
        energy_per_ask_without_operations_short_range_electric = self.fleet_model.df[
            "Short Range:energy_consumption:electric"
        ]
        energy_per_ask_without_operations_medium_range_electric = self.fleet_model.df[
            "Medium Range:energy_consumption:electric"
        ]
        energy_per_ask_without_operations_long_range_electric = self.fleet_model.df[
            "Long Range:energy_consumption:electric"
        ]

        # Drop-in - Initialization based on 2019 share - To check for consistency
        energy_consumption_per_ask_init = energy_consumption_init / ask

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_dropin_fuel"] = (
                energy_consumption_per_ask_init.loc[k]
                * short_range_energy_share_2019
                / short_range_rpk_share_2019
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_dropin_fuel"] = (
                energy_consumption_per_ask_init.loc[k]
                * medium_range_energy_share_2019
                / medium_range_rpk_share_2019
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_dropin_fuel"] = (
                energy_consumption_per_ask_init.loc[k]
                * long_range_energy_share_2019
                / long_range_rpk_share_2019
            )
        # Share
        self.df["ask_short_range_dropin_fuel_share"] = 100.0
        self.df["ask_medium_range_dropin_fuel_share"] = 100.0
        self.df["ask_long_range_dropin_fuel_share"] = 100.0

        # Hydrogen initialization
        # Energy consumption
        self.df["energy_per_ask_without_operations_short_range_hydrogen"] = 0.0
        self.df["energy_per_ask_without_operations_medium_range_hydrogen"] = 0.0
        self.df["energy_per_ask_without_operations_long_range_hydrogen"] = 0.0

        # Share
        self.df["ask_short_range_hydrogen_share"] = 0.0
        self.df["ask_medium_range_hydrogen_share"] = 0.0
        self.df["ask_long_range_hydrogen_share"] = 0.0

        # Electric initialization
        # Energy consumption
        self.df["energy_per_ask_without_operations_short_range_electric"] = 0.0
        self.df["energy_per_ask_without_operations_medium_range_electric"] = 0.0
        self.df["energy_per_ask_without_operations_long_range_electric"] = 0.0

        # Share
        self.df["ask_short_range_electric_share"] = 0.0
        self.df["ask_medium_range_electric_share"] = 0.0
        self.df["ask_long_range_electric_share"] = 0.0

        # Hybrid-electric initialization
        # Energy consumption
        self.df["energy_per_ask_without_operations_short_range_hybrid_electric"] = 0.0
        self.df["energy_per_ask_without_operations_medium_range_hybrid_electric"] = 0.0
        self.df["energy_per_ask_without_operations_long_range_hybrid_electric"] = 0.0

        # Share
        self.df["ask_short_range_hybrid_electric_share"] = 0.0
        self.df["ask_medium_range_hybrid_electric_share"] = 0.0
        self.df["ask_long_range_hybrid_electric_share"] = 0.0

        # Drop-in - Projections
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_dropin_fuel"] = (
                energy_per_ask_without_operations_short_range_dropin_fuel.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_dropin_fuel"] = (
                energy_per_ask_without_operations_medium_range_dropin_fuel.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_dropin_fuel"] = (
                energy_per_ask_without_operations_long_range_dropin_fuel.loc[k]
            )

        self.df.loc[2020, "energy_per_ask_without_operations_short_range_dropin_fuel"] = (
            self.df.loc[2019, "energy_per_ask_without_operations_short_range_dropin_fuel"]
            * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)
        )
        self.df.loc[2020, "energy_per_ask_without_operations_medium_range_dropin_fuel"] = (
            self.df.loc[2019, "energy_per_ask_without_operations_medium_range_dropin_fuel"]
            * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)
        )
        self.df.loc[2020, "energy_per_ask_without_operations_long_range_dropin_fuel"] = self.df.loc[
            2019, "energy_per_ask_without_operations_long_range_dropin_fuel"
        ] * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)

        energy_per_ask_without_operations_short_range_dropin_fuel = self.df[
            "energy_per_ask_without_operations_short_range_dropin_fuel"
        ]
        energy_per_ask_without_operations_medium_range_dropin_fuel = self.df[
            "energy_per_ask_without_operations_medium_range_dropin_fuel"
        ]
        energy_per_ask_without_operations_long_range_dropin_fuel = self.df[
            "energy_per_ask_without_operations_long_range_dropin_fuel"
        ]

        # Hydrogen
        for k in range(self.prospection_start_year + 1, self.end_year + 1):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_hydrogen"] = (
                energy_per_ask_without_operations_short_range_hydrogen.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_hydrogen"] = (
                energy_per_ask_without_operations_medium_range_hydrogen.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_hydrogen"] = (
                energy_per_ask_without_operations_long_range_hydrogen.loc[k]
            )

        energy_per_ask_without_operations_short_range_hydrogen = self.df[
            "energy_per_ask_without_operations_short_range_hydrogen"
        ]
        energy_per_ask_without_operations_medium_range_hydrogen = self.df[
            "energy_per_ask_without_operations_medium_range_hydrogen"
        ]
        energy_per_ask_without_operations_long_range_hydrogen = self.df[
            "energy_per_ask_without_operations_long_range_hydrogen"
        ]

        # Electric
        for k in range(self.prospection_start_year + 1, self.end_year + 1):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_electric"] = (
                energy_per_ask_without_operations_short_range_electric.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_electric"] = (
                energy_per_ask_without_operations_medium_range_electric.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_electric"] = (
                energy_per_ask_without_operations_long_range_electric.loc[k]
            )

        energy_per_ask_without_operations_short_range_electric = self.df[
            "energy_per_ask_without_operations_short_range_electric"
        ]
        energy_per_ask_without_operations_medium_range_electric = self.df[
            "energy_per_ask_without_operations_medium_range_electric"
        ]
        energy_per_ask_without_operations_long_range_electric = self.df[
            "energy_per_ask_without_operations_long_range_electric"
        ]

        # Share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_short_range_dropin_fuel_share"
        ] = ask_short_range_dropin_fuel_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_medium_range_dropin_fuel_share"
        ] = ask_medium_range_dropin_fuel_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_long_range_dropin_fuel_share"
        ] = ask_long_range_dropin_fuel_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_short_range_hydrogen_share"
        ] = ask_short_range_hydrogen_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_medium_range_hydrogen_share"
        ] = ask_medium_range_hydrogen_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_long_range_hydrogen_share"
        ] = ask_long_range_hydrogen_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_short_range_electric_share"
        ] = ask_short_range_electric_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_medium_range_electric_share"
        ] = ask_medium_range_electric_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_long_range_electric_share"
        ] = ask_long_range_electric_share
        # ASK
        ask_short_range_dropin_fuel = (
            ask_short_range * self.df["ask_short_range_dropin_fuel_share"] / 100
        )
        ask_medium_range_dropin_fuel = (
            ask_medium_range * self.df["ask_medium_range_dropin_fuel_share"] / 100
        )
        ask_long_range_dropin_fuel = (
            ask_long_range * self.df["ask_long_range_dropin_fuel_share"] / 100
        )
        ask_short_range_hydrogen = ask_short_range * self.df["ask_short_range_hydrogen_share"] / 100
        ask_medium_range_hydrogen = (
            ask_medium_range * self.df["ask_medium_range_hydrogen_share"] / 100
        )
        ask_long_range_hydrogen = ask_long_range * self.df["ask_long_range_hydrogen_share"] / 100
        ask_short_range_electric = ask_short_range * self.df["ask_short_range_electric_share"] / 100
        ask_medium_range_electric = (
            ask_medium_range * self.df["ask_medium_range_electric_share"] / 100
        )
        ask_long_range_electric = ask_long_range * self.df["ask_long_range_electric_share"] / 100

        self.df.loc[:, "ask_short_range_dropin_fuel"] = ask_short_range_dropin_fuel
        self.df.loc[:, "ask_medium_range_dropin_fuel"] = ask_medium_range_dropin_fuel
        self.df.loc[:, "ask_long_range_dropin_fuel"] = ask_long_range_dropin_fuel
        self.df.loc[:, "ask_short_range_hydrogen"] = ask_short_range_hydrogen
        self.df.loc[:, "ask_medium_range_hydrogen"] = ask_medium_range_hydrogen
        self.df.loc[:, "ask_long_range_hydrogen"] = ask_long_range_hydrogen
        self.df.loc[:, "ask_short_range_electric"] = ask_short_range_electric
        self.df.loc[:, "ask_medium_range_electric"] = ask_medium_range_electric
        self.df.loc[:, "ask_long_range_electric"] = ask_long_range_electric

        ask_dropin_fuel = (
            ask_short_range_dropin_fuel + ask_medium_range_dropin_fuel + ask_long_range_dropin_fuel
        )
        ask_hydrogen = (
            ask_short_range_hydrogen + ask_medium_range_hydrogen + ask_long_range_hydrogen
        )
        ask_electric = (
            ask_short_range_electric + ask_medium_range_electric + ask_long_range_electric
        )

        self.df.loc[:, "ask_dropin_fuel"] = ask_dropin_fuel
        self.df.loc[:, "ask_hydrogen"] = ask_hydrogen
        self.df.loc[:, "ask_electric"] = ask_electric

        return (
            energy_per_ask_without_operations_short_range_dropin_fuel,
            energy_per_ask_without_operations_medium_range_dropin_fuel,
            energy_per_ask_without_operations_long_range_dropin_fuel,
            energy_per_ask_without_operations_short_range_hydrogen,
            energy_per_ask_without_operations_medium_range_hydrogen,
            energy_per_ask_without_operations_long_range_hydrogen,
            energy_per_ask_without_operations_short_range_electric,
            energy_per_ask_without_operations_medium_range_electric,
            energy_per_ask_without_operations_long_range_electric,
            ask_short_range_dropin_fuel_share,
            ask_medium_range_dropin_fuel_share,
            ask_long_range_dropin_fuel_share,
            ask_short_range_hydrogen_share,
            ask_medium_range_hydrogen_share,
            ask_long_range_hydrogen_share,
            ask_short_range_electric_share,
            ask_medium_range_electric_share,
            ask_long_range_electric_share,
            ask_short_range_dropin_fuel,
            ask_medium_range_dropin_fuel,
            ask_long_range_dropin_fuel,
            ask_short_range_hydrogen,
            ask_medium_range_hydrogen,
            ask_long_range_hydrogen,
            ask_short_range_electric,
            ask_medium_range_electric,
            ask_long_range_electric,
            ask_dropin_fuel,
            ask_hydrogen,
            ask_electric,
        )


class FreightAircraftEfficiency(AeroMAPSModel):
    """Class to compute energy consumption per RTK (without operations) for freight aircraft.

    Parameters
    ----------
    name : str
        Name of the model instance ('freight_aircraft_efficiency' by default).
    """

    def __init__(self, name="freight_aircraft_efficiency", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_init: pd.Series,
        rtk: pd.Series,
        freight_energy_share_2019: float,
        energy_per_ask_without_operations_short_range_dropin_fuel: pd.Series,
        energy_per_ask_without_operations_medium_range_dropin_fuel: pd.Series,
        energy_per_ask_without_operations_long_range_dropin_fuel: pd.Series,
        energy_per_ask_without_operations_short_range_hydrogen: pd.Series,
        energy_per_ask_without_operations_medium_range_hydrogen: pd.Series,
        energy_per_ask_without_operations_long_range_hydrogen: pd.Series,
        energy_per_ask_without_operations_short_range_electric: pd.Series,
        energy_per_ask_without_operations_medium_range_electric: pd.Series,
        energy_per_ask_without_operations_long_range_electric: pd.Series,
        ask: pd.Series,
        ask_short_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_long_range: pd.Series,
        ask_short_range_dropin_fuel: pd.Series,
        ask_medium_range_dropin_fuel: pd.Series,
        ask_long_range_dropin_fuel: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_long_range_hydrogen_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        covid_energy_intensity_per_ask_increase_2020: float,
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
    ]:
        """
        Compute energy consumption per RTK (without operations) for freight aircraft.

        Parameters
        ----------
        energy_consumption_init
            Historical energy consumption of aviation over 2000-2019 [MJ].
        rtk
            Number of Revenue Tonne Kilometer (RTK) for freight air transport [RTK].
        freight_energy_share_2019
            Share of aviation energy consumed by freight market in 2019 [%].
        energy_per_ask_without_operations_short_range_dropin_fuel
            Energy consumption per ASK for passenger short-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_dropin_fuel
            Energy consumption per ASK for passenger medium-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_dropin_fuel
            Energy consumption per ASK for passenger long-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_short_range_hydrogen
            Energy consumption per ASK for passenger short-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_hydrogen
            Energy consumption per ASK for passenger medium-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_hydrogen
            Energy consumption per ASK for passenger long-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_short_range_electric
            Energy consumption per ASK for passenger short-range market aircraft using electric propulsion without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_electric
            Energy consumption per ASK for passenger medium-range market aircraft using electric propulsion without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_electric
            Energy consumption per ASK for passenger long-range market aircraft using electric propulsion without considering operation improvements [MJ/ASK].
        ask
            Number of Available Seat Kilometre (ASK) for all commercial air transport [ASK].
        ask_short_range
            Number of Available Seat Kilometre (ASK) for passenger short-range market [ASK].
        ask_medium_range
            Number of Available Seat Kilometre (ASK) for passenger medium-range market [ASK].
        ask_long_range
            Number of Available Seat Kilometre (ASK) for passenger long-range market [ASK].
        ask_short_range_dropin_fuel
            ASK for short-range market from drop-in fuel aircraft [ASK].
        ask_medium_range_dropin_fuel
            ASK for medium-range market from drop-in fuel aircraft [ASK].
        ask_long_range_dropin_fuel
            ASK for long-range market from drop-in fuel aircraft [ASK].
        ask_short_range_hydrogen_share
            Share of Available Seat Kilometre (ASK) for passenger short-range market from hydrogen aircraft [%].
        ask_medium_range_hydrogen_share
            Share of Available Seat Kilometre (ASK) for passenger medium-range market from hydrogen aircraft [%].
        ask_long_range_hydrogen_share
            Share of Available Seat Kilometre (ASK) for passenger long-range market from hydrogen aircraft [%].
        ask_short_range_electric_share
            Share of Available Seat Kilometre (ASK) for passenger short-range market from electric aircraft [%].
        ask_medium_range_electric_share
            Share of Available Seat Kilometre (ASK) for passenger medium-range market from electric aircraft [%].
        ask_long_range_electric_share
            Share of Available Seat Kilometre (ASK) for passenger long-range market from electric aircraft [%].
        covid_energy_intensity_per_ask_increase_2020
            Increase in energy intensity per ASK due to Covid-19 for the start year [%].

        Returns
        -------
        energy_per_rtk_without_operations_freight_dropin_fuel
            Energy consumption per RTK for freight market aircraft using drop-in fuel without considering operation improvements [MJ/RTK].
        energy_per_rtk_without_operations_freight_hydrogen
            Energy consumption per RTK for freight market aircraft using hydrogen without considering operation improvements [MJ/RTK].
        energy_per_rtk_without_operations_freight_electric
            Energy consumption per RTK for freight market aircraft using electric propulsion without considering operation improvements [MJ/RTK].
        rtk_dropin_fuel_share
            Share of Revenue Tonne Kilometer (RTK) for freight air transport from drop-in fuel aircraft [%].
        rtk_hydrogen_share
            Share of Revenue Tonne Kilometer (RTK) for freight air transport from hydrogen aircraft [%].
        rtk_electric_share
            Share of Revenue Tonne Kilometer (RTK) for freight air transport from electric aircraft [%].
        rtk_dropin_fuel
            Number of Revenue Tonne Kilometer (RTK) for freight air transport from drop-in fuel aircraft [RTK].
        rtk_hydrogen
            Number of Revenue Tonne Kilometer (RTK) for freight air transport from hydrogen aircraft [RTK].
        rtk_electric
            Number of Revenue Tonne Kilometer (RTK) for freight air transport from electric aircraft [RTK].
        """

        # Initialization based on 2019 share: to correct to include load factor
        hist_years = list(range(self.historic_start_year, self.prospection_start_year))
        self.df.loc[hist_years, "energy_per_rtk_without_operations_freight_dropin_fuel"] = (
            energy_consumption_init.loc[hist_years]
            / rtk.loc[hist_years]
            * freight_energy_share_2019
            / 100
        )

        # Projections
        init_energy_per_rtk_without_operations_freight_dropin_fuel = self.df.loc[
            2019, "energy_per_rtk_without_operations_freight_dropin_fuel"
        ]
        energy_per_rtk_without_operations_freight_dropin_fuel_short_range_k = (
            init_energy_per_rtk_without_operations_freight_dropin_fuel.copy()
        )
        energy_per_rtk_without_operations_freight_dropin_fuel_medium_range_k = (
            init_energy_per_rtk_without_operations_freight_dropin_fuel.copy()
        )
        energy_per_rtk_without_operations_freight_dropin_fuel_long_range_k = (
            init_energy_per_rtk_without_operations_freight_dropin_fuel.copy()
        )

        for k in range(self.prospection_start_year, self.end_year + 1):
            energy_per_rtk_without_operations_freight_dropin_fuel_short_range_k = (
                energy_per_rtk_without_operations_freight_dropin_fuel_short_range_k
                * energy_per_ask_without_operations_short_range_dropin_fuel.loc[k]
                / energy_per_ask_without_operations_short_range_dropin_fuel.loc[k - 1]
            )
            energy_per_rtk_without_operations_freight_dropin_fuel_medium_range_k = (
                energy_per_rtk_without_operations_freight_dropin_fuel_medium_range_k
                * energy_per_ask_without_operations_medium_range_dropin_fuel.loc[k]
                / energy_per_ask_without_operations_medium_range_dropin_fuel.loc[k - 1]
            )
            energy_per_rtk_without_operations_freight_dropin_fuel_long_range_k = (
                energy_per_rtk_without_operations_freight_dropin_fuel_long_range_k
                * energy_per_ask_without_operations_long_range_dropin_fuel.loc[k]
                / energy_per_ask_without_operations_long_range_dropin_fuel.loc[k - 1]
            )

            # local variables to avoid multiple locs
            ask_short_range_dropin_fuel_k = ask_short_range_dropin_fuel.loc[k]
            ask_medium_range_dropin_fuel_k = ask_medium_range_dropin_fuel.loc[k]
            ask_long_range_dropin_fuel_k = ask_long_range_dropin_fuel.loc[k]
            ask_total_dropin_fuel_k = (
                ask_short_range_dropin_fuel_k
                + ask_medium_range_dropin_fuel_k
                + ask_long_range_dropin_fuel_k
            )

            self.df.loc[k, "energy_per_rtk_without_operations_freight_dropin_fuel"] = (
                energy_per_rtk_without_operations_freight_dropin_fuel_short_range_k
                * ask_short_range_dropin_fuel_k
                / (ask_total_dropin_fuel_k)
                + energy_per_rtk_without_operations_freight_dropin_fuel_medium_range_k
                * ask_medium_range_dropin_fuel_k
                / (ask_total_dropin_fuel_k)
                + energy_per_rtk_without_operations_freight_dropin_fuel_long_range_k
                * ask_long_range_dropin_fuel_k
                / (ask_total_dropin_fuel_k)
            )

        # Covid
        self.df.loc[2020, "energy_per_rtk_without_operations_freight_dropin_fuel"] = self.df.loc[
            2019, "energy_per_rtk_without_operations_freight_dropin_fuel"
        ] * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)

        energy_per_rtk_without_operations_freight_dropin_fuel = self.df[
            "energy_per_rtk_without_operations_freight_dropin_fuel"
        ]

        rtk_hydrogen_share = (
            ask_short_range_hydrogen_share * (ask_short_range / ask)
            + ask_medium_range_hydrogen_share * (ask_medium_range / ask)
            + ask_long_range_hydrogen_share * (ask_long_range / ask)
        )
        rtk_electric_share = (
            ask_short_range_electric_share * (ask_short_range / ask)
            + ask_medium_range_electric_share * (ask_medium_range / ask)
            + ask_long_range_electric_share * (ask_long_range / ask)
        )
        rtk_dropin_fuel_share = 100 - rtk_hydrogen_share - rtk_electric_share
        self.df.loc[:, "rtk_hydrogen_share"] = rtk_hydrogen_share
        self.df.loc[:, "rtk_dropin_fuel_share"] = rtk_dropin_fuel_share
        self.df.loc[:, "rtk_electric_share"] = rtk_electric_share

        rtk_hydrogen = rtk * rtk_hydrogen_share / 100
        rtk_electric = rtk * rtk_electric_share / 100
        rtk_dropin_fuel = rtk * rtk_dropin_fuel_share / 100
        self.df.loc[:, "rtk_hydrogen"] = rtk_hydrogen
        self.df.loc[:, "rtk_dropin_fuel"] = rtk_dropin_fuel
        self.df.loc[:, "rtk_electric"] = rtk_electric

        relative_energy_per_ask_hydrogen_wrt_dropin_short_range = (
            energy_per_ask_without_operations_short_range_hydrogen
            / energy_per_ask_without_operations_short_range_dropin_fuel
        )
        relative_energy_per_ask_hydrogen_wrt_dropin_medium_range = (
            energy_per_ask_without_operations_medium_range_hydrogen
            / energy_per_ask_without_operations_medium_range_dropin_fuel
        )
        relative_energy_per_ask_hydrogen_wrt_dropin_long_range = (
            energy_per_ask_without_operations_long_range_hydrogen
            / energy_per_ask_without_operations_long_range_dropin_fuel
        )

        relative_energy_per_ask_electric_wrt_dropin_short_range = (
            energy_per_ask_without_operations_short_range_electric
            / energy_per_ask_without_operations_short_range_dropin_fuel
        )
        relative_energy_per_ask_electric_wrt_dropin_medium_range = (
            energy_per_ask_without_operations_medium_range_electric
            / energy_per_ask_without_operations_medium_range_dropin_fuel
        )
        relative_energy_per_ask_electric_wrt_dropin_long_range = (
            energy_per_ask_without_operations_long_range_electric
            / energy_per_ask_without_operations_long_range_dropin_fuel
        )

        # Vectorized computation for hydrogen => direct affectation of dropin fuel average if not used. Strange but kept old way of doing.
        hydrogen_zero_mask = rtk_hydrogen_share == 0
        hydrogen_nonzero_mask = ~hydrogen_zero_mask

        self.df.loc[hydrogen_zero_mask, "energy_per_rtk_without_operations_freight_hydrogen"] = (
            self.df.loc[hydrogen_zero_mask, "energy_per_rtk_without_operations_freight_dropin_fuel"]
        )

        hydrogen_weighted_sum = (
            relative_energy_per_ask_hydrogen_wrt_dropin_short_range
            * ask_short_range_hydrogen_share
            * (ask_short_range / ask)
            + relative_energy_per_ask_hydrogen_wrt_dropin_medium_range
            * ask_medium_range_hydrogen_share
            * (ask_medium_range / ask)
            + relative_energy_per_ask_hydrogen_wrt_dropin_long_range
            * ask_long_range_hydrogen_share
            * (ask_long_range / ask)
        ) / rtk_hydrogen_share.loc[hydrogen_nonzero_mask]

        self.df.loc[hydrogen_nonzero_mask, "energy_per_rtk_without_operations_freight_hydrogen"] = (
            energy_per_rtk_without_operations_freight_dropin_fuel.loc[hydrogen_nonzero_mask]
            * hydrogen_weighted_sum.loc[hydrogen_nonzero_mask]
        )

        # Vectorized computation for electric
        electric_zero_mask = rtk_electric_share == 0
        electric_nonzero_mask = ~electric_zero_mask

        self.df.loc[electric_zero_mask, "energy_per_rtk_without_operations_freight_electric"] = (
            self.df.loc[electric_zero_mask, "energy_per_rtk_without_operations_freight_dropin_fuel"]
        )

        electric_weighted_sum = (
            relative_energy_per_ask_electric_wrt_dropin_short_range
            * ask_short_range_electric_share
            * (ask_short_range / ask)
            + relative_energy_per_ask_electric_wrt_dropin_medium_range
            * ask_medium_range_electric_share
            * (ask_medium_range / ask)
            + relative_energy_per_ask_electric_wrt_dropin_long_range
            * ask_long_range_electric_share
            * (ask_long_range / ask)
        ) / rtk_electric_share.loc[electric_nonzero_mask]

        self.df.loc[electric_nonzero_mask, "energy_per_rtk_without_operations_freight_electric"] = (
            energy_per_rtk_without_operations_freight_dropin_fuel.loc[electric_nonzero_mask]
            * electric_weighted_sum.loc[electric_nonzero_mask]
        )

        energy_per_rtk_without_operations_freight_hydrogen = self.df[
            "energy_per_rtk_without_operations_freight_hydrogen"
        ]
        energy_per_rtk_without_operations_freight_electric = self.df[
            "energy_per_rtk_without_operations_freight_electric"
        ]
        return (
            energy_per_rtk_without_operations_freight_dropin_fuel,
            energy_per_rtk_without_operations_freight_hydrogen,
            energy_per_rtk_without_operations_freight_electric,
            rtk_dropin_fuel_share,
            rtk_hydrogen_share,
            rtk_electric_share,
            rtk_dropin_fuel,
            rtk_hydrogen,
            rtk_electric,
        )

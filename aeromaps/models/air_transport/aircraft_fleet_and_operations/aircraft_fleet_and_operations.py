"""
aircraft_fleet_and_operations
===============

Models to compute energy intensities per ASK/RTK for different aircraft pathways
including effects of operations and contrails.
"""

from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class EnergyIntensity(AeroMAPSModel):
    """Compute energy consumption per ASK/RTK including operational efficiency effects.

    Parameters
    ----------
    name
        Name of the model instance ('passenger_energy_intensity' by default).
    """

    def __init__(self, name="passenger_energy_intensity", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_per_ask_without_operations_short_range_dropin_fuel: pd.Series,
        energy_per_ask_without_operations_medium_range_dropin_fuel: pd.Series,
        energy_per_ask_without_operations_long_range_dropin_fuel: pd.Series,
        energy_per_rtk_without_operations_freight_dropin_fuel: pd.Series,
        energy_per_ask_without_operations_short_range_hydrogen: pd.Series,
        energy_per_ask_without_operations_medium_range_hydrogen: pd.Series,
        energy_per_ask_without_operations_long_range_hydrogen: pd.Series,
        energy_per_rtk_without_operations_freight_hydrogen: pd.Series,
        energy_per_ask_without_operations_short_range_electric: pd.Series,
        energy_per_ask_without_operations_medium_range_electric: pd.Series,
        energy_per_ask_without_operations_long_range_electric: pd.Series,
        energy_per_rtk_without_operations_freight_electric: pd.Series,
        operations_gain: pd.Series,
        operations_contrails_overconsumption: pd.Series,
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
        """Compute energy per ASK/RTK for each pathway including operations.

        Parameters
        ----------
        energy_per_ask_without_operations_short_range_dropin_fuel
            Energy consumption per ASK for passenger short-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_dropin_fuel
            Energy consumption per ASK for passenger medium-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_dropin_fuel
            Energy consumption per ASK for passenger long-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_rtk_without_operations_freight_dropin_fuel
            Energy consumption per RTK for freight market aircraft using drop-in fuel without considering operation improvements [MJ/RTK].
        energy_per_ask_without_operations_short_range_hydrogen
            Energy consumption per ASK for passenger short-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_hydrogen
            Energy consumption per ASK for passenger medium-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_hydrogen
            Energy consumption per ASK for passenger long-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_rtk_without_operations_freight_hydrogen
            Energy consumption per RTK for freight market aircraft using hydrogen without considering operation improvements [MJ/RTK].
        energy_per_ask_without_operations_short_range_electric
            Energy consumption per ASK for passenger short-range market aircraft using electric without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_electric
            Energy consumption per ASK for passenger medium-range market aircraft using electric without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_electric
            Energy consumption per ASK for passenger long-range market aircraft using electric without considering operation improvements [MJ/ASK].
        energy_per_rtk_without_operations_freight_electric
            Energy consumption per RTK for freight market aircraft using electric without considering operation improvements [MJ/RTK].
        operations_gain
            Impact of operational improvements in terms of percentage reduction in fuel consumption per ASK [%].
        operations_contrails_overconsumption
            Impact of contrail operational improvements in terms of percentage increase in fuel consumption [%].

        Returns
        -------
        energy_per_ask_short_range_dropin_fuel
            Energy consumption per ASK for passenger short-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_medium_range_dropin_fuel
            Energy consumption per ASK for passenger medium-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_long_range_dropin_fuel
            Energy consumption per ASK for passenger long-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_rtk_freight_dropin_fuel
            Energy consumption per RTK for freight market aircraft using drop-in fuel [MJ/RTK].
        energy_per_ask_short_range_hydrogen
            Energy consumption per ASK for passenger short-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_medium_range_hydrogen
            Energy consumption per ASK for passenger medium-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_long_range_hydrogen
            Energy consumption per ASK for passenger long-range market aircraft using hydrogen [MJ/ASK].
        energy_per_rtk_freight_hydrogen
            Energy consumption per RTK for freight market aircraft using hydrogen [MJ/RTK].
        energy_per_ask_short_range_electric
            Energy consumption per ASK for passenger short-range market aircraft using electricity [MJ/ASK].
        energy_per_ask_medium_range_electric
            Energy consumption per ASK for passenger medium-range market aircraft using electricity [MJ/ASK].
        energy_per_ask_long_range_electric
            Energy consumption per ASK for passenger long-range market aircraft using electricity [MJ/ASK].
        energy_per_rtk_freight_electric
            Energy consumption per RTK for freight market aircraft using electricity [MJ/RTK].
        """

        energy_per_ask_short_range_dropin_fuel = (
            energy_per_ask_without_operations_short_range_dropin_fuel
            * (1 - operations_gain / 100)
            * (1 + operations_contrails_overconsumption / 100)
        )
        energy_per_ask_medium_range_dropin_fuel = (
            energy_per_ask_without_operations_medium_range_dropin_fuel
            * (1 - operations_gain / 100)
            * (1 + operations_contrails_overconsumption / 100)
        )
        energy_per_ask_long_range_dropin_fuel = (
            energy_per_ask_without_operations_long_range_dropin_fuel
            * (1 - operations_gain / 100)
            * (1 + operations_contrails_overconsumption / 100)
        )
        energy_per_rtk_freight_dropin_fuel = (
            energy_per_rtk_without_operations_freight_dropin_fuel
            * (1 - operations_gain / 100)
            * (1 + operations_contrails_overconsumption / 100)
        )
        energy_per_ask_short_range_hydrogen = (
            energy_per_ask_without_operations_short_range_hydrogen
            * (1 - operations_gain / 100)
            * (1 + operations_contrails_overconsumption / 100)
        )
        energy_per_ask_medium_range_hydrogen = (
            energy_per_ask_without_operations_medium_range_hydrogen
            * (1 - operations_gain / 100)
            * (1 + operations_contrails_overconsumption / 100)
        )
        energy_per_ask_long_range_hydrogen = (
            energy_per_ask_without_operations_long_range_hydrogen
            * (1 - operations_gain / 100)
            * (1 + operations_contrails_overconsumption / 100)
        )
        energy_per_rtk_freight_hydrogen = (
            energy_per_rtk_without_operations_freight_hydrogen
            * (1 - operations_gain / 100)
            * (1 + operations_contrails_overconsumption / 100)
        )

        energy_per_ask_short_range_electric = (
            energy_per_ask_without_operations_short_range_electric
            * (1 - operations_gain / 100)
            * (1 + operations_contrails_overconsumption / 100)
        )
        energy_per_ask_medium_range_electric = (
            energy_per_ask_without_operations_medium_range_electric
            * (1 - operations_gain / 100)
            * (1 + operations_contrails_overconsumption / 100)
        )
        energy_per_ask_long_range_electric = (
            energy_per_ask_without_operations_long_range_electric
            * (1 - operations_gain / 100)
            * (1 + operations_contrails_overconsumption / 100)
        )
        energy_per_rtk_freight_electric = (
            energy_per_rtk_without_operations_freight_electric
            * (1 - operations_gain / 100)
            * (1 + operations_contrails_overconsumption / 100)
        )

        self.df.loc[:, "energy_per_ask_short_range_dropin_fuel"] = (
            energy_per_ask_short_range_dropin_fuel
        )
        self.df.loc[:, "energy_per_ask_medium_range_dropin_fuel"] = (
            energy_per_ask_medium_range_dropin_fuel
        )
        self.df.loc[:, "energy_per_ask_long_range_dropin_fuel"] = (
            energy_per_ask_long_range_dropin_fuel
        )
        self.df.loc[:, "energy_per_rtk_freight_dropin_fuel"] = energy_per_rtk_freight_dropin_fuel
        self.df.loc[:, "energy_per_ask_short_range_hydrogen"] = energy_per_ask_short_range_hydrogen
        self.df.loc[:, "energy_per_ask_medium_range_hydrogen"] = (
            energy_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "energy_per_ask_long_range_hydrogen"] = energy_per_ask_long_range_hydrogen
        self.df.loc[:, "energy_per_rtk_freight_hydrogen"] = energy_per_rtk_freight_hydrogen
        self.df.loc[:, "energy_per_ask_short_range_electric"] = energy_per_ask_short_range_electric
        self.df.loc[:, "energy_per_ask_medium_range_electric"] = (
            energy_per_ask_medium_range_electric
        )
        self.df.loc[:, "energy_per_ask_long_range_electric"] = energy_per_ask_long_range_electric
        self.df.loc[:, "energy_per_rtk_freight_electric"] = energy_per_rtk_freight_electric

        return (
            energy_per_ask_short_range_dropin_fuel,
            energy_per_ask_medium_range_dropin_fuel,
            energy_per_ask_long_range_dropin_fuel,
            energy_per_rtk_freight_dropin_fuel,
            energy_per_ask_short_range_hydrogen,
            energy_per_ask_medium_range_hydrogen,
            energy_per_ask_long_range_hydrogen,
            energy_per_rtk_freight_hydrogen,
            energy_per_ask_short_range_electric,
            energy_per_ask_medium_range_electric,
            energy_per_ask_long_range_electric,
            energy_per_rtk_freight_electric,
        )

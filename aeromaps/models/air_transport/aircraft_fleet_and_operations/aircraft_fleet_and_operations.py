from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeromapsModel


class EnergyIntensity(AeromapsModel):
    def __init__(self, name="passenger_energy_intensity", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_per_ask_without_operations_short_range_dropin_fuel: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_ask_without_operations_medium_range_dropin_fuel: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_ask_without_operations_long_range_dropin_fuel: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_rtk_without_operations_freight_dropin_fuel: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_ask_without_operations_short_range_hydrogen: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_ask_without_operations_medium_range_hydrogen: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_ask_without_operations_long_range_hydrogen: pd.Series = pd.Series(
            dtype="float64"
        ),
        energy_per_rtk_without_operations_freight_hydrogen: pd.Series = pd.Series(dtype="float64"),
        operations_gain: pd.Series = pd.Series(dtype="float64"),
        operations_contrails_overconsumption: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[
        pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series
    ]:
        """Energy consumption per ASK (with operations) calculation using simple models."""

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

        self.df.loc[
            :, "energy_per_ask_short_range_dropin_fuel"
        ] = energy_per_ask_short_range_dropin_fuel
        self.df.loc[
            :, "energy_per_ask_medium_range_dropin_fuel"
        ] = energy_per_ask_medium_range_dropin_fuel
        self.df.loc[
            :, "energy_per_ask_long_range_dropin_fuel"
        ] = energy_per_ask_long_range_dropin_fuel
        self.df.loc[:, "energy_per_rtk_freight_dropin_fuel"] = energy_per_rtk_freight_dropin_fuel
        self.df.loc[:, "energy_per_ask_short_range_hydrogen"] = energy_per_ask_short_range_hydrogen
        self.df.loc[
            :, "energy_per_ask_medium_range_hydrogen"
        ] = energy_per_ask_medium_range_hydrogen
        self.df.loc[:, "energy_per_ask_long_range_hydrogen"] = energy_per_ask_long_range_hydrogen
        self.df.loc[:, "energy_per_rtk_freight_hydrogen"] = energy_per_rtk_freight_hydrogen

        return (
            energy_per_ask_short_range_dropin_fuel,
            energy_per_ask_medium_range_dropin_fuel,
            energy_per_ask_long_range_dropin_fuel,
            energy_per_rtk_freight_dropin_fuel,
            energy_per_ask_short_range_hydrogen,
            energy_per_ask_medium_range_hydrogen,
            energy_per_ask_long_range_hydrogen,
            energy_per_rtk_freight_hydrogen,
        )

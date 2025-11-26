"""
energy_consumption
===================================
Module to compute energy consumption from different aircraft types.
"""

from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class DropInFuelConsumption(AeroMAPSModel):
    """
    Total drop-in fuel consumption calculation.

    Parameters
    --------------
    name : str
        Name of the model instance ('drop_in_fuel_consumption' by default).
    """

    def __init__(self, name="drop_in_fuel_consumption", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        ask_short_range_dropin_fuel: pd.Series,
        ask_medium_range_dropin_fuel: pd.Series,
        ask_long_range_dropin_fuel: pd.Series,
        rtk_dropin_fuel: pd.Series,
        energy_per_ask_without_operations_short_range_dropin_fuel: pd.Series,
        energy_per_ask_without_operations_medium_range_dropin_fuel: pd.Series,
        energy_per_ask_without_operations_long_range_dropin_fuel: pd.Series,
        energy_per_rtk_without_operations_freight_dropin_fuel: pd.Series,
        energy_per_ask_short_range_dropin_fuel: pd.Series,
        energy_per_ask_medium_range_dropin_fuel: pd.Series,
        energy_per_ask_long_range_dropin_fuel: pd.Series,
        energy_per_rtk_freight_dropin_fuel: pd.Series,
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
        Execute drop-in fuel consumption calculation.
        Parameters
        ----------
        ask_short_range_dropin_fuel
            Number of Available Seat Kilometer (ASK) for passenger short-range market from drop-in fuel aircraft [ASK].
        ask_medium_range_dropin_fuel
            Number of Available Seat Kilometer (ASK) for passenger medium-range market from drop-in fuel aircraft [ASK].
        ask_long_range_dropin_fuel
            Number of Available Seat Kilometer (ASK) for passenger long-range market from drop-in fuel aircraft [ASK].
        rtk_dropin_fuel
            Number of Revenue Tonne Kilometer (RTK) for freight air transport from drop-in fuel aircraft [RTK].
        energy_per_ask_without_operations_short_range_dropin_fuel
            Energy consumption per ASK for passenger short-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_dropin_fuel
            Energy consumption per ASK for passenger medium-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_dropin_fuel
            Energy consumption per ASK for passenger long-range market aircraft using drop-in fuel without considering operation improvements [MJ/ASK].
        energy_per_rtk_without_operations_freight_dropin_fuel
            Energy consumption per RTK for freight market aircraft using drop-in fuel without considering operation improvements [MJ/RTK].
        energy_per_ask_short_range_dropin_fuel
            Energy consumption per ASK for passenger short-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_medium_range_dropin_fuel
            Energy consumption per ASK for passenger medium-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_ask_long_range_dropin_fuel
            Energy consumption per ASK for passenger long-range market aircraft using drop-in fuel [MJ/ASK].
        energy_per_rtk_freight_dropin_fuel
            Energy consumption per RTK for freight market aircraft using drop-in fuel [MJ/RTK].

        Returns
        -------
        energy_consumption_short_range_dropin_fuel_without_operations
                Energy consumption in the form of drop-in fuels without considering operation improvements from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_dropin_fuel_without_operations
                Energy consumption in the form of drop-in fuels without considering operation improvements from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_dropin_fuel_without_operations
                Energy consumption in the form of drop-in fuels without considering operation improvements from passenger long-range market air transport [MJ].
        energy_consumption_passenger_dropin_fuel_without_operations
                Energy consumption in the form of drop-in fuels without considering operation improvements from total passenger air transport [MJ].
        energy_consumption_freight_dropin_fuel_without_operations
                Energy consumption in the form of drop-in fuels without considering operation improvements from freight air transport [MJ].
        energy_consumption_dropin_fuel_without_operations
                Energy consumption in the form of drop-in fuels without considering operation improvements from all commercial air transport [MJ].
        energy_consumption_short_range_dropin_fuel
                Energy consumption in the form of drop-in fuels from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_dropin_fuel
                Energy consumption in the form of drop-in fuels from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_dropin_fuel
                Energy consumption in the form of drop-in fuels from passenger long-range market air transport [MJ].
        energy_consumption_passenger_dropin_fuel
                Energy consumption in the form of drop-in fuels from total passenger air transport [MJ].
        energy_consumption_freight_dropin_fuel
                Energy consumption in the form of drop-in fuels from freight air transport [MJ].
        energy_consumption_dropin_fuel
                Energy consumption in the form of drop-in fuels from all commercial air transport [MJ].
        """

        # WITHOUT OPERATIONS
        # Drop-in fuel
        energy_consumption_short_range_dropin_fuel_without_operations = (
            energy_per_ask_without_operations_short_range_dropin_fuel * ask_short_range_dropin_fuel
        )
        energy_consumption_medium_range_dropin_fuel_without_operations = (
            energy_per_ask_without_operations_medium_range_dropin_fuel
            * ask_medium_range_dropin_fuel
        )
        energy_consumption_long_range_dropin_fuel_without_operations = (
            energy_per_ask_without_operations_long_range_dropin_fuel * ask_long_range_dropin_fuel
        )
        energy_consumption_passenger_dropin_fuel_without_operations = (
            energy_consumption_short_range_dropin_fuel_without_operations
            + energy_consumption_medium_range_dropin_fuel_without_operations
            + energy_consumption_long_range_dropin_fuel_without_operations
        )
        energy_consumption_freight_dropin_fuel_without_operations = (
            energy_per_rtk_without_operations_freight_dropin_fuel * rtk_dropin_fuel
        )
        energy_consumption_dropin_fuel_without_operations = (
            energy_consumption_passenger_dropin_fuel_without_operations
            + energy_consumption_freight_dropin_fuel_without_operations
        )

        self.df.loc[:, "energy_consumption_short_range_dropin_fuel_without_operations"] = (
            energy_consumption_short_range_dropin_fuel_without_operations
        )
        self.df.loc[:, "energy_consumption_medium_range_dropin_fuel_without_operations"] = (
            energy_consumption_medium_range_dropin_fuel_without_operations
        )
        self.df.loc[:, "energy_consumption_long_range_dropin_fuel_without_operations"] = (
            energy_consumption_long_range_dropin_fuel_without_operations
        )
        self.df.loc[:, "energy_consumption_passenger_dropin_fuel_without_operations"] = (
            energy_consumption_passenger_dropin_fuel_without_operations
        )
        self.df.loc[:, "energy_consumption_freight_dropin_fuel_without_operations"] = (
            energy_consumption_freight_dropin_fuel_without_operations
        )
        self.df.loc[:, "energy_consumption_dropin_fuel_without_operations"] = (
            energy_consumption_dropin_fuel_without_operations
        )

        # WITH OPERATIONS
        # Drop-in fuel
        energy_consumption_short_range_dropin_fuel = (
            energy_per_ask_short_range_dropin_fuel * ask_short_range_dropin_fuel
        )
        energy_consumption_medium_range_dropin_fuel = (
            energy_per_ask_medium_range_dropin_fuel * ask_medium_range_dropin_fuel
        )
        energy_consumption_long_range_dropin_fuel = (
            energy_per_ask_long_range_dropin_fuel * ask_long_range_dropin_fuel
        )
        energy_consumption_passenger_dropin_fuel = (
            energy_consumption_short_range_dropin_fuel
            + energy_consumption_medium_range_dropin_fuel
            + energy_consumption_long_range_dropin_fuel
        )
        energy_consumption_freight_dropin_fuel = (
            energy_per_rtk_freight_dropin_fuel * rtk_dropin_fuel
        )
        energy_consumption_dropin_fuel = (
            energy_consumption_passenger_dropin_fuel + energy_consumption_freight_dropin_fuel
        )

        self.df.loc[:, "energy_consumption_short_range_dropin_fuel"] = (
            energy_consumption_short_range_dropin_fuel
        )
        self.df.loc[:, "energy_consumption_medium_range_dropin_fuel"] = (
            energy_consumption_medium_range_dropin_fuel
        )
        self.df.loc[:, "energy_consumption_long_range_dropin_fuel"] = (
            energy_consumption_long_range_dropin_fuel
        )
        self.df.loc[:, "energy_consumption_passenger_dropin_fuel"] = (
            energy_consumption_passenger_dropin_fuel
        )
        self.df.loc[:, "energy_consumption_freight_dropin_fuel"] = (
            energy_consumption_freight_dropin_fuel
        )
        self.df.loc[:, "energy_consumption_dropin_fuel"] = energy_consumption_dropin_fuel

        return (
            energy_consumption_short_range_dropin_fuel_without_operations,
            energy_consumption_medium_range_dropin_fuel_without_operations,
            energy_consumption_long_range_dropin_fuel_without_operations,
            energy_consumption_passenger_dropin_fuel_without_operations,
            energy_consumption_freight_dropin_fuel_without_operations,
            energy_consumption_dropin_fuel_without_operations,
            energy_consumption_short_range_dropin_fuel,
            energy_consumption_medium_range_dropin_fuel,
            energy_consumption_long_range_dropin_fuel,
            energy_consumption_passenger_dropin_fuel,
            energy_consumption_freight_dropin_fuel,
            energy_consumption_dropin_fuel,
        )


class DropInFuelDetailledConsumption(AeroMAPSModel):
    """
    Detailled drop-in fuel consumption calculation.

    Parameters
    --------------
    name : str
        Name of the model instance ('drop_in_fuel_detailled_consumption' by default).
    """

    def __init__(self, name="drop_in_fuel_detailled_consumption", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        biomass_share_dropin_fuel: pd.Series,
        electricity_share_dropin_fuel: pd.Series,
        fossil_share_dropin_fuel: pd.Series,
        energy_consumption_short_range_dropin_fuel_without_operations: pd.Series,
        energy_consumption_medium_range_dropin_fuel_without_operations: pd.Series,
        energy_consumption_long_range_dropin_fuel_without_operations: pd.Series,
        energy_consumption_freight_dropin_fuel_without_operations: pd.Series,
        energy_consumption_short_range_dropin_fuel: pd.Series,
        energy_consumption_medium_range_dropin_fuel: pd.Series,
        energy_consumption_long_range_dropin_fuel: pd.Series,
        energy_consumption_freight_dropin_fuel: pd.Series,
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
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        # TODO further adapt to generic energy model outputs?
        """
        Drop-in fuel consumption calculation.

        Parameters
        ----------
        biomass_share_dropin_fuel
            Share of biomass-based fuels in drop-in fuels [%].
        electricity_share_dropin_fuel
            Share of electricity-based fuels in drop-in fuels [%].
        fossil_share_dropin_fuel
            Share of fossil-based fuels in drop-in fuels [%].
        energy_consumption_short_range_dropin_fuel_without_operations
            Energy consumption in the form of drop-in fuels without considering operation improvements from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_dropin_fuel_without_operations
            Energy consumption in the form of drop-in fuels without considering operation improvements from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_dropin_fuel_without_operations
            Energy consumption in the form of drop-in fuels without considering operation improvements from passenger long-range market air transport [MJ].
        energy_consumption_freight_dropin_fuel_without_operations
            Energy consumption in the form of drop-in fuels without considering operation improvements from freight air transport [MJ].
        energy_consumption_short_range_dropin_fuel
            Energy consumption in the form of drop-in fuels from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_dropin_fuel
            Energy consumption in the form of drop-in fuels from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_dropin_fuel
            Energy consumption in the form of drop-in fuels from passenger long-range market air transport [MJ].
        energy_consumption_freight_dropin_fuel
            Energy consumption in the form of drop-in fuels from freight air transport [MJ].

        Returns
        -------
        energy_consumption_short_range_biofuel_without_operations
                Energy consumption in the form of biofuels without considering operation improvements from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_biofuel_without_operations
                Energy consumption in the form of biofuels without considering operation improvements from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_biofuel_without_operations
                Energy consumption in the form of biofuels without considering operation improvements from passenger long-range market air transport [MJ].
        energy_consumption_passenger_biofuel_without_operations
                Energy consumption in the form of biofuels without considering operation improvements from total passenger air transport [MJ].
        energy_consumption_freight_biofuel_without_operations
                Energy consumption in the form of biofuels without considering operation improvements from freight air transport [MJ].
        energy_consumption_biofuel_without_operations
                Energy consumption in the form of biofuels without considering operation improvements from all commercial air transport [MJ].
        energy_consumption_short_range_electrofuel_without_operations
                Energy consumption in the form of electrofuels without considering operation improvements from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_electrofuel_without_operations
                Energy consumption in the form of electrofuels without considering operation improvements from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_electrofuel_without_operations
                Energy consumption in the form of electrofuels without considering operation improvements from passenger long-range market air transport [MJ].
        energy_consumption_passenger_electrofuel_without_operations
                Energy consumption in the form of electrofuels without considering operation improvements from total passenger air transport [MJ].
        energy_consumption_freight_electrofuel_without_operations
                Energy consumption in the form of electrofuels without considering operation improvements from freight air transport [MJ].
        energy_consumption_electrofuel_without_operations
                Energy consumption in the form of electrofuels without considering operation improvements from all commercial air transport [MJ].
        energy_consumption_short_range_kerosene_without_operations
                Energy consumption in the form of kerosene without considering operation improvements from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_kerosene_without_operations
                Energy consumption in the form of kerosene without considering operation improvements from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_kerosene_without_operations
                Energy consumption in the form of kerosene without considering operation improvements from passenger long-range market air transport [MJ].
        energy_consumption_passenger_kerosene_without_operations
                Energy consumption in the form of kerosene without considering operation improvements from total passenger air transport [MJ].
        energy_consumption_freight_kerosene_without_operations
                Energy consumption in the form of kerosene without considering operation improvements from freight air transport [MJ].
        energy_consumption_kerosene_without_operations
                Energy consumption in the form of kerosene without considering operation improvements from all commercial air transport [MJ].
        energy_consumption_short_range_biofuel
                Energy consumption in the form of biofuels from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_biofuel
                Energy consumption in the form of biofuels from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_biofuel
                Energy consumption in the form of biofuels from passenger long-range market air transport [MJ].
        energy_consumption_passenger_biofuel
                Energy consumption in the form of biofuels from total passenger air transport [MJ].
        energy_consumption_freight_biofuel
                Energy consumption in the form of biofuels from freight air transport [MJ].
        energy_consumption_biofuel
                Energy consumption in the form of biofuels from all commercial air transport [MJ].
        energy_consumption_short_range_electrofuel
                Energy consumption in the form of electrofuels from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_electrofuel
                Energy consumption in the form of electrofuels from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_electrofuel
                Energy consumption in the form of electrofuels from passenger long-range market air transport [MJ].
        energy_consumption_passenger_electrofuel
                Energy consumption in the form of electrofuels from total passenger air transport [MJ].
        energy_consumption_freight_electrofuel
                Energy consumption in the form of electrofuels from freight air transport [MJ].
        energy_consumption_electrofuel
                Energy consumption in the form of electrofuels from all commercial air transport [MJ].
        energy_consumption_short_range_kerosene
                Energy consumption in the form of kerosene from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_kerosene
                Energy consumption in the form of kerosene from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_kerosene
                Energy consumption in the form of kerosene from passenger long-range market air transport [MJ].
        energy_consumption_passenger_kerosene
                Energy consumption in the form of kerosene from total passenger air transport [MJ].
        energy_consumption_freight_kerosene
                Energy consumption in the form of kerosene from freight air transport [MJ].
        energy_consumption_kerosene
                Energy consumption in the form of kerosene from all commercial air transport [MJ].
        """
        # WITHOUT OPERATIONS
        # Biofuel
        energy_consumption_short_range_biofuel_without_operations = (
            biomass_share_dropin_fuel
            / 100
            * energy_consumption_short_range_dropin_fuel_without_operations
        )
        energy_consumption_medium_range_biofuel_without_operations = (
            biomass_share_dropin_fuel
            / 100
            * energy_consumption_medium_range_dropin_fuel_without_operations
        )
        energy_consumption_long_range_biofuel_without_operations = (
            biomass_share_dropin_fuel
            / 100
            * energy_consumption_long_range_dropin_fuel_without_operations
        )
        energy_consumption_passenger_biofuel_without_operations = (
            energy_consumption_short_range_biofuel_without_operations
            + energy_consumption_medium_range_biofuel_without_operations
            + energy_consumption_long_range_biofuel_without_operations
        )
        energy_consumption_freight_biofuel_without_operations = (
            biomass_share_dropin_fuel
            / 100
            * energy_consumption_freight_dropin_fuel_without_operations
        )
        energy_consumption_biofuel_without_operations = (
            energy_consumption_passenger_biofuel_without_operations
            + energy_consumption_freight_biofuel_without_operations
        )

        self.df.loc[:, "energy_consumption_short_range_biofuel_without_operations"] = (
            energy_consumption_short_range_biofuel_without_operations
        )
        self.df.loc[:, "energy_consumption_medium_range_biofuel_without_operations"] = (
            energy_consumption_medium_range_biofuel_without_operations
        )
        self.df.loc[:, "energy_consumption_long_range_biofuel_without_operations"] = (
            energy_consumption_long_range_biofuel_without_operations
        )
        self.df.loc[:, "energy_consumption_passenger_biofuel_without_operations"] = (
            energy_consumption_passenger_biofuel_without_operations
        )
        self.df.loc[:, "energy_consumption_freight_biofuel_without_operations"] = (
            energy_consumption_freight_biofuel_without_operations
        )
        self.df.loc[:, "energy_consumption_biofuel_without_operations"] = (
            energy_consumption_biofuel_without_operations
        )

        # Electrofuel
        energy_consumption_short_range_electrofuel_without_operations = (
            electricity_share_dropin_fuel
            / 100
            * energy_consumption_short_range_dropin_fuel_without_operations
        )
        energy_consumption_medium_range_electrofuel_without_operations = (
            electricity_share_dropin_fuel
            / 100
            * energy_consumption_medium_range_dropin_fuel_without_operations
        )
        energy_consumption_long_range_electrofuel_without_operations = (
            electricity_share_dropin_fuel
            / 100
            * energy_consumption_long_range_dropin_fuel_without_operations
        )
        energy_consumption_passenger_electrofuel_without_operations = (
            energy_consumption_short_range_electrofuel_without_operations
            + energy_consumption_medium_range_electrofuel_without_operations
            + energy_consumption_long_range_electrofuel_without_operations
        )
        energy_consumption_freight_electrofuel_without_operations = (
            electricity_share_dropin_fuel
            / 100
            * energy_consumption_freight_dropin_fuel_without_operations
        )
        energy_consumption_electrofuel_without_operations = (
            energy_consumption_passenger_electrofuel_without_operations
            + energy_consumption_freight_electrofuel_without_operations
        )

        self.df.loc[:, "energy_consumption_short_range_electrofuel_without_operations"] = (
            energy_consumption_short_range_electrofuel_without_operations
        )
        self.df.loc[:, "energy_consumption_medium_range_electrofuel_without_operations"] = (
            energy_consumption_medium_range_electrofuel_without_operations
        )
        self.df.loc[:, "energy_consumption_long_range_electrofuel_without_operations"] = (
            energy_consumption_long_range_electrofuel_without_operations
        )
        self.df.loc[:, "energy_consumption_passenger_electrofuel_without_operations"] = (
            energy_consumption_passenger_electrofuel_without_operations
        )
        self.df.loc[:, "energy_consumption_freight_electrofuel_without_operations"] = (
            energy_consumption_freight_electrofuel_without_operations
        )
        self.df.loc[:, "energy_consumption_electrofuel_without_operations"] = (
            energy_consumption_electrofuel_without_operations
        )

        # Kerosene
        energy_consumption_short_range_kerosene_without_operations = (
            fossil_share_dropin_fuel
            / 100
            * energy_consumption_short_range_dropin_fuel_without_operations
        )
        energy_consumption_medium_range_kerosene_without_operations = (
            fossil_share_dropin_fuel
            / 100
            * energy_consumption_medium_range_dropin_fuel_without_operations
        )
        energy_consumption_long_range_kerosene_without_operations = (
            fossil_share_dropin_fuel
            / 100
            * energy_consumption_long_range_dropin_fuel_without_operations
        )
        energy_consumption_passenger_kerosene_without_operations = (
            energy_consumption_short_range_kerosene_without_operations
            + energy_consumption_medium_range_kerosene_without_operations
            + energy_consumption_long_range_kerosene_without_operations
        )
        energy_consumption_freight_kerosene_without_operations = (
            fossil_share_dropin_fuel
            / 100
            * energy_consumption_freight_dropin_fuel_without_operations
        )
        energy_consumption_kerosene_without_operations = (
            energy_consumption_passenger_kerosene_without_operations
            + energy_consumption_freight_kerosene_without_operations
        )

        self.df.loc[:, "energy_consumption_short_range_kerosene_without_operations"] = (
            energy_consumption_short_range_kerosene_without_operations
        )
        self.df.loc[:, "energy_consumption_medium_range_kerosene_without_operations"] = (
            energy_consumption_medium_range_kerosene_without_operations
        )
        self.df.loc[:, "energy_consumption_long_range_kerosene_without_operations"] = (
            energy_consumption_long_range_kerosene_without_operations
        )
        self.df.loc[:, "energy_consumption_passenger_kerosene_without_operations"] = (
            energy_consumption_passenger_kerosene_without_operations
        )
        self.df.loc[:, "energy_consumption_freight_kerosene_without_operations"] = (
            energy_consumption_freight_kerosene_without_operations
        )
        self.df.loc[:, "energy_consumption_kerosene_without_operations"] = (
            energy_consumption_kerosene_without_operations
        )

        # WITH OPERATIONS
        # Biofuel
        energy_consumption_short_range_biofuel = (
            biomass_share_dropin_fuel / 100 * energy_consumption_short_range_dropin_fuel
        )
        energy_consumption_medium_range_biofuel = (
            biomass_share_dropin_fuel / 100 * energy_consumption_medium_range_dropin_fuel
        )
        energy_consumption_long_range_biofuel = (
            biomass_share_dropin_fuel / 100 * energy_consumption_long_range_dropin_fuel
        )
        energy_consumption_passenger_biofuel = (
            energy_consumption_short_range_biofuel
            + energy_consumption_medium_range_biofuel
            + energy_consumption_long_range_biofuel
        )
        energy_consumption_freight_biofuel = (
            biomass_share_dropin_fuel / 100 * energy_consumption_freight_dropin_fuel
        )
        energy_consumption_biofuel = (
            energy_consumption_passenger_biofuel + energy_consumption_freight_biofuel
        )

        self.df.loc[:, "energy_consumption_short_range_biofuel"] = (
            energy_consumption_short_range_biofuel
        )
        self.df.loc[:, "energy_consumption_medium_range_biofuel"] = (
            energy_consumption_medium_range_biofuel
        )
        self.df.loc[:, "energy_consumption_long_range_biofuel"] = (
            energy_consumption_long_range_biofuel
        )
        self.df.loc[:, "energy_consumption_passenger_biofuel"] = (
            energy_consumption_passenger_biofuel
        )
        self.df.loc[:, "energy_consumption_freight_biofuel"] = energy_consumption_freight_biofuel
        self.df.loc[:, "energy_consumption_biofuel"] = energy_consumption_biofuel

        # Electrofuel
        energy_consumption_short_range_electrofuel = (
            electricity_share_dropin_fuel / 100 * energy_consumption_short_range_dropin_fuel
        )
        energy_consumption_medium_range_electrofuel = (
            electricity_share_dropin_fuel / 100 * energy_consumption_medium_range_dropin_fuel
        )
        energy_consumption_long_range_electrofuel = (
            electricity_share_dropin_fuel / 100 * energy_consumption_long_range_dropin_fuel
        )
        energy_consumption_passenger_electrofuel = (
            energy_consumption_short_range_electrofuel
            + energy_consumption_medium_range_electrofuel
            + energy_consumption_long_range_electrofuel
        )
        energy_consumption_freight_electrofuel = (
            electricity_share_dropin_fuel / 100 * energy_consumption_freight_dropin_fuel
        )
        energy_consumption_electrofuel = (
            energy_consumption_passenger_electrofuel + energy_consumption_freight_electrofuel
        )

        self.df.loc[:, "energy_consumption_short_range_electrofuel"] = (
            energy_consumption_short_range_electrofuel
        )
        self.df.loc[:, "energy_consumption_medium_range_electrofuel"] = (
            energy_consumption_medium_range_electrofuel
        )
        self.df.loc[:, "energy_consumption_long_range_electrofuel"] = (
            energy_consumption_long_range_electrofuel
        )
        self.df.loc[:, "energy_consumption_passenger_electrofuel"] = (
            energy_consumption_passenger_electrofuel
        )
        self.df.loc[:, "energy_consumption_freight_electrofuel"] = (
            energy_consumption_freight_electrofuel
        )
        self.df.loc[:, "energy_consumption_electrofuel"] = energy_consumption_electrofuel

        # Kerosene
        energy_consumption_short_range_kerosene = (
            fossil_share_dropin_fuel / 100 * energy_consumption_short_range_dropin_fuel
        )
        energy_consumption_medium_range_kerosene = (
            fossil_share_dropin_fuel / 100 * energy_consumption_medium_range_dropin_fuel
        )
        energy_consumption_long_range_kerosene = (
            fossil_share_dropin_fuel / 100 * energy_consumption_long_range_dropin_fuel
        )
        energy_consumption_passenger_kerosene = (
            energy_consumption_short_range_kerosene
            + energy_consumption_medium_range_kerosene
            + energy_consumption_long_range_kerosene
        )
        energy_consumption_freight_kerosene = (
            fossil_share_dropin_fuel / 100 * energy_consumption_freight_dropin_fuel
        )
        energy_consumption_kerosene = (
            energy_consumption_passenger_kerosene + energy_consumption_freight_kerosene
        )

        self.df.loc[:, "energy_consumption_short_range_kerosene"] = (
            energy_consumption_short_range_kerosene
        )
        self.df.loc[:, "energy_consumption_medium_range_kerosene"] = (
            energy_consumption_medium_range_kerosene
        )
        self.df.loc[:, "energy_consumption_long_range_kerosene"] = (
            energy_consumption_long_range_kerosene
        )
        self.df.loc[:, "energy_consumption_passenger_kerosene"] = (
            energy_consumption_passenger_kerosene
        )
        self.df.loc[:, "energy_consumption_freight_kerosene"] = energy_consumption_freight_kerosene
        self.df.loc[:, "energy_consumption_kerosene"] = energy_consumption_kerosene

        return (
            energy_consumption_short_range_biofuel_without_operations,
            energy_consumption_medium_range_biofuel_without_operations,
            energy_consumption_long_range_biofuel_without_operations,
            energy_consumption_passenger_biofuel_without_operations,
            energy_consumption_freight_biofuel_without_operations,
            energy_consumption_biofuel_without_operations,
            energy_consumption_short_range_electrofuel_without_operations,
            energy_consumption_medium_range_electrofuel_without_operations,
            energy_consumption_long_range_electrofuel_without_operations,
            energy_consumption_passenger_electrofuel_without_operations,
            energy_consumption_freight_electrofuel_without_operations,
            energy_consumption_electrofuel_without_operations,
            energy_consumption_short_range_kerosene_without_operations,
            energy_consumption_medium_range_kerosene_without_operations,
            energy_consumption_long_range_kerosene_without_operations,
            energy_consumption_passenger_kerosene_without_operations,
            energy_consumption_freight_kerosene_without_operations,
            energy_consumption_kerosene_without_operations,
            energy_consumption_short_range_biofuel,
            energy_consumption_medium_range_biofuel,
            energy_consumption_long_range_biofuel,
            energy_consumption_passenger_biofuel,
            energy_consumption_freight_biofuel,
            energy_consumption_biofuel,
            energy_consumption_short_range_electrofuel,
            energy_consumption_medium_range_electrofuel,
            energy_consumption_long_range_electrofuel,
            energy_consumption_passenger_electrofuel,
            energy_consumption_freight_electrofuel,
            energy_consumption_electrofuel,
            energy_consumption_short_range_kerosene,
            energy_consumption_medium_range_kerosene,
            energy_consumption_long_range_kerosene,
            energy_consumption_passenger_kerosene,
            energy_consumption_freight_kerosene,
            energy_consumption_kerosene,
        )


class HydrogenConsumption(AeroMAPSModel):
    """
    Class to calculate hydrogen consumption for each type of market.

    Parameters
    --------------
    name : str
        Name of the model instance ('hydrogen_consumption' by default).
    """

    def __init__(self, name="hydrogen_consumption", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        ask_short_range_hydrogen: pd.Series,
        ask_medium_range_hydrogen: pd.Series,
        ask_long_range_hydrogen: pd.Series,
        rtk_hydrogen: pd.Series,
        energy_per_ask_without_operations_short_range_hydrogen: pd.Series,
        energy_per_ask_without_operations_medium_range_hydrogen: pd.Series,
        energy_per_ask_without_operations_long_range_hydrogen: pd.Series,
        energy_per_rtk_without_operations_freight_hydrogen: pd.Series,
        energy_per_ask_short_range_hydrogen: pd.Series,
        energy_per_ask_medium_range_hydrogen: pd.Series,
        energy_per_ask_long_range_hydrogen: pd.Series,
        energy_per_rtk_freight_hydrogen: pd.Series,
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
        Hydrogen consumption calculation.

        Parameters
        ----------
        ask_short_range_hydrogen
            Number of Available Seat Kilometer (ASK) for passenger short-range market from hydrogen aircraft [ASK].
        ask_medium_range_hydrogen
            Number of Available Seat Kilometer (ASK) for passenger medium-range market from hydrogen aircraft [ASK].
        ask_long_range_hydrogen
            Number of Available Seat Kilometer (ASK) for passenger long-range market from hydrogen aircraft [ASK]
        rtk_hydrogen
            Number of Revenue Tonne Kilometer (RTK) for freight air transport from hydrogen aircraft [RTK].
        energy_per_ask_without_operations_short_range_hydrogen
            Energy consumption per ASK for passenger short-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_hydrogen
            Energy consumption per ASK for passenger medium-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_hydrogen
            Energy consumption per ASK for passenger long-range market aircraft using hydrogen without considering operation improvements [MJ/ASK].
        energy_per_rtk_without_operations_freight_hydrogen
            Energy consumption per RTK for freight aircraft using hydrogen without considering operation improvements [MJ/RTK].
        energy_per_ask_short_range_hydrogen
            Energy consumption per ASK for passenger short-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_medium_range_hydrogen
            Energy consumption per ASK for passenger medium-range market aircraft using hydrogen [MJ/ASK].
        energy_per_ask_long_range_hydrogen
            Energy consumption per ASK for passenger long-range market aircraft using hydrogen [MJ/ASK].
        energy_per_rtk_freight_hydrogen
            Energy consumption per RTK for freight aircraft using hydrogen [MJ/RTK].

        Returns
        -------
        energy_consumption_short_range_hydrogen_without_operations
            Energy consumption in the form of hydrogen without considering operation improvements from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_hydrogen_without_operations
            Energy consumption in the form of hydrogen without considering operation improvements from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_hydrogen_without_operations
            Energy consumption in the form of hydrogen without considering operation improvements from passenger long-range market air transport [MJ].
        energy_consumption_passenger_hydrogen_without_operations
            Energy consumption in the form of hydrogen without considering operation improvements from total passenger air transport [MJ].
        energy_consumption_freight_hydrogen_without_operations
            Energy consumption in the form of hydrogen without considering operation improvements from freight air transport [MJ].
        energy_consumption_hydrogen_without_operations
            Energy consumption in the form of hydrogen without considering operation improvements from all commercial air transport [MJ].
        energy_consumption_short_range_hydrogen
            Energy consumption in the form of hydrogen from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_hydrogen
            Energy consumption in the form of hydrogen from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_hydrogen
            Energy consumption in the form of hydrogen from passenger long-range market air transport [MJ].
        energy_consumption_passenger_hydrogen
            Energy consumption in the form of hydrogen from total passenger air transport [MJ].
        energy_consumption_freight_hydrogen
            Energy consumption in the form of hydrogen from freight air transport [MJ].
        energy_consumption_hydrogen
            Energy consumption in the form of hydrogen from all commercial air transport [MJ].
        """

        # WITHOUT OPERATIONS
        energy_consumption_short_range_hydrogen_without_operations = (
            energy_per_ask_without_operations_short_range_hydrogen * ask_short_range_hydrogen
        )
        energy_consumption_medium_range_hydrogen_without_operations = (
            energy_per_ask_without_operations_medium_range_hydrogen * ask_medium_range_hydrogen
        )
        energy_consumption_long_range_hydrogen_without_operations = (
            energy_per_ask_without_operations_long_range_hydrogen * ask_long_range_hydrogen
        )
        energy_consumption_passenger_hydrogen_without_operations = (
            energy_consumption_short_range_hydrogen_without_operations
            + energy_consumption_medium_range_hydrogen_without_operations
            + energy_consumption_long_range_hydrogen_without_operations
        )
        energy_consumption_freight_hydrogen_without_operations = (
            energy_per_rtk_without_operations_freight_hydrogen * rtk_hydrogen
        )
        energy_consumption_hydrogen_without_operations = (
            energy_consumption_passenger_hydrogen_without_operations
            + energy_consumption_freight_hydrogen_without_operations
        )

        self.df.loc[:, "energy_consumption_short_range_hydrogen_without_operations"] = (
            energy_consumption_short_range_hydrogen_without_operations
        )
        self.df.loc[:, "energy_consumption_medium_range_hydrogen_without_operations"] = (
            energy_consumption_medium_range_hydrogen_without_operations
        )
        self.df.loc[:, "energy_consumption_long_range_hydrogen_without_operations"] = (
            energy_consumption_long_range_hydrogen_without_operations
        )
        self.df.loc[:, "energy_consumption_passenger_hydrogen_without_operations"] = (
            energy_consumption_passenger_hydrogen_without_operations
        )
        self.df.loc[:, "energy_consumption_freight_hydrogen_without_operations"] = (
            energy_consumption_freight_hydrogen_without_operations
        )
        self.df.loc[:, "energy_consumption_hydrogen_without_operations"] = (
            energy_consumption_hydrogen_without_operations
        )

        # WITH OPERATIONS
        energy_consumption_short_range_hydrogen = (
            energy_per_ask_short_range_hydrogen * ask_short_range_hydrogen
        )
        energy_consumption_medium_range_hydrogen = (
            energy_per_ask_medium_range_hydrogen * ask_medium_range_hydrogen
        )
        energy_consumption_long_range_hydrogen = (
            energy_per_ask_long_range_hydrogen * ask_long_range_hydrogen
        )
        energy_consumption_passenger_hydrogen = (
            energy_consumption_short_range_hydrogen
            + energy_consumption_medium_range_hydrogen
            + energy_consumption_long_range_hydrogen
        )
        energy_consumption_freight_hydrogen = energy_per_rtk_freight_hydrogen * rtk_hydrogen
        energy_consumption_hydrogen = (
            energy_consumption_passenger_hydrogen + energy_consumption_freight_hydrogen
        )

        self.df.loc[:, "energy_consumption_short_range_hydrogen"] = (
            energy_consumption_short_range_hydrogen
        )
        self.df.loc[:, "energy_consumption_medium_range_hydrogen"] = (
            energy_consumption_medium_range_hydrogen
        )
        self.df.loc[:, "energy_consumption_long_range_hydrogen"] = (
            energy_consumption_long_range_hydrogen
        )
        self.df.loc[:, "energy_consumption_passenger_hydrogen"] = (
            energy_consumption_passenger_hydrogen
        )
        self.df.loc[:, "energy_consumption_freight_hydrogen"] = energy_consumption_freight_hydrogen
        self.df.loc[:, "energy_consumption_hydrogen"] = energy_consumption_hydrogen

        return (
            energy_consumption_short_range_hydrogen_without_operations,
            energy_consumption_medium_range_hydrogen_without_operations,
            energy_consumption_long_range_hydrogen_without_operations,
            energy_consumption_passenger_hydrogen_without_operations,
            energy_consumption_freight_hydrogen_without_operations,
            energy_consumption_hydrogen_without_operations,
            energy_consumption_short_range_hydrogen,
            energy_consumption_medium_range_hydrogen,
            energy_consumption_long_range_hydrogen,
            energy_consumption_passenger_hydrogen,
            energy_consumption_freight_hydrogen,
            energy_consumption_hydrogen,
        )


class ElectricConsumption(AeroMAPSModel):
    """
    Class to calculate electricity consumption for each type of market.

    Parameters
    --------------
    name : str
        Name of the model instance ('electric_consumption' by default).
    """

    def __init__(self, name="electric_consumption", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        ask_short_range_electric: pd.Series,
        ask_medium_range_electric: pd.Series,
        ask_long_range_electric: pd.Series,
        rtk_electric: pd.Series,
        energy_per_ask_without_operations_short_range_electric: pd.Series,
        energy_per_ask_without_operations_medium_range_electric: pd.Series,
        energy_per_ask_without_operations_long_range_electric: pd.Series,
        energy_per_rtk_without_operations_freight_electric: pd.Series,
        energy_per_ask_short_range_electric: pd.Series,
        energy_per_ask_medium_range_electric: pd.Series,
        energy_per_ask_long_range_electric: pd.Series,
        energy_per_rtk_freight_electric: pd.Series,
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
        Electricity consumption calculation.

        Parameters
        ----------
        ask_short_range_electric
            Number of Available Seat Kilometer (ASK) for passenger short-range market from electric aircraft [ASK].
        ask_medium_range_electric
            Number of Available Seat Kilometer (ASK) for passenger medium-range market from electric aircraft [ASK].
        ask_long_range_electric
            Number of Available Seat Kilometer (ASK) for passenger long-range market from electric aircraft [ASK]
        rtk_electric
            Number of Revenue Tonne Kilometer (RTK) for freight air transport from electric aircraft [RTK].
        energy_per_ask_without_operations_short_range_electric
            Energy consumption per ASK for passenger short-range market aircraft using electricity without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_medium_range_electric
            Energy consumption per ASK for passenger medium-range market aircraft using electricity without considering operation improvements [MJ/ASK].
        energy_per_ask_without_operations_long_range_electric
            Energy consumption per ASK for passenger long-range market aircraft using electricity without considering operation improvements [MJ/ASK].
        energy_per_rtk_without_operations_freight_electric
            Energy consumption per RTK for freight aircraft using electricity without considering operation improvements [MJ/RTK].
        energy_per_ask_short_range_electric
            Energy consumption per ASK for passenger short-range market aircraft using electricity [MJ/ASK].
        energy_per_ask_medium_range_electric
            Energy consumption per ASK for passenger medium-range market aircraft using electricity [MJ/ASK].
        energy_per_ask_long_range_electric
            Energy consumption per ASK for passenger long-range market aircraft using electricity [MJ/ASK].
        energy_per_rtk_freight_electric
            Energy consumption per RTK for freight aircraft using electricity [MJ/RTK].

        Returns
        -------
        energy_consumption_short_range_electric_without_operations
            Energy consumption in the form of electricity without considering operation improvements from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_electric_without_operations
            Energy consumption in the form of electricity without considering operation improvements from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_electric_without_operations
            Energy consumption in the form of electricity without considering operation improvements from passenger long-range market air transport [MJ].
        energy_consumption_passenger_electric_without_operations
            Energy consumption in the form of electricity without considering operation improvements from total passenger air transport [MJ].
        energy_consumption_freight_electric_without_operations
            Energy consumption in the form of electricity without considering operation improvements from freight air transport [MJ].
        energy_consumption_electric_without_operations
            Energy consumption in the form of electricity without considering operation improvements from all commercial air transport [MJ].
        energy_consumption_short_range_electric
            Energy consumption in the form of electricity from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_electric
            Energy consumption in the form of electricity from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_electric
            Energy consumption in the form of electricity from passenger long-range market air transport [MJ].
        energy_consumption_passenger_electric
            Energy consumption in the form of electricity from total passenger air transport [MJ].
        energy_consumption_freight_electric
            Energy consumption in the form of electricity from freight air transport [MJ].
        energy_consumption_electric
            Energy consumption in the form of electricity from all commercial air transport [MJ].
        """

        # WITHOUT OPERATIONS
        energy_consumption_short_range_electric_without_operations = (
            energy_per_ask_without_operations_short_range_electric * ask_short_range_electric
        )
        energy_consumption_medium_range_electric_without_operations = (
            energy_per_ask_without_operations_medium_range_electric * ask_medium_range_electric
        )
        energy_consumption_long_range_electric_without_operations = (
            energy_per_ask_without_operations_long_range_electric * ask_long_range_electric
        )
        energy_consumption_passenger_electric_without_operations = (
            energy_consumption_short_range_electric_without_operations
            + energy_consumption_medium_range_electric_without_operations
            + energy_consumption_long_range_electric_without_operations
        )
        energy_consumption_freight_electric_without_operations = (
            energy_per_rtk_without_operations_freight_electric * rtk_electric
        )
        energy_consumption_electric_without_operations = (
            energy_consumption_passenger_electric_without_operations
            + energy_consumption_freight_electric_without_operations
        )

        self.df.loc[:, "energy_consumption_short_range_electric_without_operations"] = (
            energy_consumption_short_range_electric_without_operations
        )
        self.df.loc[:, "energy_consumption_medium_range_electric_without_operations"] = (
            energy_consumption_medium_range_electric_without_operations
        )
        self.df.loc[:, "energy_consumption_long_range_electric_without_operations"] = (
            energy_consumption_long_range_electric_without_operations
        )
        self.df.loc[:, "energy_consumption_passenger_electric_without_operations"] = (
            energy_consumption_passenger_electric_without_operations
        )
        self.df.loc[:, "energy_consumption_freight_electric_without_operations"] = (
            energy_consumption_freight_electric_without_operations
        )
        self.df.loc[:, "energy_consumption_electric_without_operations"] = (
            energy_consumption_electric_without_operations
        )

        # WITH OPERATIONS
        energy_consumption_short_range_electric = (
            energy_per_ask_short_range_electric * ask_short_range_electric
        )
        energy_consumption_medium_range_electric = (
            energy_per_ask_medium_range_electric * ask_medium_range_electric
        )
        energy_consumption_long_range_electric = (
            energy_per_ask_long_range_electric * ask_long_range_electric
        )
        energy_consumption_passenger_electric = (
            energy_consumption_short_range_electric
            + energy_consumption_medium_range_electric
            + energy_consumption_long_range_electric
        )
        energy_consumption_freight_electric = energy_per_rtk_freight_electric * rtk_electric
        energy_consumption_electric = (
            energy_consumption_passenger_electric + energy_consumption_freight_electric
        )

        self.df.loc[:, "energy_consumption_short_range_electric"] = (
            energy_consumption_short_range_electric
        )
        self.df.loc[:, "energy_consumption_medium_range_electric"] = (
            energy_consumption_medium_range_electric
        )
        self.df.loc[:, "energy_consumption_long_range_electric"] = (
            energy_consumption_long_range_electric
        )
        self.df.loc[:, "energy_consumption_passenger_electric"] = (
            energy_consumption_passenger_electric
        )
        self.df.loc[:, "energy_consumption_freight_electric"] = energy_consumption_freight_electric
        self.df.loc[:, "energy_consumption_electric"] = energy_consumption_electric

        return (
            energy_consumption_short_range_electric_without_operations,
            energy_consumption_medium_range_electric_without_operations,
            energy_consumption_long_range_electric_without_operations,
            energy_consumption_passenger_electric_without_operations,
            energy_consumption_freight_electric_without_operations,
            energy_consumption_electric_without_operations,
            energy_consumption_short_range_electric,
            energy_consumption_medium_range_electric,
            energy_consumption_long_range_electric,
            energy_consumption_passenger_electric,
            energy_consumption_freight_electric,
            energy_consumption_electric,
        )


class EnergyConsumption(AeroMAPSModel):
    """
    Class to calculate total energy consumption for each type of market, aggregating all energy sources.
    """

    def __init__(self, name="energy_consumption", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_short_range_dropin_fuel_without_operations: pd.Series,
        energy_consumption_medium_range_dropin_fuel_without_operations: pd.Series,
        energy_consumption_long_range_dropin_fuel_without_operations: pd.Series,
        energy_consumption_passenger_dropin_fuel_without_operations: pd.Series,
        energy_consumption_freight_dropin_fuel_without_operations: pd.Series,
        energy_consumption_short_range_hydrogen_without_operations: pd.Series,
        energy_consumption_medium_range_hydrogen_without_operations: pd.Series,
        energy_consumption_long_range_hydrogen_without_operations: pd.Series,
        energy_consumption_passenger_hydrogen_without_operations: pd.Series,
        energy_consumption_freight_hydrogen_without_operations: pd.Series,
        energy_consumption_short_range_electric_without_operations: pd.Series,
        energy_consumption_medium_range_electric_without_operations: pd.Series,
        energy_consumption_long_range_electric_without_operations: pd.Series,
        energy_consumption_passenger_electric_without_operations: pd.Series,
        energy_consumption_freight_electric_without_operations: pd.Series,
        energy_consumption_dropin_fuel_without_operations: pd.Series,
        energy_consumption_hydrogen_without_operations: pd.Series,
        energy_consumption_electric_without_operations: pd.Series,
        energy_consumption_short_range_dropin_fuel: pd.Series,
        energy_consumption_medium_range_dropin_fuel: pd.Series,
        energy_consumption_long_range_dropin_fuel: pd.Series,
        energy_consumption_passenger_dropin_fuel: pd.Series,
        energy_consumption_freight_dropin_fuel: pd.Series,
        energy_consumption_short_range_hydrogen: pd.Series,
        energy_consumption_medium_range_hydrogen: pd.Series,
        energy_consumption_long_range_hydrogen: pd.Series,
        energy_consumption_passenger_hydrogen: pd.Series,
        energy_consumption_freight_hydrogen: pd.Series,
        energy_consumption_short_range_electric: pd.Series,
        energy_consumption_medium_range_electric: pd.Series,
        energy_consumption_long_range_electric: pd.Series,
        energy_consumption_passenger_electric: pd.Series,
        energy_consumption_freight_electric: pd.Series,
        energy_consumption_dropin_fuel: pd.Series,
        energy_consumption_hydrogen: pd.Series,
        energy_consumption_electric: pd.Series,
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
        Energy consumption calculation.

        Parameters
        ----------
        energy_consumption_short_range_dropin_fuel_without_operations
            Energy consumption in the form of drop-in fuels without considering operation improvements from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_dropin_fuel_without_operations
            Energy consumption in the form of drop-in fuels without considering operation improvements from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_dropin_fuel_without_operations
            Energy consumption in the form of drop-in fuels without considering operation improvements from passenger long-range market air transport [MJ].
        energy_consumption_passenger_dropin_fuel_without_operations
            Energy consumption in the form of drop-in fuels without considering operation improvements from total passenger air transport [MJ].
        energy_consumption_freight_dropin_fuel_without_operations
            Energy consumption in the form of drop-in fuels without considering operation improvements from freight air transport [MJ].
        energy_consumption_short_range_hydrogen_without_operations
            Energy consumption in the form of hydrogen without considering operation improvements from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_hydrogen_without_operations
            Energy consumption in the form of hydrogen without considering operation improvements from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_hydrogen_without_operations
            Energy consumption in the form of hydrogen without considering operation improvements from passenger long-range market air transport [MJ].
        energy_consumption_passenger_hydrogen_without_operations
            Energy consumption in the form of hydrogen without considering operation improvements from total passenger air transport [MJ].
        energy_consumption_freight_hydrogen_without_operations
            Energy consumption in the form of hydrogen without considering operation improvements from freight air transport [MJ].
        energy_consumption_short_range_electric_without_operations
            Energy consumption in the form of electricity without considering operation improvements from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_electric_without_operations
            Energy consumption in the form of electricity without considering operation improvements from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_electric_without_operations
            Energy consumption in the form of electricity without considering operation improvements from passenger long-range market air transport [MJ].
        energy_consumption_passenger_electric_without_operations
            Energy consumption in the form of electricity without considering operation improvements from total passenger air transport [MJ].
        energy_consumption_freight_electric_without_operations
            Energy consumption in the form of electricity without considering operation improvements from freight air transport [MJ].
        energy_consumption_dropin_fuel_without_operations
            Energy consumption in the form of drop-in fuels without considering operation improvements from all commercial air transport [MJ].
        energy_consumption_hydrogen_without_operations
            Energy consumption in the form of hydrogen without considering operation improvements from all commercial air transport [MJ].
        energy_consumption_electric_without_operations
            Energy consumption in the form of electricity without considering operation improvements from all commercial air transport [MJ].
        energy_consumption_short_range_dropin_fuel
            Energy consumption in the form of drop-in fuels from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_dropin_fuel
            Energy consumption in the form of drop-in fuels from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_dropin_fuel
            Energy consumption in the form of drop-in fuels from passenger long-range market air transport [MJ].
        energy_consumption_passenger_dropin_fuel
            Energy consumption in the form of drop-in fuels from total passenger air transport [MJ].
        energy_consumption_freight_dropin_fuel
            Energy consumption in the form of drop-in fuels from freight air transport [MJ].
        energy_consumption_short_range_hydrogen
            Energy consumption in the form of hydrogen from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_hydrogen
            Energy consumption in the form of hydrogen from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_hydrogen
            Energy consumption in the form of hydrogen from passenger long-range market air transport [MJ].
        energy_consumption_passenger_hydrogen
            Energy consumption in the form of hydrogen from total passenger air transport [MJ].
        energy_consumption_freight_hydrogen
            Energy consumption in the form of hydrogen from freight air transport [MJ].
        energy_consumption_short_range_electric
            Energy consumption in the form of electricity from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_electric
            Energy consumption in the form of electricity from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_electric
            Energy consumption in the form of electricity from passenger long-range market air transport [MJ].
        energy_consumption_passenger_electric
            Energy consumption in the form of electricity from total passenger air transport [MJ].
        energy_consumption_freight_electric
            Energy consumption in the form of electricity from freight air transport [MJ].
        energy_consumption_dropin_fuel
            Energy consumption in the form of drop-in fuels from all commercial air transport [MJ].
        energy_consumption_hydrogen
            Energy consumption in the form of hydrogen from all commercial air transport [MJ].
        energy_consumption_electric
            Energy consumption in the form of electricity from all commercial air transport [MJ].

        Returns
        -------
        energy_consumption_short_range_without_operations
            Energy consumption including all fuels without considering operation improvements from passenger short-range market air transport [MJ].
        energy_consumption_medium_range_without_operations
            Energy consumption including all fuels without considering operation improvements from passenger medium-range market air transport [MJ].
        energy_consumption_long_range_without_operations
            Energy consumption including all fuels without considering operation improvements from passenger long-range market air transport [MJ
        energy_consumption_passenger_without_operations
            Energy consumption including all fuels without considering operation improvements from total passenger air transport [MJ].
        energy_consumption_freight_without_operations
            Energy consumption including all fuels without considering operation improvements from freight air transport [MJ].
        energy_consumption_without_operations
            Energy consumption including all fuels without considering operation improvements from all commercial air transport [MJ].
        energy_consumption_short_range
            Energy consumption including all fuels from passenger short-range market air transport [MJ].
        energy_consumption_medium_range
            Energy consumption including all fuels from passenger medium-range market air transport [MJ].
        energy_consumption_long_range
            Energy consumption including all fuels from passenger long-range market air transport [MJ].
        energy_consumption_passenger
            Energy consumption including all fuels from total passenger air transport [MJ].
        energy_consumption_freight
            Energy consumption including all fuels from freight air transport [MJ].
        energy_consumption
            Energy consumption including all fuels from all commercial air transport [MJ].
        """

        # WITHOUT OPERATIONS
        energy_consumption_short_range_without_operations = (
            +energy_consumption_short_range_dropin_fuel_without_operations
            + energy_consumption_short_range_hydrogen_without_operations
            + energy_consumption_short_range_electric_without_operations
        )
        energy_consumption_medium_range_without_operations = (
            +energy_consumption_medium_range_dropin_fuel_without_operations
            + energy_consumption_medium_range_hydrogen_without_operations
            + energy_consumption_medium_range_electric_without_operations
        )
        energy_consumption_long_range_without_operations = (
            +energy_consumption_long_range_dropin_fuel_without_operations
            + energy_consumption_long_range_hydrogen_without_operations
            + energy_consumption_long_range_electric_without_operations
        )
        energy_consumption_passenger_without_operations = (
            +energy_consumption_passenger_dropin_fuel_without_operations
            + energy_consumption_passenger_hydrogen_without_operations
            + energy_consumption_passenger_electric_without_operations
        )
        energy_consumption_freight_without_operations = (
            +energy_consumption_freight_dropin_fuel_without_operations
            + energy_consumption_freight_hydrogen_without_operations
            + energy_consumption_freight_electric_without_operations
        )
        energy_consumption_without_operations = (
            +energy_consumption_dropin_fuel_without_operations
            + energy_consumption_hydrogen_without_operations
            + energy_consumption_electric_without_operations
        )

        self.df.loc[:, "energy_consumption_short_range_without_operations"] = (
            energy_consumption_short_range_without_operations
        )
        self.df.loc[:, "energy_consumption_medium_range_without_operations"] = (
            energy_consumption_medium_range_without_operations
        )
        self.df.loc[:, "energy_consumption_long_range_without_operations"] = (
            energy_consumption_long_range_without_operations
        )
        self.df.loc[:, "energy_consumption_passenger_without_operations"] = (
            energy_consumption_passenger_without_operations
        )
        self.df.loc[:, "energy_consumption_freight_without_operations"] = (
            energy_consumption_freight_without_operations
        )
        self.df.loc[:, "energy_consumption_without_operations"] = (
            energy_consumption_without_operations
        )

        # WITH OPERATIONS
        energy_consumption_short_range = (
            +energy_consumption_short_range_dropin_fuel
            + energy_consumption_short_range_hydrogen
            + energy_consumption_short_range_electric
        )
        energy_consumption_medium_range = (
            +energy_consumption_medium_range_dropin_fuel
            + energy_consumption_medium_range_hydrogen
            + energy_consumption_medium_range_electric
        )
        energy_consumption_long_range = (
            +energy_consumption_long_range_dropin_fuel
            + energy_consumption_long_range_hydrogen
            + energy_consumption_long_range_electric
        )
        energy_consumption_passenger = (
            +energy_consumption_passenger_dropin_fuel
            + energy_consumption_passenger_hydrogen
            + energy_consumption_passenger_electric
        )
        energy_consumption_freight = (
            +energy_consumption_freight_dropin_fuel
            + energy_consumption_freight_hydrogen
            + energy_consumption_freight_electric
        )
        energy_consumption = (
            +energy_consumption_dropin_fuel
            + energy_consumption_hydrogen
            + energy_consumption_electric
        )

        self.df.loc[:, "energy_consumption_short_range"] = energy_consumption_short_range
        self.df.loc[:, "energy_consumption_medium_range"] = energy_consumption_medium_range
        self.df.loc[:, "energy_consumption_long_range"] = energy_consumption_long_range
        self.df.loc[:, "energy_consumption_passenger"] = energy_consumption_passenger
        self.df.loc[:, "energy_consumption_freight"] = energy_consumption_freight
        self.df.loc[:, "energy_consumption"] = energy_consumption

        return (
            energy_consumption_short_range_without_operations,
            energy_consumption_medium_range_without_operations,
            energy_consumption_long_range_without_operations,
            energy_consumption_passenger_without_operations,
            energy_consumption_freight_without_operations,
            energy_consumption_without_operations,
            energy_consumption_short_range,
            energy_consumption_medium_range,
            energy_consumption_long_range,
            energy_consumption_passenger,
            energy_consumption_freight,
            energy_consumption,
        )

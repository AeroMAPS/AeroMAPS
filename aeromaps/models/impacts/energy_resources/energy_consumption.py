from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class DropInFuelConsumption(AeroMAPSModel):
    def __init__(self, name="drop_in_fuel_consumption", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        biofuel_share: pd.Series,
        electrofuel_share: pd.Series,
        kerosene_share: pd.Series,
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
        """Drop-in fuel consumption calculation."""

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

        # Biofuel
        energy_consumption_short_range_biofuel_without_operations = (
            biofuel_share / 100 * energy_consumption_short_range_dropin_fuel_without_operations
        )
        energy_consumption_medium_range_biofuel_without_operations = (
            biofuel_share / 100 * energy_consumption_medium_range_dropin_fuel_without_operations
        )
        energy_consumption_long_range_biofuel_without_operations = (
            biofuel_share / 100 * energy_consumption_long_range_dropin_fuel_without_operations
        )
        energy_consumption_passenger_biofuel_without_operations = (
            energy_consumption_short_range_biofuel_without_operations
            + energy_consumption_medium_range_biofuel_without_operations
            + energy_consumption_long_range_biofuel_without_operations
        )
        energy_consumption_freight_biofuel_without_operations = (
            biofuel_share / 100 * energy_consumption_freight_dropin_fuel_without_operations
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
            electrofuel_share / 100 * energy_consumption_short_range_dropin_fuel_without_operations
        )
        energy_consumption_medium_range_electrofuel_without_operations = (
            electrofuel_share / 100 * energy_consumption_medium_range_dropin_fuel_without_operations
        )
        energy_consumption_long_range_electrofuel_without_operations = (
            electrofuel_share / 100 * energy_consumption_long_range_dropin_fuel_without_operations
        )
        energy_consumption_passenger_electrofuel_without_operations = (
            energy_consumption_short_range_electrofuel_without_operations
            + energy_consumption_medium_range_electrofuel_without_operations
            + energy_consumption_long_range_electrofuel_without_operations
        )
        energy_consumption_freight_electrofuel_without_operations = (
            electrofuel_share / 100 * energy_consumption_freight_dropin_fuel_without_operations
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
            kerosene_share / 100 * energy_consumption_short_range_dropin_fuel_without_operations
        )
        energy_consumption_medium_range_kerosene_without_operations = (
            kerosene_share / 100 * energy_consumption_medium_range_dropin_fuel_without_operations
        )
        energy_consumption_long_range_kerosene_without_operations = (
            kerosene_share / 100 * energy_consumption_long_range_dropin_fuel_without_operations
        )
        energy_consumption_passenger_kerosene_without_operations = (
            energy_consumption_short_range_kerosene_without_operations
            + energy_consumption_medium_range_kerosene_without_operations
            + energy_consumption_long_range_kerosene_without_operations
        )
        energy_consumption_freight_kerosene_without_operations = (
            kerosene_share / 100 * energy_consumption_freight_dropin_fuel_without_operations
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

        # Biofuel
        energy_consumption_short_range_biofuel = (
            biofuel_share / 100 * energy_consumption_short_range_dropin_fuel
        )
        energy_consumption_medium_range_biofuel = (
            biofuel_share / 100 * energy_consumption_medium_range_dropin_fuel
        )
        energy_consumption_long_range_biofuel = (
            biofuel_share / 100 * energy_consumption_long_range_dropin_fuel
        )
        energy_consumption_passenger_biofuel = (
            energy_consumption_short_range_biofuel
            + energy_consumption_medium_range_biofuel
            + energy_consumption_long_range_biofuel
        )
        energy_consumption_freight_biofuel = (
            biofuel_share / 100 * energy_consumption_freight_dropin_fuel
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
            electrofuel_share / 100 * energy_consumption_short_range_dropin_fuel
        )
        energy_consumption_medium_range_electrofuel = (
            electrofuel_share / 100 * energy_consumption_medium_range_dropin_fuel
        )
        energy_consumption_long_range_electrofuel = (
            electrofuel_share / 100 * energy_consumption_long_range_dropin_fuel
        )
        energy_consumption_passenger_electrofuel = (
            energy_consumption_short_range_electrofuel
            + energy_consumption_medium_range_electrofuel
            + energy_consumption_long_range_electrofuel
        )
        energy_consumption_freight_electrofuel = (
            electrofuel_share / 100 * energy_consumption_freight_dropin_fuel
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
            kerosene_share / 100 * energy_consumption_short_range_dropin_fuel
        )
        energy_consumption_medium_range_kerosene = (
            kerosene_share / 100 * energy_consumption_medium_range_dropin_fuel
        )
        energy_consumption_long_range_kerosene = (
            kerosene_share / 100 * energy_consumption_long_range_dropin_fuel
        )
        energy_consumption_passenger_kerosene = (
            energy_consumption_short_range_kerosene
            + energy_consumption_medium_range_kerosene
            + energy_consumption_long_range_kerosene
        )
        energy_consumption_freight_kerosene = (
            kerosene_share / 100 * energy_consumption_freight_dropin_fuel
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
            energy_consumption_short_range_dropin_fuel_without_operations,
            energy_consumption_medium_range_dropin_fuel_without_operations,
            energy_consumption_long_range_dropin_fuel_without_operations,
            energy_consumption_passenger_dropin_fuel_without_operations,
            energy_consumption_freight_dropin_fuel_without_operations,
            energy_consumption_dropin_fuel_without_operations,
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
            energy_consumption_short_range_dropin_fuel,
            energy_consumption_medium_range_dropin_fuel,
            energy_consumption_long_range_dropin_fuel,
            energy_consumption_passenger_dropin_fuel,
            energy_consumption_freight_dropin_fuel,
            energy_consumption_dropin_fuel,
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
        """Hydrogen consumption calculation."""

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
        """Hydrogen consumption calculation."""

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
    def __init__(self, name="energy_consumption", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_short_range_biofuel_without_operations: pd.Series,
        energy_consumption_medium_range_biofuel_without_operations: pd.Series,
        energy_consumption_long_range_biofuel_without_operations: pd.Series,
        energy_consumption_passenger_biofuel_without_operations: pd.Series,
        energy_consumption_freight_biofuel_without_operations: pd.Series,
        energy_consumption_short_range_electrofuel_without_operations: pd.Series,
        energy_consumption_medium_range_electrofuel_without_operations: pd.Series,
        energy_consumption_long_range_electrofuel_without_operations: pd.Series,
        energy_consumption_passenger_electrofuel_without_operations: pd.Series,
        energy_consumption_freight_electrofuel_without_operations: pd.Series,
        energy_consumption_short_range_kerosene_without_operations: pd.Series,
        energy_consumption_medium_range_kerosene_without_operations: pd.Series,
        energy_consumption_long_range_kerosene_without_operations: pd.Series,
        energy_consumption_passenger_kerosene_without_operations: pd.Series,
        energy_consumption_freight_kerosene_without_operations: pd.Series,
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
        energy_consumption_biofuel_without_operations: pd.Series,
        energy_consumption_electrofuel_without_operations: pd.Series,
        energy_consumption_kerosene_without_operations: pd.Series,
        energy_consumption_hydrogen_without_operations: pd.Series,
        energy_consumption_electric_without_operations: pd.Series,
        energy_consumption_short_range_biofuel: pd.Series,
        energy_consumption_medium_range_biofuel: pd.Series,
        energy_consumption_long_range_biofuel: pd.Series,
        energy_consumption_passenger_biofuel: pd.Series,
        energy_consumption_freight_biofuel: pd.Series,
        energy_consumption_short_range_electrofuel: pd.Series,
        energy_consumption_medium_range_electrofuel: pd.Series,
        energy_consumption_long_range_electrofuel: pd.Series,
        energy_consumption_passenger_electrofuel: pd.Series,
        energy_consumption_freight_electrofuel: pd.Series,
        energy_consumption_short_range_kerosene: pd.Series,
        energy_consumption_medium_range_kerosene: pd.Series,
        energy_consumption_long_range_kerosene: pd.Series,
        energy_consumption_passenger_kerosene: pd.Series,
        energy_consumption_freight_kerosene: pd.Series,
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
        energy_consumption_biofuel: pd.Series,
        energy_consumption_electrofuel: pd.Series,
        energy_consumption_kerosene: pd.Series,
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
        """Energy consumption calculation."""

        # WITHOUT OPERATIONS
        energy_consumption_short_range_without_operations = (
            energy_consumption_short_range_biofuel_without_operations
            + energy_consumption_short_range_electrofuel_without_operations
            + energy_consumption_short_range_kerosene_without_operations
            + energy_consumption_short_range_hydrogen_without_operations
            + energy_consumption_short_range_electric_without_operations
        )
        energy_consumption_medium_range_without_operations = (
            energy_consumption_medium_range_biofuel_without_operations
            + energy_consumption_medium_range_electrofuel_without_operations
            + energy_consumption_medium_range_kerosene_without_operations
            + energy_consumption_medium_range_hydrogen_without_operations
            + energy_consumption_medium_range_electric_without_operations
        )
        energy_consumption_long_range_without_operations = (
            energy_consumption_long_range_biofuel_without_operations
            + energy_consumption_long_range_electrofuel_without_operations
            + energy_consumption_long_range_kerosene_without_operations
            + energy_consumption_long_range_hydrogen_without_operations
            + energy_consumption_long_range_electric_without_operations
        )
        energy_consumption_passenger_without_operations = (
            energy_consumption_passenger_biofuel_without_operations
            + energy_consumption_passenger_electrofuel_without_operations
            + energy_consumption_passenger_kerosene_without_operations
            + energy_consumption_passenger_hydrogen_without_operations
            + energy_consumption_passenger_electric_without_operations
        )
        energy_consumption_freight_without_operations = (
            energy_consumption_freight_biofuel_without_operations
            + energy_consumption_freight_electrofuel_without_operations
            + energy_consumption_freight_kerosene_without_operations
            + energy_consumption_freight_hydrogen_without_operations
            + energy_consumption_freight_electric_without_operations
        )
        energy_consumption_without_operations = (
            energy_consumption_biofuel_without_operations
            + energy_consumption_electrofuel_without_operations
            + energy_consumption_kerosene_without_operations
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
            energy_consumption_short_range_biofuel
            + energy_consumption_short_range_electrofuel
            + energy_consumption_short_range_kerosene
            + energy_consumption_short_range_hydrogen
            + energy_consumption_short_range_electric
        )
        energy_consumption_medium_range = (
            energy_consumption_medium_range_biofuel
            + energy_consumption_medium_range_electrofuel
            + energy_consumption_medium_range_kerosene
            + energy_consumption_medium_range_hydrogen
            + energy_consumption_medium_range_electric
        )
        energy_consumption_long_range = (
            energy_consumption_long_range_biofuel
            + energy_consumption_long_range_electrofuel
            + energy_consumption_long_range_kerosene
            + energy_consumption_long_range_hydrogen
            + energy_consumption_long_range_electric
        )
        energy_consumption_passenger = (
            energy_consumption_passenger_biofuel
            + energy_consumption_passenger_electrofuel
            + energy_consumption_passenger_kerosene
            + energy_consumption_passenger_hydrogen
            + energy_consumption_passenger_electric
        )
        energy_consumption_freight = (
            energy_consumption_freight_biofuel
            + energy_consumption_freight_electrofuel
            + energy_consumption_freight_kerosene
            + energy_consumption_freight_hydrogen
            + energy_consumption_freight_electric
        )
        energy_consumption = (
            energy_consumption_biofuel
            + energy_consumption_electrofuel
            + energy_consumption_kerosene
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

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


class DropinFuelPathwayConsumptionAndGrowth(AeroMAPSModel):
    def __init__(self, name="dropin_fuel_pathway_consumption_and_growth", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_biofuel: pd.Series,
        energy_consumption_electrofuel: pd.Series,
        energy_consumption_kerosene: pd.Series,
        biofuel_hefa_fog_share: pd.Series,
        biofuel_hefa_others_share: pd.Series,
        biofuel_ft_others_share: pd.Series,
        biofuel_ft_msw_share: pd.Series,
        biofuel_atj_share: pd.Series,
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
        """Dropin fuel pathway consumption and growth calculation."""

        # Biofuel
        energy_consumption_biofuel_hefa_fog = (
            biofuel_hefa_fog_share / 100 * energy_consumption_biofuel
        )
        energy_consumption_biofuel_hefa_others = (
            biofuel_hefa_others_share / 100 * energy_consumption_biofuel
        )
        energy_consumption_biofuel_ft_others = (
            biofuel_ft_others_share / 100 * energy_consumption_biofuel
        )
        energy_consumption_biofuel_ft_msw = biofuel_ft_msw_share / 100 * energy_consumption_biofuel
        energy_consumption_biofuel_atj = biofuel_atj_share / 100 * energy_consumption_biofuel

        self.df.loc[:, "energy_consumption_biofuel_hefa_fog"] = energy_consumption_biofuel_hefa_fog
        self.df.loc[
            :, "energy_consumption_biofuel_hefa_others"
        ] = energy_consumption_biofuel_hefa_others
        self.df.loc[
            :, "energy_consumption_biofuel_ft_others"
        ] = energy_consumption_biofuel_ft_others
        self.df.loc[:, "energy_consumption_biofuel_ft_msw"] = energy_consumption_biofuel_ft_msw
        self.df.loc[:, "energy_consumption_biofuel_atj"] = energy_consumption_biofuel_atj

        # No need for pathway computation for electrofuel and kerosene as they are already known: no sub-pathway.

        # Growth for each pathway

        # Biofuel
        annual_growth_biofuel_hefa_fog = energy_consumption_biofuel_hefa_fog.pct_change() * 100
        annual_growth_biofuel_hefa_others = (
            energy_consumption_biofuel_hefa_others.pct_change() * 100
        )
        annual_growth_biofuel_ft_others = energy_consumption_biofuel_ft_others.pct_change() * 100
        annual_growth_biofuel_ft_msw = energy_consumption_biofuel_ft_msw.pct_change() * 100
        annual_growth_biofuel_atj = energy_consumption_biofuel_atj.pct_change() * 100

        self.df.loc[:, "annual_growth_biofuel_hefa_fog"] = annual_growth_biofuel_hefa_fog
        self.df.loc[:, "annual_growth_biofuel_hefa_others"] = annual_growth_biofuel_hefa_others
        self.df.loc[:, "annual_growth_biofuel_ft_others"] = annual_growth_biofuel_ft_others
        self.df.loc[:, "annual_growth_biofuel_ft_msw"] = annual_growth_biofuel_ft_msw
        self.df.loc[:, "annual_growth_biofuel_atj"] = annual_growth_biofuel_atj

        # Electrofuel
        annual_growth_electrofuel = energy_consumption_electrofuel.pct_change() * 100
        self.df.loc[:, "annual_growth_electrofuel"] = annual_growth_electrofuel

        # Kerosene
        annual_growth_kerosene = energy_consumption_kerosene.pct_change() * 100
        self.df.loc[:, "annual_growth_kerosene"] = annual_growth_kerosene

        return (
            energy_consumption_biofuel_hefa_fog,
            energy_consumption_biofuel_hefa_others,
            energy_consumption_biofuel_ft_others,
            energy_consumption_biofuel_ft_msw,
            energy_consumption_biofuel_atj,
            annual_growth_biofuel_hefa_fog,
            annual_growth_biofuel_hefa_others,
            annual_growth_biofuel_ft_others,
            annual_growth_biofuel_ft_msw,
            annual_growth_biofuel_atj,
            annual_growth_electrofuel,
            annual_growth_kerosene,
        )


class HydrogenPathwayConsumptionAndGrowth(AeroMAPSModel):
    def __init__(self, name="hydrogen_pathway_consumption_and_growth", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_hydrogen: pd.Series,
        hydrogen_electrolysis_share: pd.Series,
        hydrogen_gas_ccs_share: pd.Series,
        hydrogen_coal_ccs_share: pd.Series,
        hydrogen_gas_share: pd.Series,
        hydrogen_coal_share: pd.Series,
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
    ]:
        """Hydrogen pathway consumption and growth calculation."""
        energy_consumption_hydrogen_electrolysis = (
            hydrogen_electrolysis_share / 100 * energy_consumption_hydrogen
        )
        energy_consumption_hydrogen_gas_ccs = (
            hydrogen_gas_ccs_share / 100 * energy_consumption_hydrogen
        )
        energy_consumption_hydrogen_coal_ccs = (
            hydrogen_coal_ccs_share / 100 * energy_consumption_hydrogen
        )
        energy_consumption_hydrogen_gas = hydrogen_gas_share / 100 * energy_consumption_hydrogen
        energy_consumption_hydrogen_coal = hydrogen_coal_share / 100 * energy_consumption_hydrogen

        self.df.loc[
            :, "energy_consumption_hydrogen_electrolysis"
        ] = energy_consumption_hydrogen_electrolysis
        self.df.loc[:, "energy_consumption_hydrogen_gas_ccs"] = energy_consumption_hydrogen_gas_ccs
        self.df.loc[
            :, "energy_consumption_hydrogen_coal_ccs"
        ] = energy_consumption_hydrogen_coal_ccs
        self.df.loc[:, "energy_consumption_hydrogen_gas"] = energy_consumption_hydrogen_gas
        self.df.loc[:, "energy_consumption_hydrogen_coal"] = energy_consumption_hydrogen_coal

        # Growth for each pathway

        annual_growth_hydrogen_electrolysis = (
            energy_consumption_hydrogen_electrolysis.pct_change() * 100
        )
        annual_growth_hydrogen_gas_ccs = energy_consumption_hydrogen_gas_ccs.pct_change() * 100
        annual_growth_hydrogen_coal_ccs = energy_consumption_hydrogen_coal_ccs.pct_change() * 100
        annual_growth_hydrogen_gas = energy_consumption_hydrogen_gas.pct_change() * 100
        annual_growth_hydrogen_coal = energy_consumption_hydrogen_coal.pct_change() * 100

        self.df.loc[:, "annual_growth_hydrogen_electrolysis"] = annual_growth_hydrogen_electrolysis
        self.df.loc[:, "annual_growth_hydrogen_gas_ccs"] = annual_growth_hydrogen_gas_ccs
        self.df.loc[:, "annual_growth_hydrogen_coal_ccs"] = annual_growth_hydrogen_coal_ccs
        self.df.loc[:, "annual_growth_hydrogen_gas"] = annual_growth_hydrogen_gas
        self.df.loc[:, "annual_growth_hydrogen_coal"] = annual_growth_hydrogen_coal

        return (
            energy_consumption_hydrogen_electrolysis,
            energy_consumption_hydrogen_gas_ccs,
            energy_consumption_hydrogen_coal_ccs,
            energy_consumption_hydrogen_gas,
            energy_consumption_hydrogen_coal,
            annual_growth_hydrogen_electrolysis,
            annual_growth_hydrogen_gas_ccs,
            annual_growth_hydrogen_coal_ccs,
            annual_growth_hydrogen_gas,
            annual_growth_hydrogen_coal,
        )


class ElectricPathwayConsumptionAndGrowth(AeroMAPSModel):
    def __init__(self, name="electric_pathway_consumption_and_growth", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_electric: pd.Series,
    ) -> Tuple[pd.Series,]:
        """Electric pathway consumption and growth calculation."""
        # No need for pathway computation for electric aircraft they are already known: no sub-pathway.
        # Growth
        annual_growth_battery_electric = energy_consumption_electric.pct_change() * 100
        self.df.loc[:, "annual_growth_battery_electric"] = annual_growth_battery_electric
        return (annual_growth_battery_electric,)

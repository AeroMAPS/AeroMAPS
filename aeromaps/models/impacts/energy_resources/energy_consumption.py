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
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        """
        Build input_names / output_names dynamically from the MarketManager.
        Called once by AeroMAPSProcess after self.markets is injected.
        """
        self.input_names = {}
        self.output_names = {}

        passenger_markets = list(self.markets.get(traffic_type="passenger"))
        freight_markets = list(self.markets.get(traffic_type="freight"))

        # Per-market inputs and outputs (passenger: ask-based; freight: rtk-based).
        for market in passenger_markets:
            mid = market.id
            self.input_names[f"ask_{mid}_dropin_fuel"] = pd.Series([0.0])
            self.input_names[f"energy_per_ask_without_operations_{mid}_dropin_fuel"] = pd.Series(
                [0.0]
            )
            self.input_names[f"energy_per_ask_{mid}_dropin_fuel"] = pd.Series([0.0])
            self.output_names[f"energy_consumption_{mid}_dropin_fuel_without_operations"] = (
                pd.Series([0.0])
            )
            self.output_names[f"energy_consumption_{mid}_dropin_fuel"] = pd.Series([0.0])

        for market in freight_markets:
            mid = market.id
            self.input_names[f"rtk_{mid}_dropin_fuel"] = pd.Series([0.0])
            self.input_names[f"energy_per_rtk_without_operations_{mid}_dropin_fuel"] = pd.Series(
                [0.0]
            )
            self.input_names[f"energy_per_rtk_{mid}_dropin_fuel"] = pd.Series([0.0])
            self.output_names[f"energy_consumption_{mid}_dropin_fuel_without_operations"] = (
                pd.Series([0.0])
            )
            self.output_names[f"energy_consumption_{mid}_dropin_fuel"] = pd.Series([0.0])

        # Aggregate outputs (passenger sum, freight sum, grand total) — both with and without operations.
        self.output_names["energy_consumption_passenger_dropin_fuel_without_operations"] = (
            pd.Series([0.0])
        )
        self.output_names["energy_consumption_passenger_dropin_fuel"] = pd.Series([0.0])
        self.output_names["energy_consumption_freight_dropin_fuel_without_operations"] = pd.Series(
            [0.0]
        )
        self.output_names["energy_consumption_freight_dropin_fuel"] = pd.Series([0.0])
        self.output_names["energy_consumption_dropin_fuel_without_operations"] = pd.Series([0.0])
        self.output_names["energy_consumption_dropin_fuel"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        Drop-in fuel energy consumption per market and aggregates.

        Per-market: energy = energy_per_(ask|rtk) * (ask|rtk).
        Aggregates: passenger sum over passenger markets, freight sum over freight
        markets, grand total = passenger + freight. Both with-operations and
        without-operations variants are produced.
        """
        output_data = {}

        passenger_markets = list(self.markets.get(traffic_type="passenger"))
        freight_markets = list(self.markets.get(traffic_type="freight"))

        # Per-passenger-market consumption.
        passenger_total_with = None
        passenger_total_without = None
        for market in passenger_markets:
            mid = market.id
            ask = input_data[f"ask_{mid}_dropin_fuel"]
            eps_without = input_data[f"energy_per_ask_without_operations_{mid}_dropin_fuel"]
            eps_with = input_data[f"energy_per_ask_{mid}_dropin_fuel"]

            ec_without = eps_without * ask
            ec_with = eps_with * ask

            output_data[f"energy_consumption_{mid}_dropin_fuel_without_operations"] = ec_without
            output_data[f"energy_consumption_{mid}_dropin_fuel"] = ec_with

            passenger_total_without = (
                ec_without
                if passenger_total_without is None
                else passenger_total_without + ec_without
            )
            passenger_total_with = (
                ec_with if passenger_total_with is None else passenger_total_with + ec_with
            )

        # Per-freight-market consumption.
        freight_total_with = None
        freight_total_without = None
        for market in freight_markets:
            mid = market.id
            rtk = input_data[f"rtk_{mid}_dropin_fuel"]
            eps_without = input_data[f"energy_per_rtk_without_operations_{mid}_dropin_fuel"]
            eps_with = input_data[f"energy_per_rtk_{mid}_dropin_fuel"]

            ec_without = eps_without * rtk
            ec_with = eps_with * rtk

            output_data[f"energy_consumption_{mid}_dropin_fuel_without_operations"] = ec_without
            output_data[f"energy_consumption_{mid}_dropin_fuel"] = ec_with

            freight_total_without = (
                ec_without if freight_total_without is None else freight_total_without + ec_without
            )
            freight_total_with = (
                ec_with if freight_total_with is None else freight_total_with + ec_with
            )

        # Default to zero series when no markets in a traffic_type (defensive — should not happen
        # for the default 4-market config, but custom configs may have e.g. zero freight markets).
        if passenger_total_without is None:
            passenger_total_without = pd.Series(0.0, index=self.df.index)
        if passenger_total_with is None:
            passenger_total_with = pd.Series(0.0, index=self.df.index)
        if freight_total_without is None:
            freight_total_without = pd.Series(0.0, index=self.df.index)
        if freight_total_with is None:
            freight_total_with = pd.Series(0.0, index=self.df.index)

        output_data["energy_consumption_passenger_dropin_fuel_without_operations"] = (
            passenger_total_without
        )
        output_data["energy_consumption_passenger_dropin_fuel"] = passenger_total_with
        output_data["energy_consumption_freight_dropin_fuel_without_operations"] = (
            freight_total_without
        )
        output_data["energy_consumption_freight_dropin_fuel"] = freight_total_with
        output_data["energy_consumption_dropin_fuel_without_operations"] = (
            passenger_total_without + freight_total_without
        )
        output_data["energy_consumption_dropin_fuel"] = passenger_total_with + freight_total_with

        self._store_outputs(output_data)
        return output_data


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

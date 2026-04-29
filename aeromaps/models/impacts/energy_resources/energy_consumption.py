"""
energy_consumption
===================================
Module to compute energy consumption from different aircraft types.
"""

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class DropInFuelConsumption(AeroMAPSModel):
    """
    Total drop-in fuel consumption calculation.

    Parameters
    --------------
    name : str
        Name of the model instance ('drop_in_fuel_consumption' by default).

    Documentation
    --------------
    Inputs
        - ask_<market>_dropin_fuel: Passenger ASK for drop-in fuel aircraft [ASK].
        - rtk_<market>_dropin_fuel: Freight RTK for drop-in fuel aircraft [RTK].
        - energy_per_ask_without_operations_<market>_dropin_fuel: Passenger MJ/ASK (no ops).
        - energy_per_ask_<market>_dropin_fuel: Passenger MJ/ASK (with ops).
        - energy_per_rtk_without_operations_<market>_dropin_fuel: Freight MJ/RTK (no ops).
        - energy_per_rtk_<market>_dropin_fuel: Freight MJ/RTK (with ops).
    Outputs
        - energy_consumption_<market>_dropin_fuel_without_operations: Per-market drop-in [MJ].
        - energy_consumption_<market>_dropin_fuel: Per-market drop-in [MJ].
        - energy_consumption_passenger_dropin_fuel_without_operations: Passenger total [MJ].
        - energy_consumption_freight_dropin_fuel_without_operations: Freight total [MJ].
        - energy_consumption_dropin_fuel_without_operations: Passenger + freight [MJ].
        - energy_consumption_passenger_dropin_fuel: Passenger total [MJ].
        - energy_consumption_freight_dropin_fuel: Freight total [MJ].
        - energy_consumption_dropin_fuel: Passenger + freight [MJ].
    Notes
        - <market> is the MarketManager id (passenger and freight markets).
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
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

    Documentation
    --------------
    Inputs
        - biomass_share_dropin_fuel: Share of biomass-based fuels in drop-in fuels [%].
        - electricity_share_dropin_fuel: Share of electricity-based fuels in drop-in fuels [%].
        - fossil_share_dropin_fuel: Share of fossil-based fuels in drop-in fuels [%].
        - energy_consumption_<market>_dropin_fuel_without_operations: Drop-in fuel energy (no ops) [MJ].
        - energy_consumption_<market>_dropin_fuel: Drop-in fuel energy (with ops) [MJ].
    Outputs
        - energy_consumption_<market>_<fuel>_without_operations: Per-market split by fuel [MJ].
        - energy_consumption_<market>_<fuel>: Per-market split by fuel [MJ].
        - energy_consumption_passenger_<fuel>_without_operations: Passenger total [MJ].
        - energy_consumption_freight_<fuel>_without_operations: Freight total [MJ].
        - energy_consumption_<fuel>_without_operations: Passenger + freight [MJ].
        - energy_consumption_passenger_<fuel>: Passenger total [MJ].
        - energy_consumption_freight_<fuel>: Freight total [MJ].
        - energy_consumption_<fuel>: Passenger + freight [MJ].
    Notes
        - <market> is the MarketManager id (passenger and freight markets).
        - <fuel> is one of: biofuel, electrofuel, kerosene.
        - I/O names are generated from configuration and passed to GEMSEO via
            self.input_names and self.output_names grammars.
    """

    def __init__(self, name="drop_in_fuel_detailled_consumption", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        self.input_names = {
            "biomass_share_dropin_fuel": pd.Series([0.0]),
            "electricity_share_dropin_fuel": pd.Series([0.0]),
            "fossil_share_dropin_fuel": pd.Series([0.0]),
        }
        self.output_names = {}

        passenger_markets = list(self.markets.get(traffic_type="passenger"))
        freight_markets = list(self.markets.get(traffic_type="freight"))

        for market in passenger_markets + freight_markets:
            mid = market.id
            self.input_names[f"energy_consumption_{mid}_dropin_fuel_without_operations"] = (
                pd.Series([0.0])
            )
            self.input_names[f"energy_consumption_{mid}_dropin_fuel"] = pd.Series([0.0])
            for fuel in ["biofuel", "electrofuel", "kerosene"]:
                self.output_names[f"energy_consumption_{mid}_{fuel}_without_operations"] = (
                    pd.Series([0.0])
                )
                self.output_names[f"energy_consumption_{mid}_{fuel}"] = pd.Series([0.0])

        for fuel in ["biofuel", "electrofuel", "kerosene"]:
            self.output_names[f"energy_consumption_passenger_{fuel}_without_operations"] = (
                pd.Series([0.0])
            )
            self.output_names[f"energy_consumption_freight_{fuel}_without_operations"] = pd.Series(
                [0.0]
            )
            self.output_names[f"energy_consumption_{fuel}_without_operations"] = pd.Series([0.0])
            self.output_names[f"energy_consumption_passenger_{fuel}"] = pd.Series([0.0])
            self.output_names[f"energy_consumption_freight_{fuel}"] = pd.Series([0.0])
            self.output_names[f"energy_consumption_{fuel}"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """Drop-in fuel detailed consumption per market and aggregates."""
        output_data = {}

        passenger_markets = list(self.markets.get(traffic_type="passenger"))
        freight_markets = list(self.markets.get(traffic_type="freight"))

        shares = {
            "biofuel": input_data["biomass_share_dropin_fuel"] / 100,
            "electrofuel": input_data["electricity_share_dropin_fuel"] / 100,
            "kerosene": input_data["fossil_share_dropin_fuel"] / 100,
        }

        passenger_totals_without = {fuel: None for fuel in shares}
        passenger_totals_with = {fuel: None for fuel in shares}
        freight_totals_without = {fuel: None for fuel in shares}
        freight_totals_with = {fuel: None for fuel in shares}

        for market in passenger_markets:
            mid = market.id
            ec_without = input_data[f"energy_consumption_{mid}_dropin_fuel_without_operations"]
            ec_with = input_data[f"energy_consumption_{mid}_dropin_fuel"]
            for fuel, share in shares.items():
                fuel_without = share * ec_without
                fuel_with = share * ec_with
                output_data[f"energy_consumption_{mid}_{fuel}_without_operations"] = fuel_without
                output_data[f"energy_consumption_{mid}_{fuel}"] = fuel_with
                passenger_totals_without[fuel] = (
                    fuel_without
                    if passenger_totals_without[fuel] is None
                    else passenger_totals_without[fuel] + fuel_without
                )
                passenger_totals_with[fuel] = (
                    fuel_with
                    if passenger_totals_with[fuel] is None
                    else passenger_totals_with[fuel] + fuel_with
                )

        for market in freight_markets:
            mid = market.id
            ec_without = input_data[f"energy_consumption_{mid}_dropin_fuel_without_operations"]
            ec_with = input_data[f"energy_consumption_{mid}_dropin_fuel"]
            for fuel, share in shares.items():
                fuel_without = share * ec_without
                fuel_with = share * ec_with
                output_data[f"energy_consumption_{mid}_{fuel}_without_operations"] = fuel_without
                output_data[f"energy_consumption_{mid}_{fuel}"] = fuel_with
                freight_totals_without[fuel] = (
                    fuel_without
                    if freight_totals_without[fuel] is None
                    else freight_totals_without[fuel] + fuel_without
                )
                freight_totals_with[fuel] = (
                    fuel_with
                    if freight_totals_with[fuel] is None
                    else freight_totals_with[fuel] + fuel_with
                )

        for fuel in shares:
            if passenger_totals_without[fuel] is None:
                passenger_totals_without[fuel] = pd.Series(0.0, index=self.df.index)
            if passenger_totals_with[fuel] is None:
                passenger_totals_with[fuel] = pd.Series(0.0, index=self.df.index)
            if freight_totals_without[fuel] is None:
                freight_totals_without[fuel] = pd.Series(0.0, index=self.df.index)
            if freight_totals_with[fuel] is None:
                freight_totals_with[fuel] = pd.Series(0.0, index=self.df.index)

            output_data[f"energy_consumption_passenger_{fuel}_without_operations"] = (
                passenger_totals_without[fuel]
            )
            output_data[f"energy_consumption_freight_{fuel}_without_operations"] = (
                freight_totals_without[fuel]
            )
            output_data[f"energy_consumption_{fuel}_without_operations"] = (
                passenger_totals_without[fuel] + freight_totals_without[fuel]
            )
            output_data[f"energy_consumption_passenger_{fuel}"] = passenger_totals_with[fuel]
            output_data[f"energy_consumption_freight_{fuel}"] = freight_totals_with[fuel]
            output_data[f"energy_consumption_{fuel}"] = (
                passenger_totals_with[fuel] + freight_totals_with[fuel]
            )

        self._store_outputs(output_data)
        return output_data


class HydrogenConsumption(AeroMAPSModel):
    """
    Class to calculate hydrogen consumption for each type of market.

    Parameters
    --------------
    name : str
        Name of the model instance ('hydrogen_consumption' by default).

    Documentation
    --------------
    Inputs
        - ask_<market>_hydrogen: Passenger ASK for hydrogen aircraft [ASK].
        - rtk_<market>_hydrogen: Freight RTK for hydrogen aircraft [RTK].
        - energy_per_ask_without_operations_<market>_hydrogen: Passenger MJ/ASK (no ops).
        - energy_per_ask_<market>_hydrogen: Passenger MJ/ASK (with ops).
        - energy_per_rtk_without_operations_<market>_hydrogen: Freight MJ/RTK (no ops).
        - energy_per_rtk_<market>_hydrogen: Freight MJ/RTK (with ops).
    Outputs
        - energy_consumption_<market>_hydrogen_without_operations: Per-market hydrogen [MJ].
        - energy_consumption_<market>_hydrogen: Per-market hydrogen [MJ].
        - energy_consumption_passenger_hydrogen_without_operations: Passenger total [MJ].
        - energy_consumption_freight_hydrogen_without_operations: Freight total [MJ].
        - energy_consumption_hydrogen_without_operations: Passenger + freight [MJ].
        - energy_consumption_passenger_hydrogen: Passenger total [MJ].
        - energy_consumption_freight_hydrogen: Freight total [MJ].
        - energy_consumption_hydrogen: Passenger + freight [MJ].
    Notes
        - <market> is the MarketManager id (passenger and freight markets).
        - I/O names are generated from configuration and passed to GEMSEO via
            self.input_names and self.output_names grammars.
    """

    def __init__(self, name="hydrogen_consumption", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        self.input_names = {}
        self.output_names = {}

        passenger_markets = list(self.markets.get(traffic_type="passenger"))
        freight_markets = list(self.markets.get(traffic_type="freight"))

        for market in passenger_markets:
            mid = market.id
            self.input_names[f"ask_{mid}_hydrogen"] = pd.Series([0.0])
            self.input_names[f"energy_per_ask_without_operations_{mid}_hydrogen"] = pd.Series([0.0])
            self.input_names[f"energy_per_ask_{mid}_hydrogen"] = pd.Series([0.0])
            self.output_names[f"energy_consumption_{mid}_hydrogen_without_operations"] = pd.Series(
                [0.0]
            )
            self.output_names[f"energy_consumption_{mid}_hydrogen"] = pd.Series([0.0])

        for market in freight_markets:
            mid = market.id
            self.input_names[f"rtk_{mid}_hydrogen"] = pd.Series([0.0])
            self.input_names[f"energy_per_rtk_without_operations_{mid}_hydrogen"] = pd.Series([0.0])
            self.input_names[f"energy_per_rtk_{mid}_hydrogen"] = pd.Series([0.0])
            self.output_names[f"energy_consumption_{mid}_hydrogen_without_operations"] = pd.Series(
                [0.0]
            )
            self.output_names[f"energy_consumption_{mid}_hydrogen"] = pd.Series([0.0])

        self.output_names["energy_consumption_passenger_hydrogen_without_operations"] = pd.Series(
            [0.0]
        )
        self.output_names["energy_consumption_freight_hydrogen_without_operations"] = pd.Series(
            [0.0]
        )
        self.output_names["energy_consumption_hydrogen_without_operations"] = pd.Series([0.0])
        self.output_names["energy_consumption_passenger_hydrogen"] = pd.Series([0.0])
        self.output_names["energy_consumption_freight_hydrogen"] = pd.Series([0.0])
        self.output_names["energy_consumption_hydrogen"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """Hydrogen consumption per market and aggregates."""
        output_data = {}

        passenger_markets = list(self.markets.get(traffic_type="passenger"))
        freight_markets = list(self.markets.get(traffic_type="freight"))

        passenger_total_without = None
        passenger_total_with = None
        for market in passenger_markets:
            mid = market.id
            ask = input_data[f"ask_{mid}_hydrogen"]
            eps_without = input_data[f"energy_per_ask_without_operations_{mid}_hydrogen"]
            eps_with = input_data[f"energy_per_ask_{mid}_hydrogen"]

            ec_without = eps_without * ask
            ec_with = eps_with * ask

            output_data[f"energy_consumption_{mid}_hydrogen_without_operations"] = ec_without
            output_data[f"energy_consumption_{mid}_hydrogen"] = ec_with

            passenger_total_without = (
                ec_without
                if passenger_total_without is None
                else passenger_total_without + ec_without
            )
            passenger_total_with = (
                ec_with if passenger_total_with is None else passenger_total_with + ec_with
            )

        freight_total_without = None
        freight_total_with = None
        for market in freight_markets:
            mid = market.id
            rtk = input_data[f"rtk_{mid}_hydrogen"]
            eps_without = input_data[f"energy_per_rtk_without_operations_{mid}_hydrogen"]
            eps_with = input_data[f"energy_per_rtk_{mid}_hydrogen"]

            ec_without = eps_without * rtk
            ec_with = eps_with * rtk

            output_data[f"energy_consumption_{mid}_hydrogen_without_operations"] = ec_without
            output_data[f"energy_consumption_{mid}_hydrogen"] = ec_with

            freight_total_without = (
                ec_without if freight_total_without is None else freight_total_without + ec_without
            )
            freight_total_with = (
                ec_with if freight_total_with is None else freight_total_with + ec_with
            )

        if passenger_total_without is None:
            passenger_total_without = pd.Series(0.0, index=self.df.index)
        if passenger_total_with is None:
            passenger_total_with = pd.Series(0.0, index=self.df.index)
        if freight_total_without is None:
            freight_total_without = pd.Series(0.0, index=self.df.index)
        if freight_total_with is None:
            freight_total_with = pd.Series(0.0, index=self.df.index)

        output_data["energy_consumption_passenger_hydrogen_without_operations"] = (
            passenger_total_without
        )
        output_data["energy_consumption_freight_hydrogen_without_operations"] = (
            freight_total_without
        )
        output_data["energy_consumption_hydrogen_without_operations"] = (
            passenger_total_without + freight_total_without
        )
        output_data["energy_consumption_passenger_hydrogen"] = passenger_total_with
        output_data["energy_consumption_freight_hydrogen"] = freight_total_with
        output_data["energy_consumption_hydrogen"] = passenger_total_with + freight_total_with

        self._store_outputs(output_data)
        return output_data


class ElectricConsumption(AeroMAPSModel):
    """
    Class to calculate electricity consumption for each type of market.

    Parameters
    --------------
    name : str
        Name of the model instance ('electric_consumption' by default).

    Documentation
    --------------
    Inputs
        - ask_<market>_electric: Passenger ASK for electric aircraft [ASK].
        - rtk_<market>_electric: Freight RTK for electric aircraft [RTK].
        - energy_per_ask_without_operations_<market>_electric: Passenger MJ/ASK (no ops).
        - energy_per_ask_<market>_electric: Passenger MJ/ASK (with ops).
        - energy_per_rtk_without_operations_<market>_electric: Freight MJ/RTK (no ops).
        - energy_per_rtk_<market>_electric: Freight MJ/RTK (with ops).
    Outputs
        - energy_consumption_<market>_electric_without_operations: Per-market electricity [MJ].
        - energy_consumption_<market>_electric: Per-market electricity [MJ].
        - energy_consumption_passenger_electric_without_operations: Passenger total [MJ].
        - energy_consumption_freight_electric_without_operations: Freight total [MJ].
        - energy_consumption_electric_without_operations: Passenger + freight [MJ].
        - energy_consumption_passenger_electric: Passenger total [MJ].
        - energy_consumption_freight_electric: Freight total [MJ].
        - energy_consumption_electric: Passenger + freight [MJ].
    Notes
        - <market> is the MarketManager id (passenger and freight markets).
        - I/O names are generated from configuration and passed to GEMSEO via
            self.input_names and self.output_names grammars.
    """

    def __init__(self, name="electric_consumption", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        self.input_names = {}
        self.output_names = {}

        passenger_markets = list(self.markets.get(traffic_type="passenger"))
        freight_markets = list(self.markets.get(traffic_type="freight"))

        for market in passenger_markets:
            mid = market.id
            self.input_names[f"ask_{mid}_electric"] = pd.Series([0.0])
            self.input_names[f"energy_per_ask_without_operations_{mid}_electric"] = pd.Series([0.0])
            self.input_names[f"energy_per_ask_{mid}_electric"] = pd.Series([0.0])
            self.output_names[f"energy_consumption_{mid}_electric_without_operations"] = pd.Series(
                [0.0]
            )
            self.output_names[f"energy_consumption_{mid}_electric"] = pd.Series([0.0])

        for market in freight_markets:
            mid = market.id
            self.input_names[f"rtk_{mid}_electric"] = pd.Series([0.0])
            self.input_names[f"energy_per_rtk_without_operations_{mid}_electric"] = pd.Series([0.0])
            self.input_names[f"energy_per_rtk_{mid}_electric"] = pd.Series([0.0])
            self.output_names[f"energy_consumption_{mid}_electric_without_operations"] = pd.Series(
                [0.0]
            )
            self.output_names[f"energy_consumption_{mid}_electric"] = pd.Series([0.0])

        self.output_names["energy_consumption_passenger_electric_without_operations"] = pd.Series(
            [0.0]
        )
        self.output_names["energy_consumption_freight_electric_without_operations"] = pd.Series(
            [0.0]
        )
        self.output_names["energy_consumption_electric_without_operations"] = pd.Series([0.0])
        self.output_names["energy_consumption_passenger_electric"] = pd.Series([0.0])
        self.output_names["energy_consumption_freight_electric"] = pd.Series([0.0])
        self.output_names["energy_consumption_electric"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """Electricity consumption per market and aggregates."""
        output_data = {}

        passenger_markets = list(self.markets.get(traffic_type="passenger"))
        freight_markets = list(self.markets.get(traffic_type="freight"))

        passenger_total_without = None
        passenger_total_with = None
        for market in passenger_markets:
            mid = market.id
            ask = input_data[f"ask_{mid}_electric"]
            eps_without = input_data[f"energy_per_ask_without_operations_{mid}_electric"]
            eps_with = input_data[f"energy_per_ask_{mid}_electric"]

            ec_without = eps_without * ask
            ec_with = eps_with * ask

            output_data[f"energy_consumption_{mid}_electric_without_operations"] = ec_without
            output_data[f"energy_consumption_{mid}_electric"] = ec_with

            passenger_total_without = (
                ec_without
                if passenger_total_without is None
                else passenger_total_without + ec_without
            )
            passenger_total_with = (
                ec_with if passenger_total_with is None else passenger_total_with + ec_with
            )

        freight_total_without = None
        freight_total_with = None
        for market in freight_markets:
            mid = market.id
            rtk = input_data[f"rtk_{mid}_electric"]
            eps_without = input_data[f"energy_per_rtk_without_operations_{mid}_electric"]
            eps_with = input_data[f"energy_per_rtk_{mid}_electric"]

            ec_without = eps_without * rtk
            ec_with = eps_with * rtk

            output_data[f"energy_consumption_{mid}_electric_without_operations"] = ec_without
            output_data[f"energy_consumption_{mid}_electric"] = ec_with

            freight_total_without = (
                ec_without if freight_total_without is None else freight_total_without + ec_without
            )
            freight_total_with = (
                ec_with if freight_total_with is None else freight_total_with + ec_with
            )

        if passenger_total_without is None:
            passenger_total_without = pd.Series(0.0, index=self.df.index)
        if passenger_total_with is None:
            passenger_total_with = pd.Series(0.0, index=self.df.index)
        if freight_total_without is None:
            freight_total_without = pd.Series(0.0, index=self.df.index)
        if freight_total_with is None:
            freight_total_with = pd.Series(0.0, index=self.df.index)

        output_data["energy_consumption_passenger_electric_without_operations"] = (
            passenger_total_without
        )
        output_data["energy_consumption_freight_electric_without_operations"] = (
            freight_total_without
        )
        output_data["energy_consumption_electric_without_operations"] = (
            passenger_total_without + freight_total_without
        )
        output_data["energy_consumption_passenger_electric"] = passenger_total_with
        output_data["energy_consumption_freight_electric"] = freight_total_with
        output_data["energy_consumption_electric"] = passenger_total_with + freight_total_with

        self._store_outputs(output_data)
        return output_data


class EnergyConsumption(AeroMAPSModel):
    """
    Class to calculate total energy consumption for each type of market, aggregating all energy sources.

    Documentation
    --------------
    Inputs
        - energy_consumption_<market>_dropin_fuel_without_operations: Drop-in fuel [MJ].
        - energy_consumption_<market>_hydrogen_without_operations: Hydrogen [MJ].
        - energy_consumption_<market>_electric_without_operations: Electricity [MJ].
        - energy_consumption_<market>_dropin_fuel: Drop-in fuel [MJ].
        - energy_consumption_<market>_hydrogen: Hydrogen [MJ].
        - energy_consumption_<market>_electric: Electricity [MJ].
    Outputs
        - energy_consumption_<market>_without_operations: Per-market total [MJ].
        - energy_consumption_<market>: Per-market total [MJ].
        - energy_consumption_passenger_without_operations: Passenger total [MJ].
        - energy_consumption_freight_without_operations: Freight total [MJ].
        - energy_consumption_without_operations: Passenger + freight [MJ].
        - energy_consumption_passenger: Passenger total [MJ].
        - energy_consumption_freight: Freight total [MJ].
        - energy_consumption: Passenger + freight [MJ].
    Notes
        - <market> is the MarketManager id (passenger and freight markets).
        - I/O names are generated from configuration and passed to GEMSEO via
            self.input_names and self.output_names grammars.
    """

    def __init__(self, name="energy_consumption", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        self.input_names = {}
        self.output_names = {}

        passenger_markets = list(self.markets.get(traffic_type="passenger"))
        freight_markets = list(self.markets.get(traffic_type="freight"))

        for market in passenger_markets + freight_markets:
            mid = market.id
            for fuel in ["dropin_fuel", "hydrogen", "electric"]:
                self.input_names[f"energy_consumption_{mid}_{fuel}_without_operations"] = pd.Series(
                    [0.0]
                )
                self.input_names[f"energy_consumption_{mid}_{fuel}"] = pd.Series([0.0])
            self.output_names[f"energy_consumption_{mid}_without_operations"] = pd.Series([0.0])
            self.output_names[f"energy_consumption_{mid}"] = pd.Series([0.0])

        self.output_names["energy_consumption_passenger_without_operations"] = pd.Series([0.0])
        self.output_names["energy_consumption_freight_without_operations"] = pd.Series([0.0])
        self.output_names["energy_consumption_without_operations"] = pd.Series([0.0])
        self.output_names["energy_consumption_passenger"] = pd.Series([0.0])
        self.output_names["energy_consumption_freight"] = pd.Series([0.0])
        self.output_names["energy_consumption"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """Total energy consumption per market and aggregates."""
        output_data = {}

        passenger_markets = list(self.markets.get(traffic_type="passenger"))
        freight_markets = list(self.markets.get(traffic_type="freight"))

        passenger_total_without = None
        passenger_total_with = None
        for market in passenger_markets:
            mid = market.id
            total_without = (
                input_data[f"energy_consumption_{mid}_dropin_fuel_without_operations"]
                + input_data[f"energy_consumption_{mid}_hydrogen_without_operations"]
                + input_data[f"energy_consumption_{mid}_electric_without_operations"]
            )
            total_with = (
                input_data[f"energy_consumption_{mid}_dropin_fuel"]
                + input_data[f"energy_consumption_{mid}_hydrogen"]
                + input_data[f"energy_consumption_{mid}_electric"]
            )

            output_data[f"energy_consumption_{mid}_without_operations"] = total_without
            output_data[f"energy_consumption_{mid}"] = total_with

            passenger_total_without = (
                total_without
                if passenger_total_without is None
                else passenger_total_without + total_without
            )
            passenger_total_with = (
                total_with if passenger_total_with is None else passenger_total_with + total_with
            )

        freight_total_without = None
        freight_total_with = None
        for market in freight_markets:
            mid = market.id
            total_without = (
                input_data[f"energy_consumption_{mid}_dropin_fuel_without_operations"]
                + input_data[f"energy_consumption_{mid}_hydrogen_without_operations"]
                + input_data[f"energy_consumption_{mid}_electric_without_operations"]
            )
            total_with = (
                input_data[f"energy_consumption_{mid}_dropin_fuel"]
                + input_data[f"energy_consumption_{mid}_hydrogen"]
                + input_data[f"energy_consumption_{mid}_electric"]
            )

            output_data[f"energy_consumption_{mid}_without_operations"] = total_without
            output_data[f"energy_consumption_{mid}"] = total_with

            freight_total_without = (
                total_without
                if freight_total_without is None
                else freight_total_without + total_without
            )
            freight_total_with = (
                total_with if freight_total_with is None else freight_total_with + total_with
            )

        if passenger_total_without is None:
            passenger_total_without = pd.Series(0.0, index=self.df.index)
        if passenger_total_with is None:
            passenger_total_with = pd.Series(0.0, index=self.df.index)
        if freight_total_without is None:
            freight_total_without = pd.Series(0.0, index=self.df.index)
        if freight_total_with is None:
            freight_total_with = pd.Series(0.0, index=self.df.index)

        output_data["energy_consumption_passenger_without_operations"] = passenger_total_without
        output_data["energy_consumption_freight_without_operations"] = freight_total_without
        output_data["energy_consumption_without_operations"] = (
            passenger_total_without + freight_total_without
        )
        output_data["energy_consumption_passenger"] = passenger_total_with
        output_data["energy_consumption_freight"] = freight_total_with
        output_data["energy_consumption"] = passenger_total_with + freight_total_with

        self._store_outputs(output_data)
        return output_data

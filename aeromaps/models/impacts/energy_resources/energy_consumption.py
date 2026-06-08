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
        passenger_dropin_fuel = None
        passenger_dropin_fuel_without_operations = None
        for market in passenger_markets:
            mid = market.id
            ask = input_data[f"ask_{mid}_dropin_fuel"]
            energy_per_ask_without_operations = input_data[
                f"energy_per_ask_without_operations_{mid}_dropin_fuel"
            ]
            energy_per_ask = input_data[f"energy_per_ask_{mid}_dropin_fuel"]

            # Energy is zero wherever there is no traffic, even when the per-ASK intensity is
            # NaN/inf from an upstream division-by-zero (energy_per_ask = energy / ask). The mask
            # is applied per-year so partially-empty markets (zero ASK in some years only) do not
            # leak NaN: inf * 0 would otherwise produce NaN and propagate to every aggregate.
            energy_consumption_without_operations = (energy_per_ask_without_operations * ask).where(
                ask != 0.0, 0.0
            )
            energy_consumption = (energy_per_ask * ask).where(ask != 0.0, 0.0)

            output_data[f"energy_consumption_{mid}_dropin_fuel_without_operations"] = (
                energy_consumption_without_operations
            )
            output_data[f"energy_consumption_{mid}_dropin_fuel"] = energy_consumption

            passenger_dropin_fuel_without_operations = (
                energy_consumption_without_operations
                if passenger_dropin_fuel_without_operations is None
                else passenger_dropin_fuel_without_operations
                + energy_consumption_without_operations
            )
            passenger_dropin_fuel = (
                energy_consumption
                if passenger_dropin_fuel is None
                else passenger_dropin_fuel + energy_consumption
            )

        # Per-freight-market consumption.
        freight_dropin_fuel = None
        freight_dropin_fuel_without_operations = None
        for market in freight_markets:
            mid = market.id
            rtk = input_data[f"rtk_{mid}_dropin_fuel"]
            energy_per_rtk_without_operations = input_data[
                f"energy_per_rtk_without_operations_{mid}_dropin_fuel"
            ]
            energy_per_rtk = input_data[f"energy_per_rtk_{mid}_dropin_fuel"]

            # Energy is zero wherever there is no traffic, even when the per-RTK intensity is
            # NaN/inf from an upstream division-by-zero (energy_per_rtk = energy / rtk). The mask
            # is applied per-year so partially-empty markets (zero RTK in some years only) do not
            # leak NaN: inf * 0 would otherwise produce NaN and propagate to every aggregate.
            energy_consumption_without_operations = (energy_per_rtk_without_operations * rtk).where(
                rtk != 0.0, 0.0
            )
            energy_consumption = (energy_per_rtk * rtk).where(rtk != 0.0, 0.0)

            output_data[f"energy_consumption_{mid}_dropin_fuel_without_operations"] = (
                energy_consumption_without_operations
            )
            output_data[f"energy_consumption_{mid}_dropin_fuel"] = energy_consumption

            freight_dropin_fuel_without_operations = (
                energy_consumption_without_operations
                if freight_dropin_fuel_without_operations is None
                else freight_dropin_fuel_without_operations + energy_consumption_without_operations
            )
            freight_dropin_fuel = (
                energy_consumption
                if freight_dropin_fuel is None
                else freight_dropin_fuel + energy_consumption
            )

        # Default to zero series when no markets in a traffic_type (defensive — should not happen
        # for the default 4-market config, but custom configs may have e.g. zero freight markets).
        if passenger_dropin_fuel_without_operations is None:
            passenger_dropin_fuel_without_operations = pd.Series(0.0, index=self.df.index)
        if passenger_dropin_fuel is None:
            passenger_dropin_fuel = pd.Series(0.0, index=self.df.index)
        if freight_dropin_fuel_without_operations is None:
            freight_dropin_fuel_without_operations = pd.Series(0.0, index=self.df.index)
        if freight_dropin_fuel is None:
            freight_dropin_fuel = pd.Series(0.0, index=self.df.index)

        output_data["energy_consumption_passenger_dropin_fuel_without_operations"] = (
            passenger_dropin_fuel_without_operations
        )
        output_data["energy_consumption_passenger_dropin_fuel"] = passenger_dropin_fuel
        output_data["energy_consumption_freight_dropin_fuel_without_operations"] = (
            freight_dropin_fuel_without_operations
        )
        output_data["energy_consumption_freight_dropin_fuel"] = freight_dropin_fuel
        output_data["energy_consumption_dropin_fuel_without_operations"] = (
            passenger_dropin_fuel_without_operations + freight_dropin_fuel_without_operations
        )
        output_data["energy_consumption_dropin_fuel"] = passenger_dropin_fuel + freight_dropin_fuel

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

        passenger_fuel_totals_without_operations = {fuel: None for fuel in shares}
        passenger_fuel_totals = {fuel: None for fuel in shares}
        freight_fuel_totals_without_operations = {fuel: None for fuel in shares}
        freight_fuel_totals = {fuel: None for fuel in shares}

        for market in passenger_markets:
            mid = market.id
            dropin_fuel_without_operations = input_data[
                f"energy_consumption_{mid}_dropin_fuel_without_operations"
            ]
            dropin_fuel = input_data[f"energy_consumption_{mid}_dropin_fuel"]
            for fuel, share in shares.items():
                fuel_energy_without_operations = share * dropin_fuel_without_operations
                fuel_energy = share * dropin_fuel
                output_data[f"energy_consumption_{mid}_{fuel}_without_operations"] = (
                    fuel_energy_without_operations
                )
                output_data[f"energy_consumption_{mid}_{fuel}"] = fuel_energy
                passenger_fuel_totals_without_operations[fuel] = (
                    fuel_energy_without_operations
                    if passenger_fuel_totals_without_operations[fuel] is None
                    else passenger_fuel_totals_without_operations[fuel]
                    + fuel_energy_without_operations
                )
                passenger_fuel_totals[fuel] = (
                    fuel_energy
                    if passenger_fuel_totals[fuel] is None
                    else passenger_fuel_totals[fuel] + fuel_energy
                )

        for market in freight_markets:
            mid = market.id
            dropin_fuel_without_operations = input_data[
                f"energy_consumption_{mid}_dropin_fuel_without_operations"
            ]
            dropin_fuel = input_data[f"energy_consumption_{mid}_dropin_fuel"]
            for fuel, share in shares.items():
                fuel_energy_without_operations = share * dropin_fuel_without_operations
                fuel_energy = share * dropin_fuel
                output_data[f"energy_consumption_{mid}_{fuel}_without_operations"] = (
                    fuel_energy_without_operations
                )
                output_data[f"energy_consumption_{mid}_{fuel}"] = fuel_energy
                freight_fuel_totals_without_operations[fuel] = (
                    fuel_energy_without_operations
                    if freight_fuel_totals_without_operations[fuel] is None
                    else freight_fuel_totals_without_operations[fuel]
                    + fuel_energy_without_operations
                )
                freight_fuel_totals[fuel] = (
                    fuel_energy
                    if freight_fuel_totals[fuel] is None
                    else freight_fuel_totals[fuel] + fuel_energy
                )

        for fuel in shares:
            if passenger_fuel_totals_without_operations[fuel] is None:
                passenger_fuel_totals_without_operations[fuel] = pd.Series(0.0, index=self.df.index)
            if passenger_fuel_totals[fuel] is None:
                passenger_fuel_totals[fuel] = pd.Series(0.0, index=self.df.index)
            if freight_fuel_totals_without_operations[fuel] is None:
                freight_fuel_totals_without_operations[fuel] = pd.Series(0.0, index=self.df.index)
            if freight_fuel_totals[fuel] is None:
                freight_fuel_totals[fuel] = pd.Series(0.0, index=self.df.index)

            output_data[f"energy_consumption_passenger_{fuel}_without_operations"] = (
                passenger_fuel_totals_without_operations[fuel]
            )
            output_data[f"energy_consumption_freight_{fuel}_without_operations"] = (
                freight_fuel_totals_without_operations[fuel]
            )
            output_data[f"energy_consumption_{fuel}_without_operations"] = (
                passenger_fuel_totals_without_operations[fuel]
                + freight_fuel_totals_without_operations[fuel]
            )
            output_data[f"energy_consumption_passenger_{fuel}"] = passenger_fuel_totals[fuel]
            output_data[f"energy_consumption_freight_{fuel}"] = freight_fuel_totals[fuel]
            output_data[f"energy_consumption_{fuel}"] = (
                passenger_fuel_totals[fuel] + freight_fuel_totals[fuel]
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

        passenger_hydrogen_without_operations = None
        passenger_hydrogen = None
        for market in passenger_markets:
            mid = market.id
            ask = input_data[f"ask_{mid}_hydrogen"]
            energy_per_ask_without_operations = input_data[
                f"energy_per_ask_without_operations_{mid}_hydrogen"
            ]
            energy_per_ask = input_data[f"energy_per_ask_{mid}_hydrogen"]

            # Energy is zero wherever there is no traffic, even when the per-ASK intensity is
            # NaN/inf from an upstream division-by-zero (energy_per_ask = energy / ask). The mask
            # is applied per-year so partially-empty markets (zero ASK in some years only) do not
            # leak NaN: inf * 0 would otherwise produce NaN and propagate to every aggregate.
            energy_consumption_without_operations = (energy_per_ask_without_operations * ask).where(
                ask != 0.0, 0.0
            )
            energy_consumption = (energy_per_ask * ask).where(ask != 0.0, 0.0)

            output_data[f"energy_consumption_{mid}_hydrogen_without_operations"] = (
                energy_consumption_without_operations
            )
            output_data[f"energy_consumption_{mid}_hydrogen"] = energy_consumption

            passenger_hydrogen_without_operations = (
                energy_consumption_without_operations
                if passenger_hydrogen_without_operations is None
                else passenger_hydrogen_without_operations + energy_consumption_without_operations
            )
            passenger_hydrogen = (
                energy_consumption
                if passenger_hydrogen is None
                else passenger_hydrogen + energy_consumption
            )

        freight_hydrogen_without_operations = None
        freight_hydrogen = None
        for market in freight_markets:
            mid = market.id
            rtk = input_data[f"rtk_{mid}_hydrogen"]
            energy_per_rtk_without_operations = input_data[
                f"energy_per_rtk_without_operations_{mid}_hydrogen"
            ]
            energy_per_rtk = input_data[f"energy_per_rtk_{mid}_hydrogen"]

            # Energy is zero wherever there is no traffic, even when the per-RTK intensity is
            # NaN/inf from an upstream division-by-zero (energy_per_rtk = energy / rtk). The mask
            # is applied per-year so partially-empty markets (zero RTK in some years only) do not
            # leak NaN: inf * 0 would otherwise produce NaN and propagate to every aggregate.
            energy_consumption_without_operations = (energy_per_rtk_without_operations * rtk).where(
                rtk != 0.0, 0.0
            )
            energy_consumption = (energy_per_rtk * rtk).where(rtk != 0.0, 0.0)

            output_data[f"energy_consumption_{mid}_hydrogen_without_operations"] = (
                energy_consumption_without_operations
            )
            output_data[f"energy_consumption_{mid}_hydrogen"] = energy_consumption

            freight_hydrogen_without_operations = (
                energy_consumption_without_operations
                if freight_hydrogen_without_operations is None
                else freight_hydrogen_without_operations + energy_consumption_without_operations
            )
            freight_hydrogen = (
                energy_consumption
                if freight_hydrogen is None
                else freight_hydrogen + energy_consumption
            )

        if passenger_hydrogen_without_operations is None:
            passenger_hydrogen_without_operations = pd.Series(0.0, index=self.df.index)
        if passenger_hydrogen is None:
            passenger_hydrogen = pd.Series(0.0, index=self.df.index)
        if freight_hydrogen_without_operations is None:
            freight_hydrogen_without_operations = pd.Series(0.0, index=self.df.index)
        if freight_hydrogen is None:
            freight_hydrogen = pd.Series(0.0, index=self.df.index)

        output_data["energy_consumption_passenger_hydrogen_without_operations"] = (
            passenger_hydrogen_without_operations
        )
        output_data["energy_consumption_freight_hydrogen_without_operations"] = (
            freight_hydrogen_without_operations
        )
        output_data["energy_consumption_hydrogen_without_operations"] = (
            passenger_hydrogen_without_operations + freight_hydrogen_without_operations
        )
        output_data["energy_consumption_passenger_hydrogen"] = passenger_hydrogen
        output_data["energy_consumption_freight_hydrogen"] = freight_hydrogen
        output_data["energy_consumption_hydrogen"] = passenger_hydrogen + freight_hydrogen

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

        passenger_electric_without_operations = None
        passenger_electric = None
        for market in passenger_markets:
            mid = market.id
            ask = input_data[f"ask_{mid}_electric"]
            energy_per_ask_without_operations = input_data[
                f"energy_per_ask_without_operations_{mid}_electric"
            ]
            energy_per_ask = input_data[f"energy_per_ask_{mid}_electric"]

            # Energy is zero wherever there is no traffic, even when the per-ASK intensity is
            # NaN/inf from an upstream division-by-zero (energy_per_ask = energy / ask). The mask
            # is applied per-year so partially-empty markets (zero ASK in some years only) do not
            # leak NaN: inf * 0 would otherwise produce NaN and propagate to every aggregate.
            energy_consumption_without_operations = (energy_per_ask_without_operations * ask).where(
                ask != 0.0, 0.0
            )
            energy_consumption = (energy_per_ask * ask).where(ask != 0.0, 0.0)

            output_data[f"energy_consumption_{mid}_electric_without_operations"] = (
                energy_consumption_without_operations
            )
            output_data[f"energy_consumption_{mid}_electric"] = energy_consumption

            passenger_electric_without_operations = (
                energy_consumption_without_operations
                if passenger_electric_without_operations is None
                else passenger_electric_without_operations + energy_consumption_without_operations
            )
            passenger_electric = (
                energy_consumption
                if passenger_electric is None
                else passenger_electric + energy_consumption
            )

        freight_electric_without_operations = None
        freight_electric = None
        for market in freight_markets:
            mid = market.id
            rtk = input_data[f"rtk_{mid}_electric"]
            energy_per_rtk_without_operations = input_data[
                f"energy_per_rtk_without_operations_{mid}_electric"
            ]
            energy_per_rtk = input_data[f"energy_per_rtk_{mid}_electric"]

            # Energy is zero wherever there is no traffic, even when the per-RTK intensity is
            # NaN/inf from an upstream division-by-zero (energy_per_rtk = energy / rtk). The mask
            # is applied per-year so partially-empty markets (zero RTK in some years only) do not
            # leak NaN: inf * 0 would otherwise produce NaN and propagate to every aggregate.
            energy_consumption_without_operations = (energy_per_rtk_without_operations * rtk).where(
                rtk != 0.0, 0.0
            )
            energy_consumption = (energy_per_rtk * rtk).where(rtk != 0.0, 0.0)

            output_data[f"energy_consumption_{mid}_electric_without_operations"] = (
                energy_consumption_without_operations
            )
            output_data[f"energy_consumption_{mid}_electric"] = energy_consumption

            freight_electric_without_operations = (
                energy_consumption_without_operations
                if freight_electric_without_operations is None
                else freight_electric_without_operations + energy_consumption_without_operations
            )
            freight_electric = (
                energy_consumption
                if freight_electric is None
                else freight_electric + energy_consumption
            )

        if passenger_electric_without_operations is None:
            passenger_electric_without_operations = pd.Series(0.0, index=self.df.index)
        if passenger_electric is None:
            passenger_electric = pd.Series(0.0, index=self.df.index)
        if freight_electric_without_operations is None:
            freight_electric_without_operations = pd.Series(0.0, index=self.df.index)
        if freight_electric is None:
            freight_electric = pd.Series(0.0, index=self.df.index)

        output_data["energy_consumption_passenger_electric_without_operations"] = (
            passenger_electric_without_operations
        )
        output_data["energy_consumption_freight_electric_without_operations"] = (
            freight_electric_without_operations
        )
        output_data["energy_consumption_electric_without_operations"] = (
            passenger_electric_without_operations + freight_electric_without_operations
        )
        output_data["energy_consumption_passenger_electric"] = passenger_electric
        output_data["energy_consumption_freight_electric"] = freight_electric
        output_data["energy_consumption_electric"] = passenger_electric + freight_electric

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

        passenger_energy_without_operations = None
        passenger_energy = None
        for market in passenger_markets:
            mid = market.id
            market_energy_without_operations = (
                input_data[f"energy_consumption_{mid}_dropin_fuel_without_operations"]
                + input_data[f"energy_consumption_{mid}_hydrogen_without_operations"]
                + input_data[f"energy_consumption_{mid}_electric_without_operations"]
            )
            market_energy = (
                input_data[f"energy_consumption_{mid}_dropin_fuel"]
                + input_data[f"energy_consumption_{mid}_hydrogen"]
                + input_data[f"energy_consumption_{mid}_electric"]
            )

            output_data[f"energy_consumption_{mid}_without_operations"] = (
                market_energy_without_operations
            )
            output_data[f"energy_consumption_{mid}"] = market_energy

            passenger_energy_without_operations = (
                market_energy_without_operations
                if passenger_energy_without_operations is None
                else passenger_energy_without_operations + market_energy_without_operations
            )
            passenger_energy = (
                market_energy if passenger_energy is None else passenger_energy + market_energy
            )

        freight_energy_without_operations = None
        freight_energy = None
        for market in freight_markets:
            mid = market.id
            market_energy_without_operations = (
                input_data[f"energy_consumption_{mid}_dropin_fuel_without_operations"]
                + input_data[f"energy_consumption_{mid}_hydrogen_without_operations"]
                + input_data[f"energy_consumption_{mid}_electric_without_operations"]
            )
            market_energy = (
                input_data[f"energy_consumption_{mid}_dropin_fuel"]
                + input_data[f"energy_consumption_{mid}_hydrogen"]
                + input_data[f"energy_consumption_{mid}_electric"]
            )

            output_data[f"energy_consumption_{mid}_without_operations"] = (
                market_energy_without_operations
            )
            output_data[f"energy_consumption_{mid}"] = market_energy

            freight_energy_without_operations = (
                market_energy_without_operations
                if freight_energy_without_operations is None
                else freight_energy_without_operations + market_energy_without_operations
            )
            freight_energy = (
                market_energy if freight_energy is None else freight_energy + market_energy
            )

        if passenger_energy_without_operations is None:
            passenger_energy_without_operations = pd.Series(0.0, index=self.df.index)
        if passenger_energy is None:
            passenger_energy = pd.Series(0.0, index=self.df.index)
        if freight_energy_without_operations is None:
            freight_energy_without_operations = pd.Series(0.0, index=self.df.index)
        if freight_energy is None:
            freight_energy = pd.Series(0.0, index=self.df.index)

        output_data["energy_consumption_passenger_without_operations"] = (
            passenger_energy_without_operations
        )
        output_data["energy_consumption_freight_without_operations"] = (
            freight_energy_without_operations
        )
        output_data["energy_consumption_without_operations"] = (
            passenger_energy_without_operations + freight_energy_without_operations
        )
        output_data["energy_consumption_passenger"] = passenger_energy
        output_data["energy_consumption_freight"] = freight_energy
        output_data["energy_consumption"] = passenger_energy + freight_energy

        self._store_outputs(output_data)
        return output_data

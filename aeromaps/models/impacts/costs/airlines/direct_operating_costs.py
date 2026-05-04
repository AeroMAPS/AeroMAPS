"""
direct_operating_costs
=======================

Direct Operating Costs (DOC) models for passenger aircraft.
"""

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class PassengerAircraftDocNonEnergyComplex(AeroMAPSModel):
    """
    Non energy DOC per ASK calculation using generic fleet model.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_non_energy_complex' by default).

    Attributes
    ----------
    fleet_model : FleetModel(AeroMAPSModel)
        FleetModel instance to be used for complex efficiency computations.

    Documentation
    --------------
    Inputs
        - ask_<market>: Passenger ASK per market [ASK].
        - ask_<market>_<energy>_share: ASK share per energy type on a given market [%].
    Outputs
        - doc_non_energy_per_ask_<market>_<energy>: Non-energy DOC per ASK per market and aircraft energy type[€/ASK].
        - doc_non_energy_per_ask_<market>_mean: ASK-weighted mean non-energy DOC per market [€/ASK].
        - doc_non_energy_per_ask_mean: Global ASK-weighted mean non-energy DOC [€/ASK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
        - Per-energy DOC values are read directly from the fleet model DataFrame.
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
    """

    def __init__(self, name="passenger_aircraft_doc_non_energy_complex", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.fleet_model = None
        self.markets = None

    def custom_setup(self):
        """
        Build input_names / output_names dynamically from the MarketManager.
        Called once by AeroMAPSProcess after self.markets is injected.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        self.input_names = {}
        self.output_names = {}

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            for et in energy_types:
                self.input_names[f"ask_{mid}_{et}_share"] = pd.Series([0.0])
                self.output_names[f"doc_non_energy_per_ask_{mid}_{et}"] = pd.Series([0.0])
            self.output_names[f"doc_non_energy_per_ask_{mid}_mean"] = pd.Series([0.0])

        self.output_names["doc_non_energy_per_ask_mean"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        Per-market per-energy-type doc_non_energy_per_ask read from the fleet
        model DataFrame, weighted by ASK shares, aggregated to per-market and
        global means.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        output_data = {}

        # First pass: extract per-market per-energy-type DOC values from fleet df.
        doc_non_energy_per_market_energy_type = {}  # (mid, et) -> pd.Series (per-market per-energy-type DOC per ASK)
        ask_per_market = {}  # mid -> pd.Series (per-market total ASK)
        ask_market_energy_type_share = {}  # (mid, et) -> pd.Series (ASK share per energy type on a given market [%].)

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            ask_per_market[mid] = input_data[f"ask_{mid}"]
            for et in energy_types:
                doc_non_energy_per_market_energy_type[(mid, et)] = self.fleet_model.df[
                    f"{market.name}:doc_non_energy:{et}"
                ]
                ask_market_energy_type_share[(mid, et)] = input_data[f"ask_{mid}_{et}_share"]
                output_data[f"doc_non_energy_per_ask_{mid}_{et}"] = (
                    doc_non_energy_per_market_energy_type[(mid, et)]
                )

        # Second pass: per-market mean (weighted by energy-type shares).
        doc_non_energy_mean = {}  # mid -> pd.Series
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            market_mean = None
            for et in energy_types:
                term = (
                    doc_non_energy_per_market_energy_type[(mid, et)]
                    * ask_market_energy_type_share[(mid, et)]
                    / 100
                )
                market_mean = term if market_mean is None else market_mean + term
            if market_mean is None:
                market_mean = pd.Series(0.0, index=self.df.index)
            doc_non_energy_mean[mid] = market_mean
            output_data[f"doc_non_energy_per_ask_{mid}_mean"] = market_mean

        # Global mean: weighted by per-market ASK totals.
        ask_weighted_doc_sum = None
        ask_total = None
        for mid, market_mean in doc_non_energy_mean.items():
            ask_m = ask_per_market[mid]
            num_term = market_mean * ask_m
            den_term = ask_m
            ask_weighted_doc_sum = (
                num_term if ask_weighted_doc_sum is None else ask_weighted_doc_sum + num_term
            )
            ask_total = den_term if ask_total is None else ask_total + den_term

        if ask_weighted_doc_sum is None:
            # No passenger markets — defensive default.
            doc_non_energy_per_ask_mean = pd.Series(0.0, index=self.df.index)
        else:
            doc_non_energy_per_ask_mean = ask_weighted_doc_sum / ask_total

        output_data["doc_non_energy_per_ask_mean"] = doc_non_energy_per_ask_mean

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftDocNonEnergySimple(AeroMAPSModel):
    """
    Non energy DOC per ASK calculation using simple efficiency models.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_non_energy_simple' by default).

    Documentation
    --------------
    Inputs
        - <market>_doc_non_energy_per_ask_dropin_fuel_init: Initial DOC non energy for drop-in fuel aircraft [€/ASK].
        - <market>_doc_non_energy_per_ask_dropin_fuel_gain: Annual doc non energy improvement rate for dropin fuel aircraft [%/year].
        - <market>_relative_doc_non_energy_per_ask_hydrogen_wrt_dropin: Hydrogen aircraft non energy cost relative to drop-in [ratio].
        - <market>_relative_doc_non_energy_per_ask_electric_wrt_dropin: Electric aircraft non energy cost relative to drop-in [ratio].
        - ask_<market>: Passenger ASK per market [ASK].
        - ask_<market>_<energy>_share: ASK share per energy type for a given market [%].
    Outputs
        - doc_non_energy_per_ask_<market>_<energy>: Non-energy DOC per ASK [€/ASK].
        - doc_non_energy_per_ask_<market>_mean: ASK-weighted mean non-energy DOC per market [€/ASK].
        - doc_non_energy_per_ask_mean: Global ASK-weighted mean non-energy DOC [€/ASK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
        - Drop-in DOC evolves from init via annual gain multiplicatively.
        - Hydrogen and electric DOC are scalar multiples of drop-in DOC.
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
    """

    def __init__(self, name="passenger_aircraft_doc_non_energy_simple", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        """
        Build input_names / output_names dynamically from the MarketManager.
        Called once by AeroMAPSProcess after self.markets is injected.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        self.input_names = {}
        self.output_names = {}

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            # Scalars: dropin_fuel init/gain + relative-to-dropin coefficients for hydrogen/electric.
            self.input_names[f"{mid}_doc_non_energy_per_ask_dropin_fuel_init"] = 0.0
            self.input_names[f"{mid}_doc_non_energy_per_ask_dropin_fuel_gain"] = 0.0
            self.input_names[f"{mid}_relative_doc_non_energy_per_ask_hydrogen_wrt_dropin"] = 0.0
            self.input_names[f"{mid}_relative_doc_non_energy_per_ask_electric_wrt_dropin"] = 0.0
            # Series: per-market ASK + per-energy-type ASK shares.
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            for et in energy_types:
                self.input_names[f"ask_{mid}_{et}_share"] = pd.Series([0.0])
                self.output_names[f"doc_non_energy_per_ask_{mid}_{et}"] = pd.Series([0.0])
            self.output_names[f"doc_non_energy_per_ask_{mid}_mean"] = pd.Series([0.0])

        self.output_names["doc_non_energy_per_ask_mean"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        DOC (without energy DOC) per ASK using simple gain models.
        Per-market: dropin_fuel rolls forward via init*cumulative_gain;
        hydrogen and electric are scalar multiples of dropin_fuel.
        Aggregates to per-market and global ASK-weighted means.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        output_data = {}

        # Per-market per-energy-type series store.
        doc_non_energy_per_market_energy_type = {}  # (mid, et) -> pd.Series (per-market per-energy-type non-energy DOC per ASK)
        ask_per_market = {}  # mid -> pd.Series (per-market total ASK)
        ask_market_energy_type_share = {}  # (mid, et) -> pd.Series (ASK share per energy type on a given market [%])

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            init = float(input_data[f"{mid}_doc_non_energy_per_ask_dropin_fuel_init"])
            gain = float(input_data[f"{mid}_doc_non_energy_per_ask_dropin_fuel_gain"])
            rel_h = float(input_data[f"{mid}_relative_doc_non_energy_per_ask_hydrogen_wrt_dropin"])
            rel_e = float(input_data[f"{mid}_relative_doc_non_energy_per_ask_electric_wrt_dropin"])

            ask_per_market[mid] = input_data[f"ask_{mid}"]
            for et in energy_types:
                ask_market_energy_type_share[(mid, et)] = input_data[f"ask_{mid}_{et}_share"]

            col_dropin = f"doc_non_energy_per_ask_{mid}_dropin_fuel"

            # Historical block: fixed at init.
            for k in range(self.historic_start_year, self.prospection_start_year):
                self.df.loc[k, col_dropin] = init

            # Projection block: recurrence.
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, col_dropin] = self.df.loc[k - 1, col_dropin] * (1 - gain / 100)

            dropin_series = self.df[col_dropin]
            hydrogen_series = dropin_series * rel_h
            electric_series = dropin_series * rel_e

            doc_non_energy_per_market_energy_type[(mid, "dropin_fuel")] = dropin_series
            doc_non_energy_per_market_energy_type[(mid, "hydrogen")] = hydrogen_series
            doc_non_energy_per_market_energy_type[(mid, "electric")] = electric_series

            for et, series in (
                ("dropin_fuel", dropin_series),
                ("hydrogen", hydrogen_series),
                ("electric", electric_series),
            ):
                output_data[f"doc_non_energy_per_ask_{mid}_{et}"] = series

        # Per-market mean (ASK-weighted across energy types).
        doc_non_energy_mean = {}  # mid -> pd.Series
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            total = None
            for et in energy_types:
                term = (
                    doc_non_energy_per_market_energy_type[(mid, et)]
                    * ask_market_energy_type_share[(mid, et)]
                    / 100
                )
                total = term if total is None else total + term
            if total is None:
                total = pd.Series(0.0, index=self.df.index)
            doc_non_energy_mean[mid] = total
            output_data[f"doc_non_energy_per_ask_{mid}_mean"] = total

        # Global mean: weighted by per-market ASK totals.
        ask_weighted_doc_sum = None
        ask_total = None
        for mid, mm in doc_non_energy_mean.items():
            ask_m = ask_per_market[mid]
            num_term = mm * ask_m
            ask_weighted_doc_sum = (
                num_term if ask_weighted_doc_sum is None else ask_weighted_doc_sum + num_term
            )
            ask_total = ask_m if ask_total is None else ask_total + ask_m

        if ask_weighted_doc_sum is None:
            global_mean = pd.Series(0.0, index=self.df.index)
        else:
            global_mean = ask_weighted_doc_sum / ask_total

        output_data["doc_non_energy_per_ask_mean"] = global_mean

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftDocEnergy(AeroMAPSModel):
    """
    Energy DOC per ASK calculation.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_energy' by default).

    Documentation
    --------------
    Inputs
        - dropin_fuel_mean_mfsp: Mean fuel selling price for drop-in fuel [€/MJ].
        - hydrogen_mean_mfsp: Mean fuel selling price for hydrogen [€/MJ].
        - electric_mean_mfsp: Mean fuel selling price for electricity [€/MJ].
        - ask_<market>: Passenger ASK per market [ASK].
        - energy_per_ask_<market>_<energy>: Energy consumption per ASK per market and aircraft energy type [MJ/ASK].
        - ask_<market>_<energy>_share: ASK share per energy type on a given market [%].
    Outputs
        - doc_energy_per_ask_<market>_<energy>: Energy DOC per ASK per market and aircraft energy type [€/ASK].
        - doc_energy_per_ask_<market>_mean: ASK-weighted mean energy DOC per market [€/ASK].
        - doc_energy_per_ask_mean: Global ASK-weighted mean energy DOC [€/ASK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
        - Zero energy consumption is converted to NaN to preserve sparsity (no cost for unused energy).
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
    """

    def __init__(self, name="passenger_aircraft_doc_energy", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        """
        Build input_names / output_names dynamically from the MarketManager.
        Called once by AeroMAPSProcess after self.markets is injected.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        self.input_names = {
            "dropin_fuel_mean_mfsp": pd.Series([0.0]),
            "hydrogen_mean_mfsp": pd.Series([0.0]),
            "electric_mean_mfsp": pd.Series([0.0]),
        }
        self.output_names = {}

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            for et in energy_types:
                self.input_names[f"energy_per_ask_{mid}_{et}"] = pd.Series([0.0])
                self.input_names[f"ask_{mid}_{et}_share"] = pd.Series([0.0])
                self.output_names[f"doc_energy_per_ask_{mid}_{et}"] = pd.Series([0.0])
            self.output_names[f"doc_energy_per_ask_{mid}_mean"] = pd.Series([0.0])

        self.output_names["doc_energy_per_ask_mean"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        Energy-side DOC per ASK.
        Per-market per-energy-type: doc_energy = energy_per_ask * mean_mfsp
        (with 0 -> NaN to preserve sparsity); per-market mean weighted by
        ASK shares (NaN treated as 0); global mean weighted by per-market ASK.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        output_data = {}

        mfsp = {
            "dropin_fuel": input_data["dropin_fuel_mean_mfsp"],
            "hydrogen": input_data["hydrogen_mean_mfsp"],
            "electric": input_data["electric_mean_mfsp"],
        }

        doc_energy_per_market_energy_type = {}  # (mid, et) -> pd.Series (per-market per-energy-type energy DOC per ASK)
        ask_per_market = {}  # mid -> pd.Series (per-market total ASK)
        ask_market_energy_type_share = {}  # (mid, et) -> pd.Series (ASK share per energy type on a given market [%])
        doc_energy_mean = {}  # mid -> pd.Series (per-market ASK-weighted mean energy DOC)

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            ask_per_market[mid] = input_data[f"ask_{mid}"]
            for et in energy_types:
                energy = input_data[f"energy_per_ask_{mid}_{et}"]
                ask_market_energy_type_share[(mid, et)] = input_data[f"ask_{mid}_{et}_share"]
                doc = energy.replace(0, np.NaN) * mfsp[et]
                doc_energy_per_market_energy_type[(mid, et)] = doc
                output_data[f"doc_energy_per_ask_{mid}_{et}"] = doc

        # Per-market mean (NaN treated as 0).
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            total = None
            for et in energy_types:
                term = (
                    doc_energy_per_market_energy_type[(mid, et)].fillna(0)
                    * ask_market_energy_type_share[(mid, et)]
                    / 100
                )
                total = term if total is None else total + term
            if total is None:
                total = pd.Series(0.0, index=self.df.index)
            doc_energy_mean[mid] = total
            output_data[f"doc_energy_per_ask_{mid}_mean"] = total

        # Global mean: weighted by per-market ASK totals.
        ask_weighted_doc_sum = None
        ask_total = None
        for mid, mm in doc_energy_mean.items():
            ask_m = ask_per_market[mid]
            num_term = mm * ask_m
            ask_weighted_doc_sum = (
                num_term if ask_weighted_doc_sum is None else ask_weighted_doc_sum + num_term
            )
            ask_total = ask_m if ask_total is None else ask_total + ask_m

        if ask_weighted_doc_sum is None:
            global_mean = pd.Series(0.0, index=self.df.index)
        else:
            global_mean = ask_weighted_doc_sum / ask_total

        output_data["doc_energy_per_ask_mean"] = global_mean

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftDocEnergyCarbonTax(AeroMAPSModel):
    """
    Carbon tax DOC per ASK calculation.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_energy_carbon_tax' by default).

    Documentation
    --------------
    Inputs
        - dropin_fuel_mean_unit_carbon_tax: Carbon tax per energy unit for drop-in fuel [€/MJ].
        - hydrogen_mean_unit_carbon_tax: Carbon tax per energy unit for hydrogen [€/MJ].
        - electric_mean_unit_carbon_tax: Carbon tax per energy unit for electricity [€/MJ].
        - co2_emissions: Total CO2 emissions [MtCO2].
        - carbon_offset: Carbon offset amount [MtCO2].
        - ask_<market>: Passenger ASK per market [ASK].
        - energy_per_ask_<market>_<energy>: Energy consumption per ASK per market and aircraft energy type [MJ/ASK].
        - ask_<market>_<energy>_share: ASK share per energy type on a given market [%].
    Outputs
        - doc_energy_carbon_tax_per_ask_<market>_<energy>: Carbon tax DOC per ASK per market and aircraft energy type [€/ASK].
        - doc_energy_carbon_tax_per_ask_<market>_mean: ASK-weighted mean carbon tax DOC per market [€/ASK].
        - doc_carbon_tax_lowering_offset_per_ask_<market>_mean: Offset-adjusted carbon tax DOC per market [€/ASK].
        - doc_energy_carbon_tax_per_ask_mean: Global ASK-weighted mean carbon tax DOC [€/ASK].
        - doc_carbon_tax_lowering_offset_per_ask_mean: Global offset-adjusted carbon tax DOC [€/ASK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
        - Zero energy consumption is converted to NaN to preserve sparsity.
        - Lowering offset applies a carbon_remaining_ratio = (emissions - offset) / emissions.
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
    """

    def __init__(self, name="passenger_aircraft_doc_energy_carbon_tax", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        """
        Build input_names / output_names dynamically from the MarketManager.
        Called once by AeroMAPSProcess after self.markets is injected.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        self.input_names = {
            "dropin_fuel_mean_unit_carbon_tax": pd.Series([0.0]),
            "hydrogen_mean_unit_carbon_tax": pd.Series([0.0]),
            "electric_mean_unit_carbon_tax": pd.Series([0.0]),
            "co2_emissions": pd.Series([0.0]),
            "carbon_offset": pd.Series([0.0]),
        }
        self.output_names = {}

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            for et in energy_types:
                self.input_names[f"energy_per_ask_{mid}_{et}"] = pd.Series([0.0])
                self.input_names[f"ask_{mid}_{et}_share"] = pd.Series([0.0])
                self.output_names[f"doc_energy_carbon_tax_per_ask_{mid}_{et}"] = pd.Series([0.0])
            self.output_names[f"doc_energy_carbon_tax_per_ask_{mid}_mean"] = pd.Series([0.0])
            self.output_names[f"doc_carbon_tax_lowering_offset_per_ask_{mid}_mean"] = pd.Series(
                [0.0]
            )

        self.output_names["doc_energy_carbon_tax_per_ask_mean"] = pd.Series([0.0])
        self.output_names["doc_carbon_tax_lowering_offset_per_ask_mean"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        Carbon-tax DOC per ASK.
        Per-market per-energy-type: doc = energy_per_ask * mean_unit_carbon_tax
        (with 0 -> NaN to preserve sparsity); per-market mean weighted by ASK
        shares (NaN treated as 0); global mean weighted by per-market ASK.
        Then lowering-offset series scale the means by the carbon_remaining_ratio.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        output_data = {}

        unit_carbon_tax = {
            "dropin_fuel": input_data["dropin_fuel_mean_unit_carbon_tax"],
            "hydrogen": input_data["hydrogen_mean_unit_carbon_tax"],
            "electric": input_data["electric_mean_unit_carbon_tax"],
        }

        doc_carbon_tax_per_market_energy_type = {}  # (mid, et) -> pd.Series (per-market per-energy-type carbon tax DOC per ASK)
        ask_per_market = {}  # mid -> pd.Series (per-market total ASK)
        ask_market_energy_type_share = {}  # (mid, et) -> pd.Series (ASK share per energy type on a given market [%])
        doc_carbon_tax_mean = {}  # mid -> pd.Series (per-market ASK-weighted mean carbon tax DOC)

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            ask_per_market[mid] = input_data[f"ask_{mid}"]
            for et in energy_types:
                energy = input_data[f"energy_per_ask_{mid}_{et}"]
                ask_market_energy_type_share[(mid, et)] = input_data[f"ask_{mid}_{et}_share"]
                doc = energy.replace(0, np.NaN) * unit_carbon_tax[et]
                doc_carbon_tax_per_market_energy_type[(mid, et)] = doc
                output_data[f"doc_energy_carbon_tax_per_ask_{mid}_{et}"] = doc

        # Per-market mean (NaN treated as 0).
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            total = None
            for et in energy_types:
                term = (
                    doc_carbon_tax_per_market_energy_type[(mid, et)].fillna(0)
                    * ask_market_energy_type_share[(mid, et)]
                    / 100
                )
                total = term if total is None else total + term
            if total is None:
                total = pd.Series(0.0, index=self.df.index)
            doc_carbon_tax_mean[mid] = total
            output_data[f"doc_energy_carbon_tax_per_ask_{mid}_mean"] = total

        # Global mean: weighted by per-market ASK totals.
        ask_weighted_doc_sum = None
        ask_total = None
        for mid, mm in doc_carbon_tax_mean.items():
            ask_m = ask_per_market[mid]
            num_term = mm * ask_m
            ask_weighted_doc_sum = (
                num_term if ask_weighted_doc_sum is None else ask_weighted_doc_sum + num_term
            )
            ask_total = ask_m if ask_total is None else ask_total + ask_m

        if ask_weighted_doc_sum is None:
            global_mean = pd.Series(0.0, index=self.df.index)
        else:
            global_mean = ask_weighted_doc_sum / ask_total

        output_data["doc_energy_carbon_tax_per_ask_mean"] = global_mean

        # Carbon offset lowering ratio (sliced over historic_start_year..end_year).
        co2_emissions = input_data["co2_emissions"]
        carbon_offset = input_data["carbon_offset"]
        carbon_remaining_ratio = (
            co2_emissions.loc[self.historic_start_year : self.end_year] - carbon_offset.fillna(0)
        ) / co2_emissions.loc[self.historic_start_year : self.end_year]

        output_data["doc_carbon_tax_lowering_offset_per_ask_mean"] = (
            global_mean * carbon_remaining_ratio
        )

        for mid, mm in doc_carbon_tax_mean.items():
            lowering = mm * carbon_remaining_ratio
            output_data[f"doc_carbon_tax_lowering_offset_per_ask_{mid}_mean"] = lowering

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftDocEnergySubsidy(AeroMAPSModel):
    """
    Energy subsidy DOC per ASK calculation.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_energy_subsidy' by default).

    Documentation
    --------------
    Inputs
        - dropin_fuel_mean_unit_subsidy: Subsidy per energy unit for drop-in fuel [€/MJ].
        - hydrogen_mean_unit_subsidy: Subsidy per energy unit for hydrogen [€/MJ].
        - electric_mean_unit_subsidy: Subsidy per energy unit for electricity [€/MJ].
        - ask_<market>: Passenger ASK per market [ASK].
        - energy_per_ask_<market>_<energy>: Energy consumption per ASK per market and aircraft energy type [MJ/ASK].
        - ask_<market>_<energy>_share: ASK share per energy type on a given market [%].
    Outputs
        - doc_energy_subsidy_per_ask_<market>_<energy>: Subsidy DOC per ASK per market and aircraft energy type [€/ASK].
        - doc_energy_subsidy_per_ask_<market>_mean: ASK-weighted mean subsidy DOC per market [€/ASK].
        - doc_energy_subsidy_per_ask_mean: Global ASK-weighted mean subsidy DOC [€/ASK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
        - No NaN replacement (legacy behavior preserved).
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
    """

    def __init__(self, name="passenger_aircraft_doc_energy_subsidy", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        """
        Build input_names / output_names dynamically from the MarketManager.
        Called once by AeroMAPSProcess after self.markets is injected.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        self.input_names = {
            "dropin_fuel_mean_unit_subsidy": pd.Series([0.0]),
            "hydrogen_mean_unit_subsidy": pd.Series([0.0]),
            "electric_mean_unit_subsidy": pd.Series([0.0]),
        }
        self.output_names = {}

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            for et in energy_types:
                self.input_names[f"energy_per_ask_{mid}_{et}"] = pd.Series([0.0])
                self.input_names[f"ask_{mid}_{et}_share"] = pd.Series([0.0])
                self.output_names[f"doc_energy_subsidy_per_ask_{mid}_{et}"] = pd.Series([0.0])
            self.output_names[f"doc_energy_subsidy_per_ask_{mid}_mean"] = pd.Series([0.0])

        self.output_names["doc_energy_subsidy_per_ask_mean"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        Energy-subsidy DOC per ASK.
        Per-market per-energy-type: doc = energy_per_ask * mean_unit_subsidy
        (legacy preserved: no .replace(0, np.NaN) on inputs); per-market mean
        weighted by ASK shares (NaN treated as 0); global mean weighted by
        per-market ASK.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        output_data = {}

        unit_subsidy = {
            "dropin_fuel": input_data["dropin_fuel_mean_unit_subsidy"],
            "hydrogen": input_data["hydrogen_mean_unit_subsidy"],
            "electric": input_data["electric_mean_unit_subsidy"],
        }

        doc_subsidy_per_market_energy_type = {}  # (mid, et) -> pd.Series (per-market per-energy-type subsidy DOC per ASK)
        ask_per_market = {}  # mid -> pd.Series (per-market total ASK)
        ask_market_energy_type_share = {}  # (mid, et) -> pd.Series (ASK share per energy type on a given market [%])
        doc_subsidy_mean = {}  # mid -> pd.Series (per-market ASK-weighted mean subsidy DOC)

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            ask_per_market[mid] = input_data[f"ask_{mid}"]
            for et in energy_types:
                energy = input_data[f"energy_per_ask_{mid}_{et}"]
                ask_market_energy_type_share[(mid, et)] = input_data[f"ask_{mid}_{et}_share"]
                doc = energy * unit_subsidy[et]
                doc_subsidy_per_market_energy_type[(mid, et)] = doc
                output_data[f"doc_energy_subsidy_per_ask_{mid}_{et}"] = doc

        # Per-market mean (NaN treated as 0).
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            total = None
            for et in energy_types:
                term = (
                    doc_subsidy_per_market_energy_type[(mid, et)].fillna(0)
                    * ask_market_energy_type_share[(mid, et)]
                    / 100
                )
                total = term if total is None else total + term
            if total is None:
                total = pd.Series(0.0, index=self.df.index)
            doc_subsidy_mean[mid] = total
            output_data[f"doc_energy_subsidy_per_ask_{mid}_mean"] = total

        # Global mean: weighted by per-market ASK totals.
        ask_weighted_doc_sum = None
        ask_total = None
        for mid, mm in doc_subsidy_mean.items():
            ask_m = ask_per_market[mid]
            num_term = mm * ask_m
            ask_weighted_doc_sum = (
                num_term if ask_weighted_doc_sum is None else ask_weighted_doc_sum + num_term
            )
            ask_total = ask_m if ask_total is None else ask_total + ask_m

        if ask_weighted_doc_sum is None:
            global_mean = pd.Series(0.0, index=self.df.index)
        else:
            global_mean = ask_weighted_doc_sum / ask_total

        output_data["doc_energy_subsidy_per_ask_mean"] = global_mean

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftDocEnergyTax(AeroMAPSModel):
    """
    Energy tax (non-carbon) DOC per ASK calculation.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_energy_tax' by default).

    Documentation
    --------------
    Inputs
        - dropin_fuel_mean_unit_tax: Tax per energy unit for drop-in fuel [€/MJ].
        - hydrogen_mean_unit_tax: Tax per energy unit for hydrogen [€/MJ].
        - electric_mean_unit_tax: Tax per energy unit for electricity [€/MJ].
        - ask_<market>: Passenger ASK per market [ASK].
        - energy_per_ask_<market>_<energy>: Energy consumption per ASK per market and aircraft energy type [MJ/ASK].
        - ask_<market>_<energy>_share: ASK share per energy type on a given market [%].
    Outputs
        - doc_energy_tax_per_ask_<market>_<energy>: Energy tax DOC per ASK per market and aircraft energy type [€/ASK].
        - doc_energy_tax_per_ask_<market>_mean: ASK-weighted mean energy tax DOC per market [€/ASK].
        - doc_energy_tax_per_ask_mean: Global ASK-weighted mean energy tax DOC [€/ASK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
        - No NaN replacement (legacy behavior preserved).
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
    """

    def __init__(self, name="passenger_aircraft_doc_energy_tax", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        """
        Build input_names / output_names dynamically from the MarketManager.
        Called once by AeroMAPSProcess after self.markets is injected.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        self.input_names = {
            "dropin_fuel_mean_unit_tax": pd.Series([0.0]),
            "hydrogen_mean_unit_tax": pd.Series([0.0]),
            "electric_mean_unit_tax": pd.Series([0.0]),
        }
        self.output_names = {}

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            for et in energy_types:
                self.input_names[f"energy_per_ask_{mid}_{et}"] = pd.Series([0.0])
                self.input_names[f"ask_{mid}_{et}_share"] = pd.Series([0.0])
                self.output_names[f"doc_energy_tax_per_ask_{mid}_{et}"] = pd.Series([0.0])
            self.output_names[f"doc_energy_tax_per_ask_{mid}_mean"] = pd.Series([0.0])

        self.output_names["doc_energy_tax_per_ask_mean"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        Energy-tax (non-carbon) DOC per ASK.
        Per-market per-energy-type: doc = energy_per_ask * mean_unit_tax
        (legacy preserved: no .replace(0, np.NaN) on inputs); per-market mean
        weighted by ASK shares (NaN treated as 0); global mean weighted by
        per-market ASK.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        output_data = {}

        unit_tax = {
            "dropin_fuel": input_data["dropin_fuel_mean_unit_tax"],
            "hydrogen": input_data["hydrogen_mean_unit_tax"],
            "electric": input_data["electric_mean_unit_tax"],
        }

        doc_tax_per_market_energy_type = {}  # (mid, et) -> pd.Series (per-market per-energy-type tax DOC per ASK)
        ask_per_market = {}  # mid -> pd.Series (per-market total ASK)
        ask_market_energy_type_share = {}  # (mid, et) -> pd.Series (ASK share per energy type on a given market [%])
        doc_tax_mean = {}  # mid -> pd.Series (per-market ASK-weighted mean tax DOC)

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            ask_per_market[mid] = input_data[f"ask_{mid}"]
            for et in energy_types:
                energy = input_data[f"energy_per_ask_{mid}_{et}"]
                ask_market_energy_type_share[(mid, et)] = input_data[f"ask_{mid}_{et}_share"]
                doc = energy * unit_tax[et]
                doc_tax_per_market_energy_type[(mid, et)] = doc
                output_data[f"doc_energy_tax_per_ask_{mid}_{et}"] = doc

        # Per-market mean (NaN treated as 0).
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            total = None
            for et in energy_types:
                term = (
                    doc_tax_per_market_energy_type[(mid, et)].fillna(0)
                    * ask_market_energy_type_share[(mid, et)]
                    / 100
                )
                total = term if total is None else total + term
            if total is None:
                total = pd.Series(0.0, index=self.df.index)
            doc_tax_mean[mid] = total
            output_data[f"doc_energy_tax_per_ask_{mid}_mean"] = total

        # Global mean: weighted by per-market ASK totals.
        ask_weighted_doc_sum = None
        ask_total = None
        for mid, mm in doc_tax_mean.items():
            ask_m = ask_per_market[mid]
            num_term = mm * ask_m
            ask_weighted_doc_sum = (
                num_term if ask_weighted_doc_sum is None else ask_weighted_doc_sum + num_term
            )
            ask_total = ask_m if ask_total is None else ask_total + ask_m

        if ask_weighted_doc_sum is None:
            global_mean = pd.Series(0.0, index=self.df.index)
        else:
            global_mean = ask_weighted_doc_sum / ask_total

        output_data["doc_energy_tax_per_ask_mean"] = global_mean

        self._store_outputs(output_data)
        return output_data


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
    Aggregation of all DOC categories for total DOC per ASK calculation.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_total_doc' by default).

    Documentation
    --------------
    Inputs
        - doc_non_energy_per_ask_<market>_<energy>: Non-energy DOC per ASK [€/ASK].
        - doc_non_energy_per_ask_<market>_mean: Non-energy DOC per market [€/ASK].
        - doc_energy_per_ask_<market>_<energy>: Energy DOC per ASK [€/ASK].
        - doc_energy_per_ask_<market>_mean: Energy DOC per market [€/ASK].
        - doc_energy_carbon_tax_per_ask_<market>_<energy>: Carbon tax DOC per ASK [€/ASK].
        - doc_energy_carbon_tax_per_ask_<market>_mean: Carbon tax DOC per market [€/ASK].
        - doc_energy_subsidy_per_ask_<market>_<energy>: Subsidy DOC per ASK [€/ASK].
        - doc_energy_subsidy_per_ask_<market>_mean: Subsidy DOC per market [€/ASK].
        - doc_energy_tax_per_ask_<market>_<energy>: Tax DOC per ASK [€/ASK].
        - doc_energy_tax_per_ask_<market>_mean: Tax DOC per market [€/ASK].
        - All global means (no <market> suffix) of above categories [€/ASK].
    Outputs
        - doc_total_per_ask_<market>_<energy>: Total DOC per ASK [€/ASK].
        - doc_total_per_ask_<market>_mean: Total DOC per market [€/ASK].
        - doc_total_per_ask_mean: Global total DOC [€/ASK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
        - Formula: doc_total = non_energy + energy + carbon_tax - subsidy + tax.
        - Subsidy enters with negative sign (income reduces cost).
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
    """

    def __init__(self, name="passenger_aircraft_total_doc", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.fleet_model = None
        self.markets = None

    def custom_setup(self):
        """
        Build input_names / output_names dynamically from the MarketManager.
        Called once by AeroMAPSProcess after self.markets is injected.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        component_prefixes = [
            "doc_non_energy_per_ask",
            "doc_energy_per_ask",
            "doc_energy_carbon_tax_per_ask",
            "doc_energy_subsidy_per_ask",
            "doc_energy_tax_per_ask",
        ]
        self.input_names = {}
        self.output_names = {}

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            for et in energy_types:
                for prefix in component_prefixes:
                    self.input_names[f"{prefix}_{mid}_{et}"] = pd.Series([0.0])
                self.output_names[f"doc_total_per_ask_{mid}_{et}"] = pd.Series([0.0])
            for prefix in component_prefixes:
                self.input_names[f"{prefix}_{mid}_mean"] = pd.Series([0.0])
            self.output_names[f"doc_total_per_ask_{mid}_mean"] = pd.Series([0.0])

        # Global means (no per-market suffix).
        for prefix in component_prefixes:
            self.input_names[f"{prefix}_mean"] = pd.Series([0.0])
        self.output_names["doc_total_per_ask_mean"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        Aggregate DOC components into a total per (market, energy_type),
        plus per-market and global means. Subsidy enters with a negative sign
        (income from subsidy reduces the operator's cost).
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        output_data = {}

        def total(non_energy, energy, carbon_tax, subsidy, tax):
            return non_energy + energy + carbon_tax - subsidy + tax

        # Per-(market, energy_type) total.
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            for et in energy_types:
                output_data[f"doc_total_per_ask_{mid}_{et}"] = total(
                    input_data[f"doc_non_energy_per_ask_{mid}_{et}"],
                    input_data[f"doc_energy_per_ask_{mid}_{et}"],
                    input_data[f"doc_energy_carbon_tax_per_ask_{mid}_{et}"],
                    input_data[f"doc_energy_subsidy_per_ask_{mid}_{et}"],
                    input_data[f"doc_energy_tax_per_ask_{mid}_{et}"],
                )

            # Per-market mean.
            output_data[f"doc_total_per_ask_{mid}_mean"] = total(
                input_data[f"doc_non_energy_per_ask_{mid}_mean"],
                input_data[f"doc_energy_per_ask_{mid}_mean"],
                input_data[f"doc_energy_carbon_tax_per_ask_{mid}_mean"],
                input_data[f"doc_energy_subsidy_per_ask_{mid}_mean"],
                input_data[f"doc_energy_tax_per_ask_{mid}_mean"],
            )

        # Global mean.
        output_data["doc_total_per_ask_mean"] = total(
            input_data["doc_non_energy_per_ask_mean"],
            input_data["doc_energy_per_ask_mean"],
            input_data["doc_energy_carbon_tax_per_ask_mean"],
            input_data["doc_energy_subsidy_per_ask_mean"],
            input_data["doc_energy_tax_per_ask_mean"],
        )

        self._store_outputs(output_data)
        return output_data

"""
direct_operating_costs
=======================

Direct Operating Costs (DOC) models for passenger aircraft.
"""

from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class PassengerAircraftDocNonEnergyComplex(AeroMAPSModel):
    """
    Non energy DOC per ASK calculation using generic fleet model

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_non_energy_complex' by default).

    Attributes
    ----------
    fleet_model : FleetModel(AeroMAPSModel)
        FleetModel instance to be used for complex efficiency computations.
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
        doc_per_market_type = {}  # (mid, et) -> pd.Series
        ask_market = {}  # mid -> pd.Series (per-market total ASK)
        ask_share = {}  # (mid, et) -> pd.Series

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            ask_market[mid] = input_data[f"ask_{mid}"]
            for et in energy_types:
                doc_per_market_type[(mid, et)] = self.fleet_model.df[
                    f"{market.name}:doc_non_energy:{et}"
                ]
                ask_share[(mid, et)] = input_data[f"ask_{mid}_{et}_share"]
                output_data[f"doc_non_energy_per_ask_{mid}_{et}"] = doc_per_market_type[(mid, et)]

        # Second pass: per-market mean (weighted by energy-type shares).
        doc_market_mean = {}  # mid -> pd.Series
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            market_mean = None
            for et in energy_types:
                term = doc_per_market_type[(mid, et)] * ask_share[(mid, et)] / 100
                market_mean = term if market_mean is None else market_mean + term
            if market_mean is None:
                market_mean = pd.Series(0.0, index=self.df.index)
            doc_market_mean[mid] = market_mean
            output_data[f"doc_non_energy_per_ask_{mid}_mean"] = market_mean

        # Global mean: weighted by per-market ASK totals.
        numerator = None
        denominator = None
        for mid, market_mean in doc_market_mean.items():
            ask_m = ask_market[mid]
            num_term = market_mean * ask_m
            den_term = ask_m
            numerator = num_term if numerator is None else numerator + num_term
            denominator = den_term if denominator is None else denominator + den_term

        if numerator is None:
            # No passenger markets — defensive default.
            doc_non_energy_per_ask_mean = pd.Series(0.0, index=self.df.index)
        else:
            doc_non_energy_per_ask_mean = numerator / denominator

        output_data["doc_non_energy_per_ask_mean"] = doc_non_energy_per_ask_mean

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftDocNonEnergySimple(AeroMAPSModel):
    """
    Non energy DOC per ASK calculation using simple efficiency models

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_non_energy_simple' by default).
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
            self.input_names[f"doc_non_energy_per_ask_{mid}_dropin_fuel_init"] = 0.0
            self.input_names[f"doc_non_energy_per_ask_{mid}_dropin_fuel_gain"] = 0.0
            self.input_names[f"relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_{mid}"] = 0.0
            self.input_names[f"relative_doc_non_energy_per_ask_electric_wrt_dropin_{mid}"] = 0.0
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

        # Per-market series store.
        doc_pm = {}  # (mid, et) -> pd.Series
        ask_market = {}  # mid -> pd.Series
        ask_share = {}  # (mid, et) -> pd.Series

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            init = float(input_data[f"doc_non_energy_per_ask_{mid}_dropin_fuel_init"])
            gain = float(input_data[f"doc_non_energy_per_ask_{mid}_dropin_fuel_gain"])
            rel_h = float(input_data[f"relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_{mid}"])
            rel_e = float(input_data[f"relative_doc_non_energy_per_ask_electric_wrt_dropin_{mid}"])

            ask_market[mid] = input_data[f"ask_{mid}"]
            for et in energy_types:
                ask_share[(mid, et)] = input_data[f"ask_{mid}_{et}_share"]

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

            doc_pm[(mid, "dropin_fuel")] = dropin_series
            doc_pm[(mid, "hydrogen")] = hydrogen_series
            doc_pm[(mid, "electric")] = electric_series

            for et, series in (
                ("dropin_fuel", dropin_series),
                ("hydrogen", hydrogen_series),
                ("electric", electric_series),
            ):
                output_data[f"doc_non_energy_per_ask_{mid}_{et}"] = series

        # Per-market mean.
        market_mean = {}
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            total = None
            for et in energy_types:
                term = doc_pm[(mid, et)] * ask_share[(mid, et)] / 100
                total = term if total is None else total + term
            if total is None:
                total = pd.Series(0.0, index=self.df.index)
            market_mean[mid] = total
            output_data[f"doc_non_energy_per_ask_{mid}_mean"] = total

        # Global mean: weighted by per-market ASK totals.
        numerator = None
        denominator = None
        for mid, mm in market_mean.items():
            ask_m = ask_market[mid]
            num_term = mm * ask_m
            numerator = num_term if numerator is None else numerator + num_term
            denominator = ask_m if denominator is None else denominator + ask_m

        if numerator is None:
            global_mean = pd.Series(0.0, index=self.df.index)
        else:
            global_mean = numerator / denominator

        output_data["doc_non_energy_per_ask_mean"] = global_mean

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftDocEnergy(AeroMAPSModel):
    """
    Energy DOC per ASK calculation

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_energy' by default).
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

        doc_pm = {}  # (mid, et) -> pd.Series
        ask_market = {}  # mid -> pd.Series
        ask_share = {}  # (mid, et) -> pd.Series
        market_mean = {}  # mid -> pd.Series

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            ask_market[mid] = input_data[f"ask_{mid}"]
            for et in energy_types:
                energy = input_data[f"energy_per_ask_{mid}_{et}"]
                ask_share[(mid, et)] = input_data[f"ask_{mid}_{et}_share"]
                doc = energy.replace(0, np.NaN) * mfsp[et]
                doc_pm[(mid, et)] = doc
                output_data[f"doc_energy_per_ask_{mid}_{et}"] = doc

        # Per-market mean (NaN treated as 0).
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            total = None
            for et in energy_types:
                term = doc_pm[(mid, et)].fillna(0) * ask_share[(mid, et)] / 100
                total = term if total is None else total + term
            if total is None:
                total = pd.Series(0.0, index=self.df.index)
            market_mean[mid] = total
            output_data[f"doc_energy_per_ask_{mid}_mean"] = total

        # Global mean: weighted by per-market ASK totals.
        numerator = None
        denominator = None
        for mid, mm in market_mean.items():
            ask_m = ask_market[mid]
            num_term = mm * ask_m
            numerator = num_term if numerator is None else numerator + num_term
            denominator = ask_m if denominator is None else denominator + ask_m

        if numerator is None:
            global_mean = pd.Series(0.0, index=self.df.index)
        else:
            global_mean = numerator / denominator

        output_data["doc_energy_per_ask_mean"] = global_mean

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftDocEnergyCarbonTax(AeroMAPSModel):
    """
    Carbon tax DOC per ASK calculation

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_energy_carbon_tax' by default
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

        scaling = {
            "dropin_fuel": input_data["dropin_fuel_mean_unit_carbon_tax"],
            "hydrogen": input_data["hydrogen_mean_unit_carbon_tax"],
            "electric": input_data["electric_mean_unit_carbon_tax"],
        }

        doc_pm = {}  # (mid, et) -> pd.Series
        ask_market = {}  # mid -> pd.Series
        ask_share = {}  # (mid, et) -> pd.Series
        market_mean = {}  # mid -> pd.Series

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            ask_market[mid] = input_data[f"ask_{mid}"]
            for et in energy_types:
                energy = input_data[f"energy_per_ask_{mid}_{et}"]
                ask_share[(mid, et)] = input_data[f"ask_{mid}_{et}_share"]
                doc = energy.replace(0, np.NaN) * scaling[et]
                doc_pm[(mid, et)] = doc
                output_data[f"doc_energy_carbon_tax_per_ask_{mid}_{et}"] = doc

        # Per-market mean (NaN treated as 0).
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            total = None
            for et in energy_types:
                term = doc_pm[(mid, et)].fillna(0) * ask_share[(mid, et)] / 100
                total = term if total is None else total + term
            if total is None:
                total = pd.Series(0.0, index=self.df.index)
            market_mean[mid] = total
            output_data[f"doc_energy_carbon_tax_per_ask_{mid}_mean"] = total

        # Global mean: weighted by per-market ASK totals.
        numerator = None
        denominator = None
        for mid, mm in market_mean.items():
            ask_m = ask_market[mid]
            num_term = mm * ask_m
            numerator = num_term if numerator is None else numerator + num_term
            denominator = ask_m if denominator is None else denominator + ask_m

        if numerator is None:
            global_mean = pd.Series(0.0, index=self.df.index)
        else:
            global_mean = numerator / denominator

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

        lowering_offset_pm = {}
        for mid, mm in market_mean.items():
            lowering = mm * carbon_remaining_ratio
            lowering_offset_pm[mid] = lowering
            output_data[f"doc_carbon_tax_lowering_offset_per_ask_{mid}_mean"] = lowering

        # Legacy bug preserved (commit history pre-Phase-4): the short_range column of
        # doc_carbon_tax_lowering_offset_per_ask_<mid>_mean is overwritten with the
        # medium_range value. Preserved for numerical equivalence with default config.
        # NOTE: legacy bug preserved
        if "short_range" in lowering_offset_pm and "medium_range" in lowering_offset_pm:
            output_data["doc_carbon_tax_lowering_offset_per_ask_short_range_mean"] = (
                lowering_offset_pm["medium_range"]
            )

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftDocEnergySubsidy(AeroMAPSModel):
    """
    Energy subsidy DOC per ASK calculation

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_energy_subsidy' by default
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

        scaling = {
            "dropin_fuel": input_data["dropin_fuel_mean_unit_subsidy"],
            "hydrogen": input_data["hydrogen_mean_unit_subsidy"],
            "electric": input_data["electric_mean_unit_subsidy"],
        }

        doc_pm = {}  # (mid, et) -> pd.Series
        ask_market = {}  # mid -> pd.Series
        ask_share = {}  # (mid, et) -> pd.Series
        market_mean = {}  # mid -> pd.Series

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            ask_market[mid] = input_data[f"ask_{mid}"]
            for et in energy_types:
                energy = input_data[f"energy_per_ask_{mid}_{et}"]
                ask_share[(mid, et)] = input_data[f"ask_{mid}_{et}_share"]
                doc = energy * scaling[et]
                doc_pm[(mid, et)] = doc
                output_data[f"doc_energy_subsidy_per_ask_{mid}_{et}"] = doc

        # Per-market mean (NaN treated as 0).
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            total = None
            for et in energy_types:
                term = doc_pm[(mid, et)].fillna(0) * ask_share[(mid, et)] / 100
                total = term if total is None else total + term
            if total is None:
                total = pd.Series(0.0, index=self.df.index)
            market_mean[mid] = total
            output_data[f"doc_energy_subsidy_per_ask_{mid}_mean"] = total

        # Global mean: weighted by per-market ASK totals.
        numerator = None
        denominator = None
        for mid, mm in market_mean.items():
            ask_m = ask_market[mid]
            num_term = mm * ask_m
            numerator = num_term if numerator is None else numerator + num_term
            denominator = ask_m if denominator is None else denominator + ask_m

        if numerator is None:
            global_mean = pd.Series(0.0, index=self.df.index)
        else:
            global_mean = numerator / denominator

        output_data["doc_energy_subsidy_per_ask_mean"] = global_mean

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftDocEnergyTax(AeroMAPSModel):
    """
    Energy tax (non-carbon) DOC per ASK calculation

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_doc_energy_tax' by default
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

        scaling = {
            "dropin_fuel": input_data["dropin_fuel_mean_unit_tax"],
            "hydrogen": input_data["hydrogen_mean_unit_tax"],
            "electric": input_data["electric_mean_unit_tax"],
        }

        doc_pm = {}  # (mid, et) -> pd.Series
        ask_market = {}  # mid -> pd.Series
        ask_share = {}  # (mid, et) -> pd.Series
        market_mean = {}  # mid -> pd.Series

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            ask_market[mid] = input_data[f"ask_{mid}"]
            for et in energy_types:
                energy = input_data[f"energy_per_ask_{mid}_{et}"]
                ask_share[(mid, et)] = input_data[f"ask_{mid}_{et}_share"]
                doc = energy * scaling[et]
                doc_pm[(mid, et)] = doc
                output_data[f"doc_energy_tax_per_ask_{mid}_{et}"] = doc

        # Per-market mean (NaN treated as 0).
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            total = None
            for et in energy_types:
                term = doc_pm[(mid, et)].fillna(0) * ask_share[(mid, et)] / 100
                total = term if total is None else total + term
            if total is None:
                total = pd.Series(0.0, index=self.df.index)
            market_mean[mid] = total
            output_data[f"doc_energy_tax_per_ask_{mid}_mean"] = total

        # Global mean: weighted by per-market ASK totals.
        numerator = None
        denominator = None
        for mid, mm in market_mean.items():
            ask_m = ask_market[mid]
            num_term = mm * ask_m
            numerator = num_term if numerator is None else numerator + num_term
            denominator = ask_m if denominator is None else denominator + ask_m

        if numerator is None:
            global_mean = pd.Series(0.0, index=self.df.index)
        else:
            global_mean = numerator / denominator

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
    Aggregation of all DOC categories for total DOC per ASK calculation
    """

    def __init__(self, name="passenger_aircraft_total_doc", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = None

    def compute(
        self,
        doc_non_energy_per_ask_short_range_dropin_fuel: pd.Series,
        doc_non_energy_per_ask_medium_range_dropin_fuel: pd.Series,
        doc_non_energy_per_ask_long_range_dropin_fuel: pd.Series,
        doc_non_energy_per_ask_short_range_hydrogen: pd.Series,
        doc_non_energy_per_ask_medium_range_hydrogen: pd.Series,
        doc_non_energy_per_ask_long_range_hydrogen: pd.Series,
        doc_non_energy_per_ask_short_range_mean: pd.Series,
        doc_non_energy_per_ask_medium_range_mean: pd.Series,
        doc_non_energy_per_ask_long_range_mean: pd.Series,
        doc_non_energy_per_ask_mean: pd.Series,
        doc_energy_per_ask_long_range_dropin_fuel: pd.Series,
        doc_energy_per_ask_long_range_hydrogen: pd.Series,
        doc_energy_per_ask_long_range_mean: pd.Series,
        doc_energy_per_ask_medium_range_dropin_fuel: pd.Series,
        doc_energy_per_ask_medium_range_hydrogen: pd.Series,
        doc_energy_per_ask_medium_range_mean: pd.Series,
        doc_energy_per_ask_short_range_dropin_fuel: pd.Series,
        doc_energy_per_ask_short_range_hydrogen: pd.Series,
        doc_energy_per_ask_short_range_mean: pd.Series,
        doc_energy_per_ask_mean: pd.Series,
        doc_energy_carbon_tax_per_ask_long_range_dropin_fuel: pd.Series,
        doc_energy_carbon_tax_per_ask_long_range_hydrogen: pd.Series,
        doc_energy_carbon_tax_per_ask_long_range_mean: pd.Series,
        doc_energy_carbon_tax_per_ask_medium_range_dropin_fuel: pd.Series,
        doc_energy_carbon_tax_per_ask_medium_range_hydrogen: pd.Series,
        doc_energy_carbon_tax_per_ask_medium_range_mean: pd.Series,
        doc_energy_carbon_tax_per_ask_short_range_dropin_fuel: pd.Series,
        doc_energy_carbon_tax_per_ask_short_range_hydrogen: pd.Series,
        doc_energy_carbon_tax_per_ask_short_range_mean: pd.Series,
        doc_non_energy_per_ask_short_range_electric: pd.Series,
        doc_non_energy_per_ask_medium_range_electric: pd.Series,
        doc_non_energy_per_ask_long_range_electric: pd.Series,
        doc_energy_per_ask_short_range_electric: pd.Series,
        doc_energy_per_ask_medium_range_electric: pd.Series,
        doc_energy_per_ask_long_range_electric: pd.Series,
        doc_energy_carbon_tax_per_ask_short_range_electric: pd.Series,
        doc_energy_carbon_tax_per_ask_medium_range_electric: pd.Series,
        doc_energy_carbon_tax_per_ask_long_range_electric: pd.Series,
        doc_energy_carbon_tax_per_ask_mean: pd.Series,
        doc_energy_subsidy_per_ask_long_range_dropin_fuel: pd.Series,
        doc_energy_subsidy_per_ask_medium_range_dropin_fuel: pd.Series,
        doc_energy_subsidy_per_ask_short_range_dropin_fuel: pd.Series,
        doc_energy_subsidy_per_ask_long_range_hydrogen: pd.Series,
        doc_energy_subsidy_per_ask_medium_range_hydrogen: pd.Series,
        doc_energy_subsidy_per_ask_short_range_hydrogen: pd.Series,
        doc_energy_subsidy_per_ask_long_range_electric: pd.Series,
        doc_energy_subsidy_per_ask_medium_range_electric: pd.Series,
        doc_energy_subsidy_per_ask_short_range_electric: pd.Series,
        doc_energy_subsidy_per_ask_long_range_mean: pd.Series,
        doc_energy_subsidy_per_ask_medium_range_mean: pd.Series,
        doc_energy_subsidy_per_ask_short_range_mean: pd.Series,
        doc_energy_subsidy_per_ask_mean: pd.Series,
        doc_energy_tax_per_ask_long_range_dropin_fuel: pd.Series,
        doc_energy_tax_per_ask_medium_range_dropin_fuel: pd.Series,
        doc_energy_tax_per_ask_short_range_dropin_fuel: pd.Series,
        doc_energy_tax_per_ask_long_range_hydrogen: pd.Series,
        doc_energy_tax_per_ask_medium_range_hydrogen: pd.Series,
        doc_energy_tax_per_ask_short_range_hydrogen: pd.Series,
        doc_energy_tax_per_ask_long_range_electric: pd.Series,
        doc_energy_tax_per_ask_medium_range_electric: pd.Series,
        doc_energy_tax_per_ask_short_range_electric: pd.Series,
        doc_energy_tax_per_ask_long_range_mean: pd.Series,
        doc_energy_tax_per_ask_medium_range_mean: pd.Series,
        doc_energy_tax_per_ask_short_range_mean: pd.Series,
        doc_energy_tax_per_ask_mean: pd.Series,
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
    ]:
        """
        Execution of the total DOC per ASK calculation.
        Parameters
        ----------
        doc_non_energy_per_ask_short_range_dropin_fuel
            Non-energy direct operating cost per ASK for passenger short-range market aircraft using drop-in fuel [€/ASK].
        doc_non_energy_per_ask_medium_range_dropin_fuel
            Non-energy direct operating cost per ASK for passenger medium-range market aircraft using drop-in fuel [€/ASK].
        doc_non_energy_per_ask_long_range_dropin_fuel
            Non-energy direct operating cost per ASK for passenger long-range market aircraft using drop-in fuel [€/ASK].
        doc_non_energy_per_ask_short_range_hydrogen
            Non-energy direct operating cost per ASK for passenger short-range market aircraft using hydrogen [€/ASK].
        doc_non_energy_per_ask_medium_range_hydrogen
            Non-energy direct operating cost per ASK for passenger medium-range market aircraft using hydrogen [€/ASK].
        doc_non_energy_per_ask_long_range_hydrogen
            Non-energy direct operating cost per ASK for passenger long-range market aircraft using hydrogen [€/ASK].
        doc_non_energy_per_ask_short_range_mean
            Non-energy direct operating cost per ASK for passenger short-range market aircraft average [€/ASK].
        doc_non_energy_per_ask_medium_range_mean
            Non-energy direct operating cost per ASK for passenger medium-range market aircraft average [€/ASK].
        doc_non_energy_per_ask_long_range_mean
            Non-energy direct operating cost per ASK for passenger long-range market aircraft average [€/ASK].
        doc_non_energy_per_ask_mean
            Non-energy direct operating cost per ASK for passenger overall market aircraft average [€/ASK].
        doc_energy_per_ask_long_range_dropin_fuel
            Energy direct operating cost per ASK for passenger long-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_per_ask_long_range_hydrogen
            Energy direct operating cost per ASK for passenger long-range market aircraft using hydrogen [€/ASK].
        doc_energy_per_ask_long_range_mean
            Energy direct operating cost per ASK for passenger long-range market aircraft average [€/ASK].
        doc_energy_per_ask_medium_range_dropin_fuel
            Energy direct operating cost per ASK for passenger medium-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_per_ask_medium_range_hydrogen
            Energy direct operating cost per ASK for passenger medium-range market aircraft using hydrogen [€/ASK].
        doc_energy_per_ask_medium_range_mean
            Energy direct operating cost per ASK for passenger medium-range market aircraft average [€/ASK].
        doc_energy_per_ask_short_range_dropin_fuel
            Energy direct operating cost per ASK for passenger short-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_per_ask_short_range_hydrogen
            Energy direct operating cost per ASK for passenger short-range market aircraft using hydrogen [€/ASK].
        doc_energy_per_ask_short_range_mean
            Energy direct operating cost per ASK for passenger short-range market aircraft average [€/ASK].
        doc_energy_per_ask_mean
            Energy direct operating cost per ASK for passenger overall market aircraft average [€/ASK].
        doc_energy_carbon_tax_per_ask_long_range_dropin_fuel
            Energy carbon tax direct operating cost per ASK for passenger long-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_carbon_tax_per_ask_long_range_hydrogen
            Energy carbon tax direct operating cost per ASK for passenger long-range market aircraft using hydrogen [€/ASK].
        doc_energy_carbon_tax_per_ask_long_range_mean
            Energy carbon tax direct operating cost per ASK for passenger long-range market aircraft average [€/ASK].
        doc_energy_carbon_tax_per_ask_medium_range_dropin_fuel
            Energy carbon tax direct operating cost per ASK for passenger medium-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_carbon_tax_per_ask_medium_range_hydrogen
            Energy carbon tax direct operating cost per ASK for passenger medium-range market aircraft using hydrogen [€/ASK].
        doc_energy_carbon_tax_per_ask_medium_range_mean
            Energy carbon tax direct operating cost per ASK for passenger medium-range market aircraft average [€/ASK].
        doc_energy_carbon_tax_per_ask_short_range_dropin_fuel
            Energy carbon tax direct operating cost per ASK for passenger short-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_carbon_tax_per_ask_short_range_hydrogen
            Energy carbon tax direct operating cost per ASK for passenger short-range market aircraft using hydrogen [€/ASK].
        doc_energy_carbon_tax_per_ask_short_range_mean
            Energy carbon tax direct operating cost per ASK for passenger short-range market aircraft average [€/ASK].
        doc_non_energy_per_ask_short_range_electric
            Non-energy direct operating cost per ASK for passenger short-range market aircraft using electric propulsion [€/ASK].
        doc_non_energy_per_ask_medium_range_electric
            Non-energy direct operating cost per ASK for passenger medium-range market aircraft using electric propulsion [€/ASK].
        doc_non_energy_per_ask_long_range_electric
            Non-energy direct operating cost per ASK for passenger long-range market aircraft using electric propulsion [€/ASK].
        doc_energy_per_ask_short_range_electric
            Energy direct operating cost per ASK for passenger short-range market aircraft using electric propulsion [€/ASK].
        doc_energy_per_ask_medium_range_electric
            Energy direct operating cost per ASK for passenger medium-range market aircraft using electric propulsion [€/ASK].
        doc_energy_per_ask_long_range_electric
            Energy direct operating cost per ASK for passenger long-range market aircraft using electric propulsion [€/ASK].
        doc_energy_carbon_tax_per_ask_short_range_electric
            Energy carbon tax direct operating cost per ASK for passenger short-range market aircraft using electric propulsion [€/ASK].
        doc_energy_carbon_tax_per_ask_medium_range_electric
            Energy carbon tax direct operating cost per ASK for passenger medium-range market aircraft using electric propulsion [€/ASK].
        doc_energy_carbon_tax_per_ask_long_range_electric
            Energy carbon tax direct operating cost per ASK for passenger long-range market aircraft using electric propulsion [€/ASK].
        doc_energy_carbon_tax_per_ask_mean
            Energy carbon tax direct operating cost per ASK for passenger overall market aircraft average [€/ASK].
        doc_energy_subsidy_per_ask_long_range_dropin_fuel
            Energy subsidy direct operating cost per ASK for passenger long-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_subsidy_per_ask_medium_range_dropin_fuel
            Energy subsidy direct operating cost per ASK for passenger medium-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_subsidy_per_ask_short_range_dropin_fuel
            Energy subsidy direct operating cost per ASK for passenger short-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_subsidy_per_ask_long_range_hydrogen
            Energy subsidy direct operating cost per ASK for passenger long-range market aircraft using hydrogen [€/ASK].
        doc_energy_subsidy_per_ask_medium_range_hydrogen
            Energy subsidy direct operating cost per ASK for passenger medium-range market aircraft using hydrogen [€/ASK].
        doc_energy_subsidy_per_ask_short_range_hydrogen
            Energy subsidy direct operating cost per ASK for passenger short-range market aircraft using hydrogen [€/ASK].
        doc_energy_subsidy_per_ask_long_range_electric
            Energy subsidy direct operating cost per ASK for passenger long-range market aircraft using electric propulsion [€/ASK].
        doc_energy_subsidy_per_ask_medium_range_electric
            Energy subsidy direct operating cost per ASK for passenger medium-range market aircraft using electric propulsion [€/ASK].
        doc_energy_subsidy_per_ask_short_range_electric
            Energy subsidy direct operating cost per ASK for passenger short-range market aircraft using electric propulsion [€/ASK].
        doc_energy_subsidy_per_ask_long_range_mean
            Energy subsidy direct operating cost per ASK for passenger long-range market aircraft average [€/ASK].
        doc_energy_subsidy_per_ask_medium_range_mean
            Energy subsidy direct operating cost per ASK for passenger medium-range market aircraft average [€/ASK].
        doc_energy_subsidy_per_ask_short_range_mean
            Energy subsidy direct operating cost per ASK for passenger short-range market aircraft average [€/ASK].
        doc_energy_subsidy_per_ask_mean
            Energy subsidy direct operating cost per ASK for passenger overall market aircraft average [€/ASK].
        doc_energy_tax_per_ask_long_range_dropin_fuel
            Energy tax direct operating cost per ASK for passenger long-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_tax_per_ask_medium_range_dropin_fuel
            Energy tax direct operating cost per ASK for passenger medium-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_tax_per_ask_short_range_dropin_fuel
            Energy tax direct operating cost per ASK for passenger short-range market aircraft using drop-in fuel [€/ASK].
        doc_energy_tax_per_ask_long_range_hydrogen
            Energy tax direct operating cost per ASK for passenger long-range market aircraft using hydrogen [€/ASK].
        doc_energy_tax_per_ask_medium_range_hydrogen
            Energy tax direct operating cost per ASK for passenger medium-range market aircraft using hydrogen [€/ASK].
        doc_energy_tax_per_ask_short_range_hydrogen
            Energy tax direct operating cost per ASK for passenger short-range market aircraft using hydrogen [€/ASK].
        doc_energy_tax_per_ask_long_range_electric
            Energy tax direct operating cost per ASK for passenger long-range market aircraft using electric propulsion [€/ASK].
        doc_energy_tax_per_ask_medium_range_electric
            Energy tax direct operating cost per ASK for passenger medium-range market aircraft using electric propulsion [€/ASK].
        doc_energy_tax_per_ask_short_range_electric
            Energy tax direct operating cost per ASK for passenger short-range market aircraft using electric propulsion [€/ASK].
        doc_energy_tax_per_ask_long_range_mean
            Energy tax direct operating cost per ASK for passenger long-range market aircraft average [€/ASK].
        doc_energy_tax_per_ask_medium_range_mean
            Energy tax direct operating cost per ASK for passenger medium-range market aircraft average [€/ASK].
        doc_energy_tax_per_ask_short_range_mean
            Energy tax direct operating cost per ASK for passenger short-range market aircraft average [€/ASK].
        doc_energy_tax_per_ask_mean
            Energy tax direct operating cost per ASK for passenger overall market aircraft average [€/ASK].

        Returns
        -------
        doc_total_per_ask_short_range_dropin_fuel
            Total direct operating cost per ASK for passenger short-range market aircraft using drop-in fuel [€/ASK].
        doc_total_per_ask_medium_range_dropin_fuel
            Total direct operating cost per ASK for passenger medium-range market aircraft using drop-in fuel [€/ASK].
        doc_total_per_ask_long_range_dropin_fuel
            Total direct operating cost per ASK for passenger long-range market aircraft using drop-in fuel [€/ASK].
        doc_total_per_ask_short_range_hydrogen
            Total direct operating cost per ASK for passenger short-range market aircraft using hydrogen [€/ASK].
        doc_total_per_ask_medium_range_hydrogen
            Total direct operating cost per ASK for passenger medium-range market aircraft using hydrogen [€/ASK].
        doc_total_per_ask_long_range_hydrogen
            Total direct operating cost per ASK for passenger long-range market aircraft using hydrogen [€/ASK].
        doc_total_per_ask_short_range_electric
            Total direct operating cost per ASK for passenger short-range market aircraft using electric propulsion [€/ASK].
        doc_total_per_ask_medium_range_electric
            Total direct operating cost per ASK for passenger medium-range market aircraft using electric propulsion [€/ASK].
        doc_total_per_ask_long_range_electric
            Total direct operating cost per ASK for passenger long-range market aircraft using electric propulsion [€/ASK].
        doc_total_per_ask_short_range_mean
            Total direct operating cost per ASK for passenger short-range market aircraft average [€/ASK].
        doc_total_per_ask_medium_range_mean
            Total direct operating cost per ASK for passenger medium-range market aircraft average [€/ASK].
        doc_total_per_ask_long_range_mean
            Total direct operating cost per ASK for passenger long-range market aircraft average [€/ASK].
        doc_total_per_ask_mean
            Total direct operating cost per ASK for passenger overall market aircraft average [€/ASK].
        """
        # Drop-in
        doc_total_per_ask_short_range_dropin_fuel = (
            doc_non_energy_per_ask_short_range_dropin_fuel
            + doc_energy_per_ask_short_range_dropin_fuel
            + doc_energy_carbon_tax_per_ask_short_range_dropin_fuel
            - doc_energy_subsidy_per_ask_short_range_dropin_fuel
            + doc_energy_tax_per_ask_short_range_dropin_fuel
        )

        doc_total_per_ask_medium_range_dropin_fuel = (
            doc_non_energy_per_ask_medium_range_dropin_fuel
            + doc_energy_per_ask_medium_range_dropin_fuel
            + doc_energy_carbon_tax_per_ask_medium_range_dropin_fuel
            - doc_energy_subsidy_per_ask_medium_range_dropin_fuel
            + doc_energy_tax_per_ask_medium_range_dropin_fuel
        )

        doc_total_per_ask_long_range_dropin_fuel = (
            doc_non_energy_per_ask_long_range_dropin_fuel
            + doc_energy_per_ask_long_range_dropin_fuel
            + doc_energy_carbon_tax_per_ask_long_range_dropin_fuel
            - doc_energy_subsidy_per_ask_long_range_dropin_fuel
            + doc_energy_tax_per_ask_long_range_dropin_fuel
        )

        # Hydrogen
        doc_total_per_ask_short_range_hydrogen = (
            doc_non_energy_per_ask_short_range_hydrogen
            + doc_energy_per_ask_short_range_hydrogen
            + doc_energy_carbon_tax_per_ask_short_range_hydrogen
            - doc_energy_subsidy_per_ask_short_range_hydrogen
            + doc_energy_tax_per_ask_short_range_hydrogen
        )

        doc_total_per_ask_medium_range_hydrogen = (
            doc_non_energy_per_ask_medium_range_hydrogen
            + doc_energy_per_ask_medium_range_hydrogen
            + doc_energy_carbon_tax_per_ask_medium_range_hydrogen
            - doc_energy_subsidy_per_ask_medium_range_hydrogen
            + doc_energy_tax_per_ask_medium_range_hydrogen
        )

        doc_total_per_ask_long_range_hydrogen = (
            doc_non_energy_per_ask_long_range_hydrogen
            + doc_energy_per_ask_long_range_hydrogen
            + doc_energy_carbon_tax_per_ask_long_range_hydrogen
            - doc_energy_subsidy_per_ask_long_range_hydrogen
            + doc_energy_tax_per_ask_long_range_hydrogen
        )

        # Electric
        doc_total_per_ask_short_range_electric = (
            doc_non_energy_per_ask_short_range_electric
            + doc_energy_per_ask_short_range_electric
            + doc_energy_carbon_tax_per_ask_short_range_electric
            - doc_energy_subsidy_per_ask_short_range_electric
            + doc_energy_tax_per_ask_short_range_electric
        )

        doc_total_per_ask_medium_range_electric = (
            doc_non_energy_per_ask_medium_range_electric
            + doc_energy_per_ask_medium_range_electric
            + doc_energy_carbon_tax_per_ask_medium_range_electric
            - doc_energy_subsidy_per_ask_medium_range_electric
            + doc_energy_tax_per_ask_medium_range_electric
        )

        doc_total_per_ask_long_range_electric = (
            doc_non_energy_per_ask_long_range_electric
            + doc_energy_per_ask_long_range_electric
            + doc_energy_carbon_tax_per_ask_long_range_electric
            - doc_energy_subsidy_per_ask_long_range_electric
            + doc_energy_tax_per_ask_long_range_electric
        )

        # Average per category
        doc_total_per_ask_short_range_mean = (
            doc_non_energy_per_ask_short_range_mean
            + doc_energy_per_ask_short_range_mean
            + doc_energy_carbon_tax_per_ask_short_range_mean
            - doc_energy_subsidy_per_ask_short_range_mean
            + doc_energy_tax_per_ask_short_range_mean
        )

        doc_total_per_ask_medium_range_mean = (
            doc_non_energy_per_ask_medium_range_mean
            + doc_energy_per_ask_medium_range_mean
            + doc_energy_carbon_tax_per_ask_medium_range_mean
            - doc_energy_subsidy_per_ask_medium_range_mean
            + doc_energy_tax_per_ask_medium_range_mean
        )

        doc_total_per_ask_long_range_mean = (
            doc_non_energy_per_ask_long_range_mean
            + doc_energy_per_ask_long_range_mean
            + doc_energy_carbon_tax_per_ask_long_range_mean
            - doc_energy_subsidy_per_ask_long_range_mean
            + doc_energy_tax_per_ask_long_range_mean
        )

        # Total average
        doc_total_per_ask_mean = (
            doc_non_energy_per_ask_mean
            + doc_energy_per_ask_mean
            + doc_energy_carbon_tax_per_ask_mean
            - doc_energy_subsidy_per_ask_mean
            + doc_energy_tax_per_ask_mean
        )

        self.df.loc[:, "doc_total_per_ask_short_range_dropin_fuel"] = (
            doc_total_per_ask_short_range_dropin_fuel
        )
        self.df.loc[:, "doc_total_per_ask_medium_range_dropin_fuel"] = (
            doc_total_per_ask_medium_range_dropin_fuel
        )
        self.df.loc[:, "doc_total_per_ask_long_range_dropin_fuel"] = (
            doc_total_per_ask_long_range_dropin_fuel
        )
        self.df.loc[:, "doc_total_per_ask_short_range_hydrogen"] = (
            doc_total_per_ask_short_range_hydrogen
        )
        self.df.loc[:, "doc_total_per_ask_medium_range_hydrogen"] = (
            doc_total_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "doc_total_per_ask_long_range_hydrogen"] = (
            doc_total_per_ask_long_range_hydrogen
        )
        self.df.loc[:, "doc_total_per_ask_short_range_electric"] = (
            doc_total_per_ask_short_range_electric
        )
        self.df.loc[:, "doc_total_per_ask_medium_range_electric"] = (
            doc_total_per_ask_medium_range_electric
        )
        self.df.loc[:, "doc_total_per_ask_long_range_electric"] = (
            doc_total_per_ask_long_range_electric
        )
        self.df.loc[:, "doc_total_per_ask_short_range_mean"] = doc_total_per_ask_short_range_mean
        self.df.loc[:, "doc_total_per_ask_medium_range_mean"] = doc_total_per_ask_medium_range_mean
        self.df.loc[:, "doc_total_per_ask_long_range_mean"] = doc_total_per_ask_long_range_mean
        self.df.loc[:, "doc_total_per_ask_mean"] = doc_total_per_ask_mean

        return (
            doc_total_per_ask_short_range_dropin_fuel,
            doc_total_per_ask_medium_range_dropin_fuel,
            doc_total_per_ask_long_range_dropin_fuel,
            doc_total_per_ask_short_range_hydrogen,
            doc_total_per_ask_medium_range_hydrogen,
            doc_total_per_ask_long_range_hydrogen,
            doc_total_per_ask_short_range_electric,
            doc_total_per_ask_medium_range_electric,
            doc_total_per_ask_long_range_electric,
            doc_total_per_ask_short_range_mean,
            doc_total_per_ask_medium_range_mean,
            doc_total_per_ask_long_range_mean,
            doc_total_per_ask_mean,
        )

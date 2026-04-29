"""
aicraft_efficiency
=====================

This module contains models to compute aircraft efficiency, either using simple models or outputs from generic fleet model.
"""

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function


class PassengerAircraftEfficiencySimpleShares(AeroMAPSModel):
    """
    Class to compute energy consumption per ASK (without operations) using simple annual improvement rates.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_efficiency_simple_shares' by default).

    Documentation
    --------------
    Inputs
        - energy_consumption_init: Historic total energy consumption [MJ].
        - ask_init: Historic total ASK [ASK].
        - fleet_renewal_duration: Fleet renewal duration [years].
        - covid_energy_intensity_per_ask_increase_2020: 2020 intensity increase [%].
        - <market>_energy_share_2019: 2019 passenger energy share [%].
        - <market>_rpk_share_2019: 2019 passenger RPK share [%].
        - <market>_energy_per_ask_dropin_fuel_gain_reference_years: Reference years.
        - <market>_energy_per_ask_dropin_fuel_gain_reference_years_values: Gains [%].
        - <market>_relative_energy_per_ask_hydrogen_wrt_dropin_reference_years: Reference years.
        - <market>_relative_energy_per_ask_hydrogen_wrt_dropin_reference_years_values: Ratios.
        - <market>_relative_energy_per_ask_electric_wrt_dropin_reference_years: Reference years.
        - <market>_relative_energy_per_ask_electric_wrt_dropin_reference_years_values: Ratios.
        - <market>_hydrogen_final_market_share: Final market share [%].
        - <market>_hydrogen_introduction_year: Introduction year [year].
        - <market>_electric_final_market_share: Final market share [%].
        - <market>_electric_introduction_year: Introduction year [year].
    Outputs
        - energy_per_ask_without_operations_<market>_<energy>: Energy per ASK [MJ/ASK].
        - ask_<market>_<energy>_share: ASK share per energy [%].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
    """

    def __init__(self, name="passenger_aircraft_efficiency_simple_shares", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        passenger_markets = self.markets.get(traffic_type="passenger")
        self.input_names = {
            "energy_consumption_init": pd.Series([0.0]),
            "ask_init": pd.Series([0.0]),
            "fleet_renewal_duration": 0.0,
            "covid_energy_intensity_per_ask_increase_2020": 0.0,
        }
        for m in passenger_markets:
            mid = m.id
            self.input_names[f"{mid}_energy_share_2019"] = 0.0
            self.input_names[f"{mid}_rpk_share_2019"] = 0.0
            self.input_names[f"{mid}_energy_per_ask_dropin_fuel_gain_reference_years"] = []
            self.input_names[f"{mid}_energy_per_ask_dropin_fuel_gain_reference_years_values"] = [
                0.0
            ]
            self.input_names[
                f"{mid}_relative_energy_per_ask_hydrogen_wrt_dropin_reference_years"
            ] = []
            self.input_names[
                f"{mid}_relative_energy_per_ask_hydrogen_wrt_dropin_reference_years_values"
            ] = [1.0]
            self.input_names[
                f"{mid}_relative_energy_per_ask_electric_wrt_dropin_reference_years"
            ] = []
            self.input_names[
                f"{mid}_relative_energy_per_ask_electric_wrt_dropin_reference_years_values"
            ] = [1.0]
            self.input_names[f"{mid}_hydrogen_final_market_share"] = 0.0
            self.input_names[f"{mid}_hydrogen_introduction_year"] = 2051.0
            self.input_names[f"{mid}_electric_final_market_share"] = 0.0
            self.input_names[f"{mid}_electric_introduction_year"] = 2051.0

        self.output_names = {}
        for m in passenger_markets:
            mid = m.id
            for et in ("dropin_fuel", "hydrogen", "electric"):
                self.output_names[f"energy_per_ask_without_operations_{mid}_{et}"] = pd.Series(
                    [0.0]
                )
                self.output_names[f"ask_{mid}_{et}_share"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        passenger_markets = self.markets.get(traffic_type="passenger")

        energy_consumption_init = input_data["energy_consumption_init"]
        ask_init = input_data["ask_init"]
        fleet_renewal_duration = float(input_data["fleet_renewal_duration"])
        covid_increase = float(input_data["covid_energy_intensity_per_ask_increase_2020"])

        energy_consumption_per_ask_init = energy_consumption_init / ask_init

        years_hist = np.arange(self.historic_start_year, self.prospection_start_year)
        idx_hist = pd.Index(years_hist)
        years_proj = np.arange(self.prospection_start_year, self.end_year + 1)
        idx_proj = pd.Index(years_proj)
        years_all = np.arange(self.historic_start_year, self.end_year + 1)

        output_data = {}

        for m in passenger_markets:
            mid = m.id
            energy_share = float(input_data[f"{mid}_energy_share_2019"])
            rpk_share = float(input_data[f"{mid}_rpk_share_2019"])

            dropin_col = f"energy_per_ask_without_operations_{mid}_dropin_fuel"

            self.df.loc[idx_hist, dropin_col] = (
                energy_consumption_per_ask_init.loc[idx_hist] * energy_share / rpk_share
            )

            gain = aeromaps_interpolation_function(
                self,
                list(input_data[f"{mid}_energy_per_ask_dropin_fuel_gain_reference_years"]),
                list(input_data[f"{mid}_energy_per_ask_dropin_fuel_gain_reference_years_values"]),
                model_name=self.name,
            )
            self.df.loc[:, f"energy_per_ask_dropin_fuel_gain_{mid}"] = gain

            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, dropin_col] = self.df.loc[k - 1, dropin_col] * (
                    1 - gain.loc[k] / 100
                )

            self.df.loc[2020, dropin_col] = self.df.loc[2019, dropin_col] * (
                1 + covid_increase / 100
            )

            dropin_series = self.df[dropin_col]

            h2_col = f"energy_per_ask_without_operations_{mid}_hydrogen"
            rel_h2 = aeromaps_interpolation_function(
                self,
                list(
                    input_data[f"{mid}_relative_energy_per_ask_hydrogen_wrt_dropin_reference_years"]
                ),
                list(
                    input_data[
                        f"{mid}_relative_energy_per_ask_hydrogen_wrt_dropin_reference_years_values"
                    ]
                ),
                model_name=self.name,
            )
            self.df.loc[idx_hist, h2_col] = dropin_series.loc[idx_hist]
            self.df.loc[idx_proj, h2_col] = dropin_series.loc[idx_proj] * rel_h2.loc[idx_proj]

            el_col = f"energy_per_ask_without_operations_{mid}_electric"
            rel_el = aeromaps_interpolation_function(
                self,
                list(
                    input_data[f"{mid}_relative_energy_per_ask_electric_wrt_dropin_reference_years"]
                ),
                list(
                    input_data[
                        f"{mid}_relative_energy_per_ask_electric_wrt_dropin_reference_years_values"
                    ]
                ),
                model_name=self.name,
            )
            self.df.loc[idx_hist, el_col] = dropin_series.loc[idx_hist]
            self.df.loc[idx_proj, el_col] = dropin_series.loc[idx_proj] * rel_el.loc[idx_proj]

            h2_share_col = f"ask_{mid}_hydrogen_share"
            self.df.loc[:, h2_share_col] = self._simple_sigmoid_share(
                years_all,
                float(input_data[f"{mid}_hydrogen_final_market_share"]),
                float(input_data[f"{mid}_hydrogen_introduction_year"]),
                fleet_renewal_duration,
            )

            el_share_col = f"ask_{mid}_electric_share"
            self.df.loc[:, el_share_col] = self._simple_sigmoid_share(
                years_all,
                float(input_data[f"{mid}_electric_final_market_share"]),
                float(input_data[f"{mid}_electric_introduction_year"]),
                fleet_renewal_duration,
            )

            dropin_share_col = f"ask_{mid}_dropin_fuel_share"
            self.df.loc[:, dropin_share_col] = 100 - self.df[h2_share_col] - self.df[el_share_col]

            output_data[dropin_col] = self.df[dropin_col]
            output_data[h2_col] = self.df[h2_col]
            output_data[el_col] = self.df[el_col]
            output_data[dropin_share_col] = self.df[dropin_share_col]
            output_data[h2_share_col] = self.df[h2_share_col]
            output_data[el_share_col] = self.df[el_share_col]

        self._store_outputs(output_data)
        return output_data

    @staticmethod
    def _simple_sigmoid_share(years, final_share, intro_year, fleet_renewal_duration):
        transition_year = intro_year + fleet_renewal_duration / 2
        share_limit = 0.02 * final_share
        share_param = np.log(100 / 2 - 1) / (fleet_renewal_duration / 2)
        share = final_share / (1 + np.exp(-share_param * (years - transition_year)))
        share = np.where(share < share_limit, 0, share)
        return share


class PassengerAircraftEfficiencySimpleASK(AeroMAPSModel):
    """
    Class to compute ASK for each aircraft type when using simple efficiency models.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_efficiency_simple_ask' by default).

    Documentation
    --------------
    Inputs
        - ask_<market>: Passenger ASK [ASK].
        - ask_<market>_hydrogen_share: Hydrogen share [%].
        - ask_<market>_electric_share: Electric share [%].
    Outputs
        - ask_<market>_dropin_fuel: Passenger ASK [ASK].
        - ask_<market>_hydrogen: Passenger ASK [ASK].
        - ask_<market>_electric: Passenger ASK [ASK].
        - ask_dropin_fuel: Total passenger ASK [ASK].
        - ask_hydrogen: Total passenger ASK [ASK].
        - ask_electric: Total passenger ASK [ASK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
    """

    def __init__(self, name="passenger_aircraft_efficiency_simple_ask", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        passenger_markets = self.markets.get(traffic_type="passenger")
        self.input_names = {}
        for m in passenger_markets:
            mid = m.id
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            self.input_names[f"ask_{mid}_hydrogen_share"] = pd.Series([0.0])
            self.input_names[f"ask_{mid}_electric_share"] = pd.Series([0.0])

        self.output_names = {}
        for m in passenger_markets:
            mid = m.id
            self.output_names[f"ask_{mid}_dropin_fuel"] = pd.Series([0.0])
            self.output_names[f"ask_{mid}_hydrogen"] = pd.Series([0.0])
            self.output_names[f"ask_{mid}_electric"] = pd.Series([0.0])
        self.output_names["ask_dropin_fuel"] = pd.Series([0.0])
        self.output_names["ask_hydrogen"] = pd.Series([0.0])
        self.output_names["ask_electric"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        passenger_markets = self.markets.get(traffic_type="passenger")

        output_data = {}
        total_dropin = None
        total_h2 = None
        total_el = None

        for m in passenger_markets:
            mid = m.id
            ask = input_data[f"ask_{mid}"]
            h2_share = input_data[f"ask_{mid}_hydrogen_share"]
            el_share = input_data[f"ask_{mid}_electric_share"]

            ask_h2 = ask * h2_share / 100
            ask_el = ask * el_share / 100
            ask_dropin = ask - ask_h2 - ask_el

            self.df.loc[:, f"ask_{mid}_hydrogen"] = ask_h2
            self.df.loc[:, f"ask_{mid}_electric"] = ask_el
            self.df.loc[:, f"ask_{mid}_dropin_fuel"] = ask_dropin

            output_data[f"ask_{mid}_dropin_fuel"] = ask_dropin
            output_data[f"ask_{mid}_hydrogen"] = ask_h2
            output_data[f"ask_{mid}_electric"] = ask_el

            total_dropin = ask_dropin if total_dropin is None else total_dropin + ask_dropin
            total_h2 = ask_h2 if total_h2 is None else total_h2 + ask_h2
            total_el = ask_el if total_el is None else total_el + ask_el

        self.df.loc[:, "ask_dropin_fuel"] = total_dropin
        self.df.loc[:, "ask_hydrogen"] = total_h2
        self.df.loc[:, "ask_electric"] = total_el

        output_data["ask_dropin_fuel"] = total_dropin
        output_data["ask_hydrogen"] = total_h2
        output_data["ask_electric"] = total_el

        self._store_outputs(output_data)
        return output_data


class PassengerAircraftEfficiencyComplex(AeroMAPSModel):
    """
    Class to compute energy consumption per ASK (without operations) using complex models.

    Parameters
    ----------
    name : str
        Name of the model instance ('passenger_aircraft_efficiency_complex' by default).

    Documentation
    --------------
    Inputs
        - dummy_fleet_model_output: Fleet-model trigger placeholder.
        - energy_consumption_init: Historic total energy consumption [MJ].
        - ask: Global passenger ASK [ASK].
        - covid_energy_intensity_per_ask_increase_2020: 2020 intensity increase [%].
        - <market>_energy_share_2019: 2019 passenger energy share [%].
        - <market>_rpk_share_2019: 2019 passenger RPK share [%].
        - ask_<market>: Passenger ASK [ASK].
    Outputs
        - energy_per_ask_without_operations_<market>_<energy>: Energy per ASK [MJ/ASK].
        - ask_<market>_<energy>_share: ASK share per energy [%].
        - ask_<market>_<energy>: Passenger ASK [ASK].
        - ask_dropin_fuel: Total passenger ASK [ASK].
        - ask_hydrogen: Total passenger ASK [ASK].
        - ask_electric: Total passenger ASK [ASK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.

    Attributes
    ----------
    fleet_model : FleetModel(AeroMAPSModel)
        FleetModel instance to be used for complex efficiency computations.
    """

    def __init__(self, name="passenger_aircraft_efficiency_complex", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.fleet_model = None
        self.markets = None

    def custom_setup(self):
        passenger_markets = self.markets.get(traffic_type="passenger")
        self.input_names = {
            "dummy_fleet_model_output": np.array([0.0]),
            "energy_consumption_init": pd.Series([0.0]),
            "ask": pd.Series([0.0]),
            "covid_energy_intensity_per_ask_increase_2020": 0.0,
        }
        for m in passenger_markets:
            mid = m.id
            self.input_names[f"{mid}_energy_share_2019"] = 0.0
            self.input_names[f"{mid}_rpk_share_2019"] = 0.0
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])

        self.output_names = {}
        for m in passenger_markets:
            mid = m.id
            for et in ("dropin_fuel", "hydrogen", "electric"):
                self.output_names[f"energy_per_ask_without_operations_{mid}_{et}"] = pd.Series(
                    [0.0]
                )
                self.output_names[f"ask_{mid}_{et}_share"] = pd.Series([0.0])
                self.output_names[f"ask_{mid}_{et}"] = pd.Series([0.0])
        self.output_names["ask_dropin_fuel"] = pd.Series([0.0])
        self.output_names["ask_hydrogen"] = pd.Series([0.0])
        self.output_names["ask_electric"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        passenger_markets = self.markets.get(traffic_type="passenger")

        energy_consumption_init = input_data["energy_consumption_init"]
        ask_global = input_data["ask"]
        covid_increase = float(input_data["covid_energy_intensity_per_ask_increase_2020"])

        energy_consumption_per_ask_init = energy_consumption_init / ask_global

        output_data = {}
        total_dropin = None
        total_h2 = None
        total_el = None

        for m in passenger_markets:
            mid = m.id
            market_name = m.name  # human-readable, matches fleet_model.df key
            energy_share = float(input_data[f"{mid}_energy_share_2019"])
            rpk_share = float(input_data[f"{mid}_rpk_share_2019"])
            ask_market = input_data[f"ask_{mid}"]

            energy_per_ask_without_operations_dropin_fuel_col = (
                f"energy_per_ask_without_operations_{mid}_dropin_fuel"
            )
            energy_per_ask_without_operations_hydrogen_col = (
                f"energy_per_ask_without_operations_{mid}_hydrogen"
            )
            energy_per_ask_without_operations_electric_col = (
                f"energy_per_ask_without_operations_{mid}_electric"
            )
            # idx_hist = pd.Index(range(self.historic_start_year, self.prospection_start_year))
            idx_proj = slice(self.prospection_start_year, self.end_year + 1)

            for k in range(self.historic_start_year, self.prospection_start_year):
                self.df.loc[k, energy_per_ask_without_operations_dropin_fuel_col] = (
                    energy_consumption_per_ask_init.loc[k] * energy_share / rpk_share
                )

            fleet_energy_per_ask_without_operations_dropin_fuel = self.fleet_model.df[
                f"{market_name}:energy_consumption:dropin_fuel"
            ]
            fleet_energy_per_ask_without_operations_hydrogen = self.fleet_model.df[
                f"{market_name}:energy_consumption:hydrogen"
            ]
            fleet_energy_per_ask_without_operations_electric = self.fleet_model.df[
                f"{market_name}:energy_consumption:electric"
            ]

            fleet_ask_dropin_fuel_share = self.fleet_model.df[f"{market_name}:share:dropin_fuel"]
            fleet_ask_hydrogen_share = self.fleet_model.df[f"{market_name}:share:hydrogen"]
            fleet_ask_electric_share = self.fleet_model.df[f"{market_name}:share:electric"]

            self.df[f"ask_{mid}_dropin_fuel_share"] = 100.0
            self.df[f"ask_{mid}_hydrogen_share"] = 0.0
            self.df[f"ask_{mid}_electric_share"] = 0.0
            self.df[energy_per_ask_without_operations_hydrogen_col] = 0.0
            self.df[energy_per_ask_without_operations_electric_col] = 0.0

            self.df.loc[idx_proj, energy_per_ask_without_operations_dropin_fuel_col] = (
                fleet_energy_per_ask_without_operations_dropin_fuel.loc[idx_proj]
            )
            self.df.loc[idx_proj, energy_per_ask_without_operations_hydrogen_col] = (
                fleet_energy_per_ask_without_operations_hydrogen.loc[idx_proj]
            )
            self.df.loc[idx_proj, energy_per_ask_without_operations_electric_col] = (
                fleet_energy_per_ask_without_operations_electric.loc[idx_proj]
            )

            self.df.loc[2020, energy_per_ask_without_operations_dropin_fuel_col] = self.df.loc[
                2019, energy_per_ask_without_operations_dropin_fuel_col
            ] * (1 + covid_increase / 100)

            self.df.loc[idx_proj, f"ask_{mid}_dropin_fuel_share"] = fleet_ask_dropin_fuel_share
            self.df.loc[idx_proj, f"ask_{mid}_hydrogen_share"] = fleet_ask_hydrogen_share
            self.df.loc[idx_proj, f"ask_{mid}_electric_share"] = fleet_ask_electric_share

            ask_dropin_fuel = ask_market * self.df[f"ask_{mid}_dropin_fuel_share"] / 100
            ask_hydrogen = ask_market * self.df[f"ask_{mid}_hydrogen_share"] / 100
            ask_electric = ask_market * self.df[f"ask_{mid}_electric_share"] / 100

            self.df.loc[:, f"ask_{mid}_dropin_fuel"] = ask_dropin_fuel
            self.df.loc[:, f"ask_{mid}_hydrogen"] = ask_hydrogen
            self.df.loc[:, f"ask_{mid}_electric"] = ask_electric

            output_data[energy_per_ask_without_operations_dropin_fuel_col] = self.df[
                energy_per_ask_without_operations_dropin_fuel_col
            ]
            output_data[energy_per_ask_without_operations_hydrogen_col] = self.df[
                energy_per_ask_without_operations_hydrogen_col
            ]
            output_data[energy_per_ask_without_operations_electric_col] = self.df[
                energy_per_ask_without_operations_electric_col
            ]
            output_data[f"ask_{mid}_dropin_fuel_share"] = self.df[f"ask_{mid}_dropin_fuel_share"]
            output_data[f"ask_{mid}_hydrogen_share"] = self.df[f"ask_{mid}_hydrogen_share"]
            output_data[f"ask_{mid}_electric_share"] = self.df[f"ask_{mid}_electric_share"]
            output_data[f"ask_{mid}_dropin_fuel"] = ask_dropin_fuel
            output_data[f"ask_{mid}_hydrogen"] = ask_hydrogen
            output_data[f"ask_{mid}_electric"] = ask_electric

            total_dropin = (
                ask_dropin_fuel if total_dropin is None else total_dropin + ask_dropin_fuel
            )
            total_h2 = ask_hydrogen if total_h2 is None else total_h2 + ask_hydrogen
            total_el = ask_electric if total_el is None else total_el + ask_electric

        self.df.loc[:, "ask_dropin_fuel"] = total_dropin
        self.df.loc[:, "ask_hydrogen"] = total_h2
        self.df.loc[:, "ask_electric"] = total_el

        output_data["ask_dropin_fuel"] = total_dropin
        output_data["ask_hydrogen"] = total_h2
        output_data["ask_electric"] = total_el

        self._store_outputs(output_data)
        return output_data


class FreightAircraftEfficiency(AeroMAPSModel):
    """Class to compute energy consumption per RTK (without operations) for freight aircraft.

    Parameters
    ----------
    name : str
        Name of the model instance ('freight_aircraft_efficiency' by default).

    Documentation
    --------------
    Inputs
        - energy_consumption_init: Historic total energy consumption [MJ].
        - rtk: Freight RTK [RTK].
        - ask: Global passenger ASK [ASK].
        - covid_energy_intensity_per_ask_increase_2020: 2020 intensity increase [%].
        - ask_<market>: Passenger ASK [ASK].
        - ask_<market>_dropin_fuel: Passenger ASK [ASK].
        - ask_<market>_hydrogen_share: Hydrogen share [%].
        - ask_<market>_electric_share: Electric share [%].
        - energy_per_ask_without_operations_<market>_dropin_fuel: Energy per ASK [MJ/ASK].
        - energy_per_ask_without_operations_<market>_hydrogen: Energy per ASK [MJ/ASK].
        - energy_per_ask_without_operations_<market>_electric: Energy per ASK [MJ/ASK].
        - <freight>_energy_share_2019: 2019 freight energy share [%].
    Outputs
        - energy_per_rtk_without_operations_freight_dropin_fuel: Energy per RTK [MJ/RTK].
        - energy_per_rtk_without_operations_freight_hydrogen: Energy per RTK [MJ/RTK].
        - energy_per_rtk_without_operations_freight_electric: Energy per RTK [MJ/RTK].
        - rtk_dropin_fuel_share: Freight RTK share [%].
        - rtk_hydrogen_share: Freight RTK share [%].
        - rtk_electric_share: Freight RTK share [%].
        - rtk_dropin_fuel: Freight RTK [RTK].
        - rtk_hydrogen: Freight RTK [RTK].
        - rtk_electric: Freight RTK [RTK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - <freight> is the MarketManager id (freight markets).
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
    """

    def __init__(self, name="freight_aircraft_efficiency", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        passenger_markets = self.markets.get(traffic_type="passenger")
        freight_markets = self.markets.get(traffic_type="freight")

        self.input_names = {
            "energy_consumption_init": pd.Series([0.0]),
            "rtk": pd.Series([0.0]),
            "ask": pd.Series([0.0]),
            "covid_energy_intensity_per_ask_increase_2020": 0.0,
        }

        # Per-passenger-market inputs
        for m in passenger_markets:
            mid = m.id
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            self.input_names[f"ask_{mid}_dropin_fuel"] = pd.Series([0.0])
            self.input_names[f"ask_{mid}_hydrogen_share"] = pd.Series([0.0])
            self.input_names[f"ask_{mid}_electric_share"] = pd.Series([0.0])
            self.input_names[f"energy_per_ask_without_operations_{mid}_dropin_fuel"] = pd.Series(
                [0.0]
            )
            self.input_names[f"energy_per_ask_without_operations_{mid}_hydrogen"] = pd.Series([0.0])
            self.input_names[f"energy_per_ask_without_operations_{mid}_electric"] = pd.Series([0.0])

        # Freight market energy share parameter
        for m in freight_markets:
            mid = m.id
            self.input_names[f"{mid}_energy_share_2019"] = 0.0

        self.output_names = {
            "energy_per_rtk_without_operations_freight_dropin_fuel": pd.Series([0.0]),
            "energy_per_rtk_without_operations_freight_hydrogen": pd.Series([0.0]),
            "energy_per_rtk_without_operations_freight_electric": pd.Series([0.0]),
            "rtk_dropin_fuel_share": pd.Series([0.0]),
            "rtk_hydrogen_share": pd.Series([0.0]),
            "rtk_electric_share": pd.Series([0.0]),
            "rtk_dropin_fuel": pd.Series([0.0]),
            "rtk_hydrogen": pd.Series([0.0]),
            "rtk_electric": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        passenger_markets = self.markets.get(traffic_type="passenger")
        freight_markets = self.markets.get(traffic_type="freight")

        energy_consumption_init = input_data["energy_consumption_init"]
        rtk = input_data["rtk"]
        ask = input_data["ask"]
        covid_increase = float(input_data["covid_energy_intensity_per_ask_increase_2020"])

        freight_mid = freight_markets[0].id
        freight_energy_share_2019 = float(input_data[f"{freight_mid}_energy_share_2019"])

        ask_per_market = {m.id: input_data[f"ask_{m.id}"] for m in passenger_markets}
        ask_dropin_per_market = {
            m.id: input_data[f"ask_{m.id}_dropin_fuel"] for m in passenger_markets
        }
        ask_h2_share_per_market = {
            m.id: input_data[f"ask_{m.id}_hydrogen_share"] for m in passenger_markets
        }
        ask_el_share_per_market = {
            m.id: input_data[f"ask_{m.id}_electric_share"] for m in passenger_markets
        }
        ep_dropin_per_market = {
            m.id: input_data[f"energy_per_ask_without_operations_{m.id}_dropin_fuel"]
            for m in passenger_markets
        }
        ep_h2_per_market = {
            m.id: input_data[f"energy_per_ask_without_operations_{m.id}_hydrogen"]
            for m in passenger_markets
        }
        ep_el_per_market = {
            m.id: input_data[f"energy_per_ask_without_operations_{m.id}_electric"]
            for m in passenger_markets
        }

        hist_years = list(range(self.historic_start_year, self.prospection_start_year))
        self.df.loc[hist_years, "energy_per_rtk_without_operations_freight_dropin_fuel"] = (
            energy_consumption_init.loc[hist_years]
            / rtk.loc[hist_years]
            * freight_energy_share_2019
            / 100
        )

        init_val = self.df.loc[2019, "energy_per_rtk_without_operations_freight_dropin_fuel"]
        rtk_dropin_per_market_k = {mid: init_val for mid in ask_dropin_per_market}

        for k in range(self.prospection_start_year, self.end_year + 1):
            for mid in ask_per_market:
                ep_prev = ep_dropin_per_market[mid].loc[k - 1]
                ep_curr = ep_dropin_per_market[mid].loc[k]
                ratio = ep_curr / ep_prev if ep_prev != 0 else 1.0
                rtk_dropin_per_market_k[mid] = rtk_dropin_per_market_k[mid] * ratio

            total_ask_dropin_k = sum(
                ask_dropin_per_market[mid].loc[k] for mid in ask_dropin_per_market
            )

            if total_ask_dropin_k > 0:
                self.df.loc[k, "energy_per_rtk_without_operations_freight_dropin_fuel"] = sum(
                    rtk_dropin_per_market_k[mid]
                    * ask_dropin_per_market[mid].loc[k]
                    / total_ask_dropin_k
                    for mid in ask_dropin_per_market
                )
            else:
                self.df.loc[k, "energy_per_rtk_without_operations_freight_dropin_fuel"] = init_val

        self.df.loc[2020, "energy_per_rtk_without_operations_freight_dropin_fuel"] = self.df.loc[
            2019, "energy_per_rtk_without_operations_freight_dropin_fuel"
        ] * (1 + covid_increase / 100)

        energy_per_rtk_dropin = self.df["energy_per_rtk_without_operations_freight_dropin_fuel"]

        rtk_h2_share = sum(
            ask_h2_share_per_market[m.id] * (ask_per_market[m.id] / ask) for m in passenger_markets
        )
        rtk_el_share = sum(
            ask_el_share_per_market[m.id] * (ask_per_market[m.id] / ask) for m in passenger_markets
        )
        rtk_dropin_share = 100 - rtk_h2_share - rtk_el_share

        self.df.loc[:, "rtk_hydrogen_share"] = rtk_h2_share
        self.df.loc[:, "rtk_dropin_fuel_share"] = rtk_dropin_share
        self.df.loc[:, "rtk_electric_share"] = rtk_el_share

        rtk_h2 = rtk * rtk_h2_share / 100
        rtk_el = rtk * rtk_el_share / 100
        rtk_dropin = rtk * rtk_dropin_share / 100
        self.df.loc[:, "rtk_hydrogen"] = rtk_h2
        self.df.loc[:, "rtk_dropin_fuel"] = rtk_dropin
        self.df.loc[:, "rtk_electric"] = rtk_el

        rel_h2_per_market = {
            m.id: ep_h2_per_market[m.id] / ep_dropin_per_market[m.id] for m in passenger_markets
        }
        rel_el_per_market = {
            m.id: ep_el_per_market[m.id] / ep_dropin_per_market[m.id] for m in passenger_markets
        }

        h2_zero_mask = rtk_h2_share == 0
        h2_nonzero_mask = ~h2_zero_mask

        self.df.loc[h2_zero_mask, "energy_per_rtk_without_operations_freight_hydrogen"] = (
            self.df.loc[h2_zero_mask, "energy_per_rtk_without_operations_freight_dropin_fuel"]
        )

        h2_weighted = sum(
            rel_h2_per_market[m.id] * ask_h2_share_per_market[m.id] * (ask_per_market[m.id] / ask)
            for m in passenger_markets
        )
        h2_weighted_nonzero = h2_weighted.loc[h2_nonzero_mask] / rtk_h2_share.loc[h2_nonzero_mask]

        self.df.loc[h2_nonzero_mask, "energy_per_rtk_without_operations_freight_hydrogen"] = (
            energy_per_rtk_dropin.loc[h2_nonzero_mask] * h2_weighted_nonzero
        )

        el_zero_mask = rtk_el_share == 0
        el_nonzero_mask = ~el_zero_mask

        self.df.loc[el_zero_mask, "energy_per_rtk_without_operations_freight_electric"] = (
            self.df.loc[el_zero_mask, "energy_per_rtk_without_operations_freight_dropin_fuel"]
        )

        el_weighted = sum(
            rel_el_per_market[m.id] * ask_el_share_per_market[m.id] * (ask_per_market[m.id] / ask)
            for m in passenger_markets
        )
        el_weighted_nonzero = el_weighted.loc[el_nonzero_mask] / rtk_el_share.loc[el_nonzero_mask]

        self.df.loc[el_nonzero_mask, "energy_per_rtk_without_operations_freight_electric"] = (
            energy_per_rtk_dropin.loc[el_nonzero_mask] * el_weighted_nonzero
        )

        output_data = {
            "energy_per_rtk_without_operations_freight_dropin_fuel": energy_per_rtk_dropin,
            "energy_per_rtk_without_operations_freight_hydrogen": self.df[
                "energy_per_rtk_without_operations_freight_hydrogen"
            ],
            "energy_per_rtk_without_operations_freight_electric": self.df[
                "energy_per_rtk_without_operations_freight_electric"
            ],
            "rtk_dropin_fuel_share": rtk_dropin_share,
            "rtk_hydrogen_share": rtk_h2_share,
            "rtk_electric_share": rtk_el_share,
            "rtk_dropin_fuel": rtk_dropin,
            "rtk_hydrogen": rtk_h2,
            "rtk_electric": rtk_el,
        }
        self._store_outputs(output_data)
        return output_data

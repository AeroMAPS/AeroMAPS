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
        - <market>_energy_share_last_historical_year: 2019 passenger energy share [%].
        - <market>_rpk_share_last_historical_year: 2019 passenger RPK share [%].
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
            self.input_names[f"{mid}_energy_share_last_historical_year"] = 0.0
            self.input_names[f"{mid}_rpk_share_last_historical_year"] = 0.0
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
            self.output_names[f"relative_energy_per_ask_hydrogen_wrt_dropin_{mid}"] = pd.Series(
                [1.0]
            )
            self.output_names[f"relative_energy_per_ask_electric_wrt_dropin_{mid}"] = pd.Series(
                [1.0]
            )
            for et in ("dropin_fuel", "hydrogen", "electric"):
                self.output_names[f"energy_per_ask_without_operations_{mid}_{et}"] = pd.Series(
                    [0.0]
                )
                self.output_names[f"ask_{mid}_{et}_share"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        """Compute per-market energy per ASK and propulsion shares.

        Parameters
        ----------
        input_data : dict
            Inputs for passenger market efficiency and propulsion shares.

        Returns
        -------
        dict
            Output series for energy per ASK and ASK shares by energy type.
        """
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
            energy_share = float(input_data[f"{mid}_energy_share_last_historical_year"])
            rpk_share = float(input_data[f"{mid}_rpk_share_last_historical_year"])

            dropin_col = f"energy_per_ask_without_operations_{mid}_dropin_fuel"

            # TODO: improve division by zero handling
            self.df.loc[idx_hist, dropin_col] = np.where(
                rpk_share != 0,
                energy_consumption_per_ask_init.loc[idx_hist] * energy_share / rpk_share,
                np.nan,
            )

            gain = aeromaps_interpolation_function(
                self,
                list(input_data[f"{mid}_energy_per_ask_dropin_fuel_gain_reference_years"]),
                list(input_data[f"{mid}_energy_per_ask_dropin_fuel_gain_reference_years_values"]),
                model_name=self.name,
            )

            # FIXME not as gemseo variable ? do we want it ?
            self.df.loc[:, f"energy_per_ask_{mid}_dropin_fuel_gain"] = gain

            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, dropin_col] = self.df.loc[k - 1, dropin_col] * (
                    1 - gain.loc[k] / 100
                )

            if self.prospection_start_year <= 2020:
                self.df.loc[2020, dropin_col] = self.df.loc[
                    self.last_historical_year, dropin_col
                ] * (1 + covid_increase / 100)

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

            output_data[f"relative_energy_per_ask_hydrogen_wrt_dropin_{mid}"] = rel_h2

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

            output_data[f"relative_energy_per_ask_electric_wrt_dropin_{mid}"] = rel_el

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
        - ask_dropin_fuel_share: Drop-in fuel ASK share for all markets [%].
        - ask_hydrogen_share: Hydrogen ASK share for all markets [%].
        - ask_electric_share: Electric ASK share for all markets [%].
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

        self.input_names["ask"] = pd.Series([0.0])
        for m in passenger_markets:
            mid = m.id
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            self.input_names[f"ask_{mid}_hydrogen_share"] = pd.Series([0.0])
            self.input_names[f"ask_{mid}_electric_share"] = pd.Series([0.0])

        self.output_names = {}
        for m in passenger_markets:
            mid = m.id
            for et in ("dropin_fuel", "hydrogen", "electric"):
                # Per-market ASK per energy type
                self.output_names[f"ask_{mid}_{et}"] = pd.Series([0.0])

        for et in ("dropin_fuel", "hydrogen", "electric"):
            # Overall ASK per energy type
            self.output_names[f"ask_{et}"] = pd.Series([0.0])
            # Overall ASK share per energy type
            self.output_names[f"ask_{et}_share"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        """Split per-market ASK into energy types and aggregate totals.

        Parameters
        ----------
        input_data : dict
            Inputs containing per-market ASK and propulsion shares.

        Returns
        -------
        dict
            ASK series and shares by energy type for each market and total.
        """
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

            output_data[f"ask_{mid}_hydrogen"] = ask_h2
            output_data[f"ask_{mid}_electric"] = ask_el
            output_data[f"ask_{mid}_dropin_fuel"] = ask_dropin

            total_dropin = ask_dropin if total_dropin is None else total_dropin + ask_dropin
            total_h2 = ask_h2 if total_h2 is None else total_h2 + ask_h2
            total_el = ask_el if total_el is None else total_el + ask_el

        ask_total = input_data["ask"]
        ask_dropin_fuel_share = (total_dropin / ask_total) * 100
        ask_hydrogen_share = (total_h2 / ask_total) * 100
        ask_electric_share = (total_el / ask_total) * 100

        output_data["ask_dropin_fuel"] = total_dropin
        output_data["ask_hydrogen"] = total_h2
        output_data["ask_electric"] = total_el

        output_data["ask_dropin_fuel_share"] = ask_dropin_fuel_share
        output_data["ask_hydrogen_share"] = ask_hydrogen_share
        output_data["ask_electric_share"] = ask_electric_share

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
        - <market>_energy_share_last_historical_year: 2019 passenger energy share [%].
        - <market>_rpk_share_last_historical_year: 2019 passenger RPK share [%].
        - ask_<market>: Passenger ASK [ASK].
    Outputs
        - energy_per_ask_without_operations_<market>_<energy>: Energy per ASK [MJ/ASK].
        - ask_<market>_<energy>_share: ASK share per energy [%].
        - ask_<market>_<energy>: Passenger ASK [ASK].
        - ask_dropin_fuel: Total passenger ASK [ASK].
        - ask_hydrogen: Total passenger ASK [ASK].
        - ask_electric: Total passenger ASK [ASK].
        - ask_dropin_fuel_share: Drop-in fuel ASK share for all markets [%].
        - ask_hydrogen_share: Hydrogen ASK share for all markets [%].
        - ask_electric_share: Electric ASK share for all markets [%].
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
            self.input_names[f"{mid}_energy_share_last_historical_year"] = 0.0
            self.input_names[f"{mid}_rpk_share_last_historical_year"] = 0.0
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

        for et in ("dropin_fuel", "hydrogen", "electric"):
            self.output_names[f"ask_{et}_share"] = pd.Series([0.0])
            self.output_names[f"ask_{et}"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        """Compute energy per ASK and propulsion shares using fleet outputs.

        Parameters
        ----------
        input_data : dict
            Inputs containing global ASK, market shares, and fleet signals.

        Returns
        -------
        dict
            Output series for energy per ASK and ASK shares by energy type.
        """
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
            energy_share = float(input_data[f"{mid}_energy_share_last_historical_year"])
            rpk_share = float(input_data[f"{mid}_rpk_share_last_historical_year"])
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

            years_hist = np.arange(self.historic_start_year, self.prospection_start_year)
            # TODO: improve division by zero handling
            self.df.loc[years_hist, energy_per_ask_without_operations_dropin_fuel_col] = np.where(
                rpk_share != 0,
                energy_consumption_per_ask_init.loc[years_hist] * energy_share / rpk_share,
                np.nan,
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

            if self.prospection_start_year <= 2020:
                self.df.loc[2020, energy_per_ask_without_operations_dropin_fuel_col] = self.df.loc[
                    self.last_historical_year, energy_per_ask_without_operations_dropin_fuel_col
                ] * (1 + covid_increase / 100)

            self.df.loc[idx_proj, f"ask_{mid}_dropin_fuel_share"] = fleet_ask_dropin_fuel_share
            self.df.loc[idx_proj, f"ask_{mid}_hydrogen_share"] = fleet_ask_hydrogen_share
            self.df.loc[idx_proj, f"ask_{mid}_electric_share"] = fleet_ask_electric_share

            ask_dropin_fuel = ask_market * self.df[f"ask_{mid}_dropin_fuel_share"] / 100
            ask_hydrogen = ask_market * self.df[f"ask_{mid}_hydrogen_share"] / 100
            ask_electric = ask_market * self.df[f"ask_{mid}_electric_share"] / 100

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

        ask_dropin_fuel_share = (total_dropin / ask_global) * 100
        ask_hydrogen_share = (total_h2 / ask_global) * 100
        ask_electric_share = (total_el / ask_global) * 100

        output_data["ask_dropin_fuel"] = total_dropin
        output_data["ask_hydrogen"] = total_h2
        output_data["ask_electric"] = total_el
        output_data["ask_dropin_fuel_share"] = ask_dropin_fuel_share
        output_data["ask_hydrogen_share"] = ask_hydrogen_share
        output_data["ask_electric_share"] = ask_electric_share

        self._store_outputs(output_data)
        return output_data


class FreightAircraftEfficiency(AeroMAPSModel):
    """Compute energy per RTK (without operations) and RTK volumes for freight aircraft.

    Freight aircraft do not have a dedicated fleet model.  Their efficiency
    evolution and propulsion-mix adoption are instead derived from the
    passenger markets, which *do* have fleet / top-down efficiency models.
    The derivation follows three steps.

    **Step 1 — Drop-in fuel efficiency (energy_per_rtk_without_operations_<freight>_dropin_fuel)**

    *Historical years* (historic_start_year … prospection_start_year − 1):
        Calibrated directly from total energy consumption and actual RTK::

            energy_per_rtk_dropin[year] = energy_consumption_init[year]
                                          / rtk[year]
                                          * freight_energy_share_last_historical_year / 100

    *Projection years* (prospection_start_year … end_year):
        Each passenger market m provides a year-on-year efficiency-improvement
        rate via its drop-in energy-per-ASK series.  The freight model keeps a
        separate per-market proxy ``energy_per_rtk_dropin_proxy[m]`` that starts
        at the 2019 freight value and is updated each year by the *same ratio*
        as that passenger market::

            ratio_m[k] = energy_per_ask_dropin[m, k] / energy_per_ask_dropin[m, k-1]
            energy_per_rtk_dropin_proxy[m, k] = energy_per_rtk_dropin_proxy[m, k-1] * ratio_m[k]

        The freight efficiency for year k is then a weighted average of these
        proxies, weighted by each market's dropin ASK volume::

            energy_per_rtk_dropin[k] =
                Σ_m ( energy_per_rtk_dropin_proxy[m, k] * ask_dropin[m, k] )
                / Σ_m ( ask_dropin[m, k] )

        Rationale: freight drop-in aircraft renew at a similar pace to passenger
        aircraft.  By anchoring to each passenger market's rate we capture
        differences in renewal speed between short/medium/long-range fleets.
        The ASK-dropin weighted average accounts for the relative size of each
        market fleet.

    *COVID correction*: the 2020 value is reset to::

        energy_per_rtk_dropin[2019] * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)

    **Step 2 — Propulsion mix (rtk_<freight>_<energy>_share)**

    Freight aircraft are assumed to adopt alternative propulsion in proportion to
    the passenger fleet.  The RTK share for each energy type is the ASK-weighted
    average of the corresponding passenger share across all passenger markets::

        rtk_hydrogen_share  = Σ_m ( ask_m / ask_total * ask_hydrogen_share[m] )
        rtk_electric_share  = Σ_m ( ask_m / ask_total * ask_electric_share[m] )
        rtk_dropin_share    = 100 − rtk_hydrogen_share − rtk_electric_share

    The same shares apply to *all* freight markets (belly and dedicated carry
    the same mix assumption).

    **Step 3 — Hydrogen and electric energy per RTK**

    For alternative propulsion types the model derives an average efficiency
    relative to drop-in by replicating the passenger ratio at the fleet level.

    Define the relative efficiency of propulsion type *p* vs drop-in for market m::

        rel_p[m] = energy_per_ask_p[m] / energy_per_ask_dropin[m]

    The fleet-wide weighted-sum for propulsion p is::

        p_weighted_sum = Σ_m ( rel_p[m] * ask_p_share[m] * ask_m / ask_total )

    Then::

        energy_per_rtk_p = energy_per_rtk_dropin
                           * p_weighted_sum / rtk_p_share      (when rtk_p_share > 0)
        energy_per_rtk_p = energy_per_rtk_dropin               (when rtk_p_share = 0,
                                                                 i.e. no aircraft of
                                                                 that type in service)

    The zero-share fallback keeps the value well-defined for downstream models
    even in years before any alternative-propulsion freight aircraft enters
    service.

    Parameters
    ----------
    name : str
        Name of the model instance ('freight_aircraft_efficiency' by default).

    Documentation
    --------------
    Inputs
        - energy_consumption_init: Historic total energy consumption [MJ].
        - ask: Global total passenger ASK [ASK].
        - covid_energy_intensity_per_ask_increase_2020: 2020 intensity increase [%].
        - rtk_<freight>: Freight RTK per freight market [RTK].
        - <freight>_energy_share_last_historical_year: 2019 freight energy share per freight market [%].
        - ask_<market>: Passenger ASK per passenger market [ASK].
        - ask_<market>_dropin_fuel: Drop-in fuel passenger ASK per market [ASK].
        - ask_<market>_hydrogen_share: Hydrogen ASK share per market [%].
        - ask_<market>_electric_share: Electric ASK share per market [%].
        - energy_per_ask_without_operations_<market>_dropin_fuel: Energy per ASK [MJ/ASK].
        - energy_per_ask_without_operations_<market>_hydrogen: Energy per ASK [MJ/ASK].
        - energy_per_ask_without_operations_<market>_electric: Energy per ASK [MJ/ASK].
    Outputs
        - energy_per_rtk_without_operations_<freight>_<energy>: Energy per RTK [MJ/RTK].
        - rtk_<freight>_<energy>_share: Freight RTK share per energy type [%].
        - rtk_<freight>_<energy>: Freight RTK per energy type [RTK].
        - rtk_<energy>_share: RTK share of energy type for all freight markets [%].
        - rtk_<energy>: Total RTK of energy type for all freight markets [RTK].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - <freight> is the MarketManager id (freight markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
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
            "ask": pd.Series([0.0]),
            "covid_energy_intensity_per_ask_increase_2020": 0.0,
            "rtk": pd.Series([0.0]),
        }

        # Per-passenger-market inputs (used as efficiency proxy for freight)
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

        # Per-freight-market inputs
        for m in freight_markets:
            mid = m.id
            self.input_names[f"rtk_{mid}"] = pd.Series([0.0])
            self.input_names[f"{mid}_energy_share_last_historical_year"] = 0.0

        # Per-freight-market outputs
        self.output_names = {}
        for m in freight_markets:
            mid = m.id
            for energy_type in ("dropin_fuel", "hydrogen", "electric"):
                self.output_names[f"energy_per_rtk_without_operations_{mid}_{energy_type}"] = (
                    pd.Series([0.0])
                )
                self.output_names[f"rtk_{mid}_{energy_type}_share"] = pd.Series([0.0])
                self.output_names[f"rtk_{mid}_{energy_type}"] = pd.Series([0.0])

        for energy_type in ("dropin_fuel", "hydrogen", "electric"):
            # Overall freight energy shares
            self.output_names[f"rtk_{energy_type}_share"] = pd.Series([0.0])
            # Overall freight RTK per energy type
            self.output_names[f"rtk_{energy_type}"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        """Derive freight energy per RTK and propulsion mix from passenger proxies.

        Parameters
        ----------
        input_data : dict
            Inputs containing passenger market ASK/efficiency and freight RTK.

        Returns
        -------
        dict
            Output series for freight energy per RTK and RTK splits by energy type.
        """
        passenger_markets = self.markets.get(traffic_type="passenger")
        freight_markets = self.markets.get(traffic_type="freight")

        # Extract global inputs
        energy_consumption_init = input_data["energy_consumption_init"]
        ask = input_data["ask"]
        covid_energy_intensity_per_ask_increase_2020 = float(
            input_data["covid_energy_intensity_per_ask_increase_2020"]
        )

        # Extract per-passenger-market inputs
        ask_per_market = {m.id: input_data[f"ask_{m.id}"] for m in passenger_markets}
        ask_dropin_fuel_per_market = {
            m.id: input_data[f"ask_{m.id}_dropin_fuel"] for m in passenger_markets
        }
        ask_hydrogen_share_per_market = {
            m.id: input_data[f"ask_{m.id}_hydrogen_share"] for m in passenger_markets
        }
        ask_electric_share_per_market = {
            m.id: input_data[f"ask_{m.id}_electric_share"] for m in passenger_markets
        }
        energy_per_ask_without_operations_dropin_fuel_per_market = {
            m.id: input_data[f"energy_per_ask_without_operations_{m.id}_dropin_fuel"]
            for m in passenger_markets
        }
        energy_per_ask_without_operations_hydrogen_per_market = {
            m.id: input_data[f"energy_per_ask_without_operations_{m.id}_hydrogen"]
            for m in passenger_markets
        }
        energy_per_ask_without_operations_electric_per_market = {
            m.id: input_data[f"energy_per_ask_without_operations_{m.id}_electric"]
            for m in passenger_markets
        }

        # begin with operations on passsneger markets to derive freight market values, then loop over freight markets to compute outputs

        # An empty passenger market (zero ASK — e.g. a region with no traffic in the scenario)
        # has an undefined per-ASK efficiency: PassengerAircraftEfficiency* sets it to NaN when
        # rpk_share is 0. It carries zero ASK weight, so it must contribute nothing to the freight
        # averages below; an unmasked ``NaN * 0`` would otherwise poison every freight market.
        def _passenger_ask_weighted_sum(per_market_value):
            """ASK-weighted sum over passenger markets; empty markets (zero ASK) contribute zero."""
            total = None
            for market in passenger_markets:
                mid = market.id
                contribution = (per_market_value(mid) * (ask_per_market[mid] / ask)).where(
                    ask_per_market[mid] != 0.0, 0.0
                )
                total = contribution if total is None else total + contribution
            return total

        # RTK shares: freight propulsion mix follows passenger ASK-weighted propulsion mix
        # (same for all freight markets, driven by the global passenger mix)
        rtk_hydrogen_share = _passenger_ask_weighted_sum(
            lambda mid: ask_hydrogen_share_per_market[mid]
        )
        rtk_electric_share = _passenger_ask_weighted_sum(
            lambda mid: ask_electric_share_per_market[mid]
        )
        rtk_dropin_fuel_share = 100 - rtk_hydrogen_share - rtk_electric_share

        # Relative efficiency of hydrogen and electric wrt dropin, per passenger market.
        # Empty markets yield NaN here (0/0 — both intensities are NaN); they are masked out of
        # the weighted sums above/below, so silence the intended divide-by-undefined.
        with np.errstate(invalid="ignore", divide="ignore"):
            relative_energy_per_ask_hydrogen_wrt_dropin_per_market = {
                m.id: energy_per_ask_without_operations_hydrogen_per_market[m.id]
                / energy_per_ask_without_operations_dropin_fuel_per_market[m.id]
                for m in passenger_markets
            }
            relative_energy_per_ask_electric_wrt_dropin_per_market = {
                m.id: energy_per_ask_without_operations_electric_per_market[m.id]
                / energy_per_ask_without_operations_dropin_fuel_per_market[m.id]
                for m in passenger_markets
            }

        # Hydrogen and electric efficiency weighted sums across passenger markets
        # (same for all freight markets, used to derive freight energy per RTK for alt. propulsion)
        hydrogen_weighted_sum = _passenger_ask_weighted_sum(
            lambda mid: relative_energy_per_ask_hydrogen_wrt_dropin_per_market[mid]
            * ask_hydrogen_share_per_market[mid]
        )
        electric_weighted_sum = _passenger_ask_weighted_sum(
            lambda mid: relative_energy_per_ask_electric_wrt_dropin_per_market[mid]
            * ask_electric_share_per_market[mid]
        )

        # Masks for years with/without hydrogen and electric usage (same for all freight markets)
        hydrogen_zero_mask = rtk_hydrogen_share == 0
        hydrogen_nonzero_mask = ~hydrogen_zero_mask
        electric_zero_mask = rtk_electric_share == 0
        electric_nonzero_mask = ~electric_zero_mask

        hist_years = list(range(self.historic_start_year, self.prospection_start_year))
        output_data = {}
        total_rtk_dropin_fuel = None
        total_rtk_hydrogen = None
        total_rtk_electric = None

        for freight_market in freight_markets:
            freight_mid = freight_market.id
            rtk = input_data[f"rtk_{freight_mid}"]
            freight_energy_share_last_historical_year = float(
                input_data[f"{freight_mid}_energy_share_last_historical_year"]
            )

            # Initialization based on 2019 share
            self.df.loc[
                hist_years, f"energy_per_rtk_without_operations_{freight_mid}_dropin_fuel"
            ] = (
                energy_consumption_init.loc[hist_years]
                / rtk.loc[hist_years]
                * freight_energy_share_last_historical_year
                / 100
            )

            # Projections: freight dropin fuel efficiency follows a weighted average of passenger
            # market efficiencies, each evolving at the same year-on-year rate as its passenger proxy
            init_energy_per_rtk_without_operations_dropin_fuel = self.df.loc[
                self.last_historical_year,
                f"energy_per_rtk_without_operations_{freight_mid}_dropin_fuel",
            ]
            energy_per_rtk_without_operations_dropin_fuel_per_market_k = {
                mid: init_energy_per_rtk_without_operations_dropin_fuel
                for mid in ask_dropin_fuel_per_market
            }

            for k in range(self.prospection_start_year, self.end_year + 1):
                # Apply the passenger year-on-year efficiency ratio to each market's freight proxy
                for mid in ask_per_market:
                    energy_per_ask_dropin_fuel_prev = (
                        energy_per_ask_without_operations_dropin_fuel_per_market[mid].loc[k - 1]
                    )
                    energy_per_ask_dropin_fuel_k = (
                        energy_per_ask_without_operations_dropin_fuel_per_market[mid].loc[k]
                    )
                    # Empty passenger markets have undefined (NaN) per-ASK efficiency; keep their
                    # proxy unchanged (ratio 1.0) so it stays finite. They contribute nothing once
                    # weighted by their zero ASK below.
                    efficiency_ratio = (
                        energy_per_ask_dropin_fuel_k / energy_per_ask_dropin_fuel_prev
                        if energy_per_ask_dropin_fuel_prev != 0
                        and np.isfinite(energy_per_ask_dropin_fuel_prev)
                        and np.isfinite(energy_per_ask_dropin_fuel_k)
                        else 1.0
                    )
                    energy_per_rtk_without_operations_dropin_fuel_per_market_k[mid] = (
                        energy_per_rtk_without_operations_dropin_fuel_per_market_k[mid]
                        * efficiency_ratio
                    )

                # Weighted average across passenger markets by dropin ASK share
                ask_total_dropin_fuel_k = sum(
                    ask_dropin_fuel_per_market[mid].loc[k] for mid in ask_dropin_fuel_per_market
                )

                if ask_total_dropin_fuel_k > 0:
                    # Skip empty markets (zero dropin ASK): their proxy may be undefined and
                    # ``NaN * 0`` would leak into the freight efficiency.
                    self.df.loc[
                        k, f"energy_per_rtk_without_operations_{freight_mid}_dropin_fuel"
                    ] = sum(
                        energy_per_rtk_without_operations_dropin_fuel_per_market_k[mid]
                        * ask_dropin_fuel_per_market[mid].loc[k]
                        / ask_total_dropin_fuel_k
                        for mid in ask_dropin_fuel_per_market
                        if ask_dropin_fuel_per_market[mid].loc[k] != 0
                    )
                else:
                    self.df.loc[
                        k, f"energy_per_rtk_without_operations_{freight_mid}_dropin_fuel"
                    ] = init_energy_per_rtk_without_operations_dropin_fuel

            # Covid: reset 2020 value
            if self.prospection_start_year <= 2020:
                self.df.loc[
                    2020, f"energy_per_rtk_without_operations_{freight_mid}_dropin_fuel"
                ] = self.df.loc[
                    self.last_historical_year,
                    f"energy_per_rtk_without_operations_{freight_mid}_dropin_fuel",
                ] * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)

            energy_per_rtk_without_operations_dropin_fuel = self.df[
                f"energy_per_rtk_without_operations_{freight_mid}_dropin_fuel"
            ]

            # RTK volumes per energy type for this freight market
            rtk_hydrogen = rtk * rtk_hydrogen_share / 100
            rtk_electric = rtk * rtk_electric_share / 100
            rtk_dropin_fuel = rtk * rtk_dropin_fuel_share / 100

            # Hydrogen energy per RTK: equals dropin when no hydrogen is used,
            # otherwise ASK-weighted passenger ratio applied to dropin efficiency
            self.df.loc[
                hydrogen_zero_mask,
                f"energy_per_rtk_without_operations_{freight_mid}_hydrogen",
            ] = self.df.loc[
                hydrogen_zero_mask,
                f"energy_per_rtk_without_operations_{freight_mid}_dropin_fuel",
            ]
            self.df.loc[
                hydrogen_nonzero_mask,
                f"energy_per_rtk_without_operations_{freight_mid}_hydrogen",
            ] = (
                energy_per_rtk_without_operations_dropin_fuel.loc[hydrogen_nonzero_mask]
                * hydrogen_weighted_sum.loc[hydrogen_nonzero_mask]
                / rtk_hydrogen_share.loc[hydrogen_nonzero_mask]
            )

            # Electric energy per RTK: equals dropin when no electric is used,
            # otherwise ASK-weighted passenger ratio applied to dropin efficiency
            self.df.loc[
                electric_zero_mask,
                f"energy_per_rtk_without_operations_{freight_mid}_electric",
            ] = self.df.loc[
                electric_zero_mask,
                f"energy_per_rtk_without_operations_{freight_mid}_dropin_fuel",
            ]
            self.df.loc[
                electric_nonzero_mask,
                f"energy_per_rtk_without_operations_{freight_mid}_electric",
            ] = (
                energy_per_rtk_without_operations_dropin_fuel.loc[electric_nonzero_mask]
                * electric_weighted_sum.loc[electric_nonzero_mask]
                / rtk_electric_share.loc[electric_nonzero_mask]
            )

            output_data[f"energy_per_rtk_without_operations_{freight_mid}_dropin_fuel"] = (
                energy_per_rtk_without_operations_dropin_fuel
            )
            output_data[f"energy_per_rtk_without_operations_{freight_mid}_hydrogen"] = self.df[
                f"energy_per_rtk_without_operations_{freight_mid}_hydrogen"
            ]
            output_data[f"energy_per_rtk_without_operations_{freight_mid}_electric"] = self.df[
                f"energy_per_rtk_without_operations_{freight_mid}_electric"
            ]
            output_data[f"rtk_{freight_mid}_dropin_fuel_share"] = rtk_dropin_fuel_share
            output_data[f"rtk_{freight_mid}_hydrogen_share"] = rtk_hydrogen_share
            output_data[f"rtk_{freight_mid}_electric_share"] = rtk_electric_share
            output_data[f"rtk_{freight_mid}_dropin_fuel"] = rtk_dropin_fuel
            output_data[f"rtk_{freight_mid}_hydrogen"] = rtk_hydrogen
            output_data[f"rtk_{freight_mid}_electric"] = rtk_electric

            total_rtk_dropin_fuel = (
                rtk_dropin_fuel
                if total_rtk_dropin_fuel is None
                else total_rtk_dropin_fuel + rtk_dropin_fuel
            )
            total_rtk_hydrogen = (
                rtk_hydrogen if total_rtk_hydrogen is None else total_rtk_hydrogen + rtk_hydrogen
            )
            total_rtk_electric = (
                rtk_electric if total_rtk_electric is None else total_rtk_electric + rtk_electric
            )

        rtk_total = input_data["rtk"]
        rtk_dropin_fuel_share = (total_rtk_dropin_fuel / rtk_total) * 100
        rtk_hydrogen_share = (total_rtk_hydrogen / rtk_total) * 100
        rtk_electric_share = (total_rtk_electric / rtk_total) * 100

        output_data["rtk_dropin_fuel"] = total_rtk_dropin_fuel
        output_data["rtk_hydrogen"] = total_rtk_hydrogen
        output_data["rtk_electric"] = total_rtk_electric

        output_data["rtk_dropin_fuel_share"] = rtk_dropin_fuel_share
        output_data["rtk_hydrogen_share"] = rtk_hydrogen_share
        output_data["rtk_electric_share"] = rtk_electric_share

        self._store_outputs(output_data)
        return output_data


class FreightAircraftEfficiencySimple(AeroMAPSModel):
    """Simple top-down freight efficiency model — drop-in fuel only, per market.

    Alternative to :class:`FreightAircraftEfficiency`. Should be specified in
    the models list in place of FreightAircaftEfficiency, and related inputs should be provided in markets.yaml.

    Each freight market follows its **own drop-in efficiency gain curve**
    (independent of the passenger fleet). Alternative propulsion (hydrogen,
    electric) is not modelled: shares are pinned to 0 and the energy-per-RTK
    series for those carriers is set equal to the drop-in series so downstream
    models remain well-defined.

    Outputs follow the same templated names as :class:`FreightAircraftEfficiency`
    so downstream consumers (``DropInFuelConsumption``, ``CO2Emissions``,
    ``FleetAbatementCost`` …) are mode-agnostic.

    Algorithm
    ---------
    For each freight market ``<fmid>``:

    *Historical years*: same calibration as the passenger-proxy model::

        energy_per_rtk_dropin[year] = energy_consumption_init[year]
                                      / rtk_<fmid>[year]
                                      * <fmid>_energy_share_last_historical_year / 100

    *Projection years*: per-market drop-in gain curve::

        energy_per_rtk_dropin[k] = energy_per_rtk_dropin[k-1] * (1 - gain[k]/100)

    where ``gain`` is interpolated from
    ``<fmid>_energy_per_rtk_dropin_fuel_gain_reference_years[_values]``.

    *COVID correction*: 2020 value is reset to::

        energy_per_rtk_dropin[2019] * (1 + covid_energy_intensity_per_rtk_increase_2020 / 100)

    *Hydrogen / electric*: energy_per_rtk equals the drop-in series; shares
    are 0; per-market RTK volumes are 0.

    Documentation
    --------------
    Inputs
        - energy_consumption_init: Historic total energy consumption [MJ].
        - covid_energy_intensity_per_rtk_increase_2020: 2020 intensity increase [%].
        - rtk: Global freight RTK [RTK].
        - rtk_<freight>: Freight RTK per freight market [RTK].
        - <freight>_energy_share_last_historical_year: 2019 freight energy share per freight market [%].
        - <freight>_energy_per_rtk_dropin_fuel_gain_reference_years: Reference years.
        - <freight>_energy_per_rtk_dropin_fuel_gain_reference_years_values: Gains [%].
    Outputs
        - energy_per_rtk_without_operations_<freight>_<energy>: Energy per RTK [MJ/RTK].
        - rtk_<freight>_<energy>_share: Freight RTK share per energy type [%].
        - rtk_<freight>_<energy>: Freight RTK per energy type [RTK].
        - rtk_<energy>_share: RTK share of energy type for all freight markets [%].
        - rtk_<energy>: Total RTK of energy type for all freight markets [RTK].
    Notes
        - <freight> is the MarketManager id (freight markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
        - I/O names are built dynamically from the market registry.
    """

    def __init__(self, name="freight_aircraft_efficiency", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        freight_markets = self.markets.get(traffic_type="freight")

        self.input_names = {
            "energy_consumption_init": pd.Series([0.0]),
            "covid_energy_intensity_per_rtk_increase_2020": 0.0,
            "rtk": pd.Series([0.0]),
        }

        for m in freight_markets:
            mid = m.id
            self.input_names[f"rtk_{mid}"] = pd.Series([0.0])
            self.input_names[f"{mid}_energy_share_last_historical_year"] = 0.0
            self.input_names[f"{mid}_energy_per_rtk_dropin_fuel_gain_reference_years"] = []
            self.input_names[f"{mid}_energy_per_rtk_dropin_fuel_gain_reference_years_values"] = [
                0.0
            ]

        self.output_names = {}
        for m in freight_markets:
            mid = m.id
            for energy_type in ("dropin_fuel", "hydrogen", "electric"):
                self.output_names[f"energy_per_rtk_without_operations_{mid}_{energy_type}"] = (
                    pd.Series([0.0])
                )
                self.output_names[f"rtk_{mid}_{energy_type}_share"] = pd.Series([0.0])
                self.output_names[f"rtk_{mid}_{energy_type}"] = pd.Series([0.0])

        for energy_type in ("dropin_fuel", "hydrogen", "electric"):
            self.output_names[f"rtk_{energy_type}_share"] = pd.Series([0.0])
            self.output_names[f"rtk_{energy_type}"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        freight_markets = self.markets.get(traffic_type="freight")

        energy_consumption_init = input_data["energy_consumption_init"]
        covid_increase = float(input_data["covid_energy_intensity_per_rtk_increase_2020"])

        hist_years = list(range(self.historic_start_year, self.prospection_start_year))
        output_data = {}
        total_rtk_dropin_fuel = None
        total_rtk_hydrogen = None
        total_rtk_electric = None

        for freight_market in freight_markets:
            freight_mid = freight_market.id
            rtk = input_data[f"rtk_{freight_mid}"]
            freight_energy_share_last_historical_year = float(
                input_data[f"{freight_mid}_energy_share_last_historical_year"]
            )

            dropin_col = f"energy_per_rtk_without_operations_{freight_mid}_dropin_fuel"

            # Historical calibration: same formula as FreightAircraftEfficiency.
            self.df.loc[hist_years, dropin_col] = (
                energy_consumption_init.loc[hist_years]
                / rtk.loc[hist_years]
                * freight_energy_share_last_historical_year
                / 100
            )

            # Per-market drop-in efficiency gain curve.
            gain = aeromaps_interpolation_function(
                self,
                list(input_data[f"{freight_mid}_energy_per_rtk_dropin_fuel_gain_reference_years"]),
                list(
                    input_data[
                        f"{freight_mid}_energy_per_rtk_dropin_fuel_gain_reference_years_values"
                    ]
                ),
                model_name=self.name,
            )

            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, dropin_col] = self.df.loc[k - 1, dropin_col] * (
                    1 - gain.loc[k] / 100
                )

            # COVID: reset 2020 value.
            if self.prospection_start_year <= 2020:
                self.df.loc[2020, dropin_col] = self.df.loc[
                    self.last_historical_year, dropin_col
                ] * (1 + covid_increase / 100)

            energy_per_rtk_dropin = self.df[dropin_col]

            # No alternative propulsion: H2/electric energy_per_rtk equals drop-in,
            # shares are zero, per-market RTK volumes are zero.
            h2_col = f"energy_per_rtk_without_operations_{freight_mid}_hydrogen"
            el_col = f"energy_per_rtk_without_operations_{freight_mid}_electric"
            self.df.loc[:, h2_col] = energy_per_rtk_dropin
            self.df.loc[:, el_col] = energy_per_rtk_dropin

            rtk_dropin_fuel = rtk
            rtk_hydrogen = rtk * 0.0
            rtk_electric = rtk * 0.0

            output_data[dropin_col] = energy_per_rtk_dropin
            output_data[h2_col] = self.df[h2_col]
            output_data[el_col] = self.df[el_col]
            output_data[f"rtk_{freight_mid}_dropin_fuel_share"] = pd.Series(
                100.0, index=energy_per_rtk_dropin.index
            )
            output_data[f"rtk_{freight_mid}_hydrogen_share"] = pd.Series(
                0.0, index=energy_per_rtk_dropin.index
            )
            output_data[f"rtk_{freight_mid}_electric_share"] = pd.Series(
                0.0, index=energy_per_rtk_dropin.index
            )
            output_data[f"rtk_{freight_mid}_dropin_fuel"] = rtk_dropin_fuel
            output_data[f"rtk_{freight_mid}_hydrogen"] = rtk_hydrogen
            output_data[f"rtk_{freight_mid}_electric"] = rtk_electric

            total_rtk_dropin_fuel = (
                rtk_dropin_fuel
                if total_rtk_dropin_fuel is None
                else total_rtk_dropin_fuel + rtk_dropin_fuel
            )
            total_rtk_hydrogen = (
                rtk_hydrogen if total_rtk_hydrogen is None else total_rtk_hydrogen + rtk_hydrogen
            )
            total_rtk_electric = (
                rtk_electric if total_rtk_electric is None else total_rtk_electric + rtk_electric
            )

        rtk_total = input_data["rtk"]
        output_data["rtk_dropin_fuel"] = total_rtk_dropin_fuel
        output_data["rtk_hydrogen"] = total_rtk_hydrogen
        output_data["rtk_electric"] = total_rtk_electric
        output_data["rtk_dropin_fuel_share"] = (total_rtk_dropin_fuel / rtk_total) * 100
        output_data["rtk_hydrogen_share"] = (total_rtk_hydrogen / rtk_total) * 100
        output_data["rtk_electric_share"] = (total_rtk_electric / rtk_total) * 100

        self._store_outputs(output_data)
        return output_data

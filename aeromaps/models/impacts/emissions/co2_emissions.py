"""
co2_emissions
===========
This module contains models for calculating CO2 emissions and related factors.
"""

import re
from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.utils.defaults import get_default_series


def slugify(name: str) -> str:
    """Convert an arbitrary name (aircraft, category...) into a valid variable name chunk."""
    return re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()


def aircraft_efficiency_lever_names(fleet) -> dict:
    """
    Map each aircraft of a fleet to the name of the output variable containing its
    contribution to the aircraft efficiency lever of action.

    Used both by DetailedCo2EmissionsPerAircraft and by the plots so that variable
    names are built consistently.

    Parameters
    ----------
    fleet
        Fleet instance containing the fleet structure and aircraft definitions.

    Returns
    -------
    lever_names
        Dictionary mapping (category name, subcategory name, aircraft name) tuples
        to output variable names.
    """
    lever_names = {}
    for category in fleet.categories.values():
        for subcategory in category.subcategories.values():
            for aircraft in subcategory.aircraft.values():
                lever_name = (
                    f"co2_emissions_lever_efficiency_"
                    f"{slugify(category.name)}_{slugify(aircraft.name)}"
                )
                if lever_name in lever_names.values():
                    lever_name = (
                        f"co2_emissions_lever_efficiency_{slugify(category.name)}_"
                        f"{slugify(subcategory.name)}_{slugify(aircraft.name)}"
                    )
                lever_names[(category.name, subcategory.name, aircraft.name)] = lever_name
    return lever_names


# Levers of the CO2 emissions cascade that DetailedCo2EmissionsPerMarket decomposes
# by market. Freight is not affected by the (passenger) load factor lever.
MARKET_LEVERS_PASSENGER = ("efficiency", "operations", "loadfactor", "energy")
MARKET_LEVERS_FREIGHT = ("efficiency", "operations", "energy")

# Pseudo-market key holding the per-lever cross-market-mix residual.
MARKET_CROSS_MIX = "cross_mix"


def market_lever_column(lever: str, market: str) -> str:
    """Output column holding the contribution of `market` to the CO2 `lever`.

    Single source of truth for the per-market decomposition variable names, shared
    by DetailedCo2EmissionsPerMarket, its plot and the tests so that the naming
    never drifts and consumers never have to guess it via prefix matching.
    """
    return f"co2_emissions_lever_{lever}_market_{market}"


def market_lever_names(markets) -> dict:
    """
    Map each (lever, market) pair to its per-market decomposition output column.

    Parameters
    ----------
    markets
        MarketManager enumerating the passenger and freight markets.

    Returns
    -------
    names
        Dictionary mapping ``(lever, market_id)`` tuples — plus
        ``(lever, "cross_mix")`` for the cross-market-mix residual of each lever —
        to output variable names.
    """
    names = {}
    for market in markets.get(traffic_type="passenger"):
        for lever in MARKET_LEVERS_PASSENGER:
            names[(lever, market.id)] = market_lever_column(lever, market.id)
    for market in markets.get(traffic_type="freight"):
        for lever in MARKET_LEVERS_FREIGHT:
            names[(lever, market.id)] = market_lever_column(lever, market.id)
    for lever in MARKET_LEVERS_PASSENGER:
        names[(lever, MARKET_CROSS_MIX)] = market_lever_column(lever, MARKET_CROSS_MIX)
    return names


def market_lever_dataframe(df: pd.DataFrame, markets) -> pd.DataFrame:
    """
    Reshape the flat per-market lever columns of `df` into a tidy view.

    The returned DataFrame keeps the years index of `df` and carries a
    ``(lever, market)`` MultiIndex on its columns, so the multidimensional
    decomposition can be filtered efficiently, e.g.::

        per_market = market_lever_dataframe(df, markets)
        per_market.xs("energy", level="lever", axis=1)      # all markets, energy lever
        per_market.xs("short_range", level="market", axis=1)  # all levers, one market

    Columns absent from `df` (e.g. freight has no load factor lever) are simply
    omitted.

    Parameters
    ----------
    df
        Vector-outputs DataFrame produced by a computed process.
    markets
        MarketManager enumerating the passenger and freight markets.

    Returns
    -------
    tidy
        DataFrame with a ``(lever, market)`` column MultiIndex.
    """
    names = market_lever_names(markets)
    data = {key: df[column] for key, column in names.items() if column in df.columns}
    tidy = pd.DataFrame(data, index=df.index)
    if not tidy.empty:
        tidy.columns = pd.MultiIndex.from_tuples(tidy.columns, names=["lever", "market"])
    return tidy


class KayaFactors(AeroMAPSModel):
    """
    Class to compute Kaya factors for CO2 emissions calculation.

    Parameters
    --------------
    name : str
        Name of the model instance ('kaya_factors' by default).
    """

    def __init__(self, name="kaya_factors", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        ask: pd.Series,
        rtk: pd.Series,
        energy_consumption_passenger_dropin_fuel_without_operations: pd.Series,
        energy_consumption_passenger_hydrogen_without_operations: pd.Series,
        energy_consumption_passenger_electric_without_operations: pd.Series,
        energy_consumption_passenger_dropin_fuel: pd.Series,
        energy_consumption_passenger_hydrogen: pd.Series,
        energy_consumption_passenger_electric: pd.Series,
        energy_consumption_freight_dropin_fuel_without_operations: pd.Series,
        energy_consumption_freight_hydrogen_without_operations: pd.Series,
        energy_consumption_freight_electric_without_operations: pd.Series,
        energy_consumption_freight_dropin_fuel: pd.Series,
        energy_consumption_freight_hydrogen: pd.Series,
        energy_consumption_freight_electric: pd.Series,
        energy_consumption_dropin_fuel: pd.Series,
        energy_consumption_hydrogen: pd.Series,
        energy_consumption_electric: pd.Series,
        energy_consumption: pd.Series,
        dropin_fuel_mean_co2_emission_factor: pd.Series,
        hydrogen_mean_co2_emission_factor: pd.Series,
        electric_mean_co2_emission_factor: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Execute the computation of Kaya factors for CO2 emissions calculation.

        Parameters
        ----------
        ask
            Available seat kilometers (ASK) [ASK].
        rtk
            Revenue ton kilometers (RTK) [RTK].
        energy_consumption_passenger_dropin_fuel_without_operations
            Energy consumption for passenger transport using drop-in fuels without operational improvements [MJ].
        energy_consumption_passenger_hydrogen_without_operations
            Energy consumption for passenger transport using hydrogen without operational improvements [MJ].
        energy_consumption_passenger_electric_without_operations
            Energy consumption for passenger transport using electricity without operational improvements [MJ].
        energy_consumption_passenger_dropin_fuel
            Energy consumption for passenger transport using drop-in fuels [MJ].
        energy_consumption_passenger_hydrogen
            Energy consumption for passenger transport using hydrogen [MJ].
        energy_consumption_passenger_electric
            Energy consumption for passenger transport using electricity [MJ].
        energy_consumption_freight_dropin_fuel_without_operations
            Energy consumption for freight transport using drop-in fuels without operational improvements [MJ].
        energy_consumption_freight_hydrogen_without_operations
            Energy consumption for freight transport using hydrogen without operational improvements [MJ].
        energy_consumption_freight_electric_without_operations
            Energy consumption for freight transport using electricity without operational improvements [MJ].
        energy_consumption_freight_dropin_fuel
            Energy consumption for freight transport using drop-in fuels [MJ].
        energy_consumption_freight_hydrogen
            Energy consumption for freight transport using hydrogen [MJ].
        energy_consumption_freight_electric
            Energy consumption for freight transport using electricity [MJ].
        energy_consumption_dropin_fuel
            Total energy consumption using drop-in fuels [MJ].
        energy_consumption_hydrogen
            Total energy consumption using hydrogen [MJ].
        energy_consumption_electric
            Total energy consumption using electricity [MJ].
        energy_consumption
            Total energy consumption [MJ].
        dropin_fuel_mean_co2_emission_factor
            Mean CO2 emission factor for drop-in fuels [gCO2/MJ].
        hydrogen_mean_co2_emission_factor
            Mean CO2 emission factor for hydrogen [gCO2/MJ].
        electric_mean_co2_emission_factor
            Mean CO2 emission factor for electricity [gCO2/MJ].

        Returns
        -------
        energy_per_ask_mean_without_operations
            Energy consumption per ASK without operational improvements [MJ/ASK].
        energy_per_ask_mean
            Energy consumption per ASK [MJ/ASK].
        energy_per_rtk_mean_without_operations
            Energy consumption per RTK without operational improvements [MJ/RTK].
        energy_per_rtk_mean
            Energy consumption per RTK [MJ/RTK].
        co2_per_energy_mean
            CO2 emissions per unit of energy consumed [gCO2/MJ].
        """
        energy_per_ask_mean_without_operations = (
            +energy_consumption_passenger_dropin_fuel_without_operations
            + energy_consumption_passenger_hydrogen_without_operations
            + energy_consumption_passenger_electric_without_operations
        ) / ask

        energy_per_ask_mean = (
            +energy_consumption_passenger_dropin_fuel
            + energy_consumption_passenger_hydrogen
            + energy_consumption_passenger_electric
        ) / ask

        energy_per_rtk_mean_without_operations = (
            +energy_consumption_freight_dropin_fuel_without_operations
            + energy_consumption_freight_hydrogen_without_operations
            + energy_consumption_freight_electric_without_operations
        ) / rtk

        energy_per_rtk_mean = (
            +energy_consumption_freight_dropin_fuel
            + energy_consumption_freight_hydrogen
            + energy_consumption_freight_electric
        ) / rtk

        # TODO
        #  --> Better way than fillna to handle years where no energy is produced?

        co2_per_energy_mean = (
            +dropin_fuel_mean_co2_emission_factor.fillna(0) * energy_consumption_dropin_fuel
            + hydrogen_mean_co2_emission_factor.fillna(0) * energy_consumption_hydrogen
            + electric_mean_co2_emission_factor.fillna(0) * energy_consumption_electric
        ) / energy_consumption

        self.df.loc[:, "energy_per_ask_mean_without_operations"] = (
            energy_per_ask_mean_without_operations
        )
        self.df.loc[:, "energy_per_rtk_mean_without_operations"] = (
            energy_per_rtk_mean_without_operations
        )
        self.df.loc[:, "energy_per_ask_mean"] = energy_per_ask_mean
        self.df.loc[:, "energy_per_rtk_mean"] = energy_per_rtk_mean
        self.df.loc[:, "co2_per_energy_mean"] = co2_per_energy_mean

        return (
            energy_per_ask_mean_without_operations,
            energy_per_ask_mean,
            energy_per_rtk_mean_without_operations,
            energy_per_rtk_mean,
            co2_per_energy_mean,
        )


class CO2Emissions(AeroMAPSModel):
    """
    Class to compute CO2 emissions.

    Parameters
    --------------
    name : str
        Name of the model instance ('co2_emissions' by default).

    Documentation
    --------------
    Inputs
        - load_factor: Load factor [%].
        - rpk_<market>: Passenger RPK [RPK].
        - rtk_<market>: Freight RTK [RTK].
        - energy_per_ask_<market>_<energy>: Passenger MJ/ASK.
        - ask_<market>_<energy>_share: Passenger energy shares [%].
        - energy_per_rtk_<market>_<energy>: Freight MJ/RTK.
        - rtk_<market>_<energy>_share: Freight energy shares [%].
        - <energy>_mean_co2_emission_factor: Mean CO2 factor [gCO2/MJ].
    Outputs
        - co2_emissions_<market>: Per-market CO2 [MtCO2].
        - co2_emissions_passenger: Passenger total [MtCO2].
        - co2_emissions_freight: Freight total [MtCO2].
        - co2_emissions: Passenger + freight [MtCO2].
    Notes
        - <market> is the MarketManager id (passenger and freight markets).
        - <energy> is one of: dropin_fuel, hydrogen, electric.
        - I/O names are generated from configuration and passed to GEMSEO via
          self.input_names and self.output_names grammars.
    """

    def __init__(self, name="co2_emissions", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.climate_historical_data = None
        self.markets = None

    def custom_setup(self):
        """
        Dynamically build input_names and output_names based on the markets manager.
        Specific function for custom AeroMAPSModel instances.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]
        self.input_names = {
            "load_factor": pd.Series([0.0]),
        }
        self.output_names = {}

        # Per-passenger-market inputs and per-market output.
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            self.input_names[f"rpk_{mid}"] = pd.Series([0.0])
            for et in energy_types:
                self.input_names[f"energy_per_ask_{mid}_{et}"] = pd.Series([0.0])
                self.input_names[f"ask_{mid}_{et}_share"] = pd.Series([0.0])
            self.output_names[f"co2_emissions_{mid}"] = pd.Series([0.0])

        # Per-freight-market inputs and per-market output.
        for market in self.markets.get(traffic_type="freight"):
            mid = market.id
            self.input_names[f"rtk_{mid}"] = pd.Series([0.0])
            for et in energy_types:
                self.input_names[f"energy_per_rtk_{mid}_{et}"] = pd.Series([0.0])
                self.input_names[f"rtk_{mid}_{et}_share"] = pd.Series([0.0])
            self.output_names[f"co2_emissions_{mid}"] = pd.Series([0.0])

        # Mean CO2 emission factors (per energy type, global).
        for et in energy_types:
            self.input_names[f"{et}_mean_co2_emission_factor"] = pd.Series([0.0])

        # Aggregate outputs.
        self.output_names["co2_emissions_passenger"] = pd.Series([0.0])
        self.output_names["co2_emissions_freight"] = pd.Series([0.0])
        self.output_names["co2_emissions"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        CO2 emissions per market and aggregates.
        """
        energy_types = ["dropin_fuel", "hydrogen", "electric"]

        # Locally fill incomplete emission factors with zeros so that sums are not nan.
        co2_emission_factor_by_energy_type = {}
        for energy_type in energy_types:
            co2_emission_factor = input_data[f"{energy_type}_mean_co2_emission_factor"]
            co2_emission_factor.fillna(0, inplace=True)
            co2_emission_factor_by_energy_type[energy_type] = co2_emission_factor

        load_factor = input_data["load_factor"]
        output_data = {}

        # Per-passenger-market CO2 emissions.
        co2_emissions_passenger = None
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            rpk_market = input_data[f"rpk_{mid}"]
            co2_weighted_energy_intensity_sum = None
            for energy_type in energy_types:
                energy_per_ask = input_data[f"energy_per_ask_{mid}_{energy_type}"].fillna(0)
                ask_share = input_data[f"ask_{mid}_{energy_type}_share"]
                co2_weighted_energy_intensity = (
                    ask_share
                    / 100
                    * (energy_per_ask * co2_emission_factor_by_energy_type[energy_type])
                )
                co2_weighted_energy_intensity_sum = (
                    co2_weighted_energy_intensity
                    if co2_weighted_energy_intensity_sum is None
                    else co2_weighted_energy_intensity_sum + co2_weighted_energy_intensity
                )
            co2_emissions_market = (
                rpk_market / (load_factor / 100) * co2_weighted_energy_intensity_sum * 10 ** (-12)
            )
            output_data[f"co2_emissions_{mid}"] = co2_emissions_market
            co2_emissions_passenger = (
                co2_emissions_market
                if co2_emissions_passenger is None
                else co2_emissions_passenger + co2_emissions_market
            )

        # Per-freight-market CO2 emissions.
        co2_emissions_freight = None
        for market in self.markets.get(traffic_type="freight"):
            mid = market.id
            rtk_market = input_data[f"rtk_{mid}"]
            co2_weighted_energy_intensity_sum = None
            for energy_type in energy_types:
                energy_per_rtk = input_data[f"energy_per_rtk_{mid}_{energy_type}"].fillna(0)
                rtk_share = input_data[f"rtk_{mid}_{energy_type}_share"]
                co2_weighted_energy_intensity = (
                    rtk_share
                    / 100
                    * (energy_per_rtk * co2_emission_factor_by_energy_type[energy_type])
                )
                co2_weighted_energy_intensity_sum = (
                    co2_weighted_energy_intensity
                    if co2_weighted_energy_intensity_sum is None
                    else co2_weighted_energy_intensity_sum + co2_weighted_energy_intensity
                )
            co2_emissions_market = rtk_market * co2_weighted_energy_intensity_sum * 10 ** (-12)
            output_data[f"co2_emissions_{mid}"] = co2_emissions_market
            co2_emissions_freight = (
                co2_emissions_market
                if co2_emissions_freight is None
                else co2_emissions_freight + co2_emissions_market
            )

        # Defensive defaults if no markets.
        if co2_emissions_passenger is None:
            co2_emissions_passenger = pd.Series(0.0, index=self.df.index)
        if co2_emissions_freight is None:
            co2_emissions_freight = pd.Series(0.0, index=self.df.index)

        # Update climate DataFrame side-effect (matches legacy behaviour).
        historical_co2_emissions_for_temperature = self.climate_historical_data[:, 1]
        self.df_climate.loc[
            self.climate_historic_start_year : self.historic_start_year - 1, "co2_emissions"
        ] = historical_co2_emissions_for_temperature[
            : self.historic_start_year - self.climate_historic_start_year
        ]
        self.df_climate.loc[self.historic_start_year : self.end_year, "co2_emissions"] = (
            co2_emissions_passenger + co2_emissions_freight
        )

        co2_emissions_total = self.df_climate["co2_emissions"]

        output_data["co2_emissions_passenger"] = co2_emissions_passenger
        output_data["co2_emissions_freight"] = co2_emissions_freight
        output_data["co2_emissions"] = co2_emissions_total

        self._store_outputs(output_data, climate_outputs_keys=["co2_emissions"])
        return output_data


class CumulativeCO2Emissions(AeroMAPSModel):
    """
    Class to compute cumulative CO2 emissions.

    Parameters
    --------------
    name : str
        Name of the model instance ('cumulative_co2_emissions' by default).
    """

    def __init__(self, name="cumulative_co2_emissions", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions: pd.Series,
        carbon_budget_reference_year: int,
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Execute the computation of cumulative CO2 emissions.

        Parameters
        ----------
        co2_emissions
            Annual CO2 emissions [MtCO2].
        carbon_budget_reference_year
            Fixed reference year from which the budget-comparable cumulative is
            summed (default 2019), matching the aviation carbon budget framing.

        Returns
        -------
        cumulative_co2_emissions
            Cumulative CO2 emissions over the prospective window
            (prospection_start_year -> end_year) [GtCO2].
        cumulative_co2_emissions_from_carbon_budget_reference_year
            Cumulative CO2 emissions summed from carbon_budget_reference_year ->
            end_year [GtCO2]. Includes observed historic emissions from the
            reference year onward, so it is directly comparable to the aviation
            carbon budget regardless of prospection_start_year.

        """
        cumulative_co2_emissions = (
            co2_emissions.loc[self.prospection_start_year : self.end_year] / 1000
        ).cumsum()

        cumulative_co2_emissions_from_carbon_budget_reference_year = (
            co2_emissions.loc[carbon_budget_reference_year : self.end_year] / 1000
        ).cumsum()

        self.df["cumulative_co2_emissions"] = cumulative_co2_emissions
        self.df["cumulative_co2_emissions_from_carbon_budget_reference_year"] = (
            cumulative_co2_emissions_from_carbon_budget_reference_year
        )

        return (
            cumulative_co2_emissions,
            cumulative_co2_emissions_from_carbon_budget_reference_year,
        )


class DetailedCo2Emissions(AeroMAPSModel):
    """
    Class to compute detailed CO2 emissions breakdown.

    Parameters
    --------------
    name : str
        Name of the model instance ('detailed_co2_emissions' by default).
    """

    def __init__(self, name="detailed_co2_emissions", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk_reference: pd.Series,
        rtk_reference: pd.Series,
        rpk: pd.Series,
        rtk: pd.Series,
        load_factor: pd.Series,
        energy_per_ask_mean: pd.Series,
        energy_per_rtk_mean: pd.Series,
        energy_per_ask_mean_without_operations: pd.Series,
        energy_per_rtk_mean_without_operations: pd.Series,
        co2_per_energy_mean: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Execute the computation of detailed CO2 emissions breakdown.

        Parameters
        ----------
        rpk_reference
            Number of Revenue Passenger Kilometer (RPK) for all passenger air transport with a baseline air traffic growth [RPK].
        rtk_reference
            Number of Revenue Tonne Kilometer (RTK) for freight air transport with a baseline air traffic growth [RTK].
        rpk
            Revenue passenger kilometers (RPK) [RPK].
        rtk
            Revenue ton kilometers (RTK) [RTK].
        load_factor
            Load factor [%].
        energy_per_ask_mean
            Mean energy consumption per ASK for passenger market [MJ/ASK].
        energy_per_rtk_mean
            Mean energy consumption per RTK for freight market [MJ/RTK].
        energy_per_ask_mean_without_operations
            Mean energy consumption per ASK for passenger market without considering operation improvements [MJ/ASK].
        energy_per_rtk_mean_without_operations
            Mean energy consumption per RTK for freight market without considering operation improvements [MJ/RTK].
        co2_per_energy_mean
            Mean emission factor of aircraft energy [gCO2/MJ].


        Returns
        -------
        co2_emissions_last_historical_year_technology_baseline3
            CO2 emissions from all commercial air transport based on last-historical-year technological level with a baseline air traffic growth [MtCO2].
        co2_emissions_last_historical_year_technology
            CO2 emissions from all commercial air transport based on last-historical-year technological level [MtCO2].
        co2_emissions_including_aircraft_efficiency
            CO2 emissions from all commercial air transport including aircraft efficiency improvements [MtCO2].
        co2_emissions_including_operations
            CO2 emissions from all commercial air transport including aircraft efficiency and operation improvements [MtCO2].
        co2_emissions_including_load_factor
            CO2 emissions from all commercial air transport including aircraft efficiency, operation and load factor improvements [MtCO2].
        co2_emissions_including_energy
            CO2 emissions from all commercial air transport including aircraft efficiency, operation and load factor improvements and energy decarbonization [MtCO2].

        """
        years = range(self.prospection_start_year - 1, self.end_year + 1)

        # Speedup operations: access right portions of vectors
        rpk_reference_local = rpk_reference.loc[years]
        rtk_reference_local = rtk_reference.loc[years]
        rpk_local = rpk.loc[years]
        rtk_local = rtk.loc[years]
        load_factor_local = load_factor.loc[years]
        energy_per_ask_mean_local = energy_per_ask_mean.loc[years]
        energy_per_rtk_mean_local = energy_per_rtk_mean.loc[years]
        energy_per_ask_mean_without_operations_local = energy_per_ask_mean_without_operations.loc[
            years
        ]
        energy_per_rtk_mean_without_operations_local = energy_per_rtk_mean_without_operations.loc[
            years
        ]
        co2_per_energy_mean_local = co2_per_energy_mean.loc[years]

        # Start year values
        load_factor_start_year_local = load_factor.loc[self.prospection_start_year - 1]
        energy_per_ask_mean_start_year_local = energy_per_ask_mean.loc[
            self.prospection_start_year - 1
        ]
        energy_per_rtk_mean_start_year_local = energy_per_rtk_mean.loc[
            self.prospection_start_year - 1
        ]
        energy_per_ask_mean_without_operations_start_year_local = (
            energy_per_ask_mean_without_operations.loc[self.prospection_start_year - 1]
        )
        energy_per_rtk_mean_without_operations_start_year_local = (
            energy_per_rtk_mean_without_operations.loc[self.prospection_start_year - 1]
        )
        co2_per_energy_mean_start_year_local = co2_per_energy_mean.loc[
            self.prospection_start_year - 1
        ]

        co2_emissions_last_historical_year_technology_baseline3 = (
            rpk_reference_local
            * energy_per_ask_mean_without_operations_start_year_local
            * energy_per_ask_mean_start_year_local
            / energy_per_ask_mean_without_operations_start_year_local
            / (load_factor_start_year_local / 100)
            * co2_per_energy_mean_start_year_local
            * 10 ** (-12)
        ) + (
            rtk_reference_local
            * energy_per_rtk_mean_without_operations_start_year_local
            * energy_per_rtk_mean_start_year_local
            / energy_per_rtk_mean_without_operations_start_year_local
            * co2_per_energy_mean_start_year_local
            * 10 ** (-12)
        )

        co2_emissions_last_historical_year_technology = (
            rpk_local
            * energy_per_ask_mean_without_operations_start_year_local
            * energy_per_ask_mean_start_year_local
            / energy_per_ask_mean_without_operations_start_year_local
            / (load_factor_start_year_local / 100)
            * co2_per_energy_mean_start_year_local
            * 10 ** (-12)
        ) + (
            rtk_local
            * energy_per_rtk_mean_without_operations_start_year_local
            * energy_per_rtk_mean_start_year_local
            / energy_per_rtk_mean_without_operations_start_year_local
            * co2_per_energy_mean_start_year_local
            * 10 ** (-12)
        )

        co2_emissions_including_aircraft_efficiency = (
            rpk_local
            * energy_per_ask_mean_without_operations_local
            * energy_per_ask_mean_start_year_local
            / energy_per_ask_mean_without_operations_start_year_local
            / (load_factor_start_year_local / 100)
            * co2_per_energy_mean_start_year_local
            * 10 ** (-12)
        ) + (
            rtk_local
            * energy_per_rtk_mean_without_operations_local
            * energy_per_rtk_mean_start_year_local
            / energy_per_rtk_mean_without_operations_start_year_local
            * co2_per_energy_mean_start_year_local
            * 10 ** (-12)
        )

        co2_emissions_including_operations = (
            rpk_local
            * energy_per_ask_mean_without_operations_local
            * energy_per_ask_mean_local
            / energy_per_ask_mean_without_operations_local
            / (load_factor_start_year_local / 100)
            * co2_per_energy_mean_start_year_local
            * 10 ** (-12)
        ) + (
            rtk_local
            * energy_per_rtk_mean_without_operations_local
            * energy_per_rtk_mean_local
            / energy_per_rtk_mean_without_operations_local
            * co2_per_energy_mean_start_year_local
            * 10 ** (-12)
        )

        co2_emissions_including_load_factor = (
            rpk_local
            * energy_per_ask_mean_without_operations_local
            * energy_per_ask_mean_local
            / energy_per_ask_mean_without_operations_local
            / (load_factor_local / 100)
            * co2_per_energy_mean_start_year_local
            * 10 ** (-12)
        ) + (
            rtk_local
            * energy_per_rtk_mean_without_operations_local
            * energy_per_rtk_mean_local
            / energy_per_rtk_mean_without_operations_local
            * co2_per_energy_mean_start_year_local
            * 10 ** (-12)
        )

        co2_emissions_including_energy = (
            rpk_local
            * energy_per_ask_mean_without_operations_local
            * energy_per_ask_mean_local
            / energy_per_ask_mean_without_operations_local
            / (load_factor_local / 100)
            * co2_per_energy_mean_local
            * 10 ** (-12)
        ) + (
            rtk_local
            * energy_per_rtk_mean_without_operations_local
            * energy_per_rtk_mean_local
            / energy_per_rtk_mean_without_operations_local
            * co2_per_energy_mean_local
            * 10 ** (-12)
        )

        self.df.loc[years, "co2_emissions_last_historical_year_technology_baseline3"] = (
            co2_emissions_last_historical_year_technology_baseline3
        )
        self.df.loc[years, "co2_emissions_last_historical_year_technology"] = (
            co2_emissions_last_historical_year_technology
        )
        self.df.loc[years, "co2_emissions_including_aircraft_efficiency"] = (
            co2_emissions_including_aircraft_efficiency
        )
        self.df.loc[years, "co2_emissions_including_operations"] = (
            co2_emissions_including_operations
        )
        self.df.loc[years, "co2_emissions_including_load_factor"] = (
            co2_emissions_including_load_factor
        )
        self.df.loc[years, "co2_emissions_including_energy"] = co2_emissions_including_energy

        return (
            co2_emissions_last_historical_year_technology_baseline3,
            co2_emissions_last_historical_year_technology,
            co2_emissions_including_aircraft_efficiency,
            co2_emissions_including_operations,
            co2_emissions_including_load_factor,
            co2_emissions_including_energy,
        )


class DetailedCumulativeCO2Emissions(AeroMAPSModel):
    """
    Class to compute detailed cumulative CO2 emissions breakdown.

    Parameters
    --------------
    name : str
        Name of the model instance ('detailed_cumulative_co2_emissions' by default).
    """

    def __init__(self, name="detailed_cumulative_co2_emissions", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions_last_historical_year_technology_baseline3: pd.Series,
        co2_emissions_last_historical_year_technology: pd.Series,
        co2_emissions_including_aircraft_efficiency: pd.Series,
        co2_emissions_including_operations: pd.Series,
        co2_emissions_including_load_factor: pd.Series,
        co2_emissions_including_energy: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Execute the computation of detailed cumulative CO2 emissions breakdown.
        Parameters
        ----------
        co2_emissions_last_historical_year_technology_baseline3
            CO2 emissions from all commercial air transport based on last-historical-year technological level with a baseline air traffic growth [MtCO2].
        co2_emissions_last_historical_year_technology
            CO2 emissions from all commercial air transport based on last-historical-year technological level [MtCO2].
        co2_emissions_including_aircraft_efficiency
            CO2 emissions from all commercial air transport including aircraft efficiency improvements [MtCO2].
        co2_emissions_including_operations
            CO2 emissions from all commercial air transport including aircraft efficiency and operations improvements [MtCO2].
        co2_emissions_including_load_factor
            CO2 emissions from all commercial air transport including aircraft efficiency, operation and load factor improvements [MtCO2].
        co2_emissions_including_energy
            CO2 emissions from all commercial air transport including aircraft efficiency, operation and load factor improvements and energy decarbonization [MtCO2].

        Returns
        -------
        cumulative_co2_emissions_last_historical_year_technology_baseline3
            Cumulative CO2 emissions from all commercial air transport based on last-historical-year technological level with a baseline air traffic growth [GtCO2].
        cumulative_co2_emissions_last_historical_year_technology
            Cumulative CO2 emissions from all commercial air transport based on last-historical-year technological level [GtCO2].
        cumulative_co2_emissions_including_aircraft_efficiency
            Cumulative CO2 emissions from all commercial air transport including aircraft efficiency improvements [GtCO2].
        cumulative_co2_emissions_including_operations
            Cumulative CO2 emissions from all commercial air transport including aircraft efficiency and operations improvements [GtCO2].
        cumulative_co2_emissions_including_load_factor
            Cumulative CO2 emissions from all commercial air transport including aircraft efficiency, operation and load factor
            improvements [GtCO2].
        cumulative_co2_emissions_including_energy
            Cumulative CO2 emissions from all commercial air transport including aircraft efficiency, operation and load factor
            improvements and energy decarbonization [GtCO2].

        """
        cumulative_co2_emissions_last_historical_year_technology_baseline3 = (
            co2_emissions_last_historical_year_technology_baseline3.loc[
                self.prospection_start_year : self.end_year
            ]
            / 1000
        ).cumsum()

        cumulative_co2_emissions_last_historical_year_technology = (
            co2_emissions_last_historical_year_technology.loc[
                self.prospection_start_year : self.end_year
            ]
            / 1000
        ).cumsum()

        cumulative_co2_emissions_including_aircraft_efficiency = (
            co2_emissions_including_aircraft_efficiency.loc[
                self.prospection_start_year : self.end_year
            ]
            / 1000
        ).cumsum()

        cumulative_co2_emissions_including_operations = (
            co2_emissions_including_operations.loc[self.prospection_start_year : self.end_year]
            / 1000
        ).cumsum()

        cumulative_co2_emissions_including_load_factor = (
            co2_emissions_including_load_factor.loc[self.prospection_start_year : self.end_year]
            / 1000
        ).cumsum()

        cumulative_co2_emissions_including_energy = (
            co2_emissions_including_energy.loc[self.prospection_start_year : self.end_year] / 1000
        ).cumsum()

        self.df["cumulative_co2_emissions_last_historical_year_technology_baseline3"] = (
            cumulative_co2_emissions_last_historical_year_technology_baseline3
        )
        self.df["cumulative_co2_emissions_last_historical_year_technology"] = (
            cumulative_co2_emissions_last_historical_year_technology
        )
        self.df["cumulative_co2_emissions_including_aircraft_efficiency"] = (
            cumulative_co2_emissions_including_aircraft_efficiency
        )
        self.df["cumulative_co2_emissions_including_operations"] = (
            cumulative_co2_emissions_including_operations
        )
        self.df["cumulative_co2_emissions_including_load_factor"] = (
            cumulative_co2_emissions_including_load_factor
        )
        self.df["cumulative_co2_emissions_including_energy"] = (
            cumulative_co2_emissions_including_energy
        )

        return (
            cumulative_co2_emissions_last_historical_year_technology_baseline3,
            cumulative_co2_emissions_last_historical_year_technology,
            cumulative_co2_emissions_including_aircraft_efficiency,
            cumulative_co2_emissions_including_operations,
            cumulative_co2_emissions_including_load_factor,
            cumulative_co2_emissions_including_energy,
        )


class DetailedCo2EmissionsPerPathway(AeroMAPSModel):
    """
    Class to decompose the "aircraft energy" lever of action into sub-levers,
    one per energy pathway (e.g. each biofuel or electrofuel pathway).

    For each pathway, the annual CO2 emissions reduction is computed as the energy
    consumption of the pathway multiplied by the difference between the reference
    (start year) mean CO2 emission factor and the pathway emission factor. By
    construction, the sum of the pathway contributions and of the residual term
    equals the difference between co2_emissions_including_load_factor and
    co2_emissions_including_energy computed by DetailedCo2Emissions.

    Parameters
    --------------
    name : str
        Name of the model instance ('detailed_co2_emissions_per_pathway' by default).

    Attributes
    ----------
    pathways_manager : EnergyCarrierManager
        Instance of the EnergyCarrierManager containing all defined energy pathways.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.
    """

    def __init__(self, name="detailed_co2_emissions_per_pathway", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
        """
        Sets up input and output names for the model based on the pathways in the pathways_manager.

        Returns
        -------
        None
        """
        self.input_names = {
            "co2_emissions_including_load_factor": pd.Series([0.0]),
            "co2_emissions_including_energy": pd.Series([0.0]),
            "co2_per_energy_mean": pd.Series([0.0]),
        }
        self.output_names = {
            "co2_emissions_lever_energy_other": pd.Series([0.0]),
        }

        for pathway in self.pathways_manager.get_all():
            self.input_names.update(
                {
                    f"{pathway.name}_energy_consumption": pd.Series([0.0]),
                    f"{pathway.name}_mean_co2_emission_factor": pd.Series([0.0]),
                }
            )
            self.output_names.update(
                {
                    f"co2_emissions_lever_energy_{pathway.name}": pd.Series([0.0]),
                }
            )

    def compute(self, input_data) -> dict:
        """
        Execute the decomposition of the energy lever of action per energy pathway.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing, for each pathway, the annual CO2 emissions avoided
            thanks to the pathway [MtCO2], plus a residual term so that the sum of all
            contributions equals the total energy lever of action.
        """
        output_data = {}

        reference_year = self.prospection_start_year - 1
        years = range(reference_year, self.end_year + 1)

        co2_emission_factor_reference = input_data["co2_per_energy_mean"].loc[reference_year]

        total_lever = (
            input_data["co2_emissions_including_load_factor"]
            - input_data["co2_emissions_including_energy"]
        ).loc[years]

        cumulated_contributions = pd.Series(0.0, index=total_lever.index)

        for pathway in self.pathways_manager.get_all():
            pathway_energy_consumption = input_data[f"{pathway.name}_energy_consumption"]
            pathway_co2_emission_factor = input_data[f"{pathway.name}_mean_co2_emission_factor"]

            pathway_contribution = (
                pathway_energy_consumption
                * (co2_emission_factor_reference - pathway_co2_emission_factor)
            ).fillna(0) * 10 ** (-12)
            pathway_contribution = pathway_contribution.reindex(total_lever.index).fillna(0.0)

            cumulated_contributions += pathway_contribution

            contribution = get_default_series(
                self.historic_start_year, self.end_year, fill_value=float("nan")
            )
            contribution.loc[years] = pathway_contribution
            output_data[f"co2_emissions_lever_energy_{pathway.name}"] = contribution

        other = get_default_series(self.historic_start_year, self.end_year, fill_value=float("nan"))
        other.loc[years] = total_lever.fillna(0) - cumulated_contributions
        output_data["co2_emissions_lever_energy_other"] = other

        self._store_outputs(output_data)

        return output_data


class DetailedCo2EmissionsPerAircraft(AeroMAPSModel):
    """
    Class to decompose the "aircraft efficiency" lever of action into sub-levers:
    fleet renewal with reference (already existing) aircraft, introduction of each
    new aircraft of the fleet, freight fleet efficiency, and a residual term
    (mainly traffic mix effects between markets).

    The decomposition builds on the per-aircraft energy efficiency contributions
    computed by the fleet model (see FleetPerformanceMixin), which quantify how much
    each aircraft shifts the market mean energy consumption per ASK with respect to
    the recent reference aircraft. The evolution of these contributions with respect
    to the reference (start) year is converted into avoided CO2 emissions using the
    same factors as DetailedCo2Emissions. By construction, the sum of all sub-lever
    contributions equals the difference between co2_emissions_last_historical_year_technology and
    co2_emissions_including_aircraft_efficiency.

    With this convention, the "fleet renewal" sub-lever measures the gain from
    replacing old reference aircraft by recent reference aircraft, and each new
    aircraft is only credited for its additional gain beyond fleet renewal.

    This model requires the bottom-up fleet model.

    Parameters
    --------------
    name : str
        Name of the model instance ('detailed_co2_emissions_per_aircraft' by default).

    Attributes
    ----------
    fleet_model : FleetModel
        FleetModel instance containing the fleet structure and computed aircraft
        shares and efficiency contributions.
    markets : MarketManager
        MarketManager instance used to map fleet categories to the markets they serve.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.
    """

    def __init__(self, name="detailed_co2_emissions_per_aircraft", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.fleet_model = None
        self.markets = None
        self.aircraft_lever_names = {}

    def custom_setup(self):
        """
        Sets up input and output names for the model based on the fleet structure.

        Returns
        -------
        None
        """
        if self.fleet_model is None:
            raise RuntimeError(
                f"Model '{self.name}' requires the bottom-up fleet model. "
                "Add 'models.fleet' to your configuration."
            )

        self.input_names = {
            "ask": pd.Series([0.0]),
            "rpk": pd.Series([0.0]),
            "rtk": pd.Series([0.0]),
            "load_factor": pd.Series([0.0]),
            "energy_per_ask_mean": pd.Series([0.0]),
            "energy_per_ask_mean_without_operations": pd.Series([0.0]),
            "energy_per_rtk_mean": pd.Series([0.0]),
            "energy_per_rtk_mean_without_operations": pd.Series([0.0]),
            "co2_per_energy_mean": pd.Series([0.0]),
            "co2_emissions_last_historical_year_technology": pd.Series([0.0]),
            "co2_emissions_including_aircraft_efficiency": pd.Series([0.0]),
        }
        self.output_names = {
            "co2_emissions_lever_efficiency_fleet_renewal": pd.Series([0.0]),
            "co2_emissions_lever_efficiency_freight": pd.Series([0.0]),
            "co2_emissions_lever_efficiency_other": pd.Series([0.0]),
        }

        # ASK of the market served by each category, for weighting the contributions
        for category in self.fleet_model.fleet.categories.values():
            self.input_names[f"ask_{category.market_id}"] = pd.Series([0.0])

        # Map each aircraft of the fleet to a unique output variable name
        self.aircraft_lever_names = aircraft_efficiency_lever_names(self.fleet_model.fleet)
        for lever_name in self.aircraft_lever_names.values():
            self.output_names[lever_name] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        Execute the decomposition of the aircraft efficiency lever of action per aircraft.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing, for each sub-lever (fleet renewal, each new aircraft,
            freight, residual), the annual CO2 emissions avoided [MtCO2].
        """
        output_data = {}

        reference_year = self.prospection_start_year - 1
        years = range(reference_year, self.end_year + 1)

        fleet_df = self.fleet_model.df

        load_factor_reference = input_data["load_factor"].loc[reference_year]
        energy_per_ask_mean_reference = input_data["energy_per_ask_mean"].loc[reference_year]
        energy_per_ask_mean_without_operations_reference = input_data[
            "energy_per_ask_mean_without_operations"
        ].loc[reference_year]
        energy_per_rtk_mean_reference = input_data["energy_per_rtk_mean"].loc[reference_year]
        energy_per_rtk_mean_without_operations_reference = input_data[
            "energy_per_rtk_mean_without_operations"
        ].loc[reference_year]
        co2_emission_factor_reference = input_data["co2_per_energy_mean"].loc[reference_year]

        ask = input_data["ask"].loc[years]
        rpk = input_data["rpk"].loc[years]
        rtk = input_data["rtk"].loc[years]

        # Common factor of the passenger part of the aircraft efficiency lever
        # (see DetailedCo2Emissions for the corresponding formulas)
        passenger_factor = (
            rpk
            * (energy_per_ask_mean_reference / energy_per_ask_mean_without_operations_reference)
            / (load_factor_reference / 100)
            * co2_emission_factor_reference
            * 10 ** (-12)
        )

        fleet_renewal = pd.Series(0.0, index=pd.Index(years))
        cumulated_contributions = pd.Series(0.0, index=pd.Index(years))

        def co2_contribution(category_ask_share, contribution_column):
            """Convert a fleet energy efficiency contribution [MJ/ASK] into avoided CO2 [MtCO2]."""
            contribution = fleet_df.loc[years, contribution_column]
            contribution_reference = fleet_df.loc[reference_year, contribution_column]
            return passenger_factor * category_ask_share * (contribution - contribution_reference)

        for category in self.fleet_model.fleet.categories.values():
            category_ask_share = input_data[f"ask_{category.market_id}"].loc[years] / ask

            # Fleet renewal: replacement of the old reference aircraft by the recent one
            first_subcategory = category.subcategories[0]
            for reference in ("old_reference", "recent_reference"):
                contribution = co2_contribution(
                    category_ask_share,
                    f"{category.name}:{first_subcategory.name}:{reference}:energy_efficiency_contribution",
                )
                fleet_renewal += contribution
                cumulated_contributions += contribution

            # New aircraft: additional gain beyond fleet renewal
            for subcategory in category.subcategories.values():
                for aircraft in subcategory.aircraft.values():
                    lever_name = self.aircraft_lever_names[
                        (category.name, subcategory.name, aircraft.name)
                    ]
                    contribution = co2_contribution(
                        category_ask_share,
                        f"{category.name}:{subcategory.name}:{aircraft.name}:energy_efficiency_contribution",
                    )
                    cumulated_contributions += contribution
                    series = get_default_series(
                        self.historic_start_year, self.end_year, fill_value=float("nan")
                    )
                    series.loc[years] = contribution
                    output_data[lever_name] = series

        # Freight part of the aircraft efficiency lever
        freight = (
            rtk
            * (
                energy_per_rtk_mean_without_operations_reference
                - input_data["energy_per_rtk_mean_without_operations"].loc[years]
            )
            * (energy_per_rtk_mean_reference / energy_per_rtk_mean_without_operations_reference)
            * co2_emission_factor_reference
            * 10 ** (-12)
        )
        cumulated_contributions += freight

        # Residual term (mainly traffic mix effects between markets) so that the
        # sum of all sub-levers equals the total aircraft efficiency lever
        total_lever = (
            input_data["co2_emissions_last_historical_year_technology"]
            - input_data["co2_emissions_including_aircraft_efficiency"]
        ).loc[years]
        other = total_lever.fillna(0) - cumulated_contributions

        for name, values in [
            ("co2_emissions_lever_efficiency_fleet_renewal", fleet_renewal),
            ("co2_emissions_lever_efficiency_freight", freight),
            ("co2_emissions_lever_efficiency_other", other),
        ]:
            series = get_default_series(
                self.historic_start_year, self.end_year, fill_value=float("nan")
            )
            series.loc[years] = values
            output_data[name] = series

        self._store_outputs(output_data)

        return output_data


class DetailedCo2EmissionsPerMarket(AeroMAPSModel):
    """
    Class to decompose every lever of action of the CO2 emissions cascade by
    market (each passenger market and each freight market).

    The global CO2 emissions cascade computed by DetailedCo2Emissions goes, for
    a given year, through five successive emission levels::

        last-historical-year technology
          -> including aircraft efficiency
          -> including operations
          -> including load factor
          -> including energy (actual emissions)

    and defines four levers of action as the differences between consecutive
    levels. This model recomputes the same cascade *per market*, using the
    per-market traffic (``rpk_<market>`` / ``rtk_<market>``) and the per-market,
    per-energy-type physical intensities (``energy_per_ask_<market>_<energy>``
    and their ``without_operations`` counterparts). Each lever therefore gets a
    per-market contribution answering "how much of this lever is attributable to
    the short/medium/long-range (or freight) market?".

    Because the global cascade uses fleet-wide mean intensities and a fleet-wide
    load factor while the per-market cascade uses market-resolved quantities, the
    sum of the per-market contributions does not exactly reproduce the global
    lever: the difference is a genuine cross-market traffic-mix term. It is
    emitted as a ``..._market_cross_mix`` residual for each lever, so that by
    construction::

        sum_over_markets(lever_market) + lever_market_cross_mix == global lever

    The energy lever additionally uses the per-market, per-energy-type CO2
    emission factors (exactly as :class:`CO2Emissions`), so the per-market energy
    lever captures market-specific fuel-mix decarbonisation.

    This model requires the bottom-up fleet model and the generic energy models
    (which produce the per-market intensities); it is registered next to
    DetailedCo2EmissionsPerAircraft in the bottom-up efficiency group.

    Parameters
    --------------
    name : str
        Name of the model instance ('detailed_co2_emissions_per_market' by default).

    Attributes
    ----------
    markets : MarketManager
        MarketManager instance enumerating the passenger and freight markets.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.
    """

    ENERGY_TYPES = ("dropin_fuel", "hydrogen", "electric")

    def __init__(self, name="detailed_co2_emissions_per_market", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        """
        Sets up input and output names for the model based on the markets manager.

        Returns
        -------
        None
        """
        self.input_names = {
            "load_factor": pd.Series([0.0]),
            "co2_per_energy_mean": pd.Series([0.0]),
            "co2_emissions_last_historical_year_technology": pd.Series([0.0]),
            "co2_emissions_including_aircraft_efficiency": pd.Series([0.0]),
            "co2_emissions_including_operations": pd.Series([0.0]),
            "co2_emissions_including_load_factor": pd.Series([0.0]),
            "co2_emissions_including_energy": pd.Series([0.0]),
        }
        for energy_type in self.ENERGY_TYPES:
            self.input_names[f"{energy_type}_mean_co2_emission_factor"] = pd.Series([0.0])

        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            self.input_names[f"rpk_{mid}"] = pd.Series([0.0])
            for energy_type in self.ENERGY_TYPES:
                self.input_names[f"ask_{mid}_{energy_type}_share"] = pd.Series([0.0])
                self.input_names[f"energy_per_ask_{mid}_{energy_type}"] = pd.Series([0.0])
                self.input_names[f"energy_per_ask_without_operations_{mid}_{energy_type}"] = (
                    pd.Series([0.0])
                )

        for market in self.markets.get(traffic_type="freight"):
            mid = market.id
            self.input_names[f"rtk_{mid}"] = pd.Series([0.0])
            for energy_type in self.ENERGY_TYPES:
                self.input_names[f"rtk_{mid}_{energy_type}_share"] = pd.Series([0.0])
                self.input_names[f"energy_per_rtk_{mid}_{energy_type}"] = pd.Series([0.0])
                self.input_names[f"energy_per_rtk_without_operations_{mid}_{energy_type}"] = (
                    pd.Series([0.0])
                )

        # Output columns come from the shared naming helper (single source of truth).
        self.output_names = {
            column: pd.Series([0.0]) for column in market_lever_names(self.markets).values()
        }

    def compute(self, input_data) -> dict:
        """
        Execute the per-market decomposition of the CO2 emissions levers.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing, for each market and each lever (efficiency,
            operations, load factor, energy), the annual CO2 emissions avoided
            [MtCO2], plus a cross-market-mix residual per lever.
        """
        output_data = {}

        reference_year = self.prospection_start_year - 1
        years = pd.Index(range(reference_year, self.end_year + 1))

        load_factor = input_data["load_factor"].loc[years]
        load_factor_reference = input_data["load_factor"].loc[reference_year]
        co2_emission_factor_reference = input_data["co2_per_energy_mean"].loc[reference_year]

        co2_factor = {
            energy_type: input_data[f"{energy_type}_mean_co2_emission_factor"].fillna(0).loc[years]
            for energy_type in self.ENERGY_TYPES
        }

        def emit(name, series):
            out = get_default_series(
                self.historic_start_year, self.end_year, fill_value=float("nan")
            )
            out.loc[years] = series
            output_data[name] = out

        # Per-lever accumulators of the market contributions (to derive the
        # cross-market-mix residual against the global levers).
        lever_sum = {lever: pd.Series(0.0, index=years) for lever in MARKET_LEVERS_PASSENGER}

        def weighted_intensity(prefix, share_prefix, mid):
            """Traffic-weighted market mean of a per-energy-type intensity [MJ/ASK or MJ/RTK]."""
            total = pd.Series(0.0, index=years)
            for energy_type in self.ENERGY_TYPES:
                share = input_data[f"{share_prefix}_{mid}_{energy_type}_share"].loc[years] / 100
                intensity = input_data[f"{prefix}_{mid}_{energy_type}"].fillna(0).loc[years]
                total = total + share * intensity
            return total

        def co2_weighted_intensity(prefix, share_prefix, mid):
            """Traffic-weighted market mean of intensity x CO2 factor [gCO2/ASK or /RTK]."""
            total = pd.Series(0.0, index=years)
            for energy_type in self.ENERGY_TYPES:
                share = input_data[f"{share_prefix}_{mid}_{energy_type}_share"].loc[years] / 100
                intensity = input_data[f"{prefix}_{mid}_{energy_type}"].fillna(0).loc[years]
                total = total + share * intensity * co2_factor[energy_type]
            return total

        # --- Passenger markets ---
        for market in self.markets.get(traffic_type="passenger"):
            mid = market.id
            rpk = input_data[f"rpk_{mid}"].loc[years]

            energy_per_ask = weighted_intensity("energy_per_ask", "ask", mid)
            energy_per_ask_without_operations = weighted_intensity(
                "energy_per_ask_without_operations", "ask", mid
            )
            co2_per_ask = co2_weighted_intensity("energy_per_ask", "ask", mid)

            energy_per_ask_reference = energy_per_ask.loc[reference_year]
            energy_per_ask_without_operations_reference = energy_per_ask_without_operations.loc[
                reference_year
            ]

            # Emission levels of the cascade for this market [MtCO2].
            level_last_historical_year = (
                rpk
                * energy_per_ask_reference
                / (load_factor_reference / 100)
                * co2_emission_factor_reference
                * 10 ** (-12)
            )
            level_efficiency = (
                rpk
                * energy_per_ask_without_operations
                * (energy_per_ask_reference / energy_per_ask_without_operations_reference)
                / (load_factor_reference / 100)
                * co2_emission_factor_reference
                * 10 ** (-12)
            )
            level_operations = (
                rpk
                * energy_per_ask
                / (load_factor_reference / 100)
                * co2_emission_factor_reference
                * 10 ** (-12)
            )
            level_load_factor = (
                rpk
                * energy_per_ask
                / (load_factor / 100)
                * co2_emission_factor_reference
                * 10 ** (-12)
            )
            level_energy = rpk / (load_factor / 100) * co2_per_ask * 10 ** (-12)

            levers = {
                "efficiency": level_last_historical_year - level_efficiency,
                "operations": level_efficiency - level_operations,
                "loadfactor": level_operations - level_load_factor,
                "energy": level_load_factor - level_energy,
            }
            for lever, values in levers.items():
                emit(market_lever_column(lever, mid), values)
                lever_sum[lever] = lever_sum[lever] + values

        # --- Freight markets (no passenger load factor lever) ---
        for market in self.markets.get(traffic_type="freight"):
            mid = market.id
            rtk = input_data[f"rtk_{mid}"].loc[years]

            energy_per_rtk = weighted_intensity("energy_per_rtk", "rtk", mid)
            energy_per_rtk_without_operations = weighted_intensity(
                "energy_per_rtk_without_operations", "rtk", mid
            )
            co2_per_rtk = co2_weighted_intensity("energy_per_rtk", "rtk", mid)

            energy_per_rtk_reference = energy_per_rtk.loc[reference_year]
            energy_per_rtk_without_operations_reference = energy_per_rtk_without_operations.loc[
                reference_year
            ]

            level_last_historical_year = (
                rtk * energy_per_rtk_reference * co2_emission_factor_reference * 10 ** (-12)
            )
            level_efficiency = (
                rtk
                * energy_per_rtk_without_operations
                * (energy_per_rtk_reference / energy_per_rtk_without_operations_reference)
                * co2_emission_factor_reference
                * 10 ** (-12)
            )
            level_operations = rtk * energy_per_rtk * co2_emission_factor_reference * 10 ** (-12)
            level_energy = rtk * co2_per_rtk * 10 ** (-12)

            levers = {
                "efficiency": level_last_historical_year - level_efficiency,
                "operations": level_efficiency - level_operations,
                "energy": level_operations - level_energy,
            }
            for lever, values in levers.items():
                emit(market_lever_column(lever, mid), values)
                lever_sum[lever] = lever_sum[lever] + values

        # --- Cross-market-mix residual per lever ---
        # Global levers from the DetailedCo2Emissions cascade.
        global_levers = {
            "efficiency": input_data["co2_emissions_last_historical_year_technology"]
            - input_data["co2_emissions_including_aircraft_efficiency"],
            "operations": input_data["co2_emissions_including_aircraft_efficiency"]
            - input_data["co2_emissions_including_operations"],
            "loadfactor": input_data["co2_emissions_including_operations"]
            - input_data["co2_emissions_including_load_factor"],
            "energy": input_data["co2_emissions_including_load_factor"]
            - input_data["co2_emissions_including_energy"],
        }
        for lever, global_lever in global_levers.items():
            residual = global_lever.loc[years].fillna(0) - lever_sum[lever]
            emit(market_lever_column(lever, MARKET_CROSS_MIX), residual)

        self._store_outputs(output_data)

        return output_data


class SimpleCO2Emissions(AeroMAPSModel):
    """
    Class to compute simple CO2 emissions.

    Parameters
    --------------
    name : str
        Name of the model instance ('simple_co2_emissions' by default).
    """

    def __init__(self, name="simple_co2_emissions", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.climate_historical_data = None

    def compute(
        self,
        energy_consumption_init: pd.Series,
        dropin_fuel_mean_co2_emission_factor: pd.Series,
        hydrogen_mean_co2_emission_factor: pd.Series,
        electric_mean_co2_emission_factor: pd.Series,
        energy_consumption_dropin_fuel: pd.Series,
        energy_consumption_hydrogen: pd.Series,
        energy_consumption_electricity: pd.Series,
    ) -> pd.Series:
        """
        Simple CO2 emissions calculation

        Parameters
        ----------
        energy_consumption_init
            Historical energy consumption of aviation over 2000-2019 [MJ].
        dropin_fuel_mean_co2_emission_factor
            Mean CO2 emission factor for drop-in fuels [gCO2/MJ].
        hydrogen_mean_co2_emission_factor
            Mean CO2 emission factor for hydrogen [gCO2/MJ].
        electric_mean_co2_emission_factor
            Mean CO2 emission factor for electric aviation [gCO2/MJ].
        energy_consumption_dropin_fuel
            Energy consumption in the form of drop-in fuels from all commercial air transport [MJ].
        energy_consumption_hydrogen
            Energy consumption in the form of hydrogen from all commercial air transport [MJ].
        energy_consumption_electricity
            Energy consumption in the form of electricity from all commercial air transport [MJ].

        Returns
        -------
        co2_emissions
            CO2 emissions from all commercial air transport [MtCO2].
        """

        ## Initialization
        historical_co2_emissions_for_temperature = self.climate_historical_data[:, 1]

        # Calculation
        for k in range(self.climate_historic_start_year, self.historic_start_year):
            self.df_climate.loc[k, "co2_emissions"] = historical_co2_emissions_for_temperature[
                k - self.climate_historic_start_year
            ]

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df_climate.loc[k, "co2_emissions"] = (
                dropin_fuel_mean_co2_emission_factor.loc[k]
                / 10**12
                * energy_consumption_init.loc[k]
            )

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df_climate.loc[k, "co2_emissions"] = (
                dropin_fuel_mean_co2_emission_factor.loc[k]
                / 10**12
                * energy_consumption_dropin_fuel.loc[k]
                + electric_mean_co2_emission_factor.loc[k]
                / 10**12
                * energy_consumption_electricity.loc[k]
                + hydrogen_mean_co2_emission_factor.loc[k]
                / 10**12
                * energy_consumption_hydrogen.loc[k]
            )

        co2_emissions = self.df_climate.loc[:, "co2_emissions"]

        return co2_emissions

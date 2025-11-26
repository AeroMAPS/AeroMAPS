"""
co2_emissions
===========
This module contains models for calculating CO2 emissions and related factors.
"""

from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


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
    """

    def __init__(self, name="co2_emissions", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.climate_historical_data = None

    def compute(
        self,
        rpk_short_range: pd.Series,
        rpk_medium_range: pd.Series,
        rpk_long_range: pd.Series,
        rtk: pd.Series,
        load_factor: pd.Series,
        energy_per_ask_short_range_dropin_fuel: pd.Series,
        energy_per_ask_medium_range_dropin_fuel: pd.Series,
        energy_per_ask_long_range_dropin_fuel: pd.Series,
        energy_per_rtk_freight_dropin_fuel: pd.Series,
        energy_per_ask_short_range_hydrogen: pd.Series,
        energy_per_ask_medium_range_hydrogen: pd.Series,
        energy_per_ask_long_range_hydrogen: pd.Series,
        energy_per_rtk_freight_hydrogen: pd.Series,
        energy_per_ask_short_range_electric: pd.Series,
        energy_per_ask_medium_range_electric: pd.Series,
        energy_per_ask_long_range_electric: pd.Series,
        energy_per_rtk_freight_electric: pd.Series,
        ask_short_range_dropin_fuel_share: pd.Series,
        ask_medium_range_dropin_fuel_share: pd.Series,
        ask_long_range_dropin_fuel_share: pd.Series,
        rtk_dropin_fuel_share: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_long_range_hydrogen_share: pd.Series,
        rtk_hydrogen_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        rtk_electric_share: pd.Series,
        dropin_fuel_mean_co2_emission_factor: pd.Series,
        hydrogen_mean_co2_emission_factor: pd.Series,
        electric_mean_co2_emission_factor: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        CO2 emissions calculation.

        Parameters
        ----------
        rpk_short_range
            Revenue passenger kilometers for short-range flights [RPK].
        rpk_medium_range
            Revenue passenger kilometers for medium-range flights [RPK].
        rpk_long_range
            Revenue passenger kilometers for long-range flights [RPK].
        rtk
            Revenue ton kilometers [RTK].
        load_factor
            Load factor [%].
        energy_per_ask_short_range_dropin_fuel
            Energy consumption per ASK for short-range flights using drop-in fuels [MJ/ASK].
        energy_per_ask_medium_range_dropin_fuel
            Energy consumption per ASK for medium-range flights using drop-in fuels [MJ/ASK].
        energy_per_ask_long_range_dropin_fuel
            Energy consumption per ASK for long-range flights using drop-in fuels [MJ/ASK].
        energy_per_rtk_freight_dropin_fuel
            Energy consumption per RTK for freight using drop-in fuels [MJ/RTK].
        energy_per_ask_short_range_hydrogen
            Energy consumption per ASK for short-range flights using hydrogen [MJ/ASK].
        energy_per_ask_medium_range_hydrogen
            Energy consumption per ASK for medium-range flights using hydrogen [MJ/ASK].
        energy_per_ask_long_range_hydrogen
            Energy consumption per ASK for long-range flights using hydrogen [MJ/ASK].
        energy_per_rtk_freight_hydrogen
            Energy consumption per RTK for freight using hydrogen [MJ/RTK].
        energy_per_ask_short_range_electric
            Energy consumption per ASK for short-range flights using electricity [MJ/ASK].
        energy_per_ask_medium_range_electric
            Energy consumption per ASK for medium-range flights using electricity [MJ/ASK].
        energy_per_ask_long_range_electric
            Energy consumption per ASK for long-range flights using electricity [MJ/ASK].
        energy_per_rtk_freight_electric
            Energy consumption per RTK for freight using electricity [MJ/RTK].
        ask_short_range_dropin_fuel_share
            Share of drop-in fuels in ASK for short-range flights [%].
        ask_medium_range_dropin_fuel_share
            Share of drop-in fuels in ASK for medium-range flights [%].
        ask_long_range_dropin_fuel_share
            Share of drop-in fuels in ASK for long-range flights [%].
        rtk_dropin_fuel_share
            Share of drop-in fuels in RTK for freight [%].
        ask_short_range_hydrogen_share
            Share of hydrogen in ASK for short-range flights [%].
        ask_medium_range_hydrogen_share
            Share of hydrogen in ASK for medium-range flights [%].
        ask_long_range_hydrogen_share
            Share of hydrogen in ASK for long-range flights [%].
        rtk_hydrogen_share
            Share of hydrogen in RTK for freight [%].
        ask_short_range_electric_share
            Share of electricity in ASK for short-range flights [%].
        ask_medium_range_electric_share
            Share of electricity in ASK for medium-range flights [%].
        ask_long_range_electric_share
            Share of electricity in ASK for long-range flights [%].
        rtk_electric_share
            Share of electricity in RTK for freight [%].
        dropin_fuel_mean_co2_emission_factor
            Mean CO2 emission factor for drop-in fuels [gCO2/MJ].
        hydrogen_mean_co2_emission_factor
            Mean CO2 emission factor for hydrogen [gCO2/MJ].
        electric_mean_co2_emission_factor
            Mean CO2 emission factor for electricity [gCO2/MJ].

        Returns
        -------
        co2_emissions_short_range
            CO2 emissions from short-range flights [MtCO2].
        co2_emissions_medium_range
            CO2 emissions from medium-range flights [MtCO2].
        co2_emissions_long_range
            CO2 emissions from long-range flights [MtCO2].
        co2_emissions_passenger
            CO2 emissions from passenger transport [MtCO2].
        co2_emissions_freight
            CO2 emissions from freight transport [MtCO2].
        co2_emissions
            Total CO2 emissions [MtCO2].
        """
        # Locally filling incomplete emission factors with zeros so that sums are not nan if one is undefined
        dropin_fuel_mean_co2_emission_factor.fillna(0, inplace=True)
        hydrogen_mean_co2_emission_factor.fillna(0, inplace=True)
        electric_mean_co2_emission_factor.fillna(0, inplace=True)

        # Short range
        co2_emissions_short_range = (
            rpk_short_range
            / (load_factor / 100)
            * (
                ask_short_range_dropin_fuel_share
                / 100
                * (dropin_fuel_mean_co2_emission_factor * energy_per_ask_short_range_dropin_fuel)
                + ask_short_range_hydrogen_share
                / 100
                * (energy_per_ask_short_range_hydrogen * hydrogen_mean_co2_emission_factor)
                + ask_short_range_electric_share
                / 100
                * (energy_per_ask_short_range_electric * electric_mean_co2_emission_factor)
            )
            * 10 ** (-12)
        )

        # Medium range
        co2_emissions_medium_range = (
            rpk_medium_range
            / (load_factor / 100)
            * (
                ask_medium_range_dropin_fuel_share
                / 100
                * (dropin_fuel_mean_co2_emission_factor * energy_per_ask_medium_range_dropin_fuel)
                + ask_medium_range_hydrogen_share
                / 100
                * (energy_per_ask_medium_range_hydrogen * hydrogen_mean_co2_emission_factor)
                + ask_medium_range_electric_share
                / 100
                * (energy_per_ask_medium_range_electric * electric_mean_co2_emission_factor)
            )
            * 10 ** (-12)
        )

        # Long range
        co2_emissions_long_range = (
            rpk_long_range
            / (load_factor / 100)
            * (
                ask_long_range_dropin_fuel_share
                / 100
                * (dropin_fuel_mean_co2_emission_factor * energy_per_ask_long_range_dropin_fuel)
                + ask_long_range_hydrogen_share
                / 100
                * (energy_per_ask_long_range_hydrogen * hydrogen_mean_co2_emission_factor)
                + ask_long_range_electric_share
                / 100
                * (energy_per_ask_long_range_electric * electric_mean_co2_emission_factor)
            )
            * 10 ** (-12)
        )

        # Freight
        co2_emissions_freight = (
            rtk
            * (
                rtk_dropin_fuel_share
                / 100
                * (dropin_fuel_mean_co2_emission_factor * energy_per_rtk_freight_dropin_fuel)
                + rtk_hydrogen_share
                / 100
                * (energy_per_rtk_freight_hydrogen * hydrogen_mean_co2_emission_factor)
                + rtk_electric_share
                / 100
                * (energy_per_rtk_freight_electric * electric_mean_co2_emission_factor)
            )
            * 10 ** (-12)
        )

        # Passenger
        co2_emissions_passenger = (
            co2_emissions_short_range + co2_emissions_medium_range + co2_emissions_long_range
        )

        # Total: new way to affect without for loops
        historical_co2_emissions_for_temperature = self.climate_historical_data[:, 1]
        self.df_climate.loc[
            self.climate_historic_start_year : self.historic_start_year - 1, "co2_emissions"
        ] = historical_co2_emissions_for_temperature[
            : self.historic_start_year - self.climate_historic_start_year
        ]
        self.df_climate.loc[self.historic_start_year : self.end_year, "co2_emissions"] = (
            co2_emissions_passenger + co2_emissions_freight
        )

        self.df["co2_emissions_short_range"] = co2_emissions_short_range
        self.df["co2_emissions_medium_range"] = co2_emissions_medium_range
        self.df["co2_emissions_long_range"] = co2_emissions_long_range
        self.df["co2_emissions_freight"] = co2_emissions_freight
        self.df["co2_emissions_passenger"] = co2_emissions_passenger
        co2_emissions = self.df_climate["co2_emissions"]

        return (
            co2_emissions_short_range,
            co2_emissions_medium_range,
            co2_emissions_long_range,
            co2_emissions_passenger,
            co2_emissions_freight,
            co2_emissions,
        )


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
    ) -> pd.Series:
        """
        Execute the computation of cumulative CO2 emissions.

        Parameters
        ----------
        co2_emissions
            Annual CO2 emissions [MtCO2].

        Returns
        -------
        cumulative_co2_emissions
            Cumulative CO2 emissions [GtCO2].

        """
        cumulative_co2_emissions = (
            co2_emissions.loc[self.prospection_start_year : self.end_year] / 1000
        ).cumsum()

        self.df["cumulative_co2_emissions"] = cumulative_co2_emissions

        return cumulative_co2_emissions


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
        co2_emissions_2019technology_baseline3
            CO2 emissions from all commercial air transport based on 2019 technological level with a baseline air traffic growth [MtCO2].
        co2_emissions_2019technology
            CO2 emissions from all commercial air transport based on 2019 technological level [MtCO2].
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

        co2_emissions_2019technology_baseline3 = (
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

        co2_emissions_2019technology = (
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

        self.df.loc[years, "co2_emissions_2019technology_baseline3"] = (
            co2_emissions_2019technology_baseline3
        )
        self.df.loc[years, "co2_emissions_2019technology"] = co2_emissions_2019technology
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
            co2_emissions_2019technology_baseline3,
            co2_emissions_2019technology,
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
        co2_emissions_2019technology_baseline3: pd.Series,
        co2_emissions_2019technology: pd.Series,
        co2_emissions_including_load_factor: pd.Series,
        co2_emissions_including_energy: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Execute the computation of detailed cumulative CO2 emissions breakdown.
        Parameters
        ----------
        co2_emissions_2019technology_baseline3
            CO2 emissions from all commercial air transport based on 2019 technological level with a baseline air traffic growth [MtCO2].
        co2_emissions_2019technology
            CO2 emissions from all commercial air transport based on 2019 technological level [MtCO2].
        co2_emissions_including_load_factor
            CO2 emissions from all commercial air transport including aircraft efficiency, operation and load factor improvements [MtCO2].
        co2_emissions_including_energy
            CO2 emissions from all commercial air transport including aircraft efficiency, operation and load factor improvements and energy decarbonization [MtCO2].

        Returns
        -------
        cumulative_co2_emissions_2019technology_baseline3
            Cumulative CO2 emissions from all commercial air transport based on 2019 technological level with a baseline air traffic growth [GtCO2].
        cumulative_co2_emissions_2019technology
            Cumulative CO2 emissions from all commercial air transport based on 2019 technological level [GtCO2].
        cumulative_co2_emissions_including_load_factor
            Cumulative CO2 emissions from all commercial air transport including aircraft efficiency, operation and load factor
            improvements [GtCO2].
        cumulative_co2_emissions_including_energy
            Cumulative CO2 emissions from all commercial air transport including aircraft efficiency, operation and load factor
            improvements and energy decarbonization [GtCO2].

        """
        cumulative_co2_emissions_2019technology_baseline3 = (
            co2_emissions_2019technology_baseline3.loc[self.prospection_start_year : self.end_year]
            / 1000
        ).cumsum()

        cumulative_co2_emissions_2019technology = (
            co2_emissions_2019technology.loc[self.prospection_start_year : self.end_year] / 1000
        ).cumsum()

        cumulative_co2_emissions_including_load_factor = (
            co2_emissions_including_load_factor.loc[self.prospection_start_year : self.end_year]
            / 1000
        ).cumsum()

        cumulative_co2_emissions_including_energy = (
            co2_emissions_including_energy.loc[self.prospection_start_year : self.end_year] / 1000
        ).cumsum()

        self.df["cumulative_co2_emissions_2019technology_baseline3"] = (
            cumulative_co2_emissions_2019technology_baseline3
        )
        self.df["cumulative_co2_emissions_2019technology"] = cumulative_co2_emissions_2019technology
        self.df["cumulative_co2_emissions_including_load_factor"] = (
            cumulative_co2_emissions_including_load_factor
        )
        self.df["cumulative_co2_emissions_including_energy"] = (
            cumulative_co2_emissions_including_energy
        )

        return (
            cumulative_co2_emissions_2019technology_baseline3,
            cumulative_co2_emissions_2019technology,
            cumulative_co2_emissions_including_load_factor,
            cumulative_co2_emissions_including_energy,
        )


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

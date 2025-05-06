from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class KayaFactors(AeroMAPSModel):
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
        #  --> Caution with the 3.6 there !!
        #      With the new model we should stick to MJ instead of KWh even for the electricity
        #  --> Update: removed the 3.6, emission factor converted in the input file
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
        """CO2 emissions calculation."""
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
    def __init__(self, name="cumulative_co2_emissions", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions: pd.Series,
    ) -> pd.Series:
        cumulative_co2_emissions = (
            co2_emissions.loc[self.prospection_start_year : self.end_year] / 1000
        ).cumsum()

        self.df["cumulative_co2_emissions"] = cumulative_co2_emissions

        return cumulative_co2_emissions


class DetailedCo2Emissions(AeroMAPSModel):
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
    def __init__(self, name="detailed_cumulative_co2_emissions", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions_2019technology_baseline3: pd.Series,
        co2_emissions_2019technology: pd.Series,
        co2_emissions_including_load_factor: pd.Series,
        co2_emissions_including_energy: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
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

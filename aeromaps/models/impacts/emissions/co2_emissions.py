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
        freight_energy_share_2019: float,
        energy_consumption_passenger_biofuel_without_operations: pd.Series,
        energy_consumption_passenger_electrofuel_without_operations: pd.Series,
        energy_consumption_passenger_kerosene_without_operations: pd.Series,
        energy_consumption_passenger_hydrogen_without_operations: pd.Series,
        energy_consumption_passenger_electric_without_operations: pd.Series,
        energy_consumption_passenger_biofuel: pd.Series,
        energy_consumption_passenger_electrofuel: pd.Series,
        energy_consumption_passenger_kerosene: pd.Series,
        energy_consumption_passenger_hydrogen: pd.Series,
        energy_consumption_passenger_electric: pd.Series,
        energy_consumption_freight_biofuel_without_operations: pd.Series,
        energy_consumption_freight_electrofuel_without_operations: pd.Series,
        energy_consumption_freight_kerosene_without_operations: pd.Series,
        energy_consumption_freight_hydrogen_without_operations: pd.Series,
        energy_consumption_freight_electric_without_operations: pd.Series,
        energy_consumption_freight_biofuel: pd.Series,
        energy_consumption_freight_electrofuel: pd.Series,
        energy_consumption_freight_kerosene: pd.Series,
        energy_consumption_freight_hydrogen: pd.Series,
        energy_consumption_freight_electric: pd.Series,
        energy_consumption_biofuel: pd.Series,
        energy_consumption_electrofuel: pd.Series,
        energy_consumption_kerosene: pd.Series,
        energy_consumption_hydrogen: pd.Series,
        energy_consumption_electric: pd.Series,
        energy_consumption: pd.Series,
        kerosene_emission_factor: pd.Series,
        biofuel_mean_emission_factor: pd.Series,
        electrofuel_emission_factor: pd.Series,
        liquid_hydrogen_mean_emission_factor: pd.Series,
        electricity_emission_factor: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        energy_per_ask_mean_without_operations = (
            energy_consumption_passenger_biofuel_without_operations
            + energy_consumption_passenger_electrofuel_without_operations
            + energy_consumption_passenger_kerosene_without_operations
            + energy_consumption_passenger_hydrogen_without_operations
            + energy_consumption_passenger_electric_without_operations
        ) / ask

        energy_per_ask_mean = (
            energy_consumption_passenger_biofuel
            + energy_consumption_passenger_electrofuel
            + energy_consumption_passenger_kerosene
            + energy_consumption_passenger_hydrogen
            + energy_consumption_passenger_electric
        ) / ask

        energy_per_rtk_mean_without_operations = (
            energy_consumption_freight_biofuel_without_operations
            + energy_consumption_freight_electrofuel_without_operations
            + energy_consumption_freight_kerosene_without_operations
            + energy_consumption_freight_hydrogen_without_operations
            + energy_consumption_freight_electric_without_operations
        ) / rtk

        energy_per_rtk_mean = (
            energy_consumption_freight_biofuel
            + energy_consumption_freight_electrofuel
            + energy_consumption_freight_kerosene
            + energy_consumption_freight_hydrogen
            + energy_consumption_freight_electric
        ) / rtk

        co2_per_energy_mean = (
            biofuel_mean_emission_factor * energy_consumption_biofuel
            + electrofuel_emission_factor * energy_consumption_electrofuel
            + kerosene_emission_factor * energy_consumption_kerosene
            + liquid_hydrogen_mean_emission_factor * energy_consumption_hydrogen
            + electricity_emission_factor / 3.6 * energy_consumption_electric
        ) / energy_consumption

        for k in range(self.historic_start_year, self.prospection_start_year):
            energy_per_ask_mean_without_operations.loc[k] = (
                energy_consumption.loc[k] / ask.loc[k] * (1 - freight_energy_share_2019 / 100)
            )
            energy_per_ask_mean.loc[k] = (
                energy_consumption.loc[k] / ask.loc[k] * (1 - freight_energy_share_2019 / 100)
            )
            energy_per_rtk_mean.loc[k] = (
                energy_consumption.loc[k] / rtk.loc[k] * freight_energy_share_2019 / 100
            )
            energy_per_rtk_mean.loc[k] = (
                energy_consumption.loc[k] / rtk.loc[k] * freight_energy_share_2019 / 100
            )
            co2_per_energy_mean.loc[k] = kerosene_emission_factor.loc[k]

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
        biofuel_share: pd.Series,
        electrofuel_share: pd.Series,
        kerosene_share: pd.Series,
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
        kerosene_emission_factor: pd.Series,
        biofuel_mean_emission_factor: pd.Series,
        electrofuel_emission_factor: pd.Series,
        liquid_hydrogen_mean_emission_factor: pd.Series,
        electricity_emission_factor: pd.Series,
        energy_per_ask_mean: pd.Series,
        energy_per_rtk_mean: pd.Series,
        co2_per_energy_mean: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """CO2 emissions calculation."""
        # To be improved

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "co2_emissions_short_range"] = (
                rpk_short_range.loc[k]
                / (load_factor.loc[k] / 100)
                * energy_per_ask_mean.loc[k]
                * co2_per_energy_mean.loc[k]
                * 10 ** (-12)
            )
            self.df.loc[k, "co2_emissions_medium_range"] = (
                rpk_medium_range.loc[k]
                / (load_factor.loc[k] / 100)
                * energy_per_ask_mean.loc[k]
                * co2_per_energy_mean.loc[k]
                * 10 ** (-12)
            )
            self.df.loc[k, "co2_emissions_long_range"] = (
                rpk_long_range.loc[k]
                / (load_factor.loc[k] / 100)
                * energy_per_ask_mean.loc[k]
                * co2_per_energy_mean.loc[k]
                * 10 ** (-12)
            )
            self.df.loc[k, "co2_emissions_freight"] = (
                rtk.loc[k] * energy_per_rtk_mean.loc[k] * co2_per_energy_mean.loc[k] * 10 ** (-12)
            )

        # Short range
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "co2_emissions_short_range"] = (
                rpk_short_range.loc[k]
                / (load_factor.loc[k] / 100)
                * (
                    ask_short_range_dropin_fuel_share.loc[k]
                    / 100
                    * (
                        biofuel_share.loc[k]
                        / 100
                        * energy_per_ask_short_range_dropin_fuel.loc[k]
                        * biofuel_mean_emission_factor.loc[k]
                        + electrofuel_share.loc[k]
                        / 100
                        * energy_per_ask_short_range_dropin_fuel.loc[k]
                        * electrofuel_emission_factor.loc[k]
                        + kerosene_share.loc[k]
                        / 100
                        * energy_per_ask_short_range_dropin_fuel.loc[k]
                        * kerosene_emission_factor.loc[k]
                    )
                    + ask_short_range_hydrogen_share.loc[k]
                    / 100
                    * energy_per_ask_short_range_hydrogen.loc[k]
                    * liquid_hydrogen_mean_emission_factor.loc[k]
                    + ask_short_range_electric_share.loc[k]
                    / 100
                    * energy_per_ask_short_range_electric.loc[k]
                    * electricity_emission_factor.loc[k]
                    / 3.6
                )
                * 10 ** (-12)
            )

        # Medium range
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "co2_emissions_medium_range"] = (
                rpk_medium_range.loc[k]
                / (load_factor.loc[k] / 100)
                * (
                    ask_medium_range_dropin_fuel_share.loc[k]
                    / 100
                    * (
                        biofuel_share.loc[k]
                        / 100
                        * energy_per_ask_medium_range_dropin_fuel.loc[k]
                        * biofuel_mean_emission_factor.loc[k]
                        + electrofuel_share.loc[k]
                        / 100
                        * energy_per_ask_medium_range_dropin_fuel.loc[k]
                        * electrofuel_emission_factor.loc[k]
                        + kerosene_share.loc[k]
                        / 100
                        * energy_per_ask_medium_range_dropin_fuel.loc[k]
                        * kerosene_emission_factor.loc[k]
                    )
                    + ask_medium_range_hydrogen_share.loc[k]
                    / 100
                    * energy_per_ask_medium_range_hydrogen.loc[k]
                    * liquid_hydrogen_mean_emission_factor.loc[k]
                    + ask_medium_range_electric_share.loc[k]
                    / 100
                    * energy_per_ask_medium_range_electric.loc[k]
                    * electricity_emission_factor.loc[k]
                    / 3.6
                )
                * 10 ** (-12)
            )

        # Long range
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "co2_emissions_long_range"] = (
                rpk_long_range.loc[k]
                / (load_factor.loc[k] / 100)
                * (
                    ask_long_range_dropin_fuel_share.loc[k]
                    / 100
                    * (
                        biofuel_share.loc[k]
                        / 100
                        * energy_per_ask_long_range_dropin_fuel.loc[k]
                        * biofuel_mean_emission_factor.loc[k]
                        + electrofuel_share.loc[k]
                        / 100
                        * energy_per_ask_long_range_dropin_fuel.loc[k]
                        * electrofuel_emission_factor.loc[k]
                        + kerosene_share.loc[k]
                        / 100
                        * energy_per_ask_long_range_dropin_fuel.loc[k]
                        * kerosene_emission_factor.loc[k]
                    )
                    + ask_long_range_hydrogen_share.loc[k]
                    / 100
                    * energy_per_ask_long_range_hydrogen.loc[k]
                    * liquid_hydrogen_mean_emission_factor.loc[k]
                    + ask_long_range_electric_share.loc[k]
                    / 100
                    * energy_per_ask_long_range_electric.loc[k]
                    * electricity_emission_factor.loc[k]
                    / 3.6
                )
                * 10 ** (-12)
            )

        # Freight
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "co2_emissions_freight"] = (
                rtk.loc[k]
                * (
                    rtk_dropin_fuel_share.loc[k]
                    / 100
                    * (
                        biofuel_share.loc[k]
                        / 100
                        * energy_per_rtk_freight_dropin_fuel.loc[k]
                        * biofuel_mean_emission_factor.loc[k]
                        + electrofuel_share.loc[k]
                        / 100
                        * energy_per_rtk_freight_dropin_fuel.loc[k]
                        * electrofuel_emission_factor.loc[k]
                        + kerosene_share.loc[k]
                        / 100
                        * energy_per_rtk_freight_dropin_fuel.loc[k]
                        * kerosene_emission_factor.loc[k]
                    )
                    + rtk_hydrogen_share.loc[k]
                    / 100
                    * energy_per_rtk_freight_hydrogen.loc[k]
                    * liquid_hydrogen_mean_emission_factor.loc[k]
                    + rtk_electric_share.loc[k]
                    / 100
                    * energy_per_rtk_freight_electric.loc[k]
                    * electricity_emission_factor.loc[k]
                    / 3.6
                )
                * 10 ** (-12)
            )

        # Passenger
        for k in range(self.historic_start_year, self.end_year + 1):
            self.df.loc[k, "co2_emissions_passenger"] = (
                self.df.loc[k, "co2_emissions_short_range"]
                + self.df.loc[k, "co2_emissions_medium_range"]
                + self.df.loc[k, "co2_emissions_long_range"]
            )

        # Total
        historical_co2_emissions_for_temperature = self.climate_historical_data[:, 1]
        for k in range(self.climate_historic_start_year, self.historic_start_year):
            self.df_climate.loc[k, "co2_emissions"] = historical_co2_emissions_for_temperature[
                k - self.climate_historic_start_year
            ]
        for k in range(self.historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "co2_emissions"] = (
                self.df.loc[k, "co2_emissions_passenger"] + self.df.loc[k, "co2_emissions_freight"]
            )

        co2_emissions_short_range = self.df["co2_emissions_short_range"]
        co2_emissions_medium_range = self.df["co2_emissions_medium_range"]
        co2_emissions_long_range = self.df["co2_emissions_long_range"]
        co2_emissions_freight = self.df["co2_emissions_freight"]
        co2_emissions_passenger = self.df["co2_emissions_passenger"]
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
        self.df.loc[self.prospection_start_year - 1, "cumulative_co2_emissions"] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "cumulative_co2_emissions"] = (
                self.df.loc[k - 1, "cumulative_co2_emissions"] + co2_emissions.loc[k] / 1000
            )

        cumulative_co2_emissions = self.df["cumulative_co2_emissions"]

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
        for k in range(self.prospection_start_year - 1, self.end_year + 1):
            self.df.loc[k, "co2_emissions_2019technology_baseline3"] = (
                rpk_reference.loc[k]
                * energy_per_ask_mean_without_operations.loc[self.prospection_start_year - 1]
                * energy_per_ask_mean.loc[self.prospection_start_year - 1]
                / energy_per_ask_mean_without_operations.loc[self.prospection_start_year - 1]
                / (load_factor.loc[self.prospection_start_year - 1] / 100)
                * co2_per_energy_mean.loc[self.prospection_start_year - 1]
                * 10 ** (-12)
            ) + (
                rtk_reference.loc[k]
                * energy_per_rtk_mean_without_operations.loc[self.prospection_start_year - 1]
                * energy_per_rtk_mean.loc[self.prospection_start_year - 1]
                / energy_per_rtk_mean_without_operations.loc[self.prospection_start_year - 1]
                * co2_per_energy_mean.loc[self.prospection_start_year - 1]
                * 10 ** (-12)
            )
            self.df.loc[k, "co2_emissions_2019technology"] = rpk.loc[
                k
            ] * energy_per_ask_mean_without_operations.loc[
                self.prospection_start_year - 1
            ] * energy_per_ask_mean.loc[
                self.prospection_start_year - 1
            ] / energy_per_ask_mean_without_operations.loc[self.prospection_start_year - 1] / (
                load_factor.loc[self.prospection_start_year - 1] / 100
            ) * co2_per_energy_mean.loc[self.prospection_start_year - 1] * 10 ** (-12) + (
                rtk.loc[k]
                * energy_per_rtk_mean_without_operations.loc[self.prospection_start_year - 1]
                * energy_per_rtk_mean.loc[self.prospection_start_year - 1]
                / energy_per_rtk_mean_without_operations.loc[self.prospection_start_year - 1]
                * co2_per_energy_mean.loc[self.prospection_start_year - 1]
                * 10 ** (-12)
            )
            self.df.loc[k, "co2_emissions_including_aircraft_efficiency"] = rpk.loc[
                k
            ] * energy_per_ask_mean_without_operations.loc[k] * energy_per_ask_mean.loc[
                self.prospection_start_year - 1
            ] / energy_per_ask_mean_without_operations.loc[self.prospection_start_year - 1] / (
                load_factor.loc[self.prospection_start_year - 1] / 100
            ) * co2_per_energy_mean.loc[self.prospection_start_year - 1] * 10 ** (-12) + (
                rtk.loc[k]
                * energy_per_rtk_mean_without_operations.loc[k]
                * energy_per_rtk_mean.loc[self.prospection_start_year - 1]
                / energy_per_rtk_mean_without_operations.loc[self.prospection_start_year - 1]
                * co2_per_energy_mean.loc[self.prospection_start_year - 1]
                * 10 ** (-12)
            )
            self.df.loc[k, "co2_emissions_including_operations"] = rpk.loc[
                k
            ] * energy_per_ask_mean_without_operations.loc[k] * energy_per_ask_mean.loc[
                k
            ] / energy_per_ask_mean_without_operations.loc[k] / (
                load_factor.loc[self.prospection_start_year - 1] / 100
            ) * co2_per_energy_mean.loc[self.prospection_start_year - 1] * 10 ** (-12) + (
                rtk.loc[k]
                * energy_per_rtk_mean_without_operations.loc[k]
                * energy_per_rtk_mean.loc[k]
                / energy_per_rtk_mean_without_operations.loc[k]
                * co2_per_energy_mean.loc[self.prospection_start_year - 1]
                * 10 ** (-12)
            )
            self.df.loc[k, "co2_emissions_including_load_factor"] = rpk.loc[
                k
            ] * energy_per_ask_mean_without_operations.loc[k] * energy_per_ask_mean.loc[
                k
            ] / energy_per_ask_mean_without_operations.loc[k] / (
                load_factor.loc[k] / 100
            ) * co2_per_energy_mean.loc[self.prospection_start_year - 1] * 10 ** (-12) + (
                rtk.loc[k]
                * energy_per_rtk_mean_without_operations.loc[k]
                * energy_per_rtk_mean.loc[k]
                / energy_per_rtk_mean_without_operations.loc[k]
                * co2_per_energy_mean.loc[self.prospection_start_year - 1]
                * 10 ** (-12)
            )
            self.df.loc[k, "co2_emissions_including_energy"] = rpk.loc[
                k
            ] * energy_per_ask_mean_without_operations.loc[k] * energy_per_ask_mean.loc[
                k
            ] / energy_per_ask_mean_without_operations.loc[k] / (
                load_factor.loc[k] / 100
            ) * co2_per_energy_mean.loc[k] * 10 ** (-12) + (
                rtk.loc[k]
                * energy_per_rtk_mean_without_operations.loc[k]
                * energy_per_rtk_mean.loc[k]
                / energy_per_rtk_mean_without_operations.loc[k]
                * co2_per_energy_mean.loc[k]
                * 10 ** (-12)
            )

        co2_emissions_2019technology_baseline3 = self.df["co2_emissions_2019technology_baseline3"]
        co2_emissions_2019technology = self.df["co2_emissions_2019technology"]
        co2_emissions_including_aircraft_efficiency = self.df[
            "co2_emissions_including_aircraft_efficiency"
        ]
        co2_emissions_including_operations = self.df["co2_emissions_including_operations"]
        co2_emissions_including_load_factor = self.df["co2_emissions_including_load_factor"]
        co2_emissions_including_energy = self.df["co2_emissions_including_energy"]

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
        self.df.loc[
            self.prospection_start_year - 1, "cumulative_co2_emissions_2019technology_baseline3"
        ] = 0.0
        self.df.loc[self.prospection_start_year - 1, "cumulative_co2_emissions_2019technology"] = (
            0.0
        )
        self.df.loc[
            self.prospection_start_year - 1, "cumulative_co2_emissions_including_load_factor"
        ] = 0.0
        self.df.loc[
            self.prospection_start_year - 1, "cumulative_co2_emissions_including_energy"
        ] = 0.0

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "cumulative_co2_emissions_2019technology_baseline3"] = (
                self.df.loc[k - 1, "cumulative_co2_emissions_2019technology_baseline3"]
                + co2_emissions_2019technology_baseline3.loc[k] / 1000
            )
            self.df.loc[k, "cumulative_co2_emissions_2019technology"] = (
                self.df.loc[k - 1, "cumulative_co2_emissions_2019technology"]
                + co2_emissions_2019technology.loc[k] / 1000
            )
            self.df.loc[k, "cumulative_co2_emissions_including_load_factor"] = (
                self.df.loc[k - 1, "cumulative_co2_emissions_including_load_factor"]
                + co2_emissions_including_load_factor.loc[k] / 1000
            )
            self.df.loc[k, "cumulative_co2_emissions_including_energy"] = (
                self.df.loc[k - 1, "cumulative_co2_emissions_including_energy"]
                + co2_emissions_including_energy.loc[k] / 1000
            )

        cumulative_co2_emissions_2019technology_baseline3 = self.df[
            "cumulative_co2_emissions_2019technology_baseline3"
        ]
        cumulative_co2_emissions_2019technology = self.df["cumulative_co2_emissions_2019technology"]
        cumulative_co2_emissions_including_load_factor = self.df[
            "cumulative_co2_emissions_including_load_factor"
        ]
        cumulative_co2_emissions_including_energy = self.df[
            "cumulative_co2_emissions_including_energy"
        ]

        return (
            cumulative_co2_emissions_2019technology_baseline3,
            cumulative_co2_emissions_2019technology,
            cumulative_co2_emissions_including_load_factor,
            cumulative_co2_emissions_including_energy,
        )


class SimpleCO2Emissions(AeroMAPSModel):
    def __init__(self, name="simple_co2_emissions", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.climate_historical_data = None

    def compute(
        self,
        energy_consumption_init: pd.Series,
        biofuel_mean_emission_factor: pd.Series,
        electrofuel_emission_factor: pd.Series,
        kerosene_emission_factor: pd.Series,
        liquid_hydrogen_mean_emission_factor: pd.Series,
        energy_consumption_kerosene: pd.Series,
        energy_consumption_biofuel: pd.Series,
        energy_consumption_electrofuel: pd.Series,
        energy_consumption_hydrogen: pd.Series,
    ) -> pd.Series:
        """Simple CO2 emissions calculation."""

        ## Initialization
        historical_co2_emissions_for_temperature = self.climate_historical_data[:, 1]

        # Calculation
        for k in range(self.climate_historic_start_year, self.historic_start_year):
            self.df_climate.loc[k, "co2_emissions"] = historical_co2_emissions_for_temperature[
                k - self.climate_historic_start_year
            ]

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df_climate.loc[k, "co2_emissions"] = (
                kerosene_emission_factor.loc[k] / 10**12 * energy_consumption_init.loc[k]
            )

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df_climate.loc[k, "co2_emissions"] = (
                biofuel_mean_emission_factor.loc[k] / 10**12 * energy_consumption_biofuel.loc[k]
                + electrofuel_emission_factor.loc[k]
                / 10**12
                * energy_consumption_electrofuel.loc[k]
                + kerosene_emission_factor.loc[k] / 10**12 * energy_consumption_kerosene.loc[k]
                + liquid_hydrogen_mean_emission_factor.loc[k]
                / 10**12
                * energy_consumption_hydrogen.loc[k]
            )

        co2_emissions = self.df_climate.loc[:, "co2_emissions"]

        return co2_emissions

from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class PassengerAircraftEfficiencySimple(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_efficiency_simple", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_init: pd.Series,
        ask: pd.Series,
        short_range_energy_share_2019: float,
        medium_range_energy_share_2019: float,
        long_range_energy_share_2019: float,
        short_range_rpk_share_2019: float,
        medium_range_rpk_share_2019: float,
        long_range_rpk_share_2019: float,
        energy_per_ask_short_range_dropin_fuel_gain_reference_years: list,
        energy_per_ask_short_range_dropin_fuel_gain_reference_years_values: list,
        energy_per_ask_medium_range_dropin_fuel_gain_reference_years: list,
        energy_per_ask_medium_range_dropin_fuel_gain_reference_years_values: list,
        energy_per_ask_long_range_dropin_fuel_gain_reference_years: list,
        energy_per_ask_long_range_dropin_fuel_gain_reference_years_values: list,
        ask_short_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_long_range: pd.Series,
        relative_energy_per_ask_hydrogen_wrt_dropin_short_range_reference_years: list,
        relative_energy_per_ask_hydrogen_wrt_dropin_short_range_reference_years_values: list,
        relative_energy_per_ask_hydrogen_wrt_dropin_medium_range_reference_years: list,
        relative_energy_per_ask_hydrogen_wrt_dropin_medium_range_reference_years_values: list,
        relative_energy_per_ask_hydrogen_wrt_dropin_long_range_reference_years: list,
        relative_energy_per_ask_hydrogen_wrt_dropin_long_range_reference_years_values: list,
        relative_energy_per_ask_electric_wrt_dropin_short_range_reference_years: list,
        relative_energy_per_ask_electric_wrt_dropin_short_range_reference_years_values: list,
        relative_energy_per_ask_electric_wrt_dropin_medium_range_reference_years: list,
        relative_energy_per_ask_electric_wrt_dropin_medium_range_reference_years_values: list,
        relative_energy_per_ask_electric_wrt_dropin_long_range_reference_years: list,
        relative_energy_per_ask_electric_wrt_dropin_long_range_reference_years_values: list,
        hydrogen_final_market_share_short_range: float,
        hydrogen_introduction_year_short_range: int,
        hydrogen_final_market_share_medium_range: float,
        hydrogen_introduction_year_medium_range: int,
        hydrogen_final_market_share_long_range: float,
        hydrogen_introduction_year_long_range: int,
        electric_final_market_share_short_range: float,
        electric_introduction_year_short_range: int,
        electric_final_market_share_medium_range: float,
        electric_introduction_year_medium_range: int,
        electric_final_market_share_long_range: float,
        electric_introduction_year_long_range: int,
        fleet_renewal_duration: float,
        covid_energy_intensity_per_ask_increase_2020: float,
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
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        """Energy consumption per ASK (without operations) calculation using simple models."""

        # Initialization based on 2019 share
        energy_consumption_per_ask_init = energy_consumption_init / ask

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_dropin_fuel"] = (
                energy_consumption_per_ask_init.loc[k]
                * short_range_energy_share_2019
                / short_range_rpk_share_2019
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_dropin_fuel"] = (
                energy_consumption_per_ask_init.loc[k]
                * medium_range_energy_share_2019
                / medium_range_rpk_share_2019
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_dropin_fuel"] = (
                energy_consumption_per_ask_init.loc[k]
                * long_range_energy_share_2019
                / long_range_rpk_share_2019
            )

        # Projections

        ## Drop-in

        energy_per_ask_short_range_dropin_fuel_gain = AeromapsInterpolationFunction(
            self,
            energy_per_ask_short_range_dropin_fuel_gain_reference_years,
            energy_per_ask_short_range_dropin_fuel_gain_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "energy_per_ask_short_range_dropin_fuel_gain"] = (
            energy_per_ask_short_range_dropin_fuel_gain
        )
        energy_per_ask_medium_range_dropin_fuel_gain = AeromapsInterpolationFunction(
            self,
            energy_per_ask_medium_range_dropin_fuel_gain_reference_years,
            energy_per_ask_medium_range_dropin_fuel_gain_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "energy_per_ask_medium_range_dropin_fuel_gain"] = (
            energy_per_ask_medium_range_dropin_fuel_gain
        )
        energy_per_ask_long_range_dropin_fuel_gain = AeromapsInterpolationFunction(
            self,
            energy_per_ask_long_range_dropin_fuel_gain_reference_years,
            energy_per_ask_long_range_dropin_fuel_gain_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "energy_per_ask_long_range_dropin_fuel_gain"] = (
            energy_per_ask_long_range_dropin_fuel_gain
        )

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_dropin_fuel"] = (
                self.df.loc[k - 1, "energy_per_ask_without_operations_short_range_dropin_fuel"]
                * (1 - energy_per_ask_short_range_dropin_fuel_gain.loc[k] / 100)
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_dropin_fuel"] = (
                self.df.loc[k - 1, "energy_per_ask_without_operations_medium_range_dropin_fuel"]
                * (1 - energy_per_ask_medium_range_dropin_fuel_gain.loc[k] / 100)
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_dropin_fuel"] = (
                self.df.loc[k - 1, "energy_per_ask_without_operations_long_range_dropin_fuel"]
                * (1 - energy_per_ask_long_range_dropin_fuel_gain.loc[k] / 100)
            )

        self.df.loc[2020, "energy_per_ask_without_operations_short_range_dropin_fuel"] = (
            self.df.loc[2019, "energy_per_ask_without_operations_short_range_dropin_fuel"]
            * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)
        )
        self.df.loc[2020, "energy_per_ask_without_operations_medium_range_dropin_fuel"] = (
            self.df.loc[2019, "energy_per_ask_without_operations_medium_range_dropin_fuel"]
            * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)
        )
        self.df.loc[2020, "energy_per_ask_without_operations_long_range_dropin_fuel"] = self.df.loc[
            2019, "energy_per_ask_without_operations_long_range_dropin_fuel"
        ] * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)

        energy_per_ask_without_operations_short_range_dropin_fuel = self.df[
            "energy_per_ask_without_operations_short_range_dropin_fuel"
        ]
        energy_per_ask_without_operations_medium_range_dropin_fuel = self.df[
            "energy_per_ask_without_operations_medium_range_dropin_fuel"
        ]
        energy_per_ask_without_operations_long_range_dropin_fuel = self.df[
            "energy_per_ask_without_operations_long_range_dropin_fuel"
        ]

        ## Hydrogen

        relative_energy_per_ask_hydrogen_wrt_dropin_short_range = AeromapsInterpolationFunction(
            self,
            relative_energy_per_ask_hydrogen_wrt_dropin_short_range_reference_years,
            relative_energy_per_ask_hydrogen_wrt_dropin_short_range_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "relative_energy_per_ask_hydrogen_wrt_dropin_short_range"] = (
            relative_energy_per_ask_hydrogen_wrt_dropin_short_range
        )
        relative_energy_per_ask_hydrogen_wrt_dropin_medium_range = AeromapsInterpolationFunction(
            self,
            relative_energy_per_ask_hydrogen_wrt_dropin_medium_range_reference_years,
            relative_energy_per_ask_hydrogen_wrt_dropin_medium_range_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "relative_energy_per_ask_hydrogen_wrt_dropin_medium_range"] = (
            relative_energy_per_ask_hydrogen_wrt_dropin_medium_range
        )
        relative_energy_per_ask_hydrogen_wrt_dropin_long_range = AeromapsInterpolationFunction(
            self,
            relative_energy_per_ask_hydrogen_wrt_dropin_long_range_reference_years,
            relative_energy_per_ask_hydrogen_wrt_dropin_long_range_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "relative_energy_per_ask_hydrogen_wrt_dropin_long_range"] = (
            relative_energy_per_ask_hydrogen_wrt_dropin_long_range
        )

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_hydrogen"] = (
                energy_per_ask_without_operations_short_range_dropin_fuel.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_hydrogen"] = (
                energy_per_ask_without_operations_medium_range_dropin_fuel.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_hydrogen"] = (
                energy_per_ask_without_operations_long_range_dropin_fuel.loc[k]
            )

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_hydrogen"] = (
                energy_per_ask_without_operations_short_range_dropin_fuel.loc[k]
                * relative_energy_per_ask_hydrogen_wrt_dropin_short_range.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_hydrogen"] = (
                energy_per_ask_without_operations_medium_range_dropin_fuel.loc[k]
                * relative_energy_per_ask_hydrogen_wrt_dropin_medium_range.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_hydrogen"] = (
                energy_per_ask_without_operations_long_range_dropin_fuel.loc[k]
                * relative_energy_per_ask_hydrogen_wrt_dropin_long_range.loc[k]
            )

        energy_per_ask_without_operations_short_range_hydrogen = self.df[
            "energy_per_ask_without_operations_short_range_hydrogen"
        ]
        energy_per_ask_without_operations_medium_range_hydrogen = self.df[
            "energy_per_ask_without_operations_medium_range_hydrogen"
        ]
        energy_per_ask_without_operations_long_range_hydrogen = self.df[
            "energy_per_ask_without_operations_long_range_hydrogen"
        ]

        ## Electric

        relative_energy_per_ask_electric_wrt_dropin_short_range = AeromapsInterpolationFunction(
            self,
            relative_energy_per_ask_electric_wrt_dropin_short_range_reference_years,
            relative_energy_per_ask_electric_wrt_dropin_short_range_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "relative_energy_per_ask_electric_wrt_dropin_short_range"] = (
            relative_energy_per_ask_electric_wrt_dropin_short_range
        )
        relative_energy_per_ask_electric_wrt_dropin_medium_range = AeromapsInterpolationFunction(
            self,
            relative_energy_per_ask_electric_wrt_dropin_medium_range_reference_years,
            relative_energy_per_ask_electric_wrt_dropin_medium_range_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "relative_energy_per_ask_electric_wrt_dropin_medium_range"] = (
            relative_energy_per_ask_electric_wrt_dropin_medium_range
        )
        relative_energy_per_ask_electric_wrt_dropin_long_range = AeromapsInterpolationFunction(
            self,
            relative_energy_per_ask_electric_wrt_dropin_long_range_reference_years,
            relative_energy_per_ask_electric_wrt_dropin_long_range_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "relative_energy_per_ask_electric_wrt_dropin_long_range"] = (
            relative_energy_per_ask_electric_wrt_dropin_long_range
        )

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_electric"] = (
                energy_per_ask_without_operations_short_range_dropin_fuel.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_electric"] = (
                energy_per_ask_without_operations_medium_range_dropin_fuel.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_electric"] = (
                energy_per_ask_without_operations_long_range_dropin_fuel.loc[k]
            )

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_electric"] = (
                energy_per_ask_without_operations_short_range_dropin_fuel.loc[k]
                * relative_energy_per_ask_electric_wrt_dropin_short_range.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_electric"] = (
                energy_per_ask_without_operations_medium_range_dropin_fuel.loc[k]
                * relative_energy_per_ask_electric_wrt_dropin_medium_range.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_electric"] = (
                energy_per_ask_without_operations_long_range_dropin_fuel.loc[k]
                * relative_energy_per_ask_electric_wrt_dropin_long_range.loc[k]
            )

        energy_per_ask_without_operations_short_range_electric = self.df[
            "energy_per_ask_without_operations_short_range_electric"
        ]
        energy_per_ask_without_operations_medium_range_electric = self.df[
            "energy_per_ask_without_operations_medium_range_electric"
        ]
        energy_per_ask_without_operations_long_range_electric = self.df[
            "energy_per_ask_without_operations_long_range_electric"
        ]

        # ASK Hydrogen

        ## Short range
        transition_year = hydrogen_introduction_year_short_range + fleet_renewal_duration / 2
        hydrogen_share_limit = 0.02 * hydrogen_final_market_share_short_range
        hydrogen_share_parameter = np.log(100 / 2 - 1) / (fleet_renewal_duration / 2)
        for k in range(self.historic_start_year, self.end_year + 1):
            if (
                hydrogen_final_market_share_short_range
                / (1 + np.exp(-hydrogen_share_parameter * (k - transition_year)))
                < hydrogen_share_limit
            ):
                self.df.loc[k, "ask_short_range_hydrogen_share"] = 0
            else:
                self.df.loc[k, "ask_short_range_hydrogen_share"] = (
                    hydrogen_final_market_share_short_range
                    / (1 + np.exp(-hydrogen_share_parameter * (k - transition_year)))
                )

        ## Medium range
        transition_year = hydrogen_introduction_year_medium_range + fleet_renewal_duration / 2
        hydrogen_share_limit = 0.02 * hydrogen_final_market_share_medium_range
        hydrogen_share_parameter = np.log(100 / 2 - 1) / (fleet_renewal_duration / 2)
        for k in range(self.historic_start_year, self.end_year + 1):
            if (
                hydrogen_final_market_share_medium_range
                / (1 + np.exp(-hydrogen_share_parameter * (k - transition_year)))
                < hydrogen_share_limit
            ):
                self.df.loc[k, "ask_medium_range_hydrogen_share"] = 0
            else:
                self.df.loc[k, "ask_medium_range_hydrogen_share"] = (
                    hydrogen_final_market_share_medium_range
                    / (1 + np.exp(-hydrogen_share_parameter * (k - transition_year)))
                )

        ## Long range
        transition_year = hydrogen_introduction_year_long_range + fleet_renewal_duration / 2
        hydrogen_share_limit = 0.02 * hydrogen_final_market_share_long_range
        hydrogen_share_parameter = np.log(100 / 2 - 1) / (fleet_renewal_duration / 2)
        for k in range(self.historic_start_year, self.end_year + 1):
            if (
                hydrogen_final_market_share_long_range
                / (1 + np.exp(-hydrogen_share_parameter * (k - transition_year)))
                < hydrogen_share_limit
            ):
                self.df.loc[k, "ask_long_range_hydrogen_share"] = 0
            else:
                self.df.loc[k, "ask_long_range_hydrogen_share"] = (
                    hydrogen_final_market_share_long_range
                    / (1 + np.exp(-hydrogen_share_parameter * (k - transition_year)))
                )

        ask_short_range_hydrogen_share = self.df["ask_short_range_hydrogen_share"]
        ask_medium_range_hydrogen_share = self.df["ask_medium_range_hydrogen_share"]
        ask_long_range_hydrogen_share = self.df["ask_long_range_hydrogen_share"]

        ask_short_range_hydrogen = ask_short_range * ask_short_range_hydrogen_share / 100
        ask_medium_range_hydrogen = ask_medium_range * ask_medium_range_hydrogen_share / 100
        ask_long_range_hydrogen = ask_long_range * ask_long_range_hydrogen_share / 100
        self.df.loc[:, "ask_short_range_hydrogen"] = ask_short_range_hydrogen
        self.df.loc[:, "ask_medium_range_hydrogen"] = ask_medium_range_hydrogen
        self.df.loc[:, "ask_long_range_hydrogen"] = ask_long_range_hydrogen

        # ASK Electric

        ## Short range
        transition_year = electric_introduction_year_short_range + fleet_renewal_duration / 2
        electric_share_limit = 0.02 * electric_final_market_share_short_range
        electric_share_parameter = np.log(100 / 2 - 1) / (fleet_renewal_duration / 2)
        for k in range(self.historic_start_year, self.end_year + 1):
            if (
                electric_final_market_share_short_range
                / (1 + np.exp(-electric_share_parameter * (k - transition_year)))
                < electric_share_limit
            ):
                self.df.loc[k, "ask_short_range_electric_share"] = 0
            else:
                self.df.loc[k, "ask_short_range_electric_share"] = (
                    electric_final_market_share_short_range
                    / (1 + np.exp(-electric_share_parameter * (k - transition_year)))
                )

        ## Medium range
        transition_year = electric_introduction_year_medium_range + fleet_renewal_duration / 2
        electric_share_limit = 0.02 * electric_final_market_share_medium_range
        electric_share_parameter = np.log(100 / 2 - 1) / (fleet_renewal_duration / 2)
        for k in range(self.historic_start_year, self.end_year + 1):
            if (
                electric_final_market_share_medium_range
                / (1 + np.exp(-electric_share_parameter * (k - transition_year)))
                < electric_share_limit
            ):
                self.df.loc[k, "ask_medium_range_electric_share"] = 0
            else:
                self.df.loc[k, "ask_medium_range_electric_share"] = (
                    electric_final_market_share_medium_range
                    / (1 + np.exp(-electric_share_parameter * (k - transition_year)))
                )

        ## Long range
        transition_year = electric_introduction_year_long_range + fleet_renewal_duration / 2
        electric_share_limit = 0.02 * electric_final_market_share_long_range
        electric_share_parameter = np.log(100 / 2 - 1) / (fleet_renewal_duration / 2)
        for k in range(self.historic_start_year, self.end_year + 1):
            if (
                electric_final_market_share_long_range
                / (1 + np.exp(-electric_share_parameter * (k - transition_year)))
                < electric_share_limit
            ):
                self.df.loc[k, "ask_long_range_electric_share"] = 0
            else:
                self.df.loc[k, "ask_long_range_electric_share"] = (
                    electric_final_market_share_long_range
                    / (1 + np.exp(-electric_share_parameter * (k - transition_year)))
                )

        ask_short_range_electric_share = self.df["ask_short_range_electric_share"]
        ask_medium_range_electric_share = self.df["ask_medium_range_electric_share"]
        ask_long_range_electric_share = self.df["ask_long_range_electric_share"]

        ask_short_range_electric = ask_short_range * ask_short_range_electric_share / 100
        ask_medium_range_electric = ask_medium_range * ask_medium_range_electric_share / 100
        ask_long_range_electric = ask_long_range * ask_long_range_electric_share / 100
        self.df.loc[:, "ask_short_range_electric"] = ask_short_range_electric
        self.df.loc[:, "ask_medium_range_electric"] = ask_medium_range_electric
        self.df.loc[:, "ask_long_range_electric"] = ask_long_range_electric

        # ASK Drop-in fuel

        ask_short_range_dropin_fuel_share = (
            100 - ask_short_range_hydrogen_share - ask_short_range_electric_share
        )
        ask_medium_range_dropin_fuel_share = (
            100 - ask_medium_range_hydrogen_share - ask_medium_range_electric_share
        )
        ask_long_range_dropin_fuel_share = (
            100 - ask_long_range_hydrogen_share - ask_long_range_electric_share
        )
        self.df.loc[:, "ask_short_range_dropin_fuel_share"] = ask_short_range_dropin_fuel_share
        self.df.loc[:, "ask_medium_range_dropin_fuel_share"] = ask_medium_range_dropin_fuel_share
        self.df.loc[:, "ask_long_range_dropin_fuel_share"] = ask_long_range_dropin_fuel_share

        ask_short_range_dropin_fuel = (
            ask_short_range - ask_short_range_hydrogen - ask_short_range_electric
        )
        ask_medium_range_dropin_fuel = (
            ask_medium_range - ask_medium_range_hydrogen - ask_medium_range_electric
        )
        ask_long_range_dropin_fuel = (
            ask_long_range - ask_long_range_hydrogen - ask_long_range_electric
        )
        self.df.loc[:, "ask_short_range_dropin_fuel"] = ask_short_range_dropin_fuel
        self.df.loc[:, "ask_medium_range_dropin_fuel"] = ask_medium_range_dropin_fuel
        self.df.loc[:, "ask_long_range_dropin_fuel"] = ask_long_range_dropin_fuel

        # Total ASK

        ask_dropin_fuel = (
            ask_short_range_dropin_fuel + ask_medium_range_dropin_fuel + ask_long_range_dropin_fuel
        )
        ask_hydrogen = (
            ask_short_range_hydrogen + ask_medium_range_hydrogen + ask_long_range_hydrogen
        )
        ask_electric = (
            ask_short_range_electric + ask_medium_range_electric + ask_long_range_electric
        )

        self.df.loc[:, "ask_dropin_fuel"] = ask_dropin_fuel
        self.df.loc[:, "ask_hydrogen"] = ask_hydrogen
        self.df.loc[:, "ask_electric"] = ask_electric

        return (
            energy_per_ask_without_operations_short_range_dropin_fuel,
            energy_per_ask_without_operations_medium_range_dropin_fuel,
            energy_per_ask_without_operations_long_range_dropin_fuel,
            energy_per_ask_without_operations_short_range_hydrogen,
            energy_per_ask_without_operations_medium_range_hydrogen,
            energy_per_ask_without_operations_long_range_hydrogen,
            energy_per_ask_without_operations_short_range_electric,
            energy_per_ask_without_operations_medium_range_electric,
            energy_per_ask_without_operations_long_range_electric,
            ask_short_range_dropin_fuel_share,
            ask_medium_range_dropin_fuel_share,
            ask_long_range_dropin_fuel_share,
            ask_short_range_hydrogen_share,
            ask_medium_range_hydrogen_share,
            ask_long_range_hydrogen_share,
            ask_short_range_electric_share,
            ask_medium_range_electric_share,
            ask_long_range_electric_share,
            ask_short_range_dropin_fuel,
            ask_medium_range_dropin_fuel,
            ask_long_range_dropin_fuel,
            ask_short_range_hydrogen,
            ask_medium_range_hydrogen,
            ask_long_range_hydrogen,
            ask_short_range_electric,
            ask_medium_range_electric,
            ask_long_range_electric,
            ask_dropin_fuel,
            ask_hydrogen,
            ask_electric,
        )


class PassengerAircraftEfficiencyComplex(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_efficiency_complex", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = None

    def compute(
        self,
        dummy_fleet_model_output: np.ndarray,
        energy_consumption_init: pd.Series,
        ask: pd.Series,
        short_range_energy_share_2019: float,
        medium_range_energy_share_2019: float,
        long_range_energy_share_2019: float,
        short_range_rpk_share_2019: float,
        medium_range_rpk_share_2019: float,
        long_range_rpk_share_2019: float,
        covid_energy_intensity_per_ask_increase_2020: float,
        ask_short_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_long_range: pd.Series,
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
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        ask_short_range_dropin_fuel_share = self.fleet_model.df["Short Range:share:dropin_fuel"]
        ask_medium_range_dropin_fuel_share = self.fleet_model.df["Medium Range:share:dropin_fuel"]
        ask_long_range_dropin_fuel_share = self.fleet_model.df["Long Range:share:dropin_fuel"]
        ask_short_range_hydrogen_share = self.fleet_model.df["Short Range:share:hydrogen"]
        ask_medium_range_hydrogen_share = self.fleet_model.df["Medium Range:share:hydrogen"]
        ask_long_range_hydrogen_share = self.fleet_model.df["Long Range:share:hydrogen"]
        ask_short_range_electric_share = self.fleet_model.df["Short Range:share:electric"]
        ask_medium_range_electric_share = self.fleet_model.df["Medium Range:share:electric"]
        ask_long_range_electric_share = self.fleet_model.df["Long Range:share:electric"]

        energy_per_ask_without_operations_short_range_dropin_fuel = self.fleet_model.df[
            "Short Range:energy_consumption:dropin_fuel"
        ]
        energy_per_ask_without_operations_medium_range_dropin_fuel = self.fleet_model.df[
            "Medium Range:energy_consumption:dropin_fuel"
        ]
        energy_per_ask_without_operations_long_range_dropin_fuel = self.fleet_model.df[
            "Long Range:energy_consumption:dropin_fuel"
        ]
        energy_per_ask_without_operations_short_range_hydrogen = self.fleet_model.df[
            "Short Range:energy_consumption:hydrogen"
        ]
        energy_per_ask_without_operations_medium_range_hydrogen = self.fleet_model.df[
            "Medium Range:energy_consumption:hydrogen"
        ]
        energy_per_ask_without_operations_long_range_hydrogen = self.fleet_model.df[
            "Long Range:energy_consumption:hydrogen"
        ]
        energy_per_ask_without_operations_short_range_electric = self.fleet_model.df[
            "Short Range:energy_consumption:electric"
        ]
        energy_per_ask_without_operations_medium_range_electric = self.fleet_model.df[
            "Medium Range:energy_consumption:electric"
        ]
        energy_per_ask_without_operations_long_range_electric = self.fleet_model.df[
            "Long Range:energy_consumption:electric"
        ]

        """Energy consumption per ASK (without operations) calculation using complex models."""

        # Drop-in - Initialization based on 2019 share - To check for consistency
        energy_consumption_per_ask_init = energy_consumption_init / ask

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_dropin_fuel"] = (
                energy_consumption_per_ask_init.loc[k]
                * short_range_energy_share_2019
                / short_range_rpk_share_2019
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_dropin_fuel"] = (
                energy_consumption_per_ask_init.loc[k]
                * medium_range_energy_share_2019
                / medium_range_rpk_share_2019
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_dropin_fuel"] = (
                energy_consumption_per_ask_init.loc[k]
                * long_range_energy_share_2019
                / long_range_rpk_share_2019
            )
        # Share
        self.df["ask_short_range_dropin_fuel_share"] = 100.0
        self.df["ask_medium_range_dropin_fuel_share"] = 100.0
        self.df["ask_long_range_dropin_fuel_share"] = 100.0

        # Hydrogen initialization
        # Energy consumption
        self.df["energy_per_ask_without_operations_short_range_hydrogen"] = 0.0
        self.df["energy_per_ask_without_operations_medium_range_hydrogen"] = 0.0
        self.df["energy_per_ask_without_operations_long_range_hydrogen"] = 0.0

        # Share
        self.df["ask_short_range_hydrogen_share"] = 0.0
        self.df["ask_medium_range_hydrogen_share"] = 0.0
        self.df["ask_long_range_hydrogen_share"] = 0.0

        # Electric initialization
        # Energy consumption
        self.df["energy_per_ask_without_operations_short_range_electric"] = 0.0
        self.df["energy_per_ask_without_operations_medium_range_electric"] = 0.0
        self.df["energy_per_ask_without_operations_long_range_electric"] = 0.0

        # Share
        self.df["ask_short_range_electric_share"] = 0.0
        self.df["ask_medium_range_electric_share"] = 0.0
        self.df["ask_long_range_electric_share"] = 0.0

        # Hybrid-electric initialization
        # Energy consumption
        self.df["energy_per_ask_without_operations_short_range_hybrid_electric"] = 0.0
        self.df["energy_per_ask_without_operations_medium_range_hybrid_electric"] = 0.0
        self.df["energy_per_ask_without_operations_long_range_hybrid_electric"] = 0.0

        # Share
        self.df["ask_short_range_hybrid_electric_share"] = 0.0
        self.df["ask_medium_range_hybrid_electric_share"] = 0.0
        self.df["ask_long_range_hybrid_electric_share"] = 0.0

        # Drop-in - Projections
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_dropin_fuel"] = (
                energy_per_ask_without_operations_short_range_dropin_fuel.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_dropin_fuel"] = (
                energy_per_ask_without_operations_medium_range_dropin_fuel.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_dropin_fuel"] = (
                energy_per_ask_without_operations_long_range_dropin_fuel.loc[k]
            )

        self.df.loc[2020, "energy_per_ask_without_operations_short_range_dropin_fuel"] = (
            self.df.loc[2019, "energy_per_ask_without_operations_short_range_dropin_fuel"]
            * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)
        )
        self.df.loc[2020, "energy_per_ask_without_operations_medium_range_dropin_fuel"] = (
            self.df.loc[2019, "energy_per_ask_without_operations_medium_range_dropin_fuel"]
            * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)
        )
        self.df.loc[2020, "energy_per_ask_without_operations_long_range_dropin_fuel"] = self.df.loc[
            2019, "energy_per_ask_without_operations_long_range_dropin_fuel"
        ] * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)

        energy_per_ask_without_operations_short_range_dropin_fuel = self.df[
            "energy_per_ask_without_operations_short_range_dropin_fuel"
        ]
        energy_per_ask_without_operations_medium_range_dropin_fuel = self.df[
            "energy_per_ask_without_operations_medium_range_dropin_fuel"
        ]
        energy_per_ask_without_operations_long_range_dropin_fuel = self.df[
            "energy_per_ask_without_operations_long_range_dropin_fuel"
        ]

        # Hydrogen
        for k in range(self.prospection_start_year + 1, self.end_year + 1):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_hydrogen"] = (
                energy_per_ask_without_operations_short_range_hydrogen.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_hydrogen"] = (
                energy_per_ask_without_operations_medium_range_hydrogen.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_hydrogen"] = (
                energy_per_ask_without_operations_long_range_hydrogen.loc[k]
            )

        energy_per_ask_without_operations_short_range_hydrogen = self.df[
            "energy_per_ask_without_operations_short_range_hydrogen"
        ]
        energy_per_ask_without_operations_medium_range_hydrogen = self.df[
            "energy_per_ask_without_operations_medium_range_hydrogen"
        ]
        energy_per_ask_without_operations_long_range_hydrogen = self.df[
            "energy_per_ask_without_operations_long_range_hydrogen"
        ]

        # Electric
        for k in range(self.prospection_start_year + 1, self.end_year + 1):
            self.df.loc[k, "energy_per_ask_without_operations_short_range_electric"] = (
                energy_per_ask_without_operations_short_range_electric.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_medium_range_electric"] = (
                energy_per_ask_without_operations_medium_range_electric.loc[k]
            )
            self.df.loc[k, "energy_per_ask_without_operations_long_range_electric"] = (
                energy_per_ask_without_operations_long_range_electric.loc[k]
            )

        energy_per_ask_without_operations_short_range_electric = self.df[
            "energy_per_ask_without_operations_short_range_electric"
        ]
        energy_per_ask_without_operations_medium_range_electric = self.df[
            "energy_per_ask_without_operations_medium_range_electric"
        ]
        energy_per_ask_without_operations_long_range_electric = self.df[
            "energy_per_ask_without_operations_long_range_electric"
        ]

        # Share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_short_range_dropin_fuel_share"
        ] = ask_short_range_dropin_fuel_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_medium_range_dropin_fuel_share"
        ] = ask_medium_range_dropin_fuel_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_long_range_dropin_fuel_share"
        ] = ask_long_range_dropin_fuel_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_short_range_hydrogen_share"
        ] = ask_short_range_hydrogen_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_medium_range_hydrogen_share"
        ] = ask_medium_range_hydrogen_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_long_range_hydrogen_share"
        ] = ask_long_range_hydrogen_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_short_range_electric_share"
        ] = ask_short_range_electric_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_medium_range_electric_share"
        ] = ask_medium_range_electric_share
        self.df.loc[
            self.prospection_start_year : self.end_year + 1, "ask_long_range_electric_share"
        ] = ask_long_range_electric_share
        # ASK
        ask_short_range_dropin_fuel = (
            ask_short_range * self.df["ask_short_range_dropin_fuel_share"] / 100
        )
        ask_medium_range_dropin_fuel = (
            ask_medium_range * self.df["ask_medium_range_dropin_fuel_share"] / 100
        )
        ask_long_range_dropin_fuel = (
            ask_long_range * self.df["ask_long_range_dropin_fuel_share"] / 100
        )
        ask_short_range_hydrogen = ask_short_range * self.df["ask_short_range_hydrogen_share"] / 100
        ask_medium_range_hydrogen = (
            ask_medium_range * self.df["ask_medium_range_hydrogen_share"] / 100
        )
        ask_long_range_hydrogen = ask_long_range * self.df["ask_long_range_hydrogen_share"] / 100
        ask_short_range_electric = ask_short_range * self.df["ask_short_range_electric_share"] / 100
        ask_medium_range_electric = (
            ask_medium_range * self.df["ask_medium_range_electric_share"] / 100
        )
        ask_long_range_electric = ask_long_range * self.df["ask_long_range_electric_share"] / 100

        self.df.loc[:, "ask_short_range_dropin_fuel"] = ask_short_range_dropin_fuel
        self.df.loc[:, "ask_medium_range_dropin_fuel"] = ask_medium_range_dropin_fuel
        self.df.loc[:, "ask_long_range_dropin_fuel"] = ask_long_range_dropin_fuel
        self.df.loc[:, "ask_short_range_hydrogen"] = ask_short_range_hydrogen
        self.df.loc[:, "ask_medium_range_hydrogen"] = ask_medium_range_hydrogen
        self.df.loc[:, "ask_long_range_hydrogen"] = ask_long_range_hydrogen
        self.df.loc[:, "ask_short_range_electric"] = ask_short_range_electric
        self.df.loc[:, "ask_medium_range_electric"] = ask_medium_range_electric
        self.df.loc[:, "ask_long_range_electric"] = ask_long_range_electric

        ask_dropin_fuel = (
            ask_short_range_dropin_fuel + ask_medium_range_dropin_fuel + ask_long_range_dropin_fuel
        )
        ask_hydrogen = (
            ask_short_range_hydrogen + ask_medium_range_hydrogen + ask_long_range_hydrogen
        )
        ask_electric = (
            ask_short_range_electric + ask_medium_range_electric + ask_long_range_electric
        )

        self.df.loc[:, "ask_dropin_fuel"] = ask_dropin_fuel
        self.df.loc[:, "ask_hydrogen"] = ask_hydrogen
        self.df.loc[:, "ask_electric"] = ask_electric

        return (
            energy_per_ask_without_operations_short_range_dropin_fuel,
            energy_per_ask_without_operations_medium_range_dropin_fuel,
            energy_per_ask_without_operations_long_range_dropin_fuel,
            energy_per_ask_without_operations_short_range_hydrogen,
            energy_per_ask_without_operations_medium_range_hydrogen,
            energy_per_ask_without_operations_long_range_hydrogen,
            energy_per_ask_without_operations_short_range_electric,
            energy_per_ask_without_operations_medium_range_electric,
            energy_per_ask_without_operations_long_range_electric,
            ask_short_range_dropin_fuel_share,
            ask_medium_range_dropin_fuel_share,
            ask_long_range_dropin_fuel_share,
            ask_short_range_hydrogen_share,
            ask_medium_range_hydrogen_share,
            ask_long_range_hydrogen_share,
            ask_short_range_electric_share,
            ask_medium_range_electric_share,
            ask_long_range_electric_share,
            ask_short_range_dropin_fuel,
            ask_medium_range_dropin_fuel,
            ask_long_range_dropin_fuel,
            ask_short_range_hydrogen,
            ask_medium_range_hydrogen,
            ask_long_range_hydrogen,
            ask_short_range_electric,
            ask_medium_range_electric,
            ask_long_range_electric,
            ask_dropin_fuel,
            ask_hydrogen,
            ask_electric,
        )


class FreightAircraftEfficiency(AeroMAPSModel):
    def __init__(self, name="freight_aircraft_efficiency", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_init: pd.Series,
        rtk: pd.Series,
        freight_energy_share_2019: float,
        energy_per_ask_without_operations_short_range_dropin_fuel: pd.Series,
        energy_per_ask_without_operations_medium_range_dropin_fuel: pd.Series,
        energy_per_ask_without_operations_long_range_dropin_fuel: pd.Series,
        energy_per_ask_without_operations_short_range_hydrogen: pd.Series,
        energy_per_ask_without_operations_medium_range_hydrogen: pd.Series,
        energy_per_ask_without_operations_long_range_hydrogen: pd.Series,
        energy_per_ask_without_operations_short_range_electric: pd.Series,
        energy_per_ask_without_operations_medium_range_electric: pd.Series,
        energy_per_ask_without_operations_long_range_electric: pd.Series,
        ask: pd.Series,
        ask_short_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_long_range: pd.Series,
        ask_short_range_dropin_fuel: pd.Series,
        ask_medium_range_dropin_fuel: pd.Series,
        ask_long_range_dropin_fuel: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_long_range_hydrogen_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        covid_energy_intensity_per_ask_increase_2020: float,
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
    ]:
        """Energy consumption per RTK (without operations) calculation."""

        # Initialization based on 2019 share: to correct to include load factor
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "energy_per_rtk_without_operations_freight_dropin_fuel"] = (
                energy_consumption_init.loc[k] / rtk.loc[k] * freight_energy_share_2019 / 100
            )

        # Projections
        energy_per_rtk_without_operations_freight_dropin_fuel_short_range_k = self.df.loc[
            2019, "energy_per_rtk_without_operations_freight_dropin_fuel"
        ]
        energy_per_rtk_without_operations_freight_dropin_fuel_medium_range_k = self.df.loc[
            2019, "energy_per_rtk_without_operations_freight_dropin_fuel"
        ]
        energy_per_rtk_without_operations_freight_dropin_fuel_long_range_k = self.df.loc[
            2019, "energy_per_rtk_without_operations_freight_dropin_fuel"
        ]
        for k in range(self.prospection_start_year, self.end_year + 1):
            energy_per_rtk_without_operations_freight_dropin_fuel_short_range_k = (
                energy_per_rtk_without_operations_freight_dropin_fuel_short_range_k
                * energy_per_ask_without_operations_short_range_dropin_fuel.loc[k]
                / energy_per_ask_without_operations_short_range_dropin_fuel.loc[k - 1]
            )
            energy_per_rtk_without_operations_freight_dropin_fuel_medium_range_k = (
                energy_per_rtk_without_operations_freight_dropin_fuel_medium_range_k
                * energy_per_ask_without_operations_medium_range_dropin_fuel.loc[k]
                / energy_per_ask_without_operations_medium_range_dropin_fuel.loc[k - 1]
            )
            energy_per_rtk_without_operations_freight_dropin_fuel_long_range_k = (
                energy_per_rtk_without_operations_freight_dropin_fuel_long_range_k
                * energy_per_ask_without_operations_long_range_dropin_fuel.loc[k]
                / energy_per_ask_without_operations_long_range_dropin_fuel.loc[k - 1]
            )
            self.df.loc[k, "energy_per_rtk_without_operations_freight_dropin_fuel"] = (
                energy_per_rtk_without_operations_freight_dropin_fuel_short_range_k
                * ask_short_range_dropin_fuel.loc[k]
                / (
                    ask_short_range_dropin_fuel.loc[k]
                    + ask_medium_range_dropin_fuel.loc[k]
                    + ask_long_range_dropin_fuel.loc[k]
                )
                + energy_per_rtk_without_operations_freight_dropin_fuel_medium_range_k
                * ask_medium_range_dropin_fuel.loc[k]
                / (
                    ask_short_range_dropin_fuel.loc[k]
                    + ask_medium_range_dropin_fuel.loc[k]
                    + ask_long_range_dropin_fuel.loc[k]
                )
                + energy_per_rtk_without_operations_freight_dropin_fuel_long_range_k
                * ask_long_range_dropin_fuel.loc[k]
                / (
                    ask_short_range_dropin_fuel.loc[k]
                    + ask_medium_range_dropin_fuel.loc[k]
                    + ask_long_range_dropin_fuel.loc[k]
                )
            )

        # Covid
        self.df.loc[2020, "energy_per_rtk_without_operations_freight_dropin_fuel"] = self.df.loc[
            2019, "energy_per_rtk_without_operations_freight_dropin_fuel"
        ] * (1 + covid_energy_intensity_per_ask_increase_2020 / 100)

        energy_per_rtk_without_operations_freight_dropin_fuel = self.df[
            "energy_per_rtk_without_operations_freight_dropin_fuel"
        ]

        rtk_hydrogen_share = (
            ask_short_range_hydrogen_share * (ask_short_range / ask)
            + ask_medium_range_hydrogen_share * (ask_medium_range / ask)
            + ask_long_range_hydrogen_share * (ask_long_range / ask)
        )
        rtk_electric_share = (
            ask_short_range_electric_share * (ask_short_range / ask)
            + ask_medium_range_electric_share * (ask_medium_range / ask)
            + ask_long_range_electric_share * (ask_long_range / ask)
        )
        rtk_dropin_fuel_share = 100 - rtk_hydrogen_share - rtk_electric_share
        self.df.loc[:, "rtk_hydrogen_share"] = rtk_hydrogen_share
        self.df.loc[:, "rtk_dropin_fuel_share"] = rtk_dropin_fuel_share

        rtk_hydrogen = rtk * rtk_hydrogen_share / 100
        rtk_electric = rtk * rtk_electric_share / 100
        rtk_dropin_fuel = rtk * rtk_dropin_fuel_share / 100
        self.df.loc[:, "rtk_hydrogen"] = rtk_hydrogen
        self.df.loc[:, "rtk_dropin_fuel"] = rtk_dropin_fuel

        relative_energy_per_ask_hydrogen_wrt_dropin_short_range = (
            energy_per_ask_without_operations_short_range_hydrogen
            / energy_per_ask_without_operations_short_range_dropin_fuel
        )
        relative_energy_per_ask_hydrogen_wrt_dropin_medium_range = (
            energy_per_ask_without_operations_medium_range_hydrogen
            / energy_per_ask_without_operations_medium_range_dropin_fuel
        )
        relative_energy_per_ask_hydrogen_wrt_dropin_long_range = (
            energy_per_ask_without_operations_long_range_hydrogen
            / energy_per_ask_without_operations_long_range_dropin_fuel
        )

        relative_energy_per_ask_electric_wrt_dropin_short_range = (
            energy_per_ask_without_operations_short_range_electric
            / energy_per_ask_without_operations_short_range_dropin_fuel
        )
        relative_energy_per_ask_electric_wrt_dropin_medium_range = (
            energy_per_ask_without_operations_medium_range_electric
            / energy_per_ask_without_operations_medium_range_dropin_fuel
        )
        relative_energy_per_ask_electric_wrt_dropin_long_range = (
            energy_per_ask_without_operations_long_range_electric
            / energy_per_ask_without_operations_long_range_dropin_fuel
        )

        for k in range(self.historic_start_year, self.end_year + 1):
            if rtk_hydrogen_share.loc[k] == 0:
                self.df.loc[k, "energy_per_rtk_without_operations_freight_hydrogen"] = self.df.loc[
                    k, "energy_per_rtk_without_operations_freight_dropin_fuel"
                ]
            else:
                self.df.loc[k, "energy_per_rtk_without_operations_freight_hydrogen"] = (
                    energy_per_rtk_without_operations_freight_dropin_fuel.loc[k]
                    * (
                        relative_energy_per_ask_hydrogen_wrt_dropin_short_range.loc[k]
                        * ask_short_range_hydrogen_share.loc[k]
                        * (ask_short_range.loc[k] / ask.loc[k])
                        / rtk_hydrogen_share.loc[k]
                        + relative_energy_per_ask_hydrogen_wrt_dropin_medium_range.loc[k]
                        * ask_medium_range_hydrogen_share.loc[k]
                        * (ask_medium_range.loc[k] / ask.loc[k])
                        / rtk_hydrogen_share.loc[k]
                        + relative_energy_per_ask_hydrogen_wrt_dropin_long_range.loc[k]
                        * ask_long_range_hydrogen_share.loc[k]
                        * (ask_long_range.loc[k] / ask.loc[k])
                        / rtk_hydrogen_share.loc[k]
                    )
                )

            if rtk_electric_share.loc[k] == 0:
                self.df.loc[k, "energy_per_rtk_without_operations_freight_electric"] = self.df.loc[
                    k, "energy_per_rtk_without_operations_freight_dropin_fuel"
                ]
            else:
                self.df.loc[k, "energy_per_rtk_without_operations_freight_electric"] = (
                    energy_per_rtk_without_operations_freight_dropin_fuel.loc[k]
                    * (
                        relative_energy_per_ask_electric_wrt_dropin_short_range.loc[k]
                        * ask_short_range_electric_share.loc[k]
                        * (ask_short_range.loc[k] / ask.loc[k])
                        / rtk_electric_share.loc[k]
                        + relative_energy_per_ask_electric_wrt_dropin_medium_range.loc[k]
                        * ask_medium_range_electric_share.loc[k]
                        * (ask_medium_range.loc[k] / ask.loc[k])
                        / rtk_electric_share.loc[k]
                        + relative_energy_per_ask_electric_wrt_dropin_long_range.loc[k]
                        * ask_long_range_electric_share.loc[k]
                        * (ask_long_range.loc[k] / ask.loc[k])
                        / rtk_electric_share.loc[k]
                    )
                )

        energy_per_rtk_without_operations_freight_hydrogen = self.df[
            "energy_per_rtk_without_operations_freight_hydrogen"
        ]
        energy_per_rtk_without_operations_freight_electric = self.df[
            "energy_per_rtk_without_operations_freight_electric"
        ]

        return (
            energy_per_rtk_without_operations_freight_dropin_fuel,
            energy_per_rtk_without_operations_freight_hydrogen,
            energy_per_rtk_without_operations_freight_electric,
            rtk_dropin_fuel_share,
            rtk_hydrogen_share,
            rtk_electric_share,
            rtk_dropin_fuel,
            rtk_hydrogen,
            rtk_electric,
        )

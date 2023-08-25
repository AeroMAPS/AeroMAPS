from typing import Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeromapsModel



class PassengerAircraftDOCComplex(AeromapsModel):
    def __init__(
        self, name="passenger_aircraft_doc_complex", fleet_model=None, *args, **kwargs
    ):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = fleet_model

    def compute(
        self,
        energy_consumption_init: pd.Series = pd.Series(dtype="float64"),
        ask: pd.Series = pd.Series(dtype="float64"),
        short_range_energy_share_2019: float = 0.0,
        medium_range_energy_share_2019: float = 0.0,
        long_range_energy_share_2019: float = 0.0,
        short_range_rpk_share_2019: float = 0.0,
        medium_range_rpk_share_2019: float = 0.0,
        long_range_rpk_share_2019: float = 0.0,
        covid_energy_intensity_per_ask_increase_2020: float = 0.0,
        ask_short_range: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range: pd.Series = pd.Series(dtype="float64"),
        ask_long_range: pd.Series = pd.Series(dtype="float64"),
        # ask_short_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        # ask_medium_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        # ask_long_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        # ask_short_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        # ask_medium_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        # ask_long_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        # energy_per_ask_without_operations_short_range_dropin_fuel: pd.Series = pd.Series(
        #     dtype="float64"
        # ),
        # energy_per_ask_without_operations_medium_range_dropin_fuel: pd.Series = pd.Series(
        #     dtype="float64"
        # ),
        # energy_per_ask_without_operations_long_range_dropin_fuel: pd.Series = pd.Series(
        #     dtype="float64"
        # ),
        # energy_per_ask_without_operations_short_range_hydrogen: pd.Series = pd.Series(
        #     dtype="float64"
        # ),
        # energy_per_ask_without_operations_medium_range_hydrogen: pd.Series = pd.Series(
        #     dtype="float64"
        # ),
        # energy_per_ask_without_operations_long_range_hydrogen: pd.Series = pd.Series(
        #     dtype="float64"
        # ),
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
    ]:
        ask_short_range_dropin_fuel_share = self.fleet_model.df["Short Range:share:dropin_fuel"]
        ask_medium_range_dropin_fuel_share = self.fleet_model.df["Medium Range:share:dropin_fuel"]
        ask_long_range_dropin_fuel_share = self.fleet_model.df["Long Range:share:dropin_fuel"]
        ask_short_range_hydrogen_share = self.fleet_model.df["Short Range:share:hydrogen"]
        ask_medium_range_hydrogen_share = self.fleet_model.df["Medium Range:share:hydrogen"]
        ask_long_range_hydrogen_share = self.fleet_model.df["Long Range:share:hydrogen"]

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

        """Energy consumption per ASK (without operations) calculation using simple models."""

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

        # Drop-in - Projections
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[
                k, "energy_per_ask_without_operations_short_range_dropin_fuel"
            ] = energy_per_ask_without_operations_short_range_dropin_fuel.loc[k]
            self.df.loc[
                k, "energy_per_ask_without_operations_medium_range_dropin_fuel"
            ] = energy_per_ask_without_operations_medium_range_dropin_fuel.loc[k]
            self.df.loc[
                k, "energy_per_ask_without_operations_long_range_dropin_fuel"
            ] = energy_per_ask_without_operations_long_range_dropin_fuel.loc[k]

        self.df.loc[
            2020, "energy_per_ask_without_operations_short_range_dropin_fuel"
        ] = self.df.loc[2020, "energy_per_ask_without_operations_short_range_dropin_fuel"] * (
            1 + covid_energy_intensity_per_ask_increase_2020 / 100
        )
        self.df.loc[
            2020, "energy_per_ask_without_operations_medium_range_dropin_fuel"
        ] = self.df.loc[2020, "energy_per_ask_without_operations_medium_range_dropin_fuel"] * (
            1 + covid_energy_intensity_per_ask_increase_2020 / 100
        )
        self.df.loc[2020, "energy_per_ask_without_operations_long_range_dropin_fuel"] = self.df.loc[
            2020, "energy_per_ask_without_operations_long_range_dropin_fuel"
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
            self.df.loc[
                k, "energy_per_ask_without_operations_short_range_hydrogen"
            ] = energy_per_ask_without_operations_short_range_hydrogen.loc[k]
            self.df.loc[
                k, "energy_per_ask_without_operations_medium_range_hydrogen"
            ] = energy_per_ask_without_operations_medium_range_hydrogen.loc[k]
            self.df.loc[
                k, "energy_per_ask_without_operations_long_range_hydrogen"
            ] = energy_per_ask_without_operations_long_range_hydrogen.loc[k]

        energy_per_ask_without_operations_short_range_hydrogen = self.df[
            "energy_per_ask_without_operations_short_range_hydrogen"
        ]
        energy_per_ask_without_operations_medium_range_hydrogen = self.df[
            "energy_per_ask_without_operations_medium_range_hydrogen"
        ]
        energy_per_ask_without_operations_long_range_hydrogen = self.df[
            "energy_per_ask_without_operations_long_range_hydrogen"
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

        self.df.loc[:, "ask_short_range_dropin_fuel"] = ask_short_range_dropin_fuel
        self.df.loc[:, "ask_medium_range_dropin_fuel"] = ask_medium_range_dropin_fuel
        self.df.loc[:, "ask_long_range_dropin_fuel"] = ask_long_range_dropin_fuel
        self.df.loc[:, "ask_short_range_hydrogen"] = ask_short_range_hydrogen
        self.df.loc[:, "ask_medium_range_hydrogen"] = ask_medium_range_hydrogen
        self.df.loc[:, "ask_long_range_hydrogen"] = ask_long_range_hydrogen

        return (
            energy_per_ask_without_operations_short_range_dropin_fuel,
            energy_per_ask_without_operations_medium_range_dropin_fuel,
            energy_per_ask_without_operations_long_range_dropin_fuel,
            energy_per_ask_without_operations_short_range_hydrogen,
            energy_per_ask_without_operations_medium_range_hydrogen,
            energy_per_ask_without_operations_long_range_hydrogen,
            ask_short_range_dropin_fuel_share,
            ask_medium_range_dropin_fuel_share,
            ask_long_range_dropin_fuel_share,
            ask_short_range_hydrogen_share,
            ask_medium_range_hydrogen_share,
            ask_long_range_hydrogen_share,
            ask_short_range_dropin_fuel,
            ask_medium_range_dropin_fuel,
            ask_long_range_dropin_fuel,
            ask_short_range_hydrogen,
            ask_medium_range_hydrogen,
            ask_long_range_hydrogen,
        )

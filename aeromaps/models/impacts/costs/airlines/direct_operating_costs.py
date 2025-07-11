from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class PassengerAircraftDocNonEnergyComplex(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_doc_non_energy_complex", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = None

    def compute(
        self,
        ask_long_range_hydrogen_share: pd.Series,
        ask_long_range_dropin_fuel_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_medium_range_dropin_fuel_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_short_range_dropin_fuel_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_long_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_short_range: pd.Series,
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
        doc_non_energy_per_ask_short_range_dropin_fuel = self.fleet_model.df[
            "Short Range:doc_non_energy:dropin_fuel"
        ]
        doc_non_energy_per_ask_medium_range_dropin_fuel = self.fleet_model.df[
            "Medium Range:doc_non_energy:dropin_fuel"
        ]
        doc_non_energy_per_ask_long_range_dropin_fuel = self.fleet_model.df[
            "Long Range:doc_non_energy:dropin_fuel"
        ]
        doc_non_energy_per_ask_short_range_hydrogen = self.fleet_model.df[
            "Short Range:doc_non_energy:hydrogen"
        ]
        doc_non_energy_per_ask_medium_range_hydrogen = self.fleet_model.df[
            "Medium Range:doc_non_energy:hydrogen"
        ]
        doc_non_energy_per_ask_long_range_hydrogen = self.fleet_model.df[
            "Long Range:doc_non_energy:hydrogen"
        ]
        doc_non_energy_per_ask_short_range_electric = self.fleet_model.df[
            "Short Range:doc_non_energy:electric"
        ]
        doc_non_energy_per_ask_medium_range_electric = self.fleet_model.df[
            "Medium Range:doc_non_energy:electric"
        ]
        doc_non_energy_per_ask_long_range_electric = self.fleet_model.df[
            "Long Range:doc_non_energy:electric"
        ]

        # Drop-in - Projections

        self.df.loc[:, "doc_non_energy_per_ask_short_range_dropin_fuel"] = (
            doc_non_energy_per_ask_short_range_dropin_fuel
        )
        self.df.loc[:, "doc_non_energy_per_ask_medium_range_dropin_fuel"] = (
            doc_non_energy_per_ask_medium_range_dropin_fuel
        )
        self.df.loc[:, "doc_non_energy_per_ask_long_range_dropin_fuel"] = (
            doc_non_energy_per_ask_long_range_dropin_fuel
        )

        # Hydrogen
        self.df.loc[:, "doc_non_energy_per_ask_short_range_hydrogen"] = (
            doc_non_energy_per_ask_short_range_hydrogen
        )
        self.df.loc[:, "doc_non_energy_per_ask_medium_range_hydrogen"] = (
            doc_non_energy_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "doc_non_energy_per_ask_long_range_hydrogen"] = (
            doc_non_energy_per_ask_long_range_hydrogen
        )

        # Electric
        self.df.loc[:, "doc_non_energy_per_ask_short_range_electric"] = (
            doc_non_energy_per_ask_short_range_electric
        )
        self.df.loc[:, "doc_non_energy_per_ask_medium_range_electric"] = (
            doc_non_energy_per_ask_medium_range_electric
        )
        self.df.loc[:, "doc_non_energy_per_ask_long_range_electric"] = (
            doc_non_energy_per_ask_long_range_electric
        )

        doc_non_energy_per_ask_long_range_mean = (
            doc_non_energy_per_ask_long_range_hydrogen * ask_long_range_hydrogen_share / 100
            + doc_non_energy_per_ask_long_range_dropin_fuel * ask_long_range_dropin_fuel_share / 100
            + doc_non_energy_per_ask_long_range_electric * ask_long_range_electric_share / 100
        )

        doc_non_energy_per_ask_medium_range_mean = (
            doc_non_energy_per_ask_medium_range_hydrogen * ask_medium_range_hydrogen_share / 100
            + doc_non_energy_per_ask_medium_range_dropin_fuel
            * ask_medium_range_dropin_fuel_share
            / 100
            + doc_non_energy_per_ask_medium_range_electric * ask_medium_range_electric_share / 100
        )

        doc_non_energy_per_ask_short_range_mean = (
            doc_non_energy_per_ask_short_range_hydrogen * ask_short_range_hydrogen_share / 100
            + doc_non_energy_per_ask_short_range_dropin_fuel
            * ask_short_range_dropin_fuel_share
            / 100
            + doc_non_energy_per_ask_short_range_electric * ask_short_range_electric_share / 100
        )

        doc_non_energy_per_ask_mean = (
            doc_non_energy_per_ask_long_range_mean * ask_long_range
            + doc_non_energy_per_ask_medium_range_mean * ask_medium_range
            + doc_non_energy_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        self.df.loc[:, "doc_non_energy_per_ask_long_range_mean"] = (
            doc_non_energy_per_ask_long_range_mean
        )

        self.df.loc[:, "doc_non_energy_per_ask_medium_range_mean"] = (
            doc_non_energy_per_ask_medium_range_mean
        )

        self.df.loc[:, "doc_non_energy_per_ask_short_range_mean"] = (
            doc_non_energy_per_ask_short_range_mean
        )

        self.df.loc[:, "doc_non_energy_per_ask_mean"] = doc_non_energy_per_ask_mean

        return (
            doc_non_energy_per_ask_short_range_dropin_fuel,
            doc_non_energy_per_ask_medium_range_dropin_fuel,
            doc_non_energy_per_ask_long_range_dropin_fuel,
            doc_non_energy_per_ask_short_range_hydrogen,
            doc_non_energy_per_ask_medium_range_hydrogen,
            doc_non_energy_per_ask_long_range_hydrogen,
            doc_non_energy_per_ask_short_range_electric,
            doc_non_energy_per_ask_medium_range_electric,
            doc_non_energy_per_ask_long_range_electric,
            doc_non_energy_per_ask_short_range_mean,
            doc_non_energy_per_ask_medium_range_mean,
            doc_non_energy_per_ask_long_range_mean,
            doc_non_energy_per_ask_mean,
        )


class PassengerAircraftDocNonEnergySimple(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_doc_non_energy_simple", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        doc_non_energy_per_ask_short_range_dropin_fuel_init: float,
        doc_non_energy_per_ask_medium_range_dropin_fuel_init: float,
        doc_non_energy_per_ask_long_range_dropin_fuel_init: float,
        doc_non_energy_per_ask_short_range_dropin_fuel_gain: float,
        doc_non_energy_per_ask_medium_range_dropin_fuel_gain: float,
        doc_non_energy_per_ask_long_range_dropin_fuel_gain: float,
        relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_short_range: float,
        relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_medium_range: float,
        relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_long_range: float,
        relative_doc_non_energy_per_ask_electric_wrt_dropin_short_range: float,
        relative_doc_non_energy_per_ask_electric_wrt_dropin_medium_range: float,
        relative_doc_non_energy_per_ask_electric_wrt_dropin_long_range: float,
        ask_long_range_hydrogen_share: pd.Series,
        ask_long_range_dropin_fuel_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_medium_range_dropin_fuel_share: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_short_range_dropin_fuel_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_long_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_short_range: pd.Series,
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
        """DOC (without energy DOC) per ASK calculation using simple models."""

        # Initialization based on 2019 values

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "doc_non_energy_per_ask_short_range_dropin_fuel"] = (
                doc_non_energy_per_ask_short_range_dropin_fuel_init
            )
            self.df.loc[k, "doc_non_energy_per_ask_medium_range_dropin_fuel"] = (
                doc_non_energy_per_ask_medium_range_dropin_fuel_init
            )
            self.df.loc[k, "doc_non_energy_per_ask_long_range_dropin_fuel"] = (
                doc_non_energy_per_ask_long_range_dropin_fuel_init
            )

        # Projections

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "doc_non_energy_per_ask_short_range_dropin_fuel"] = self.df.loc[
                k - 1, "doc_non_energy_per_ask_short_range_dropin_fuel"
            ] * (1 - doc_non_energy_per_ask_short_range_dropin_fuel_gain / 100)
            self.df.loc[k, "doc_non_energy_per_ask_medium_range_dropin_fuel"] = self.df.loc[
                k - 1, "doc_non_energy_per_ask_medium_range_dropin_fuel"
            ] * (1 - doc_non_energy_per_ask_medium_range_dropin_fuel_gain / 100)
            self.df.loc[k, "doc_non_energy_per_ask_long_range_dropin_fuel"] = self.df.loc[
                k - 1, "doc_non_energy_per_ask_long_range_dropin_fuel"
            ] * (1 - doc_non_energy_per_ask_long_range_dropin_fuel_gain / 100)

        doc_non_energy_per_ask_short_range_dropin_fuel = self.df[
            "doc_non_energy_per_ask_short_range_dropin_fuel"
        ]
        doc_non_energy_per_ask_medium_range_dropin_fuel = self.df[
            "doc_non_energy_per_ask_medium_range_dropin_fuel"
        ]
        doc_non_energy_per_ask_long_range_dropin_fuel = self.df[
            "doc_non_energy_per_ask_long_range_dropin_fuel"
        ]

        # Hydrogen

        doc_non_energy_per_ask_short_range_hydrogen = (
            doc_non_energy_per_ask_short_range_dropin_fuel
            * relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_short_range
        )
        doc_non_energy_per_ask_medium_range_hydrogen = (
            doc_non_energy_per_ask_medium_range_dropin_fuel
            * relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_medium_range
        )
        doc_non_energy_per_ask_long_range_hydrogen = (
            doc_non_energy_per_ask_long_range_dropin_fuel
            * relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_long_range
        )

        self.df.loc[:, "doc_non_energy_per_ask_short_range_hydrogen"] = (
            doc_non_energy_per_ask_short_range_hydrogen
        )
        self.df.loc[:, "doc_non_energy_per_ask_medium_range_hydrogen"] = (
            doc_non_energy_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "doc_non_energy_per_ask_long_range_hydrogen"] = (
            doc_non_energy_per_ask_long_range_hydrogen
        )

        # Electric
        doc_non_energy_per_ask_short_range_electric = (
            doc_non_energy_per_ask_short_range_dropin_fuel
            * relative_doc_non_energy_per_ask_electric_wrt_dropin_short_range
        )
        doc_non_energy_per_ask_medium_range_electric = (
            doc_non_energy_per_ask_medium_range_dropin_fuel
            * relative_doc_non_energy_per_ask_electric_wrt_dropin_medium_range
        )
        doc_non_energy_per_ask_long_range_electric = (
            doc_non_energy_per_ask_long_range_dropin_fuel
            * relative_doc_non_energy_per_ask_electric_wrt_dropin_long_range
        )

        self.df.loc[:, "doc_non_energy_per_ask_short_range_electric"] = (
            doc_non_energy_per_ask_short_range_electric
        )
        self.df.loc[:, "doc_non_energy_per_ask_medium_range_electric"] = (
            doc_non_energy_per_ask_medium_range_electric
        )
        self.df.loc[:, "doc_non_energy_per_ask_long_range_electric"] = (
            doc_non_energy_per_ask_long_range_electric
        )

        doc_non_energy_per_ask_long_range_mean = (
            doc_non_energy_per_ask_long_range_hydrogen * ask_long_range_hydrogen_share / 100
            + doc_non_energy_per_ask_long_range_dropin_fuel * ask_long_range_dropin_fuel_share / 100
            + doc_non_energy_per_ask_long_range_electric * ask_long_range_electric_share / 100
        )

        doc_non_energy_per_ask_medium_range_mean = (
            doc_non_energy_per_ask_medium_range_hydrogen * ask_medium_range_hydrogen_share / 100
            + doc_non_energy_per_ask_medium_range_dropin_fuel
            * ask_medium_range_dropin_fuel_share
            / 100
            + doc_non_energy_per_ask_medium_range_electric * ask_medium_range_electric_share / 100
        )

        doc_non_energy_per_ask_short_range_mean = (
            doc_non_energy_per_ask_short_range_hydrogen * ask_short_range_hydrogen_share / 100
            + doc_non_energy_per_ask_short_range_dropin_fuel
            * ask_short_range_dropin_fuel_share
            / 100
            + doc_non_energy_per_ask_short_range_electric * ask_short_range_electric_share / 100
        )

        doc_non_energy_per_ask_mean = (
            doc_non_energy_per_ask_long_range_mean * ask_long_range
            + doc_non_energy_per_ask_medium_range_mean * ask_medium_range
            + doc_non_energy_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        self.df.loc[:, "doc_non_energy_per_ask_long_range_mean"] = (
            doc_non_energy_per_ask_long_range_mean
        )

        self.df.loc[:, "doc_non_energy_per_ask_medium_range_mean"] = (
            doc_non_energy_per_ask_medium_range_mean
        )

        self.df.loc[:, "doc_non_energy_per_ask_short_range_mean"] = (
            doc_non_energy_per_ask_short_range_mean
        )

        self.df.loc[:, "doc_non_energy_per_ask_mean"] = doc_non_energy_per_ask_mean

        return (
            doc_non_energy_per_ask_short_range_dropin_fuel,
            doc_non_energy_per_ask_medium_range_dropin_fuel,
            doc_non_energy_per_ask_long_range_dropin_fuel,
            doc_non_energy_per_ask_short_range_hydrogen,
            doc_non_energy_per_ask_medium_range_hydrogen,
            doc_non_energy_per_ask_long_range_hydrogen,
            doc_non_energy_per_ask_short_range_electric,
            doc_non_energy_per_ask_medium_range_electric,
            doc_non_energy_per_ask_long_range_electric,
            doc_non_energy_per_ask_short_range_mean,
            doc_non_energy_per_ask_medium_range_mean,
            doc_non_energy_per_ask_long_range_mean,
            doc_non_energy_per_ask_mean,
        )


class PassengerAircraftDocEnergy(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_doc_energy", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = None

    def compute(
        self,
        energy_per_ask_long_range_dropin_fuel: pd.Series,
        energy_per_ask_long_range_hydrogen: pd.Series,
        energy_per_ask_medium_range_dropin_fuel: pd.Series,
        energy_per_ask_medium_range_hydrogen: pd.Series,
        energy_per_ask_short_range_dropin_fuel: pd.Series,
        energy_per_ask_short_range_hydrogen: pd.Series,
        energy_per_ask_long_range_electric: pd.Series,
        energy_per_ask_medium_range_electric: pd.Series,
        energy_per_ask_short_range_electric: pd.Series,
        dropin_mean_mfsp: pd.Series,
        average_hydrogen_mean_mfsp_kg: pd.Series,
        ask_long_range_hydrogen_share: pd.Series,
        ask_long_range_dropin_fuel_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_medium_range_dropin_fuel_share: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_short_range_dropin_fuel_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_long_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_short_range: pd.Series,
        electricity_market_price: pd.Series,
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
        # Drop-in fuels lower heating value (MJ/L)
        fuel_lhv = 35.3
        # LH2 specific energy (MJ/kg)
        hydrogen_specific_energy = 119.93

        doc_energy_per_ask_long_range_dropin_fuel = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_energy_per_ask_long_range_hydrogen = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_energy_per_ask_long_range_electric = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_energy_per_ask_medium_range_dropin_fuel = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_energy_per_ask_medium_range_hydrogen = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_energy_per_ask_medium_range_electric = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_energy_per_ask_short_range_dropin_fuel = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_energy_per_ask_short_range_hydrogen = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_energy_per_ask_short_range_electric = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        mask_long_range_dropin = ask_long_range_dropin_fuel_share > 0
        doc_energy_per_ask_long_range_dropin_fuel[mask_long_range_dropin] = (
            energy_per_ask_long_range_dropin_fuel[mask_long_range_dropin]
            * dropin_mean_mfsp[mask_long_range_dropin]
            / fuel_lhv
        )

        mask_long_range_hydrogen = ask_long_range_hydrogen_share > 0
        doc_energy_per_ask_long_range_hydrogen[mask_long_range_hydrogen] = (
            energy_per_ask_long_range_hydrogen[mask_long_range_hydrogen]
            * average_hydrogen_mean_mfsp_kg[mask_long_range_hydrogen]
            / hydrogen_specific_energy
        )

        mask_long_range_electric = ask_long_range_electric_share > 0
        doc_energy_per_ask_long_range_electric[mask_long_range_electric] = (
            energy_per_ask_long_range_electric[mask_long_range_electric]
            * electricity_market_price[mask_long_range_electric]
            / 3.6
        )

        mask_medium_range_dropin = ask_medium_range_dropin_fuel_share > 0
        doc_energy_per_ask_medium_range_dropin_fuel[mask_medium_range_dropin] = (
            energy_per_ask_medium_range_dropin_fuel[mask_medium_range_dropin]
            * dropin_mean_mfsp[mask_medium_range_dropin]
            / fuel_lhv
        )

        mask_medium_range_hydrogen = ask_medium_range_hydrogen_share > 0
        doc_energy_per_ask_medium_range_hydrogen[mask_medium_range_hydrogen] = (
            energy_per_ask_medium_range_hydrogen[mask_medium_range_hydrogen]
            * average_hydrogen_mean_mfsp_kg[mask_medium_range_hydrogen]
            / hydrogen_specific_energy
        )

        mask_medium_range_electric = ask_medium_range_electric_share > 0
        doc_energy_per_ask_medium_range_electric[mask_medium_range_electric] = (
            energy_per_ask_medium_range_electric[mask_medium_range_electric]
            * electricity_market_price[mask_medium_range_electric]
            / 3.6
        )

        mask_short_range_dropin = ask_short_range_dropin_fuel_share > 0
        doc_energy_per_ask_short_range_dropin_fuel[mask_short_range_dropin] = (
            energy_per_ask_short_range_dropin_fuel[mask_short_range_dropin]
            * dropin_mean_mfsp[mask_short_range_dropin]
            / fuel_lhv
        )

        mask_short_range_hydrogen = ask_short_range_hydrogen_share > 0
        doc_energy_per_ask_short_range_hydrogen[mask_short_range_hydrogen] = (
            energy_per_ask_short_range_hydrogen[mask_short_range_hydrogen]
            * average_hydrogen_mean_mfsp_kg[mask_short_range_hydrogen]
            / hydrogen_specific_energy
        )

        mask_short_range_electric = ask_short_range_electric_share > 0
        doc_energy_per_ask_short_range_electric[mask_short_range_electric] = (
            energy_per_ask_short_range_electric[mask_short_range_electric]
            * electricity_market_price[mask_short_range_electric]
            / 3.6
        )

        doc_energy_per_ask_long_range_mean = (
            doc_energy_per_ask_long_range_hydrogen.fillna(0) * ask_long_range_hydrogen_share / 100
            + doc_energy_per_ask_long_range_dropin_fuel.fillna(0)
            * ask_long_range_dropin_fuel_share
            / 100
            + doc_energy_per_ask_long_range_electric.fillna(0) * ask_long_range_electric_share / 100
        )

        doc_energy_per_ask_medium_range_mean = (
            doc_energy_per_ask_medium_range_hydrogen.fillna(0)
            * ask_medium_range_hydrogen_share
            / 100
            + doc_energy_per_ask_medium_range_dropin_fuel.fillna(0)
            * ask_medium_range_dropin_fuel_share
            / 100
            + doc_energy_per_ask_medium_range_electric.fillna(0)
            * ask_medium_range_electric_share
            / 100
        )

        doc_energy_per_ask_short_range_mean = (
            doc_energy_per_ask_short_range_hydrogen.fillna(0) * ask_short_range_hydrogen_share / 100
            + doc_energy_per_ask_short_range_dropin_fuel.fillna(0)
            * ask_short_range_dropin_fuel_share
            / 100
            + doc_energy_per_ask_short_range_electric.fillna(0)
            * ask_short_range_electric_share
            / 100
        )

        doc_energy_per_ask_mean = (
            doc_energy_per_ask_long_range_mean * ask_long_range
            + doc_energy_per_ask_medium_range_mean * ask_medium_range
            + doc_energy_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        self.df.loc[:, "doc_energy_per_ask_long_range_dropin_fuel"] = (
            doc_energy_per_ask_long_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_per_ask_long_range_hydrogen"] = (
            doc_energy_per_ask_long_range_hydrogen
        )
        self.df.loc[:, "doc_energy_per_ask_long_range_electric"] = (
            doc_energy_per_ask_long_range_electric
        )
        self.df.loc[:, "doc_energy_per_ask_long_range_mean"] = doc_energy_per_ask_long_range_mean
        self.df.loc[:, "doc_energy_per_ask_medium_range_dropin_fuel"] = (
            doc_energy_per_ask_medium_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_per_ask_medium_range_hydrogen"] = (
            doc_energy_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "doc_energy_per_ask_medium_range_electric"] = (
            doc_energy_per_ask_medium_range_electric
        )
        self.df.loc[:, "doc_energy_per_ask_medium_range_mean"] = (
            doc_energy_per_ask_medium_range_mean
        )
        self.df.loc[:, "doc_energy_per_ask_short_range_dropin_fuel"] = (
            doc_energy_per_ask_short_range_dropin_fuel
        )
        self.df.loc[:, "doc_energy_per_ask_short_range_hydrogen"] = (
            doc_energy_per_ask_short_range_hydrogen
        )
        self.df.loc[:, "doc_energy_per_ask_short_range_electric"] = (
            doc_energy_per_ask_short_range_electric
        )
        self.df.loc[:, "doc_energy_per_ask_short_range_mean"] = doc_energy_per_ask_short_range_mean
        self.df.loc[:, "doc_energy_per_ask_mean"] = doc_energy_per_ask_mean
        return (
            doc_energy_per_ask_long_range_dropin_fuel,
            doc_energy_per_ask_long_range_hydrogen,
            doc_energy_per_ask_long_range_electric,
            doc_energy_per_ask_long_range_mean,
            doc_energy_per_ask_medium_range_dropin_fuel,
            doc_energy_per_ask_medium_range_hydrogen,
            doc_energy_per_ask_medium_range_electric,
            doc_energy_per_ask_medium_range_mean,
            doc_energy_per_ask_short_range_dropin_fuel,
            doc_energy_per_ask_short_range_hydrogen,
            doc_energy_per_ask_short_range_electric,
            doc_energy_per_ask_short_range_mean,
            doc_energy_per_ask_mean,
        )


class PassengerAircraftDocCarbonTax(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_doc_carbon_tax", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = None

    def compute(
        self,
        energy_per_ask_long_range_dropin_fuel: pd.Series,
        energy_per_ask_long_range_hydrogen: pd.Series,
        energy_per_ask_long_range_electric: pd.Series,
        energy_per_ask_medium_range_dropin_fuel: pd.Series,
        energy_per_ask_medium_range_hydrogen: pd.Series,
        energy_per_ask_medium_range_electric: pd.Series,
        energy_per_ask_short_range_dropin_fuel: pd.Series,
        energy_per_ask_short_range_hydrogen: pd.Series,
        energy_per_ask_short_range_electric: pd.Series,
        dropin_mfsp_carbon_tax_supplement: pd.Series,
        average_hydrogen_mean_carbon_tax_kg: pd.Series,
        electricity_direct_use_carbon_tax_kWh: pd.Series,
        ask_long_range_hydrogen_share: pd.Series,
        ask_long_range_dropin_fuel_share: pd.Series,
        ask_long_range_electric_share: pd.Series,
        ask_medium_range_hydrogen_share: pd.Series,
        ask_medium_range_dropin_fuel_share: pd.Series,
        ask_medium_range_electric_share: pd.Series,
        ask_short_range_hydrogen_share: pd.Series,
        ask_short_range_dropin_fuel_share: pd.Series,
        ask_short_range_electric_share: pd.Series,
        ask_long_range: pd.Series,
        ask_medium_range: pd.Series,
        ask_short_range: pd.Series,
        co2_emissions: pd.Series,
        carbon_offset: pd.Series,
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
    ]:
        # Drop-in fuels lower heating value (MJ/L)
        fuel_lhv = 35.3
        # LH2 specific energy (MJ/kg)
        hydrogen_specific_energy = 119.93

        # Vectorized operations with masks for increased speed: we add
        mask_long_range_dropin = ask_long_range_dropin_fuel_share > 0
        mask_long_range_hydrogen = ask_long_range_hydrogen_share > 0
        mask_long_range_electric = ask_long_range_electric_share > 0
        mask_medium_range_dropin = ask_medium_range_dropin_fuel_share > 0
        mask_medium_range_hydrogen = ask_medium_range_hydrogen_share > 0
        mask_medium_range_electric = ask_medium_range_electric_share > 0
        mask_short_range_dropin = ask_short_range_dropin_fuel_share > 0
        mask_short_range_hydrogen = ask_short_range_hydrogen_share > 0
        mask_short_range_electric = ask_short_range_electric_share > 0

        idx = pd.Index(range(self.historic_start_year, self.end_year + 1))

        doc_carbon_tax_per_ask_long_range_dropin_fuel = pd.Series(np.nan, idx)
        doc_carbon_tax_per_ask_long_range_hydrogen = pd.Series(np.nan, idx)
        doc_carbon_tax_per_ask_long_range_electric = pd.Series(np.nan, idx)
        doc_carbon_tax_per_ask_medium_range_dropin_fuel = pd.Series(np.nan, idx)
        doc_carbon_tax_per_ask_medium_range_hydrogen = pd.Series(np.nan, idx)
        doc_carbon_tax_per_ask_medium_range_electric = pd.Series(np.nan, idx)
        doc_carbon_tax_per_ask_short_range_dropin_fuel = pd.Series(np.nan, idx)
        doc_carbon_tax_per_ask_short_range_hydrogen = pd.Series(np.nan, idx)
        doc_carbon_tax_per_ask_short_range_electric = pd.Series(np.nan, idx)

        # Vectorized assignments
        doc_carbon_tax_per_ask_long_range_dropin_fuel[mask_long_range_dropin] = (
            energy_per_ask_long_range_dropin_fuel[mask_long_range_dropin]
            * dropin_mfsp_carbon_tax_supplement[mask_long_range_dropin]
            / fuel_lhv
        )
        doc_carbon_tax_per_ask_long_range_hydrogen[mask_long_range_hydrogen] = (
            energy_per_ask_long_range_hydrogen[mask_long_range_hydrogen]
            * average_hydrogen_mean_carbon_tax_kg[mask_long_range_hydrogen]
            / hydrogen_specific_energy
        )
        doc_carbon_tax_per_ask_long_range_electric[mask_long_range_electric] = (
            energy_per_ask_long_range_electric[mask_long_range_electric]
            * electricity_direct_use_carbon_tax_kWh[mask_long_range_electric]
            / 3.6
        )
        doc_carbon_tax_per_ask_medium_range_dropin_fuel[mask_medium_range_dropin] = (
            energy_per_ask_medium_range_dropin_fuel[mask_medium_range_dropin]
            * dropin_mfsp_carbon_tax_supplement[mask_medium_range_dropin]
            / fuel_lhv
        )
        doc_carbon_tax_per_ask_medium_range_hydrogen[mask_medium_range_hydrogen] = (
            energy_per_ask_medium_range_hydrogen[mask_medium_range_hydrogen]
            * average_hydrogen_mean_carbon_tax_kg[mask_medium_range_hydrogen]
            / hydrogen_specific_energy
        )
        doc_carbon_tax_per_ask_medium_range_electric[mask_medium_range_electric] = (
            energy_per_ask_medium_range_electric[mask_medium_range_electric]
            * electricity_direct_use_carbon_tax_kWh[mask_medium_range_electric]
            / 3.6
        )
        doc_carbon_tax_per_ask_short_range_dropin_fuel[mask_short_range_dropin] = (
            energy_per_ask_short_range_dropin_fuel[mask_short_range_dropin]
            * dropin_mfsp_carbon_tax_supplement[mask_short_range_dropin]
            / fuel_lhv
        )
        doc_carbon_tax_per_ask_short_range_hydrogen[mask_short_range_hydrogen] = (
            energy_per_ask_short_range_hydrogen[mask_short_range_hydrogen]
            * average_hydrogen_mean_carbon_tax_kg[mask_short_range_hydrogen]
            / hydrogen_specific_energy
        )
        doc_carbon_tax_per_ask_short_range_electric[mask_short_range_electric] = (
            energy_per_ask_short_range_electric[mask_short_range_electric]
            * electricity_direct_use_carbon_tax_kWh[mask_short_range_electric]
            / 3.6
        )

        doc_carbon_tax_per_ask_long_range_mean = (
            doc_carbon_tax_per_ask_long_range_hydrogen.fillna(0)
            * ask_long_range_hydrogen_share
            / 100
            + doc_carbon_tax_per_ask_long_range_dropin_fuel.fillna(0)
            * ask_long_range_dropin_fuel_share
            / 100
            + doc_carbon_tax_per_ask_long_range_electric.fillna(0)
            * ask_long_range_electric_share
            / 100
        )

        doc_carbon_tax_per_ask_medium_range_mean = (
            doc_carbon_tax_per_ask_medium_range_hydrogen.fillna(0)
            * ask_medium_range_hydrogen_share
            / 100
            + doc_carbon_tax_per_ask_medium_range_dropin_fuel.fillna(0)
            * ask_medium_range_dropin_fuel_share
            / 100
            + doc_carbon_tax_per_ask_medium_range_electric.fillna(0)
            * ask_medium_range_electric_share
            / 100
        )

        doc_carbon_tax_per_ask_short_range_mean = (
            doc_carbon_tax_per_ask_short_range_hydrogen.fillna(0)
            * ask_short_range_hydrogen_share
            / 100
            + doc_carbon_tax_per_ask_short_range_dropin_fuel.fillna(0)
            * ask_short_range_dropin_fuel_share
            / 100
            + doc_carbon_tax_per_ask_short_range_electric.fillna(0)
            * ask_short_range_electric_share
            / 100
        )

        doc_carbon_tax_per_ask_mean = (
            doc_carbon_tax_per_ask_long_range_mean * ask_long_range.fillna(0)
            + doc_carbon_tax_per_ask_medium_range_mean * ask_medium_range.fillna(0)
            + doc_carbon_tax_per_ask_short_range_mean * ask_short_range.fillna(0)
        ) / (ask_long_range.fillna(0) + ask_medium_range.fillna(0) + ask_short_range.fillna(0))

        co2_local = co2_emissions.loc[idx].fillna(0)
        offset_local = carbon_offset.loc[idx].fillna(0)

        doc_carbon_tax_lowering_offset_per_ask_mean = (
            doc_carbon_tax_per_ask_mean.loc[idx] * (co2_local - offset_local) / co2_local
        )

        doc_carbon_tax_lowering_offset_per_ask_short_range_mean = (
            doc_carbon_tax_per_ask_short_range_mean * (co2_local - offset_local) / co2_local
        )

        doc_carbon_tax_lowering_offset_per_ask_medium_range_mean = (
            doc_carbon_tax_per_ask_medium_range_mean * (co2_local - offset_local) / co2_local
        )

        doc_carbon_tax_lowering_offset_per_ask_long_range_mean = (
            doc_carbon_tax_per_ask_long_range_mean * (co2_local - offset_local) / co2_local
        )

        self.df.loc[:, "doc_carbon_tax_per_ask_long_range_dropin_fuel"] = (
            doc_carbon_tax_per_ask_long_range_dropin_fuel
        )
        self.df.loc[:, "doc_carbon_tax_per_ask_long_range_hydrogen"] = (
            doc_carbon_tax_per_ask_long_range_hydrogen
        )
        self.df.loc[:, "doc_carbon_tax_per_ask_long_range_mean"] = (
            doc_carbon_tax_per_ask_long_range_mean
        )
        self.df.loc[:, "doc_carbon_tax_per_ask_medium_range_dropin_fuel"] = (
            doc_carbon_tax_per_ask_medium_range_dropin_fuel
        )
        self.df.loc[:, "doc_carbon_tax_per_ask_medium_range_hydrogen"] = (
            doc_carbon_tax_per_ask_medium_range_hydrogen
        )
        self.df.loc[:, "doc_carbon_tax_per_ask_medium_range_mean"] = (
            doc_carbon_tax_per_ask_medium_range_mean
        )
        self.df.loc[:, "doc_carbon_tax_per_ask_short_range_dropin_fuel"] = (
            doc_carbon_tax_per_ask_short_range_dropin_fuel
        )
        self.df.loc[:, "doc_carbon_tax_per_ask_short_range_hydrogen"] = (
            doc_carbon_tax_per_ask_short_range_hydrogen
        )
        self.df.loc[:, "doc_carbon_tax_per_ask_short_range_mean"] = (
            doc_carbon_tax_per_ask_short_range_mean
        )
        self.df.loc[:, "doc_carbon_tax_per_ask_long_range_electric"] = (
            doc_carbon_tax_per_ask_long_range_electric
        )
        self.df.loc[:, "doc_carbon_tax_per_ask_medium_range_electric"] = (
            doc_carbon_tax_per_ask_medium_range_electric
        )
        self.df.loc[:, "doc_carbon_tax_per_ask_short_range_electric"] = (
            doc_carbon_tax_per_ask_short_range_electric
        )
        self.df.loc[:, "doc_carbon_tax_per_ask_mean"] = doc_carbon_tax_per_ask_mean

        self.df.loc[:, "doc_carbon_tax_lowering_offset_per_ask_mean"] = (
            doc_carbon_tax_lowering_offset_per_ask_mean
        )

        self.df.loc[:, "doc_carbon_tax_lowering_offset_per_ask_short_range_mean"] = (
            doc_carbon_tax_lowering_offset_per_ask_short_range_mean
        )

        self.df.loc[:, "doc_carbon_tax_lowering_offset_per_ask_medium_range_mean"] = (
            doc_carbon_tax_lowering_offset_per_ask_medium_range_mean
        )

        self.df.loc[:, "doc_carbon_tax_lowering_offset_per_ask_long_range_mean"] = (
            doc_carbon_tax_lowering_offset_per_ask_long_range_mean
        )

        return (
            doc_carbon_tax_per_ask_long_range_dropin_fuel,
            doc_carbon_tax_per_ask_long_range_hydrogen,
            doc_carbon_tax_per_ask_long_range_electric,
            doc_carbon_tax_per_ask_long_range_mean,
            doc_carbon_tax_per_ask_medium_range_dropin_fuel,
            doc_carbon_tax_per_ask_medium_range_hydrogen,
            doc_carbon_tax_per_ask_medium_range_electric,
            doc_carbon_tax_per_ask_medium_range_mean,
            doc_carbon_tax_per_ask_short_range_dropin_fuel,
            doc_carbon_tax_per_ask_short_range_hydrogen,
            doc_carbon_tax_per_ask_short_range_electric,
            doc_carbon_tax_per_ask_short_range_mean,
            doc_carbon_tax_per_ask_mean,
            doc_carbon_tax_lowering_offset_per_ask_mean,
            doc_carbon_tax_lowering_offset_per_ask_short_range_mean,
            doc_carbon_tax_lowering_offset_per_ask_medium_range_mean,
            doc_carbon_tax_lowering_offset_per_ask_long_range_mean,
        )


class PassengerAircraftTotalDoc(AeroMAPSModel):
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
        doc_carbon_tax_per_ask_long_range_dropin_fuel: pd.Series,
        doc_carbon_tax_per_ask_long_range_hydrogen: pd.Series,
        doc_carbon_tax_per_ask_long_range_mean: pd.Series,
        doc_carbon_tax_per_ask_medium_range_dropin_fuel: pd.Series,
        doc_carbon_tax_per_ask_medium_range_hydrogen: pd.Series,
        doc_carbon_tax_per_ask_medium_range_mean: pd.Series,
        doc_carbon_tax_per_ask_short_range_dropin_fuel: pd.Series,
        doc_carbon_tax_per_ask_short_range_hydrogen: pd.Series,
        doc_carbon_tax_per_ask_short_range_mean: pd.Series,
        doc_non_energy_per_ask_short_range_electric: pd.Series,
        doc_non_energy_per_ask_medium_range_electric: pd.Series,
        doc_non_energy_per_ask_long_range_electric: pd.Series,
        doc_energy_per_ask_short_range_electric: pd.Series,
        doc_energy_per_ask_medium_range_electric: pd.Series,
        doc_energy_per_ask_long_range_electric: pd.Series,
        doc_carbon_tax_per_ask_short_range_electric: pd.Series,
        doc_carbon_tax_per_ask_medium_range_electric: pd.Series,
        doc_carbon_tax_per_ask_long_range_electric: pd.Series,
        doc_carbon_tax_per_ask_mean: pd.Series,
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
        # dropin
        doc_total_per_ask_short_range_dropin_fuel = (
            doc_non_energy_per_ask_short_range_dropin_fuel
            + doc_energy_per_ask_short_range_dropin_fuel
            + doc_carbon_tax_per_ask_short_range_dropin_fuel
        )

        doc_total_per_ask_medium_range_dropin_fuel = (
            doc_non_energy_per_ask_medium_range_dropin_fuel
            + doc_energy_per_ask_medium_range_dropin_fuel
            + doc_carbon_tax_per_ask_medium_range_dropin_fuel
        )

        doc_total_per_ask_long_range_dropin_fuel = (
            doc_non_energy_per_ask_long_range_dropin_fuel
            + doc_energy_per_ask_long_range_dropin_fuel
            + doc_carbon_tax_per_ask_long_range_dropin_fuel
        )

        # Hydrogen
        doc_total_per_ask_short_range_hydrogen = (
            doc_non_energy_per_ask_short_range_hydrogen
            + doc_energy_per_ask_short_range_hydrogen
            + doc_carbon_tax_per_ask_short_range_hydrogen
        )

        doc_total_per_ask_medium_range_hydrogen = (
            doc_non_energy_per_ask_medium_range_hydrogen
            + doc_energy_per_ask_medium_range_hydrogen
            + doc_carbon_tax_per_ask_medium_range_hydrogen
        )

        doc_total_per_ask_long_range_hydrogen = (
            doc_non_energy_per_ask_long_range_hydrogen
            + doc_energy_per_ask_long_range_hydrogen
            + doc_carbon_tax_per_ask_long_range_hydrogen
        )

        # Electric
        doc_total_per_ask_short_range_electric = (
            doc_non_energy_per_ask_short_range_electric
            + doc_energy_per_ask_short_range_electric
            + doc_carbon_tax_per_ask_short_range_electric
        )

        doc_total_per_ask_medium_range_electric = (
            doc_non_energy_per_ask_medium_range_electric
            + doc_energy_per_ask_medium_range_electric
            + doc_carbon_tax_per_ask_medium_range_electric
        )

        doc_total_per_ask_long_range_electric = (
            doc_non_energy_per_ask_long_range_electric
            + doc_energy_per_ask_long_range_electric
            + doc_carbon_tax_per_ask_long_range_electric
        )

        # Average per category
        doc_total_per_ask_short_range_mean = (
            doc_non_energy_per_ask_short_range_mean
            + doc_energy_per_ask_short_range_mean
            + doc_carbon_tax_per_ask_short_range_mean
        )

        doc_total_per_ask_medium_range_mean = (
            doc_non_energy_per_ask_medium_range_mean
            + doc_energy_per_ask_medium_range_mean
            + doc_carbon_tax_per_ask_medium_range_mean
        )

        doc_total_per_ask_long_range_mean = (
            doc_non_energy_per_ask_long_range_mean
            + doc_energy_per_ask_long_range_mean
            + doc_carbon_tax_per_ask_long_range_mean
        )

        # total average

        doc_total_per_ask_mean = (
            doc_non_energy_per_ask_mean + doc_energy_per_ask_mean + doc_carbon_tax_per_ask_mean
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


class DropInMeanMfsp(AeroMAPSModel):
    def __init__(self, name="dropin_mean_mfsp", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = None

    def compute(
        self,
        biofuel_mean_mfsp: pd.Series,
        biofuel_marginal_mfsp: pd.Series,
        biofuel_mean_carbon_tax_per_l: pd.Series,
        biofuel_share: pd.Series,
        electrofuel_mean_mfsp_litre: pd.Series,
        electrofuel_mfsp_carbon_tax_supplement: pd.Series,
        electrofuel_share: pd.Series,
        kerosene_market_price: pd.Series,
        kerosene_price_supplement_carbon_tax: pd.Series,
        kerosene_share: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        dropin_mean_mfsp = (
            (biofuel_mean_mfsp * biofuel_share / 100).fillna(0)
            + (electrofuel_mean_mfsp_litre * electrofuel_share / 100).fillna(0)
            + (kerosene_market_price * kerosene_share / 100).fillna(0)
        )

        for k in range(self.prospection_start_year - 1, self.end_year + 1):
            # check for vals
            valid = []
            if biofuel_share.loc[k] > 0:
                valid.append(biofuel_marginal_mfsp.loc[k])
            if electrofuel_share.loc[k] > 0:
                valid.append(electrofuel_mean_mfsp_litre.loc[k])
            if kerosene_share.loc[k] > 0:
                valid.append(kerosene_market_price.loc[k])

            self.df.loc[k, "dropin_marginal_mfsp"] = np.max(valid)

        dropin_marginal_mfsp = self.df.loc[:, "dropin_marginal_mfsp"]

        dropin_mfsp_carbon_tax_supplement = (
            (biofuel_mean_carbon_tax_per_l * biofuel_share / 100).fillna(0)
            + (electrofuel_mfsp_carbon_tax_supplement * electrofuel_share / 100).fillna(0)
            + (kerosene_price_supplement_carbon_tax * kerosene_share / 100).fillna(0)
        )

        self.df.loc[:, "dropin_mean_mfsp"] = dropin_mean_mfsp
        self.df.loc[:, "dropin_mfsp_carbon_tax_supplement"] = dropin_mfsp_carbon_tax_supplement

        return (dropin_mean_mfsp, dropin_marginal_mfsp, dropin_mfsp_carbon_tax_supplement)

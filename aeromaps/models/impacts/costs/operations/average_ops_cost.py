from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel


class PassengerAircraftDocNonEnergyComplex(AeromapsModel):
    def __init__(
        self, name="passenger_aircraft_doc_non_energy_complex", fleet_model=None, *args, **kwargs
    ):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = fleet_model

    def compute(
        self,
        ask_long_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        ask_long_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        ask_short_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        ask_short_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        ask_long_range: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range: pd.Series = pd.Series(dtype="float64"),
        ask_short_range: pd.Series = pd.Series(dtype="float64"),
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

        # Drop-in - Projections

        self.df.loc[
            :, "doc_non_energy_per_ask_short_range_dropin_fuel"
        ] = doc_non_energy_per_ask_short_range_dropin_fuel
        self.df.loc[
            :, "doc_non_energy_per_ask_medium_range_dropin_fuel"
        ] = doc_non_energy_per_ask_medium_range_dropin_fuel
        self.df.loc[
            :, "doc_non_energy_per_ask_long_range_dropin_fuel"
        ] = doc_non_energy_per_ask_long_range_dropin_fuel

        # Hydrogen
        self.df.loc[
            :, "doc_non_energy_per_ask_short_range_hydrogen"
        ] = doc_non_energy_per_ask_short_range_hydrogen
        self.df.loc[
            :, "doc_non_energy_per_ask_medium_range_hydrogen"
        ] = doc_non_energy_per_ask_medium_range_hydrogen
        self.df.loc[
            :, "doc_non_energy_per_ask_long_range_hydrogen"
        ] = doc_non_energy_per_ask_long_range_hydrogen

        doc_non_energy_per_ask_long_range_mean = (
            doc_non_energy_per_ask_long_range_hydrogen * ask_long_range_hydrogen_share / 100
            + doc_non_energy_per_ask_long_range_dropin_fuel * ask_long_range_dropin_fuel_share / 100
        )

        doc_non_energy_per_ask_medium_range_mean = (
            doc_non_energy_per_ask_medium_range_hydrogen * ask_medium_range_hydrogen_share / 100
            + doc_non_energy_per_ask_medium_range_dropin_fuel
            * ask_medium_range_dropin_fuel_share
            / 100
        )

        doc_non_energy_per_ask_short_range_mean = (
            doc_non_energy_per_ask_short_range_hydrogen * ask_short_range_hydrogen_share / 100
            + doc_non_energy_per_ask_short_range_dropin_fuel
            * ask_short_range_dropin_fuel_share
            / 100
        )

        doc_non_energy_per_ask_mean = (
            doc_non_energy_per_ask_long_range_mean * ask_long_range
            + doc_non_energy_per_ask_medium_range_mean * ask_medium_range
            + doc_non_energy_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        self.df.loc[
            :, "doc_non_energy_per_ask_long_range_mean"
        ] = doc_non_energy_per_ask_long_range_mean

        self.df.loc[
            :, "doc_non_energy_per_ask_medium_range_mean"
        ] = doc_non_energy_per_ask_medium_range_mean

        self.df.loc[
            :, "doc_non_energy_per_ask_short_range_mean"
        ] = doc_non_energy_per_ask_short_range_mean

        self.df.loc[:, "doc_non_energy_per_ask_mean"] = doc_non_energy_per_ask_mean

        return (
            doc_non_energy_per_ask_short_range_dropin_fuel,
            doc_non_energy_per_ask_medium_range_dropin_fuel,
            doc_non_energy_per_ask_long_range_dropin_fuel,
            doc_non_energy_per_ask_short_range_hydrogen,
            doc_non_energy_per_ask_medium_range_hydrogen,
            doc_non_energy_per_ask_long_range_hydrogen,
            doc_non_energy_per_ask_short_range_mean,
            doc_non_energy_per_ask_medium_range_mean,
            doc_non_energy_per_ask_long_range_mean,
            doc_non_energy_per_ask_mean,
        )


class PassengerAircraftDocNonEnergySimple(AeromapsModel):
    def __init__(self, name="passenger_aircraft_doc_non_energy_simple", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        doc_non_energy_per_ask_short_range_dropin_fuel_init: float = 0.0,
        doc_non_energy_per_ask_medium_range_dropin_fuel_init: float = 0.0,
        doc_non_energy_per_ask_long_range_dropin_fuel_init: float = 0.0,
        doc_non_energy_per_ask_short_range_dropin_fuel_gain: float = 0.0,
        doc_non_energy_per_ask_medium_range_dropin_fuel_gain: float = 0.0,
        doc_non_energy_per_ask_long_range_dropin_fuel_gain: float = 0.0,
        relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_short_range: float = 0.0,
        relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_medium_range: float = 0.0,
        relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_long_range: float = 0.0,
        ask_long_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        ask_long_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        ask_short_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        ask_short_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        ask_long_range: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range: pd.Series = pd.Series(dtype="float64"),
        ask_short_range: pd.Series = pd.Series(dtype="float64"),
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
    ]:
        """DOC (without energy DOC) per ASK calculation using simple models."""

        # Initialization based on 2019 values

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[
                k, "doc_non_energy_per_ask_short_range_dropin_fuel"
            ] = doc_non_energy_per_ask_short_range_dropin_fuel_init
            self.df.loc[
                k, "doc_non_energy_per_ask_medium_range_dropin_fuel"
            ] = doc_non_energy_per_ask_medium_range_dropin_fuel_init
            self.df.loc[
                k, "doc_non_energy_per_ask_long_range_dropin_fuel"
            ] = doc_non_energy_per_ask_long_range_dropin_fuel_init

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

        self.df.loc[
            :, "doc_non_energy_per_ask_short_range_hydrogen"
        ] = doc_non_energy_per_ask_short_range_hydrogen
        self.df.loc[
            :, "doc_non_energy_per_ask_medium_range_hydrogen"
        ] = doc_non_energy_per_ask_medium_range_hydrogen
        self.df.loc[
            :, "doc_non_energy_per_ask_long_range_hydrogen"
        ] = doc_non_energy_per_ask_long_range_hydrogen

        doc_non_energy_per_ask_long_range_mean = (
            doc_non_energy_per_ask_long_range_hydrogen * ask_long_range_hydrogen_share / 100
            + doc_non_energy_per_ask_long_range_dropin_fuel * ask_long_range_dropin_fuel_share / 100
        )

        doc_non_energy_per_ask_medium_range_mean = (
            doc_non_energy_per_ask_medium_range_hydrogen * ask_medium_range_hydrogen_share / 100
            + doc_non_energy_per_ask_medium_range_dropin_fuel
            * ask_medium_range_dropin_fuel_share
            / 100
        )

        doc_non_energy_per_ask_short_range_mean = (
            doc_non_energy_per_ask_short_range_hydrogen * ask_short_range_hydrogen_share / 100
            + doc_non_energy_per_ask_short_range_dropin_fuel
            * ask_short_range_dropin_fuel_share
            / 100
        )

        doc_non_energy_per_ask_mean = (
            doc_non_energy_per_ask_long_range_mean * ask_long_range
            + doc_non_energy_per_ask_medium_range_mean * ask_medium_range
            + doc_non_energy_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        self.df.loc[
            :, "doc_non_energy_per_ask_long_range_mean"
        ] = doc_non_energy_per_ask_long_range_mean

        self.df.loc[
            :, "doc_non_energy_per_ask_medium_range_mean"
        ] = doc_non_energy_per_ask_medium_range_mean

        self.df.loc[
            :, "doc_non_energy_per_ask_short_range_mean"
        ] = doc_non_energy_per_ask_short_range_mean

        self.df.loc[:, "doc_non_energy_per_ask_mean"] = doc_non_energy_per_ask_mean

        return (
            doc_non_energy_per_ask_short_range_dropin_fuel,
            doc_non_energy_per_ask_medium_range_dropin_fuel,
            doc_non_energy_per_ask_long_range_dropin_fuel,
            doc_non_energy_per_ask_short_range_hydrogen,
            doc_non_energy_per_ask_medium_range_hydrogen,
            doc_non_energy_per_ask_long_range_hydrogen,
            doc_non_energy_per_ask_short_range_mean,
            doc_non_energy_per_ask_medium_range_mean,
            doc_non_energy_per_ask_long_range_mean,
            doc_non_energy_per_ask_mean,
        )


class PassengerAircraftDocEnergy(AeromapsModel):
    def __init__(self, name="passenger_aircraft_doc_energy", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_per_ask_long_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_long_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_medium_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_medium_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_short_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_short_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        dropin_mean_mfsp: pd.Series = pd.Series(dtype="float64"),
        h2_avg_cost_per_kg: pd.Series = pd.Series(dtype="float64"),
        ask_long_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        ask_long_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        ask_short_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        ask_short_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        ask_long_range: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range: pd.Series = pd.Series(dtype="float64"),
        ask_short_range: pd.Series = pd.Series(dtype="float64"),
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
        doc_energy_per_ask_medium_range_dropin_fuel = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_energy_per_ask_medium_range_hydrogen = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_energy_per_ask_short_range_dropin_fuel = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_energy_per_ask_short_range_hydrogen = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        for k in range(self.historic_start_year, self.end_year + 1):
            if ask_long_range_dropin_fuel_share[k] > 0:
                doc_energy_per_ask_long_range_dropin_fuel[k] = (
                    energy_per_ask_long_range_dropin_fuel[k] * dropin_mean_mfsp[k] / fuel_lhv
                )
            if ask_long_range_hydrogen_share[k] > 0:
                doc_energy_per_ask_long_range_hydrogen[k] = (
                    energy_per_ask_long_range_hydrogen[k]
                    * h2_avg_cost_per_kg[k]
                    / hydrogen_specific_energy
                )
            if ask_medium_range_dropin_fuel_share[k] > 0:
                doc_energy_per_ask_medium_range_dropin_fuel[k] = (
                    energy_per_ask_medium_range_dropin_fuel[k] * dropin_mean_mfsp[k] / fuel_lhv
                )
            if ask_medium_range_hydrogen_share[k] > 0:
                doc_energy_per_ask_medium_range_hydrogen[k] = (
                    energy_per_ask_medium_range_hydrogen[k]
                    * h2_avg_cost_per_kg[k]
                    / hydrogen_specific_energy
                )
            if ask_short_range_dropin_fuel_share[k] > 0:
                doc_energy_per_ask_short_range_dropin_fuel[k] = (
                    energy_per_ask_short_range_dropin_fuel[k] * dropin_mean_mfsp[k] / fuel_lhv
                )
            if ask_short_range_hydrogen_share[k] > 0:
                doc_energy_per_ask_short_range_hydrogen[k] = (
                    energy_per_ask_short_range_hydrogen[k]
                    * h2_avg_cost_per_kg[k]
                    / hydrogen_specific_energy
                )

        doc_energy_per_ask_long_range_mean = (
            doc_energy_per_ask_long_range_hydrogen.fillna(0) * ask_long_range_hydrogen_share / 100
            + doc_energy_per_ask_long_range_dropin_fuel.fillna(0)
            * ask_long_range_dropin_fuel_share
            / 100
        )

        doc_energy_per_ask_medium_range_mean = (
            doc_energy_per_ask_medium_range_hydrogen.fillna(0)
            * ask_medium_range_hydrogen_share
            / 100
            + doc_energy_per_ask_medium_range_dropin_fuel.fillna(0)
            * ask_medium_range_dropin_fuel_share
            / 100
        )

        doc_energy_per_ask_short_range_mean = (
            doc_energy_per_ask_short_range_hydrogen.fillna(0) * ask_short_range_hydrogen_share / 100
            + doc_energy_per_ask_short_range_dropin_fuel.fillna(0)
            * ask_short_range_dropin_fuel_share
            / 100
        )

        doc_energy_per_ask_mean = (
            doc_energy_per_ask_long_range_mean * ask_long_range
            + doc_energy_per_ask_medium_range_mean * ask_medium_range
            + doc_energy_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        self.df.loc[
            :, "doc_energy_per_ask_long_range_dropin_fuel"
        ] = doc_energy_per_ask_long_range_dropin_fuel
        self.df.loc[
            :, "doc_energy_per_ask_long_range_hydrogen"
        ] = doc_energy_per_ask_long_range_hydrogen
        self.df.loc[:, "doc_energy_per_ask_long_range_mean"] = doc_energy_per_ask_long_range_mean
        self.df.loc[
            :, "doc_energy_per_ask_medium_range_dropin_fuel"
        ] = doc_energy_per_ask_medium_range_dropin_fuel
        self.df.loc[
            :, "doc_energy_per_ask_medium_range_hydrogen"
        ] = doc_energy_per_ask_medium_range_hydrogen
        self.df.loc[
            :, "doc_energy_per_ask_medium_range_mean"
        ] = doc_energy_per_ask_medium_range_mean
        self.df.loc[
            :, "doc_energy_per_ask_short_range_dropin_fuel"
        ] = doc_energy_per_ask_short_range_dropin_fuel
        self.df.loc[
            :, "doc_energy_per_ask_short_range_hydrogen"
        ] = doc_energy_per_ask_short_range_hydrogen
        self.df.loc[:, "doc_energy_per_ask_short_range_mean"] = doc_energy_per_ask_short_range_mean
        self.df.loc[:, "doc_energy_per_ask_mean"] = doc_energy_per_ask_mean
        return (
            doc_energy_per_ask_long_range_dropin_fuel,
            doc_energy_per_ask_long_range_hydrogen,
            doc_energy_per_ask_long_range_mean,
            doc_energy_per_ask_medium_range_dropin_fuel,
            doc_energy_per_ask_medium_range_hydrogen,
            doc_energy_per_ask_medium_range_mean,
            doc_energy_per_ask_short_range_dropin_fuel,
            doc_energy_per_ask_short_range_hydrogen,
            doc_energy_per_ask_short_range_mean,
            doc_energy_per_ask_mean,
        )


class PassengerAircraftDocCarbonTax(AeromapsModel):
    def __init__(self, name="passenger_aircraft_doc_carbon_tax", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_per_ask_long_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_long_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_medium_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_medium_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_short_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        energy_per_ask_short_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        dropin_mfsp_carbon_tax_supplement: pd.Series = pd.Series(dtype="float64"),
        h2_avg_carbon_tax_per_kg: pd.Series = pd.Series(dtype="float64"),
        ask_long_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        ask_long_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        ask_short_range_hydrogen_share: pd.Series = pd.Series(dtype="float64"),
        ask_short_range_dropin_fuel_share: pd.Series = pd.Series(dtype="float64"),
        ask_long_range: pd.Series = pd.Series(dtype="float64"),
        ask_medium_range: pd.Series = pd.Series(dtype="float64"),
        ask_short_range: pd.Series = pd.Series(dtype="float64"),
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
        carbon_offset: pd.Series = pd.Series(dtype="float64"),
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
    ]:
        # Drop-in fuels lower heating value (MJ/L)
        fuel_lhv = 35.3
        # LH2 specific energy (MJ/kg)
        hydrogen_specific_energy = 119.93

        doc_carbon_tax_per_ask_long_range_dropin_fuel = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_carbon_tax_per_ask_long_range_hydrogen = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_carbon_tax_per_ask_medium_range_dropin_fuel = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_carbon_tax_per_ask_medium_range_hydrogen = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_carbon_tax_per_ask_short_range_dropin_fuel = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        doc_carbon_tax_per_ask_short_range_hydrogen = pd.Series(
            np.nan, range(self.historic_start_year, self.end_year + 1)
        )
        for k in range(self.historic_start_year, self.end_year + 1):
            if ask_long_range_dropin_fuel_share[k] > 0:
                doc_carbon_tax_per_ask_long_range_dropin_fuel[k] = (
                    energy_per_ask_long_range_dropin_fuel[k]
                    * dropin_mfsp_carbon_tax_supplement[k]
                    / fuel_lhv
                )
            if ask_long_range_hydrogen_share[k] > 0:
                doc_carbon_tax_per_ask_long_range_hydrogen[k] = (
                    energy_per_ask_long_range_hydrogen[k]
                    * h2_avg_carbon_tax_per_kg[k]
                    / hydrogen_specific_energy
                )
            if ask_medium_range_dropin_fuel_share[k] > 0:
                doc_carbon_tax_per_ask_medium_range_dropin_fuel[k] = (
                    energy_per_ask_medium_range_dropin_fuel[k]
                    * dropin_mfsp_carbon_tax_supplement[k]
                    / fuel_lhv
                )
            if ask_medium_range_hydrogen_share[k] > 0:
                doc_carbon_tax_per_ask_medium_range_hydrogen[k] = (
                    energy_per_ask_medium_range_hydrogen[k]
                    * h2_avg_carbon_tax_per_kg[k]
                    / hydrogen_specific_energy
                )
            if ask_short_range_dropin_fuel_share[k] > 0:
                doc_carbon_tax_per_ask_short_range_dropin_fuel[k] = (
                    energy_per_ask_short_range_dropin_fuel[k]
                    * dropin_mfsp_carbon_tax_supplement[k]
                    / fuel_lhv
                )
            if ask_short_range_hydrogen_share[k] > 0:
                doc_carbon_tax_per_ask_short_range_hydrogen[k] = (
                    energy_per_ask_short_range_hydrogen[k]
                    * h2_avg_carbon_tax_per_kg[k]
                    / hydrogen_specific_energy
                )

        doc_carbon_tax_per_ask_long_range_mean = (
            doc_carbon_tax_per_ask_long_range_hydrogen.fillna(0)
            * ask_long_range_hydrogen_share
            / 100
            + doc_carbon_tax_per_ask_long_range_dropin_fuel.fillna(0)
            * ask_long_range_dropin_fuel_share
            / 100
        )

        doc_carbon_tax_per_ask_medium_range_mean = (
            doc_carbon_tax_per_ask_medium_range_hydrogen.fillna(0)
            * ask_medium_range_hydrogen_share
            / 100
            + doc_carbon_tax_per_ask_medium_range_dropin_fuel.fillna(0)
            * ask_medium_range_dropin_fuel_share
            / 100
        )

        doc_carbon_tax_per_ask_short_range_mean = (
            doc_carbon_tax_per_ask_short_range_hydrogen.fillna(0)
            * ask_short_range_hydrogen_share
            / 100
            + doc_carbon_tax_per_ask_short_range_dropin_fuel.fillna(0)
            * ask_short_range_dropin_fuel_share
            / 100
        )

        doc_carbon_tax_per_ask_mean = (
            doc_carbon_tax_per_ask_long_range_mean * ask_long_range
            + doc_carbon_tax_per_ask_medium_range_mean * ask_medium_range
            + doc_carbon_tax_per_ask_short_range_mean * ask_short_range
        ) / (ask_long_range + ask_medium_range + ask_short_range)

        doc_carbon_tax_lowering_offset_per_ask_mean = (
            doc_carbon_tax_per_ask_mean * (co2_emissions - carbon_offset) / co2_emissions
        )

        self.df.loc[
            :, "doc_carbon_tax_per_ask_long_range_dropin_fuel"
        ] = doc_carbon_tax_per_ask_long_range_dropin_fuel
        self.df.loc[
            :, "doc_carbon_tax_per_ask_long_range_hydrogen"
        ] = doc_carbon_tax_per_ask_long_range_hydrogen
        self.df.loc[
            :, "doc_carbon_tax_per_ask_long_range_mean"
        ] = doc_carbon_tax_per_ask_long_range_mean
        self.df.loc[
            :, "doc_carbon_tax_per_ask_medium_range_dropin_fuel"
        ] = doc_carbon_tax_per_ask_medium_range_dropin_fuel
        self.df.loc[
            :, "doc_carbon_tax_per_ask_medium_range_hydrogen"
        ] = doc_carbon_tax_per_ask_medium_range_hydrogen
        self.df.loc[
            :, "doc_carbon_tax_per_ask_medium_range_mean"
        ] = doc_carbon_tax_per_ask_medium_range_mean
        self.df.loc[
            :, "doc_carbon_tax_per_ask_short_range_dropin_fuel"
        ] = doc_carbon_tax_per_ask_short_range_dropin_fuel
        self.df.loc[
            :, "doc_carbon_tax_per_ask_short_range_hydrogen"
        ] = doc_carbon_tax_per_ask_short_range_hydrogen
        self.df.loc[
            :, "doc_carbon_tax_per_ask_short_range_mean"
        ] = doc_carbon_tax_per_ask_short_range_mean
        self.df.loc[:, "doc_carbon_tax_per_ask_mean"] = doc_carbon_tax_per_ask_mean
        self.df.loc[
            :, "doc_carbon_tax_lowering_offset_per_ask_mean"
        ] = doc_carbon_tax_lowering_offset_per_ask_mean

        return (
            doc_carbon_tax_per_ask_long_range_dropin_fuel,
            doc_carbon_tax_per_ask_long_range_hydrogen,
            doc_carbon_tax_per_ask_long_range_mean,
            doc_carbon_tax_per_ask_medium_range_dropin_fuel,
            doc_carbon_tax_per_ask_medium_range_hydrogen,
            doc_carbon_tax_per_ask_medium_range_mean,
            doc_carbon_tax_per_ask_short_range_dropin_fuel,
            doc_carbon_tax_per_ask_short_range_hydrogen,
            doc_carbon_tax_per_ask_short_range_mean,
            doc_carbon_tax_per_ask_mean,
            doc_carbon_tax_lowering_offset_per_ask_mean,
        )


class PassengerAircraftTotalDoc(AeromapsModel):
    def __init__(self, name="passenger_aircraft_total_doc", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        doc_non_energy_per_ask_short_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        doc_non_energy_per_ask_medium_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        doc_non_energy_per_ask_long_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        doc_non_energy_per_ask_short_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        doc_non_energy_per_ask_medium_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        doc_non_energy_per_ask_long_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        doc_non_energy_per_ask_short_range_mean: pd.Series = pd.Series(dtype="float64"),
        doc_non_energy_per_ask_medium_range_mean: pd.Series = pd.Series(dtype="float64"),
        doc_non_energy_per_ask_long_range_mean: pd.Series = pd.Series(dtype="float64"),
        doc_non_energy_per_ask_mean: pd.Series = pd.Series(dtype="float64"),
        doc_energy_per_ask_long_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        doc_energy_per_ask_long_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        doc_energy_per_ask_long_range_mean: pd.Series = pd.Series(dtype="float64"),
        doc_energy_per_ask_medium_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        doc_energy_per_ask_medium_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        doc_energy_per_ask_medium_range_mean: pd.Series = pd.Series(dtype="float64"),
        doc_energy_per_ask_short_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        doc_energy_per_ask_short_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        doc_energy_per_ask_short_range_mean: pd.Series = pd.Series(dtype="float64"),
        doc_energy_per_ask_mean: pd.Series = pd.Series(dtype="float64"),
        doc_carbon_tax_per_ask_long_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        doc_carbon_tax_per_ask_long_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        doc_carbon_tax_per_ask_long_range_mean: pd.Series = pd.Series(dtype="float64"),
        doc_carbon_tax_per_ask_medium_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        doc_carbon_tax_per_ask_medium_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        doc_carbon_tax_per_ask_medium_range_mean: pd.Series = pd.Series(dtype="float64"),
        doc_carbon_tax_per_ask_short_range_dropin_fuel: pd.Series = pd.Series(dtype="float64"),
        doc_carbon_tax_per_ask_short_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
        doc_carbon_tax_per_ask_short_range_mean: pd.Series = pd.Series(dtype="float64"),
        doc_carbon_tax_per_ask_mean: pd.Series = pd.Series(dtype="float64"),
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

        self.df.loc[
            :, "doc_total_per_ask_short_range_dropin_fuel"
        ] = doc_total_per_ask_short_range_dropin_fuel
        self.df.loc[
            :, "doc_total_per_ask_medium_range_dropin_fuel"
        ] = doc_total_per_ask_medium_range_dropin_fuel
        self.df.loc[
            :, "doc_total_per_ask_long_range_dropin_fuel"
        ] = doc_total_per_ask_long_range_dropin_fuel
        self.df.loc[
            :, "doc_total_per_ask_short_range_hydrogen"
        ] = doc_total_per_ask_short_range_hydrogen
        self.df.loc[
            :, "doc_total_per_ask_medium_range_hydrogen"
        ] = doc_total_per_ask_medium_range_hydrogen
        self.df.loc[
            :, "doc_total_per_ask_long_range_hydrogen"
        ] = doc_total_per_ask_long_range_hydrogen
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
            doc_total_per_ask_short_range_mean,
            doc_total_per_ask_medium_range_mean,
            doc_total_per_ask_long_range_mean,
            doc_total_per_ask_mean,
        )


class DropInMeanMfsp(AeromapsModel):
    def __init__(self, name="dropin_mean_mfsp", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        biofuel_mean_mfsp: pd.Series = pd.Series(dtype="float64"),
        biofuel_mean_carbon_tax_per_l: pd.Series = pd.Series(dtype="float64"),
        biofuel_share: pd.Series = pd.Series(dtype="float64"),
        electrofuel_avg_cost_per_l: pd.Series = pd.Series(dtype="float64"),
        electrofuel_mfsp_carbon_tax_supplement: pd.Series = pd.Series(dtype="float64"),
        electrofuel_share: pd.Series = pd.Series(dtype="float64"),
        kerosene_market_price: pd.Series = pd.Series(dtype="float64"),
        kerosene_price_supplement_carbon_tax: pd.Series = pd.Series(dtype="float64"),
        kerosene_share: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series]:

        dropin_mean_mfsp = (
            biofuel_mean_mfsp.fillna(0) * biofuel_share / 100
            + electrofuel_avg_cost_per_l.fillna(0) * electrofuel_share / 100
            + kerosene_market_price.fillna(0) * kerosene_share / 100
        )

        dropin_mfsp_carbon_tax_supplement = (
            biofuel_mean_carbon_tax_per_l.fillna(0) * biofuel_share / 100
            + electrofuel_mfsp_carbon_tax_supplement.fillna(0) * electrofuel_share / 100
            + kerosene_price_supplement_carbon_tax.fillna(0) * kerosene_share / 100
        )

        self.df.loc[:, "dropin_mean_mfsp"] = dropin_mean_mfsp
        self.df.loc[:, "dropin_mfsp_carbon_tax_supplement"] = dropin_mfsp_carbon_tax_supplement

        return (dropin_mean_mfsp, dropin_mfsp_carbon_tax_supplement)

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class EmissionsPerRPK(AeroMAPSModel):
    def __init__(self, name="emissions_per_rpk", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions_passenger: pd.Series,
        rpk: pd.Series,
    ) -> pd.Series:
        """CO2 emissions per Revenue Passenger Kilometer calculation."""

        self.df["co2_emissions_per_rpk"] = co2_emissions_passenger * 1e6 * 1e6 / rpk
        co2_emissions_per_rpk = self.df["co2_emissions_per_rpk"]

        return co2_emissions_per_rpk


class EmissionsPerRTK(AeroMAPSModel):
    def __init__(self, name="emissions_per_rpk", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions_freight: pd.Series,
        rtk: pd.Series,
    ) -> pd.Series:
        """CO2 emissions per Revenue Tonne Kilometer calculation."""

        self.df["co2_emissions_per_rtk"] = co2_emissions_freight * 1e6 * 1e6 / rtk
        co2_emissions_per_rtk = self.df["co2_emissions_per_rtk"]

        return co2_emissions_per_rtk


class DropinFuelConsumptionLiterPerPax100km(AeroMAPSModel):
    def __init__(self, name="dropin_fuel_consumption_liter_per_pax_100km", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_passenger_kerosene: pd.Series,
        energy_consumption_passenger_biofuel: pd.Series,
        energy_consumption_passenger_electrofuel: pd.Series,
        lhv_kerosene: float,
        lhv_biofuel: float,
        lhv_electrofuel: float,
        rpk: pd.Series,
    ) -> pd.Series:
        """Drop-in fuel consumption in liter per passenger per 100 km calculation."""

        density = 0.8
        self.df["dropin_fuel_consumption_liter_per_pax_100km"] = (
            (
                energy_consumption_passenger_kerosene / lhv_kerosene
                + energy_consumption_passenger_biofuel / lhv_biofuel
                + energy_consumption_passenger_electrofuel / lhv_electrofuel
            )
            / density
            * 100
            / rpk
        )
        dropin_fuel_consumption_liter_per_pax_100km = self.df[
            "dropin_fuel_consumption_liter_per_pax_100km"
        ]

        return dropin_fuel_consumption_liter_per_pax_100km

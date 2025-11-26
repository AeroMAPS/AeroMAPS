"""
others

========
This module contains models for various KPI computations.
"""

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class EmissionsPerRPK(AeroMAPSModel):
    """
    This class computes the CO2 emissions per Revenue Passenger Kilometer (RPK).

    Parameters
    ----------
    name : str
        Name of the model instance ('emissions_per_rpk' by default).
    """

    def __init__(self, name="emissions_per_rpk", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions_passenger: pd.Series,
        rpk: pd.Series,
    ) -> pd.Series:
        """
        CO2 emissions per Revenue Passenger Kilometer calculation.

        Parameters
        ----------
        co2_emissions_passenger
            CO2 emissions from passenger air transport [MtCO2].
        rpk
            Revenue Passenger Kilometer [RPK].

        Returns
        -------
        co2_emissions_per_rpk
            CO2 emissions per Revenue Passenger Kilometer [gCO2/RPK].
        """

        self.df["co2_emissions_per_rpk"] = co2_emissions_passenger * 1e6 * 1e6 / rpk
        co2_emissions_per_rpk = self.df["co2_emissions_per_rpk"]

        return co2_emissions_per_rpk


class EmissionsPerRTK(AeroMAPSModel):
    """
    This class computes the freight CO2 emissions per Revenue Tonne Kilometer (RTK).
    """

    def __init__(self, name="emissions_per_rpk", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        co2_emissions_freight: pd.Series,
        rtk: pd.Series,
    ) -> pd.Series:
        """CO2 emissions per Revenue Tonne Kilometer calculation.

        Parameters
        ----------
        co2_emissions_freight
            CO2 emissions from freight air transport [MtCO2].
        rtk
            Revenue Tonne Kilometer [RTK].

        Returns
        -------
        co2_emissions_per_rtk
            CO2 emissions per Revenue Tonne Kilometer [gCO2/RTK].
        """

        self.df["co2_emissions_per_rtk"] = co2_emissions_freight * 1e6 * 1e6 / rtk
        co2_emissions_per_rtk = self.df["co2_emissions_per_rtk"]

        return co2_emissions_per_rtk


class DropinFuelConsumptionLiterPerPax100km(AeroMAPSModel):
    """
    This class computes the drop-in fuel consumption in liter per passenger per 100 km.

    Parameters
    ----------
    name : str
        Name of the model instance ('dropin_fuel_consumption_liter_per_pax_100km' by default).
    """

    def __init__(self, name="dropin_fuel_consumption_liter_per_pax_100km", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_passenger_dropin_fuel: pd.Series,
        dropin_fuel_mean_lhv: pd.Series,
        rpk: pd.Series,
    ) -> pd.Series:
        """
        Drop-in fuel consumption in liter per passenger per 100 km calculation.

        Parameters
        ----------
        energy_consumption_passenger_dropin_fuel
            Energy consumption in the form of drop-in fuels from passenger air transport [MJ].
        dropin_fuel_mean_lhv
            Mean Lower Heating Value for drop-in fuels [MJ/liter].
        rpk
            Revenue Passenger Kilometer [RPK].

        Returns
        -------
        dropin_fuel_consumption_liter_per_pax_100km
            Drop-in fuel consumption in liter per passenger per 100 km [L/PAX/100km].
        """

        density = 0.8
        self.df["dropin_fuel_consumption_liter_per_pax_100km"] = (
            energy_consumption_passenger_dropin_fuel / dropin_fuel_mean_lhv / density * 100 / rpk
        )
        dropin_fuel_consumption_liter_per_pax_100km = self.df[
            "dropin_fuel_consumption_liter_per_pax_100km"
        ]

        return dropin_fuel_consumption_liter_per_pax_100km

"""
Module for computing non-operating costs and passenger taxes.
"""

import pandas as pd
from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function


class PassengerAircraftNonOpCosts(AeroMAPSModel):
    """
    Class to compute non-operating costs for passenger aircraft based on user-defined reference years and values.

    Parameters
    ----------
    (none)
    """

    def __init__(self, name="passenger_aircraft_noc", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        noc_reference_years: list,
        noc_reference_years_values: list,
    ) -> pd.Series:
        """
        Execute the computation of non-operating costs.

        Parameters
        ----------
        noc_reference_years : list
            Scenario years corresponding to interpolation values specified in noc_reference_years_values.
        noc_reference_years_values : list
            User-defined interpolation values for non-operating costs [€/ASK].
            :units: €/ASK

        Returns
        -------
        pd.Series
            annual non-operating cost per available seat kilometer.
            :units: €/ASK
        """
        noc_prospective = aeromaps_interpolation_function(
            self,
            noc_reference_years,
            noc_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "non_operating_cost_per_ask"] = noc_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "non_operating_cost_per_ask"] = self.df.loc[
                self.prospection_start_year, "non_operating_cost_per_ask"
            ]
        non_operating_cost_per_ask = self.df["non_operating_cost_per_ask"]
        return non_operating_cost_per_ask


class PassengerAircraftPassengerTax(AeroMAPSModel):
    """
    Class to compute basic passenger taxes for passenger aircraft based on user-defined reference years and values.

    Notes
    -----
    NB: fuel based taxes are not included here.
    """

    def __init__(self, name="passenger_aircraft_passenger_tax", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        passenger_tax_reference_years: list,
        passenger_tax_reference_years_values: list,
    ) -> pd.Series:
        """
        Execute the computation of basic passenger taxes.

        Parameters
        ----------
        passenger_tax_reference_years : list
            (no additional description provided)
        passenger_tax_reference_years_values : list
            (no additional description provided)
            :units: €/ASK

        Returns
        -------
        pd.Series
            (no return description provided)
            :units: €/ASK
        """

        passenger_tax_prospective = aeromaps_interpolation_function(
            self,
            passenger_tax_reference_years,
            passenger_tax_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "passenger_tax_per_ask"] = passenger_tax_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "passenger_tax_per_ask"] = self.df.loc[
                self.prospection_start_year, "passenger_tax_per_ask"
            ]
        passenger_tax_per_ask = self.df["passenger_tax_per_ask"]
        return passenger_tax_per_ask

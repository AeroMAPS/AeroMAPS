"""
load_factor
================
Module for computing aircraft load factor evolution
"""

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class LoadFactor(AeroMAPSModel):
    """Model for computing aircraft load factor evolution based on user's inputs.

    Parameters
    ----------
    name : str
        Name of the model instance ('load_factor' by default).
    """

    def __init__(self, name="load_factor", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        load_factor_end_year: float,
        covid_load_factor_2020: float,
        rpk: pd.Series,
        ask_init: pd.Series,
    ) -> pd.Series:
        """Execute the computation of aircraft load factor.

        Historical load factor values are computed from provided RPK and
        historical ASK, initializes the 2019 load factor as a baseline, then
        projects load factor forward to `end_year` using a quadratic model.
        The 2020 value is overwritten with a Covid-19-specific value.

        Parameters
        ----------
        load_factor_end_year
            Value of mean aircraft load factor in the considered end year [%].
        covid_load_factor_2020
            Load factor due to Covid-19 for the start_year [%].
        rpk
            Total number of Revenue Passenger Kilometer (RPK).
        ask_init
            Historical number of Available Seat Kilometer (ASK) over 2000-2019 [ASK].

        Returns
        -------
        load_factor
            Mean aircraft load factor for each year of the model period [%].
        """
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "load_factor"] = rpk.loc[k] / ask_init.loc[k] * 100

        # Initialization for load factor
        load_factor_2019 = self.df.loc[2019, "load_factor"]

        # Parameters for the model
        a, b = self.parameters_load_factor_model(
            self.end_year, load_factor_2019, load_factor_end_year
        )

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "load_factor"] = a * (k - 2019) ** 2 + b * (k - 2019) + load_factor_2019

        # Covid-19 : à refaire proprement
        self.df.loc[2020, "load_factor"] = covid_load_factor_2020

        load_factor = self.df["load_factor"]

        return load_factor

    @staticmethod
    def parameters_load_factor_model(end_year, load_factor_2019, load_factor_end_year):
        """
        Compute the parameters of the quadratic model for load factor evolution.

        Parameters
        ----------
        end_year
            Year at which the target load factor is reached [yr]
        load_factor_2019
            Load factor in 2019 [%]
        load_factor_end_year
            Target load factor in end_year [%]

        Returns
        -------
        a
            Second order parameter of the quadratic model
        b
            First order parameter of the quadratic model

        """
        # Calculate via derivative : 2ax+b
        derivative = 2 * (-5.62003082e-05) * 31 + 3.59670410e-03
        a = (
            -(load_factor_end_year - load_factor_2019 - derivative * (end_year - 2019))
            / (end_year - 2019) ** 2
        )
        b = derivative - 2 * a * (end_year - 2019)
        return [a, b]

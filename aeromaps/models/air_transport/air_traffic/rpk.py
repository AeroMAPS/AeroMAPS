"""
rpk
=============================

Module for computing air traffic (RPK) without price elasticity and effect of ad-hoc measures to reduce traffic.
"""

from typing import Tuple
from numbers import Number

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeroMAPSModel, aeromaps_leveling_function


class RPK(AeroMAPSModel):
    """
    Class to compute traffic (RPK) without price elasticity considering COVID-19 impact and exogenous growth rates by segment.

    Parameters
    ----------
    name : str
        Name of the model instance ('rpk' by default).
    """

    def __init__(self, name="rpk", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk_init: pd.Series,
        short_range_rpk_share_2019: float,
        medium_range_rpk_share_2019: float,
        long_range_rpk_share_2019: float,
        covid_start_year: Number,
        covid_rpk_drop_start_year: float,
        covid_end_year_passenger: Number,
        covid_end_year_reference_rpk_ratio: float,
        cagr_passenger_short_range_reference_periods: list,
        cagr_passenger_short_range_reference_periods_values: list,
        cagr_passenger_medium_range_reference_periods: list,
        cagr_passenger_medium_range_reference_periods_values: list,
        cagr_passenger_long_range_reference_periods: list,
        cagr_passenger_long_range_reference_periods_values: list,
        rpk_short_range_measures_impact: pd.Series,
        rpk_medium_range_measures_impact: pd.Series,
        rpk_long_range_measures_impact: pd.Series,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
    ]:
        """
        RPK calculation.

        Parameters
        ----------
        rpk_init : pd.Series
            Historical number of Revenue Passenger Kilometer (RPK) over 2000-2019 [RPK].
        short_range_rpk_share_2019 : float
            Share of RPK from short-range market in 2019 [%].
        medium_range_rpk_share_2019 : float
            Share of RPK from medium-range market in 2019 [%].
        long_range_rpk_share_2019 : float
            Share of RPK from long-range market in 2019 [%].
        covid_start_year : Number
            Covid-19 start year [yr].
        covid_rpk_drop_start_year : float
            Drop in RPK due to Covid-19 for the start year [%].
        covid_end_year_passenger : Number
            Covid-19 end year [yr].
        covid_end_year_reference_rpk_ratio : float
            Percentage of traffic level reached in Covid-19 end year compared with the one in Covid-19 start year [%].
        cagr_passenger_short_range_reference_periods : list
            Reference periods for the CAGR for passenger short-range market [yr].
        cagr_passenger_short_range_reference_periods_values : list
            CAGR for passenger short-range market for the reference periods [%].
        cagr_passenger_medium_range_reference_periods : list
            Reference periods for the CAGR for passenger medium-range market [yr].
        cagr_passenger_medium_range_reference_periods_values : list
            CAGR for passenger medium-range market for the reference periods [%].
        cagr_passenger_long_range_reference_periods : list
            Reference periods for the CAGR for passenger long-range market [yr].
        cagr_passenger_long_range_reference_periods_values : list
            CAGR for passenger long-range market for the reference periods [%].
        rpk_short_range_measures_impact : pd.Series
            Traffic reduction impact of specific measures for passenger short-range market [%].
        rpk_medium_range_measures_impact : pd.Series
            Traffic reduction impact of specific measures for passenger medium-range market [%].
        rpk_long_range_measures_impact : pd.Series
            Traffic reduction impact of specific measures for passenger long-range market [%].

        Returns
        -------
        rpk_short_range : pd.Series
            Number of Revenue Passenger Kilometer (RPK) for passenger short-range market [RPK].
        rpk_medium_range : pd.Series
            Number of Revenue Passenger Kilometer (RPK) for passenger medium-range market [RPK].
        rpk_long_range : pd.Series
            Number of Revenue Passenger Kilometer (RPK) for passenger long-range market [RPK].
        rpk : pd.Series
            Number of Revenue Passenger Kilometer (RPK) for total passenger air transport [RPK].
        annual_growth_rate_passenger_short_range : pd.Series
            Annual growth rate for short-range passengers [%/year].
        annual_growth_rate_passenger_medium_range : pd.Series
            Annual growth rate for medium-range passengers [%/year].
        annual_growth_rate_passenger_long_range : pd.Series
            Annual growth rate for long-range passengers [%/year].
        annual_growth_rate_passenger : pd.Series
            Annual growth rate for total passengers [%/year].
        cagr_rpk_short_range : float
            Air traffic CAGR over prospective_years for passenger short-range market [%].
        cagr_rpk_medium_range : float
            Air traffic CAGR over prospective_years for passenger medium-range market [%].
        cagr_rpk_long_range : float
            Air traffic CAGR over prospective_years for passenger long-range market [%].
        cagr_rpk : float
            Air traffic CAGR over prospective_years for total passenger market [%].
        prospective_evolution_rpk_short_range : float
            Evolution in percentage of Revenue Passenger Kilometer (RPK) for passenger short-range market between prospection_start_year and end_year [%].
        prospective_evolution_rpk_medium_range : float
            Evolution in percentage of Revenue Passenger Kilometer (RPK) for passenger medium-range market between prospection_start_year and end_year [%].
        prospective_evolution_rpk_long_range : float
            Evolution in percentage of Revenue Passenger Kilometer (RPK) for passenger long-range market between prospection_start_year and end_year [%].
        prospective_evolution_rpk : float
            Evolution in percentage of Revenue Passenger Kilometer (RPK) for total passenger market between prospection_start_year and end_year [%].
        """
        # Initialization based on 2019 share
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "rpk_short_range"] = short_range_rpk_share_2019 / 100 * rpk_init.loc[k]
            self.df.loc[k, "rpk_medium_range"] = medium_range_rpk_share_2019 / 100 * rpk_init.loc[k]
            self.df.loc[k, "rpk_long_range"] = long_range_rpk_share_2019 / 100 * rpk_init.loc[k]

        # Covid functions
        reference_years = [covid_start_year, covid_end_year_passenger]
        reference_values_covid = [
            1 - covid_rpk_drop_start_year / 100,
            covid_end_year_reference_rpk_ratio / 100,
        ]
        covid_function = interp1d(reference_years, reference_values_covid, kind="linear")

        # CAGR function
        ## Short range
        annual_growth_rate_passenger_short_range_prospective = aeromaps_leveling_function(
            self,
            cagr_passenger_short_range_reference_periods,
            cagr_passenger_short_range_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "annual_growth_rate_passenger_short_range"] = (
            annual_growth_rate_passenger_short_range_prospective
        )
        ## Medium range
        annual_growth_rate_passenger_medium_range_prospective = aeromaps_leveling_function(
            self,
            cagr_passenger_medium_range_reference_periods,
            cagr_passenger_medium_range_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "annual_growth_rate_passenger_medium_range"] = (
            annual_growth_rate_passenger_medium_range_prospective
        )
        ## Long range
        annual_growth_rate_passenger_long_range_prospective = aeromaps_leveling_function(
            self,
            cagr_passenger_long_range_reference_periods,
            cagr_passenger_long_range_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "annual_growth_rate_passenger_long_range"] = (
            annual_growth_rate_passenger_long_range_prospective
        )

        # Short range
        for k in range(covid_start_year, covid_end_year_passenger + 1):
            self.df.loc[k, "rpk_short_range"] = self.df.loc[
                covid_start_year - 1, "rpk_short_range"
            ] * covid_function(k)
        for k in range(covid_end_year_passenger + 1, self.end_year + 1):
            self.df.loc[k, "rpk_short_range"] = self.df.loc[k - 1, "rpk_short_range"] * (
                1 + self.df.loc[k, "annual_growth_rate_passenger_short_range"] / 100
            )

        # Medium range
        for k in range(covid_start_year, covid_end_year_passenger + 1):
            self.df.loc[k, "rpk_medium_range"] = self.df.loc[
                covid_start_year - 1, "rpk_medium_range"
            ] * covid_function(k)
        for k in range(covid_end_year_passenger + 1, self.end_year + 1):
            self.df.loc[k, "rpk_medium_range"] = self.df.loc[k - 1, "rpk_medium_range"] * (
                1 + self.df.loc[k, "annual_growth_rate_passenger_medium_range"] / 100
            )

        # Long range
        for k in range(covid_start_year, covid_end_year_passenger + 1):
            self.df.loc[k, "rpk_long_range"] = self.df.loc[
                covid_start_year - 1, "rpk_long_range"
            ] * covid_function(k)
        for k in range(covid_end_year_passenger + 1, self.end_year + 1):
            self.df.loc[k, "rpk_long_range"] = self.df.loc[k - 1, "rpk_long_range"] * (
                1 + self.df.loc[k, "annual_growth_rate_passenger_long_range"] / 100
            )

        rpk_short_range = self.df["rpk_short_range"]
        rpk_medium_range = self.df["rpk_medium_range"]
        rpk_long_range = self.df["rpk_long_range"]

        rpk_short_range = rpk_short_range * rpk_short_range_measures_impact
        rpk_medium_range = rpk_medium_range * rpk_medium_range_measures_impact
        rpk_long_range = rpk_long_range * rpk_long_range_measures_impact

        self.df.loc[:, "rpk_short_range"] = rpk_short_range
        self.df.loc[:, "rpk_medium_range"] = rpk_medium_range
        self.df.loc[:, "rpk_long_range"] = rpk_long_range

        # Total
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "rpk"] = rpk_init.loc[k]
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "rpk"] = (
                self.df.loc[k, "rpk_short_range"]
                + self.df.loc[k, "rpk_medium_range"]
                + self.df.loc[k, "rpk_long_range"]
            )
        rpk = self.df["rpk"]

        # Annual growth rate
        for k in range(self.historic_start_year + 1, self.prospection_start_year):
            self.df.loc[k, "annual_growth_rate_passenger_short_range"] = (
                self.df.loc[k, "rpk_short_range"] / self.df.loc[k - 1, "rpk_short_range"] - 1
            ) * 100
        for k in range(self.historic_start_year + 1, self.prospection_start_year):
            self.df.loc[k, "annual_growth_rate_passenger_medium_range"] = (
                self.df.loc[k, "rpk_medium_range"] / self.df.loc[k - 1, "rpk_medium_range"] - 1
            ) * 100
        for k in range(self.historic_start_year + 1, self.prospection_start_year):
            self.df.loc[k, "annual_growth_rate_passenger_long_range"] = (
                self.df.loc[k, "rpk_long_range"] / self.df.loc[k - 1, "rpk_long_range"] - 1
            ) * 100
        for k in range(self.historic_start_year + 1, self.end_year + 1):
            self.df.loc[k, "annual_growth_rate_passenger"] = (
                self.df.loc[k, "rpk"] / self.df.loc[k - 1, "rpk"] - 1
            ) * 100

        annual_growth_rate_passenger_short_range = self.df[
            "annual_growth_rate_passenger_short_range"
        ]
        annual_growth_rate_passenger_medium_range = self.df[
            "annual_growth_rate_passenger_medium_range"
        ]
        annual_growth_rate_passenger_long_range = self.df["annual_growth_rate_passenger_long_range"]
        annual_growth_rate_passenger = self.df["annual_growth_rate_passenger"]

        # Compound Annual Growth Rate (CAGR)
        cagr_rpk_short_range = 100 * (
            (
                self.df.loc[self.end_year, "rpk_short_range"]
                / self.df.loc[self.prospection_start_year - 1, "rpk_short_range"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        cagr_rpk_medium_range = 100 * (
            (
                self.df.loc[self.end_year, "rpk_medium_range"]
                / self.df.loc[self.prospection_start_year - 1, "rpk_medium_range"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        cagr_rpk_long_range = 100 * (
            (
                self.df.loc[self.end_year, "rpk_long_range"]
                / self.df.loc[self.prospection_start_year - 1, "rpk_long_range"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        cagr_rpk = 100 * (
            (
                self.df.loc[self.end_year, "rpk"]
                / self.df.loc[self.prospection_start_year - 1, "rpk"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )

        # Prospective evolution of RPK (between prospection_start_year-1 and end_year)
        prospective_evolution_rpk_short_range = 100 * (
            self.df.loc[self.end_year, "rpk_short_range"]
            / self.df.loc[self.prospection_start_year - 1, "rpk_short_range"]
            - 1
        )
        prospective_evolution_rpk_medium_range = 100 * (
            self.df.loc[self.end_year, "rpk_medium_range"]
            / self.df.loc[self.prospection_start_year - 1, "rpk_medium_range"]
            - 1
        )
        prospective_evolution_rpk_long_range = 100 * (
            self.df.loc[self.end_year, "rpk_long_range"]
            / self.df.loc[self.prospection_start_year - 1, "rpk_long_range"]
            - 1
        )
        prospective_evolution_rpk = 100 * (
            self.df.loc[self.end_year, "rpk"] / self.df.loc[self.prospection_start_year - 1, "rpk"]
            - 1
        )

        self.float_outputs["cagr_rpk_short_range"] = cagr_rpk_short_range
        self.float_outputs["cagr_rpk_medium_range"] = cagr_rpk_medium_range
        self.float_outputs["cagr_rpk_long_range"] = cagr_rpk_long_range
        self.float_outputs["cagr_rpk"] = cagr_rpk
        self.float_outputs["prospective_evolution_rpk_short_range"] = (
            prospective_evolution_rpk_short_range
        )
        self.float_outputs["prospective_evolution_rpk_medium_range"] = (
            prospective_evolution_rpk_medium_range
        )
        self.float_outputs["prospective_evolution_rpk_long_range"] = (
            prospective_evolution_rpk_long_range
        )
        self.float_outputs["prospective_evolution_rpk"] = prospective_evolution_rpk

        return (
            rpk_short_range,
            rpk_medium_range,
            rpk_long_range,
            rpk,
            annual_growth_rate_passenger_short_range,
            annual_growth_rate_passenger_medium_range,
            annual_growth_rate_passenger_long_range,
            annual_growth_rate_passenger,
            cagr_rpk_short_range,
            cagr_rpk_medium_range,
            cagr_rpk_long_range,
            cagr_rpk,
            prospective_evolution_rpk_short_range,
            prospective_evolution_rpk_medium_range,
            prospective_evolution_rpk_long_range,
            prospective_evolution_rpk,
        )


class RPKReference(AeroMAPSModel):
    """
    Class to compute reference Revenue Passenger Kilometers (RPK) with baseline air traffic growth.

    Parameters
    ----------
    name : str
        Name of the model instance ('rpk_reference' by default).
    """

    def __init__(self, name="rpk_reference", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk: pd.Series,
        reference_cagr_passenger_reference_periods: list,
        reference_cagr_passenger_reference_periods_values: list,
        covid_start_year: Number,
        covid_rpk_drop_start_year: float,
        covid_end_year_passenger: Number,
        covid_end_year_reference_rpk_ratio: float,
    ) -> Tuple[pd.Series, pd.Series]:
        """
        RPK reference calculation.

        Parameters
        ----------
        rpk : pd.Series
            Number of Revenue Passenger Kilometer (RPK) for all passenger air transport [RPK].
        reference_cagr_passenger_reference_periods : list
            Reference periods for the reference CAGR for passenger market [yr].
        reference_cagr_passenger_reference_periods_values : list
            Reference CAGR for passenger market for the reference periods [%].
        covid_start_year : Number
            Covid-19 start year [yr].
        covid_rpk_drop_start_year : float
            Drop in RPK due to Covid-19 for the start year [%].
        covid_end_year_passenger : Number
            Covid-19 end year [yr].
        covid_end_year_reference_rpk_ratio : float
            Percentage of traffic level reached in Covid-19 end year compared with the one in Covid-19 start year [%].

        Returns
        -------
        rpk_reference : pd.Series
            Number of Revenue Passenger Kilometer (RPK) for all passenger air transport with a baseline air traffic growth [RPK].
        reference_annual_growth_rate_passenger : pd.Series
            Reference annual growth rate for passenger market [%/year].
        """
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "rpk_reference"] = rpk.loc[k]

        covid_start_year = int(covid_start_year)
        covid_rpk_drop_start_year = int(covid_rpk_drop_start_year)
        covid_end_year_passenger = int(covid_end_year_passenger)
        covid_end_year_reference_rpk_ratio = int(covid_end_year_reference_rpk_ratio)

        self.df.loc[covid_start_year - 1, "rpk_reference"] = rpk.loc[covid_start_year - 1]

        # Covid functions
        reference_years = [covid_start_year, covid_end_year_passenger]
        reference_values_covid = [
            1 - covid_rpk_drop_start_year / 100,
            covid_end_year_reference_rpk_ratio / 100,
        ]
        covid_function = interp1d(reference_years, reference_values_covid, kind="linear")

        # CAGR function
        reference_annual_growth_rate_passenger = aeromaps_leveling_function(
            self,
            reference_cagr_passenger_reference_periods,
            reference_cagr_passenger_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "reference_annual_growth_rate_passenger"] = (
            reference_annual_growth_rate_passenger
        )

        # Main
        for k in range(covid_start_year, covid_end_year_passenger + 1):
            self.df.loc[k, "rpk_reference"] = self.df.loc[
                covid_start_year - 1, "rpk_reference"
            ] * covid_function(k)
        for k in range(covid_end_year_passenger + 1, self.end_year + 1):
            self.df.loc[k, "rpk_reference"] = self.df.loc[k - 1, "rpk_reference"] * (
                1 + self.df.loc[k, "reference_annual_growth_rate_passenger"] / 100
            )

        rpk_reference = self.df["rpk_reference"]

        return (rpk_reference, reference_annual_growth_rate_passenger)


class RPKMeasures(AeroMAPSModel):
    """
    Class to compute the impact of ad-hoc measures to reduce short, medium, and long-range traffic.

    Parameters
    ----------
    name : str
        Name of the model instance ('rpk_measures' by default).
    """

    def __init__(self, name="rpk_measures", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk_short_range_measures_final_impact: float,
        rpk_medium_range_measures_final_impact: float,
        rpk_long_range_measures_final_impact: float,
        rpk_short_range_measures_start_year: Number,
        rpk_medium_range_measures_start_year: Number,
        rpk_long_range_measures_start_year: Number,
        rpk_short_range_measures_duration: float,
        rpk_medium_range_measures_duration: float,
        rpk_long_range_measures_duration: float,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        RPK measures impact calculation.

        Parameters
        ----------
        rpk_short_range_measures_final_impact : float
            Final impact of specific measures in terms of percentage reduction in RPK for short-range market [%].
        rpk_medium_range_measures_final_impact : float
            Final impact of specific measures in terms of percentage reduction in RPK for medium-range market [%].
        rpk_long_range_measures_final_impact : float
            Final impact of specific measures in terms of percentage reduction in RPK for long-range market [%].
        rpk_short_range_measures_start_year : Number
            Start year for implementing specific measures to reduce RPK on short-range market [yr].
        rpk_medium_range_measures_start_year : Number
            Start year for implementing specific measures to reduce RPK on medium-range market [yr].
        rpk_long_range_measures_start_year : Number
            Start year for implementing specific measures to reduce RPK on long-range market [yr].
        rpk_short_range_measures_duration : float
            Duration for implementing 98% of specific measures to reduce RPK on short-range market [yr].
        rpk_medium_range_measures_duration : float
            Duration for implementing 98% of specific measures to reduce RPK on medium-range market [yr].
        rpk_long_range_measures_duration : float
            Duration for implementing 98% of specific measures to reduce RPK on long-range market [yr].

        Returns
        -------
        rpk_short_range_measures_impact : pd.Series
            Traffic reduction impact of specific measures for passenger short-range market [%].
        rpk_medium_range_measures_impact : pd.Series
            Traffic reduction impact of specific measures for passenger medium-range market [%].
        rpk_long_range_measures_impact : pd.Series
            Traffic reduction impact of specific measures for passenger long-range market [%].
        """
        short_range_transition_year = (
            rpk_short_range_measures_start_year + rpk_short_range_measures_duration / 2
        )
        medium_range_transition_year = (
            rpk_medium_range_measures_start_year + rpk_medium_range_measures_duration / 2
        )
        long_range_transition_year = (
            rpk_long_range_measures_start_year + rpk_long_range_measures_duration / 2
        )
        rpk_short_range_measures_limit = 0.02 * rpk_short_range_measures_final_impact
        rpk_medium_range_measures_limit = 0.02 * rpk_medium_range_measures_final_impact
        rpk_long_range_measures_limit = 0.02 * rpk_long_range_measures_final_impact
        rpk_short_range_measures_parameter = np.log(100 / 2 - 1) / (
            rpk_short_range_measures_duration / 2
        )
        rpk_medium_range_measures_parameter = np.log(100 / 2 - 1) / (
            rpk_medium_range_measures_duration / 2
        )
        rpk_long_range_measures_parameter = np.log(100 / 2 - 1) / (
            rpk_long_range_measures_duration / 2
        )

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "rpk_short_range_measures_impact"] = 1
            self.df.loc[k, "rpk_medium_range_measures_impact"] = 1
            self.df.loc[k, "rpk_long_range_measures_impact"] = 1

        for k in range(self.prospection_start_year - 1, self.end_year + 1):
            if (
                rpk_short_range_measures_final_impact
                / (
                    1
                    + np.exp(
                        -rpk_short_range_measures_parameter * (k - short_range_transition_year)
                    )
                )
                < rpk_short_range_measures_limit
            ):
                self.df.loc[k, "rpk_short_range_measures_impact"] = 1
            else:
                self.df.loc[k, "rpk_short_range_measures_impact"] = (
                    1
                    - rpk_short_range_measures_final_impact
                    / 100
                    / (
                        1
                        + np.exp(
                            -rpk_short_range_measures_parameter * (k - short_range_transition_year)
                        )
                    )
                )
            if (
                rpk_medium_range_measures_final_impact
                / (
                    1
                    + np.exp(
                        -rpk_medium_range_measures_parameter * (k - medium_range_transition_year)
                    )
                )
                < rpk_medium_range_measures_limit
            ):
                self.df.loc[k, "rpk_medium_range_measures_impact"] = 1
            else:
                self.df.loc[k, "rpk_medium_range_measures_impact"] = (
                    1
                    - rpk_medium_range_measures_final_impact
                    / 100
                    / (
                        1
                        + np.exp(
                            -rpk_medium_range_measures_parameter
                            * (k - medium_range_transition_year)
                        )
                    )
                )
            if (
                rpk_long_range_measures_final_impact
                / (
                    1
                    + np.exp(-rpk_long_range_measures_parameter * (k - long_range_transition_year))
                )
                < rpk_long_range_measures_limit
            ):
                self.df.loc[k, "rpk_long_range_measures_impact"] = 1
            else:
                self.df.loc[k, "rpk_long_range_measures_impact"] = (
                    1
                    - rpk_long_range_measures_final_impact
                    / 100
                    / (
                        1
                        + np.exp(
                            -rpk_long_range_measures_parameter * (k - long_range_transition_year)
                        )
                    )
                )

        rpk_short_range_measures_impact = self.df["rpk_short_range_measures_impact"]
        rpk_medium_range_measures_impact = self.df["rpk_medium_range_measures_impact"]
        rpk_long_range_measures_impact = self.df["rpk_long_range_measures_impact"]

        return (
            rpk_short_range_measures_impact,
            rpk_medium_range_measures_impact,
            rpk_long_range_measures_impact,
        )

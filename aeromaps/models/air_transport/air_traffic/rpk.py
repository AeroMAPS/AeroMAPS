from typing import Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeromapsModel, AeromapsLevelingFunction


class RPK(AeromapsModel):
    def __init__(self, name="rpk", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk_init: pd.Series = pd.Series(dtype="float64"),
        short_range_rpk_share_2019: float = 0.0,
        medium_range_rpk_share_2019: float = 0.0,
        long_range_rpk_share_2019: float = 0.0,
        covid_start_year: int = 0,
        covid_rpk_drop_start_year: float = 0.0,
        covid_end_year: int = 0,
        covid_end_year_reference_rpk_ratio: float = 0.0,
        cagr_passenger_short_range_reference_periods: list = [],
        cagr_passenger_short_range_reference_periods_values: list = [],
        cagr_passenger_medium_range_reference_periods: list = [],
        cagr_passenger_medium_range_reference_periods_values: list = [],
        cagr_passenger_long_range_reference_periods: list = [],
        cagr_passenger_long_range_reference_periods_values: list = [],
        rpk_short_range_measures_impact: pd.Series = pd.Series(dtype="float64"),
        rpk_medium_range_measures_impact: pd.Series = pd.Series(dtype="float64"),
        rpk_long_range_measures_impact: pd.Series = pd.Series(dtype="float64"),
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
        """RPK calculation."""

        # Initialization based on 2019 share
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "rpk_short_range"] = short_range_rpk_share_2019 / 100 * rpk_init.loc[k]
            self.df.loc[k, "rpk_medium_range"] = medium_range_rpk_share_2019 / 100 * rpk_init.loc[k]
            self.df.loc[k, "rpk_long_range"] = long_range_rpk_share_2019 / 100 * rpk_init.loc[k]

        # Covid functions
        reference_years = [covid_start_year, covid_end_year]
        reference_values_covid = [
            1 - covid_rpk_drop_start_year / 100,
            covid_end_year_reference_rpk_ratio / 100,
        ]
        covid_function = interp1d(reference_years, reference_values_covid, kind="linear")

        # CAGR function
        ## Short range
        annual_growth_rate_passenger_short_range_prospective = AeromapsLevelingFunction(
            self,
            cagr_passenger_short_range_reference_periods,
            cagr_passenger_short_range_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[
            :, "annual_growth_rate_passenger_short_range"
        ] = annual_growth_rate_passenger_short_range_prospective
        ## Medium range
        annual_growth_rate_passenger_medium_range_prospective = AeromapsLevelingFunction(
            self,
            cagr_passenger_medium_range_reference_periods,
            cagr_passenger_medium_range_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[
            :, "annual_growth_rate_passenger_medium_range"
        ] = annual_growth_rate_passenger_medium_range_prospective
        ## Long range
        annual_growth_rate_passenger_long_range_prospective = AeromapsLevelingFunction(
            self,
            cagr_passenger_long_range_reference_periods,
            cagr_passenger_long_range_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[
            :, "annual_growth_rate_passenger_long_range"
        ] = annual_growth_rate_passenger_long_range_prospective

        # Short range
        for k in range(covid_start_year, covid_end_year + 1):
            self.df.loc[k, "rpk_short_range"] = self.df.loc[
                covid_start_year - 1, "rpk_short_range"
            ] * covid_function(k)
        for k in range(covid_end_year + 1, self.end_year + 1):
            self.df.loc[k, "rpk_short_range"] = self.df.loc[k - 1, "rpk_short_range"] * (
                1 + self.df.loc[k, "annual_growth_rate_passenger_short_range"] / 100
            )

        # Medium range
        for k in range(covid_start_year, covid_end_year + 1):
            self.df.loc[k, "rpk_medium_range"] = self.df.loc[
                covid_start_year - 1, "rpk_medium_range"
            ] * covid_function(k)
        for k in range(covid_end_year + 1, self.end_year + 1):
            self.df.loc[k, "rpk_medium_range"] = self.df.loc[k - 1, "rpk_medium_range"] * (
                1 + self.df.loc[k, "annual_growth_rate_passenger_medium_range"] / 100
            )

        # Long range
        for k in range(covid_start_year, covid_end_year + 1):
            self.df.loc[k, "rpk_long_range"] = self.df.loc[
                covid_start_year - 1, "rpk_long_range"
            ] * covid_function(k)
        for k in range(covid_end_year + 1, self.end_year + 1):
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
            self.df.loc[k, "annual_growth_rate_passenger_short_range"] = (
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
        self.float_outputs[
            "prospective_evolution_rpk_short_range"
        ] = prospective_evolution_rpk_short_range
        self.float_outputs[
            "prospective_evolution_rpk_medium_range"
        ] = prospective_evolution_rpk_medium_range
        self.float_outputs[
            "prospective_evolution_rpk_long_range"
        ] = prospective_evolution_rpk_long_range
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


class RPKReference(AeromapsModel):
    def __init__(self, name="rpk_reference", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk: pd.Series = pd.Series(dtype="float64"),
        reference_cagr_aviation_reference_periods: list = [],
        reference_cagr_aviation_reference_periods_values: list = [],
        covid_start_year: int = 0,
        covid_rpk_drop_start_year: int = 0,
        covid_end_year: int = 0,
        covid_end_year_reference_rpk_ratio: int = 0,
    ) -> Tuple[pd.Series, pd.Series]:
        """RPK reference calculation."""

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "rpk_reference"] = rpk.loc[k]

        covid_start_year = int(covid_start_year)
        covid_rpk_drop_start_year = int(covid_rpk_drop_start_year)
        covid_end_year = int(covid_end_year)
        covid_end_year_reference_rpk_ratio = int(covid_end_year_reference_rpk_ratio)

        self.df.loc[covid_start_year - 1, "rpk_reference"] = rpk.loc[covid_start_year - 1]

        # Covid functions
        reference_years = [covid_start_year, covid_end_year]
        reference_values_covid = [
            1 - covid_rpk_drop_start_year / 100,
            covid_end_year_reference_rpk_ratio / 100,
        ]
        covid_function = interp1d(reference_years, reference_values_covid, kind="linear")

        # CAGR function
        reference_annual_growth_rate_aviation = AeromapsLevelingFunction(
            self,
            reference_cagr_aviation_reference_periods,
            reference_cagr_aviation_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[
            :, "reference_annual_growth_rate_aviation"
        ] = reference_annual_growth_rate_aviation

        # Main
        for k in range(covid_start_year, covid_end_year + 1):
            self.df.loc[k, "rpk_reference"] = self.df.loc[
                covid_start_year - 1, "rpk_reference"
            ] * covid_function(k)
        for k in range(covid_end_year + 1, self.end_year + 1):
            self.df.loc[k, "rpk_reference"] = self.df.loc[k - 1, "rpk_reference"] * (
                1 + self.df.loc[k, "reference_annual_growth_rate_aviation"] / 100
            )

        rpk_reference = self.df["rpk_reference"]

        return (rpk_reference, reference_annual_growth_rate_aviation)


class RPKMeasures(AeromapsModel):
    def __init__(self, name="rpk_measures", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk_short_range_measures_final_impact: float,
        rpk_medium_range_measures_final_impact: float,
        rpk_long_range_measures_final_impact: float,
        rpk_short_range_measures_start_year: float,
        rpk_medium_range_measures_start_year: float,
        rpk_long_range_measures_start_year: float,
        rpk_short_range_measures_duration: float,
        rpk_medium_range_measures_duration: float,
        rpk_long_range_measures_duration: float,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """RPK measures impact calculation."""

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
                self.df.loc[
                    k, "rpk_short_range_measures_impact"
                ] = 1 - rpk_short_range_measures_final_impact / 100 / (
                    1
                    + np.exp(
                        -rpk_short_range_measures_parameter * (k - short_range_transition_year)
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
                self.df.loc[
                    k, "rpk_medium_range_measures_impact"
                ] = 1 - rpk_medium_range_measures_final_impact / 100 / (
                    1
                    + np.exp(
                        -rpk_medium_range_measures_parameter * (k - medium_range_transition_year)
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
                self.df.loc[
                    k, "rpk_long_range_measures_impact"
                ] = 1 - rpk_long_range_measures_final_impact / 100 / (
                    1
                    + np.exp(-rpk_long_range_measures_parameter * (k - long_range_transition_year))
                )

        rpk_short_range_measures_impact = self.df["rpk_short_range_measures_impact"]
        rpk_medium_range_measures_impact = self.df["rpk_medium_range_measures_impact"]
        rpk_long_range_measures_impact = self.df["rpk_long_range_measures_impact"]

        return (
            rpk_short_range_measures_impact,
            rpk_medium_range_measures_impact,
            rpk_long_range_measures_impact,
        )

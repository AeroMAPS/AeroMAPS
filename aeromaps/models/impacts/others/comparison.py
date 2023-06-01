from typing import Tuple

import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel


class CarbonBudgetConsumedShare(AeromapsModel):
    def __init__(self, name="carbon_budget_consumed_share", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        cumulative_co2_emissions: pd.Series = pd.Series(dtype="float64"),
        cumulative_total_equivalent_emissions: pd.Series = pd.Series(dtype="float64"),
        gross_carbon_budget_2050: float = 0.0,
        equivalent_gross_carbon_budget_2050: float = 0.0,
    ) -> Tuple[float, float]:
        """(Equivalent) Carbon budget consumption share calculation."""

        carbon_budget_consumed_share = (
            cumulative_co2_emissions.loc[self.end_year] / gross_carbon_budget_2050 * 100
        )
        equivalent_carbon_budget_consumed_share = (
            cumulative_total_equivalent_emissions.loc[self.end_year]
            / equivalent_gross_carbon_budget_2050
            * 100
        )

        self.float_outputs["carbon_budget_consumed_share"] = carbon_budget_consumed_share
        self.float_outputs[
            "equivalent_carbon_budget_consumed_share"
        ] = equivalent_carbon_budget_consumed_share

        return carbon_budget_consumed_share, equivalent_carbon_budget_consumed_share


class ResourcesConsumedShare(AeromapsModel):
    def __init__(self, name="resources_consumed_share", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        biomass_consumption_end_year: float = 0.0,
        electricity_consumption_end_year: float = 0.0,
        available_biomass_total: float = 0.0,
        available_electricity: float = 0.0,
    ) -> Tuple[float, float]:
        """Resources consumption share calculation."""

        biomass_consumed_share = biomass_consumption_end_year / available_biomass_total * 100
        electricity_consumed_share = electricity_consumption_end_year / available_electricity * 100

        self.float_outputs["biomass_consumed_share"] = biomass_consumed_share
        self.float_outputs["electricity_consumed_share"] = electricity_consumed_share

        return biomass_consumed_share, electricity_consumed_share

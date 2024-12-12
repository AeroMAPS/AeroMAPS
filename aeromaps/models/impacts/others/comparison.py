from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class CarbonBudgetConsumedShare(AeroMAPSModel):
    def __init__(self, name="carbon_budget_consumed_share", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        cumulative_co2_emissions: pd.Series,
        gross_carbon_budget_2050: float,
    ) -> float:
        """Carbon budget consumption share calculation."""

        carbon_budget_consumed_share = (
            cumulative_co2_emissions.loc[self.end_year] / gross_carbon_budget_2050 * 100
        )

        self.float_outputs["carbon_budget_consumed_share"] = carbon_budget_consumed_share

        return carbon_budget_consumed_share


class EquivalentCarbonBudgetConsumedShare(AeroMAPSModel):
    def __init__(self, name="equivalent_carbon_budget_consumed_share", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        cumulative_total_equivalent_emissions: pd.Series,
        equivalent_gross_carbon_budget_2050: float,
    ) -> float:
        """Equivalent Carbon budget consumption share calculation."""

        equivalent_carbon_budget_consumed_share = (
            cumulative_total_equivalent_emissions.loc[self.end_year]
            / equivalent_gross_carbon_budget_2050
            * 100
        )

        self.float_outputs["equivalent_carbon_budget_consumed_share"] = (
            equivalent_carbon_budget_consumed_share
        )

        return equivalent_carbon_budget_consumed_share


class ResourcesConsumedShare(AeroMAPSModel):
    def __init__(self, name="resources_consumed_share", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        biomass_consumption_end_year: float,
        electricity_consumption_end_year: float,
        available_biomass_total: float,
        available_electricity: float,
    ) -> Tuple[float, float]:
        """Resources consumption share calculation."""

        biomass_consumed_share = biomass_consumption_end_year / available_biomass_total * 100
        electricity_consumed_share = electricity_consumption_end_year / available_electricity * 100

        self.float_outputs["biomass_consumed_share"] = biomass_consumed_share
        self.float_outputs["electricity_consumed_share"] = electricity_consumed_share

        return biomass_consumed_share, electricity_consumed_share

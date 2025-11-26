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


class TemperatureTargetConsumedShare(AeroMAPSModel):
    def __init__(self, name="carbon_budget_consumed_share", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        historical_temperature_increase: float,
        temperature_target: float,
        temperature_increase_from_aviation: pd.Series,
    ) -> float:
        """Temperature target consumption share calculation."""

        temperature_target_consumed_share = (
            (temperature_increase_from_aviation.loc[self.end_year] -
            temperature_increase_from_aviation.loc[self.prospection_start_year]) / (
                         temperature_target - historical_temperature_increase) * 100
             )

        self.float_outputs["temperature_target_consumed_share"] = temperature_target_consumed_share

        return temperature_target_consumed_share
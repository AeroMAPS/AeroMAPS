# @Time : 04/01/2024 15:41
# @Author : a.salgas
# @File : total_airline_cost_and_airfare.py
# @Software: PyCharm
from typing import Tuple
import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class PassengerAircraftTotalCostAirfare(AeroMAPSModel):
    def __init__(
        self, name="passenger_aircraft_total_cost_and_airfare", fleet_model=None, *args, **kwargs
    ):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        doc_non_energy_per_ask_mean: pd.Series,
        doc_energy_per_ask_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_mean: pd.Series,
        noc_carbon_offset_per_ask: pd.Series,
        non_operating_cost_per_ask: pd.Series,
        indirect_operating_cost_per_ask: pd.Series,
        passenger_tax_per_ask: pd.Series,
        operational_profit_per_ask: pd.Series,
        operational_efficiency_cost_non_energy_per_ask: pd.Series,
        load_factor_cost_non_energy_per_ask: pd.Series,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        # Cost without any tax
        total_cost_per_ask_without_extra_tax = (
            doc_non_energy_per_ask_mean
            + doc_energy_per_ask_mean
            + non_operating_cost_per_ask
            + indirect_operating_cost_per_ask
            + noc_carbon_offset_per_ask
            + operational_efficiency_cost_non_energy_per_ask
            + load_factor_cost_non_energy_per_ask
        )

        # Tax revenue
        total_extra_tax_per_ask = (
            doc_carbon_tax_lowering_offset_per_ask_mean + passenger_tax_per_ask
        )

        # Cost
        total_cost_per_ask = total_cost_per_ask_without_extra_tax + total_extra_tax_per_ask

        # Airfare
        airfare_per_ask = total_cost_per_ask + operational_profit_per_ask

        self.df.loc[:, "total_cost_per_ask_without_extra_tax"] = (
            total_cost_per_ask_without_extra_tax
        )

        self.df.loc[:, "total_extra_tax_per_ask"] = total_extra_tax_per_ask

        self.df.loc[:, "total_cost_per_ask"] = total_cost_per_ask

        self.df.loc[:, "airfare_per_ask"] = airfare_per_ask

        return (
            total_cost_per_ask_without_extra_tax,
            total_extra_tax_per_ask,
            total_cost_per_ask,
            airfare_per_ask,
        )

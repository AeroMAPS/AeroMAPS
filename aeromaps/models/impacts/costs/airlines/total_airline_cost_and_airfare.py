# @Time : 04/01/2024 15:41
# @Author : a.salgas
# @File : total_airline_cost_and_airfare.py
# @Software: PyCharm
from typing import Tuple

# import numpy as np
import pandas as pd
# from scipy.interpolate import interp1d

from aeromaps.models.base import AeroMAPSModel  # , aeromaps_interpolation_function


class PassengerAircraftTotalCostAirfare(AeroMAPSModel):
    def __init__(
        self, name="passenger_aircraft_total_cost_and_airfare", fleet_model=None, *args, **kwargs
    ):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        doc_non_energy_per_ask_mean: pd.Series,
        doc_non_energy_per_ask_short_range_mean: pd.Series,
        doc_non_energy_per_ask_medium_range_mean: pd.Series,
        doc_non_energy_per_ask_long_range_mean: pd.Series,
        doc_energy_per_ask_mean: pd.Series,
        doc_energy_per_ask_short_range_mean: pd.Series,
        doc_energy_per_ask_medium_range_mean: pd.Series,
        doc_energy_per_ask_long_range_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_short_range_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_medium_range_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_long_range_mean: pd.Series,
        noc_carbon_offset_per_ask: pd.Series,
        non_operating_cost_per_ask: pd.Series,
        indirect_operating_cost_per_ask: pd.Series,
        passenger_tax_per_ask: pd.Series,
        operational_profit_per_ask: pd.Series,
        operational_efficiency_cost_non_energy_per_ask: pd.Series,
        load_factor_cost_non_energy_per_ask: pd.Series,
        load_factor: pd.Series,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        ######## Overall #########

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

        total_cost_per_ask_without_extra_tax_short_range = (
            doc_non_energy_per_ask_short_range_mean
            + doc_energy_per_ask_short_range_mean
            + non_operating_cost_per_ask
            + indirect_operating_cost_per_ask
            + noc_carbon_offset_per_ask
            + operational_efficiency_cost_non_energy_per_ask
            + load_factor_cost_non_energy_per_ask
        )

        total_cost_per_ask_without_extra_tax_medium_range = (
            doc_non_energy_per_ask_medium_range_mean
            + doc_energy_per_ask_medium_range_mean
            + non_operating_cost_per_ask
            + indirect_operating_cost_per_ask
            + noc_carbon_offset_per_ask
            + operational_efficiency_cost_non_energy_per_ask
            + load_factor_cost_non_energy_per_ask
        )

        total_cost_per_ask_without_extra_tax_long_range = (
            doc_non_energy_per_ask_long_range_mean
            + doc_energy_per_ask_long_range_mean
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
        total_extra_tax_per_ask_short_range = (
            doc_carbon_tax_lowering_offset_per_ask_short_range_mean + passenger_tax_per_ask
        )
        total_extra_tax_per_ask_medium_range = (
            doc_carbon_tax_lowering_offset_per_ask_medium_range_mean + passenger_tax_per_ask
        )
        total_extra_tax_per_ask_long_range = (
            doc_carbon_tax_lowering_offset_per_ask_long_range_mean + passenger_tax_per_ask
        )

        # Cost
        total_cost_per_ask = total_cost_per_ask_without_extra_tax + total_extra_tax_per_ask
        total_cost_per_ask_short_range = (
            total_cost_per_ask_without_extra_tax_short_range + total_extra_tax_per_ask_short_range
        )
        total_cost_per_ask_medium_range = (
            total_cost_per_ask_without_extra_tax_medium_range + total_extra_tax_per_ask_medium_range
        )
        total_cost_per_ask_long_range = (
            total_cost_per_ask_without_extra_tax_long_range + total_extra_tax_per_ask_long_range
        )

        # Airfare per ask
        airfare_per_ask = total_cost_per_ask + operational_profit_per_ask
        airfare_per_ask_short_range = total_cost_per_ask_short_range + operational_profit_per_ask
        airfare_per_ask_medium_range = total_cost_per_ask_medium_range + operational_profit_per_ask
        airfare_per_ask_long_range = total_cost_per_ask_long_range + operational_profit_per_ask

        # Airfare per rpk
        airfare_per_rpk = airfare_per_ask / (load_factor / 100)
        airfare_per_rpk_short_range = airfare_per_ask_short_range / (load_factor / 100)
        airfare_per_rpk_medium_range = airfare_per_ask_medium_range / (load_factor / 100)
        airfare_per_rpk_long_range = airfare_per_ask_long_range / (load_factor / 100)

        # Tax per rpk
        total_extra_tax_per_rpk = total_extra_tax_per_ask / (load_factor / 100)
        total_extra_tax_per_rpk_short_range = total_extra_tax_per_ask_short_range / (
            load_factor / 100
        )
        total_extra_tax_per_rpk_medium_range = total_extra_tax_per_ask_medium_range / (
            load_factor / 100
        )
        total_extra_tax_per_rpk_long_range = total_extra_tax_per_ask_long_range / (
            load_factor / 100
        )

        self.df.loc[:, "total_cost_per_ask_without_extra_tax"] = (
            total_cost_per_ask_without_extra_tax
        )
        self.df.loc[:, "total_cost_per_ask_without_extra_tax_short_range"] = (
            total_cost_per_ask_without_extra_tax_short_range
        )
        self.df.loc[:, "total_cost_per_ask_without_extra_tax_medium_range"] = (
            total_cost_per_ask_without_extra_tax_medium_range
        )
        self.df.loc[:, "total_cost_per_ask_without_extra_tax_long_range"] = (
            total_cost_per_ask_without_extra_tax_long_range
        )

        self.df.loc[:, "total_extra_tax_per_ask"] = total_extra_tax_per_ask
        self.df.loc[:, "total_extra_tax_per_ask_short_range"] = total_extra_tax_per_ask_short_range
        self.df.loc[:, "total_extra_tax_per_ask_medium_range"] = (
            total_extra_tax_per_ask_medium_range
        )
        self.df.loc[:, "total_extra_tax_per_ask_long_range"] = total_extra_tax_per_ask_long_range

        self.df.loc[:, "total_extra_tax_per_rpk"] = total_extra_tax_per_rpk
        self.df.loc[:, "total_extra_tax_per_rpk_short_range"] = total_extra_tax_per_rpk_short_range
        self.df.loc[:, "total_extra_tax_per_rpk_medium_range"] = (
            total_extra_tax_per_rpk_medium_range
        )
        self.df.loc[:, "total_extra_tax_per_rpk_long_range"] = total_extra_tax_per_rpk_long_range

        self.df.loc[:, "total_cost_per_ask"] = total_cost_per_ask
        self.df.loc[:, "total_cost_per_ask_short_range"] = total_cost_per_ask_short_range
        self.df.loc[:, "total_cost_per_ask_medium_range"] = total_cost_per_ask_medium_range
        self.df.loc[:, "total_cost_per_ask_long_range"] = total_cost_per_ask_long_range

        self.df.loc[:, "airfare_per_ask"] = airfare_per_ask
        self.df.loc[:, "airfare_per_ask_short_range"] = airfare_per_ask_short_range
        self.df.loc[:, "airfare_per_ask_medium_range"] = airfare_per_ask_medium_range
        self.df.loc[:, "airfare_per_ask_long_range"] = airfare_per_ask_long_range

        self.df.loc[:, "airfare_per_rpk"] = airfare_per_rpk
        self.df.loc[:, "airfare_per_rpk_short_range"] = airfare_per_rpk_short_range
        self.df.loc[:, "airfare_per_rpk_medium_range"] = airfare_per_rpk_medium_range
        self.df.loc[:, "airfare_per_rpk_long_range"] = airfare_per_rpk_long_range

        return (
            total_cost_per_ask_without_extra_tax,
            total_cost_per_ask_without_extra_tax_short_range,
            total_cost_per_ask_without_extra_tax_medium_range,
            total_cost_per_ask_without_extra_tax_long_range,
            total_extra_tax_per_ask,
            total_extra_tax_per_ask_short_range,
            total_extra_tax_per_ask_medium_range,
            total_extra_tax_per_ask_long_range,
            total_extra_tax_per_rpk,
            total_extra_tax_per_rpk_short_range,
            total_extra_tax_per_rpk_medium_range,
            total_extra_tax_per_rpk_long_range,
            total_cost_per_ask,
            total_cost_per_ask_short_range,
            total_cost_per_ask_medium_range,
            total_cost_per_ask_long_range,
            airfare_per_ask,
            airfare_per_ask_short_range,
            airfare_per_ask_medium_range,
            airfare_per_ask_long_range,
            airfare_per_rpk,
            airfare_per_rpk_short_range,
            airfare_per_rpk_medium_range,
            airfare_per_rpk_long_range,
        )


class PassengerAircraftTotalCost(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_total_cost", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        doc_non_energy_per_ask_mean: pd.Series,
        doc_non_energy_per_ask_short_range_mean: pd.Series,
        doc_non_energy_per_ask_medium_range_mean: pd.Series,
        doc_non_energy_per_ask_long_range_mean: pd.Series,
        doc_energy_per_ask_mean: pd.Series,
        doc_energy_per_ask_short_range_mean: pd.Series,
        doc_energy_per_ask_medium_range_mean: pd.Series,
        doc_energy_per_ask_long_range_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_short_range_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_medium_range_mean: pd.Series,
        doc_carbon_tax_lowering_offset_per_ask_long_range_mean: pd.Series,
        noc_carbon_offset_per_ask: pd.Series,
        non_operating_cost_per_ask: pd.Series,
        indirect_operating_cost_per_ask: pd.Series,
        passenger_tax_per_ask: pd.Series,
        operational_efficiency_cost_non_energy_per_ask: pd.Series,
        load_factor_cost_non_energy_per_ask: pd.Series,
        load_factor: pd.Series,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        ######## Overall #########

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

        total_cost_per_ask_without_extra_tax_short_range = (
            doc_non_energy_per_ask_short_range_mean
            + doc_energy_per_ask_short_range_mean
            + non_operating_cost_per_ask
            + indirect_operating_cost_per_ask
            + noc_carbon_offset_per_ask
            + operational_efficiency_cost_non_energy_per_ask
            + load_factor_cost_non_energy_per_ask
        )

        total_cost_per_ask_without_extra_tax_medium_range = (
            doc_non_energy_per_ask_medium_range_mean
            + doc_energy_per_ask_medium_range_mean
            + non_operating_cost_per_ask
            + indirect_operating_cost_per_ask
            + noc_carbon_offset_per_ask
            + operational_efficiency_cost_non_energy_per_ask
            + load_factor_cost_non_energy_per_ask
        )

        total_cost_per_ask_without_extra_tax_long_range = (
            doc_non_energy_per_ask_long_range_mean
            + doc_energy_per_ask_long_range_mean
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
        total_extra_tax_per_ask_short_range = (
            doc_carbon_tax_lowering_offset_per_ask_short_range_mean + passenger_tax_per_ask
        )
        total_extra_tax_per_ask_medium_range = (
            doc_carbon_tax_lowering_offset_per_ask_medium_range_mean + passenger_tax_per_ask
        )
        total_extra_tax_per_ask_long_range = (
            doc_carbon_tax_lowering_offset_per_ask_long_range_mean + passenger_tax_per_ask
        )

        # Average Cost per ask
        total_cost_per_ask = total_cost_per_ask_without_extra_tax + total_extra_tax_per_ask
        total_cost_per_ask_short_range = (
            total_cost_per_ask_without_extra_tax_short_range + total_extra_tax_per_ask_short_range
        )
        total_cost_per_ask_medium_range = (
            total_cost_per_ask_without_extra_tax_medium_range + total_extra_tax_per_ask_medium_range
        )
        total_cost_per_ask_long_range = (
            total_cost_per_ask_without_extra_tax_long_range + total_extra_tax_per_ask_long_range
        )

        # Cost per rpk
        total_cost_per_rpk_without_extra_tax = total_cost_per_ask_without_extra_tax / (
            load_factor / 100
        )
        total_cost_per_rpk_without_extra_tax_short_range = (
            total_cost_per_ask_without_extra_tax_short_range / (load_factor / 100)
        )
        total_cost_per_rpk_without_extra_tax_medium_range = (
            total_cost_per_ask_without_extra_tax_medium_range / (load_factor / 100)
        )
        total_cost_per_rpk_without_extra_tax_long_range = (
            total_cost_per_ask_without_extra_tax_long_range / (load_factor / 100)
        )

        # Tax per rpk
        total_extra_tax_per_rpk = total_extra_tax_per_ask / (load_factor / 100)
        total_extra_tax_per_rpk_short_range = total_extra_tax_per_ask_short_range / (
            load_factor / 100
        )
        total_extra_tax_per_rpk_medium_range = total_extra_tax_per_ask_medium_range / (
            load_factor / 100
        )
        total_extra_tax_per_rpk_long_range = total_extra_tax_per_ask_long_range / (
            load_factor / 100
        )

        # Average Cost per rpk
        total_cost_per_rpk = total_cost_per_rpk_without_extra_tax + total_extra_tax_per_rpk
        total_cost_per_rpk_short_range = (
            total_cost_per_rpk_without_extra_tax_short_range + total_extra_tax_per_rpk_short_range
        )
        total_cost_per_rpk_medium_range = (
            total_cost_per_rpk_without_extra_tax_medium_range + total_extra_tax_per_rpk_medium_range
        )
        total_cost_per_rpk_long_range = (
            total_cost_per_rpk_without_extra_tax_long_range + total_extra_tax_per_rpk_long_range
        )

        self.df.loc[:, "total_cost_per_ask_without_extra_tax"] = (
            total_cost_per_ask_without_extra_tax
        )
        self.df.loc[:, "total_cost_per_ask_without_extra_tax_short_range"] = (
            total_cost_per_ask_without_extra_tax_short_range
        )
        self.df.loc[:, "total_cost_per_ask_without_extra_tax_medium_range"] = (
            total_cost_per_ask_without_extra_tax_medium_range
        )
        self.df.loc[:, "total_cost_per_ask_without_extra_tax_long_range"] = (
            total_cost_per_ask_without_extra_tax_long_range
        )

        self.df.loc[:, "total_extra_tax_per_ask"] = total_extra_tax_per_ask
        self.df.loc[:, "total_extra_tax_per_ask_short_range"] = total_extra_tax_per_ask_short_range
        self.df.loc[:, "total_extra_tax_per_ask_medium_range"] = (
            total_extra_tax_per_ask_medium_range
        )
        self.df.loc[:, "total_extra_tax_per_ask_long_range"] = total_extra_tax_per_ask_long_range

        self.df.loc[:, "total_extra_tax_per_rpk"] = total_extra_tax_per_rpk
        self.df.loc[:, "total_extra_tax_per_rpk_short_range"] = total_extra_tax_per_rpk_short_range
        self.df.loc[:, "total_extra_tax_per_rpk_medium_range"] = (
            total_extra_tax_per_rpk_medium_range
        )
        self.df.loc[:, "total_extra_tax_per_rpk_long_range"] = total_extra_tax_per_rpk_long_range

        self.df.loc[:, "total_cost_per_ask"] = total_cost_per_ask
        self.df.loc[:, "total_cost_per_ask_short_range"] = total_cost_per_ask_short_range
        self.df.loc[:, "total_cost_per_ask_medium_range"] = total_cost_per_ask_medium_range
        self.df.loc[:, "total_cost_per_ask_long_range"] = total_cost_per_ask_long_range

        self.df.loc[:, "total_cost_per_rpk_without_extra_tax"] = (
            total_cost_per_rpk_without_extra_tax
        )
        self.df.loc[:, "total_cost_per_rpk_without_extra_tax_short_range"] = (
            total_cost_per_rpk_without_extra_tax_short_range
        )
        self.df.loc[:, "total_cost_per_rpk_without_extra_tax_medium_range"] = (
            total_cost_per_rpk_without_extra_tax_medium_range
        )
        self.df.loc[:, "total_cost_per_rpk_without_extra_tax_long_range"] = (
            total_cost_per_rpk_without_extra_tax_long_range
        )

        self.df.loc[:, "total_cost_per_rpk"] = total_cost_per_rpk
        self.df.loc[:, "total_cost_per_rpk_short_range"] = total_cost_per_rpk_short_range
        self.df.loc[:, "total_cost_per_rpk_medium_range"] = total_cost_per_rpk_medium_range
        self.df.loc[:, "total_cost_per_rpk_long_range"] = total_cost_per_rpk_long_range

        return (
            total_cost_per_ask_without_extra_tax,
            total_cost_per_ask_without_extra_tax_short_range,
            total_cost_per_ask_without_extra_tax_medium_range,
            total_cost_per_ask_without_extra_tax_long_range,
            total_extra_tax_per_ask,
            total_extra_tax_per_ask_short_range,
            total_extra_tax_per_ask_medium_range,
            total_extra_tax_per_ask_long_range,
            total_extra_tax_per_rpk,
            total_extra_tax_per_rpk_short_range,
            total_extra_tax_per_rpk_medium_range,
            total_extra_tax_per_rpk_long_range,
            total_cost_per_ask,
            total_cost_per_ask_short_range,
            total_cost_per_ask_medium_range,
            total_cost_per_ask_long_range,
            total_cost_per_rpk_without_extra_tax,
            total_cost_per_rpk_without_extra_tax_short_range,
            total_cost_per_rpk_without_extra_tax_medium_range,
            total_cost_per_rpk_without_extra_tax_long_range,
            total_cost_per_rpk,
            total_cost_per_rpk_short_range,
            total_cost_per_rpk_medium_range,
            total_cost_per_rpk_long_range,
        )


class PassengerAircraftMarginalCost(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_marginal_cost", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk: pd.Series,
        # airfare_per_rpk: np.ndarray,
        rpk_no_elasticity: pd.Series,
        total_cost_per_rpk_without_extra_tax: pd.Series,
        total_extra_tax_per_rpk: pd.Series,
        initial_price_per_rpk: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        # np.ndarray,
    ]:
        # airfare_per_rpk = pd.Series(airfare_per_rpk, index=range(2025,2051))
        # interp_af = interp1d([2025, 2030, 2035, 2040, 2045, 2050], airfare_per_rpk, kind="linear")
        #
        # years_new = np.arange(2025, 2051, 1)
        # airfare_per_rpk = interp_af(years_new)
        # airfare_per_rpk = pd.Series(airfare_per_rpk, index=range(2025, 2051))

        intial_total_cost_per_rpk_without_extra_tax = total_cost_per_rpk_without_extra_tax[
            self.prospection_start_year - 1
        ]
        initial_price_per_rpk_corrected = (
            initial_price_per_rpk - 0.078692893 + intial_total_cost_per_rpk_without_extra_tax
        )

        b = 2 * intial_total_cost_per_rpk_without_extra_tax - initial_price_per_rpk_corrected
        a = (
            2
            * (initial_price_per_rpk_corrected - intial_total_cost_per_rpk_without_extra_tax)
            / rpk_no_elasticity
        )

        # For latter update replace total cost by the step component of the marginal cost.
        marginal_cost_per_rpk = (
            a * rpk
            + b
            + total_cost_per_rpk_without_extra_tax
            - intial_total_cost_per_rpk_without_extra_tax
        )

        airfare_per_rpk_true = marginal_cost_per_rpk + total_extra_tax_per_rpk
        airfare_per_rpk_true = airfare_per_rpk_true
        airfare_per_rpk = airfare_per_rpk_true

        # print('a',a[self.end_year], 'b', b + total_cost_per_rpk_without_extra_tax[self.end_year] - intial_total_cost_per_rpk_without_extra_tax + total_extra_tax_per_rpk[self.end_year])
        # print('checker',marginal_cost_per_rpk[self.end_year], rpk[self.end_year], airfare_per_rpk[self.end_year])

        self.df.loc[:, "marginal_cost_per_rpk"] = marginal_cost_per_rpk
        self.df.loc[:, "airfare_per_rpk"] = airfare_per_rpk
        # self.df.loc[:, "airfare_per_rpk"] = airfare_per_rpk

        # print('End PaxCostAF: Airfare 2050:{}, A{}'.format(airfare_per_rpk[self.end_year], a[self.end_year]))

        # airfare_per_rpk_real_constraint_consistency = []
        # for year in [2025, 2030, 2035, 2040, 2045, 2050]:
        #     airfare_per_rpk_real_constraint_consistency.append(
        #         (airfare_per_rpk_true[year] - airfare_per_rpk[year]) / airfare_per_rpk_true[year]
        #     )
        #
        # airfare_per_rpk_real_constraint_consistency = np.array(
        #     airfare_per_rpk_real_constraint_consistency
        # )

        return (
            marginal_cost_per_rpk,
            airfare_per_rpk_true,
            airfare_per_rpk,
            # airfare_per_rpk_real_constraint_consistency,
        )

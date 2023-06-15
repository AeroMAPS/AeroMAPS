# @Time : 03/03/2023 13:20
# @Author : a.salgas
# @File : average_ops_cost.py
# @Software: PyCharm


from typing import Tuple

import numpy as np
import pandas as pd
from cast.models.base import CastModel

from scipy.interpolate import interp1d


class SimpleDirectOperatingCostASK(CastModel):
    def __init__(self, name="simple_direct_operating_cost_ask", *args, **kwargs):
        super().__init__(name, *args, **kwargs)


    def compute(self,
                short_range_landing_doc_ask: float = 0.0,
                short_range_handling_doc_ask: float =0.0,
                short_range_navigation_doc_ask: float =0.0,
                short_range_mro_airframe_doc_ask: float =0.0,
                short_range_mro_labor_doc_ask: float =0.0,
                short_range_mro_engine_doc_ask: float =0.0,
                short_range_pilot_doc_ask: float =0.0,
                short_range_fa_doc_ask: float =0.0,
                short_range_capital_doc_ask: float =0.0,
                medium_range_landing_doc_ask: float =0.0,
                medium_range_handling_doc_ask: float =0.0,
                medium_range_navigation_doc_ask: float =0.0,
                medium_range_mro_airframe_doc_ask: float =0.0,
                medium_range_mro_labor_doc_ask: float =0.0,
                medium_range_mro_engine_doc_ask: float =0.0,
                medium_range_pilot_doc_ask: float =0.0,
                medium_range_fa_doc_ask: float =0.0,
                medium_range_capital_doc_ask: float =0.0,
                long_range_landing_doc_ask: float =0.0,
                long_range_handling_doc_ask: float =0.0,
                long_range_navigation_doc_ask: float =0.0,
                long_range_mro_airframe_doc_ask: float =0.0,
                long_range_mro_labor_doc_ask: float =0.0,
                long_range_mro_engine_doc_ask: float =0.0,
                long_range_pilot_doc_ask: float =0.0,
                long_range_fa_doc_ask: float =0.0,
                long_range_capital_doc_ask: float =0.0,
                capital_interest_rate: float = 0.0,
                capital_depreciation_period: float = 0.0,
                energy_consumption_short_range_biofuel: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_medium_range_biofuel: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_long_range_biofuel: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_biofuel: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_short_range_electrofuel: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_medium_range_electrofuel: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_long_range_electrofuel: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_electrofuel: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_short_range_kerosene: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_medium_range_kerosene: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_long_range_kerosene: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_kerosene: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_short_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_medium_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_long_range_hydrogen: pd.Series = pd.Series(dtype="float64"),
                energy_consumption_hydrogen: pd.Series = pd.Series(dtype="float64"),
                ask_short_range: pd.Series = pd.Series(dtype="float64"),
                ask_medium_range: pd.Series = pd.Series(dtype="float64"),
                ask_long_range: pd.Series = pd.Series(dtype="float64"),
                kerosene_cost: pd.Series = pd.Series(dtype="float64"),
                biofuel_cost_hefa_fog: pd.Series = pd.Series(dtype="float64"),
                biofuel_cost_hefa_others: pd.Series = pd.Series(dtype="float64"),
                biofuel_cost_ft_others: pd.Series = pd.Series(dtype="float64"),
                biofuel_cost_ft_msw: pd.Series = pd.Series(dtype="float64"),
                biofuel_cost_atj: pd.Series = pd.Series(dtype="float64"),
                electrofuel_total_cost: pd.Series = pd.Series(dtype="float64"),
                total_hydrogen_supply_cost: pd.Series = pd.Series(dtype="float64"),
                ):

        total_biofuel_cost=biofuel_cost_ft_msw+biofuel_cost_atj+biofuel_cost_ft_others+biofuel_cost_hefa_others+biofuel_cost_hefa_fog

        ### Short range fuel DOC

        kerosene_short_range_share =  energy_consumption_short_range_kerosene / energy_consumption_kerosene
        kerosene_short_range_cost_per_ask = kerosene_cost * kerosene_short_range_share / ask_short_range
        
        biofuel_short_range_share = energy_consumption_short_range_biofuel / energy_consumption_biofuel
        biofuel_short_range_cost_per_ask = total_biofuel_cost * biofuel_short_range_share / ask_short_range
        
        electrofuel_short_range_share = energy_consumption_short_range_electrofuel / energy_consumption_electrofuel
        electrofuel_short_range_cost_per_ask = electrofuel_total_cost * electrofuel_short_range_share / ask_short_range
        
        hydrogen_short_range_share = energy_consumption_short_range_hydrogen / energy_consumption_hydrogen
        hydrogen_short_range_cost_per_ask = total_hydrogen_supply_cost * hydrogen_short_range_share / ask_short_range

        ### Medium range fuel DOC

        kerosene_medium_range_share = energy_consumption_medium_range_kerosene / energy_consumption_kerosene
        kerosene_medium_range_cost_per_ask = kerosene_cost * kerosene_medium_range_share / ask_medium_range

        biofuel_medium_range_share = energy_consumption_medium_range_biofuel / energy_consumption_biofuel
        biofuel_medium_range_cost_per_ask = total_biofuel_cost * biofuel_medium_range_share / ask_medium_range

        electrofuel_medium_range_share = energy_consumption_medium_range_electrofuel / energy_consumption_electrofuel
        electrofuel_medium_range_cost_per_ask = electrofuel_total_cost * electrofuel_medium_range_share / ask_medium_range

        hydrogen_medium_range_share = energy_consumption_medium_range_hydrogen / energy_consumption_hydrogen
        hydrogen_medium_range_cost_per_ask = total_hydrogen_supply_cost * hydrogen_medium_range_share / ask_medium_range

        ### Long range fuel DOC

        kerosene_long_range_share = energy_consumption_long_range_kerosene / energy_consumption_kerosene
        kerosene_long_range_cost_per_ask = kerosene_cost * kerosene_long_range_share / ask_long_range

        biofuel_long_range_share = energy_consumption_long_range_biofuel / energy_consumption_biofuel
        biofuel_long_range_cost_per_ask = total_biofuel_cost * biofuel_long_range_share / ask_long_range

        electrofuel_long_range_share = energy_consumption_long_range_electrofuel / energy_consumption_electrofuel
        electrofuel_long_range_cost_per_ask = electrofuel_total_cost * electrofuel_long_range_share / ask_long_range

        hydrogen_long_range_share = energy_consumption_long_range_hydrogen / energy_consumption_hydrogen
        hydrogen_long_range_cost_per_ask = total_hydrogen_supply_cost * hydrogen_long_range_share / ask_long_range
        
        ### Capital tuning

        base_annuity_factor = 0.04
        new_annuity = capital_interest_rate/(1 - (1 / (1 + capital_interest_rate)) ** capital_depreciation_period)

        short_range_capital_doc_ask = short_range_capital_doc_ask/0.04*new_annuity
        medium_range_capital_doc_ask = medium_range_capital_doc_ask/0.04*new_annuity
        long_range_capital_doc_ask = long_range_capital_doc_ask/0.04*new_annuity







        ## TODO




        return



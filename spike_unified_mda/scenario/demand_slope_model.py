"""Brief 2 deliverable: the ``DemandSlope`` stub discipline.

Exposes ``{region}:fuel_demand_slope`` — the local response of regional passenger
demand to the SAF price, ``s = dRPK/dp_SAF`` in RPK per (EUR/MJ) — so that a fuel
market module can be handed ``(D0, s)`` and solve for the cleared price inside its
own optimisation, instead of iterating on ``D`` through a fixed point.

It is a *regional* discipline: it declares unprefixed names and
``apply_namespace_to_disciplines`` turns ``fuel_demand_slope`` into
``{region}:fuel_demand_slope``, exactly like ``SpikeFuelDemand``.

The slope is the product of the four stages of the chain, closed on the airline
supply function:

    s = eta * kappa * alpha / (1 - a * eta)

    alpha  = SAF share of drop-in energy            (d mfsp_mean / d p_SAF)
    kappa  = drop-in energy intensity per RPK       (d total_cost_per_rpk / d mfsp_mean)
    eta    = price_elasticity * RPK / airfare       (d RPK / d airfare)
    a      = slope of the inverse supply function of ``PassengerAircraftMarginalCost``

``1 / (1 - a*eta)`` is the equilibrium cost pass-through: the fraction of the fuel
shock that reaches the passenger.  The complement is what the airline absorbs
through the quantity term of its own supply curve.

Assumptions, all of them checked against the code in ``spike_unified_mda/BRIEF2.md``:

* ``d alpha / d p_SAF = 0``.  Shares come from ``EnergyUseChoice``, which reads
  exogenous ``{pathway}_mandate_share`` / ``_mandate_quantity``; nothing in the
  chain makes a pathway share respond to a price.  A price-responsive blend would
  add ``(p_SAF - p_fossil) * d alpha / d p_SAF`` to stage 4.
* The airline cost model in force is ``models_operation_cost_*_feedback``
  (``PassengerAircraftMarginalCost``).  With ``PassengerAircraftSimpleAirfare``
  there is no ``a`` term, ``price_elasticity`` is not wired, and the slope is zero
  by construction.
* Extra taxes (carbon tax, passenger tax) do not depend on ``p_SAF``, so they drop
  out of the derivative.  They do move ``airfare``, hence ``eta``, and that is
  picked up because ``eta`` is read off the converged point.
"""

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel

# ``PassengerAircraftMarginalCost.compute`` hard-codes this as
# ``initial_price_per_rpk_corrected`` (total_airline_cost_and_airfare.py:314).
# It is NOT read from ``initial_airfare_per_rpk``: the two are equal in the shipped
# configs but nothing enforces it.
INITIAL_PRICE_PER_RPK = 0.09236379319842411


class DemandSlope(AeroMAPSModel):
    """Local slope of regional demand with respect to the SAF price [RPK/(EUR/MJ)]."""

    MARKET_SCOPE = "cross_market"

    def __init__(self, name="demand_slope", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        # Injected by AeroMAPSProcess before custom_setup().
        self.markets = None
        self.pathways_manager = None
        self.saf_pathways = []
        self.passenger_market_ids = []
        self.input_names = {}
        self.output_names = {}

    def custom_setup(self):
        if self.markets is None or self.pathways_manager is None:
            return  # called once per injection; the grammar is built on the last one

        self.passenger_market_ids = [m.id for m in self.markets.get(traffic_type="passenger")]
        # p_SAF is the price of the non-fossil drop-in blend.
        self.saf_pathways = [
            p.name
            for p in self.pathways_manager.get(aircraft_type="dropin_fuel")
            if p.energy_origin != "fossil"
        ]

        self.input_names = {
            "rpk": pd.Series([0.0]),
            "rpk_no_elasticity": pd.Series([0.0]),
            "airfare_per_rpk": pd.Series([0.0]),
            "total_cost_per_rpk_without_extra_tax": pd.Series([0.0]),
            "load_factor": pd.Series([0.0]),
            "price_elasticity": 0.0,
        }
        for mid in self.passenger_market_ids:
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            self.input_names[f"energy_per_ask_{mid}_dropin_fuel"] = pd.Series([0.0])
            self.input_names[f"ask_{mid}_dropin_fuel_share"] = pd.Series([0.0])
            self.input_names[f"{mid}_covid_end_year"] = 0.0
        for pathway in self.saf_pathways:
            self.input_names[f"{pathway}_share_dropin_fuel"] = pd.Series([0.0])

        self.output_names = {
            "fuel_demand_slope": pd.Series([0.0]),
            "fuel_demand_slope_open_loop": pd.Series([0.0]),
            "saf_blend_share": pd.Series([0.0]),
            "dropin_energy_per_rpk": pd.Series([0.0]),
            "airfare_cost_passthrough": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        rpk = input_data["rpk"]
        rpk_no_elasticity = input_data["rpk_no_elasticity"]
        airfare = input_data["airfare_per_rpk"]
        cost_per_rpk = input_data["total_cost_per_rpk_without_extra_tax"]
        load_factor = input_data["load_factor"]
        price_elasticity = float(input_data["price_elasticity"])

        # Stage 4 — dilution by the blend share.  Exogenous-alpha case: the second
        # term of d mfsp_mean/d p_SAF vanishes (see the module docstring).
        alpha = sum(
            input_data[f"{p}_share_dropin_fuel"].fillna(0) / 100.0 for p in self.saf_pathways
        )

        # Stage 3 — energy share of cost.  ASK-weighted drop-in energy per ASK,
        # converted to per RPK by the load factor.  Mirrors PassengerAircraftDocEnergy
        # then PassengerAircraftTotalCost.
        ask_total = sum(input_data[f"ask_{mid}"] for mid in self.passenger_market_ids)
        energy_per_ask = (
            sum(
                input_data[f"energy_per_ask_{mid}_dropin_fuel"].fillna(0)
                * input_data[f"ask_{mid}_dropin_fuel_share"].fillna(0)
                / 100.0
                * input_data[f"ask_{mid}"]
                for mid in self.passenger_market_ids
            )
            / ask_total
        )
        energy_per_rpk = energy_per_ask / (load_factor / 100.0)

        # Stage 2 — the ad-hoc inverse supply function of PassengerAircraftMarginalCost:
        #   airfare = a*RPK + b + C(t) - C0 + extra_tax,  a = 2(p0 - C0)/rpk_no_elasticity.
        # The partial d airfare/d total_cost is 1; the incidence is the a*RPK term.
        c0 = float(cost_per_rpk.loc[self.prospection_start_year - 1])
        supply_slope = 2.0 * (INITIAL_PRICE_PER_RPK - c0) / rpk_no_elasticity

        # Stage 1 — elasticity.  d/dP of D_ne*(P/P_init)^eps is eps*D/P; P_init cancels.
        eta = price_elasticity * rpk / airfare

        # RPKElasticity clamps its multiplier to 1 up to the latest covid_end_year,
        # so demand is exogenous there and the slope is identically zero.
        elasticity_start = max(
            max(int(input_data[f"{mid}_covid_end_year"]) for mid in self.passenger_market_ids) + 1,
            self.prospection_start_year,
        )
        active = pd.Series(0.0, index=self.df.index)
        active.loc[elasticity_start : self.end_year] = 1.0

        loop_gain = supply_slope * eta
        passthrough = 1.0 / (1.0 - loop_gain)
        open_loop = eta * energy_per_rpk * alpha
        slope = open_loop * passthrough

        output_data = {
            "fuel_demand_slope": (slope * active).replace([np.inf, -np.inf], np.nan),
            "fuel_demand_slope_open_loop": (open_loop * active).replace([np.inf, -np.inf], np.nan),
            "saf_blend_share": alpha,
            "dropin_energy_per_rpk": energy_per_rpk,
            "airfare_cost_passthrough": passthrough * active,
        }
        for key, value in output_data.items():
            self.df.loc[:, key] = value
        self._store_outputs(output_data)
        return output_data

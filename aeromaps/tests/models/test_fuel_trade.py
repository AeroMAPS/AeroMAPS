"""Tests of ``FuelTrade``: who makes the fuel each region burns.

Three layers. The discipline alone, on hand-made series (cheap, no MDA), in both modes --
an explicit sourcing matrix, and the pro-rata pool -- and the unit values it hands on. The
guards that keep the regional flag and the global model declared together. And end-to-end
runs of the two-region benches, because the point of this model is the plumbing: that
production differing from consumption actually travels through the multi-regional MDA to
the models that read it. ``fuel_clearing_step1/trade_plumbing.py`` and ``pool_plumbing.py``
run the fuller comparisons.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import yaml

from aeromaps.models.impacts.generic_energy_model.common.energy_carriers_manager import (
    EnergyCarrierManager,
    EnergyCarrierMetadata,
)
from aeromaps.models.impacts.generic_energy_model.fuel_trade.fuel_trade import (
    DELIVERED_VALUES,
    MAKER_VALUES,
    FuelTrade,
    FuelTradeConfigurationError,
    fill_pools,
)

REGIONS = ("A", "B")
YEARS = range(2015, 2031)
PROSPECTIVE = slice(2020, 2030)
HISTORICAL = slice(2015, 2019)
BENCH = Path(__file__).parents[3] / "fuel_clearing_step1" / "scenario"

CARRIERS = (
    EnergyCarrierMetadata(
        name="fossil_kerosene", aircraft_type="dropin_fuel", default=True, energy_origin="fossil"
    ),
    EnergyCarrierMetadata(name="hefa_fog", aircraft_type="dropin_fuel", energy_origin="biomass"),
    EnergyCarrierMetadata(
        name="electrofuel", aircraft_type="dropin_fuel", energy_origin="electricity"
    ),
)
PATHWAYS = tuple(carrier.name for carrier in CARRIERS)
POOLED = ("electrofuel", "hefa_fog")

# Per region, the unit values of the fuel it makes: A a clean grid and dear power, B a
# dirty grid and cheap power; A taxes carbon at 100 EUR/t, B at 10.
EMISSION_FACTOR = {
    "A": {"fossil_kerosene": 88.7, "hefa_fog": 20.0, "electrofuel": 5.0},
    "B": {"fossil_kerosene": 88.7, "hefa_fog": 25.0, "electrofuel": 60.0},
}
MFSP = {
    "A": {"fossil_kerosene": 0.012, "hefa_fog": 0.023, "electrofuel": 0.100},
    "B": {"fossil_kerosene": 0.012, "hefa_fog": 0.025, "electrofuel": 0.070},
}
SUBSIDY = {"A": 0.002, "B": 0.0}
TAX = {"A": 0.0, "B": 0.001}
CARBON_TAX = {"A": 100.0, "B": 10.0}


def _series(value):
    return pd.Series(float(value), index=YEARS)


def _unit_values():
    data = {}
    for region in REGIONS:
        data[f"{region}:carbon_tax"] = _series(CARBON_TAX[region])
        for pathway in PATHWAYS:
            mfsp = MFSP[region][pathway]
            data[f"{region}:{pathway}_mean_co2_emission_factor"] = _series(
                EMISSION_FACTOR[region][pathway]
            )
            data[f"{region}:{pathway}_mean_mfsp"] = _series(mfsp)
            data[f"{region}:{pathway}_mean_unit_subsidy"] = _series(SUBSIDY[region])
            data[f"{region}:{pathway}_mean_unit_tax"] = _series(TAX[region])
            data[f"{region}:{pathway}_net_mfsp_without_carbon_tax"] = _series(
                mfsp - SUBSIDY[region] + TAX[region]
            )
    return data


def _model(mode, configuration_data=None, carriers=CARRIERS):
    model = FuelTrade("fuel_trade", configuration_data=configuration_data or {})
    model.parameters = SimpleNamespace(
        climate_historic_start_year=2015,
        historic_start_year=2015,
        prospection_start_year=2020,
        end_year=2030,
    )
    model._initialize_df()
    model.regions = list(REGIONS)
    model.mode = mode
    model.pathways_manager = EnergyCarrierManager(list(carriers))
    model.custom_setup()
    model._initialize_df()
    return model


def _trade(sourcing):
    return _model("matrix", {"sourcing": sourcing})


# --- matrix mode ----------------------------------------------------------------------


def _consumption():
    """Kerosene and e-fuel everywhere; HEFA only from 2020, NaN before -- as
    EnergyUseChoice emits."""
    data = _unit_values()
    for scale, region in ((1.0, "A"), (2.0, "B")):
        for pathway, low, high in (("fossil_kerosene", 10.0, 20.0), ("electrofuel", 0.0, 2.0)):
            data[f"{region}:{pathway}_energy_consumption"] = pd.Series(
                scale * np.linspace(low, high, len(YEARS)), index=YEARS
            )
        hefa = pd.Series(scale * np.linspace(0.0, 5.0, len(YEARS)), index=YEARS)
        hefa.loc[:2019] = np.nan
        data[f"{region}:hefa_fog_energy_consumption"] = hefa
    return data


def test_an_untraded_pathway_is_produced_where_it_is_consumed_nan_included():
    """Bit for bit, NaN included: a pathway nobody trades must reach the environmental
    model exactly as it did before trade existed."""
    out = _trade({"hefa_fog": {"B": {"A": 1.0}}}).compute(_consumption())
    data = _consumption()
    for region in REGIONS:
        pd.testing.assert_series_equal(
            out[f"{region}:fossil_kerosene_energy_production"],
            data[f"{region}:fossil_kerosene_energy_consumption"],
            check_names=False,
        )
        assert float(out[f"{region}:fossil_kerosene_energy_net_export"].abs().max()) == 0.0


def test_the_matrix_moves_production_in_prospective_years_only():
    data = _consumption()
    out = _trade({"hefa_fog": {"B": {"A": 0.6, "B": 0.4}}}).compute(data)
    a, b = data["A:hefa_fog_energy_consumption"], data["B:hefa_fog_energy_consumption"]

    made_in_a = out["A:hefa_fog_energy_production"]
    made_in_b = out["B:hefa_fog_energy_production"]
    assert np.allclose(made_in_a.loc[PROSPECTIVE], a.loc[PROSPECTIVE] + 0.6 * b.loc[PROSPECTIVE])
    assert np.allclose(made_in_b.loc[PROSPECTIVE], 0.4 * b.loc[PROSPECTIVE])
    # Historical years: the data describe no trade, so there production is consumption.
    pd.testing.assert_series_equal(made_in_b.loc[:2019], b.loc[:2019], check_names=False)


def test_flows_add_up_to_net_exports_and_nothing_is_created_or_lost():
    data = _consumption()
    sourcing = {
        "hefa_fog": {"B": {"A": 1.0}},
        "fossil_kerosene": {"A": {"A": 0.75, "B": 0.25}},
    }
    out = _trade(sourcing).compute(data)
    for pathway in sourcing:
        a_to_b = out[f"overall:{pathway}_energy_flow_A_to_B"]
        b_to_a = out[f"overall:{pathway}_energy_flow_B_to_A"]
        assert np.allclose(a_to_b - b_to_a, out[f"A:{pathway}_energy_net_export"], atol=0)
        assert np.allclose(b_to_a - a_to_b, out[f"B:{pathway}_energy_net_export"], atol=0)
        made = sum(out[f"{r}:{pathway}_energy_production"].fillna(0.0) for r in REGIONS)
        burnt = sum(data[f"{r}:{pathway}_energy_consumption"].fillna(0.0) for r in REGIONS)
        assert np.allclose(made, burnt, rtol=1e-15, atol=0)
    # The two directions are really there, not one flow written twice.
    assert float(out["overall:hefa_fog_energy_flow_A_to_B"].max()) > 0
    assert float(out["overall:fossil_kerosene_energy_flow_B_to_A"].max()) > 0
    assert float(out["overall:hefa_fog_energy_flow_B_to_A"].abs().max()) == 0.0


@pytest.mark.parametrize(
    "sourcing, match",
    [
        ({}, "no 'sourcing' matrix"),
        ({"jet_zero": {"B": {"A": 1.0}}}, "does not declare"),
        ({"hefa_fog": {"C": {"A": 1.0}}}, "row for region 'C'"),
        ({"hefa_fog": {"B": {"C": 1.0}}}, "names producer 'C'"),
        ({"hefa_fog": {"B": {"A": 0.6}}}, "sums to 0.6, not 1"),
        ({"hefa_fog": {"B": {"A": 60.0, "B": 40.0}}}, "not a percentage"),
    ],
)
def test_a_matrix_that_cannot_be_applied_is_refused_by_name(sourcing, match):
    with pytest.raises(FuelTradeConfigurationError, match=match):
        _trade(sourcing)


# --- delivered unit values ------------------------------------------------------------


def test_with_nothing_traded_every_delivered_value_is_the_regions_own_to_the_bit():
    """The blend has one term, so the delivered values must BE the regional ones --
    including the carbon tax, which is recomputed from the burner's rate."""
    data = _consumption()
    out = _trade({"hefa_fog": {"B": {"B": 1.0}}}).compute(data)
    for region in REGIONS:
        for pathway in PATHWAYS:
            for value in MAKER_VALUES:
                pd.testing.assert_series_equal(
                    out[f"{region}:{pathway}_delivered_{value}"],
                    data[f"{region}:{pathway}_{value}"],
                    check_names=False,
                )
            # TopDownCost's own arithmetic, bracketed the same way.
            unit_tax = (data[f"{region}:carbon_tax"] / 1000) * (
                data[f"{region}:{pathway}_mean_co2_emission_factor"] / 1000
            )
            pd.testing.assert_series_equal(
                out[f"{region}:{pathway}_delivered_mean_unit_carbon_tax"],
                unit_tax,
                check_names=False,
            )
            pd.testing.assert_series_equal(
                out[f"{region}:{pathway}_delivered_net_mfsp"],
                data[f"{region}:{pathway}_net_mfsp_without_carbon_tax"].add(unit_tax, fill_value=0),
                check_names=False,
            )


def test_fuel_made_elsewhere_carries_the_makers_cost_and_co2_and_the_burners_tax():
    """All of B's e-fuel is made in A: B burns A's clean, dear e-fuel -- at B's carbon
    tax, not A's."""
    out = _trade({"electrofuel": {"B": {"A": 1.0}}}).compute(_consumption())
    years = PROSPECTIVE
    ef = out["B:electrofuel_delivered_mean_co2_emission_factor"].loc[years]
    assert np.allclose(ef, EMISSION_FACTOR["A"]["electrofuel"], rtol=0, atol=0)
    assert np.allclose(
        out["B:electrofuel_delivered_mean_mfsp"].loc[years], MFSP["A"]["electrofuel"]
    )
    assert np.allclose(out["B:electrofuel_delivered_mean_unit_subsidy"].loc[years], SUBSIDY["A"])
    unit_tax = CARBON_TAX["B"] / 1000 * EMISSION_FACTOR["A"]["electrofuel"] / 1000
    assert np.allclose(out["B:electrofuel_delivered_mean_unit_carbon_tax"].loc[years], unit_tax)
    assert np.allclose(
        out["B:electrofuel_delivered_net_mfsp"].loc[years],
        MFSP["A"]["electrofuel"] - SUBSIDY["A"] + TAX["A"] + unit_tax,
    )
    # Historical years: nothing traded, B's own values.
    assert np.allclose(
        out["B:electrofuel_delivered_mean_co2_emission_factor"].loc[HISTORICAL],
        EMISSION_FACTOR["B"]["electrofuel"],
    )


def test_a_blend_weights_each_maker_by_what_it_supplies():
    out = _trade({"electrofuel": {"A": {"A": 0.25, "B": 0.75}}}).compute(_consumption())
    expected = (
        0.25 * EMISSION_FACTOR["A"]["electrofuel"] + 0.75 * EMISSION_FACTOR["B"]["electrofuel"]
    )
    assert np.allclose(
        out["A:electrofuel_delivered_mean_co2_emission_factor"].loc[2021:2030], expected, rtol=1e-15
    )


def test_a_region_that_burns_none_keeps_its_own_values_not_a_nan():
    """B's HEFA is NaN before 2020: no blend is defined there, and a NaN would reach the
    means through a zero share. Its own value stands; from 2020, A's."""
    out = _trade({"hefa_fog": {"B": {"A": 1.0}}}).compute(_consumption())
    delivered = out["B:hefa_fog_delivered_mean_co2_emission_factor"]
    assert np.allclose(delivered.loc[HISTORICAL], EMISSION_FACTOR["B"]["hefa_fog"], rtol=0)
    assert np.allclose(delivered.loc[PROSPECTIVE], EMISSION_FACTOR["A"]["hefa_fog"], rtol=0)
    assert not delivered.isna().any()


# --- pool mode ------------------------------------------------------------------------


def _demand():
    return {
        "A": pd.Series(np.linspace(100.0, 120.0, len(YEARS)), index=YEARS),
        "B": pd.Series(np.linspace(200.0, 300.0, len(YEARS)), index=YEARS),
    }


def _offers(scale=1.0):
    """Prospective offers, NaN before 2020 -- as the YAML interpolators emit them."""
    offered = {
        "A": {"hefa_fog": 30.0, "electrofuel": 10.0},
        "B": {"hefa_fog": 0.0, "electrofuel": 20.0},
    }
    data = {}
    for region, pathways in offered.items():
        for pathway, volume in pathways.items():
            series = _series(scale * volume)
            series.loc[:2019] = np.nan
            data[f"{region}:{pathway}_energy_offered"] = series
    return data


def _pool_inputs(scale=1.0):
    data = {**_unit_values(), **_offers(scale)}
    for region, series in _demand().items():
        data[f"{region}:energy_consumption_dropin_fuel"] = series
        data[f"{region}:energy_consumption"] = series
    return data


def _pool(scale=1.0):
    model = _model("pool")
    return model, model.compute(_pool_inputs(scale))


def test_every_region_burns_the_world_mix():
    _, out = _pool()
    demand = _demand()
    world = demand["A"] + demand["B"]
    for pathway in POOLED:
        pool = sum(_offers()[f"{r}:{pathway}_energy_offered"] for r in REGIONS)
        for region in REGIONS:
            share = out[f"{region}:{pathway}_energy_consumption"] / demand[region]
            assert np.allclose(share.loc[PROSPECTIVE], (pool / world).loc[PROSPECTIVE], rtol=1e-14)
    # ... which is not what either region offers: A offers more than it burns, B less.
    assert float(out["A:hefa_fog_energy_net_export"].loc[2025]) > 0
    assert float(out["B:hefa_fog_energy_net_export"].loc[2025]) < 0


def test_the_pool_conserves_every_mj_region_by_region_and_pathway_by_pathway():
    _, out = _pool()
    demand = _demand()
    for region in REGIONS:
        burnt = sum(out[f"{region}:{p}_energy_consumption"] for p in PATHWAYS)
        assert np.allclose(burnt, demand[region], rtol=1e-14, atol=0)
    for pathway in PATHWAYS:
        made = sum(out[f"{r}:{pathway}_energy_production"] for r in REGIONS)
        burnt = sum(out[f"{r}:{pathway}_energy_consumption"] for r in REGIONS)
        assert np.allclose(made, burnt, rtol=1e-14, atol=0)
    for pathway in POOLED:
        a_to_b = out[f"overall:{pathway}_energy_flow_A_to_B"]
        b_to_a = out[f"overall:{pathway}_energy_flow_B_to_A"]
        assert np.allclose(a_to_b - b_to_a, out[f"A:{pathway}_energy_net_export"], atol=1e-12)
    # Each pool is split by demand share: B takes its share of what A makes.
    share_b = demand["B"] / (demand["A"] + demand["B"])
    assert np.allclose(
        out["overall:hefa_fog_energy_flow_A_to_B"].loc[PROSPECTIVE],
        (30.0 * share_b).loc[PROSPECTIVE],
        rtol=1e-14,
    )


def test_the_residual_fills_each_region_and_never_travels():
    _, out = _pool()
    assert not any(name.startswith("overall:fossil_kerosene_energy_flow") for name in out)
    for region in REGIONS:
        pd.testing.assert_series_equal(
            out[f"{region}:fossil_kerosene_energy_production"],
            out[f"{region}:fossil_kerosene_energy_consumption"],
            check_names=False,
        )


def test_historical_years_describe_no_trade():
    _, out = _pool()
    demand = _demand()
    for region in REGIONS:
        assert np.allclose(
            out[f"{region}:fossil_kerosene_energy_consumption"].loc[HISTORICAL],
            demand[region].loc[HISTORICAL],
        )
        for pathway in POOLED:
            assert (
                float(out[f"{region}:{pathway}_energy_consumption"].loc[HISTORICAL].abs().max())
                == 0.0
            )
    for pathway in POOLED:
        assert (
            float(out[f"overall:{pathway}_energy_flow_A_to_B"].loc[HISTORICAL].abs().max()) == 0.0
        )


def test_a_historical_offer_is_burnt_where_it_is_made():
    data = _pool_inputs()
    data["A:hefa_fog_energy_offered"].loc[:2019] = 7.0
    out = _model("pool").compute(data)
    assert np.allclose(out["A:hefa_fog_energy_consumption"].loc[HISTORICAL], 7.0)
    assert np.allclose(out["B:hefa_fog_energy_consumption"].loc[HISTORICAL], 0.0)
    assert np.allclose(out["overall:hefa_fog_energy_flow_A_to_B"].loc[HISTORICAL], 0.0)


def test_an_offer_above_world_demand_is_not_scaled_down_but_reported_unused():
    """Offers x 10 exceed world demand in every prospective year: the same use rate for
    every offered MJ, the rest reported unused, and no fossil at all."""
    _, out = _pool(scale=10.0)

    demand = _demand()
    world = demand["A"] + demand["B"]
    offered_total = 10.0 * (30.0 + 10.0 + 20.0)
    rate = (world / offered_total).loc[PROSPECTIVE]
    assert np.allclose(out["overall:fuel_pool_use_rate"].loc[PROSPECTIVE], rate, rtol=1e-14)
    offers = _offers(10.0)
    for region in REGIONS:
        assert np.allclose(
            out[f"{region}:fossil_kerosene_energy_consumption"].loc[PROSPECTIVE], 0.0, atol=1e-12
        )
        for pathway in POOLED:
            offered = offers[f"{region}:{pathway}_energy_offered"].loc[PROSPECTIVE]
            made = out[f"{region}:{pathway}_energy_production"].loc[PROSPECTIVE]
            unused = out[f"{region}:{pathway}_energy_unused"].loc[PROSPECTIVE]
            # The offer is kept whole: made + unused.
            assert np.allclose(made + unused, offered, rtol=1e-14)
            assert np.allclose(made, rate * offered, rtol=1e-14)
        burnt = sum(out[f"{region}:{p}_energy_consumption"] for p in PATHWAYS)
        assert np.allclose(burnt, demand[region], rtol=1e-14)


def test_below_world_demand_nothing_is_unused():
    _, out = _pool()
    assert np.all(out["overall:fuel_pool_use_rate"].loc[PROSPECTIVE] == 1.0)
    for region in REGIONS:
        for pathway in POOLED:
            assert float(out[f"{region}:{pathway}_energy_unused"].abs().max()) == 0.0


def test_the_model_never_warns_since_a_sweep_is_not_the_converged_state():
    """An early MDA sweep's demand is not the converged one; a warning from it would name
    the wrong years (the bench's first draft said 2038 where the answer is 2041)."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _pool(scale=10.0)


@pytest.mark.parametrize("rate, warns", [((1.0, 1.0, 1.0), False), ((1.0, 0.8, 0.7), True)])
def test_the_process_warns_once_from_the_converged_use_rates(rate, warns):
    """Per pathway: HEFA short in 2041-2042, e-fuel fully used, and the all-pathways rate
    -- which says nothing a per-pathway rate does not -- never named."""
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    process = SimpleNamespace(
        _global_namespace="overall",
        data={
            "vector_outputs": pd.DataFrame(
                {
                    "overall:hefa_fog_pool_use_rate": list(rate),
                    "overall:electrofuel_pool_use_rate": [1.0, 1.0, 1.0],
                    "overall:fuel_pool_use_rate": list(rate),
                },
                index=[2040, 2041, 2042],
            )
        },
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        MultiRegionalProcess._warn_unused_fuel(process)
    messages = [str(w.message) for w in caught]
    assert len(messages) == int(warns)
    if warns:
        assert "hefa_fog in 2041-2042" in messages[0] and "0.700" in messages[0]
        assert "electrofuel" not in messages[0] and "fuel in" not in messages[0]


def test_the_pool_blends_the_makers_values_and_charges_the_burners_tax():
    """A offers 10 of e-fuel, B 20: every region's e-fuel is one third A's, two thirds
    B's -- same emission factor everywhere, different carbon tax."""
    _, out = _pool()
    ef = (EMISSION_FACTOR["A"]["electrofuel"] + 2 * EMISSION_FACTOR["B"]["electrofuel"]) / 3
    for region in REGIONS:
        delivered = out[f"{region}:electrofuel_delivered_mean_co2_emission_factor"]
        assert np.allclose(delivered.loc[PROSPECTIVE], ef, rtol=1e-14)
        assert np.allclose(
            out[f"{region}:electrofuel_delivered_mean_unit_carbon_tax"].loc[PROSPECTIVE],
            CARBON_TAX[region] / 1000 * ef / 1000,
            rtol=1e-14,
        )
        # Historical years: no trade, own values.
        assert np.allclose(delivered.loc[HISTORICAL], EMISSION_FACTOR[region]["electrofuel"])


def test_the_pool_emits_the_share_families_the_means_read():
    _, out = _pool()
    for region in REGIONS:
        total = sum(out[f"{region}:{p}_share_dropin_fuel"] for p in PATHWAYS)
        assert np.allclose(total, 100.0, rtol=1e-13)
        assert f"{region}:biomass_share_total_energy" in out
        assert f"{region}:dropin_fuel_electricity_energy_consumption" in out


def test_every_delivered_family_is_emitted_for_every_region_and_pathway():
    model = _model("pool")
    for region in REGIONS:
        for pathway in PATHWAYS:
            for value in DELIVERED_VALUES:
                assert f"{region}:{pathway}_delivered_{value}" in model.output_names


def test_a_negative_offer_is_refused():
    data = _pool_inputs()
    data["B:electrofuel_energy_offered"].loc[2025] = -1.0
    with pytest.raises(ValueError, match="B:electrofuel_energy_offered is negative"):
        _model("pool").compute(data)


@pytest.mark.parametrize(
    "mode, configuration, carriers, match",
    [
        (None, {}, CARRIERS, "needs a mode"),
        ("both", {}, CARRIERS, "needs a mode"),
        ("pool", {"sourcing": {"hefa_fog": {"B": {"A": 1.0}}}}, CARRIERS, "does not read"),
        ("pool", {"eligibilty": {"hefa_fog": {"A": False}}}, CARRIERS, "does not read"),
        (
            "matrix",
            {"sourcing": {}, "eligibility": {"hefa_fog": {"A": False}}},
            CARRIERS,
            "does not read",
        ),
        (
            "pool",
            {},
            CARRIERS
            + (
                EnergyCarrierMetadata(
                    name="lh2", aircraft_type="hydrogen", default=True, energy_origin="electricity"
                ),
            ),
            "serves 'dropin_fuel' only",
        ),
        ("pool", {}, CARRIERS[1:], "Exactly one default"),
        ("pool", {}, CARRIERS[:1], "nothing to share"),
    ],
)
def test_a_pool_that_cannot_be_set_up_is_refused_by_name(mode, configuration, carriers, match):
    with pytest.raises(FuelTradeConfigurationError, match=match):
        _model(mode, configuration, carriers)


# --- eligibility ----------------------------------------------------------------------


def test_fill_pools_with_nothing_excluded_is_the_pro_rata_split():
    demand, pool = np.array([100.0, 300.0]), np.array([30.0, 10.0])
    burnt, left = fill_pools(demand, pool, np.ones((2, 2), dtype=bool))
    assert np.allclose(burnt, np.outer(demand / demand.sum(), pool), rtol=1e-15)
    assert np.all(left == 0.0)  # exactly: a use rate of one is exactly one

    # Above world demand: everyone fills at once, by one factor.
    burnt, left = fill_pools(demand, 20 * pool, np.ones((2, 2), dtype=bool))
    rate = demand.sum() / (20 * pool).sum()
    assert np.allclose(burnt, np.outer(demand / demand.sum(), 20 * pool * rate), rtol=1e-14)
    assert np.allclose(burnt.sum(axis=1), demand, rtol=1e-14)
    assert np.allclose(left, 20 * pool * (1 - rate), rtol=1e-14)


def test_fill_pools_caps_a_full_region_and_hands_the_excess_back():
    """A may not burn HEFA; B, the only taker, burns 10 in all. B is handed all 30 of HEFA
    plus its 1/11 of e-fuel, keeps a proportional slice of each that fills it exactly, and
    what it cannot take of e-fuel goes back to A. HEFA has no other taker: unused."""
    demand, pool = np.array([100.0, 10.0]), np.array([30.0, 10.0])  # (hefa, e-fuel)
    eligible = np.array([[False, True], [True, True]])
    burnt, left = fill_pools(demand, pool, eligible)

    assert burnt[0, 0] == 0.0
    assert np.isclose(burnt[1].sum(), 10.0, rtol=1e-15)
    assert np.isclose(burnt[1, 0] / burnt[1, 1], 30.0 / (10.0 / 11.0), rtol=1e-14)
    assert np.isclose(burnt[0, 1], 10.0 - burnt[1, 1], rtol=1e-14)  # A gets the rest
    assert left[1] == 0.0
    assert np.isclose(left[0], 30.0 - burnt[1, 0], rtol=1e-14)


def _excluded(inputs, row):
    return _model("pool", {"eligibility": row}).compute(inputs)


def test_an_excluded_region_burns_none_and_the_others_take_it_all():
    """A offers all the HEFA and may not burn it: every MJ goes to B. E-fuel is untouched
    and still split by world demand."""
    out = _excluded(_pool_inputs(), {"hefa_fog": {"A": False}})
    demand = _demand()
    assert float(out["A:hefa_fog_energy_consumption"].loc[PROSPECTIVE].abs().max()) == 0.0
    assert np.allclose(out["B:hefa_fog_energy_consumption"].loc[PROSPECTIVE], 30.0, rtol=1e-14)
    assert np.allclose(out["overall:hefa_fog_energy_flow_A_to_B"].loc[PROSPECTIVE], 30.0)
    # A still MAKES it all: production and consumption fully uncoupled.
    assert np.allclose(out["A:hefa_fog_energy_production"].loc[PROSPECTIVE], 30.0)
    share_a = (demand["A"] / (demand["A"] + demand["B"])).loc[PROSPECTIVE]
    assert np.allclose(
        out["A:electrofuel_energy_consumption"].loc[PROSPECTIVE], 30.0 * share_a, rtol=1e-14
    )
    for region in REGIONS:
        burnt = sum(out[f"{region}:{p}_energy_consumption"] for p in PATHWAYS)
        assert np.allclose(burnt, demand[region], rtol=1e-14)
    for pathway in PATHWAYS:
        made = sum(out[f"{r}:{pathway}_energy_production"] for r in REGIONS)
        burnt = sum(out[f"{r}:{pathway}_energy_consumption"] for r in REGIONS)
        assert np.allclose(made, burnt, rtol=1e-14)


def test_an_excluded_pool_its_takers_cannot_absorb_goes_unused_alone():
    """B, the only HEFA taker, burns 10 in all: most of A's HEFA is unused, the e-fuel is
    not, and each has its own use rate."""
    data = _pool_inputs()
    data["B:energy_consumption_dropin_fuel"] = _series(10.0)
    data["B:energy_consumption"] = _series(10.0)
    out = _excluded(data, {"hefa_fog": {"A": False}})
    years = PROSPECTIVE
    hefa_rate = out["overall:hefa_fog_pool_use_rate"].loc[years]
    assert float(hefa_rate.max()) < 0.5
    assert np.all(out["overall:electrofuel_pool_use_rate"].loc[years] == 1.0)
    assert np.allclose(out["B:fossil_kerosene_energy_consumption"].loc[years], 0.0, atol=1e-12)
    assert np.allclose(
        out["A:hefa_fog_energy_unused"].loc[years], 30.0 * (1.0 - hefa_rate), rtol=1e-12
    )
    assert np.allclose(out["A:hefa_fog_energy_production"].loc[years], 30.0 * hefa_rate)
    assert 0.0 < float(out["overall:fuel_pool_use_rate"].loc[2025]) < 1.0


def test_eligibility_does_not_reach_the_historical_years():
    data = _pool_inputs()
    data["A:hefa_fog_energy_offered"].loc[:2019] = 7.0
    out = _excluded(data, {"hefa_fog": {"A": False}})
    assert np.allclose(out["A:hefa_fog_energy_consumption"].loc[HISTORICAL], 7.0)
    assert np.allclose(out["overall:hefa_fog_energy_flow_A_to_B"].loc[HISTORICAL], 0.0)


def test_listing_a_region_as_eligible_changes_nothing():
    base = _pool()[1]
    listed = _excluded(_pool_inputs(), {"hefa_fog": {"A": True, "B": True}})
    for name, series in base.items():
        pd.testing.assert_series_equal(listed[name], series, check_names=False)


@pytest.mark.parametrize(
    "row, match",
    [
        ({"fossil_kerosene": {"A": False}}, "cannot be excluded"),
        ({"jet_zero": {"A": False}}, "not pooled here"),
        ({"hefa_fog": {"C": False}}, "names region 'C'"),
        ({"hefa_fog": {"A": 0}}, "must be true or false"),
    ],
)
def test_an_eligibility_that_cannot_be_applied_is_refused_by_name(row, match):
    with pytest.raises(FuelTradeConfigurationError, match=match):
        _model("pool", {"eligibility": row})


def test_a_bottom_up_pathway_is_refused_with_trade():
    """It would size its plants on consumption, in the region that burns the fuel."""
    from aeromaps.models.impacts.generic_energy_model.common.energy_carriers_factory import (
        AviationEnergyCarriersFactory,
    )

    data = {"p": {"environmental_model": "top-down", "cost_model": "bottom-up"}}
    with pytest.raises(NotImplementedError, match="bottom-up"):
        AviationEnergyCarriersFactory.create_carrier("p", data, {}, {}, fuel_trade=True)


# --- the multi-regional process -----------------------------------------------------


def _bench_config(tmp_path, edit, name="regionalisation_trade.yaml"):
    """A bench with absolute region paths, edited, written to ``tmp_path``."""
    config = yaml.safe_load((BENCH / name).read_text())
    for region in config["regionalisation"]["regions"].values():
        region["config_file"] = str(BENCH / region["config_file"])
    edit(config["regionalisation"])
    target = tmp_path / "regionalisation.yaml"
    target.write_text(yaml.safe_dump(config))
    return str(target)


needs_bench = pytest.mark.skipif(
    not (BENCH / "regionalisation_trade.yaml").exists(), reason="step-1 bench not present"
)
needs_pool_bench = pytest.mark.skipif(
    not (BENCH / "regionalisation_pool.yaml").exists(), reason="pool bench not present"
)


@needs_bench
def test_the_flag_without_the_model_is_refused(tmp_path):
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    def edit(block):
        block["global_models"] = {}

    with pytest.raises(ValueError, match="no FuelTrade model is declared"):
        MultiRegionalProcess(_bench_config(tmp_path, edit))


@needs_bench
def test_the_model_without_the_flag_is_refused(tmp_path):
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    def edit(block):
        block["fuel_trade"] = False

    with pytest.raises(ValueError, match="'regionalisation.fuel_trade' is off"):
        MultiRegionalProcess(_bench_config(tmp_path, edit))


@needs_bench
def test_a_flag_that_names_no_stand_in_is_refused(tmp_path):
    """`true` does not say which stand-in, and the two wire the regions differently."""
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    def edit(block):
        block["fuel_trade"] = True

    with pytest.raises(ValueError, match="must be one of"):
        MultiRegionalProcess(_bench_config(tmp_path, edit))


@needs_bench
def test_trade_needs_the_unified_mda(tmp_path):
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    def edit(block):
        block["execution_mode"] = "separate_processes"
        block["global_models"] = {}

    with pytest.raises(NotImplementedError, match="only 'unified_mda'"):
        MultiRegionalProcess(_bench_config(tmp_path, edit))


@needs_bench
def test_the_pool_and_the_market_are_refused_together(tmp_path):
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    def edit(block):
        block["fuel_trade"] = "pool"
        block["fuel_market"] = True

    with pytest.raises(ValueError, match="one variable cannot have two writers"):
        MultiRegionalProcess(_bench_config(tmp_path, edit))


@needs_bench
def test_a_pool_without_offers_is_refused_naming_them(tmp_path):
    """The matrix bench's regions offer nothing: a pool on them must say so, not run
    with every region silently making nothing."""
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    def edit(block):
        block["fuel_trade"] = "pool"
        block["global_models"] = {"standards": ["models_fuel_trade"]}

    with pytest.raises(ValueError, match=r"region_A:hefa_fog.*declare no offer"):
        MultiRegionalProcess(_bench_config(tmp_path, edit))


@needs_bench
def test_the_bench_carries_the_flows_through_the_mda():
    """End to end: the matrix's flows reach the feedstock models and the aggregator.

    All of B's HEFA is made in A. So A makes both regions' HEFA and uses the waste oil for
    it; B makes none and uses none; the world totals match on both sides.
    """
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    process = MultiRegionalProcess(str(BENCH / "regionalisation_trade.yaml"))
    process.compute()
    v = process.data["vector_outputs"]
    years = slice(2025, 2050)

    burnt_a = v["region_A:hefa_fog_energy_consumption"].loc[years]
    burnt_b = v["region_B:hefa_fog_energy_consumption"].loc[years]
    assert float(burnt_b.min()) > 0, "B burns no HEFA; the case moves nothing"
    assert np.allclose(v["region_A:hefa_fog_energy_production"].loc[years], burnt_a + burnt_b)
    assert np.allclose(v["region_B:hefa_fog_energy_production"].loc[years], 0.0)
    assert np.allclose(v["overall:hefa_fog_energy_flow_region_A_to_region_B"].loc[years], burnt_b)

    # Feedstock follows production: 1.14 MJ of waste oil per MJ of HEFA, in A only.
    assert np.allclose(
        v["region_A:hefa_fog_biomass_total_consumption"].loc[years],
        1.14 * (burnt_a + burnt_b),
    )
    assert np.allclose(v["region_B:hefa_fog_biomass_total_consumption"].loc[years], 0.0)

    # And the aggregator sees one world: as much made as burnt.
    assert np.allclose(
        v["overall:hefa_fog_energy_production"].loc[years],
        v["overall:hefa_fog_energy_consumption"].loc[years],
        rtol=1e-14,
    )


@needs_pool_bench
def test_the_pool_bench_runs_end_to_end_and_closes_every_balance():
    """The asymmetric pool bench, full MDA: every region burns the world mix of what all
    regions offer; feedstock is booked where fuel is made; each region's CO2 is its
    consumption at the makers' emission factors."""
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    process = MultiRegionalProcess(str(BENCH / "regionalisation_pool.yaml"))
    process.compute()
    v = process.data["vector_outputs"]
    years = slice(2025, 2050)
    regions = ("region_A", "region_B")
    pooled = ("atj", "electrofuel", "ft_msw", "hefa_fog")
    demand = {r: v[f"{r}:energy_consumption_dropin_fuel"].loc[years] for r in regions}
    world = demand["region_A"] + demand["region_B"]

    for pathway in pooled:
        offered = sum(v[f"{r}:{pathway}_energy_offered"].loc[years] for r in regions)
        for region in regions:
            share = v[f"{region}:{pathway}_energy_consumption"].loc[years] / demand[region]
            assert np.allclose(share, offered / world, rtol=1e-12)
            # Feedstock where the fuel is made, not where it is burnt.
            assert np.allclose(
                v[f"{region}:{pathway}_energy_production"].loc[years],
                v[f"{region}:{pathway}_energy_offered"].loc[years],
                rtol=1e-12,
            )
    for region in regions:
        burnt = sum(
            v[f"{region}:{p}_energy_consumption"].loc[years] for p in (*pooled, "fossil_kerosene")
        )
        assert np.allclose(burnt, demand[region], rtol=1e-12)
    assert float(v["overall:hefa_fog_energy_flow_region_A_to_region_B"].loc[years].min()) > 0

    # The unit values reached the consumer side. Same mix, same makers: both regions'
    # drop-in fuel has the same emission factor and pre-tax cost -- which their own values
    # (a clean grid in A, a dirty one in B) would not give.
    for name in ("dropin_fuel_mean_co2_emission_factor", "dropin_fuel_mean_mfsp"):
        assert np.allclose(
            v[f"region_A:{name}"].loc[years], v[f"region_B:{name}"].loc[years], rtol=1e-12
        )
    assert not np.allclose(
        v["region_A:electrofuel_mean_co2_emission_factor"].loc[years],
        v["region_B:electrofuel_mean_co2_emission_factor"].loc[years],
    )
    for region in regions:
        burnt = {
            p: v[f"{region}:{p}_energy_consumption"].loc[years]
            for p in (*pooled, "fossil_kerosene")
        }
        # Per-pathway CO2 totals at the makers' emission factors add up to the region's.
        assert np.allclose(
            v[f"{region}:dropin_fuel_mean_co2_emission_factor"].loc[years] * demand[region],
            sum(v[f"{region}:{p}_total_co2_emissions"].loc[years] for p in burnt),
            rtol=1e-9,
        )
        # And the region pays for what it burns at the delivered price.
        assert np.allclose(
            v[f"{region}:non_discounted_energy_expenses"].loc[years],
            sum(burnt[p] * v[f"{region}:{p}_delivered_mean_mfsp"].loc[years] for p in burnt) / 1e6,
            rtol=1e-12,
        )


needs_eligibility_bench = pytest.mark.skipif(
    not (BENCH / "regionalisation_pool_eligibility.yaml").exists(),
    reason="eligibility bench not present",
)


@needs_eligibility_bench
def test_the_eligibility_bench_runs_end_to_end():
    """Region A may not burn HEFA, of which it makes most: A makes it all the same and
    burns none, B burns the whole pool, and every other pool is still split by demand."""
    from aeromaps.core.multi_regional_process import MultiRegionalProcess

    process = MultiRegionalProcess(str(BENCH / "regionalisation_pool_eligibility.yaml"))
    process.compute()
    v = process.data["vector_outputs"]
    years = slice(2025, 2050)
    regions = ("region_A", "region_B")
    demand = {r: v[f"{r}:energy_consumption_dropin_fuel"].loc[years] for r in regions}

    hefa_offered = sum(v[f"{r}:hefa_fog_energy_offered"].loc[years] for r in regions)
    assert float(v["region_A:hefa_fog_energy_consumption"].loc[years].abs().max()) == 0.0
    assert np.allclose(v["region_B:hefa_fog_energy_consumption"].loc[years], hefa_offered)
    assert np.allclose(
        v["region_A:hefa_fog_energy_production"].loc[years],
        v["region_A:hefa_fog_energy_offered"].loc[years],
    )
    assert np.allclose(
        v["overall:hefa_fog_energy_flow_region_A_to_region_B"].loc[years],
        v["region_A:hefa_fog_energy_offered"].loc[years],
    )
    for pathway in ("atj", "electrofuel", "ft_msw"):
        share = {r: v[f"{r}:{pathway}_energy_consumption"].loc[years] / demand[r] for r in regions}
        assert np.allclose(share["region_A"], share["region_B"], rtol=1e-12)
    for region in regions:
        burnt = sum(
            v[f"{region}:{p}_energy_consumption"].loc[years]
            for p in ("atj", "electrofuel", "ft_msw", "hefa_fog", "fossil_kerosene")
        )
        assert np.allclose(burnt, demand[region], rtol=1e-12)
    # A's waste oil is used where the HEFA is made, in A, although A burns none of it.
    assert np.allclose(
        v["region_A:hefa_fog_biomass_total_consumption"].loc[years],
        1.14 * v["region_A:hefa_fog_energy_offered"].loc[years],
    )

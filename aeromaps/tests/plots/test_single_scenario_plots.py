"""
Test module for single scenario plots.

This module tests that all single scenario plots can be created without errors
when running a scenario with default configuration.
"""

import pytest
from aeromaps import create_process


@pytest.fixture(scope="module")
def process():
    """
    Create and run an AeroMAPS process with test configuration.
    
    This fixture is module-scoped to avoid running the computation multiple times.
    Uses the full test configuration which includes all necessary models.
    """
    # Create process with full test configuration
    import os
    config_path = os.path.join(
        os.path.dirname(__file__),
        "../core/tested_configs/config_full.yaml"
    )
    proc = create_process(configuration_file=config_path)
    
    # Run the scenario
    proc.compute()
    
    return proc


def test_air_transport_co2_emissions_plot(process):
    """Test that air_transport_co2_emissions plot can be created."""
    plot = process.plot("air_transport_co2_emissions", save=False)
    assert plot is not None


def test_air_transport_climate_impacts_plot(process):
    """Test that air_transport_climate_impacts plot can be created."""
    plot = process.plot("air_transport_climate_impacts", save=False)
    assert plot is not None


def test_carbon_budget_assessment_plot(process):
    """Test that carbon_budget_assessment plot can be created."""
    plot = process.plot("carbon_budget_assessment", save=False)
    assert plot is not None


def test_temperature_target_assessment_plot(process):
    """Test that temperature_target_assessment plot can be created."""
    plot = process.plot("temperature_target_assessment", save=False)
    assert plot is not None


def test_biomass_resource_budget_assessment_plot(process):
    """Test that biomass_resource_budget_assessment plot can be created."""
    plot = process.plot("biomass_resource_budget_assessment", save=False)
    assert plot is not None


def test_electricity_resource_budget_assessment_plot(process):
    """Test that electricity_resource_budget_assessment plot can be created."""
    plot = process.plot("electricity_resource_budget_assessment", save=False)
    assert plot is not None


def test_multidisciplinary_assessment_plot(process):
    """Test that multidisciplinary_assessment plot can be created."""
    plot = process.plot("multidisciplinary_assessment", save=False)
    assert plot is not None


def test_temperature_increase_plot(process):
    """Test that temperature_increase_from_air_transport plot can be created."""
    plot = process.plot("temperature_increase_from_air_transport", save=False)
    assert plot is not None


def test_biomass_consumption_plot(process):
    """Test that biomass_consumption plot can be created."""
    plot = process.plot("biomass_consumption", save=False)
    assert plot is not None


def test_electricity_consumption_plot(process):
    """Test that electricity_consumption plot can be created."""
    plot = process.plot("electricity_consumption", save=False)
    assert plot is not None


def test_co2_per_rpk_plot(process):
    """Test that co2_per_rpk plot can be created."""
    plot = process.plot("co2_per_rpk", save=False)
    assert plot is not None


def test_co2_per_rtk_plot(process):
    """Test that co2_per_rtk plot can be created."""
    plot = process.plot("co2_per_rtk", save=False)
    assert plot is not None


def test_passenger_kaya_factors_plot(process):
    """Test that passenger_kaya_factors plot can be created."""
    plot = process.plot("passenger_kaya_factors", save=False)
    assert plot is not None


def test_freight_kaya_factors_plot(process):
    """Test that freight_kaya_factors plot can be created."""
    plot = process.plot("freight_kaya_factors", save=False)
    assert plot is not None


def test_levers_of_action_distribution_plot(process):
    """Test that levers_of_action_distribution plot can be created."""
    plot = process.plot("levers_of_action_distribution", save=False)
    assert plot is not None


def test_revenue_passenger_kilometer_plot(process):
    """Test that revenue_passenger_kilometer plot can be created."""
    plot = process.plot("revenue_passenger_kilometer", save=False)
    assert plot is not None


def test_revenue_tonne_kilometer_plot(process):
    """Test that revenue_tonne_kilometer plot can be created."""
    plot = process.plot("revenue_tonne_kilometer", save=False)
    assert plot is not None


def test_available_seat_kilometer_plot(process):
    """Test that available_seat_kilometer plot can be created."""
    plot = process.plot("available_seat_kilometer", save=False)
    assert plot is not None


def test_total_aircraft_distance_plot(process):
    """Test that total_aircraft_distance plot can be created."""
    plot = process.plot("total_aircraft_distance", save=False)
    assert plot is not None


def test_load_factor_plot(process):
    """Test that load_factor plot can be created."""
    plot = process.plot("load_factor", save=False)
    assert plot is not None


def test_energy_per_ask_plot(process):
    """Test that energy_per_ask plot can be created."""
    plot = process.plot("energy_per_ask", save=False)
    assert plot is not None


def test_energy_per_rtk_plot(process):
    """Test that energy_per_rtk plot can be created."""
    plot = process.plot("energy_per_rtk", save=False)
    assert plot is not None


def test_energy_consumption_plot(process):
    """Test that energy_consumption plot can be created."""
    plot = process.plot("energy_consumption", save=False)
    assert plot is not None


def test_fuel_consumption_liter_per_pax_100km_plot(process):
    """Test that fuel_consumption_liter_per_pax_100km plot can be created."""
    plot = process.plot("fuel_consumption_liter_per_pax_100km", save=False)
    assert plot is not None


def test_mean_fuel_emission_factor_plot(process):
    """Test that mean_fuel_emission_factor plot can be created."""
    plot = process.plot("mean_fuel_emission_factor", save=False)
    assert plot is not None


def test_emission_factor_per_fuel_category_plot(process):
    """Test that emission_factor_per_fuel_category plot can be created."""
    plot = process.plot("emission_factor_per_fuel_category", save=False)
    assert plot is not None


def test_emission_factor_per_fuel_plot(process):
    """Test that emission_factor_per_fuel plot can be created."""
    plot = process.plot("emission_factor_per_fuel", save=False)
    assert plot is not None


def test_cumulative_co2_emissions_plot(process):
    """Test that cumulative_co2_emissions plot can be created."""
    plot = process.plot("cumulative_co2_emissions", save=False)
    assert plot is not None


def test_direct_h2o_emissions_plot(process):
    """Test that direct_h2o_emissions plot can be created."""
    plot = process.plot("direct_h2o_emissions", save=False)
    assert plot is not None


def test_direct_nox_emissions_plot(process):
    """Test that direct_nox_emissions plot can be created."""
    plot = process.plot("direct_nox_emissions", save=False)
    assert plot is not None


def test_direct_sulfur_emissions_plot(process):
    """Test that direct_sulfur_emissions plot can be created."""
    plot = process.plot("direct_sulfur_emissions", save=False)
    assert plot is not None


def test_direct_soot_emissions_plot(process):
    """Test that direct_soot_emissions plot can be created."""
    plot = process.plot("direct_soot_emissions", save=False)
    assert plot is not None


def test_carbon_offset_plot(process):
    """Test that carbon_offset plot can be created."""
    plot = process.plot("carbon_offset", save=False)
    assert plot is not None


def test_cumulative_carbon_offset_plot(process):
    """Test that cumulative_carbon_offset plot can be created."""
    plot = process.plot("cumulative_carbon_offset", save=False)
    assert plot is not None


def test_final_effective_radiative_forcing_plot(process):
    """Test that final_effective_radiative_forcing plot can be created."""
    plot = process.plot("final_effective_radiative_forcing", save=False)
    assert plot is not None


def test_distribution_effective_radiative_forcing_plot(process):
    """Test that distribution_effective_radiative_forcing plot can be created."""
    plot = process.plot("distribution_effective_radiative_forcing", save=False)
    assert plot is not None


def test_energy_capex_plot(process):
    """Test that energy_capex plot can be created."""
    plot = process.plot("energy_capex", save=False)
    assert plot is not None


def test_energy_expenses_plot(process):
    """Test that energy_expenses plot can be created."""
    plot = process.plot("energy_expenses", save=False)
    assert plot is not None


def test_energy_mfsp_plot(process):
    """Test that energy_mfsp plot can be created."""
    plot = process.plot("energy_mfsp", save=False)
    assert plot is not None


def test_energy_expenses_discounted_plot(process):
    """Test that energy_expenses_discounted plot can be created."""
    plot = process.plot("energy_expenses_discounted", save=False)
    assert plot is not None


def test_energy_expenses_comparison_plot(process):
    """Test that energy_expenses_comparison plot can be created."""
    plot = process.plot("energy_expenses_comparison", save=False)
    assert plot is not None


def test_doc_fleet_breakdown_plot(process):
    """Test that doc_fleet_breakdown plot can be created."""
    plot = process.plot("doc_fleet_breakdown", save=False)
    assert plot is not None


def test_doc_fleet_category_plot(process):
    """Test that doc_fleet_category plot can be created."""
    plot = process.plot("doc_fleet_category", save=False)
    assert plot is not None


def test_airfare_breakdown_plot(process):
    """Test that airfare_breakdown plot can be created."""
    plot = process.plot("airfare_breakdown", save=False)
    assert plot is not None


def test_mfsp_detailled_plot(process):
    """Test that mfsp_detailled plot can be created."""
    plot = process.plot("mfsp_detailled", save=False)
    assert plot is not None


def test_annual_macc_simple_fleet_plot(process):
    """Test that annual_MACC_simple_fleet plot can be created."""
    plot = process.plot("annual_MACC_simple_fleet", save=False)
    assert plot is not None


def test_shadow_carbon_pricing_simple_fleet_plot(process):
    """Test that shadow_carbon_pricing_simple_fleet plot can be created."""
    plot = process.plot("shadow_carbon_pricing_simple_fleet", save=False)
    assert plot is not None

from dataclasses import dataclass


@dataclass
class SustainabilityAssessmentParameters(object):

    # Carbon budgets
    net_carbon_budget: float = 900
    T_nonCO2: float = 0.2
    carbon_dioxyde_removal_2100: float = 100
    world_co2_emissions_2019: float = 43.05
    world_ghg_emissions_2019: float = 59
    aviation_carbon_budget_allocated_share: float = 2.6
    aviation_equivalentcarbonbudget_allocated_share: float = 5.1

    # Energy availability - Biomass
    waste_biomass: float = 12
    crops_biomass: float = 63
    forest_residues_biomass: float = 17
    agricultural_residues_biomass: float = 57
    algae_biomass: float = 15
    fog_waste_biomass: float = 1
    oil_crops_biomass_share: float = 9
    sugarystarchy_crops_biomass_share: float = 28
    lignocellulosic_crops_biomass_share: float = 63  # Model here ?
    aviation_biomass_allocated_share: float = 10

    # Energy availability - Electricity
    available_electricity: float = 300
    aviation_electricity_allocated_share: float = 3

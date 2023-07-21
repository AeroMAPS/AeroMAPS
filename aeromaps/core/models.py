from aeromaps.models.air_transport.air_traffic.rpk import (
    RPK,
    RPKReference,
    RPKMeasures,
)
from aeromaps.models.air_transport.air_traffic.rtk import RTK, RTKReference
from aeromaps.models.air_transport.air_traffic.total_aircraft_distance import TotalAircraftDistance
from aeromaps.models.air_transport.aircraft_fleet_and_operations.load_factor.load_factor import (
    LoadFactor,
)
from aeromaps.models.air_transport.air_traffic.ask import ASK
from aeromaps.models.air_transport.aircraft_fleet_and_operations.operations.operations import (
    OperationsSimple,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.non_co2.non_co2 import (
    OperationsContrailsSimple,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.aircraft_efficiency import (
    PassengerAircraftEfficiencySimple,
    PassengerAircraftEfficiencyComplex,
    FreightAircraftEfficiency,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.aircraft_fleet_and_operations import (
    EnergyIntensity,
)
from aeromaps.models.air_transport.aircraft_energy.fuel_distribution import FuelDistribution
from aeromaps.models.sustainability_assessment.climate.carbon_budgets import GrossCarbonBudget
from aeromaps.models.sustainability_assessment.climate.equivalent_carbon_budgets import (
    EquivalentGrossCarbonBudget,
)
from aeromaps.models.air_transport.aircraft_energy.efficiency import (
    BiofuelEfficiency,
    ElectricityBasedFuelEfficiency,
)
from aeromaps.models.air_transport.aircraft_energy.fuel_emissions import (
    BiofuelEmissionFactor,
    ElectricityEmissionFactor,
    HydrogenEmissionFactor,
    ElectrofuelEmissionFactor,
    KeroseneEmissionFactor,
)
from aeromaps.models.air_transport.aircraft_energy.production_choices import (
    BiofuelProduction,
    HydrogenProduction,
)
from aeromaps.models.sustainability_assessment.energy.resources_availability import (
    BiomassAvailability,
    ElectricityAvailability,
)

from aeromaps.models.impacts.effective_radiative_forcing.effective_radiative_forcing import (
    ERF,
    DetailedERF,
)
from aeromaps.models.impacts.emissions.co2_emissions import (
    CO2Emissions,
    KayaFactors,
    CumulativeCO2Emissions,
    DetailedCo2Emissions,
    DetailedCumulativeCO2Emissions,
)
from aeromaps.models.impacts.emissions.non_co2_emissions import NOxEmissionIndex, NonCO2Emissions
from aeromaps.models.impacts.energy_resources.energy_consumption import (
    DropInFuelConsumption,
    HydrogenConsumption,
    EnergyConsumption,
)
from aeromaps.models.impacts.energy_resources.resources_consumption import (
    BiomassConsumption,
    ElectricityConsumption,
)
from aeromaps.models.impacts.equivalent_co2_emissions.equivalent_co2_emissions import (
    EquivalentCO2Emissions,
)
from aeromaps.models.impacts.climate.climate import Temperature
from aeromaps.models.impacts.others.others import EmissionsPerRPK, EmissionsPerRTK
from aeromaps.models.impacts.others.comparison import (
    CarbonBudgetConsumedShare,
    ResourcesConsumedShare,
)

models_simple = {
    "rpk_measures": RPKMeasures("rpk_measures"),
    "rpk": RPK("rpk"),
    "rpk_reference": RPKReference("rpk_reference"),
    "total_aircraft_distance": TotalAircraftDistance("total_aircraft_distance"),
    "rtk": RTK("rtk"),
    "rtk_reference": RTKReference("rtk_reference"),
    # "short_range_distribution": ShortRangeDistribution(
    #     "short_range_distribution"
    # ),
    # "rpk_short_range": RPKShortRange(
    #     "rpk_short_range"
    # ),
    "load_factor": LoadFactor("load_factor"),
    "ask": ASK("ask"),
    "operations_simple": OperationsSimple("operations_simple"),
    "operations_contrails_simple": OperationsContrailsSimple("operations_contrails_simple"),
    "passenger_aircraft_efficiency_simple": PassengerAircraftEfficiencySimple(
        "passenger_aircraft_efficiency_simple",
    ),
    "freight_aircraft_efficiency": FreightAircraftEfficiency(
        "freight_aircraft_efficiency",
    ),
    "energy_intensity": EnergyIntensity("energy_intensity"),
    "aircraft_energy": FuelDistribution("aircraft_energy"),
    "gross_carbon_budget": GrossCarbonBudget("gross_carbon_budget"),
    "equivalent_gross_carbon_budget": EquivalentGrossCarbonBudget(
        "equivalent_gross_carbon_budget",
    ),
    "biofuel_efficiency": BiofuelEfficiency("biofuel_efficiency"),
    "electricity_based_fuel_efficiency": ElectricityBasedFuelEfficiency(
        "electricity_based_fuel_efficiency",
    ),
    "biofuel_emission_factor": BiofuelEmissionFactor("biofuel_emission_factor"),
    "electricity_emission_factor": ElectricityEmissionFactor("electricity_emission_factor"),
    "hydrogen_emission_factor": HydrogenEmissionFactor("hydrogen_emission_factor"),
    "electrofuel_emission_factor": ElectrofuelEmissionFactor("electrofuel_emission_factor"),
    "kerosene_emission_factor": KeroseneEmissionFactor("kerosene_emission_factor"),
    "biofuel_production": BiofuelProduction("biofuel_production"),
    "hydrogen_production": HydrogenProduction(
        "hydrogen_production",
    ),
    "biomass_availability": BiomassAvailability("biomass_availability"),
    "electricity_availability": ElectricityAvailability("electricity_availability"),
    "effective_radiative_forcing": ERF("effective_radiative_forcing"),
    "detailed_erf": DetailedERF("detailed_erf"),
    "kaya_factors": KayaFactors("kaya_factors"),
    "co2_emissions": CO2Emissions("co2_emissions"),
    "cumulative_co2_emissions": CumulativeCO2Emissions("cumulative_co2_emissions"),
    "detailed_co2_emissions": DetailedCo2Emissions("detailed_co2_emissions"),
    "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
        "detailed_cumulative_co2_emissions",
    ),
    "nox_emission_index": NOxEmissionIndex("nox_emission_index"),
    "non_co2_emissions": NonCO2Emissions("non_co2_emissions"),
    "drop_in_fuel_consumption": DropInFuelConsumption("drop_in_fuel_consumption"),
    "hydrogen_consumption": HydrogenConsumption("hydrogen_consumption"),
    "energy_consumption": EnergyConsumption("energy_consumption"),
    "biomass_consumption": BiomassConsumption("biomass_consumption"),
    "electricity_consumption": ElectricityConsumption("electricity_consumption"),
    "equivalent_co2_emissions": EquivalentCO2Emissions("equivalent_co2_emissions"),
    "temperature": Temperature("temperature"),
    "emissions_per_rpk": EmissionsPerRPK("emissions_per_rpk"),
    "emissions_per_rtk": EmissionsPerRTK("emissions_per_rtk"),
    "carbon_budget_consumed_share": CarbonBudgetConsumedShare("carbon_budget_consumed_share"),
    "resources_consumed_share": ResourcesConsumedShare("resources_consumed_share"),
}


models_complex = {
    "rpk_measures": RPKMeasures("rpk_measures"),
    "rpk": RPK("rpk"),
    "rpk_reference": RPKReference("rpk_reference"),
    "total_aircraft_distance": TotalAircraftDistance("total_aircraft_distance"),
    "rtk": RTK("rtk"),
    "rtk_reference": RTKReference("rtk_reference"),
    # "short_range_distribution": ShortRangeDistribution(
    #     "short_range_distribution"
    # ),
    # "rpk_short_range": RPKShortRange(
    #     "rpk_short_range"
    # ),
    "load_factor": LoadFactor("load_factor"),
    "ask": ASK("ask"),
    "operations_simple": OperationsSimple("operations_simple"),
    "operations_contrails_simple": OperationsContrailsSimple("operations_contrails_simple"),
    "passenger_aircraft_efficiency_complex": PassengerAircraftEfficiencyComplex(
        "passenger_aircraft_efficiency_complex",
    ),
    "freight_aircraft_efficiency": FreightAircraftEfficiency(
        "freight_aircraft_efficiency",
    ),
    "energy_intensity": EnergyIntensity("energy_intensity"),
    "aircraft_energy": FuelDistribution("aircraft_energy"),
    "gross_carbon_budget": GrossCarbonBudget("gross_carbon_budget"),
    "equivalent_gross_carbon_budget": EquivalentGrossCarbonBudget(
        "equivalent_gross_carbon_budget",
    ),
    "biofuel_efficiency": BiofuelEfficiency("biofuel_efficiency"),
    "electricity_based_fuel_efficiency": ElectricityBasedFuelEfficiency(
        "electricity_based_fuel_efficiency",
    ),
    "biofuel_emission_factor": BiofuelEmissionFactor("biofuel_emission_factor"),
    "electricity_emission_factor": ElectricityEmissionFactor("electricity_emission_factor"),
    "hydrogen_emission_factor": HydrogenEmissionFactor("hydrogen_emission_factor"),
    "electrofuel_emission_factor": ElectrofuelEmissionFactor("electrofuel_emission_factor"),
    "kerosene_emission_factor": KeroseneEmissionFactor("kerosene_emission_factor"),
    "biofuel_production": BiofuelProduction("biofuel_production"),
    "hydrogen_production": HydrogenProduction(
        "hydrogen_production",
    ),
    "biomass_availability": BiomassAvailability("biomass_availability"),
    "electricity_availability": ElectricityAvailability("electricity_availability"),
    "effective_radiative_forcing": ERF("effective_radiative_forcing"),
    "detailed_erf": DetailedERF("detailed_erf"),
    "kaya_factors": KayaFactors("kaya_factors"),
    "co2_emissions": CO2Emissions("co2_emissions"),
    "cumulative_co2_emissions": CumulativeCO2Emissions("cumulative_co2_emissions"),
    "detailed_co2_emissions": DetailedCo2Emissions("detailed_co2_emissions"),
    "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
        "detailed_cumulative_co2_emissions",
    ),
    "nox_emission_index": NOxEmissionIndex("nox_emission_index"),
    "non_co2_emissions": NonCO2Emissions("non_co2_emissions"),
    "drop_in_fuel_consumption": DropInFuelConsumption("drop_in_fuel_consumption"),
    "hydrogen_consumption": HydrogenConsumption("hydrogen_consumption"),
    "energy_consumption": EnergyConsumption("energy_consumption"),
    "biomass_consumption": BiomassConsumption("biomass_consumption"),
    "electricity_consumption": ElectricityConsumption("electricity_consumption"),
    "equivalent_co2_emissions": EquivalentCO2Emissions("equivalent_co2_emissions"),
    "temperature": Temperature("temperature"),
    "emissions_per_rpk": EmissionsPerRPK("emissions_per_rpk"),
    "emissions_per_rtk": EmissionsPerRTK("emissions_per_rtk"),
    "carbon_budget_consumed_share": CarbonBudgetConsumedShare("carbon_budget_consumed_share"),
    "resources_consumed_share": ResourcesConsumedShare("resources_consumed_share"),
}

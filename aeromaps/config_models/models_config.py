"""AeroMAPS process models configuration."""

from typing import Optional

from aeromaps.config_models.base_config import BaseConfig
from pathlib import Path


class ClimateConfig(BaseConfig):
    climate_model_data_file: Path = Path("./default_climate_models/climate_model_fair.yaml")


class MarketsConfig(BaseConfig):
    markets_data_file: Path = Path("./default_markets/markets.yaml")


class FleetConfig(BaseConfig):
    aircraft_inventory_model_data_file: Path = Path("./default_fleet/aircraft_inventory.yaml")
    fleet_model_data_file: Path = Path("./default_fleet/fleet.yaml")


class FleetPushConfig(BaseConfig):
    classification_data_file: Path = Path(
        "./default_fleet_push/default_aircraft_classification.yaml"
    )
    market_param_data_file: Path = Path("./default_fleet_push/default_market_param.yaml")
    in_production_inventory_file: Path = Path(
        "./default_fleet_push/default_in_production_aircraft_inventory.yaml"
    )
    new_aircraft_inventory_file: Path = Path(
        "./default_fleet_push/default_new_aircraft_inventory.yaml"
    )
    aircraft_parameters_file: Path = Path(
        "../../utils/calibration_notebooks/"
        "fleet_calibrated_inputs_processed_here/"
        "aircraft_type_key_parameters.xlsx"
    )
    fleet_snapshot_file: Path = Path(
        "../../utils/calibration_notebooks/"
        "fleet_calibrated_inputs_processed_here/"
        "agg_fleet_end_2024.xlsx"
    )


class EnergyConfig(BaseConfig):
    energy_carriers_model_data_file: Path = Path(
        "./default_energy_carriers/energy_carriers_data.yaml"
    )
    resources_model_data_file: Path = Path("./default_energy_carriers/resources_data.yaml")
    processes_model_data_file: Path = Path("./default_energy_carriers/processes_data.yaml")


class OperationsConfig(BaseConfig):
    operations_model_data_file: Path = Path("./default_operations/operations_data.yaml")


class OffsetsConfig(BaseConfig):
    offsets_model_data_file: Path = Path("./default_offsets/offsets_data.yaml")


class LifeCycleAssessmentConfig(BaseConfig):
    lca_model_data_file: Path = Path("./default_lca/default_lca_model.json")
    split_by: str = "phase"


class ModelsConfig(BaseConfig):
    climate: ClimateConfig = ClimateConfig()
    markets: MarketsConfig = MarketsConfig()
    fleet: FleetConfig = FleetConfig()
    fleet_push: FleetPushConfig = FleetPushConfig()
    energy: EnergyConfig = EnergyConfig()
    operations: OperationsConfig = OperationsConfig()
    offsets: OffsetsConfig = OffsetsConfig()
    life_cycle_assessment: LifeCycleAssessmentConfig = LifeCycleAssessmentConfig()

    standards: list[str] = [
        "models_traffic",
        "models_efficiency_bottom_up",
        "models_energy_without_fuel_effect",
        "models_offset",
        "models_emissions",
        "models_sustainability",
        "models_energy_cost",
        "models_operation_cost_bottom_up",
        "models_production_cost",
        "models_abatements_cost",
    ]

    customs: Optional[dict[str, str]] = None

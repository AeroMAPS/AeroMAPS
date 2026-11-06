"""AeroMAPS process models configuration."""

from enum import StrEnum
from typing import Any

# from pydantic import field_validator

from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration
from pathlib import Path


class StandardModels(StrEnum):
    """Standard AeroMAPSModels."""

    MODELS_TRAFFIC = "models_traffic"
    MODELS_EFFICIENCY_BOTTOM_UP = "models_efficiency_bottom_up"
    MODELS_ENERGY_WITHOUT_FUEL_EFFECT = "models_energy_without_fuel_effect"
    MODELS_OFFSET = "models_offset"
    MODELS_EMISSIONS = "models_emissions"
    MODELS_SUSTAINABILITY = "models_sustainability"
    MODELS_ENERGY_COST = "models_energy_cost"
    MODELS_OPERATION_COST_BOTTOM_UP = "models_operation_cost_bottom_up"
    MODELS_PRODUCTION_COST = "models_production_cost"
    MODELS_ABATEMENTS_COST = "models_abatements_cost"


class ClimateModelConfiguration(BaseProcessConfiguration):
    climate_model_data_file: Path | str | None = "./default_climate_models/climate_model_fair.yaml"


class MarketsModelConfiguration(BaseProcessConfiguration):
    markets_data_file: Path | str | None = "./default_markets/markets.yaml"


class FleetModelConfiguration(BaseProcessConfiguration):
    aircraft_inventory_model_data_file: Path | str | None = (
        "./default_fleet/aircraft_inventory.yaml"
    )
    fleet_model_data_file: Path | str | None = "./default_fleet/fleet.yaml"


class FleetPushModelConfiguration(BaseProcessConfiguration):
    classification_data_file: Path | str | None = (
        "./default_fleet_push/default_aircraft_classification.yaml"
    )
    market_param_data_file: Path | str | None = "./default_fleet_push/default_market_param.yaml"
    in_production_inventory_file: Path | str | None = (
        "./default_fleet_push/default_in_production_aircraft_inventory.yaml"
    )
    new_aircraft_inventory_file: Path | str | None = (
        "./default_fleet_push/default_new_aircraft_inventory.yaml"
    )
    aircraft_parameters_file: Path | str | None = (
        "../../utils/calibration_notebooks/"
        "fleet_calibrated_inputs_processed_here/"
        "aircraft_type_key_parameters.xlsx"
    )
    fleet_snapshot_file: Path | str | None = (
        "../../utils/calibration_notebooks/"
        "fleet_calibrated_inputs_processed_here/"
        "agg_fleet_end_2024.xlsx"
    )


class EnergyModelConfiguration(BaseProcessConfiguration):
    energy_carriers_model_data_file: Path | str | None = (
        "./default_energy_carriers/energy_carriers_data.yaml"
    )
    resources_model_data_file: Path | str | None = "./default_energy_carriers/resources_data.yaml"
    processes_model_data_file: Path | str | None = "./default_energy_carriers/processes_data.yaml"


class OperationsModelConfiguration(BaseProcessConfiguration):
    operations_model_data_file: Path | str | None = "./default_operations/operations_data.yaml"


class OffsetsModelConfiguration(BaseProcessConfiguration):
    offsets_model_data_file: Path | str | None = "./default_offsets/offsets_data.yaml"


class LifeCycleAssessmentModelConfiguration(BaseProcessConfiguration):
    lca_model_data_file: Path | str | None = "./default_lca/default_lca_model.json"
    split_by: str = "phase"


class ProcessModelsConfiguration(BaseProcessConfiguration):
    climate: ClimateModelConfiguration = ClimateModelConfiguration()
    markets: MarketsModelConfiguration = MarketsModelConfiguration()
    fleet: FleetModelConfiguration = FleetModelConfiguration()
    fleet_push: FleetPushModelConfiguration = FleetPushModelConfiguration()
    energy: EnergyModelConfiguration = EnergyModelConfiguration()
    operations: OperationsModelConfiguration = OperationsModelConfiguration()
    offsets: OffsetsModelConfiguration = OffsetsModelConfiguration()
    life_cycle_assessment: LifeCycleAssessmentModelConfiguration = (
        LifeCycleAssessmentModelConfiguration()
    )

    standards: list[str] = [model.value for model in StandardModels]

    customs: dict[str, Any] = {}

    # TODO: properly validate standard models.
    # @field_validator("standards")
    # @classmethod
    # def is_standard_model(cls, value: list[str]) -> list[str]:
    #     """Check that the models in standards are indeed standard models."""
    #     standard_models = [model.value for model in StandardModels]
    #     for model in value:
    #         if model not in standard_models:
    #             raise ValueError(
    #                 f"The model {model} doesn't correspond to any standard model. "
    #                 f"Available standard models: {', '.join(standard_models)}"
    #             )

    #     return value

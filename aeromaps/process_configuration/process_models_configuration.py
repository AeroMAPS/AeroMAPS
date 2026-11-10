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


class BaseModelConfiguration(BaseProcessConfiguration):
    """Base class for model configuration classes."""

    standards: list[str] = []
    """The list of standard models to be used by the process from :mod:`aeromaps.models.models`."""

    customs: dict[str, Any] = {}
    """A mapping of custom models to be used by the process, if any."""


class ClimateModelConfiguration(BaseProcessConfiguration):
    """Climate model configuration."""

    climate_model_data_file: Path | str | None = "./default_climate_models/climate_model_fair.yaml"
    """The process' the climate model data file path, either relative or absolute."""


class MarketsModelConfiguration(BaseProcessConfiguration):
    """Markets model configuration."""

    markets_data_file: Path | str | None = "./default_markets/markets.yaml"
    """The process' the markets model data file path, either relative or absolute."""


class FleetModelConfiguration(BaseProcessConfiguration):
    """Fleet model configuration."""

    aircraft_inventory_model_data_file: Path | str | None = (
        "./default_fleet/aircraft_inventory.yaml"
    )
    """The process' the aircraft inventory model data file path, either relative or absolute."""

    fleet_model_data_file: Path | str | None = "./default_fleet/fleet.yaml"
    """The process' the fleet model data file path, either relative or absolute."""


class FleetPushModelConfiguration(BaseProcessConfiguration):
    """Fleet push model configuration."""

    classification_data_file: Path | str | None = (
        "./default_fleet_push/default_aircraft_classification.yaml"
    )
    """The process' the fleet push model's classification data file path, either relative or absolute."""

    market_param_data_file: Path | str | None = "./default_fleet_push/default_market_param.yaml"
    """The process' the fleet push model's market parameters data file path, either relative or absolute."""

    in_production_inventory_file: Path | str | None = (
        "./default_fleet_push/default_in_production_aircraft_inventory.yaml"
    )
    """The process' the fleet push model's in production inventory data file path, either relative or absolute."""

    new_aircraft_inventory_file: Path | str | None = (
        "./default_fleet_push/default_new_aircraft_inventory.yaml"
    )
    """The process' the fleet push model's new inventory file path, either relative or absolute."""

    aircraft_parameters_file: Path | str | None = (
        "../../utils/calibration_notebooks/"
        "fleet_calibrated_inputs_processed_here/"
        "aircraft_type_key_parameters.xlsx"
    )
    """The process' the fleet push model's aircraft parameters file path, either relative or absolute."""

    fleet_snapshot_file: Path | str | None = (
        "../../utils/calibration_notebooks/"
        "fleet_calibrated_inputs_processed_here/"
        "agg_fleet_end_2024.xlsx"
    )
    """The process' the fleet push model's fleet snapshot data file path, either relative or absolute."""


class EnergyModelConfiguration(BaseProcessConfiguration):
    """Energy model configuration."""

    energy_carriers_model_data_file: Path | str | None = (
        "./default_energy_carriers/energy_carriers_data.yaml"
    )
    resources_model_data_file: Path | str | None = "./default_energy_carriers/resources_data.yaml"
    processes_model_data_file: Path | str | None = "./default_energy_carriers/processes_data.yaml"


class OperationsModelConfiguration(BaseProcessConfiguration):
    """Operations model configuration."""

    operations_model_data_file: Path | str | None = "./default_operations/operations_data.yaml"
    """The process' the operations model data file path, either relative or absolute."""


class OffsetsModelConfiguration(BaseProcessConfiguration):
    """Offsets model configuration."""

    offsets_model_data_file: Path | str | None = "./default_offsets/offsets_data.yaml"
    """The process' the offsets model data file path, either relative or absolute."""


class LifeCycleAssessmentModelConfiguration(BaseProcessConfiguration):
    """Life cycle assessment model configuration."""

    lca_model_data_file: Path | str | None = "./default_lca/default_lca_model.json"
    """The process' the life cycle assessment model data file path, either relative or absolute."""

    split_by: str | None = "phase"
    """Axis to split the life cycle assessment results by."""

    # TODO: better define the field typing as the field is never used during the tests.
    methods: list[Any] | None = None
    """List of impact assessment methods available."""


class ProcessModelsConfiguration(BaseModelConfiguration):
    """The process' models configuration."""

    climate: ClimateModelConfiguration = ClimateModelConfiguration()
    """The process' climate model configuration."""

    markets: MarketsModelConfiguration = MarketsModelConfiguration()
    """The process' markets model configuration."""

    fleet: FleetModelConfiguration = FleetModelConfiguration()
    """The process' fleet model configuration."""

    fleet_push: FleetPushModelConfiguration = FleetPushModelConfiguration()
    """The process' fleet push model configuration."""

    energy: EnergyModelConfiguration = EnergyModelConfiguration()
    """The process' energy model configuration."""

    operations: OperationsModelConfiguration = OperationsModelConfiguration()
    """The process' operations model configuration."""

    offsets: OffsetsModelConfiguration = OffsetsModelConfiguration()
    """The process' offsets model configuration."""

    life_cycle_assessment: LifeCycleAssessmentModelConfiguration = (
        LifeCycleAssessmentModelConfiguration()
    )
    """The process' life cycle assessment model configuration."""

    standards: list[str] = [model.value for model in StandardModels]
    """The list of standard models to be used by the process from :mod:`aeromaps.models.models`."""

    customs: dict[str, Any] = {}
    """A mapping of custom models to be used by the process, if any."""

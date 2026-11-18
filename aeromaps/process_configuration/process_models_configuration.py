"""AeroMAPS process models configuration."""

from enum import Enum
from typing import Any

from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration
from pathlib import Path


# TODO: To be removed once support for 3.10 is dropped.
# Work around as StrEnum is not available on python 3.10.
try:
    from enum import StrEnum
except ImportError:

    class StrEnum(str, Enum):
        pass


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
    """The model bundles to be used by the process.
    Each must be a `models_*` dict define in the :mod:`aeromaps.models.models`.
    An unknown name raises a Value error. 

    NOTE: This field replaces the default list. Include all you need.

    Keep efficiency / operation-cost bundles consistent with the `fleet block:
        - top-down  → trend-based efficiency, no explicit fleet needed
        - bottom-up → requires the `fleet` block below
    """

    customs: dict[str, Any] = {}
    """An optional mapping of custom models loaded from external python files. 

    Path is relative to the data directory.
    Custom models can be inferred either by:
    - adding `::MyModelClass` to the end of the path 
        (eg: my_model : "path/to/model.py::MyModelClass") -> model inferred: `MyModelClass`
    - with the key of the model in the mapping as a CamelCase.
        (eg: another_model: "path/to/another.py") -> model inferred: `AnotherModel`
    """


class ClimateModelConfiguration(BaseProcessConfiguration):
    """Climate model configuration."""

    climate_model_data_file: Path | str | None = "./default_climate_models/climate_model_fair.yaml"
    """The the climate model data file path of the process, either relative or absolute.
    FaIR (default), available models: GWP*, IPCC or LWE — see default_climate_models/.
    """


class MarketsModelConfiguration(BaseProcessConfiguration):
    """Markets model configuration."""

    markets_data_file: Path | str | None = "./default_markets/markets.yaml"
    """The the markets model data file path of the process, either relative or absolute."""


class FleetModelConfiguration(BaseProcessConfiguration):
    """Fleet model configuration."""

    aircraft_inventory_model_data_file: Path | str | None = (
        "./default_fleet/aircraft_inventory.yaml"
    )
    """The the aircraft inventory model data file path of the process, either relative or absolute."""

    fleet_model_data_file: Path | str | None = "./default_fleet/fleet.yaml"
    """The the fleet model data file path of the process, either relative or absolute."""


class FleetPushModelConfiguration(BaseProcessConfiguration):
    """Fleet push model configuration."""

    classification_data_file: Path | str | None = (
        "./default_fleet_push/default_aircraft_classification.yaml"
    )
    """The the fleet push model's classification data file path of the process, either relative or absolute."""

    market_param_data_file: Path | str | None = "./default_fleet_push/default_market_param.yaml"
    """The the fleet push model's market parameters data file path of the process, either relative or absolute."""

    in_production_inventory_file: Path | str | None = (
        "./default_fleet_push/default_in_production_aircraft_inventory.yaml"
    )
    """The the fleet push model's in production inventory data file path of the process, either relative or absolute."""

    new_aircraft_inventory_file: Path | str | None = (
        "./default_fleet_push/default_new_aircraft_inventory.yaml"
    )
    """The the fleet push model's new inventory file path of the process, either relative or absolute."""

    aircraft_parameters_file: Path | str | None = (
        "../../utils/calibration_notebooks/"
        "fleet_calibrated_inputs_processed_here/"
        "aircraft_type_key_parameters.xlsx"
    )
    """The the fleet push model's aircraft parameters file path of the process, either relative or absolute."""

    fleet_snapshot_file: Path | str | None = (
        "../../utils/calibration_notebooks/"
        "fleet_calibrated_inputs_processed_here/"
        "agg_fleet_end_2024.xlsx"
    )
    """The the fleet push model's fleet snapshot data file path of the process, either relative or absolute."""


class EnergyModelConfiguration(BaseProcessConfiguration):
    """Generic energy model configuration."""

    energy_carriers_model_data_file: Path | str | None = (
        "./default_energy_carriers/energy_carriers_data.yaml"
    )
    """The energy carrier model data file path of the process, either relative or absolute."""
    resources_model_data_file: Path | str | None = "./default_energy_carriers/resources_data.yaml"

    """The energy resources model data file path of the process, either relative or absolute."""

    processes_model_data_file: Path | str | None = "./default_energy_carriers/processes_data.yaml"
    """The energy processes model data file path of the process, either relative or absolute."""


class OperationsModelConfiguration(BaseProcessConfiguration):
    """Operations model configuration."""

    operations_model_data_file: Path | str | None = "./default_operations/operations_data.yaml"
    """The the operations model data file path of the process, either relative or absolute."""


class OffsetsModelConfiguration(BaseProcessConfiguration):
    """Offsets model configuration."""

    offsets_model_data_file: Path | str | None = "./default_offsets/offsets_data.yaml"
    """The the offsets model data file path of the process, either relative or absolute."""


class LifeCycleAssessmentModelConfiguration(BaseProcessConfiguration):
    """Life cycle assessment model configuration."""

    lca_model_data_file: Path | str | None = "./default_lca/default_lca_model.json"
    """The the life cycle assessment model data file path of the process, either relative or absolute."""

    split_by: str | None = "phase"
    """Optional grouping of results. Axis to split the life cycle assessment results by."""

    methods: list[str] | None = None
    """Optional impact assessment methods."""


class ProcessModelsConfiguration(BaseModelConfiguration):
    """The models configuration of the process."""

    climate: ClimateModelConfiguration | None = ClimateModelConfiguration()
    """The climate model configuration of the process."""

    markets: MarketsModelConfiguration | None = MarketsModelConfiguration()
    """The markets model configuration of the process."""

    fleet: FleetModelConfiguration | None = FleetModelConfiguration()
    """The fleet model configuration of the process.
    Only needed with a `bottom-up` efficiency bundle declared in the standards field.
    """

    fleet_push: FleetPushModelConfiguration | None = FleetPushModelConfiguration()
    """The fleet push model configuration of the process."""

    energy: EnergyModelConfiguration | None = EnergyModelConfiguration()
    """The generic energy model configuration of the process."""

    operations: OperationsModelConfiguration | None = OperationsModelConfiguration()
    """The operations model configuration of the process."""

    offsets: OffsetsModelConfiguration | None = OffsetsModelConfiguration()
    """The optional generic offsets model configuration of the process.

    Offsetting schemes (ETS, CORSIA, removals...), each with its own quantity rule and
    price; replaces the simple offset models and the single offset price.
    """

    life_cycle_assessment: LifeCycleAssessmentModelConfiguration | None = (
        LifeCycleAssessmentModelConfiguration()
    )
    """The optional life cycle assessment model configuration of the process."""

    standards: list[str] = [model.value for model in StandardModels]

"""AeroMAPS multi-regional process configuration model."""

from typing import Any, Literal

from aeromaps.process_configuration.process_configuration import (
    AeroMAPSProcessConfiguration,
    BaseProcessConfiguration,
)


class RegionConfiguration(BaseProcessConfiguration):
    config_file: str | None = None


class WeightedAverageConfiguration(BaseProcessConfiguration):
    variable: str | None = None
    weight_by: str | None = None


class AggregationConfiguration(BaseProcessConfiguration):
    sum: list[str] | None = None
    weighted_average: list[WeightedAverageConfiguration] | None = None


class RegionalisationConfiguration(BaseProcessConfiguration):
    execution_mode: Literal["separate_process", "unified_mda"] = "separate_processes"
    global_namespace: str = "overall"
    regions: dict[str, RegionConfiguration] = {}
    aggregation: AggregationConfiguration = AggregationConfiguration()
    global_models: dict[str, Any] = {}
    top_level_models: dict[str, Any] = {}


class AeroMAPSMultiRegionalProcessConfiguration(AeroMAPSProcessConfiguration):
    """Configuration data model for multi-regional processes."""

    regionalisation: RegionalisationConfiguration = RegionalisationConfiguration()

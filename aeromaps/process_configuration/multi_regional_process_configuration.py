"""AeroMAPS multi-regional process configuration model."""

from typing import Any

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
    execution_mode: str | None = None
    global_namespace: str | None = None
    regions: dict[str, RegionConfiguration] | None = None
    aggregation: AggregationConfiguration = AggregationConfiguration()
    global_models: dict[str, Any] = {}


class AeroMAPSMultiRegionalProcessConfiguration(AeroMAPSProcessConfiguration):
    regionalisation: RegionalisationConfiguration = RegionalisationConfiguration()

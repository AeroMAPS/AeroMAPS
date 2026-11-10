"""AeroMAPS multi-regional process configuration model."""

from typing import Any, Literal

from aeromaps.process_configuration.process_configuration import (
    AeroMAPSProcessConfiguration,
    BaseProcessConfiguration,
)


class RegionConfiguration(BaseProcessConfiguration):
    """The multi-regional process region configuration."""

    config_file: str | None = None
    """The region configuration file, either relative or absolute.."""


class WeightedAverageConfiguration(BaseProcessConfiguration):
    """Weighted average aggregation configurations."""

    variable: str | None = None
    """The variable to be aggregated by weighted average."""

    weight_by: str | None = None
    """The variable to compute the weighted average by."""


class AggregationConfiguration(BaseProcessConfiguration):
    """The multi-regional process aggregation rules configuration."""

    sum: list[str] | None = None
    """The list of variables to be aggregated by summation."""

    weighted_average: list[WeightedAverageConfiguration] | None = None
    """The list of weighted averaged configurations."""


class RegionalisationConfiguration(BaseProcessConfiguration):
    """The process' regionalisation configuration."""

    execution_mode: Literal["separate_processes", "unified_mda"] = "separate_processes"
    """The multi-regional process execution mode."""

    global_namespace: str = "overall"
    """Namespace prefix for aggregated global outputs."""

    regions: dict[str, RegionConfiguration] = {}
    """The region name to region configuration mapping of regions for the multi-regional process."""

    aggregation: AggregationConfiguration = AggregationConfiguration()
    """Process aggregation configuration."""

    global_models: dict[str, Any] = {}
    """Models to  deliberately keep out of the multi-regional process namespacing."""

    top_level_models: dict[str, Any] = {}
    """Models that operate in a global namespace (under :attr:`MultiRegionalProcess._global_namespace`) in the multi-regional process."""


class AeroMAPSMultiRegionalProcessConfiguration(AeroMAPSProcessConfiguration):
    """Configuration data model for multi-regional processes."""

    regionalisation: RegionalisationConfiguration = RegionalisationConfiguration()
    """The process' regionalisation configuration."""

"""
Multi-regional modeling components for AeroMAPS.

This module provides models and utilities for running multiple regional AeroMAPS
scenarios in parallel and aggregating their outputs into global metrics.
"""

from aeromaps.models.multi_regional.regional_aggregator import RegionalAggregator

__all__ = ["RegionalAggregator"]

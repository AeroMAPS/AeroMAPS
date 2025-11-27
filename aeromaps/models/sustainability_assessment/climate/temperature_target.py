"""
temperature_target
===========================
Module to compute global world and aviation temperature targets.
"""

from typing import Tuple
from scipy.optimize import fsolve


from aeromaps.models.base import AeroMAPSModel


class TemperatureTarget(AeroMAPSModel):
    """
    Global world and aviation temperature targets.

    Parameters
    ----------
    name : str, optional
        Name of the model instance, by default "temperature_target"
    """
    def __init__(self, name="temperature_target", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        historical_temperature_increase: float,
        temperature_target: float,
        aviation_temperature_target_allocated_share: float,
    ) -> Tuple[float, float]:
        """
        Temperature targets calculation.

        Parameters
        ----------
        historical_temperature_increase : float
            Historical temperature increase (°C).
        temperature_target : float
            Global temperature target (°C), set by user.
        aviation_temperature_target_allocated_share : float
            Aviation temperature target allocated share (%).

        Returns
        -------
        world_temperature_target : float
            World temperature target (°C).
        aviation_temperature_target : float
            Aviation temperature target (°C).
        """

        world_temperature_target = temperature_target-historical_temperature_increase
        aviation_temperature_target = world_temperature_target * aviation_temperature_target_allocated_share / 100

        self.float_outputs["world_temperature_target"] = world_temperature_target
        self.float_outputs["aviation_temperature_target"] = aviation_temperature_target

        return world_temperature_target, aviation_temperature_target


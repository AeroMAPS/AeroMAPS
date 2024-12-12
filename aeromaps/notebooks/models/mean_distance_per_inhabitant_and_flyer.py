from typing import Tuple
import pandas as pd
from aeromaps.models.base import (
    AeroMAPSModel,
    AeromapsInterpolationFunction,
)


class MeanDistancePerInhabitantFlyer(AeroMAPSModel):
    def __init__(self, name="mean_distance_per_inhabitant_flyer", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk: pd.Series,
        world_inhabitant_number_reference_years: list,
        world_inhabitant_number_reference_years_values: list,
        inhabitant_flyer_share_reference_years: list,
        inhabitant_flyer_share_reference_years_values: list,
    ) -> Tuple[pd.Series, pd.Series]:
        """Mean distance per inhabitant reference calculation."""
        # Calculation of the mean distance per inhabitant

        world_inhabitant_number = AeromapsInterpolationFunction(
            self,
            world_inhabitant_number_reference_years,
            world_inhabitant_number_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "world_inhabitant_number"] = world_inhabitant_number
        mean_distance_per_inhabitant = rpk / world_inhabitant_number
        self.df.loc[:, "mean_distance_per_inhabitant"] = mean_distance_per_inhabitant

        # Calculation of the mean distance per flyer
        inhabitant_flyer_share = AeromapsInterpolationFunction(
            self,
            inhabitant_flyer_share_reference_years,
            inhabitant_flyer_share_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "inhabitant_flyer_share "] = inhabitant_flyer_share
        mean_distance_per_flyer = mean_distance_per_inhabitant / (inhabitant_flyer_share / 100)
        self.df.loc[:, "mean_distance_per_flyer"] = mean_distance_per_flyer

        return (mean_distance_per_inhabitant, mean_distance_per_flyer)

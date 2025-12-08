from typing import Tuple
import pandas as pd
from aeromaps.models.base import (
    AeroMAPSModel,
    aeromaps_interpolation_function,
)


class MeanDistancePerInhabitantFlyer(AeroMAPSModel):
    """Simple model for calculating distance per flyer.

    Parameters
    ----------
    name
        Name of the model instance ('mean_distance_per_inhabitant_flyer' by default).
    """
    
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
        """Mean distance per inhabitant reference calculation.
        
        Parameters
        ----------
        rpk
            Revenue Passenger Kilometers [-].
        world_inhabitant_number_reference_years
            Reference years for the inhabitants [yr].
        world_inhabitant_number_reference_years_values
            Inhabitants for the reference years [-].
        inhabitant_flyer_share_reference_years
            Reference years for the share of flyers among the inhabitants [yr].
        inhabitant_flyer_share_reference_years_values
            Share of flyers among the inhabitants for the reference years [%].

        Returns
        -------
        mean_distance_per_inhabitant
            Mean distance per inhabitant [km].
        mean_distance_per_flyer
            Mean distance per flyer [km].
        """
        
        # Calculation of the mean distance per inhabitant

        world_inhabitant_number = aeromaps_interpolation_function(
            self,
            world_inhabitant_number_reference_years,
            world_inhabitant_number_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "world_inhabitant_number"] = world_inhabitant_number
        mean_distance_per_inhabitant = rpk / world_inhabitant_number
        self.df.loc[:, "mean_distance_per_inhabitant"] = mean_distance_per_inhabitant

        # Calculation of the mean distance per flyer
        inhabitant_flyer_share = aeromaps_interpolation_function(
            self,
            inhabitant_flyer_share_reference_years,
            inhabitant_flyer_share_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "inhabitant_flyer_share "] = inhabitant_flyer_share
        mean_distance_per_flyer = mean_distance_per_inhabitant / (inhabitant_flyer_share / 100)
        self.df.loc[:, "mean_distance_per_flyer"] = mean_distance_per_flyer

        return (mean_distance_per_inhabitant, mean_distance_per_flyer)

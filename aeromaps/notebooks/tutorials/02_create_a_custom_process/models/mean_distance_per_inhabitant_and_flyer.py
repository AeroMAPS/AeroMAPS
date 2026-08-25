from typing import Tuple
import jax.numpy as jnp
import pandas as pd
from aeromaps.models.base import (
    AeroMAPSModel,
    aeromaps_interpolation_function,
)
from aeromaps.models.jax_helpers import jax_interpolation_function


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

    # Intermediates ``compute`` writes to ``self.df`` without declaring them as
    # GEMSEO outputs; ``jax_compute`` returns them after the declared outputs so
    # both paths expose the same columns (the trailing space in the flyer-share
    # column name is historical, hence the explicit mapping).
    jax_extra_output_names = ("world_inhabitant_number", "inhabitant_flyer_share")
    jax_df_output_names = {"inhabitant_flyer_share": "inhabitant_flyer_share "}

    # Interpolation reference years are static knots for the JAX path.
    jax_static_input_names = (
        "world_inhabitant_number_reference_years",
        "inhabitant_flyer_share_reference_years",
    )

    def jax_compute(
        self,
        rpk,
        world_inhabitant_number_reference_years,
        world_inhabitant_number_reference_years_values,
        inhabitant_flyer_share_reference_years,
        inhabitant_flyer_share_reference_years_values,
    ):
        """JAX version of :meth:`compute` (same signature, pure jax.numpy).

        Providing it lets this custom model run on the JAX execution path when
        the process is created with ``use_jax=True``; ``compute`` is unchanged
        and still used otherwise.
        """
        world_inhabitant_number = jax_interpolation_function(
            self,
            world_inhabitant_number_reference_years,
            world_inhabitant_number_reference_years_values,
        )
        mean_distance_per_inhabitant = jnp.asarray(rpk) / world_inhabitant_number

        inhabitant_flyer_share = jax_interpolation_function(
            self,
            inhabitant_flyer_share_reference_years,
            inhabitant_flyer_share_reference_years_values,
        )
        mean_distance_per_flyer = mean_distance_per_inhabitant / (inhabitant_flyer_share / 100.0)

        return (
            mean_distance_per_inhabitant,
            mean_distance_per_flyer,
            world_inhabitant_number,
            inhabitant_flyer_share,
        )

"""
operations
===============

Module for computing operational improvements (efficiency gains) used in
energy and emissions calculations. Provides logistic and interpolation-based
models to produce an annual `operations_gain` series representing percentage
reductions in fuel consumption per ASK.
"""

from numbers import Number

import numpy as np
import pandas as pd

import jax.numpy as jnp

from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function
from aeromaps.models.jax_helpers import hist_mask, jax_interpolation_function, years_index


class OperationsLogistic(AeroMAPSModel):
    """Logistic model implementation to project operational efficiency gains.

    Parameters
    ----------
    name
        Name of the model instance ('operations_logistic' by default).
    """

    def __init__(self, name="operations_logistic", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        operations_final_gain: float,
        operations_start_year: Number,
        operations_duration: float,
    ) -> pd.Series:
        """Compute the annual operational efficiency gains.

        Parameters
        ----------
        operations_final_gain
            Final impact of operational improvements in terms of percentage reduction in fuel consumption per ASK [%].
        operations_start_year
            Start year for implementing operational improvements to reduce fuel consumption [yr].
        operations_duration
            Duration for implementing 98% of operational improvements to reduce fuel consumption [yr].

        Returns
        -------
        operations_gain
            Impact of operational improvements in terms of percentage reduction in fuel consumption per ASK [%].
        """

        transition_year = operations_start_year + operations_duration / 2
        operations_limit = 0.02 * operations_final_gain
        operations_parameter = np.log(100 / 2 - 1) / (operations_duration / 2)
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "operations_gain"] = 0
        for k in range(self.prospection_start_year - 1, self.end_year + 1):
            if (
                operations_final_gain / (1 + np.exp(-operations_parameter * (k - transition_year)))
                < operations_limit
            ):
                self.df.loc[k, "operations_gain"] = 0
            else:
                self.df.loc[k, "operations_gain"] = operations_final_gain / (
                    1 + np.exp(-operations_parameter * (k - transition_year))
                )

        operations_gain = self.df["operations_gain"]

        return operations_gain

    def jax_compute(
        self,
        operations_final_gain,
        operations_start_year,
        operations_duration,
    ):
        """JAX version of :meth:`compute` (same signature, pure jax.numpy)."""
        transition_year = operations_start_year + operations_duration / 2.0
        operations_limit = 0.02 * operations_final_gain
        operations_parameter = jnp.log(100.0 / 2.0 - 1.0) / (operations_duration / 2.0)

        years = jnp.asarray(years_index(self), dtype=jnp.float64)
        sigmoid_val = operations_final_gain / (
            1.0 + jnp.exp(-operations_parameter * (years - transition_year))
        )
        gain = jnp.where(sigmoid_val < operations_limit, 0.0, sigmoid_val)
        # The sigmoid is applied from prospection_start_year - 1.
        operations_gain = jnp.where(
            years_index(self) < self.prospection_start_year - 1, 0.0, gain
        )
        return operations_gain


class OperationsInterpolation(AeroMAPSModel):
    """Interpolation-based implementation to project operational efficiency gains.

    Parameters
    ----------
    name
        Name of the model instance ('operations_interpolation' by default).
    """

    def __init__(self, name="operations_interpolation", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        operations_gain_reference_years: list,
        operations_gain_reference_years_values: list,
    ) -> pd.Series:
        """Compute the annual operations efficiency gain by interpolating provided reference points.

        Parameters
        ----------
        operations_gain_reference_years
            Reference years for the operations gain [yr].
        operations_gain_reference_years_values
            Operations gain for the reference years [%].

        Returns
        -------
        operations_gain
            Impact of operational improvements in terms of percentage reduction in fuel consumption per ASK [%].
        """

        operations_gain_prospective = aeromaps_interpolation_function(
            self,
            operations_gain_reference_years,
            operations_gain_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "operations_gain"] = operations_gain_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "operations_gain"] = 0
        operations_gain = self.df["operations_gain"]

        return operations_gain

    # Interpolation reference years are static knots for the JAX path.
    jax_static_input_names = ("operations_gain_reference_years",)

    def jax_compute(
        self,
        operations_gain_reference_years,
        operations_gain_reference_years_values,
    ):
        """JAX version of :meth:`compute` (same signature, pure jax.numpy)."""
        operations_gain_prospective = jax_interpolation_function(
            self, operations_gain_reference_years, operations_gain_reference_years_values
        )
        operations_gain = jnp.where(hist_mask(self), 0.0, operations_gain_prospective)
        return operations_gain

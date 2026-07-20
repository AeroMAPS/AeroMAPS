"""
Utility base classes and climate-related helper functions used by AeroMAPS models.
"""

import xarray as xr
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import warnings


class AeroMapsCustomDataType:
    """
    Custom type class to handle yaml data input for AeroMAPS models.
    It contains reference years and values, and interpolation options.
    When an AeroMapsCustomDataType is found when reading the yaml it
    instantiates an interpolation model from yaml_interpolator.py

    Parameters
    ----------
    reference_data
        Dictionary containing interpolation attributes.

    Attributes
    ----------
    years
        List of reference years for the interpolation.
    values
        List of reference values for the interpolation.
    method
        Interpolation method, default is 'linear'.
    positive_constraint
        If True, ensures interpolated values are non-negative.
    """

    def __init__(self, reference_data: dict):
        self.years = reference_data["years"]
        self.values = reference_data["values"]
        if "method" in reference_data:
            self.method = reference_data["method"]
        else:
            self.method = "linear"
        if "positive_constraint" in reference_data:
            self.positive_constraint = reference_data["positive_constraint"]
        else:
            self.positive_constraint = False


# Allowed values for AeroMAPSModel.MARKET_SCOPE (the market-axis granularity of a
# discipline). The *region* axis is orthogonal and is applied uniformly by
# namespacing regional disciplines (see aeromaps.core.gemseo.apply_namespace_to_disciplines),
# so a discipline never needs to declare its region granularity — only its market one.
#
#   "per_market"      One discipline INSTANCE per market, parameterised by a
#                     ``market_id``; every I/O name carries that market as a token
#                     (``ask_<mid>``, ``<mid>_rpk``). Instantiated in a loop by the
#                     ``create_market_*`` factories.
#   "cross_market"    A SINGLE instance spanning all markets: it loops over the
#                     market registry internally and emits market-templated I/O
#                     (the price-coupled demand models and the top-down aircraft
#                     efficiency models).
#   "aggregator"      A single instance that sums per-market series into the bare
#                     total consumed downstream (``ask``, ``rpk``, ``load_factor``).
#   "market_agnostic" Operates on already-aggregated totals and never touches the
#                     market dimension (the default: most downstream cost/emissions
#                     /climate models).
MARKET_SCOPES = frozenset({"per_market", "cross_market", "aggregator", "market_agnostic"})


class AeroMAPSModel(object):
    """
    Base class for AeroMAPS model components that provides shared state and utilities.

    Parameters
    ----------
    name
        Name of the model instance.
    parameters
        AeroMAPS process parameters object containing model inputs.
    model_type
        Type of the model, either 'auto' or 'custom'.

    Attributes
    ----------
    MARKET_SCOPE
        Class attribute declaring how this discipline relates to the market
        dimension — one of :data:`MARKET_SCOPES`. Single source of truth for the
        per-market / cross-market / aggregator / market-agnostic distinction, so
        callers (and the N2 topology) don't have to infer it from the class name
        or the factory wiring. Defaults to ``"market_agnostic"``; market-family
        disciplines override it at the class level.
    name
        Name of the model instance.
    parameters
        Reference to the parameters object passed at construction.
    float_outputs
        Dictionary storing scalar outputs produced by the model.
    model_type
        Configured model type, either 'auto' or 'custom'.
    input_names
        Dictionary of expected input names and types (only for 'custom' models).
    output_names
        Dictionary of output names and types (only for 'custom' models).
    default_input_data
        Default input data provided internally by the model (only for 'custom' models).
    _skip_data_type_validation
        Flag to skip input/output data type validation for custom models.
    climate_historic_start_year
        Start year for climate-related historical data.
    historic_start_year
        Start year for general historical data.
    prospection_start_year
        First year of the prospection/projection period.
    end_year
        Last year of the model time horizon.
    df
        pandas DataFrame indexed by model years for vector outputs.
    df_climate
        pandas DataFrame indexed by climate years for climate-specific outputs.
    xarray_lca
        xarray DataArray placeholder used by some LCA computations.
    years
        Numpy array of years spanning the model horizon.
    """

    # Market-axis granularity of this discipline (see MARKET_SCOPES above).
    # Market-family disciplines override this at the class level.
    MARKET_SCOPE: str = "market_agnostic"

    def __init__(self, name, parameters=None, model_type="auto"):
        self.name = name
        self.parameters = parameters
        self.float_outputs = {}
        if self.parameters is not None:
            self._initialize_df()

        # Verify model type
        self.model_type = model_type
        if self.model_type == "custom":
            self.input_names = {}  # Dictionary to store input names and their types (or values)
            self.output_names = {}  # Dictionary to store output names and their types (or values)
            self.default_input_data = {}  # Dictionary to store default input data (i.e. provided internally by the model rather than parameters.json)
            self._skip_data_type_validation = False  # Whether to skip input/output data type validation. If True, input_names and output_names can be lists of names only.
        elif self.model_type != "auto":
            raise ValueError("model_type must be either 'auto' or 'custom'")

    def _initialize_df(self):
        self.climate_historic_start_year = self.parameters.climate_historic_start_year
        self.historic_start_year = self.parameters.historic_start_year
        self.prospection_start_year = self.parameters.prospection_start_year
        # Initialisation of last_historical_year is based on the assumption that the year before the prospection start year is the last historical year.
        self.last_historical_year = self.parameters.prospection_start_year - 1
        self.end_year = self.parameters.end_year
        self.df: pd.DataFrame = pd.DataFrame(
            index=range(self.historic_start_year, self.end_year + 1)
        )
        self.df_climate: pd.DataFrame = pd.DataFrame(
            index=range(self.climate_historic_start_year, self.end_year + 1)
        )
        self.xarray_lca: xr.DataArray = xr.DataArray()
        self.years = np.linspace(self.historic_start_year, self.end_year, len(self.df.index))

    def _store_outputs(self, output_data, climate_outputs_keys=None):
        """
        Store vector outputs in self.df and float outputs in self.float_outputs.
        Checks if the columns already exist to update them in place, otherwise joins new columns.

        Parameters
        ----------
        output_data
            Dictionary with output names as keys and output data as values.
        climate_outputs_keys
            List of keys from output_data that should be stored in self.df_climate instead of self.df.
        """
        # Store climate-specific outputs in self.df_climate if provided
        if climate_outputs_keys:
            climate_items = {k: v for k, v in output_data.items() if k in climate_outputs_keys}
            for key, val in climate_items.items():
                if isinstance(val, pd.Series):
                    # check index of climate output series is compatible with climate years
                    if not val.index.isin(self.df_climate.index).all():
                        raise ValueError(
                            f"Climate output {key} has an index that is not compatible with climate years."
                        )
                    self.df_climate.loc[:, key] = val
                else:
                    raise ValueError(
                        f"Climate output {key} is not a valid type (expected pandas Series)."
                    )
            regular_items = {k: v for k, v in output_data.items() if k not in climate_outputs_keys}
        else:
            regular_items = output_data

        # Separate series-like outputs and scalar outputs from regular items
        series_items = {k: v for k, v in regular_items.items() if isinstance(v, pd.Series)}
        other_items = {k: v for k, v in regular_items.items() if k not in series_items}

        # If there are Series outputs, update existing columns and join new ones
        if series_items:
            df_series = pd.DataFrame(series_items)

            # Columns that already exist in self.df -> update in place
            existing_cols = [c for c in df_series.columns if c in self.df.columns]
            for c in existing_cols:
                self.df.loc[:, c] = df_series[c]

            # New columns -> join to self.df
            new_cols = [c for c in df_series.columns if c not in self.df.columns]
            if new_cols:
                self.df = self.df.join(df_series[new_cols])

        # Handle non-series outputs (floats) and validate types
        for key, val in other_items.items():
            if isinstance(val, float) or isinstance(val, (int, np.floating, np.integer)):
                # store numeric scalars as float_outputs (coerce ints)
                self.float_outputs[key] = float(val)
            elif isinstance(val, pd.Series):
                # Shouldn't reach here, but handle defensively
                self.df.loc[:, key] = val
            else:
                raise ValueError(f"Output {key} is not a valid type.")


def aeromaps_interpolation_function(
    self,
    reference_years,
    reference_years_values,
    method="linear",
    positive_constraint=False,
    model_name="Not provided",
):
    """
    Interpolate values across the scenario horizon from reference years and values.

    Parameters
    ----------
    reference_years
        Sequence of reference years used for interpolation.
    reference_years_values
        Sequence of values corresponding to the reference years.
    method
        Interpolation method to use (e.g. 'linear').
    positive_constraint
        If True, negative interpolated values are clipped to zero.
    model_name
        Optional name used in warnings.

    Returns
    -------
    interpolation_function_values
        Series of interpolated values indexed by year taken from the model's DataFrame.
    """
    # Main
    if len(reference_years_values) == 0:
        raise ValueError(f"[{model_name}] reference_years_values must not be empty.")
    if len(reference_years) > 0 and len(reference_years) != len(reference_years_values):
        raise ValueError(
            f"[{model_name}] reference_years and reference_years_values must have the same length "
            f"(got {len(reference_years)} years and {len(reference_years_values)} values)."
        )
    if len(reference_years) == 0:
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "interpolation_function_values"] = reference_years_values[0]
    else:
        interpolation_function = interp1d(
            reference_years,
            reference_years_values,
            kind=method,
        )

        # If first reference year is lower than prospection start year, we start interpolating before
        if reference_years[0] != self.prospection_start_year:
            warnings.warn(
                f"\n[Interpolation Model: {model_name} Warning]\n"
                f"The first reference year ({reference_years[0]}) differs from the prospection start year ({self.prospection_start_year}).\n"
                f"Interpolation will begin at the first reference year."
            )
            prospection_start_year = reference_years[0]
        else:
            prospection_start_year = self.prospection_start_year

        if reference_years[-1] == self.end_year:
            for k in range(prospection_start_year, reference_years[-1] + 1):
                if positive_constraint and interpolation_function(k) <= 0.0:
                    self.df.loc[k, "interpolation_function_values"] = 0.0
                else:
                    self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
        elif reference_years[-1] > self.end_year:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on aeromaps_interpolation_function:"
                + " The last reference year for the interpolation is higher than end_year, the interpolation function is therefore not used in its entirety.",
            )
            for k in range(prospection_start_year, self.end_year + 1):
                if positive_constraint and interpolation_function(k) <= 0.0:
                    self.df.loc[k, "interpolation_function_values"] = 0.0
                else:
                    self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
        else:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on aeromaps_interpolation_function:"
                + " The last reference year for the interpolation is lower than end_year, the value associated to the last reference year is therefore used as a constant for the upper years.",
            )
            for k in range(prospection_start_year, reference_years[-1] + 1):
                if positive_constraint and interpolation_function(k) <= 0.0:
                    self.df.loc[k, "interpolation_function_values"] = 0.0
                else:
                    self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
            for k in range(reference_years[-1] + 1, self.end_year + 1):
                self.df.loc[k, "interpolation_function_values"] = self.df.loc[
                    k - 1, "interpolation_function_values"
                ]

    interpolation_function_values = self.df.loc[:, "interpolation_function_values"]

    # Delete intermediate df column
    self.df.pop("interpolation_function_values")

    return interpolation_function_values


def aeromaps_leveling_function(
    self, reference_periods, reference_periods_values, model_name="Not provided"
):
    """
    Build a stepwise series that holds values constant across defined reference periods.

    Parameters
    ----------
    reference_periods
        Sequence of period boundary years used to define steps.
    reference_periods_values
        Sequence of values corresponding to each reference period.
    model_name
        Optional name used in warnings.

    Returns
    -------
    leveling_function_values
        Series of leveled values indexed by year taken from the model's DataFrame.
    """
    # Main
    if len(reference_periods) == 0:
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "leveling_function_values"] = reference_periods_values[0]
    else:
        if reference_periods[-1] == self.end_year:
            for i in range(0, len(reference_periods) - 1):
                for k in range(reference_periods[i], reference_periods[i + 1] + 1):
                    self.df.loc[k, "leveling_function_values"] = reference_periods_values[i]
        elif reference_periods[-1] > self.end_year:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on aeromaps_leveling_function:"
                + " The last reference year for the leveling is higher than end_year, the leveling function is therefore not used in its entirety.",
            )
            for i in range(0, len(reference_periods) - 1):
                for k in range(reference_periods[i], reference_periods[i + 1] + 1):
                    if k <= self.end_year:
                        self.df.loc[k, "leveling_function_values"] = reference_periods_values[i]
                    else:
                        pass
        else:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on aeromaps_leveling_function:"
                + " The last reference year for the leveling is lower than end_year, the value associated to the last reference period is therefore used as a constant for the upper period.",
            )
            for i in range(0, len(reference_periods) - 1):
                for k in range(reference_periods[i], reference_periods[i + 1] + 1):
                    self.df.loc[k, "leveling_function_values"] = reference_periods_values[i]
            for k in range(reference_periods[-1] + 1, self.end_year + 1):
                self.df.loc[k, "leveling_function_values"] = self.df.loc[
                    k - 1, "leveling_function_values"
                ]

    leveling_function_values = self.df.loc[:, "leveling_function_values"]

    # Delete intermediate df column
    self.df.pop("leveling_function_values")

    return leveling_function_values

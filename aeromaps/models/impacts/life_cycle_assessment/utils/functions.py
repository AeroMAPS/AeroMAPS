"""
Helper functions to support AeroMAPS life cycle assessment models.
"""

import re
import pandas as pd
import numpy as np


def tuple_to_varname(items):
    """
    Convert a tuple or list of strings into a clean, Python-friendly variable name.

    Parameters
    ----------
    items : tuple or list
        The tuple or list of strings to convert.

    Returns
    -------
    str
        A cleaned variable name string.
    """
    if isinstance(items, (list, tuple)):
        text = "__".join(items)  # join parts with double underscores
    else:
        text = str(items)

    # Lowercase everything
    text = text.lower()

    # Replace anything that’s not alphanumeric or underscore with underscore
    text = re.sub(r"[^0-9a-zA-Z_]+", "_", text)

    # Remove leading/trailing underscores and collapse multiple underscores
    text = re.sub(r"_+", "_", text).strip("_")

    # Add lca to variable
    text = "lca_" + text

    return text


def is_not_nan(x):
    """
    Return True if x is not NaN or None. Handles single values and arrays/lists.

    Parameters
    ----------
    x : any
        The input to check.

    Returns
    -------
    bool
        True if x is not NaN or None, False otherwise.
    """
    if x is None:
        return False
    if isinstance(x, (float, int, np.number)):
        return not pd.isna(x)
    if isinstance(x, (pd.Series, np.ndarray, list, tuple)):
        return pd.notna(np.asarray(x)).any()
    return True


def compute_param_length(params):
    """
    Compute the length of parameter values, ensuring consistency across all parameters.

    Parameters
    ----------
    params : Dict[str, ListOrScalar]
        Dictionary of parameter names and their corresponding values.

    Returns
    -------
    int
        The length of the parameter values.
    """
    # Check length of parameter values
    param_length = 1
    for key, val in params.items():
        if isinstance(val, (list, np.ndarray)):
            if param_length == 1:
                param_length = len(val)
            elif param_length != len(val):
                raise Exception("Parameters should be a single value or a list of same number of values")
    return param_length
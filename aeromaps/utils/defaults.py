import pandas as pd


def get_default_series(start_year, end_year, fill_value=0.0):
    """
    Create a pandas Series with years as index and a constant fill value.

    Parameters
    ----------
    start_year
        The starting year of the series.
    end_year
        The ending year of the series.
    fill_value
        The constant value to fill the series with (default is 0.0).

    Returns
    -------
    pd.Series
        A pandas Series indexed by years from start_year to end_year, filled with fill_value.

    """
    return pd.Series(
        [fill_value] * len(range(start_year, end_year + 1)),
        index=range(start_year, end_year + 1),
    )

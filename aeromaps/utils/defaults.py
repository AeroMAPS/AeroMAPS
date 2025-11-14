import pandas as pd


def get_default_series(start_year, end_year, fill_value=0.0):
    return pd.Series(
        [fill_value] * len(range(start_year, end_year + 1)),
        index=range(start_year, end_year + 1),
    )

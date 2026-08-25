"""Parity tests between the pandas and the JAX execution paths.

``create_process(..., use_jax=True)`` wraps every model exposing a
``jax_compute`` in a gemseo-jax discipline. The results must be identical to the
pandas path: same variables in ``vector_outputs`` / ``climate_outputs`` /
``float_outputs``, same values.
"""

import numpy as np
import pandas as pd
import pytest

from aeromaps import create_process

CONFIG_DIR = "aeromaps/tests/tested_configs"

# Columns the JAX path stores in ``model.df`` although the pandas ``compute``
# only returns them without writing them to the dataframe.
JAX_ONLY_COLUMNS = {"operational_profit_per_rpk"}


def _drop_duplicate_columns(frame):
    return frame.loc[:, ~frame.columns.duplicated()]


def _assert_frames_match(pandas_frame, jax_frame, label):
    pandas_frame = _drop_duplicate_columns(pandas_frame)
    jax_frame = _drop_duplicate_columns(jax_frame)

    missing = sorted(set(pandas_frame.columns) - set(jax_frame.columns))
    assert not missing, f"{label}: columns missing from the JAX run: {missing}"

    extra = sorted(set(jax_frame.columns) - set(pandas_frame.columns) - JAX_ONLY_COLUMNS)
    assert not extra, f"{label}: unexpected columns in the JAX run: {extra}"

    for column in pandas_frame.columns:
        expected = pd.to_numeric(pandas_frame[column], errors="coerce").to_numpy(float)
        actual = pd.to_numeric(jax_frame[column], errors="coerce").to_numpy(float)
        assert expected.shape == actual.shape, f"{label}/{column}: shape mismatch"
        # NaN marks "no value for this year" in both paths, so compare the
        # zero-filled arrays and require the NaN patterns to agree.
        np.testing.assert_array_equal(
            np.isnan(expected), np.isnan(actual), err_msg=f"{label}/{column}: NaN pattern"
        )
        np.testing.assert_allclose(
            np.nan_to_num(actual),
            np.nan_to_num(expected),
            rtol=1e-6,
            atol=1e-8,
            err_msg=f"{label}/{column}",
        )


@pytest.mark.parametrize(
    "config_name",
    [
        "config_basic",
        "config_advanced_simplified",
        "config_elasticity_demand",
    ],
)
def test_jax_matches_pandas(config_name):
    config_file = f"{CONFIG_DIR}/{config_name}.yaml"

    pandas_process = create_process(configuration_file=config_file)
    pandas_process.compute()

    jax_process = create_process(configuration_file=config_file, use_jax=True)
    jax_process.compute()

    _assert_frames_match(
        pandas_process.data["vector_outputs"], jax_process.data["vector_outputs"], "vector_outputs"
    )
    _assert_frames_match(
        pandas_process.data["climate_outputs"],
        jax_process.data["climate_outputs"],
        "climate_outputs",
    )

    pandas_floats = pandas_process.data["float_outputs"]
    jax_floats = jax_process.data["float_outputs"]
    missing = sorted(set(pandas_floats) - set(jax_floats))
    assert not missing, f"float_outputs missing from the JAX run: {missing}"
    for name, expected in pandas_floats.items():
        np.testing.assert_allclose(
            float(jax_floats[name]), float(expected), rtol=1e-6, atol=1e-8, err_msg=name
        )

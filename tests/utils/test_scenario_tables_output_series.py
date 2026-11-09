"""``output_series`` reads year-keyed mappings in chronological order."""

import numpy as np

from aeromaps.utils.scenario_tables import output_series, value_at


def test_year_keyed_mapping_is_sorted_by_year():
    view = {"vector_outputs": {"x": {"2002": 3.0, "2000": 1.0, "2001": 2.0, "2010": 4.0}}}
    np.testing.assert_array_equal(output_series(view, "x"), [1.0, 2.0, 3.0, 4.0])


def test_list_is_kept_as_is_and_value_at_indexes_by_year():
    view = {"vector_outputs": {"x": [5.0, 6.0, 7.0]}}
    values = output_series(view, "x")
    assert value_at(values, 2001) == 6.0

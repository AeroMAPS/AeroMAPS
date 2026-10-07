"""Validation errors and the LaTeX table emitter."""

import pytest

from aeromaps.utils.scenario_tables import latex_table, relative_errors


def test_point_errors_are_relative_to_the_reference():
    # Reproduced runs 10 % above a flat reference of 100 from 2000.
    reproduced = [110.0] * 51
    errors = relative_errors(reproduced, [2000, 2050], [100.0, 100.0], (2010, 2050), (2000, 2050))
    assert errors[:2] == pytest.approx([10.0, 10.0])
    assert errors[-1] == pytest.approx(10.0)


def test_reference_is_interpolated_onto_the_reported_year():
    """The reference may be sampled irregularly; the comparison is at our year."""
    reproduced = [0.0] * 51
    reproduced[20] = 150.0  # 2020
    errors = relative_errors(reproduced, [2000, 2040], [100.0, 300.0], (2020,), (2020, 2020))
    # Reference interpolates to 200 at 2020, so 150 is 25 % low.
    assert errors[0] == pytest.approx(-25.0)


def test_cumulative_integrates_both_sides_on_the_same_grid():
    """A reference with sparse anchors must not weight its own anchor years."""
    reproduced = [0.0] * 51
    for year in range(2000, 2051):
        reproduced[year - 2000] = 100.0
    # Reference rises 0 -> 200 linearly, mean 100 over the span, so the cumulative
    # error is zero even though it is anchored at only two points.
    errors = relative_errors(reproduced, [2000, 2050], [0.0, 200.0], (2050,), (2000, 2050))
    assert errors[-1] == pytest.approx(0.0)


def test_latex_table_structure():
    fragment = latex_table(
        headers=["Scenario", "2050"],
        rows=[["S1", "1.0"], ["S2", "2.0"]],
        widths=["0.20", "0.10"],
        caption="A caption.",
        label="tab:example",
    )
    assert r"\begin{tabular}{m{0.20\textwidth}M{0.10\textwidth}}" in fragment
    assert r"\textbf{Scenario} & \textbf{2050} \\" in fragment
    assert "S1 & 1.0 \\\\" in fragment
    assert r"\label{tab:example}" in fragment
    # booktabs rules, in order, and the caption above the tabular.
    assert fragment.index(r"\caption") < fragment.index(r"\toprule")
    assert (
        fragment.index(r"\toprule") < fragment.index(r"\midrule") < fragment.index(r"\bottomrule")
    )


def test_latex_table_passes_raw_rows_through():
    """Separator and multicolumn rows are emitted verbatim, not joined."""
    raw = r"  &   \\"
    fragment = latex_table(["A", "B"], [raw, ["1", "2"]], ["0.5", "0.5"], "c", "tab:x")
    assert raw in fragment


def test_latex_table_rejects_a_mismatched_column_count():
    with pytest.raises(ValueError, match="2 headers against 3"):
        latex_table(["A", "B"], [], ["0.1", "0.2", "0.3"], "c", "tab:x")


def test_widths_are_written_as_given():
    """Passing 0.10 as a float would emit 0.1, a noisier diff for the same width."""
    fragment = latex_table(["A"], [], ["0.10"], "c", "tab:x")
    assert r"m{0.10\textwidth}" in fragment

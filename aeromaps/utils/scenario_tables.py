"""Build the tables a paper reports scenario results in.

Two pieces, both deliberately unopinionated about what is being tabulated:

:func:`relative_errors`
    Compare a reproduced trajectory against a reference one, at named years and
    over a cumulative span. This is the arithmetic behind a validation table, and
    it is worth having in one place because the cumulative column is easy to get
    subtly wrong: both sides have to be integrated on the same yearly grid, or a
    reference sampled at irregular intervals silently weights its own anchors.

:func:`latex_table`
    Wrap already-formatted rows in a booktabs table. Formatting the cells stays
    with the caller, since how a number is written (a signed percentage, a mass, a
    dash for a value that does not exist) is a property of the table being built
    and not of the wrapper.
"""

import numpy as np


def relative_errors(
    reproduced, reference_years, reference_values, at_years, cumulative_span, first_year=2000
):
    """Relative error at each reporting year, then over the cumulative span.

    Parameters
    ----------
    reproduced : sequence of float
        The reproduced annual series, starting at ``first_year``.
    reference_years, reference_values : sequence
        The reference curve, which may be sampled irregularly; it is interpolated
        onto the years being compared.
    at_years : sequence of int
        Years to report a point error at.
    cumulative_span : tuple of int
        Inclusive ``(start, end)`` for the cumulative column.
    first_year : int, optional
        Year ``reproduced`` begins at.

    Returns
    -------
    list of float
        One percentage per entry in ``at_years``, then the cumulative one. A
        positive value means the reproduction sits above the reference.
    """
    series = np.asarray(reproduced, dtype=float)

    def at(year):
        return series[year - first_year]

    errors = [
        100.0 * (at(year) / float(np.interp(year, reference_years, reference_values)) - 1.0)
        for year in at_years
    ]

    # Integrate both on the same yearly grid, so an irregularly sampled reference
    # does not weight its own anchor years.
    span = np.arange(cumulative_span[0], cumulative_span[1] + 1)
    reference = np.interp(span, reference_years, reference_values)
    errors.append(100.0 * (np.array([at(year) for year in span]).sum() / reference.sum() - 1.0))
    return errors


def latex_table(headers, rows, widths, caption, label, caption_margin="0.5in", small=True):
    """A booktabs table, as a LaTeX fragment.

    Parameters
    ----------
    headers : sequence of str
        Column headings, emitted inside ``\\textbf{}``.
    rows : sequence
        Each entry is either a sequence of already-formatted cells, joined with
        ``&``, or a raw string emitted verbatim. The raw form carries separator
        rows and anything using ``\\multicolumn``.
    widths : sequence of str or float
        Column widths as fractions of ``\\textwidth``. The first column is set
        ``m{}`` (left aligned) and the rest ``M{}`` (centred); both are vertically
        centred, so a heading that wraps to two lines does not leave the first
        column riding above the others. Pass strings to control the written form:
        ``0.10`` as a float emits ``0.1``, which is the same width but a noisier
        diff against a hand-maintained file.
    caption, label : str
        Caption body and the ``\\label`` key.
    caption_margin : str, optional
        Symmetric caption margin. Asymmetric margins put the caption off-centre
        above a centred table, which is why this is a single value.

    Returns
    -------
    str
        The fragment, newline-terminated.
    """
    if len(headers) != len(widths):
        raise ValueError(f"{len(headers)} headers against {len(widths)} column widths")

    spec = "".join(
        r"%s{%s\textwidth}" % ("m" if index == 0 else "M", width)
        for index, width in enumerate(widths)
    )

    out = [
        r"\begin{table}",
        r"\captionsetup{margin=%s}" % caption_margin,
        r"\caption{%s}" % caption,
        r"\centering",
    ]
    if small:
        out.append(r"\begin{small}")
    out += [
        r"\begin{tabular}{%s}" % spec,
        "",
        r"\toprule",
        "",
        " & ".join(r"\textbf{%s}" % header for header in headers) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        out.append(row if isinstance(row, str) else " & ".join(row) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    if small:
        out.append(r"\end{small}")
    out.append(r"\label{%s}" % label)
    out.append(r"\end{table}")
    return "\n".join(out) + "\n"

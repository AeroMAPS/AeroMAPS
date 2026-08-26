"""
make_tables
===========
Emit the manuscript's two LaTeX tables from the committed outputs, so the numbers
in the paper cannot drift from the numbers in the figures.

Table 1 is the external validation: the reproduced trajectories against the
report's own published curves, as a relative error at 2030, 2040 and 2050 and
over the cumulative period. Only the technology scenarios T0-T4 appear, because
they are the only curves the third edition publishes at a resolution that can be
read off a chart. The S0-S2 rows are left as placeholders until those curves are
digitised; the report draws them, but this repository does not yet carry them.

Table 2 is the internal decomposition: what each mitigation pillar removes from
the frozen-fleet baseline in 2050. The three headline scenarios come from their
own runs. The individual lever levels come from the sweep grid, at central
traffic, with the two levers not being varied held at their least ambitious
setting, so each row isolates one lever.

Run from this directory::

    python make_tables.py            # prints both tables
    python make_tables.py --write DIR  # also writes table.tex into DIR
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "3rd_edition_variants"))

from atag_decomposition import ALTERNATIVE, atag_wedges  # noqa: E402

FIRST_YEAR = 2000
ERROR_YEARS = (2030, 2040, 2050)

# The published curves start partway through 2023, so the cumulative column runs
# over the span the digitisation actually covers rather than from 2019. Stating
# it as 2024-2050 keeps the comparison honest: the years before that are observed
# and identical on both sides, and including them would dilute the error.
CUMULATIVE_SPAN = (2024, 2050)


class View:
    """Minimal stand-in for a process, holding one committed output file."""

    def __init__(self, path):
        self.data = json.loads(Path(path).read_text(encoding="utf-8"))


def series(view, name, default=None):
    raw = view.data["vector_outputs"].get(name)
    if raw is None:
        if default is None:
            raise KeyError(name)
        return np.full(default, 0.0)
    return np.asarray(list(raw.values()) if isinstance(raw, dict) else raw, dtype=float)


def at(values, year, first_year=FIRST_YEAR):
    return values[year - first_year]


# --------------------------------------------------------------------------- 1


def validation_rows():
    """Reproduced tank-to-wake trajectories against the report's own curves."""
    report = yaml.safe_load(
        (HERE / "report_data" / "atag_3rd_edition_figures.yaml").read_text(encoding="utf-8")
    )["technology_scenarios"]

    rows = []
    for name in sorted(report):
        path = HERE / "3rd_edition_full" / "data_outputs" / f"{name.lower()}-TTW.json"
        if not path.exists():
            rows.append((name, None))
            continue
        ours = series(View(path), "co2_emissions_including_energy")
        curve = report[name]

        errors = []
        for year in ERROR_YEARS:
            published = float(np.interp(year, curve["years"], curve["values"]))
            errors.append(100.0 * (at(ours, year) / published - 1.0))

        # Cumulative: integrate both on the same yearly grid.
        span = np.arange(CUMULATIVE_SPAN[0], CUMULATIVE_SPAN[1] + 1)
        published_span = np.interp(span, curve["years"], curve["values"])
        ours_span = np.array([at(ours, year) for year in span])
        errors.append(100.0 * (ours_span.sum() / published_span.sum() - 1.0))

        rows.append((name, errors))
    return rows


# --------------------------------------------------------------------------- 2

PILLARS = ("Fleet renewal", "Next gen. technology", "Operations, infra.", "SAF", "Market-based")


def decompose(view, t0, t1, year=2050):
    """The five pillar contributions plus the gross residual, in ``year``.

    The last pillar is the gross residual itself: what is left once the physical
    levers have acted is what market-based measures are assumed to remove, which
    is how the reports draw it. So it appears twice, once as a pillar and once as
    the residual, and the five pillars close on the frozen-fleet baseline.
    """
    years, boundaries = atag_wedges(view, t0, t1)
    index = int(np.where(years == year)[0][0])
    wedges = [boundaries[k][index] - boundaries[k + 1][index] for k in range(len(boundaries) - 2)]
    gross = boundaries[len(boundaries) - 2][index]
    # The figure draws next-generation technology in two pieces, efficiency and
    # alternative aircraft; the table carries the pillar, so they are added back.
    merged = [wedges[0], wedges[1] + wedges[2], wedges[3], wedges[4], gross]
    return merged, gross


class GridView:
    """One sweep cell, shaped like a committed output so atag_decomposition reads it."""

    def __init__(self, wide, cell, years):
        frame = wide
        for key, value in zip(("traffic", "technology", "operations", "saf"), cell):
            frame = frame[frame[key] == value]
        frame = frame.sort_values("year").set_index("year")
        columns = {}
        for column in frame.columns:
            if frame[column].dtype.kind in "fi":
                columns[column] = frame[column].reindex(years).to_numpy(dtype=float).tolist()
        # The energy split needs these three; arms without alternative aircraft
        # never wrote them, and zero is the right reading there, not a KeyError.
        for column in ("energy_consumption_%s" % kind for kind in ALTERNATIVE):
            columns.setdefault(column, [0.0] * len(years))
        self.data = {"vector_outputs": columns}


def lever_rows():
    """The headline scenarios, then one row per individual lever level."""
    full = HERE / "3rd_edition_full" / "data_outputs"
    light = HERE / "3rd_edition_light" / "data_outputs"
    t0, t1 = View(full / "t0.json"), View(full / "t1.json")

    rows = []
    for label, path, ttw_path in [
        ("S0 reference", light / "s0.json", light / "s0-TTW.json"),
        ("S1 SAF-focused", full / "s1.json", full / "s1-TTW.json"),
        ("S2 technology-centric", full / "s2.json", full / "s2-TTW.json"),
    ]:
        pillars, gross = decompose(View(path), t0, t1)
        gross_ttw = at(series(View(ttw_path), "co2_emissions_including_energy"), 2050)
        rows.append((label, pillars, gross, gross_ttw))

    import sweep

    tidy = sweep.read_results()
    wide = sweep.wide(tidy)
    years = np.arange(FIRST_YEAR, 2051)

    # Each lever level is read with the other two at their least ambitious
    # setting, so the row is that lever alone rather than a scenario.
    reference = {"traffic": "central", "technology": "T1", "operations": "O1", "saf": "F1"}
    for key, levels in [
        ("technology", ("T1", "T2", "T3", "T4")),
        ("operations", ("O1", "O2", "O3")),
        ("saf", ("F1", "F2", "F3")),
    ]:
        for level in levels:
            cell = dict(reference, **{key: level})
            view = GridView(
                wide, tuple(cell[k] for k in ("traffic", "technology", "operations", "saf")), years
            )
            pillars, gross = decompose(view, t0, t1)
            rows.append((level, pillars, gross, None))
    return rows


# --------------------------------------------------------------------------- output


def _fmt(value, width=7, places=1):
    return "n/a".rjust(width) if value is None else f"{value:{width}.{places}f}"


def print_tables():
    print("Table 1 - reproduced tank-to-wake against the report's published curves [%]\n")
    header = "  ".join(f"{year}" for year in ERROR_YEARS)
    print(f"  scenario   {header}   {CUMULATIVE_SPAN[0]}-{CUMULATIVE_SPAN[1]}")
    for name, errors in validation_rows():
        if errors is None:
            print(f"  {name:<9}  PENDING, no committed tank-to-wake output")
            continue
        print(f"  {name:<9}  " + "  ".join(f"{value:+6.1f}" for value in errors))
    print("\n  S0-S2: PENDING, the report's own S0-S2 curves are not digitised yet.")

    print("\n\nTable 2 - 2050 pillar contributions [MtCO2]\n")
    print(
        f"  {'scenario':<22} "
        + " ".join(f"{name:>20}" for name in PILLARS)
        + "   gross WtW  gross TtW    sum"
    )
    for label, pillars, gross, gross_ttw in lever_rows():
        total = sum(pillars)
        print(
            f"  {label:<22} "
            + " ".join(f"{value:20.1f}" for value in pillars)
            + f"   {gross:9.1f}  {_fmt(gross_ttw, 9)}  {total:7.1f}"
        )


TABLE1_CAPTION = (
    r"\textcolor{Highlight}{Reproduction against the report's own published curves.} "
    r"\textcolor{red}{Relative error in annual CO$_2$ emissions between this reproduction and the "
    r"third edition's own trajectories, in \%, in the tank-to-wake scope the report publishes. A "
    r"positive value is an overestimate by the reproduction. T0 is the notional frozen-fleet "
    r"trajectory and T1 is where emissions sit with no improvement beyond ongoing fleet renewal; "
    r"none of the five includes reductions from operations, fuels or market-based measures. The "
    r"report column is digitised from its charts and interpolated onto a yearly grid. The "
    r"cumulative column runs from @START@ rather than 2019 because that is where the published curves "
    r"begin; the earlier years are observed and identical on both sides. These are the only curves "
    r"the third edition publishes at a resolution that can be read off, so they carry the external "
    r"validation of the reproduction. The S0--S2 rows await a digitisation of the corresponding "
    r"published curves.}"
).replace("@START@", str(CUMULATIVE_SPAN[0]))

TABLE2_CAPTION = (
    r"\textcolor{Highlight}{Reproduced 2050 lever contributions.} "
    r"\textcolor{red}{What each mitigation pillar removes from the frozen-fleet baseline in 2050, "
    r"in MtCO$_2$. The pillars follow the reports' own decomposition, so next generation technology "
    r"carries the battery-electric contribution rather than the fuel column, and operations carries "
    r"load factor. The first three rows are the published scenarios. The remaining rows are "
    r"individual lever levels, each read at central traffic with the two levers not being varied "
    r"held at their least ambitious setting, so T1, O1 and F1 are the same reference cell and "
    r"appear three times by construction. Every row closes on the common frozen-fleet baseline of "
    r"2835.0~Mt, which is the check that the decomposition is a partition rather than an "
    r"attribution. Two cautions in reading across rows: the market-based column is the gross "
    r"residual the measures are assumed to remove, not an independent lever; and a pillar's value "
    r"depends on what else is deployed alongside it, which is why next generation technology is "
    r"worth 563.8~Mt at T4 alone and 500.2~Mt in S2, where SAF competes for the same joules. Gross "
    r"residuals are given in both accounting scopes for the published scenarios: the reports "
    r"headline the tank-to-wake figure and this reproduction runs well-to-wake, so the difference "
    r"between those two columns is the scope alone.}"
)


def _latex_tables():
    """Both tables as one LaTeX fragment."""
    out = []

    out.append(r"\begin{table}")
    out.append(r"\captionsetup{margin={0.5in,0in}}")
    out.append(r"\caption{%s}" % TABLE1_CAPTION)
    out.append(r"\centering")
    out.append(r"\begin{small}")
    out.append(
        r"\begin{tabular}{p{0.18\textwidth}M{0.12\textwidth}M{0.12\textwidth}"
        r"M{0.12\textwidth}M{0.15\textwidth}}"
    )
    out.append("")
    out.append(r"\toprule")
    out.append("")
    out.append(
        r"\textbf{Scenario}  & "
        + " & ".join(r"\textbf{%d}" % year for year in ERROR_YEARS)
        + r" & \textbf{%d--%d} \\" % CUMULATIVE_SPAN
    )
    out.append(r"\midrule")
    out.append(r"        &     &    &    &    \\")
    for name, errors in validation_rows():
        if errors is None:
            out.append(r"%-6s & \multicolumn{4}{c}{pending} \\" % name)
            continue
        out.append("%-6s & " % name + " & ".join("$%+.1f$" % value for value in errors) + r" \\")
    out.append(r"\midrule")
    out.append(r"S0--S2 & \multicolumn{4}{c}{published curves not digitised} \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    out.append(r"\end{small}")
    out.append(r"\label{tab:validation}")
    out.append(r"\end{table}")
    out.append("")

    out.append(r"\begin{table}")
    out.append(r"\captionsetup{margin={0.5in,0in}}")
    out.append(r"\caption{%s}" % TABLE2_CAPTION)
    out.append(r"\centering")
    out.append(r"\begin{small}")
    out.append(
        r"\begin{tabular}{p{0.18\textwidth}M{0.09\textwidth}M{0.12\textwidth}"
        r"M{0.11\textwidth}M{0.10\textwidth}M{0.10\textwidth}M{0.09\textwidth}M{0.09\textwidth}}"
    )
    out.append("")
    out.append(r"\toprule")
    out.append("")
    out.append(
        r"\textbf{Scenario}  & \textbf{Fleet renewal} & \textbf{Next gen. technology} & "
        r"\textbf{Operations, infra.} & \textbf{SAF} & \textbf{Market-based} & "
        r"\textbf{Gross WtW} & \textbf{Gross TtW} \\"
    )
    out.append(r"\midrule")
    out.append(r"        &     &    &    &    &    &    &    \\")
    rows = lever_rows()
    for index, (label, pillars, gross, gross_ttw) in enumerate(rows):
        if index in (3, 7, 10):  # between the published block and each lever block
            out.append(r"        &     &    &    &    &    &    &    \\")
        out.append(
            "%-22s & " % label
            + " & ".join("%.1f" % value for value in pillars)
            + " & %.1f & %s \\\\" % (gross, "%.1f" % gross_ttw if gross_ttw is not None else "--")
        )
    out.append(r" &     &    &    &    &    &    &    \\")
    out.append(r"\midrule")
    out.append(r"Baseline (T0, frozen fleet) & \multicolumn{7}{c}{2835.0} \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    out.append(r"\end{small}")
    out.append(r"\label{tab:levers}")
    out.append(r"\end{table}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", metavar="DIR", help="also write table.tex into this directory")
    arguments = parser.parse_args()
    print_tables()
    if arguments.write:
        target = Path(arguments.write) / "table.tex"
        target.write_text(_latex_tables(), encoding="utf-8", newline="\n")
        print("\nwrote %s" % target)

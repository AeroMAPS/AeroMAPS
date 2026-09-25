"""
make_tables
===========
Emit the manuscript's two LaTeX tables from the committed outputs, so the numbers
in the paper cannot drift from the numbers in the figures.

Table 1 is the external validation: the reproduced trajectories against the
report's own published curves, as a relative error at 2030, 2040 and 2050 and
over the cumulative period. The technology scenarios T0-T4 are compared against
the hand-digitised curves, and S0-S2 against the curves traced by
report_data/digitise_scenarios.py. Both sides are gross, that is, before any
offsetting: `co2_emissions_including_energy` on ours, and the upper boundary of
the market-based band on theirs.

Table 2 is the same validation carried out lever by lever: what each pillar
abates in the reproduction against the thickness of the matching band in the
report's own scenario charts, traced per pixel by
report_data/digitise_scenarios.py. It is laid out like Table 1, at the same
reporting years and over the same cumulative span.

Printed beside the two tables, but not emitted as one, is the internal
decomposition the Discussion cites: what each mitigation pillar removes from the
frozen-fleet baseline in 2050, for the headline scenarios and for the individual
lever levels. Every one of those rows is read from a standalone run rather than
from the sweep grid, whose cells inherit S1's full configuration, load factor
included, so a lever level read from it carries S1's load-factor gain on top of
whatever the lever itself varies. make_lever_rows.py builds the levels that do
not already exist as a scenario or a technology run.

Run from this directory::

    python make_tables.py            # prints both tables
    python make_tables.py --write DIR  # also writes table.tex into DIR
"""

import argparse
from pathlib import Path

import numpy as np
import yaml

from aeromaps.utils.decomposition import pillar_totals
from aeromaps.utils.results_view import load_results
from aeromaps.utils.scenario_tables import latex_table, relative_errors

HERE = Path(__file__).parent

FIRST_YEAR = 2000
ERROR_YEARS = (2030, 2040, 2050)

# The published curves start partway through 2023, so the cumulative column runs
# over the span the digitisation actually covers rather than from 2019. Stating
# it as 2024-2050 keeps the comparison honest: the years before that are observed
# and identical on both sides, and including them would dilute the error.
CUMULATIVE_SPAN = (2024, 2050)


def series(view, name):
    """One vector output as a float array."""
    return np.asarray(view.data["vector_outputs"][name], dtype=float)


def at(values, year, first_year=FIRST_YEAR):
    return values[year - first_year]


# --------------------------------------------------------------------------- 1


def _errors(ours, years, values):
    """Relative error at each reporting year, then over the cumulative span."""
    return relative_errors(ours, years, values, ERROR_YEARS, CUMULATIVE_SPAN, FIRST_YEAR)


def validation_rows():
    """Reproduced tank-to-wake trajectories against the report's own curves.

    Both sides are gross. Ours is ``co2_emissions_including_energy``, which is
    emissions before any offsetting, and the traced curve is the top of the
    report's market-based band, which is the same quantity on its side. The
    dashed line in the report's charts is net of offsets and reaches zero in
    2050, so comparing against it would compare two different things.
    """
    report = yaml.safe_load(
        (HERE / "report_data" / "atag_3rd_edition_figures.yaml").read_text(encoding="utf-8")
    )

    rows = []
    for name in sorted(report["technology_scenarios"]):
        path = HERE / "3rd_edition_full" / "data_outputs" / f"{name.lower()}-TTW.json"
        if not path.exists():
            rows.append((name, None))
            continue
        curve = report["technology_scenarios"][name]
        ours = series(load_results(path), "co2_emissions_including_energy")
        rows.append((name, _band_pairs(ours, curve["years"], curve["values"], thin=0.0)))

    # The scenarios sit in a different edition folder from the technology runs,
    # and S0 only exists in the light edition.
    locations = {
        "S0": ("3rd_edition_light", "s0-TTW.json"),
        "S1": ("3rd_edition_full", "s1-TTW.json"),
        "S2": ("3rd_edition_full", "s2-TTW.json"),
    }
    for name in sorted(report.get("scenarios", {})):
        edition, filename = locations[name]
        path = HERE / edition / "data_outputs" / filename
        if not path.exists():
            rows.append((name, None))
            continue
        curve = report["scenarios"][name]
        ours = series(load_results(path), "co2_emissions_including_energy")
        rows.append((name, _band_pairs(ours, curve["years"], curve["mbm_top"], thin=0.0)))
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
    pillars, gross = pillar_totals(view, anchors=(t0, t1), year=year)
    # The market-based column repeats the gross residual: what the physical levers
    # leave is what those measures are assumed to remove, which is how the reports
    # draw it. It is dropped from the LaTeX table and kept in the console one.
    return pillars + [gross], gross


def lever_rows():
    """The headline scenarios, then one row per individual lever level.

    Every row is read from a standalone run rather than from the sweep grid.
    The sweep's cells inherit S1's full configuration -- load factor included --
    so its "T1" carried 5.8 points of load-factor gain that the standalone T1
    run does not, and its operations column read that drift rather than the
    operations lever. O1 and F0 coincide with T1 exactly (zero operations gain,
    no drop-in SAF), so only O2, O3, F1, F2 and F3 needed dedicated runs; see
    make_lever_rows.py for how those five were built.
    """
    full = HERE / "3rd_edition_full" / "data_outputs"
    light = HERE / "3rd_edition_light" / "data_outputs"
    t0, t1 = load_results(full / "t0.json"), load_results(full / "t1.json")

    rows = []
    for label, path, ttw_path in [
        ("S0 reference", light / "s0.json", light / "s0-TTW.json"),
        ("S1 SAF-focused", full / "s1.json", full / "s1-TTW.json"),
        ("S2 technology-centric", full / "s2.json", full / "s2-TTW.json"),
    ]:
        pillars, gross = decompose(load_results(path), t0, t1)
        gross_ttw = at(series(load_results(ttw_path), "co2_emissions_including_energy"), 2050)
        rows.append((label, pillars, gross, gross_ttw))

    for label, filename in [
        ("T0", "t0.json"),
        ("T1", "t1.json"),
        ("T2", "t2.json"),
        ("T3", "t3.json"),
        ("T4", "t4.json"),
        ("O1", "t1.json"),
        ("O2", "o2.json"),
        ("O3", "o3.json"),
        ("F0", "t1.json"),
        ("F1", "f1.json"),
        ("F2", "f2.json"),
        ("F3", "f3.json"),
    ]:
        pillars, gross = decompose(load_results(full / filename), t0, t1)
        rows.append((label, pillars, gross, None))
    return rows


# --------------------------------------------------------------------------- 2, validation

# The scenario outputs each lever row is read from: tank-to-wake, the report's own
# scope, since the traced bands are its tank-to-wake charts.
SCENARIO_TTW = {
    "S0": ("3rd_edition_light", "s0-TTW.json"),
    "S1": ("3rd_edition_full", "s1-TTW.json"),
    "S2": ("3rd_edition_full", "s2-TTW.json"),
}
SCENARIO_LABELS = {"S0": "S0 reference", "S1": "S1 SAF-focused", "S2": "S2 technology-centric"}


def our_lever_series(view, t0, t1):
    """Each pillar's annual abatement, as the decomposition figure stacks it.

    The wedge boundaries run frozen fleet, renewal only, the scenario's own
    technology, after alternative aircraft, after operations, gross, and net of
    offsets, so consecutive differences are the pillars. Alternative aircraft join
    next generation technology, as the reports count them.
    """
    from aeromaps.utils.decomposition import mitigation_wedges

    _, b = mitigation_wedges(view, anchors=(t0, t1))
    return {
        "fleet_renewal": b[0] - b[1],
        "next_generation": (b[1] - b[2]) + (b[2] - b[3]),
        "operations": b[3] - b[4],
        "saf": b[4] - b[5],
        "market_based": b[5] - b[6],
        "gross": b[5],
    }


# Below this, a band is under one pixel of the report's chart, so its thickness
# cannot be read off: the cell says so rather than quoting a number the tracing
# cannot support.
MIN_BAND_MT = 5.0

# The cumulative column is reported in Gt, the annual ones in Mt, since a lever
# integrated over twenty-seven years runs to thousands of Mt.
MT_PER_GT = 1000.0


def _band_pairs(ours, years, values, thin=MIN_BAND_MT):
    """``(reproduction, report)`` per reporting year, then over the cumulative span.

    Both sides are abatement in Mt, and the cumulative pair in Gt. The report's
    side is ``None`` where its band is thinner than a pixel of its own chart.
    """
    ours = np.asarray(ours, dtype=float)
    pairs = []
    for year in ERROR_YEARS:
        traced = float(np.interp(year, years, values))
        pairs.append((at(ours, year), traced if traced >= thin else None))

    span = np.arange(CUMULATIVE_SPAN[0], CUMULATIVE_SPAN[1] + 1)
    reproduced = float(sum(at(ours, year) for year in span)) / MT_PER_GT
    traced = float(np.interp(span, years, values).sum()) / MT_PER_GT
    pairs.append((reproduced, traced))
    return pairs


def lever_validation_rows():
    """Abatement per lever, reproduction against the report's own traced bands.

    Returns ``{scenario: [(lever label, pairs), ...]}``, one pair per reporting
    year and one for the cumulative span, each ``(reproduction, report)``.
    """
    report = yaml.safe_load(
        (HERE / "report_data" / "atag_3rd_edition_figures.yaml").read_text(encoding="utf-8")
    )["scenarios"]
    full = HERE / "3rd_edition_full" / "data_outputs"
    t0, t1 = load_results(full / "t0-TTW.json"), load_results(full / "t1-TTW.json")

    table = {}
    for name, (edition, filename) in SCENARIO_TTW.items():
        curve = report[name]
        bands, years = curve["bands"], curve["years"]
        ours = our_lever_series(load_results(HERE / edition / "data_outputs" / filename), t0, t1)
        hatched = any(value > 0 for value in bands["saf_hatched"])
        saf_total = [s + h for s, h in zip(bands["saf_solid"], bands["saf_hatched"])]

        rows = [
            ("Fleet renewal", _band_pairs(ours["fleet_renewal"], years, bands["fleet_renewal"])),
            (
                "Next gen. tech.",
                _band_pairs(ours["next_generation"], years, bands["next_generation"]),
            ),
            ("Operations, infra.", _band_pairs(ours["operations"], years, bands["operations"])),
        ]
        if hatched:
            rows.append(("SAF, solid band", _band_pairs(ours["saf"], years, bands["saf_solid"])))
            rows.append(("SAF + increment", _band_pairs(ours["saf"], years, saf_total)))
        else:
            rows.append(("SAF", _band_pairs(ours["saf"], years, saf_total)))
        rows.append(
            ("Market-based", _band_pairs(ours["market_based"], years, bands["market_based"]))
        )
        rows.append(("Gross residual", _band_pairs(ours["gross"], years, curve["mbm_top"])))
        table[name] = rows
    return table


# Errors are stated in Mt (Gt in the cumulative column) and, in brackets, as a
# share of the frozen-fleet (T0) emissions of the same year or span: an absolute
# figure says how much CO2 is at stake, and the share puts every row, thin band or
# thick, on one common base.
SPAN_YEARS = CUMULATIVE_SPAN[1] - CUMULATIVE_SPAN[0] + 1

# Cell shading by the error as a share of T0: one hue, light to dark, so the eye
# finds the large errors before reading a number. The share already puts every
# column, the cumulative one included, on one base, so one scale serves them all.
# Below the first bound the cell is left white; the darkest tint still carries
# black text.
ERROR_SHADES_PCT = (
    (1.0, None),
    (2.5, "FDE9D9"),
    (5.0, "F9C9A6"),
    (10.0, "F2A06E"),
    (float("inf"), "E4733F"),
)

_T0 = []


def t0_reference():
    """Frozen-fleet tank-to-wake emissions: each reporting year in Mt, then the span in Gt."""
    if not _T0:
        t0 = series(
            load_results(HERE / "3rd_edition_full" / "data_outputs" / "t0-TTW.json"),
            "co2_emissions_including_energy",
        )
        span = np.arange(CUMULATIVE_SPAN[0], CUMULATIVE_SPAN[1] + 1)
        _T0.extend([at(t0, year) for year in ERROR_YEARS])
        _T0.append(float(sum(at(t0, year) for year in span)) / MT_PER_GT)
    return _T0


def _shade(share):
    """The cell colour command for an error in % of T0, or nothing below 1 %."""
    for bound, colour in ERROR_SHADES_PCT:
        if abs(share) < bound:
            return r"\cellcolor[HTML]{%s}" % colour if colour else ""
    return ""


def _pair_cell(pair, column, latex=True):
    """Error in Mt (Gt in the cumulative column), with its share of T0 in brackets.

    Where the report's band is too thin to trace there is no error to report.
    """
    reproduced, reference = pair
    if reference is None:
        return "--"
    error = reproduced - reference
    share = 100.0 * error / t0_reference()[column]
    if abs(share) < 0.05:
        share = 0.0  # no "-0.0" for an error that rounds to nothing
    cumulative = column == len(ERROR_YEARS)
    value = ("%+.2f" if cumulative else "%+.1f") % error
    if not latex:
        return "%s (%+.1f%%)" % (value, share)
    return r"%s$%s$ ($%+.1f$~\%%)" % (_shade(share), value, share)


def _cells(pairs, latex=True):
    return [_pair_cell(pair, column, latex) for column, pair in enumerate(pairs)]


def hatched_errors(year=2050):
    """2050 error of S0 and S2 in Mt, against the gross curve and with the hatch as fuel."""
    report = yaml.safe_load(
        (HERE / "report_data" / "atag_3rd_edition_figures.yaml").read_text(encoding="utf-8")
    )["scenarios"]
    out = {}
    for name in ("S0", "S2"):
        edition, filename = SCENARIO_TTW[name]
        ours = at(
            series(
                load_results(HERE / edition / "data_outputs" / filename),
                "co2_emissions_including_energy",
            ),
            year,
        )
        curve = report[name]
        top = float(np.interp(year, curve["years"], curve["mbm_top"]))
        hatch = float(np.interp(year, curve["years"], curve["bands"]["saf_hatched"]))
        out[name] = (ours - top, ours - (top + hatch))
    return out


# --------------------------------------------------------------------------- output


def _fmt(value, width=7, places=1):
    return "n/a".rjust(width) if value is None else f"{value:{width}.{places}f}"


def print_tables():
    print(
        "Table 1 - reproduced tank-to-wake against the report's curves, error in Mt "
        "(Gt cumulative) and share of T0\n"
    )
    header = "  ".join(f"{year}" for year in ERROR_YEARS)
    print(f"  scenario   {header}   {CUMULATIVE_SPAN[0]}-{CUMULATIVE_SPAN[1]}")
    for name, errors in validation_rows():
        if errors is None:
            print(f"  {name:<9}  PENDING, no committed tank-to-wake output")
            continue
        print(f"  {name:<9}  " + "".join(f"{cell:>18}" for cell in _cells(errors, latex=False)))

    print("\n\nTable 2 - lever abatement, error in Mt (Gt cumulative) and share of T0\n")
    span = "%d-%d" % CUMULATIVE_SPAN
    print(f"  {'lever':<22}" + "".join(f"{year:>16}" for year in ERROR_YEARS) + f"{span:>16}")
    for name, rows in lever_validation_rows().items():
        print(f"  {SCENARIO_LABELS[name]}")
        for label, pairs in rows:
            cells = "".join(f"{cell:>18}" for cell in _cells(pairs, latex=False))
            print(f"    {label:<20}{cells}")

    print("\n\nStandalone lever runs, cited in the Discussion - 2050 pillars [MtCO2]\n")
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
    r"\textcolor{Highlight}{Validation against the report's curves.} "
    r"\textcolor{red}{Error of the reproduced annual CO$_2$ emissions against the third "
    r"edition, tank-to-wake, in Mt (Gt for the cumulative column), with in brackets the error "
    r"as a share of the frozen-fleet (T0) emissions of the same year. Positive values mean the "
    r"reproduction is higher. T0 to T4 are compared with hand-digitised curves, S0 to S2 with "
    r"curves traced from the report charts. T0 is the frozen fleet and T1 the fleet renewed "
    r"with existing aircraft; neither includes operations, fuels or market-based measures. Both "
    r"sides are gross emissions, before offsets. The report adds a hatched band above S0 and "
    r"S2, to be covered by carbon removals if SAF falls short. Counting it as SAF moves the 2050 "
    r"error from @S0A@ to @S0B@~Mt for S0, and from @S2A@ to @S2B@~Mt for S2. The cumulative "
    r"column starts in @START@, where the report curves begin. Shading marks errors of 1 to "
    r"2.5, 2.5 to 5, 5 to 10 and over 10~\% of T0, from light to dark.}"
).replace("@START@", str(CUMULATIVE_SPAN[0]))

TABLE2_CAPTION = (
    r"\textcolor{Highlight}{Validation of each lever.} "
    r"\textcolor{red}{Error of the abatement of each lever against the report's charts, "
    r"tank-to-wake, in Mt (Gt for the cumulative column), with in brackets the error as a share "
    r"of the frozen-fleet (T0) emissions of the same year. Positive values mean the reproduction "
    r"attributes more abatement to the lever. The report bands are traced from the report at "
    r"600~dpi and match its printed 2050 shares within 1.0 point. Bands thinner than one pixel, "
    r"about @MIN@~Mt, cannot be read and are marked with a dash. SAF is compared with and "
    r"without the hatched band. Two rows differ by construction: S0 fuel comes from stated "
    r"country policies, and market-based measures follow the offset path harmonised in the "
    r"Methods. Shading as in Table \ref{tab:validation}.}"
).replace("@MIN@", "%.0f" % MIN_BAND_MT)


def _table1_caption():
    """Table 1's caption, with the hatched-band errors computed rather than typed."""
    errors = hatched_errors()
    caption = TABLE1_CAPTION
    for name in ("S0", "S2"):
        caption = caption.replace("@%sA@" % name, "$%+.0f$" % errors[name][0])
        caption = caption.replace("@%sB@" % name, "$%+.0f$" % errors[name][1])
    return caption


def _latex_tables():
    """Both tables as one LaTeX fragment."""
    # Blank separator rows are passed through verbatim, so the emitter never
    # has to guess how many columns a spacer needs.
    blank = r"        &     &    &    &    \\"

    rows1 = [blank]
    for name, errors in validation_rows():
        # The two blocks are validated against differently sourced curves, so they
        # are separated rather than run together.
        if name == "S0":
            rows1.append(blank)
        if errors is None:
            rows1.append(r"%-6s & \multicolumn{4}{c}{pending} \\" % name)
            continue
        rows1.append(["%-6s" % name] + _cells(errors))

    table1 = latex_table(
        headers=["Scenario"]
        + ["%d [Mt]" % year for year in ERROR_YEARS]
        + ["%d--%d [Gt]" % CUMULATIVE_SPAN],
        rows=rows1,
        # m{} in the label column rather than p{}: p is top-aligned while M is
        # vertically centred, so a heading wrapping to two lines left "Scenario"
        # riding above the others in the header row.
        widths=["0.12", "0.18", "0.18", "0.18", "0.18"],
        caption=_table1_caption(),
        label="tab:validation",
    )

    # The frame of Table 1, one block per scenario: the same reporting years and
    # the same cumulative span, so that the two tables are read the same way.
    rows2 = []
    for name, rows in lever_validation_rows().items():
        rows2.append(blank)
        rows2.append(r"\multicolumn{5}{l}{\textbf{%s}} \\" % SCENARIO_LABELS[name])
        for label, pairs in rows:
            rows2.append(["%-22s" % label] + _cells(pairs))
    rows2.append(blank)

    table2 = latex_table(
        headers=["Lever"]
        + ["%d [Mt]" % year for year in ERROR_YEARS]
        + ["%d--%d [Gt]" % CUMULATIVE_SPAN],
        rows=rows2,
        # A wider first column than Table 1, the lever names being longer than the
        # scenario names they are grouped under, and wider value columns, each
        # carrying two numbers rather than one.
        widths=["0.19", "0.175", "0.175", "0.175", "0.175"],
        caption=TABLE2_CAPTION,
        label="tab:levers",
    )

    return table1 + "\n" + table2


# The document includes this rather than displaying it from a code cell, because
# a table displayed from a cell does not survive the typst export.
MARKDOWN_TABLE = HERE / "report_data" / "lever_validation.md"


def write_markdown(target=MARKDOWN_TABLE):
    """Table 2 as Markdown, for the document to include."""
    header = ["Scenario", "Lever"]
    header += ["%d [Mt]" % year for year in ERROR_YEARS] + ["%d--%d [Gt]" % CUMULATIVE_SPAN]
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for name, rows in lever_validation_rows().items():
        for index, (label, pairs) in enumerate(rows):
            scenario = SCENARIO_LABELS[name] if index == 0 else ""
            cells = _cells(pairs, latex=False)
            lines.append("| " + " | ".join([scenario, label] + cells) + " |")
    lines.append("")
    lines.append(
        "*Error of the abatement attributed to each lever against the report's own charts, "
        "tank-to-wake, in Mt (Gt for the cumulative column), with in brackets the error as a "
        "share of the frozen-fleet (T0) emissions of the same year. A band thinner than a "
        "pixel of the report's chart, about %d Mt, cannot be read off it, which a dash "
        "marks (%d Mt). The fuel lever is compared against the solid band alone and against that band "
        "plus the hatched increment the report assigns to carbon removals. S0's fuel row and "
        "every market-based row deviate by construction rather than by error, the first "
        "deriving its volumes from stated policies and the second carrying an offsetting "
        "trajectory harmonised across scenarios.*" % (MIN_BAND_MT, MIN_BAND_MT)
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", metavar="DIR", help="also write table.tex into this directory")
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="skip refreshing the Markdown copy the document includes",
    )
    arguments = parser.parse_args()
    print_tables()
    if not arguments.no_markdown:
        print("\nwrote %s" % write_markdown())
    if arguments.write:
        target = Path(arguments.write) / "table.tex"
        target.write_text(_latex_tables(), encoding="utf-8", newline="\n")
        print("wrote %s" % target)

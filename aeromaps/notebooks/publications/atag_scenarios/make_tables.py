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

Table 2 is the internal decomposition: what each mitigation pillar removes from
the frozen-fleet baseline in 2050. Every row, headline scenarios and individual
lever levels alike, is read from a standalone run rather than from the sweep
grid: the sweep's cells inherit S1's full configuration, load factor included,
so a lever level read from it carries S1's load-factor gain on top of whatever
the lever itself varies. make_lever_rows.py builds the levels that do not
already exist as a scenario or a technology run.

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
        rows.append((name, _errors(ours, curve["years"], curve["values"])))

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
        rows.append((name, _errors(ours, curve["years"], curve["mbm_top"])))
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
    r"third edition's own trajectories, in \%, in the tank-to-wake scope adopted by the report. A "
    r"positive value indicates an overestimate by the reproduction. The technology scenarios T0 to "
    r"T4 are compared against curves digitised by hand, whereas S0 to S2 are compared against "
    r"curves traced per pixel from the published charts. T0 is the notional frozen-fleet "
    r"trajectory and T1 corresponds to emissions with no improvement beyond ongoing fleet renewal, "
    r"neither of which includes reductions from operations, fuels or market-based measures. "
    r"Both sides of the comparison are gross, that is, before any offsetting: the reproduction "
    r"reports \texttt{co2\_emissions\_including\_energy}, and the traced curve is the upper "
    r"boundary of the market-based band, which represents the emissions remaining once every "
    r"physical lever has acted. The dashed line drawn on the same charts is net of offsets and "
    r"reaches zero in 2050, and is therefore not used. Regarding S0 and S2, a hatched band lies "
    r"above that boundary, labelled as an increment to be covered by carbon removals should "
    r"sustainable aviation fuel not deliver it. Taking the increment as delivered by fuel instead "
    r"moves the 2050 error from $+32.4$~\% to $+12.6$~\% for S0, and from $-27.3$~\% to "
    r"$-58.7$~\% for S2. The cumulative column starts in @START@ rather than in 2019 because the "
    r"published curves begin there, the preceding years being observed and therefore identical on "
    r"both sides.}"
).replace("@START@", str(CUMULATIVE_SPAN[0]))

TABLE2_CAPTION = (
    r"\textcolor{Highlight}{Reproduced 2050 lever contributions.} "
    r"\textcolor{red}{What each mitigation pillar removes from the frozen-fleet baseline in 2050, "
    r"in MtCO$_2$. The pillars follow the decomposition adopted by the reports, so that next "
    r"generation technology carries the battery-electric contribution rather than the fuel column, "
    r"and operations carries load factor. The first three rows correspond to the published "
    r"scenarios. The remaining rows correspond to standalone single-lever runs, each starting from "
    r"the technology-only T1 configuration (zero operations gain, no drop-in SAF) and varying "
    r"exactly one lever, so that T1, O1 and F0 designate the same run and appear three times by "
    r"construction; O2 and O3 vary the operations gain and load factor together, since the reports "
    r"bundle both into that pillar, and F1 to F3 vary the energy carrier file alone. Every "
    r"row closes on the common frozen-fleet baseline of 2835.0~Mt once the gross residual is "
    r"added to the four pillars, which verifies that the "
    r"decomposition constitutes a partition rather than an attribution; T0 is included as an "
    r"ordinary row and closes the same way, every one of its pillars being zero since it is "
    r"the baseline the other columns are measured against. The rows carrying no operations lever "
    r"report exactly zero for it because the load factor is held at its last observed value, "
    r"82.116~\% in 2023, rather than at the 82.4~\% the reports state: 82.4~\% is the pre-COVID "
    r"2019 value, so reaching it by 2050 is a small recovery rather than no change, and booking "
    r"that recovery as an operations gain would credit the pillar in rows built to exclude it. "
    r"The operations axis proper stays anchored on the reports' own published pair, O3 at "
    r"88.389~\% and O2 interpolated midway between it and 82.4~\%, the reports giving no "
    r"intermediate value. Two "
    r"cautions apply when reading across rows. First, market-based measures carry no column of "
    r"their own, since the reports define them as removing whatever gross residual the physical "
    r"levers leave: their contribution is the Gross WtW column read a second time, rather than an "
    r"independent lever. Second, the value of a given pillar depends on what else is deployed "
    r"alongside it, "
    r"which explains why next generation technology amounts to 529.1~Mt under T4 alone and to "
    r"500.2~Mt under S2, where sustainable aviation fuel competes for the same joules. Gross "
    r"residuals are reported in both accounting scopes for the published scenarios, the reports "
    r"headlining tank-to-wake emissions while this reproduction is run well-to-wake, so that the "
    r"difference between those two columns is attributable to the accounting scope alone.}"
)


def _latex_tables():
    """Both tables as one LaTeX fragment."""
    # Blank separator rows are passed through verbatim, so the widths of the two
    # tables can differ without the emitter having to guess how many columns a
    # spacer needs.
    blank1 = r"        &     &    &    &    \\"
    blank2 = r"        &     &    &    &    &    &    \\"

    rows1 = [blank1]
    for name, errors in validation_rows():
        # The two blocks are validated against differently sourced curves, so they
        # are separated rather than run together.
        if name == "S0":
            rows1.append(blank1)
        if errors is None:
            rows1.append(r"%-6s & \multicolumn{4}{c}{pending} \\" % name)
            continue
        rows1.append(["%-6s" % name] + ["$%+.1f$" % value for value in errors])

    table1 = latex_table(
        headers=["Scenario"] + [str(year) for year in ERROR_YEARS] + ["%d--%d" % CUMULATIVE_SPAN],
        rows=rows1,
        # m{} in the label column rather than p{}: p is top-aligned while M is
        # vertically centred, so a heading wrapping to two lines left "Scenario"
        # riding above the others in the header row.
        widths=["0.18", "0.12", "0.12", "0.12", "0.15"],
        caption=TABLE1_CAPTION,
        label="tab:validation",
    )

    # Seven columns, not eight: the market-based pillar is numerically identical
    # to Gross WtW in every row, being defined as the gross residual the measures
    # are assumed to remove, so printing it twice spent a column on a duplicate.
    #
    # Widths sum to 0.82	extwidth rather than the 0.88 the eight-column version
    # used. With 	abcolsep at 6pt each of the seven columns also carries 12pt of
    # padding, or 84pt over the row, and the text block is 7.2in (letterpaper less
    # the 0.65in margins), so anything above roughly 0.84 overflows. The old
    # layout did overflow; this one leaves a little room, and the width freed by
    # dropping the column goes to the two headings that wrap worst.
    rows2 = [blank2]
    # Blank separator before each block: the published scenarios, the five
    # technology runs T0-T4, the three operations runs O1-O3, and the four
    # fuel runs F0-F3.
    for index, (label, pillars, gross, gross_ttw) in enumerate(lever_rows()):
        if index in (3, 8, 11):
            rows2.append(blank2)
        rows2.append(
            ["%-22s" % label]
            # pillars[:-1] drops the market-based entry; it is kept in PILLARS and
            # in decompose() because the console table still shows it and the sum
            # check needs it to close on the frozen-fleet baseline.
            + ["%.1f" % value for value in pillars[:-1]]
            + ["%.1f" % gross, "%.1f" % gross_ttw if gross_ttw is not None else "--"]
        )
    rows2.append(r" &     &    &    &    &    &    \\")

    table2 = latex_table(
        headers=[
            "Scenario",
            "Fleet renewal",
            "Next gen. technology",
            "Operations, infra.",
            "SAF",
            "Gross WtW",
            "Gross TtW",
        ],
        rows=rows2,
        widths=["0.17", "0.10", "0.13", "0.12", "0.10", "0.10", "0.10"],
        caption=TABLE2_CAPTION,
        label="tab:levers",
    )

    return table1 + "\n" + table2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", metavar="DIR", help="also write table.tex into this directory")
    arguments = parser.parse_args()
    print_tables()
    if arguments.write:
        target = Path(arguments.write) / "table.tex"
        target.write_text(_latex_tables(), encoding="utf-8", newline="\n")
        print("\nwrote %s" % target)

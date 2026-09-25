"""
make_literature_tables
======================
Emit the comparison tables that set this work beside the literature it draws on,
one per assumption the paper varies: contrail forcing and its efficacy, the effect
of sustainable aviation fuel on contrails, contrail
avoidance, and the coupling of demand to price.

Each table is built from one file in ``literature/``, where every number is
recorded beside the source it was read from. Nothing is formatted by hand here and
nothing is converted by hand there, so a cell of a printed table can always be
traced to a page of a paper, and the harmonised columns can always be recomputed.

The forcing table is the one that needs computing rather than assembling. Its
sources do not publish the same quantity: some scale with distance and one with
fuel, some publish a radiative forcing and others an effective one, and the factor
between them is called an efficacy by some and a ratio by others. The table
therefore carries each study's own numbers, in its own units, and then two columns
that put every row on a single activity, AeroMAPS's own 2019 distance and fuel
burn, so that the rows can be read against each other at all.

Run from this directory::

    python make_literature_tables.py             # prints every table
    python make_literature_tables.py --write DIR # also writes literature_tables.tex

``make_tables.py`` emits the manuscript's own results tables; this module emits the
ones whose numbers come from elsewhere.
"""

import argparse
import json
import re
from pathlib import Path

import yaml

from aeromaps.utils.scenario_tables import latex_table

HERE = Path(__file__).parent
LITERATURE = HERE / "literature"
FIRST_YEAR = 2000

# Lee et al.'s ratio, used where a study publishes a radiative forcing and no
# factor of its own. Those cells are marked in the table rather than passed off
# as the study's own choice.
FALLBACK_ERF_RF = 0.42

# The generic tables, in the order the paper introduces them. The forcing table is
# not in this list: it is assembled by its own function.
GENERIC_TABLES = (
    "climate_assumptions",
    "saf_contrails",
    "contrail_avoidance",
    "demand_price",
)


def read(name):
    return yaml.safe_load((LITERATURE / f"{name}.yaml").read_text(encoding="utf-8"))


# --------------------------------------------------------------- common activity


def common_activity(document):
    """AeroMAPS's own distance and fuel burn in the table's reference year."""
    settings = document["common_activity"]
    outputs = json.loads((HERE / settings["results"]).read_text(encoding="utf-8"))
    vectors = outputs["vector_outputs"]
    index = settings["year"] - FIRST_YEAR

    distance = sum(
        vectors[f"total_aircraft_distance_{carrier}"][index]
        for carrier in ("dropin_fuel", "hydrogen", "electric")
    )
    fuel = {
        year: vectors["energy_consumption"][year - FIRST_YEAR] / settings["kerosene_lhv_mj_per_kg"]
        for year in range(FIRST_YEAR, FIRST_YEAR + len(vectors["energy_consumption"]))
    }
    return settings["year"], distance, fuel


# ------------------------------------------------------------- 1, contrail forcing


def _per_km(study):
    """RF and ERF per flight kilometre, in mW m-2 km-1, with the RF's provenance.

    The third value is True where the radiative forcing per kilometre is not
    published as such but implied, by dividing an effective forcing by the study's
    own ratio. A study that scales with fuel has no per-kilometre value at all;
    one is read off the common activity in :func:`forcing_rows`, so that the column
    can be compared across rows.
    """
    rf, implied = study.get("rf_per_km"), False
    if rf is None and study.get("rf_total") and study.get("own_distance_km"):
        rf = study["rf_total"] / study["own_distance_km"]
    if rf is None and study.get("erf_per_km") and study.get("erf_rf"):
        rf, implied = study["erf_per_km"] / study["erf_rf"], True

    erf = study.get("erf_per_km")
    if erf is None and rf is not None and study.get("erf_rf"):
        erf = rf * study["erf_rf"]
    return rf, erf, implied


def _range_per_km(study, rf):
    """The RF band per kilometre, scaled from whichever band the study gives."""
    if study.get("rf_per_km_range"):
        return study["rf_per_km_range"]
    if study.get("rf_total_range") and study.get("own_distance_km"):
        return [value / study["own_distance_km"] for value in study["rf_total_range"]]
    if study.get("rf_total_range") and study.get("rf_total") and rf:
        # A per-kilometre value with a band given on the total: carry the relative
        # band across, which is what a study reporting +-70 % means by it.
        return [rf * value / study["rf_total"] for value in study["rf_total_range"]]
    return None


def harmonised(study, year, distance, fuel):
    """2019 RF and ERF on one common activity, whatever the study scales with.

    A distance-scaled study is applied to AeroMAPS's own distance. A fuel-scaled
    one carries its own base year's global total, moved to the reference year by
    the ratio of the two years' fuel burn, which is the rule Wang et al. apply.
    """
    rf_per_km, erf_per_km, _ = _per_km(study)
    if study["scaling"] == "fuel":
        rf = study["rf_total"] * fuel[year] / fuel[study["rf_total_year"]]
    else:
        rf = rf_per_km * distance if rf_per_km else None

    ratio = study.get("erf_rf") or FALLBACK_ERF_RF
    if study["scaling"] == "fuel":
        erf = rf * ratio
    elif erf_per_km:
        erf = erf_per_km * distance
    else:
        erf = rf * ratio if rf else None
    return rf, erf


def _band(central, bounds, scale=1.0, places=2):
    """``central (low, high)`` in one cell, or the central value alone."""
    if central is None:
        return "--"
    text = f"{central * scale:.{places}f}"
    if bounds:
        low, high = (value * scale for value in bounds)
        text += f" ({low:.{places}f}, {high:.{places}f})"
    return text


def forcing_rows():
    """One row per study, its own numbers then the harmonised pair."""
    document = read("contrail_forcing")
    year, distance, fuel = common_activity(document)

    rows = []
    for study in document["studies"]:
        rf_per_km, _, implied = _per_km(study)
        rf, erf = harmonised(study, year, distance, fuel)
        if rf_per_km is None and rf is not None:
            # Fuel-scaled: no per-kilometre value exists, so quote the one its own
            # rule implies on the common activity rather than leaving the cell out.
            rf_per_km, implied = rf / distance, True
        rows.append(
            {
                "label": study["label"],
                "approach": study["approach"].strip(),
                "scaling": study["scaling"],
                "rf_per_km": _band(rf_per_km, _range_per_km(study, rf_per_km), scale=1e9)
                + (r"$^{\dagger}$" if implied else ""),
                "erf_rf": _band(study.get("erf_rf"), study.get("erf_rf_range"), places=2),
                "efficacy": "--" if study.get("efficacy") is None else f"{study['efficacy']:.1f}",
                "rf": "--" if rf is None else f"{rf:.1f}",
                "erf": "--" if erf is None else f"{erf:.1f}",
                "estimated_ratio": study.get("erf_rf") is None,
            }
        )
    return year, distance, fuel, rows


FORCING_CAPTION = (
    r"\textcolor{Highlight}{Contrail forcing in the literature.} "
    r"\textcolor{red}{Each estimate in its own terms, then on one common activity. Studies differ "
    r"in what the forcing scales with (given in the approach), and in whether they report a "
    r"radiative (RF) or effective (ERF) forcing. RF per km is in pW~m$^{-2}$~km$^{-1}$, with the "
    r"reported interval; a dagger marks a value derived from an ERF or from the study's rule. The "
    r"last column applies each study's rule to this model's @YEAR@ activity (@DIST@~billion~km, "
    r"@FUEL@~Mt of fuel), in mW~m$^{-2}$; where a study gives no ratio, Lee et al.'s "
    r"@FALLBACK@ is used.}"
)


def forcing_caption(year, distance, fuel):
    """The forcing table's caption, carrying the activity it was harmonised on."""
    return (
        FORCING_CAPTION.replace("@YEAR@", str(year))
        .replace("@DIST@", "%.1f" % (distance / 1e9))
        .replace("@FUEL@", "%.0f" % (fuel[year] / 1e9))
        .replace("@FALLBACK@", "%.2f" % FALLBACK_ERF_RF)
    )


SCALING_PHRASE = {"distance": "per flight km", "fuel": "with fuel burn"}


def forcing_headers(year):
    return [
        "Study",
        "Approach",
        "RF per km",
        "Efficacy (ERF/RF)",
        "%d RF / ERF" % year,
    ]


def forcing_body(rows):
    """Five columns: the scaling joins the approach and the two forcings share a cell."""
    return [
        [
            row["label"],
            "%s, %s" % (row["approach"], SCALING_PHRASE[row["scaling"]]),
            row["rf_per_km"],
            row["erf_rf"],
            "%s / %s" % (row["rf"], row["erf"]),
        ]
        for row in rows
    ]


def forcing_table():
    year, distance, fuel, rows = forcing_rows()
    return latex_table(
        headers=forcing_headers(year),
        rows=forcing_body(rows),
        widths=["0.15", "0.26", "0.16", "0.14", "0.13"],
        caption=forcing_caption(year, distance, fuel),
        label="tab:contrail_forcing",
    )


# ------------------------------------------------------------- 2, generic tables


def generic_table(name):
    """A table whose cells are written out in its own file."""
    document = read(name)
    # A row of the wrong length is a LaTeX error several pages later, and the
    # usual cause is an unquoted comma inside a flow-style cell, so check here.
    for row in document["rows"]:
        if len(row["cells"]) != len(document["columns"]):
            raise ValueError(
                "%s: row %r has %d cells against %d columns"
                % (name, row["cells"][0], len(row["cells"]), len(document["columns"]))
            )
    caption = r"\textcolor{Highlight}{%s} \textcolor{red}{%s}" % (
        document["caption_head"].strip(),
        " ".join(document["caption_body"].split()),
    )
    return latex_table(
        headers=[column["header"] for column in document["columns"]],
        rows=[[cell.strip() for cell in row["cells"]] for row in document["rows"]],
        widths=[column["width"] for column in document["columns"]],
        caption=caption,
        label=document["label"],
    )


# ----------------------------------------------------------------------- markdown

# LaTeX that has to survive as text when the same table is rendered in the
# documentation. Only the constructs these tables actually use are handled; a new
# one shows up as a stray backslash rather than being silently dropped.
_PLAIN = (
    (r"\%", "%"),
    (r"\$", "$"),
    (r"\&", "&"),
    (r"\_", "_"),
    (r"\"a", "ä"),
    (r"\"o", "ö"),
    (r"\"u", "ü"),
    (r"\`e", "è"),
    (r"'e", "é"),
    (r"$^{\dagger}$", "†"),
    (r"\times", "×"),
    (r"_2$e", "₂e"),
    (r"_2$", "₂"),
    (r"~", " "),
)

SUPERSCRIPTS = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def _plain(text):
    """A LaTeX cell as plain text, for the Markdown rendering."""
    for latex, plain in _PLAIN:
        text = text.replace(latex, plain)
    text = re.sub(r"\^\{([-\d]+)\}", lambda m: m.group(1).translate(SUPERSCRIPTS), text)
    text = re.sub(r"\\ref\{tab:([a-z_]+)\}", lambda m: m.group(1).replace("_", " "), text)
    text = re.sub(r"\\textcolor\{[^}]*\}\{", "", text).replace("}", "")
    # Whatever math is left is plain arithmetic, so the delimiters can go.
    text = text.replace("$", "").replace("|", r"\|")
    return " ".join(text.split())


def markdown_table(name):
    """One table as Markdown, with its caption below it in italics."""
    if name == "contrail_forcing":
        year, distance, fuel, rows = forcing_rows()
        headers = forcing_headers(year)
        body = forcing_body(rows)
        caption = forcing_caption(year, distance, fuel)
    else:
        document = read(name)
        headers = [column["header"] for column in document["columns"]]
        body = [row["cells"] for row in document["rows"]]
        caption = r"\textcolor{Highlight}{%s} \textcolor{red}{%s}" % (
            document["caption_head"].strip(),
            " ".join(document["caption_body"].split()),
        )

    lines = [
        "| " + " | ".join(_plain(header) for header in headers) + " |",
        "|" + "---|" * len(headers),
    ]
    lines += ["| " + " | ".join(_plain(cell) for cell in row) + " |" for row in body]
    return "\n".join(lines) + "\n\n*" + _plain(caption) + "*\n"


# ------------------------------------------------------------------------ output


def print_tables():
    year, distance, fuel, rows = forcing_rows()
    print(
        "Contrail forcing [RF per km in pW/m2/km; %d forcings in mW/m2 on %.2fe10 km, %.0f Mt]\n"
        % (year, distance / 1e10, fuel[year] / 1e9)
    )
    print(
        "  %-26s %-9s %-22s %-18s %-8s %7s %7s"
        % ("study", "scales", "RF per km", "ERF/RF", "efficacy", "RF", "ERF")
    )
    for row in rows:
        print(
            "  %-26s %-9s %-22s %-18s %-8s %7s %7s"
            % (
                row["label"],
                row["scaling"],
                row["rf_per_km"].replace(r"$^{\dagger}$", " implied"),
                row["erf_rf"] + (" (assumed)" if row["estimated_ratio"] else ""),
                row["efficacy"],
                row["rf"],
                row["erf"],
            )
        )

    for name in GENERIC_TABLES:
        document = read(name)
        print("\n\n%s\n" % document["caption_head"].strip())
        for row in document["rows"]:
            cells = [" ".join(cell.split()) for cell in row["cells"]]
            print("  %s" % cells[0])
            for header, cell in zip(document["columns"][1:], cells[1:]):
                print("      %-20s %s" % (header["header"] + ":", cell))


def _latex_tables():
    tables = [forcing_table()] + [generic_table(name) for name in GENERIC_TABLES]
    return "\n".join(tables)


# Where the Markdown copies live. The document includes these rather than
# displaying the tables from a code cell, because a table displayed from a cell
# does not survive the typst export.
MARKDOWN_DIR = LITERATURE / "tables"


def write_markdown(directory=MARKDOWN_DIR):
    """One Markdown file per table, for the document to include."""
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for name in ("contrail_forcing",) + GENERIC_TABLES:
        target = directory / ("%s.md" % name)
        target.write_text(markdown_table(name), encoding="utf-8", newline="\n")
        written.append(target)
    return written


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write", metavar="DIR", help="also write literature_tables.tex into this directory"
    )
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="skip refreshing the Markdown copies the document includes",
    )
    arguments = parser.parse_args()
    print_tables()
    if not arguments.no_markdown:
        written = write_markdown()
        print("\nwrote %d Markdown tables into %s" % (len(written), MARKDOWN_DIR))
    if arguments.write:
        target = Path(arguments.write) / "literature_tables.tex"
        target.write_text(_latex_tables(), encoding="utf-8", newline="\n")
        print("wrote %s" % target)

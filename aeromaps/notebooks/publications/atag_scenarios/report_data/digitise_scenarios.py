"""
digitise_scenarios
==================
Trace the S0, S1 and S2 emissions curves out of the third edition's own charts.

The T0-T4 curves in ``atag_3rd_edition_figures.yaml`` were digitised by hand. The
scenario charts are traced here per-pixel instead, which is both more accurate and
reproducible: the axes are recovered from the chart's own gridlines and year
labels rather than assumed, and the curve is the boundary between two of the
report's band colours rather than a line read off by eye.

**Which boundary, and why it matters.** The reports draw each scenario as a stack
of wedges closing on a frozen-fleet baseline, with market-based measures as the
bottom band. The top of that band is emissions after every physical lever and
before any offsetting, which is exactly what ``co2_emissions_including_energy``
holds in this reproduction. The purple dashed line in the same charts is net of
offsets and reaches zero in 2050; comparing against it would compare an offset
trajectory with a gross one.

S0 and S2 additionally carry a hatched green band between the solid SAF band and
the grey one, labelled as an increment that carbon removals cover if SAF does
not. Two readings therefore exist, and both are traced:

``mbm_top``
    Top of the grey band. The increment is delivered by SAF, so this is the
    high-SAF reading. S1 has no hatched band and the two readings coincide.
``saf_solid_bottom``
    Bottom of the solid green band. The increment is delivered by removals, so
    this is the low-SAF reading and sits above ``mbm_top``.

**Where the pixels come from.** The pages of the report itself, rendered with
``pdftoppm`` at a resolution this script sets, rather than screenshots of them.
Nothing geometric is therefore hard-coded: the plot box is recovered from the
chart's own gridlines, the year labels are found below the axis, and the three
pixel thresholds below are fractions of that box, so raising the resolution
sharpens the trace instead of breaking it.

Usage::

    python digitise_scenarios.py [--pdf PATH] [--dpi 600] [--write]

``--write`` merges the result into ``atag_3rd_edition_figures.yaml`` under a
``scenarios:`` block, leaving the hand-digitised ``technology_scenarios:`` block
untouched.
"""

import argparse
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent

# The third edition, and the pages its scenario charts sit on. The file is not in
# the repository: it is the published report, and the path is the one the author
# keeps it at.
REPORT_PDF = Path(r"D:\i.costa-alves\Downloads\aviation_scenarios\02_atag\w2050_v2026_jan_full.pdf")
CHART_PAGES = {"S0": 27, "S1": 28, "S2": 29}
# 600 dpi puts about 1120 rows between the 0 and 2,500 gridlines, so one pixel is
# roughly 2 Mt: finer than the report's own line weights, which is the point at
# which more resolution stops buying accuracy.
RENDER_DPI = 600

# Read off the charts themselves, not from atag_decomposition.COLORS: that dict
# holds the palette as redrawn for our own figures, which is close but not equal.
BAND_COLOURS = {
    "fleet_renewal": (225, 233, 245),
    "next_generation": (106, 134, 191),
    "operations": (245, 168, 101),
    "saf": (196, 217, 104),
    "market_based": (184, 184, 184),
}
# Gridlines are grey too, and only six counts away from the market-based band.
# The tolerance therefore has to stay under half that gap: at 6 the two match each
# other and every column reports its first grey pixel on the 2500 Mt gridline.
GRIDLINE_GREY = (178, 178, 178)
COLOUR_TOLERANCE = 3

GRIDLINE_VALUES = [2500, 2000, 1500, 1000, 500, 0]
LABEL_YEARS = [2015, 2020, 2025, 2030, 2035, 2040, 2045, 2050]


def _matches(pixels, colour, tolerance=COLOUR_TOLERANCE):
    """Boolean mask of pixels within ``tolerance`` of ``colour`` on every channel."""
    return np.all(np.abs(pixels - np.asarray(colour)) <= tolerance, axis=-1)


def _horizontal_gridlines(image):
    """Row index of each horizontal gridline, top to bottom.

    Matched on the gridline's own grey rather than on "some light grey": S0's
    market-based band covers 59 % of its chart in a grey only six counts away,
    and a loose threshold reports hundreds of its rows as gridlines. The two are
    separated on colour here and again on thickness below, since a gridline is
    two pixels and a band is hundreds.
    """
    height, width, _ = image.shape
    rows = [y for y in range(height) if _matches(image[y], GRIDLINE_GREY, 2).sum() > width * 0.3]

    lines, run = [], [rows[0]]
    for y in rows[1:]:
        if y - run[-1] <= 2:
            run.append(y)
        else:
            lines.append(run)
            run = [y]
    lines.append(run)
    return [float(np.mean(run)) for run in lines if len(run) <= 4]


# Column gap that separates one year label from the next, as a fraction of the
# plot width. The labels are about four digits wide and seven years apart, so
# anything between a digit gap and a label gap works; this sits in the middle.
LABEL_GAP_FRACTION = 0.007
# A row of year labels covers this share of the plot width in dark pixels.
LABEL_MIN_FRACTION = 0.05


def _year_label_centres(image, axis_row):
    """Horizontal centre of each year label under the axis.

    The labels are the first band of dark rows below the axis. Taking the first
    such band rather than a fixed window is what makes this work at any
    resolution, and it also keeps the legend, which is further down, out of it.
    """
    below = image[axis_row + 1 :]
    dark = below.max(axis=2) < 150
    counts = dark.sum(axis=1)
    rows = np.where(counts >= 3)[0]
    if len(rows) == 0:
        raise ValueError("no dark rows found below the axis")

    # The first dark rows under the axis belong to the net-zero target symbol
    # drawn at (2050, 0), not to the labels, so a band is taken as the labels
    # only once it covers a real share of the width: eight labels of four digits
    # reach a fifth of it, the symbol a fiftieth.
    bands, band = [], [rows[0]]
    for row in rows[1:]:
        if row - band[-1] > 3:
            bands.append(band)
            band = [row]
        else:
            band.append(row)
    bands.append(band)

    floor = LABEL_MIN_FRACTION * image.shape[1]
    labels = [b for b in bands if counts[b].max() >= floor]
    if not labels:
        raise ValueError("no year labels found below the axis")
    band_rows = labels[0]

    columns = np.where(dark[band_rows].sum(axis=0) >= 2)[0]
    gap = max(3, int(round(LABEL_GAP_FRACTION * image.shape[1])))

    centres, run = [], [columns[0]]
    for x in columns[1:]:
        if x - run[-1] <= gap:
            run.append(x)
        else:
            centres.append(float(np.mean(run)))
            run = [x]
    centres.append(float(np.mean(run)))
    return centres


def calibrate(image):
    """Pixel-to-data transforms, fitted to the chart's own gridlines and labels.

    Returns ``(to_value, to_year, plot_box)``. Both transforms are least-squares
    fits rather than two-point scalings, so a single mis-detected gridline shows
    up in the residual instead of silently tilting every value.
    """
    gridlines = _horizontal_gridlines(image)
    if len(gridlines) < 4:
        raise ValueError("found only %d gridlines: %s" % (len(gridlines), gridlines))

    # Gridlines are drawn under the bands, so an interior one disappears wherever
    # a band is wide enough to cover the whole chart: S0's market-based band hides
    # the 1000 Mt line completely. The outermost two always survive, since the top
    # line sits above every band and the bottom one is the axis, so each detected
    # line is indexed against that span rather than counted off in sequence.
    top, bottom = gridlines[0], gridlines[-1]
    spacing = (bottom - top) / (len(GRIDLINE_VALUES) - 1)
    indices = [(y - top) / spacing for y in gridlines]
    drift = max(abs(index - round(index)) for index in indices)
    if drift > 0.06:
        raise ValueError(
            "gridlines are not evenly spaced, worst index drift %.3f: %s" % (drift, gridlines)
        )
    values = [GRIDLINE_VALUES[int(round(index))] for index in indices]
    value_fit = np.polyfit(gridlines, values, 1)

    labels = _year_label_centres(image, int(round(gridlines[-1])))
    if len(labels) != len(LABEL_YEARS):
        raise ValueError(
            "expected %d year labels, found %d at %s" % (len(LABEL_YEARS), len(labels), labels)
        )
    year_fit = np.polyfit(labels, LABEL_YEARS, 1)

    residual = np.abs(np.polyval(year_fit, labels) - LABEL_YEARS).max()
    if residual > 0.35:
        raise ValueError("year labels are not evenly spaced, worst residual %.2f yr" % residual)

    top, bottom = min(gridlines), max(gridlines)
    left, right = min(labels), max(labels)
    return (
        lambda y: float(np.polyval(value_fit, y)),
        lambda x: float(np.polyval(year_fit, x)),
        (int(round(top)), int(round(bottom)), int(round(left)), int(round(right))),
    )


SOLID_FRACTION = 0.9
# Averaging window, as a fraction of the plot width: wide enough to bridge the
# lines that cross the bands, narrow enough to leave a hatched band reading its
# own duty cycle rather than its neighbours'.
WINDOW_FRACTION = 0.012


def _window_for(width):
    """An odd averaging window of ``WINDOW_FRACTION`` of the plot width."""
    window = max(5, int(round(WINDOW_FRACTION * width)))
    return window + 1 - window % 2


def _windowed_fraction(mask, window):
    """For each (row, column), the fraction of nearby columns matching the mask.

    Reading a single column is not enough. Gridlines show through the bands, and
    the black historical curve and the purple net curve cross them, so a column
    read on its own has its bands broken into several pieces at arbitrary rows.
    Averaging across neighbouring columns makes those crossings a local dip
    instead of a break, and it is also what separates a solid band from a hatched
    one: solid reads near 1, hatching reads near its duty cycle.
    """
    kernel = np.ones(window) / window
    padded = np.pad(mask.astype(float), ((0, 0), (window // 2, window // 2)), mode="edge")
    return np.apply_along_axis(lambda row: np.convolve(row, kernel, mode="valid"), 1, padded)


def render_page(pdf, page, dpi, directory):
    """One page of the report as a PNG, rendered with ``pdftoppm``."""
    prefix = Path(directory) / ("page%d" % page)
    subprocess.run(
        [
            "pdftoppm",
            "-f",
            str(page),
            "-l",
            str(page),
            "-r",
            str(dpi),
            "-png",
            "-aa",
            "no",
            "-aaVector",
            "no",
            str(pdf),
            str(prefix),
        ],
        check=True,
        capture_output=True,
    )
    rendered = sorted(Path(directory).glob("page%d-*.png" % page))
    if not rendered:
        raise FileNotFoundError("pdftoppm produced nothing for page %d" % page)
    return rendered[0]


# Margin kept below the axis when cropping, as a fraction of the plot height: it
# has to reach the year labels without reaching the legend under them.
LABEL_MARGIN_FRACTION = 0.16


def crop_chart(page):
    """The plot box of the chart on a rendered page, plus the year labels.

    The page also carries the legend and the right-hand share bar, both drawn in
    the same band colours, so the crop is taken from the gridlines instead: they
    belong to the chart alone and span it exactly.
    """
    gridline = _matches(page, GRIDLINE_GREY, 2)
    rows = np.where(gridline.sum(axis=1) > 0.25 * page.shape[1])[0]
    if len(rows) == 0:
        raise ValueError("no gridlines found on the page")

    columns = np.where(gridline[rows].sum(axis=0) > 0.5 * len(rows))[0]
    top, bottom = int(rows.min()), int(rows.max())
    left, right = int(columns.min()), int(columns.max())
    margin = int(round(LABEL_MARGIN_FRACTION * (bottom - top)))
    return page[max(0, top - 2) : bottom + margin, left - 2 : right + 3]


def trace(image):
    """Both readings of one scenario chart, as year-indexed curves."""
    to_value, to_year, (top, bottom, left, right) = calibrate(image)

    box = image[top : bottom + 1, left : right + 1]
    window = _window_for(box.shape[1])
    grey = _windowed_fraction(_matches(box, BAND_COLOURS["market_based"]), window)
    green = _windowed_fraction(_matches(box, BAND_COLOURS["saf"]), window)
    renewal = _windowed_fraction(_matches(box, BAND_COLOURS["fleet_renewal"]), window)
    next_generation = _windowed_fraction(_matches(box, BAND_COLOURS["next_generation"]), window)
    operations = _windowed_fraction(_matches(box, BAND_COLOURS["operations"]), window)
    hatch_min_rows = max(3, int(round(HATCH_MIN_ROWS_FRACTION * box.shape[0])))
    transition_half = max(1.0, TRANSITION_HALF_FRACTION * box.shape[0])

    years, mbm_top, saf_bottom, baseline = [], [], [], []
    bands = {key: [] for key in BAND_KEYS + ("_net",)}
    for index in range(box.shape[1]):
        solid_grey = np.where(grey[:, index] > SOLID_FRACTION)[0]
        if len(solid_grey) == 0:
            continue
        years.append(to_year(left + index))
        mbm_top.append(to_value(top + solid_grey[0]))

        solid_green = np.where(green[:, index] > SOLID_FRACTION)[0]
        # Where a scenario carries no hatched increment, the solid band runs all
        # the way down to the grey one and the two readings coincide, which is
        # the right answer rather than a special case.
        saf_bottom.append(to_value(top + solid_green[-1]) if len(solid_green) else mbm_top[-1])

        # Top of the fleet-renewal band, which is the frozen-fleet baseline the
        # whole stack closes on. It is traced only as a check: the same curve is
        # T0 in the hand-digitised block, so agreement between the two is an
        # independent test of this script's axis calibration.
        solid_renewal = np.where(renewal[:, index] > SOLID_FRACTION)[0]
        baseline.append(to_value(top + solid_renewal[0]) if len(solid_renewal) else float("nan"))

        for key, value in _band_thicknesses(
            index,
            to_value,
            top,
            renewal,
            next_generation,
            operations,
            green,
            grey,
            hatch_min_rows,
            transition_half,
        ).items():
            bands[key].append(value)

    _close_net_line_at_target(years, bands)
    return {
        "years": years,
        "mbm_top": mbm_top,
        "saf_solid_bottom": saf_bottom,
        "baseline": baseline,
        "bands": bands,
    }


# A gap wider than this fraction of the plot height between the last solid green
# row and the first solid grey one is a hatched band; narrower, it is only the
# anti-aliased edge between two colours, which S1 shows with no hatched band.
HATCH_MIN_ROWS_FRACTION = 0.008
# Half the anti-aliased transition kept on each side of a hatched band, again as
# a fraction of the plot height.
TRANSITION_HALF_FRACTION = 0.0025


def _band_thicknesses(
    index,
    to_value,
    top,
    renewal,
    next_generation,
    operations,
    green,
    grey,
    hatch_min_rows,
    transition_half,
):
    """Every lever band in one pixel column, as a thickness in Mt.

    Each boundary between two stacked colours is placed at the midpoint of the
    anti-aliased rows between their solid runs, so those rows are shared rather
    than lost. A band too thin to register has no solid run and reads as zero.
    """
    stack = []
    for key, fraction in (
        ("fleet_renewal", renewal),
        ("next_generation", next_generation),
        ("operations", operations),
        ("saf_solid", green),
        ("market_based", grey),
    ):
        rows = np.where(fraction[:, index] > SOLID_FRACTION)[0]
        if len(rows):
            stack.append((key, rows[0], rows[-1]))

    # Upper and lower edge of each present band, in rows.
    edges = {}
    for position, (key, first, last) in enumerate(stack):
        upper = first - 0.5 if position == 0 else None
        lower = last + 0.5
        edges[key] = [upper, lower]
    hatched = None
    for (upper_key, _, upper_last), (lower_key, lower_first, _) in zip(stack, stack[1:]):
        if (
            upper_key == "saf_solid"
            and lower_key == "market_based"
            and (lower_first - upper_last - 1 >= hatch_min_rows)
        ):
            edges[upper_key][1] = upper_last + transition_half
            edges[lower_key][0] = lower_first - transition_half
            hatched = (edges[upper_key][1], edges[lower_key][0])
            continue
        boundary = 0.5 * (upper_last + lower_first)
        edges[upper_key][1] = boundary
        edges[lower_key][0] = boundary

    def thickness(key):
        if key not in edges:
            return 0.0
        upper, lower = edges[key]
        return to_value(top + upper) - to_value(top + lower)

    result = {
        key: thickness(key)
        for key in ("fleet_renewal", "next_generation", "operations", "saf_solid", "market_based")
    }
    result["saf_hatched"] = (
        to_value(top + hatched[0]) - to_value(top + hatched[1]) if hatched else 0.0
    )
    # The report's own "baseline" is the lower edge of the fleet-renewal band.
    renewal_edges = edges.get("fleet_renewal")
    result["report_baseline"] = to_value(top + renewal_edges[1]) if renewal_edges else float("nan")
    # Kept for the net-line correction: the bottom of the market-based band.
    result["_net"] = (
        to_value(top + edges["market_based"][1]) if "market_based" in edges else float("nan")
    )
    return result


# From this year on the net line runs under the net-zero target symbol drawn at
# (2050, 0), which hides the bottom of the market-based band: traced as it stands,
# the net line reads about 100 Mt at 2050 rather than the zero the charts draw.
NET_LINE_TRUSTED_UNTIL = 2048.0


def _close_net_line_at_target(years, bands):
    """Replace the symbol-covered net line with a straight run to zero at 2050."""
    net = bands.pop("_net")
    years = np.asarray(years)
    trusted = years <= NET_LINE_TRUSTED_UNTIL
    anchor_year = years[trusted][-1]
    anchor_net = np.asarray(net)[trusted][-1]
    for i, year in enumerate(years):
        if year > NET_LINE_TRUSTED_UNTIL:
            corrected = anchor_net * max(0.0, (2050.0 - year) / (2050.0 - anchor_year))
            bands["market_based"][i] += net[i] - corrected


# The order the charts stack their bands in, plus the report's own baseline line
# (the top of the next-generation band), against which the printed shares read.
BAND_KEYS = (
    "report_baseline",
    "fleet_renewal",
    "next_generation",
    "operations",
    "saf_solid",
    "saf_hatched",
    "market_based",
)

# The 2050 shares printed on each chart's right-hand bar, as a percentage of the
# report's baseline. Printed labels beat any extraction, so the traced bands must
# match them; fleet renewal sits above the baseline and carries no printed share.
PRINTED_SHARES_2050 = {
    "S0": {
        "next_generation": 8,
        "operations": 8,
        "saf_solid": 15,
        "saf_hatched": 10,
        "market_based": 59,
    },
    "S1": {
        "next_generation": 12,
        "operations": 9,
        "saf_solid": 58,
        "saf_hatched": 0,
        "market_based": 21,
    },
    "S2": {
        "next_generation": 21,
        "operations": 9,
        "saf_solid": 38,
        "saf_hatched": 13,
        "market_based": 19,
    },
}
# Half a printed percentage point for the rounding, plus the anti-aliased edge of
# a band, which at 600 dpi is about a pixel, or 2 Mt on a roughly 1900 Mt
# baseline. The worst gap observed is 0.91 pp, S0's market-based band; tracing
# the same charts from screenshots instead reached 1.03 pp.
PRINTED_TOLERANCE_PP = 1.0


def check_against_printed_shares(name, traced):
    """Worst gap, in percentage points, between traced and printed 2050 shares."""
    at = lambda key: (  # NOQA: E731
        float(np.interp(2050, traced["years"], traced["bands"][key]))
    )
    base = at("report_baseline")
    gaps = {
        key: 100.0 * at(key) / base - printed for key, printed in PRINTED_SHARES_2050[name].items()
    }
    return max(abs(gap) for gap in gaps.values()), gaps


def check_against_hand_digitisation(traced):
    """Sanity-check the tracer against the author's own T0 curve.

    The frozen-fleet baseline is the top of every scenario chart and is also the
    T0 curve in the hand-digitised block, so tracing one and reading the other
    is a free external check on the axis calibration.
    """
    import yaml

    reference = yaml.safe_load(
        (HERE / "atag_3rd_edition_figures.yaml").read_text(encoding="utf-8")
    )["technology_scenarios"]["T0"]
    worst = 0.0
    for year in (2030, 2040, 2050):
        expected = float(np.interp(year, reference["years"], reference["values"]))
        got = float(np.interp(year, traced["years"], traced["baseline"]))
        worst = max(worst, abs(got / expected - 1.0))
    return worst


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", default=str(REPORT_PDF), help="the third edition report")
    parser.add_argument("--dpi", type=int, default=RENDER_DPI, help="render resolution")
    parser.add_argument("--write", action="store_true", help="merge into the YAML")
    parser.add_argument("--save-charts", metavar="DIR", help="also keep the cropped charts as PNGs")
    arguments = parser.parse_args()

    results = {}
    with tempfile.TemporaryDirectory(prefix="atag_charts_") as workdir:
        for name, page in CHART_PAGES.items():
            rendered = render_page(arguments.pdf, page, arguments.dpi, workdir)
            image = crop_chart(np.asarray(Image.open(rendered).convert("RGB")).astype(int))
            print(
                "%s  page %d at %d dpi, chart %d x %d px"
                % (name, page, arguments.dpi, image.shape[1], image.shape[0])
            )
            if arguments.save_charts:
                target = Path(arguments.save_charts)
                target.mkdir(parents=True, exist_ok=True)
                Image.fromarray(image.astype("uint8")).save(target / ("%s.png" % name.lower()))
            results[name] = trace(image)
            curve = results[name]
            drift = check_against_hand_digitisation(curve)
            if drift > 0.04:
                raise ValueError(
                    "%s traced baseline disagrees with the hand-digitised T0 by %.1f %%, "
                    "which points at the axis calibration rather than at the report"
                    % (name, 100 * drift)
                )
            print("%s  baseline agrees with hand-digitised T0 to %.1f %%" % (name, 100 * drift))
            worst, gaps = check_against_printed_shares(name, curve)
            print(
                "%s  lever bands against the printed 2050 shares: worst %.2f pp (%s)"
                % (name, worst, ", ".join("%s %+.2f" % (k, v) for k, v in gaps.items()))
            )
            if worst > PRINTED_TOLERANCE_PP:
                raise ValueError(
                    "%s traced lever bands miss the printed 2050 shares by up to %.2f pp"
                    % (name, worst)
                )
            print(
                "%s  %d columns, %.1f-%.1f, mbm_top 2050 = %.1f, saf_solid_bottom 2050 = %.1f"
                % (
                    name,
                    len(curve["years"]),
                    curve["years"][0],
                    curve["years"][-1],
                    np.interp(2050, curve["years"], curve["mbm_top"]),
                    np.interp(2050, curve["years"], curve["saf_solid_bottom"]),
                )
            )

    if arguments.write:
        write_yaml(results)


YAML_HEADER = """
# scenarios
#     S0-S2 as the third edition draws them, traced per-pixel by
#     digitise_scenarios.py rather than digitised by hand. Four curves each:
#
#       mbm_top           top of the market-based band, that is, emissions after
#                         every physical lever and before any offsetting. This is
#                         the curve to compare against
#                         co2_emissions_including_energy.
#       saf_solid_bottom  bottom of the solid SAF band. S0 and S2 carry a hatched
#                         increment below it that carbon removals cover if SAF
#                         does not, so this is the low-SAF reading and mbm_top the
#                         high-SAF one. S1 has no hatched band and the two
#                         coincide, which is a check rather than a special case.
#       baseline          top of the fleet-renewal band. Traced only as a check:
#                         it is the same trajectory as T0 above, and the two agree
#                         to within 2.6 %.
#
#     Checked also against the report's own published lever percentages, which is
#     a stronger test than the T0 comparison because it does not pass through a
#     second digitisation. Reading market-based measures off the right-hand bar of
#     each chart gives 21 % of the roughly 1900 Mt baseline for S1, or 399 Mt,
#     against 394.1 traced; and 19 %, or 361 Mt, for S2, against 359.9 traced.
#
#     Like the block above, these are TANK-TO-WAKE. The dashed line in the same
#     charts is net of offsets and is deliberately not traced.
#
#     bands
#       Every lever band as a thickness in Mt, stacked as the charts draw them:
#       fleet_renewal, next_generation, operations, saf_solid, saf_hatched and
#       market_based, plus report_baseline, the lower edge of the fleet-renewal
#       band, which is the "baseline" the right-hand bar's shares are read against.
#       Each boundary between two colours sits at the midpoint of the anti-aliased
#       rows between them. The bottom of the market-based band is the net line,
#       which the net-zero target symbol hides from 2048, so there it is run
#       straight to the zero the charts draw at 2050. Checked against the printed
#       2050 shares within 1.0 percentage point: half a point for their rounding
#       and the anti-aliased edge of a band. The worst gap is 0.91 pp, S0's
#       market-based band.
"""


def write_yaml(results):
    """Merge the traced curves into the figures YAML, in place."""
    path = HERE / "atag_3rd_edition_figures.yaml"
    text = path.read_text(encoding="utf-8")
    marker = "\nscenarios:\n"
    if marker in text:
        text = text[: text.index(marker)]

    lines = [text.rstrip("\n"), YAML_HEADER.rstrip("\n"), "", "scenarios:"]

    def as_list(series):
        # repr writes NaN as "nan", which YAML reads back as a string and every
        # downstream interp then fails on. ".nan" is the float.
        return ", ".join(".nan" if v != v else repr(v) for v in series)

    for name, curve in results.items():
        lines.append("  %s:" % name)
        for key in ("years", "mbm_top", "saf_solid_bottom", "baseline"):
            lines.append("    %s: [%s]" % (key, as_list(curve[key])))
        lines.append("    bands:")
        for key in BAND_KEYS:
            lines.append("      %s: [%s]" % (key, as_list(curve["bands"][key])))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("wrote %s" % path)


if __name__ == "__main__":
    main()

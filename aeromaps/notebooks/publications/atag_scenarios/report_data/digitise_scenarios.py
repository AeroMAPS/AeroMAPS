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

Usage::

    python digitise_scenarios.py --images DIR [--write]

``--write`` merges the result into ``atag_3rd_edition_figures.yaml`` under a
``scenarios:`` block, leaving the hand-digitised ``technology_scenarios:`` block
untouched.
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent

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


def _year_label_centres(image):
    """Horizontal centre of each year label under the axis."""
    # The label band sits below the axis line; this window catches the digits
    # without catching the legend further down.
    band = image[615:637]
    dark = band.max(axis=2) < 150
    columns = np.where(dark.sum(axis=0) >= 2)[0]

    centres, run = [], [columns[0]]
    for x in columns[1:]:
        if x - run[-1] <= 12:
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

    labels = _year_label_centres(image)
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
WINDOW = 21


def _windowed_fraction(mask, window=WINDOW):
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


def trace(path):
    """Both readings of one scenario chart, as year-indexed curves."""
    image = np.asarray(Image.open(path).convert("RGB")).astype(int)
    to_value, to_year, (top, bottom, left, right) = calibrate(image)

    box = image[top : bottom + 1, left : right + 1]
    grey = _windowed_fraction(_matches(box, BAND_COLOURS["market_based"]))
    green = _windowed_fraction(_matches(box, BAND_COLOURS["saf"]))
    renewal = _windowed_fraction(_matches(box, BAND_COLOURS["fleet_renewal"]))

    years, mbm_top, saf_bottom, baseline = [], [], [], []
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

    return {
        "years": years,
        "mbm_top": mbm_top,
        "saf_solid_bottom": saf_bottom,
        "baseline": baseline,
    }


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
    parser.add_argument(
        "--images",
        default=r"D:\i.costa-alves\Downloads",
        help="directory holding atag_3rd_s0/s1/s2.PNG",
    )
    parser.add_argument("--write", action="store_true", help="merge into the YAML")
    arguments = parser.parse_args()

    results = {}
    for name in ("S0", "S1", "S2"):
        path = Path(arguments.images) / ("atag_3rd_%s.PNG" % name.lower())
        results[name] = trace(path)
        curve = results[name]
        drift = check_against_hand_digitisation(curve)
        if drift > 0.04:
            raise ValueError(
                "%s traced baseline disagrees with the hand-digitised T0 by %.1f %%, "
                "which points at the axis calibration rather than at the report"
                % (name, 100 * drift)
            )
        print("%s  baseline agrees with hand-digitised T0 to %.1f %%" % (name, 100 * drift))
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
"""


def write_yaml(results):
    """Merge the traced curves into the figures YAML, in place."""
    path = HERE / "atag_3rd_edition_figures.yaml"
    text = path.read_text(encoding="utf-8")
    marker = "\nscenarios:\n"
    if marker in text:
        text = text[: text.index(marker)]

    lines = [text.rstrip("\n"), YAML_HEADER.rstrip("\n"), "", "scenarios:"]
    for name, curve in results.items():
        lines.append("  %s:" % name)
        for key in ("years", "mbm_top", "saf_solid_bottom", "baseline"):
            # repr writes NaN as "nan", which YAML reads back as a string and
            # every downstream interp then fails on. ".nan" is the float.
            values = ", ".join(".nan" if v != v else repr(v) for v in curve[key])
            lines.append("    %s: [%s]" % (key, values))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("wrote %s" % path)


if __name__ == "__main__":
    main()

"""
retime_mandates
===============
Re-anchor every energy-pathway mandate curve in the ATAG scenarios so that it
starts at the prospection start year (2024) instead of 2020.

Why
---
``aeromaps/models/yaml_interpolator.py`` extends a curve backwards whenever its
first reference year precedes ``prospection_start_year``. With the observed
period extended to 2023, a mandate anchored at ``(2020, 0.0)`` therefore
back-filled SAF across 2020-2023 -- 1.31 % biofuel in 2023 for S1 and 2.33 % for
S2, against roughly 0.2 % actually observed. That both asserts counterfactual
fuel volumes for years we now have data for, and makes the frozen-technology
wedge baseline scenario-dependent (2,790 / 2,762 / 2,736 Mt where it had been a
single 2,845.1 Mt), which breaks the wedge comparison Paper 1 rests on.

What it does
------------
For each mandate curve, evaluated against its *original* anchors:

1. compute ``v(2024)`` by interpolating the original curve;
2. drop every anchor before 2024;
3. anchor 2024 at ``v(2024)`` (if 2024 is already an anchor, keep its value);
4. leave every anchor from 2024 onwards untouched.

The 2024-2050 trajectory is therefore preserved exactly as the reports specify,
while the historic period carries no mandate. Anchoring ``(2024, 0.0)`` instead
would have cut 2025 SAF by 40 % and is deliberately not done.

The transform is text-level so the provenance comments in the scenario files
(e.g. ``# Crop oils pathway from f2 * 44e9``) survive, and it handles both YAML
list styles in the tree: inline ``years: [ 2020, ... ]`` in the full editions and
block ``- 2020`` in the light edition. It is idempotent -- a curve already
starting at 2024 or later is left alone.

Usage
-----
    python retime_mandates.py [--check]
"""

import glob
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
NEW_START = 2024

TAG = re.compile(r"^(\s*)(mandate_quantity|mandate_share): !AeroMapsCustomDataType\s*$")
INLINE = re.compile(r"^(\s*)(years|values):\s*\[(.*)\]\s*$")
BLOCK_KEY = re.compile(r"^(\s*)(years|values):\s*$")
BLOCK_ITEM = re.compile(r"^(\s*)-\s*(\S+)\s*$")


def interpolate(years, values, target):
    """Linear interpolation of the original curve at `target`."""
    if target <= years[0]:
        return values[0]
    if target >= years[-1]:
        return values[-1]
    for i in range(len(years) - 1):
        if years[i] <= target <= years[i + 1]:
            span = years[i + 1] - years[i]
            if span == 0:
                return values[i]
            w = (target - years[i]) / span
            return values[i] + w * (values[i + 1] - values[i])
    raise AssertionError("unreachable")


def parse_number(text):
    """Parse a YAML scalar, tolerating the ``.nan`` spelling used in some files."""
    if text.lower().lstrip(".") == "nan":
        return float("nan")
    return float(text)


def fmt(value, as_int=False):
    """Render a number without gaining spurious precision.

    ``as_int`` preserves an all-integer source list. The GEMSEO grammar infers
    its type from the data, so emitting a float into a list that was written as
    integers fails validation at run time.
    """
    if value != value:  # NaN, written as ``.nan`` in these files
        return ".nan"
    if as_int:
        return str(int(round(value)))
    if isinstance(value, int) or (isinstance(value, float) and value.is_integer() and abs(value) < 1e15):
        # keep integers looking like integers, as in the source files
        return str(int(value))
    return repr(value)


def retime(years, values):
    """Apply the re-anchoring. Returns (new_years, new_values, changed)."""
    if years[0] >= NEW_START:
        return years, values, False
    keep = [i for i, y in enumerate(years) if y >= NEW_START]
    new_years = [NEW_START] + [years[i] for i in keep if years[i] != NEW_START]
    if NEW_START in years:
        v0 = values[years.index(NEW_START)]
    else:
        v0 = interpolate(years, values, NEW_START)
    new_values = [v0] + [values[i] for i in keep if years[i] != NEW_START]
    return new_years, new_values, True


def parse_list(lines, start):
    """Read the list beginning at `lines[start]`. Returns (values, end_index, style, indent)."""
    m = INLINE.match(lines[start])
    if m:
        indent, key, body = m.groups()
        items = [x.strip() for x in body.split(",") if x.strip()]
        return items, start + 1, "inline", indent
    m = BLOCK_KEY.match(lines[start])
    if not m:
        raise ValueError(f"unrecognised list at line {start + 1}: {lines[start]!r}")
    indent, key = m.groups()
    items, i = [], start + 1
    while i < len(lines):
        mi = BLOCK_ITEM.match(lines[i])
        if not mi:
            break
        items.append(mi.group(2))
        i += 1
    return items, i, "block", indent


def render_list(key, items, style, indent):
    if style == "inline":
        return [f"{indent}{key}: [ " + ", ".join(items) + " ]"]
    return [f"{indent}{key}:"] + [f"{indent}- {v}" for v in items]


def process_file(path, check=False):
    lines = Path(path).read_text().splitlines()
    out, i, changes = [], 0, []
    while i < len(lines):
        m = TAG.match(lines[i])
        if not m:
            out.append(lines[i]); i += 1; continue
        out.append(lines[i]); i += 1

        # The tagged block holds `years` then `values` (comments may sit between).
        pending, found = [], {}
        while i < len(lines) and len(found) < 2:
            if INLINE.match(lines[i]) or BLOCK_KEY.match(lines[i]):
                key = (INLINE.match(lines[i]) or BLOCK_KEY.match(lines[i])).group(2)
                items, nxt, style, indent = parse_list(lines, i)
                found[key] = (items, style, indent)
                i = nxt
            else:
                pending.append(lines[i]); i += 1

        years = [int(float(x)) for x in found["years"][0]]
        values = [parse_number(x) for x in found["values"][0]]
        new_years, new_values, changed = retime(years, values)
        if changed:
            changes.append((years[0], new_years[0], values[0], new_values[0], len(years), len(new_years)))
            ystyle, yind = found["years"][1], found["years"][2]
            vstyle, vind = found["values"][1], found["values"][2]
            out += render_list("years", [str(y) for y in new_years], ystyle, yind)
            out += pending
            all_int = all(re.fullmatch(r"-?\d+", t) for t in found["values"][0])
            out += render_list(
                "values", [fmt(v, as_int=all_int) for v in new_values], vstyle, vind
            )
        else:
            out += render_list("years", found["years"][0], found["years"][1], found["years"][2])
            out += pending
            out += render_list("values", found["values"][0], found["values"][1], found["values"][2])

    if changes and not check:
        Path(path).write_text("\n".join(out) + "\n")
    return changes


def main(check=False):
    files = sorted(glob.glob(str(HERE / "*" / "data_inputs" / "*_energy.yaml")))
    total = 0
    for f in files:
        changes = process_file(f, check=check)
        total += len(changes)
        rel = Path(f).relative_to(HERE)
        if changes:
            print(f"{rel}: {len(changes)} mandate curve(s) re-anchored")
            for oy, ny, ov, nv, n0, n1 in changes:
                print(f"    {oy}->{ny}   first value {ov:.6g} -> {nv:.6g}   anchors {n0} -> {n1}")
        else:
            print(f"{rel}: no change")
    print(f"\n{'would re-anchor' if check else 're-anchored'} {total} mandate curve(s) across {len(files)} files")


if __name__ == "__main__":
    main(check="--check" in sys.argv)

"""Derive the energy files the coupled-demand scenario runs against.

The share and no-SAF files are generated from the uncoupled third-edition S1
files rather than maintained by hand, so a change upstream cannot leave them
quietly stale. The transforms themselves live in :mod:`aeromaps.utils.mandates`;
what is specific to this reproduction, and therefore stays here, is which files
feed which, where the shares are sampled from, and the kerosene price the coupled
analysis assumes.

``s1_energy_share.yaml``
    S1 with every quantity mandate rewritten as the equivalent share mandate.
    A quantity mandate cannot be used with price-elastic demand: it makes the
    blend share depend on total demand, which is itself a coupling variable, and
    the MDA fails on the resulting coupling shape mismatch. It is also the wrong
    policy object, since holding a volume fixed while demand falls raises the
    blend share with no policy saying so. Real mandates (ReFuelEU Aviation, the
    UK and Brazilian schemes) are written as percentages.

    The shares are not invented: they are the ones the *uncoupled* S1 run
    actually realises, sampled from its committed outputs at each mandate's own
    anchor years, so with demand held exogenous this file reproduces S1's SAF
    trajectory exactly.

``s1_energy_nosaf.yaml``
    The same file with every drop-in SAF mandate zeroed, so fossil kerosene
    supplies the whole drop-in fleet. Alternative-aircraft carriers are left
    alone: S1's own ``*_electric_final_market_share`` is zero in every market, so
    their mandates are inert regardless, and zeroing them too would only be
    noise. This is the fuel-only counterfactual the demand response is read
    against.

The kerosene price
    Demand responds to the price of fuel, so the coupled runs cannot inherit the
    report-era price the uncoupled reproduction carries, which declines from
    0.0126 EUR/MJ in 2024 to 0.012 in 2050 and sits on the 1990-2026 real mean.
    From 2026 they hold the observed 2026 mean flat instead, with the observed
    2025 annual mean between the two. All three coupled energy files get the same
    trajectory: the two generated here, and the hand-maintained
    ``s1_energy.yaml``, whose kerosene block alone is rewritten so its comments
    survive. The uncoupled S1 and S2 keep the report-era price.

    2026 is a spike year, rising from 2.03 $/gal in January to 3.70 in March, so
    holding it flat treats that shock as lasting. That is the assumption, and the
    paper states it.

Run from this directory::

    python make_energy_files.py
"""

import io
import json
import re
from pathlib import Path

from aeromaps.utils.mandates import quantity_to_share, zero_mandates
from aeromaps.utils.scenarios import find_scenario
from aeromaps.utils.yaml import read_yaml_file, write_yaml_file

HERE = Path(__file__).resolve().parent
ATAG = HERE.parent
# The scenario definitions ship with the package; the S1 result these shares are
# sampled from is a published one and stays here with the document that reports it.
SOURCE_ENERGY = find_scenario("atag_3rd_edition_full").path / "data_inputs" / "s1_energy.yaml"
SOURCE_OUTPUTS = ATAG / "3rd_edition_full" / "data_outputs" / "s1.json"
COUPLED_INPUTS = find_scenario("atag_3rd_edition_coupled_demand").path / "data_inputs"
SHARE_FILE = COUPLED_INPUTS / "s1_energy_share.yaml"
NOSAF_FILE = COUPLED_INPUTS / "s1_energy_nosaf.yaml"
QUANTITY_FILE = COUPLED_INPUTS / "s1_energy.yaml"

FIRST_YEAR = 2000

# Every drop-in pathway in the source file except fossil kerosene itself. Liquid
# hydrogen and battery electric are aircraft-type carriers, not drop-in fuel
# pathways, and are left out on purpose: see the module docstring.
DROPIN_SAF_PATHWAYS = (
    "hefa_oil_crops_trees",
    "atj_cellulosic_cover_crops",
    "hefa_waste_residue_lipids",
    "atj_agricultural_residues",
    "ft_woody_biomass",
    "ft_municipal_solid_waste",
    "atj_waste_gas",
    "electrofuel",
)

# --- The kerosene price ------------------------------------------------------
# Model prices are in 2019 euros per MJ. The conversion is the one the WCTR
# paper uses (Costa-Alves et al., 2026): its constant 2019 price of 0.0126556
# EUR/MJ is the 2019 annual mean of EIA's U.S. Gulf Coast kerosene-type jet fuel
# spot price (series MJFUELUSGULF), 1.877583 $/gal, so one 2019 dollar per
# gallon is 0.0126556 / 1.877583 EUR/MJ. That is 0.898 EUR/$ over 133.25 MJ/gal
# (0.8 kg/L, 44 MJ/kg, 3.7854 L/gal).
EUR_PER_MJ_PER_2019_USD_PER_GAL = 0.01265556850664434 / 1.877583

# U.S. CPI-U, not seasonally adjusted (BLS, via FRED series CPIAUCNS).
CPI_2019_MEAN = 255.6574
CPI_AUG_2026 = 334.980

# 2025: the EIA monthly series deflated month by month to 2019 dollars. October
# 2025 has no CPI-U, as BLS did not publish it, so it is interpolated between
# September and November.
PRICE_2025_IN_2019_USD_PER_GAL = 1.68088
# 2026: mean of the EIA weekly spot price, 1 January to 11 September 2026, in
# August-2026 dollars (median 3.51, interquartile range 2.80-3.95).
PRICE_2026_MEAN_REAL_AUG2026_USD_PER_GAL = 3.31

KEROSENE_PRICE_2025 = PRICE_2025_IN_2019_USD_PER_GAL * EUR_PER_MJ_PER_2019_USD_PER_GAL
KEROSENE_PRICE_FROM_2026 = (
    PRICE_2026_MEAN_REAL_AUG2026_USD_PER_GAL
    * CPI_2019_MEAN
    / CPI_AUG_2026
    * EUR_PER_MJ_PER_2019_USD_PER_GAL
)
LAST_HISTORICAL_YEAR = 2024
END_YEAR = 2050

SHARE_HEADER = """\
# GENERATED by make_energy_files.py -- do not edit by hand.
#
# {source} with every quantity mandate rewritten as the equivalent share mandate.
# Shares are the ones the uncoupled S1 scenario realises, sampled from its committed
# outputs at each mandate's own anchor years, so with exogenous demand this reproduces
# S1's SAF trajectory exactly.
#
# Quantity mandates cannot be used with price-elastic demand: they make the blend share
# a function of total demand, which is itself a coupling variable, and the MDA fails with
# a coupling shape mismatch. See the module docstring of make_energy_files.py.
#
# Fossil kerosene holds the observed 2026 mean price from 2026, not the report-era
# price of the uncoupled S1, since demand here responds to it.
"""

NOSAF_HEADER = """\
# GENERATED by make_energy_files.py -- do not edit by hand.
#
# {source} with every drop-in SAF mandate zeroed, so fossil kerosene supplies the whole
# drop-in fleet. The fuel-only counterfactual the coupled demand response is read
# against; alternative-aircraft carriers are untouched and already inert.
"""


def realised_shares():
    """Share of drop-in energy carried by each carrier in the uncoupled S1 run."""
    outputs = json.loads(SOURCE_OUTPUTS.read_text(encoding="utf-8"))["vector_outputs"]
    years = list(range(FIRST_YEAR, FIRST_YEAR + len(outputs["energy_consumption_dropin_fuel"])))
    total = dict(zip(years, outputs["energy_consumption_dropin_fuel"]))
    shares = {}
    for column, series in outputs.items():
        if not column.endswith("_energy_consumption"):
            continue
        per_year = dict(zip(years, series))
        shares[column[: -len("_energy_consumption")]] = {
            year: (100.0 * per_year[year] / total[year] if total[year] else 0.0) for year in years
        }
    return shares


def kerosene_price(years, values):
    """History to 2024 unchanged, observed 2025, then the 2026 mean held flat."""
    history = [(int(y), float(v)) for y, v in zip(years, values) if int(y) <= LAST_HISTORICAL_YEAR]
    if not history or history[-1][0] != LAST_HISTORICAL_YEAR:
        raise ValueError(f"the kerosene price history must run to {LAST_HISTORICAL_YEAR}")
    tail = [
        (2025, round(KEROSENE_PRICE_2025, 6)),
        (2026, round(KEROSENE_PRICE_FROM_2026, 6)),
        (END_YEAR, round(KEROSENE_PRICE_FROM_2026, 6)),
    ]
    points = history + tail
    return [y for y, _ in points], [v for _, v in points]


def set_kerosene_price(path):
    """Apply the coupled price to a generated energy file, through the YAML writer."""
    document = read_yaml_file(str(path))
    price = document["fossil_kerosene"]["inputs"]["economics"]["mean_mfsp_without_resource"]
    price.years, price.values = kerosene_price(price.years, price.values)
    write_yaml_file(document, str(path))


_FLOW_LIST = re.compile(r"(?P<key>years|values):\s*\[(?P<body>[^\]]*)\]", re.S)


def _format_flow(key, items, indent, per_line):
    """A flow sequence laid out like the hand-maintained file's own."""
    lead = f"{key}: [ "
    lines, prefix = [], " " * indent + lead
    for start in range(0, len(items), per_line):
        chunk = ", ".join(items[start : start + per_line])
        lines.append(prefix + chunk)
        prefix = " " * (indent + len(lead))
    return ",\n".join(lines) + " ]"


def set_kerosene_price_in_place(path):
    """Rewrite only the kerosene cost block of a hand-maintained file.

    Parsing and re-writing the file would lose its 80 lines of comments, so the
    two flow sequences are replaced as text, inside the ``fossil_kerosene``
    block only, and everything else is left byte-for-byte as it was.
    """
    text = io.open(path, encoding="utf-8").read()
    start = text.index("\nfossil_kerosene:")
    following = re.search(r"\n[A-Za-z_][\w-]*:", text[start + 1 :])
    end = start + 1 + following.start() if following else len(text)
    block = text[start:end]

    anchor = block.index("mean_mfsp_without_resource:")
    head, cost = block[:anchor], block[anchor:]
    lists = {m.group("key"): m for m in _FLOW_LIST.finditer(cost)}
    if set(lists) < {"years", "values"}:
        raise ValueError(f"no flow-style years/values under mean_mfsp_without_resource in {path}")

    def parse(match):
        return [s.strip() for s in match.group("body").split(",") if s.strip()]

    years, values = kerosene_price(parse(lists["years"]), parse(lists["values"]))
    indent = len(cost[: lists["years"].start()].rsplit("\n", 1)[-1])
    new_years = _format_flow("years", [str(y) for y in years], indent, 6)
    new_values = _format_flow("values", [f"{v:.9g}" for v in values], indent, 5)

    # Replace the later span first so the earlier one's offsets stay valid.
    for key, replacement in sorted(
        (("years", new_years), ("values", new_values)),
        key=lambda item: lists[item[0]].start(),
        reverse=True,
    ):
        match = lists[key]
        cost = cost[: match.start()] + replacement.lstrip() + cost[match.end() :]

    io.open(path, "w", encoding="utf-8", newline="").write(text[:start] + head + cost + text[end:])


def _prepend(path, header):
    """Put the generated-by banner back, which the YAML writer does not carry."""
    body = io.open(path, encoding="utf-8").read()
    io.open(path, "w", encoding="utf-8", newline="").write(header + body)


def main():
    quantity_to_share(SOURCE_ENERGY, realised_shares(), output_file=SHARE_FILE)
    set_kerosene_price(SHARE_FILE)
    _prepend(SHARE_FILE, SHARE_HEADER.format(source=SOURCE_ENERGY.name))
    print("wrote %s" % SHARE_FILE.name)

    zero_mandates(SHARE_FILE, DROPIN_SAF_PATHWAYS, output_file=NOSAF_FILE)
    _prepend(NOSAF_FILE, NOSAF_HEADER.format(source=SHARE_FILE.name))
    print("wrote %s (%d pathways zeroed)" % (NOSAF_FILE.name, len(DROPIN_SAF_PATHWAYS)))

    set_kerosene_price_in_place(QUANTITY_FILE)
    print("set the kerosene price in %s" % QUANTITY_FILE.name)
    print(
        "kerosene: %.6f EUR/MJ in 2025, %.6f from 2026"
        % (KEROSENE_PRICE_2025, KEROSENE_PRICE_FROM_2026)
    )


if __name__ == "__main__":
    main()

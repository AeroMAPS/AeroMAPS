"""
utils
=====
Loading helpers specific to the ATAG *Waypoint 2050* climate analysis.

Only what is specific to this analysis lives here. Two things that used to sit
in this module have moved into the package, so they exist once rather than in
parallel:

* reading committed ``<edition>/data_outputs/<scenario>.json`` back into a
  plot-compatible object is :func:`aeromaps.utils.results_view.load_results`;
* the five-family mechanism grouping and its palette are in
  :mod:`aeromaps.plots.climate_mechanisms`, shared with the plot classes.
"""

from __future__ import annotations

import copy
import csv
from pathlib import Path

import pandas as pd

# atag_scenarios/
BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[3]
OBSERVED = (
    REPO
    / "aeromaps"
    / "resources"
    / "historical_data"
    / ("world_air_transport_traffic_1929_2024.csv")
)


def load_observed():
    """The A4A/ICAO observed traffic series, indexed by year.

    Blank cells in the source stay as NaN -- they are years the source does not
    cover, never interpolated.
    """
    rows = list(csv.DictReader(OBSERVED.open(encoding="utf-8"), delimiter=";"))
    frame = pd.DataFrame(rows)
    frame["year"] = frame["year"].astype(int)
    frame = frame.set_index("year")
    return frame.apply(pd.to_numeric, errors="coerce")


# Scenario naming differs between editions: the third edition swapped its two
# scenarios relative to the second, so analogous scenarios must be paired
# explicitly rather than by name. Asserted in the analysis notebook.
ANALOGOUS = {
    ("3rd_edition_full", "s1"): ("2nd_edition_full", "s2"),
    ("3rd_edition_full", "s2"): ("2nd_edition_full", "s1"),
}


# --------------------------------------------------------------------------
# Contrail mitigation variants
# --------------------------------------------------------------------------

CONTRAIL_VARIANTS = Path(__file__).resolve().parent / "contrail_variants.yaml"

LEVELS = ("Low", "Central", "High")


def load_contrail_variants(path=CONTRAIL_VARIANTS):
    """Load the Teoh-based contrail mitigation variants.

    Returns
    -------
    reference : dict
        Citation and DOI of the source study.
    families : dict
        ``{family_key: {"label": str, "description": str,
                        "levels": {level: {parameter: value}}}}`` where each
        level's mapping is the complete set of ``process.parameters`` overrides
        for that variant, with the shared defaults already merged in.
    """
    import yaml

    document = yaml.safe_load(Path(path).read_text())
    defaults = document.get("defaults", {})

    families = {}
    for key, family in document["families"].items():
        shared = {
            "operations_contrails_start_year": family["operations_contrails_start_year"],
            **defaults,
        }
        families[key] = {
            "label": family["label"],
            "description": " ".join(family["description"].split()),
            "levels": {level: {**shared, **values} for level, values in family["levels"].items()},
        }
        missing = set(LEVELS) - set(families[key]["levels"])
        if missing:
            raise ValueError(f"family {key!r} is missing level(s) {sorted(missing)}")

    return document["reference"], families


def variant_name(family_label, level):
    """Scenario name used in the assembly, e.g. 'Low-risk diversion - Central'."""
    return f"{family_label} - {level}"


# --------------------------------------------------------------------------
# Non-CO2 uncertainty bands
# --------------------------------------------------------------------------

NON_CO2_BANDS = Path(__file__).resolve().parent / "non_co2_uncertainty.yaml"

BANDS = ("low", "central", "high")


def load_non_co2_bands(path=NON_CO2_BANDS):
    """Load the non-CO2 uncertainty bands.

    Returns
    -------
    reference : dict
        Citations and DOIs behind the bounds.
    bands : dict
        ``{band_key: {"label", "description", "sensitivity_rf",
        "saf_emission_index_particles_number", ...}}`` in low -> central ->
        high order, i.e. increasing warming.
    pairing : dict
        ``{band_key: "strongest" | "central" | "weakest"}``, which mitigation
        bound each band takes when the avoidance scenarios are run under it.
    """
    import yaml

    document = yaml.safe_load(Path(path).read_text())
    bands = {key: dict(document["bands"][key]) for key in BANDS}
    missing = set(BANDS) - set(document["bands"])
    if missing:
        raise ValueError(f"non-CO2 band file is missing band(s) {sorted(missing)}")

    kerosene = float(document["kerosene_emission_index_particles_number"])
    for key, band in bands.items():
        # Re-derive the implied reduction from the emission index rather than
        # trusting the comment: the model scales contrail forcing by
        # sqrt(EIn_pathway / EIn_default), so the two must stay consistent.
        implied = 100.0 * (
            1.0 - (float(band["saf_emission_index_particles_number"]) / kerosene) ** 0.5
        )
        declared = float(band["implied_saf_contrail_reduction_percent"])
        if abs(implied - declared) > 0.1:
            raise ValueError(
                f"band {key!r} declares a {declared} % SAF contrail reduction but its "
                f"emission index implies {implied:.1f} %"
            )
        band["implied_saf_contrail_reduction_percent"] = implied

    _check_contrail_bands(document["derivation"], bands)
    return document["reference"], bands, document["mitigation_pairing"]


def derive_contrail_bands(derivation):
    """Contrail RF and efficacy for each band, from the inputs they rest on.

    The band on the product RF x efficacy is its ±1σ: the product of two
    independent factors, with coefficients of variation taken from Lee et al.'s
    RF range (±70 % at 5–95 %, so 0.70 / 1.645) and from the spread of Wang et
    al.'s three efficacies. That deviation is split between the two factors in
    proportion to their squared coefficients of variation, so each band states
    both explicitly without pushing either to an extreme.

    Returns
    -------
    dict
        ``{band: {"sensitivity_rf", "ratio_erf_rf", "contrail_erf_multiplier"}}``.
    """
    from statistics import NormalDist, pstdev

    cv_rf = float(derivation["lee_rf_5_95_relative"]) / NormalDist().inv_cdf(0.95)
    efficacies = [float(e) for e in derivation["wang_efficacy_samples"]]
    mean_efficacy = sum(efficacies) / len(efficacies)
    cv_efficacy = pstdev(efficacies) / mean_efficacy

    cv2_rf, cv2_efficacy = cv_rf**2, cv_efficacy**2
    cv_product = ((1.0 + cv2_rf) * (1.0 + cv2_efficacy) - 1.0) ** 0.5
    share_rf = cv2_rf / (cv2_rf + cv2_efficacy)

    central_rf = float(derivation["central_sensitivity_rf"])
    central_efficacy = float(derivation["central_ratio_erf_rf"])
    derived = {}
    for key, multiplier in (
        ("low", 1.0 - cv_product),
        ("central", 1.0),
        ("high", 1.0 + cv_product),
    ):
        derived[key] = {
            "sensitivity_rf": central_rf * multiplier**share_rf,
            "ratio_erf_rf": central_efficacy * multiplier ** (1.0 - share_rf),
            "contrail_erf_multiplier": multiplier,
        }
    return derived


def _check_contrail_bands(derivation, bands, tolerance=5e-4):
    """Refuse a band file whose declared values drift from their derivation."""
    derived = derive_contrail_bands(derivation)
    for key, band in bands.items():
        for field, expected in derived[key].items():
            declared = float(band[field])
            if abs(declared / expected - 1.0) > tolerance:
                raise ValueError(
                    f"band {key!r} declares {field} = {declared} but its derivation "
                    f"gives {expected:.6g}; update non_co2_uncertainty.yaml"
                )


def apply_non_co2_band(process, band):
    """Apply one uncertainty band to an already-built process, in place.

    Sets the contrail RF sensitivity and the ERF/RF ratio carrying the efficacy
    on the climate model, and the particle-number emission index on every SAF
    pathway. All three are read at compute time, so this must be called before
    ``compute()`` and after ``create_process()``.

    Only non-fossil drop-in pathways take the SAF index. Fossil kerosene is the
    reference the correction is relative to, and a fossil pathway that is not the
    default, such as hydroprocessed kerosene, keeps the index it declares: it is
    not SAF, and stamping SAF's value on it would silently give it SAF's contrail
    benefit.
    """
    climate_model = process.models["climate_model"]
    # Deep-copy first. The settings dict is shared with whatever the climate
    # configuration file was parsed into, so mutating it in place would leak
    # this band into every process built afterwards -- silently, and in a way
    # that depends on the order the bands happen to be run in.
    climate_model.species_settings = copy.deepcopy(climate_model.species_settings)
    contrails = climate_model.species_settings["Contrails"]
    contrails["sensitivity_rf"] = float(band["sensitivity_rf"])
    contrails["ratio_erf_rf"] = float(band["ratio_erf_rf"])

    emission_index = float(band["saf_emission_index_particles_number"])
    applied = []
    for pathway in process.pathways_manager.get(aircraft_type="dropin_fuel"):
        if getattr(pathway, "default", False) or pathway.energy_origin == "fossil":
            continue
        setattr(
            process.parameters, f"{pathway.name}_emission_index_particles_number", emission_index
        )
        applied.append(pathway.name)

    if not applied:
        raise ValueError(
            "no non-default drop-in pathway found; the SAF axis of the band would "
            "have no effect and the result would silently be a contrail-only band"
        )
    return applied


def band_name(scenario_label, band_label):
    """Scenario name used in the assembly, e.g. 'S1 SAF-focused - High non-CO2'."""
    return f"{scenario_label} - {band_label}"

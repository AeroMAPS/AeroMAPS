"""Generate the push-fleet markets profile ``markets_push.yaml`` (next to the demo notebook).

Phase 1 of the push-fleet-model integration (see ``FLEET_PUSH_INTEGRATION_PLAN.md``).

Paco's delivery-driven ("push") fleet engine partitions the passenger fleet into
four segments — turboprop (TP), regional jet (RJ), narrow body (NB) and wide body
(WB).  This script turns those segments into AeroMAPS *passenger markets* and emits
a ``markets.yaml`` profile that mirrors ``default_markets/markets.yaml`` exactly
(same ``global`` / ``defaults`` blocks), so a process can be built on it and the
generic RPK->ASK chain runs per segment.

The per-segment ``initial`` shares are **sourced from the calibration Excel**, not
hand-typed, by reusing :func:`calculate_stats_by_market` (the same aggregation the
engine uses).  With flexible start year the pivot is ``last_historical_year = 2024``,
so these are 2024 shares (no 2019 back-cast):

* ``rpk_share_last_historical_year``    = segment ASK / total passenger ASK * 100.
  ASK is used as a proxy for the RPK split (load factors per segment are not in the
  Excel) — documented as an assumption in the emitted YAML.
* ``energy_share_last_historical_year`` = segment Sum(MJ_fuel_ask * ASK) /
  total Sum(MJ_fuel_ask * ASK) * 100.

The existing ``freight`` market is copied verbatim from the default profile.

Run from the repo root::

    python aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here/generate_push_markets.py

Regenerable: rerun whenever the calibration Excel or the classification YAML change.
"""

from pathlib import Path

from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet_push.fleet_model_push import (
    calculate_stats_by_market,
)


# --- paths (relative to the repo root; this file sits 5 levels under it) -------
def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


ROOT = _project_root()
CLASSIFICATION_YAML = (
    ROOT / "aeromaps/resources/data/default_fleet_push/default_aircraft_classification.yaml"
)
AIRCRAFT_PARAMETERS_XLSX = (
    ROOT
    / "aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here"
    / "aircraft_type_key_parameters.xlsx"
)
DEFAULT_MARKETS_YAML = ROOT / "aeromaps/resources/data/default_markets/markets.yaml"
# markets_push.yaml is push-scenario data, not a shipped default: it lives next to the
# demo notebook (like tutorials/05's fleet.yaml), so regenerate it there.
OUTPUT_YAML = ROOT / "aeromaps/notebooks/custom_workflow/push_fleet_model/data/markets_push.yaml"

# A market's AeroMAPS id IS the engine segment label (the ``market:`` value in the
# classification YAML) — no mapping table. The dicts below only supply per-segment
# *display* metadata, keyed by that same label; both fall back gracefully so adding a
# segment to the classification YAML needs no edit here.
MARKET_NAMES = {
    "TP": "Turboprop",
    "RJ": "Regional Jet",
    "NB": "Narrow Body",
    "WB": "Wide Body",
}
# Preferred emit order; any segment not listed is appended alphabetically.
SEGMENT_ORDER = ("TP", "RJ", "NB", "WB")
# Placeholder DOC non-energy per ASK init values reused from the default profile's
# per-range markets (short/medium/long). The push profile does not yet calibrate
# these per segment; they are only consumed when a bottom-up cost model is wired in.
PLACEHOLDER_DOC_NON_ENERGY = {
    "TP": 0.048375,  # placeholder (default short_range value)
    "RJ": 0.048375,  # placeholder (default short_range value)
    "NB": 0.0301,  # placeholder (default medium_range value)
    "WB": 0.024725,  # placeholder (default long_range value)
}
_DEFAULT_DOC_NON_ENERGY = 0.0301  # fallback for a segment without a calibrated placeholder


def _ordered_segments(segments) -> list:
    """Preferred order first (SEGMENT_ORDER), then any extras alphabetically."""
    extras = sorted(s for s in segments if s not in SEGMENT_ORDER)
    return [s for s in SEGMENT_ORDER if s in segments] + extras


def compute_segment_shares() -> dict:
    """Aggregate per-type Excel rows to segment rpk/energy shares (sum to 100)."""
    grouped = calculate_stats_by_market(
        classification_yaml_path=str(CLASSIFICATION_YAML),
        aircraft_parameters_excel_path=str(AIRCRAFT_PARAMETERS_XLSX),
    )
    # ``MJ_fuel_ask_segment`` is the ASK-weighted mean MJ/ASK, so
    # segment energy proxy = total_adjusted_asks * MJ_fuel_ask_segment
    #                      = sum(MJ_fuel_ask * ASK) over the segment's types.
    grouped = grouped.copy()
    grouped["energy"] = grouped["total_adjusted_asks"] * grouped["MJ_fuel_ask_segment"]
    total_ask = grouped["total_adjusted_asks"].sum()
    total_energy = grouped["energy"].sum()

    shares = {}
    for _, row in grouped.iterrows():
        segment = str(row["market"]).strip()
        # The market id IS the engine segment label.
        shares[segment] = {
            "rpk_share": round(float(row["total_adjusted_asks"]) / total_ask * 100, 4),
            "energy_share": round(float(row["energy"]) / total_energy * 100, 4),
        }
    return shares


def _segment_comment(segment: str) -> str:
    return f"  # Paco push segment '{segment}' — id == engine segment label"


def render_yaml(shares: dict) -> str:
    """Render the push markets profile mirroring the default file's schema.

    The ``global`` and ``defaults`` blocks are copied verbatim from
    ``default_markets/markets.yaml``; only the per-market entries differ.
    """
    default_text = DEFAULT_MARKETS_YAML.read_text(encoding="utf-8")
    # Reuse everything up to (but excluding) the first market entry. In the default
    # file the market blocks start at the ``short_range:`` top-level key.
    marker = "\nshort_range:"
    head = default_text[: default_text.index(marker)].rstrip("\n")

    lines = [
        head,
        "",
        "# ── Push-fleet passenger segments (Paco's TP/RJ/NB/WB) ──────────────────────",
        "# Shares are SOURCED FROM THE CALIBRATION EXCEL (aircraft_type_key_parameters.xlsx)",
        "# by aggregating per-type rows to each segment via default_aircraft_classification.yaml;",
        "# regenerate with generate_push_markets.py. Pivot = last_historical_year = 2024.",
        "#   rpk_share    : segment ASK / total passenger ASK * 100",
        "#                  (ASK used as a PROXY for the RPK split — no per-segment LF).",
        "#   energy_share : segment Σ(MJ_fuel_ask·ASK) / total Σ(MJ_fuel_ask·ASK) * 100.",
        "# costs.doc_non_energy_per_ask_dropin_fuel_init values are PLACEHOLDERS reused",
        "# from the default per-range markets (not yet calibrated per push segment).",
        "",
    ]

    # Emit in preferred engine order (TP, RJ, NB, WB), extras alphabetically.
    for segment in _ordered_segments(shares):
        s = shares[segment]
        doc = PLACEHOLDER_DOC_NON_ENERGY.get(segment, _DEFAULT_DOC_NON_ENERGY)
        lines.append(f"{segment}:{_segment_comment(segment)}")
        lines.append(f'  name: "{MARKET_NAMES.get(segment, segment)}"')
        lines.append("  traffic_type: passenger")
        lines.append("  traffic_unit: RPK")
        lines.append("  inputs:")
        lines.append("    initial:")
        lines.append(f"      rpk_share_last_historical_year: {s['rpk_share']}")
        lines.append(f"      energy_share_last_historical_year: {s['energy_share']}")
        lines.append("    costs:")
        lines.append(f"      doc_non_energy_per_ask_dropin_fuel_init: {doc}  # placeholder")
        lines.append("")

    # Freight market: copy verbatim from the default profile.
    freight_block = default_text[default_text.index("\nfreight:") :].strip("\n")
    lines.append("# Freight market — copied verbatim from default_markets/markets.yaml.")
    lines.append(freight_block)
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    shares = compute_segment_shares()
    OUTPUT_YAML.write_text(render_yaml(shares), encoding="utf-8")
    print(f"Wrote {OUTPUT_YAML.relative_to(ROOT)}")
    for segment in _ordered_segments(shares):
        s = shares[segment]
        print(f"  {segment:>4}  rpk={s['rpk_share']:>8.4f}%  energy={s['energy_share']:>8.4f}%")


if __name__ == "__main__":
    main()

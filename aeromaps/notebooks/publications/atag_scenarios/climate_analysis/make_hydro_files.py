"""Derive the hydroprocessed-kerosene variant of S1 for the climate analysis.

Hydroprocessing raises the hydrogen content of fossil kerosene, which lowers
soot and ice-particle numbers and therefore contrail forcing, at a small cost and
a small CO2 penalty. Wang et al. (2026) include it alongside SAF as a near-term
contrail lever; the Waypoint 2050 reports do not, so it is run here as a variant
of the third-edition S1 rather than written into the reproduction.

It is modelled as a drop-in pathway of its own, ``hydroprocessed_kerosene``,
distinct from fossil kerosene. Its three properties are taken from the literature:

cost
    Kerosene's selling price x 1.02: Faber et al. (2022) put the increase in jet
    fuel cost at about 2 % for hydrotreating straight-run kerosene with hydrogen
    from existing steam-methane reforming units, as quoted by Piris-Cabezas et
    al. (2024) and in the ICAO Environmental Report 2025.
well-to-wake CO2
    Kerosene's factor x 1.025: the same sources give a GHG penalty of about 2.5 %
    of the lifecycle emissions of fossil jet fuel.
contrails
    A particle-number emission index of 7.442e13 against kerosene's 2.0e14, the
    contrail energy-forcing reduction of 39 % that Wang et al. simulate for 14.6 %
    hydrogen content, the midpoint between mild and harsh hydroprocessing of
    Quante et al. (2024). The low and high warming levels of the climate analysis
    set it to their 48 % and 30 % bounds in place.

Its deployment follows Wang et al.'s schedule, 2 % of aviation fuel in 2025,
10 % in 2030, 20 % in 2035 and 30 % from 2040, as a share mandate. Only fossil
kerosene can be hydroprocessed, so the share is capped at the fossil share S1
actually leaves, taken from its committed outputs. S1's SAF displaces fossil fuel
fast enough that the cap binds from the early 2040s. The energy model gives
quantity-mandated SAF priority in any case, the same rule the ICCT (2025)
applies, and the explicit cap only keeps the input self-describing.

The variant is well-to-wake, like the rest of the climate analysis. A tank-to-wake
twin would need the penalty removed rather than scaled, since it is upstream: the
combustion factor stays kerosene's.

Run from this directory::

    python make_hydro_files.py
"""

import copy
import io
import json
from pathlib import Path

from aeromaps.models.base import AeroMapsCustomDataType
from aeromaps.utils.scenarios import find_scenario
from aeromaps.utils.yaml import read_yaml_file, write_yaml_file

HERE = Path(__file__).resolve().parent
ATAG = HERE.parent
SOURCE_ENERGY = find_scenario("atag_3rd_edition_full").path / "data_inputs" / "s1_energy.yaml"
SOURCE_OUTPUTS = ATAG / "3rd_edition_full" / "data_outputs" / "s1.json"
CLIMATE_SCENARIO = find_scenario("atag_climate_analysis").path
HYDRO_ENERGY = CLIMATE_SCENARIO / "data_inputs" / "s1_energy_hydro.yaml"
HYDRO_CONFIG = CLIMATE_SCENARIO / "config_files" / "config_s1_hydro.yaml"

PATHWAY = "hydroprocessed_kerosene"
FIRST_YEAR = 2000

COST_FACTOR = 1.02  # Faber et al. (2022)
CO2_FACTOR = 1.025  # Faber et al. (2022)
KEROSENE_PARTICLES = 2.0e14
CONTRAIL_REDUCTION = {"low": 0.48, "central": 0.39, "high": 0.30}  # Wang et al. (2026)
# Wang et al. (2026), Methods: hydroprocessed share of aviation fuel.
SCHEDULE = {2025: 2.0, 2030: 10.0, 2035: 20.0, 2040: 30.0}
LAST_YEAR = 2050
# Kept this far below the fossil share, in percentage points, so the capped share
# never exceeds what is left by floating-point rounding alone.
CAP_MARGIN = 1e-6


def particles_for(reduction):
    """Emission index whose sqrt-law correction gives ``reduction`` at 100 %."""
    return KEROSENE_PARTICLES * (1.0 - reduction) ** 2


def scheduled_share(year):
    """Wang et al.'s share for ``year``, linear between anchors and flat after."""
    anchors = sorted(SCHEDULE.items())
    if year <= anchors[0][0]:
        return anchors[0][1]
    for (y0, v0), (y1, v1) in zip(anchors, anchors[1:]):
        if y0 <= year <= y1:
            return v0 + (v1 - v0) * (year - y0) / (y1 - y0)
    return anchors[-1][1]


def fossil_share():
    """Fossil kerosene's share of S1's drop-in energy, in %, by year."""
    outputs = json.loads(SOURCE_OUTPUTS.read_text(encoding="utf-8"))["vector_outputs"]
    total = outputs["energy_consumption_dropin_fuel"]
    fossil = outputs["fossil_kerosene_energy_consumption"]
    return {FIRST_YEAR + i: 100.0 * f / t for i, (f, t) in enumerate(zip(fossil, total)) if t}


def mandate_share():
    """Scheduled share capped at the fossil share S1 leaves, 2025 to 2050."""
    fossil = fossil_share()
    years = list(range(min(SCHEDULE), LAST_YEAR + 1))
    values = [round(min(scheduled_share(y), fossil[y] - CAP_MARGIN), 6) for y in years]
    return years, values


def _scaled(series, factor):
    return AeroMapsCustomDataType(
        {
            "years": list(series.years),
            "values": [v * factor for v in series.values],
            "method": series.method,
        }
    )


def hydroprocessed_pathway(kerosene, level="central"):
    """Kerosene's block, turned into a separate mandated pathway."""
    pathway = copy.deepcopy(kerosene)
    pathway["name"] = PATHWAY
    pathway["default"] = False
    pathway["compute_all_years"] = True
    inputs = pathway["inputs"]

    environmental = inputs["environmental"]
    environmental["mean_co2_emission_factor_without_resource"] = _scaled(
        environmental["mean_co2_emission_factor_without_resource"], CO2_FACTOR
    )
    environmental["emission_index"]["particles_number"] = particles_for(CONTRAIL_REDUCTION[level])

    economics = inputs["economics"]
    economics["mean_mfsp_without_resource"] = _scaled(
        economics["mean_mfsp_without_resource"], COST_FACTOR
    )

    years, values = mandate_share()
    mandate = {
        "mandate_type": "share",
        "mandate_share": AeroMapsCustomDataType(
            {"years": years, "values": values, "method": "linear"}
        ),
    }
    # The mandate first, as the SAF pathways carry it.
    pathway["inputs"] = {"mandate": mandate, **inputs}
    return pathway


ENERGY_HEADER = """\
# GENERATED by make_hydro_files.py -- do not edit by hand.
#
# {source} with a hydroprocessed_kerosene pathway added: kerosene's cost x 1.02 and
# well-to-wake CO2 x 1.025 (Faber et al. 2022), a particle index giving a 39 %
# contrail reduction at 14.6 % hydrogen content (Wang et al. 2026), and Wang et al.'s
# deployment schedule capped at the fossil share S1 leaves. See the module
# docstring of make_hydro_files.py.
"""

CONFIG = """\
# GENERATED by make_hydro_files.py -- do not edit by hand.
#
# Third-edition S1 with hydroprocessed kerosene added as a separate drop-in
# pathway. Identical to atag_3rd_edition_full/config_files/config_s1.yaml except
# for the energy carriers file and the output path, so the committed edition
# results are never touched.
data:
  inputs:
    json_inputs_file: ../../atag_3rd_edition_full/data_inputs/s1_inputs.json
  outputs:
    json_outputs_file: ../data_outputs/s1_hydro.json
models:
  climate:
    climate_model_data_file: ../../climate_models/climate_model_fair_contrail_efficacy.yaml
  energy:
    energy_carriers_model_data_file: ../data_inputs/s1_energy_hydro.yaml
    resources_model_data_file: ../../atag_3rd_edition_full/data_inputs/resources.yaml
    processes_model_data_file: ../../atag_3rd_edition_full/data_inputs/processes.yaml
  standards:
  - models_traffic
  - models_efficiency_top_down_interp
  - models_energy_with_fuel_effect
  - models_energy_cost
  - models_emissions
  - models_offset
  - models_sustainability
  - models_operation_cost_top_down
  markets:
    markets_data_file: ../../markets/markets_central.yaml
"""


def main():
    document = read_yaml_file(str(SOURCE_ENERGY))
    if PATHWAY in document:
        raise ValueError(f"{SOURCE_ENERGY.name} already defines {PATHWAY}")

    ordered = {}
    for name, block in document.items():
        ordered[name] = block
        if name == "fossil_kerosene":
            ordered[PATHWAY] = hydroprocessed_pathway(block)

    HYDRO_ENERGY.parent.mkdir(parents=True, exist_ok=True)
    write_yaml_file(ordered, str(HYDRO_ENERGY))
    body = io.open(HYDRO_ENERGY, encoding="utf-8").read()
    io.open(HYDRO_ENERGY, "w", encoding="utf-8", newline="").write(
        ENERGY_HEADER.format(source=SOURCE_ENERGY.name) + body
    )
    HYDRO_CONFIG.write_text(CONFIG, encoding="utf-8")

    years, values = mandate_share()
    print("wrote", HYDRO_ENERGY.name, "and", HYDRO_CONFIG.name)
    print("hydroprocessed share, % of drop-in energy:")
    for year in (2025, 2030, 2035, 2040, 2043, 2045, 2050):
        print("  %d  %6.2f" % (year, values[years.index(year)]))


if __name__ == "__main__":
    main()

"""Reject energy YAML keys that no energy model reads.

Every input the generic energy models read is looked up with ``input_data.get(key, default)``
where ``default`` is zero-filled, so a key that does not match resolves to zero rather than
raising. Zero is a physically meaningful emission factor, cost or consumption rate, so a
misspelling produces a run that completes with plausible-looking but wrong numbers. Four such
mistakes reached production data and three more sit latent in the code.

Making the lookups strict is not an option: of the pathways shipped in this repository, most do
not declare ``mean_co2_emission_factor_without_resource`` at all and are right not to. The
separable signal is that a misspelling produces an *unknown* key while a legitimately absent
optional input produces *no* key, and that distinction only exists at load time.

Each historical shape is reproduced below next to the case it must not break.
"""

import shutil
from pathlib import Path

import pytest
import yaml

from aeromaps import create_process
from aeromaps.models.impacts.generic_energy_model.common.energy_use_choice import EnergyUseChoice
from aeromaps.models.impacts.generic_energy_model.common.yaml_schema import (
    PATHWAY_KEY_BLOCKS,
    PROCESS_KEY_BLOCKS,
    RESOURCE_SPECIFICATION_KEYS,
    validate_energy_carriers_data,
    validate_processes_data,
    validate_resources_data,
)
from aeromaps.utils.yaml import read_yaml_file

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPOSITORY_ROOT / "tests" / "tested_configs"
DEFAULT_ENERGY_DIR = REPOSITORY_ROOT / "resources" / "data" / "default_energy_carriers"

DEFAULT_DATA_FILES = {
    "energy_carriers_model_data_file": DEFAULT_ENERGY_DIR / "energy_carriers_data.yaml",
    "processes_model_data_file": DEFAULT_ENERGY_DIR / "processes_data.yaml",
    "resources_model_data_file": DEFAULT_ENERGY_DIR / "resources_data.yaml",
}

VALIDATORS = {
    "energy_carriers_model_data_file": validate_energy_carriers_data,
    "processes_model_data_file": validate_processes_data,
    "resources_model_data_file": validate_resources_data,
}


def _pathway(**technical):
    """A minimal, valid top-down pathway, so a test only varies the key under scrutiny."""
    return {
        "pw": {
            "name": "pw",
            "environmental_model": "top-down",
            "cost_model": "top-down",
            "aircraft_type": "dropin_fuel",
            "energy_origin": "biomass",
            "default": False,
            "inputs": {
                "mandate": {"mandate_type": "share", "mandate_share": 1.0},
                "technical": {"lhv": 44, **technical},
                "environmental": {"mean_co2_emission_factor_without_resource": 20.0},
                "economics": {"mean_mfsp_without_resource": 0.02},
            },
        }
    }


def _process(**economics):
    return {
        "proc": {
            "name": "proc",
            "inputs": {
                "technical": {"resource_names": ["res"]},
                "environmental": {"mean_co2_emission_factor_without_resource": 0.0},
                "economics": {"mean_mfsp_without_resource": 0.01, **economics},
            },
        }
    }


# --------------------------------------------------------------------------------------
# The four shapes that reached production data, and the three latent in the code.
# --------------------------------------------------------------------------------------


def test_dropped_mean_prefix_is_rejected():
    """Shape of instance #1: all twelve ATAG files, seven SAF pathways read as zero-carbon."""
    data = _pathway()
    data["pw"]["inputs"]["environmental"] = {"co2_emission_factor_without_resource": 20.0}

    with pytest.raises(ValueError, match="co2_emission_factor_without_resource"):
        validate_energy_carriers_data(data, "carriers.yaml")


def test_stray_plural_is_rejected():
    """Shape of instance #4: ``resources_names`` in ``mea_2024``, still on main until now."""
    data = _pathway(resources_names=["res"])

    with pytest.raises(ValueError, match="resources_names"):
        validate_energy_carriers_data(data, "carriers.yaml")


def test_emission_factor_under_economics_is_rejected():
    """Only the cost models register ``economics``; the emission factor would read zero."""
    data = _pathway()
    data["pw"]["inputs"]["environmental"] = {}
    data["pw"]["inputs"]["economics"]["mean_co2_emission_factor_without_resource"] = 20.0

    with pytest.raises(ValueError, match="do not register the 'economics' block"):
        validate_energy_carriers_data(data, "carriers.yaml")


def test_mfsp_under_environmental_is_rejected():
    """The mirror case: only the environmental models register ``environmental``."""
    data = _pathway()
    data["pw"]["inputs"]["economics"] = {}
    data["pw"]["inputs"]["environmental"]["mean_mfsp_without_resource"] = 0.02

    with pytest.raises(ValueError, match="do not register the 'environmental' block"):
        validate_energy_carriers_data(data, "carriers.yaml")


def test_process_subsidy_plural_is_rejected():
    """Latent instance: the template used to write a plural the cost model never read."""
    with pytest.raises(ValueError, match="mean_unit_subsidies_without_resource"):
        validate_processes_data(
            _process(mean_unit_subsidies_without_resource=0.0), "processes.yaml"
        )


def test_resource_subsidy_plural_is_rejected():
    """Latent instance: the cost model reads ``{resource}_subsidy``, not ``_subsidies``."""
    data = {"res": {"name": "res", "specifications": {"subsidies": 0.0}}}

    with pytest.raises(ValueError, match="subsidies"):
        validate_resources_data(data, "resources.yaml")


def test_misspelled_emission_index_species_is_rejected():
    """``{pathway}_emission_index_{species}`` is declared unconditionally, so it reads zero."""
    data = _pathway()
    data["pw"]["inputs"]["environmental"]["emission_index"] = {"particle_number": 1e13}

    with pytest.raises(ValueError, match="particle_number"):
        validate_energy_carriers_data(data, "carriers.yaml")


def test_consumption_for_an_undeclared_resource_is_rejected():
    """The second half of instance #4: the consumption is only read per declared resource."""
    data = _pathway(
        resource_names=["res"], resource_specific_consumption={"res": 1.0, "transport": 1.0}
    )

    with pytest.raises(ValueError, match="transport"):
        validate_energy_carriers_data(data, "carriers.yaml")


def test_unknown_block_is_rejected():
    data = _pathway()
    data["pw"]["inputs"]["policy"] = {"mandate_share": 1.0}

    with pytest.raises(ValueError, match="unknown block"):
        validate_energy_carriers_data(data, "carriers.yaml")


def test_unknown_metadata_key_is_rejected():
    data = _pathway()
    data["pw"]["environnemental_model"] = "top-down"

    with pytest.raises(ValueError, match="environnemental_model"):
        validate_energy_carriers_data(data, "carriers.yaml")


# --------------------------------------------------------------------------------------
# What must keep loading. A validator that rejects legitimate files is worse than none.
# --------------------------------------------------------------------------------------


def test_optional_inputs_may_simply_be_absent():
    """Most shipped pathways declare no emission factor; they derive it elsewhere."""
    data = _pathway()
    data["pw"]["inputs"]["environmental"] = {}
    data["pw"]["inputs"]["economics"] = None
    data["pw"]["outputs"] = None

    validate_energy_carriers_data(data, "carriers.yaml")


def test_technical_block_accepts_keys_of_both_readers():
    """``technical`` is registered by every model, so a key sitting there is still read.

    Three ``icas_2024`` pathways put ``mean_co2_emission_factor_without_resource`` under
    ``technical``. That is harmless and must not be "fixed".
    """
    data = _pathway(mean_co2_emission_factor_without_resource=88.7, mean_mfsp_without_resource=0.01)
    data["pw"]["inputs"]["environmental"] = {}
    data["pw"]["inputs"]["economics"] = {}

    validate_energy_carriers_data(data, "carriers.yaml")


@pytest.mark.parametrize("mandate_type", EnergyUseChoice.MANDATE_TYPES)
def test_both_mandate_types_are_accepted(mandate_type):
    data = _pathway()
    data["pw"]["inputs"]["mandate"] = {
        "mandate_type": mandate_type,
        f"mandate_{mandate_type}": 1.0,
    }

    validate_energy_carriers_data(data, "carriers.yaml")


def test_documented_but_unimplemented_mandate_type_is_rejected():
    """The template used to document ``"volume"``; the dispatch only ever tested for
    ``"share"`` and ``"quantity"``, so following the template gave a pathway that silently
    never deployed."""
    data = _pathway()
    data["pw"]["inputs"]["mandate"] = {"mandate_type": "volume", "mandate_share": 1.0}

    with pytest.raises(ValueError, match="not a mandate type"):
        validate_energy_carriers_data(data, "carriers.yaml")


def test_energy_use_choice_refuses_an_unknown_mandate_type():
    """The same guard one layer down, for configurations built in code rather than YAML."""

    class _Pathway:
        name = "pw"
        default = False
        mandate_type = "volume"

    class _Manager:
        @staticmethod
        def get_all():
            return [_Pathway()]

        @staticmethod
        def get_all_types(_):
            return []

        @staticmethod
        def get(**_):
            return []

    with pytest.raises(ValueError, match="Unsupported mandate type"):
        EnergyUseChoice(
            name="energy_use_choice", configuration_data={}, pathways_manager=_Manager()
        )


# --------------------------------------------------------------------------------------
# The vocabulary comes from the models, and the whole repository satisfies it.
# --------------------------------------------------------------------------------------


def test_vocabulary_is_collected_from_the_models():
    """The allow-list is derived, not transcribed: the templates disagree with the code."""
    assert PATHWAY_KEY_BLOCKS["mandate_type"] == frozenset({"mandate"})
    # Read by the environmental models only, which register 'environmental' and 'technical'.
    assert PATHWAY_KEY_BLOCKS["mean_co2_emission_factor_without_resource"] == frozenset(
        {"environmental", "technical"}
    )
    # Read by the cost models only.
    assert PATHWAY_KEY_BLOCKS["mean_mfsp_without_resource"] == frozenset({"economics", "technical"})
    # Read by models registering different blocks, so only their intersection is left.
    assert PATHWAY_KEY_BLOCKS["eis_plant_lifespan"] == frozenset({"technical"})
    assert PROCESS_KEY_BLOCKS["resource_names"] == frozenset({"technical"})
    assert {"cost", "subsidy", "tax", "availability"} <= RESOURCE_SPECIFICATION_KEYS


def _referenced_energy_files():
    """Every energy file any configuration in the repository points at."""
    referenced = {field: set() for field in DEFAULT_DATA_FILES}
    for path in sorted(REPOSITORY_ROOT.rglob("*.yaml")):
        try:
            configuration = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.Loader)
        except (yaml.YAMLError, UnicodeDecodeError):
            continue
        if not isinstance(configuration, dict) or not isinstance(configuration.get("models"), dict):
            continue
        energy = configuration["models"].get("energy")
        if not isinstance(energy, dict):
            continue
        for field, default in DEFAULT_DATA_FILES.items():
            value = energy.get(field)
            if not value:
                continue
            target = default if value == "default" else (path.parent / value).resolve()
            if target.is_file():
                referenced[field].add(target)
    return referenced


def test_every_energy_file_in_the_repository_is_accepted():
    """The sweep the rollout depends on: one offender was found, and it is fixed."""
    referenced = _referenced_energy_files()
    assert (
        sum(len(paths) for paths in referenced.values()) > 100
    ), "the configuration sweep found almost nothing; its resolution logic is broken"

    for field, paths in referenced.items():
        for path in sorted(paths):
            VALIDATORS[field](read_yaml_file(str(path)), str(path))


def test_a_corrupted_file_fails_the_process_and_not_the_run(tmp_path):
    """End-to-end: the validator runs where files are loaded, before anything computes."""
    shutil.copytree(CONFIG_DIR, tmp_path / "tested_configs")
    carriers = tmp_path / "tested_configs" / "data" / "energy_carriers_data.yaml"
    carriers.write_text(
        carriers.read_text(encoding="utf-8").replace(
            "      resource_names:", "      resources_names:", 1
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="resources_names"):
        create_process(configuration_file=tmp_path / "tested_configs" / "config_advanced.yaml")

"""Keep the energy configuration page in step with the keys the energy models read.

The accepted vocabulary of the energy YAML files is declared by the models themselves and
collected in ``yaml_schema``. The user guide documents each key with its status (required,
optional, zero if absent) and the model reading it; a key added to a model without a line in
the guide leaves users unable to tell whether they may omit it. This test lists the keys the
page does not mention.
"""

from pathlib import Path

import pytest

from aeromaps.models.impacts.generic_energy_model.common.energy_use_choice import EnergyUseChoice
from aeromaps.models.impacts.generic_energy_model.common.yaml_schema import (
    NESTED_KEYS,
    PATHWAY_KEY_BLOCKS,
    PATHWAY_METADATA_KEYS,
    PROCESS_KEY_BLOCKS,
    PROCESS_METADATA_KEYS,
    RESOURCE_METADATA_KEYS,
    RESOURCE_SPECIFICATION_KEYS,
)

ENERGY_PAGE = Path(__file__).resolve().parents[3] / "docs" / "books" / "configuration" / "energy.md"

pytestmark = pytest.mark.skipif(
    not ENERGY_PAGE.exists(), reason="documentation sources are not installed with the package"
)


def _is_documented(text, key):
    """A key counts as documented when it appears in code formatting, alone or as a parent."""
    return f"`{key}`" in text or f"`{key}." in text


def test_every_energy_key_is_documented():
    text = ENERGY_PAGE.read_text(encoding="utf-8")
    keys = (
        set(PATHWAY_METADATA_KEYS)
        | set(PATHWAY_KEY_BLOCKS)
        | set(PROCESS_METADATA_KEYS)
        | set(PROCESS_KEY_BLOCKS)
        | set(RESOURCE_METADATA_KEYS)
        | set(RESOURCE_SPECIFICATION_KEYS)
    )
    nested = {f"{parent}.{sub}" for parent, subs in NESTED_KEYS.items() for sub in subs}

    missing = sorted(key for key in keys | nested if not _is_documented(text, key))

    assert (
        not missing
    ), f"Keys read by the energy models but absent from {ENERGY_PAGE.name}: {missing}"


def test_every_mandate_type_is_documented():
    text = ENERGY_PAGE.read_text(encoding="utf-8")

    missing = [t for t in EnergyUseChoice.MANDATE_TYPES if f"`{t}`" not in text]

    assert not missing, f"Mandate types absent from {ENERGY_PAGE.name}: {missing}"

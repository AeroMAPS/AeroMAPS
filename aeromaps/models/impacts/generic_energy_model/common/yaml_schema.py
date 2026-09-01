"""
yaml_schema

================
Validation of the energy YAML files against the vocabulary the energy models actually read.

Every input the generic energy models read is looked up with ``input_data.get(key, default)``,
where ``default`` is a zero-filled series. A key that does not match — because it is misspelled,
because it lost a prefix, or because it sits in a block the reading model does not register —
therefore resolves to zero rather than raising. Zero is a physically meaningful emission factor,
cost or consumption rate, so the run completes with plausible-looking but wrong numbers.

Making the lookups strict does not work: many of these inputs are genuinely optional. The
distinguishing signal is that a misspelling produces an *unknown* key, whereas a legitimately
absent optional input produces *no* key at all. Those two cases are separable at load time,
which a strict lookup cannot do.

The accepted vocabulary is not written down here. Each energy model declares, per ``inputs``
block, the keys it consumes from that block, and this module collects those declarations: a key
is known only under the one block it is declared in. Models must agree on that block, which
:func:`_key_blocks` checks at import.

Placement is exact. Several blocks happen to be registered by more than one model, so a key
written under the wrong one would still be read — but relying on that would leave the files
without a single answer to "where does this belong", so it is rejected all the same.
"""

from aeromaps.models.impacts.energy_resources.energy_resources import (
    EnergyResourceConsumption,
    OverallResourcesConsumption,
)
from aeromaps.models.impacts.generic_energy_model.bottom_up.cost import BottomUpCost
from aeromaps.models.impacts.generic_energy_model.bottom_up.environmental import (
    BottomUpEnvironmental,
)
from aeromaps.models.impacts.generic_energy_model.bottom_up.production_capacity import (
    BottomUpCapacity,
)
from aeromaps.models.impacts.generic_energy_model.common.energy_use_choice import EnergyUseChoice
from aeromaps.models.impacts.generic_energy_model.top_down.cost import TopDownCost
from aeromaps.models.impacts.generic_energy_model.top_down.environmental import (
    TopDownEnvironmental,
)

#: The models whose declarations make up the accepted vocabulary.
ENERGY_MODELS = (
    EnergyUseChoice,
    TopDownEnvironmental,
    TopDownCost,
    BottomUpEnvironmental,
    BottomUpCost,
    BottomUpCapacity,
    EnergyResourceConsumption,
    OverallResourcesConsumption,
)

#: Pathway-level metadata, read by ``AviationEnergyCarriersFactory.create_carrier``, by
#: ``AeroMAPSProcess._instantiate_generic_energy_models`` and by the models' ``__init__``.
PATHWAY_METADATA_KEYS = frozenset(
    {
        "name",
        "environmental_model",
        "cost_model",
        "aircraft_type",
        "energy_origin",
        "default",
        "abatement_cost",
        "abatement_cost_reference",
        "compute_all_years",
        "inputs",
        "outputs",
    }
)

PROCESS_METADATA_KEYS = frozenset({"name", "inputs"})

RESOURCE_METADATA_KEYS = frozenset({"name", "origin", "specifications"})

#: Sub-keys of the nested mappings, flattened into ``{entry}_{key}_{sub_key}`` by
#: ``_flatten_dict``. ``emission_index`` species are read by the non-CO2 models as
#: ``{pathway}_emission_index_{species}``; ``availability`` by the resource models.
NESTED_KEYS = {
    "emission_index": frozenset({"h2o", "nox", "sulfur", "soot", "particles_number"}),
    "availability": frozenset({"global", "aviation_allocated_share"}),
}

#: Nested mappings whose sub-keys are resource names rather than a fixed vocabulary. A
#: consumption declared for a resource the entry does not list is never read.
RESOURCE_KEYED_MAPPINGS = ("resource_specific_consumption", "eis_resource_specific_consumption")


def _key_blocks(attribute):
    """Map each declared key to the one ``inputs`` block it must be written in.

    Parameters
    ----------
    attribute : str
        Name of the model attribute mapping a block to the keys the model consumes from it.

    Returns
    -------
    dict
        Key to its block.

    Raises
    ------
    ValueError
        If two models place the same key in different blocks. There would then be no single
        right answer for a configuration file to give.
    """
    blocks = {}
    origin = {}
    for model in ENERGY_MODELS:
        for block, keys in getattr(model, attribute, {}).items():
            for key in keys:
                if blocks.setdefault(key, block) != block:
                    raise ValueError(
                        f"{model.__name__} declares '{key}' under '{block}' while "
                        f"{origin[key]} declares it under '{blocks[key]}'."
                    )
                origin[key] = model.__name__
    return blocks


PATHWAY_KEY_BLOCKS = _key_blocks("PATHWAY_INPUT_KEYS")

PROCESS_KEY_BLOCKS = _key_blocks("PROCESS_INPUT_KEYS")

#: Resources have no blocks: their ``specifications`` mapping is flattened as a whole.
RESOURCE_SPECIFICATION_KEYS = frozenset().union(
    *(frozenset(getattr(model, "RESOURCE_INPUT_KEYS", ())) for model in ENERGY_MODELS)
)


def _known_blocks(key_blocks):
    """Return the set of block names any model declares keys in."""
    return frozenset(key_blocks.values())


def _accepted_in(block, key_blocks):
    """Return the sorted keys that belong in ``block``."""
    return sorted(key for key, declared in key_blocks.items() if declared == block)


def _check_entry_keys(entry, accepted, location, problems):
    """Record a problem for every key of ``entry`` outside ``accepted``."""
    for key in entry:
        if key not in accepted:
            problems.append(
                f"{location}.{key}: unknown key. Accepted here: {', '.join(sorted(accepted))}."
            )


def _check_nested(key, value, entry_name, location, resource_names, problems):
    """Validate the sub-keys of the nested mappings of a block."""
    if key in NESTED_KEYS:
        if not isinstance(value, dict):
            problems.append(f"{location}.{key}: expected a mapping, got {type(value).__name__}.")
            return
        for sub_key in value:
            if sub_key not in NESTED_KEYS[key]:
                problems.append(
                    f"{location}.{key}.{sub_key}: unknown key. Accepted here: "
                    f"{', '.join(sorted(NESTED_KEYS[key]))}."
                )
    elif key in RESOURCE_KEYED_MAPPINGS and isinstance(value, dict):
        for sub_key in value:
            if sub_key not in resource_names:
                problems.append(
                    f"{location}.{key}.{sub_key}: '{sub_key}' is not one of the resources "
                    f"'{entry_name}' declares in 'resource_names', so this consumption is never "
                    "read."
                )


def _check_blocks(entry, entry_name, key_blocks, file_name, problems):
    """Validate the ``inputs`` blocks of a pathway or a process entry."""
    inputs = entry.get("inputs")
    if inputs is None:
        return
    if not isinstance(inputs, dict):
        problems.append(f"{entry_name}: 'inputs' should be a mapping, got {type(inputs).__name__}.")
        return

    known_blocks = _known_blocks(key_blocks)
    technical = inputs.get("technical") or {}
    resource_names = (
        set(technical.get("resource_names") or []) if isinstance(technical, dict) else set()
    )

    for block, content in inputs.items():
        location = f"{entry_name}.inputs.{block}"
        if block not in known_blocks:
            problems.append(
                f"{location}: unknown block. Accepted blocks: {', '.join(sorted(known_blocks))}."
            )
            continue
        if content is None:
            continue
        if not isinstance(content, dict):
            problems.append(f"{location}: expected a mapping, got {type(content).__name__}.")
            continue
        for key, value in content.items():
            declared_block = key_blocks.get(key)
            if declared_block is None:
                problems.append(
                    f"{location}.{key}: unknown key, no energy model reads it. Accepted in "
                    f"'{block}': {', '.join(_accepted_in(block, key_blocks))}."
                )
            elif declared_block != block:
                problems.append(
                    f"{location}.{key}: this key belongs under '{declared_block}', not "
                    f"'{block}'."
                )
            else:
                _check_nested(key, value, entry_name, location, resource_names, problems)


def _raise(problems, kind, file_name):
    """Raise a single error listing every problem found in a file."""
    if problems:
        listed = "\n  - ".join(problems)
        raise ValueError(
            f"Invalid {kind} configuration in '{file_name}'. Keys that no energy model reads are "
            f"silently taken as zero, so they are rejected here:\n  - {listed}"
        )


def validate_energy_carriers_data(data, file_name):
    """Validate an energy carriers configuration file.

    Parameters
    ----------
    data : dict
        Contents of the energy carriers YAML file, one entry per pathway.
    file_name : str
        Path of the file, used in the error message.

    Raises
    ------
    ValueError
        If a pathway declares a key or a block that no energy model reads, or a key in a block
        whose reading model does not register it.
    """
    problems = []
    for pathway_name, pathway in (data or {}).items():
        if not isinstance(pathway, dict):
            continue
        _check_entry_keys(pathway, PATHWAY_METADATA_KEYS, pathway_name, problems)
        _check_blocks(pathway, pathway_name, PATHWAY_KEY_BLOCKS, file_name, problems)
        mandate = (pathway.get("inputs") or {}).get("mandate") or {}
        mandate_type = mandate.get("mandate_type") if isinstance(mandate, dict) else None
        if mandate_type is not None and mandate_type not in EnergyUseChoice.MANDATE_TYPES:
            problems.append(
                f"{pathway_name}.inputs.mandate.mandate_type: '{mandate_type}' is not a mandate "
                f"type. Accepted: {', '.join(repr(t) for t in EnergyUseChoice.MANDATE_TYPES)}."
            )
    _raise(problems, "energy carriers", file_name)


def validate_processes_data(data, file_name):
    """Validate an energy processes configuration file.

    Parameters
    ----------
    data : dict
        Contents of the processes YAML file, one entry per process.
    file_name : str
        Path of the file, used in the error message.

    Raises
    ------
    ValueError
        If a process declares a key or a block that no energy model reads, or a key in a block
        whose reading model does not register it.
    """
    problems = []
    for process_name, process in (data or {}).items():
        if not isinstance(process, dict):
            continue
        _check_entry_keys(process, PROCESS_METADATA_KEYS, process_name, problems)
        _check_blocks(process, process_name, PROCESS_KEY_BLOCKS, file_name, problems)
    _raise(problems, "energy processes", file_name)


def validate_resources_data(data, file_name):
    """Validate an energy resources configuration file.

    Parameters
    ----------
    data : dict
        Contents of the resources YAML file, one entry per resource.
    file_name : str
        Path of the file, used in the error message.

    Raises
    ------
    ValueError
        If a resource declares a specification that no energy model reads.
    """
    problems = []
    for resource_name, resource in (data or {}).items():
        if not isinstance(resource, dict):
            continue
        _check_entry_keys(resource, RESOURCE_METADATA_KEYS, resource_name, problems)
        specifications = resource.get("specifications")
        if specifications is None:
            continue
        location = f"{resource_name}.specifications"
        if not isinstance(specifications, dict):
            problems.append(f"{location}: expected a mapping, got {type(specifications).__name__}.")
            continue
        for key, value in specifications.items():
            if key not in RESOURCE_SPECIFICATION_KEYS:
                problems.append(
                    f"{location}.{key}: unknown key, no energy model reads it. Accepted: "
                    f"{', '.join(sorted(RESOURCE_SPECIFICATION_KEYS))}."
                )
            else:
                _check_nested(key, value, resource_name, location, set(), problems)
    _raise(problems, "energy resources", file_name)

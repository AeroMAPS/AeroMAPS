"""Serialising an AeroMapsCustomDataType through PyYAML's dumpers.

``add_representer`` registers on ``yaml.Dumper`` alone. ``write_yaml_file`` uses
``yaml.dump``, so that is the one that matters in practice, but a caller reaching
for ``safe_dump`` would otherwise hit a RepresenterError on a type the library
knows perfectly well how to write. Both dumpers are registered, and this pins that.

Only the dumping side is covered: the constructor stays on the default ``Loader``,
matching ``read_yaml_file``, so ``safe_load`` still does not know the tag.
"""

import yaml

from aeromaps.models.base import AeroMapsCustomDataType
from aeromaps.utils.yaml import read_yaml_file, write_yaml_file


def _sample():
    return AeroMapsCustomDataType({"years": [2020, 2050], "values": [1.0, 2.0], "method": "linear"})


def test_safe_dump_emits_the_tag():
    text = yaml.safe_dump({"pathway": _sample()})
    assert "!AeroMapsCustomDataType" in text
    assert "years" in text and "values" in text


def test_plain_dump_emits_the_tag():
    text = yaml.dump({"pathway": _sample()})
    assert "!AeroMapsCustomDataType" in text


def test_write_then_read_round_trips(tmp_path):
    """The pairing the package actually uses: yaml.dump out, yaml.Loader back in."""
    path = tmp_path / "carriers.yaml"
    write_yaml_file({"pathway": _sample()}, str(path))
    restored = read_yaml_file(str(path))["pathway"]
    assert isinstance(restored, AeroMapsCustomDataType)
    assert list(restored.years) == [2020, 2050]
    assert list(restored.values) == [1.0, 2.0]
    assert restored.method == "linear"

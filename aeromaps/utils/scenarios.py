"""Find the reference scenarios shipped with AeroMAPS, and run them in a sandbox.

A scenario here is a configuration and the input files it names: the definition of
a published trajectory, not its results. Those live with the publication that drew
conclusions from them, because they are large and because a result belongs to the
work that reported it.

Scenario folders sit flat under ``resources/scenarios`` rather than nested by
category. The configurations address their neighbours with relative paths -- most
of them reach a shared ``markets/`` through ``../../`` -- and a directory per
category would have changed the depth of every one of those. Category and tags are
metadata instead, which also lets a scenario belong to several groupings at once:
``category`` says who produced the scenario, ``tags`` cut across that, so every
coupled-demand study can be asked for regardless of family.

Running a scenario copies it somewhere writable first. The notebooks regenerate
derived inputs as they go -- tank-to-wake twins, share mandates -- and write their
outputs beside the configuration, so running one in place edits the installed
package. :func:`prepare_scenario` hands back a copy and leaves the original alone.
"""

import re
import shutil
from dataclasses import dataclass, field
from difflib import get_close_matches
from importlib.resources import files
from pathlib import Path
from typing import List, Optional

from aeromaps.utils.yaml import read_yaml_file

# The shared market definitions several scenarios reach through ``../../markets``.
# Not a scenario itself, and travels with every sandbox for that reason.
SHARED_DIRS = ("markets",)

METADATA_FILE = "scenario.yaml"

# A folder is a scenario if it holds configurations under one of these names.
CONFIG_DIRS = ("config_files", "configs")


@dataclass
class Scenario:
    """One reference scenario, as declared by its folder and metadata file."""

    folder: str
    path: Path
    name: str
    category: str = "uncategorised"
    tags: List[str] = field(default_factory=list)
    description: str = ""

    @property
    def config_dir(self) -> Path:
        for candidate in CONFIG_DIRS:
            if (self.path / candidate).is_dir():
                return self.path / candidate
        raise FileNotFoundError(f"{self.folder} holds no configuration directory")

    def configs(self) -> List[Path]:
        """Every configuration file in the scenario, sorted, recursing into groups."""
        return sorted(self.config_dir.rglob("*.yaml"))


def scenarios_root() -> Path:
    """The packaged directory holding the reference scenarios."""
    return Path(str(files("aeromaps") / "resources" / "scenarios"))


def _read(folder: Path) -> Scenario:
    """Build a scenario record, tolerating a folder with no metadata file.

    A half-filled folder should still be discoverable: a scenario someone has just
    dropped in is exactly when listing it is most useful.
    """
    meta = {}
    metadata_path = folder / METADATA_FILE
    if metadata_path.is_file():
        meta = read_yaml_file(str(metadata_path)) or {}
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return Scenario(
        folder=folder.name,
        path=folder,
        name=meta.get("name") or folder.name.replace("_", " ").title(),
        category=meta.get("category") or "uncategorised",
        tags=[str(tag) for tag in tags],
        description=meta.get("description") or "",
    )


def list_scenarios(category: Optional[str] = None, tag: Optional[str] = None) -> List[Scenario]:
    """Every packaged scenario, optionally filtered by category or tag.

    Matching is case-insensitive on both, since these are labels written by hand.
    """
    found = []
    for folder in sorted(scenarios_root().iterdir()):
        if not folder.is_dir() or folder.name in SHARED_DIRS:
            continue
        if not any((folder / candidate).is_dir() for candidate in CONFIG_DIRS):
            continue
        found.append(_read(folder))
    if category is not None:
        found = [s for s in found if s.category.lower() == category.lower()]
    if tag is not None:
        wanted = tag.lower()
        found = [s for s in found if any(t.lower() == wanted for t in s.tags)]
    return found


def find_scenario(key: str) -> Scenario:
    """One scenario, by folder name or by display name.

    Raises with the near misses rather than a bare lookup error: the caller has
    almost always mistyped a name that exists.
    """
    available = list_scenarios()
    for scenario in available:
        if key in (scenario.folder, scenario.name):
            return scenario
    for scenario in available:  # a second pass, so an exact match always wins
        if key.lower() in (scenario.folder.lower(), scenario.name.lower()):
            return scenario
    known = [s.folder for s in available]
    suggestions = get_close_matches(key, known, n=3)
    hint = f" Did you mean {', '.join(suggestions)}?" if suggestions else ""
    raise KeyError(f"no scenario {key!r} in {scenarios_root()}.{hint} Known: {', '.join(known)}")


# A configuration reaching a sibling scenario, as ``../../<folder>/``. Two of the
# ATAG scenarios do: the climate analysis reads energy files from the editions it
# perturbs, and F1 borrows the aggregated edition's S0 carriers.
_SIBLING = re.compile(r"\.\./\.\./([A-Za-z0-9_]+)/")


def _siblings(scenario: "Scenario", known) -> List[str]:
    """Folders this scenario's configurations reach into, besides the shared ones."""
    wanted = set()
    for config in scenario.configs():
        for match in _SIBLING.findall(config.read_text(encoding="utf-8")):
            if match in known and match != scenario.folder:
                wanted.add(match)
    return sorted(wanted)


def prepare_scenario(key: str, workdir="workdir", overwrite: bool = False) -> Path:
    """Copy a scenario into a writable sandbox and return its path there.

    The shared directories come too, at the same depth, so the configurations'
    relative paths resolve inside the sandbox exactly as they do in the package.
    Outputs and regenerated inputs then land in the copy, which is the point: a
    notebook run leaves the installed package untouched.

    Parameters
    ----------
    key : str
        Folder or display name, as accepted by :func:`find_scenario`.
    workdir : path-like, optional
        Directory to copy into, created if absent. Defaults to ``workdir`` in the
        current directory.
    overwrite : bool, optional
        Replace an existing copy. Off by default so a second run of a notebook
        cannot silently discard edits made in the sandbox.
    """
    scenario = find_scenario(key)
    destination = Path(workdir) / scenario.folder
    if destination.exists():
        if not overwrite:
            return destination
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(scenario.path, destination)

    for shared in SHARED_DIRS:
        source = scenarios_root() / shared
        if source.is_dir():
            shutil.copytree(source, destination.parent / shared, dirs_exist_ok=True)

    # Scenarios that read a sibling's input files need that sibling present at the
    # same relative depth, or the copy is a sandbox the configurations cannot run in.
    known = {s.folder for s in list_scenarios()}
    for folder in _siblings(scenario, known):
        beside = destination.parent / folder
        if not beside.exists():
            shutil.copytree(scenarios_root() / folder, beside)
    return destination


def publish_outputs(sandbox_scenario, destination, patterns=("data_outputs/*.json",)) -> List[Path]:
    """Copy results out of a sandbox and into the publication that reports them.

    The maintainer's half of the sandbox: a run produces its outputs in the
    workdir, and refreshing what a paper reads is then a deliberate step rather
    than a side effect of opening a notebook.
    """
    sandbox_scenario, destination = Path(sandbox_scenario), Path(destination)
    written = []
    for pattern in patterns:
        for source in sorted(sandbox_scenario.glob(pattern)):
            target = destination / source.relative_to(sandbox_scenario)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            written.append(target)
    return written

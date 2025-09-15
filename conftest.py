# conftest.py
import pytest
import os
from IPython import get_ipython
from IPython.display import clear_output

# patterns relative to the project root (use forward slashes)
EXCLUDE_PATTERNS = [
    "aeromaps/notebooks/publications/icas_2024/examples_life_cycle_assessment-icas.ipynb",
    "aeromaps/notebooks/publications/tsas_2025/examples_life_cycle_assessment-tsas.ipynb",
    "aeromaps/notebooks/publications/optimisation",  # directory
    "aeromaps/notebooks/private",  # directory
    ".ipynb_checkpoints",  # checkpoint dirs anywhere
]


def _is_excluded(rel_path: str) -> bool:
    """Check if rel_path (forward-slash normalized) matches any exclude pattern."""
    for pat in EXCLUDE_PATTERNS:
        if pat.endswith("/"):
            pat = pat.rstrip("/")
        # directory patterns: if pat is contained anywhere in rel_path -> exclude
        if (
            rel_path == pat
            or rel_path.endswith(pat)
            or (("/" + pat + "/") in ("/" + rel_path + "/"))
            or (rel_path.startswith(pat + "/"))
        ):
            return True
        # checkpoint directories partial match
        if pat == ".ipynb_checkpoints" and ".ipynb_checkpoints" in rel_path:
            return True
    return False


def pytest_collection_modifyitems(config, items):
    """
    Remove collected items whose path matches EXCLUDE_PATTERNS.
    This is robust to working-directory differences because we compute paths
    relative to the pytest rootdir (config.rootpath).
    """
    root = str(config.rootpath)  # usually the project root where pytest.ini sits
    root = os.path.abspath(root).replace(os.sep, "/")

    kept = []
    deselected = []

    for item in items:
        # absolute path of the collected node
        full = os.path.abspath(str(item.fspath)).replace(os.sep, "/")
        try:
            rel = os.path.relpath(full, root).replace(os.sep, "/")
        except Exception:
            rel = full

        if _is_excluded(rel):
            deselected.append(item)
        else:
            kept.append(item)

    if deselected:
        items[:] = kept
        config.hook.pytest_deselected(items=deselected)


@pytest.fixture(autouse=True, scope="module")
def clean_notebook_state():
    """
    Automatically clear variables and outputs *after each notebook*
    when pytest is executing them.
    """
    yield
    if "PYTEST_CURRENT_TEST" in os.environ:
        ip = get_ipython()
        if ip is not None:
            ip.magic("reset -f")
        clear_output(wait=False)

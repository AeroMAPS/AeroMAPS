# conftest.py
import os

# ------------------- Notebook exclusion -------------------
EXCLUDE_PATTERNS = [
    ".ipynb_checkpoints",
    "aeromaps/notebooks/private",
    "aeromaps/notebooks/publications/optimisation",
    "aeromaps/notebooks/publications/icas_2024/examples_life_cycle_assessment-icas.ipynb",
    "aeromaps/notebooks/publications/tsas_2025/examples_life_cycle_assessment-tsas.ipynb",
]


def _is_excluded(rel_path: str) -> bool:
    for pat in EXCLUDE_PATTERNS:
        if pat in rel_path:
            print(f"[conftest.py] Excluding: {rel_path} (matched {pat})")
            return True
    return False


def pytest_collection_modifyitems(config, items):
    """Deselect items matching EXCLUDE_PATTERNS"""
    print("\n[conftest.py] Modifying collected test items...")
    root = str(config.rootpath).replace(os.sep, "/")
    kept, deselected = [], []
    for item in items:
        full = str(item.fspath).replace(os.sep, "/")
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
        print(f"[conftest.py] Deselected {len(deselected)} items.")
    else:
        print("[conftest.py] No items deselected.")

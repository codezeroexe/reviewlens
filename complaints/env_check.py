"""Print which optional packages import. Phase 3 uses fallbacks when missing."""

import importlib

PACKAGES = ["sentence_transformers", "hdbscan", "sklearn", "umap"]


def check() -> dict[str, bool]:
    status = {}
    for name in PACKAGES:
        try:
            importlib.import_module(name)
            status[name] = True
        except ImportError:
            status[name] = False
    return status


if __name__ == "__main__":
    for name, ok in check().items():
        print(f"{name}: {'available' if ok else 'MISSING (fallback used)'}")

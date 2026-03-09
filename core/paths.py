from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """Return repository root based on this file location."""
    return Path(__file__).resolve().parent.parent


def project_path(relative_path: str) -> Path:
    """Resolve a repo-relative path to absolute path."""
    return project_root() / relative_path


from __future__ import annotations

import os
from pathlib import Path

from app.config import settings
from app.errors import UnsafePath

_BLOCKED = ("\x00",)


def allowed_roots() -> list[Path]:
    roots = [Path(r).resolve() for r in settings.file_roots]
    roots.append(settings.data_dir.resolve())
    return roots


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def resolve_managed(raw: str) -> Path:
    if not raw or any(token in raw for token in _BLOCKED):
        raise UnsafePath("Invalid path")

    candidate = Path(os.path.normpath(raw))
    if not candidate.is_absolute():
        raise UnsafePath("Path must be absolute")

    resolved = Path(os.path.realpath(candidate))
    for root in allowed_roots():
        if resolved == root or is_within(resolved, root):
            return resolved
    raise UnsafePath("Path is outside the managed roots")


def resolve_for_create(raw: str) -> Path:
    candidate = Path(os.path.normpath(raw))
    if not candidate.is_absolute():
        raise UnsafePath("Path must be absolute")
    parent = resolve_managed(str(candidate.parent))
    return parent / candidate.name


def safe_site_name(name: str) -> str:
    cleaned = name.strip().lower()
    if not cleaned or len(cleaned) > 253:
        raise UnsafePath("Invalid site name")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789.-_")
    if not set(cleaned) <= allowed:
        raise UnsafePath("Site name contains invalid characters")
    if cleaned.startswith((".", "-")) or ".." in cleaned:
        raise UnsafePath("Invalid site name")
    return cleaned


def safe_identifier(name: str, limit: int = 64) -> str:
    cleaned = name.strip()
    if not cleaned or len(cleaned) > limit:
        raise UnsafePath("Invalid identifier")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
    if not set(cleaned) <= allowed:
        raise UnsafePath("Identifier may only contain letters, digits and underscore")
    return cleaned

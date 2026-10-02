from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import Conflict, NotFound, PanelError
from app.models import RecycleItem
from app.services.paths import allowed_roots, resolve_managed


def enabled() -> bool:
    return settings.recycle_bin


def list_items(session: Session, limit: int = 500) -> list[RecycleItem]:
    return list(
        session.exec(select(RecycleItem).order_by(RecycleItem.id.desc()).limit(limit)).all()
    )


def get_item(session: Session, item_id: int) -> RecycleItem:
    item = session.get(RecycleItem, item_id)
    if not item:
        raise NotFound("Recycle bin entry not found")
    return item


def _directory_size(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        try:
            if child.is_file() and not child.is_symlink():
                total += child.stat().st_size
        except OSError:
            continue
    return total


def move_to_bin(session: Session, raw_path: str) -> RecycleItem:
    """Move a path into the bin instead of unlinking it."""
    path = resolve_managed(raw_path)
    if path in allowed_roots():
        raise PanelError("Refusing to bin a managed root")
    # realpath happily resolves a name that is not there, so check before stat.
    if not path.exists() and not path.is_symlink():
        raise NotFound(f"{path} does not exist")

    settings.ensure_dirs()
    is_dir = path.is_dir() and not path.is_symlink()
    size = _directory_size(path) if is_dir else path.lstat().st_size

    stored = settings.recycle_dir / f"{uuid.uuid4().hex}_{path.name}"
    shutil.move(str(path), str(stored))

    item = RecycleItem(
        original_path=str(path), stored_path=str(stored), is_dir=is_dir, size=size
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def restore(session: Session, item_id: int, overwrite: bool = False) -> dict:
    item = get_item(session, item_id)
    stored = Path(item.stored_path)
    if not stored.exists():
        raise NotFound("The stored copy is gone from disk")

    target = Path(item.original_path)
    if target.exists():
        if not overwrite:
            raise Conflict(f"{target} exists again; restore with overwrite to replace it")
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(stored), str(target))
    session.delete(item)
    session.commit()
    return {"restored": str(target)}


def purge(session: Session, item_id: int) -> None:
    item = get_item(session, item_id)
    stored = Path(item.stored_path)
    if stored.is_dir() and not stored.is_symlink():
        shutil.rmtree(stored, ignore_errors=True)
    else:
        stored.unlink(missing_ok=True)
    session.delete(item)
    session.commit()


def _orphans(session: Session) -> list[Path]:
    """Stored copies with no row left: dropped databases, manual meddling."""
    if not settings.recycle_dir.is_dir():
        return []
    tracked = {item.stored_path for item in list_items(session, limit=100000)}
    return [path for path in settings.recycle_dir.iterdir() if str(path) not in tracked]


def empty(session: Session) -> int:
    items = list_items(session, limit=100000)
    for item in items:
        purge(session, item.id)

    for path in _orphans(session):
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
    return len(items)


def usage(session: Session) -> dict:
    items = list_items(session, limit=100000)
    orphans = _orphans(session)
    orphan_bytes = 0
    for path in orphans:
        try:
            orphan_bytes += _directory_size(path) if path.is_dir() else path.stat().st_size
        except OSError:
            continue

    return {
        "enabled": enabled(),
        "count": len(items),
        "bytes": sum(item.size for item in items),
        # Reported separately so the number matches what `du` says.
        "orphans": len(orphans),
        "orphan_bytes": orphan_bytes,
        "path": str(settings.recycle_dir),
    }

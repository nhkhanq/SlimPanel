from __future__ import annotations

import shutil
import tarfile
import tempfile
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import NotFound, PanelError
from app.models import BackupRecord, Database, Site, utcnow
from app.services import mysql, shell
from app.services.sites import get_site


def list_records(session: Session, kind: str = "") -> list[BackupRecord]:
    statement = select(BackupRecord).order_by(BackupRecord.id.desc())
    if kind:
        statement = statement.where(BackupRecord.kind == kind)
    return list(session.exec(statement).all())


def backup_site(session: Session, site_id: int) -> BackupRecord:
    site = get_site(session, site_id)
    root = Path(site.root)
    if not root.is_dir():
        raise NotFound("Site root not found")

    settings.ensure_dirs()
    stamp = utcnow().strftime("%Y%m%d%H%M%S")
    target = settings.backup_dir / f"site_{site.name}_{stamp}.tar.gz"

    with tarfile.open(target, "w:gz") as archive:
        archive.add(root, arcname=site.name)

    record = BackupRecord(
        kind="site", target=site.name, filename=str(target), size=target.stat().st_size
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def backup_database(session: Session, db_id: int) -> BackupRecord:
    return mysql.backup(session, db_id)


def get_record(session: Session, record_id: int) -> BackupRecord:
    record = session.get(BackupRecord, record_id)
    if not record:
        raise NotFound("Backup not found")
    return record


def delete_record(session: Session, record_id: int) -> None:
    record = get_record(session, record_id)
    Path(record.filename).unlink(missing_ok=True)
    session.delete(record)
    session.commit()


def resolve_file(session: Session, record_id: int) -> Path:
    record = get_record(session, record_id)
    path = Path(record.filename)
    if not path.is_file():
        raise NotFound("Backup file is missing on disk")
    return path


def prune(session: Session, keep: int = 7, kind: str = "") -> int:
    records = list_records(session, kind)
    removed = 0
    for record in records[keep:]:
        delete_record(session, record.id)
        removed += 1
    return removed


def backup_all(session: Session, upload: bool = False) -> dict:
    """One archive per site and per database, the way a nightly job wants it."""
    from app.services import storage

    records: list[BackupRecord] = []
    errors: list[dict] = []

    for site in session.exec(select(Site)).all():
        try:
            records.append(backup_site(session, site.id))
        except PanelError as exc:
            errors.append({"kind": "site", "target": site.name, "error": exc.message})

    for database in session.exec(select(Database)).all():
        try:
            records.append(backup_database(session, database.id))
        except PanelError as exc:
            errors.append({"kind": "database", "target": database.name, "error": exc.message})

    uploads = []
    if upload:
        for record in records:
            uploads += storage.fan_out(session, record.filename)

    return {
        "records": [record.model_dump() for record in records],
        "errors": errors,
        "uploads": uploads,
    }


def restore_site(session: Session, record_id: int, site_id: int) -> dict:
    """Unpack a site tarball back over its root, keeping a safety copy first."""
    record = get_record(session, record_id)
    if record.kind != "site":
        raise PanelError("That backup is not a site archive")

    archive = resolve_file(session, record_id)
    site = get_site(session, site_id)
    root = Path(site.root)
    root.mkdir(parents=True, exist_ok=True)

    stamp = utcnow().strftime("%Y%m%d%H%M%S")
    safety = settings.backup_dir / f"pre-restore_{site.name}_{stamp}.tar.gz"
    with tarfile.open(safety, "w:gz") as handle:
        handle.add(root, arcname=site.name)

    with tempfile.TemporaryDirectory(dir=str(settings.backup_dir)) as staging:
        staging_path = Path(staging)
        with tarfile.open(archive) as handle:
            resolved = staging_path.resolve()
            for member in handle.getmembers():
                if member.issym() or member.islnk():
                    continue
                destination = (staging_path / member.name).resolve()
                if destination != resolved and resolved not in destination.parents:
                    raise PanelError(f"Archive entry escapes the staging directory: {member.name}")
            handle.extractall(staging_path)

        # Most archives carry a single top-level directory named after the site.
        candidates = [child for child in staging_path.iterdir()]
        source = candidates[0] if len(candidates) == 1 and candidates[0].is_dir() else staging_path

        for child in root.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
        for child in source.iterdir():
            shutil.move(str(child), str(root / child.name))

    return {"site": site.name, "archive": Path(record.filename).name, "safety_copy": str(safety)}


def restore_database(session: Session, record_id: int, db_id: int) -> dict:
    record = get_record(session, record_id)
    if record.kind not in {"database", "postgres"}:
        raise PanelError("That backup is not a database dump")

    path = resolve_file(session, record_id)
    database = mysql.get_record(session, db_id)

    if record.kind == "postgres":
        raise PanelError("Restore a PostgreSQL dump with psql; the panel only restores MySQL")

    result = shell.run(
        mysql.base_argv(settings.mysql_bin) + [database.name],
        stdin=path.read_text(errors="replace"),
        timeout=3600,
    )
    if not result.ok:
        raise PanelError("Restore failed", result.output[:2000])
    return {"database": database.name, "archive": path.name}


def usage(session: Session) -> dict:
    records = list_records(session)
    by_kind: dict[str, dict] = {}
    for record in records:
        entry = by_kind.setdefault(record.kind, {"kind": record.kind, "count": 0, "bytes": 0})
        entry["count"] += 1
        entry["bytes"] += record.size

    on_disk = 0
    if settings.backup_dir.is_dir():
        for path in settings.backup_dir.glob("*"):
            if path.is_file():
                on_disk += path.stat().st_size

    return {
        "path": str(settings.backup_dir),
        "records": len(records),
        "bytes": sum(record.size for record in records),
        "on_disk": on_disk,
        "by_kind": list(by_kind.values()),
    }

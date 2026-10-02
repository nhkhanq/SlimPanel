from __future__ import annotations

import tarfile
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import NotFound
from app.models import BackupRecord, utcnow
from app.services import mysql
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

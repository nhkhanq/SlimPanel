from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.deps import SessionDep, UserDep, audit
from app.models import BackupRecord
from app.schemas import Ok
from app.services import backup

router = APIRouter(prefix="/backups", tags=["backups"])


@router.get("", response_model=list[BackupRecord])
def list_backups(session: SessionDep, user: UserDep, kind: str = ""):
    return backup.list_records(session, kind)


@router.post("/site/{site_id}", response_model=BackupRecord)
def backup_site(site_id: int, session: SessionDep, user: UserDep):
    record = backup.backup_site(session, site_id)
    audit(session, user, "backup.site", record.target)
    return record


@router.post("/database/{db_id}", response_model=BackupRecord)
def backup_database(db_id: int, session: SessionDep, user: UserDep):
    record = backup.backup_database(session, db_id)
    audit(session, user, "backup.database", record.target)
    return record


@router.get("/{record_id}/download")
def download(record_id: int, session: SessionDep, user: UserDep):
    path = backup.resolve_file(session, record_id)
    return FileResponse(path, filename=path.name)


@router.delete("/{record_id}", response_model=Ok)
def delete(record_id: int, session: SessionDep, user: UserDep):
    record = backup.get_record(session, record_id)
    name = record.filename
    backup.delete_record(session, record_id)
    audit(session, user, "backup.delete", name)
    return Ok(message="Backup removed")


@router.post("/prune", response_model=Ok)
def prune(session: SessionDep, user: UserDep, keep: int = 7, kind: str = ""):
    removed = backup.prune(session, keep, kind)
    audit(session, user, "backup.prune", kind, detail=f"removed={removed}")
    return Ok(message=f"Removed {removed} backups")

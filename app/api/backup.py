from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.deps import SessionDep, UserDep, audit
from app.models import BackupRecord
from app.schemas import Ok
from app.services import backup, storage

router = APIRouter(prefix="/backups", tags=["backups"])


class TargetIn(BaseModel):
    name: str
    kind: str
    config: dict


class TargetUpdate(BaseModel):
    name: str = ""
    config: dict | None = None
    enabled: bool | None = None


@router.get("", response_model=list[BackupRecord])
def list_backups(session: SessionDep, user: UserDep, kind: str = ""):
    return backup.list_records(session, kind)


@router.get("/targets/kinds")
def target_kinds(user: UserDep):
    return storage.kinds()


@router.get("/targets")
def list_targets(session: SessionDep, user: UserDep):
    return storage.list_targets(session)


@router.post("/targets")
def create_target(payload: TargetIn, session: SessionDep, user: UserDep):
    target = storage.create_target(session, payload.name, payload.kind, payload.config)
    audit(session, user, "backup.target.create", target.name, detail=target.kind)
    return target.model_dump(exclude={"config"})


@router.patch("/targets/{target_id}")
def update_target(target_id: int, payload: TargetUpdate, session: SessionDep, user: UserDep):
    target = storage.update_target(session, target_id, payload.name, payload.config, payload.enabled)
    audit(session, user, "backup.target.update", target.name)
    return target.model_dump(exclude={"config"})


@router.post("/targets/{target_id}/test")
def test_target(target_id: int, session: SessionDep, user: UserDep):
    result = storage.test_target(session, target_id)
    audit(session, user, "backup.target.test", str(target_id))
    return result


@router.delete("/targets/{target_id}", response_model=Ok)
def delete_target(target_id: int, session: SessionDep, user: UserDep):
    target = storage.get_target(session, target_id)
    name = target.name
    storage.delete_target(session, target_id)
    audit(session, user, "backup.target.delete", name)
    return Ok(message=f"Target {name} removed")


@router.post("/site/{site_id}", response_model=BackupRecord)
def backup_site(site_id: int, session: SessionDep, user: UserDep, upload: bool = False):
    record = backup.backup_site(session, site_id)
    audit(session, user, "backup.site", record.target)
    if upload:
        storage.fan_out(session, record.filename)
    return record


@router.post("/database/{db_id}", response_model=BackupRecord)
def backup_database(db_id: int, session: SessionDep, user: UserDep, upload: bool = False):
    record = backup.backup_database(session, db_id)
    audit(session, user, "backup.database", record.target)
    if upload:
        storage.fan_out(session, record.filename)
    return record


@router.post("/all")
def backup_everything(session: SessionDep, user: UserDep, upload: bool = False):
    result = backup.backup_all(session, upload=upload)
    audit(session, user, "backup.all", detail=f"{len(result['records'])} archives")
    return result


@router.post("/{record_id}/upload/{target_id}")
def upload_backup(record_id: int, target_id: int, session: SessionDep, user: UserDep):
    record = backup.get_record(session, record_id)
    task = storage.upload_async(session, target_id, record.filename)
    audit(session, user, "backup.upload", record.filename, detail=f"task={task.id}")
    return task


@router.get("/{record_id}/download")
def download(record_id: int, session: SessionDep, user: UserDep):
    path = backup.resolve_file(session, record_id)
    return FileResponse(path, filename=path.name)


@router.post("/{record_id}/restore-site/{site_id}", response_model=Ok)
def restore_site(record_id: int, site_id: int, session: SessionDep, user: UserDep):
    result = backup.restore_site(session, record_id, site_id)
    audit(session, user, "backup.restore.site", result["site"], detail=result["archive"])
    return Ok(message=f"Restored {result['site']} from {result['archive']}")


@router.post("/{record_id}/restore-database/{db_id}", response_model=Ok)
def restore_database(record_id: int, db_id: int, session: SessionDep, user: UserDep):
    result = backup.restore_database(session, record_id, db_id)
    audit(session, user, "backup.restore.database", result["database"])
    return Ok(message=f"Restored {result['database']}")


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

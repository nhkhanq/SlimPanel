from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import SessionDep, UserDep, audit
from app.models import FtpUser
from app.schemas import Ok
from app.services import ftp

router = APIRouter(prefix="/ftp", tags=["ftp"])


class FtpCreate(BaseModel):
    username: str
    password: str = ""
    home: str = ""
    quota_mb: int = 0
    note: str = ""


class PasswordIn(BaseModel):
    password: str = ""


class HomeIn(BaseModel):
    home: str


class QuotaIn(BaseModel):
    quota_mb: int


@router.get("/status")
def status(user: UserDep):
    return ftp.status()


@router.get("", response_model=list[FtpUser])
def list_users(session: SessionDep, user: UserDep):
    return ftp.list_users(session)


@router.post("", response_model=FtpUser)
def create_user(payload: FtpCreate, session: SessionDep, user: UserDep):
    row = ftp.create_user(
        session, payload.username, payload.password, payload.home, payload.quota_mb, payload.note
    )
    audit(session, user, "ftp.create", row.username)
    return row


@router.post("/{user_id}/password", response_model=FtpUser)
def set_password(user_id: int, payload: PasswordIn, session: SessionDep, user: UserDep):
    row = ftp.set_password(session, user_id, payload.password)
    audit(session, user, "ftp.password", row.username)
    return row


@router.post("/{user_id}/home", response_model=FtpUser)
def set_home(user_id: int, payload: HomeIn, session: SessionDep, user: UserDep):
    row = ftp.set_home(session, user_id, payload.home)
    audit(session, user, "ftp.home", row.username, detail=row.home)
    return row


@router.post("/{user_id}/quota", response_model=FtpUser)
def set_quota(user_id: int, payload: QuotaIn, session: SessionDep, user: UserDep):
    row = ftp.set_quota(session, user_id, payload.quota_mb)
    audit(session, user, "ftp.quota", row.username, detail=str(row.quota_mb))
    return row


@router.post("/{user_id}/enabled", response_model=FtpUser)
def set_enabled(user_id: int, enabled: bool, session: SessionDep, user: UserDep):
    row = ftp.set_enabled(session, user_id, enabled)
    audit(session, user, "ftp.toggle", row.username, detail=str(enabled))
    return row


@router.delete("/{user_id}", response_model=Ok)
def delete_user(user_id: int, session: SessionDep, user: UserDep, remove_files: bool = False):
    row = ftp.get_user(session, user_id)
    name = row.username
    ftp.delete_user(session, user_id, remove_files)
    audit(session, user, "ftp.delete", name, detail=f"remove_files={remove_files}")
    return Ok(message=f"FTP user {name} removed")


@router.post("/service/{action}", response_model=Ok)
def service(action: str, session: SessionDep, user: UserDep):
    result = ftp.service_action(action)
    audit(session, user, "ftp.service", action, success=result.ok)
    return Ok(ok=result.ok, message=result.output[:1000])


@router.get("/logs")
def logs(user: UserDep, lines: int = 200):
    return ftp.logs(min(lines, 2000))

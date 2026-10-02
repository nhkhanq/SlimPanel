from __future__ import annotations

from fastapi import APIRouter
from sqlmodel import select

from app.config import settings
from app.deps import SessionDep, UserDep, audit
from app.models import LoginLog, OperationLog
from app.schemas import Ok
from app.services import files, logstats, sites

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/sizes")
def sizes(session: SessionDep, user: UserDep):
    return logstats.sizes(session)


@router.get("/site/{site_id}")
def site_log(
    site_id: int, session: SessionDep, user: UserDep, kind: str = "access", lines: int = 200
):
    site = sites.get_site(session, site_id)
    suffix = ".error.log" if kind == "error" else ".log"
    return files.tail(str(settings.log_root / f"{site.name}{suffix}"), min(lines, 5000))


@router.get("/site/{site_id}/analysis")
def analysis(site_id: int, session: SessionDep, user: UserDep, max_lines: int = 50000, top: int = 20):
    return logstats.analyse(session, site_id, min(max_lines, 400000), min(top, 100))


@router.get("/site/{site_id}/errors")
def errors(site_id: int, session: SessionDep, user: UserDep, lines: int = 200):
    return logstats.errors(session, site_id, min(lines, 5000))


@router.post("/site/{site_id}/rotate")
def rotate(site_id: int, session: SessionDep, user: UserDep, kind: str = "access"):
    result = logstats.rotate(session, site_id, kind)
    audit(session, user, "log.rotate", result["path"], detail=f"{result['bytes']} bytes")
    return result


@router.post("/site/{site_id}/truncate", response_model=Ok)
def truncate(site_id: int, session: SessionDep, user: UserDep, kind: str = "access"):
    result = logstats.truncate(session, site_id, kind)
    audit(session, user, "log.truncate", result["path"], detail=f"{result['freed']} bytes")
    return Ok(message=f"Freed {result['freed']} bytes")


@router.get("/operations", response_model=list[OperationLog])
def operations(
    session: SessionDep, user: UserDep, limit: int = 100, action: str = "", username: str = ""
):
    statement = select(OperationLog).order_by(OperationLog.id.desc())
    if action:
        statement = statement.where(OperationLog.action.like(f"{action}%"))
    if username:
        statement = statement.where(OperationLog.username == username)
    return list(session.exec(statement.limit(min(limit, 1000))).all())


@router.get("/logins", response_model=list[LoginLog])
def logins(session: SessionDep, user: UserDep, limit: int = 100):
    return list(
        session.exec(select(LoginLog).order_by(LoginLog.id.desc()).limit(min(limit, 1000))).all()
    )


@router.delete("/operations", response_model=Ok)
def clear_operations(session: SessionDep, user: UserDep, keep: int = 500):
    rows = list(session.exec(select(OperationLog).order_by(OperationLog.id.desc())).all())
    removed = 0
    for row in rows[max(0, keep):]:
        session.delete(row)
        removed += 1
    session.commit()
    return Ok(message=f"Removed {removed} entries")

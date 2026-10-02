from __future__ import annotations

from fastapi import APIRouter
from sqlmodel import select

from app.config import settings
from app.deps import SessionDep, UserDep
from app.models import OperationLog
from app.services import files, sites

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/site/{site_id}")
def site_log(site_id: int, session: SessionDep, user: UserDep, kind: str = "access", lines: int = 200):
    site = sites.get_site(session, site_id)
    suffix = ".error.log" if kind == "error" else ".log"
    return files.tail(str(settings.log_root / f"{site.name}{suffix}"), min(lines, 2000))


@router.get("/operations", response_model=list[OperationLog])
def operations(session: SessionDep, user: UserDep, limit: int = 100):
    return list(
        session.exec(select(OperationLog).order_by(OperationLog.id.desc()).limit(min(limit, 500))).all()
    )

from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.deps import SessionDep, UserDep, audit
from app.schemas import Ok
from app.services import monitor

router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.get("/status")
def status(user: UserDep):
    return {
        "enabled": settings.monitor_enabled,
        "running": monitor.running(),
        "interval": settings.monitor_interval,
        "retention_days": settings.monitor_retention_days,
    }


@router.get("/history")
def history(session: SessionDep, user: UserDep, hours: int = 6, points: int = 240):
    return monitor.history(session, min(max(hours, 1), 720), min(max(points, 10), 2000))


@router.get("/summary")
def summary(session: SessionDep, user: UserDep, hours: int = 24):
    return monitor.summary(session, min(max(hours, 1), 720))


@router.post("/sample")
def take_sample(session: SessionDep, user: UserDep):
    return monitor.record(session)


@router.post("/prune", response_model=Ok)
def prune(session: SessionDep, user: UserDep, days: int = 0):
    removed = monitor.prune(session, days or None)
    audit(session, user, "monitor.prune", detail=f"removed={removed}")
    return Ok(message=f"Removed {removed} samples")


@router.delete("", response_model=Ok)
def clear(session: SessionDep, user: UserDep):
    removed = monitor.clear(session)
    audit(session, user, "monitor.clear", detail=f"removed={removed}")
    return Ok(message=f"Cleared {removed} samples")

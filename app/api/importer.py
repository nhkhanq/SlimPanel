from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import SessionDep, UserDep, audit
from app.services import importer

router = APIRouter(prefix="/import/aapanel", tags=["import"])


class SourceRequest(BaseModel):
    panel_dir: str = str(importer.DEFAULT_PANEL_DIR)
    cron_dir: str = str(importer.DEFAULT_CRON_DIR)
    activate: bool = False


def _source(payload: SourceRequest) -> importer.Source:
    return importer.Source(panel_dir=Path(payload.panel_dir), cron_dir=Path(payload.cron_dir))


@router.post("/inspect")
def inspect(payload: SourceRequest, user: UserDep):
    return importer.inspect(_source(payload))


@router.post("/preview")
def preview(payload: SourceRequest, session: SessionDep, user: UserDep):
    return importer.plan(session, _source(payload)).to_dict()


@router.post("/apply")
def apply(payload: SourceRequest, session: SessionDep, user: UserDep):
    report = importer.apply(session, _source(payload), payload.activate)
    audit(session, user, "import.aapanel", payload.panel_dir, detail=str(report.summary()))
    return report.to_dict()

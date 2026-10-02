from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import SessionDep, UserDep, audit
from app.services import oneclick

router = APIRouter(prefix="/one-click", tags=["one-click"])


class DeployIn(BaseModel):
    app: str
    site_name: str
    domains: list[str] = []
    php_version: str = ""


@router.get("")
def catalogue(user: UserDep):
    return oneclick.catalogue()


@router.post("/deploy")
def deploy(payload: DeployIn, session: SessionDep, user: UserDep):
    result = oneclick.deploy(
        session, payload.app, payload.site_name, payload.domains or None, payload.php_version
    )
    audit(session, user, "oneclick.deploy", payload.site_name, detail=payload.app)
    return result

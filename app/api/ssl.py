from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session

from app.deps import SessionDep, UserDep, audit
from app.models import Site
from app.schemas import CertRequest, Ok
from app.services import acme, nginx, sites

router = APIRouter(prefix="/ssl", tags=["ssl"])


class CertUpload(BaseModel):
    fullchain: str
    private_key: str


@router.get("/{site_id}")
def status(site_id: int, session: SessionDep, user: UserDep):
    return acme.status(session, site_id)


@router.post("/{site_id}/issue")
def issue(site_id: int, payload: CertRequest, session: SessionDep, user: UserDep):
    cert = acme.issue(session, site_id, payload.domains or None)
    if payload.force_https:
        _set_force_https(session, site_id, True)
    audit(session, user, "ssl.issue", cert.domains)
    return cert


@router.post("/{site_id}/upload")
def upload(site_id: int, payload: CertUpload, session: SessionDep, user: UserDep):
    cert = acme.upload(session, site_id, payload.fullchain, payload.private_key)
    audit(session, user, "ssl.upload", cert.domains)
    return cert


@router.post("/{site_id}/disable", response_model=Ok)
def disable(site_id: int, session: SessionDep, user: UserDep):
    site = acme.disable(session, site_id)
    audit(session, user, "ssl.disable", site.name)
    return Ok(message="SSL disabled")


@router.post("/{site_id}/force-https", response_model=Ok)
def force_https(site_id: int, enabled: bool, session: SessionDep, user: UserDep):
    site = _set_force_https(session, site_id, enabled)
    audit(session, user, "ssl.force_https", site.name, detail=str(enabled))
    return Ok(message=f"force_https={enabled}")


@router.post("/renew", response_model=Ok)
def renew(session: SessionDep, user: UserDep):
    result = acme.renew_all()
    audit(session, user, "ssl.renew", success=result.ok, detail=result.output)
    return Ok(ok=result.ok, message=result.output[:500])


def _set_force_https(session: Session, site_id: int, enabled: bool) -> Site:
    site = sites.get_site(session, site_id)
    site.force_https = enabled
    session.add(site)
    session.commit()
    session.refresh(site)
    nginx.write_vhost(site, sites.domain_names(session, site.id))
    return site

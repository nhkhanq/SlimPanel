from __future__ import annotations

from fastapi import APIRouter
from sqlmodel import Session

from app.deps import SessionDep, UserDep, audit
from app.models import Site
from app.schemas import DomainCreate, Ok, SiteCreate, SiteOut, SiteUpdate
from app.services import nginx, sites

router = APIRouter(prefix="/sites", tags=["sites"])


def _to_out(session: Session, site: Site) -> SiteOut:
    return SiteOut(**site.model_dump(), domains=sites.domain_names(session, site.id))


@router.get("", response_model=list[SiteOut])
def list_sites(session: SessionDep, user: UserDep):
    return [_to_out(session, site) for site in sites.list_sites(session)]


@router.post("", response_model=SiteOut)
def create_site(payload: SiteCreate, session: SessionDep, user: UserDep):
    site = sites.create_site(session, payload)
    audit(session, user, "site.create", site.name)
    return _to_out(session, site)


@router.get("/{site_id}", response_model=SiteOut)
def get_site(site_id: int, session: SessionDep, user: UserDep):
    return _to_out(session, sites.get_site(session, site_id))


@router.patch("/{site_id}", response_model=SiteOut)
def update_site(site_id: int, payload: SiteUpdate, session: SessionDep, user: UserDep):
    site = sites.update_site(session, site_id, payload)
    audit(session, user, "site.update", site.name)
    return _to_out(session, site)


@router.delete("/{site_id}", response_model=Ok)
def delete_site(site_id: int, session: SessionDep, user: UserDep, remove_files: bool = False):
    site = sites.get_site(session, site_id)
    name = site.name
    sites.delete_site(session, site_id, remove_files=remove_files)
    audit(session, user, "site.delete", name, detail=f"remove_files={remove_files}")
    return Ok(message=f"Site {name} removed")


@router.post("/{site_id}/start", response_model=SiteOut)
def start_site(site_id: int, session: SessionDep, user: UserDep):
    site = sites.set_status(session, site_id, True)
    audit(session, user, "site.start", site.name)
    return _to_out(session, site)


@router.post("/{site_id}/stop", response_model=SiteOut)
def stop_site(site_id: int, session: SessionDep, user: UserDep):
    site = sites.set_status(session, site_id, False)
    audit(session, user, "site.stop", site.name)
    return _to_out(session, site)


@router.get("/{site_id}/domains")
def list_domains(site_id: int, session: SessionDep, user: UserDep):
    site = sites.get_site(session, site_id)
    return sites.domain_names(session, site.id)


@router.post("/{site_id}/domains")
def add_domain(site_id: int, payload: DomainCreate, session: SessionDep, user: UserDep):
    domain = sites.add_domain(session, site_id, payload.name, payload.port)
    audit(session, user, "site.domain.add", domain.name)
    return domain


@router.delete("/{site_id}/domains/{domain_id}", response_model=Ok)
def remove_domain(site_id: int, domain_id: int, session: SessionDep, user: UserDep):
    sites.remove_domain(session, site_id, domain_id)
    audit(session, user, "site.domain.remove", str(domain_id))
    return Ok(message="Domain removed")


@router.get("/{site_id}/config")
def get_config(site_id: int, session: SessionDep, user: UserDep):
    site = sites.get_site(session, site_id)
    path = nginx.vhost_file(site.name)
    return {
        "path": str(path),
        "content": path.read_text() if path.exists() else "",
        "rendered": nginx.render_vhost(site, sites.domain_names(session, site.id)),
    }


@router.get("/{site_id}/rewrite")
def get_rewrite(site_id: int, session: SessionDep, user: UserDep):
    site = sites.get_site(session, site_id)
    path = nginx.rewrite_file(site.name)
    return {"path": str(path), "content": path.read_text() if path.exists() else ""}

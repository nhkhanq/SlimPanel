from __future__ import annotations

import shutil
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import Conflict, NotFound, PanelError
from app.models import Domain, Site, SiteType
from app.schemas import SiteCreate, SiteUpdate
from app.services import nginx
from app.services.paths import safe_site_name

PLACEHOLDER = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>{name}</title></head>
<body><h1>{name}</h1><p>Managed by SlimPanel.</p></body>
</html>
"""


def domain_names(session: Session, site_id: int) -> list[str]:
    rows = session.exec(select(Domain).where(Domain.site_id == site_id)).all()
    return [row.name for row in rows]


def get_site(session: Session, site_id: int) -> Site:
    site = session.get(Site, site_id)
    if not site:
        raise NotFound("Site not found")
    return site


def list_sites(session: Session) -> list[Site]:
    return list(session.exec(select(Site).order_by(Site.name)).all())


def _sync(session: Session, site: Site) -> None:
    nginx.write_vhost(site, domain_names(session, site.id))


def create_site(session: Session, payload: SiteCreate) -> Site:
    name = safe_site_name(payload.name)
    if session.exec(select(Site).where(Site.name == name)).first():
        raise Conflict("Site already exists")

    if payload.site_type == SiteType.proxy and not payload.proxy_target:
        raise PanelError("proxy_target is required for a proxy site")

    root = Path(payload.root) if payload.root else settings.www_root / name
    root.mkdir(parents=True, exist_ok=True)
    index_file = root / "index.html"
    if payload.site_type != SiteType.proxy and not any(root.iterdir()):
        index_file.write_text(PLACEHOLDER.format(name=name))

    site = Site(
        name=name,
        site_type=payload.site_type,
        root=str(root),
        php_version=payload.php_version,
        proxy_target=payload.proxy_target,
        index_files="index.php index.html index.htm"
        if payload.site_type == SiteType.php
        else "index.html index.htm",
        note=payload.note,
    )
    session.add(site)
    session.commit()
    session.refresh(site)

    domains = [safe_site_name(d) for d in (payload.domains or [name])]
    for domain in domains:
        session.add(Domain(site_id=site.id, name=domain))
    session.commit()

    try:
        _sync(session, site)
    except PanelError:
        session.delete(site)
        session.commit()
        raise
    return site


def update_site(session: Session, site_id: int, payload: SiteUpdate) -> Site:
    site = get_site(session, site_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(site, field, value)

    if site.site_type == SiteType.proxy and not site.proxy_target:
        raise PanelError("proxy_target is required for a proxy site")

    if payload.rewrite is not None:
        nginx.rewrite_file(site.name).write_text(payload.rewrite)

    session.add(site)
    session.commit()
    session.refresh(site)
    _sync(session, site)
    return site


def set_status(session: Session, site_id: int, enabled: bool) -> Site:
    site = get_site(session, site_id)
    site.enabled = enabled
    session.add(site)
    session.commit()
    session.refresh(site)
    nginx.set_enabled(site.name, enabled)
    return site


def delete_site(session: Session, site_id: int, remove_files: bool = False) -> None:
    site = get_site(session, site_id)
    nginx.remove_vhost(site.name)
    nginx.rewrite_file(site.name).unlink(missing_ok=True)

    for domain in session.exec(select(Domain).where(Domain.site_id == site.id)).all():
        session.delete(domain)

    root = Path(site.root)
    session.delete(site)
    session.commit()

    if remove_files and root.is_dir() and root != settings.www_root:
        shutil.rmtree(root, ignore_errors=True)


def add_domain(session: Session, site_id: int, name: str, port: int = 80) -> Domain:
    site = get_site(session, site_id)
    clean = safe_site_name(name)
    if session.exec(select(Domain).where(Domain.name == clean)).first():
        raise Conflict("Domain already bound")

    domain = Domain(site_id=site.id, name=clean, port=port)
    session.add(domain)
    session.commit()
    session.refresh(domain)
    _sync(session, site)
    return domain


def remove_domain(session: Session, site_id: int, domain_id: int) -> None:
    site = get_site(session, site_id)
    domain = session.get(Domain, domain_id)
    if not domain or domain.site_id != site.id:
        raise NotFound("Domain not found")
    if len(domain_names(session, site.id)) <= 1:
        raise PanelError("A site must keep at least one domain")

    session.delete(domain)
    session.commit()
    _sync(session, site)

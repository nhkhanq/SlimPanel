from __future__ import annotations

import shutil
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import Conflict, NotFound, PanelError
from app.models import Domain, Project, Site, SiteGroup, SiteType
from app.schemas import SiteCreate, SiteUpdate
from app.services import nginx
from app.services.paths import safe_site_name

# The site types that forward to something else rather than serving files.
PROXY_LIKE = {SiteType.proxy, SiteType.balance}
APP_TYPES = {SiteType.node, SiteType.python, SiteType.java, SiteType.go, SiteType.dotnet}

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
    from app.services import site_extras

    nginx.write_vhost(site, domain_names(session, site.id), site_extras.bundle(session, site))


def create_site(session: Session, payload: SiteCreate) -> Site:
    name = safe_site_name(payload.name)
    if session.exec(select(Site).where(Site.name == name)).first():
        raise Conflict("Site already exists")

    if payload.site_type == SiteType.proxy and not payload.proxy_target:
        raise PanelError("proxy_target is required for a proxy site")
    if payload.site_type == SiteType.balance and not payload.upstream_name:
        raise PanelError("upstream_name is required for a load-balanced site")
    if payload.group_id and not session.get(SiteGroup, payload.group_id):
        raise NotFound("Site group not found")
    if payload.project_id and not session.get(Project, payload.project_id):
        raise NotFound("Project not found")

    root = Path(payload.root) if payload.root else settings.www_root / name
    root.mkdir(parents=True, exist_ok=True)
    index_file = root / "index.html"
    serves_files = payload.site_type not in PROXY_LIKE | APP_TYPES
    if serves_files and not any(root.iterdir()):
        index_file.write_text(PLACEHOLDER.format(name=name))

    site = Site(
        name=name,
        site_type=payload.site_type,
        root=str(root),
        php_version=payload.php_version,
        proxy_target=payload.proxy_target,
        upstream_name=payload.upstream_name,
        project_id=payload.project_id,
        group_id=payload.group_id,
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
    before = site.model_dump()

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(site, field, value)

    if site.site_type == SiteType.proxy and not site.proxy_target:
        raise PanelError("proxy_target is required for a proxy site")
    if site.site_type == SiteType.balance and not site.upstream_name:
        raise PanelError("upstream_name is required for a load-balanced site")
    if site.group_id and not session.get(SiteGroup, site.group_id):
        raise NotFound("Site group not found")
    if site.project_id and not session.get(Project, site.project_id):
        raise NotFound("Project not found")

    rewrite_path = nginx.rewrite_file(site.name)
    previous_rewrite = rewrite_path.read_text(errors="replace") if rewrite_path.exists() else None
    if payload.rewrite is not None:
        rewrite_path.write_text(payload.rewrite)

    session.add(site)
    session.commit()
    session.refresh(site)

    try:
        _sync(session, site)
    except PanelError:
        # nginx refused the result, so the row goes back to what it was.
        for field, value in before.items():
            setattr(site, field, value)
        session.add(site)
        session.commit()
        if previous_rewrite is not None:
            rewrite_path.write_text(previous_rewrite)
        raise
    return site


def groups(session: Session) -> list[SiteGroup]:
    return list(session.exec(select(SiteGroup).order_by(SiteGroup.name)).all())


def create_group(session: Session, name: str) -> SiteGroup:
    cleaned = name.strip()
    if not cleaned:
        raise PanelError("A group name is required")
    if session.exec(select(SiteGroup).where(SiteGroup.name == cleaned)).first():
        raise Conflict("That group already exists")
    group = SiteGroup(name=cleaned)
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def delete_group(session: Session, group_id: int) -> None:
    group = session.get(SiteGroup, group_id)
    if not group:
        raise NotFound("Site group not found")
    for site in session.exec(select(Site).where(Site.group_id == group.id)).all():
        site.group_id = None
        session.add(site)
    session.delete(group)
    session.commit()


def set_status(session: Session, site_id: int, enabled: bool) -> Site:
    site = get_site(session, site_id)
    site.enabled = enabled
    session.add(site)
    session.commit()
    session.refresh(site)
    nginx.set_enabled(site.name, enabled)
    return site


def delete_site(session: Session, site_id: int, remove_files: bool = False) -> None:
    from app.models import Certificate, DirAuth, ProxyRule, Redirect

    site = get_site(session, site_id)
    nginx.remove_vhost(site.name)
    nginx.rewrite_file(site.name).unlink(missing_ok=True)

    for domain in session.exec(select(Domain).where(Domain.site_id == site.id)).all():
        session.delete(domain)

    # Everything hanging off the site goes with it, including the htpasswd files.
    for auth in session.exec(select(DirAuth).where(DirAuth.site_id == site.id)).all():
        nginx.auth_file(site.name, auth.id).unlink(missing_ok=True)
        session.delete(auth)
    for model in (ProxyRule, Redirect, Certificate):
        for row in session.exec(select(model).where(model.site_id == site.id)).all():
            session.delete(row)

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

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session, select

from app.deps import SessionDep, UserDep, audit
from app.models import Certificate, DirAuth, ProxyRule, Redirect, Site, SiteGroup
from app.schemas import DomainCreate, Ok, SiteCreate, SiteOut, SiteUpdate
from app.services import nginx, rewrites, site_extras, sites

router = APIRouter(prefix="/sites", tags=["sites"])


class GroupIn(BaseModel):
    name: str


class RedirectIn(BaseModel):
    source: str
    target: str
    kind: str = "path"
    code: int = 301
    keep_path: bool = True
    keep_query: bool = True
    name: str = ""


class ProxyIn(BaseModel):
    location: str
    target: str
    name: str = ""
    host_header: str = "$host"
    cache_enabled: bool = False
    cache_time: int = 3600
    websocket: bool = True
    replace_rules: str = ""
    extra: str = ""


class ProxyUpdate(BaseModel):
    location: str | None = None
    target: str | None = None
    name: str | None = None
    host_header: str | None = None
    cache_enabled: bool | None = None
    cache_time: int | None = None
    websocket: bool | None = None
    replace_rules: str | None = None
    extra: str | None = None
    enabled: bool | None = None


class DirAuthIn(BaseModel):
    name: str
    location: str
    username: str
    password: str


class PasswordIn(BaseModel):
    password: str


class RawContent(BaseModel):
    content: str


class UpstreamIn(BaseModel):
    name: str
    method: str = "round_robin"
    keepalive: int = 32
    note: str = ""


class NodeIn(BaseModel):
    address: str
    weight: int = 1
    max_fails: int = 3
    fail_timeout: int = 30
    backup: bool = False


def _to_out(session: Session, site: Site) -> SiteOut:
    group = session.get(SiteGroup, site.group_id) if site.group_id else None
    cert = session.exec(
        select(Certificate).where(Certificate.site_id == site.id).order_by(Certificate.id.desc())
    ).first()
    return SiteOut(
        **site.model_dump(),
        domains=sites.domain_names(session, site.id),
        group_name=group.name if group else "",
        ssl_expires_at=cert.not_after if cert else None,
    )


# ------------------------------------------------------------------- the basics


@router.get("", response_model=list[SiteOut])
def list_sites(session: SessionDep, user: UserDep, group_id: int | None = None):
    rows = sites.list_sites(session)
    if group_id is not None:
        rows = [site for site in rows if site.group_id == group_id]
    return [_to_out(session, site) for site in rows]


@router.post("", response_model=SiteOut)
def create_site(payload: SiteCreate, session: SessionDep, user: UserDep):
    site = sites.create_site(session, payload)
    audit(session, user, "site.create", site.name, detail=site.site_type.value)
    return _to_out(session, site)


@router.get("/groups", response_model=list[SiteGroup])
def list_groups(session: SessionDep, user: UserDep):
    return sites.groups(session)


@router.post("/groups", response_model=SiteGroup)
def create_group(payload: GroupIn, session: SessionDep, user: UserDep):
    group = sites.create_group(session, payload.name)
    audit(session, user, "site.group.create", group.name)
    return group


@router.delete("/groups/{group_id}", response_model=Ok)
def delete_group(group_id: int, session: SessionDep, user: UserDep):
    sites.delete_group(session, group_id)
    audit(session, user, "site.group.delete", str(group_id))
    return Ok(message="Group removed")


@router.get("/rewrite-templates")
def rewrite_templates(user: UserDep):
    return rewrites.list_templates()


@router.get("/rewrite-templates/{key}")
def rewrite_template(key: str, user: UserDep):
    return rewrites.get_template(key)


@router.get("/upstreams")
def list_upstreams(session: SessionDep, user: UserDep):
    return site_extras.list_upstreams(session)


@router.post("/upstreams")
def create_upstream(payload: UpstreamIn, session: SessionDep, user: UserDep):
    pool = site_extras.create_upstream(session, payload.name, payload.method, payload.keepalive, payload.note)
    audit(session, user, "upstream.create", pool.name)
    return pool


@router.post("/upstreams/{upstream_id}/nodes")
def add_node(upstream_id: int, payload: NodeIn, session: SessionDep, user: UserDep):
    node = site_extras.add_node(
        session, upstream_id, payload.address, payload.weight, payload.max_fails,
        payload.fail_timeout, payload.backup,
    )
    audit(session, user, "upstream.node.add", payload.address)
    return node


@router.post("/upstreams/nodes/{node_id}/down/{down}")
def set_node_down(node_id: int, down: bool, session: SessionDep, user: UserDep):
    node = site_extras.set_node_down(session, node_id, down)
    audit(session, user, "upstream.node.down", node.address, detail=str(down))
    return node


@router.delete("/upstreams/nodes/{node_id}", response_model=Ok)
def remove_node(node_id: int, session: SessionDep, user: UserDep):
    site_extras.remove_node(session, node_id)
    audit(session, user, "upstream.node.remove", str(node_id))
    return Ok(message="Node removed")


@router.delete("/upstreams/{upstream_id}", response_model=Ok)
def delete_upstream(upstream_id: int, session: SessionDep, user: UserDep):
    pool = site_extras.get_upstream(session, upstream_id)
    name = pool.name
    site_extras.delete_upstream(session, upstream_id)
    audit(session, user, "upstream.delete", name)
    return Ok(message=f"Upstream {name} removed")


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


# --------------------------------------------------------------------- domains


@router.get("/{site_id}/domains")
def list_domains(site_id: int, session: SessionDep, user: UserDep):
    site = sites.get_site(session, site_id)
    from app.models import Domain

    return list(session.exec(select(Domain).where(Domain.site_id == site.id)).all())


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


# ------------------------------------------------------------- config & rewrite


@router.get("/{site_id}/config")
def get_config(site_id: int, session: SessionDep, user: UserDep):
    return site_extras.read_config(session, site_id)


@router.post("/{site_id}/config")
def set_config(site_id: int, payload: RawContent, session: SessionDep, user: UserDep):
    info = site_extras.write_config(session, site_id, payload.content)
    audit(session, user, "site.config.write", str(site_id))
    return info


@router.get("/{site_id}/rewrite")
def get_rewrite(site_id: int, session: SessionDep, user: UserDep):
    info = site_extras.read_rewrite(session, site_id)
    site = sites.get_site(session, site_id)
    info["suggested"] = rewrites.detect(site.root)
    return info


@router.post("/{site_id}/rewrite")
def set_rewrite(site_id: int, payload: RawContent, session: SessionDep, user: UserDep):
    info = site_extras.write_rewrite(session, site_id, payload.content)
    audit(session, user, "site.rewrite.write", str(site_id))
    return info


# ------------------------------------------------------------------- redirects


@router.get("/{site_id}/redirects", response_model=list[Redirect])
def list_redirects(site_id: int, session: SessionDep, user: UserDep):
    return site_extras.list_redirects(session, site_id)


@router.post("/{site_id}/redirects", response_model=Redirect)
def create_redirect(site_id: int, payload: RedirectIn, session: SessionDep, user: UserDep):
    row = site_extras.create_redirect(
        session, site_id, payload.source, payload.target, payload.kind,
        payload.code, payload.keep_path, payload.keep_query, payload.name,
    )
    audit(session, user, "site.redirect.create", f"{row.source} -> {row.target}")
    return row


@router.post("/redirects/{redirect_id}/enabled/{enabled}", response_model=Redirect)
def set_redirect_enabled(redirect_id: int, enabled: bool, session: SessionDep, user: UserDep):
    row = site_extras.set_redirect_enabled(session, redirect_id, enabled)
    audit(session, user, "site.redirect.toggle", row.source, detail=str(enabled))
    return row


@router.delete("/redirects/{redirect_id}", response_model=Ok)
def delete_redirect(redirect_id: int, session: SessionDep, user: UserDep):
    site_extras.delete_redirect(session, redirect_id)
    audit(session, user, "site.redirect.delete", str(redirect_id))
    return Ok(message="Redirect removed")


# ----------------------------------------------------------------- proxy rules


@router.get("/{site_id}/proxies", response_model=list[ProxyRule])
def list_proxies(site_id: int, session: SessionDep, user: UserDep):
    return site_extras.list_proxies(session, site_id)


@router.post("/{site_id}/proxies", response_model=ProxyRule)
def create_proxy(site_id: int, payload: ProxyIn, session: SessionDep, user: UserDep):
    row = site_extras.create_proxy(
        session, site_id, payload.location, payload.target, payload.name, payload.host_header,
        payload.cache_enabled, payload.cache_time, payload.websocket,
        payload.replace_rules, payload.extra,
    )
    audit(session, user, "site.proxy.create", f"{row.location} -> {row.target}")
    return row


@router.patch("/proxies/{proxy_id}", response_model=ProxyRule)
def update_proxy(proxy_id: int, payload: ProxyUpdate, session: SessionDep, user: UserDep):
    row = site_extras.update_proxy(session, proxy_id, payload.model_dump())
    audit(session, user, "site.proxy.update", row.location)
    return row


@router.delete("/proxies/{proxy_id}", response_model=Ok)
def delete_proxy(proxy_id: int, session: SessionDep, user: UserDep):
    site_extras.delete_proxy(session, proxy_id)
    audit(session, user, "site.proxy.delete", str(proxy_id))
    return Ok(message="Proxy rule removed")


# -------------------------------------------------------- directory protection


@router.get("/{site_id}/dir-auth", response_model=list[DirAuth])
def list_dir_auth(site_id: int, session: SessionDep, user: UserDep):
    return site_extras.list_dir_auths(session, site_id)


@router.post("/{site_id}/dir-auth", response_model=DirAuth)
def create_dir_auth(site_id: int, payload: DirAuthIn, session: SessionDep, user: UserDep):
    row = site_extras.create_dir_auth(
        session, site_id, payload.name, payload.location, payload.username, payload.password
    )
    audit(session, user, "site.dirauth.create", row.location)
    return row


@router.post("/dir-auth/{auth_id}/password", response_model=DirAuth)
def set_dir_auth_password(auth_id: int, payload: PasswordIn, session: SessionDep, user: UserDep):
    row = site_extras.set_dir_auth_password(session, auth_id, payload.password)
    audit(session, user, "site.dirauth.password", row.location)
    return row


@router.post("/dir-auth/{auth_id}/enabled/{enabled}", response_model=DirAuth)
def set_dir_auth_enabled(auth_id: int, enabled: bool, session: SessionDep, user: UserDep):
    row = site_extras.set_dir_auth_enabled(session, auth_id, enabled)
    audit(session, user, "site.dirauth.toggle", row.location, detail=str(enabled))
    return row


@router.delete("/dir-auth/{auth_id}", response_model=Ok)
def delete_dir_auth(auth_id: int, session: SessionDep, user: UserDep):
    site_extras.delete_dir_auth(session, auth_id)
    audit(session, user, "site.dirauth.delete", str(auth_id))
    return Ok(message="Directory protection removed")


@router.get("/{site_id}/include-snippet")
def include_snippet(site_id: int, session: SessionDep, user: UserDep):
    sites.get_site(session, site_id)
    return {"snippet": nginx.include_snippet()}

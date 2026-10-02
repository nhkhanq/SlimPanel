from __future__ import annotations

import base64
import hashlib
import re
import secrets

from sqlmodel import Session, select

from app.config import settings
from app.errors import Conflict, NotFound, PanelError
from app.models import DirAuth, Project, Redirect, ProxyRule, Site, Upstream, UpstreamNode
from app.services import nginx
from app.services.paths import safe_site_name

LOCATION_PATTERN = re.compile(r"^(?:=\s*|\^~\s*|~\*?\s*)?[^\s{};]+$")
TARGET_PATTERN = re.compile(r"^https?://[^\s{};\"']+$")
UPSTREAM_NAME = re.compile(r"^[a-z0-9][a-z0-9_.-]{1,48}$")
NODE_ADDRESS = re.compile(r"^[A-Za-z0-9._-]+(?::\d{1,5})?$|^\d+\.\d+\.\d+\.\d+(?::\d{1,5})?$")


def _validate_location(location: str) -> str:
    cleaned = location.strip() or "/"
    if not LOCATION_PATTERN.match(cleaned):
        raise PanelError(f"'{location}' is not a usable nginx location")
    return cleaned


def _validate_target(target: str) -> str:
    cleaned = target.strip().rstrip("/") or ""
    if not TARGET_PATTERN.match(cleaned):
        raise PanelError("Target must be an http:// or https:// URL")
    return cleaned


def _no_injection(value: str, label: str) -> str:
    if any(token in value for token in ("{", "}", ";", "\n")):
        raise PanelError(f"{label} may not contain braces, semicolons or newlines")
    return value


# ---------------------------------------------------------------- extras bundle


def bundle(session: Session, site: Site) -> dict:
    """Everything the vhost template needs beyond the Site row itself."""
    return {
        "dir_auths": [
            {
                "id": row.id,
                "name": row.name,
                "location": row.location,
                "file": str(nginx.auth_file(site.name, row.id)),
            }
            for row in session.exec(
                select(DirAuth).where(DirAuth.site_id == site.id, DirAuth.enabled == True)  # noqa: E712
            ).all()
        ],
        "proxy_rules": [
            {
                "id": row.id,
                "location": row.location,
                "target": row.target,
                "host_header": row.host_header or "$host",
                "cache_enabled": row.cache_enabled,
                "cache_time": row.cache_time,
                "websocket": row.websocket,
                "replacements": _parse_replacements(row.replace_rules),
                "extra": row.extra,
            }
            for row in session.exec(
                select(ProxyRule).where(ProxyRule.site_id == site.id, ProxyRule.enabled == True)  # noqa: E712
            ).all()
        ],
        "redirects": [
            {
                "id": row.id,
                "kind": row.kind,
                "source": row.source,
                "target": row.target,
                "code": row.code,
                "keep_path": row.keep_path,
                "keep_query": row.keep_query,
            }
            for row in session.exec(
                select(Redirect).where(Redirect.site_id == site.id, Redirect.enabled == True)  # noqa: E712
            ).all()
        ],
        "app_port": _app_port(session, site),
    }


def _parse_replacements(raw: str) -> list[tuple[str, str]]:
    pairs = []
    for line in (raw or "").splitlines():
        if "|" not in line:
            continue
        source, target = line.split("|", 1)
        if source.strip():
            pairs.append((source.strip().replace('"', ""), target.strip().replace('"', "")))
    return pairs


def upstream_payload(session: Session, pool: Upstream) -> dict:
    nodes = session.exec(select(UpstreamNode).where(UpstreamNode.upstream_id == pool.id)).all()
    return {
        "name": pool.name,
        "method": pool.method,
        "keepalive": pool.keepalive,
        "nodes": [
            {
                "address": node.address,
                "weight": node.weight,
                "max_fails": node.max_fails,
                "fail_timeout": node.fail_timeout,
                "backup": node.backup,
                "down": node.down,
            }
            for node in nodes
        ],
    }


def _app_port(session: Session, site: Site) -> int:
    if site.project_id:
        project = session.get(Project, site.project_id)
        if project and project.port:
            return project.port
    return 3000


# --------------------------------------------------------------------- reloads


def _reload(session: Session, site: Site) -> None:
    from app.services.sites import domain_names

    nginx.write_vhost(site, domain_names(session, site.id), bundle(session, site))


def _site(session: Session, site_id: int) -> Site:
    site = session.get(Site, site_id)
    if not site:
        raise NotFound("Site not found")
    return site


# ------------------------------------------------------------------- redirects


def list_redirects(session: Session, site_id: int) -> list[Redirect]:
    site = _site(session, site_id)
    return list(session.exec(select(Redirect).where(Redirect.site_id == site.id)).all())


def create_redirect(
    session: Session,
    site_id: int,
    source: str,
    target: str,
    kind: str = "path",
    code: int = 301,
    keep_path: bool = True,
    keep_query: bool = True,
    name: str = "",
) -> Redirect:
    site = _site(session, site_id)
    if kind not in {"path", "domain"}:
        raise PanelError("Redirect kind must be path or domain")
    if code not in {301, 302, 307, 308}:
        raise PanelError("Redirect code must be 301, 302, 307 or 308")

    clean_source = safe_site_name(source) if kind == "domain" else _validate_location(source)
    row = Redirect(
        site_id=site.id,
        name=name.strip() or clean_source,
        kind=kind,
        source=clean_source,
        target=_validate_target(target),
        code=code,
        keep_path=keep_path,
        keep_query=keep_query,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    try:
        _reload(session, site)
    except PanelError:
        session.delete(row)
        session.commit()
        raise
    return row


def set_redirect_enabled(session: Session, redirect_id: int, enabled: bool) -> Redirect:
    row = session.get(Redirect, redirect_id)
    if not row:
        raise NotFound("Redirect not found")
    row.enabled = enabled
    session.add(row)
    session.commit()
    session.refresh(row)
    _reload(session, _site(session, row.site_id))
    return row


def delete_redirect(session: Session, redirect_id: int) -> None:
    row = session.get(Redirect, redirect_id)
    if not row:
        raise NotFound("Redirect not found")
    site = _site(session, row.site_id)
    session.delete(row)
    session.commit()
    _reload(session, site)


# ----------------------------------------------------------------- proxy rules


def list_proxies(session: Session, site_id: int) -> list[ProxyRule]:
    site = _site(session, site_id)
    return list(session.exec(select(ProxyRule).where(ProxyRule.site_id == site.id)).all())


def create_proxy(
    session: Session,
    site_id: int,
    location: str,
    target: str,
    name: str = "",
    host_header: str = "$host",
    cache_enabled: bool = False,
    cache_time: int = 3600,
    websocket: bool = True,
    replace_rules: str = "",
    extra: str = "",
) -> ProxyRule:
    site = _site(session, site_id)
    clean_location = _validate_location(location)
    if session.exec(
        select(ProxyRule).where(ProxyRule.site_id == site.id, ProxyRule.location == clean_location)
    ).first():
        raise Conflict(f"A proxy already handles {clean_location}")

    row = ProxyRule(
        site_id=site.id,
        name=name.strip() or clean_location,
        location=clean_location,
        target=_validate_target(target),
        host_header=_no_injection(host_header.strip() or "$host", "Host header"),
        cache_enabled=cache_enabled,
        cache_time=max(1, min(cache_time, 31536000)),
        websocket=websocket,
        replace_rules=replace_rules,
        extra=extra,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    try:
        _reload(session, site)
    except PanelError:
        session.delete(row)
        session.commit()
        raise
    return row


def update_proxy(session: Session, proxy_id: int, values: dict) -> ProxyRule:
    row = session.get(ProxyRule, proxy_id)
    if not row:
        raise NotFound("Proxy rule not found")
    for field, value in values.items():
        if value is None:
            continue
        if field == "location":
            value = _validate_location(value)
        elif field == "target":
            value = _validate_target(value)
        elif field == "host_header":
            value = _no_injection(value.strip() or "$host", "Host header")
        elif field == "cache_time":
            value = max(1, min(int(value), 31536000))
        elif field not in {"name", "cache_enabled", "websocket", "replace_rules", "extra", "enabled"}:
            continue
        setattr(row, field, value)

    session.add(row)
    session.commit()
    session.refresh(row)
    _reload(session, _site(session, row.site_id))
    return row


def delete_proxy(session: Session, proxy_id: int) -> None:
    row = session.get(ProxyRule, proxy_id)
    if not row:
        raise NotFound("Proxy rule not found")
    site = _site(session, row.site_id)
    session.delete(row)
    session.commit()
    _reload(session, site)


# -------------------------------------------------------- directory protection


def list_dir_auths(session: Session, site_id: int) -> list[DirAuth]:
    site = _site(session, site_id)
    return list(session.exec(select(DirAuth).where(DirAuth.site_id == site.id)).all())


def _htpasswd_line(username: str, password: str) -> str:
    """One htpasswd line nginx's auth_basic accepts.

    sha512-crypt where the stdlib still ships `crypt` (gone in 3.13), otherwise
    the {SHA} form, which nginx has supported since 0.6 and which needs no
    external tool.
    """
    try:
        import crypt  # noqa: PLC0415  (removed in Python 3.13)

        salt = "$6$" + secrets.token_hex(8)
        hashed = crypt.crypt(password, salt)
        if hashed:
            return f"{username}:{hashed}\n"
    except (ImportError, OSError):
        pass
    digest = base64.b64encode(hashlib.sha1(password.encode()).digest()).decode()
    return f"{username}:{{SHA}}{digest}\n"


def create_dir_auth(
    session: Session,
    site_id: int,
    name: str,
    location: str,
    username: str,
    password: str,
) -> DirAuth:
    site = _site(session, site_id)
    clean_location = _validate_location(location)
    if not username.strip() or ":" in username:
        raise PanelError("A username without a colon is required")
    if len(password) < 6:
        raise PanelError("The password must be at least 6 characters")
    if session.exec(
        select(DirAuth).where(DirAuth.site_id == site.id, DirAuth.location == clean_location)
    ).first():
        raise Conflict(f"{clean_location} is already protected")

    row = DirAuth(
        site_id=site.id,
        name=_no_injection(name.strip() or clean_location, "Name").replace('"', ""),
        location=clean_location,
        username=username.strip(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    settings.ensure_dirs()
    target = nginx.auth_file(site.name, row.id)
    target.write_text(_htpasswd_line(row.username, password))
    target.chmod(0o640)

    try:
        _reload(session, site)
    except PanelError:
        target.unlink(missing_ok=True)
        session.delete(row)
        session.commit()
        raise
    return row


def set_dir_auth_password(session: Session, auth_id: int, password: str) -> DirAuth:
    row = session.get(DirAuth, auth_id)
    if not row:
        raise NotFound("Directory protection not found")
    if len(password) < 6:
        raise PanelError("The password must be at least 6 characters")
    site = _site(session, row.site_id)
    target = nginx.auth_file(site.name, row.id)
    target.write_text(_htpasswd_line(row.username, password))
    target.chmod(0o640)
    return row


def set_dir_auth_enabled(session: Session, auth_id: int, enabled: bool) -> DirAuth:
    row = session.get(DirAuth, auth_id)
    if not row:
        raise NotFound("Directory protection not found")
    row.enabled = enabled
    session.add(row)
    session.commit()
    session.refresh(row)
    _reload(session, _site(session, row.site_id))
    return row


def delete_dir_auth(session: Session, auth_id: int) -> None:
    row = session.get(DirAuth, auth_id)
    if not row:
        raise NotFound("Directory protection not found")
    site = _site(session, row.site_id)
    nginx.auth_file(site.name, row.id).unlink(missing_ok=True)
    session.delete(row)
    session.commit()
    _reload(session, site)


# ------------------------------------------------------------------- upstreams


def list_upstreams(session: Session) -> list[dict]:
    rows = []
    for pool in session.exec(select(Upstream).order_by(Upstream.name)).all():
        nodes = session.exec(select(UpstreamNode).where(UpstreamNode.upstream_id == pool.id)).all()
        rows.append({**pool.model_dump(), "nodes": [node.model_dump() for node in nodes]})
    return rows


def get_upstream(session: Session, upstream_id: int) -> Upstream:
    pool = session.get(Upstream, upstream_id)
    if not pool:
        raise NotFound("Upstream not found")
    return pool


def create_upstream(
    session: Session, name: str, method: str = "round_robin", keepalive: int = 32, note: str = ""
) -> Upstream:
    cleaned = name.strip().lower()
    if not UPSTREAM_NAME.match(cleaned):
        raise PanelError("Upstream name must be 2-49 lowercase letters, digits, dot, dash or underscore")
    if method not in {"round_robin", "ip_hash", "least_conn"}:
        raise PanelError("Method must be round_robin, ip_hash or least_conn")
    if session.exec(select(Upstream).where(Upstream.name == cleaned)).first():
        raise Conflict("That upstream already exists")

    pool = Upstream(name=cleaned, method=method, keepalive=max(0, keepalive), note=note)
    session.add(pool)
    session.commit()
    session.refresh(pool)
    return pool


def add_node(
    session: Session,
    upstream_id: int,
    address: str,
    weight: int = 1,
    max_fails: int = 3,
    fail_timeout: int = 30,
    backup: bool = False,
) -> UpstreamNode:
    pool = get_upstream(session, upstream_id)
    cleaned = address.strip()
    if not NODE_ADDRESS.match(cleaned):
        raise PanelError("A node is host:port, for example 10.0.0.2:8080")

    node = UpstreamNode(
        upstream_id=pool.id,
        address=cleaned,
        weight=max(1, weight),
        max_fails=max(0, max_fails),
        fail_timeout=max(1, fail_timeout),
        backup=backup,
    )
    session.add(node)
    session.commit()
    session.refresh(node)
    try:
        _sync_upstream(session, pool)
    except PanelError:
        session.delete(node)
        session.commit()
        raise
    return node


def set_node_down(session: Session, node_id: int, down: bool) -> UpstreamNode:
    node = session.get(UpstreamNode, node_id)
    if not node:
        raise NotFound("Node not found")
    node.down = down
    session.add(node)
    session.commit()
    session.refresh(node)
    _sync_upstream(session, get_upstream(session, node.upstream_id))
    return node


def remove_node(session: Session, node_id: int) -> None:
    node = session.get(UpstreamNode, node_id)
    if not node:
        raise NotFound("Node not found")
    pool = get_upstream(session, node.upstream_id)
    session.delete(node)
    session.commit()
    _sync_upstream(session, pool)


def delete_upstream(session: Session, upstream_id: int) -> None:
    pool = get_upstream(session, upstream_id)
    bound = session.exec(select(Site).where(Site.upstream_name == pool.name)).all()
    if bound:
        raise PanelError(
            f"{pool.name} is still used by {', '.join(site.name for site in bound)}"
        )
    for node in session.exec(select(UpstreamNode).where(UpstreamNode.upstream_id == pool.id)).all():
        session.delete(node)
    session.delete(pool)
    session.commit()
    nginx.remove_upstream(pool.name)


def _sync_upstream(session: Session, pool: Upstream) -> None:
    """Rewrite the pool's own file, or remove it while the pool has no nodes.

    An `upstream` block with no `server` line does not parse, so an empty pool
    must leave nothing behind rather than an invalid file.
    """
    payload = upstream_payload(session, pool)
    if payload["nodes"]:
        nginx.write_upstream(payload)
    else:
        nginx.remove_upstream(pool.name)


# ---------------------------------------------------------- pseudo-static file


def read_rewrite(session: Session, site_id: int) -> dict:
    site = _site(session, site_id)
    path = nginx.rewrite_file(site.name)
    return {"path": str(path), "content": path.read_text(errors="replace") if path.exists() else ""}


def write_rewrite(session: Session, site_id: int, content: str) -> dict:
    site = _site(session, site_id)
    path = nginx.rewrite_file(site.name)
    previous = path.read_text(errors="replace") if path.exists() else ""
    path.write_text(content)
    site.rewrite = content
    session.add(site)
    session.commit()
    try:
        _reload(session, site)
    except PanelError:
        path.write_text(previous)
        nginx.apply_config(ignore_errors=True)
        raise
    return {"path": str(path), "content": content}


def read_config(session: Session, site_id: int) -> dict:
    site = _site(session, site_id)
    path = nginx.vhost_file(site.name)
    if not path.exists():
        path = nginx.disabled_vhost_file(site.name)
    from app.services.sites import domain_names

    return {
        "path": str(path),
        "content": path.read_text(errors="replace") if path.exists() else "",
        "rendered": nginx.render_vhost(site, domain_names(session, site.id), bundle(session, site)),
    }


def write_config(session: Session, site_id: int, content: str) -> dict:
    """Overwrite the generated vhost by hand. Saving the site regenerates it."""
    site = _site(session, site_id)
    path = nginx.vhost_file(site.name) if site.enabled else nginx.disabled_vhost_file(site.name)
    previous = path.read_text(errors="replace") if path.exists() else None
    path.write_text(content)
    try:
        nginx.apply_config()
    except PanelError:
        if previous is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(previous)
        nginx.apply_config(ignore_errors=True)
        raise
    return {"path": str(path), "content": content}

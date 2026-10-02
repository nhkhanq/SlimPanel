from __future__ import annotations

import re
import shutil
from pathlib import Path

import psutil

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.config import settings
from app.errors import CommandFailed
from app.models import Site, SiteType
from app.services import shell

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "nginx"
HTTP2_DIRECTIVE_SINCE = (1, 25, 1)
VERSION_PATTERN = re.compile(r"nginx/(\d+)\.(\d+)\.(\d+)")
ROOT_LOCATION = re.compile(r"^\s*location\s+(?:=\s+|\^~\s*)?/\s*\{", re.M)

_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=False,
    lstrip_blocks=False,
)


_UNSET = object()

_binary_cache: str | None = None
_version_cache: tuple[int, int, int] | None | object = _UNSET


def _discover_binary() -> str:
    for process in psutil.process_iter(["name", "exe"]):
        if process.info.get("name") == "nginx" and process.info.get("exe"):
            return process.info["exe"]
    return shutil.which("nginx") or "/usr/sbin/nginx"


def binary() -> str:
    """Which nginx is serving this host.

    The answer is cached: scanning the process table on every vhost render is
    the single slowest thing the panel used to do, and the running nginx does
    not move between restarts of the panel.
    """
    global _binary_cache
    configured = (settings.nginx_bin or "").strip()
    if configured and configured != "auto":
        return configured
    if _binary_cache is None:
        _binary_cache = _discover_binary()
    return _binary_cache


def version() -> tuple[int, int, int] | None:
    global _version_cache
    if _version_cache is _UNSET:
        result = shell.run([binary(), "-v"], timeout=10)
        match = VERSION_PATTERN.search(result.output)
        _version_cache = tuple(int(part) for part in match.groups()) if match else None
    return _version_cache


def reset_cache() -> None:
    """Forget the detected binary and version, after an nginx upgrade."""
    global _binary_cache, _version_cache
    _binary_cache = None
    _version_cache = _UNSET


def uses_inline_http2() -> bool:
    """nginx moved HTTP/2 from a listen flag to its own directive in 1.25.1."""
    current = version()
    return current is None or current < HTTP2_DIRECTIVE_SINCE


def vhost_file(site_name: str) -> Path:
    return settings.vhost_dir / f"{site_name}.conf"


def disabled_vhost_file(site_name: str) -> Path:
    return settings.vhost_dir / f"{site_name}.conf.disabled"


def rewrite_file(site_name: str) -> Path:
    return settings.rewrite_dir / f"{site_name}.conf"


def cert_paths(site_name: str) -> tuple[Path, Path]:
    base = settings.cert_dir / site_name
    return base / "fullchain.pem", base / "privkey.pem"


def rewrite_defines_root(site_name: str) -> bool:
    path = rewrite_file(site_name)
    if not path.is_file():
        return False
    return bool(ROOT_LOCATION.search(path.read_text(errors="replace")))


def document_root(site: Site) -> str:
    root = Path(site.root)
    if site.run_path:
        root = root / site.run_path.strip("/")
    return str(root)


def upstream_file(name: str) -> Path:
    return settings.upstream_dir / f"{name}.conf"


def auth_file(site_name: str, auth_id: int) -> Path:
    return settings.auth_dir / f"{site_name}_{auth_id}.pass"


def cache_root() -> Path:
    return settings.data_dir / "proxy_cache"


def _zone_name(site_name: str) -> str:
    """nginx zone names allow a narrower character set than site names do."""
    return "sp_" + re.sub(r"[^A-Za-z0-9_]", "_", site_name)


def _split_list(raw: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,\s]+", raw or "") if part.strip()]


def _extensions(raw: str) -> str:
    parts = [re.sub(r"[^A-Za-z0-9]", "", part) for part in _split_list(raw)]
    return "|".join(part for part in parts if part)


def render_vhost(site: Site, domains: list[str], extras: dict | None = None) -> str:
    """Render the vhost.

    `extras` carries everything that lives in its own table — redirects, extra
    proxies, directory passwords, the load balancing pool — so that the caller
    decides how much to look up and this function stays testable with a plain
    dict.
    """
    extras = extras or {}
    cert, key = cert_paths(site.name)
    template = _env.get_template("site.conf.j2")

    dir_auths = extras.get("dir_auths", [])
    proxy_rules = extras.get("proxy_rules", [])
    redirects = extras.get("redirects", [])

    path_redirects = [
        {
            "match": rule["source"] if rule["source"].startswith(("/", "~", "=", "^~")) else f"= {rule['source']}",
            "target": rule["target"],
            "code": rule["code"],
            "keep_path": rule["keep_path"],
        }
        for rule in redirects
        if rule.get("kind") == "path"
    ]
    domain_redirects = [rule for rule in redirects if rule.get("kind") == "domain"]

    is_proxy_like = site.site_type in (
        SiteType.proxy,
        SiteType.balance,
        SiteType.node,
        SiteType.python,
        SiteType.java,
        SiteType.go,
        SiteType.dotnet,
    )

    # Exactly one block may own `location /`. An explicit rule in the panel wins
    # over everything; after that the rewrite file wins for a site that serves
    # files, while a proxy site keeps its own proxy_pass and drops the rewrite.
    rewrite_claims_root = rewrite_defines_root(site.name)
    extras_claim_root = (
        any(auth["location"].strip() == "/" for auth in dir_auths)
        or any(rule["location"].strip() == "/" for rule in proxy_rules)
        or any(rule["match"].strip() in {"/", "= /"} for rule in path_redirects)
    )
    root_claimed = extras_claim_root or (rewrite_claims_root and not is_proxy_like)

    return template.render(
        site=site,
        server_names=" ".join(domains) if domains else site.name,
        document_root=document_root(site),
        access_log=str(settings.log_root / f"{site.name}.log"),
        error_log=str(settings.log_root / f"{site.name}.error.log"),
        acme_webroot=str(settings.acme_webroot),
        cert_path=str(cert),
        key_path=str(key),
        php_socket=settings.php_fpm_socket.format(version=site.php_version or "8.1"),
        rewrite_file=str(rewrite_file(site.name)),
        rewrite_glob=str(rewrite_file(site.name)) + "*",
        http2_inline=uses_inline_http2(),
        zone_name=_zone_name(site.name),
        cache_root=str(cache_root()),
        root_claimed=root_claimed,
        include_rewrite=not (rewrite_claims_root and is_proxy_like),
        app_port=extras.get("app_port") or 3000,
        deny_extensions=_extensions(site.deny_extensions),
        anti_leech_extensions=_extensions(site.anti_leech_extensions),
        anti_leech_allow=" ".join(_split_list(site.anti_leech_allow)),
        ip_allow_list=_split_list(site.ip_allow),
        ip_deny_list=_split_list(site.ip_deny),
        dir_auths=dir_auths,
        proxy_rules=proxy_rules,
        proxy_cache_rules=[rule for rule in proxy_rules if rule.get("cache_enabled")],
        path_redirects=path_redirects,
        domain_redirects=domain_redirects,
    )


def render_upstream(upstream: dict) -> str:
    return _env.get_template("upstream.conf.j2").render(upstream=upstream)


def write_upstream(upstream: dict) -> Path:
    """A pool lives in its own file.

    Inlining it in each vhost means two sites sharing a pool declare the same
    upstream twice, which nginx rejects outright.
    """
    settings.ensure_dirs()
    target = upstream_file(upstream["name"])
    previous = target.read_text() if target.exists() else None
    target.write_text(render_upstream(upstream))
    try:
        apply_config()
    except CommandFailed:
        if previous is None:
            target.unlink(missing_ok=True)
        else:
            target.write_text(previous)
        apply_config(ignore_errors=True)
        raise
    return target


def remove_upstream(name: str) -> None:
    upstream_file(name).unlink(missing_ok=True)
    apply_config(ignore_errors=True)


def write_vhost(site: Site, domains: list[str], extras: dict | None = None) -> Path:
    settings.ensure_dirs()
    cache_root().mkdir(parents=True, exist_ok=True)
    rewrite = rewrite_file(site.name)
    if not rewrite.exists():
        rewrite.write_text(site.rewrite or "")

    # A parked site keeps its name but stays out of nginx's include glob.
    target = vhost_file(site.name) if site.enabled else disabled_vhost_file(site.name)
    previous = target.read_text() if target.exists() else None
    target.write_text(render_vhost(site, domains, extras))

    try:
        apply_config()
    except CommandFailed:
        if previous is None:
            target.unlink(missing_ok=True)
        else:
            target.write_text(previous)
        apply_config(ignore_errors=True)
        raise
    return target


def remove_vhost(site_name: str) -> None:
    vhost_file(site_name).unlink(missing_ok=True)
    disabled_vhost_file(site_name).unlink(missing_ok=True)
    apply_config(ignore_errors=True)


def set_enabled(site_name: str, enabled: bool) -> None:
    active = vhost_file(site_name)
    parked = disabled_vhost_file(site_name)
    if enabled and parked.exists():
        parked.rename(active)
    elif not enabled and active.exists():
        active.rename(parked)
    apply_config(ignore_errors=True)


def test_config() -> shell.Result:
    return shell.run([binary(), "-t"], timeout=30)


def reload_config() -> shell.Result:
    command = settings.nginx_reload_cmd.strip()
    return shell.run(command or [binary(), "-s", "reload"], timeout=30)


def apply_config(ignore_errors: bool = False) -> None:
    check = test_config()
    if not check.ok:
        if ignore_errors:
            return
        raise CommandFailed("nginx configuration test failed", check.output)

    reloaded = reload_config()
    if not reloaded.ok and not ignore_errors:
        raise CommandFailed("nginx reload failed", reloaded.output)


def include_snippet() -> str:
    return (
        f"include {settings.upstream_dir}/*.conf;\n"
        f"include {settings.vhost_dir}/*.conf;"
    )


MAIN_CONFIG_CANDIDATES = (
    "/etc/nginx/nginx.conf",
    "/www/server/nginx/conf/nginx.conf",
    "/usr/local/nginx/conf/nginx.conf",
)


def main_config_path() -> Path | None:
    """Where this host's nginx.conf lives, asked of the binary when possible."""
    result = shell.run([binary(), "-t"], timeout=20)
    match = re.search(r"configuration file (\S+) ", result.output)
    if match:
        candidate = Path(match.group(1))
        if candidate.is_file():
            return candidate
    for candidate in MAIN_CONFIG_CANDIDATES:
        if Path(candidate).is_file():
            return Path(candidate)
    return None


def read_main_config() -> dict:
    """Read-only: the panel shows nginx.conf but never rewrites it."""
    path = main_config_path()
    if path is None:
        return {"path": "", "content": "", "includes_slimpanel": False}
    content = path.read_text(errors="replace")
    return {
        "path": str(path),
        "content": content,
        "includes_slimpanel": str(settings.vhost_dir) in content,
        "snippet": include_snippet(),
    }

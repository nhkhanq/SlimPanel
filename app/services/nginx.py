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


def binary() -> str:
    configured = (settings.nginx_bin or "").strip()
    if configured and configured != "auto":
        return configured

    for process in psutil.process_iter(["name", "exe"]):
        if process.info.get("name") == "nginx" and process.info.get("exe"):
            return process.info["exe"]
    return shutil.which("nginx") or "/usr/sbin/nginx"


def version() -> tuple[int, int, int] | None:
    result = shell.run([binary(), "-v"], timeout=10)
    match = VERSION_PATTERN.search(result.output)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


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


def render_vhost(site: Site, domains: list[str]) -> str:
    cert, key = cert_paths(site.name)
    template = _env.get_template("site.conf.j2")
    rewrite_root = rewrite_defines_root(site.name)
    is_proxy = site.site_type == SiteType.proxy
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
        http2_inline=uses_inline_http2(),
        rewrite_root=rewrite_root and not is_proxy,
        include_rewrite=not (rewrite_root and is_proxy),
    )


def write_vhost(site: Site, domains: list[str]) -> Path:
    settings.ensure_dirs()
    rewrite = rewrite_file(site.name)
    if not rewrite.exists():
        rewrite.write_text(site.rewrite or "")

    target = vhost_file(site.name)
    previous = target.read_text() if target.exists() else None
    target.write_text(render_vhost(site, domains))

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
    return f"include {settings.vhost_dir}/*.conf;"

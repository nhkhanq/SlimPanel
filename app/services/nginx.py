from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.config import settings
from app.errors import CommandFailed
from app.models import Site
from app.services import shell

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "nginx"

_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=False,
    lstrip_blocks=False,
)


def vhost_file(site_name: str) -> Path:
    return settings.vhost_dir / f"{site_name}.conf"


def disabled_vhost_file(site_name: str) -> Path:
    return settings.vhost_dir / f"{site_name}.conf.disabled"


def rewrite_file(site_name: str) -> Path:
    return settings.rewrite_dir / f"{site_name}.conf"


def cert_paths(site_name: str) -> tuple[Path, Path]:
    base = settings.cert_dir / site_name
    return base / "fullchain.pem", base / "privkey.pem"


def document_root(site: Site) -> str:
    root = Path(site.root)
    if site.run_path:
        root = root / site.run_path.strip("/")
    return str(root)


def render_vhost(site: Site, domains: list[str]) -> str:
    cert, key = cert_paths(site.name)
    template = _env.get_template("site.conf.j2")
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
    return shell.run([settings.nginx_bin, "-t"], timeout=30)


def reload_config() -> shell.Result:
    return shell.run(settings.nginx_reload_cmd, timeout=30)


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

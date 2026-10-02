from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import CommandFailed, NotFound, PanelError
from app.models import Certificate, Site
from app.services import nginx, shell
from app.services.sites import domain_names, get_site

LIVE_DIR = Path("/etc/letsencrypt/live")


def _certbot_available() -> bool:
    return settings.dry_run or shutil.which(settings.acme_bin) is not None


def issue(session: Session, site_id: int, domains: list[str] | None = None) -> Certificate:
    site = get_site(session, site_id)
    targets = domains or domain_names(session, site.id)
    if not targets:
        raise PanelError("No domain to issue a certificate for")
    if not _certbot_available():
        raise PanelError(f"{settings.acme_bin} is not installed on this server")

    settings.ensure_dirs()
    argv = [
        settings.acme_bin,
        "certonly",
        "--webroot",
        "-w",
        str(settings.acme_webroot),
        "--non-interactive",
        "--agree-tos",
        "--cert-name",
        site.name,
    ]
    argv += ["--email", settings.acme_email] if settings.acme_email else ["--register-unsafely-without-email"]
    for domain in targets:
        argv += ["-d", domain]

    result = shell.run(argv, timeout=300)
    if not result.ok:
        raise CommandFailed("Certificate request failed", result.output)

    install(session, site, targets)
    return _record(session, site, targets)


def install(session: Session, site: Site, domains: list[str]) -> None:
    cert_path, key_path = nginx.cert_paths(site.name)
    cert_path.parent.mkdir(parents=True, exist_ok=True)

    source = LIVE_DIR / site.name
    if settings.dry_run:
        cert_path.write_text("dry-run-cert")
        key_path.write_text("dry-run-key")
    else:
        if not (source / "fullchain.pem").exists():
            raise NotFound(f"Issued certificate not found at {source}")
        shutil.copyfile(source / "fullchain.pem", cert_path)
        shutil.copyfile(source / "privkey.pem", key_path)
    key_path.chmod(0o600)

    site.ssl_enabled = True
    session.add(site)
    session.commit()
    session.refresh(site)
    nginx.write_vhost(site, domains or domain_names(session, site.id))


def upload(session: Session, site_id: int, fullchain: str, private_key: str) -> Certificate:
    site = get_site(session, site_id)
    cert_path, key_path = nginx.cert_paths(site.name)
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_text(fullchain)
    key_path.write_text(private_key)
    key_path.chmod(0o600)

    site.ssl_enabled = True
    session.add(site)
    session.commit()
    session.refresh(site)
    nginx.write_vhost(site, domain_names(session, site.id))
    return _record(session, site, domain_names(session, site.id), issuer="custom")


def disable(session: Session, site_id: int) -> Site:
    site = get_site(session, site_id)
    site.ssl_enabled = False
    site.force_https = False
    session.add(site)
    session.commit()
    session.refresh(site)
    nginx.write_vhost(site, domain_names(session, site.id))
    return site


def renew_all() -> shell.Result:
    if not _certbot_available():
        raise PanelError(f"{settings.acme_bin} is not installed on this server")
    return shell.run([settings.acme_bin, "renew", "--quiet"], timeout=600)


def status(session: Session, site_id: int) -> dict:
    site = get_site(session, site_id)
    cert_path, _ = nginx.cert_paths(site.name)
    cert = session.exec(
        select(Certificate).where(Certificate.site_id == site.id).order_by(Certificate.id.desc())
    ).first()
    return {
        "ssl_enabled": site.ssl_enabled,
        "force_https": site.force_https,
        "cert_exists": cert_path.exists(),
        "issuer": cert.issuer if cert else "",
        "not_after": cert.not_after if cert else None,
        "domains": cert.domains.split(",") if cert else [],
    }


def _record(
    session: Session, site: Site, domains: list[str], issuer: str = "letsencrypt"
) -> Certificate:
    cert_path, key_path = nginx.cert_paths(site.name)
    cert = Certificate(
        site_id=site.id,
        domains=",".join(domains),
        issuer=issuer,
        not_after=_expiry(cert_path),
        cert_path=str(cert_path),
        key_path=str(key_path),
    )
    session.add(cert)
    session.commit()
    session.refresh(cert)
    return cert


def _expiry(cert_path: Path) -> datetime | None:
    if not cert_path.exists() or settings.dry_run:
        return None
    result = shell.run(["openssl", "x509", "-enddate", "-noout", "-in", str(cert_path)])
    if not result.ok or "notAfter=" not in result.stdout:
        return None
    raw = result.stdout.split("notAfter=", 1)[1].strip()
    try:
        return datetime.strptime(raw, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    except ValueError:
        return None

from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.errors import NotFound, PanelError
from app.services import shell


def cert_path() -> Path:
    return settings.panel_cert_dir / "fullchain.pem"


def key_path() -> Path:
    return settings.panel_cert_dir / "privkey.pem"


def status() -> dict:
    cert, key = cert_path(), key_path()
    return {
        "enabled": settings.panel_ssl,
        "cert_exists": cert.is_file(),
        "key_exists": key.is_file(),
        "cert_path": str(cert),
        "key_path": str(key),
        "subject": _subject(cert) if cert.is_file() else "",
        "not_after": _expiry(cert) if cert.is_file() else None,
        "self_signed": _is_self_signed(cert) if cert.is_file() else False,
    }


def _openssl(args: list[str]) -> shell.Result:
    if not shutil.which("openssl"):
        raise PanelError("openssl is not installed on this host")
    return shell.run(["openssl", *args], timeout=30)


def _subject(cert: Path) -> str:
    result = _openssl(["x509", "-noout", "-subject", "-in", str(cert)])
    return result.stdout.strip().replace("subject=", "") if result.ok else ""


def _expiry(cert: Path) -> datetime | None:
    result = _openssl(["x509", "-noout", "-enddate", "-in", str(cert)])
    if not result.ok or "notAfter=" not in result.stdout:
        return None
    raw = result.stdout.split("notAfter=", 1)[1].strip()
    try:
        return datetime.strptime(raw, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _is_self_signed(cert: Path) -> bool:
    issuer = _openssl(["x509", "-noout", "-issuer", "-in", str(cert)]).stdout.strip()
    return issuer.replace("issuer=", "") == _subject(cert)


def generate_self_signed(common_name: str = "", days: int = 3650) -> dict:
    """A self-signed certificate so the panel can speak HTTPS immediately."""
    settings.ensure_dirs()
    name = (common_name or shell.run(["hostname"], timeout=10).stdout.strip() or "slimpanel").strip()
    if any(ch in name for ch in " ;|&$`\n/"):
        raise PanelError("Invalid common name")

    result = _openssl(
        [
            "req", "-x509", "-nodes",
            "-days", str(max(1, min(days, 7300))),
            "-newkey", "rsa:2048",
            "-keyout", str(key_path()),
            "-out", str(cert_path()),
            "-subj", f"/CN={name}",
            "-addext", f"subjectAltName=DNS:{name}",
        ]
    )
    if not result.ok:
        raise PanelError("Could not generate a certificate", result.output)
    key_path().chmod(0o600)
    return status()


def upload(fullchain: str, private_key: str) -> dict:
    if "BEGIN CERTIFICATE" not in fullchain:
        raise PanelError("That does not look like a PEM certificate")
    if "PRIVATE KEY" not in private_key:
        raise PanelError("That does not look like a PEM private key")

    settings.ensure_dirs()
    cert_path().write_text(fullchain)
    key_path().write_text(private_key)
    key_path().chmod(0o600)

    check = _openssl(["x509", "-noout", "-in", str(cert_path())])
    if not check.ok:
        cert_path().unlink(missing_ok=True)
        key_path().unlink(missing_ok=True)
        raise PanelError("openssl rejected the certificate", check.output)

    if not _pair_matches():
        raise PanelError("The private key does not match the certificate")
    return status()


def _pair_matches() -> bool:
    cert_mod = _openssl(["x509", "-noout", "-modulus", "-in", str(cert_path())]).stdout.strip()
    key_mod = _openssl(["rsa", "-noout", "-modulus", "-in", str(key_path())]).stdout.strip()
    if not cert_mod or not key_mod:
        return True  # non-RSA keys: openssl has no modulus to compare
    return cert_mod == key_mod


def borrow_from_site(site_name: str) -> dict:
    """Reuse a site's certificate for the panel, which is what most people want."""
    from app.services import nginx

    source_cert, source_key = nginx.cert_paths(site_name)
    if not source_cert.is_file():
        raise NotFound(f"{site_name} has no certificate yet")

    settings.ensure_dirs()
    shutil.copyfile(source_cert, cert_path())
    shutil.copyfile(source_key, key_path())
    key_path().chmod(0o600)
    return status()


def set_enabled(enabled: bool) -> dict:
    from app.config import save_settings

    if enabled and not (cert_path().is_file() and key_path().is_file()):
        raise PanelError("Install a certificate before turning panel HTTPS on")
    save_settings({"panel_ssl": enabled})
    settings.panel_ssl = enabled
    return {**status(), "restart_required": True}


def disable() -> dict:
    return set_enabled(False)


def uvicorn_kwargs() -> dict:
    """SSL arguments for uvicorn, empty when panel HTTPS is off."""
    if not settings.panel_ssl:
        return {}
    if not (cert_path().is_file() and key_path().is_file()):
        return {}
    return {"ssl_certfile": str(cert_path()), "ssl_keyfile": str(key_path())}


def restart_panel() -> dict:
    """Ask systemd to restart the panel, detached so the reply still goes out."""
    unit = "slimpanel"
    if not shutil.which(settings.systemctl_bin):
        raise PanelError("systemctl not found; restart the panel by hand")
    if settings.dry_run:
        return {"scheduled": True, "unit": unit}
    subprocess.Popen(  # noqa: S603  the unit name is fixed, not user input
        ["/bin/sh", "-c", f"sleep 1; {settings.systemctl_bin} restart {unit}"],
        start_new_session=True,
    )
    return {"scheduled": True, "unit": unit}

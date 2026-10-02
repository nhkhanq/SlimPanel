from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import select

from app.config import save_settings, settings
from app.deps import SessionDep, UserDep, audit
from app.errors import PanelError
from app.models import PanelSetting, utcnow
from app.schemas import Ok
from app.services import nginx, panelssl

router = APIRouter(prefix="/settings", tags=["settings"])

# Only these may be changed from the web UI; the rest stay file-only on purpose.
EDITABLE = {
    "port": int,
    "entry_path": str,
    "www_root": str,
    "log_root": str,
    "file_roots": list,
    "managed_services": list,
    "php_fpm_socket": str,
    "nginx_bin": str,
    "nginx_reload_cmd": str,
    "mysql_host": str,
    "mysql_port": int,
    "mysql_user": str,
    "mysql_password": str,
    "acme_email": str,
    "acme_bin": str,
    "cron_target": str,
    "session_max_age": int,
    "login_max_attempts": int,
    "login_block_minutes": int,
    "panel_ip_allowlist": list,
    "monitor_enabled": bool,
    "monitor_interval": int,
    "monitor_retention_days": int,
    "recycle_bin": bool,
    "ftp_root": str,
    "redis_host": str,
    "redis_port": int,
    "redis_password": str,
    "pg_host": str,
    "pg_port": int,
    "pg_user": str,
    "pg_password": str,
    "mongo_uri": str,
}

SECRET_KEYS = {"mysql_password", "redis_password", "pg_password", "secret_key"}


class SettingsIn(BaseModel):
    values: dict


class PreferenceIn(BaseModel):
    key: str
    value: str


class CertUpload(BaseModel):
    fullchain: str
    private_key: str


class SelfSigned(BaseModel):
    common_name: str = ""
    days: int = 3650


@router.get("")
def read_settings(user: UserDep):
    data = settings.to_dict()
    for key in SECRET_KEYS:
        if data.get(key):
            data[key] = "********"
    data["nginx_include_snippet"] = nginx.include_snippet()
    data["editable"] = sorted(EDITABLE)
    return data


@router.post("")
def write_settings(payload: SettingsIn, session: SessionDep, user: UserDep):
    """Persist to slimpanel.json. Most keys only take effect after a restart."""
    cleaned: dict = {}
    for key, value in payload.values.items():
        if key not in EDITABLE:
            raise PanelError(f"{key} cannot be changed from the web interface")
        if key in SECRET_KEYS and value == "********":
            continue

        kind = EDITABLE[key]
        if kind is int:
            try:
                cleaned[key] = int(value)
            except (TypeError, ValueError) as exc:
                raise PanelError(f"{key} must be a number") from exc
        elif kind is bool:
            cleaned[key] = value if isinstance(value, bool) else str(value).lower() in {"1", "true", "yes", "on"}
        elif kind is list:
            cleaned[key] = (
                [part.strip() for part in value.split(",") if part.strip()]
                if isinstance(value, str)
                else list(value)
            )
        else:
            cleaned[key] = str(value)

    if "port" in cleaned and not 1 <= cleaned["port"] <= 65535:
        raise PanelError("Port out of range")

    save_settings(cleaned)
    for key, value in cleaned.items():
        setattr(settings, key, value)

    audit(session, user, "settings.write", detail=", ".join(cleaned))
    return {"saved": sorted(cleaned), "restart_required": True}


# ----------------------------------------------------------- UI preferences


@router.get("/preferences")
def preferences(session: SessionDep, user: UserDep):
    rows = session.exec(select(PanelSetting)).all()
    return {row.key: row.value for row in rows}


@router.post("/preferences", response_model=Ok)
def set_preference(payload: PreferenceIn, session: SessionDep, user: UserDep):
    if len(payload.key) > 64 or len(payload.value) > 4000:
        raise PanelError("Preference key or value is too long")
    row = session.get(PanelSetting, payload.key)
    if row:
        row.value = payload.value
        row.updated_at = utcnow()
    else:
        row = PanelSetting(key=payload.key, value=payload.value)
    session.add(row)
    session.commit()
    return Ok(message="Saved")


# --------------------------------------------------------------- panel HTTPS


@router.get("/ssl")
def ssl_status(user: UserDep):
    return panelssl.status()


@router.post("/ssl/self-signed")
def self_signed(payload: SelfSigned, session: SessionDep, user: UserDep):
    result = panelssl.generate_self_signed(payload.common_name, payload.days)
    audit(session, user, "panel.ssl.self_signed", payload.common_name)
    return result


@router.post("/ssl/upload")
def upload_cert(payload: CertUpload, session: SessionDep, user: UserDep):
    result = panelssl.upload(payload.fullchain, payload.private_key)
    audit(session, user, "panel.ssl.upload")
    return result


@router.post("/ssl/borrow/{site_name}")
def borrow_cert(site_name: str, session: SessionDep, user: UserDep):
    result = panelssl.borrow_from_site(site_name)
    audit(session, user, "panel.ssl.borrow", site_name)
    return result


@router.post("/ssl/enabled/{enabled}")
def set_ssl(enabled: bool, session: SessionDep, user: UserDep):
    result = panelssl.set_enabled(enabled)
    audit(session, user, "panel.ssl.toggle", str(enabled))
    return result


@router.post("/restart")
def restart(session: SessionDep, user: UserDep):
    audit(session, user, "panel.restart")
    return panelssl.restart_panel()

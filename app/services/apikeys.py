from __future__ import annotations

import hashlib
import hmac
import ipaddress
import secrets
import time

from sqlmodel import Session, select

from app.config import settings
from app.errors import NotFound, PanelError
from app.models import ApiKey, utcnow

SIGNATURE_WINDOW = 300  # how long a signed request stays valid, in seconds


def _fingerprint(secret: str) -> str:
    """A salted digest, so a leaked listing does not leak usable secrets."""
    return hashlib.sha256((settings.secret_key + secret).encode()).hexdigest()


def list_keys(session: Session) -> list[dict]:
    rows = session.exec(select(ApiKey).order_by(ApiKey.id)).all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "key_id": row.key_id,
            "fingerprint": row.secret_hash[:16],
            "allow_ips": row.allow_ips,
            "enabled": row.enabled,
            "last_used_at": row.last_used_at,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def get_key(session: Session, key_id: int) -> ApiKey:
    row = session.get(ApiKey, key_id)
    if not row:
        raise NotFound("API key not found")
    return row


def _clean_ips(allow_ips: str) -> str:
    cleaned = []
    for entry in (allow_ips or "").replace("\n", ",").split(","):
        value = entry.strip()
        if not value:
            continue
        try:
            ipaddress.ip_network(value, strict=False)
        except ValueError as exc:
            raise PanelError(f"'{value}' is not an IP address or CIDR block") from exc
        cleaned.append(value)
    return ",".join(cleaned)


def create(session: Session, name: str, allow_ips: str = "") -> dict:
    identifier = "sp_" + secrets.token_hex(8)
    secret = secrets.token_urlsafe(32)
    row = ApiKey(
        name=name.strip() or identifier,
        key_id=identifier,
        secret=secret,
        secret_hash=_fingerprint(secret),
        allow_ips=_clean_ips(allow_ips),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    # The secret is shown once; after this the UI only ever sees a fingerprint.
    return {
        "id": row.id,
        "name": row.name,
        "key_id": row.key_id,
        "secret": secret,
        "allow_ips": row.allow_ips,
    }


def set_enabled(session: Session, key_id: int, enabled: bool) -> ApiKey:
    row = get_key(session, key_id)
    row.enabled = enabled
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def set_allow_ips(session: Session, key_id: int, allow_ips: str) -> ApiKey:
    row = get_key(session, key_id)
    row.allow_ips = _clean_ips(allow_ips)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def delete(session: Session, key_id: int) -> None:
    session.delete(get_key(session, key_id))
    session.commit()


def signature(key_id: str, secret: str, timestamp: int) -> str:
    return hmac.new(secret.encode(), f"{key_id}:{timestamp}".encode(), hashlib.sha256).hexdigest()


def sign(key_id: str, secret: str, timestamp: int | None = None) -> dict:
    """Build the headers a client sends. The counterpart of `verify`."""
    stamp = timestamp or int(time.time())
    return {
        "X-Api-Key": key_id,
        "X-Api-Timestamp": str(stamp),
        "X-Api-Signature": signature(key_id, secret, stamp),
    }


def _ip_allowed(row: ApiKey, ip: str) -> bool:
    if not row.allow_ips:
        return True
    if not ip:
        return False
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for entry in row.allow_ips.split(","):
        try:
            if address in ipaddress.ip_network(entry.strip(), strict=False):
                return True
        except ValueError:
            continue
    return False


def verify(
    session: Session,
    key_id: str,
    ip: str = "",
    secret: str = "",
    timestamp: str = "",
    presented_signature: str = "",
) -> ApiKey:
    """Authenticate a request, by secret over TLS or by HMAC signature.

    The signed form keeps the secret off the wire, which matters when the panel
    sits behind a plain-HTTP reverse proxy on a trusted network.
    """
    row = session.exec(select(ApiKey).where(ApiKey.key_id == key_id)).first()
    if not row or not row.enabled:
        raise PanelError("Unknown or disabled API key")
    if not _ip_allowed(row, ip):
        raise PanelError(f"This API key is not allowed from {ip or 'an unknown address'}")

    if presented_signature:
        try:
            stamp = int(timestamp)
        except (TypeError, ValueError) as exc:
            raise PanelError("A signed request needs X-Api-Timestamp") from exc
        if abs(time.time() - stamp) > SIGNATURE_WINDOW:
            raise PanelError("Request timestamp is outside the signing window")
        expected = signature(row.key_id, row.secret, stamp)
        if not hmac.compare_digest(expected, presented_signature):
            raise PanelError("Invalid signature")
    elif secret:
        if not hmac.compare_digest(_fingerprint(secret), row.secret_hash):
            raise PanelError("Invalid API secret")
    else:
        raise PanelError("Send either X-Api-Secret or X-Api-Signature")

    row.last_used_at = utcnow()
    session.add(row)
    session.commit()
    return row

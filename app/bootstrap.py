from __future__ import annotations

import secrets

from sqlmodel import Session, select

from app.config import settings
from app.models import User
from app.security import hash_password

CREDENTIALS_FILE = "initial_credentials.txt"


def ensure_admin(session: Session, username: str = "admin", password: str = "") -> tuple[str, str] | None:
    if session.exec(select(User)).first():
        return None

    plain = password or secrets.token_urlsafe(12)
    session.add(User(username=username, password_hash=hash_password(plain)))
    session.commit()

    target = settings.data_dir / CREDENTIALS_FILE
    target.write_text(f"username: {username}\npassword: {plain}\n")
    target.chmod(0o600)
    return username, plain

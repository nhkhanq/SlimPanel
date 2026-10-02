from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SESSION_SALT = "slimpanel-session"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, digest_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(digest_hex) // 2,
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key, salt=SESSION_SALT)


def create_session_token(username: str) -> str:
    return _serializer().dumps({"u": username})


def read_session_token(token: str) -> str | None:
    try:
        data = _serializer().loads(token, max_age=settings.session_max_age)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("u")


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def totp_code(secret: str, at: float | None = None, step: int = 30, digits: int = 6) -> str:
    padded = secret + "=" * (-len(secret) % 8)
    key = base64.b32decode(padded, casefold=True)
    counter = int((at if at is not None else time.time()) // step)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code % 10**digits).zfill(digits)


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    if not code or not code.isdigit():
        return False
    now = time.time()
    for drift in range(-window, window + 1):
        if hmac.compare_digest(totp_code(secret, now + drift * 30), code):
            return True
    return False


def totp_uri(secret: str, username: str, issuer: str = "SlimPanel") -> str:
    return f"otpauth://totp/{issuer}:{username}?secret={secret}&issuer={issuer}"

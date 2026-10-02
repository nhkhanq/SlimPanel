from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlmodel import select

from app.config import settings
from app.deps import SESSION_COOKIE, SessionDep, UserDep, audit, client_ip
from app.models import LoginLog, User
from app.schemas import LoginRequest, Ok, PasswordChange, TotpVerify
from app.security import (
    create_session_token,
    generate_totp_secret,
    hash_password,
    totp_uri,
    verify_password,
    verify_totp,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _record_login(session: SessionDep, username: str, ip: str, success: bool, detail: str) -> None:
    session.add(LoginLog(username=username, ip=ip, success=success, detail=detail))
    session.commit()


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response, session: SessionDep):
    ip = client_ip(request)
    user = session.exec(select(User).where(User.username == payload.username)).first()

    if not user or not verify_password(payload.password, user.password_hash):
        _record_login(session, payload.username, ip, False, "bad credentials")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

    if user.totp_enabled:
        if not verify_totp(user.totp_secret or "", payload.code):
            _record_login(session, user.username, ip, False, "bad totp")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid two-factor code")

    token = create_session_token(user.username)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_max_age,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    _record_login(session, user.username, ip, True, "")
    return {"ok": True, "username": user.username, "totp_enabled": user.totp_enabled}


@router.post("/logout", response_model=Ok)
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/")
    return Ok(message="Logged out")


@router.get("/me")
def me(user: UserDep):
    return {
        "username": user.username,
        "totp_enabled": user.totp_enabled,
        "password_changed_at": user.password_changed_at,
    }


@router.post("/password", response_model=Ok)
def change_password(payload: PasswordChange, session: SessionDep, user: UserDep):
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")

    user.password_hash = hash_password(payload.new_password)
    session.add(user)
    session.commit()
    audit(session, user, "auth.password")
    return Ok(message="Password updated")


@router.post("/totp/setup")
def totp_setup(session: SessionDep, user: UserDep):
    secret = generate_totp_secret()
    user.totp_secret = secret
    user.totp_enabled = False
    session.add(user)
    session.commit()
    return {"secret": secret, "uri": totp_uri(secret, user.username)}


@router.post("/totp/enable", response_model=Ok)
def totp_enable(payload: TotpVerify, session: SessionDep, user: UserDep):
    if not user.totp_secret:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Run the setup step first")
    if not verify_totp(user.totp_secret, payload.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid code")

    user.totp_enabled = True
    session.add(user)
    session.commit()
    audit(session, user, "auth.totp.enable")
    return Ok(message="Two-factor authentication enabled")


@router.post("/totp/disable", response_model=Ok)
def totp_disable(session: SessionDep, user: UserDep):
    user.totp_enabled = False
    user.totp_secret = None
    session.add(user)
    session.commit()
    audit(session, user, "auth.totp.disable")
    return Ok(message="Two-factor authentication disabled")


@router.get("/login-logs")
def login_logs(session: SessionDep, user: UserDep, limit: int = 100):
    rows = session.exec(
        select(LoginLog).order_by(LoginLog.id.desc()).limit(min(limit, 500))
    ).all()
    return list(rows)

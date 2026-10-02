from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from app.db import get_session
from app.models import OperationLog, User
from app.security import read_session_token

SESSION_COOKIE = "slimpanel_session"

SessionDep = Annotated[Session, Depends(get_session)]


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def current_user(
    session: SessionDep,
    slimpanel_session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
    )
    if not slimpanel_session:
        raise unauthorized

    username = read_session_token(slimpanel_session)
    if not username:
        raise unauthorized

    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise unauthorized
    return user


UserDep = Annotated[User, Depends(current_user)]


def audit(
    session: Session,
    user: User | None,
    action: str,
    target: str = "",
    success: bool = True,
    detail: str = "",
) -> None:
    session.add(
        OperationLog(
            username=user.username if user else "",
            action=action,
            target=target,
            success=success,
            detail=detail[:2000],
        )
    )
    session.commit()

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import SessionDep, UserDep, audit
from app.schemas import Ok
from app.services import php

router = APIRouter(prefix="/php", tags=["php"])


class IniValues(BaseModel):
    values: dict[str, str]


class RawContent(BaseModel):
    content: str


@router.get("")
def versions(user: UserDep):
    return php.discover()


@router.get("/{version}")
def detail(version: str, user: UserDep):
    return php.get(version)


@router.get("/{version}/ini")
def read_ini(version: str, user: UserDep):
    return php.read_ini(version)


@router.post("/{version}/ini")
def write_ini(version: str, payload: RawContent, session: SessionDep, user: UserDep):
    info = php.write_ini(version, payload.content)
    audit(session, user, "php.ini.write", version)
    return info


@router.post("/{version}/ini/values")
def set_values(version: str, payload: IniValues, session: SessionDep, user: UserDep):
    info = php.set_values(version, payload.values)
    audit(session, user, "php.ini.set", version, detail=", ".join(payload.values))
    return info


@router.get("/{version}/extensions")
def extensions(version: str, user: UserDep):
    return php.extensions(version)


@router.get("/{version}/fpm")
def fpm_status(version: str, user: UserDep):
    return php.fpm_status(version)


@router.get("/{version}/fpm/config")
def read_fpm(version: str, user: UserDep):
    return php.read_fpm_conf(version)


@router.post("/{version}/fpm/config")
def write_fpm(version: str, payload: RawContent, session: SessionDep, user: UserDep):
    info = php.write_fpm_conf(version, payload.content)
    audit(session, user, "php.fpm.write", version)
    return info


@router.post("/{version}/service/{action}", response_model=Ok)
def service(version: str, action: str, session: SessionDep, user: UserDep):
    result = php.service_action(version, action)
    audit(session, user, "php.service", f"{version}:{action}", success=result.ok, detail=result.output)
    return Ok(ok=result.ok, message=result.output[:1000])


@router.get("/{version}/slow-log")
def slow_log(version: str, user: UserDep, lines: int = 200):
    return php.slow_log(version, min(lines, 2000))

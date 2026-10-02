from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import SessionDep, UserDep, audit
from app.schemas import Ok
from app.services import apikeys

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class KeyIn(BaseModel):
    name: str
    allow_ips: str = ""


class AllowIps(BaseModel):
    allow_ips: str


@router.get("")
def list_keys(session: SessionDep, user: UserDep):
    return apikeys.list_keys(session)


@router.post("")
def create(payload: KeyIn, session: SessionDep, user: UserDep):
    created = apikeys.create(session, payload.name, payload.allow_ips)
    audit(session, user, "apikey.create", created["key_id"])
    return created


@router.post("/{key_id}/enabled")
def set_enabled(key_id: int, enabled: bool, session: SessionDep, user: UserDep):
    row = apikeys.set_enabled(session, key_id, enabled)
    audit(session, user, "apikey.toggle", row.key_id, detail=str(enabled))
    return {"id": row.id, "key_id": row.key_id, "enabled": row.enabled}


@router.post("/{key_id}/allow-ips")
def set_allow_ips(key_id: int, payload: AllowIps, session: SessionDep, user: UserDep):
    row = apikeys.set_allow_ips(session, key_id, payload.allow_ips)
    audit(session, user, "apikey.allow_ips", row.key_id, detail=row.allow_ips)
    return {"id": row.id, "key_id": row.key_id, "allow_ips": row.allow_ips}


@router.delete("/{key_id}", response_model=Ok)
def delete(key_id: int, session: SessionDep, user: UserDep):
    row = apikeys.get_key(session, key_id)
    label = row.key_id
    apikeys.delete(session, key_id)
    audit(session, user, "apikey.delete", label)
    return Ok(message=f"API key {label} removed")

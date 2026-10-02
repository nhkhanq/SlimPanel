from __future__ import annotations

from fastapi import APIRouter

from app.deps import SessionDep, UserDep, audit
from app.models import RecycleItem
from app.schemas import Ok
from app.services import recycle

router = APIRouter(prefix="/recycle", tags=["recycle"])


@router.get("/usage")
def usage(session: SessionDep, user: UserDep):
    return recycle.usage(session)


@router.get("", response_model=list[RecycleItem])
def list_items(session: SessionDep, user: UserDep, limit: int = 500):
    return recycle.list_items(session, min(limit, 5000))


@router.post("/{item_id}/restore")
def restore(item_id: int, session: SessionDep, user: UserDep, overwrite: bool = False):
    item = recycle.get_item(session, item_id)
    original = item.original_path
    result = recycle.restore(session, item_id, overwrite)
    audit(session, user, "recycle.restore", original)
    return result


@router.delete("/{item_id}", response_model=Ok)
def purge(item_id: int, session: SessionDep, user: UserDep):
    item = recycle.get_item(session, item_id)
    original = item.original_path
    recycle.purge(session, item_id)
    audit(session, user, "recycle.purge", original)
    return Ok(message="Permanently removed")


@router.delete("", response_model=Ok)
def empty(session: SessionDep, user: UserDep):
    removed = recycle.empty(session)
    audit(session, user, "recycle.empty", detail=f"removed={removed}")
    return Ok(message=f"Emptied {removed} entries")

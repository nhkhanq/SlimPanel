from __future__ import annotations

from fastapi import APIRouter

from app.deps import SessionDep, UserDep, audit
from app.models import TaskRecord
from app.services import apps

router = APIRouter(prefix="/apps", tags=["apps"])


@router.get("")
def catalogue(user: UserDep):
    return {"package_manager": apps.package_manager(), "apps": apps.catalogue()}


@router.post("/{slug}/install", response_model=TaskRecord)
def install(slug: str, session: SessionDep, user: UserDep):
    task = apps.install(session, slug)
    audit(session, user, "app.install", slug, detail=f"task={task.id}")
    return task


@router.post("/{slug}/uninstall", response_model=TaskRecord)
def uninstall(slug: str, session: SessionDep, user: UserDep):
    task = apps.uninstall(session, slug)
    audit(session, user, "app.uninstall", slug, detail=f"task={task.id}")
    return task


@router.get("/{slug}/config-files")
def config_files(slug: str, user: UserDep):
    apps.get(slug)
    return apps.config_files(slug)


@router.get("/system/upgradable")
def upgradable(user: UserDep):
    return apps.upgradable()


@router.post("/system/update", response_model=TaskRecord)
def system_update(session: SessionDep, user: UserDep):
    task = apps.system_update(session)
    audit(session, user, "system.update", detail=f"task={task.id}")
    return task

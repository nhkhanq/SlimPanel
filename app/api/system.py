from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.deps import SessionDep, UserDep, audit
from app.schemas import Ok, ServiceAction
from app.services import backup, nginx, system

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/overview")
def overview(user: UserDep):
    return system.overview()


@router.get("/disks")
def disks(user: UserDep):
    return system.disks()


@router.get("/network")
def network(user: UserDep):
    return system.network()


@router.get("/processes")
def processes(user: UserDep, limit: int = 30, sort_by: str = "cpu"):
    return system.processes(min(limit, 200), sort_by)


@router.post("/processes/{pid}/kill", response_model=Ok)
def kill(pid: int, session: SessionDep, user: UserDep):
    system.kill(pid)
    audit(session, user, "system.kill", str(pid))
    return Ok(message=f"Signalled pid {pid}")


@router.get("/services")
def services(user: UserDep):
    return system.services()


@router.post("/services", response_model=Ok)
def service_action(payload: ServiceAction, session: SessionDep, user: UserDep):
    result = system.service_action(payload.name, payload.action)
    audit(
        session,
        user,
        "system.service",
        f"{payload.name}:{payload.action}",
        success=result.ok,
        detail=result.output,
    )
    return Ok(ok=result.ok, message=result.output[:500])


@router.get("/nginx/test", response_model=Ok)
def nginx_test(user: UserDep):
    result = nginx.test_config()
    return Ok(ok=result.ok, message=result.output[:1000])


@router.post("/nginx/reload", response_model=Ok)
def nginx_reload(session: SessionDep, user: UserDep):
    result = nginx.reload_config()
    audit(session, user, "system.nginx.reload", success=result.ok, detail=result.output)
    return Ok(ok=result.ok, message=result.output[:1000])


@router.get("/connections")
def connections(user: UserDep, limit: int = 100):
    return system.connections(min(limit, 500))


@router.get("/users")
def system_users(user: UserDep):
    return system.system_users()


@router.get("/storage")
def storage_usage(session: SessionDep, user: UserDep):
    return backup.usage(session)


@router.get("/nginx/config")
def nginx_config(user: UserDep):
    return nginx.read_main_config()


@router.get("/settings")
def panel_settings(user: UserDep):
    data = settings.to_dict()
    data.pop("secret_key", None)
    data.pop("mysql_password", None)
    data["nginx_include_snippet"] = nginx.include_snippet()
    return data

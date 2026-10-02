from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import SessionDep, UserDep, audit
from app.schemas import Ok
from app.services import toolbox

router = APIRouter(prefix="/toolbox", tags=["toolbox"])


class NameIn(BaseModel):
    name: str


class DnsIn(BaseModel):
    servers: list[str]


class SwapIn(BaseModel):
    size_mb: int
    path: str = "/swapfile"


class SysctlIn(BaseModel):
    values: dict[str, str]


@router.get("")
def info(user: UserDep):
    return toolbox.info()


@router.get("/timezones")
def timezones(user: UserDep):
    return toolbox.timezones()


@router.post("/timezone", response_model=Ok)
def set_timezone(payload: NameIn, session: SessionDep, user: UserDep):
    toolbox.set_timezone(payload.name)
    audit(session, user, "toolbox.timezone", payload.name)
    return Ok(message=f"Timezone set to {payload.name}")


@router.post("/hostname", response_model=Ok)
def set_hostname(payload: NameIn, session: SessionDep, user: UserDep):
    toolbox.set_hostname(payload.name)
    audit(session, user, "toolbox.hostname", payload.name)
    return Ok(message=f"Hostname set to {payload.name}")


@router.get("/dns")
def dns(user: UserDep):
    return {"servers": toolbox.dns_servers()}


@router.post("/dns")
def set_dns(payload: DnsIn, session: SessionDep, user: UserDep):
    info = toolbox.set_dns(payload.servers)
    audit(session, user, "toolbox.dns", ", ".join(payload.servers))
    return info


@router.get("/resolve")
def resolve(host: str, user: UserDep):
    return toolbox.resolve_test(host)


@router.get("/swap")
def swap(user: UserDep):
    return toolbox.swap_info()


@router.post("/swap")
def create_swap(payload: SwapIn, session: SessionDep, user: UserDep):
    info = toolbox.create_swap(payload.size_mb, payload.path)
    audit(session, user, "toolbox.swap.create", payload.path, detail=f"{payload.size_mb}MB")
    return info


@router.delete("/swap")
def remove_swap(session: SessionDep, user: UserDep, path: str = "/swapfile"):
    info = toolbox.remove_swap(path)
    audit(session, user, "toolbox.swap.remove", path)
    return info


@router.post("/release-memory")
def release_memory(session: SessionDep, user: UserDep):
    info = toolbox.release_memory()
    audit(session, user, "toolbox.release_memory", detail=f"freed={info['freed']}")
    return info


@router.get("/sysctl")
def sysctl(user: UserDep):
    return toolbox.sysctl_values()


@router.post("/sysctl")
def set_sysctl(payload: SysctlIn, session: SessionDep, user: UserDep):
    rows = toolbox.set_sysctl(payload.values)
    audit(session, user, "toolbox.sysctl", detail=", ".join(payload.values))
    return rows


@router.get("/ports")
def ports(user: UserDep):
    return toolbox.ports_in_use()


@router.post("/reboot", response_model=Ok)
def reboot(session: SessionDep, user: UserDep, confirm: str = ""):
    if confirm != "reboot":
        return Ok(ok=False, message="Pass confirm=reboot to restart the server")
    audit(session, user, "toolbox.reboot")
    result = toolbox.reboot()
    return Ok(ok=result.ok, message=result.output[:500])

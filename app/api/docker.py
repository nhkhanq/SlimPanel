from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import SessionDep, UserDep, audit
from app.models import TaskRecord
from app.schemas import Ok
from app.services import docker

router = APIRouter(prefix="/docker", tags=["docker"])


class RunContainer(BaseModel):
    image: str
    name: str = ""
    ports: list[str] = []
    volumes: list[str] = []
    env: list[str] = []
    network: str = ""
    restart: str = "unless-stopped"
    command: str = ""


class Reference(BaseModel):
    reference: str


class NetworkIn(BaseModel):
    name: str
    driver: str = "bridge"
    subnet: str = ""


class VolumeIn(BaseModel):
    name: str


class ComposeIn(BaseModel):
    compose_file: str
    action: str = "up"


class ComposeWrite(BaseModel):
    path: str
    content: str


@router.get("/info")
def info(user: UserDep):
    return docker.info()


@router.get("/containers")
def containers(user: UserDep, all_states: bool = True):
    return docker.containers(all_states)


@router.post("/containers", response_model=TaskRecord)
def run(payload: RunContainer, session: SessionDep, user: UserDep):
    task = docker.run_container(
        session,
        image=payload.image,
        name=payload.name,
        ports=payload.ports,
        volumes=payload.volumes,
        env=payload.env,
        network=payload.network,
        restart=payload.restart,
        command=payload.command,
    )
    audit(session, user, "docker.run", payload.image, detail=f"task={task.id}")
    return task


@router.post("/containers/{name}/{action}", response_model=Ok)
def container_action(name: str, action: str, session: SessionDep, user: UserDep):
    result = docker.container_action(name, action)
    audit(session, user, f"docker.{action}", name, success=result.ok, detail=result.output)
    return Ok(ok=result.ok, message=result.output[:1000])


@router.get("/containers/{name}/logs")
def container_logs(name: str, user: UserDep, lines: int = 200):
    return docker.container_logs(name, lines)


@router.get("/containers/{name}/inspect")
def container_inspect(name: str, user: UserDep):
    return docker.container_inspect(name)


@router.get("/stats")
def stats(user: UserDep):
    return docker.container_stats()


@router.get("/images")
def images(user: UserDep):
    return docker.images()


@router.post("/images/pull", response_model=TaskRecord)
def pull(payload: Reference, session: SessionDep, user: UserDep):
    task = docker.pull_image(session, payload.reference)
    audit(session, user, "docker.pull", payload.reference, detail=f"task={task.id}")
    return task


@router.delete("/images/{reference:path}", response_model=Ok)
def remove_image(reference: str, session: SessionDep, user: UserDep, force: bool = False):
    result = docker.remove_image(reference, force)
    audit(session, user, "docker.rmi", reference, success=result.ok)
    return Ok(ok=result.ok, message=result.output[:1000])


@router.get("/networks")
def networks(user: UserDep):
    return docker.networks()


@router.post("/networks", response_model=Ok)
def create_network(payload: NetworkIn, session: SessionDep, user: UserDep):
    result = docker.create_network(payload.name, payload.driver, payload.subnet)
    audit(session, user, "docker.network.create", payload.name)
    return Ok(ok=result.ok, message=result.output[:500])


@router.delete("/networks/{name}", response_model=Ok)
def remove_network(name: str, session: SessionDep, user: UserDep):
    result = docker.remove_network(name)
    audit(session, user, "docker.network.rm", name)
    return Ok(ok=result.ok, message=result.output[:500])


@router.get("/volumes")
def volumes(user: UserDep):
    return docker.volumes()


@router.post("/volumes", response_model=Ok)
def create_volume(payload: VolumeIn, session: SessionDep, user: UserDep):
    result = docker.create_volume(payload.name)
    audit(session, user, "docker.volume.create", payload.name)
    return Ok(ok=result.ok, message=result.output[:500])


@router.delete("/volumes/{name}", response_model=Ok)
def remove_volume(name: str, session: SessionDep, user: UserDep, force: bool = False):
    result = docker.remove_volume(name, force)
    audit(session, user, "docker.volume.rm", name)
    return Ok(ok=result.ok, message=result.output[:500])


@router.post("/prune/{target}")
def prune(target: str, session: SessionDep, user: UserDep):
    result = docker.prune(target)
    audit(session, user, "docker.prune", target)
    return result


@router.get("/compose")
def compose_projects(user: UserDep):
    return docker.compose_projects()


@router.post("/compose", response_model=TaskRecord)
def compose_action(payload: ComposeIn, session: SessionDep, user: UserDep):
    task = docker.compose_action(session, payload.compose_file, payload.action)
    audit(session, user, f"docker.compose.{payload.action}", payload.compose_file)
    return task


@router.post("/compose/write")
def write_compose(payload: ComposeWrite, session: SessionDep, user: UserDep):
    info = docker.write_compose(payload.path, payload.content)
    audit(session, user, "docker.compose.write", payload.path)
    return info

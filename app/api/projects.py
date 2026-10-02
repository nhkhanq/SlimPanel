from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import SessionDep, UserDep, audit
from app.schemas import Ok
from app.services import projects

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    runtime: str = "node"
    path: str = ""
    command: str = ""
    port: int = 0
    user: str = "root"
    env: str = ""
    autostart: bool = True
    note: str = ""


class ProjectUpdate(BaseModel):
    runtime: str | None = None
    path: str | None = None
    command: str | None = None
    port: int | None = None
    user: str | None = None
    env: str | None = None
    autostart: bool | None = None
    note: str | None = None


@router.get("/runtimes")
def runtimes(user: UserDep):
    return projects.runtimes()


@router.get("")
def list_projects(session: SessionDep, user: UserDep):
    return [projects.describe(row) for row in projects.list_projects(session)]


@router.post("")
def create(payload: ProjectCreate, session: SessionDep, user: UserDep):
    project = projects.create(
        session,
        name=payload.name,
        runtime=payload.runtime,
        path=payload.path,
        command=payload.command,
        port=payload.port,
        user=payload.user,
        env=payload.env,
        autostart=payload.autostart,
        note=payload.note,
    )
    audit(session, user, "project.create", project.name)
    return projects.describe(project)


@router.get("/{project_id}")
def detail(project_id: int, session: SessionDep, user: UserDep):
    return projects.describe(projects.get_project(session, project_id))


@router.patch("/{project_id}")
def update(project_id: int, payload: ProjectUpdate, session: SessionDep, user: UserDep):
    project = projects.update(session, project_id, payload.model_dump())
    audit(session, user, "project.update", project.name)
    return projects.describe(project)


@router.get("/{project_id}/unit")
def unit(project_id: int, session: SessionDep, user: UserDep):
    project = projects.get_project(session, project_id)
    return {"path": str(projects.unit_path(project)), "content": projects.render_unit(project)}


@router.post("/{project_id}/{action}", response_model=Ok)
def action(project_id: int, action: str, session: SessionDep, user: UserDep):
    result = projects.action(session, project_id, action)
    project = projects.get_project(session, project_id)
    audit(session, user, f"project.{action}", project.name, success=result.ok, detail=result.output)
    return Ok(ok=result.ok, message=result.output[:1000])


@router.post("/{project_id}/autostart/{enabled}")
def autostart(project_id: int, enabled: bool, session: SessionDep, user: UserDep):
    project = projects.set_autostart(session, project_id, enabled)
    audit(session, user, "project.autostart", project.name, detail=str(enabled))
    return projects.describe(project)


@router.get("/{project_id}/logs")
def logs(project_id: int, session: SessionDep, user: UserDep, lines: int = 200):
    return projects.logs(session, project_id, min(lines, 5000))


@router.delete("/{project_id}", response_model=Ok)
def delete(project_id: int, session: SessionDep, user: UserDep, remove_files: bool = False):
    project = projects.get_project(session, project_id)
    name = project.name
    projects.delete(session, project_id, remove_files)
    audit(session, user, "project.delete", name, detail=f"remove_files={remove_files}")
    return Ok(message=f"Project {name} removed")

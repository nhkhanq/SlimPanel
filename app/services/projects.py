from __future__ import annotations

import re
import shlex
import shutil
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import Conflict, NotFound, PanelError
from app.models import Project
from app.services import shell
from app.services.paths import resolve_for_create, resolve_managed

UNIT_DIR = Path("/etc/systemd/system")
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,48}$")
ENV_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")

RUNTIMES = {
    "node": {"label": "Node.js", "probe": "node", "default_command": "npm start"},
    "python": {"label": "Python", "probe": "python3", "default_command": "python3 app.py"},
    "java": {"label": "Java", "probe": "java", "default_command": "java -jar app.jar"},
    "go": {"label": "Go", "probe": "go", "default_command": "./app"},
    "dotnet": {"label": ".NET", "probe": "dotnet", "default_command": "dotnet App.dll"},
    "other": {"label": "Other", "probe": "", "default_command": ""},
}

UNIT_TEMPLATE = """# Managed by SlimPanel - edits are overwritten
[Unit]
Description=SlimPanel project {name}
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={path}
ExecStart={exec_start}
Restart=always
RestartSec=3
StandardOutput=append:{log}
StandardError=append:{log}
{environment}
[Install]
WantedBy=multi-user.target
"""


def runtimes() -> list[dict]:
    rows = []
    for key, meta in RUNTIMES.items():
        probe = meta["probe"]
        version = ""
        if probe and shutil.which(probe):
            version = shell.run([probe, "--version"], timeout=15).output.splitlines()[:1]
            version = version[0].strip() if version else "installed"
        rows.append(
            {
                "key": key,
                "label": meta["label"],
                "available": not probe or bool(shutil.which(probe)),
                "version": version,
                "default_command": meta["default_command"],
            }
        )
    return rows


def safe_name(name: str) -> str:
    cleaned = name.strip().lower()
    if not NAME_PATTERN.match(cleaned):
        raise PanelError("Project name must be 2-49 lowercase letters, digits, dash or underscore")
    return cleaned


def unit_name(project: Project | str) -> str:
    name = project if isinstance(project, str) else project.name
    return f"slimpanel-{name}.service"


def unit_path(project: Project | str) -> Path:
    return UNIT_DIR / unit_name(project)


def log_path(project: Project | str) -> Path:
    name = project if isinstance(project, str) else project.name
    return settings.project_dir / f"{name}.log"


def _validate_command(command: str) -> str:
    cleaned = command.strip()
    if not cleaned:
        raise PanelError("A start command is required")
    if "\n" in cleaned:
        raise PanelError("The start command must be a single line")
    try:
        parts = shlex.split(cleaned)
    except ValueError as exc:
        raise PanelError(f"Could not parse the start command: {exc}") from exc
    if not parts:
        raise PanelError("A start command is required")
    return cleaned


def _exec_start(project: Project) -> str:
    """systemd needs an absolute ExecStart, so wrap anything else in a login shell."""
    parts = shlex.split(project.command)
    binary = parts[0]
    if binary.startswith("/"):
        return project.command
    resolved = shutil.which(binary)
    if resolved:
        return " ".join([resolved, *(shlex.quote(p) for p in parts[1:])])
    return f"/bin/bash -lc {shlex.quote(project.command)}"


def _environment_block(project: Project) -> str:
    lines = []
    for raw in (project.env or "").splitlines():
        entry = raw.strip()
        if not entry or entry.startswith("#"):
            continue
        match = ENV_LINE.match(entry)
        if not match:
            raise PanelError(f"Environment entries must look like KEY=value: {entry}")
        lines.append(f'Environment="{match.group(1)}={match.group(2)}"')
    if project.port:
        if not any(line.startswith('Environment="PORT=') for line in lines):
            lines.append(f'Environment="PORT={project.port}"')
    return "".join(f"{line}\n" for line in lines)


def render_unit(project: Project) -> str:
    return UNIT_TEMPLATE.format(
        name=project.name,
        user=project.user or "root",
        path=project.path,
        exec_start=_exec_start(project),
        log=log_path(project),
        environment=_environment_block(project),
    )


def _write_unit(project: Project) -> Path:
    settings.ensure_dirs()
    log_path(project).touch(exist_ok=True)
    target = unit_path(project)
    content = render_unit(project)
    if settings.dry_run:
        (settings.project_dir / unit_name(project)).write_text(content)
        return target
    target.write_text(content)
    shell.run([settings.systemctl_bin, "daemon-reload"], timeout=60)
    if project.autostart:
        shell.run([settings.systemctl_bin, "enable", unit_name(project)], timeout=60)
    else:
        shell.run([settings.systemctl_bin, "disable", unit_name(project)], timeout=60)
    return target


def list_projects(session: Session) -> list[Project]:
    return list(session.exec(select(Project).order_by(Project.name)).all())


def get_project(session: Session, project_id: int) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise NotFound("Project not found")
    return project


def state(project: Project) -> dict:
    active = shell.run([settings.systemctl_bin, "is-active", unit_name(project)], timeout=10)
    enabled = shell.run([settings.systemctl_bin, "is-enabled", unit_name(project)], timeout=10)
    return {
        "state": active.stdout.strip() or active.stderr.strip() or "unknown",
        "enabled": enabled.stdout.strip() == "enabled",
        "unit": unit_name(project),
        "log": str(log_path(project)),
    }


def describe(project: Project) -> dict:
    data = project.model_dump()
    data.update(state(project))
    data["url"] = f"http://127.0.0.1:{project.port}" if project.port else ""
    return data


def create(
    session: Session,
    name: str,
    runtime: str,
    path: str,
    command: str = "",
    port: int = 0,
    user: str = "root",
    env: str = "",
    autostart: bool = True,
    note: str = "",
) -> Project:
    clean_name = safe_name(name)
    if runtime not in RUNTIMES:
        raise PanelError(f"Unknown runtime '{runtime}'")
    if session.exec(select(Project).where(Project.name == clean_name)).first():
        raise Conflict("A project with that name already exists")
    if port and not 1 <= port <= 65535:
        raise PanelError("Port out of range")

    raw = path.strip() or str(settings.www_root / clean_name)
    directory = resolve_managed(raw) if Path(raw).exists() else resolve_for_create(raw)
    directory.mkdir(parents=True, exist_ok=True)

    project = Project(
        name=clean_name,
        runtime=runtime,
        path=str(directory),
        command=_validate_command(command or RUNTIMES[runtime]["default_command"]),
        port=port,
        user=user.strip() or "root",
        env=env,
        autostart=autostart,
        note=note,
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    try:
        _write_unit(project)
    except PanelError:
        session.delete(project)
        session.commit()
        raise
    return project


def update(session: Session, project_id: int, values: dict) -> Project:
    project = get_project(session, project_id)
    for field, value in values.items():
        if value is None or field not in {
            "runtime",
            "path",
            "command",
            "port",
            "user",
            "env",
            "autostart",
            "note",
        }:
            continue
        if field == "runtime" and value not in RUNTIMES:
            raise PanelError(f"Unknown runtime '{value}'")
        if field == "command":
            value = _validate_command(value)
        if field == "path":
            directory = resolve_managed(value) if Path(value).exists() else resolve_for_create(value)
            directory.mkdir(parents=True, exist_ok=True)
            value = str(directory)
        if field == "port" and value and not 1 <= int(value) <= 65535:
            raise PanelError("Port out of range")
        setattr(project, field, value)

    session.add(project)
    session.commit()
    session.refresh(project)
    _write_unit(project)
    return project


def action(session: Session, project_id: int, verb: str) -> shell.Result:
    if verb not in {"start", "stop", "restart", "reload"}:
        raise PanelError(f"Unsupported action '{verb}'")
    project = get_project(session, project_id)
    if not unit_path(project).is_file() and not settings.dry_run:
        _write_unit(project)
    return shell.run([settings.systemctl_bin, verb, unit_name(project)], timeout=120)


def set_autostart(session: Session, project_id: int, enabled: bool) -> Project:
    project = get_project(session, project_id)
    project.autostart = enabled
    session.add(project)
    session.commit()
    session.refresh(project)
    _write_unit(project)
    return project


def logs(session: Session, project_id: int, lines: int = 200) -> dict:
    project = get_project(session, project_id)
    path = log_path(project)
    body: list[str] = []
    if path.is_file():
        body = path.read_text(errors="replace").splitlines()[-lines:]
    if not body:
        result = shell.run(
            ["journalctl", "-u", unit_name(project), "-n", str(lines), "--no-pager"], timeout=30
        )
        body = result.output.splitlines()
    return {"path": str(path), "lines": body}


def delete(session: Session, project_id: int, remove_files: bool = False) -> None:
    project = get_project(session, project_id)
    unit = unit_name(project)
    if not settings.dry_run:
        shell.run([settings.systemctl_bin, "stop", unit], timeout=60)
        shell.run([settings.systemctl_bin, "disable", unit], timeout=60)
        unit_path(project).unlink(missing_ok=True)
        shell.run([settings.systemctl_bin, "daemon-reload"], timeout=60)

    root = Path(project.path)
    log_path(project).unlink(missing_ok=True)
    session.delete(project)
    session.commit()

    if remove_files and root.is_dir() and root != settings.www_root:
        try:
            resolve_managed(str(root))
        except PanelError:
            return
        shutil.rmtree(root, ignore_errors=True)

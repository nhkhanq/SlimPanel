from __future__ import annotations

import json
import re
import shlex
import shutil
from pathlib import Path

from sqlmodel import Session

from app.config import settings
from app.errors import NotFound, PanelError
from app.models import TaskRecord
from app.services import shell, tasks

NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
# [host-ip:]host-port:container-port[/proto] and nothing else.
PORT_MAPPING = re.compile(
    r"^(?:(?:\d{1,3}\.){3}\d{1,3}:)?\d{1,5}:\d{1,5}(?:/(?:tcp|udp))?$"
)


def available() -> bool:
    return settings.dry_run or shutil.which(settings.docker_bin) is not None


def _require() -> None:
    if not available():
        raise PanelError("Docker is not installed. Install it from the App Store page.")


def _docker(args: list[str], timeout: int = 60) -> shell.Result:
    _require()
    return shell.run([settings.docker_bin, *args], timeout=timeout)


def _json_lines(result: shell.Result) -> list[dict]:
    rows = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def _safe_id(value: str) -> str:
    cleaned = value.strip()
    if not ID_PATTERN.match(cleaned):
        raise PanelError(f"'{value}' is not a valid Docker reference")
    return cleaned


def info() -> dict:
    if not available():
        return {"available": False, "version": "", "info": {}}
    version = _docker(["version", "--format", "{{json .}}"], timeout=30)
    system = _docker(["system", "info", "--format", "{{json .}}"], timeout=30)
    try:
        parsed = json.loads(system.stdout or "{}")
    except ValueError:
        parsed = {}
    try:
        version_data = json.loads(version.stdout or "{}")
    except ValueError:
        version_data = {}
    return {
        "available": True,
        "version": (version_data.get("Server") or {}).get("Version", "")
        or (version_data.get("Client") or {}).get("Version", ""),
        "containers": parsed.get("Containers", 0),
        "containers_running": parsed.get("ContainersRunning", 0),
        "images": parsed.get("Images", 0),
        "driver": parsed.get("Driver", ""),
        "root_dir": parsed.get("DockerRootDir", ""),
        "cpus": parsed.get("NCPU", 0),
        "memory": parsed.get("MemTotal", 0),
    }


def containers(all_states: bool = True) -> list[dict]:
    args = ["ps", "--format", "{{json .}}"]
    if all_states:
        args.append("-a")
    rows = _json_lines(_docker(args, timeout=60))
    return [
        {
            "id": row.get("ID", ""),
            "name": row.get("Names", ""),
            "image": row.get("Image", ""),
            "command": row.get("Command", ""),
            "state": row.get("State", ""),
            "status": row.get("Status", ""),
            "ports": row.get("Ports", ""),
            "created": row.get("CreatedAt", ""),
            "size": row.get("Size", ""),
        }
        for row in rows
    ]


def container_action(name: str, action: str) -> shell.Result:
    if action not in {"start", "stop", "restart", "pause", "unpause", "kill", "rm"}:
        raise PanelError(f"Unsupported container action '{action}'")
    target = _safe_id(name)
    args = ["rm", "-f", target] if action == "rm" else [action, target]
    result = _docker(args, timeout=180)
    if not result.ok:
        raise PanelError(f"docker {action} failed", result.output)
    return result


def container_logs(name: str, lines: int = 200) -> dict:
    result = _docker(["logs", "--tail", str(min(lines, 5000)), _safe_id(name)], timeout=60)
    return {"name": name, "lines": result.output.splitlines()}


def container_inspect(name: str) -> dict:
    result = _docker(["inspect", _safe_id(name)], timeout=60)
    if not result.ok:
        raise NotFound("Container not found")
    try:
        data = json.loads(result.stdout)
    except ValueError as exc:
        raise PanelError("Could not parse docker inspect output") from exc
    return data[0] if data else {}


def container_stats() -> list[dict]:
    result = _docker(["stats", "--no-stream", "--format", "{{json .}}"], timeout=60)
    rows = _json_lines(result)
    return [
        {
            "name": row.get("Name", ""),
            "cpu": row.get("CPUPerc", ""),
            "memory": row.get("MemUsage", ""),
            "memory_percent": row.get("MemPerc", ""),
            "net": row.get("NetIO", ""),
            "block": row.get("BlockIO", ""),
            "pids": row.get("PIDs", ""),
        }
        for row in rows
    ]


def run_container(
    session: Session,
    image: str,
    name: str = "",
    ports: list[str] | None = None,
    volumes: list[str] | None = None,
    env: list[str] | None = None,
    network: str = "",
    restart: str = "unless-stopped",
    command: str = "",
    detach: bool = True,
) -> TaskRecord:
    """Start a container. Runs as a task because an image pull can take a while."""
    _require()
    argv = [settings.docker_bin, "run"]
    if detach:
        argv.append("-d")
    if name:
        if not NAME_PATTERN.match(name):
            raise PanelError("Container name may contain letters, digits, dot, dash and underscore")
        argv += ["--name", name]
    if restart:
        if restart not in {"no", "always", "unless-stopped", "on-failure"}:
            raise PanelError("Invalid restart policy")
        argv += ["--restart", restart]
    for mapping in ports or []:
        cleaned = mapping.strip()
        if not PORT_MAPPING.match(cleaned):
            raise PanelError(f"Invalid port mapping: {mapping}. Use host:container, e.g. 8080:80")
        if not all(1 <= int(part) <= 65535 for part in re.findall(r"(?<![\d.])\d{1,5}(?![\d.])", cleaned)):
            raise PanelError(f"Port out of range in mapping: {mapping}")
        argv += ["-p", cleaned]
    for mapping in volumes or []:
        if ":" not in mapping or any(ch in mapping for ch in ";|&$`\n"):
            raise PanelError(f"Invalid volume mapping: {mapping}")
        argv += ["-v", mapping.strip()]
    for pair in env or []:
        if "=" not in pair or "\n" in pair:
            raise PanelError(f"Invalid environment entry: {pair}")
        argv += ["-e", pair.strip()]
    if network:
        argv += ["--network", _safe_id(network)]
    argv.append(_safe_id(image))
    if command:
        argv += shlex.split(command)

    return tasks.run_shell(
        session, f"docker run {image}", " ".join(shlex.quote(part) for part in argv), timeout=1800
    )


def images() -> list[dict]:
    rows = _json_lines(_docker(["images", "--format", "{{json .}}"], timeout=60))
    return [
        {
            "id": row.get("ID", ""),
            "repository": row.get("Repository", ""),
            "tag": row.get("Tag", ""),
            "size": row.get("Size", ""),
            "created": row.get("CreatedSince", ""),
        }
        for row in rows
    ]


def pull_image(session: Session, reference: str) -> TaskRecord:
    _require()
    target = _safe_id(reference)
    return tasks.run_shell(
        session, f"docker pull {target}", f"{settings.docker_bin} pull {shlex.quote(target)}", timeout=3600
    )


def remove_image(reference: str, force: bool = False) -> shell.Result:
    args = ["rmi", _safe_id(reference)]
    if force:
        args.insert(1, "-f")
    result = _docker(args, timeout=180)
    if not result.ok:
        raise PanelError("docker rmi failed", result.output)
    return result


def networks() -> list[dict]:
    rows = _json_lines(_docker(["network", "ls", "--format", "{{json .}}"], timeout=30))
    return [
        {
            "id": row.get("ID", ""),
            "name": row.get("Name", ""),
            "driver": row.get("Driver", ""),
            "scope": row.get("Scope", ""),
        }
        for row in rows
    ]


def create_network(name: str, driver: str = "bridge", subnet: str = "") -> shell.Result:
    if not NAME_PATTERN.match(name):
        raise PanelError("Invalid network name")
    if driver not in {"bridge", "overlay", "macvlan", "host", "none"}:
        raise PanelError("Invalid network driver")
    args = ["network", "create", "--driver", driver]
    if subnet:
        import ipaddress

        try:
            ipaddress.ip_network(subnet, strict=False)
        except ValueError as exc:
            raise PanelError("Subnet must be a CIDR block") from exc
        args += ["--subnet", subnet]
    args.append(name)
    result = _docker(args, timeout=60)
    if not result.ok:
        raise PanelError("docker network create failed", result.output)
    return result


def remove_network(name: str) -> shell.Result:
    result = _docker(["network", "rm", _safe_id(name)], timeout=60)
    if not result.ok:
        raise PanelError("docker network rm failed", result.output)
    return result


def volumes() -> list[dict]:
    rows = _json_lines(_docker(["volume", "ls", "--format", "{{json .}}"], timeout=30))
    return [
        {
            "name": row.get("Name", ""),
            "driver": row.get("Driver", ""),
            "mountpoint": row.get("Mountpoint", ""),
            "size": row.get("Size", ""),
        }
        for row in rows
    ]


def create_volume(name: str) -> shell.Result:
    if not NAME_PATTERN.match(name):
        raise PanelError("Invalid volume name")
    result = _docker(["volume", "create", name], timeout=30)
    if not result.ok:
        raise PanelError("docker volume create failed", result.output)
    return result


def remove_volume(name: str, force: bool = False) -> shell.Result:
    args = ["volume", "rm", _safe_id(name)]
    if force:
        args.insert(2, "-f")
    result = _docker(args, timeout=60)
    if not result.ok:
        raise PanelError("docker volume rm failed", result.output)
    return result


def prune(what: str = "system") -> dict:
    if what not in {"system", "image", "container", "volume", "network", "builder"}:
        raise PanelError("Invalid prune target")
    result = _docker([what, "prune", "-f"], timeout=600)
    return {"target": what, "output": result.output[:4000], "ok": result.ok}


def compose_projects() -> list[dict]:
    _require()
    result = shell.run(f"{settings.compose_bin} ls --format json", timeout=60)
    try:
        data = json.loads(result.stdout or "[]")
    except ValueError:
        return []
    return [
        {
            "name": row.get("Name", ""),
            "status": row.get("Status", ""),
            "config_files": row.get("ConfigFiles", ""),
        }
        for row in (data if isinstance(data, list) else [])
    ]


def compose_action(session: Session, compose_file: str, action: str) -> TaskRecord:
    if action not in {"up", "down", "restart", "pull", "stop", "start"}:
        raise PanelError(f"Unsupported compose action '{action}'")
    path = Path(compose_file)
    if not path.is_file() and not settings.dry_run:
        raise NotFound(f"{compose_file} not found")

    suffix = " -d" if action == "up" else ""
    command = f"{settings.compose_bin} -f {shlex.quote(str(path))} {action}{suffix}"
    return tasks.run_shell(session, f"compose {action} {path.name}", command, timeout=3600)


def write_compose(path: str, content: str) -> dict:
    target = Path(path)
    if target.suffix not in {".yml", ".yaml"}:
        raise PanelError("A compose file must end in .yml or .yaml")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return {"path": str(target), "bytes": len(content)}

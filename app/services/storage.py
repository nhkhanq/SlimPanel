from __future__ import annotations

import json
import shlex
import shutil
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import NotFound, PanelError
from app.models import BackupTarget
from app.services import shell

KINDS = {"local", "s3", "ftp", "sftp", "rsync", "webdav"}

REQUIRED = {
    "local": ["path"],
    "s3": ["bucket", "access_key", "secret_key"],
    "ftp": ["host", "username", "password"],
    "sftp": ["host", "username"],
    "rsync": ["destination"],
    "webdav": ["url", "username", "password"],
}

SECRET_FIELDS = {"password", "secret_key", "access_key", "token"}


def kinds() -> list[dict]:
    return [
        {"key": "local", "label": "Another local directory", "requires": REQUIRED["local"],
         "tool": "", "available": True},
        {"key": "s3", "label": "S3-compatible object storage", "requires": REQUIRED["s3"],
         "tool": "aws or s3cmd", "available": bool(shutil.which("aws") or shutil.which("s3cmd"))},
        {"key": "ftp", "label": "FTP", "requires": REQUIRED["ftp"],
         "tool": "lftp or curl", "available": bool(shutil.which("lftp") or shutil.which("curl"))},
        {"key": "sftp", "label": "SFTP / SCP", "requires": REQUIRED["sftp"],
         "tool": "scp", "available": bool(shutil.which("scp"))},
        {"key": "rsync", "label": "rsync", "requires": REQUIRED["rsync"],
         "tool": "rsync", "available": bool(shutil.which("rsync"))},
        {"key": "webdav", "label": "WebDAV", "requires": REQUIRED["webdav"],
         "tool": "curl", "available": bool(shutil.which("curl"))},
    ]


def _config(target: BackupTarget) -> dict:
    try:
        parsed = json.loads(target.config or "{}")
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def list_targets(session: Session) -> list[dict]:
    rows = []
    for target in session.exec(select(BackupTarget).order_by(BackupTarget.id)).all():
        config = _config(target)
        rows.append(
            {
                **target.model_dump(exclude={"config"}),
                "config": {
                    key: ("********" if key in SECRET_FIELDS else value)
                    for key, value in config.items()
                },
            }
        )
    return rows


def get_target(session: Session, target_id: int) -> BackupTarget:
    target = session.get(BackupTarget, target_id)
    if not target:
        raise NotFound("Backup target not found")
    return target


def create_target(session: Session, name: str, kind: str, config: dict) -> BackupTarget:
    if kind not in KINDS:
        raise PanelError(f"Target kind must be one of {', '.join(sorted(KINDS))}")
    missing = [field for field in REQUIRED[kind] if not str(config.get(field, "")).strip()]
    if missing:
        raise PanelError(f"{kind} needs: {', '.join(missing)}")

    target = BackupTarget(name=name.strip() or kind, kind=kind, config=json.dumps(config))
    session.add(target)
    session.commit()
    session.refresh(target)
    return target


def update_target(
    session: Session, target_id: int, name: str = "", config: dict | None = None,
    enabled: bool | None = None,
) -> BackupTarget:
    target = get_target(session, target_id)
    if name:
        target.name = name.strip()
    if config is not None:
        merged = _config(target)
        for key, value in config.items():
            if value == "********":
                continue
            merged[key] = value
        target.config = json.dumps(merged)
    if enabled is not None:
        target.enabled = enabled

    session.add(target)
    session.commit()
    session.refresh(target)
    return target


def delete_target(session: Session, target_id: int) -> None:
    session.delete(get_target(session, target_id))
    session.commit()


def _upload_command(target: BackupTarget, source: Path) -> str:
    config = _config(target)
    quoted = shlex.quote(str(source))
    prefix = str(config.get("prefix", "slimpanel")).strip("/")

    if target.kind == "local":
        destination = Path(config["path"])
        return f"mkdir -p {shlex.quote(str(destination))} && cp -f {quoted} {shlex.quote(str(destination))}/"

    if target.kind == "s3":
        bucket = config["bucket"].strip("/")
        key = f"s3://{bucket}/{prefix}/{source.name}" if prefix else f"s3://{bucket}/{source.name}"
        endpoint = config.get("endpoint", "").strip()
        if shutil.which("aws"):
            env = (
                f"AWS_ACCESS_KEY_ID={shlex.quote(config['access_key'])} "
                f"AWS_SECRET_ACCESS_KEY={shlex.quote(config['secret_key'])} "
            )
            if config.get("region"):
                env += f"AWS_DEFAULT_REGION={shlex.quote(config['region'])} "
            flag = f" --endpoint-url {shlex.quote(endpoint)}" if endpoint else ""
            return f"{env}aws s3 cp {quoted} {shlex.quote(key)}{flag}"
        return (
            f"s3cmd --access_key={shlex.quote(config['access_key'])} "
            f"--secret_key={shlex.quote(config['secret_key'])}"
            + (f" --host={shlex.quote(endpoint)}" if endpoint else "")
            + f" put {quoted} {shlex.quote(key)}"
        )

    if target.kind == "ftp":
        host = config["host"]
        port = config.get("port", 21)
        remote = f"{prefix}/" if prefix else ""
        if shutil.which("lftp"):
            script = (
                f"set ftp:ssl-allow {'true' if config.get('tls') else 'false'}; "
                f"mkdir -p {remote or '.'}; put -O {remote or '.'} {source}"
            )
            return (
                f"lftp -u {shlex.quote(config['username'])},{shlex.quote(config['password'])} "
                f"-p {int(port)} {shlex.quote(host)} -e {shlex.quote(script + '; bye')}"
            )
        url = f"ftp://{host}:{int(port)}/{remote}{source.name}"
        return (
            f"curl --ftp-create-dirs -T {quoted} "
            f"-u {shlex.quote(config['username'] + ':' + config['password'])} {shlex.quote(url)}"
        )

    if target.kind == "sftp":
        host = config["host"]
        port = config.get("port", 22)
        remote = config.get("path", ".")
        identity = f" -i {shlex.quote(config['key_file'])}" if config.get("key_file") else ""
        return (
            f"scp -P {int(port)}{identity} -o StrictHostKeyChecking=accept-new "
            f"{quoted} {shlex.quote(config['username'])}@{shlex.quote(host)}:{shlex.quote(remote)}"
        )

    if target.kind == "rsync":
        extra = config.get("options", "-az")
        return f"rsync {extra} {quoted} {shlex.quote(config['destination'])}"

    if target.kind == "webdav":
        base = config["url"].rstrip("/")
        url = f"{base}/{prefix}/{source.name}" if prefix else f"{base}/{source.name}"
        return (
            f"curl -T {quoted} -u {shlex.quote(config['username'] + ':' + config['password'])} "
            f"{shlex.quote(url)}"
        )

    raise PanelError(f"Unknown target kind '{target.kind}'")


def upload(session: Session, target_id: int, file_path: str) -> dict:
    """Copy one finished backup to a target. Synchronous; callers may wrap it."""
    target = get_target(session, target_id)
    if not target.enabled:
        raise PanelError(f"{target.name} is disabled")

    source = Path(file_path)
    if not source.is_file():
        raise NotFound(f"{file_path} not found")

    command = _upload_command(target, source)
    result = shell.run(["/bin/bash", "-lc", command], timeout=3600)
    if not result.ok:
        raise PanelError(f"Upload to {target.name} failed", result.output[:2000])
    return {"target": target.name, "file": source.name, "output": result.output[:2000]}


def upload_async(session: Session, target_id: int, file_path: str):
    from app.services import tasks

    target = get_target(session, target_id)
    source = Path(file_path)
    if not source.is_file():
        raise NotFound(f"{file_path} not found")
    command = _upload_command(target, source)
    return tasks.run_shell(session, f"Upload {source.name} to {target.name}", command, timeout=7200)


def test_target(session: Session, target_id: int) -> dict:
    """Send a tiny probe file, so credentials are checked before a real backup."""
    target = get_target(session, target_id)
    settings.ensure_dirs()
    probe = settings.backup_dir / ".slimpanel-probe.txt"
    probe.write_text("SlimPanel connectivity probe\n")
    try:
        result = upload(session, target.id, str(probe))
    finally:
        probe.unlink(missing_ok=True)
    return {"ok": True, **result}


def fan_out(session: Session, file_path: str) -> list[dict]:
    """Push a backup to every enabled target; report each result separately."""
    results = []
    for target in session.exec(
        select(BackupTarget).where(BackupTarget.enabled == True)  # noqa: E712
    ).all():
        try:
            results.append({"target": target.name, "ok": True, **upload(session, target.id, file_path)})
        except PanelError as exc:
            results.append({"target": target.name, "ok": False, "error": exc.message})
    return results

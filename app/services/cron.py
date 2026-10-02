from __future__ import annotations

import re
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import NotFound, PanelError
from app.models import CronJob, utcnow
from app.schemas import CronCreate, CronUpdate
from app.services import shell

HEADER = "# Managed by SlimPanel - edits are overwritten\nSHELL=/bin/bash\nPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n"
FIELD_PATTERN = re.compile(r"^[\d*,\-/]+$")


def validate_schedule(schedule: str) -> str:
    fields = schedule.split()
    if len(fields) != 5:
        raise PanelError("Schedule must have 5 fields, for example '0 3 * * *'")
    for field in fields:
        if not FIELD_PATTERN.match(field):
            raise PanelError(f"Invalid schedule field: {field}")
    return " ".join(fields)


def validate_command(command: str) -> str:
    cleaned = command.strip()
    if not cleaned:
        raise PanelError("Command is required")
    if "\n" in cleaned or "%" in cleaned:
        raise PanelError("Command may not contain newlines or '%'")
    return cleaned


def list_jobs(session: Session) -> list[CronJob]:
    return list(session.exec(select(CronJob).order_by(CronJob.id)).all())


def get_job(session: Session, job_id: int) -> CronJob:
    job = session.get(CronJob, job_id)
    if not job:
        raise NotFound("Cron job not found")
    return job


def log_file(job_id: int) -> Path:
    return settings.cron_log_dir / f"job_{job_id}.log"


def create(session: Session, payload: CronCreate) -> CronJob:
    job = CronJob(
        name=payload.name.strip() or "job",
        schedule=validate_schedule(payload.schedule),
        command=validate_command(payload.command),
        enabled=payload.enabled,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    sync(session)
    return job


def update(session: Session, job_id: int, payload: CronUpdate) -> CronJob:
    job = get_job(session, job_id)
    data = payload.model_dump(exclude_none=True)
    if "schedule" in data:
        data["schedule"] = validate_schedule(data["schedule"])
    if "command" in data:
        data["command"] = validate_command(data["command"])
    for field, value in data.items():
        setattr(job, field, value)

    session.add(job)
    session.commit()
    session.refresh(job)
    sync(session)
    return job


def delete(session: Session, job_id: int) -> None:
    job = get_job(session, job_id)
    log_file(job.id).unlink(missing_ok=True)
    session.delete(job)
    session.commit()
    sync(session)


def render(session: Session) -> str:
    lines = [HEADER]
    for job in list_jobs(session):
        prefix = "" if job.enabled else "# "
        lines.append(
            f"{prefix}{job.schedule} {settings.cron_user} "
            f"{job.command} >> {log_file(job.id)} 2>&1\n"
        )
    return "".join(lines)


def sync(session: Session) -> dict:
    settings.ensure_dirs()
    content = render(session)
    settings.cron_file.write_text(content)

    target = Path(settings.cron_target)
    if settings.dry_run:
        return {"installed": False, "reason": "dry-run", "path": str(settings.cron_file)}
    try:
        target.write_text(content)
        target.chmod(0o644)
    except OSError as exc:
        return {"installed": False, "reason": str(exc), "path": str(settings.cron_file)}
    return {"installed": True, "path": str(target)}


def run_now(session: Session, job_id: int) -> shell.Result:
    job = get_job(session, job_id)
    settings.ensure_dirs()
    result = shell.run(["/bin/bash", "-lc", job.command], timeout=600)

    with log_file(job.id).open("a") as handle:
        handle.write(f"\n=== manual run {utcnow().isoformat()} ===\n{result.output}\n")

    job.last_run_at = utcnow()
    session.add(job)
    session.commit()
    return result


def logs(session: Session, job_id: int, lines: int = 200) -> list[str]:
    job = get_job(session, job_id)
    path = log_file(job.id)
    if not path.exists():
        return []
    return path.read_text(errors="replace").splitlines()[-lines:]

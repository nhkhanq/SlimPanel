from __future__ import annotations

from fastapi import APIRouter

from app.deps import SessionDep, UserDep, audit
from app.models import CronJob
from app.schemas import CronCreate, CronUpdate, Ok
from app.services import cron

router = APIRouter(prefix="/cron", tags=["cron"])


@router.get("", response_model=list[CronJob])
def list_jobs(session: SessionDep, user: UserDep):
    return cron.list_jobs(session)


@router.post("", response_model=CronJob)
def create_job(payload: CronCreate, session: SessionDep, user: UserDep):
    job = cron.create(session, payload)
    audit(session, user, "cron.create", job.name)
    return job


@router.patch("/{job_id}", response_model=CronJob)
def update_job(job_id: int, payload: CronUpdate, session: SessionDep, user: UserDep):
    job = cron.update(session, job_id, payload)
    audit(session, user, "cron.update", job.name)
    return job


@router.delete("/{job_id}", response_model=Ok)
def delete_job(job_id: int, session: SessionDep, user: UserDep):
    job = cron.get_job(session, job_id)
    name = job.name
    cron.delete(session, job_id)
    audit(session, user, "cron.delete", name)
    return Ok(message=f"Cron job {name} removed")


@router.post("/{job_id}/run", response_model=Ok)
def run_job(job_id: int, session: SessionDep, user: UserDep):
    result = cron.run_now(session, job_id)
    audit(session, user, "cron.run", str(job_id), success=result.ok)
    return Ok(ok=result.ok, message=result.output[:2000])


@router.get("/{job_id}/logs")
def job_logs(job_id: int, session: SessionDep, user: UserDep, lines: int = 200):
    return {"lines": cron.logs(session, job_id, min(lines, 2000))}


@router.get("/render")
def render(session: SessionDep, user: UserDep):
    return {"content": cron.render(session)}


@router.post("/sync")
def sync(session: SessionDep, user: UserDep):
    return cron.sync(session)

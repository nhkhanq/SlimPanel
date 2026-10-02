from __future__ import annotations

from fastapi import APIRouter

from app.deps import SessionDep, UserDep, audit
from app.models import TaskRecord
from app.schemas import Ok
from app.services import tasks

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRecord])
def list_tasks(session: SessionDep, user: UserDep, limit: int = 100, status: str = ""):
    return tasks.list_tasks(session, min(limit, 500), status)


@router.get("/{task_id}", response_model=TaskRecord)
def detail(task_id: int, session: SessionDep, user: UserDep):
    return tasks.get_task(session, task_id)


@router.get("/{task_id}/output")
def output(task_id: int, session: SessionDep, user: UserDep, lines: int = 400):
    return {"lines": tasks.output(session, task_id, min(lines, 5000))}


@router.post("/{task_id}/cancel", response_model=Ok)
def cancel(task_id: int, session: SessionDep, user: UserDep):
    cancelled = tasks.cancel(session, task_id)
    audit(session, user, "task.cancel", str(task_id), success=cancelled)
    return Ok(ok=cancelled, message="Cancelled" if cancelled else "Task is already finished")


@router.delete("/{task_id}", response_model=Ok)
def delete(task_id: int, session: SessionDep, user: UserDep):
    tasks.delete(session, task_id)
    return Ok(message="Task removed")


@router.post("/prune", response_model=Ok)
def prune(session: SessionDep, user: UserDep, keep: int = 200):
    removed = tasks.prune(session, max(0, keep))
    return Ok(message=f"Removed {removed} tasks")

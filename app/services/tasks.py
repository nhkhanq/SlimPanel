from __future__ import annotations

import subprocess
import threading
from collections.abc import Callable
from pathlib import Path

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import StaleDataError
from sqlmodel import Session, select

from app.config import settings
from app.db import engine
from app.errors import NotFound
from app.models import TaskRecord, utcnow

_lock = threading.Lock()
_threads: dict[int, threading.Thread] = {}
_processes: dict[int, subprocess.Popen] = {}


def log_file(task_id: int) -> Path:
    return settings.task_log_dir / f"task_{task_id}.log"


def list_tasks(session: Session, limit: int = 100, status: str = "") -> list[TaskRecord]:
    statement = select(TaskRecord).order_by(TaskRecord.id.desc()).limit(limit)
    if status:
        statement = statement.where(TaskRecord.status == status)
    return list(session.exec(statement).all())


def get_task(session: Session, task_id: int) -> TaskRecord:
    task = session.get(TaskRecord, task_id)
    if not task:
        raise NotFound("Task not found")
    return task


def create(session: Session, name: str, kind: str = "shell", detail: str = "") -> TaskRecord:
    settings.ensure_dirs()
    task = TaskRecord(name=name, kind=kind, detail=detail, status="pending")
    session.add(task)
    session.commit()
    session.refresh(task)
    task.log_file = str(log_file(task.id))
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def _update(task_id: int, **fields) -> None:
    """Write progress back, tolerating a row the operator deleted mid-run."""
    try:
        with Session(engine) as session:
            task = session.get(TaskRecord, task_id)
            if not task:
                return
            for key, value in fields.items():
                setattr(task, key, value)
            session.add(task)
            session.commit()
    except (StaleDataError, OperationalError):
        # The task was removed while it was still running; nothing to record.
        return


def _finish(task_id: int, status: str, detail: str = "", progress: int = 100) -> None:
    _update(
        task_id, status=status, detail=detail[:2000], progress=progress, finished_at=utcnow()
    )


def _start(task_id: int) -> None:
    _update(task_id, status="running", started_at=utcnow())


def run_shell(session: Session, name: str, command: str, timeout: int = 3600) -> TaskRecord:
    """Run a shell command in the background, streaming into the task log."""
    task = create(session, name, kind="shell", detail=command)
    path = log_file(task.id)

    def worker() -> None:
        _start(task.id)
        if settings.dry_run:
            path.write_text(f"dry-run: {command}\n")
            _finish(task.id, "done", "dry-run")
            return
        try:
            with path.open("w") as handle:
                handle.write(f"$ {command}\n\n")
                handle.flush()
                process = subprocess.Popen(
                    ["/bin/bash", "-lc", command],
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                with _lock:
                    _processes[task.id] = process
                code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _finish(task.id, "failed", f"timed out after {timeout}s")
        except OSError as exc:
            _finish(task.id, "failed", str(exc))
        else:
            _finish(task.id, "done" if code == 0 else "failed", f"exit={code}")
        finally:
            with _lock:
                _processes.pop(task.id, None)
                _threads.pop(task.id, None)

    thread = threading.Thread(target=worker, name=f"task-{task.id}", daemon=True)
    with _lock:
        _threads[task.id] = thread
    thread.start()
    return task


def run_callable(session: Session, name: str, func: Callable[[], str], kind: str = "job") -> TaskRecord:
    """Run a Python callable in the background; its return value becomes the detail."""
    task = create(session, name, kind=kind)
    path = log_file(task.id)

    def worker() -> None:
        _start(task.id)
        try:
            output = func() or ""
        except Exception as exc:  # a background job must never take the panel down
            path.write_text(f"{type(exc).__name__}: {exc}\n")
            _finish(task.id, "failed", f"{type(exc).__name__}: {exc}")
        else:
            path.write_text(output)
            _finish(task.id, "done", output[:2000])
        finally:
            with _lock:
                _threads.pop(task.id, None)

    thread = threading.Thread(target=worker, name=f"task-{task.id}", daemon=True)
    with _lock:
        _threads[task.id] = thread
    thread.start()
    return task


def cancel(session: Session, task_id: int) -> bool:
    task = get_task(session, task_id)
    with _lock:
        process = _processes.get(task_id)
    if process and process.poll() is None:
        process.terminate()
        _finish(task_id, "cancelled", "terminated by operator")
        return True
    if task.status in {"pending", "running"}:
        _finish(task_id, "cancelled", "no process to signal")
        return True
    return False


def output(session: Session, task_id: int, lines: int = 400) -> list[str]:
    get_task(session, task_id)
    path = log_file(task_id)
    if not path.exists():
        return []
    return path.read_text(errors="replace").splitlines()[-lines:]


def delete(session: Session, task_id: int) -> None:
    task = get_task(session, task_id)
    log_file(task.id).unlink(missing_ok=True)
    session.delete(task)
    session.commit()


def prune(session: Session, keep: int = 200) -> int:
    rows = list(session.exec(select(TaskRecord).order_by(TaskRecord.id.desc())).all())
    removed = 0
    for task in rows[keep:]:
        log_file(task.id).unlink(missing_ok=True)
        session.delete(task)
        removed += 1
    session.commit()
    return removed

from __future__ import annotations

import threading
import time
from datetime import timedelta

import psutil
from sqlmodel import Session, col, delete, select

from app.config import settings
from app.db import engine
from app.models import MonitorSample, utcnow

_thread: threading.Thread | None = None
_stop = threading.Event()
_last: dict[str, float] = {}


def _rates(now: float) -> dict[str, float | int]:
    """Per-second network and disk rates, derived from the previous sample."""
    net = psutil.net_io_counters()
    try:
        disk = psutil.disk_io_counters()
    except (RuntimeError, OSError):
        disk = None

    sent, recv = net.bytes_sent, net.bytes_recv
    read = getattr(disk, "read_bytes", 0) if disk else 0
    write = getattr(disk, "write_bytes", 0) if disk else 0

    previous = dict(_last)
    _last.update({"t": now, "sent": sent, "recv": recv, "read": read, "write": write})

    span = now - previous.get("t", now)
    if span <= 0:
        return {"net_up": 0.0, "net_down": 0.0, "disk_read": 0, "disk_write": 0,
                "net_sent": sent, "net_recv": recv}

    return {
        "net_up": max(0.0, (sent - previous.get("sent", sent)) / span),
        "net_down": max(0.0, (recv - previous.get("recv", recv)) / span),
        "disk_read": int(max(0, (read - previous.get("read", read)) / span)),
        "disk_write": int(max(0, (write - previous.get("write", write)) / span)),
        "net_sent": sent,
        "net_recv": recv,
    }


def sample() -> MonitorSample:
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    rates = _rates(time.time())

    try:
        disk_percent = psutil.disk_usage("/").percent
    except OSError:
        disk_percent = 0.0
    try:
        connections = len(psutil.net_connections(kind="inet"))
    except (psutil.AccessDenied, RuntimeError):
        connections = 0

    import os

    return MonitorSample(
        cpu=psutil.cpu_percent(interval=None),
        memory=memory.percent,
        swap=swap.percent,
        load1=os.getloadavg()[0],
        disk_percent=disk_percent,
        disk_read=rates["disk_read"],
        disk_write=rates["disk_write"],
        net_sent=rates["net_sent"],
        net_recv=rates["net_recv"],
        net_up=round(rates["net_up"], 2),
        net_down=round(rates["net_down"], 2),
        processes=len(psutil.pids()),
        connections=connections,
    )


def record(session: Session) -> MonitorSample:
    row = sample()
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def prune(session: Session, days: int | None = None) -> int:
    keep_days = settings.monitor_retention_days if days is None else days
    cutoff = utcnow() - timedelta(days=max(1, keep_days))
    rows = session.exec(select(MonitorSample).where(col(MonitorSample.taken_at) < cutoff)).all()
    count = len(rows)
    if count:
        session.exec(delete(MonitorSample).where(col(MonitorSample.taken_at) < cutoff))
        session.commit()
    return count


def history(session: Session, hours: int = 6, points: int = 240) -> dict:
    """Samples for the last N hours, thinned to roughly `points` rows."""
    cutoff = utcnow() - timedelta(hours=max(1, hours))
    rows = list(
        session.exec(
            select(MonitorSample)
            .where(col(MonitorSample.taken_at) >= cutoff)
            .order_by(MonitorSample.taken_at)
        ).all()
    )
    step = max(1, len(rows) // max(1, points))
    thinned = rows[::step]
    return {
        "hours": hours,
        "count": len(thinned),
        "total": len(rows),
        "samples": [
            {
                "t": row.taken_at.isoformat(),
                "cpu": row.cpu,
                "memory": row.memory,
                "swap": row.swap,
                "load1": row.load1,
                "disk": row.disk_percent,
                "net_up": row.net_up,
                "net_down": row.net_down,
                "disk_read": row.disk_read,
                "disk_write": row.disk_write,
                "processes": row.processes,
                "connections": row.connections,
            }
            for row in thinned
        ],
    }


def summary(session: Session, hours: int = 24) -> dict:
    cutoff = utcnow() - timedelta(hours=max(1, hours))
    rows = list(
        session.exec(select(MonitorSample).where(col(MonitorSample.taken_at) >= cutoff)).all()
    )
    if not rows:
        return {"hours": hours, "count": 0}

    def stats(values: list[float]) -> dict:
        return {
            "avg": round(sum(values) / len(values), 2),
            "max": round(max(values), 2),
            "min": round(min(values), 2),
        }

    return {
        "hours": hours,
        "count": len(rows),
        "cpu": stats([r.cpu for r in rows]),
        "memory": stats([r.memory for r in rows]),
        "load1": stats([r.load1 for r in rows]),
        "disk": stats([r.disk_percent for r in rows]),
        "net_up": stats([r.net_up for r in rows]),
        "net_down": stats([r.net_down for r in rows]),
        "traffic_sent": max(r.net_sent for r in rows) - min(r.net_sent for r in rows),
        "traffic_recv": max(r.net_recv for r in rows) - min(r.net_recv for r in rows),
    }


def clear(session: Session) -> int:
    rows = session.exec(select(MonitorSample)).all()
    count = len(rows)
    session.exec(delete(MonitorSample))
    session.commit()
    return count


def _loop() -> None:
    from app.services import notify

    psutil.cpu_percent(interval=None)  # prime the counter
    _rates(time.time())
    ticks = 0
    while not _stop.wait(max(10, settings.monitor_interval)):
        try:
            with Session(engine) as session:
                row = record(session)
                notify.evaluate(session, row)
                ticks += 1
                if ticks % 60 == 0:
                    prune(session)
        except Exception:  # a sampler must never kill the panel
            continue


def start() -> bool:
    """Start the sampling thread. Called once from app startup."""
    global _thread
    if not settings.monitor_enabled or settings.dry_run:
        return False
    if _thread and _thread.is_alive():
        return True
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="slimpanel-monitor", daemon=True)
    _thread.start()
    return True


def stop() -> None:
    _stop.set()


def running() -> bool:
    return bool(_thread and _thread.is_alive())

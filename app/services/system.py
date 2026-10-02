from __future__ import annotations

import os
import platform
import time

import psutil

from app.config import settings
from app.errors import PanelError
from app.services import shell

SERVICE_ACTIONS = {"start", "stop", "restart", "reload", "status"}
PSEUDO_FILESYSTEMS = {"squashfs", "tmpfs", "devtmpfs", "overlay", "ramfs", "autofs"}


def overview() -> dict:
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    load = os.getloadavg()
    cores = psutil.cpu_count() or 1
    boot = psutil.boot_time()

    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "uptime_seconds": int(time.time() - boot),
        "cpu": {
            "percent": psutil.cpu_percent(interval=0.2),
            "cores": cores,
            "per_core": psutil.cpu_percent(interval=None, percpu=True),
        },
        "load": {"1m": load[0], "5m": load[1], "15m": load[2], "pressure": round(load[0] / cores, 2)},
        "memory": {
            "total": memory.total,
            "used": memory.used,
            "available": memory.available,
            "percent": memory.percent,
        },
        "swap": {"total": swap.total, "used": swap.used, "percent": swap.percent},
        "disks": disks(),
        "network": network(),
    }


def disks() -> list[dict]:
    result = []
    for part in psutil.disk_partitions(all=False):
        if part.fstype in PSEUDO_FILESYSTEMS:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        result.append(
            {
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            }
        )
    return result


def network() -> dict:
    counters = psutil.net_io_counters()
    return {
        "bytes_sent": counters.bytes_sent,
        "bytes_recv": counters.bytes_recv,
        "packets_sent": counters.packets_sent,
        "packets_recv": counters.packets_recv,
    }


def processes(limit: int = 30, sort_by: str = "cpu") -> list[dict]:
    key = "cpu_percent" if sort_by == "cpu" else "memory_percent"
    rows = []
    for proc in psutil.process_iter(
        ["pid", "name", "username", "cpu_percent", "memory_percent", "status"]
    ):
        info = proc.info
        if info.get("pid") == 0:
            continue
        rows.append(
            {
                "pid": info["pid"],
                "name": info.get("name") or "",
                "username": info.get("username") or "",
                "cpu_percent": info.get("cpu_percent") or 0.0,
                "memory_percent": round(info.get("memory_percent") or 0.0, 2),
                "status": info.get("status") or "",
            }
        )
    rows.sort(key=lambda row: row[key], reverse=True)
    return rows[:limit]


def kill(pid: int) -> None:
    if pid <= 1:
        raise PanelError("Refusing to signal this pid")
    try:
        psutil.Process(pid).terminate()
    except psutil.NoSuchProcess as exc:
        raise PanelError("Process not found") from exc
    except psutil.AccessDenied as exc:
        raise PanelError("Permission denied") from exc


def services() -> list[dict]:
    rows = []
    for name in settings.managed_services:
        result = shell.run([settings.systemctl_bin, "is-active", name], timeout=10)
        rows.append({"name": name, "state": result.stdout.strip() or result.stderr.strip()})
    return rows


def service_action(name: str, action: str) -> shell.Result:
    if name not in settings.managed_services:
        raise PanelError(f"Service '{name}' is not managed by SlimPanel")
    if action not in SERVICE_ACTIONS:
        raise PanelError(f"Unsupported action '{action}'")
    return shell.run([settings.systemctl_bin, action, name], timeout=60)


def connections(limit: int = 100) -> list[dict]:
    """Established connections, grouped by remote address."""
    counts: dict[str, dict] = {}
    try:
        rows = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, RuntimeError):
        return []

    for conn in rows:
        if conn.status != psutil.CONN_ESTABLISHED or not conn.raddr:
            continue
        key = conn.raddr.ip
        entry = counts.setdefault(key, {"address": key, "count": 0, "ports": set()})
        entry["count"] += 1
        if conn.laddr:
            entry["ports"].add(conn.laddr.port)

    result = [
        {"address": entry["address"], "count": entry["count"], "ports": sorted(entry["ports"])}
        for entry in counts.values()
    ]
    result.sort(key=lambda row: row["count"], reverse=True)
    return result[:limit]


def system_users() -> list[dict]:
    """Login-capable accounts, which is what matters for an FTP or SSH home."""
    import pwd

    rows = []
    for entry in pwd.getpwall():
        if entry.pw_shell.rstrip().endswith(("nologin", "false")) and entry.pw_uid >= 1000:
            continue
        rows.append(
            {
                "name": entry.pw_name,
                "uid": entry.pw_uid,
                "gid": entry.pw_gid,
                "home": entry.pw_dir,
                "shell": entry.pw_shell,
                "system": entry.pw_uid < 1000,
            }
        )
    rows.sort(key=lambda row: (row["system"], row["uid"]))
    return rows
